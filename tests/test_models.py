"""Tests for models."""

import pytest
from pydantic import ValidationError

from code_assistant.models import (
    BugReport,
    CodeFile,
    CodeLocation,
    FunctionInfo,
    Parameter,
    Severity,
)


class TestParameter:
    """Tests for Parameter model."""

    def test_create_simple_parameter(self):
        """Test creating a simple parameter."""
        param = Parameter(name="x")
        assert param.name == "x"
        assert param.annotation is None
        assert param.default is None

    def test_create_annotated_parameter(self):
        """Test creating an annotated parameter."""
        param = Parameter(name="items", annotation="list[str]", default="[]")
        assert param.name == "items"
        assert param.annotation == "list[str]"
        assert param.default == "[]"


class TestFunctionInfo:
    """Tests for FunctionInfo model."""

    def test_create_function_info(self):
        """Test creating FunctionInfo."""
        func = FunctionInfo(
            name="test_func",
            qualified_name="module.test_func",
            docstring="A test function.",
            parameters=[Parameter(name="x", annotation="int")],
            return_type="str",
            start_line=1,
            end_line=5,
            source_code="def test_func(x: int) -> str: ...",
        )

        assert func.name == "test_func"
        assert len(func.parameters) == 1
        assert func.is_async is False
        assert func.is_method is False

    def test_signature_property(self):
        """Test the signature property."""
        func = FunctionInfo(
            name="greet",
            qualified_name="greet",
            parameters=[
                Parameter(name="name", annotation="str"),
                Parameter(name="count", annotation="int"),
            ],
            return_type="str",
            start_line=1,
            end_line=2,
            source_code="...",
        )

        sig = func.signature
        assert "def greet" in sig
        assert "name: str" in sig
        assert "-> str" in sig

    def test_async_signature(self):
        """Test signature for async function."""
        func = FunctionInfo(
            name="fetch",
            qualified_name="fetch",
            is_async=True,
            parameters=[],
            start_line=1,
            end_line=1,
            source_code="...",
        )

        assert "async def" in func.signature


class TestBugReport:
    """Tests for BugReport model."""

    def test_create_bug_report(self):
        """Test creating a bug report."""
        bug = BugReport(
            id="bug-001",
            severity=Severity.HIGH,
            category="null_reference",
            title="Potential None dereference",
            description="Variable may be None when accessed",
            location=CodeLocation(
                file_path="test.py",
                start_line=10,
                end_line=10,
            ),
            code_snippet="result = obj.value",
            suggestion="Add a None check before accessing",
            confidence=0.85,
        )

        assert bug.severity == Severity.HIGH
        assert bug.confidence == 0.85
        assert bug.location.start_line == 10

    def test_confidence_validation(self):
        """Test that confidence must be between 0 and 1."""
        with pytest.raises(ValidationError):
            BugReport(
                id="bug-001",
                severity=Severity.LOW,
                category="test",
                title="Test",
                description="Test",
                location=CodeLocation(file_path="test.py", start_line=1, end_line=1),
                code_snippet="...",
                suggestion="...",
                confidence=1.5,  # Invalid: > 1
            )
