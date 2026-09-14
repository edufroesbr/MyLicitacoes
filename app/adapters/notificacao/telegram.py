# app/adapters/notificacao/telegram.py
from app.domain.digest import Digest
from app.adapters.http_client import make_client
from app.adapters.notificacao.render import render_texto


class TelegramDigest:
    def __init__(self, bot_token: str, chat_id: str, client_factory=make_client) -> None:
        self._token = bot_token
        self._chat = chat_id
        self._cf = client_factory

    def enviar(self, d: Digest) -> None:
        with self._cf("https://api.telegram.org") as c:
            r = c.post(f"/bot{self._token}/sendMessage",
                       json={"chat_id": self._chat, "text": render_texto(d)[:4000]})
            r.raise_for_status()
