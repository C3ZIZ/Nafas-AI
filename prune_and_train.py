"""Prune and full-retrain script.

Use this when you want to wipe every saved model weight file and retrain
all three brains on the **full** dataset (no sample cap):

    python prune_and_train.py            # interactive confirmation
    python prune_and_train.py --yes      # non-interactive
    python prune_and_train.py --keep clinical nlp   # only delete audio weights

Trained components:
    * clinical Random Forest  (full master_clinical_data.csv)
    * NLP TF-IDF + Naive Bayes (full master_nlp_data.csv)
    * Audio CNN               (every breath segment found under data/)

Existing weight files are removed BEFORE training; if training of any
component fails, the others still proceed and the script reports a summary
at the end.
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
WEIGHTS = {
    "audio": ROOT / "nafas_weights.pth",
    "clinical": ROOT / "clinical_weights.pkl",
    "nlp": ROOT / "nlp_weights.pkl",
}

# Treat ~unbounded as the "use everything" cap for the audio dataset.
FULL_AUDIO_CAP = 10**9


def _confirm(prompt: str) -> bool:
    try:
        return input(prompt).strip().lower() in {"y", "yes"}
    except EOFError:
        return False


def prune(keep: list[str]) -> dict[str, str]:
    status: dict[str, str] = {}
    for name, path in WEIGHTS.items():
        if name in keep:
            status[name] = f"kept ({path.name})"
            continue
        if path.exists():
            try:
                path.unlink()
                status[name] = f"deleted ({path.name})"
            except Exception as e:
                status[name] = f"delete failed: {e}"
        else:
            status[name] = f"not present ({path.name})"
    return status


def train_clinical_full() -> str:
    try:
        # Train script lives in app/clinical_model.py and reads
        # data/master_clinical_data.csv via a relative path, so cd to ROOT.
        cwd = os.getcwd()
        os.chdir(ROOT)
        try:
            from app.clinical_model import train_and_save_rf
            train_and_save_rf()
        finally:
            os.chdir(cwd)
        return "clinical: trained on full dataset"
    except Exception as e:
        return f"clinical: FAILED ({e})"


def train_nlp_full() -> str:
    try:
        cwd = os.getcwd()
        os.chdir(ROOT)
        try:
            from app.nlp_model import train_nlp
            train_nlp()
        finally:
            os.chdir(cwd)
        return "nlp: trained on full dataset"
    except Exception as e:
        return f"nlp: FAILED ({e})"


def train_audio_full(epochs: int = 5) -> str:
    try:
        import torch
        import torch.nn as nn
        import torch.optim as optim
        from torch.utils.data import DataLoader

        from app.dataset import NafasDiseaseDataset
        from app.model import device, nafas_model

        print(f"[audio] Building dataset (no sample cap)…")
        dataset = NafasDiseaseDataset(data_dir=str(ROOT / "data"), max_samples=FULL_AUDIO_CAP)
        n = len(dataset)
        if n == 0:
            return "audio: skipped (no breath segments found)"
        print(f"[audio] Loaded {n} breath segments. Training {epochs} epochs on {device}.")

        loader = DataLoader(dataset, batch_size=1, shuffle=True)
        criterion = nn.CrossEntropyLoss()
        optimizer = optim.Adam(nafas_model.parameters(), lr=0.001)

        nafas_model.train()
        for epoch in range(epochs):
            running = 0.0
            correct = 0
            for x, y in loader:
                x, y = x.to(device), y.to(device)
                optimizer.zero_grad()
                out = nafas_model(x)
                loss = criterion(out, y)
                loss.backward()
                optimizer.step()
                running += loss.item()
                correct += (torch.argmax(out, 1) == y).sum().item()
            avg = running / max(1, len(loader))
            acc = (correct / max(1, len(loader))) * 100
            print(f"[audio] epoch {epoch+1}/{epochs} loss={avg:.4f} acc={acc:.2f}%")

        torch.save(nafas_model.state_dict(), str(WEIGHTS["audio"]))
        return f"audio: trained on full dataset (n={n}, epochs={epochs})"
    except Exception as e:
        return f"audio: FAILED ({e})"


def main() -> int:
    parser = argparse.ArgumentParser(description="Prune model weights and full-retrain.")
    parser.add_argument("--yes", "-y", action="store_true", help="Skip confirmation prompt.")
    parser.add_argument(
        "--keep",
        nargs="*",
        choices=list(WEIGHTS.keys()),
        default=[],
        help="Names of weight files to keep (others are deleted).",
    )
    parser.add_argument(
        "--only",
        nargs="*",
        choices=list(WEIGHTS.keys()),
        default=[],
        help="If set, only retrain these components (still deletes their weights first).",
    )
    parser.add_argument("--audio-epochs", type=int, default=5, help="Epochs for the audio CNN.")
    args = parser.parse_args()

    targets = args.only or list(WEIGHTS.keys())

    print("=" * 60)
    print("Prune & full retrain")
    print(f"  ROOT         : {ROOT}")
    print(f"  Will delete  : {[k for k in WEIGHTS if k not in args.keep]}")
    print(f"  Will retrain : {targets}")
    print(f"  Audio epochs : {args.audio_epochs}")
    print("=" * 60)

    if not args.yes and not _confirm("Proceed? This deletes existing weights. [y/N] "):
        print("Aborted.")
        return 1

    print("\n[1/2] Pruning weight files…")
    for name, msg in prune(args.keep).items():
        print(f"  {name:<8} {msg}")

    print("\n[2/2] Training…")
    summary: dict[str, str] = {}
    if "clinical" in targets:
        summary["clinical"] = train_clinical_full()
        print(f"  {summary['clinical']}")
    if "nlp" in targets:
        summary["nlp"] = train_nlp_full()
        print(f"  {summary['nlp']}")
    if "audio" in targets:
        summary["audio"] = train_audio_full(epochs=args.audio_epochs)
        print(f"  {summary['audio']}")

    print("\nDone.")
    print("Summary:")
    for k, v in summary.items():
        print(f"  - {k}: {v}")

    failed = [k for k, v in summary.items() if "FAILED" in v]
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
