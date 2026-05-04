"""Medication Advisor — a small AI component that turns the curated
`saudi_medications.json` dataset into ranked, ready-to-render cards.

Architecture (stays small and explainable on purpose):

1. **Retrieval** — TF-IDF over each medication's descriptor text
   (mechanism + purpose + category + brand + generic). Cosine similarity
   against the patient's free-text symptom notes surfaces the entries the
   notes match best.
2. **Ranker** — a feature-weighted score combining:
       * classification rank   (first_line ≫ rescue/controller ≫ adjunct ≫ …)
       * evidence level         (A=1.0, B=0.85, C=0.7)
       * age-group match        (adult / pediatric / all)
       * contraindication gate  (smoker × Champix bonus, paediatric guard)
       * TF-IDF relevance       (cosine against patient_notes)
3. **Synthesiser** — template builder that emits the 5-field card the UI
   asks for: `name`, `description`, `why`, `bullets`, `link` (plus AR
   variants and a `meta` block carrying price/evidence/pharmacies).

This is intentionally NOT a generative LLM. The dataset is hand-curated
and we want the explanations to be deterministic and auditable.
"""

from __future__ import annotations

import os
import urllib.parse
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional

import joblib
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from .medications import _DB, get_medications  # reuses the same loader

# Persisted index so the advisor is a real "trained" artifact alongside the
# audio CNN, clinical RF and NLP models. Lives at the project root next to
# the other *_weights.* files so prune_and_train.py can manage it uniformly.
_WEIGHTS_PATH = Path(__file__).resolve().parent.parent / "advisor_weights.pkl"

# ---- ranking weights ------------------------------------------------------

# Lower rank number → first_line, controller, rescue come first.
# Anything not in the legend defaults to rank 99.
_CLASS_BASE = {
    "first_line": 1.00,
    "controller": 0.92,
    "rescue":     0.92,
    "second_line": 0.78,
    "adjunct":     0.72,
    "symptom_relief": 0.65,
    "supportive":  0.55,
    "preventive":  0.50,
}
_EVIDENCE_W = {"A": 1.00, "B": 0.85, "C": 0.70}


@dataclass
class MedicationCard:
    """The 5-field card the UI consumes."""
    name: str
    name_ar: str
    description: str
    description_ar: str
    why: str
    why_ar: str
    bullets: list[str] = field(default_factory=list)
    bullets_ar: list[str] = field(default_factory=list)
    link: str = ""
    extra_links: list[dict] = field(default_factory=list)
    meta: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "name_ar": self.name_ar,
            "description": self.description,
            "description_ar": self.description_ar,
            "why": self.why,
            "why_ar": self.why_ar,
            "bullets": list(self.bullets),
            "bullets_ar": list(self.bullets_ar),
            "link": self.link,
            "extra_links": list(self.extra_links),
            "meta": dict(self.meta),
        }


def _descriptor(med: dict) -> str:
    """Free-text we run TF-IDF over."""
    parts = [
        med.get("brand", ""),
        med.get("generic", ""),
        med.get("category", ""),
        med.get("mechanism_en", ""),
        med.get("purpose_en", ""),  # backward-compat with v1
        med.get("dosage_hint_en", ""),
    ]
    return " ".join(p for p in parts if p)


class MedicationAdvisor:
    """Builds and serves ranked medication cards.

    `_DB` is the dataset already loaded by `medications.py`, so we share
    the same in-memory copy instead of re-reading the JSON.
    """

    def __init__(self) -> None:
        self.legend = (_DB.get("_meta", {}) or {}).get("classification_legend", {}) or {}
        self.search_templates = (((_DB.get("_meta", {}) or {})
                                  .get("validation", {}) or {})
                                 .get("search_url_templates", {}) or {})
        self.live_checks_by_brand = self._index_live_checks()
        self.tfidf: Optional[TfidfVectorizer] = None
        self.tfidf_corpus_size: int = 0
        # Try to warm-load a persisted index. This is just an optimisation —
        # the advisor still works if the file is missing (it rebuilds per call).
        self._load_persisted()

    # ---- persistence ------------------------------------------------------

    def _all_descriptors(self) -> list[str]:
        """Build the descriptor corpus across every disease in the DB."""
        out: list[str] = []
        diseases = (_DB or {}).get("diseases", {}) or {}
        for d in diseases.values():
            for m in (d or {}).get("medications", []) or []:
                out.append(_descriptor(m))
        return out

    def fit_and_save(self, path: Path | None = None) -> dict[str, Any]:
        """Fit a global TF-IDF over every medication descriptor and persist it.

        Called by prune_and_train.py and auto_train.py. The persisted file
        gives the advisor a real artifact that can be deleted/re-built like
        the other model weights.
        """
        path = path or _WEIGHTS_PATH
        corpus = self._all_descriptors()
        if not corpus:
            raise RuntimeError("No medication descriptors found — is data/saudi_medications.json valid?")
        vec = TfidfVectorizer(stop_words="english", ngram_range=(1, 2))
        vec.fit(corpus)

        meta = (_DB.get("_meta", {}) or {})
        payload = {
            "format": "nafas-advisor-v1",
            "tfidf": vec,
            "n_terms": len(vec.vocabulary_),
            "n_descriptors": len(corpus),
            "schema_version": meta.get("version", "?"),
            "data_last_verified": (meta.get("validation", {}) or {}).get("last_verified", ""),
        }
        joblib.dump(payload, str(path))
        self.tfidf = vec
        self.tfidf_corpus_size = len(corpus)
        return {
            "saved_to": str(path),
            "n_terms": payload["n_terms"],
            "n_descriptors": payload["n_descriptors"],
        }

    def _load_persisted(self, path: Path | None = None) -> bool:
        path = path or _WEIGHTS_PATH
        if not path.exists():
            return False
        try:
            payload = joblib.load(str(path))
            if not isinstance(payload, dict) or payload.get("format") != "nafas-advisor-v1":
                return False
            self.tfidf = payload.get("tfidf")
            self.tfidf_corpus_size = int(payload.get("n_descriptors", 0))
            return True
        except Exception as e:
            print(f"[advisor] could not load persisted index: {e}")
            return False

    # ---- helpers ---------------------------------------------------------

    @staticmethod
    def _norm(token: str) -> str:
        """Normalise a token for fuzzy matching: lower, strip punctuation, collapse units."""
        return "".join(c for c in token.lower() if c.isalnum())

    @staticmethod
    def _index_live_checks() -> dict[str, list[dict]]:
        out: dict[str, list[dict]] = {}
        meta = _DB.get("_meta", {}) or {}
        for chk in (meta.get("validation", {}) or {}).get("live_spot_checks", []) or []:
            out.setdefault(chk.get("brand", ""), []).append(chk)
        return out

    # ---- ranking ---------------------------------------------------------

    def _classification_score(self, key: str) -> float:
        return _CLASS_BASE.get(key, 0.40)

    def _age_match_score(self, med: dict, patient_age: Optional[float]) -> float:
        ag = med.get("age_group", "all")
        if patient_age is None:
            return 0.95
        if ag == "all":
            return 1.0
        if ag == "pediatric":
            return 1.0 if patient_age <= 16 else 0.40
        if ag == "adult":
            return 1.0 if patient_age > 16 else 0.45
        return 0.85

    def _smoker_bonus(self, med: dict, smoker: int) -> float:
        # Slight nudge: if patient is a smoker, smoking-cessation aid relevance up.
        if smoker == 1 and "varenicline" in (med.get("generic", "") or "").lower():
            return 0.20
        return 0.0

    def _tfidf_relevance(self, meds: list[dict], query: str) -> list[float]:
        if not meds or not query.strip():
            return [0.0] * len(meds)
        try:
            corpus = [_descriptor(m) for m in meds]
            if self.tfidf is not None:
                # Use persisted vectoriser — vocabulary already learned across all meds.
                med_mat = self.tfidf.transform(corpus)
                q_mat = self.tfidf.transform([query])
                sims = cosine_similarity(q_mat, med_mat).flatten()
                return [float(s) for s in sims]
            # Cold path — fit on the candidate set.
            vec = TfidfVectorizer(stop_words="english", ngram_range=(1, 2))
            mat = vec.fit_transform(corpus + [query])
            sims = cosine_similarity(mat[-1], mat[:-1]).flatten()
            return [float(s) for s in sims]
        except Exception:
            return [0.0] * len(meds)

    def _rank(self, meds: list[dict], context: dict) -> list[tuple[float, dict, dict]]:
        relevances = self._tfidf_relevance(meds, context.get("patient_notes", ""))
        scored: list[tuple[float, dict, dict]] = []
        age = context.get("age")
        smoker = int(context.get("smoker", 0) or 0)

        for med, rel in zip(meds, relevances):
            cls = self._classification_score(med.get("classification", ""))
            ev = _EVIDENCE_W.get(med.get("evidence_level", ""), 0.70)
            age_w = self._age_match_score(med, age)
            smk = self._smoker_bonus(med, smoker)

            # Weighted average — classification & evidence dominate, TF-IDF tilts.
            score = (
                0.42 * cls
                + 0.22 * ev
                + 0.16 * age_w
                + 0.20 * min(1.0, rel * 4.0)  # scale weak cosine values up
                + smk
            )
            features = {
                "classification_w": round(cls, 3),
                "evidence_w": round(ev, 3),
                "age_match": round(age_w, 3),
                "tfidf_rel": round(rel, 3),
                "smoker_bonus": round(smk, 3),
                "total": round(score, 3),
            }
            scored.append((score, med, features))

        scored.sort(key=lambda t: t[0], reverse=True)
        return scored

    # ---- link builder ----------------------------------------------------

    def _primary_link(self, med: dict) -> tuple[str, list[dict]]:
        """Pick the strongest link for the 'View product' button.

        Preference order:
          1. A live-verified product URL (from `_meta.validation.live_spot_checks`).
             Match is fuzzy by first-token (e.g. brand "Augmentin 1g" matches
             a spot-check "Augmentin 1 g (14 tablets)").
          2. Search URL on the largest chain that stocks this medication
             (Nahdi → Al-Dawaa → Tadawi → Boots → Innova → Bin Dawood → Whites).
          3. Empty string.

        Also returns up to 3 search-URL fallbacks so the UI can offer
        "search on chain X" buttons.
        """
        brand = med.get("brand", "") or ""
        live = self.live_checks_by_brand.get(brand, [])
        if not live:
            # Fuzzy match: highest token-overlap spot-check sharing the
            # brand's first token. Picks "Augmentin 1g" → "Augmentin 1 g (14 tablets)"
            # rather than the 625 mg variant.
            tokens = {self._norm(t) for t in brand.split() if t}
            first = next(iter(brand.split()), "").lower()
            best, best_score = None, 0
            for k, items in self.live_checks_by_brand.items():
                if not k or not first or k.split()[0].lower() != first:
                    continue
                check_tokens = {self._norm(t) for t in k.split() if t}
                overlap = len(tokens & check_tokens)
                if overlap > best_score:
                    best, best_score = items[0], overlap
            if best:
                live = [best]
        primary = ""
        extras: list[dict] = []
        if live:
            primary = live[0].get("url", "") or ""
            for item in live:
                extras.append({
                    "label": f"{item.get('chain')} — verified product page",
                    "label_ar": f"{item.get('chain')} — صفحة المنتج",
                    "url": item.get("url", ""),
                    "verified": item.get("verified", ""),
                })

        chain_priority = ["Nahdi", "Al-Dawaa", "Tadawi", "Boots", "Innova", "Bin Dawood", "Whites", "Al-Mamlaka"]
        encoded = urllib.parse.quote_plus(brand)
        present = set(med.get("pharmacies", []) or [])
        added = 0
        for ch in chain_priority:
            if ch not in present:
                continue
            tpl = self.search_templates.get(ch) or ""
            if not tpl:
                continue
            url = tpl.replace("{q}", encoded)
            if not primary:
                primary = url
            if url != primary and added < 3:
                extras.append({
                    "label": f"Search on {ch}",
                    "label_ar": f"ابحث في {ch}",
                    "url": url,
                })
                added += 1

        return primary, extras

    # ---- synthesiser -----------------------------------------------------

    def _legend_label(self, key: str, lang: str = "en") -> str:
        item = self.legend.get(key) or {}
        return item.get(lang) or key.replace("_", " ").title()

    def _build_why(self, med: dict, lang: str = "en") -> str:
        cls = self._legend_label(med.get("classification", ""), lang)
        ev = med.get("evidence_level", "")
        if lang == "ar":
            mech = med.get("mechanism_ar", "") or med.get("mechanism_en", "")
            return f"اختير كـ«{cls}» (مستوى الدليل {ev}). {mech}"
        mech = med.get("mechanism_en", "") or med.get("mechanism_ar", "")
        return f"Selected as {cls} (evidence level {ev}). {mech}"

    def _build_bullets(self, med: dict, context: dict, lang: str = "en") -> list[str]:
        bullets: list[str] = []
        if lang == "ar":
            if med.get("dosage_hint_ar"):
                bullets.append(f"الجرعة: {med['dosage_hint_ar']}")
            if med.get("side_effects_ar"):
                bullets.append(f"الآثار الجانبية: {med['side_effects_ar']}")
            if med.get("contraindications_ar"):
                bullets.append(f"موانع الاستخدام: {med['contraindications_ar']}")
            if med.get("rx_required"):
                bullets.append("يحتاج وصفة طبية.")
            else:
                bullets.append("يصرف بدون وصفة طبية.")
            price = med.get("indicative_price_sar")
            if price not in (None, "", 0):
                bullets.append(f"السعر التقريبي: {price} ريال سعودي")
        else:
            if med.get("dosage_hint_en"):
                bullets.append(f"Dosage: {med['dosage_hint_en']}")
            if med.get("side_effects_en"):
                bullets.append(f"Side effects: {med['side_effects_en']}")
            if med.get("contraindications_en"):
                bullets.append(f"Contraindications: {med['contraindications_en']}")
            if med.get("rx_required"):
                bullets.append("Prescription required.")
            else:
                bullets.append("Available over-the-counter.")
            price = med.get("indicative_price_sar")
            if price not in (None, "", 0):
                bullets.append(f"Indicative price: {price} SAR")

        # Smoker-specific note for smoking-cessation aids.
        if int(context.get("smoker", 0) or 0) == 1 and "varenicline" in (med.get("generic", "") or "").lower():
            bullets.append(
                "Patient is a smoker — quit-aid is highly relevant." if lang == "en"
                else "المريض مدخن — هذا العلاج لمساعدة الإقلاع ذو صلة عالية."
            )
        return bullets

    def _description(self, med: dict, lang: str = "en") -> str:
        if lang == "ar":
            base = med.get("category", "")
            generic = med.get("generic_ar", "") or med.get("generic", "")
            return f"{base} — {generic}".strip(" —")
        return f"{med.get('category', '')} — {med.get('generic', '')}".strip(" —")

    def build_card(self, med: dict, context: dict) -> MedicationCard:
        link, extras = self._primary_link(med)
        return MedicationCard(
            name=med.get("brand", ""),
            name_ar=med.get("brand_ar", ""),
            description=self._description(med, "en"),
            description_ar=self._description(med, "ar"),
            why=self._build_why(med, "en"),
            why_ar=self._build_why(med, "ar"),
            bullets=self._build_bullets(med, context, "en"),
            bullets_ar=self._build_bullets(med, context, "ar"),
            link=link,
            extra_links=extras,
            meta={
                "classification": med.get("classification", ""),
                "classification_label_en": self._legend_label(med.get("classification", ""), "en"),
                "classification_label_ar": self._legend_label(med.get("classification", ""), "ar"),
                "evidence_level": med.get("evidence_level", ""),
                "rx_required": bool(med.get("rx_required", False)),
                "indicative_price_sar": med.get("indicative_price_sar"),
                "age_group": med.get("age_group", "all"),
                "pharmacies": list(med.get("pharmacies", []) or []),
                "category": med.get("category", ""),
            },
        )

    # ---- public API ------------------------------------------------------

    def recommend(self, disease: str, context: Optional[dict] = None, top_n: int = 4) -> dict[str, Any]:
        """Return a disease-aware ranked list of medication cards.

        Args:
            disease:    one of the 8 disease labels.
            context:    optional patient context. Recognised keys:
                            age (float), sex (0/1), bmi, spo2, temperature,
                            smoker (0/1), patient_notes (str).
            top_n:      max number of cards to return.

        Returns a dict shaped for direct JSON serialisation:
            {
              "disease": ...,
              "disease_ar": ...,
              "cards": [ {name, description, why, bullets, link, ...}, ... ],
              "model": "tfidf+ranker",
              "ranking_signals": ["classification", "evidence_level",
                                  "age_match", "tfidf_relevance", "smoker_bonus"]
            }
        """
        ctx = context or {}
        bundle = get_medications(disease)
        meds = bundle.get("items", []) or []
        if not meds:
            return {
                "disease": disease,
                "disease_ar": bundle.get("disease_ar", disease),
                "cards": [],
                "model": "tfidf+ranker",
                "ranking_signals": [],
            }

        ranked = self._rank(meds, ctx)
        top = ranked[: max(1, top_n)]
        cards = []
        for score, med, feats in top:
            card = self.build_card(med, ctx)
            card.meta["score"] = round(score, 3)
            card.meta["features"] = feats
            cards.append(card.to_dict())

        return {
            "disease": disease,
            "disease_ar": bundle.get("disease_ar", disease),
            "cards": cards,
            "model": "tfidf+ranker",
            "ranking_signals": ["classification", "evidence_level", "age_match", "tfidf_relevance", "smoker_bonus"],
            "total_candidates": len(meds),
        }


# Module-level singleton — built lazily so failures don't break the app boot.
_advisor: Optional[MedicationAdvisor] = None


def get_advisor() -> MedicationAdvisor:
    global _advisor
    if _advisor is None:
        _advisor = MedicationAdvisor()
    return _advisor


def recommend(disease: str, context: Optional[dict] = None, top_n: int = 4) -> dict[str, Any]:
    """Module-level shortcut used by `main.py`."""
    return get_advisor().recommend(disease, context=context, top_n=top_n)
