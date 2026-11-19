from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=ROOT / ".env", extra="ignore")

    database_url: str = "postgresql+psycopg://finops:finops@127.0.0.1:5432/finops"
    org_code: str = "simpar"                 # tenant padrao; em SaaS vem do token/header
    secret_key: str = ""                     # chave Fernet; se vazia, gera arquivo .secret_key local
    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173,http://localhost:8000,http://127.0.0.1:8000,http://localhost:8888,http://127.0.0.1:8888"


settings = Settings()
