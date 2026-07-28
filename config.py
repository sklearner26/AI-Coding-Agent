"""Central configuration for the AI coding agent.

All tunables live here so no other module reaches into os.environ directly.
"""

from __future__ import annotations

import os
from dataclasses import dataclass

# ---------------------------------------------------------------------------
# Filesystem scan settings
# ---------------------------------------------------------------------------

IGNORED_DIRS = {
    "node_modules",
    ".git",
    "dist",
    "build",
    "coverage",
    "venv",
    "__pycache__",
}

IGNORED_EXTENSIONS = {
    ".png",
    ".jpg",
    ".jpeg",
    ".svg",
    ".ico",
    ".lock",
}

IGNORED_FILES = {
    ".env",
}

# Files the analyzer will actually open and read (source + config, not assets).
ANALYZABLE_EXTENSIONS = {
    ".js",
    ".jsx",
    ".ts",
    ".tsx",
    ".json",
    ".md",
    ".yml",
    ".yaml",
    ".env.example",
}

# Cap on how much of a single file's content is sent to the LLM.
MAX_FILE_CHARS_FOR_PROMPT = 6000

# Cap on how many candidate files the analyzer will read from disk.
MAX_FILES_TO_READ = 40

# Folder where remote repositories are cloned to (relative to cwd unless absolute).
WORKSPACE_DIR = os.environ.get("AGENT_WORKSPACE_DIR", ".")

# ---------------------------------------------------------------------------
# LLM / Groq settings
# ---------------------------------------------------------------------------

LLM_ENDPOINT = "https://api.groq.com/openai/v1"
LLM_PROVIDER = "Groq"
DEFAULT_MODEL = "llama-3.3-70b-versatile"

@dataclass(frozen=True)
class LLMSettings:
    """Groq API configuration (via OpenAI-compatible endpoint), read once at startup."""

    api_key: str
    model: str
    max_tokens: int = 4000
    temperature: float = 0.1

    # ------------------------------------------------------------------
    # Factory
    # ------------------------------------------------------------------

    @staticmethod
    def from_env() -> "LLMSettings":
        api_key = os.environ.get("GROQ_API_KEY", "")
        model = os.environ.get("GROQ_MODEL", DEFAULT_MODEL)
        max_tokens = int(os.environ.get("GROQ_MAX_TOKENS", "4000"))
        temperature = float(os.environ.get("GROQ_TEMPERATURE", "0.1"))
        return LLMSettings(
            api_key=api_key,
            model=model,
            max_tokens=max_tokens,
            temperature=temperature,
        )

    # ------------------------------------------------------------------
    # Validation
    # ------------------------------------------------------------------

    def validate(self) -> None:
        if not self.api_key:
            raise RuntimeError("GROQ_API_KEY is missing. Please set it in your .env file or environment.")


