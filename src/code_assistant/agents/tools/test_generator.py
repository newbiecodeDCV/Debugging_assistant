"""Test generation tool."""

from typing import Any

from langchain.tools import BaseTool
from pydantic import Field

from code_assistant.embeddings import EmbeddingService


class TestGeneratorTool(BaseTool):
    """Tool for generating test cases."""

    name: str = "test_generator"
    description: str = """Get code context for test generation.
    Input should be the name of a function or class to generate tests for.
    Example: "calculate_total" or "UserService"
    """
    
    embedding_service: EmbeddingService = Field(exclude=True)

    def __init__(self, embedding_service: EmbeddingService, **kwargs: Any):
        """Initialize with embedding service."""
        super().__init__(embedding_service=embedding_service, **kwargs)

    def _run(self, name: str) -> str:
        """Get code context for test generation."""
        # Search for the code element
        results = self.embedding_service.search(name, n_results=5)
        
        if not results:
            return f"Could not find code element: {name}"
        
        # Find the best match
        target_result = None
        related_results = []
        
        for result in results:
            metadata = result.get("metadata", {})
            qualified_name = metadata.get("qualified_name", "")
            
            if name.lower() in qualified_name.lower():
                if target_result is None:
                    target_result = result
                else:
                    related_results.append(result)
            else:
                related_results.append(result)
        
        if target_result is None:
            target_result = results[0]
            related_results = results[1:]
        
        # Build output
        target_meta = target_result.get("metadata", {})
        target_content = target_result.get("content", "")
        
        output_parts = [
            f"Target for Test Generation:\n"
            f"Name: {target_meta.get('qualified_name', name)}\n"
            f"Type: {target_meta.get('chunk_type', 'unknown')}\n"
            f"File: {target_meta.get('file_path', 'unknown')}\n"
            f"\n```python\n{target_content}\n```\n"
        ]
        
        if related_results:
            output_parts.append("\nRelated Code (for context):\n")
            for result in related_results[:3]:
                meta = result.get("metadata", {})
                content = result.get("content", "")
                output_parts.append(
                    f"\n--- {meta.get('qualified_name', 'unknown')} ---\n"
                    f"{content[:500]}{'...' if len(content) > 500 else ''}\n"
                )
        
        output_parts.append(
            "\nGenerate comprehensive tests including:\n"
            "1. Normal operation tests\n"
            "2. Edge cases\n"
            "3. Error cases\n"
            "4. Use pytest style with descriptive test names\n"
        )
        
        return "".join(output_parts)

    async def _arun(self, name: str) -> str:
        """Async version."""
        return self._run(name)
