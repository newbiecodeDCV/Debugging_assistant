"""Code indexer service."""

import logging
from pathlib import Path
from typing import Any

from code_assistant.embeddings import EmbeddingService

logger = logging.getLogger(__name__)


class CodeIndexer:
    """Service for indexing codebases."""

    def __init__(self, embedding_service: EmbeddingService | None = None):
        """
        Initialize code indexer.

        Args:
            embedding_service: Optional embedding service.
        """
        self._embedding_service = embedding_service or EmbeddingService()

    @property
    def indexed_count(self) -> int:
        """Get number of indexed chunks."""
        return self._embedding_service.store.count

    def index_directory(
        self,
        directory: Path | str,
        exclude_patterns: list[str] | None = None,
    ) -> dict[str, Any]:
        """
        Index a directory.

        Args:
            directory: Directory to index.
            exclude_patterns: Patterns to exclude.

        Returns:
            Indexing statistics.
        """
        directory = Path(directory)

        if not directory.exists():
            raise ValueError(f"Directory does not exist: {directory}")

        results = self._embedding_service.index_directory(directory, exclude_patterns)

        stats = {
            "directory": str(directory),
            "files_indexed": len(results),
            "total_chunks": sum(results.values()),
            "files": results,
        }

        logger.info(
            f"Indexed {stats['files_indexed']} files with "
            f"{stats['total_chunks']} chunks"
        )

        return stats

    def index_file(self, file_path: Path | str) -> dict[str, Any]:
        """
        Index a single file.

        Args:
            file_path: File to index.

        Returns:
            Indexing statistics.
        """
        file_path = Path(file_path)

        if not file_path.exists():
            raise ValueError(f"File does not exist: {file_path}")

        count = self._embedding_service.index_file(file_path)

        return {
            "file": str(file_path),
            "chunks_indexed": count,
        }

    def clear_index(self) -> None:
        """Clear all indexed data."""
        self._embedding_service.store.clear()
        logger.info("Index cleared")

    def search(
        self,
        query: str,
        n_results: int = 10,
        chunk_type: str | None = None,
    ) -> list[dict[str, Any]]:
        """
        Search indexed code.

        Args:
            query: Search query.
            n_results: Number of results.
            chunk_type: Optional type filter.

        Returns:
            Search results.
        """
        return self._embedding_service.search(query, n_results, chunk_type)
