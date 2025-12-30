"""Tests for indexer service."""

from pathlib import Path

import pytest

from code_assistant.services import CodeIndexer


class TestCodeIndexer:
    """Tests for CodeIndexer service."""

    def test_index_file(self, sample_python_file: Path, monkeypatch):
        """Test indexing a single file."""
        # Mock the embedding service to avoid Chroma dependency in tests
        from code_assistant.embeddings import EmbeddingService
        
        class MockStore:
            def __init__(self):
                self._count = 0
                self._chunks = []
            
            def count(self):
                return self._count
            
            def add_chunks(self, chunks):
                self._chunks.extend(chunks)
                self._count += len(chunks)
            
            def delete_by_file(self, path):
                pass
        
        mock_store = MockStore()
        
        # Create indexer with mock
        indexer = CodeIndexer()
        indexer._embedding_service._store = mock_store
        
        result = indexer.index_file(sample_python_file)
        
        assert "file" in result
        assert "chunks_indexed" in result
        assert result["chunks_indexed"] >= 0

    def test_index_nonexistent_file(self):
        """Test indexing a file that doesn't exist."""
        indexer = CodeIndexer()
        
        with pytest.raises(ValueError, match="does not exist"):
            indexer.index_file("/nonexistent/file.py")

    def test_index_nonexistent_directory(self):
        """Test indexing a directory that doesn't exist."""
        indexer = CodeIndexer()
        
        with pytest.raises(ValueError, match="does not exist"):
            indexer.index_directory("/nonexistent/directory")
