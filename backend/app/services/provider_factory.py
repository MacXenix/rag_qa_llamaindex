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
    elif provider == "groq":
        _configure_groq(app_settings)
    else:
        raise ValueError(
            f"Unknown LLM_PROVIDER: {provider!r}. Must be ollama, openai, gemini, or groq."
        )

    # Set explicit global context window and max output tokens to prevent negative context window calculations in PromptHelper
    Settings.context_window = 16384
    Settings.num_output = 1024
    Settings.chunk_size = 512
    Settings.chunk_overlap = 64


def _configure_ollama(app_settings: AppSettings) -> None:
    from llama_index.llms.ollama import Ollama
    from llama_index.embeddings.ollama import OllamaEmbedding

    Settings.llm = Ollama(
        model=app_settings.ollama_llm_model,
        base_url=app_settings.ollama_base_url,
        request_timeout=120.0,
        context_window=16384,
    )
    
    # Nomic embedding model requires search prefixes for correct retrieval
    model_name = app_settings.ollama_embedding_model
    is_nomic = "nomic" in model_name.lower()
    Settings.embed_model = OllamaEmbedding(
        model_name=model_name,
        base_url=app_settings.ollama_base_url,
        query_instruction="search_query: " if is_nomic else None,
        text_instruction="search_document: " if is_nomic else None,
    )


def _configure_openai(app_settings: AppSettings) -> None:
    from llama_index.llms.openai import OpenAI
    from llama_index.embeddings.openai import OpenAIEmbedding

    Settings.llm = OpenAI(
        model=app_settings.openai_llm_model,
        api_key=app_settings.openai_api_key,
    )
    Settings.embed_model = OpenAIEmbedding(
        model_name=app_settings.openai_embedding_model,
        api_key=app_settings.openai_api_key,
    )


def _configure_groq(app_settings: AppSettings) -> None:
    from llama_index.llms.groq import Groq
    from llama_index.embeddings.ollama import OllamaEmbedding

    Settings.llm = Groq(
        model=app_settings.groq_llm_model,
        api_key=app_settings.groq_api_key,
    )
    
    # Nomic embedding model requires search prefixes for correct retrieval
    model_name = app_settings.groq_embedding_model
    is_nomic = "nomic" in model_name.lower()
    Settings.embed_model = OllamaEmbedding(
        model_name=model_name,
        base_url=app_settings.ollama_base_url,
        query_instruction="search_query: " if is_nomic else None,
        text_instruction="search_document: " if is_nomic else None,
    )


def _configure_gemini(app_settings: AppSettings) -> None:
    from llama_index.llms.google_genai import GoogleGenAI
    from llama_index.embeddings.ollama import OllamaEmbedding

    Settings.llm = GoogleGenAI(
        model=app_settings.gemini_llm_model,
        api_key=app_settings.gemini_api_key,
    )
    # Gemini embedding API has v1beta incompatibilities — use Ollama instead.
    # Nomic embedding model requires search prefixes for correct retrieval
    model_name = app_settings.gemini_embedding_model
    is_nomic = "nomic" in model_name.lower()
    Settings.embed_model = OllamaEmbedding(
        model_name=model_name,
        base_url=app_settings.ollama_base_url,
        query_instruction="search_query: " if is_nomic else None,
        text_instruction="search_document: " if is_nomic else None,
    )