"""Python AST-based code parser."""

import ast
import inspect
from pathlib import Path
from typing import Any

from code_assistant.models import (
    ClassInfo,
    CodeFile,
    FunctionInfo,
    ImportInfo,
    Parameter,
)
from code_assistant.parsers.base import BaseParser


class PythonParser(BaseParser):
    """Parser for Python source files using AST."""

    @property
    def supported_extensions(self) -> set[str]:
        """Supported Python file extensions."""
        return {".py", ".pyw"}

    @property
    def language(self) -> str:
        """Return language name."""
        return "python"

    def parse_file(self, file_path: Path, base_path: Path | None = None) -> CodeFile:
        """Parse a Python file."""
        content = file_path.read_text(encoding="utf-8")
        relative_path = (
            str(file_path.relative_to(base_path))
            if base_path
            else str(file_path)
        )

        return self._parse(content, file_path, relative_path)

    def parse_content(
        self,
        content: str,
        file_path: str = "<string>",
    ) -> CodeFile:
        """Parse Python content string."""
        return self._parse(content, Path(file_path), file_path)

    def _parse(
        self,
        content: str,
        file_path: Path,
        relative_path: str,
    ) -> CodeFile:
        """Internal parsing logic."""
        try:
            tree = ast.parse(content)
        except SyntaxError as e:
            # Return a minimal CodeFile for files with syntax errors
            return CodeFile(
                path=file_path,
                relative_path=relative_path,
                language=self.language,
                content=content,
                module_docstring=f"Syntax error: {e}",
            )

        lines = content.splitlines()

        return CodeFile(
            path=file_path,
            relative_path=relative_path,
            language=self.language,
            content=content,
            module_docstring=ast.get_docstring(tree),
            imports=self._extract_imports(tree),
            functions=self._extract_functions(tree, lines, ""),
            classes=self._extract_classes(tree, lines, ""),
        )

    def _extract_imports(self, tree: ast.Module) -> list[ImportInfo]:
        """Extract import statements from AST."""
        imports: list[ImportInfo] = []

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append(
                        ImportInfo(
                            module=alias.name,
                            alias=alias.asname,
                            is_from_import=False,
                            line=node.lineno,
                        )
                    )
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ""
                imports.append(
                    ImportInfo(
                        module=module,
                        names=[alias.name for alias in node.names],
                        is_from_import=True,
                        line=node.lineno,
                    )
                )

        return imports

    def _extract_functions(
        self,
        tree: ast.Module | ast.ClassDef,
        lines: list[str],
        prefix: str,
    ) -> list[FunctionInfo]:
        """Extract function definitions from AST."""
        functions: list[FunctionInfo] = []

        for node in ast.iter_child_nodes(tree):
            if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):
                func_info = self._parse_function(node, lines, prefix)
                functions.append(func_info)

        return functions

    def _parse_function(
        self,
        node: ast.FunctionDef | ast.AsyncFunctionDef,
        lines: list[str],
        prefix: str,
    ) -> FunctionInfo:
        """Parse a single function definition."""
        qualified_name = f"{prefix}.{node.name}" if prefix else node.name

        # Extract parameters
        parameters = self._extract_parameters(node.args)

        # Get return type annotation
        return_type = None
        if node.returns:
            return_type = self._get_annotation_string(node.returns)

        # Get decorators
        decorators = [
            self._get_decorator_string(dec) for dec in node.decorator_list
        ]

        # Get source code
        source_lines = lines[node.lineno - 1 : node.end_lineno]
        source_code = "\n".join(source_lines)

        return FunctionInfo(
            name=node.name,
            qualified_name=qualified_name,
            docstring=ast.get_docstring(node),
            parameters=parameters,
            return_type=return_type,
            decorators=decorators,
            is_async=isinstance(node, ast.AsyncFunctionDef),
            is_method=bool(prefix),
            start_line=node.lineno,
            end_line=node.end_lineno or node.lineno,
            source_code=source_code,
        )

    def _extract_parameters(self, args: ast.arguments) -> list[Parameter]:
        """Extract function parameters."""
        parameters: list[Parameter] = []

        # Calculate default offset
        num_defaults = len(args.defaults)
        num_args = len(args.args)
        default_offset = num_args - num_defaults

        for i, arg in enumerate(args.args):
            # Get annotation
            annotation = None
            if arg.annotation:
                annotation = self._get_annotation_string(arg.annotation)

            # Get default value
            default = None
            default_idx = i - default_offset
            if default_idx >= 0 and default_idx < len(args.defaults):
                default = self._get_const_value(args.defaults[default_idx])

            parameters.append(
                Parameter(
                    name=arg.arg,
                    annotation=annotation,
                    default=default,
                    kind="POSITIONAL_OR_KEYWORD",
                )
            )

        # Handle *args
        if args.vararg:
            parameters.append(
                Parameter(
                    name=f"*{args.vararg.arg}",
                    annotation=self._get_annotation_string(args.vararg.annotation)
                    if args.vararg.annotation
                    else None,
                    kind="VAR_POSITIONAL",
                )
            )

        # Handle keyword-only args
        for i, arg in enumerate(args.kwonlyargs):
            default = None
            if i < len(args.kw_defaults) and args.kw_defaults[i]:
                default = self._get_const_value(args.kw_defaults[i])

            parameters.append(
                Parameter(
                    name=arg.arg,
                    annotation=self._get_annotation_string(arg.annotation)
                    if arg.annotation
                    else None,
                    default=default,
                    kind="KEYWORD_ONLY",
                )
            )

        # Handle **kwargs
        if args.kwarg:
            parameters.append(
                Parameter(
                    name=f"**{args.kwarg.arg}",
                    annotation=self._get_annotation_string(args.kwarg.annotation)
                    if args.kwarg.annotation
                    else None,
                    kind="VAR_KEYWORD",
                )
            )

        return parameters

    def _extract_classes(
        self,
        tree: ast.Module,
        lines: list[str],
        prefix: str,
    ) -> list[ClassInfo]:
        """Extract class definitions from AST."""
        classes: list[ClassInfo] = []

        for node in ast.iter_child_nodes(tree):
            if isinstance(node, ast.ClassDef):
                class_info = self._parse_class(node, lines, prefix)
                classes.append(class_info)

        return classes

    def _parse_class(
        self,
        node: ast.ClassDef,
        lines: list[str],
        prefix: str,
    ) -> ClassInfo:
        """Parse a single class definition."""
        qualified_name = f"{prefix}.{node.name}" if prefix else node.name

        # Get bases
        bases = [self._get_annotation_string(base) for base in node.bases]

        # Get decorators
        decorators = [
            self._get_decorator_string(dec) for dec in node.decorator_list
        ]

        # Get methods
        methods = self._extract_functions(node, lines, qualified_name)

        # Get class variables (simple assignments at class level)
        class_variables: dict[str, str] = {}
        for child in ast.iter_child_nodes(node):
            if isinstance(child, ast.AnnAssign) and isinstance(child.target, ast.Name):
                var_name = child.target.id
                var_type = self._get_annotation_string(child.annotation)
                class_variables[var_name] = var_type

        # Get source code
        source_lines = lines[node.lineno - 1 : node.end_lineno]
        source_code = "\n".join(source_lines)

        return ClassInfo(
            name=node.name,
            qualified_name=qualified_name,
            docstring=ast.get_docstring(node),
            bases=bases,
            decorators=decorators,
            methods=methods,
            class_variables=class_variables,
            start_line=node.lineno,
            end_line=node.end_lineno or node.lineno,
            source_code=source_code,
        )

    def _get_annotation_string(self, node: ast.expr | None) -> str:
        """Convert an annotation node to its string representation."""
        if node is None:
            return "Any"

        try:
            return ast.unparse(node)
        except Exception:
            return "Any"

    def _get_decorator_string(self, node: ast.expr) -> str:
        """Convert a decorator node to its string representation."""
        try:
            return ast.unparse(node)
        except Exception:
            return "@unknown"

    def _get_const_value(self, node: ast.expr | None) -> str | None:
        """Get the string representation of a constant/default value."""
        if node is None:
            return None

        try:
            return ast.unparse(node)
        except Exception:
            return "..."
