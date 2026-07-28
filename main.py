

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(override=True) 

from agent.workflow import AgentWorkflow
from config import LLM_ENDPOINT, LLM_PROVIDER, LLMSettings, WORKSPACE_DIR
from llm.client import LLMClient, LLMError
from tools.git_tools import RepositoryError, resolve_repository

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="AI Coding Agent")
    parser.add_argument("--repo", help="Local path or GitHub URL of the target repository")
    parser.add_argument("--request", help="Natural language description of the desired change")
    return parser.parse_args(argv)


def load_llm_client() -> LLMClient:
    """Load model/API key from environment and fail fast with a clear error."""
    settings = LLMSettings.from_env()
    try:
        client = LLMClient(settings)  
    except RuntimeError as exc:
        raise LLMError(str(exc)) from exc
    logger.info(
        "LLM Provider : %s\n"
        "Model        : %s\n"
        "Endpoint     : OpenAI Compatible API\n",
        LLM_PROVIDER,
        settings.model,
        
    )
    return client


def prompt_repo_url() -> str:
    repo_url = input("Enter the GitHub repository URL: ").strip()
    if not repo_url:
        raise RepositoryError("No repository URL was provided")
    return repo_url


def prompt_request() -> str:
    request = input("What should the agent implement? ").strip()
    if not request:
        raise RepositoryError("No feature request was provided")
    return request


def run_interactive() -> int:
    try:
        llm_client = load_llm_client()
    except LLMError as exc:
        logger.error("LLM configuration error: %s", exc)
        return 1

    try:
        repo_arg = prompt_repo_url()
        repo_path = resolve_repository(repo_arg, Path(WORKSPACE_DIR))
        logger.info("Repository ready at %s", repo_path)
        request = prompt_request()
    except RepositoryError as exc:
        logger.error("Repository error: %s", exc)
        return 1

    return execute_pipeline(llm_client, repo_path, request)


def run_with_args(args: argparse.Namespace) -> int:
    try:
        llm_client = load_llm_client()
    except LLMError as exc:
        logger.error("LLM configuration error: %s", exc)
        return 1

    try:
        repo_path = resolve_repository(args.repo, Path(WORKSPACE_DIR))
    except RepositoryError as exc:
        logger.error("Repository error: %s", exc)
        return 1

    return execute_pipeline(llm_client, repo_path, args.request)


def execute_pipeline(llm_client: LLMClient, repo_path: Path, request: str) -> int:
    workflow = AgentWorkflow(llm_client)

    try:
        result = workflow.run(repo_path, request)
    except LLMError as exc:
        logger.error("LLM error: %s", exc)
        return 1
    except (FileNotFoundError, OSError) as exc:
        logger.error("Filesystem error: %s", exc)
        return 1

    logger.info("Done.")
    print("\n" + result.summary)
    return 0


def main(argv: list[str]) -> int:
    args = parse_args(argv)
    if args.repo and args.request:
        return run_with_args(args)
    return run_interactive()


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
