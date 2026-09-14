# app/adapters/classificador/keyword.py
from app.domain.edital import Edital
from app.domain.relevancia import Lexico, ScoreRelevancia, classificar_relevancia


class KeywordClassificador:
    def __init__(self, lexico: Lexico) -> None:
        self._lexico = lexico

    def classificar(self, e: Edital) -> ScoreRelevancia:
        return classificar_relevancia(e.objeto, e.texto_extra, self._lexico)
