"""Pydantic models for code representation."""

from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field


class Parameter(BaseModel):
    """Function parameter representation."""

    name: str
    annotation: str | None = None
    default: str | None = None
    kind: str = "POSITIONAL_OR_KEYWORD"


class FunctionInfo(BaseModel):
    """Information about a function in the codebase."""

    name: str
    qualified_name: str = Field(description="Fully qualified name including module")
    docstring: str | None = None
    parameters: list[Parameter] = Field(default_factory=list)
    return_type: str | None = None
    decorators: list[str] = Field(default_factory=list)
    is_async: bool = False
    is_method: bool = False
    start_line: int
    end_line: int
    source_code: str

    @property
    def signature(self) -> str:
        """Generate function signature string."""
        params = ", ".join(
            f"{p.name}: {p.annotation}" if p.annotation else p.name
            for p in self.parameters
        )
        async_prefix = "async " if self.is_async else ""
        return_suffix = f" -> {self.return_type}" if self.return_type else ""
        return f"{async_prefix}def {self.name}({params}){return_suffix}"


class ClassInfo(BaseModel):
    """Information about a class in the codebase."""

    name: str
    qualified_name: str
    docstring: str | None = None
    bases: list[str] = Field(default_factory=list)
    decorators: list[str] = Field(default_factory=list)
    methods: list[FunctionInfo] = Field(default_factory=list)
    class_variables: dict[str, str] = Field(default_factory=dict)
    start_line: int
    end_line: int
    source_code: str


class ImportInfo(BaseModel):
    """Information about an import statement."""

    module: str
    names: list[str] = Field(default_factory=list)
    alias: str | None = None
    is_from_import: bool = False
    line: int


class CodeFile(BaseModel):
    """Representation of a parsed code file."""

    path: Path
    relative_path: str
    language: str = "python"
    content: str
    imports: list[ImportInfo] = Field(default_factory=list)
    functions: list[FunctionInfo] = Field(default_factory=list)
    classes: list[ClassInfo] = Field(default_factory=list)
    module_docstring: str | None = None

    @property
    def all_functions(self) -> list[FunctionInfo]:
        """Get all functions including class methods."""
        all_funcs = list(self.functions)
        for cls in self.classes:
            all_funcs.extend(cls.methods)
        return all_funcs


class CodeChunk(BaseModel):
    """A chunk of code for embedding."""

    id: str = Field(description="Unique identifier for this chunk")
    content: str = Field(description="The code content")
    file_path: str
    chunk_type: str = Field(description="Type: function, class, or module")
    name: str = Field(description="Name of the code element")
    qualified_name: str
    start_line: int
    end_line: int
    metadata: dict[str, Any] = Field(default_factory=dict)
