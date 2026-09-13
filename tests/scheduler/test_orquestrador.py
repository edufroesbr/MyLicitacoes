# tests/scheduler/test_orquestrador.py
from datetime import date, datetime, timezone
from decimal import Decimal
from app.domain.edital import Edital, Fonte, ArquivoRef, TipoArquivo
from app.domain.relevancia import ScoreRelevancia


class FonteFake:
    def __init__(self, nome, editais, explode=False):
        self.nome = nome
        self._e = editais
        self._explode = explode
    def buscar(self, inicio, fim):
        if self._explode:
            raise RuntimeError("fonte caiu")
        return self._e
    def listar_arquivos(self, e):
        return [ArquivoRef(TipoArquivo.EDITAL, "http://x/edital.pdf", "edital.pdf")]


class ClassifFake:
    def classificar(self, e):
        rel = "clipping" in e.objeto
        return ScoreRelevancia(0.9 if rel else 0.0, ("clipping",) if rel else ())


class StoreFake:
    def __init__(self): self.guardados = []
    def guardar(self, e, arq, conteudo): self.guardados.append(e.chave_natural); return "/tmp/x.pdf"


class CanalFake:
    def __init__(self): self.enviados = []
    def enviar(self, d): self.enviados.append(d)


class SessionFake:
    def __enter__(self): return self
    def __exit__(self, *a): pass
    def add(self, *a): pass
    def commit(self): pass
    def scalar(self, *a, **k): return None


def _ed(fonte, chave, objeto):
    return Edital(fonte, chave, objeto, "Org", "00000000000191", "AM", "Manaus",
                  "Pregao", Decimal("1"), date(2026, 9, 1), None, None, "http://x")


def test_fonte_que_cai_nao_derruba_a_outra(monkeypatch):
    import app.scheduler.orquestrador as orq
    monkeypatch.setattr(orq, "upsert_editais", lambda s, itens: (len(itens), 0))
    monkeypatch.setattr(orq, "registar_execucao", lambda *a, **k: None)
    monkeypatch.setattr(orq, "ultima_captura", lambda s, fonte: None)
    boa = FonteFake("pncp", [_ed(Fonte.PNCP, "k1", "servico de clipping")])
    ma = FonteFake("compras_gov", [], explode=True)
    store, canal = StoreFake(), CanalFake()
    res = orq.executar(SessionFake(), [boa, ma], ClassifFake(), store, [canal],
                       baixar_conteudo=lambda url: b"%PDF", janela_inicial_dias=7,
                       score_piso=0.34, hoje=date(2026, 9, 2))
    assert "compras_gov" in res.fontes_falha
    assert res.novos == 1
    assert store.guardados == ["k1"]
    assert len(canal.enviados) == 1


class FonteArquivosExplode:
    """Fonte cujo listar_arquivos falha para um edital especifico (ex.: timeout/500 do PNCP)."""
    nome = "pncp"
    def __init__(self, editais, chave_que_explode):
        self._e = editais
        self._chave_que_explode = chave_que_explode
    def buscar(self, inicio, fim):
        return self._e
    def listar_arquivos(self, e):
        if e.chave_natural == self._chave_que_explode:
            raise RuntimeError("timeout pncp")
        return [ArquivoRef(TipoArquivo.EDITAL, "http://x/edital.pdf", "edital.pdf")]


def test_listar_arquivos_que_falha_nao_bloqueia_outro_edital_nem_o_digest(monkeypatch):
    import app.scheduler.orquestrador as orq
    monkeypatch.setattr(orq, "upsert_editais", lambda s, itens: (len(itens), 0))
    monkeypatch.setattr(orq, "registar_execucao", lambda *a, **k: None)
    monkeypatch.setattr(orq, "ultima_captura", lambda s, fonte: None)
    e1 = _ed(Fonte.PNCP, "k1", "servico de clipping")
    e2 = Edital(Fonte.PNCP, "k2", "servico de clipping", "Org", "00000000000292", "AM",
                "Manaus", "Pregao", Decimal("1"), date(2026, 9, 1), None, None, "http://x")
    fonte = FonteArquivosExplode([e1, e2], chave_que_explode="k1")
    store, canal = StoreFake(), CanalFake()
    res = orq.executar(SessionFake(), [fonte], ClassifFake(), store, [canal],
                       baixar_conteudo=lambda url: b"%PDF", janela_inicial_dias=7,
                       score_piso=0.34, hoje=date(2026, 9, 2))
    assert res.relevantes == 2
    assert store.guardados == ["k2"]
    assert len(canal.enviados) == 1


class CanalExplode:
    def enviar(self, d):
        raise RuntimeError("smtp fora do ar")


def test_canal_que_falha_nao_impede_os_restantes(monkeypatch):
    import app.scheduler.orquestrador as orq
    monkeypatch.setattr(orq, "upsert_editais", lambda s, itens: (len(itens), 0))
    monkeypatch.setattr(orq, "registar_execucao", lambda *a, **k: None)
    monkeypatch.setattr(orq, "ultima_captura", lambda s, fonte: None)
    boa = FonteFake("pncp", [_ed(Fonte.PNCP, "k1", "servico de clipping")])
    store, canal_ok = StoreFake(), CanalFake()
    res = orq.executar(SessionFake(), [boa], ClassifFake(), store, [CanalExplode(), canal_ok],
                       baixar_conteudo=lambda url: b"%PDF", janela_inicial_dias=7,
                       score_piso=0.34, hoje=date(2026, 9, 2))
    assert len(canal_ok.enviados) == 1


class FonteQueRegistaJanela:
    """Fonte fake que grava a janela (inicio, fim) com que buscar() foi chamada,
    para verificar que cada fonte recebe a SUA PROPRIA janela incremental."""
    def __init__(self, nome):
        self.nome = nome
        self.janelas_recebidas = []
    def buscar(self, inicio, fim):
        self.janelas_recebidas.append((inicio, fim))
        return []
    def listar_arquivos(self, e):
        return []


def test_cada_fonte_recebe_a_sua_propria_janela_incremental(monkeypatch):
    import app.scheduler.orquestrador as orq
    monkeypatch.setattr(orq, "upsert_editais", lambda s, itens: (len(itens), 0))
    monkeypatch.setattr(orq, "registar_execucao", lambda *a, **k: None)

    # pncp ja tem captura anterior ate 2026-09-05; compras_gov nunca capturou (usa o fallback)
    def ultima_captura_fake(session, fonte):
        if fonte == "pncp":
            return datetime(2026, 9, 5, tzinfo=timezone.utc)
        return None
    monkeypatch.setattr(orq, "ultima_captura", ultima_captura_fake)

    pncp = FonteQueRegistaJanela("pncp")
    compras = FonteQueRegistaJanela("compras_gov")
    orq.executar(SessionFake(), [pncp, compras], ClassifFake(), StoreFake(), [],
                 baixar_conteudo=lambda url: b"%PDF", janela_inicial_dias=7,
                 score_piso=0.34, hoje=date(2026, 9, 10))

    assert pncp.janelas_recebidas == [(date(2026, 9, 5), date(2026, 9, 10))]
    assert compras.janelas_recebidas == [(date(2026, 9, 3), date(2026, 9, 10))]
