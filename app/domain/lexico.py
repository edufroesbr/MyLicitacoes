# app/domain/lexico.py
from app.domain.relevancia import Lexico

LEXICO_TIPO_LEXFLOW = Lexico(
    positivos=frozenset({
        "clipping",
        "monitoramento de publicacoes",
        "monitoramento de publicacoes oficiais",
        "recorte de publicacoes",
        "recorte de materias",
        "diario de justica",
        "diario oficial",
        "dje",
        "acompanhamento processual",
        "captura de publicacoes",
        "software juridico",
        "sistema juridico",
        "gestao de publicacoes",
        "publicacoes oficiais",
    }),
    negativos=frozenset({
        "merenda escolar",
        "material de construcao",
        "combustivel",
    }),
)
