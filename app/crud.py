from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy.orm import Session

from app.calculations.risk_calculator import calcular_avaliacao_completa
from app.calculations.schemas import AvaliacaoCompletaInput
from .models import Avaliacao, NivelRiscoEnum, Paciente


def criar_paciente(
    db: Session,
    nome: str,
    data_nascimento: Optional[datetime] = None,
    sexo: Optional[str] = None,
    email: Optional[str] = None,
    telefone: Optional[str] = None,
) -> Paciente:
    paciente = Paciente(
        nome=nome,
        data_nascimento=data_nascimento,
        sexo=sexo,
        email=email,
        telefone=telefone,
    )
    db.add(paciente)
    db.commit()
    db.refresh(paciente)
    return paciente


def criar_avaliacao(
    db: Session,
    paciente_id: int,
    data_avaliacao: datetime,
    resultado_json: dict,
    indice_risco_geral: Optional[float] = None,
    nivel_risco_geral: Optional[NivelRiscoEnum] = None,
) -> Avaliacao:
    avaliacao = Avaliacao(
        paciente_id=paciente_id,
        data_avaliacao=data_avaliacao,
        resultado_json=resultado_json,
        indice_risco_geral=indice_risco_geral,
        nivel_risco_geral=nivel_risco_geral,
    )
    db.add(avaliacao)
    db.commit()
    db.refresh(avaliacao)
    return avaliacao


def criar_avaliacao_completa(
    db: Session,
    paciente_id: int,
    avaliacao_input: AvaliacaoCompletaInput,
) -> Avaliacao:
    resultado = calcular_avaliacao_completa(avaliacao_input)
    nivel_risco_geral = (
        NivelRiscoEnum(resultado.nivel_risco_geral.value)
        if resultado.nivel_risco_geral is not None
        else None
    )
    return criar_avaliacao(
        db,
        paciente_id=paciente_id,
        data_avaliacao=datetime.fromisoformat(avaliacao_input.data_avaliacao),
        resultado_json=resultado.dict(),
        indice_risco_geral=resultado.indice_risco_geral,
        nivel_risco_geral=nivel_risco_geral,
    )


def get_paciente(db: Session, paciente_id: int) -> Optional[Paciente]:
    return db.get(Paciente, paciente_id)


def listar_pacientes(db: Session) -> list[Paciente]:
    return db.query(Paciente).all()


def get_avaliacao(db: Session, avaliacao_id: int) -> Optional[Avaliacao]:
    return db.get(Avaliacao, avaliacao_id)


def listar_avaliacoes_por_paciente(db: Session, paciente_id: int) -> list[Avaliacao]:
    return db.query(Avaliacao).filter(Avaliacao.paciente_id == paciente_id).all()
