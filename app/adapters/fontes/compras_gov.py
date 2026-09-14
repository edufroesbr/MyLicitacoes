# app/adapters/fontes/compras_gov.py
# Endpoint usado (confirmado contra a API real, 2026-09-10):
#   GET https://dadosabertos.compras.gov.br/modulo-legado/1_consultarLicitacao
#   params: pagina, tamanhoPagina (10-500), data_publicacao_inicial (YYYY-MM-DD),
#           data_publicacao_final (YYYY-MM-DD)
# Confirmado via OpenAPI (/v3/api-docs): é o "módulo legado" (Comprasnet,
# licitações fora do PNCP/Lei 14.133), por isso não devolve `cnpj`/`orgao`
# nem `uf` — só `uasg` (código da unidade, não o CNPJ). A janela
# 2026-09-01..2026-09-02 (a do plano original) devolveu resultado=[] porque o
# módulo legado está esvaziando (a maioria das licitações migrou para o PNCP,
# já coberto pelo adaptador `pncp.py`); o fixture foi capturado com
# data_publicacao_inicial=2025-01-01 / data_publicacao_final=2025-12-31, que
# tem registos reais (totalRegistros=7562 nessa janela).
from datetime import date, datetime
from decimal import Decimal
from app.adapters.http_client import make_client
from app.domain.edital import Edital, Fonte, ArquivoRef


def _d(s: str | None) -> date | None:
    if not s:
        return None
    try:
        return datetime.fromisoformat(str(s)[:19]).date()
    except ValueError:
        return None


def _parse_item(item: dict) -> Edital:
    valor = item.get("valor_estimado_total")
    return Edital(
        fonte=Fonte.COMPRAS_GOV,
        chave_natural=str(item.get("identificador") or item.get("id_compra") or ""),
        objeto=str(item.get("objeto") or ""),
        orgao_nome="",
        orgao_cnpj="",
        uf=None,
        municipio=None,
        modalidade=item.get("nome_modalidade"),
        valor_estimado=Decimal(str(valor)) if valor is not None else None,
        data_publicacao=_d(item.get("data_publicacao")),
        data_abertura=_d(item.get("data_abertura_proposta")),
        data_fim_propostas=_d(item.get("data_entrega_proposta")),
        url_origem="https://compras.gov.br",
    )


class FonteComprasGov:
    """Adaptador do módulo legado (Comprasnet) do Compras.gov.br.

    Cobre licitações fora do PNCP/Lei 14.133; o endpoint não devolve
    CNPJ/UF/nome do órgão, só o código UASG embutido no `identificador`.
    """

    nome = "compras_gov"

    def __init__(self, base_url: str = "https://dadosabertos.compras.gov.br") -> None:
        self._base_url = base_url

    def buscar(self, inicio: date, fim: date) -> list[Edital]:
        out: list[Edital] = []
        with make_client(self._base_url) as c:
            pagina = 1
            while True:
                r = c.get("/modulo-legado/1_consultarLicitacao", params={
                    "pagina": pagina, "tamanhoPagina": 500,
                    "data_publicacao_inicial": inicio.isoformat(),
                    "data_publicacao_final": fim.isoformat(),
                })
                r.raise_for_status()
                body = r.json()
                itens = body.get("resultado") or []
                out.extend(_parse_item(i) for i in itens)
                total_pag = int(body.get("totalPaginas") or 0)
                if not itens or pagina >= total_pag:
                    break
                pagina += 1
        return out

    def listar_arquivos(self, e: Edital) -> list[ArquivoRef]:
        return []
