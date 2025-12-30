"""Code explanation tool."""

from typing import Any

from langchain.tools import BaseTool
from pydantic import Field

from code_assistant.embeddings import EmbeddingService


class CodeExplainTool(BaseTool):
    """Tool for explaining code."""

    name: str = "code_explain"
    description: str = """Get detailed explanation of a code element.
    Input should be the name of a function, class, or method to explain.
    Example: "calculate_sum" or "DataProcessor.process"
    """
    
    embedding_service: EmbeddingService = Field(exclude=True)

    def __init__(self, embedding_service: EmbeddingService, **kwargs: Any):
        """Initialize with embedding service."""
        super().__init__(embedding_service=embedding_service, **kwargs)

    def _run(self, name: str) -> str:
        """Get code for explanation."""
        # Search for the code element
        results = self.embedding_service.search(name, n_results=3)
        
        if not results:
            return f"Could not find code element: {name}"
        
        # Find best match
        best_match = None
        for result in results:
            metadata = result.get("metadata", {})
            qualified_name = metadata.get("qualified_name", "")
            if name.lower() in qualified_name.lower():
                best_match = result
                break
        
        if not best_match:
            best_match = results[0]
        
        metadata = best_match.get("metadata", {})
        content = best_match.get("content", "")
        
        return (
            f"Code Element: {metadata.get('qualified_name', name)}\n"
            f"Type: {metadata.get('chunk_type', 'unknown')}\n"
            f"File: {metadata.get('file_path', 'unknown')}\n"
            f"Lines: {metadata.get('start_line', '?')}-{metadata.get('end_line', '?')}\n"
            f"\n{content}\n\n"
            "Use this code context to provide a detailed explanation."
        )

    async def _arun(self, name: str) -> str:
        """Async version."""
        return self._run(name)
