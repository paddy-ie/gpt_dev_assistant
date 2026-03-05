from __future__ import annotations

from flask import Blueprint, jsonify, request

from projects import manager


def register_file_routes(bp: Blueprint) -> None:
    @bp.get("/tree")
    def api_tree():
        project = request.args.get("project")
        try:
            data = manager.project_tree(project)
        except ValueError as exc:
            return _error(str(exc), 400)
        return jsonify({"ok": True, **data})

    @bp.get("/file")
    def api_read_file():
        project = request.args.get("project")
        path = request.args.get("path", "")
        if not path:
            return _error("Missing path", 400)
        try:
            content = manager.read_file(project, path)
        except FileNotFoundError:
            return _error("File not found", 404)
        except IsADirectoryError:
            return _error("Requested path is a directory", 400)
        return jsonify({"ok": True, "content": content})

    @bp.post("/save")
    def api_save_file():
        data = request.get_json(silent=True) or {}
        project = data.get("project")
        path = data.get("path")
        content = data.get("content", "")
        if not path:
            return _error("Missing path", 400)
        try:
            manager.write_file(project, path, content)
        except ValueError as exc:
            return _error(str(exc), 400)
        return jsonify({"ok": True})

    @bp.post("/new")
    def api_new_entry():
        data = request.get_json(silent=True) or {}
        project = data.get("project")
        path = data.get("path")
        entry_type = data.get("type", "file")
        if not path:
            return _error("Missing path", 400)
        if entry_type not in {"file", "dir"}:
            return _error("Invalid type", 400)
        try:
            manager.create_entry(project, path, entry_type)
        except FileExistsError:
            return _error("Path already exists", 409)
        except ValueError as exc:
            return _error(str(exc), 400)
        return jsonify({"ok": True})

    @bp.post("/rename")
    def api_rename():
        data = request.get_json(silent=True) or {}
        project = data.get("project")
        old_path = data.get("path")
        new_path = data.get("new_path")
        if not old_path or not new_path:
            return _error("Missing path", 400)
        try:
            manager.rename_entry(project, old_path, new_path)
        except FileNotFoundError:
            return _error("Source path not found", 404)
        except FileExistsError:
            return _error("Destination already exists", 409)
        except ValueError as exc:
            return _error(str(exc), 400)
        return jsonify({"ok": True})

    @bp.post("/delete")
    def api_delete():
        data = request.get_json(silent=True) or {}
        project = data.get("project")
        path = data.get("path")
        recursive = bool(data.get("recursive", False))
        if not path:
            return _error("Missing path", 400)
        try:
            manager.delete_entry(project, path, recursive)
        except FileNotFoundError:
            return _error("Path not found", 404)
        except OSError:
            return _error("Directory not empty. Pass recursive=true to remove it.", 400)
        return jsonify({"ok": True})


def _error(message: str, status: int):
    return jsonify({"ok": False, "error": message}), status

