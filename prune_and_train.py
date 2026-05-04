"""Prune and full-retrain script.

Wipes every saved model artifact and retrains all four components on the
**full** dataset (no sample cap):

    python prune_and_train.py            # interactive confirmation
    python prune_and_train.py --yes      # non-interactive
    python prune_and_train.py --keep clinical nlp   # only delete audio + advisor

Trained components:
    * clinical  — Random Forest         (full master_clinical_data.csv)
    * nlp       — TF-IDF + Naive Bayes  (full master_nlp_data.csv)
    * audio     — Audio CNN             (every breath segment found under data/)
    * advisor   — Medication-advisor    (TF-IDF over saudi_medications.json,
                                          plus a schema validation pass on the
                                          curated dataset itself)

Existing weight files are removed BEFORE training. If training of any
component fails, the others still proceed and the script reports a summary
at the end. Exit code is non-zero iff any component failed OR the
medication dataset failed schema validation.
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
WEIGHTS = {
    "audio":    ROOT / "nafas_weights.pth",
    "clinical": ROOT / "clinical_weights.pkl",
    "nlp":      ROOT / "nlp_weights.pkl",
    "advisor":  ROOT / "advisor_weights.pkl",
}

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


def validate_medication_dataset() -> tuple[str, int]:
    """Run scripts/validate_medications.py to schema-check the medication dataset.

    Returns (message, exit_code). Non-zero exit code if any schema error was found.
    """
    script = ROOT / "scripts" / "validate_medications.py"
    if not script.exists():
        return ("medication-dataset: validator not found (scripts/validate_medications.py missing)", 0)
    try:
        env = {**os.environ, "PYTHONIOENCODING": "utf-8"}
        proc = subprocess.run(
            [sys.executable, str(script)],
            cwd=str(ROOT),
            capture_output=True,
            text=True,
            encoding="utf-8",
            env=env,
        )
        # Print the summary line so the user sees medication count etc.
        last = (proc.stdout or "").strip().splitlines()[-1:] or [""]
        msg = f"medication-dataset: {last[0]}" if proc.returncode == 0 \
              else f"medication-dataset: SCHEMA ERRORS (rc={proc.returncode})"
        if proc.returncode != 0 and proc.stdout:
            msg += "\n" + proc.stdout.strip()
        return (msg, proc.returncode)
    except Exception as e:
        return (f"medication-dataset: validator failed to run ({e})", 1)


def train_advisor_full() -> str:
    """Build and persist the Medication Advisor TF-IDF index."""
    try:
        cwd = os.getcwd()
        os.chdir(ROOT)
        try:
            from app.medication_advisor import get_advisor
            info = get_advisor().fit_and_save()
        finally:
            os.chdir(cwd)
        return (
            f"advisor: trained "
            f"(terms={info['n_terms']}, descriptors={info['n_descriptors']}, "
            f"file={Path(info['saved_to']).name})"
        )
    except Exception as e:
        return f"advisor: FAILED ({e})"


def train_audio_full(epochs: int = 5) -> str:
    try:
        import torch
        import torch.nn as nn
        import torch.optim as optim
        from torch.utils.data import DataLoader

        from app.dataset import NafasDiseaseDataset
        from app.model import device, nafas_model

        print(f"[audio] Building dataset (no sample cap)…")
        dataset = NafasDiseaseDataset(data_dir=str(ROOT / "data"), max_samples=None)
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

    # If --only is set, narrow the prune scope to those components too — so
    # `--only advisor` doesn't blow away clinical/nlp/audio weights.
    if args.only:
        keep = list({k for k in WEIGHTS if k not in args.only} | set(args.keep))
    else:
        keep = list(args.keep)

    print("=" * 60)
    print("Prune & full retrain")
    print(f"  ROOT         : {ROOT}")
    print(f"  Will delete  : {[k for k in WEIGHTS if k not in keep]}")
    print(f"  Will retrain : {targets}")
    print(f"  Audio epochs : {args.audio_epochs}")
    print("=" * 60)

    if not args.yes and not _confirm("Proceed? This deletes existing weights. [y/N] "):
        print("Aborted.")
        return 1

    print("\n[1/3] Pruning weight files…")
    for name, msg in prune(keep).items():
        print(f"  {name:<8} {msg}")

    print("\n[2/3] Training…")
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
    if "advisor" in targets:
        summary["advisor"] = train_advisor_full()
        print(f"  {summary['advisor']}")

    print("\n[3/3] Validating medication dataset…")
    msg, val_rc = validate_medication_dataset()
    summary["medication_dataset"] = msg
    print(f"  {msg}")

    print("\nDone.")
    print("Summary:")
    for k, v in summary.items():
        print(f"  - {k}: {v}")

    failed = [k for k, v in summary.items() if "FAILED" in v]
    return 1 if failed or val_rc != 0 else 0


if __name__ == "__main__":
    sys.exit(main())
