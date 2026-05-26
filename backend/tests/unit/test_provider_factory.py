import pytest
from unittest.mock import MagicMock, patch

from app.core.startup import validate_provider_config
from app.services.provider_factory import configure_provider


class TestValidateProviderConfig:
    def test_ollama_is_valid(self):
        cfg = MagicMock()
        cfg.llm_provider = "ollama"
        validate_provider_config(cfg)  # should not raise

    def test_openai_without_key_raises(self):
        cfg = MagicMock()
        cfg.llm_provider = "openai"
        cfg.openai_api_key = ""
        with pytest.raises(RuntimeError, match="OPENAI_API_KEY"):
            validate_provider_config(cfg)

    def test_gemini_without_key_raises(self):
        cfg = MagicMock()
        cfg.llm_provider = "gemini"
        cfg.gemini_api_key = ""
        with pytest.raises(RuntimeError, match="GEMINI_API_KEY"):
            validate_provider_config(cfg)

    def test_unknown_provider_raises(self):
        cfg = MagicMock()
        cfg.llm_provider = "unknown"
        with pytest.raises(RuntimeError, match="Unknown LLM_PROVIDER"):
            validate_provider_config(cfg)

    def test_openai_with_key_is_valid(self):
        cfg = MagicMock()
        cfg.llm_provider = "openai"
        cfg.openai_api_key = "sk-test-key"
        validate_provider_config(cfg)  # should not raise

    def test_gemini_with_key_is_valid(self):
        cfg = MagicMock()
        cfg.llm_provider = "gemini"
        cfg.gemini_api_key = "test-gemini-key"
        validate_provider_config(cfg)  # should not raise


class TestConfigureProvider:
    def test_unknown_provider_raises_value_error(self):
        cfg = MagicMock()
        cfg.llm_provider = "unknown"
        with pytest.raises(ValueError, match="Unknown LLM_PROVIDER"):
            configure_provider(cfg)

    def test_ollama_delegates_to_configure_ollama(self):
        cfg = MagicMock()
        cfg.llm_provider = "ollama"
        with patch("app.services.provider_factory._configure_ollama") as mock_fn:
            configure_provider(cfg)
            mock_fn.assert_called_once_with(cfg)

    def test_openai_delegates_to_configure_openai(self):
        cfg = MagicMock()
        cfg.llm_provider = "openai"
        with patch("app.services.provider_factory._configure_openai") as mock_fn:
            configure_provider(cfg)
            mock_fn.assert_called_once_with(cfg)

    def test_gemini_delegates_to_configure_gemini(self):
        cfg = MagicMock()
        cfg.llm_provider = "gemini"
        with patch("app.services.provider_factory._configure_gemini") as mock_fn:
            configure_provider(cfg)
            mock_fn.assert_called_once_with(cfg)

    def test_provider_matching_is_case_insensitive(self):
        cfg = MagicMock()
        cfg.llm_provider = "Ollama"
        with patch("app.services.provider_factory._configure_ollama") as mock_fn:
            configure_provider(cfg)
            mock_fn.assert_called_once_with(cfg)