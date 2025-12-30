"""Pydantic models for analysis results."""

from enum import Enum
from typing import Literal

from pydantic import BaseModel, Field


class Severity(str, Enum):
    """Bug severity levels."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class RefactorType(str, Enum):
    """Types of refactoring suggestions."""

    EXTRACT_METHOD = "extract_method"
    RENAME = "rename"
    SIMPLIFY = "simplify"
    REMOVE_DUPLICATION = "remove_duplication"
    ADD_TYPE_HINTS = "add_type_hints"
    IMPROVE_NAMING = "improve_naming"
    SPLIT_FUNCTION = "split_function"
    USE_PYTHONIC_IDIOM = "use_pythonic_idiom"
    IMPROVE_ERROR_HANDLING = "improve_error_handling"
    ADD_DOCUMENTATION = "add_documentation"


class CodeLocation(BaseModel):
    """Location in code."""

    file_path: str
    start_line: int
    end_line: int
    start_col: int | None = None
    end_col: int | None = None


class BugReport(BaseModel):
    """Report of a detected bug or issue."""

    id: str = Field(description="Unique identifier for this bug")
    severity: Severity
    category: str = Field(description="Bug category e.g., 'logic_error', 'null_reference'")
    title: str = Field(description="Short title of the bug")
    description: str = Field(description="Detailed description of the issue")
    location: CodeLocation
    code_snippet: str = Field(description="The problematic code")
    suggestion: str = Field(description="How to fix the bug")
    suggested_fix: str | None = Field(
        default=None,
        description="Suggested code fix if available",
    )
    confidence: float = Field(
        ge=0,
        le=1,
        description="Confidence score of the detection",
    )


class RefactorSuggestion(BaseModel):
    """A refactoring suggestion."""

    id: str
    type: RefactorType
    priority: Literal["low", "medium", "high"]
    title: str
    description: str
    location: CodeLocation
    before_code: str
    after_code: str
    explanation: str = Field(description="Why this refactoring is beneficial")
    estimated_impact: str = Field(
        description="Expected impact on code quality/maintainability",
    )


class ExplanationResult(BaseModel):
    """Result of code explanation."""

    target_name: str = Field(description="Name of the explained element")
    target_type: Literal["function", "class", "module"]
    summary: str = Field(description="Brief summary of what it does")
    detailed_explanation: str = Field(description="Detailed explanation")
    parameters_explanation: dict[str, str] | None = Field(
        default=None,
        description="Explanation of each parameter",
    )
    return_value_explanation: str | None = None
    usage_examples: list[str] = Field(
        default_factory=list,
        description="Example usages",
    )
    related_code: list[str] = Field(
        default_factory=list,
        description="Related functions/classes",
    )


class TestCase(BaseModel):
    """A generated test case."""

    name: str
    description: str
    test_code: str
    test_type: Literal["unit", "integration", "edge_case"]
    covers: list[str] = Field(
        default_factory=list,
        description="What aspects this test covers",
    )


class TestGenerationResult(BaseModel):
    """Result of test generation."""

    target_name: str
    test_file_name: str
    imports: list[str]
    fixtures: list[str] = Field(default_factory=list)
    test_cases: list[TestCase]
    full_test_code: str


class AnalysisResult(BaseModel):
    """Complete analysis result for a file or codebase."""

    analyzed_files: list[str]
    total_functions: int
    total_classes: int
    bugs: list[BugReport] = Field(default_factory=list)
    refactor_suggestions: list[RefactorSuggestion] = Field(default_factory=list)
    summary: str
