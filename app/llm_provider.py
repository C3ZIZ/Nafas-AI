"""
Hugging Face Inference Providers integration.

A single module talks to Hugging Face. It exposes two functions used by
the rest of the backend:

  - `translate_ar_to_en(text)` ........ Arabic -> English (used by the
                                        NLP brain and the medication
                                        ranker).
  - `chat(messages, system=None, ...)`  General chat completion (used by
                                        the doctor-assistant endpoint).

Both go through the OpenAI-compatible **Inference Providers router**
(`https://router.huggingface.co/v1/chat/completions`). Hugging Face has
deprecated the legacy `api-inference.huggingface.co/models/{id}`
serverless endpoint, so we no longer use it. Routing translation through
chat completions also collapses configuration down to a SINGLE model
env var (`HF_CHAT_MODEL`) — the same key/model serves both features.

Configuration
-------------
Set in the project-root `.env` file (see `.env.example`):

    HF_TOKEN=hf_xxx                                # required
    HF_CHAT_MODEL=meta-llama/Llama-3.1-8B-Instruct # optional override

Behaviour
---------
- A missing/invalid token raises `LLMProviderError` with a user-facing
  message. The caller (FastAPI route) returns it as a 503.
- All network calls have a bounded timeout. Failures bubble up the same
  way — no silent fallback to a hard-coded dictionary.
"""

from __future__ import annotations

import os
from typing import Optional

import httpx
from dotenv import load_dotenv

# Load .env once at import time. Subsequent os.getenv() calls see the
# vars. No-op if there is no .env file (legitimate when the user sets
# HF_TOKEN via the shell environment instead).
load_dotenv()


class LLMProviderError(RuntimeError):
    """Raised when the provider can't fulfil a request.

    The string message is safe to surface to the user as the body of a
    503 response — it explains what they need to do (set HF_TOKEN, pick
    a different model, etc.) without leaking secrets.
    """


_CHAT_URL = "https://router.huggingface.co/v1/chat/completions"

_DEFAULT_CHAT_MODEL = "meta-llama/Llama-3.1-8B-Instruct"

# Prompt that turns a chat-completion model into a deterministic
# AR -> EN clinical translator. Output is fed straight into the
# downstream TF-IDF model, so we keep the prompt minimal — small Llama
# models become unreliable when the system message looks like a glossary
# and silently return placeholders like "no translation provided".
_TRANSLATE_SYSTEM_PROMPT = (
    "Translate the user's Arabic medical text to English using standard "
    "clinical terminology. Output only the translated text — no quotes, "
    "no notes, no preamble. If the input is already English, return it "
    "unchanged."
)

_DEFAULT_TIMEOUT = httpx.Timeout(60.0, connect=10.0)


def _require_token() -> str:
    token = (
        os.getenv("HF_TOKEN")
        or os.getenv("HUGGINGFACE_API_KEY")
        or ""
    ).strip()
    if not token or token == "hf_replace_me":
        raise LLMProviderError(
            "Hugging Face API key not configured. Create a free token at "
            "https://huggingface.co/settings/tokens, then put it in the "
            ".env file at the project root as HF_TOKEN=hf_xxx and restart "
            "the server."
        )
    return token


def _auth_headers() -> dict[str, str]:
    return {
        "Authorization": f"Bearer {_require_token()}",
        "Accept": "application/json",
        "Content-Type": "application/json",
    }


def _post_chat(payload: dict, timeout: httpx.Timeout = _DEFAULT_TIMEOUT) -> str:
    """POST to the chat-completions router, return assistant text or raise."""
    try:
        with httpx.Client(timeout=timeout) as client:
            resp = client.post(_CHAT_URL, headers=_auth_headers(), json=payload)
    except httpx.HTTPError as e:
        raise LLMProviderError(
            f"Could not reach Hugging Face Inference Providers router: {e}"
        ) from e

    if resp.status_code in (401, 403):
        raise LLMProviderError(
            "Hugging Face rejected the token (401/403). Generate a new "
            "token with the 'Inference Providers' permission at "
            "https://huggingface.co/settings/tokens and put it in .env."
        )
    if resp.status_code == 404:
        model = payload.get("model", "<unknown>")
        raise LLMProviderError(
            f"Chat model '{model}' is not available on the Hugging Face "
            "Inference Providers router. Set HF_CHAT_MODEL in .env to a "
            "supported model (e.g. meta-llama/Llama-3.1-8B-Instruct, "
            "Qwen/Qwen2.5-7B-Instruct)."
        )
    if resp.status_code == 429:
        raise LLMProviderError(
            "Hugging Face rate-limited this request (429). Wait a moment "
            "and try again, or upgrade your HF plan."
        )
    if resp.status_code >= 400:
        # Pass the upstream error string through verbatim (truncated) so
        # the user sees, e.g., "model X is not a chat model" directly.
        raise LLMProviderError(
            f"Hugging Face returned {resp.status_code}: {resp.text[:400]}"
        )

    try:
        data = resp.json()
    except ValueError as e:
        raise LLMProviderError(
            f"Hugging Face returned non-JSON: {resp.text[:300]}"
        ) from e

    try:
        return data["choices"][0]["message"]["content"].strip()
    except (KeyError, IndexError, TypeError, AttributeError) as e:
        raise LLMProviderError(
            f"Unexpected chat response shape: {str(data)[:400]}"
        ) from e


def translate_ar_to_en(text: str) -> str:
    """Translate Arabic free-text into English clinical terminology.

    Pure-whitespace / empty input returns "" without making a network
    call. Any failure raises `LLMProviderError`.
    """
    text = (text or "").strip()
    if not text:
        return ""

    model = os.getenv("HF_CHAT_MODEL", _DEFAULT_CHAT_MODEL)
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": _TRANSLATE_SYSTEM_PROMPT},
            {"role": "user", "content": text},
        ],
        "temperature": 0.1,
        "max_tokens": 256,
        "stream": False,
    }
    return _post_chat(payload, timeout=httpx.Timeout(30.0, connect=10.0))


def chat(
    messages: list[dict],
    system: Optional[str] = None,
    temperature: float = 0.3,
    max_tokens: int = 768,
) -> str:
    """Run a chat completion against Hugging Face Inference Providers.

    `messages` is a list of {"role": "user"|"assistant", "content": str}.
    If `system` is provided it is prepended as the system message.
    Returns the assistant text. Failures raise `LLMProviderError`.
    """
    if not messages:
        raise LLMProviderError("chat() called with an empty messages list.")

    model = os.getenv("HF_CHAT_MODEL", _DEFAULT_CHAT_MODEL)

    payload_messages: list[dict] = []
    if system:
        payload_messages.append({"role": "system", "content": system})
    payload_messages.extend(messages)

    payload = {
        "model": model,
        "messages": payload_messages,
        "temperature": float(temperature),
        "max_tokens": int(max_tokens),
        "stream": False,
    }
    return _post_chat(payload)


def health() -> dict:
    """Cheap diagnostic for the /llm_status endpoint.

    Reports whether a token is configured and which chat model is wired
    in. Does NOT actually call HF, so it is safe and fast.
    """
    token = (os.getenv("HF_TOKEN") or os.getenv("HUGGINGFACE_API_KEY") or "").strip()
    return {
        "configured": bool(token) and token != "hf_replace_me",
        "chat_model": os.getenv("HF_CHAT_MODEL", _DEFAULT_CHAT_MODEL),
    }
