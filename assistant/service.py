from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Sequence

from dotenv import load_dotenv

from .providers import ProviderResult, get_provider

load_dotenv()

BASE_SYSTEM_PROMPT = (
    "You are a focused coding assistant living inside a self-hosted IDE. "
    "Help the user build and debug projects quickly while keeping responses concise."
)

MAX_CONTEXT_CHARS = 4000
MAX_HISTORY_MESSAGES = 12  # number of historical turns to include (user+assistant)


@dataclass(slots=True)
class AssistantFile:
    path: str
    content: str


def _coerce_files(files: Optional[Sequence[dict]]) -> list[AssistantFile]:
    if not files:
        return []
    coerced: list[AssistantFile] = []
    for item in files:
        if not item:
            continue
        path = str(item.get("path", "")).strip()
        content = item.get("content")
        if not path or content is None:
            continue
        text = str(content)
        truncated = text[:MAX_CONTEXT_CHARS]
        if len(text) > MAX_CONTEXT_CHARS:
            truncated += "\n... truncated ..."
        coerced.append(AssistantFile(path=path, content=truncated))
    return coerced


def _coerce_history(history: Optional[Sequence[dict]]) -> list[dict]:
    if not history:
        return []
    filtered: list[dict] = []
    for entry in history[-MAX_HISTORY_MESSAGES:]:
        role = entry.get("role")
        text = entry.get("text")
        if role in {"user", "assistant"} and text:
            filtered.append(
                {
                    "role": role,
                    "content": [{"type": "input_text", "text": str(text)}],
                }
            )
    return filtered


def ask_assistant(
    prompt: str,
    *,
    project: Optional[str] = None,
    files: Optional[Sequence[dict]] = None,
    history: Optional[Sequence[dict]] = None,
    model: Optional[str] = None,
    temperature: float = 0.2,
) -> dict:
    if not prompt or not prompt.strip():
        raise ValueError("Prompt is required")

    file_context = _coerce_files(files)
    history_context = _coerce_history(history)

    context_chunks: list[str] = []
    if project:
        context_chunks.append(f"Active project: {project}")
    if file_context:
        rendered = [f"=== {f.path} ===\n{f.content}" for f in file_context]
        context_chunks.append("\n\n".join(rendered))

    system_prompt = BASE_SYSTEM_PROMPT
    if context_chunks:
        system_prompt += "\n\n" + "\n".join(context_chunks)

    provider_name: Optional[str] = None
    model_override: Optional[str] = model
    if model and ":" in model:
        maybe_provider, maybe_model = model.split(":", 1)
        if maybe_provider:
            provider_name = maybe_provider
        model_override = maybe_model or None

    provider = get_provider(provider_name)

    request_messages = [
        {
            "role": "system",
            "content": [{"type": "input_text", "text": system_prompt}],
        },
        *history_context,
        {
            "role": "user",
            "content": [{"type": "input_text", "text": prompt.strip()}],
        },
    ]

    result: ProviderResult = provider.generate(
        request_messages,
        temperature=temperature,
        model=model_override,
    )

    actual_model = model_override
    if not actual_model and result.raw:
        actual_model = (
            result.raw.get("model")
            or result.raw.get("id")
            or result.raw.get("name")
        )

    return {
        "message": result.message,
        "model": actual_model,
        "usage": result.usage,
        "raw": result.raw,
    }
