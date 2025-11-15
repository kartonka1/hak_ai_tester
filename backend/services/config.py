import os
from functools import lru_cache
from pydantic import BaseModel
from dotenv import load_dotenv

# Загружаем переменные окружения из .env, если файл существует.
# Это упрощает локальную настройку, включая переключение между OpenAI и Ollama.
load_dotenv()


class Settings(BaseModel):
	openai_api_key: str | None = os.getenv("OPENAI_API_KEY")
	openai_base_url: str | None = os.getenv("OPENAI_BASE_URL")
	openai_model: str = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
	github_token: str | None = os.getenv("GITHUB_TOKEN")
	default_repo_root: str = os.getenv("DEFAULT_REPO_ROOT", ".")
	ai_provider: str = os.getenv("AI_PROVIDER", "openai")  # openai | ollama
	ollama_base_url: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
	ollama_model: str = os.getenv("OLLAMA_MODEL", "llama3")


@lru_cache
def get_settings() -> Settings:
	return Settings()


