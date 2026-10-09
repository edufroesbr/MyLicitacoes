# app/scheduler/run_daily.py
from app.config import Settings
from app.db.engine import make_session
from app.db.models import PerfilRow
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


def montar_canais(perfil: PerfilRow | None, s: Settings, session_factory) -> list:
    """Monta a lista de canais do digest a partir do perfil (preferencias de
    recebimento) e das credenciais de infra (Settings). PortalDigest sempre
    entra - e o canal interno que alimenta /digest/hoje, sem relacao com o
    perfil. Email/Telegram só entram se a infra existir E o perfil pedir
    aquele canal E houver um destinatario/chat id resolvido."""
    canais = [PortalDigest(session_factory)]
    if s.telegram_bot_token and perfil is not None and perfil.receber_telegram:
        chat_id = perfil.telegram_chat_id or s.telegram_chat_id
        if chat_id:
            canais.append(TelegramDigest(s.telegram_bot_token, chat_id))
    if s.smtp_host and perfil is not None and perfil.receber_email:
        destinatario = perfil.email_digest or s.smtp_to
        if destinatario:
            canais.append(EmailDigest(s.smtp_host, s.smtp_port, s.smtp_user,
                                       s.smtp_password, s.smtp_from, destinatario))
    return canais


_NOMES_CANAL = {PortalDigest: "portal", TelegramDigest: "telegram", EmailDigest: "email"}


def nomes_canais(canais: list) -> list[str]:
    """Deriva os nomes dos canais efetivamente incluidos no digest desta
    execucao, a partir dos objetos ja construidos por montar_canais. Usado
    so para log - nao influencia o envio."""
    return [_NOMES_CANAL.get(type(c), type(c).__name__) for c in canais]


def main() -> None:
    s = Settings()
    Session = make_session(s.database_url)
    fontes = [FontePncp(s.pncp_base_url), FonteComprasGov(s.compras_base_url)]

    def baixar(url: str) -> bytes:
        with make_client("") as c:
            r = c.get(url)
            r.raise_for_status()
            return r.content

    with Session() as sess:
        perfil = sess.get(PerfilRow, 1)
        canais = montar_canais(perfil, s, Session)
        res = executar(sess, fontes, KeywordClassificador(LEXICO_TIPO_LEXFLOW),
                       ArmazenamentoDisco(s.pdf_dir), canais, baixar,
                       s.janela_inicial_dias, s.score_piso)
    print(f"novos={res.novos} relevantes={res.relevantes} downloads={res.downloads} "
          f"fontes_falha={res.fontes_falha} fontes_zero={res.fontes_zero} "
          f"canais_digest={nomes_canais(canais)}")


if __name__ == "__main__":
    main()
