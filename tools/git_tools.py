

from __future__ import annotations

import logging
import os
import shutil
import stat
import subprocess
from pathlib import Path

logger = logging.getLogger(__name__)


class RepositoryError(RuntimeError):
    """Raised when the target repository cannot be resolved."""


def is_remote_url(repo_arg: str) -> bool:
    return repo_arg.startswith(("http://", "https://", "git@"))


def resolve_repository(repo_arg: str, workspace_dir: Path) -> Path:
    """Return a local directory path for the given repo argument.

    Local paths are used as-is. Remote URLs are cloned into
    `workspace_dir/<repo-name>`.
    """
    if is_remote_url(repo_arg):
        return _clone_into_workspace(repo_arg, workspace_dir)

    local_path = Path(repo_arg).expanduser().resolve()
    if not local_path.is_dir():
        raise RepositoryError(f"Repository path does not exist: {local_path}")
    return local_path


def _repo_name_from_url(url: str) -> str:
    name = url.rstrip("/").rsplit("/", 1)[-1]
    return name[:-4] if name.endswith(".git") else name


def _clone_into_workspace(url: str, workspace_dir: Path) -> Path:
    workspace_dir.mkdir(parents=True, exist_ok=True)
    destination = workspace_dir / _repo_name_from_url(url)

    if destination.exists():
        logger.info("Removing existing folder %s before re-cloning", destination)
        _force_rmtree(destination)

    logger.info("Cloning %s into %s", url, destination)
    try:
        subprocess.run(
            ["git", "clone", "--depth", "1", url, str(destination)],
            check=True,
            capture_output=True,
            text=True,
            timeout=120,
        )
    except subprocess.CalledProcessError as exc:
        raise RepositoryError(f"git clone failed: {exc.stderr.strip()}") from exc
    except subprocess.TimeoutExpired as exc:
        raise RepositoryError(f"git clone timed out: {exc}") from exc
    return destination


def _force_rmtree(path: Path) -> None:
    """Delete a directory tree, handling Windows read-only files inside .git/."""

    def _on_error(func, fpath, exc_info):
        # Clear the read-only bit and retry.
        os.chmod(fpath, stat.S_IWRITE)
        func(fpath)

    shutil.rmtree(path, onerror=_on_error)
