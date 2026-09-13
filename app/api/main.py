from fastapi import FastAPI
from app.api import editais, digest, projetos

app = FastAPI(title="MyLicitacoes")
app.include_router(editais.router)
app.include_router(digest.router)
app.include_router(projetos.router)
