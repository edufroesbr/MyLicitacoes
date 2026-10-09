from datetime import datetime, timezone
from app.config import Settings
from app.db.models import PerfilRow
from app.scheduler.run_daily import montar_canais, nomes_canais
from app.adapters.notificacao.portal import PortalDigest
from app.adapters.notificacao.email import EmailDigest
from app.adapters.notificacao.telegram import TelegramDigest


def _settings_com_infra() -> Settings:
    return Settings(database_url="sqlite://", smtp_host="smtp.exemplo.com", smtp_port=587,
                     smtp_user=None, smtp_password=None, smtp_from="radar@exemplo.com",
                     smtp_to="fallback@exemplo.com", telegram_bot_token="tok-abc",
                     telegram_chat_id="chat-fallback")


def _perfil(**over) -> PerfilRow:
    base = dict(id=1, nome="", email_digest=None, telegram_chat_id=None,
                receber_email=False, receber_telegram=False,
                atualizado_em=datetime.now(timezone.utc))
    base.update(over)
    return PerfilRow(**base)


def test_sem_perfil_so_entra_portal_mesmo_com_infra_configurada():
    canais = montar_canais(None, _settings_com_infra(), session_factory=lambda: None)
    assert len(canais) == 1
    assert isinstance(canais[0], PortalDigest)


def test_perfil_com_tudo_desligado_nao_gera_email_nem_telegram():
    perfil = _perfil(receber_email=False, receber_telegram=False)
    canais = montar_canais(perfil, _settings_com_infra(), session_factory=lambda: None)
    assert not any(isinstance(c, EmailDigest) for c in canais)
    assert not any(isinstance(c, TelegramDigest) for c in canais)
    assert len(canais) == 1


def test_perfil_com_receber_email_ligado_usa_destinatario_do_perfil():
    perfil = _perfil(receber_email=True, email_digest="eu@exemplo.com")
    canais = montar_canais(perfil, _settings_com_infra(), session_factory=lambda: None)
    emails = [c for c in canais if isinstance(c, EmailDigest)]
    assert len(emails) == 1
    assert emails[0]._para == "eu@exemplo.com"


def test_perfil_com_receber_telegram_ligado_usa_chat_id_do_perfil():
    perfil = _perfil(receber_telegram=True, telegram_chat_id="chat-perfil")
    canais = montar_canais(perfil, _settings_com_infra(), session_factory=lambda: None)
    tgs = [c for c in canais if isinstance(c, TelegramDigest)]
    assert len(tgs) == 1
    assert tgs[0]._chat == "chat-perfil"


def test_perfil_ligado_sem_destinatario_proprio_cai_no_fallback_do_settings():
    perfil = _perfil(receber_email=True, email_digest=None,
                      receber_telegram=True, telegram_chat_id=None)
    canais = montar_canais(perfil, _settings_com_infra(), session_factory=lambda: None)
    emails = [c for c in canais if isinstance(c, EmailDigest)]
    tgs = [c for c in canais if isinstance(c, TelegramDigest)]
    assert emails[0]._para == "fallback@exemplo.com"
    assert tgs[0]._chat == "chat-fallback"


def test_perfil_ligado_mas_sem_infra_no_settings_nao_gera_canal():
    perfil = _perfil(receber_email=True, email_digest="eu@exemplo.com",
                      receber_telegram=True, telegram_chat_id="chat-perfil")
    s = Settings(database_url="sqlite://", smtp_host=None, telegram_bot_token=None)
    canais = montar_canais(perfil, s, session_factory=lambda: None)
    assert len(canais) == 1
    assert isinstance(canais[0], PortalDigest)


def test_nomes_canais_so_portal():
    canais = montar_canais(None, _settings_com_infra(), session_factory=lambda: None)
    assert nomes_canais(canais) == ["portal"]


def test_nomes_canais_com_email_e_telegram_ligados():
    perfil = _perfil(receber_email=True, email_digest="eu@exemplo.com",
                      receber_telegram=True, telegram_chat_id="chat-perfil")
    canais = montar_canais(perfil, _settings_com_infra(), session_factory=lambda: None)
    assert nomes_canais(canais) == ["portal", "telegram", "email"]
