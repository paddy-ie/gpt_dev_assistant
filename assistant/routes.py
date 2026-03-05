from __future__ import annotations

from flask import Blueprint, jsonify, request

from . import history
from .service import ask_assistant

assistant_bp = Blueprint("assistant_api", __name__, url_prefix="/api/assistant")


@assistant_bp.get("/history")
def get_history():
    project = request.args.get("project")
    limit = request.args.get("limit")
    limit_value = None
    if limit is not None:
        try:
            limit_value = max(1, int(limit))
        except (TypeError, ValueError):
            return _error("Invalid limit", 400)
    messages = history.load_messages(project, limit_value)
    return jsonify({"ok": True, "messages": messages})


@assistant_bp.post("/history/clear")
def clear_history():
    data = request.get_json(silent=True) or {}
    project = data.get("project")
    history.clear_history(project)
    return jsonify({"ok": True})


@assistant_bp.post("/chat")
def chat():
    data = request.get_json(silent=True) or {}
    prompt = data.get("prompt", "")
    project = data.get("project")
    files = data.get("files")
    model = data.get("model")
    provider = data.get("provider")
    temperature = data.get("temperature")

    temp_value = 0.2
    if temperature is not None:
        try:
            temp_value = float(temperature)
        except (TypeError, ValueError):
            return _error("Invalid temperature", 400)

    previous_messages = history.load_messages(project)

    model_identifier = model
    if provider:
        provider = str(provider).strip()
        if provider:
            if model:
                model_identifier = f"{provider}:{model}"
            else:
                model_identifier = f"{provider}:"

    try:
        result = ask_assistant(
            prompt,
            project=project,
            files=files,
            history=previous_messages,
            model=model_identifier,
            temperature=temp_value,
        )
    except ValueError as exc:
        return _error(str(exc), 400)
    except RuntimeError as exc:
        return _error(str(exc), 502)

    assistant_message = result.get("message", "")
    if assistant_message:
        updated_messages = history.append_exchange(project, prompt.strip(), assistant_message)
    else:
        updated_messages = previous_messages

    payload = {
        "ok": True,
        "message": assistant_message,
        "model": result.get("model"),
        "usage": result.get("usage"),
        "messages": updated_messages,
    }
    return jsonify(payload)


def _error(message: str, status: int):
    return jsonify({"ok": False, "error": message}), status

