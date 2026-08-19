from __future__ import annotations

import json
from datetime import datetime

from app.calculations.schemas import (
    AvaliacaoCompletaInput,
    DadosAdmAtivaOmbro,
    DadosAdmPassivaOmbro,
    DadosCore,
    DadosEscalaCargaRecuperacao,
    DadosFlexoAducaoOmbro,
    DadosForcaQuadricepsIsquiotibiais,
    DadosMobilidadeQuadril,
    DadosMobilidadeTornozelo,
    DadosPreensaoPalmar,
    DadosSingleHop,
    DadosYBalance,
)
from app.crud import criar_avaliacao_completa, criar_paciente
from app.db import init_db, SessionLocal
from app.pdf_generator import gerar_laudo_pdf


def main() -> None:
    init_db()

    with SessionLocal() as db:
        paciente = criar_paciente(
            db,
            nome="Regiane Zaparoli",
            data_nascimento=datetime(1982, 6, 24),
            sexo="F",
        )

        avaliacao_input = AvaliacaoCompletaInput(
            paciente_id=str(paciente.id),
            data_avaliacao="2026-06-18T10:00:00",
            forca_quadriceps_isquiotibiais=DadosForcaQuadricepsIsquiotibiais(
                quadriceps_1rm_d=20.16,
                quadriceps_1rm_e=34.79,
                isquiotibiais_1rm_d=4.92,
                isquiotibiais_1rm_e=5.31,
            ),
            core=DadosCore(
                extensores_tronco_s=135,
                prancha_lateral_d_s=60,
                prancha_lateral_e_s=60,
            ),
            mobilidade_quadril=DadosMobilidadeQuadril(
                quadril_d_graus=25,
                quadril_e_graus=30,
            ),
            mobilidade_tornozelo=DadosMobilidadeTornozelo(
                lunge_d_graus=35,
                lunge_e_graus=30,
            ),
            adm_passiva_ombro=DadosAdmPassivaOmbro(
                rotacao_externa_d=120,
                rotacao_interna_d=90,
                rotacao_externa_e=115,
                rotacao_interna_e=110,
            ),
            adm_ativa_ombro=DadosAdmAtivaOmbro(
                rotacao_interna_d=90,
                rotacao_interna_e=92,
                rotacao_externa_d=88,
                rotacao_externa_e=91,
            ),
            single_hop=DadosSingleHop(
                media_mid_cm=120,
                media_mie_cm=104.5,
            ),
            preensao_palmar=DadosPreensaoPalmar(
                direita_kgf=67.4,
                esquerda_kgf=54.4,
            ),
            flexo_aducao_ombro=DadosFlexoAducaoOmbro(
                flexao_passiva_d=90,
                flexao_passiva_e=95,
                aducao_horizontal_d=75,
                aducao_horizontal_e=85,
            ),
            escala_carga_recuperacao=DadosEscalaCargaRecuperacao(
                treino=4.5,
                estado_fisico=3.5,
                prontidao_sono=2.5,
                dor=2.5,
            ),
            y_balance=DadosYBalance(
                comprimento_mid_cm=100,
                comprimento_mie_cm=100,
                anterior_mid=56,
                posteromedial_mid=77,
                posterolateral_mid=66,
                anterior_mie=53,
                posteromedial_mie=90,
                posterolateral_mie=74,
            ),
        )

        avaliacao = criar_avaliacao_completa(db, paciente.id, avaliacao_input)

        print("resultado_json:")
        print(json.dumps(avaliacao.resultado_json, indent=2, ensure_ascii=False))
        print()
        print("indice_risco_geral:", avaliacao.indice_risco_geral)
        output_path = "output/laudo_regiane_teste.pdf"
        gerar_laudo_pdf(output_path, paciente, avaliacao.resultado_json)
        print("laudo_pdf:", output_path)


if __name__ == "__main__":
    main()
