from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import List, Optional

from sqlalchemy import (
    JSON,
    Column,
    DateTime,
    Enum as SQLEnum,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, DeclarativeBase, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class NivelRiscoEnum(str, Enum):
    NORMAL = "normal"
    MODERADO = "moderado"
    ALTO = "alto"


class Paciente(Base):
    __tablename__ = "pacientes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    nome: Mapped[str] = mapped_column(String(255), nullable=False)
    data_nascimento: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    sexo: Mapped[Optional[str]] = mapped_column(String(24), nullable=True)
    email: Mapped[Optional[str]] = mapped_column(String(255), unique=True, nullable=True)
    telefone: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    avaliacoes: Mapped[List["Avaliacao"]] = relationship(
        "Avaliacao",
        back_populates="paciente",
        cascade="all, delete-orphan",
    )


class Avaliacao(Base):
    __tablename__ = "avaliacoes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    paciente_id: Mapped[int] = mapped_column(ForeignKey("pacientes.id"), nullable=False)
    data_avaliacao: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    indice_risco_geral: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    nivel_risco_geral: Mapped[Optional[NivelRiscoEnum]] = mapped_column(SQLEnum(NivelRiscoEnum), nullable=True)
    resultado_json: Mapped[dict] = mapped_column(JSON, nullable=False)

    paciente: Mapped[Paciente] = relationship("Paciente", back_populates="avaliacoes")
