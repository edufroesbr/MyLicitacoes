# app/ports/portas.py
from datetime import date
from typing import Protocol
from app.domain.edital import Edital, ArquivoRef
from app.domain.relevancia import ScoreRelevancia
from app.domain.digest import Digest


class FonteEditais(Protocol):
    nome: str
    def buscar(self, inicio: date, fim: date) -> list[Edital]: ...
    def listar_arquivos(self, e: Edital) -> list[ArquivoRef]: ...


class ClassificadorRelevancia(Protocol):
    def classificar(self, e: Edital) -> ScoreRelevancia: ...


class ArmazenamentoEditalPdf(Protocol):
    def guardar(self, e: Edital, arq: ArquivoRef, conteudo: bytes) -> str: ...


class CanalDigest(Protocol):
    def enviar(self, d: Digest) -> None: ...
