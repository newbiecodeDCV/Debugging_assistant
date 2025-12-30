"""Tests for Python parser."""

from pathlib import Path

import pytest

from code_assistant.parsers import PythonParser


class TestPythonParser:
    """Test suite for PythonParser."""

    def test_supported_extensions(self):
        """Test that parser supports Python file extensions."""
        parser = PythonParser()
        assert ".py" in parser.supported_extensions
        assert ".pyw" in parser.supported_extensions

    def test_language(self):
        """Test language property."""
        parser = PythonParser()
        assert parser.language == "python"

    def test_can_parse_python_file(self, temp_directory: Path):
        """Test can_parse returns True for Python files."""
        parser = PythonParser()
        py_file = temp_directory / "test.py"
        py_file.touch()
        assert parser.can_parse(py_file) is True

    def test_cannot_parse_non_python_file(self, temp_directory: Path):
        """Test can_parse returns False for non-Python files."""
        parser = PythonParser()
        js_file = temp_directory / "test.js"
        js_file.touch()
        assert parser.can_parse(js_file) is False

    def test_parse_file_extracts_functions(self, sample_python_file: Path):
        """Test that functions are extracted correctly."""
        parser = PythonParser()
        result = parser.parse_file(sample_python_file)

        assert len(result.functions) == 2
        
        # Check calculate_sum
        calc_sum = next(f for f in result.functions if f.name == "calculate_sum")
        assert calc_sum.docstring is not None
        assert "sum" in calc_sum.docstring.lower()
        assert len(calc_sum.parameters) == 1
        assert calc_sum.parameters[0].name == "numbers"
        assert calc_sum.return_type == "int"

    def test_parse_file_extracts_classes(self, sample_python_file: Path):
        """Test that classes are extracted correctly."""
        parser = PythonParser()
        result = parser.parse_file(sample_python_file)

        assert len(result.classes) == 1
        
        calculator = result.classes[0]
        assert calculator.name == "Calculator"
        assert calculator.docstring is not None
        assert len(calculator.methods) == 4  # __init__, add, subtract, reset

    def test_parse_file_extracts_docstring(self, sample_python_file: Path):
        """Test that module docstring is extracted."""
        parser = PythonParser()
        result = parser.parse_file(sample_python_file)

        assert result.module_docstring is not None
        assert "sample" in result.module_docstring.lower()

    def test_parse_file_extracts_imports(self, sample_python_file: Path):
        """Test that imports are extracted."""
        parser = PythonParser()
        result = parser.parse_file(sample_python_file)

        assert len(result.imports) == 1
        assert result.imports[0].module == "typing"
        assert "List" in result.imports[0].names

    def test_parse_content_string(self):
        """Test parsing a code string directly."""
        parser = PythonParser()
        code = '''
def hello(name: str) -> str:
    """Say hello."""
    return f"Hello, {name}!"
'''
        result = parser.parse_content(code)

        assert len(result.functions) == 1
        assert result.functions[0].name == "hello"
        assert result.functions[0].is_async is False

    def test_parse_async_function(self):
        """Test parsing async functions."""
        parser = PythonParser()
        code = '''
async def fetch_data(url: str) -> dict:
    """Fetch data from URL."""
    pass
'''
        result = parser.parse_content(code)

        assert len(result.functions) == 1
        assert result.functions[0].is_async is True

    def test_parse_decorated_function(self):
        """Test parsing decorated functions."""
        parser = PythonParser()
        code = '''
@staticmethod
@cache
def cached_function():
    pass
'''
        result = parser.parse_content(code)

        assert len(result.functions) == 1
        assert "staticmethod" in result.functions[0].decorators
        assert "cache" in result.functions[0].decorators

    def test_parse_class_with_bases(self):
        """Test parsing class inheritance."""
        parser = PythonParser()
        code = '''
class Child(Parent, Mixin):
    """Child class."""
    pass
'''
        result = parser.parse_content(code)

        assert len(result.classes) == 1
        assert "Parent" in result.classes[0].bases
        assert "Mixin" in result.classes[0].bases

    def test_function_signature_property(self):
        """Test the signature property of FunctionInfo."""
        parser = PythonParser()
        code = '''
async def process(data: list, flag: bool = False) -> dict:
    pass
'''
        result = parser.parse_content(code)
        func = result.functions[0]

        assert "async def" in func.signature
        assert "process" in func.signature
        assert "data: list" in func.signature
        assert "-> dict" in func.signature

    def test_parse_syntax_error(self):
        """Test handling of syntax errors."""
        parser = PythonParser()
        code = '''
def broken(
    # Missing closing paren
'''
        result = parser.parse_content(code)
        
        # Should return a CodeFile with syntax error in docstring
        assert result is not None
        assert "Syntax error" in (result.module_docstring or "")
