from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    supabase_url: str = Field(..., env="SUPABASE_URL")
    supabase_anon_key: str = Field(..., env="SUPABASE_ANON_KEY")
    supabase_service_role_key: str = Field(..., env="SUPABASE_SERVICE_ROLE_KEY")

    ai_provider: Literal["openai", "anthropic"] = Field(default="openai", env="AI_PROVIDER")

    openai_api_key: str = Field(..., env="OPENAI_API_KEY")
    openai_embed_model: str = Field(default="text-embedding-3-small", env="OPENAI_EMBED_MODEL")
    openai_chat_model: str = Field(default="gpt-4o", env="OPENAI_CHAT_MODEL")

    anthropic_api_key: str = Field(default="", env="ANTHROPIC_API_KEY")
    anthropic_chat_model: str = Field(default="claude-3-5-sonnet-20240620", env="ANTHROPIC_CHAT_MODEL")

    environment: str = Field(default="development", env="ENVIRONMENT")
    log_level: str = Field(default="INFO", env="LOG_LEVEL")

    default_top_k: int = Field(default=6)
    chunk_size: int = Field(default=400)
    chunk_overlap: int = Field(default=60)
    temperature: float = Field(default=0.1)
    embedding_dimensions: int = Field(default=1536)

    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "ignore"


settings = Settings()


def get_settings() -> Settings:
    return settings
