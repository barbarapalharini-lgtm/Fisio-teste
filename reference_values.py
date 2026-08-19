"""
Valores de referência (normalidade) extraídos do modelo de laudo da
clínica funcional.e — "Avaliação Biomecânica do Risco de Lesões".

Cada constante representa os limites usados para classificar um teste como
NORMAL, RISCO MODERADO ou RISCO ALTO. Ajuste aqui se a fisioterapeuta
trouxer novos parâmetros — o restante do sistema não precisa mudar.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class FaixaClassificacao:
    """Representa os limites de um teste com faixas de risco."""
    normal_min: float | None = None
    normal_max: float | None = None
    assimetria_max: float | None = None


# ---------------------------------------------------------------------------
# Força de Quadríceps e Isquiotibiais (1RM) — Razão QD/IT
# ---------------------------------------------------------------------------
# Ótimo: IT > 75% de QD. Faixas de classificação da razão (%):
RAZAO_QD_IT_BOM = 60.0        # >= 60% => bom
RAZAO_QD_IT_MODERADO_MIN = 50.0  # 50–60% => risco moderado
# < 50% => déficit muscular grave / risco alto

# ---------------------------------------------------------------------------
# Resistência dos músculos do CORE
# ---------------------------------------------------------------------------
CORE_EXTENSORES_TRONCO_MIN_S = 101.0   # segundos
CORE_PRANCHA_LATERAL_MIN_S = 58.0      # segundos
CORE_ASSIMETRIA_MAX = 10.0             # %

# ---------------------------------------------------------------------------
# Mobilidade de quadril (graus)
# ---------------------------------------------------------------------------
MOBILIDADE_QUADRIL = FaixaClassificacao(normal_min=30, normal_max=40, assimetria_max=5)

# ---------------------------------------------------------------------------
# Mobilidade de tornozelo — Lunge test (graus)
# ---------------------------------------------------------------------------
MOBILIDADE_TORNOZELO = FaixaClassificacao(normal_min=36, normal_max=45, assimetria_max=5)

# ---------------------------------------------------------------------------
# ADM passiva de rotação de ombro (GIRD)
# ---------------------------------------------------------------------------
ROTACAO_EXTERNA_OMBRO_REF = 90.0
ROTACAO_INTERNA_OMBRO_REF = 80.0
ADM_PASSIVA_ASSIMETRIA_MAX = 18.0        # graus
ADM_TOTAL_OMBRO_REF = 170.0              # RE + RI
ADM_TOTAL_REDUCAO_MAX = 10.0             # graus (atleta geral)
ADM_TOTAL_REDUCAO_MAX_ARREMESSO = 5.0    # graus (atleta de arremesso)

# ---------------------------------------------------------------------------
# ADM ativa de rotação de ombro
# ---------------------------------------------------------------------------
ADM_ATIVA_OMBRO = FaixaClassificacao(normal_min=80, normal_max=90, assimetria_max=10)

# ---------------------------------------------------------------------------
# Y Balance Test
# ---------------------------------------------------------------------------
Y_BALANCE_DIFERENCA_DIRECAO_MAX_CM = 4.0
Y_BALANCE_ESCORE_MIN_PCT = 94.0

# ---------------------------------------------------------------------------
# Simetria de força — dinamômetro isométrico (qualquer grupo muscular)
# ---------------------------------------------------------------------------
FORCA_ASSIMETRIA_NORMAL_MAX = 10.0     # < 10% = normal
FORCA_ASSIMETRIA_MODERADO_MAX = 20.0   # 10–20% = risco moderado
# > 20% = risco alto

# ---------------------------------------------------------------------------
# Testes de salto (Single Hop, Triple Hop, etc.)
# ---------------------------------------------------------------------------
SALTO_ASSIMETRIA_MAX = 10.0  # %

# ---------------------------------------------------------------------------
# Membros superiores — força de preensão palmar, flexão/adução de ombro
# ---------------------------------------------------------------------------
MMSS_ASSIMETRIA_MAX_PCT = 10.0    # preensão palmar (%)
MMSS_ASSIMETRIA_MAX_GRAUS = 10.0  # flexão / adução horizontal de ombro (°)

# ---------------------------------------------------------------------------
# Escala de carga e recuperação (subjetiva, 0–10 cada item, soma 0–40)
# Quanto MENOR o escore, MELHOR.
# ---------------------------------------------------------------------------
ESCALA_CARGA_RECUPERACAO_MAX = 40.0
