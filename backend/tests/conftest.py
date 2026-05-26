from unittest.mock import patch

import pytest


@pytest.fixture(autouse=True)
def mock_llamaindex_startup():
    """Prevent LlamaIndex from trying to connect to Ollama during tests."""
    with patch("app.services.provider_factory.configure_provider"):
        yield