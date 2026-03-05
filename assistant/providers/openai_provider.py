from __future__ import annotations

import os
from functools import lru_cache
from typing import Iterable

from openai import APIStatusError, OpenAIError, OpenAI

from .types import ChatMessage, ProviderResult, ProviderSpec


@lru_cache(maxsize=1)
def _client() -> OpenAI:
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY environment variable is not set")
    return OpenAI(api_key=api_key)


def _model() -> str:
    default_model = os.environ.get("IDE_ASSISTANT_MODEL", "gpt-4.1-mini")
    return os.environ.get("OPENAI_ASSISTANT_MODEL", default_model)


class OpenAIProvider(ProviderSpec):
    def generate(
        self,
        messages: Iterable[ChatMessage],
        *,
        temperature: float,
        model: str | None = None,
    ) -> ProviderResult:
        model_name = model or _model()
        try:
            response = _client().responses.create(
                model=model_name,
                input=list(messages),
                temperature=temperature,
            )
        except (APIStatusError, OpenAIError) as exc:  # pragma: no cover - network interaction
            raise RuntimeError(f"OpenAI API error: {exc}") from exc

        message = (getattr(response, "output_text", "") or "").strip()
        usage = getattr(response, "usage", None)
        return ProviderResult(
            message=message,
            usage=usage.to_dict() if hasattr(usage, "to_dict") else usage,
            raw=response.to_dict() if hasattr(response, "to_dict") else None,
        )
