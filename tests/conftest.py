import os
import pytest


@pytest.fixture(autouse=True)
def _limpa_db():
    url = os.getenv("MYLIC_DATABASE_URL")
    if not url:
        yield
        return
    # Guarda contra apagar dados reais por acidente: isto faz TRUNCATE antes
    # de CADA teste. Ja aconteceu de rodar pytest com a URL do banco real
    # (a mesma usada pelas capturas de verdade) e zerar tudo em silencio.
    assert "mylic_test" in url, (
        f"MYLIC_DATABASE_URL nao aponta para o banco de testes (precisa conter "
        f"'mylic_test'): {url!r}. Recusando truncar para nao apagar dados reais."
    )
    from sqlalchemy import text
    from app.db.engine import make_session
    S = make_session(url)
    with S() as s:
        s.execute(text("TRUNCATE arquivo_edital, edital, projeto_interesse, "
                       "execucao_captura, digest_log, perfil RESTART IDENTITY CASCADE"))
        s.commit()
    yield
