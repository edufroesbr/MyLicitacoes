from sqlalchemy import func, or_
from app.db.models import EditalRow, ProjetoInteresseRow


def _sem_acento(col):
    """ILIKE acento-insensitivo via extensao `unaccent` do Postgres (migracao
    unaccent_extension)."""
    return func.unaccent(col)


def _escapar_like(s: str) -> str:
    """Escapa os wildcards do LIKE/ILIKE (% e _) para que busca literal nao
    vire wildcard acidental."""
    return s.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")


def condicoes_projeto(proj: ProjetoInteresseRow) -> list:
    """Condicoes SQLAlchemy que filtram EditalRow pelas palavras-chave e
    filtros salvos num projeto de interesse. Reusada por /editais (listar,
    via projeto_id) e por /projetos-interesse/{id}/resumo - nao duplicar
    esta logica nos dois lugares."""
    cond = []
    if proj.palavras_chave:
        cond.append(or_(*(_sem_acento(EditalRow.objeto).ilike(_sem_acento(f"%{_escapar_like(p)}%"), escape="\\")
                           for p in proj.palavras_chave)))
    f = proj.filtros or {}
    if f.get("uf"): cond.append(EditalRow.uf == f["uf"])
    if f.get("modalidade"): cond.append(EditalRow.modalidade == f["modalidade"])
    return cond
