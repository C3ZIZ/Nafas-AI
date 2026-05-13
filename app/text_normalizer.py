"""
Map Arabic patient_notes onto the English clinical vocabulary the NLP
brain (nlp_model.py) and the medication-advisor's TF-IDF ranker were
trained on.

This module is intentionally a *thin wrapper* over the Hugging Face
translation API exposed by `llm_provider.translate_ar_to_en`. We do
the minimum of cheap, deterministic work locally:

  - Detect whether the input contains Arabic at all (pure-English text
    is a no-op — we do not waste an API call).
  - Strip diacritics / unify letter variants before sending, so the
    upstream model sees a clean form.
  - Strip residual Arabic characters from the API output as a safety
    net.

Any failure to translate raises `LLMProviderError`, which the FastAPI
route converts into a 503 with a clear message — there is no silent
dictionary fallback (the user opted for hard-fail behaviour).
"""

from __future__ import annotations

import re
import unicodedata

from .llm_provider import translate_ar_to_en, LLMProviderError  # noqa: F401


# Tashkeel (vowel marks) + superscript alef + Quranic annotation marks.
# IMPORTANT: this MUST NOT cover the letter block (U+0621-U+064A) — an
# earlier version did, which silently emptied every Arabic message
# before it reached the translator.
_AR_DIACRITICS = re.compile(
    "[ً-ْ"   # fathatan, dammatan, kasratan, fatha, damma, kasra, shadda, sukun
    "ٰ"           # superscript alef (dagger alef)
    "ۖ-ۭ"    # Quranic annotation signs
    "]"
)
_AR_TATWEEL = "ـ"
# Full Arabic script block range — used only to detect Arabic and to
# scrub stray Arabic chars from the model's English output.
_AR_RANGE = re.compile(
    "[؀-ۿ"   # Arabic
    "ݐ-ݿ"    # Arabic Supplement
    "ࢠ-ࣿ"    # Arabic Extended-A
    "ﭐ-﷿"    # Arabic Presentation Forms-A
    "ﹰ-﻿"    # Arabic Presentation Forms-B
    "]"
)


def contains_arabic(text: str) -> bool:
    """True if any Arabic-script character appears in `text`."""
    return bool(_AR_RANGE.search(text or ""))


def _strip_arabic(text: str) -> str:
    """Remove tashkeel / tatweel and unify common Arabic letter variants."""
    text = unicodedata.normalize("NFKC", text)
    text = _AR_DIACRITICS.sub("", text)
    text = text.replace(_AR_TATWEEL, "")
    table = str.maketrans({
        "أ": "ا", "إ": "ا", "آ": "ا", "ٱ": "ا",
        "ى": "ي", "ئ": "ي",
        "ؤ": "و",
        "ة": "ه",
    })
    return text.translate(table)


def to_clinical_english(text: str) -> str:
    """Return clinical English suitable for the NLP TF-IDF model.

    - Empty / whitespace input -> "".
    - Pure-English input -> returned unchanged (no API call).
    - Arabic (or mixed) input -> translated via Hugging Face. Raises
      `LLMProviderError` on any failure.
    """
    if not text or not text.strip():
        return ""
    if not contains_arabic(text):
        return text

    pre = _strip_arabic(text)
    translated = translate_ar_to_en(pre)

    # Safety net: drop any Arabic chars that survived (some MT models
    # occasionally pass-through unknown tokens). Collapse whitespace.
    translated = _AR_RANGE.sub(" ", translated)
    translated = re.sub(r"\s+", " ", translated).strip()
    return translated
