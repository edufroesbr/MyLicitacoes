from fastapi import FastAPI
from app.api import editais

app = FastAPI(title="MyLicitacoes")
app.include_router(editais.router)
