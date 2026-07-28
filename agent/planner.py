
from __future__ import annotations

import logging

from llm.client import LLMClient
from models.plan import ImplementationPlan, RepositoryAnalysis
from prompts import PLANNER_SYSTEM_PROMPT, PLANNER_USER_TEMPLATE

logger = logging.getLogger(__name__)


class Planner:
    """Produces an ImplementationPlan from analysis + request via the LLM."""

    def __init__(self, llm_client: LLMClient) -> None:
        self._llm_client = llm_client

    def create_plan(self, analysis: RepositoryAnalysis, tree: str, request: str) -> ImplementationPlan:
        user_prompt = PLANNER_USER_TEMPLATE.format(
            analysis_json=analysis.model_dump_json(indent=2),
            tree=tree,
            request=request,
        )
        raw_plan = self._llm_client.complete_json(PLANNER_SYSTEM_PROMPT, user_prompt)
        plan = ImplementationPlan.model_validate(raw_plan)
        logger.info("Plan created: %d files to modify, %d steps", len(plan.files_to_modify), len(plan.steps))
        return plan
