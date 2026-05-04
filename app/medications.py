"""Saudi pharmacy medication suggestion lookup.

Loads `data/saudi_medications.json` once and exposes a small helper used by
the diagnosis API to attach pharmacist-level suggestions to each result.

The dataset is curated for educational use — it is NOT a prescription.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

_DATA_PATH = Path(__file__).resolve().parent.parent / "data" / "saudi_medications.json"

_DEFAULT_DISCLAIMER = {
    "en": "Educational reference only. Confirm with a licensed pharmacist or physician.",
    "ar": "للأغراض التعليمية فقط. يجب تأكيد الوصفة من قبل صيدلي أو طبيب مرخّص.",
}


def _load() -> dict[str, Any]:
    if not _DATA_PATH.exists():
        return {}
    try:
        with open(_DATA_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


_DB: dict[str, Any] = _load()


def get_medications(disease: str) -> dict[str, Any]:
    """Return medication suggestions for a disease label.

    Shape:
        {
            "disease": "Asthma",
            "items": [ { brand, brand_ar, generic, category, purpose_en, purpose_ar,
                         rx_required, indicative_price_sar, pharmacies[] }, ... ],
            "disclaimer_en": "...",
            "disclaimer_ar": "..."
        }
    """
    items = _DB.get(disease, []) if isinstance(_DB, dict) else []
    meta = _DB.get("_meta", {}) if isinstance(_DB, dict) else {}
    return {
        "disease": disease,
        "items": items if isinstance(items, list) else [],
        "disclaimer_en": meta.get("disclaimer_en", _DEFAULT_DISCLAIMER["en"]),
        "disclaimer_ar": meta.get("disclaimer_ar", _DEFAULT_DISCLAIMER["ar"]),
        "currency": meta.get("currency", "SAR"),
    }
