# tests/adapters/test_pncp.py
import json
from pathlib import Path
from app.adapters.fontes.pncp import _parse_item
from app.domain.edital import Edital, Fonte

FIX = json.loads(Path("tests/fixtures/pncp_publicacao.json").read_text(encoding="utf-8"))


def test_parse_item_primeiro_registo():
    item = FIX["data"][0]
    e = _parse_item(item)
    assert isinstance(e, Edital)
    assert e.fonte == Fonte.PNCP
    assert e.orgao_cnpj and e.chave_natural.count("-") == 2
    assert e.objeto  # objeto não vazio
