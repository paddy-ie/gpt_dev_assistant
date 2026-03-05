from __future__ import annotations

from datetime import datetime
import json
from pathlib import Path
from typing import List, Optional

from utils.paths import WORKSPACE_ROOT

HISTORY_ROOT = WORKSPACE_ROOT / ".assistant_history"
MAX_STORED_MESSAGES = 200


def _sanitize_project(project: Optional[str]) -> str:
    if not project or project == "root":
        return "root"
    cleaned = project.strip().replace("\\", "/")
    if cleaned.startswith("/"):
        cleaned = cleaned.lstrip("/")
    parts = [p for p in cleaned.split("/") if p not in {"", "."}]
    safe = "__".join(parts) if parts else "root"
    if ".." in parts:
        raise ValueError("Project name may not contain '..'")
    return safe


def _history_file(project: Optional[str]) -> Path:
    safe_proj = _sanitize_project(project)
    HISTORY_ROOT.mkdir(parents=True, exist_ok=True)
    return HISTORY_ROOT / f"{safe_proj}.json"


def load_messages(project: Optional[str], limit: Optional[int] = None) -> List[dict]:
    history_path = _history_file(project)
    if not history_path.exists():
        return []
    try:
        data = json.loads(history_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return []
    messages: List[dict] = data if isinstance(data, list) else []
    if limit is not None and limit > 0:
        return messages[-limit:]
    return messages


def append_exchange(project: Optional[str], user_prompt: str, assistant_message: str) -> List[dict]:
    timestamp = datetime.utcnow().isoformat() + "Z"
    messages = load_messages(project)
    messages.extend(
        [
            {"role": "user", "text": user_prompt, "timestamp": timestamp},
            {"role": "assistant", "text": assistant_message, "timestamp": timestamp},
        ]
    )
    if len(messages) > MAX_STORED_MESSAGES:
        messages = messages[-MAX_STORED_MESSAGES:]
    history_path = _history_file(project)
    history_path.write_text(json.dumps(messages, ensure_ascii=False, indent=2), encoding="utf-8")
    return messages


def clear_history(project: Optional[str]) -> None:
    history_path = _history_file(project)
    if history_path.exists():
        history_path.unlink()

