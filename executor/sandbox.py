from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path
import subprocess
import sys
import tempfile
from typing import Callable, Optional

from utils.paths import get_project_root, safe_project_path

try:  # pragma: no cover - platform guard
    import resource
except ImportError:  # pragma: no cover - Windows
    resource = None


DEFAULT_TIMEOUT = int(os.environ.get("IDE_EXEC_TIMEOUT", "5"))
DEFAULT_MEMORY_LIMIT_MB = int(os.environ.get("IDE_EXEC_MEMORY_MB", "256"))


@dataclass(slots=True)
class SandboxResult:
    stdout: str
    stderr: str
    returncode: Optional[int]
    timed_out: bool
    script_path: str


@dataclass(slots=True)
class _TempScript:
    path: Path
    cleanup: Callable[[], None]


def _limit_resources() -> None:
    if resource is None:
        return
    cpu_seconds = float(os.environ.get("IDE_EXEC_CPU_SECONDS", DEFAULT_TIMEOUT))
    mem_bytes = DEFAULT_MEMORY_LIMIT_MB * 1024 * 1024
    try:
        resource.setrlimit(resource.RLIMIT_CPU, (cpu_seconds, cpu_seconds))
        resource.setrlimit(resource.RLIMIT_AS, (mem_bytes, mem_bytes))
    except ValueError:
        pass


def _prepare_temp_script(root: Path, code: str, hint: str | None) -> _TempScript:
    temp_dir = tempfile.TemporaryDirectory(dir=root)
    filename = Path(hint).name if hint else "snippet.py"
    script_path = Path(temp_dir.name) / filename
    script_path.write_text(code, encoding="utf-8")
    return _TempScript(path=script_path, cleanup=temp_dir.cleanup)


def execute_python(
    *,
    project: str | None,
    path: str | None = None,
    code: str | None = None,
    timeout: Optional[int] = None,
) -> SandboxResult:
    if path is None and code is None:
        raise ValueError("Either 'path' or 'code' must be provided")

    root = get_project_root(project)
    timeout = timeout or DEFAULT_TIMEOUT

    temp_script: Optional[_TempScript] = None

    if code is not None:
        temp_script = _prepare_temp_script(root, code, path)
        script_path = temp_script.path
    else:
        script_path = safe_project_path(project, path or "")

    cmd = [sys.executable, "-I", script_path.as_posix()]
    env = os.environ.copy()
    env.update({"PYTHONUNBUFFERED": "1", "PYTHONPATH": root.as_posix()})

    preexec = _limit_resources if os.name != "nt" else None

    try:
        completed = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=root,
            env=env,
            preexec_fn=preexec,
            check=False,
        )
        relative = _relative_to_root(script_path, root)
        result = SandboxResult(
            stdout=completed.stdout,
            stderr=completed.stderr,
            returncode=completed.returncode,
            timed_out=False,
            script_path=relative,
        )
    except subprocess.TimeoutExpired as exc:
        relative = _relative_to_root(script_path, root)
        result = SandboxResult(
            stdout=(exc.stdout or ""),
            stderr=(exc.stderr or ""),
            returncode=None,
            timed_out=True,
            script_path=relative,
        )
    finally:
        if temp_script is not None:
            temp_script.cleanup()

    if result.stdout and len(result.stdout) > 200_000:
        result.stdout = result.stdout[:200_000] + "\n... output truncated ...\n"
    if result.stderr and len(result.stderr) > 200_000:
        result.stderr = result.stderr[:200_000] + "\n... output truncated ...\n"
    return result


def _relative_to_root(path: Path, root: Path) -> str:
    try:
        return path.resolve().relative_to(root).as_posix()
    except ValueError:
        return path.as_posix()

