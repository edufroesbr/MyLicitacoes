import os
import uuid
from datetime import date
from decimal import Decimal
import pytest
from app.domain.edital import Edital, Fonte
from app.domain.relevancia import ScoreRelevancia
from app.domain.dedup import hash_conteudo
from app.db.engine import make_session
from app.db import repo

pytestmark = pytest.mark.skipif(not os.getenv("MYLIC_DATABASE_URL"), reason="sem Postgres")


def _ed(chave, objeto="clipping"):
    return Edital(Fonte.PNCP, chave, objeto, "Org", "00000000000191", "AM", "Manaus",
                  "Pregao", Decimal("1"), date(2026, 9, 1), None, None, "http://x")


def test_upsert_nao_duplica_e_conta():
    Session = make_session(os.environ["MYLIC_DATABASE_URL"])
    with Session() as s:
        e = _ed("k-upsert-1")
        sc = ScoreRelevancia(0.5, ("clipping",))
        novos, atual = repo.upsert_editais(s, [(e, sc, hash_conteudo(e))])
        s.commit()
        assert (novos, atual) == (1, 0)
        novos2, _ = repo.upsert_editais(s, [(e, sc, hash_conteudo(e))])
        s.commit()
        assert novos2 == 0


def test_ultima_captura_ignora_execucao_com_falha():
    """Guard de ultima_captura/registar_execucao: uma execucao 'falha' mais
    recente NAO pode mascarar a janela da ultima execucao 'sucesso' — senao a
    janela incremental (orquestrador.py) reprocessa desde a falha para sempre
    (se a janela_fim da falha for usada) ou pula a janela real capturada."""
    Session = make_session(os.environ["MYLIC_DATABASE_URL"])
    fonte = f"t-uc-{uuid.uuid4().hex[:8]}"
    with Session() as s:
        repo.registar_execucao(s, fonte, date(2026, 9, 1), date(2026, 9, 2),
                               1, 1, 1, "sucesso")
        s.commit()
        repo.registar_execucao(s, fonte, date(2026, 9, 2), date(2026, 9, 5),
                               0, 0, 0, "falha", "timeout")
        s.commit()
        uc = repo.ultima_captura(s, fonte)
        assert uc is not None
        assert uc.date() == date(2026, 9, 2)  # janela_fim do "sucesso", ignora o "falha" (9/5)
