from __future__ import annotations

from pathlib import Path
import os

BASE_DIR = Path(__file__).resolve().parent.parent
WORKSPACE_ROOT = Path(os.environ.get("IDE_WORKSPACE_ROOT", BASE_DIR / "workspace")).resolve()
WORKSPACE_ROOT.mkdir(parents=True, exist_ok=True)


def ensure_within_workspace(path: Path) -> Path:
    """Validate that *path* stays inside the workspace and return it."""
    resolved = path.resolve()
    try:
        resolved.relative_to(WORKSPACE_ROOT)
    except ValueError as exc:  # pragma: no cover - defensive guard
        raise ValueError("Path escapes workspace root") from exc
    return resolved


def get_project_root(project: str | None) -> Path:
    """Return the on-disk root for *project*, creating it if needed."""
    if not project or project == "root":
        root = WORKSPACE_ROOT
    else:
        project = project.strip().replace("\\", "/")
        if project.startswith("/"):
            project = project.lstrip("/")
        safe_name = Path(project)
        if ".." in safe_name.parts:
            raise ValueError("Project name may not contain parent traversal")
        root = WORKSPACE_ROOT / safe_name
    root.mkdir(parents=True, exist_ok=True)
    return ensure_within_workspace(root)


def safe_project_path(project: str | None, relative_path: str | Path) -> Path:
    """Return the absolute path for *relative_path* inside *project* root."""
    base = get_project_root(project)
    candidate = ensure_within_workspace(base / Path(relative_path))
    try:
        candidate.relative_to(base)
    except ValueError as exc:
        raise ValueError("Path escapes project root") from exc
    return candidate


def to_workspace_relative(path: Path) -> str:
    """Return POSIX-style path relative to the workspace root."""
    rel = path.resolve().relative_to(WORKSPACE_ROOT)
    return rel.as_posix()

