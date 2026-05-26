from app.core.config import Settings as AppSettings
from app.core.config import settings as default_settings


def validate_provider_config(app_settings: AppSettings = default_settings) -> None:
    """Fail fast at startup if the provider's required config is missing."""
    provider = app_settings.llm_provider.lower()

    if provider not in ("ollama", "openai", "gemini"):
        raise RuntimeError(
            f"Unknown LLM_PROVIDER: {provider!r}. Must be ollama, openai, or gemini."
        )

    if provider == "openai" and not app_settings.openai_api_key:
        raise RuntimeError(
            "LLM_PROVIDER=openai but OPENAI_API_KEY is not set in .env"
        )

    if provider == "gemini" and not app_settings.gemini_api_key:
        raise RuntimeError(
            "LLM_PROVIDER=gemini but GEMINI_API_KEY is not set in .env"
        )


async def run_startup() -> None:
    """Called from FastAPI lifespan — validate config then wire LlamaIndex."""
    validate_provider_config()

    from app.services.provider_factory import configure_provider
    configure_provider()