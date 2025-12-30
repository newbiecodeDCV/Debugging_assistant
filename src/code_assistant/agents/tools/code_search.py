"""Code search tool using vector store."""

from typing import Any

from langchain.tools import BaseTool
from pydantic import Field

from code_assistant.embeddings import EmbeddingService


class CodeSearchTool(BaseTool):
    """Tool for searching code in the indexed codebase."""

    name: str = "code_search"
    description: str = """Search for relevant code in the codebase.
    Use this to find functions, classes, or code related to a specific topic or functionality.
    Input should be a natural language description of what you're looking for.
    """
    
    embedding_service: EmbeddingService = Field(exclude=True)

    def __init__(self, embedding_service: EmbeddingService, **kwargs: Any):
        """Initialize with embedding service."""
        super().__init__(embedding_service=embedding_service, **kwargs)

    def _run(self, query: str) -> str:
        """Execute the search."""
        results = self.embedding_service.search(query, n_results=5)
        
        if not results:
            return "No relevant code found for the query."
        
        output_parts = [f"Found {len(results)} relevant code snippets:\n"]
        
        for i, result in enumerate(results, 1):
            metadata = result.get("metadata", {})
            content = result.get("content", "")
            
            output_parts.append(
                f"\n--- Result {i} ---\n"
                f"Type: {metadata.get('chunk_type', 'unknown')}\n"
                f"Name: {metadata.get('qualified_name', 'unknown')}\n"
                f"File: {metadata.get('file_path', 'unknown')}\n"
                f"Lines: {metadata.get('start_line', '?')}-{metadata.get('end_line', '?')}\n"
                f"\n{content[:1000]}{'...' if len(content) > 1000 else ''}\n"
            )
        
        return "".join(output_parts)

    async def _arun(self, query: str) -> str:
        """Async version - just calls sync."""
        return self._run(query)


class CodeSearchByTypeTool(BaseTool):
    """Tool for searching specific types of code."""

    name: str = "code_search_by_type"
    description: str = """Search for specific types of code elements.
    Input format: "type:query" where type is one of: function, class, method, module.
    Example: "function:calculate sum" or "class:data processor"
    """
    
    embedding_service: EmbeddingService = Field(exclude=True)

    def __init__(self, embedding_service: EmbeddingService, **kwargs: Any):
        """Initialize with embedding service."""
        super().__init__(embedding_service=embedding_service, **kwargs)

    def _run(self, input_str: str) -> str:
        """Execute the typed search."""
        # Parse input
        if ":" not in input_str:
            return "Invalid format. Use 'type:query' format."
        
        chunk_type, query = input_str.split(":", 1)
        chunk_type = chunk_type.strip().lower()
        query = query.strip()
        
        valid_types = {"function", "class", "method", "module"}
        if chunk_type not in valid_types:
            return f"Invalid type. Must be one of: {', '.join(valid_types)}"
        
        results = self.embedding_service.search(
            query, n_results=5, chunk_type=chunk_type
        )
        
        if not results:
            return f"No {chunk_type}s found matching '{query}'."
        
        output_parts = [f"Found {len(results)} {chunk_type}(s):\n"]
        
        for i, result in enumerate(results, 1):
            metadata = result.get("metadata", {})
            content = result.get("content", "")
            
            output_parts.append(
                f"\n--- {chunk_type.title()} {i} ---\n"
                f"Name: {metadata.get('qualified_name', 'unknown')}\n"
                f"File: {metadata.get('file_path', 'unknown')}\n"
                f"\n{content[:800]}{'...' if len(content) > 800 else ''}\n"
            )
        
        return "".join(output_parts)

    async def _arun(self, input_str: str) -> str:
        """Async version."""
        return self._run(input_str)
