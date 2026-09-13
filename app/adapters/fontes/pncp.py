# app/adapters/fontes/pncp.py
from datetime import date, datetime
from decimal import Decimal
from app.adapters.http_client import make_client
from app.domain.edital import Edital, Fonte, ArquivoRef, TipoArquivo

MODALIDADES = (6, 7, 8, 9, 12)  # confirmado: modalidadeId=8 (Dispensa) no fixture real


def _d(s: str | None) -> date | None:
    if not s:
        return None
    try:
        return datetime.fromisoformat(str(s).replace("Z", "+00:00")).date()
    except (ValueError, TypeError):
        return None


def _parse_item(item: dict) -> Edital:
    orgao = item.get("orgaoEntidade") or {}
    unidade = item.get("unidadeOrgao") or {}
    cnpj = str(orgao.get("cnpj") or "")
    ano = item.get("anoCompra")
    seq = item.get("sequencialCompra")
    valor = item.get("valorTotalEstimado")
    return Edital(
        fonte=Fonte.PNCP,
        chave_natural=f"{cnpj}-{ano}-{seq}",
        objeto=str(item.get("objetoCompra") or ""),
        orgao_nome=str(orgao.get("razaoSocial") or ""),
        orgao_cnpj=cnpj,
        uf=unidade.get("ufSigla"),
        municipio=unidade.get("municipioNome"),
        modalidade=item.get("modalidadeNome"),
        valor_estimado=Decimal(str(valor)) if valor is not None else None,
        data_publicacao=_d(item.get("dataPublicacaoPncp")),
        data_abertura=_d(item.get("dataAberturaProposta")),
        data_fim_propostas=_d(item.get("dataEncerramentoProposta")),
        url_origem=f"https://pncp.gov.br/app/editais/{cnpj}/{ano}/{seq}",
    )


class FontePncp:
    """Adaptador da fonte PNCP.

    NOTA (confirmado contra a API real, 2026-09-10): a busca por publicação e a
    listagem de arquivos de uma compra vivem em raízes distintas do mesmo
    domínio `pncp.gov.br/api` — `/consulta/v1/...` para busca,
    `/pncp/v1/...` para arquivos. `base_url` é a raiz comum (`.../api`); cada
    método compõe o sub-caminho correcto.
    """

    nome = "pncp"

    def __init__(self, base_url: str = "https://pncp.gov.br/api") -> None:
        self._base_url = base_url

    def buscar(self, inicio: date, fim: date) -> list[Edital]:
        out: list[Edital] = []
        di, df = inicio.strftime("%Y%m%d"), fim.strftime("%Y%m%d")
        with make_client(self._base_url) as c:
            for mod in MODALIDADES:
                try:
                    pagina = 1
                    while True:
                        r = c.get("/consulta/v1/contratacoes/publicacao", params={
                            "dataInicial": di, "dataFinal": df,
                            "codigoModalidadeContratacao": mod,
                            "pagina": pagina, "tamanhoPagina": 500,
                        })
                        if r.status_code == 204:
                            break
                        r.raise_for_status()
                        body = r.json()
                        itens = body.get("data") or []
                        for i in itens:
                            try:
                                out.append(_parse_item(i))
                            except Exception:
                                pass  # item malformado nao aborta a fonte
                        if pagina >= int(body.get("totalPaginas") or 1):
                            break
                        pagina += 1
                except Exception:
                    pass  # modalidade com erro (ex.: 400) nao derruba as restantes
        return out

    def listar_arquivos(self, e: Edital) -> list[ArquivoRef]:
        cnpj, ano, seq = e.chave_natural.split("-")
        with make_client(self._base_url) as c:
            r = c.get(f"/pncp/v1/orgaos/{cnpj}/compras/{ano}/{seq}/arquivos")
            if r.status_code == 204:
                return []
            r.raise_for_status()
            refs = []
            for a in r.json():
                refs.append(ArquivoRef(tipo=TipoArquivo.EDITAL,
                                       url=a.get("url") or a.get("uri") or "",
                                       nome=a.get("titulo") or a.get("nomeArquivo") or "arquivo"))
            return refs
