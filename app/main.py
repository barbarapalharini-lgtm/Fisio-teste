from __future__ import annotations

from datetime import datetime
from io import BytesIO
from typing import Dict, List, Optional

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.crud import (
    criar_avaliacao_completa,
    criar_paciente,
    get_avaliacao,
    get_paciente,
    listar_avaliacoes_por_paciente,
    listar_pacientes,
)
from app.db import SessionLocal, init_db
from app.models import Avaliacao, Paciente
from app.pdf_generator import gerar_laudo_pdf
from app.calculations.schemas import AvaliacaoCompletaInput, AvaliacaoCompletaResultado

# ---------------------------------------------------------------------------
# Application constants
# ---------------------------------------------------------------------------
ALLOWED_ORIGINS = [
    "http://127.0.0.1:5173",
    "http://localhost:5173",
    "https://seu-projeto.vercel.app",
]


class PacienteCreate(BaseModel):
    nome: str
    data_nascimento: Optional[str] = None
    sexo: Optional[str] = None
    email: Optional[str] = None
    telefone: Optional[str] = None


class PacienteResponse(BaseModel):
    id: int
    nome: str
    data_nascimento: Optional[str] = None
    sexo: Optional[str] = None
    email: Optional[str] = None
    telefone: Optional[str] = None


def _paciente_to_response(paciente: Paciente) -> PacienteResponse:
    return PacienteResponse(
        id=paciente.id,
        nome=paciente.nome,
        data_nascimento=paciente.data_nascimento.isoformat() if paciente.data_nascimento else None,
        sexo=paciente.sexo,
        email=paciente.email,
        telefone=paciente.telefone,
    )


def _avaliacao_to_response(avaliacao: Avaliacao) -> AvaliacaoCompletaResultado:
    return AvaliacaoCompletaResultado(
        avaliacao_id=avaliacao.id,
        paciente_id=str(avaliacao.paciente_id),
        data_avaliacao=avaliacao.data_avaliacao.isoformat(),
        resultados=avaliacao.resultado_json["resultados"],
        indice_risco_geral=avaliacao.indice_risco_geral,
        nivel_risco_geral=avaliacao.nivel_risco_geral,
    )


def _get_paciente_or_404(db: Session, paciente_id: int) -> Paciente:
    paciente = get_paciente(db, paciente_id)
    if paciente is None:
        raise HTTPException(status_code=404, detail="Paciente não encontrado")
    return paciente


def _get_avaliacao_or_404(db: Session, avaliacao_id: int) -> Avaliacao:
    avaliacao = get_avaliacao(db, avaliacao_id)
    if avaliacao is None:
        raise HTTPException(status_code=404, detail="Avaliação não encontrada")
    return avaliacao


def _create_pdf_response(avaliacao_id: int, paciente: Paciente, resultado_json: dict) -> StreamingResponse:
    buffer = BytesIO()
    gerar_laudo_pdf(buffer, paciente, resultado_json)
    buffer.seek(0)
    return StreamingResponse(
        buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=laudo_avaliacao_{avaliacao_id}.pdf"},
    )


# ---------------------------------------------------------------------------
# Application setup
# ---------------------------------------------------------------------------
app = FastAPI(
    title="Sistema Fisio API",
    description="API de avaliação de risco de lesões com persistência de pacientes, avaliações e geração de laudo em PDF.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup_event() -> None:
    init_db()


def get_db() -> Session:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ---------------------------------------------------------------------------
# API endpoints
# ---------------------------------------------------------------------------
@app.get("/", response_model=Dict[str, str], tags=["Informações"])
def root() -> Dict[str, str]:
    return {
        "message": "Bem-vindo à API Sistema Fisio.",
        "documentation": "/docs",
        "create_patient": "POST /pacientes",
        "list_patients": "GET /pacientes",
    }


@app.post("/pacientes", response_model=PacienteResponse, tags=["Pacientes"])
def criar_paciente_endpoint(
    payload: PacienteCreate,
    db: Session = Depends(get_db),
) -> PacienteResponse:
    paciente = criar_paciente(
        db,
        nome=payload.nome,
        data_nascimento=datetime.fromisoformat(payload.data_nascimento) if payload.data_nascimento else None,
        sexo=payload.sexo,
        email=payload.email,
        telefone=payload.telefone,
    )
    return _paciente_to_response(paciente)


@app.get("/pacientes", response_model=List[PacienteResponse], tags=["Pacientes"])
def listar_pacientes_endpoint(db: Session = Depends(get_db)) -> List[PacienteResponse]:
    pacientes = listar_pacientes(db)
    return [_paciente_to_response(paciente) for paciente in pacientes]


@app.get("/pacientes/{paciente_id}", response_model=PacienteResponse, tags=["Pacientes"])
def get_paciente_endpoint(paciente_id: int, db: Session = Depends(get_db)) -> PacienteResponse:
    paciente = _get_paciente_or_404(db, paciente_id)
    return _paciente_to_response(paciente)


@app.post("/pacientes/{paciente_id}/avaliacoes", response_model=AvaliacaoCompletaResultado, tags=["Avaliações"], summary="Registrar avaliação de paciente")
def criar_avaliacao_endpoint(
    paciente_id: int,
    avaliacao_input: AvaliacaoCompletaInput,
    db: Session = Depends(get_db),
) -> AvaliacaoCompletaResultado:
    paciente = _get_paciente_or_404(db, paciente_id)
    avaliacao_input = avaliacao_input.copy(update={"paciente_id": str(paciente.id)})
    avaliacao = criar_avaliacao_completa(db, paciente.id, avaliacao_input)
    return _avaliacao_to_response(avaliacao)


@app.get("/pacientes/{paciente_id}/avaliacoes", response_model=List[AvaliacaoCompletaResultado], tags=["Avaliações"])
def listar_avaliacoes_por_paciente_endpoint(paciente_id: int, db: Session = Depends(get_db)) -> List[AvaliacaoCompletaResultado]:
    _get_paciente_or_404(db, paciente_id)
    avaliacoes = listar_avaliacoes_por_paciente(db, paciente_id)
    return [_avaliacao_to_response(avaliacao) for avaliacao in avaliacoes]


@app.get("/avaliacoes/{avaliacao_id}", response_model=AvaliacaoCompletaResultado, tags=["Avaliações"])
def get_avaliacao_endpoint(avaliacao_id: int, db: Session = Depends(get_db)) -> AvaliacaoCompletaResultado:
    avaliacao = _get_avaliacao_or_404(db, avaliacao_id)
    return _avaliacao_to_response(avaliacao)


@app.get("/avaliacoes/{avaliacao_id}/laudo", tags=["Avaliações"])
def baixar_laudo_avaliacao(avaliacao_id: int, db: Session = Depends(get_db)) -> StreamingResponse:
    avaliacao = _get_avaliacao_or_404(db, avaliacao_id)
    paciente = _get_paciente_or_404(db, avaliacao.paciente_id)
    return _create_pdf_response(avaliacao_id, paciente, avaliacao.resultado_json)
