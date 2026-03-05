from __future__ import annotations

from flask import Blueprint, jsonify, request

from .models import JobStartRequest
from .runner import runner
from .storage import storage

agent_bp = Blueprint("agent3", __name__, url_prefix="/api/agent3")


@agent_bp.get("/jobs")
def list_jobs():
    jobs = [job.to_dict() for job in storage.list_jobs()]
    return jsonify({"ok": True, "jobs": jobs})


@agent_bp.post("/start")
def start_job():
    data = request.get_json(silent=True) or {}
    goal = (data.get("goal") or "").strip()
    if not goal:
        return _error("Goal is required", 400)

    test_command = data.get("test_command")
    project = data.get("project")
    model = data.get("model")

    reflections = _coerce_int(data.get("max_reflections"), default=0, minimum=0, maximum=5, field="max_reflections")
    if isinstance(reflections, tuple):
        return _error(reflections[1], 400)

    timeout = _coerce_int(data.get("timeout_minutes"), default=10, minimum=1, maximum=120, field="timeout_minutes")
    if isinstance(timeout, tuple):
        return _error(timeout[1], 400)

    payload = JobStartRequest(
        goal=goal,
        test_command=(test_command or None),
        reflections=reflections,
        timeout_minutes=timeout,
        model=(model or None),
        project=(project or None),
    )

    job = storage.create_job(payload)
    runner.start_job(job)
    return jsonify({"ok": True, "job": job.to_dict(), "events": []})


@agent_bp.get("/status")
def job_status():
    job_id = request.args.get("job_id")
    if not job_id:
        return _error("job_id is required", 400)
    cursor_raw = request.args.get("cursor")
    cursor = None
    if cursor_raw is not None and cursor_raw != "":
        try:
            cursor = int(cursor_raw)
        except ValueError:
            return _error("cursor must be an integer", 400)

    job = storage.get_job(job_id)
    if not job:
        return _error("Job not found", 404)

    events = storage.list_events(job_id, cursor)
    next_cursor = events[-1].seq if events else (cursor or 0)
    return jsonify(
        {
            "ok": True,
            "job": job.to_dict(),
            "events": [event.to_dict() for event in events],
            "next_cursor": next_cursor,
        }
    )


@agent_bp.post("/stop")
def stop_job():
    data = request.get_json(silent=True) or {}
    job_id = data.get("job_id")
    if not job_id:
        return _error("job_id is required", 400)
    success = runner.request_stop(job_id)
    if not success:
        return _error("Job not found", 404)
    return jsonify({"ok": True})


def _coerce_int(value, *, default: int, minimum: int, maximum: int, field: str):
    if value is None:
        return default
    try:
        number = int(value)
    except (TypeError, ValueError):
        return None, f"{field} must be an integer"
    if number < minimum or number > maximum:
        return None, f"{field} must be between {minimum} and {maximum}"
    return number


def _error(message: str, status: int):
    return jsonify({"ok": False, "error": message}), status

