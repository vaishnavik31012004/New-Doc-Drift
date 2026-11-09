"""Three-stage Google ADK pipeline used by the scan worker.

The agents are created per scan so repository credentials never have to be put
into the LLM prompt. Repository-specific tools are closures over the scan's
owner/name/token and therefore the model only sees the tool results.
"""
import asyncio
from typing import Callable, Optional

from google.adk.agents import LlmAgent, SequentialAgent
from google.adk.runners import InMemoryRunner
from google.adk.tools import FunctionTool
from google.genai import types

from config import get_settings
from agents.tools import search_repo_docs, read_documentation_file, list_documentation_files

settings = get_settings()
APP_NAME = "doc_drift_guardian"


def _build_pipeline(repo_full_name: str, github_token: Optional[str]) -> SequentialAgent:
    owner, name = repo_full_name.split("/", 1)

    def read_doc(path: str) -> str:
        """Read the full current content of a documentation file in the connected repository."""
        return read_documentation_file(owner, name, path, github_token or "")

    def list_docs() -> str:
        """List documentation files in the connected repository."""
        return list_documentation_files(owner, name, github_token or "")

    def search_docs(query: str) -> str:
        """Semantically search the connected repository's indexed documentation."""
        return search_repo_docs(repo_full_name, query)

    diff_agent = LlmAgent(
        name="diff_analyzer",
        model=settings.adk_model,
        description="Explains the semantic meaning of a code change and its documentation impact.",
        instruction=(
            "You are a senior engineer reviewing a commit. You are given the commit "
            "message and raw file diffs. Summarize in plain language: "
            "(1) what behavior, API, configuration, or public interface changed; "
            "(2) whether it typically requires documentation changes or is purely internal. "
            "Be concise and name the actual files/functions/flags involved."
        ),
        output_key="diff_analysis",
    )

    doc_matcher_agent = LlmAgent(
        name="doc_matcher",
        model=settings.adk_model,
        description="Finds documentation that is stale relative to the code change.",
        instruction=(
            "A code change was just analyzed:\n\n{diff_analysis}\n\n"
            "Use the search_repo_docs tool to find documentation passages related to the change. "
            "Then decide, file by file, whether the documentation is inaccurate, incomplete, or "
            "missing. For every affected file output exactly:\n\n"
            "FILE: <path>\nSEVERITY: <low|medium|high>\n"
            "ISSUE: <one or two sentence explanation>\n\n"
            "If nothing is affected, output exactly NO_DRIFT_DETECTED."
        ),
        tools=[FunctionTool(search_docs)],
        output_key="drift_findings",
    )

    patch_writer_agent = LlmAgent(
        name="patch_writer",
        model=settings.adk_model,
        description="Drafts corrected documentation for each stale file.",
        instruction=(
            "The following documentation drift was found:\n\n{drift_findings}\n\n"
            "The original code change analysis was:\n\n{diff_analysis}\n\n"
            "If drift findings are NO_DRIFT_DETECTED, output exactly NO_PATCH_NEEDED. "
            "Otherwise, for each affected file, call read_documentation_file to obtain its "
            "current full content, then output a corrected full file in exactly this format:\n\n"
            "FILE: <path>\n```markdown\n<full corrected file content>\n```\n\n"
            "Preserve everything that remains accurate and only change stale parts."
        ),
        tools=[FunctionTool(read_doc), FunctionTool(list_docs)],
        output_key="doc_patch",
    )

    return SequentialAgent(
        name="doc_drift_guardian_pipeline",
        sub_agents=[diff_agent, doc_matcher_agent, patch_writer_agent],
    )


def run_pipeline_sync(
    repo_full_name: str,
    commit_message: str,
    diff_text: str,
    github_token: Optional[str] = None,
    on_progress: Optional[Callable[[str, str], None]] = None,
) -> dict:
    """Run the three ADK agents for one repository scan."""
    return asyncio.run(
        _run_pipeline_async(repo_full_name, commit_message, diff_text, github_token, on_progress)
    )


async def _run_pipeline_async(
    repo_full_name: str,
    commit_message: str,
    diff_text: str,
    github_token: Optional[str],
    on_progress: Optional[Callable[[str, str], None]],
) -> dict:
    pipeline_agent = _build_pipeline(repo_full_name, github_token)
    runner = InMemoryRunner(agent=pipeline_agent, app_name=APP_NAME)
    session = await runner.session_service.create_session(
        app_name=APP_NAME, user_id="doc-drift-guardian-user"
    )

    prompt = (
        f"Repository full_name: {repo_full_name}\n"
        f"Commit message: {commit_message}\n\n"
        f"Diff:\n{diff_text}"
    )

    outputs = {"diff_analyzer": "", "doc_matcher": "", "patch_writer": ""}
    last_author = None

    async for event in runner.run_async(
        user_id="doc-drift-guardian-user",
        session_id=session.id,
        new_message=types.Content(role="user", parts=[types.Part(text=prompt)]),
    ):
        author = getattr(event, "author", None)
        if author and author != last_author and on_progress:
            on_progress(author, "running")
            last_author = author

        if event.is_final_response() and event.content and event.content.parts:
            text = "".join(part.text or "" for part in event.content.parts)
            if author in outputs:
                outputs[author] = text
            if on_progress and author:
                on_progress(author, "done")

    return {
        "diff_analysis": outputs["diff_analyzer"],
        "drift_findings": outputs["doc_matcher"],
        "doc_patch": outputs["patch_writer"],
    }
