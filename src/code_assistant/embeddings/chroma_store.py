"""Chroma vector store integration."""

import hashlib
import logging
from pathlib import Path
from typing import Any

import chromadb
from chromadb.config import Settings as ChromaSettings

from code_assistant.config import get_settings
from code_assistant.models import CodeChunk

logger = logging.getLogger(__name__)


class ChromaStore:
    """Chroma vector store for code embeddings."""

    def __init__(
        self,
        persist_dir: Path | None = None,
        collection_name: str | None = None,
    ):
        """
        Initialize Chroma store.

        Args:
            persist_dir: Directory for persistence. Defaults to settings.
            collection_name: Collection name. Defaults to settings.
        """
        settings = get_settings()
        self._persist_dir = persist_dir or settings.chroma_persist_dir
        self._collection_name = collection_name or settings.chroma_collection_name

        # Ensure persist directory exists
        self._persist_dir.mkdir(parents=True, exist_ok=True)

        # Initialize Chroma client with persistence
        self._client = chromadb.PersistentClient(
            path=str(self._persist_dir),
            settings=ChromaSettings(
                anonymized_telemetry=False,
                allow_reset=True,
            ),
        )

        # Get or create collection with OpenAI embeddings
        self._collection = self._client.get_or_create_collection(
            name=self._collection_name,
            metadata={"description": "Code embeddings for assistant"},
        )

        logger.info(
            f"Initialized ChromaStore with collection '{self._collection_name}' "
            f"at '{self._persist_dir}'"
        )

    @property
    def count(self) -> int:
        """Return the number of documents in the collection."""
        return self._collection.count()

    def add_chunks(self, chunks: list[CodeChunk]) -> None:
        """
        Add code chunks to the vector store.

        Args:
            chunks: List of code chunks to add.
        """
        if not chunks:
            return

        ids = [chunk.id for chunk in chunks]
        documents = [chunk.content for chunk in chunks]
        metadatas = [
            {
                "file_path": chunk.file_path,
                "chunk_type": chunk.chunk_type,
                "name": chunk.name,
                "qualified_name": chunk.qualified_name,
                "start_line": chunk.start_line,
                "end_line": chunk.end_line,
                **chunk.metadata,
            }
            for chunk in chunks
        ]

        # Upsert to handle updates
        self._collection.upsert(
            ids=ids,
            documents=documents,
            metadatas=metadatas,
        )

        logger.debug(f"Added {len(chunks)} chunks to vector store")

    def search(
        self,
        query: str,
        n_results: int = 10,
        filter_dict: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        """
        Search for similar code chunks.

        Args:
            query: Search query.
            n_results: Number of results to return.
            filter_dict: Optional metadata filters.

        Returns:
            List of matching documents with metadata.
        """
        results = self._collection.query(
            query_texts=[query],
            n_results=n_results,
            where=filter_dict,
            include=["documents", "metadatas", "distances"],
        )

        # Format results
        matches: list[dict[str, Any]] = []
        if results["documents"] and results["documents"][0]:
            for i, doc in enumerate(results["documents"][0]):
                match = {
                    "content": doc,
                    "metadata": results["metadatas"][0][i] if results["metadatas"] else {},
                    "distance": results["distances"][0][i] if results["distances"] else 0,
                }
                matches.append(match)

        return matches

    def search_by_type(
        self,
        query: str,
        chunk_type: str,
        n_results: int = 5,
    ) -> list[dict[str, Any]]:
        """
        Search for chunks of a specific type.

        Args:
            query: Search query.
            chunk_type: Type of chunk (function, class, module).
            n_results: Number of results.

        Returns:
            Matching documents.
        """
        return self.search(
            query=query,
            n_results=n_results,
            filter_dict={"chunk_type": chunk_type},
        )

    def get_by_file(self, file_path: str) -> list[dict[str, Any]]:
        """
        Get all chunks from a specific file.

        Args:
            file_path: Path to the file.

        Returns:
            All chunks from the file.
        """
        results = self._collection.get(
            where={"file_path": file_path},
            include=["documents", "metadatas"],
        )

        chunks: list[dict[str, Any]] = []
        if results["documents"]:
            for i, doc in enumerate(results["documents"]):
                chunks.append({
                    "content": doc,
                    "metadata": results["metadatas"][i] if results["metadatas"] else {},
                })

        return chunks

    def delete_by_file(self, file_path: str) -> None:
        """
        Delete all chunks from a specific file.

        Args:
            file_path: Path to the file.
        """
        # Get IDs of documents to delete
        results = self._collection.get(
            where={"file_path": file_path},
        )

        if results["ids"]:
            self._collection.delete(ids=results["ids"])
            logger.debug(f"Deleted {len(results['ids'])} chunks for {file_path}")

    def clear(self) -> None:
        """Clear all documents from the collection."""
        self._client.delete_collection(self._collection_name)
        self._collection = self._client.create_collection(
            name=self._collection_name,
            metadata={"description": "Code embeddings for assistant"},
        )
        logger.info("Cleared vector store")

    @staticmethod
    def generate_chunk_id(file_path: str, name: str, start_line: int) -> str:
        """
        Generate a unique ID for a code chunk.

        Args:
            file_path: Path to the file.
            name: Name of the code element.
            start_line: Starting line number.

        Returns:
            Unique chunk ID.
        """
        content = f"{file_path}:{name}:{start_line}"
        return hashlib.sha256(content.encode()).hexdigest()[:16]
