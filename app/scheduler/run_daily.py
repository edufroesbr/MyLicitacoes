# app/scheduler/run_daily.py
from app.config import Settings
from app.db.engine import make_session
from app.domain.lexico import LEXICO_TIPO_LEXFLOW
from app.adapters.classificador.keyword import KeywordClassificador
from app.adapters.fontes.pncp import FontePncp
from app.adapters.fontes.compras_gov import FonteComprasGov
from app.adapters.armazenamento.disco import ArmazenamentoDisco
from app.adapters.notificacao.telegram import TelegramDigest
from app.adapters.notificacao.email import EmailDigest
from app.adapters.notificacao.portal import PortalDigest
from app.adapters.http_client import make_client
from app.scheduler.orquestrador import executar


def main() -> None:
    s = Settings()
    Session = make_session(s.database_url)
    fontes = [FontePncp(s.pncp_base_url), FonteComprasGov(s.compras_base_url)]
    canais = [PortalDigest(Session)]
    if s.telegram_bot_token and s.telegram_chat_id:
        canais.append(TelegramDigest(s.telegram_bot_token, s.telegram_chat_id))
    if s.smtp_host and s.smtp_to:
        canais.append(EmailDigest(s.smtp_host, s.smtp_port, s.smtp_user, s.smtp_password, s.smtp_from, s.smtp_to))

    def baixar(url: str) -> bytes:
        with make_client("") as c:
            r = c.get(url)
            r.raise_for_status()
            return r.content

    with Session() as sess:
        res = executar(sess, fontes, KeywordClassificador(LEXICO_TIPO_LEXFLOW),
                       ArmazenamentoDisco(s.pdf_dir), canais, baixar,
                       s.janela_inicial_dias, s.score_piso)
    print(f"novos={res.novos} relevantes={res.relevantes} downloads={res.downloads} "
          f"fontes_falha={res.fontes_falha}")


if __name__ == "__main__":
    main()
