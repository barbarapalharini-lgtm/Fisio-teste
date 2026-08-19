from __future__ import annotations

from datetime import datetime

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.calculations.schemas import AvaliacaoCompletaInput, DadosCore
from app.db import init_db
from app.crud import criar_avaliacao, criar_avaliacao_completa, criar_paciente, get_paciente, listar_avaliacoes_por_paciente
from app.models import Avaliacao, Paciente


def test_db_models_create_and_query():
    engine = create_engine("sqlite:///:memory:", future=True)
    init_db(engine)

    with Session(engine) as db:
        paciente = criar_paciente(db, nome="Regiane Zaparoli", data_nascimento=datetime(1990, 1, 1), sexo="F")
        assert paciente.id is not None
        assert paciente.nome == "Regiane Zaparoli"

        avaliacao = criar_avaliacao(
            db,
            paciente_id=paciente.id,
            data_avaliacao=datetime(2026, 1, 1, 10, 0),
            resultado_json={"resultado": "ok"},
            indice_risco_geral=50.0,
            nivel_risco_geral="moderado",
        )
        assert avaliacao.id is not None
        assert avaliacao.paciente_id == paciente.id

        paciente_salvo = get_paciente(db, paciente.id)
        assert paciente_salvo is not None
        assert paciente_salvo.nome == "Regiane Zaparoli"

        avaliacoes = listar_avaliacoes_por_paciente(db, paciente.id)
        assert len(avaliacoes) == 1
        assert avaliacoes[0].resultado_json["resultado"] == "ok"


def test_criar_avaliacao_completa_calculada():
    engine = create_engine("sqlite:///:memory:", future=True)
    init_db(engine)

    with Session(engine) as db:
        paciente = criar_paciente(db, nome="Regiane Zaparoli", data_nascimento=datetime(1990, 1, 1), sexo="F")
        assert paciente.id is not None

        avaliacao_input = AvaliacaoCompletaInput(
            paciente_id="123",
            data_avaliacao="2026-01-01T10:00:00",
            core=DadosCore(extensores_tronco_s=120, prancha_lateral_d_s=60, prancha_lateral_e_s=60),
        )

        avaliacao = criar_avaliacao_completa(db, paciente.id, avaliacao_input)
        assert avaliacao.id is not None
        assert avaliacao.paciente_id == paciente.id
        assert avaliacao.indice_risco_geral == 0.0
        assert avaliacao.nivel_risco_geral == "normal"
        assert isinstance(avaliacao.resultado_json, dict)
        assert avaliacao.resultado_json["paciente_id"] == "123"
