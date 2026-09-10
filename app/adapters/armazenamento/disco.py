import re
from pathlib import Path
from app.domain.edital import Edital, ArquivoRef


def _sane(nome: str) -> str:
    return re.sub(r"[^A-Za-z0-9._-]+", "_", nome) or "arquivo"


class ArmazenamentoDisco:
    def __init__(self, base_dir: str) -> None:
        self._base = Path(base_dir)

    def guardar(self, e: Edital, arq: ArquivoRef, conteudo: bytes) -> str:
        destino = self._base / e.fonte.value / _sane(e.chave_natural) / _sane(arq.nome)
        destino.parent.mkdir(parents=True, exist_ok=True)
        destino.write_bytes(conteudo)
        return str(destino.resolve())
