"""
Learned multi-modal fusion (stacking meta-classifier).

The audio CNN, vitals RF and NLP NB each output an 8-class probability
distribution. Rather than combining them with hand-tuned weights, we
treat their concatenated outputs as a 24-dim feature vector and train
a logistic-regression classifier on top: classical stacking.

The meta-classifier learns from data:

  - Per-class bias corrections (e.g. the vitals RF over-predicts
    Healthy because normal vitals dominate its training distribution).
  - Per-brain reliability per class (the audio CNN is the dominant
    signal for breath-sound disease; the NLP brain helps disambiguate
    upper/lower respiratory entities; vitals refines the prior).
  - Cross-brain interactions (audio + nlp jointly indicating disease
    overrides a "Healthy"-favouring vitals row).

This module owns load / save / predict. Training lives in the
companion `train_meta_fusion.py` script at the project root so the
training data plumbing (file IO, audio segment loading) does not leak
into the request path.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Optional

import joblib
import numpy as np


# 24 = audio (8) + vitals (8) + nlp (8) — order matters and is mirrored
# in train_meta_fusion.py.
EXPECTED_N_FEATURES = 24

_WEIGHTS_PATH = Path(__file__).resolve().parent.parent / "meta_fusion_weights.pkl"

# Loaded at import time; reload_meta_fusion() refreshes it.
_meta_model = None
_meta_meta: Optional[dict] = None


def _load() -> None:
    """Read the pickled meta-classifier into module state."""
    global _meta_model, _meta_meta
    if not _WEIGHTS_PATH.exists():
        _meta_model = None
        _meta_meta = None
        return
    try:
        bundle = joblib.load(_WEIGHTS_PATH)
        _meta_model = bundle["model"]
        _meta_meta = bundle.get("meta", {})
    except Exception as e:
        _meta_model = None
        _meta_meta = {"load_error": str(e)}


_load()


def reload_meta_fusion() -> bool:
    """Re-read the weights file after a training run. Returns True on success."""
    _load()
    return _meta_model is not None


def is_available() -> bool:
    """True if a trained meta-classifier is loaded and ready to use."""
    return _meta_model is not None


def info() -> dict:
    """Status snapshot for /llm_status-style diagnostics."""
    return {
        "available": is_available(),
        "weights_path": str(_WEIGHTS_PATH),
        "meta": _meta_meta or {},
    }


class MetaFusionUnavailableError(RuntimeError):
    """Raised when fuse() is called but no trained meta-classifier exists."""


def _stack_features(audio_probs, vitals_probs, nlp_probs) -> np.ndarray:
    """Concatenate the three brains' probability vectors into a (1, 24) row.

    Each input is normalised to sum to 1 (so an upstream brain that
    returns logits or unnormalised scores still yields a usable feature
    row).
    """
    def norm(v):
        v = np.asarray(v, dtype=float).ravel()
        s = v.sum()
        return v / s if s > 0 else np.full_like(v, 1.0 / max(1, v.size))
    feats = np.concatenate([norm(audio_probs), norm(vitals_probs), norm(nlp_probs)])
    if feats.size != EXPECTED_N_FEATURES:
        raise ValueError(
            f"meta-fusion expected {EXPECTED_N_FEATURES} features, "
            f"got {feats.size}"
        )
    return feats.reshape(1, -1)


def fuse(audio_probs, vitals_probs, nlp_probs) -> tuple[np.ndarray, dict]:
    """Return the fused 8-class probability vector + a small info dict.

    Raises MetaFusionUnavailableError if the meta-classifier has not
    been trained yet. The caller (FastAPI route) should map that to a
    503 with a clear "run training" message — the system must NOT
    silently fall back to a hard-coded heuristic.
    """
    if _meta_model is None:
        raise MetaFusionUnavailableError(
            "Meta-fusion classifier has not been trained. Run "
            "`python train_meta_fusion.py` (or restart the API to "
            "auto-train) to produce meta_fusion_weights.pkl."
        )
    feats = _stack_features(audio_probs, vitals_probs, nlp_probs)
    probs = _meta_model.predict_proba(feats)[0]

    # The meta-classifier's `classes_` attribute is the canonical
    # column order. We pad with zeros if any class was absent from
    # training (e.g. only 1 Asthma patient meant LogReg might have
    # been trained on 7 classes if folds were drawn unluckily — but
    # train_meta_fusion.py enforces full 8-class coverage, so this
    # branch should never fire in practice).
    n_classes = 8
    if probs.size == n_classes:
        out = probs
    else:
        out = np.zeros(n_classes, dtype=float)
        for c_idx, cls in enumerate(_meta_model.classes_):
            out[int(cls)] = probs[c_idx]
        s = out.sum()
        out = out / s if s > 0 else np.full(n_classes, 1.0 / n_classes)

    return out, {
        "meta_classifier": (_meta_meta or {}).get("estimator", "LogisticRegression"),
        "trained_at": (_meta_meta or {}).get("trained_at"),
        "cv_macro_f1": (_meta_meta or {}).get("cv_macro_f1"),
    }
