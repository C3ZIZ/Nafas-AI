"""Dataset helper for Nafas breath segments.

This module provides `NafasDataset`, a small PyTorch `Dataset` that:
- searches for annotation `.txt` files (recursively under `data_dir`),
- finds the matching audio file (tries common extensions),
- slices the audio according to annotation start/end times,
- applies a band-pass filter, and
- returns on-the-fly Mel-spectrogram tensors ready for a CNN.

Notes:
- `self.sr` is the target sampling rate (in Hz). 22050 = 22.05 kHz (Librosa's common default).
  It balances audio quality and speed for spectrogram extraction; change it if you need
  higher/lower resolution (e.g., 16000 Hz for telephony or 44100 Hz for full fidelity).
"""

import os
import glob
import pandas as pd
import librosa
import numpy as np
import torch
from torch.utils.data import Dataset
from .utils import butter_bandpass_filter


class NafasDataset(Dataset):
    """PyTorch Dataset for breath-segment classification.

    Args:
        data_dir (str): Root folder to search for annotations/audio (recursive).
        max_samples (int): Maximum number of segments to load (useful for quick tests).
    """

    def __init__(self, data_dir="data", max_samples=250):
        self.samples = []

        # Sampling rate (Hz) used for loading and spectrogram creation.
        # 22050 (22.05 kHz) is a common librosa default and a good trade-off
        # between frequency resolution and CPU/memory usage for short breath sounds.
        self.sr = 22050

        # Look for annotation files recursively so callers can pass `data` or
        # `data/audio_and_txt_files` interchangeably.
        pattern = os.path.join(data_dir, "**", "*.txt")
        txt_files = glob.glob(pattern, recursive=True)

        if len(txt_files) == 0:
            print(f"Warning: no .txt annotation files found under {data_dir}")

        # Try a few common audio file extensions next to each annotation file.
        audio_exts = [".wav", ".WAV", ".flac", ".FLAC", ".mp3", ".MP3"]

        for txt_path in txt_files:
            if len(self.samples) >= max_samples:
                break

            # match audio file by base name (annotation: foo.txt -> audio: foo.wav)
            base = os.path.splitext(txt_path)[0]
            audio_path = None
            for ext in audio_exts:
                candidate = base + ext
                if os.path.exists(candidate):
                    audio_path = candidate
                    break

            if audio_path is None:
                # No corresponding audio file found for this annotation -> skip
                continue

            # Load the audio at the target sample rate and apply band-pass filtering.
            try:
                y, _ = librosa.load(audio_path, sr=self.sr)
            except Exception:
                # If a file fails to load for any reason, skip it rather than crashing.
                continue
            y_clean = butter_bandpass_filter(y, fs=self.sr)

            # Parse annotation file. The ICBHI-like files are whitespace/tab delimited
            # and contain rows: <start_sec> <end_sec> <crackle> <wheeze>
            try:
                annotations = pd.read_csv(
                    txt_path,
                    sep=r"\s+",
                    header=None,
                    names=["start", "end", "crackle", "wheeze"],
                    engine="python",
                )
            except Exception:
                # Skip malformed annotation files
                continue

            for _, row in annotations.iterrows():
                if len(self.samples) >= max_samples:
                    break

                # Convert times (seconds) -> sample indices and clip to the audio length.
                try:
                    start_sec = float(row["start"])
                    end_sec = float(row["end"])
                except Exception:
                    # Skip rows with invalid numeric fields
                    continue

                start_idx = max(0, int(start_sec * self.sr))
                end_idx = min(int(end_sec * self.sr), len(y_clean))
                if end_idx <= start_idx:
                    # Skip zero-length or inverted intervals
                    continue

                audio_segment = y_clean[start_idx:end_idx]

                # Map labels to integers: 0=Normal, 1=Wheeze, 2=Crackle.
                # If both present we prioritize wheeze over crackle for this simple test.
                try:
                    wheeze = int(row.get("wheeze", 0))
                except Exception:
                    wheeze = 0
                try:
                    crackle = int(row.get("crackle", 0))
                except Exception:
                    crackle = 0

                label = 0
                if wheeze == 1:
                    label = 1
                elif crackle == 1:
                    label = 2

                # Store the raw audio slice and label; spectrograms are created on-the-fly
                # in __getitem__ to avoid storing large arrays in memory.
                self.samples.append((audio_segment, label))

        print(f"Dataset loaded with {len(self.samples)} breath segments from {data_dir}.")

    def __len__(self):
        return len(self.samples)

    def __getitem__(self, idx):
        """Return a single sample as (`tensor`, `label_tensor`).

        - `tensor` shape: [1, 128, time_frames] (channel-first for PyTorch Conv2d)
        - `label_tensor` dtype: `torch.long` (for `CrossEntropyLoss`)
        """
        audio_segment, label = self.samples[idx]

        # If the slice was empty for any reason, replace with short silence.
        if audio_segment is None or len(audio_segment) == 0:
            audio_segment = np.zeros(int(self.sr * 0.1))  # 0.1s silence

        # Create Mel-spectrogram (power) and convert to dB scale (log) to match
        # common audio-ML preprocessing (improves dynamic range for faint sounds).
        S = librosa.feature.melspectrogram(y=audio_segment, sr=self.sr, n_mels=128, fmax=2500)
        S_dB = librosa.power_to_db(S, ref=np.max)

        # Add channel dimension -> [1, 128, Time]
        tensor = torch.tensor(S_dB, dtype=torch.float32).unsqueeze(0)
        label_tensor = torch.tensor(label, dtype=torch.long)

        return tensor, label_tensor
