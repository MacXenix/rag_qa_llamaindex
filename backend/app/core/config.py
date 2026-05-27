from pydantic_settings import BaseSettings, SettingsConfigDict, PydanticBaseSettingsSource


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    llm_provider: str = "ollama"

    # Model names — override in .env to switch without touching code
    ollama_llm_model: str = "llama3.2"
    ollama_embedding_model: str = "nomic-embed-text"
    openai_llm_model: str = "gpt-4o-mini"
    openai_embedding_model: str = "text-embedding-3-small"
    gemini_llm_model: str = "gemini-2.0-flash"
    gemini_embedding_model: str = "nomic-embed-text"  # via Ollama
    groq_llm_model: str = "llama-3.1-70b-versatile"
    groq_embedding_model: str = "nomic-embed-text"  # via Ollama

    openai_api_key: str = ""
    gemini_api_key: str = ""
    groq_api_key: str = ""
    ollama_base_url: str = "http://localhost:11434"

    database_url: str = "postgresql+asyncpg://ragqa:ragqa@localhost:5432/ragqa"

    chroma_host: str = "localhost"
    chroma_port: int = 8001

    tavily_api_key: str = ""
    
    retrieval_mode: str = "basic"  # basic | hyde | rerank | hyde+rerank | multiquery

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,  # ← was secrets_dir
    ) -> tuple[PydanticBaseSettingsSource, ...]:
        # dotenv takes priority over system env vars
        return init_settings, dotenv_settings, env_settings, file_secret_settings


settings = Settings()