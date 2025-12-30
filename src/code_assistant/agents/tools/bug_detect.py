"""Bug detection tool."""

from pathlib import Path
from typing import Any

from langchain.tools import BaseTool
from pydantic import Field

from code_assistant.embeddings import EmbeddingService


class BugDetectTool(BaseTool):
    """Tool for analyzing code for potential bugs."""

    name: str = "bug_detect"
    description: str = """Analyze code for potential bugs and issues.
    Input should be a file path to analyze.
    Example: "src/utils/helpers.py"
    """
    
    embedding_service: EmbeddingService = Field(exclude=True)

    def __init__(self, embedding_service: EmbeddingService, **kwargs: Any):
        """Initialize with embedding service."""
        super().__init__(embedding_service=embedding_service, **kwargs)

    def _run(self, file_path: str) -> str:
        """Get file content for bug analysis."""
        # Get all chunks from the file
        results = self.embedding_service.store.get_by_file(file_path)
        
        if not results:
            # Try searching
            results = self.embedding_service.search(file_path, n_results=10)
            results = [
                r for r in results 
                if file_path in r.get("metadata", {}).get("file_path", "")
            ]
        
        if not results:
            return f"Could not find file or code: {file_path}"
        
        output_parts = [f"File: {file_path}\n\nCode elements to analyze:\n"]
        
        for result in results:
            metadata = result.get("metadata", {})
            content = result.get("content", "")
            
            output_parts.append(
                f"\n--- {metadata.get('chunk_type', 'code').title()}: "
                f"{metadata.get('name', 'unknown')} ---\n"
                f"Lines: {metadata.get('start_line', '?')}-{metadata.get('end_line', '?')}\n"
                f"\n{content}\n"
            )
        
        output_parts.append(
            "\nAnalyze the above code for:\n"
            "1. Logic errors\n"
            "2. Null/None handling issues\n"
            "3. Resource leaks\n"
            "4. Error handling gaps\n"
            "5. Security vulnerabilities\n"
            "6. Performance issues\n"
        )
        
        return "".join(output_parts)

    async def _arun(self, file_path: str) -> str:
        """Async version."""
        return self._run(file_path)


class GetFileContentTool(BaseTool):
    """Tool for getting raw file content."""

    name: str = "get_file_content"
    description: str = """Get the raw content of a source file.
    Input should be the absolute or relative file path.
    """
    
    base_path: Path = Field(default=Path("."))

    def __init__(self, base_path: Path | str = ".", **kwargs: Any):
        """Initialize with base path."""
        super().__init__(base_path=Path(base_path), **kwargs)

    def _run(self, file_path: str) -> str:
        """Get file content."""
        try:
            path = Path(file_path)
            if not path.is_absolute():
                path = self.base_path / path
            
            if not path.exists():
                return f"File not found: {file_path}"
            
            content = path.read_text(encoding="utf-8")
            
            # Add line numbers
            lines = content.splitlines()
            numbered_lines = [
                f"{i:4d} | {line}" for i, line in enumerate(lines, 1)
            ]
            
            return (
                f"File: {file_path}\n"
                f"Lines: {len(lines)}\n\n"
                + "\n".join(numbered_lines)
            )
            
        except Exception as e:
            return f"Error reading file: {e}"

    async def _arun(self, file_path: str) -> str:
        """Async version."""
        return self._run(file_path)
