from datetime import date
from decimal import Decimal
from pathlib import Path
from app.domain.edital import Edital, Fonte, ArquivoRef, TipoArquivo
from app.adapters.armazenamento.disco import ArmazenamentoDisco


def test_guarda_pdf(tmp_path):
    e = Edital(Fonte.PNCP, "00000000000191-2026-42", "clipping", "Org", "00000000000191",
               "AM", "Manaus", "Pregao", Decimal("1"), date(2026, 9, 1), None, None, "http://x")
    arq = ArquivoRef(TipoArquivo.EDITAL, "http://x/edital.pdf", "edital.pdf")
    store = ArmazenamentoDisco(str(tmp_path))
    caminho = store.guardar(e, arq, b"%PDF-1.4 conteudo")
    p = Path(caminho)
    assert p.exists()
    assert p.read_bytes().startswith(b"%PDF")
    assert "00000000000191-2026-42" in caminho
