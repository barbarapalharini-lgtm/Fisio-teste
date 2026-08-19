from __future__ import annotations

from io import BytesIO
from pathlib import Path
from typing import Any, BinaryIO, Dict, List, Union

import re
from reportlab.graphics.shapes import Circle, Drawing, Line, PolyLine, Rect, String
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.lib.utils import ImageReader
from reportlab.platypus import Image, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

LOGO_DIR = Path(__file__).parent / "assets"
LOGO_IMAGE_PATTERNS = ["functional-logo.*", "logo.*"]
LOGO_IMAGE_EXTENSIONS = {"png", "jpg", "jpeg", "gif"}


def _find_logo_path() -> Union[Path, None]:
    if not LOGO_DIR.exists():
        return None
    for pattern in LOGO_IMAGE_PATTERNS:
        for path in LOGO_DIR.glob(pattern):
            if path.suffix.lower().lstrip(".") in LOGO_IMAGE_EXTENSIONS:
                return path
    return None


def _format_valores(resultado: Dict[str, Any]) -> str:
    nome = str(resultado.get("nome_teste", "")).lower()

    # ADM passiva de ombro: resultado_texto contains both external and internal rotations
    if "adm passiva" in nome or "gird" in nome:
        texto = resultado.get("resultado_texto", "")
        # procura por 'Rotação externa X°' e 'rotação interna Y°'
        re_ext = re.search(r"rot[aã]o externa\s*:?\s*([0-9]+(?:\.[0-9]+)?)°", texto, flags=re.IGNORECASE)
        re_int = re.search(r"rot[aã]o interna\s*:?\s*([0-9]+(?:\.[0-9]+)?)°", texto, flags=re.IGNORECASE)
        parts = []
        if re_ext:
            parts.append(f"Ext: {re_ext.group(1)}°")
        if re_int:
            parts.append(f"Int: {re_int.group(1)}°")
        if resultado.get("assimetria_pct") is not None:
            parts.append(f"Assimetria: {resultado['assimetria_pct']}%")
        return " / ".join(parts)

    # Y Balance: use MID / MIE labels instead of D/E
    if nome.strip().startswith("y balance"):
        partes = []
        if resultado.get("valor_direito") is not None:
            partes.append(f"MID: {resultado['valor_direito']}%")
        if resultado.get("valor_esquerdo") is not None:
            partes.append(f"MIE: {resultado['valor_esquerdo']}%")
        return " / ".join(partes)

    # Escala de carga e recuperação: show total without D/E
    if "escala de carga" in nome:
        if resultado.get("valor_direito") is not None:
            return f"Total: {resultado['valor_direito']}"
        return ""

    partes: List[str] = []
    if resultado.get("valor_direito") is not None:
        partes.append(f"D: {resultado['valor_direito']}")
    if resultado.get("valor_esquerdo") is not None:
        partes.append(f"E: {resultado['valor_esquerdo']}")
    if resultado.get("assimetria_pct") is not None:
        partes.append(f"Assimetria: {resultado['assimetria_pct']}%")
    return " / ".join(partes)


def _shorten_label(text: str, max_len: int = 40) -> str:
    return text if len(text) <= max_len else text[: max_len - 3].rstrip() + "..."


def _chart_label_lines(text: str, max_len: int = 18) -> List[str]:
    text = _shorten_label(text, max_len * 2)
    if " - " in text:
        first, second = text.split(" - ", 1)
        return [_shorten_label(first, max_len), _shorten_label(second, max_len)]

    words = text.split()
    first_line = ""
    second_line = ""
    for word in words:
        candidate = f"{first_line} {word}".strip()
        if len(candidate) <= max_len or not first_line:
            first_line = candidate
        else:
            second_line = f"{second_line} {word}".strip()
    return [first_line, second_line] if second_line else [first_line]


BRAND_DARK = colors.HexColor("#0f172a")
BRAND_PRIMARY = colors.HexColor("#2076f4")
BRAND_HEADER = colors.HexColor("#1b3a74")
BRAND_ACCENT = colors.HexColor("#00b7c7")
BRAND_LIGHT = colors.HexColor("#eff6ff")


def _criar_logo_funcionale(width: float = 14 * cm, height: float = 2.5 * cm) -> Drawing:
    drawing = Drawing(width, height)
    accent_width = 1.2 * cm
    drawing.add(Rect(0, 0, accent_width, height, fillColor=BRAND_ACCENT, strokeColor=None))
    drawing.add(Circle(accent_width * 0.5, height * 0.5, 6, fillColor=colors.white, strokeColor=None))
    drawing.add(String(accent_width + 10, height - 10, "functional.e", fontName="Helvetica-Bold", fontSize=22, fillColor=BRAND_DARK))
    drawing.add(String(accent_width + 10, height - 26, "Laudo de Avaliação", fontName="Helvetica", fontSize=10, fillColor=colors.HexColor("#475569")))
    return drawing


def _get_logo_flowable(width: float = 9.5 * cm, height: float = 2.4 * cm):
    logo_path = _find_logo_path()
    if logo_path is not None:
        image = ImageReader(str(logo_path))
        orig_width, orig_height = image.getSize()
        aspect = orig_height / orig_width
        if width * aspect <= height:
            return Image(str(logo_path), width=width, height=width * aspect)
        return Image(str(logo_path), width=height / aspect, height=height)
    return _criar_logo_funcionale(width=width, height=height)


def _criar_grafico_individual_por_resultado(resultado: Dict[str, Any], width: float = 7.5 * cm, height: float = 5 * cm) -> Drawing:
    drawing = Drawing(width, height)
    padding_left = 1.2 * cm
    padding_right = 0.8 * cm
    padding_top = 1.4 * cm
    padding_bottom = 1.4 * cm
    plot_width = width - padding_left - padding_right
    plot_height = height - padding_top - padding_bottom
    color_map = {
        "normal": colors.HexColor("#5cb85c"),
        "moderado": colors.HexColor("#f0ad4e"),
        "alto": colors.HexColor("#d9534f"),
    }

    valores = []
    labels = []
    if resultado.get("valor_direito") is not None:
        valores.append(float(resultado["valor_direito"]))
        labels.append("D")
    if resultado.get("valor_esquerdo") is not None:
        valores.append(float(resultado["valor_esquerdo"]))
        labels.append("E")
    if resultado.get("assimetria_pct") is not None and not valores:
        valores.append(float(resultado["assimetria_pct"]))
        labels.append("Assim.")

    max_valor = max(valores + [100])
    eixo_y = padding_bottom
    eixo_x = padding_left

    # Título do gráfico
    drawing.add(String(padding_left, height - 10, _shorten_label(str(resultado.get("nome_teste", "")), 24), fontName="Helvetica-Bold", fontSize=8, fillColor=colors.black))
    drawing.add(
        String(
            width - padding_right,
            height - 10,
            str(resultado.get("nivel_risco", "")).capitalize(),
            fontName="Helvetica",
            fontSize=7,
            fillColor=color_map.get(str(resultado.get("nivel_risco", "normal")), colors.black),
            textAnchor="end",
        )
    )

    # Eixos
    drawing.add(Line(eixo_x, eixo_y, eixo_x + plot_width, eixo_y, strokeColor=colors.HexColor("#4b5563"), strokeWidth=1))
    drawing.add(Line(eixo_x, eixo_y, eixo_x, eixo_y + plot_height, strokeColor=colors.HexColor("#4b5563"), strokeWidth=1))

    # Grade horizontal
    for i in range(0, 6):
        y_pos = eixo_y + (plot_height / 5) * i
        drawing.add(Line(eixo_x, y_pos, eixo_x + plot_width, y_pos, strokeColor=colors.HexColor("#e2e8f0"), strokeWidth=0.4))
        drawing.add(
            String(
                eixo_x - 14,
                y_pos - 3,
                f"{int(max_valor * i / 5)}",
                fontName="Helvetica",
                fontSize=6,
                fillColor=colors.HexColor("#475569"),
            )
        )

    points = []
    for idx, valor in enumerate(valores):
        x = eixo_x + (plot_width * idx / max(1, len(valores) - 1)) if len(valores) > 1 else eixo_x + plot_width / 2
        y = eixo_y + (valor / max_valor) * plot_height
        points.extend([x, y])
        drawing.add(Circle(x, y, 3, fillColor=colors.HexColor("#2563eb"), strokeColor=None))
        drawing.add(
            String(
                x,
                eixo_y - 14,
                labels[idx],
                fontName="Helvetica",
                fontSize=7,
                fillColor=colors.black,
                textAnchor="middle",
            )
        )
        drawing.add(
            String(
                x,
                y + 6,
                f"{int(valor)}",
                fontName="Helvetica",
                fontSize=6,
                fillColor=colors.HexColor("#0f172a"),
                textAnchor="middle",
            )
        )

    if len(points) > 2:
        drawing.add(PolyLine(points, strokeColor=BRAND_PRIMARY, strokeWidth=1.5, fillColor=None))

    drawing.add(String(eixo_x + plot_width + 6, eixo_y - 4, "%", fontName="Helvetica", fontSize=7, fillColor=BRAND_DARK))
    return drawing


GROUP_KEYWORDS = {
    "Mobilidade": [
        "mobilidade",
        "lunge",
        "quadril",
        "tornozelo",
        "rotação",
    ],
    "Força": ["força", "1rm", "quadriceps", "isquiotibiais", "prensa"],
    "Core": ["core", "prancha", "extensores"],
    "Salto / Potência": ["single hop", "salto", "hop"],
    "Equilíbrio": ["y balance", "equilíbrio", "y balance test"],
}


def _assign_group(nome: str) -> str:
    low = nome.lower()
    for group, keys in GROUP_KEYWORDS.items():
        for k in keys:
            if k in low:
                return group
    return "Outros"


def _criar_grafico_grupo_vertical(group_name: str, resultados: List[Dict[str, Any]], width: float = 16 * cm, height: float = 9 * cm) -> Drawing:
    drawing = Drawing(width, height)
    drawing.hAlign = "CENTER"
    padding_left = 1.0 * cm
    padding_right = 1.0 * cm
    padding_bottom = 3.0 * cm
    padding_top = 1.0 * cm
    plot_width = width - padding_left - padding_right
    plot_height = height - padding_top - padding_bottom

    drawing.add(String(padding_left, height - 10, group_name, fontName="Helvetica-Bold", fontSize=12, fillColor=BRAND_DARK))

    tests = []
    for res in resultados:
        nome = str(res.get("nome_teste", ""))
        d_val = res.get("valor_direito")
        e_val = res.get("valor_esquerdo")
        if d_val is not None or e_val is not None:
            tests.append({"nome": nome, "d": float(d_val) if d_val is not None else None, "e": float(e_val) if e_val is not None else None})
        elif res.get("assimetria_pct") is not None:
            tests.append({"nome": nome, "a": float(res.get("assimetria_pct"))})

    if not tests:
        drawing.add(String(padding_left, height / 2, "Sem dados neste grupo.", fontName="Helvetica", fontSize=9, fillColor=BRAND_DARK))
        return drawing

    max_val = max([v for test in tests for v in [test.get("d"), test.get("e"), test.get("a")] if v is not None] + [100])
    round_base = 10
    max_val = max(100, int((max_val + round_base - 1) // round_base * round_base))

    bar_gap = 0.25 * cm
    cluster_gap = 0.8 * cm
    bar_width = 0.55 * cm
    cluster_width = bar_width * 2 + bar_gap
    required_width = len(tests) * cluster_width + (len(tests) + 1) * cluster_gap
    if required_width > plot_width:
        cluster_width = max(0.0, (plot_width - (len(tests) + 1) * cluster_gap) / len(tests))
        bar_width = max(0.3 * cm, (cluster_width - bar_gap) / 2)

    start_x = padding_left + max(0, (plot_width - (len(tests) * cluster_width + (len(tests) + 1) * cluster_gap)) / 2)

    # grid lines and Y labels
    steps = 5
    for i in range(steps + 1):
        frac = i / steps
        y_pos = padding_bottom + frac * plot_height
        drawing.add(Line(padding_left, y_pos, padding_left + plot_width, y_pos, strokeColor=colors.HexColor("#eef3fb"), strokeWidth=0.5))
        drawing.add(String(padding_left - 16, y_pos - 4, f"{int(max_val * frac)}", fontName="Helvetica", fontSize=7, fillColor=colors.HexColor("#6b7280")))

    legend_y = height - 18
    drawing.add(Rect(width - padding_right - 34, legend_y - 5, 8, 8, fillColor=BRAND_PRIMARY, strokeColor=None))
    drawing.add(String(width - padding_right - 24, legend_y, "D", fontName="Helvetica", fontSize=7, fillColor=BRAND_DARK, textAnchor="start"))
    drawing.add(Rect(width - padding_right - 16, legend_y - 5, 8, 8, fillColor=BRAND_ACCENT, strokeColor=None))
    drawing.add(String(width - padding_right - 6, legend_y, "E", fontName="Helvetica", fontSize=7, fillColor=BRAND_DARK, textAnchor="start"))

    x = start_x
    for test in tests:
        cluster_center = x + cluster_width / 2
        d_val = test.get("d")
        e_val = test.get("e")
        a_val = test.get("a")
        if d_val is not None and e_val is not None:
            d_height = (d_val / max_val) * plot_height
            e_height = (e_val / max_val) * plot_height
            drawing.add(Rect(x, padding_bottom, bar_width, d_height, fillColor=BRAND_PRIMARY, strokeColor=None))
            drawing.add(Rect(x + bar_width + bar_gap, padding_bottom, bar_width, e_height, fillColor=BRAND_ACCENT, strokeColor=None))
            drawing.add(String(x + bar_width / 2, padding_bottom + d_height + 6, f"{int(d_val)}", fontName="Helvetica-Bold", fontSize=8, fillColor=BRAND_DARK, textAnchor="middle"))
            drawing.add(String(x + bar_width + bar_gap + bar_width / 2, padding_bottom + e_height + 6, f"{int(e_val)}", fontName="Helvetica-Bold", fontSize=8, fillColor=BRAND_DARK, textAnchor="middle"))
        elif d_val is not None:
            d_height = (d_val / max_val) * plot_height
            bar_x = cluster_center - bar_width / 2
            drawing.add(Rect(bar_x, padding_bottom, bar_width, d_height, fillColor=BRAND_PRIMARY, strokeColor=None))
            drawing.add(String(cluster_center, padding_bottom + d_height + 6, f"{int(d_val)}", fontName="Helvetica-Bold", fontSize=8, fillColor=BRAND_DARK, textAnchor="middle"))
        elif e_val is not None:
            e_height = (e_val / max_val) * plot_height
            bar_x = cluster_center - bar_width / 2
            drawing.add(Rect(bar_x, padding_bottom, bar_width, e_height, fillColor=BRAND_ACCENT, strokeColor=None))
            drawing.add(String(cluster_center, padding_bottom + e_height + 6, f"{int(e_val)}", fontName="Helvetica-Bold", fontSize=8, fillColor=BRAND_DARK, textAnchor="middle"))
        elif a_val is not None:
            a_height = (a_val / max_val) * plot_height
            bar_x = cluster_center - bar_width / 2
            drawing.add(Rect(bar_x, padding_bottom, bar_width, a_height, fillColor=BRAND_PRIMARY, strokeColor=None))
            drawing.add(String(cluster_center, padding_bottom + a_height + 6, f"{int(a_val)}", fontName="Helvetica-Bold", fontSize=8, fillColor=BRAND_DARK, textAnchor="middle"))

        label_lines = _chart_label_lines(test["nome"])
        for line_index, label_line in enumerate(label_lines):
            drawing.add(
                String(
                    cluster_center,
                    padding_bottom - 10 - (line_index * 10),
                    label_line,
                    fontName="Helvetica",
                    fontSize=7,
                    fillColor=BRAND_DARK,
                    textAnchor="middle",
                )
            )
        x += cluster_width + cluster_gap

    return drawing


def _criar_medidor_risco(indice: float, width: float = 10 * cm, height: float = 2.5 * cm) -> Drawing:
    drawing = Drawing(width, height)
    padding = 0.3 * cm
    bar_x = padding
    bar_y = padding
    bar_w = width - padding * 2
    bar_h = height - padding * 2

    # segments: green(0-50), yellow(50-75), red(75-100)
    g1 = Rect(bar_x, bar_y, bar_w * 0.5, bar_h, fillColor=colors.HexColor("#5cb85c"), strokeColor=None)
    g2 = Rect(bar_x + bar_w * 0.5, bar_y, bar_w * 0.25, bar_h, fillColor=colors.HexColor("#f0ad4e"), strokeColor=None)
    g3 = Rect(bar_x + bar_w * 0.75, bar_y, bar_w * 0.25, bar_h, fillColor=colors.HexColor("#d9534f"), strokeColor=None)
    drawing.add(g1)
    drawing.add(g2)
    drawing.add(g3)

    # pointer
    pos = bar_x + max(0, min(1.0, (indice or 0) / 100.0)) * bar_w
    triangle = PolyLine([pos - 6, bar_y + bar_h + 2, pos + 6, bar_y + bar_h + 2, pos, bar_y + bar_h + 12, pos - 6, bar_y + bar_h + 2], strokeColor=None, fillColor=BRAND_DARK)
    drawing.add(triangle)

    # labels and percent
    drawing.add(String(bar_x, bar_y + bar_h + 14, "Medidor de Risco de Lesão", fontName="Helvetica-Bold", fontSize=8, fillColor=BRAND_DARK))
    drawing.add(String(pos, bar_y + bar_h + 16, f"{int(indice or 0)}%", fontName="Helvetica-Bold", fontSize=8, fillColor=BRAND_DARK, textAnchor="middle"))

    # small legend
    drawing.add(String(bar_x, bar_y - 8, "Baixo", fontName="Helvetica", fontSize=6, fillColor=colors.HexColor("#0f172a")))
    drawing.add(String(bar_x + bar_w * 0.45, bar_y - 8, "Moderado", fontName="Helvetica", fontSize=6, fillColor=colors.HexColor("#0f172a")))
    drawing.add(String(bar_x + bar_w * 0.75, bar_y - 8, "Alto", fontName="Helvetica", fontSize=6, fillColor=colors.HexColor("#0f172a")))

    return drawing

def _criar_medidor_gauge(indice: float, width: float = 10 * cm, height: float = 4 * cm) -> Drawing:
    drawing = Drawing(width, height)
    cx = width / 2
    cy = height * 0.72
    radius = min(width * 0.42, height * 0.45)

    # arcs: draw three colored arcs (green, yellow, red)
    start_angle = 200
    total_angle = 140
    a1 = start_angle
    a2 = start_angle + total_angle * 0.5
    a3 = start_angle + total_angle * 0.75
    a4 = start_angle + total_angle

    # helper to draw arc as series of small lines approximating curved arc using many points
    def arc_points(center_x, center_y, r, start_deg, end_deg, steps=60):
        pts = []
        import math

        for i in range(steps + 1):
            ang = math.radians(start_deg + (end_deg - start_deg) * i / steps)
            x = center_x + r * math.cos(ang)
            y = center_y + r * math.sin(ang)
            pts.append((x, y))
        return pts

    # draw colored arcs as thick polylines
    def draw_arc_colored(s_deg, e_deg, color):
        pts = arc_points(cx, cy, radius, s_deg, e_deg, steps=48)
        flat = []
        for (x, y) in pts:
            flat.extend([x, y])
        drawing.add(PolyLine(flat, strokeColor=color, strokeWidth=radius * 0.35, fillColor=None))

    draw_arc_colored(a1, a2, colors.HexColor("#5cb85c"))
    draw_arc_colored(a2, a3, colors.HexColor("#f0ad4e"))
    draw_arc_colored(a3, a4, colors.HexColor("#d9534f"))

    # pointer
    import math

    pct = max(0.0, min(1.0, (indice or 0) / 100.0))
    angle = math.radians(start_angle + total_angle * pct)
    px = cx + (radius * 0.6) * math.cos(angle)
    py = cy + (radius * 0.6) * math.sin(angle)
    # needle line
    drawing.add(Line(cx, cy, px, py, strokeColor=BRAND_DARK, strokeWidth=3))
    # center circle
    drawing.add(Circle(cx, cy, 6, fillColor=BRAND_DARK, strokeColor=None))

    # labels
    drawing.add(String(cx, 8, "Medidor de Risco de Lesão", fontName="Helvetica-Bold", fontSize=8, fillColor=BRAND_DARK, textAnchor="middle"))
    drawing.add(String(cx, height - 24, f"{int((indice or 0))}%", fontName="Helvetica-Bold", fontSize=10, fillColor=BRAND_DARK, textAnchor="middle"))
    # small legend under arcs
    drawing.add(String(cx - radius * 0.7, height - 8, "Baixo", fontName="Helvetica", fontSize=6, fillColor=BRAND_DARK))
    drawing.add(String(cx - 6, height - 8, "Moderado", fontName="Helvetica", fontSize=6, fillColor=BRAND_DARK))
    drawing.add(String(cx + radius * 0.45, height - 8, "Alto", fontName="Helvetica", fontSize=6, fillColor=BRAND_DARK))

    return drawing



def gerar_laudo_pdf(
    destino: Union[Path, str, BinaryIO],
    paciente: Any,
    resultado_json: Dict[str, Any],
) -> None:
    if isinstance(destino, (str, Path)):
        destino = Path(destino)
        destino.parent.mkdir(parents=True, exist_ok=True)
        output_target = str(destino)
    else:
        output_target = destino

    doc = SimpleDocTemplate(
        output_target,
        pagesize=A4,
        leftMargin=2 * cm,
        rightMargin=2 * cm,
        topMargin=2 * cm,
        bottomMargin=2 * cm,
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "Title",
        parent=styles["Heading1"],
        alignment=TA_CENTER,
        fontSize=18,
        leading=22,
        spaceAfter=12,
    )
    subtitle_style = ParagraphStyle(
        "Subtitle",
        parent=styles["Heading2"],
        alignment=TA_CENTER,
        fontSize=12,
        leading=14,
        spaceAfter=10,
    )
    heading_style = ParagraphStyle(
        "Heading",
        parent=styles["Heading2"],
        alignment=TA_LEFT,
        fontSize=12,
        leading=14,
        spaceAfter=8,
    )
    normal_style = ParagraphStyle(
        "Normal",
        parent=styles["BodyText"],
        fontSize=10,
        leading=13,
        alignment=TA_LEFT,
    )

    story: list[Any] = []

    data_avaliacao = resultado_json.get("data_avaliacao", "")
    indice_risco = resultado_json.get("indice_risco_geral")
    nivel_risco = resultado_json.get("nivel_risco_geral")

    header_logo = _get_logo_flowable(width=9.5 * cm, height=2.4 * cm)
    story.append(header_logo)
    story.append(Spacer(1, 16))
    title_style.textColor = BRAND_HEADER
    story.append(Paragraph("Funcional.e Fisioterapia Esportiva", title_style))
    story.append(Paragraph("Relatório de Avaliação de Risco de Lesões", subtitle_style))

    paciente_info = [
        ["Nome:", getattr(paciente, "nome", "")],
        ["Data de avaliação:", data_avaliacao],
        ["Índice de risco geral:", f"{indice_risco} ({nivel_risco})" if indice_risco is not None else "-"],
    ]
    table = Table(paciente_info, colWidths=[5 * cm, 10 * cm])
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
                ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("INNERGRID", (0, 0), (-1, -1), 0.25, colors.grey),
                ("BOX", (0, 0), (-1, -1), 0.25, colors.grey),
            ]
        )
    )
    story.append(table)
    story.append(Spacer(1, 12))

    story.append(Paragraph("Resumo dos testes", heading_style))

    rows = [["Teste", "Valores", "Resultado", "Risco"]]
    for resultado in resultado_json.get("resultados", []):
        rows.append(
            [
                Paragraph(str(resultado.get("nome_teste", "")), normal_style),
                Paragraph(_format_valores(resultado), normal_style),
                Paragraph(str(resultado.get("resultado_texto", "")), normal_style),
                Paragraph(str(resultado.get("nivel_risco", "")), normal_style),
            ]
        )

    table = Table(rows, colWidths=[5.5 * cm, 3.5 * cm, 6 * cm, 2.5 * cm])
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#d9d9d9")),
                ("GRID", (0, 0), (-1, -1), 0.25, colors.grey),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("ALIGN", (3, 1), (3, -1), "CENTER"),
            ]
        )
    )
    story.append(table)
    story.append(Spacer(1, 12))

    resultados = resultado_json.get("resultados", [])
    if resultados:
        story.append(Paragraph("Gráficos por grupo", heading_style))
        story.append(Spacer(1, 6))

        groups: Dict[str, List[Dict[str, Any]]] = {}
        for resultado in resultados:
            nome = str(resultado.get("nome_teste", ""))
            grp = _assign_group(nome)
            groups.setdefault(grp, []).append(resultado)

        ordered_groups = [g for g in GROUP_KEYWORDS.keys() if g in groups]
        if "Outros" in groups:
            ordered_groups.append("Outros")

        # layout charts in full width for readability and larger labels
        for grp in ordered_groups:
            drawing = _criar_grafico_grupo_vertical(grp, groups[grp], width=16.5 * cm, height=9 * cm)
            story.append(drawing)
            story.append(Spacer(1, 12))

    # Insert risk meter and condutas side-by-side to avoid overlap
    indice_risco_val = resultado_json.get("indice_risco_geral", 0)
    gauge = _criar_medidor_gauge(indice_risco_val, width=8 * cm, height=5.8 * cm)

    condutas = [Paragraph("Conduta fisioterapêutica sugerida", heading_style)]
    for resultado in resultado_json.get("resultados", []):
        conduta = resultado.get("conduta_fisioterapeutica")
        if conduta:
            condutas.append(Paragraph(f"• {resultado.get('nome_teste')}: {conduta}", normal_style))
    if len(condutas) == 1:
        condutas = [Paragraph("Nenhuma conduta sugerida específica.", normal_style)]

    story.append(Spacer(1, 12))
    story.append(gauge)
    story.append(Spacer(1, 30))
    story.extend(condutas)
    story.append(Spacer(1, 12))

    doc.build(story)
