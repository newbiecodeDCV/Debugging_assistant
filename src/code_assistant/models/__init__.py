"""Pydantic models for code and analysis."""

from code_assistant.models.analysis import (
    AnalysisResult,
    BugReport,
    CodeLocation,
    ExplanationResult,
    RefactorSuggestion,
    RefactorType,
    Severity,
    TestCase,
    TestGenerationResult,
)
from code_assistant.models.code import (
    ClassInfo,
    CodeChunk,
    CodeFile,
    FunctionInfo,
    ImportInfo,
    Parameter,
)

__all__ = [
    # Code models
    "Parameter",
    "FunctionInfo",
    "ClassInfo",
    "ImportInfo",
    "CodeFile",
    "CodeChunk",
    # Analysis models
    "Severity",
    "RefactorType",
    "CodeLocation",
    "BugReport",
    "RefactorSuggestion",
    "ExplanationResult",
    "TestCase",
    "TestGenerationResult",
    "AnalysisResult",
]
