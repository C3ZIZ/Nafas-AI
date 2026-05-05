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

    # Read the .txt file (Start, End, Crackle, Wheeze).
    # ICBHI labels are whitespace-delimited (spaces/tabs depending on export).
    annotations = pd.read_csv(
        annotation_path,
        sep=r'\s+',
        header=None,
        names=['start', 'end', 'crackle', 'wheeze'],
        engine='python',
    )

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




def generate_mel_spectrogram(audio_path):
    # 1. Load the audio at our standardized sample rate
    y, sr = librosa.load(audio_path, sr=22050)
    
    # Optional: You could pass 'y' through your Day 2 butter_bandpass_filter here!
    
    # 2. Generate the Mel-Spectrogram
    # n_mels: Number of frequency bands (resolution on the Y axis)
    # fmax: Max frequency. We set it to 2500Hz because human breath sounds rarely exceed this.
    S = librosa.feature.melspectrogram(y=y, sr=sr, n_mels=128, fmax=2500)
    
    # 3. Convert power (amplitude) to Decibels (logarithmic scale)
    # This makes faint sounds more visible and matches human hearing limits.
    S_dB = librosa.power_to_db(S, ref=np.max)
    
    # 4. Create the visual plot in memory
    plt.switch_backend('Agg')
    plt.figure(figsize=(10, 4))
    
    # Display the spectrogram
    librosa.display.specshow(S_dB, x_axis='time', y_axis='mel', sr=sr, fmax=2500, cmap='magma')
    
    plt.colorbar(format='%+2.0f dB')
    plt.title(f"Mel-Spectrogram: {audio_path.split('/')[-1]}")
    plt.tight_layout()
    
    # Save to buffer
    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)
    plt.close()
    
    return buf


def prepare_tensor_for_ai(audio_path):
    """Convert an audio file into a model-ready mel-spectrogram tensor.

    IMPORTANT: this MUST match how the training dataset processes audio
    (`app/dataset.py`):

        1. Resample to 22050 Hz
        2. Butterworth band-pass filter 50–2500 Hz
        3. Mel-spectrogram (n_mels=128, fmax=2500)
        4. Log-power conversion vs ref=max

    Returns a tensor with shape [1, 1, 128, time_frames].

    NOTE: this still passes the *whole* file as a single sample. For
    breath-cycle classification you should prefer
    `predict_audio_segmented(...)` which slices into segments using the
    matching `.txt` annotation (or a sliding window) and aggregates
    softmax probabilities — the same way the model was trained.
    """
    y, sr = librosa.load(audio_path, sr=22050)
    # Apply the same band-pass filter the training dataset uses,
    # otherwise inference sees a different input distribution.
    y = butter_bandpass_filter(y, fs=sr)
    S = librosa.feature.melspectrogram(y=y, sr=sr, n_mels=128, fmax=2500)
    S_dB = librosa.power_to_db(S, ref=np.max)

    tensor = torch.tensor(S_dB, dtype=torch.float32).unsqueeze(0).unsqueeze(0)
    return tensor


def _segment_audio(y, sr, txt_path=None, window_sec=2.5, hop_sec=1.5,
                   min_segment_samples=4096):
    """Slice cleaned audio into breath-cycle segments.

    If `txt_path` exists and is parseable, uses the ICBHI per-breath
    annotation (start, end, crackle, wheeze) — this matches training
    exactly. Otherwise falls back to a sliding window.

    Returns a list of 1-D np.ndarrays.
    """
    segments = []
    if txt_path is not None:
        try:
            ann = pd.read_csv(
                txt_path,
                sep=r"\s+",
                header=None,
                names=["start", "end", "crackle", "wheeze"],
                engine="python",
            )
            for _, row in ann.iterrows():
                s = max(0, int(float(row["start"]) * sr))
                e = min(len(y), int(float(row["end"]) * sr))
                if e - s >= min_segment_samples:
                    segments.append(y[s:e])
        except Exception:
            segments = []
    if segments:
        return segments

    # Fallback: sliding-window over the whole file.
    win = int(window_sec * sr)
    hop = int(hop_sec * sr)
    if len(y) <= win:
        if len(y) >= min_segment_samples:
            return [y]
        return []
    out = []
    for start in range(0, len(y) - win + 1, hop):
        out.append(y[start:start + win])
    # Always include the trailing window so we don't drop the end.
    if out and out[-1] is not y[-win:]:
        out.append(y[-win:])
    return out


def _melspec_tensor(segment, sr=22050):
    """Mel-spec a single segment into the [1,1,128,T] tensor the CNN expects."""
    S = librosa.feature.melspectrogram(y=segment, sr=sr, n_mels=128, fmax=2500)
    S_dB = librosa.power_to_db(S, ref=np.max)
    return torch.tensor(S_dB, dtype=torch.float32).unsqueeze(0).unsqueeze(0)


def predict_audio_segmented(audio_path, model, device, txt_path=None,
                            return_per_segment=False):
    """Run the audio CNN on every breath segment and average softmax probs.

    This is the recommended inference path. It mirrors what the model
    actually saw during training (filtered, per-breath-cycle mel-specs).

    Args:
        audio_path:  path to the .wav file.
        model:       the audio CNN (will be set to eval()).
        device:      torch device.
        txt_path:    optional ICBHI-style annotation. Pass `None` and the
                     function falls back to a sliding window.
        return_per_segment: if True, also return the per-segment probability
                     matrix shaped [n_segments, n_classes].

    Returns:
        np.ndarray of shape (n_classes,) — mean softmax probabilities.
        If `return_per_segment=True`, returns
        (mean_probs, per_segment_probs, n_segments).
    """
    import torch.nn.functional as F  # local import to avoid hard top-level dep cost

    y, sr = librosa.load(audio_path, sr=22050)
    y = butter_bandpass_filter(y, fs=sr)
    segments = _segment_audio(y, sr, txt_path=txt_path)

    if not segments:
        # Empty audio — fall back to whole-file mel-spec so we never crash.
        tensor = _melspec_tensor(y, sr=sr).to(device)
        model.eval()
        with torch.no_grad():
            logits = model(tensor)
            probs = F.softmax(logits, dim=1).cpu().numpy()[0]
        return (probs, probs.reshape(1, -1), 1) if return_per_segment else probs

    per_seg = []
    model.eval()
    with torch.no_grad():
        for seg in segments:
            tensor = _melspec_tensor(seg, sr=sr).to(device)
            logits = model(tensor)
            probs = F.softmax(logits, dim=1).cpu().numpy()[0]
            per_seg.append(probs)

    per_seg_arr = np.vstack(per_seg)
    mean_probs = per_seg_arr.mean(axis=0)
    return (mean_probs, per_seg_arr, len(segments)) if return_per_segment else mean_probs