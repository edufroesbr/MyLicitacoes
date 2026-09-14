# tests/adapters/test_compras_gov.py
import json
from pathlib import Path
from app.adapters.fontes.compras_gov import _parse_item
from app.domain.edital import Edital, Fonte

FIX = json.loads(Path("tests/fixtures/compras_gov.json").read_text(encoding="utf-8"))


def test_parse_item_primeiro_registo():
    itens = FIX.get("resultado") or []
    e = _parse_item(itens[0])
    assert isinstance(e, Edital)
    assert e.fonte == Fonte.COMPRAS_GOV
    assert e.chave_natural
    assert e.objeto  # objeto não vazio
