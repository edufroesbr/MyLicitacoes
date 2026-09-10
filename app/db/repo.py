from datetime import datetime, timezone
from sqlalchemy import select
from app.domain.edital import Edital
from app.domain.relevancia import ScoreRelevancia
from app.db.models import EditalRow, ExecucaoCapturaRow


def upsert_editais(session, editais_com_score: list[tuple[Edital, ScoreRelevancia, str]]) -> tuple[int, int]:
    novos = atualizados = 0
    for e, sc, h in editais_com_score:
        row = session.scalar(select(EditalRow).where(
            EditalRow.fonte == e.fonte.value, EditalRow.chave_natural == e.chave_natural))
        if row is None:
            session.add(EditalRow(
                fonte=e.fonte.value, chave_natural=e.chave_natural, hash_conteudo=h,
                objeto=e.objeto, orgao_nome=e.orgao_nome, orgao_cnpj=e.orgao_cnpj,
                uf=e.uf, municipio=e.municipio, modalidade=e.modalidade,
                valor_estimado=e.valor_estimado, data_publicacao=e.data_publicacao,
                data_abertura=e.data_abertura, data_fim_propostas=e.data_fim_propostas,
                score_relevancia=sc.valor, motivo_relevancia=",".join(sc.termos),
                status="novo", url_origem=e.url_origem,
                capturado_em=datetime.now(timezone.utc)))
            novos += 1
        elif row.hash_conteudo != h:
            row.hash_conteudo = h
            row.objeto = e.objeto
            row.score_relevancia = sc.valor
            row.motivo_relevancia = ",".join(sc.termos)
            atualizados += 1
    return novos, atualizados


def registar_execucao(session, fonte, inicio, fim, lidos, novos, relevantes, status, erro="", iniciado=None, terminado=None):
    agora = datetime.now(timezone.utc)
    session.add(ExecucaoCapturaRow(
        fonte=fonte, janela_inicio=inicio, janela_fim=fim, total_lidos=lidos,
        total_novos=novos, total_relevantes=relevantes, status=status, erro=erro,
        iniciado_em=iniciado or agora, terminado_em=terminado or agora))


def ultima_captura(session, fonte) -> datetime | None:
    return session.scalar(select(ExecucaoCapturaRow.janela_fim)
                          .where(ExecucaoCapturaRow.fonte == fonte, ExecucaoCapturaRow.status != "falha")
                          .order_by(ExecucaoCapturaRow.janela_fim.desc()).limit(1))
