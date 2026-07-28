
from __future__ import annotations

import logging
from pathlib import Path

from config import IGNORED_DIRS, IGNORED_EXTENSIONS, IGNORED_FILES

logger = logging.getLogger(__name__)


def should_ignore(path: Path) -> bool:
    """Return True if a path lives inside an ignored dir or has an ignored type."""
    if any(part in IGNORED_DIRS for part in path.parts):
        return True
    if path.name in IGNORED_FILES:
        return True
    if path.suffix in IGNORED_EXTENSIONS:
        return True
    return False


def iter_repo_files(root: Path) -> list[Path]:
    """Return all non-ignored file paths under root, relative to root."""
    files: list[Path] = []
    for path in root.rglob("*"):
        if path.is_dir():
            continue
        relative = path.relative_to(root)
        if should_ignore(relative):
            continue
        files.append(relative)
    return sorted(files)


def read_text(root: Path, relative_path: str) -> str:
    """Read a file's text content, raising FileNotFoundError if missing."""
    full_path = root / relative_path
    if not full_path.is_file():
        raise FileNotFoundError(f"File not found: {relative_path}")
    return full_path.read_text(encoding="utf-8", errors="replace")


def write_text(root: Path, relative_path: str, content: str) -> None:
    """Overwrite a file's text content, creating parent dirs if needed."""
    full_path = root / relative_path
    full_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        full_path.write_text(content, encoding="utf-8")
    except OSError as exc:
        raise OSError(f"Failed to write {relative_path}: {exc}") from exc
