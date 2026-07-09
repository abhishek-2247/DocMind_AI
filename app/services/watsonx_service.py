"""
DocMind AI — IBM watsonx.ai service
=====================================
Handles all communication with the watsonx.ai API.
The AGENT_CONFIGURATION dict in config.py drives all AI behaviour.

Compatible with ibm-watsonx-ai >= 1.1.2 (tested up to 1.5.x).
"""

from __future__ import annotations

import re
from typing import Optional

from flask import current_app

# IBM SDK — imported lazily so the app starts even without credentials
try:
    from ibm_watsonx_ai import Credentials
    from ibm_watsonx_ai.foundation_models import ModelInference

    # ibm-watsonx-ai ≥ 1.1 renamed GenTextParamsMetaNames; try both locations
    try:
        from ibm_watsonx_ai.metanames import GenTextParamsMetaNames as GenParams
    except ImportError:
        from ibm_watsonx_ai.foundation_models.schema import (
            TextGenParameters as GenParams,  # type: ignore[assignment]
        )

    IBM_SDK_AVAILABLE = True
except ImportError:
    IBM_SDK_AVAILABLE = False


def _get_client() -> "ModelInference":
    """Return an initialised watsonx.ai ModelInference client."""
    cfg = current_app.config
    agent = cfg["AGENT_CONFIGURATION"]

    if not IBM_SDK_AVAILABLE:
        raise RuntimeError(
            "ibm-watsonx-ai package is not installed. "
            "Run: pip install ibm-watsonx-ai"
        )

    api_key = cfg.get("IBM_API_KEY", "")
    project_id = cfg.get("IBM_PROJECT_ID", "")
    url = cfg.get("IBM_WATSONX_URL", "https://us-south.ml.cloud.ibm.com")

    if not api_key or not project_id:
        raise ValueError(
            "IBM_API_KEY and IBM_PROJECT_ID must be set in your .env file."
        )

    credentials = Credentials(url=url, api_key=api_key)

    # Build generation parameters dict — works regardless of whether GenParams
    # is the old MetaNames class or the newer TextGenParameters schema.
    params = {
        "max_new_tokens": agent["max_new_tokens"],
        "temperature": agent["temperature"],
        "top_p": agent["top_p"],
        "repetition_penalty": agent["repetition_penalty"],
    }

    model = ModelInference(
        model_id=agent["model_id"],
        params=params,
        credentials=credentials,
        project_id=project_id,
    )
    return model


def _build_system_preamble() -> str:
    agent = current_app.config["AGENT_CONFIGURATION"]
    return (
        f"{agent['safety_instructions']}\n\n"
        f"{agent['personality']}\n"
        f"Always respond in a {agent['tone']} tone.\n"
    )


def _call(prompt: str) -> str:
    """Send a prompt to the model and return stripped text, or an error string."""
    try:
        model = _get_client()
        response = model.generate_text(prompt=prompt)
        return (response or "").strip()
    except Exception as exc:  # noqa: BLE001
        current_app.logger.error("watsonx.ai error: %s", exc)
        return f"[AI Error] {exc}"


# ── Public API ────────────────────────────────────────────────────────────────

def generate_response(prompt: str) -> str:
    """Send a raw prompt to the model and return the text response."""
    full_prompt = f"{_build_system_preamble()}\n{prompt}"
    return _call(full_prompt)


def answer_question(
    document_text: str,
    question: str,
    history: Optional[list] = None,
) -> str:
    """Answer a question about a document, optionally using conversation history."""
    history = history or []
    history_str = ""
    for turn in history[-6:]:  # keep last 6 turns to fit context window
        role = "User" if turn["role"] == "user" else "Assistant"
        history_str += f"{role}: {turn['content']}\n"

    prompt = (
        f"{_build_system_preamble()}\n"
        "You are analysing the following document excerpt:\n"
        "---DOCUMENT START---\n"
        f"{document_text[:6000]}\n"
        "---DOCUMENT END---\n\n"
        f"{f'Conversation so far:{chr(10)}{history_str}{chr(10)}' if history_str else ''}"
        f"User: {question}\n"
        "Assistant:"
    )
    return _call(prompt)


def summarise_document(document_text: str, style: str = "bullets") -> str:
    """Generate a summary in the requested style (short | detailed | bullets)."""
    agent = current_app.config["AGENT_CONFIGURATION"]
    style = style or agent["summary_style"]

    style_instructions = {
        "short": "Write a concise 3–5 sentence summary capturing the core message.",
        "detailed": (
            "Write a comprehensive summary covering all major sections, "
            "key arguments, and conclusions. Use clear paragraphs."
        ),
        "bullets": (
            "Summarise the document as a structured bullet-point list. "
            "Group related points under bold headings."
        ),
    }
    instruction = style_instructions.get(style, style_instructions["bullets"])

    prompt = (
        f"{_build_system_preamble()}\n"
        f"Document text:\n{document_text[:7000]}\n\n"
        f"Task: {instruction}\n"
        "Summary:"
    )
    return _call(prompt)


def compare_documents(
    text_a: str,
    text_b: str,
    name_a: str = "Document A",
    name_b: str = "Document B",
) -> dict:
    """Compare two documents and return a structured findings dict."""
    prompt = (
        f"{_build_system_preamble()}\n"
        f"You are comparing two documents: '{name_a}' and '{name_b}'.\n\n"
        f"--- {name_a} ---\n{text_a[:3500]}\n\n"
        f"--- {name_b} ---\n{text_b[:3500]}\n\n"
        "Provide a structured comparison with these four clearly labelled sections:\n"
        "SIMILARITIES:\n"
        "DIFFERENCES:\n"
        "KEY TOPICS IN BOTH:\n"
        "COMPARISON SUMMARY:\n"
    )
    raw = _call(prompt)

    def _extract(section: str) -> str:
        pattern = rf"{re.escape(section)}[:\s]*(.*?)(?=\n[A-Z ]+:|$)"
        match = re.search(pattern, raw, re.DOTALL | re.IGNORECASE)
        return match.group(1).strip() if match else ""

    return {
        "similarities": _extract("SIMILARITIES"),
        "differences": _extract("DIFFERENCES"),
        "key_topics": _extract("KEY TOPICS IN BOTH"),
        "summary": _extract("COMPARISON SUMMARY"),
        "raw": raw,
    }


def extract_insights(document_text: str) -> dict:
    """Extract keywords, topics, and tags from a document."""
    prompt = (
        f"{_build_system_preamble()}\n"
        f"Document:\n{document_text[:5000]}\n\n"
        "Extract and return the following, each on its own clearly labelled line:\n"
        "KEYWORDS: (comma-separated list of 8–12 important keywords)\n"
        "TOPICS: (comma-separated list of 3–6 main topics)\n"
        "TAGS: (comma-separated list of 5–8 short category tags)\n"
        "ONE_LINE_SUMMARY: (a single sentence describing the document)\n"
    )
    raw = _call(prompt)

    def _line(label: str) -> str:
        match = re.search(rf"{re.escape(label)}[:\s]*(.*)", raw, re.IGNORECASE)
        return match.group(1).strip() if match else ""

    return {
        "keywords": [k.strip() for k in _line("KEYWORDS").split(",") if k.strip()],
        "topics": [t.strip() for t in _line("TOPICS").split(",") if t.strip()],
        "tags": [t.strip() for t in _line("TAGS").split(",") if t.strip()],
        "one_line_summary": _line("ONE_LINE_SUMMARY"),
    }
