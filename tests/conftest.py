"""Pytest configuration and fixtures."""

import tempfile
from pathlib import Path
from typing import Generator

import pytest


@pytest.fixture
def temp_directory() -> Generator[Path, None, None]:
    """Create a temporary directory for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def sample_python_file(temp_directory: Path) -> Path:
    """Create a sample Python file for testing."""
    file_path = temp_directory / "sample.py"
    file_path.write_text('''
"""Sample module for testing."""

from typing import List


def calculate_sum(numbers: List[int]) -> int:
    """
    Calculate the sum of a list of numbers.
    
    Args:
        numbers: List of integers to sum.
        
    Returns:
        The sum of all numbers.
    """
    return sum(numbers)


def calculate_average(numbers: List[int]) -> float:
    """Calculate the average of numbers."""
    if not numbers:
        return 0.0
    return calculate_sum(numbers) / len(numbers)


class Calculator:
    """A simple calculator class."""
    
    def __init__(self, initial_value: int = 0):
        """Initialize calculator with optional initial value."""
        self.value = initial_value
    
    def add(self, n: int) -> int:
        """Add n to the current value."""
        self.value += n
        return self.value
    
    def subtract(self, n: int) -> int:
        """Subtract n from the current value."""
        self.value -= n
        return self.value
    
    def reset(self) -> None:
        """Reset value to zero."""
        self.value = 0
''')
    return file_path


@pytest.fixture
def sample_project(temp_directory: Path) -> Path:
    """Create a sample project structure for testing."""
    # Create package
    pkg = temp_directory / "sample_pkg"
    pkg.mkdir()
    (pkg / "__init__.py").write_text('"""Sample package."""')
    
    (pkg / "utils.py").write_text('''
"""Utility functions."""

def validate_input(value: str) -> bool:
    """Validate input string."""
    return bool(value and value.strip())
''')
    
    (pkg / "models.py").write_text('''
"""Data models."""

from dataclasses import dataclass


@dataclass
class User:
    """User model."""
    name: str
    email: str
''')
    
    return temp_directory
