"""
Testes de validação: usam os dados REAIS da avaliação da Regiane Zaparoli
(extraídos do laudo em PDF e da planilha) para conferir se a lógica do
sistema reproduz os mesmos resultados que a fisioterapeuta calculou
manualmente.
"""

from app.calculations.risk_calculator import (
    avaliar_core,
    avaliar_forca_quadriceps_isquiotibiais,
    avaliar_forca_simetrica,
    avaliar_mobilidade_quadril,
    avaliar_mobilidade_tornozelo,
    avaliar_single_hop,
    avaliar_y_balance,
    calcular_assimetria_pct,
)
from app.calculations.schemas import (
    DadosCore,
    DadosForcaQuadricepsIsquiotibiais,
    DadosForcaSimetrica,
    DadosMobilidadeQuadril,
    DadosMobilidadeTornozelo,
    DadosSingleHop,
    DadosYBalance,
    NivelRisco,
)


def test_assimetria_basica():
    # PDF: assimetria de força de quadríceps = 42,05%
    assert calcular_assimetria_pct(20.16, 34.79) == 42.05


def test_forca_quadriceps_isquiotibiais_regiane():
    dados = DadosForcaQuadricepsIsquiotibiais(
        quadriceps_1rm_d=20.16,
        quadriceps_1rm_e=34.79,
        isquiotibiais_1rm_d=4.92,
        isquiotibiais_1rm_e=5.31,
    )
    resultados = avaliar_forca_quadriceps_isquiotibiais(dados)

    # Assimetria de quadríceps deve bater com o laudo: 42,05%
    assimetria_quad = next(r for r in resultados if "quadríceps" in r.nome_teste)
    assert assimetria_quad.assimetria_pct == 42.05

    # Assimetria de isquiotibiais deve bater com o laudo: 7,34%
    assimetria_isq = next(r for r in resultados if "isquiotibiais" in r.nome_teste)
    assert assimetria_isq.assimetria_pct == 7.34

    # Razões QD/IT (IT como % de QD): D = 24,40% E = 15,26% (conforme laudo)
    razao_d = next(r for r in resultados if "direito" in r.nome_teste)
    razao_e = next(r for r in resultados if "esquerdo" in r.nome_teste)
    assert razao_d.valor_direito == 24.40
    assert razao_e.valor_esquerdo == 15.26
    # Ambos abaixo de 50% -> risco alto, conforme conduta indicada no laudo
    assert razao_d.nivel_risco == NivelRisco.ALTO
    assert razao_e.nivel_risco == NivelRisco.ALTO


def test_core_regiane_dentro_da_normalidade():
    dados = DadosCore(extensores_tronco_s=135, prancha_lateral_d_s=60, prancha_lateral_e_s=60)
    resultado = avaliar_core(dados)
    assert resultado.nivel_risco == NivelRisco.NORMAL
    assert resultado.assimetria_pct == 0.0


def test_mobilidade_quadril_regiane_alterada():
    # Laudo: D=25 E=30 assimetria=5 -> quadril direito abaixo da normalidade (min 30)
    dados = DadosMobilidadeQuadril(quadril_d_graus=25, quadril_e_graus=30)
    resultado = avaliar_mobilidade_quadril(dados)
    assert resultado.nivel_risco == NivelRisco.MODERADO
    assert "direito" in resultado.conduta_fisioterapeutica


def test_mobilidade_tornozelo_regiane_alterada():
    # Laudo: D=35 E=30 -> tornozelo esquerdo abaixo da normalidade (min 36)
    dados = DadosMobilidadeTornozelo(lunge_d_graus=35, lunge_e_graus=30)
    resultado = avaliar_mobilidade_tornozelo(dados)
    assert resultado.nivel_risco == NivelRisco.MODERADO
    assert "esquerdo" in resultado.conduta_fisioterapeutica


def test_forca_simetrica_adutores_risco_moderado():
    # Exemplo hipotético dentro da faixa de risco moderado (10-20%)
    dados = DadosForcaSimetrica(nome_grupo_muscular="adutores de quadril", valor_d=30, valor_e=25)
    resultado = avaliar_forca_simetrica(dados)
    assert resultado.nivel_risco == NivelRisco.MODERADO
    assert "esquerdo" in resultado.conduta_fisioterapeutica


def test_single_hop_regiane():
    # Laudo: Média MID=120 MIE=104,5 assimetria=12,91% (diferença de
    # arredondamento de centésimos é esperada: nosso cálculo dá 12,92%
    # a partir dos valores já arredondados do laudo)
    dados = DadosSingleHop(media_mid_cm=120, media_mie_cm=104.5)
    resultado = avaliar_single_hop(dados)
    assert resultado.assimetria_pct == 12.92
    assert resultado.nivel_risco == NivelRisco.MODERADO


def test_y_balance_regiane_escore_baixo():
    dados = DadosYBalance(
        comprimento_mid_cm=100,  # valor de exemplo (não informado no PDF fornecido)
        comprimento_mie_cm=100,
        anterior_mid=56,
        posteromedial_mid=77,
        posterolateral_mid=66,
        anterior_mie=53,
        posteromedial_mie=90,
        posterolateral_mie=74,
    )
    resultado = avaliar_y_balance(dados)
    # Com comprimento de exemplo o escore não vai bater exatamente com o
    # laudo (75,82% / 76,56%), mas deve ficar abaixo de 94% e ser sinalizado
    # como risco.
    assert resultado.nivel_risco == NivelRisco.MODERADO


if __name__ == "__main__":
    import pytest

    raise SystemExit(pytest.main([__file__, "-v"]))
