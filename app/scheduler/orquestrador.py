# app/scheduler/orquestrador.py
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import date
from app.domain.dedup import deduplicar, hash_conteudo
from app.domain.digest import montar_digest
from app.db.repo import upsert_editais, registar_execucao


@dataclass
class Resultado:
    novos: int = 0
    relevantes: int = 0
    downloads: int = 0
    fontes_falha: list[str] = field(default_factory=list)


def executar(session, fontes, classificador, armazenamento, canais,
             baixar_conteudo: Callable[[str], bytes], inicio: date, fim: date,
             score_piso: float) -> Resultado:
    res = Resultado()
    capturados = []
    por_nome = {}
    for f in fontes:
        try:
            editais = f.buscar(inicio, fim)
            capturados.extend(editais)
            por_nome[f.nome] = f
            registar_execucao(session, f.nome, inicio, fim, len(editais), 0, 0, "sucesso")
        except Exception as exc:  # isolamento por fonte
            res.fontes_falha.append(f.nome)
            registar_execucao(session, f.nome, inicio, fim, 0, 0, 0, "falha", str(exc))
    session.commit()

    editais = deduplicar(capturados)
    com_score = [(e, classificador.classificar(e), hash_conteudo(e)) for e in editais]
    res.novos, _ = upsert_editais(session, com_score)
    session.commit()

    relevantes = [e for e, sc, _ in com_score if sc.valor >= score_piso]
    res.relevantes = len(relevantes)
    for e in relevantes:
        fonte = por_nome.get(e.fonte.value)
        if fonte is None:
            continue
        for arq in fonte.listar_arquivos(e):
            if not arq.url:
                continue
            try:
                armazenamento.guardar(e, arq, baixar_conteudo(arq.url))
                res.downloads += 1
            except Exception:
                pass  # PDF que falha nao bloqueia o edital

    digest = montar_digest(fim, relevantes, res.novos, res.downloads, res.fontes_falha, [])
    for canal in canais:
        canal.enviar(digest)
    return res
