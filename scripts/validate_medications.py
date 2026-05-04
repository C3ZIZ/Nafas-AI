"""Validate the Saudi pharmacy medication dataset.

What this script does:

1. Loads `data/saudi_medications.json`.
2. Schema-checks every disease and medication entry (required fields,
   pharmacy IDs that aren't in the registered list, dangling source IDs,
   classification keys not present in the legend).
3. For each pharmacy it knows about, builds a search URL using the
   `_meta.validation.search_url_templates` map, so a human can re-verify
   any medication by clicking the printed link.
4. Optional `--ping` mode performs a HEAD request against every pharmacy
   homepage and the live spot-check URLs from `_meta.validation` so you
   can confirm the catalogue endpoints are still reachable. Requires
   `requests` (standard in the project venv).

Usage
-----
    # Schema + reference integrity report
    python scripts/validate_medications.py

    # Same plus live HEAD pings (catalogue homepages + spot-check URLs)
    python scripts/validate_medications.py --ping

    # Print verify-this-medication URLs for a single disease
    python scripts/validate_medications.py --disease Asthma --links

    # Emit a CSV your pharmacy team can re-confirm row-by-row
    python scripts/validate_medications.py --csv out/validation.csv

The exit code is non-zero if schema checks fail, so it is safe to wire
into CI.
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
import urllib.parse
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data" / "saudi_medications.json"

REQUIRED_MED_FIELDS = (
    "brand", "brand_ar", "generic", "category", "classification",
    "evidence_level", "mechanism_en", "mechanism_ar",
    "dosage_hint_en", "dosage_hint_ar",
    "side_effects_en", "side_effects_ar",
    "contraindications_en", "contraindications_ar",
    "age_group", "rx_required", "indicative_price_sar",
    "pharmacies", "sources",
)


def load() -> dict:
    if not DATA.exists():
        print(f"ERROR: data file not found: {DATA}")
        sys.exit(2)
    with open(DATA, "r", encoding="utf-8") as f:
        return json.load(f)


def schema_check(db: dict) -> tuple[list[str], list[str]]:
    """Return (errors, warnings)."""
    errors: list[str] = []
    warnings: list[str] = []

    meta = db.get("_meta", {})
    pharmacies = set(meta.get("pharmacies", []))
    legend = set(meta.get("classification_legend", {}).keys())
    source_ids = {s["id"] for s in meta.get("sources", []) if isinstance(s, dict) and "id" in s}

    if not pharmacies:
        errors.append("_meta.pharmacies is empty.")
    if not legend:
        errors.append("_meta.classification_legend is empty.")
    if not source_ids:
        errors.append("_meta.sources is empty.")

    diseases = db.get("diseases", {})
    if not diseases:
        errors.append("No diseases defined.")
        return errors, warnings

    for d_name, d in diseases.items():
        for f in ("icd10", "name_ar", "overview_en", "overview_ar"):
            if not d.get(f):
                warnings.append(f"[{d_name}] missing {f}")

        meds = d.get("medications", [])
        if not meds:
            warnings.append(f"[{d_name}] no medications listed")

        for i, m in enumerate(meds):
            tag = f"[{d_name}#{i} {m.get('brand', '?')}]"
            for f in REQUIRED_MED_FIELDS:
                if f not in m:
                    errors.append(f"{tag} missing required field '{f}'")

            cls = m.get("classification")
            if cls and cls not in legend:
                errors.append(f"{tag} classification '{cls}' not in _meta.classification_legend")

            for ph in m.get("pharmacies", []):
                if ph not in pharmacies:
                    errors.append(f"{tag} pharmacy '{ph}' not registered in _meta.pharmacies")

            for sid in m.get("sources", []):
                if sid not in source_ids:
                    errors.append(f"{tag} source id '{sid}' not registered in _meta.sources")

            ev = m.get("evidence_level")
            if ev and ev not in (meta.get("evidence_levels", {}) or {}):
                warnings.append(f"{tag} evidence_level '{ev}' not in _meta.evidence_levels")

    return errors, warnings


def search_links(db: dict, disease: str | None = None) -> list[dict]:
    """Build verify-this-medication URLs for every pharmacy that lists it."""
    meta = db.get("_meta", {})
    templates = meta.get("validation", {}).get("search_url_templates", {})
    diseases = db.get("diseases", {})
    if disease and disease not in diseases:
        print(f"Unknown disease '{disease}'. Known: {list(diseases.keys())}")
        sys.exit(2)
    targets = [disease] if disease else list(diseases.keys())

    rows: list[dict] = []
    for d_name in targets:
        for m in diseases[d_name].get("medications", []):
            brand = m.get("brand", "")
            for ph in m.get("pharmacies", []):
                tpl = templates.get(ph) or ""
                url = tpl.replace("{q}", urllib.parse.quote_plus(brand)) if tpl else ""
                rows.append({
                    "disease": d_name,
                    "brand": brand,
                    "brand_ar": m.get("brand_ar", ""),
                    "pharmacy": ph,
                    "search_url": url,
                    "rx_required": m.get("rx_required", False),
                    "indicative_price_sar": m.get("indicative_price_sar", ""),
                    "evidence_level": m.get("evidence_level", ""),
                    "classification": m.get("classification", ""),
                })
    return rows


def ping(db: dict) -> list[tuple[str, str, int | str]]:
    try:
        import requests  # noqa: WPS433
    except ImportError:
        print("ERROR: --ping needs the 'requests' package (already in requirements.txt).")
        sys.exit(2)

    targets: list[tuple[str, str]] = []
    profiles = db.get("_meta", {}).get("pharmacy_profiles", {}) or {}
    for ph, p in profiles.items():
        url = (p or {}).get("site")
        if url:
            targets.append((f"home:{ph}", url))

    for chk in db.get("_meta", {}).get("validation", {}).get("live_spot_checks", []) or []:
        targets.append((f"check:{chk.get('chain')}/{chk.get('brand')}", chk.get("url", "")))

    out: list[tuple[str, str, int | str]] = []
    for label, url in targets:
        if not url:
            out.append((label, url, "skipped(no url)"))
            continue
        try:
            r = requests.head(url, allow_redirects=True, timeout=8,
                              headers={"User-Agent": "Mozilla/5.0 (NafasAI medication validator)"})
            out.append((label, url, r.status_code))
        except Exception as e:
            out.append((label, url, f"err: {type(e).__name__}: {e}"))
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description="Validate the Saudi pharmacy medication dataset.")
    ap.add_argument("--ping", action="store_true", help="HEAD-request every catalogue homepage and spot-check URL.")
    ap.add_argument("--links", action="store_true", help="Print verify-this-medication search URLs.")
    ap.add_argument("--disease", help="Limit --links output to one disease (e.g. Asthma).")
    ap.add_argument("--csv", help="Write a verification CSV to this path.")
    args = ap.parse_args()

    db = load()
    errors, warnings = schema_check(db)

    print("=" * 64)
    print(f"Saudi Medications dataset — {DATA}")
    print(f"Schema version: {db.get('_meta', {}).get('version', '?')}")
    print(f"Last verified : {db.get('_meta', {}).get('validation', {}).get('last_verified', '?')}")
    print(f"Pharmacies    : {db.get('_meta', {}).get('pharmacies', [])}")
    print(f"Sources       : {len(db.get('_meta', {}).get('sources', []))}")
    print(f"Diseases      : {list(db.get('diseases', {}).keys())}")

    n_meds = sum(len(d.get("medications", [])) for d in db.get("diseases", {}).values())
    print(f"Medications   : {n_meds}")
    print("=" * 64)

    if errors:
        print(f"\n[FAIL] {len(errors)} schema errors:")
        for e in errors:
            print(f"  - {e}")
    else:
        print("\n[OK] Schema clean.")
    if warnings:
        print(f"\n[warn] {len(warnings)} warnings:")
        for w in warnings:
            print(f"  - {w}")

    if args.ping:
        print("\nLive HEAD pings:")
        for label, url, status in ping(db):
            print(f"  {status:<10} {label} -> {url}")

    if args.links:
        rows = search_links(db, args.disease)
        print(f"\nVerify-this-medication search URLs ({len(rows)}):")
        for r in rows:
            if r["search_url"]:
                print(f"  [{r['pharmacy']:<10}] {r['brand']:<35} -> {r['search_url']}")
            else:
                print(f"  [{r['pharmacy']:<10}] {r['brand']:<35}    (no search template)")

    if args.csv:
        rows = search_links(db, args.disease)
        out_path = Path(args.csv)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        with open(out_path, "w", encoding="utf-8", newline="") as f:
            w = csv.DictWriter(f, fieldnames=list(rows[0].keys()) if rows else [])
            w.writeheader()
            w.writerows(rows)
        print(f"\nWrote CSV: {out_path} ({len(rows)} rows)")

    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
