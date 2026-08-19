"""
Modelos de dados (Pydantic) para entrada e saída dos cálculos de risco.

Os nomes de campo seguem, propositalmente, a mesma nomenclatura usada na
planilha "Perfil de Risco" da fisioterapeuta, para facilitar o mapeamento
direto entre o formulário do sistema e o que ela já preenche hoje.
"""

from __future__ import annotations

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class NivelRisco(str, Enum):
    NORMAL = "normal"
    MODERADO = "moderado"
    ALTO = "alto"


class ResultadoTeste(BaseModel):
    """Resultado padronizado de qualquer teste avaliado."""
    nome_teste: str
    valor_direito: Optional[float] = None
    valor_esquerdo: Optional[float] = None
    assimetria_pct: Optional[float] = None
    nivel_risco: NivelRisco
    resultado_texto: str
    conduta_fisioterapeutica: Optional[str] = None


# ---------------------------------------------------------------------------
# Entrada: dados brutos de uma avaliação (um subconjunto inicial de testes —
# os mais representativos do laudo. Novos testes podem ser adicionados aqui
# sem quebrar o restante do sistema).
# ---------------------------------------------------------------------------
class DadosForcaQuadricepsIsquiotibiais(BaseModel):
    quadriceps_1rm_d: float = Field(..., description="1RM de quadríceps direito (Kgf)")
    quadriceps_1rm_e: float = Field(..., description="1RM de quadríceps esquerdo (Kgf)")
    isquiotibiais_1rm_d: float = Field(..., description="1RM de isquiotibiais direito (Kgf)")
    isquiotibiais_1rm_e: float = Field(..., description="1RM de isquiotibiais esquerdo (Kgf)")


class DadosCore(BaseModel):
    extensores_tronco_s: float = Field(..., description="Tempo de resistência dos extensores de tronco (s)")
    prancha_lateral_d_s: float = Field(..., description="Prancha lateral direita (s)")
    prancha_lateral_e_s: float = Field(..., description="Prancha lateral esquerda (s)")


class DadosMobilidadeQuadril(BaseModel):
    quadril_d_graus: float
    quadril_e_graus: float


class DadosMobilidadeTornozelo(BaseModel):
    lunge_d_graus: float
    lunge_e_graus: float


class DadosAdmPassivaOmbro(BaseModel):
    rotacao_externa_d: float
    rotacao_interna_d: float
    rotacao_externa_e: float
    rotacao_interna_e: float
    atleta_arremesso: bool = False


class DadosAdmAtivaOmbro(BaseModel):
    rotacao_interna_d: float
    rotacao_interna_e: float
    rotacao_externa_d: float
    rotacao_externa_e: float


class DadosYBalance(BaseModel):
    comprimento_mid_cm: float
    comprimento_mie_cm: float
    anterior_mid: float
    posteromedial_mid: float
    posterolateral_mid: float
    anterior_mie: float
    posteromedial_mie: float
    posterolateral_mie: float


class DadosForcaSimetrica(BaseModel):
    """Genérico — usado para qualquer par de grupos musculares avaliados
    no dinamômetro isométrico (glúteo médio, glúteo máximo, adutores etc.)."""
    nome_grupo_muscular: str
    valor_d: float
    valor_e: float


class DadosSingleHop(BaseModel):
    media_mid_cm: float
    media_mie_cm: float


class DadosPreensaoPalmar(BaseModel):
    direita_kgf: float
    esquerda_kgf: float


class DadosFlexoAducaoOmbro(BaseModel):
    flexao_passiva_d: float
    flexao_passiva_e: float
    aducao_horizontal_d: float
    aducao_horizontal_e: float


class DadosEscalaCargaRecuperacao(BaseModel):
    treino: float = Field(..., ge=0, le=10)
    estado_fisico: float = Field(..., ge=0, le=10)
    prontidao_sono: float = Field(..., ge=0, le=10)
    dor: float = Field(..., ge=0, le=10)


class AvaliacaoCompletaInput(BaseModel):
    """Payload de uma avaliação completa — todos os blocos são opcionais
    para permitir avaliações parciais (nem toda sessão inclui todos os
    testes)."""
    paciente_id: str
    data_avaliacao: str

    forca_quadriceps_isquiotibiais: Optional[DadosForcaQuadricepsIsquiotibiais] = None
    core: Optional[DadosCore] = None
    mobilidade_quadril: Optional[DadosMobilidadeQuadril] = None
    mobilidade_tornozelo: Optional[DadosMobilidadeTornozelo] = None
    adm_passiva_ombro: Optional[DadosAdmPassivaOmbro] = None
    adm_ativa_ombro: Optional[DadosAdmAtivaOmbro] = None
    y_balance: Optional[DadosYBalance] = None
    forcas_simetricas: list[DadosForcaSimetrica] = Field(default_factory=list)
    single_hop: Optional[DadosSingleHop] = None
    preensao_palmar: Optional[DadosPreensaoPalmar] = None
    flexo_aducao_ombro: Optional[DadosFlexoAducaoOmbro] = None
    escala_carga_recuperacao: Optional[DadosEscalaCargaRecuperacao] = None


class AvaliacaoCompletaResultado(BaseModel):
    paciente_id: str
    data_avaliacao: str
    resultados: list[ResultadoTeste]
    indice_risco_geral: Optional[float] = None
    nivel_risco_geral: Optional[NivelRisco] = None
