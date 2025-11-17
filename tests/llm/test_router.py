"""Tests for LLM router with fallback chain."""

from unittest.mock import MagicMock, patch

import pytest
from langchain_core.messages import AIMessage

from src.llm.router import LLMRouter


class TestLLMRouter:
    """Test suite for LLMRouter class."""

    def test_initialization_with_defaults(self):
        """Test router initializes with default settings."""
        router = LLMRouter()

        assert router.primary_model == "anthropic/claude-3.5-sonnet"
        assert router.fallback_models == ["openai/gpt-4o", "openai/gpt-3.5-turbo"]
        assert router.temperature == 0.7
        assert router.max_tokens == 2000
        assert router.model_chain == [
            "anthropic/claude-3.5-sonnet",
            "openai/gpt-4o",
            "openai/gpt-3.5-turbo",
        ]

    def test_initialization_with_custom_values(self):
        """Test router initializes with custom values."""
        router = LLMRouter(
            primary_model="openai/gpt-4",
            fallback_models=["openai/gpt-3.5-turbo"],
            temperature=0.5,
            max_tokens=1000,
        )

        assert router.primary_model == "openai/gpt-4"
        assert router.fallback_models == ["openai/gpt-3.5-turbo"]
        assert router.temperature == 0.5
        assert router.max_tokens == 1000
        assert router.model_chain == ["openai/gpt-4", "openai/gpt-3.5-turbo"]

    @patch("src.llm.router.LLMRouter._call_model_with_retry")
    def test_primary_model_success(self, mock_call_model_retry):
        """Test successful call to primary model."""
        mock_call_model_retry.return_value = "Generated response from Claude"

        router = LLMRouter()
        result = router.generate("Test prompt")

        assert result == "Generated response from Claude"
        mock_call_model_retry.assert_called_once()
        # Verify it was called with the primary model
        call_args = mock_call_model_retry.call_args
        assert call_args[0][0] == "anthropic/claude-3.5-sonnet"

    @patch("src.llm.router.LLMRouter._call_model_with_retry")
    def test_fallback_on_primary_failure(self, mock_call_model_retry):
        """Test fallback to second model when primary fails."""
        # First call (primary) fails, second call (fallback) succeeds
        mock_call_model_retry.side_effect = [
            Exception("Primary model failed"),
            "Response from GPT-4o",
        ]

        router = LLMRouter()
        result = router.generate("Test prompt")

        assert result == "Response from GPT-4o"
        assert mock_call_model_retry.call_count == 2
        # Verify it tried primary first, then fallback
        assert mock_call_model_retry.call_args_list[0][0][0] == "anthropic/claude-3.5-sonnet"
        assert mock_call_model_retry.call_args_list[1][0][0] == "openai/gpt-4o"

    @patch("src.llm.router.LLMRouter._call_model_with_retry")
    def test_all_models_fail(self, mock_call_model_retry):
        """Test exception raised when all models fail."""
        # All models fail
        mock_call_model_retry.side_effect = [
            Exception("Claude failed"),
            Exception("GPT-4o failed"),
            Exception("GPT-3.5 failed"),
        ]

        router = LLMRouter()

        with pytest.raises(Exception) as exc_info:
            router.generate("Test prompt")

        assert "All models in fallback chain failed" in str(exc_info.value)
        assert mock_call_model_retry.call_count == 3

    @patch("src.llm.router.LLMRouter._call_model_with_retry")
    def test_system_prompt_passed(self, mock_call_model_retry):
        """Test system prompt is passed to model call."""
        mock_call_model_retry.return_value = "Response"

        router = LLMRouter()
        router.generate("User prompt", system_prompt="You are a helpful assistant")

        call_args = mock_call_model_retry.call_args
        assert call_args[0][2] == "You are a helpful assistant"

    @patch("src.llm.router.LLMRouter._call_model_with_retry")
    def test_temperature_override(self, mock_call_model_retry):
        """Test custom temperature overrides default."""
        mock_call_model_retry.return_value = "Response"

        router = LLMRouter(temperature=0.7)
        router.generate("Test prompt", temperature=0.9)

        call_args = mock_call_model_retry.call_args
        assert call_args[0][3] == 0.9

    @patch("src.llm.router.LLMRouter._call_model_with_retry")
    def test_max_tokens_override(self, mock_call_model_retry):
        """Test custom max_tokens overrides default."""
        mock_call_model_retry.return_value = "Response"

        router = LLMRouter(max_tokens=2000)
        router.generate("Test prompt", max_tokens=500)

        call_args = mock_call_model_retry.call_args
        assert call_args[0][4] == 500

    @patch("src.llm.router.ChatOpenAI")
    def test_call_model_success(self, mock_chat_openai):
        """Test _call_model makes correct API call."""
        # Mock the ChatOpenAI instance and its invoke method
        mock_client = MagicMock()
        mock_response = AIMessage(content="Generated text")
        mock_client.invoke.return_value = mock_response
        mock_chat_openai.return_value = mock_client

        router = LLMRouter()
        result = router._call_model(
            model="anthropic/claude-3.5-sonnet",
            prompt="Test prompt",
            system_prompt="System context",
            temperature=0.7,
            max_tokens=2000,
        )

        assert result == "Generated text"
        # Verify client was created with correct parameters
        mock_chat_openai.assert_called_once()
        # Verify invoke was called with messages
        mock_client.invoke.assert_called_once()
        messages = mock_client.invoke.call_args[0][0]
        assert len(messages) == 2
        assert messages[0]["role"] == "system"
        assert messages[0]["content"] == "System context"
        assert messages[1]["role"] == "user"
        assert messages[1]["content"] == "Test prompt"

    @patch("src.llm.router.ChatOpenAI")
    def test_call_model_without_system_prompt(self, mock_chat_openai):
        """Test _call_model works without system prompt."""
        mock_client = MagicMock()
        mock_response = AIMessage(content="Generated text")
        mock_client.invoke.return_value = mock_response
        mock_chat_openai.return_value = mock_client

        router = LLMRouter()
        result = router._call_model(
            model="anthropic/claude-3.5-sonnet",
            prompt="Test prompt",
            system_prompt=None,
            temperature=0.7,
            max_tokens=2000,
        )

        assert result == "Generated text"
        messages = mock_client.invoke.call_args[0][0]
        assert len(messages) == 1
        assert messages[0]["role"] == "user"
        assert messages[0]["content"] == "Test prompt"

    @patch("src.llm.router.ChatOpenAI")
    @patch("src.llm.router.time.sleep")
    def test_retry_logic_with_exponential_backoff(self, mock_sleep, mock_chat_openai):
        """Test retry logic with exponential backoff."""
        mock_client = MagicMock()
        # Fail twice, succeed on third attempt
        mock_client.invoke.side_effect = [
            Exception("API error 1"),
            Exception("API error 2"),
            AIMessage(content="Success on retry"),
        ]
        mock_chat_openai.return_value = mock_client

        router = LLMRouter()
        result = router._call_model_with_retry(
            model="anthropic/claude-3.5-sonnet",
            prompt="Test prompt",
            system_prompt=None,
            temperature=0.7,
            max_tokens=2000,
        )

        assert result == "Success on retry"
        # Verify exponential backoff sleep times
        assert mock_sleep.call_count == 2
        assert mock_sleep.call_args_list[0][0][0] == 1  # 2^0 = 1
        assert mock_sleep.call_args_list[1][0][0] == 2  # 2^1 = 2

    @patch("src.llm.router.ChatOpenAI")
    @patch("src.llm.router.time.sleep")
    def test_retry_exhaustion(self, mock_sleep, mock_chat_openai):
        """Test exception raised when retries exhausted."""
        mock_client = MagicMock()
        # Fail all attempts
        mock_client.invoke.side_effect = Exception("Persistent API error")
        mock_chat_openai.return_value = mock_client

        router = LLMRouter()

        with pytest.raises(Exception) as exc_info:
            router._call_model_with_retry(
                model="anthropic/claude-3.5-sonnet",
                prompt="Test prompt",
                system_prompt=None,
                temperature=0.7,
                max_tokens=2000,
            )

        assert "Persistent API error" in str(exc_info.value)
        # Max retries is 3, so should try 3 times total
        assert mock_client.invoke.call_count == 3
        # Should sleep 2 times (between attempts 1-2 and 2-3)
        assert mock_sleep.call_count == 2

    def test_create_client(self):
        """Test _create_client creates properly configured client."""
        router = LLMRouter()
        client = router._create_client("anthropic/claude-3.5-sonnet")

        assert client.model_name == "anthropic/claude-3.5-sonnet"
        assert client.openai_api_base == "https://openrouter.ai/api/v1"
        assert client.temperature == 0.7
        assert client.max_tokens == 2000
