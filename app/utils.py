import librosa
import torch
import librosa
import librosa.display
import matplotlib.pyplot as plt
import io

def get_audio_info(file_path):
    # Load audio
    y, sr = librosa.load(file_path, sr=None)
    duration = librosa.get_duration(y=y, sr=sr)
    
    # Check GPU status
    gpu_available = torch.cuda.is_available()
    gpu_name = torch.cuda.get_device_name(0) if gpu_available else "None"

    return {
        "sample_rate": sr,
        "duration_sec": round(duration, 2),
        "total_samples": len(y),
        "device_info": {"gpu_available": gpu_available, "gpu_name": gpu_name}
    }




def generate_waveform_plot(file_path):
    # 1. Load the audio
    y, sr = librosa.load(file_path, sr=None)
    
    # 2. Create the plot without opening a window (Agg backend)
    plt.switch_backend('Agg') 
    plt.figure(figsize=(10, 4))
    librosa.display.waveshow(y, sr=sr, color='blue')
    plt.title(f"Waveform: {file_path.split('/')[-1]}")
    plt.xlabel("Time (s)")
    plt.ylabel("Amplitude")
    plt.tight_layout()

    # 3. Save plot to a buffer (RAM)
    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)
    plt.close() # Free up memory
    
    return buf