"""LLM router with fallback chain for resilient API calls.

This module provides intelligent routing to multiple LLM providers via OpenRouter,
with automatic fallback and retry logic for resilience.
"""

import logging
import time
from typing import TypeVar

from langchain_openai import ChatOpenAI
from pydantic import BaseModel

from src.config.settings import settings

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)


class LLMRouter:
    """Router for LLM calls with fallback chain and retry logic.

    This class manages calls to multiple LLM models via OpenRouter,
    implementing a fallback chain for resilience. If the primary model
    fails, it automatically tries fallback models in order.

    Example:
        router = LLMRouter()
        response = router.generate("Write a LinkedIn post about AI")
    """

    def __init__(
        self,
        primary_model: str | None = None,
        fallback_models: list[str] | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
    ):
        """Initialize the LLM router.

        Args:
            primary_model: Primary model to use (default from settings)
            fallback_models: List of fallback models (default from settings)
            temperature: Generation temperature (default from settings)
            max_tokens: Maximum tokens to generate (default from settings)
        """
        self.primary_model = primary_model or settings.primary_model
        self.fallback_models = fallback_models or settings.fallback_models_list
        self.temperature = temperature or settings.llm_temperature
        self.max_tokens = max_tokens or settings.llm_max_tokens

        # Build model chain (primary + fallbacks)
        self.model_chain = [self.primary_model] + self.fallback_models

        # Retry configuration
        self.max_retries = 3

    def generate(
        self,
        prompt: str,
        system_prompt: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
    ) -> str:
        """Generate text using LLM with fallback chain.

        Args:
            prompt: User prompt for generation
            system_prompt: Optional system prompt for context
            temperature: Override default temperature
            max_tokens: Override default max tokens

        Returns:
            Generated text from the LLM

        Raises:
            Exception: If all models in the chain fail
        """
        temp = temperature if temperature is not None else self.temperature
        max_tok = max_tokens if max_tokens is not None else self.max_tokens

        for model in self.model_chain:
            try:
                response = self._call_model_with_retry(model, prompt, system_prompt, temp, max_tok)
                logger.info(f"Successfully generated with {model}")
                return response
            except Exception as e:
                logger.warning(f"Model {model} failed: {e}")
                continue

        raise Exception("All models in fallback chain failed")

    def generate_structured(
        self,
        prompt: str,
        response_model: type[T],
        system_prompt: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
    ) -> T:
        """Generate structured output using Pydantic model with fallback chain.

        This method ensures the LLM returns properly formatted and validated data
        according to the specified Pydantic model. This is more robust than asking
        for JSON in the prompt and parsing it manually.

        Args:
            prompt: User prompt for generation
            response_model: Pydantic model class for structured output
            system_prompt: Optional system prompt for context
            temperature: Override default temperature
            max_tokens: Override default max tokens

        Returns:
            Instance of response_model with validated data from LLM

        Raises:
            Exception: If all models in the chain fail

        Example:
            class MyOutput(BaseModel):
                title: str
                tags: list[str]

            router = LLMRouter()
            result = router.generate_structured(
                prompt="Analyze this topic",
                response_model=MyOutput
            )
            # result.title and result.tags are guaranteed to exist and be valid
        """
        temp = temperature if temperature is not None else self.temperature
        max_tok = max_tokens if max_tokens is not None else self.max_tokens

        for model in self.model_chain:
            try:
                response = self._call_model_structured_with_retry(
                    model, prompt, response_model, system_prompt, temp, max_tok
                )
                logger.info(f"Successfully generated structured output with {model}")
                return response
            except Exception as e:
                logger.warning(f"Model {model} failed for structured output: {e}")
                continue

        raise Exception("All models in fallback chain failed for structured output")

    def _call_model_with_retry(
        self,
        model: str,
        prompt: str,
        system_prompt: str | None,
        temperature: float,
        max_tokens: int,
    ) -> str:
        """Call model with exponential backoff retry.

        Args:
            model: Model identifier
            prompt: User prompt
            system_prompt: System prompt
            temperature: Generation temperature
            max_tokens: Maximum tokens

        Returns:
            Generated text

        Raises:
            Exception: If all retries fail
        """
        for attempt in range(self.max_retries):
            try:
                return self._call_model(model, prompt, system_prompt, temperature, max_tokens)
            except Exception:
                if attempt < self.max_retries - 1:
                    sleep_time = 2**attempt
                    logger.debug(f"Retry {attempt + 1} after {sleep_time}s")
                    time.sleep(sleep_time)
                else:
                    raise

    def _call_model_structured_with_retry(
        self,
        model: str,
        prompt: str,
        response_model: type[T],
        system_prompt: str | None,
        temperature: float,
        max_tokens: int,
    ) -> T:
        """Call model with structured output and exponential backoff retry.

        Args:
            model: Model identifier
            prompt: User prompt
            response_model: Pydantic model for structured output
            system_prompt: System prompt
            temperature: Generation temperature
            max_tokens: Maximum tokens

        Returns:
            Pydantic model instance with validated data

        Raises:
            Exception: If all retries fail
        """
        for attempt in range(self.max_retries):
            try:
                return self._call_model_structured(
                    model, prompt, response_model, system_prompt, temperature, max_tokens
                )
            except Exception:
                if attempt < self.max_retries - 1:
                    sleep_time = 2**attempt
                    logger.debug(f"Retry {attempt + 1} after {sleep_time}s")
                    time.sleep(sleep_time)
                else:
                    raise

    def _call_model(
        self,
        model: str,
        prompt: str,
        system_prompt: str | None,
        temperature: float,
        max_tokens: int,
    ) -> str:
        """Call a specific model via OpenRouter.

        Args:
            model: Model identifier (e.g., "anthropic/claude-3.5-sonnet")
            prompt: User prompt
            system_prompt: System prompt
            temperature: Generation temperature
            max_tokens: Maximum tokens

        Returns:
            Generated text
        """
        client = self._create_client(model)

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        response = client.invoke(messages)
        return response.content

    def _call_model_structured(
        self,
        model: str,
        prompt: str,
        response_model: type[T],
        system_prompt: str | None,
        temperature: float,
        max_tokens: int,
    ) -> T:
        """Call a specific model with structured output via OpenRouter.

        Uses LangChain's with_structured_output() to ensure the LLM returns
        properly formatted data matching the Pydantic model.

        Args:
            model: Model identifier (e.g., "anthropic/claude-3.5-sonnet")
            prompt: User prompt
            response_model: Pydantic model for structured output
            system_prompt: System prompt
            temperature: Generation temperature
            max_tokens: Maximum tokens

        Returns:
            Pydantic model instance with validated data from LLM
        """
        client = self._create_client(model, temperature, max_tokens)

        # Configure client for structured output
        structured_client = client.with_structured_output(response_model)

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        response = structured_client.invoke(messages)
        return response

    def _create_client(
        self,
        model: str,
        temperature: float | None = None,
        max_tokens: int | None = None,
    ) -> ChatOpenAI:
        """Create LangChain ChatOpenAI client for OpenRouter.

        Args:
            model: Model identifier
            temperature: Optional temperature override
            max_tokens: Optional max_tokens override

        Returns:
            Configured ChatOpenAI client
        """
        return ChatOpenAI(
            model=model,
            openai_api_key=settings.openrouter_api_key,
            openai_api_base="https://openrouter.ai/api/v1",
            temperature=temperature or self.temperature,
            max_tokens=max_tokens or self.max_tokens,
        )
