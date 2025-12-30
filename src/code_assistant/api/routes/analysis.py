"""Analysis API routes."""

from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from code_assistant.services import CodeAnalyzer, CodeIndexer

router = APIRouter()

# Service instances (singleton pattern)
_indexer: CodeIndexer | None = None
_analyzer: CodeAnalyzer | None = None


def get_indexer() -> CodeIndexer:
    """Get or create indexer instance."""
    global _indexer
    if _indexer is None:
        _indexer = CodeIndexer()
    return _indexer


def get_analyzer() -> CodeAnalyzer:
    """Get or create analyzer instance."""
    global _analyzer
    if _analyzer is None:
        _analyzer = CodeAnalyzer()
    return _analyzer


# Request/Response Models
class IndexRequest(BaseModel):
    """Request to index a codebase."""

    directory: str = Field(description="Directory path to index")
    exclude_patterns: list[str] | None = Field(
        default=None,
        description="Patterns to exclude",
    )


class IndexResponse(BaseModel):
    """Response from indexing."""

    directory: str
    files_indexed: int
    total_chunks: int


class ExplainRequest(BaseModel):
    """Request to explain code."""

    target: str = Field(description="Name of function/class to explain")


class DebugRequest(BaseModel):
    """Request to debug a file."""

    file_path: str = Field(description="Path to file to analyze")


class RefactorRequest(BaseModel):
    """Request for refactoring suggestions."""

    target: str = Field(description="Code or file to refactor")


class GenerateTestsRequest(BaseModel):
    """Request to generate tests."""

    target: str = Field(description="Name of function/class to test")


class ExecuteCodeRequest(BaseModel):
    """Request to execute code in sandbox."""

    code: str = Field(description="Python code to execute")


class SearchRequest(BaseModel):
    """Request to search codebase."""

    query: str = Field(description="Search query")
    n_results: int = Field(default=10, ge=1, le=50)
    chunk_type: str | None = Field(
        default=None,
        description="Filter by type: function, class, method, module",
    )


class AnalysisResponse(BaseModel):
    """Generic analysis response."""

    target: str | None = None
    result: str


# Endpoints
@router.post("/index", response_model=IndexResponse)
async def index_codebase(request: IndexRequest) -> IndexResponse:
    """Index a codebase directory."""
    indexer = get_indexer()

    try:
        result = indexer.index_directory(
            request.directory,
            request.exclude_patterns,
        )
        return IndexResponse(
            directory=result["directory"],
            files_indexed=result["files_indexed"],
            total_chunks=result["total_chunks"],
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Indexing failed: {e}")


@router.post("/explain", response_model=AnalysisResponse)
async def explain_code(request: ExplainRequest) -> AnalysisResponse:
    """Explain a code element."""
    analyzer = get_analyzer()

    try:
        result = await analyzer.explain(request.target)
        return AnalysisResponse(
            target=request.target,
            result=result["explanation"],
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Explanation failed: {e}")


@router.post("/debug", response_model=AnalysisResponse)
async def debug_file(request: DebugRequest) -> AnalysisResponse:
    """Analyze a file for bugs."""
    analyzer = get_analyzer()

    try:
        result = await analyzer.debug(request.file_path)
        return AnalysisResponse(
            target=request.file_path,
            result=result["report"],
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Debug failed: {e}")


@router.post("/refactor", response_model=AnalysisResponse)
async def suggest_refactoring(request: RefactorRequest) -> AnalysisResponse:
    """Get refactoring suggestions."""
    analyzer = get_analyzer()

    try:
        result = await analyzer.refactor(request.target)
        return AnalysisResponse(
            target=request.target,
            result=result["suggestions"],
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Refactoring failed: {e}")


@router.post("/generate-tests", response_model=AnalysisResponse)
async def generate_tests(request: GenerateTestsRequest) -> AnalysisResponse:
    """Generate tests for a code element."""
    analyzer = get_analyzer()

    try:
        result = await analyzer.generate_tests(request.target)
        return AnalysisResponse(
            target=request.target,
            result=result["tests"],
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Test generation failed: {e}")


@router.post("/execute")
async def execute_code(request: ExecuteCodeRequest) -> dict[str, Any]:
    """Execute code in Docker sandbox."""
    analyzer = get_analyzer()

    result = analyzer.execute_code(request.code)
    if not result["success"] and "not available" in str(result.get("error", "")):
        raise HTTPException(status_code=503, detail="Docker sandbox not available")

    return result


@router.post("/search")
async def search_code(request: SearchRequest) -> list[dict[str, Any]]:
    """Search the indexed codebase."""
    indexer = get_indexer()

    results = indexer.search(
        request.query,
        request.n_results,
        request.chunk_type,
    )

    # Simplify results for API response
    return [
        {
            "name": r.get("metadata", {}).get("qualified_name", "unknown"),
            "type": r.get("metadata", {}).get("chunk_type", "unknown"),
            "file": r.get("metadata", {}).get("file_path", "unknown"),
            "content": r.get("content", "")[:500],
            "distance": r.get("distance", 0),
        }
        for r in results
    ]


@router.get("/stats")
async def get_stats() -> dict[str, Any]:
    """Get indexing statistics."""
    indexer = get_indexer()
    return {
        "indexed_chunks": indexer.indexed_count,
    }
