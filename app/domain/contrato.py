# app/domain/contrato.py
from dataclasses import dataclass
from datetime import date
from decimal import Decimal


@dataclass(frozen=True)
class Contrato:
    fonte: str
    chave_natural: str
    chave_natural_compra: str
    numero_contrato: str
    fornecedor_nome: str
    fornecedor_documento: str
    valor_inicial: Decimal | None
    valor_global: Decimal | None
    data_assinatura: date | None
    data_publicacao: date | None
    orgao_nome: str
    orgao_cnpj: str
    uf: str | None
    municipio: str | None


def chave_compra_de_numero_controle(numero: str) -> str | None:
    """Converte numeroControlePncpCompra ('{cnpj}-{tipo}-{seq}/{ano}') pro
    formato de chave_natural que ja usamos pra EditalRow
    ('{cnpj}-{ano}-{seq}', seq sem zero a esquerda) - ver
    app/adapters/fontes/pncp.py::_parse_item. Nunca lanca; None se o
    formato vier diferente do esperado (contrato e descartado, nao quebra
    a captura)."""
    try:
        cnpj, _tipo, resto = numero.split("-", 2)
        seq_str, ano_str = resto.split("/")
        return f"{cnpj}-{int(ano_str)}-{int(seq_str)}"
    except (ValueError, AttributeError):
        return None
