"""
Train the multi-modal fusion meta-classifier.

The three base brains (audio CNN, vitals RF, NLP NB) each emit an
8-class probability distribution per patient. This script stacks them:

  for each patient:
      a = audio_cnn(patient.audio)        # (8,)
      v = vitals_rf(patient.vitals)       # (8,)
      n = nlp_nb(sample(patient.disease)) # (8,) — one per NLP sample
      X[i] = concat(a, v, n)              # 24-dim feature row
      y[i] = patient.disease_id

We data-augment by drawing several NLP templates per patient (the NLP
training set is templated, ~50–120 rows per class), so the meta
classifier sees varied NLP outputs paired with the same audio+vitals.

A LogisticRegression with class_weight='balanced' and L2 regularisation
is fit on the result. We evaluate generalisation with GroupKFold keyed
on patient_id — held-out patients are NEVER in the training fold,
giving an honest read on how the model handles a brand-new patient.

Run:
    python train_meta_fusion.py

Output:
    meta_fusion_weights.pkl   (loaded automatically by app/meta_fusion.py)
"""

from __future__ import annotations

import json
import os
import random
import sys
import time
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report, confusion_matrix, f1_score
from sklearn.model_selection import GroupKFold

ROOT = Path(__file__).resolve().parent
DATA_DIR = ROOT / "data"
AUDIO_DIR = DATA_DIR / "audio_and_txt_files"
OUT_PATH = ROOT / "meta_fusion_weights.pkl"
AUDIO_CACHE = ROOT / ".audio_probs_cache.npz"  # per-patient mean CNN probs;
                                               # auto-rebuilt if the cache
                                               # was made by a different
                                               # CNN checkpoint (mtime check)

DISEASE_MAP = {
    "Healthy": 0, "COPD": 1, "Asthma": 2, "Bronchiectasis": 3,
    "Pneumonia": 4, "URTI": 5, "LRTI": 6, "Bronchiolitis": 7,
}
CLASS_NAMES = [k for k, _ in sorted(DISEASE_MAP.items(), key=lambda kv: kv[1])]

SAMPLES_PER_PATIENT = 12      # how many training rows to emit per patient
NLP_MISMATCH_RATIO = 0.5      # fraction of rows where the NLP feature is
                              # drawn from a random *different* disease
                              # while the patient's TRUE disease stays as
                              # the label.
VITALS_MISMATCH_RATIO = 0.5   # same idea for the vitals feature.
                              #
                              # Why both: in the raw training data the
                              # NLP templates are hand-labelled per
                              # disease and each patient's vitals come
                              # from their actual disease, so without
                              # mismatch the NLP + vitals features
                              # become near-perfect predictors. The
                              # meta-model would then degenerate into
                              # "NLP says X -> answer is X" / "vitals
                              # say Healthy -> answer is Healthy". At
                              # inference the doctor's input can pair
                              # an arbitrary audio file with arbitrary
                              # vitals + symptom notes; mismatched
                              # augmentation teaches the meta-model
                              # that the AUDIO BRAIN carries truth when
                              # the others disagree.
RANDOM_SEED = 42


def _load_base_models():
    """Import and load the three trained base models from disk."""
    sys.path.insert(0, str(ROOT))
    from app import clinical_model as cm
    from app import nlp_model as nm
    from app.model import nafas_model, device
    from app.utils import predict_audio_segmented

    if cm.rf_model is None:
        raise RuntimeError("clinical_weights.pkl missing — train the vitals RF first.")
    if nm.nlp_model is None:
        raise RuntimeError("nlp_weights.pkl missing — train the NLP NB first.")

    return cm.rf_model, nm.nlp_model, nafas_model, device, predict_audio_segmented


def _audio_files_for_patient(patient_id: str) -> list[Path]:
    """Return all WAV files for a patient (the ICBHI set has multiple
    recordings per patient at different chest positions)."""
    return sorted(AUDIO_DIR.glob(f"{patient_id}_*.wav"))


def _patient_audio_probs(patient_id, audio_model, device, predict_fn):
    """Run the audio CNN over every recording for a patient, average
    the per-recording mean-probability vectors. Returns (8,) or None
    if no recordings could be loaded.
    """
    wavs = _audio_files_for_patient(patient_id)
    if not wavs:
        return None
    per_rec = []
    for wav in wavs:
        txt = wav.with_suffix(".txt")
        try:
            probs, _, n_seg = predict_fn(
                str(wav), audio_model, device,
                txt_path=str(txt) if txt.exists() else None,
                return_per_segment=True,
            )
        except Exception:
            continue
        if n_seg > 0:
            per_rec.append(np.asarray(probs, dtype=float))
    if not per_rec:
        return None
    return np.mean(per_rec, axis=0)


def _nlp_pool_by_disease() -> dict[str, list[str]]:
    """{disease_name: list of NLP template strings}"""
    df = pd.read_csv(DATA_DIR / "master_nlp_data.csv")
    pool = defaultdict(list)
    for _, row in df.iterrows():
        d = str(row["mapped_disease"]).strip()
        t = str(row["patient_text"])
        if d in DISEASE_MAP:
            pool[d].append(t)
    return pool


def _load_audio_cache(cnn_weights_mtime: float):
    """Return cached {patient_id: probs(8,)} if valid; else None."""
    if not AUDIO_CACHE.exists():
        return None
    try:
        bundle = np.load(AUDIO_CACHE, allow_pickle=True)
        if float(bundle["cnn_mtime"]) != cnn_weights_mtime:
            return None  # weights changed, cache is stale
        return {str(k): np.asarray(v, dtype=float)
                for k, v in zip(bundle["ids"], bundle["probs"])}
    except Exception:
        return None


def _save_audio_cache(cache: dict, cnn_weights_mtime: float) -> None:
    ids = list(cache.keys())
    probs = np.stack([cache[k] for k in ids], axis=0)
    np.savez(AUDIO_CACHE,
             ids=np.array(ids),
             probs=probs,
             cnn_mtime=np.array(cnn_weights_mtime))


def build_dataset(verbose: bool = True):
    """Return (X, y, groups) for stacking training.

    X has shape (n_rows, 24); y is the patient's disease id; groups is
    the patient_id (used by GroupKFold so a patient is never in both
    train and validation).
    """
    rng = random.Random(RANDOM_SEED)

    rf_model, nlp_model, audio_model, device, predict_fn = _load_base_models()
    cnn_weights_mtime = (ROOT / "nafas_weights.pth").stat().st_mtime
    audio_cache = _load_audio_cache(cnn_weights_mtime) or {}
    cache_hits = len(audio_cache)
    if verbose and audio_cache:
        print(f"  audio cache: {cache_hits} patients pre-computed.")

    # Patient roster
    diag = pd.read_csv(DATA_DIR / "patient_diagnosis.csv",
                       header=None, names=["patient_id", "disease"])
    diag["patient_id"] = diag["patient_id"].astype(str)

    # Vitals lookup: patient_id -> 6-dim feature vector, and a pool of
    # vitals rows grouped by disease (for mismatched-vitals augmentation).
    clin = pd.read_csv(DATA_DIR / "master_clinical_data.csv")
    clin["patient_id"] = clin["patient_id"].astype(str)
    vitals_lookup = {}
    vitals_by_disease: dict[str, list[np.ndarray]] = defaultdict(list)
    for _, row in clin.iterrows():
        try:
            v = np.array([row.age, row.sex, row.bmi, row.spo2,
                          row.temperature, row.smoker], dtype=float)
        except Exception:
            continue
        vitals_lookup[str(row.patient_id)] = v
        d = str(row.disease).strip()
        if d in DISEASE_MAP:
            vitals_by_disease[d].append(v)

    nlp_pool = _nlp_pool_by_disease()

    X_rows, y_rows, groups = [], [], []
    skipped = 0
    started = time.time()

    for pi, prow in enumerate(diag.itertuples(index=False), 1):
        pid = str(prow.patient_id)
        disease = str(prow.disease).strip()
        if disease not in DISEASE_MAP:
            skipped += 1
            continue
        if pid not in vitals_lookup:
            skipped += 1
            continue
        if not nlp_pool.get(disease):
            skipped += 1
            continue

        if verbose and pi % 10 == 0:
            print(f"  [{pi:3d}/{len(diag)}] elapsed={time.time()-started:.0f}s "
                  f"rows={len(X_rows)} skipped={skipped}")

        # Audio (slow — run once per patient, cached to disk). The audio
        # feature is NEVER mismatched — the audio file IS the case under
        # diagnosis, so its probability vector is the ground-truth
        # source the meta-classifier should learn to trust.
        if pid in audio_cache:
            a = audio_cache[pid]
        else:
            a = _patient_audio_probs(pid, audio_model, device, predict_fn)
            if a is None:
                skipped += 1
                continue
            audio_cache[pid] = a

        # Emit SAMPLES_PER_PATIENT rows. Each row independently decides
        # whether to use the patient's true-disease NLP / vitals or
        # to draw from a *random different* disease pool — keeping the
        # patient's true disease as the label. This breaks the
        # degenerate "NLP/vitals -> answer" shortcut and forces the
        # meta-classifier to anchor on the audio signal.
        other_nlp = [d for d in DISEASE_MAP if d != disease and nlp_pool.get(d)]
        other_vit = [d for d in DISEASE_MAP if d != disease and vitals_by_disease.get(d)]

        for _ in range(SAMPLES_PER_PATIENT):
            # Vitals feature
            if rng.random() < VITALS_MISMATCH_RATIO and other_vit:
                v_src = rng.choice(other_vit)
                v_row = rng.choice(vitals_by_disease[v_src])
            else:
                v_row = vitals_lookup[pid]
            v = rf_model.predict_proba(v_row.reshape(1, -1))[0]

            # NLP feature
            if rng.random() < NLP_MISMATCH_RATIO and other_nlp:
                txt = rng.choice(nlp_pool[rng.choice(other_nlp)])
            else:
                txt = rng.choice(nlp_pool[disease])
            n = nlp_model.predict_proba([txt])[0]

            feat = np.concatenate([a, v, n])
            X_rows.append(feat)
            y_rows.append(DISEASE_MAP[disease])
            groups.append(pid)

    if verbose:
        print(f"\n  Built {len(X_rows)} rows from "
              f"{len(set(groups))} patients in {time.time()-started:.0f}s "
              f"(skipped {skipped} patients, "
              f"audio cache hits {cache_hits} -> {len(audio_cache)}).")

    # Persist audio cache so subsequent runs are fast.
    if audio_cache:
        try:
            _save_audio_cache(audio_cache, cnn_weights_mtime)
        except Exception as e:
            if verbose:
                print(f"  (audio cache save skipped: {e})")

    X = np.asarray(X_rows, dtype=float)
    y = np.asarray(y_rows, dtype=int)
    groups = np.asarray(groups)
    return X, y, groups


def cross_validate(X, y, groups, verbose: bool = True) -> dict:
    """GroupKFold CV — held-out patients never appear in the training fold.

    With Asthma (1 patient) and LRTI (2 patients) we can't run high-fold
    CV without one fold lacking a class entirely. We use up to 5 folds
    and accept that some folds will miss rare classes; the reported
    macro-F1 is a conservative lower bound on real-world performance.
    """
    n_groups = len(set(groups))
    n_splits = min(5, n_groups)
    if n_splits < 2:
        return {"cv_macro_f1": None, "note": "not enough patients for CV"}

    kf = GroupKFold(n_splits=n_splits)
    fold_scores = []
    for fold, (tr, va) in enumerate(kf.split(X, y, groups), 1):
        if len(set(y[tr])) < 2 or len(set(y[va])) < 1:
            continue
        m = LogisticRegression(
            class_weight="balanced",
            C=1.0,
            max_iter=2000,
            solver="lbfgs",
        )
        m.fit(X[tr], y[tr])
        pred = m.predict(X[va])
        f = f1_score(y[va], pred, average="macro", zero_division=0)
        fold_scores.append(f)
        if verbose:
            unique_va = sorted(set(y[va]))
            print(f"    fold {fold}/{n_splits}: macro-F1={f:.3f} "
                  f"(val patients={len(set(groups[va]))}, "
                  f"val classes={[CLASS_NAMES[c] for c in unique_va]})")
    if not fold_scores:
        return {"cv_macro_f1": None, "note": "no usable CV folds"}
    return {
        "cv_macro_f1": float(np.mean(fold_scores)),
        "cv_macro_f1_std": float(np.std(fold_scores)),
        "n_folds": len(fold_scores),
    }


def train_and_save(X, y, groups, cv: dict) -> dict:
    """Fit the final meta-classifier on ALL the data and persist it."""
    model = LogisticRegression(
        class_weight="balanced",
        C=1.0,
        max_iter=2000,
        solver="lbfgs",
    )
    model.fit(X, y)

    # In-sample sanity: should be high; not a generalisation measure.
    train_pred = model.predict(X)
    train_f1 = f1_score(y, train_pred, average="macro", zero_division=0)

    bundle = {
        "model": model,
        "meta": {
            "estimator": "LogisticRegression(class_weight='balanced', C=1.0)",
            "n_features": int(X.shape[1]),
            "n_train_rows": int(X.shape[0]),
            "n_patients": int(len(set(groups))),
            "class_counts": dict(Counter(int(c) for c in y)),
            "train_macro_f1": float(train_f1),
            "cv_macro_f1": cv.get("cv_macro_f1"),
            "cv_macro_f1_std": cv.get("cv_macro_f1_std"),
            "cv_n_folds": cv.get("n_folds"),
            "trained_at": datetime.now(timezone.utc).isoformat(),
            "feature_layout": ["audio_probs(8)", "vitals_probs(8)", "nlp_probs(8)"],
            "class_names": CLASS_NAMES,
        },
    }
    joblib.dump(bundle, OUT_PATH)
    return bundle["meta"]


def main():
    print("=" * 70)
    print("Training meta-fusion classifier (stacking over audio + vitals + NLP)")
    print("=" * 70)
    print(f"data dir : {DATA_DIR}")
    print(f"audio dir: {AUDIO_DIR}")
    print(f"out path : {OUT_PATH}")
    print()

    print(">>> Building stacking dataset...")
    X, y, groups = build_dataset(verbose=True)
    print(f"\n    X shape: {X.shape}")
    print(f"    y shape: {y.shape}")
    cnt = Counter(int(c) for c in y)
    print(f"    per-class row counts:")
    for cls_id in range(8):
        nm = CLASS_NAMES[cls_id]
        print(f"      {nm:16s}: {cnt.get(cls_id, 0):4d}")

    print("\n>>> GroupKFold cross-validation (patients held out)...")
    cv = cross_validate(X, y, groups, verbose=True)
    print(f"\n    CV macro-F1: {cv.get('cv_macro_f1')}")
    if "cv_macro_f1_std" in cv:
        print(f"    CV macro-F1 std: {cv['cv_macro_f1_std']:.3f}")

    print("\n>>> Fitting final model on all patients...")
    info = train_and_save(X, y, groups, cv)
    print(f"\n    saved -> {OUT_PATH}")
    print(f"    train macro-F1: {info['train_macro_f1']:.3f}")
    print(f"    CV    macro-F1: {info['cv_macro_f1']}")

    # Pretty-print the metadata so the user can audit the run.
    print("\n=== meta ===")
    print(json.dumps(info, indent=2, default=str))


if __name__ == "__main__":
    main()
