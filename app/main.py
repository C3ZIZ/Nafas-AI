from fastapi import FastAPI, HTTPException
from .utils import get_audio_info, generate_waveform_plot
from fastapi.responses import StreamingResponse
import os
from .utils import get_segments

app = FastAPI(title="Nafas AI")

@app.get("/")
def read_root():
    return {"message": "Nafas API is running!"}

@app.get("/inspect/{filename}")
def inspect_audio(filename: str):
    # Assuming files are in a folder named 'data'
    path = f"data/{filename}"
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="File not found in data")
    
    info = get_audio_info(path)
    return info



@app.get("/plot/{filename}")
def get_waveform(filename: str):
    path = f"data/{filename}"
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="File not found")
    
    image_buffer = generate_waveform_plot(path)
    return StreamingResponse(image_buffer, media_type="image/png")





@app.get("/process/{filename}")
def process_audio(filename: str):
    # Filenames in Kaggle are like '101_1b1_Al_sc_Meditron.wav'
    # The annotation is '101_1b1_Al_sc_Meditron.txt'
    base_name = filename.replace(".wav", "")
    audio_path = f"data/{filename}"
    txt_path = f"data/{base_name}.txt"
    
    if not os.path.exists(audio_path) or not os.path.exists(txt_path):
        raise HTTPException(status_code=404, detail="Audio or Annotation file missing")
    
    segments, sr = get_segments(audio_path, txt_path)
    
    return {
        "filename": filename,
        "total_breaths_found": len(segments),
        "sampling_rate_used": sr,
        "segments_summary": [
            {"id": s["id"], "label": s["label"], "samples": len(s["data"])} 
            for s in segments
        ]
    }