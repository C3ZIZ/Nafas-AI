from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
import librosa
import torch

from .utils import (
    get_audio_info,
    generate_waveform_plot,
    get_segments,
    generate_mel_spectrogram,
    prepare_tensor_for_ai,
)
from .model import nafas_model, device

app = FastAPI(title="Nafas AI")

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
AUDIO_DATA_DIR = DATA_DIR / "audio_and_txt_files"


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

    classes = {0: "Normal", 1: "Wheeze", 2: "Crackle"}
    result = classes.get(prediction_index, "Unknown")

    return {
        "filename": filename,
        "prediction": result,
        "raw_model_output": output.detach().cpu().tolist(),
        "device_used": str(device),
    }
