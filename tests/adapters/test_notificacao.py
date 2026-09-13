# tests/adapters/test_notificacao.py
from datetime import date
from app.domain.digest import Digest
from app.adapters.notificacao.render import render_html, render_texto
from app.adapters.notificacao.telegram import TelegramDigest


def _digest():
    return Digest(date(2026, 9, 1), 40, 3, 3, ("compras_gov",), (), ())


def test_render_html_tem_totais():
    html = render_html(_digest())
    assert "40" in html and "compras_gov" in html


def test_render_texto_nao_quebra_sem_destaques():
    txt = render_texto(_digest())
    assert "Radar de Editais" in txt


def test_telegram_faz_post():
    chamadas = {}

    class FakeResp:
        status_code = 200
        def raise_for_status(self): pass

    class FakeClient:
        def __enter__(self): return self
        def __exit__(self, *a): pass
        def post(self, url, json):
            chamadas["url"] = url
            chamadas["json"] = json
            return FakeResp()

    tg = TelegramDigest("TOKEN", "123", client_factory=lambda base: FakeClient())
    tg.enviar(_digest())
    assert "/botTOKEN/sendMessage" in chamadas["url"]
    assert chamadas["json"]["chat_id"] == "123"
