from fastapi import FastAPI, HTTPException
from .utils import get_audio_info, generate_waveform_plot
from fastapi.responses import StreamingResponse
import os

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