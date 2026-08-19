"""
Lógica de cálculo de risco de lesões, replicando as fórmulas e faixas de
referência já usadas pela fisioterapeuta na planilha e no laudo da
clínica funcional.e.

Cada função `avaliar_*` recebe os dados brutos de um teste e devolve um
`ResultadoTeste` já com: valores, % de assimetria, classificação de risco
e o texto de conduta fisioterapêutica sugerida (mesmo texto-modelo do
laudo, adaptado dinamicamente ao lado/grupo muscular afetado).
"""

from __future__ import annotations

from . import reference_values as ref
from .schemas import (
    AvaliacaoCompletaInput,
    AvaliacaoCompletaResultado,
    DadosAdmAtivaOmbro,
    DadosAdmPassivaOmbro,
    DadosCore,
    DadosEscalaCargaRecuperacao,
    DadosFlexoAducaoOmbro,
    DadosForcaQuadricepsIsquiotibiais,
    DadosForcaSimetrica,
    DadosMobilidadeQuadril,
    DadosMobilidadeTornozelo,
    DadosPreensaoPalmar,
    DadosSingleHop,
    DadosYBalance,
    NivelRisco,
    ResultadoTeste,
)


# ---------------------------------------------------------------------------
# Utilitários genéricos
# ---------------------------------------------------------------------------
def calcular_assimetria_pct(valor_d: float, valor_e: float) -> float:
    """Réplica da fórmula usada na planilha: 100 - (menor/maior * 100).
    Sempre retorna um valor >= 0, independente de qual lado é maior."""
    if valor_d == 0 and valor_e == 0:
        return 0.0
    maior = max(valor_d, valor_e)
    menor = min(valor_d, valor_e)
    if maior == 0:
        return 0.0
    return round(100 - (menor / maior * 100), 2)


def lado_mais_fraco(valor_d: float, valor_e: float) -> str:
    if valor_d == valor_e:
        return "bilateral"
    return "esquerdo" if valor_e < valor_d else "direito"


# ---------------------------------------------------------------------------
# Força de Quadríceps e Isquiotibiais — Razão QD/IT
# ---------------------------------------------------------------------------
def avaliar_forca_quadriceps_isquiotibiais(
    dados: DadosForcaQuadricepsIsquiotibiais,
) -> list[ResultadoTeste]:
    resultados: list[ResultadoTeste] = []

    assimetria_quad = calcular_assimetria_pct(dados.quadriceps_1rm_d, dados.quadriceps_1rm_e)
    assimetria_isq = calcular_assimetria_pct(dados.isquiotibiais_1rm_d, dados.isquiotibiais_1rm_e)

    lado_fraco_quad = lado_mais_fraco(dados.quadriceps_1rm_d, dados.quadriceps_1rm_e)
    lado_fraco_isq = lado_mais_fraco(dados.isquiotibiais_1rm_d, dados.isquiotibiais_1rm_e)

    # Razão QD/IT por lado (IT como % de QD)
    razao_d = round((dados.isquiotibiais_1rm_d * 100) / dados.quadriceps_1rm_d, 2)
    razao_e = round((dados.isquiotibiais_1rm_e * 100) / dados.quadriceps_1rm_e, 2)

    for lado, razao in (("direito", razao_d), ("esquerdo", razao_e)):
        if razao >= ref.RAZAO_QD_IT_BOM:
            nivel = NivelRisco.NORMAL
            texto = f"Razão QD/IT {lado} ({razao}%) dentro da faixa considerada boa."
        elif razao >= ref.RAZAO_QD_IT_MODERADO_MIN:
            nivel = NivelRisco.MODERADO
            texto = f"Razão QD/IT {lado} ({razao}%) em zona moderada de risco."
        else:
            nivel = NivelRisco.ALTO
            texto = (
                f"Razão QD/IT {lado} ({razao}%) indica déficit muscular grave "
                "e risco de lesão alto para patologias do joelho."
            )
        resultados.append(
            ResultadoTeste(
                nome_teste=f"Razão QD/IT - {lado}",
                valor_direito=razao_d if lado == "direito" else None,
                valor_esquerdo=razao_e if lado == "esquerdo" else None,
                nivel_risco=nivel,
                resultado_texto=texto,
                conduta_fisioterapeutica=(
                    "Fortalecer/melhorar a ativação dos músculos isquiotibiais "
                    "bilateral para aumentar a razão QD/IT."
                    if nivel != NivelRisco.NORMAL
                    else None
                ),
            )
        )

    resultados.append(
        ResultadoTeste(
            nome_teste="Assimetria de força de quadríceps (1RM)",
            valor_direito=dados.quadriceps_1rm_d,
            valor_esquerdo=dados.quadriceps_1rm_e,
            assimetria_pct=assimetria_quad,
            nivel_risco=_classificar_assimetria_forca(assimetria_quad),
            resultado_texto=f"Assimetria de {assimetria_quad}% entre os lados (lado mais fraco: {lado_fraco_quad}).",
            conduta_fisioterapeutica=(
                f"Fortalecer/melhorar a ativação do quadríceps {lado_fraco_quad} para reduzir assimetria."
                if assimetria_quad >= ref.FORCA_ASSIMETRIA_NORMAL_MAX
                else None
            ),
        )
    )
    resultados.append(
        ResultadoTeste(
            nome_teste="Assimetria de força de isquiotibiais (1RM)",
            valor_direito=dados.isquiotibiais_1rm_d,
            valor_esquerdo=dados.isquiotibiais_1rm_e,
            assimetria_pct=assimetria_isq,
            nivel_risco=_classificar_assimetria_forca(assimetria_isq),
            resultado_texto=f"Assimetria de {assimetria_isq}% entre os lados (lado mais fraco: {lado_fraco_isq}).",
            conduta_fisioterapeutica=(
                f"Fortalecer/melhorar a ativação dos isquiotibiais {lado_fraco_isq} para reduzir assimetria."
                if assimetria_isq >= ref.FORCA_ASSIMETRIA_NORMAL_MAX
                else None
            ),
        )
    )
    return resultados


def _classificar_assimetria_forca(assimetria_pct: float) -> NivelRisco:
    if assimetria_pct < ref.FORCA_ASSIMETRIA_NORMAL_MAX:
        return NivelRisco.NORMAL
    if assimetria_pct <= ref.FORCA_ASSIMETRIA_MODERADO_MAX:
        return NivelRisco.MODERADO
    return NivelRisco.ALTO


# ---------------------------------------------------------------------------
# CORE
# ---------------------------------------------------------------------------
def avaliar_core(dados: DadosCore) -> ResultadoTeste:
    assimetria_prancha = calcular_assimetria_pct(dados.prancha_lateral_d_s, dados.prancha_lateral_e_s)

    dentro_padrao = (
        dados.extensores_tronco_s > ref.CORE_EXTENSORES_TRONCO_MIN_S
        and dados.prancha_lateral_d_s > ref.CORE_PRANCHA_LATERAL_MIN_S
        and dados.prancha_lateral_e_s > ref.CORE_PRANCHA_LATERAL_MIN_S
        and assimetria_prancha <= ref.CORE_ASSIMETRIA_MAX
    )

    nivel = NivelRisco.NORMAL if dentro_padrao else NivelRisco.MODERADO
    texto = (
        "Valores dentro do padrão de normalidade."
        if dentro_padrao
        else "Valores abaixo do padrão de normalidade e/ou assimetria acima do aceitável entre as pranchas laterais."
    )
    return ResultadoTeste(
        nome_teste="Resistência dos músculos do CORE",
        valor_direito=dados.prancha_lateral_d_s,
        valor_esquerdo=dados.prancha_lateral_e_s,
        assimetria_pct=assimetria_prancha,
        nivel_risco=nivel,
        resultado_texto=texto,
        conduta_fisioterapeutica=None if dentro_padrao else "Fortalecer musculatura estabilizadora do CORE, com foco no lado mais fraco.",
    )


# ---------------------------------------------------------------------------
# Mobilidade de quadril / tornozelo (faixa fixa + assimetria)
# ---------------------------------------------------------------------------
def _avaliar_faixa_com_assimetria(
    nome_teste: str,
    valor_d: float,
    valor_e: float,
    faixa: ref.FaixaClassificacao,
    conduta_base: str,
) -> ResultadoTeste:
    assimetria = calcular_assimetria_pct(valor_d, valor_e)
    lado_fraco = lado_mais_fraco(valor_d, valor_e)

    fora_da_faixa = []
    if faixa.normal_min is not None and valor_d < faixa.normal_min:
        fora_da_faixa.append("direito")
    if faixa.normal_min is not None and valor_e < faixa.normal_min:
        fora_da_faixa.append("esquerdo")
    if faixa.normal_max is not None and valor_d > faixa.normal_max:
        fora_da_faixa.append("direito")
    if faixa.normal_max is not None and valor_e > faixa.normal_max:
        fora_da_faixa.append("esquerdo")

    assimetria_alta = faixa.assimetria_max is not None and assimetria > faixa.assimetria_max

    if not fora_da_faixa and not assimetria_alta:
        nivel = NivelRisco.NORMAL
        texto = "Valores dentro do padrão de normalidade."
        conduta = None
    else:
        nivel = NivelRisco.MODERADO
        partes = []
        if fora_da_faixa:
            partes.append(f"valores abaixo/acima da normalidade no lado {', '.join(set(fora_da_faixa))}")
        if assimetria_alta:
            partes.append(f"assimetria de {assimetria}% acima do limite aceitável")
        texto = "Resultado alterado: " + "; ".join(partes) + "."
        conduta = f"{conduta_base} (foco no lado {lado_fraco})."

    return ResultadoTeste(
        nome_teste=nome_teste,
        valor_direito=valor_d,
        valor_esquerdo=valor_e,
        assimetria_pct=assimetria,
        nivel_risco=nivel,
        resultado_texto=texto,
        conduta_fisioterapeutica=conduta,
    )


def avaliar_mobilidade_quadril(dados: DadosMobilidadeQuadril) -> ResultadoTeste:
    return _avaliar_faixa_com_assimetria(
        "Mobilidade de quadril",
        dados.quadril_d_graus,
        dados.quadril_e_graus,
        ref.MOBILIDADE_QUADRIL,
        "Realizar exercícios para ganho de mobilidade de quadril",
    )


def avaliar_mobilidade_tornozelo(dados: DadosMobilidadeTornozelo) -> ResultadoTeste:
    return _avaliar_faixa_com_assimetria(
        "Mobilidade de tornozelo (Lunge test)",
        dados.lunge_d_graus,
        dados.lunge_e_graus,
        ref.MOBILIDADE_TORNOZELO,
        "Melhorar mobilidade de tornozelo e flexibilidade dos músculos plantiflexores (tríceps sural)",
    )


# ---------------------------------------------------------------------------
# ADM passiva de ombro (GIRD)
# ---------------------------------------------------------------------------
def avaliar_adm_passiva_ombro(dados: DadosAdmPassivaOmbro) -> list[ResultadoTeste]:
    resultados = []
    assimetria_d = round(abs(dados.rotacao_externa_d - ref.ROTACAO_EXTERNA_OMBRO_REF), 2)
    total_d = dados.rotacao_externa_d + dados.rotacao_interna_d
    total_e = dados.rotacao_externa_e + dados.rotacao_interna_e

    reducao_max = (
        ref.ADM_TOTAL_REDUCAO_MAX_ARREMESSO if dados.atleta_arremesso else ref.ADM_TOTAL_REDUCAO_MAX
    )

    for lado, re_, ri_, total in (
        ("direito", dados.rotacao_externa_d, dados.rotacao_interna_d, total_d),
        ("esquerdo", dados.rotacao_externa_e, dados.rotacao_interna_e, total_e),
    ):
        assimetria_re = round(abs(re_ - ref.ROTACAO_EXTERNA_OMBRO_REF), 2)
        assimetria_ri = round(abs(ri_ - ref.ROTACAO_INTERNA_OMBRO_REF), 2)
        reducao_total = round(ref.ADM_TOTAL_OMBRO_REF - total, 2)

        alterado = (
            assimetria_re > ref.ADM_PASSIVA_ASSIMETRIA_MAX
            or assimetria_ri > ref.ADM_PASSIVA_ASSIMETRIA_MAX
            or reducao_total > reducao_max
        )
        nivel = NivelRisco.MODERADO if alterado else NivelRisco.NORMAL
        texto = (
            f"Rotação externa {re_}°, rotação interna {ri_}° (ombro {lado})."
            + (" Redução de amplitude total acima do aceitável." if reducao_total > reducao_max else "")
        )
        resultados.append(
            ResultadoTeste(
                nome_teste=f"ADM passiva de rotação de ombro - {lado} (GIRD)",
                valor_direito=re_ if lado == "direito" else None,
                valor_esquerdo=re_ if lado == "esquerdo" else None,
                nivel_risco=nivel,
                resultado_texto=texto,
                conduta_fisioterapeutica=(
                    f"Realizar exercícios de fortalecimento/mobilidade para rotadores do ombro {lado}."
                    if alterado
                    else None
                ),
            )
        )
    return resultados


def avaliar_adm_ativa_ombro(dados: DadosAdmAtivaOmbro) -> list[ResultadoTeste]:
    resultados = []
    assimetria_interna = calcular_assimetria_pct(dados.rotacao_interna_d, dados.rotacao_interna_e)
    assimetria_externa = calcular_assimetria_pct(dados.rotacao_externa_d, dados.rotacao_externa_e)

    for nome, valor_d, valor_e, assimetria in (
        ("ADM ativa - rotação interna de ombro", dados.rotacao_interna_d, dados.rotacao_interna_e, assimetria_interna),
        ("ADM ativa - rotação externa de ombro", dados.rotacao_externa_d, dados.rotacao_externa_e, assimetria_externa),
    ):
        faixa = ref.ADM_ATIVA_OMBRO
        fora_da_faixa = valor_d < faixa.normal_min or valor_d > faixa.normal_max or valor_e < faixa.normal_min or valor_e > faixa.normal_max
        assimetria_alta = assimetria > faixa.assimetria_max
        nivel = NivelRisco.NORMAL if not (fora_da_faixa or assimetria_alta) else NivelRisco.MODERADO
        texto = "Valores dentro do padrão de normalidade." if nivel == NivelRisco.NORMAL else "Resultado alterado — fora da faixa esperada ou assimetria elevada."
        resultados.append(
            ResultadoTeste(
                nome_teste=nome,
                valor_direito=valor_d,
                valor_esquerdo=valor_e,
                assimetria_pct=assimetria,
                nivel_risco=nivel,
                resultado_texto=texto,
                conduta_fisioterapeutica=None if nivel == NivelRisco.NORMAL else "Realizar exercícios de fortalecimento/mobilidade dos rotadores de ombro.",
            )
        )
    return resultados


# ---------------------------------------------------------------------------
# Y Balance Test
# ---------------------------------------------------------------------------
def avaliar_y_balance(dados: DadosYBalance) -> ResultadoTeste:
    escore_mid = round(
        (dados.anterior_mid + dados.posteromedial_mid + dados.posterolateral_mid)
        / (dados.comprimento_mid_cm * 3)
        * 100,
        2,
    )
    escore_mie = round(
        (dados.anterior_mie + dados.posteromedial_mie + dados.posterolateral_mie)
        / (dados.comprimento_mie_cm * 3)
        * 100,
        2,
    )

    diffs = {
        "anterior": abs(dados.anterior_mid - dados.anterior_mie),
        "posteromedial": abs(dados.posteromedial_mid - dados.posteromedial_mie),
        "posterolateral": abs(dados.posterolateral_mid - dados.posterolateral_mie),
    }
    direcao_alterada = [d for d, v in diffs.items() if v > ref.Y_BALANCE_DIFERENCA_DIRECAO_MAX_CM]
    escore_baixo = escore_mid < ref.Y_BALANCE_ESCORE_MIN_PCT or escore_mie < ref.Y_BALANCE_ESCORE_MIN_PCT

    nivel = NivelRisco.NORMAL if not (direcao_alterada or escore_baixo) else NivelRisco.MODERADO
    texto = (
        "Teste dentro dos valores de normalidade."
        if nivel == NivelRisco.NORMAL
        else (
            f"Escore MID: {escore_mid}% / MIE: {escore_mie}%. "
            + (f"Assimetria significativa nas direções: {', '.join(direcao_alterada)}. " if direcao_alterada else "")
            + "Valores alterados indicam risco de lesões em joelhos e tornozelos."
        )
    )
    return ResultadoTeste(
        nome_teste="Y Balance Test",
        valor_direito=escore_mid,
        valor_esquerdo=escore_mie,
        nivel_risco=nivel,
        resultado_texto=texto,
        conduta_fisioterapeutica=(
            None
            if nivel == NivelRisco.NORMAL
            else "Realizar exercícios de equilíbrio dinâmico e fortalecimento dos músculos estabilizadores de tornozelo e quadril."
        ),
    )


# ---------------------------------------------------------------------------
# Força simétrica genérica (dinamômetro isométrico)
# ---------------------------------------------------------------------------
def avaliar_forca_simetrica(dados: DadosForcaSimetrica) -> ResultadoTeste:
    assimetria = calcular_assimetria_pct(dados.valor_d, dados.valor_e)
    lado_fraco = lado_mais_fraco(dados.valor_d, dados.valor_e)
    nivel = _classificar_assimetria_forca(assimetria)

    if nivel == NivelRisco.NORMAL:
        texto = f"Assimetria de {assimetria}% — dentro da normalidade."
        conduta = None
    elif nivel == NivelRisco.MODERADO:
        texto = f"Assimetria de {assimetria}% — risco moderado."
        conduta = f"Fortalecer/melhorar ativação muscular de {dados.nome_grupo_muscular} do lado {lado_fraco}."
    else:
        texto = f"Assimetria de {assimetria}% — risco alto para lesões de sobrecarga em quadril e joelho."
        conduta = f"Fortalecer/melhorar ativação muscular de {dados.nome_grupo_muscular} do lado {lado_fraco} com prioridade."

    return ResultadoTeste(
        nome_teste=f"Força de {dados.nome_grupo_muscular}",
        valor_direito=dados.valor_d,
        valor_esquerdo=dados.valor_e,
        assimetria_pct=assimetria,
        nivel_risco=nivel,
        resultado_texto=texto,
        conduta_fisioterapeutica=conduta,
    )


# ---------------------------------------------------------------------------
# Single Hop Test
# ---------------------------------------------------------------------------
def avaliar_single_hop(dados: DadosSingleHop) -> ResultadoTeste:
    assimetria = calcular_assimetria_pct(dados.media_mid_cm, dados.media_mie_cm)
    lado_fraco = lado_mais_fraco(dados.media_mid_cm, dados.media_mie_cm)
    nivel = NivelRisco.NORMAL if assimetria <= ref.SALTO_ASSIMETRIA_MAX else NivelRisco.MODERADO
    texto = (
        f"Assimetria de {assimetria}% entre os membros — dentro do aceitável."
        if nivel == NivelRisco.NORMAL
        else f"Assimetria de {assimetria}% — acima do aceitável (>{ref.SALTO_ASSIMETRIA_MAX}%), indicando sobrecarga unilateral."
    )
    return ResultadoTeste(
        nome_teste="Single Hop Test",
        valor_direito=dados.media_mid_cm,
        valor_esquerdo=dados.media_mie_cm,
        assimetria_pct=assimetria,
        nivel_risco=nivel,
        resultado_texto=texto,
        conduta_fisioterapeutica=(
            None if nivel == NivelRisco.NORMAL else f"Melhorar potência e estabilidade do membro inferior {lado_fraco}."
        ),
    )


# ---------------------------------------------------------------------------
# Preensão palmar / Flexão e Adução de ombro (membros superiores)
# ---------------------------------------------------------------------------
def avaliar_preensao_palmar(dados: DadosPreensaoPalmar) -> ResultadoTeste:
    assimetria = calcular_assimetria_pct(dados.direita_kgf, dados.esquerda_kgf)
    lado_fraco = lado_mais_fraco(dados.direita_kgf, dados.esquerda_kgf)
    nivel = NivelRisco.NORMAL if assimetria <= ref.MMSS_ASSIMETRIA_MAX_PCT else NivelRisco.MODERADO
    texto = "Assimetria dentro da normalidade." if nivel == NivelRisco.NORMAL else "Assimetria alta."
    return ResultadoTeste(
        nome_teste="Força de preensão palmar",
        valor_direito=dados.direita_kgf,
        valor_esquerdo=dados.esquerda_kgf,
        assimetria_pct=assimetria,
        nivel_risco=nivel,
        resultado_texto=texto,
        conduta_fisioterapeutica=(
            None if nivel == NivelRisco.NORMAL else f"Realizar exercícios de fortalecimento de flexores de punho e dedos da mão {lado_fraco}."
        ),
    )


def avaliar_flexo_aducao_ombro(dados: DadosFlexoAducaoOmbro) -> list[ResultadoTeste]:
    resultados = []
    for nome, d, e in (
        ("Flexão passiva de ombro", dados.flexao_passiva_d, dados.flexao_passiva_e),
        ("Adução horizontal passiva do ombro", dados.aducao_horizontal_d, dados.aducao_horizontal_e),
    ):
        assimetria = round(abs(d - e), 2)
        nivel = NivelRisco.NORMAL if assimetria <= ref.MMSS_ASSIMETRIA_MAX_GRAUS else NivelRisco.MODERADO
        texto = "Valores dentro dos padrões de normalidade." if nivel == NivelRisco.NORMAL else "Assimetria acima do aceitável entre os membros superiores."
        resultados.append(
            ResultadoTeste(
                nome_teste=nome,
                valor_direito=d,
                valor_esquerdo=e,
                assimetria_pct=assimetria,
                nivel_risco=nivel,
                resultado_texto=texto,
                conduta_fisioterapeutica=None if nivel == NivelRisco.NORMAL else "Avaliar necessidade de trabalho de mobilidade/flexibilidade de ombro.",
            )
        )
    return resultados


# ---------------------------------------------------------------------------
# Escala de carga e recuperação
# ---------------------------------------------------------------------------
def avaliar_escala_carga_recuperacao(dados: DadosEscalaCargaRecuperacao) -> ResultadoTeste:
    total = dados.treino + dados.estado_fisico + dados.prontidao_sono + dados.dor
    return ResultadoTeste(
        nome_teste="Escala de carga e recuperação",
        valor_direito=total,
        nivel_risco=NivelRisco.NORMAL if total <= 15 else NivelRisco.MODERADO,
        resultado_texto=f"Escore total: {total} de {ref.ESCALA_CARGA_RECUPERACAO_MAX} possíveis (quanto menor, melhor).",
    )


# ---------------------------------------------------------------------------
# Orquestração: avalia uma AvaliacaoCompletaInput inteira
# ---------------------------------------------------------------------------
def calcular_avaliacao_completa(dados: AvaliacaoCompletaInput) -> AvaliacaoCompletaResultado:
    resultados: list[ResultadoTeste] = []

    if dados.forca_quadriceps_isquiotibiais:
        resultados += avaliar_forca_quadriceps_isquiotibiais(dados.forca_quadriceps_isquiotibiais)
    if dados.core:
        resultados.append(avaliar_core(dados.core))
    if dados.mobilidade_quadril:
        resultados.append(avaliar_mobilidade_quadril(dados.mobilidade_quadril))
    if dados.mobilidade_tornozelo:
        resultados.append(avaliar_mobilidade_tornozelo(dados.mobilidade_tornozelo))
    if dados.adm_passiva_ombro:
        resultados += avaliar_adm_passiva_ombro(dados.adm_passiva_ombro)
    if dados.adm_ativa_ombro:
        resultados += avaliar_adm_ativa_ombro(dados.adm_ativa_ombro)
    if dados.y_balance:
        resultados.append(avaliar_y_balance(dados.y_balance))
    for forca in dados.forcas_simetricas:
        resultados.append(avaliar_forca_simetrica(forca))
    if dados.single_hop:
        resultados.append(avaliar_single_hop(dados.single_hop))
    if dados.preensao_palmar:
        resultados.append(avaliar_preensao_palmar(dados.preensao_palmar))
    if dados.flexo_aducao_ombro:
        resultados += avaliar_flexo_aducao_ombro(dados.flexo_aducao_ombro)
    if dados.escala_carga_recuperacao:
        resultados.append(avaliar_escala_carga_recuperacao(dados.escala_carga_recuperacao))

    # NOTA: o "índice de risco geral (ua)" mostrado no medidor do laudo
    # (ex.: 50,9 ua = risco moderado) não tem fórmula explícita na planilha
    # da fisioterapeuta. Está calculado abaixo como uma média ponderada
    # simples de placeholder (0 = sem risco, 100 = risco máximo) até que a
    # fisioterapeuta confirme/ajuste a metodologia oficial.
    indice_geral, nivel_geral = _calcular_indice_risco_geral_provisorio(resultados)

    return AvaliacaoCompletaResultado(
        paciente_id=dados.paciente_id,
        data_avaliacao=dados.data_avaliacao,
        resultados=resultados,
        indice_risco_geral=indice_geral,
        nivel_risco_geral=nivel_geral,
    )


def _calcular_indice_risco_geral_provisorio(
    resultados: list[ResultadoTeste],
) -> tuple[float | None, NivelRisco | None]:
    """Placeholder: precisa ser validado com a fisioterapeuta.

    Metodologia provisória: cada teste com nível NORMAL conta 0 pontos,
    MODERADO conta 50, ALTO conta 100. O índice geral é a média desses
    pontos, na mesma escala 0–100 usada pelo medidor do laudo (ua).
    """
    if not resultados:
        return None, None

    pesos = {NivelRisco.NORMAL: 0, NivelRisco.MODERADO: 50, NivelRisco.ALTO: 100}
    media = sum(pesos[r.nivel_risco] for r in resultados) / len(resultados)
    media = round(media, 1)

    if media < 34:
        nivel = NivelRisco.NORMAL
    elif media < 67:
        nivel = NivelRisco.MODERADO
    else:
        nivel = NivelRisco.ALTO

    return media, nivel
