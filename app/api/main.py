from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import editais, digest, projetos

app = FastAPI(title="MyLicitacoes")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(editais.router)
app.include_router(digest.router)
app.include_router(projetos.router)
