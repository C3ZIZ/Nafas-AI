import librosa
import torch
import librosa.display
import matplotlib.pyplot as plt
import io
import numpy as np
from scipy.signal import butter, lfilter
import pandas as pd

def get_audio_info(file_path):
    """Load an audio file and return basic metadata.

    Args:
        file_path (str): Path to an audio file readable by `librosa`.

    Returns:
        dict: Contains `sample_rate`, `duration_sec`, `total_samples`, and `device_info`.
    """
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
    """Generate a waveform plot for `file_path` and return it as a PNG buffer.

    The returned value is an in-memory `io.BytesIO` buffer positioned at byte 0,
    ready to be streamed as `image/png` (e.g., via `StreamingResponse`).
    """
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





# 1. The Butterworth "Cleaner"
def butter_bandpass_filter(data, lowcut=50, highcut=2500, fs=22050, order=5):
    """Apply a Butterworth band-pass filter to 1D audio data.

    Args:
        data (np.ndarray): Input audio signal.
        lowcut (float): Low cutoff frequency in Hz.
        highcut (float): High cutoff frequency in Hz.
        fs (int): Sampling frequency of the audio in Hz.
        order (int): Filter order.

    Returns:
        np.ndarray: Filtered audio signal.
    """
    nyq = 0.5 * fs
    low = lowcut / nyq
    high = highcut / nyq
    b, a = butter(order, [low, high], btype='band')
    y = lfilter(b, a, data)
    return y




# 2. The Slicer (Segmentation)
def get_segments(audio_path, annotation_path):
    """Extract labeled audio segments using an annotation file.

    The function:
    - Loads audio at 22050 Hz.
    - Applies the Butterworth band-pass filter.
    - Reads annotations (start, end, crackle, wheeze) and slices the audio into segments.

    Args:
        audio_path (str): Path to the audio `.wav` file.
        annotation_path (str): Path to the annotation `.txt` file (tab/TSV-like).

    Returns:
        tuple: (`segments`, `sr`) where `segments` is a list of dicts with `id`, `data` (np.ndarray), and `label`.
    """
    # Load audio at a fixed sample rate (Resampling)
    y, sr = librosa.load(audio_path, sr=22050)

    # Clean the audio immediately
    y_clean = butter_bandpass_filter(y, fs=sr)

    # Read the .txt file (Start, End, Crackle, Wheeze)
    # The Kaggle dataset uses space-separated values
    annotations = pd.read_csv(annotation_path, sep='\t', header=None, 
                             names=['start', 'end', 'crackle', 'wheeze'])

    segments = []
    for i, row in annotations.iterrows():
        start_sample = int(row['start'] * sr)
        end_sample = int(row['end'] * sr)
        segment = y_clean[start_sample:end_sample]
        segments.append({
            "id": i,
            "data": segment,
            "label": "unhealthy" if (row['crackle'] or row['wheeze']) else "healthy"
        })

    return segments, sr