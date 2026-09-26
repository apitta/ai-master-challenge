"""Configuração via variáveis de ambiente (12-factor, pronto para container)."""

from datetime import date
from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # "sqlite://" = banco em memória. Use "sqlite:////data/app.db" para persistir em disco.
    database_url: str = "sqlite://"
    seed_file: Path = ROOT_DIR / "data" / "lead_scoring_pipeline.xlsx"
    # Sobrescreve a data de referência da planilha (os dados param em 31/12/2017).
    reference_date: date | None = None


@lru_cache
def get_settings() -> Settings:
    return Settings()
