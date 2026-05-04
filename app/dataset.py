"""
Disease-aware dataset for Nafas diagnostic training.

This dataset reads `patient_diagnosis.csv` to obtain the true disease
label for each patient, then pairs annotation slices (from the
`.txt` files) with the patient's disease label. It searches
recursively under `data_dir` for annotation files so the
`data/audio_and_txt_files` layout is supported.
"""

import os
import glob
import pandas as pd
import librosa
import numpy as np
import torch
from torch.utils.data import Dataset
from .utils import butter_bandpass_filter


# The 8 possible conditions in the Kaggle Dataset
DISEASE_MAP = {
    "Healthy": 0,
    "COPD": 1,
    "Asthma": 2,
    "Bronchiectasis": 3,
    "Pneumonia": 4,
    "URTI": 5,
    "LRTI": 6,
    "Bronchiolitis": 7,
}


class NafasDiseaseDataset(Dataset):
    def __init__(self, data_dir="data", max_samples=100):
        """Build the breath-segment dataset.

        Args:
            data_dir:    folder containing `patient_diagnosis.csv` and the
                         annotation/.wav files (recursively scanned).
            max_samples: cap on number of (segment, label) pairs to load.
                         Pass `None` (or any value <= 0) to load every
                         segment found — used for full-dataset training.
        """
        self.samples = []
        self.sr = 22050
        # Treat None / non-positive caps as "no limit".
        self._unlimited = max_samples is None or max_samples <= 0

        # Load the patient diagnoses
        csv_path = os.path.join(data_dir, "patient_diagnosis.csv")
        if not os.path.exists(csv_path):
            raise FileNotFoundError("Please download patient_diagnosis.csv from Kaggle and put it in the data folder.")

        diagnoses_df = pd.read_csv(csv_path, header=None, names=["patient_id", "disease"])
        # Convert patient_id to string for easy matching
        diagnoses_df["patient_id"] = diagnoses_df["patient_id"].astype(str)

        # Find annotation files recursively (supports data/audio_and_txt_files/)
        txt_pattern = os.path.join(data_dir, "**", "*.txt")
        txt_files = glob.glob(txt_pattern, recursive=True)

        for txt_path in txt_files:
            if not self._unlimited and len(self.samples) >= max_samples:
                break

            filename = os.path.basename(txt_path)
            patient_id = filename.split("_")[0]

            # Find the patient's disease in the CSV
            disease_row = diagnoses_df[diagnoses_df["patient_id"] == patient_id]
            if disease_row.empty:
                # If diagnosis not found, skip
                continue

            disease_name = disease_row.iloc[0]["disease"]
            if disease_name not in DISEASE_MAP:
                # Unknown disease label, skip
                continue

            label = DISEASE_MAP[disease_name]

            audio_path = os.path.splitext(txt_path)[0] + ".wav"
            if not os.path.exists(audio_path):
                # Try alternate common locations (audio may be elsewhere); skip if missing
                continue

            try:
                y, _ = librosa.load(audio_path, sr=self.sr)
            except Exception:
                continue

            y_clean = butter_bandpass_filter(y, fs=self.sr)

            # Parse annotations (whitespace or tab separated)
            try:
                annotations = pd.read_csv(txt_path, sep=r"\s+", header=None, names=["start", "end", "crackle", "wheeze"], engine="python")
            except Exception:
                continue

            for _, row in annotations.iterrows():
                if not self._unlimited and len(self.samples) >= max_samples:
                    break

                start_idx = int(float(row["start"]) * self.sr)
                end_idx = int(float(row["end"]) * self.sr)
                start_idx = max(0, start_idx)
                end_idx = min(end_idx, len(y_clean))
                if end_idx <= start_idx:
                    continue

                audio_segment = y_clean[start_idx:end_idx]
                self.samples.append((audio_segment, label))

    def __len__(self):
        return len(self.samples)

    def __getitem__(self, idx):
        audio_segment, label = self.samples[idx]
        S = librosa.feature.melspectrogram(y=audio_segment, sr=self.sr, n_mels=128, fmax=2500)
        S_dB = librosa.power_to_db(S, ref=np.max)

        tensor = torch.tensor(S_dB, dtype=torch.float32).unsqueeze(0)
        label_tensor = torch.tensor(label, dtype=torch.long)
        return tensor, label_tensor
