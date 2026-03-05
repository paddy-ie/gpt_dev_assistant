from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import shutil
from typing import List

from utils.paths import (
    WORKSPACE_ROOT,
    ensure_within_workspace,
    get_project_root,
    safe_project_path,
)

IGNORED_NAMES = {"__pycache__"}


@dataclass(slots=True)
class FileNode:
    name: str
    path: str
    type: str  # "file" | "dir"
    children: List["FileNode"] | None = None

    def to_dict(self) -> dict:
        data = {"name": self.name, "path": self.path, "type": self.type}
        if self.children is not None:
            data["children"] = [child.to_dict() for child in self.children]
        return data


def list_projects() -> list[str]:
    names = {"root"}
    for item in WORKSPACE_ROOT.iterdir():
        if item.is_dir():
            names.add(item.name)
    return sorted(names)


def create_project(name: str) -> str:
    cleaned = name.strip().replace("\\", "/")
    if not cleaned:
        raise ValueError("Project name is required")
    if cleaned.startswith("/"):
        cleaned = cleaned.lstrip("/")
    safe_name = Path(cleaned)
    if safe_name.name == "" or safe_name.name in {".", ".."}:
        raise ValueError("Invalid project name")
    if ".." in safe_name.parts:
        raise ValueError("Project name may not contain '..'")
    target = ensure_within_workspace(WORKSPACE_ROOT / safe_name)
    if target.exists():
        raise FileExistsError(cleaned)
    target.mkdir(parents=True, exist_ok=False)
    return safe_name.as_posix()


def delete_project(name: str) -> None:
    if name in {"root", "", ".", ".."}:
        raise ValueError("Cannot delete the root workspace")
    target = ensure_within_workspace(WORKSPACE_ROOT / Path(name))
    if not target.exists():
        raise FileNotFoundError(name)
    shutil.rmtree(target)


def _walk(root: Path, current: Path) -> list[FileNode]:
    nodes: list[FileNode] = []
    try:
        entries = sorted(current.iterdir(), key=lambda p: (p.is_file(), p.name.lower()))
    except FileNotFoundError:
        return []
    for entry in entries:
        if entry.name in IGNORED_NAMES:
            continue
        rel_path = entry.relative_to(root).as_posix()
        if entry.is_dir():
            children = _walk(root, entry)
            nodes.append(FileNode(name=entry.name, path=rel_path, type="dir", children=children))
        else:
            nodes.append(FileNode(name=entry.name, path=rel_path, type="file"))
    return nodes


def project_tree(project: str | None) -> dict:
    root = get_project_root(project)
    nodes = _walk(root, root)
    return {"project": project or "root", "nodes": [node.to_dict() for node in nodes]}


def read_file(project: str | None, relative_path: str) -> str:
    file_path = safe_project_path(project, relative_path)
    if not file_path.exists():
        raise FileNotFoundError(relative_path)
    if file_path.is_dir():
        raise IsADirectoryError(relative_path)
    return file_path.read_text(encoding="utf-8")


def write_file(project: str | None, relative_path: str, content: str) -> None:
    file_path = safe_project_path(project, relative_path)
    file_path.parent.mkdir(parents=True, exist_ok=True)
    file_path.write_text(content, encoding="utf-8")


def create_entry(project: str | None, relative_path: str, entry_type: str) -> None:
    target = safe_project_path(project, relative_path)
    if target.exists():
        raise FileExistsError(relative_path)
    if entry_type == "dir":
        target.mkdir(parents=True, exist_ok=True)
    else:
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text("", encoding="utf-8")


def rename_entry(project: str | None, old_path: str, new_path: str) -> None:
    src = safe_project_path(project, old_path)
    dst = safe_project_path(project, new_path)
    if not src.exists():
        raise FileNotFoundError(old_path)
    if dst.exists():
        raise FileExistsError(new_path)
    dst.parent.mkdir(parents=True, exist_ok=True)
    src.rename(dst)


def delete_entry(project: str | None, relative_path: str, recursive: bool = False) -> None:
    target = safe_project_path(project, relative_path)
    if not target.exists():
        raise FileNotFoundError(relative_path)
    if target.is_dir():
        if recursive:
            shutil.rmtree(target)
        else:
            target.rmdir()
    else:
        target.unlink()

