

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path

from agent.analyzer import RepositoryAnalyzer
from agent.editor import Editor
from agent.explorer import RepositoryExplorer
from agent.planner import Planner
from agent.summarizer import Summarizer
from llm.client import LLMClient
from models.plan import FileEdit, ImplementationPlan, RepositoryAnalysis

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class WorkflowResult:
    """Everything produced by a full pipeline run, for CLI reporting."""

    analysis: RepositoryAnalysis
    plan: ImplementationPlan
    edits: list[FileEdit]
    summary: str


class AgentWorkflow:
    """Runs the full explore -> analyze -> plan -> edit -> summarize pipeline."""

    def __init__(self, llm_client: LLMClient) -> None:
        self._explorer = RepositoryExplorer()
        self._analyzer = RepositoryAnalyzer()
        self._planner = Planner(llm_client)
        self._editor = Editor(llm_client)
        self._summarizer = Summarizer()

    def run(self, root: Path, request: str) -> WorkflowResult:
        logger.info("Scanning repository...")
        scan = self._explorer.scan(root)

        logger.info("Analyzing project...")
        analysis = self._analyzer.analyze(scan)

        logger.info("Creating implementation plan...")
        plan = self._planner.create_plan(analysis, scan.tree, request)

        logger.info("Editing files...")
        edits = self._editor.apply_plan(root, plan, request, summary=analysis.notes)

        logger.info("Generating summary...")
        summary = self._summarizer.summarize(plan, edits)

        return WorkflowResult(analysis=analysis, plan=plan, edits=edits, summary=summary)
