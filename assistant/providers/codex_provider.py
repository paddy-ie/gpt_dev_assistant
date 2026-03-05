from __future__ import annotations

import os
from typing import Iterable

import httpx

from .types import ChatMessage, ProviderResult, ProviderSpec


class CodexProvider(ProviderSpec):
    def __init__(self) -> None:
        base_url = os.environ.get("CODEX_API_BASE")
        if not base_url:
            raise RuntimeError("CODEX_API_BASE environment variable is required for Codex provider")
        self.base_url = base_url.rstrip("/")
        self.api_key = os.environ.get("CODEX_API_KEY")
        if not self.api_key:
            raise RuntimeError("CODEX_API_KEY environment variable is required for Codex provider")
        self.default_model = os.environ.get("CODEX_ASSISTANT_MODEL", "codex-latest")

    def generate(
        self,
        messages: Iterable[ChatMessage],
        *,
        temperature: float,
        model: str | None = None,
    ) -> ProviderResult:
        payload = {
            "model": model or self.default_model,
            "messages": list(messages),
            "temperature": temperature,
        }
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        url = f"{self.base_url}/v1/assistant/generate"

        with httpx.Client(timeout=30.0) as client:
            response = client.post(url, json=payload, headers=headers)

        if response.status_code >= 400:
            detail = response.text
            raise RuntimeError(f"Codex API error ({response.status_code}): {detail}")

        data = response.json()
        message = data.get("message") or data.get("output_text") or ""
        return ProviderResult(
            message=str(message).strip(),
            usage=data.get("usage"),
            raw=data,
        )
