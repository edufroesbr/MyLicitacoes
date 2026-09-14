# app/adapters/notificacao/portal.py
from datetime import datetime, timezone
from app.domain.digest import Digest
from app.db.models import DigestLogRow


class PortalDigest:
    def __init__(self, session_factory) -> None:
        self._sf = session_factory

    def enviar(self, d: Digest) -> None:
        with self._sf() as s:
            s.add(DigestLogRow(
                data_ref=d.data_ref, canais="portal",
                enviado_em=datetime.now(timezone.utc),
                resumo={"novos": d.total_novos, "relevantes": d.total_relevantes,
                        "downloads": d.total_downloads,
                        "fontes_com_falha": list(d.fontes_com_falha)}))
            s.commit()
