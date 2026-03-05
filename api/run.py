from __future__ import annotations

from flask import Blueprint, jsonify, request

from executor.sandbox import execute_python


def register_run_routes(bp: Blueprint) -> None:
    @bp.post("/run")
    def api_run():
        data = request.get_json(silent=True) or {}
        project = data.get("project")
        path = data.get("path")
        code = data.get("code")
        timeout = data.get("timeout")
        timeout_value = None
        if timeout is not None:
            try:
                timeout_value = max(1, int(timeout))
            except (TypeError, ValueError):
                return _error("Invalid timeout", 400)
        try:
            result = execute_python(project=project, path=path, code=code, timeout=timeout_value)
        except FileNotFoundError:
            return _error("File not found", 404)
        except ValueError as exc:
            return _error(str(exc), 400)
        return jsonify(
            {
                "ok": True,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "returncode": result.returncode,
                "timed_out": result.timed_out,
                "script_path": result.script_path,
            }
        )


def _error(message: str, status: int):
    return jsonify({"ok": False, "error": message}), status

