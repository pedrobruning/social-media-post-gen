"""Tests for Langfuse observability integration."""

from unittest.mock import MagicMock, patch

from src.llm.observability import ObservabilityManager


class TestObservabilityManager:
    """Test suite for ObservabilityManager class."""

    @patch("src.llm.observability.settings")
    @patch("src.llm.observability.Langfuse")
    def test_initialization_with_credentials(self, mock_langfuse, mock_settings):
        """Test observability manager initializes when credentials available."""
        mock_settings.langfuse_public_key = "pk-test"
        mock_settings.langfuse_secret_key = "sk-test"
        mock_settings.langfuse_host = "https://cloud.langfuse.com"

        obs = ObservabilityManager()

        assert obs.enabled is True
        assert obs.client is not None
        mock_langfuse.assert_called_once_with(
            public_key="pk-test",
            secret_key="sk-test",
            host="https://cloud.langfuse.com",
        )

    @patch("src.llm.observability.settings")
    def test_initialization_without_credentials(self, mock_settings):
        """Test observability manager disables when credentials missing."""
        mock_settings.langfuse_public_key = ""
        mock_settings.langfuse_secret_key = ""

        obs = ObservabilityManager()

        assert obs.enabled is False
        assert obs.client is None

    @patch("src.llm.observability.settings")
    @patch("src.llm.observability.Langfuse")
    def test_trace_llm_call_enabled(self, mock_langfuse, mock_settings):
        """Test trace_llm_call logs when enabled."""
        mock_settings.langfuse_public_key = "pk-test"
        mock_settings.langfuse_secret_key = "sk-test"
        mock_settings.langfuse_host = "https://cloud.langfuse.com"

        mock_client = MagicMock()
        mock_langfuse.return_value = mock_client

        obs = ObservabilityManager()
        obs.trace_llm_call(
            model="gpt-4",
            prompt="Test prompt",
            response="Test response",
            tokens=50,
            latency_ms=150.5,
            metadata={"post_id": 1, "platform": "linkedin"},
        )

        # Verify generation was created
        mock_client.generation.assert_called_once()
        call_kwargs = mock_client.generation.call_args[1]
        assert call_kwargs["model"] == "gpt-4"
        assert call_kwargs["input"] == "Test prompt"
        assert call_kwargs["output"] == "Test response"
        assert call_kwargs["usage"]["total_tokens"] == 50
        assert "post_id" in call_kwargs["metadata"]
        assert call_kwargs["metadata"]["post_id"] == 1

    @patch("src.llm.observability.settings")
    def test_trace_llm_call_disabled(self, mock_settings):
        """Test trace_llm_call does nothing when disabled."""
        mock_settings.langfuse_public_key = ""
        mock_settings.langfuse_secret_key = ""

        obs = ObservabilityManager()
        # Should not raise exception
        obs.trace_llm_call(
            model="gpt-4",
            prompt="Test",
            response="Response",
            tokens=10,
            latency_ms=100,
        )

        # No assertions needed - just verify no exception

    @patch("src.llm.observability.settings")
    @patch("src.llm.observability.Langfuse")
    def test_trace_agent_execution_enabled(self, mock_langfuse, mock_settings):
        """Test trace_agent_execution logs when enabled."""
        mock_settings.langfuse_public_key = "pk-test"
        mock_settings.langfuse_secret_key = "sk-test"
        mock_settings.langfuse_host = "https://cloud.langfuse.com"

        mock_client = MagicMock()
        mock_langfuse.return_value = mock_client

        obs = ObservabilityManager()
        obs.trace_agent_execution(
            post_id=1,
            topic="AI trends",
            status="approved",
            duration_ms=5000.0,
            metadata={"total_tokens": 500},
        )

        # Verify trace was created
        mock_client.trace.assert_called_once()
        call_kwargs = mock_client.trace.call_args[1]
        assert call_kwargs["name"] == "agent_execution"
        assert call_kwargs["metadata"]["post_id"] == 1
        assert call_kwargs["metadata"]["topic"] == "AI trends"
        assert call_kwargs["metadata"]["status"] == "approved"
        assert call_kwargs["metadata"]["duration_ms"] == 5000.0

    @patch("src.llm.observability.settings")
    def test_trace_agent_execution_disabled(self, mock_settings):
        """Test trace_agent_execution does nothing when disabled."""
        mock_settings.langfuse_public_key = ""
        mock_settings.langfuse_secret_key = ""

        obs = ObservabilityManager()
        # Should not raise exception
        obs.trace_agent_execution(
            post_id=1,
            topic="Test",
            status="approved",
            duration_ms=1000.0,
        )

    @patch("src.llm.observability.settings")
    @patch("src.llm.observability.Langfuse")
    def test_trace_custom_event_enabled(self, mock_langfuse, mock_settings):
        """Test trace_custom_event logs when enabled."""
        mock_settings.langfuse_public_key = "pk-test"
        mock_settings.langfuse_secret_key = "sk-test"
        mock_settings.langfuse_host = "https://cloud.langfuse.com"

        mock_client = MagicMock()
        mock_langfuse.return_value = mock_client

        obs = ObservabilityManager()
        obs.trace_custom_event(
            event_name="image_generation",
            post_id=1,
            data={"model": "dall-e-3", "size": "1024x1024"},
        )

        # Verify event was created
        mock_client.event.assert_called_once()
        call_kwargs = mock_client.event.call_args[1]
        assert call_kwargs["name"] == "image_generation"
        assert call_kwargs["metadata"]["post_id"] == 1
        assert call_kwargs["metadata"]["model"] == "dall-e-3"

    @patch("src.llm.observability.settings")
    def test_trace_custom_event_disabled(self, mock_settings):
        """Test trace_custom_event does nothing when disabled."""
        mock_settings.langfuse_public_key = ""
        mock_settings.langfuse_secret_key = ""

        obs = ObservabilityManager()
        # Should not raise exception
        obs.trace_custom_event(
            event_name="test_event",
            post_id=1,
            data={"key": "value"},
        )

    @patch("src.llm.observability.settings")
    @patch("src.llm.observability.Langfuse")
    def test_flush_enabled(self, mock_langfuse, mock_settings):
        """Test flush calls Langfuse flush when enabled."""
        mock_settings.langfuse_public_key = "pk-test"
        mock_settings.langfuse_secret_key = "sk-test"
        mock_settings.langfuse_host = "https://cloud.langfuse.com"

        mock_client = MagicMock()
        mock_langfuse.return_value = mock_client

        obs = ObservabilityManager()
        obs.flush()

        mock_client.flush.assert_called_once()

    @patch("src.llm.observability.settings")
    def test_flush_disabled(self, mock_settings):
        """Test flush does nothing when disabled."""
        mock_settings.langfuse_public_key = ""
        mock_settings.langfuse_secret_key = ""

        obs = ObservabilityManager()
        # Should not raise exception
        obs.flush()

    @patch("src.llm.observability.settings")
    @patch("src.llm.observability.Langfuse")
    def test_trace_llm_call_without_metadata(self, mock_langfuse, mock_settings):
        """Test trace_llm_call works without metadata."""
        mock_settings.langfuse_public_key = "pk-test"
        mock_settings.langfuse_secret_key = "sk-test"
        mock_settings.langfuse_host = "https://cloud.langfuse.com"

        mock_client = MagicMock()
        mock_langfuse.return_value = mock_client

        obs = ObservabilityManager()
        obs.trace_llm_call(
            model="gpt-4",
            prompt="Test",
            response="Response",
            tokens=10,
            latency_ms=100,
            metadata=None,
        )

        mock_client.generation.assert_called_once()
        call_kwargs = mock_client.generation.call_args[1]
        assert call_kwargs["metadata"] == {}

    @patch("src.llm.observability.settings")
    @patch("src.llm.observability.Langfuse")
    def test_trace_agent_execution_without_metadata(self, mock_langfuse, mock_settings):
        """Test trace_agent_execution works without metadata."""
        mock_settings.langfuse_public_key = "pk-test"
        mock_settings.langfuse_secret_key = "sk-test"
        mock_settings.langfuse_host = "https://cloud.langfuse.com"

        mock_client = MagicMock()
        mock_langfuse.return_value = mock_client

        obs = ObservabilityManager()
        obs.trace_agent_execution(
            post_id=1,
            topic="Test",
            status="approved",
            duration_ms=1000,
            metadata=None,
        )

        mock_client.trace.assert_called_once()
        call_kwargs = mock_client.trace.call_args[1]
        # Should still have basic metadata
        assert "post_id" in call_kwargs["metadata"]
        assert "topic" in call_kwargs["metadata"]
