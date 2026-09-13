# tests/e2e/test_captura_ate_digest.py
from datetime import date
from tests.e2e.fake_portais import servidor_fake
from app.adapters.fontes.pncp import FontePncp
from app.adapters.classificador.keyword import KeywordClassificador
from app.domain.lexico import LEXICO_TIPO_LEXFLOW


class StoreFake:
    def __init__(self): self.n = 0
    def guardar(self, e, arq, conteudo): self.n += 1; return "/tmp/x.pdf"


class CanalFake:
    def __init__(self): self.enviados = []
    def enviar(self, d): self.enviados.append(d)


class SessionFake:
    def __enter__(self): return self
    def __exit__(self, *a): pass
    def add(self, *a): pass
    def commit(self): pass
    def rollback(self): pass
    def scalar(self, *a, **k): return None


def test_captura_ate_digest(monkeypatch):
    import app.scheduler.orquestrador as orq
    monkeypatch.setattr(orq, "upsert_editais", lambda s, itens: (
        {(e.fonte.value, e.chave_natural): 1 for e, sc, h in itens}, len(itens)))
    monkeypatch.setattr(orq, "persistir_arquivo", lambda *a, **k: None)
    monkeypatch.setattr(orq, "registar_execucao", lambda *a, **k: None)
    with servidor_fake() as base_url:
        fonte = FontePncp(base_url)
        store, canal = StoreFake(), CanalFake()
        res = orq.executar(SessionFake(), [fonte], KeywordClassificador(LEXICO_TIPO_LEXFLOW),
                           store, [canal], baixar_conteudo=lambda url: b"%PDF",
                           janela_inicial_dias=1, score_piso=0.05, hoje=date(2026, 9, 2))
    assert res.novos >= 1
    assert res.relevantes >= 1
    assert store.n >= 1
    assert len(canal.enviados) == 1
    print(f"E2E cenarios: novos={res.novos} relevantes={res.relevantes} downloads={store.n}")
