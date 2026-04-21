from pathlib import Path

from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.responses import StreamingResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import librosa
import torch
import torch.nn.functional as F
import pandas as pd
import os
from pydantic import BaseModel
import numpy as np
import json
import shutil
import uuid

from .clinical_model import rf_model
from .nlp_model import nlp_model

from .utils import (
    get_audio_info,
    generate_waveform_plot,
    get_segments,
    generate_mel_spectrogram,
    prepare_tensor_for_ai,
)
from .model import nafas_model, device

# Reverse mapping to get string names for the 8 diseases
REVERSE_DISEASE_MAP = {
    0: "Healthy",
    1: "COPD",
    2: "Asthma",
    3: "Bronchiectasis",
    4: "Pneumonia",
    5: "URTI",
    6: "LRTI",
    7: "Bronchiolitis",
}

app = FastAPI(title="Nafas AI")

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
AUDIO_DATA_DIR = DATA_DIR / "audio_and_txt_files"

# Allow the Vue dev server to communicate during development
_DEV_ORIGINS = ["http://localhost:5173", "http://127.0.0.1:5173"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=_DEV_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Optionally mount a built frontend (frontend/dist) so the API can serve the UI
_FRONTEND_DIST = Path(__file__).resolve().parent.parent / "frontend" / "dist"
if _FRONTEND_DIST.exists():
    app.mount("/frontend", StaticFiles(directory=str(_FRONTEND_DIST), html=True), name="frontend")

# Load the Knowledge Base created by prepare_nlp.py (if present)
KB_PATH = DATA_DIR / "knowledge_base.json"
if KB_PATH.exists():
    try:
        with open(KB_PATH, 'r', encoding='utf-8') as _f:
            knowledge_base = json.load(_f)
    except Exception:
        knowledge_base = {}
else:
    knowledge_base = {}


def _resolve_data_file(filename: str) -> Path:
    """Resolve a dataset file from known data directories.

    Supports files placed either directly under `data/` or in
    `data/audio_and_txt_files/`.
    """
    if Path(filename).name != filename:
        raise HTTPException(status_code=400, detail="Invalid filename")

    candidates = [DATA_DIR / filename, AUDIO_DATA_DIR / filename]
    for candidate in candidates:
        if candidate.exists() and candidate.is_file():
            return candidate

    raise HTTPException(status_code=404, detail="File not found in data folders")


@app.get("/")
def read_root():
    """Root endpoint.

    Returns a simple JSON message confirming the API is reachable.
    """
    return {"message": "Nafas API is running!"}


@app.post("/upload_audio/")
async def upload_audio(file: UploadFile = File(...)):
    """Accept an uploaded audio file from the browser and save it into `data/`.

    The endpoint returns the server-side filename which can be passed to
    `/diagnose_trinity/{filename}`.
    """
    # Basic extension check
    name = Path(file.filename).name
    ext = Path(name).suffix.lower()
    if ext not in [".wav", ".mp3", ".m4a", ".flac"]:
        raise HTTPException(status_code=400, detail="Unsupported file type")

    dest_name = f"{uuid.uuid4().hex}{ext}"
    dest_path = DATA_DIR / dest_name

    try:
        with open(dest_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save file: {e}")
    finally:
        await file.close()

    return {"filename": dest_name, "saved_at": str(dest_path)}


@app.get("/inspect/{filename}")
def inspect_audio(filename: str):
    """Inspect an audio file and return basic audio metadata.

    Args:
        filename (str): Name of the audio file located under the `data/` folder.

    Returns:
        dict: metadata returned by `get_audio_info` (sample rate, duration, total samples, device info).
    """
    path = _resolve_data_file(filename)
    info = get_audio_info(str(path))
    return info


@app.get("/plot/{filename}")
def get_waveform(filename: str):
    """Return a PNG waveform image for the given audio file.

    The image is returned as a `StreamingResponse` with media type `image/png`.
    """
    path = _resolve_data_file(filename)
    image_buffer = generate_waveform_plot(str(path))
    return StreamingResponse(image_buffer, media_type="image/png")


@app.get("/audio/{filename}")
def serve_audio(filename: str):
    """Serve raw audio files from the `data/` folder so the frontend can play samples.

    This endpoint resolves allowed data locations and returns a `FileResponse`.
    """
    path = _resolve_data_file(filename)
    return FileResponse(str(path), media_type="audio/wav")


@app.get("/process/{filename}")
def process_audio(filename: str):
    """Process an audio file to return annotated segments or fallback raw segment.

    Workflow:
    - If a corresponding annotation `.txt` file exists, uses `get_segments` to extract labeled segments.
    - Otherwise, loads the full audio and returns it as a single 'unknown' segment.

    Returns a JSON summary including filename, annotation status, number of segments, sampling rate, and per-segment sizes.
    """
    audio_path = _resolve_data_file(filename)
    txt_path = audio_path.with_suffix(".txt")

    if txt_path.exists():
        segments, sr = get_segments(str(audio_path), str(txt_path))
        annotation_status = "found"
    else:
        y, sr = librosa.load(str(audio_path), sr=22050)
        segments = [{"id": 0, "data": y, "label": "unknown"}]
        annotation_status = "missing"

    return {
        "filename": filename,
        "annotation_status": annotation_status,
        "total_breaths_found": len(segments),
        "sampling_rate_used": sr,
        "segments_summary": [
            {"id": s["id"], "label": s["label"], "samples": len(s["data"])}
            for s in segments
        ],
    }


@app.get("/spectrogram/{filename}")
def get_spectrogram(filename: str):
    path = _resolve_data_file(filename)

    # Generate the image buffer
    image_buffer = generate_mel_spectrogram(str(path))

    # Return it as an image stream to the browser
    return StreamingResponse(image_buffer, media_type="image/png")


@app.get("/predict/{filename}")
def predict_audio(filename: str):
    path = _resolve_data_file(filename)

    # Convert audio into the tensor format expected by the CNN.
    input_tensor = prepare_tensor_for_ai(str(path)).to(device)

    nafas_model.eval()
    with torch.no_grad():
        output = nafas_model(input_tensor)
        prediction_index = torch.argmax(output, dim=1).item()

    # Map prediction index to disease name using the reverse map
    result = REVERSE_DISEASE_MAP.get(prediction_index, "Unknown")

    return {
        "filename": filename,
        "prediction": result,
        "raw_model_output": output.detach().cpu().tolist(),
        "device_used": str(device),
    }


@app.get("/diagnose/{filename}")
def full_diagnosis(filename: str):
    path = _resolve_data_file(filename)
    txt_path = path.with_suffix(".txt")

    if not path.exists():
        raise HTTPException(status_code=404, detail="File not found")

    # 1. Count Crackles and Wheezes from the annotation file (if present)
    crackles_count = 0
    wheezes_count = 0
    if txt_path.exists():
        try:
            annotations = pd.read_csv(str(txt_path), sep=r"\s+", header=None, names=["start", "end", "crackle", "wheeze"], engine="python")
            crackles_count = int(annotations["crackle"].sum())
            wheezes_count = int(annotations["wheeze"].sum())
        except Exception:
            # If annotation parsing fails, leave counts at zero
            crackles_count = 0
            wheezes_count = 0

    # 2. Prepare the audio for the AI
    input_tensor = prepare_tensor_for_ai(str(path)).to(device)

    # 3. AI Prediction Pipeline
    nafas_model.eval()
    with torch.no_grad():
        raw_output = nafas_model(input_tensor)
        # Convert raw logits to percentages using softmax
        probabilities = F.softmax(raw_output, dim=1)[0] * 100
        top_prob, top_class_idx = torch.max(probabilities, dim=0)

    # 4. Format all confidences nicely
    all_confidences = {}
    for idx, prob in enumerate(probabilities):
        disease_name = REVERSE_DISEASE_MAP.get(idx, str(idx))
        all_confidences[disease_name] = round(prob.item(), 2)

    return {
        "filename": filename,
        "most_likely_disease": REVERSE_DISEASE_MAP.get(top_class_idx.item(), "Unknown"),
        "confidence_score": f"{round(top_prob.item(), 2)}%",
        "anomalies_detected": {
            "total_crackles": crackles_count,
            "total_wheezes": wheezes_count,
        },
        "all_disease_probabilities": all_confidences,
    }


# --- Multi-Modal Fusion Endpoint ---
class PatientVitals(BaseModel):
    age: float
    sex: int          # 1 for Male, 0 for Female
    bmi: float
    spo2: float       # e.g., 98.5
    temperature: float# e.g., 37.1
    smoker: int       # 1 for Yes, 0 for No


@app.post("/diagnose_fusion/{filename}")
def multi_modal_diagnosis(filename: str, vitals: PatientVitals):
    audio_path = str(_resolve_data_file(filename))
    if not os.path.exists(audio_path):
        raise HTTPException(status_code=404, detail="Audio file not found")
        
    if rf_model is None:
        raise HTTPException(status_code=500, detail="Clinical model not trained. Run train.py first.")

    # --- PIPELINE A: AUDIO (CNN) ---
    input_tensor = prepare_tensor_for_ai(audio_path).to(device)
    nafas_model.eval()
    with torch.no_grad():
        raw_audio_output = nafas_model(input_tensor)
        # Get audio probabilities (shape: 1x8)
        audio_probs = F.softmax(raw_audio_output, dim=1).cpu().numpy()[0]

    # --- PIPELINE B: CLINICAL (Random Forest) ---
    vitals_array = np.array([[vitals.age, vitals.sex, vitals.bmi, 
                              vitals.spo2, vitals.temperature, vitals.smoker]])
    clinical_probs = rf_model.predict_proba(vitals_array)[0]

    # --- THE FUSION CENTER (Soft Voting) ---
    fused_probs = (audio_probs * 0.6) + (clinical_probs * 0.4)
    top_class_idx = int(np.argmax(fused_probs))
    top_prob = fused_probs[top_class_idx] * 100

    all_confidences = {
        REVERSE_DISEASE_MAP[idx]: round(float(prob * 100), 2)
        for idx, prob in enumerate(fused_probs)
    }

    return {
        "filename": filename,
        "final_diagnosis": REVERSE_DISEASE_MAP[top_class_idx],
        "confidence_score": f"{round(top_prob, 2)}%",
        "breakdown": {
            "audio_model_top_pick": REVERSE_DISEASE_MAP[int(np.argmax(audio_probs))],
            "clinical_model_top_pick": REVERSE_DISEASE_MAP[int(np.argmax(clinical_probs))]
        },
        "all_disease_probabilities": all_confidences
    }


# --- Trinity Endpoint (Audio + Vitals + Subjective History) ---
class PatientProfile(BaseModel):
    age: float
    sex: int          # 1 Male, 0 Female
    bmi: float
    spo2: float       # Blood oxygen
    temperature: float
    smoker: int       # 1 Yes, 0 No
    patient_notes: str # The Subjective History text


@app.post("/diagnose_trinity/{filename}")
def diagnose_trinity(filename: str, patient: PatientProfile):
    audio_path = str(_resolve_data_file(filename))
    if not os.path.exists(audio_path):
        raise HTTPException(status_code=404, detail="Audio file not found")
        
    if rf_model is None or nlp_model is None:
        raise HTTPException(status_code=500, detail="Models missing. Run train.py")

    # --- BRAIN 1: AUDIO (CNN) ---
    input_tensor = prepare_tensor_for_ai(audio_path).to(device)
    nafas_model.eval()
    with torch.no_grad():
        raw_audio = nafas_model(input_tensor)
        audio_probs = F.softmax(raw_audio, dim=1).cpu().numpy()[0]

    # --- BRAIN 2: VITALS (Random Forest) ---
    vitals_array = np.array([[patient.age, patient.sex, patient.bmi, 
                              patient.spo2, patient.temperature, patient.smoker]])
    vitals_probs = rf_model.predict_proba(vitals_array)[0]

    # --- BRAIN 3: TEXT (NLP) ---
    nlp_probs = nlp_model.predict_proba([patient.patient_notes])[0]

    # --- THE FUSION CENTER (Soft Voting) ---
    # We assign weights based on clinical importance
    # Audio: 40% | Vitals: 30% | NLP (Text): 30%
    fused_probs = (audio_probs * 0.40) + (vitals_probs * 0.30) + (nlp_probs * 0.30)
    
    top_class_idx = int(np.argmax(fused_probs))
    final_disease = REVERSE_DISEASE_MAP[top_class_idx]
    confidence = fused_probs[top_class_idx] * 100

    # Fetch Doctor Advice
    doctor_advice = knowledge_base.get(final_disease, {
        "description": "Diagnosis confirmed.",
        "precautions": ["Consult a healthcare provider for a detailed plan."]
    })

    return {
        "status": "Success",
        "final_diagnosis": final_disease,
        "overall_confidence": f"{round(confidence, 2)}%",
        "doctor_summary": {
            "disease_description": doctor_advice.get("description", ""),
            "recommended_precautions": doctor_advice.get("precautions", [])
        },
        "model_breakdown": {
            "audio_cnn_prediction": REVERSE_DISEASE_MAP[int(np.argmax(audio_probs))],
            "vitals_rf_prediction": REVERSE_DISEASE_MAP[int(np.argmax(vitals_probs))],
            "symptoms_nlp_prediction": REVERSE_DISEASE_MAP[int(np.argmax(nlp_probs))]
        }
    }
