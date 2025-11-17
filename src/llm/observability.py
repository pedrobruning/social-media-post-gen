"""Langfuse integration for LLM observability and tracing.

This module provides observability for all LLM calls and agent executions
using Langfuse, enabling debugging, monitoring, and cost tracking.
"""

from typing import Any

from langfuse import Langfuse

from src.config.settings import settings


class ObservabilityManager:
    """Manager for Langfuse observability and tracing.

    This class wraps Langfuse to provide observability for:
    - Individual LLM calls (with prompts, responses, tokens, latency)
    - Agent workflow executions
    - Custom events (image generation, human review, etc.)

    Example:
        obs = ObservabilityManager()
        obs.trace_llm_call(
            model="gpt-4",
            prompt="Hello",
            response="Hi there!",
            tokens=10,
            latency_ms=150
        )
    """

    def __init__(self):
        """Initialize Langfuse client if credentials are available."""
        self.enabled = bool(settings.langfuse_public_key and settings.langfuse_secret_key)

        if self.enabled:
            self.client = Langfuse(
                public_key=settings.langfuse_public_key,
                secret_key=settings.langfuse_secret_key,
                host=settings.langfuse_host,
            )
        else:
            self.client = None

    def trace_llm_call(
        self,
        model: str,
        prompt: str,
        response: str,
        tokens: int,
        latency_ms: float,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """Trace an LLM API call.

        Args:
            model: Model identifier used
            prompt: Input prompt
            response: Generated response
            tokens: Total tokens used
            latency_ms: Latency in milliseconds
            metadata: Additional metadata (post_id, platform, etc.)
        """
        if not self.enabled:
            return

        # TODO: Implement Langfuse LLM call tracing
        pass

    def trace_agent_execution(
        self,
        post_id: int,
        topic: str,
        status: str,
        duration_ms: float,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """Trace a full agent workflow execution.

        Args:
            post_id: Post database ID
            topic: Original topic
            status: Final status (approved, rejected, error)
            duration_ms: Total execution time
            metadata: Additional metadata
        """
        if not self.enabled:
            return

        # TODO: Implement agent execution tracing
        pass

    def trace_custom_event(
        self,
        event_name: str,
        post_id: int,
        data: dict[str, Any],
    ) -> None:
        """Trace a custom event (image generation, human review, etc.).

        Args:
            event_name: Name of the event
            post_id: Related post ID
            data: Event data
        """
        if not self.enabled:
            return

        # TODO: Implement custom event tracing
        pass

    def flush(self) -> None:
        """Flush any pending traces to Langfuse."""
        if self.enabled and self.client:
            self.client.flush()


# Global observability manager instance
observability = ObservabilityManager()
