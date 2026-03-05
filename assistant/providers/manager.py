from __future__ import annotations

import os
from typing import Callable, Dict

from .types import ProviderSpec
from .openai_provider import OpenAIProvider
from .codex_provider import CodexProvider

ProviderFactory = Callable[[], ProviderSpec]

_REGISTRY: Dict[str, ProviderFactory] = {
    "openai": OpenAIProvider,
    "codex": CodexProvider,
}


def get_provider(name: str | None = None) -> ProviderSpec:
    """Return an instantiated provider, defaulting to env configuration."""
    provider_name = (name or os.environ.get("IDE_ASSISTANT_PROVIDER", "openai")).lower()
    try:
        factory = _REGISTRY[provider_name]
    except KeyError as exc:
        available = ", ".join(sorted(_REGISTRY))
        raise ValueError(f"Unknown assistant provider '{provider_name}'. Available: {available}") from exc
    return factory()


def list_providers() -> list[str]:
    """Return the available provider names."""
    return sorted(_REGISTRY)
