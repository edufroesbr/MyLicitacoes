from fastapi import FastAPI
from app.api import editais, digest

app = FastAPI(title="MyLicitacoes")
app.include_router(editais.router)
app.include_router(digest.router)
