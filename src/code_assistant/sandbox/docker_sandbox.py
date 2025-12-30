"""Docker sandbox for safe code execution."""

import logging
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import docker
from docker.errors import ContainerError, ImageNotFound, APIError

from code_assistant.config import get_settings

logger = logging.getLogger(__name__)


@dataclass
class ExecutionResult:
    """Result of code execution."""

    success: bool
    output: str
    error: str | None
    exit_code: int
    execution_time: float | None = None


class DockerSandbox:
    """Docker-based sandbox for safe code execution."""

    def __init__(
        self,
        image: str | None = None,
        timeout: int | None = None,
        memory_limit: str | None = None,
    ):
        """
        Initialize Docker sandbox.

        Args:
            image: Docker image to use.
            timeout: Execution timeout in seconds.
            memory_limit: Memory limit (e.g., "512m").
        """
        settings = get_settings()

        self._enabled = settings.docker_enabled
        self._image = image or settings.docker_image
        self._timeout = timeout or settings.docker_timeout
        self._memory_limit = memory_limit or settings.docker_memory_limit

        self._client: docker.DockerClient | None = None

        if self._enabled:
            self._initialize_client()

    def _initialize_client(self) -> None:
        """Initialize Docker client."""
        try:
            self._client = docker.from_env()
            # Test connection
            self._client.ping()
            logger.info(f"Docker sandbox initialized with image: {self._image}")
        except Exception as e:
            logger.warning(f"Failed to initialize Docker: {e}. Sandbox disabled.")
            self._enabled = False
            self._client = None

    @property
    def is_available(self) -> bool:
        """Check if Docker sandbox is available."""
        return self._enabled and self._client is not None

    def ensure_image(self) -> bool:
        """
        Ensure the Docker image is available.

        Returns:
            True if image is available.
        """
        if not self.is_available:
            return False

        try:
            self._client.images.get(self._image)
            return True
        except ImageNotFound:
            logger.info(f"Pulling Docker image: {self._image}")
            try:
                self._client.images.pull(self._image)
                return True
            except Exception as e:
                logger.error(f"Failed to pull image: {e}")
                return False

    def execute_code(
        self,
        code: str,
        language: str = "python",
        stdin: str | None = None,
    ) -> ExecutionResult:
        """
        Execute code in a sandboxed container.

        Args:
            code: Code to execute.
            language: Programming language (currently only Python supported).
            stdin: Optional standard input.

        Returns:
            ExecutionResult with output and status.
        """
        if not self.is_available:
            return ExecutionResult(
                success=False,
                output="",
                error="Docker sandbox is not available",
                exit_code=-1,
            )

        if language != "python":
            return ExecutionResult(
                success=False,
                output="",
                error=f"Language '{language}' not supported. Only Python is supported.",
                exit_code=-1,
            )

        if not self.ensure_image():
            return ExecutionResult(
                success=False,
                output="",
                error="Docker image not available",
                exit_code=-1,
            )

        # Create temporary file for the code
        with tempfile.TemporaryDirectory() as tmpdir:
            code_file = Path(tmpdir) / "script.py"
            code_file.write_text(code, encoding="utf-8")

            # Build command
            command = ["python", "/workspace/script.py"]

            try:
                import time

                start_time = time.time()

                # Run container
                result = self._client.containers.run(
                    image=self._image,
                    command=command,
                    volumes={tmpdir: {"bind": "/workspace", "mode": "ro"}},
                    working_dir="/workspace",
                    mem_limit=self._memory_limit,
                    network_disabled=True,  # No network access for security
                    remove=True,
                    timeout=self._timeout,
                    stdin_open=bool(stdin),
                    stderr=True,
                    stdout=True,
                )

                execution_time = time.time() - start_time

                # Decode output
                output = result.decode("utf-8") if isinstance(result, bytes) else str(result)

                return ExecutionResult(
                    success=True,
                    output=output,
                    error=None,
                    exit_code=0,
                    execution_time=execution_time,
                )

            except ContainerError as e:
                return ExecutionResult(
                    success=False,
                    output=e.container.logs().decode("utf-8") if e.container else "",
                    error=str(e),
                    exit_code=e.exit_status,
                )
            except APIError as e:
                return ExecutionResult(
                    success=False,
                    output="",
                    error=f"Docker API error: {e}",
                    exit_code=-1,
                )
            except Exception as e:
                return ExecutionResult(
                    success=False,
                    output="",
                    error=f"Execution error: {e}",
                    exit_code=-1,
                )

    def execute_tests(
        self,
        test_code: str,
        target_code: str,
    ) -> ExecutionResult:
        """
        Execute pytest tests in sandbox.

        Args:
            test_code: The test code to run.
            target_code: The code being tested.

        Returns:
            ExecutionResult with test output.
        """
        if not self.is_available:
            return ExecutionResult(
                success=False,
                output="",
                error="Docker sandbox is not available",
                exit_code=-1,
            )

        # Create combined code with both target and tests
        combined = f'''# Target code
{target_code}

# Test code
{test_code}

# Run tests
if __name__ == "__main__":
    import pytest
    import sys
    sys.exit(pytest.main([__file__, "-v"]))
'''

        return self.execute_code(combined)

    def validate_syntax(self, code: str) -> ExecutionResult:
        """
        Validate Python syntax without executing.

        Args:
            code: Code to validate.

        Returns:
            ExecutionResult indicating if syntax is valid.
        """
        validation_code = f'''
import ast
code = {repr(code)}
try:
    ast.parse(code)
    print("Syntax OK")
except SyntaxError as e:
    print(f"Syntax Error: {{e}}")
    exit(1)
'''
        return self.execute_code(validation_code)
