"""Application configuration using Pydantic Settings."""

from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # OpenAI Configuration
    openai_api_key: str = Field(..., description="OpenAI API key")
    openai_model: str = Field(
        default="gpt-4-turbo-preview",
        description="OpenAI model to use",
    )

    # Chroma Configuration
    chroma_persist_dir: Path = Field(
        default=Path(".chroma_db"),
        description="Directory for Chroma persistence",
    )
    chroma_collection_name: str = Field(
        default="code_embeddings",
        description="Name of the Chroma collection",
    )

    # Docker Configuration
    docker_enabled: bool = Field(
        default=True,
        description="Enable Docker sandbox for code execution",
    )
    docker_image: str = Field(
        default="python:3.11-slim",
        description="Docker image for sandbox",
    )
    docker_timeout: int = Field(
        default=30,
        ge=5,
        le=300,
        description="Timeout for Docker execution in seconds",
    )
    docker_memory_limit: str = Field(
        default="512m",
        description="Memory limit for Docker container",
    )

    # Application Settings
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = Field(
        default="INFO",
        description="Logging level",
    )
    debug: bool = Field(
        default=False,
        description="Enable debug mode",
    )

    # API Settings
    api_host: str = Field(
        default="0.0.0.0",
        description="API host",
    )
    api_port: int = Field(
        default=8000,
        ge=1,
        le=65535,
        description="API port",
    )

    @field_validator("chroma_persist_dir", mode="before")
    @classmethod
    def ensure_path(cls, v: str | Path) -> Path:
        """Convert string to Path."""
        return Path(v)

    @field_validator("openai_api_key")
    @classmethod
    def validate_api_key(cls, v: str) -> str:
        """Validate API key format."""
        if not v or v.startswith("sk-your"):
            raise ValueError("Please set a valid OPENAI_API_KEY")
        return v


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
