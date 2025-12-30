"""Embedding service for code indexing."""

import logging
from pathlib import Path
from typing import Any

from code_assistant.embeddings.chroma_store import ChromaStore
from code_assistant.models import CodeChunk, CodeFile
from code_assistant.parsers import PythonParser

logger = logging.getLogger(__name__)


class EmbeddingService:
    """Service for embedding and indexing code."""

    def __init__(self, store: ChromaStore | None = None):
        """
        Initialize embedding service.

        Args:
            store: Optional ChromaStore instance.
        """
        self._store = store or ChromaStore()
        self._parser = PythonParser()

    @property
    def store(self) -> ChromaStore:
        """Get the underlying vector store."""
        return self._store

    def index_file(self, file_path: Path, base_path: Path | None = None) -> int:
        """
        Index a single file.

        Args:
            file_path: Path to the file.
            base_path: Base path for relative paths.

        Returns:
            Number of chunks indexed.
        """
        if not self._parser.can_parse(file_path):
            logger.debug(f"Skipping non-Python file: {file_path}")
            return 0

        try:
            code_file = self._parser.parse_file(file_path, base_path)
            chunks = self._create_chunks(code_file)

            if chunks:
                # Delete old chunks for this file first
                self._store.delete_by_file(str(code_file.relative_path))
                self._store.add_chunks(chunks)

            logger.info(f"Indexed {len(chunks)} chunks from {file_path}")
            return len(chunks)

        except Exception as e:
            logger.error(f"Failed to index {file_path}: {e}")
            return 0

    def index_directory(
        self,
        directory: Path,
        exclude_patterns: list[str] | None = None,
    ) -> dict[str, int]:
        """
        Index all Python files in a directory.

        Args:
            directory: Directory to index.
            exclude_patterns: Glob patterns to exclude.

        Returns:
            Dictionary mapping file paths to chunk counts.
        """
        exclude_patterns = exclude_patterns or [
            "__pycache__",
            ".git",
            ".venv",
            "venv",
            "node_modules",
            ".egg-info",
        ]

        results: dict[str, int] = {}
        python_files = list(directory.rglob("*.py"))

        for file_path in python_files:
            # Check exclusions
            should_exclude = any(
                pattern in str(file_path) for pattern in exclude_patterns
            )
            if should_exclude:
                continue

            count = self.index_file(file_path, directory)
            results[str(file_path)] = count

        total = sum(results.values())
        logger.info(
            f"Indexed {len(results)} files with {total} total chunks from {directory}"
        )

        return results

    def _create_chunks(self, code_file: CodeFile) -> list[CodeChunk]:
        """
        Create code chunks from a parsed file.

        Args:
            code_file: Parsed code file.

        Returns:
            List of code chunks.
        """
        chunks: list[CodeChunk] = []
        file_path = str(code_file.relative_path)

        # Create chunk for module-level content
        if code_file.module_docstring:
            module_chunk = CodeChunk(
                id=ChromaStore.generate_chunk_id(file_path, "__module__", 1),
                content=self._format_module_content(code_file),
                file_path=file_path,
                chunk_type="module",
                name=code_file.path.stem,
                qualified_name=code_file.path.stem,
                start_line=1,
                end_line=10,  # Approximate
                metadata={"has_docstring": True},
            )
            chunks.append(module_chunk)

        # Create chunks for functions
        for func in code_file.functions:
            chunk = CodeChunk(
                id=ChromaStore.generate_chunk_id(
                    file_path, func.qualified_name, func.start_line
                ),
                content=self._format_function_content(func),
                file_path=file_path,
                chunk_type="function",
                name=func.name,
                qualified_name=func.qualified_name,
                start_line=func.start_line,
                end_line=func.end_line,
                metadata={
                    "is_async": func.is_async,
                    "has_docstring": func.docstring is not None,
                    "param_count": len(func.parameters),
                },
            )
            chunks.append(chunk)

        # Create chunks for classes
        for cls in code_file.classes:
            chunk = CodeChunk(
                id=ChromaStore.generate_chunk_id(
                    file_path, cls.qualified_name, cls.start_line
                ),
                content=self._format_class_content(cls),
                file_path=file_path,
                chunk_type="class",
                name=cls.name,
                qualified_name=cls.qualified_name,
                start_line=cls.start_line,
                end_line=cls.end_line,
                metadata={
                    "has_docstring": cls.docstring is not None,
                    "method_count": len(cls.methods),
                    "bases": ",".join(cls.bases),
                },
            )
            chunks.append(chunk)

            # Also create chunks for class methods
            for method in cls.methods:
                method_chunk = CodeChunk(
                    id=ChromaStore.generate_chunk_id(
                        file_path, method.qualified_name, method.start_line
                    ),
                    content=self._format_function_content(method),
                    file_path=file_path,
                    chunk_type="method",
                    name=method.name,
                    qualified_name=method.qualified_name,
                    start_line=method.start_line,
                    end_line=method.end_line,
                    metadata={
                        "is_async": method.is_async,
                        "has_docstring": method.docstring is not None,
                        "class_name": cls.name,
                    },
                )
                chunks.append(method_chunk)

        return chunks

    def _format_module_content(self, code_file: CodeFile) -> str:
        """Format module content for embedding."""
        parts = [
            f"Module: {code_file.path.stem}",
            f"File: {code_file.relative_path}",
        ]

        if code_file.module_docstring:
            parts.append(f"Description: {code_file.module_docstring}")

        if code_file.imports:
            imports = [imp.module for imp in code_file.imports[:10]]
            parts.append(f"Imports: {', '.join(imports)}")

        if code_file.functions:
            funcs = [f.name for f in code_file.functions[:10]]
            parts.append(f"Functions: {', '.join(funcs)}")

        if code_file.classes:
            classes = [c.name for c in code_file.classes[:10]]
            parts.append(f"Classes: {', '.join(classes)}")

        return "\n".join(parts)

    def _format_function_content(self, func: Any) -> str:
        """Format function content for embedding."""
        parts = [
            f"Function: {func.name}",
            f"Signature: {func.signature}",
        ]

        if func.docstring:
            parts.append(f"Description: {func.docstring}")

        parts.append(f"Source:\n{func.source_code}")

        return "\n".join(parts)

    def _format_class_content(self, cls: Any) -> str:
        """Format class content for embedding."""
        parts = [
            f"Class: {cls.name}",
        ]

        if cls.bases:
            parts.append(f"Inherits: {', '.join(cls.bases)}")

        if cls.docstring:
            parts.append(f"Description: {cls.docstring}")

        if cls.methods:
            methods = [m.name for m in cls.methods]
            parts.append(f"Methods: {', '.join(methods)}")

        parts.append(f"Source:\n{cls.source_code}")

        return "\n".join(parts)

    def search(
        self,
        query: str,
        n_results: int = 10,
        chunk_type: str | None = None,
    ) -> list[dict[str, Any]]:
        """
        Search for relevant code.

        Args:
            query: Search query.
            n_results: Number of results.
            chunk_type: Optional filter by chunk type.

        Returns:
            Search results.
        """
        if chunk_type:
            return self._store.search_by_type(query, chunk_type, n_results)
        return self._store.search(query, n_results)
