
from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path

from tools.filesystem import iter_repo_files

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class RepositoryScan:
    """Raw result of scanning a repository: file list and a rendered tree."""

    root: Path
    files: list[Path]
    tree: str


class RepositoryExplorer:
    """Scans a repository directory into a `RepositoryScan`."""

    def scan(self, root: Path) -> RepositoryScan:
        files = iter_repo_files(root)
        logger.info("Discovered %d files under %s", len(files), root)
        tree = self._render_tree(files)
        return RepositoryScan(root=root, files=files, tree=tree)

    @staticmethod
    def _render_tree(files: list[Path]) -> str:
        """Render a flat, sorted indented tree from relative file paths."""
        lines: list[str] = []
        seen_dirs: set[str] = set()
        for file_path in files:
            parts = file_path.parts
            for depth in range(len(parts) - 1):
                dir_key = "/".join(parts[: depth + 1])
                if dir_key in seen_dirs:
                    continue
                seen_dirs.add(dir_key)
                lines.append(f"{'  ' * depth}{parts[depth]}/")
            lines.append(f"{'  ' * (len(parts) - 1)}{parts[-1]}")
        return "\n".join(lines)
