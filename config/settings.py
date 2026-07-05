from dotenv import load_dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict

load_dotenv()


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    ADK_APP_NAME: str
    APP_VERSION: str
    EXPOSE_API_DOCS: bool
    AGENT_THINKING_ENABLED: bool = True

    OPENAI_API_KEY: str
    OPENAI_TEXT_MODEL_DEFAULT: str
    OPENAI_TEXT_MODEL_CHEAP: str
    OPENAI_TEXT_MODEL_HEAVY: str
    OPENAI_EMBED_MODEL_DEFAULT: str
    OPENAI_IMAGE_MODEL_DEFAULT: str
    OPENAI_TTS_MODEL_DEFAULT: str
    OPENAI_REALTIME_MODEL_DEFAULT: str

    GOOGLE_GENAI_USE_VERTEXAI: int
    GEMINI_API_KEY: str
    GEMINI_TEXT_MODEL_DEFAULT: str


settings = Settings()
