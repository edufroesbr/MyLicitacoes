import os
import pytest


@pytest.fixture(autouse=True)
def _limpa_db():
    url = os.getenv("MYLIC_DATABASE_URL")
    if not url:
        yield
        return
    from sqlalchemy import text
    from app.db.engine import make_session
    S = make_session(url)
    with S() as s:
        s.execute(text("TRUNCATE arquivo_edital, edital, projeto_interesse, "
                       "execucao_captura, digest_log RESTART IDENTITY CASCADE"))
        s.commit()
    yield
