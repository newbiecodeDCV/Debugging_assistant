"""Abstract base class for code parsers."""

from abc import ABC, abstractmethod
from pathlib import Path

from code_assistant.models import CodeFile


class BaseParser(ABC):
    """Abstract base parser for code files."""

    @property
    @abstractmethod
    def supported_extensions(self) -> set[str]:
        """Return supported file extensions (e.g., {'.py'})."""
        ...

    @property
    @abstractmethod
    def language(self) -> str:
        """Return the language name."""
        ...

    def can_parse(self, file_path: Path) -> bool:
        """Check if this parser can handle the given file."""
        return file_path.suffix.lower() in self.supported_extensions

    @abstractmethod
    def parse_file(self, file_path: Path, base_path: Path | None = None) -> CodeFile:
        """
        Parse a file and return structured code information.

        Args:
            file_path: Path to the file to parse.
            base_path: Base path for calculating relative paths.

        Returns:
            CodeFile with parsed information.
        """
        ...

    @abstractmethod
    def parse_content(
        self,
        content: str,
        file_path: str = "<string>",
    ) -> CodeFile:
        """
        Parse content string and return structured code information.

        Args:
            content: The code content to parse.
            file_path: Virtual file path for identification.

        Returns:
            CodeFile with parsed information.
        """
        ...
