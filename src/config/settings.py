"""Application configuration using Pydantic Settings.

This module provides type-safe configuration management by loading environment
variables and validating them using Pydantic. All configuration is centralized here.
"""

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables.

    All settings are loaded from .env file or environment variables.
    See .env.example for all available configuration options.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,  # Allow uppercase env vars (standard convention)
        extra="ignore",
    )

    # OpenRouter Configuration
    openrouter_api_key: str = Field(
        ...,
        description="OpenRouter API key for LLM and image generation",
    )

    # Database Configuration
    database_url: str = Field(
        default="postgresql://admin:secret@localhost:5432/social_media_posts",
        description="PostgreSQL connection string",
    )

    # Langfuse Observability
    langfuse_public_key: str = Field(
        default="",
        description="Langfuse public key for observability",
    )
    langfuse_secret_key: str = Field(
        default="",
        description="Langfuse secret key for observability",
    )
    langfuse_host: str = Field(
        default="https://cloud.langfuse.com",
        description="Langfuse host URL",
    )

    # Application Configuration
    environment: str = Field(
        default="development",
        description="Environment: development, staging, production",
    )
    log_level: str = Field(
        default="INFO",
        description="Logging level: DEBUG, INFO, WARNING, ERROR, CRITICAL",
    )
    api_host: str = Field(
        default="0.0.0.0",
        description="API host to bind to",
    )
    api_port: int = Field(
        default=8000,
        description="API port to bind to",
    )

    # Image Storage Configuration
    image_storage_path: str = Field(
        default="./storage/images",
        description="Local storage path for generated images",
    )
    max_image_size_mb: int = Field(
        default=10,
        description="Maximum image size in MB",
    )
    image_format: str = Field(
        default="png",
        description="Image format: png, jpeg, webp",
    )

    # LangGraph Checkpoint Configuration
    checkpoint_table_name: str = Field(
        default="checkpoints",
        description="PostgreSQL table name for agent checkpoints",
    )

    # LLM Model Configuration
    primary_model: str = Field(
        default="anthropic/claude-3.5-sonnet",
        description="Primary LLM model via OpenRouter",
    )
    fallback_models: str = Field(
        default="openai/gpt-4o,openai/gpt-3.5-turbo",
        description="Comma-separated list of fallback models",
    )
    llm_temperature: float = Field(
        default=0.7,
        ge=0.0,
        le=2.0,
        description="Temperature for text generation",
    )
    llm_max_tokens: int = Field(
        default=2000,
        description="Maximum tokens for text generation",
    )

    # Image Generation Configuration
    image_model: str = Field(
        default="dall-e-3",
        description="DALL-E model: dall-e-3, dall-e-2",
    )
    image_size: str = Field(
        default="1024x1024",
        description="Image size: 1024x1024, 1792x1024, 1024x1792",
    )
    image_quality: str = Field(
        default="standard",
        description="Image quality: standard, hd",
    )
    image_style: str = Field(
        default="vivid",
        description="Image style: vivid, natural",
    )

    # Evaluation Configuration
    auto_evaluate: bool = Field(
        default=True,
        description="Enable automatic evaluation after generation",
    )
    evaluation_model: str = Field(
        default="openai/gpt-4o",
        description="LLM model for evaluation (LLM-as-judge)",
    )

    # Security Configuration
    secret_key: str = Field(
        default="change-me-in-production",
        description="Secret key for session management",
    )
    cors_origins: str = Field(
        default="http://localhost:3000,http://localhost:8080",
        description="Comma-separated list of allowed CORS origins",
    )

    # Rate Limiting
    rate_limit_per_minute: int = Field(
        default=60,
        description="Maximum requests per minute per IP",
    )

    @property
    def fallback_models_list(self) -> list[str]:
        """Parse fallback models from comma-separated string."""
        return [m.strip() for m in self.fallback_models.split(",") if m.strip()]

    @property
    def cors_origins_list(self) -> list[str]:
        """Parse CORS origins from comma-separated string."""
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


# Global settings instance
settings = Settings()
