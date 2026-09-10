import os
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
