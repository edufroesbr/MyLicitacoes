from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="MYLIC_", env_file=".env", extra="ignore")

    database_url: str
    pdf_dir: str
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
