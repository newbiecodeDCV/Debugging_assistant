"""Main code assistant agent using LangChain."""

import logging
from pathlib import Path
from typing import Any

from langchain.agents import AgentExecutor, create_react_agent
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_openai import ChatOpenAI

from code_assistant.agents.prompts import PROMPTS
from code_assistant.agents.tools.bug_detect import BugDetectTool, GetFileContentTool
from code_assistant.agents.tools.code_explain import CodeExplainTool
from code_assistant.agents.tools.code_search import CodeSearchByTypeTool, CodeSearchTool
from code_assistant.agents.tools.test_generator import TestGeneratorTool
from code_assistant.config import get_settings
from code_assistant.embeddings import ChromaStore, EmbeddingService
from code_assistant.models import (
    AnalysisResult,
    BugReport,
    ExplanationResult,
    RefactorSuggestion,
    TestGenerationResult,
)

logger = logging.getLogger(__name__)


class CodeAssistantAgent:
    """LangChain-based code assistant agent."""

    def __init__(
        self,
        base_path: Path | str = ".",
        embedding_service: EmbeddingService | None = None,
    ):
        """
        Initialize the code assistant agent.

        Args:
            base_path: Base path for the codebase.
            embedding_service: Optional pre-configured embedding service.
        """
        self._settings = get_settings()
        self._base_path = Path(base_path)

        # Initialize embedding service
        self._embedding_service = embedding_service or EmbeddingService()

        # Initialize LLM
        self._llm = ChatOpenAI(
            model=self._settings.openai_model,
            temperature=0,
            api_key=self._settings.openai_api_key,
        )

        # Initialize tools
        self._tools = self._create_tools()

        # Create prompt template
        self._prompt = self._create_prompt()

        # Create agent
        self._agent = create_react_agent(
            llm=self._llm,
            tools=self._tools,
            prompt=self._prompt,
        )

        # Create executor
        self._executor = AgentExecutor(
            agent=self._agent,
            tools=self._tools,
            verbose=self._settings.debug,
            handle_parsing_errors=True,
            max_iterations=10,
        )

        logger.info(f"Initialized CodeAssistantAgent with base path: {self._base_path}")

    def _create_tools(self) -> list:
        """Create agent tools."""
        return [
            CodeSearchTool(embedding_service=self._embedding_service),
            CodeSearchByTypeTool(embedding_service=self._embedding_service),
            CodeExplainTool(embedding_service=self._embedding_service),
            BugDetectTool(embedding_service=self._embedding_service),
            TestGeneratorTool(embedding_service=self._embedding_service),
            GetFileContentTool(base_path=self._base_path),
        ]

    def _create_prompt(self) -> ChatPromptTemplate:
        """Create the agent prompt template."""
        return ChatPromptTemplate.from_messages([
            ("system", PROMPTS["system"]),
            MessagesPlaceholder(variable_name="chat_history", optional=True),
            ("human", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad"),
        ])

    @property
    def embedding_service(self) -> EmbeddingService:
        """Get the embedding service."""
        return self._embedding_service

    def index_codebase(
        self,
        directory: Path | str | None = None,
        exclude_patterns: list[str] | None = None,
    ) -> dict[str, int]:
        """
        Index a codebase directory.

        Args:
            directory: Directory to index. Defaults to base path.
            exclude_patterns: Patterns to exclude.

        Returns:
            Dictionary of indexed files and chunk counts.
        """
        target_dir = Path(directory) if directory else self._base_path
        return self._embedding_service.index_directory(target_dir, exclude_patterns)

    async def explain(self, target: str) -> str:
        """
        Explain a code element.

        Args:
            target: Name of the function, class, or method to explain.

        Returns:
            Explanation text.
        """
        prompt = PROMPTS["explain"].format(
            target_name=target,
            target_type="code element",
            code="[Agent will retrieve the code]",
        )

        result = await self._executor.ainvoke({
            "input": f"Explain the code element '{target}'. First use the code_explain tool "
                     f"to get the code, then provide a detailed explanation."
        })

        return result.get("output", "No explanation generated.")

    async def debug(self, file_path: str) -> str:
        """
        Analyze a file for bugs.

        Args:
            file_path: Path to the file to analyze.

        Returns:
            Bug analysis report.
        """
        result = await self._executor.ainvoke({
            "input": f"Analyze the file '{file_path}' for potential bugs and issues. "
                     f"First use the bug_detect tool to get the code, then provide "
                     f"a detailed analysis of any bugs found."
        })

        return result.get("output", "No analysis generated.")

    async def suggest_refactoring(self, code_or_file: str) -> str:
        """
        Suggest refactoring improvements.

        Args:
            code_or_file: Code snippet or file path.

        Returns:
            Refactoring suggestions.
        """
        result = await self._executor.ainvoke({
            "input": f"Analyze '{code_or_file}' and suggest refactoring improvements. "
                     f"Look for code that could be simplified, made more Pythonic, "
                     f"or better organized."
        })

        return result.get("output", "No suggestions generated.")

    async def generate_tests(self, target: str) -> str:
        """
        Generate tests for a code element.

        Args:
            target: Name of the function or class.

        Returns:
            Generated test code.
        """
        result = await self._executor.ainvoke({
            "input": f"Generate comprehensive pytest tests for '{target}'. "
                     f"First use the test_generator tool to get the code context, "
                     f"then create tests covering normal operation, edge cases, and errors."
        })

        return result.get("output", "No tests generated.")

    async def chat(
        self,
        message: str,
        chat_history: list[tuple[str, str]] | None = None,
    ) -> str:
        """
        Interactive chat about the codebase.

        Args:
            message: User's question or request.
            chat_history: Optional conversation history as (user, assistant) tuples.

        Returns:
            Agent's response.
        """
        # Convert chat history to message format
        history = []
        if chat_history:
            for human, assistant in chat_history:
                history.append(HumanMessage(content=human))
                history.append(SystemMessage(content=assistant))

        result = await self._executor.ainvoke({
            "input": message,
            "chat_history": history,
        })

        return result.get("output", "No response generated.")

    def search(
        self,
        query: str,
        n_results: int = 10,
        chunk_type: str | None = None,
    ) -> list[dict[str, Any]]:
        """
        Search the indexed codebase.

        Args:
            query: Search query.
            n_results: Number of results.
            chunk_type: Optional filter by type.

        Returns:
            Search results.
        """
        return self._embedding_service.search(query, n_results, chunk_type)
