"""Code analyzer service."""

import logging
from pathlib import Path
from typing import Any

from code_assistant.agents import CodeAssistantAgent
from code_assistant.sandbox import DockerSandbox

logger = logging.getLogger(__name__)


class CodeAnalyzer:
    """High-level service for code analysis operations."""

    def __init__(
        self,
        base_path: Path | str = ".",
        agent: CodeAssistantAgent | None = None,
    ):
        """
        Initialize code analyzer.

        Args:
            base_path: Base path for the codebase.
            agent: Optional pre-configured agent.
        """
        self._base_path = Path(base_path)
        self._agent = agent or CodeAssistantAgent(base_path=self._base_path)
        self._sandbox = DockerSandbox()

    @property
    def agent(self) -> CodeAssistantAgent:
        """Get the underlying agent."""
        return self._agent

    @property
    def sandbox(self) -> DockerSandbox:
        """Get the sandbox."""
        return self._sandbox

    def index_codebase(
        self,
        directory: Path | str | None = None,
        exclude_patterns: list[str] | None = None,
    ) -> dict[str, int]:
        """
        Index the codebase.

        Args:
            directory: Directory to index. Defaults to base path.
            exclude_patterns: Patterns to exclude.

        Returns:
            Indexing results.
        """
        return self._agent.index_codebase(directory, exclude_patterns)

    async def explain(self, target: str) -> dict[str, Any]:
        """
        Explain a code element.

        Args:
            target: Name of the code element.

        Returns:
            Explanation result.
        """
        explanation = await self._agent.explain(target)
        return {
            "target": target,
            "explanation": explanation,
        }

    async def debug(self, file_path: str) -> dict[str, Any]:
        """
        Analyze file for bugs.

        Args:
            file_path: File to analyze.

        Returns:
            Debug report.
        """
        report = await self._agent.debug(file_path)
        return {
            "file": file_path,
            "report": report,
        }

    async def refactor(self, target: str) -> dict[str, Any]:
        """
        Get refactoring suggestions.

        Args:
            target: Code or file to refactor.

        Returns:
            Refactoring suggestions.
        """
        suggestions = await self._agent.suggest_refactoring(target)
        return {
            "target": target,
            "suggestions": suggestions,
        }

    async def generate_tests(self, target: str) -> dict[str, Any]:
        """
        Generate tests for a code element.

        Args:
            target: Name of the code element.

        Returns:
            Generated tests.
        """
        tests = await self._agent.generate_tests(target)
        return {
            "target": target,
            "tests": tests,
        }

    async def chat(
        self,
        message: str,
        history: list[tuple[str, str]] | None = None,
    ) -> str:
        """
        Chat with the assistant.

        Args:
            message: User message.
            history: Conversation history.

        Returns:
            Assistant response.
        """
        return await self._agent.chat(message, history)

    def execute_code(self, code: str) -> dict[str, Any]:
        """
        Execute code in sandbox.

        Args:
            code: Code to execute.

        Returns:
            Execution result.
        """
        if not self._sandbox.is_available:
            return {
                "success": False,
                "error": "Docker sandbox not available",
            }

        result = self._sandbox.execute_code(code)
        return {
            "success": result.success,
            "output": result.output,
            "error": result.error,
            "exit_code": result.exit_code,
        }

    def search(
        self,
        query: str,
        n_results: int = 10,
    ) -> list[dict[str, Any]]:
        """
        Search the codebase.

        Args:
            query: Search query.
            n_results: Number of results.

        Returns:
            Search results.
        """
        return self._agent.search(query, n_results)
