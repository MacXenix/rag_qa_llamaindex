from llama_index.core import Settings

from app.core.config import Settings as AppSettings
from app.core.config import settings as default_settings


def configure_provider(app_settings: AppSettings = default_settings) -> None:
    """Read LLM_PROVIDER from config and wire up LlamaIndex Settings."""
    provider = app_settings.llm_provider.lower()

    if provider == "ollama":
        _configure_ollama(app_settings)
    elif provider == "openai":
        _configure_openai(app_settings)
    elif provider == "gemini":
        _configure_gemini(app_settings)
    else:
        raise ValueError(
            f"Unknown LLM_PROVIDER: {provider!r}. Must be ollama, openai, or gemini."
        )


def _configure_ollama(app_settings: AppSettings) -> None:
    from llama_index.llms.ollama import Ollama
    from llama_index.embeddings.ollama import OllamaEmbedding

    Settings.llm = Ollama(
        model="llama3.2",
        base_url=app_settings.ollama_base_url,
        request_timeout=120.0,
    )
    Settings.embed_model = OllamaEmbedding(
        model_name="nomic-embed-text",
        base_url=app_settings.ollama_base_url,
    )


def _configure_openai(app_settings: AppSettings) -> None:
    from llama_index.llms.openai import OpenAI
    from llama_index.embeddings.openai import OpenAIEmbedding

    Settings.llm = OpenAI(
        model="gpt-4o-mini",
        api_key=app_settings.openai_api_key,
    )
    Settings.embed_model = OpenAIEmbedding(
        model="text-embedding-3-small",
        api_key=app_settings.openai_api_key,
    )


def _configure_gemini(app_settings: AppSettings) -> None:
    from llama_index.llms.gemini import Gemini
    from llama_index.embeddings.gemini import GeminiEmbedding

    Settings.llm = Gemini(
        model="models/gemini-1.5-flash",
        api_key=app_settings.gemini_api_key,
    )
    Settings.embed_model = GeminiEmbedding(
        model_name="models/text-embedding-004",
        api_key=app_settings.gemini_api_key,
    )