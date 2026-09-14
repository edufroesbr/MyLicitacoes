from functools import lru_cache
from app.config import Settings
from app.db.engine import make_session


@lru_cache
def _sessionmaker():
    return make_session(Settings().database_url)


def get_session():
    S = _sessionmaker()
    with S() as s:
        yield s
