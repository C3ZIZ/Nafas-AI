from pathlib import Path
from typing import Optional

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

from . import clinical_model as _clinical_module
from . import nlp_model as _nlp_module
from .text_normalizer import to_clinical_english, contains_arabic
from .llm_provider import chat as llm_chat, health as llm_health, LLMProviderError
from . import meta_fusion as _meta_fusion

from .utils import (
    get_audio_info,
    generate_waveform_plot,
    get_segments,
    generate_mel_spectrogram,
    prepare_tensor_for_ai,
    predict_audio_segmented,
)
from .model import nafas_model, device
from .medications import get_medications, get_all_sources
from .medication_advisor import recommend as advisor_recommend
from .auto_train import ensure_models_trained

# ---------------------------------------------------------------------------
# Multi-modal fusion is delegated to a TRAINED stacking meta-classifier
# (see app/meta_fusion.py and train_meta_fusion.py). The meta-model
# takes the three brains' 8-dim probability vectors as 24 features and
# outputs the fused 8-dim distribution. Per-brain reliability, per-class
# bias correction, and cross-brain interactions are LEARNED from
# patient-grouped data — not hard-coded.
# ---------------------------------------------------------------------------


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


@app.on_event("startup")
def _ensure_trained_on_startup():
    """Train any missing models (CNN half-dataset, full NLP, full clinical RF).

    This makes the API self-bootstrapping: a fresh checkout of the repo can
    `uvicorn app.main:app` and the server will train whatever weights are
    missing before serving the first request. No-ops once weights exist.
    """
    try:
        ensure_models_trained()
    except Exception as e:
        print(f"[startup] auto-train guard caught: {e}")

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
    txt_path = path.with_suffix(".txt")
    txt_arg = str(txt_path) if txt_path.exists() else None

    # Use the segment-aggregating inference path that mirrors training.
    mean_probs, per_seg_probs, n_seg = predict_audio_segmented(
        str(path), nafas_model, device, txt_path=txt_arg, return_per_segment=True
    )
    prediction_index = int(np.argmax(mean_probs))

    return {
        "filename": filename,
        "prediction": REVERSE_DISEASE_MAP.get(prediction_index, "Unknown"),
        "n_segments": int(n_seg),
        "mean_probabilities": {
            REVERSE_DISEASE_MAP[i]: round(float(p) * 100, 2) for i, p in enumerate(mean_probs)
        },
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

    # 2. Run the audio CNN over per-breath segments (matches training).
    txt_arg = str(txt_path) if txt_path.exists() else None
    mean_probs = predict_audio_segmented(
        str(path), nafas_model, device, txt_path=txt_arg
    )
    top_class_idx = int(np.argmax(mean_probs))
    top_prob = float(mean_probs[top_class_idx]) * 100

    all_confidences = {
        REVERSE_DISEASE_MAP.get(i, str(i)): round(float(p) * 100, 2)
        for i, p in enumerate(mean_probs)
    }

    return {
        "filename": filename,
        "most_likely_disease": REVERSE_DISEASE_MAP.get(top_class_idx, "Unknown"),
        "confidence_score": f"{round(top_prob, 2)}%",
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
        
    if _clinical_module.rf_model is None:
        raise HTTPException(status_code=500, detail="Clinical model not trained. Run train.py first.")

    # --- PIPELINE A: AUDIO (CNN) — segment-aggregated to match training. ---
    txt_p = Path(audio_path).with_suffix(".txt")
    audio_probs = predict_audio_segmented(
        audio_path, nafas_model, device,
        txt_path=str(txt_p) if txt_p.exists() else None,
    )

    # --- PIPELINE B: CLINICAL (Random Forest) ---
    vitals_array = np.array([[vitals.age, vitals.sex, vitals.bmi,
                              vitals.spo2, vitals.temperature, vitals.smoker]])
    clinical_probs = _clinical_module.rf_model.predict_proba(vitals_array)[0]

    # --- FUSION (learned stacking) ---
    # This endpoint takes only two modalities (audio + vitals), but the
    # meta-classifier was trained on three. Pass a uniform NLP vector
    # so the meta-model gets an uninformative prior for that feature —
    # principled "missing modality" handling without any hand-tuned
    # rebalancing of the remaining brains.
    uniform_nlp = np.full(8, 1.0 / 8)
    try:
        fused_probs, _ = _meta_fusion.fuse(audio_probs, clinical_probs, uniform_nlp)
    except _meta_fusion.MetaFusionUnavailableError as e:
        raise HTTPException(status_code=503, detail=str(e))
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
def diagnose_trinity(filename: str, patient: PatientProfile, debug: bool = False):
    audio_path = str(_resolve_data_file(filename))
    if not os.path.exists(audio_path):
        raise HTTPException(status_code=404, detail="Audio file not found")
        
    if _clinical_module.rf_model is None or _nlp_module.nlp_model is None:
        raise HTTPException(status_code=500, detail="Models missing. Run train.py")

    # --- BRAIN 1: AUDIO (CNN) — segment-aggregated to match training. ---
    txt_p = Path(audio_path).with_suffix(".txt")
    audio_probs, per_seg_probs, n_segments = predict_audio_segmented(
        audio_path, nafas_model, device,
        txt_path=str(txt_p) if txt_p.exists() else None,
        return_per_segment=True,
    )

    # --- BRAIN 2: VITALS (Random Forest) ---
    vitals_array = np.array([[patient.age, patient.sex, patient.bmi,
                              patient.spo2, patient.temperature, patient.smoker]])
    vitals_probs = _clinical_module.rf_model.predict_proba(vitals_array)[0]

    # --- BRAIN 3: TEXT (NLP) ---
    # The NLP pipeline (TF-IDF + Naive Bayes) and the medication-advisor's
    # TF-IDF ranker were both trained on an English clinical vocabulary
    # (see data/master_nlp_data.csv). If the user types Arabic, the
    # Hugging Face translation API converts it before inference. A
    # missing/invalid HF_TOKEN surfaces here as a 503 — by design, we
    # do NOT fall back to a partial local dictionary.
    try:
        nlp_text = to_clinical_english(patient.patient_notes)
    except LLMProviderError as e:
        raise HTTPException(status_code=503, detail=str(e))
    nlp_probs = _nlp_module.nlp_model.predict_proba([nlp_text])[0]

    # --- THE FUSION CENTER ---
    # Learned stacking classifier (LogisticRegression trained on
    # patient-grouped triplets — see train_meta_fusion.py). If the
    # meta-classifier hasn't been trained yet, surface a 503 so the
    # user knows to run training; we do NOT fall back to heuristic
    # weights.
    try:
        fused_probs, fusion_info = _meta_fusion.fuse(audio_probs, vitals_probs, nlp_probs)
    except _meta_fusion.MetaFusionUnavailableError as e:
        raise HTTPException(status_code=503, detail=str(e))

    top_class_idx = int(np.argmax(fused_probs))
    final_disease = REVERSE_DISEASE_MAP[top_class_idx]
    confidence = fused_probs[top_class_idx] * 100

    # Fetch Doctor Advice
    doctor_advice = knowledge_base.get(final_disease, {
        "description": "Diagnosis confirmed.",
        "precautions": ["Consult a healthcare provider for a detailed plan."]
    })

    all_confidences = {
        REVERSE_DISEASE_MAP[idx]: round(float(prob * 100), 2)
        for idx, prob in enumerate(fused_probs)
    }

    response = {
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
        },
        "all_disease_probabilities": all_confidences,
        "medication_suggestions": get_medications(final_disease),
        "medication_cards": advisor_recommend(
            final_disease,
            context={
                "age": patient.age,
                "sex": patient.sex,
                "bmi": patient.bmi,
                "spo2": patient.spo2,
                "temperature": patient.temperature,
                "smoker": patient.smoker,
                # Feed the normalized form so the advisor's TF-IDF cosine
                # against med descriptors works for Arabic input too.
                "patient_notes": nlp_text,
            },
            top_n=4,
        ),
    }

    if debug:
        # Surface per-stage outputs so the user can see exactly where a
        # diagnosis went wrong. Pass `?debug=true` on the request.
        response["debug"] = {
            "audio": {
                "n_segments": int(n_segments),
                "probs": {REVERSE_DISEASE_MAP[i]: round(float(p) * 100, 2) for i, p in enumerate(audio_probs)},
                "per_segment_top_class": [
                    REVERSE_DISEASE_MAP[int(np.argmax(p))] for p in per_seg_probs
                ],
            },
            "vitals": {
                "probs": {REVERSE_DISEASE_MAP[i]: round(float(p) * 100, 2) for i, p in enumerate(vitals_probs)},
            },
            "nlp": {
                "probs": {REVERSE_DISEASE_MAP[i]: round(float(p) * 100, 2) for i, p in enumerate(nlp_probs)},
                "input_text": patient.patient_notes,
                "normalized_text": nlp_text,
                "was_translated": nlp_text != patient.patient_notes,
            },
            "fusion": {
                **fusion_info,
                "fused_probs": all_confidences,
            },
        }

    return response


class AdvisorContext(BaseModel):
    age: Optional[float] = None
    sex: Optional[int] = None
    bmi: Optional[float] = None
    spo2: Optional[float] = None
    temperature: Optional[float] = None
    smoker: Optional[int] = 0
    patient_notes: Optional[str] = ""
    top_n: Optional[int] = 4


@app.post("/medications/{disease}/cards")
def medication_cards(disease: str, ctx: AdvisorContext):
    """Run the medication advisor (TF-IDF + ranker) for a disease.

    Returns ranked, ready-to-render medication cards with name, description,
    why-this-medicine reasoning, bulleted dosage / side-effects / price, and
    a link to the product page (or chain search URL).
    """
    payload = ctx.model_dump(exclude_none=True)
    # Normalize Arabic patient_notes onto the English clinical vocabulary
    # the advisor's TF-IDF ranker was fitted on. Pure-English text passes
    # through unchanged.
    if payload.get("patient_notes"):
        try:
            payload["patient_notes"] = to_clinical_english(payload["patient_notes"])
        except LLMProviderError as e:
            raise HTTPException(status_code=503, detail=str(e))
    return advisor_recommend(
        disease,
        context=payload,
        top_n=ctx.top_n or 4,
    )


# ---------------------------------------------------------------------------
# Doctor-facing chat assistant
#
# Unrelated to the breath-flow pipeline above: a free-form medical
# consultation chat for clinicians. Routed through Hugging Face
# Inference Providers via app/llm_provider.py.
# ---------------------------------------------------------------------------

_DOCTOR_SYSTEM_PROMPT_EN = (
    "You are an evidence-based clinical decision-support assistant for "
    "licensed physicians. The user is a doctor seeking help reasoning "
    "about symptoms, differential diagnoses, and medication options.\n\n"
    "Guidelines:\n"
    "- Give concrete, actionable answers; do not refuse normal clinical "
    "questions about drugs, doses, interactions, or contraindications.\n"
    "- When suggesting medications, include drug class, typical adult "
    "dose range, key contraindications, and notable interactions.\n"
    "- For differentials, rank the most likely conditions first and note "
    "the discriminating features.\n"
    "- Flag red-flag symptoms that warrant urgent escalation.\n"
    "- Reply in the SAME language the doctor used (English or Arabic). "
    "If asked in Arabic, answer in Arabic.\n"
    "- Always close with a one-line reminder that this is decision "
    "support, not a substitute for the physician's own judgement."
)


class ChatMessage(BaseModel):
    role: str    # 'user' or 'assistant'
    content: str


class DoctorChatRequest(BaseModel):
    messages: list[ChatMessage]
    temperature: Optional[float] = 0.3
    max_tokens: Optional[int] = 768


@app.post("/doctor_chat")
def doctor_chat(req: DoctorChatRequest):
    """Free-form clinical chat for a doctor. Bilingual (EN/AR).

    Body:
        {
          "messages": [ {"role": "user", "content": "..."} , ... ],
          "temperature": 0.3,   # optional
          "max_tokens": 768     # optional
        }

    Returns:
        { "reply": "...", "model": "<hf chat model id>" }

    503 is returned with a human-readable message if HF_TOKEN is missing
    or the inference API is unreachable.
    """
    msgs = [{"role": m.role, "content": m.content} for m in req.messages if m.content.strip()]
    if not msgs:
        raise HTTPException(status_code=400, detail="messages is empty.")
    if msgs[-1]["role"] != "user":
        raise HTTPException(status_code=400, detail="Last message must be from the user.")

    try:
        reply = llm_chat(
            messages=msgs,
            system=_DOCTOR_SYSTEM_PROMPT_EN,
            temperature=float(req.temperature or 0.3),
            max_tokens=int(req.max_tokens or 768),
        )
    except LLMProviderError as e:
        raise HTTPException(status_code=503, detail=str(e))

    return {"reply": reply, "model": llm_health()["chat_model"]}


@app.get("/llm_status")
def llm_status():
    """Lightweight diagnostic: is HF_TOKEN configured? Which models?

    Does NOT call Hugging Face. Safe to poll from the UI to decide
    whether to surface a 'configure your key' banner.
    """
    return llm_health()


@app.get("/meta_fusion_status")
def meta_fusion_status():
    """Is the trained stacking fusion classifier loaded and ready?

    Returns the persisted training metadata (CV macro-F1, row counts,
    estimator, etc.) when available. Safe to poll from the UI.
    """
    return _meta_fusion.info()


@app.get("/medications/{disease}")
def medications_for_disease(disease: str):
    """Lookup Saudi pharmacy medication suggestions for a disease label.

    Disease must be one of: Healthy, COPD, Asthma, Bronchiectasis,
    Pneumonia, URTI, LRTI, Bronchiolitis.
    """
    return get_medications(disease)


@app.get("/sources")
def list_data_sources():
    """Return the full registry of data sources (guidelines, formularies, pharmacy listings)."""
    return {"count": len(get_all_sources()), "sources": get_all_sources()}


@app.post("/admin/retrain")
def admin_retrain():
    """Force a re-check of model weights and train any that are missing.

    Does NOT delete existing weights. To retrain from scratch, delete
    the relevant `*_weights.*` files first, then call this endpoint.
    """
    return ensure_models_trained()
