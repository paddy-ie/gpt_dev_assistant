from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Protocol


ChatMessage = dict


@dataclass(slots=True)
class ProviderResult:
    message: str
    usage: dict | None = None
    raw: dict | None = None


class ProviderSpec(Protocol):
    def generate(
        self,
        messages: Iterable[ChatMessage],
        *,
        temperature: float,
        model: str | None = None,
    ) -> ProviderResult:
        ...
