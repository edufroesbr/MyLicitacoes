# app/adapters/notificacao/email.py
import smtplib
from email.message import EmailMessage
from app.domain.digest import Digest
from app.adapters.notificacao.render import render_html, render_texto


class EmailDigest:
    def __init__(self, host, port, user, password, remetente, destinatario) -> None:
        self._host, self._port = host, port
        self._user, self._password = user, password
        self._de, self._para = remetente, destinatario

    def enviar(self, d: Digest) -> None:
        msg = EmailMessage()
        msg["Subject"] = f"Radar de Editais — {d.data_ref.isoformat()}"
        msg["From"] = self._de
        msg["To"] = self._para
        msg.set_content(render_texto(d))
        msg.add_alternative(render_html(d), subtype="html")
        with smtplib.SMTP(self._host, self._port) as s:
            s.starttls()
            if self._user:
                s.login(self._user, self._password)
            s.send_message(msg)
