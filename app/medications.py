"""Saudi pharmacy medication suggestion lookup.

Reads `data/saudi_medications.json` (schema v2) which contains:

* `_meta`             — pharmacies, currency, version, disclaimers (EN+AR),
                        classification legend, evidence levels, sources.
* `diseases.<Name>`   — clinical context (overview, treatment goals, red
                        flags, ICD-10) and a `medications` list. Each
                        medication carries classification, mechanism,
                        dosage, side effects, contraindications, age group,
                        pharmacy availability, indicative SAR price, and
                        source IDs justifying its inclusion.

The loader is tolerant of the older flat schema (v1) so the API does not
break if the data file is rolled back.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

_DATA_PATH = Path(__file__).resolve().parent.parent / "data" / "saudi_medications.json"

_FALLBACK_DISCLAIMER = {
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


def _resolve_sources(source_ids: list[str], all_sources: list[dict]) -> list[dict]:
    """Look up source objects for a list of IDs (preserves order, drops misses)."""
    by_id = {s.get("id"): s for s in all_sources if isinstance(s, dict)}
    out = []
    for sid in source_ids or []:
        if sid in by_id:
            out.append(by_id[sid])
    return out


def get_medications(disease: str) -> dict[str, Any]:
    """Return enriched medication suggestions for a disease label.

    Response shape:
        {
          "disease": "Asthma",
          "disease_ar": "الربو",
          "icd10": "J45",
          "overview_en": "...",
          "overview_ar": "...",
          "treatment_goals_en": [...],
          "treatment_goals_ar": [...],
          "red_flags_en": [...],
          "red_flags_ar": [...],
          "items": [ { ... medication objects with resolved sources[] ... } ],
          "primary_sources": [ {id, name_en, name_ar, type, url}, ... ],
          "classification_legend": { ... },
          "evidence_levels": { ... },
          "currency": "SAR",
          "disclaimer_en": "...",
          "disclaimer_ar": "...",
          "schema_version": "2.0"
        }
    """
    if not isinstance(_DB, dict):
        return _empty(disease)

    meta = _DB.get("_meta", {}) if isinstance(_DB.get("_meta"), dict) else {}
    all_sources = meta.get("sources", []) if isinstance(meta.get("sources"), list) else []

    # ---- v2 schema ----
    diseases = _DB.get("diseases")
    if isinstance(diseases, dict) and disease in diseases:
        d = diseases[disease] or {}
        items = d.get("medications", []) or []
        resolved_items = []
        for m in items:
            if not isinstance(m, dict):
                continue
            mc = dict(m)
            mc["sources_resolved"] = _resolve_sources(mc.get("sources", []), all_sources)
            resolved_items.append(mc)

        return {
            "disease": disease,
            "disease_ar": d.get("name_ar", disease),
            "icd10": d.get("icd10", ""),
            "overview_en": d.get("overview_en", ""),
            "overview_ar": d.get("overview_ar", ""),
            "treatment_goals_en": d.get("treatment_goals_en", []),
            "treatment_goals_ar": d.get("treatment_goals_ar", []),
            "red_flags_en": d.get("red_flags_en", []),
            "red_flags_ar": d.get("red_flags_ar", []),
            "items": resolved_items,
            "primary_sources": _resolve_sources(d.get("primary_sources", []), all_sources),
            "classification_legend": meta.get("classification_legend", {}),
            "evidence_levels": meta.get("evidence_levels", {}),
            "currency": meta.get("currency", "SAR"),
            "pharmacies_ar": meta.get("pharmacies_ar", {}),
            "disclaimer_en": meta.get("disclaimer_en", _FALLBACK_DISCLAIMER["en"]),
            "disclaimer_ar": meta.get("disclaimer_ar", _FALLBACK_DISCLAIMER["ar"]),
            "schema_version": meta.get("version", "2.0"),
        }

    # ---- v1 backward-compat (flat keys) ----
    legacy = _DB.get(disease)
    if isinstance(legacy, list):
        return {
            "disease": disease,
            "disease_ar": disease,
            "items": legacy,
            "primary_sources": [],
            "classification_legend": {},
            "evidence_levels": {},
            "currency": meta.get("currency", "SAR"),
            "disclaimer_en": meta.get("disclaimer_en", _FALLBACK_DISCLAIMER["en"]),
            "disclaimer_ar": meta.get("disclaimer_ar", _FALLBACK_DISCLAIMER["ar"]),
            "schema_version": "1.0",
        }

    return _empty(disease)


def _empty(disease: str) -> dict[str, Any]:
    return {
        "disease": disease,
        "disease_ar": disease,
        "items": [],
        "primary_sources": [],
        "classification_legend": {},
        "evidence_levels": {},
        "currency": "SAR",
        "disclaimer_en": _FALLBACK_DISCLAIMER["en"],
        "disclaimer_ar": _FALLBACK_DISCLAIMER["ar"],
        "schema_version": "n/a",
    }


def get_all_sources() -> list[dict]:
    """Return every registered data source (for an /admin/sources endpoint)."""
    if not isinstance(_DB, dict):
        return []
    meta = _DB.get("_meta", {}) if isinstance(_DB.get("_meta"), dict) else {}
    return meta.get("sources", []) if isinstance(meta.get("sources"), list) else []
