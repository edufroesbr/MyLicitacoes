from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


def make_session(database_url: str) -> sessionmaker:
    engine = create_engine(database_url, future=True)
    return sessionmaker(bind=engine, future=True)
