from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "HotComment-AI"
    llm_provider: str = Field(default="openai", validation_alias="LLM_PROVIDER")
    openai_api_key: str | None = Field(default=None, validation_alias="OPENAI_API_KEY")
    openai_base_url: str | None = Field(default=None, validation_alias="OPENAI_BASE_URL")
    openai_model: str = Field(default="gpt-4o-mini", validation_alias="OPENAI_MODEL")
    openai_embedding_model: str = Field(
        default="text-embedding-3-small", validation_alias="OPENAI_EMBEDDING_MODEL"
    )
    use_openai_embeddings: bool = Field(default=False, validation_alias="USE_OPENAI_EMBEDDINGS")
    request_timeout_seconds: float = Field(default=30.0, validation_alias="REQUEST_TIMEOUT_SECONDS")
    knowledge_dir: Path = Field(default=Path("app/knowledge"), validation_alias="KNOWLEDGE_DIR")
    rag_index_path: Path = Field(default=Path(".rag_index/index.json"), validation_alias="RAG_INDEX_PATH")

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


@lru_cache
def get_settings() -> Settings:
    return Settings()
