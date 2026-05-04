"""Robust startup auto-training.

On API startup we check the three weight files and train the missing ones:

* `clinical_weights.pkl` — fast (Random Forest on tabular CSV).
* `nlp_weights.pkl`      — fast (TF-IDF + Naive Bayes, full dataset).
* `nafas_weights.pth`    — slowest (audio CNN). We train on **half** of the
  available breath segments so the API can come up in a reasonable time even
  on a fresh checkout.

Each step is wrapped in try/except so a failure in one model never blocks the
others or the server from starting.
"""

from __future__ import annotations

import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
NAFAS_W = ROOT / "nafas_weights.pth"
NLP_W = ROOT / "nlp_weights.pkl"
CLINICAL_W = ROOT / "clinical_weights.pkl"
ADVISOR_W = ROOT / "advisor_weights.pkl"


def _train_clinical_if_missing() -> str:
    if CLINICAL_W.exists():
        return "clinical: already trained"
    try:
        from .clinical_model import reload_rf_model, train_and_save_rf
        cwd = os.getcwd()
        os.chdir(ROOT)
        try:
            train_and_save_rf()
        finally:
            os.chdir(cwd)
        reload_rf_model()
        return "clinical: trained"
    except Exception as e:
        return f"clinical: skipped ({e})"


def _train_nlp_if_missing() -> str:
    if NLP_W.exists():
        return "nlp: already trained"
    try:
        from .nlp_model import reload_nlp_model, train_nlp
        cwd = os.getcwd()
        os.chdir(ROOT)
        try:
            train_nlp()
        finally:
            os.chdir(cwd)
        reload_nlp_model()
        return "nlp: trained (full dataset)"
    except Exception as e:
        return f"nlp: skipped ({e})"


def _train_audio_if_missing() -> str:
    if NAFAS_W.exists():
        return "audio: already trained"
    try:
        import glob

        import torch
        import torch.nn as nn
        import torch.optim as optim
        from torch.utils.data import DataLoader

        from .dataset import NafasDiseaseDataset
        from .model import device, nafas_model, reload_weights

        # Half-of-dataset cap: count txt annotations and use ~50%.
        txt_files = glob.glob(str(DATA_DIR / "**" / "*.txt"), recursive=True)
        # Each txt file produces multiple breath segments; cap at half of the
        # available txt files but never more than 400 segments to stay quick.
        cap = max(50, min(400, len(txt_files) // 2))

        dataset = NafasDiseaseDataset(data_dir=str(DATA_DIR), max_samples=cap)
        if len(dataset) == 0:
            return "audio: skipped (no usable breath segments)"

        loader = DataLoader(dataset, batch_size=1, shuffle=True)
        criterion = nn.CrossEntropyLoss()
        optimizer = optim.Adam(nafas_model.parameters(), lr=0.001)

        nafas_model.train()
        epochs = 3
        for epoch in range(epochs):
            running = 0.0
            for x, y in loader:
                x, y = x.to(device), y.to(device)
                optimizer.zero_grad()
                out = nafas_model(x)
                loss = criterion(out, y)
                loss.backward()
                optimizer.step()
                running += loss.item()
            print(f"[auto-train][audio] epoch {epoch+1}/{epochs} loss={running/max(1,len(loader)):.4f}")

        torch.save(nafas_model.state_dict(), str(NAFAS_W))
        reload_weights()
        return f"audio: trained (samples={len(dataset)}, epochs={epochs})"
    except Exception as e:
        return f"audio: skipped ({e})"


def _build_advisor_if_missing() -> str:
    if ADVISOR_W.exists():
        return "advisor: already built"
    try:
        from .medication_advisor import get_advisor
        info = get_advisor().fit_and_save()
        return (
            f"advisor: built (terms={info['n_terms']}, descriptors={info['n_descriptors']})"
        )
    except Exception as e:
        return f"advisor: skipped ({e})"


def ensure_models_trained() -> dict[str, str]:
    """Train any missing model. Safe to call repeatedly — it no-ops once weights exist.

    Four components are managed:
        clinical Random Forest, NLP TF-IDF/NB, Audio CNN, and the
        Medication Advisor TF-IDF index.

    Returns a dict of per-model status strings for logging.
    """
    status = {
        "clinical": _train_clinical_if_missing(),
        "nlp": _train_nlp_if_missing(),
        "audio": _train_audio_if_missing(),
        "advisor": _build_advisor_if_missing(),
    }
    for k, v in status.items():
        print(f"[auto-train] {v}")
    return status
