from __future__ import annotations

from flask import Blueprint, jsonify, request

from projects import manager


def register_project_routes(bp: Blueprint) -> None:
    @bp.get("/projects")
    def api_projects():
        return jsonify({"ok": True, "projects": manager.list_projects()})

    @bp.post("/projects")
    def api_create_project():
        data = request.get_json(silent=True) or {}
        name = data.get("name", "")
        try:
            created = manager.create_project(name)
        except ValueError as exc:
            return _error(str(exc), 400)
        except FileExistsError:
            return _error("Project already exists", 409)
        return jsonify({"ok": True, "project": created})

    @bp.delete("/projects/<path:name>")
    def api_delete_project(name: str):
        try:
            manager.delete_project(name)
        except ValueError as exc:
            return _error(str(exc), 400)
        except FileNotFoundError:
            return _error("Project not found", 404)
        return jsonify({"ok": True})


def _error(message: str, status: int):
    return jsonify({"ok": False, "error": message}), status

