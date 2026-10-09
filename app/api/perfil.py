from datetime import datetime, timezone
from fastapi import APIRouter, Depends
from app.api.deps import get_session
from app.api.schemas import PerfilSchema, PerfilUpdate
from app.db.models import PerfilRow

router = APIRouter()


def _obter_ou_criar(session) -> PerfilRow:
    row = session.get(PerfilRow, 1)
    if row is None:
        row = PerfilRow(id=1, atualizado_em=datetime.now(timezone.utc))
        session.add(row)
        session.commit()
    return row


@router.get("/perfil", response_model=PerfilSchema)
def obter(session=Depends(get_session)):
    return _obter_ou_criar(session)


@router.put("/perfil", response_model=PerfilSchema)
def atualizar(body: PerfilUpdate, session=Depends(get_session)):
    row = _obter_ou_criar(session)
    row.nome = body.nome
    row.email_digest = body.email_digest
    row.telegram_chat_id = body.telegram_chat_id
    row.receber_email = body.receber_email
    row.receber_telegram = body.receber_telegram
    row.atualizado_em = datetime.now(timezone.utc)
    session.commit()
    return row
