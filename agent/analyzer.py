
from __future__ import annotations

import json
import logging
from pathlib import Path

from config import ANALYZABLE_EXTENSIONS, MAX_FILES_TO_READ
from agent.explorer import RepositoryScan
from models.plan import RepositoryAnalysis

logger = logging.getLogger(__name__)

_FRAMEWORK_DEPENDENCIES = {
    "express": "Express",
    "fastify": "Fastify",
    "koa": "Koa",
    "next": "Next.js",
    "@nestjs/core": "NestJS",
}

_DATABASE_DEPENDENCIES = {
    "mongoose": "MongoDB (Mongoose)",
    "mongodb": "MongoDB",
    "pg": "PostgreSQL",
    "mysql": "MySQL",
    "mysql2": "MySQL",
    "sequelize": "SQL (Sequelize)",
    "sqlite3": "SQLite",
    "lowdb": "lowdb (file-based JSON)",
}

_ROLE_KEYWORDS = {
    "models": "models",
    "model": "models",
    "controllers": "controllers",
    "controller": "controllers",
    "routes": "routes",
    "router": "routes",
    "config": "config_files",
}


class RepositoryAnalyzer:
    """Turns a RepositoryScan into a structured RepositoryAnalysis."""

    def analyze(self, scan: RepositoryScan) -> RepositoryAnalysis:
        package_json = self._read_package_json(scan.root)
        framework, database = self._detect_stack(package_json)
        entry_point = self._detect_entry_point(scan.root, package_json)
        role_buckets = self._bucket_by_role(scan.files)

        analysis = RepositoryAnalysis(
            framework=framework,
            database=database,
            entry_point=entry_point,
            models=role_buckets["models"],
            controllers=role_buckets["controllers"],
            routes=role_buckets["routes"],
            config_files=role_buckets["config_files"],
            notes=self._build_notes(scan),
        )
        logger.info(
            "Analysis complete: framework=%s, %d routes, %d models, %d controllers",
            analysis.framework,
            len(analysis.routes),
            len(analysis.models),
            len(analysis.controllers),
        )
        return analysis

    @staticmethod
    def _read_package_json(root: Path) -> dict:
        package_path = root / "package.json"
        if not package_path.is_file():
            return {}
        try:
            return json.loads(package_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            logger.warning("package.json is not valid JSON, skipping dependency detection")
            return {}

    @staticmethod
    def _detect_stack(package_json: dict) -> tuple[str, str]:
        dependencies = {
            **package_json.get("dependencies", {}),
            **package_json.get("devDependencies", {}),
        }
        framework = "Node.js (no framework detected)"
        for dep_name, label in _FRAMEWORK_DEPENDENCIES.items():
            if dep_name in dependencies:
                framework = label
                break

        database = "unknown"
        for dep_name, label in _DATABASE_DEPENDENCIES.items():
            if dep_name in dependencies:
                database = label
                break
        return framework, database

    @staticmethod
    def _detect_entry_point(root: Path, package_json: dict) -> str:
        main_field = package_json.get("main")
        if main_field and (root / main_field).is_file():
            return main_field

        start_script = package_json.get("scripts", {}).get("start", "")
        for token in start_script.split():
            if token.endswith(".js") and (root / token).is_file():
                return token

        for candidate in ("server.js", "app.js", "index.js", "src/index.js"):
            if (root / candidate).is_file():
                return candidate
        return "unknown"

    @staticmethod
    def _bucket_by_role(files: list[Path]) -> dict[str, list[str]]:
        buckets: dict[str, list[str]] = {"models": [], "controllers": [], "routes": [], "config_files": []}
        for file_path in files:
            if file_path.suffix not in ANALYZABLE_EXTENSIONS:
                continue
            role = _match_role(file_path)
            if role:
                buckets[role].append(str(file_path))
        return buckets

    @staticmethod
    def _build_notes(scan: RepositoryScan) -> str:
        files_read = min(len(scan.files), MAX_FILES_TO_READ)
        return f"Scanned {len(scan.files)} files, considered {files_read} for role detection."


def _match_role(file_path: Path) -> str | None:
    """Match a file to a role based on its containing directory or filename."""
    lowercase_parts = [part.lower() for part in file_path.parts]
    for keyword, role in _ROLE_KEYWORDS.items():
        if keyword in lowercase_parts:
            return role
    stem = file_path.stem.lower()
    for keyword, role in _ROLE_KEYWORDS.items():
        if keyword in stem:
            return role
    return None
