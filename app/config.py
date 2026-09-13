from pathlib import Path

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="MYLIC_", env_file=".env", extra="ignore")

    database_url: str
    pdf_dir: str = "./pdfs"

    @field_validator("pdf_dir")
    @classmethod
    def _ancora_pdf_dir(cls, v: str) -> str:
        p = Path(v)
        if not p.is_absolute():
            p = Path(__file__).resolve().parents[1] / p
        return str(p.resolve())
    pncp_base_url: str = "https://pncp.gov.br/api"
    compras_base_url: str = "https://dadosabertos.compras.gov.br"
    janela_inicial_dias: int = 7
    score_piso: float = 0.34
    smtp_host: str | None = None
    smtp_port: int = 587
    smtp_user: str | None = None
    smtp_password: str | None = None
    smtp_from: str | None = None
    smtp_to: str | None = None
    telegram_bot_token: str | None = None
    telegram_chat_id: str | None = None
