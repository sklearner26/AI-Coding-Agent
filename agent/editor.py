

from __future__ import annotations

import logging
from pathlib import Path

from config import MAX_FILE_CHARS_FOR_PROMPT
from llm.client import LLMClient, _strip_code_fences
from models.plan import FileEdit, ImplementationPlan
from prompts import EDITOR_SYSTEM_PROMPT, EDITOR_USER_TEMPLATE
from tools.filesystem import read_text, write_text

logger = logging.getLogger(__name__)


class EditValidationError(RuntimeError):
    """Raised when an LLM edit response fails basic sanity checks."""


class Editor:
    """Applies an ImplementationPlan's file changes via the LLM."""

    def __init__(self, llm_client: LLMClient) -> None:
        self._llm_client = llm_client

    def apply_plan(self, root: Path, plan: ImplementationPlan, request: str, summary: str) -> list[FileEdit]:
        edits: list[FileEdit] = []
        for relative_path in plan.files_to_modify:
            edit = self._edit_file(root, relative_path, plan, request, summary)
            if edit is not None:
                edits.append(edit)
        return edits

    def _edit_file(
        self, root: Path, relative_path: str, plan: ImplementationPlan, request: str, summary: str
    ) -> FileEdit | None:
        try:
            original_content = read_text(root, relative_path)
        except FileNotFoundError:
            logger.warning("Skipping %s: file does not exist", relative_path)
            return None

        prompt = EDITOR_USER_TEMPLATE.format(
            summary=summary,
            path=relative_path,
            content=original_content[:MAX_FILE_CHARS_FOR_PROMPT],
            request=request,
            steps="\n".join(f"- {step}" for step in plan.steps),
        )
        updated_content = self._llm_client.complete(EDITOR_SYSTEM_PROMPT, prompt)
        updated_content = _strip_code_fences(updated_content)

        self._validate(relative_path, original_content, updated_content)
        write_text(root, relative_path, updated_content)
        logger.info("Updated %s", relative_path)
        return FileEdit(path=relative_path, original_content=original_content, updated_content=updated_content)

    @staticmethod
    def _validate(relative_path: str, original_content: str, updated_content: str) -> None:
        if not updated_content.strip():
            raise EditValidationError(f"LLM returned empty content for {relative_path}")
        if len(updated_content) < len(original_content) * 0.3:
            raise EditValidationError(
                f"LLM response for {relative_path} looks truncated ({len(updated_content)} chars)"
            )
