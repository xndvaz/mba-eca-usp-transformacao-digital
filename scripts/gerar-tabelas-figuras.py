#!/usr/bin/env python3
"""Gera tabelas e figuras finais a partir das 140 auditorias Lighthouse."""

from __future__ import annotations

import csv
from collections import defaultdict
from pathlib import Path
import statistics

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[1]
FIG_DIR = ROOT / "figuras-geradas"
MANIFEST = ROOT / "protocolo" / "manifesto-de-urls.csv"
SUMMARY = ROOT / "dados" / "resumo-medianas-iqr.csv"
AGENTIC_DETAIL = ROOT / "dados" / "agentic-browsing-detalhado.csv"

SITE_ORDER = [
    "Nintendista News",
    "Coelho News",
    "Universo Nintendo",
    "A Casa do Cogumelo",
    "Nintendo Blast",
    "Project N",
    "Nintendo Boy",
]
SITE_SHORT = {
    "Nintendista News": "Nintendista\nNews",
    "Coelho News": "Coelho\nNews",
    "Universo Nintendo": "Universo\nNintendo",
    "A Casa do Cogumelo": "A Casa do\nCogumelo",
    "Nintendo Blast": "Nintendo\nBlast",
    "Project N": "Project N",
    "Nintendo Boy": "Nintendo\nBoy",
}
CONTEXTS = [
    ("inicial", "mobile", "Inicial - mobile"),
    ("inicial", "desktop", "Inicial - desktop"),
    ("interna", "mobile", "Interna - mobile"),
    ("interna", "desktop", "Interna - desktop"),
]
CAT_METRICS = [
    ("performance", "Performance"),
    ("accessibility", "Accessibility"),
    ("best_practices", "Best Practices"),
    ("seo", "SEO"),
]
TIME_METRICS = [
    ("fcp_ms", "FCP (ms)"),
    ("lcp_ms", "LCP (ms)"),
    ("speed_index_ms", "Speed Index (ms)"),
    ("tbt_ms", "TBT (ms)"),
    ("cls", "CLS"),
]


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as fh:
        return list(csv.DictReader(fh))


def index_summary(rows: list[dict[str, str]]):
    return {
        (row["veiculo"], row["tipo_pagina"], row["perfil"], row["metrica"]): row
        for row in rows
    }


def fmt_value(metric: str, value: float) -> str:
    if metric == "cls":
        return f"{value:.3f}".replace(".", ",")
    return f"{value:.0f}"


def fmt_cell(metric: str, row: dict[str, str]) -> str:
    med = fmt_value(metric, float(row["mediana"]))
    q1 = fmt_value(metric, float(row["q1"]))
    q3 = fmt_value(metric, float(row["q3"]))
    return f"{med} [{q1}-{q3}]"


def quantile(values: list[float], probability: float) -> float:
    ordered = sorted(values)
    if len(ordered) == 1:
        return ordered[0]
    position = (len(ordered) - 1) * probability
    lower = int(position)
    upper = min(lower + 1, len(ordered) - 1)
    fraction = position - lower
    return ordered[lower] + (ordered[upper] - ordered[lower]) * fraction


def index_agentic(rows: list[dict[str, str]]):
    category_runs: dict[tuple[str, str, str], dict[tuple[str, str, str], float]] = defaultdict(dict)
    audit_rows: dict[tuple[str, str, str, str], list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        context = (row["veiculo"], row["tipo_pagina"], row["perfil"])
        run = (row["id"], row["perfil"], row["repeticao"])
        category_runs[context][run] = float(row["categoria_score_fracao"])
        audit_rows[(*context, row["auditoria"])].append(row)
    return category_runs, audit_rows


def format_fraction(values: list[float]) -> str:
    med = statistics.median(values)
    q1 = quantile(values, 0.25)
    q3 = quantile(values, 0.75)
    return f"{med:.2f} [{q1:.2f}-{q3:.2f}]".replace(".", ",")


def audit_total_status(rows: list[dict[str, str]]) -> str:
    applicable = [row for row in rows if row["modo"] != "notApplicable" and row["score"] != ""]
    if not applicable:
        return "N/A"
    passed = sum(float(row["score"]) == 1 for row in applicable)
    return f"{passed}/{len(applicable)}"


def write_markdown_tables(idx, manifest_rows):
    url_lines = [
        "# Tabela 1 - Páginas auditadas na comparação técnica",
        "",
        "| Veículo | Tipo | URL auditada |",
        "|---|---|---|",
    ]
    for row in manifest_rows:
        page = "Inicial" if row["tipo_pagina"] == "inicial" else "Interna"
        url_lines.append(f"| {row['veiculo']} | {page} | {row['url']} |")
    url_lines.extend([
        "",
        "Fonte: elaboração própria com base no manifesto fixado antes da coleta.",
    ])
    (FIG_DIR / "Tabela_1_URLs_Auditadas.md").write_text("\n".join(url_lines) + "\n", encoding="utf-8")

    cat_lines = [
        "# Tabela 2 - Categorias Lighthouse: mediana [Q1-Q3] das cinco repetições",
        "",
        "| Contexto | Veículo | Performance | Accessibility | Best Practices | SEO |",
        "|---|---|---:|---:|---:|---:|",
    ]
    time_lines = [
        "# Tabela 3 - Métricas Lighthouse: mediana [Q1-Q3] das cinco repetições",
        "",
        "| Contexto | Veículo | FCP (ms) | LCP (ms) | Speed Index (ms) | TBT (ms) | CLS |",
        "|---|---|---:|---:|---:|---:|---:|",
    ]
    for page, profile, label in CONTEXTS:
        for site in SITE_ORDER:
            cats = [fmt_cell(metric, idx[(site, page, profile, metric)]) for metric, _ in CAT_METRICS]
            times = [fmt_cell(metric, idx[(site, page, profile, metric)]) for metric, _ in TIME_METRICS]
            cat_lines.append(f"| {label} | {site} | " + " | ".join(cats) + " |")
            time_lines.append(f"| {label} | {site} | " + " | ".join(times) + " |")
    cat_lines.extend(["", "Fonte: elaboração própria a partir dos 140 relatórios JSON do Lighthouse 13.4.1."])
    time_lines.extend(["", "Fonte: elaboração própria a partir dos 140 relatórios JSON do Lighthouse 13.4.1."])
    (FIG_DIR / "Tabela_2_Categorias_Lighthouse.md").write_text("\n".join(cat_lines) + "\n", encoding="utf-8")
    (FIG_DIR / "Tabela_3_Metricas_Lighthouse.md").write_text("\n".join(time_lines) + "\n", encoding="utf-8")


def write_agentic_table(agentic_rows):
    category_runs, audit_rows = index_agentic(agentic_rows)
    lines = [
        "# Tabela 4 - Agentic Browsing: fração mediana [Q1-Q3] e aprovações nas verificações binárias",
        "",
        "| Veículo | Inicial mobile | Inicial desktop | Interna mobile | Interna desktop | Árvore de acessibilidade | llms.txt |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for site in SITE_ORDER:
        fractions = []
        for page, profile, _ in CONTEXTS:
            fractions.append(format_fraction(list(category_runs[(site, page, profile)].values())))
        tree_rows = []
        llms_rows = []
        for page, profile, _ in CONTEXTS:
            tree_rows.extend(audit_rows[(site, page, profile, "agent-accessibility-tree")])
            llms_rows.extend(audit_rows[(site, page, profile, "llms-txt")])
        lines.append(
            f"| {site} | " + " | ".join(fractions) +
            f" | {audit_total_status(tree_rows)} | {audit_total_status(llms_rows)} |"
        )
    lines.extend([
        "",
        "Nota: a fração experimental não corresponde a um escore ponderado de 0 a 100. As colunas finais indicam aprovações sobre execuções aplicáveis; N/A significa não aplicável. As três auditorias WebMCP foram não aplicáveis em todas as execuções.",
        "",
        "Fonte: elaboração própria a partir dos 140 relatórios JSON do Lighthouse 13.4.1.",
    ])
    path = FIG_DIR / "Tabela_4_Agentic_Browsing.md"
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


FONT_REGULAR_CANDIDATES = (
    str(ROOT / "assets" / "fonts" / "DejaVuSans.ttf"),
    "/System/Library/Fonts/Supplemental/Arial.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
)
FONT_BOLD_CANDIDATES = (
    str(ROOT / "assets" / "fonts" / "DejaVuSans-Bold.ttf"),
    "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
)


def font(size: int, bold: bool = False):
    candidates = FONT_BOLD_CANDIDATES if bold else FONT_REGULAR_CANDIDATES
    selected = next((path for path in candidates if Path(path).exists()), None)
    if not selected:
        raise FileNotFoundError("Nenhuma fonte compatível foi localizada.")
    return ImageFont.truetype(selected, size)


def text_center(draw, xy, value, font_obj, fill="#202124"):
    box = draw.textbbox((0, 0), value, font=font_obj)
    draw.text((xy[0] - (box[2] - box[0]) / 2, xy[1] - (box[3] - box[1]) / 2), value, font=font_obj, fill=fill)


def chart_panel(draw, bounds, title, series, y_max, y_label, colors):
    x0, y0, x1, y1 = bounds
    text_center(draw, ((x0 + x1) / 2, y0 + 30), title, font(38, True))
    left, top, right, bottom = x0 + 165, y0 + 100, x1 - 30, y1 - 165
    for i in range(6):
        value = y_max * i / 5
        yy = bottom - (bottom - top) * i / 5
        draw.line((left, yy, right, yy), fill="#dddddd", width=1)
        if y_max <= 0.1:
            label = f"{value:.3f}"
        elif y_max <= 1:
            label = f"{value:.2f}"
        else:
            label = f"{value:.0f}"
        draw.text((left - 128, yy - 21), label, font=font(36), fill="#444444")
    draw.line((left, top, left, bottom), fill="#777777", width=2)
    draw.line((left, bottom, right, bottom), fill="#777777", width=2)
    n_sites = len(SITE_ORDER)
    group_w = (right - left) / n_sites
    bar_w = min(27, group_w / (len(series) + 0.8))
    for site_i, site in enumerate(SITE_ORDER):
        center = left + group_w * (site_i + 0.5)
        for series_i, (_, values) in enumerate(series):
            value = values[site_i]
            height = 0 if y_max == 0 else (bottom - top) * min(value, y_max) / y_max
            bx0 = center + (series_i - (len(series) - 1) / 2) * bar_w - bar_w * 0.43
            draw.rectangle((bx0, bottom - height, bx0 + bar_w * 0.86, bottom), fill=colors[series_i])
        short = SITE_SHORT[site]
        label_font = font(28)
        lines = short.split("\n")
        for line_i, line in enumerate(lines[:2]):
            box = draw.textbbox((0, 0), line, font=label_font)
            draw.text((center - (box[2] - box[0]) / 2, bottom + 18 + line_i * 32), line, font=label_font, fill="#333333")
    draw.text((x0 + 8, top - 58), y_label, font=font(36), fill="#444444")


def plot_categories(idx):
    image = Image.new("RGB", (2640, 1640), "white")
    draw = ImageDraw.Draw(image)
    colors = ["#3569b7", "#2b9b7b", "#e19634", "#8c5bb8"]
    text_center(draw, (1320, 46), "Categorias do Google Lighthouse por contexto", font(48, True))
    legend_x = 500
    for i, ((_, label), color) in enumerate(zip(CAT_METRICS, colors)):
        x = legend_x + i * 430
        draw.rectangle((x, 88, x + 40, 118), fill=color)
        draw.text((x + 52, 80), label, font=font(36), fill="#333333")
    panels = [(20, 130, 1310, 855), (1330, 130, 2620, 855), (20, 875, 1310, 1615), (1330, 875, 2620, 1615)]
    for bounds, (page, profile, label) in zip(panels, CONTEXTS):
        series = [(m_label, [float(idx[(site, page, profile, metric)]["mediana"]) for site in SITE_ORDER]) for metric, m_label in CAT_METRICS]
        chart_panel(draw, bounds, label, series, 100, "Escore (0-100)", colors)
    image.save(FIG_DIR / "Figura_2_Categorias_Lighthouse.png", dpi=(240, 240))


def plot_loading_metrics(idx):
    image = Image.new("RGB", (2640, 1640), "white")
    draw = ImageDraw.Draw(image)
    metrics = [("fcp_ms", "FCP"), ("lcp_ms", "LCP"), ("speed_index_ms", "Speed Index")]
    colors = ["#3569b7", "#e19634", "#8c5bb8"]
    text_center(draw, (1320, 46), "FCP, LCP e Speed Index por contexto", font(48, True))
    legend_x = 720
    for i, ((_, label), color) in enumerate(zip(metrics, colors)):
        x = legend_x + i * 430
        draw.rectangle((x, 88, x + 40, 118), fill=color)
        draw.text((x + 52, 80), label, font=font(36), fill="#333333")
    panels = [(20, 130, 1310, 855), (1330, 130, 2620, 855), (20, 875, 1310, 1615), (1330, 875, 2620, 1615)]
    for bounds, (page, profile, label) in zip(panels, CONTEXTS):
        series = [(m_label, [float(idx[(site, page, profile, metric)]["mediana"]) / 1000 for site in SITE_ORDER]) for metric, m_label in metrics]
        y_max = max(max(vals) for _, vals in series) * 1.08
        chart_panel(draw, bounds, label, series, y_max, "Tempo (s)", colors)
    image.save(FIG_DIR / "Figura_3_FCP_LCP_Speed_Index.png", dpi=(240, 240))


def plot_single_metric(idx, metric, metric_label, color, output):
    image = Image.new("RGB", (2640, 1640), "white")
    draw = ImageDraw.Draw(image)
    title = "Tempo total de bloqueio por contexto" if metric == "tbt_ms" else "Estabilidade visual por contexto"
    text_center(draw, (1320, 48), title, font(48, True))
    panels = [(20, 100, 1310, 855), (1330, 100, 2620, 855), (20, 875, 1310, 1625), (1330, 875, 2620, 1625)]
    for bounds, (page, profile, label) in zip(panels, CONTEXTS):
        values = [float(idx[(site, page, profile, metric)]["mediana"]) for site in SITE_ORDER]
        y_max = max(values) * 1.08 if max(values) > 0 else 1
        chart_panel(draw, bounds, label, [(metric_label, values)], y_max, metric_label, [color])
    image.save(FIG_DIR / output, dpi=(240, 240))


def plot_tbt_cls(idx):
    plot_single_metric(idx, "tbt_ms", "TBT (ms)", "#d65d5d", "Figura_4A_TBT.png")
    plot_single_metric(idx, "cls", "CLS", "#2b9b7b", "Figura_4B_CLS.png")


def heat_color(value: float) -> str:
    value = max(0.0, min(1.0, value))
    if value < 0.5:
        ratio = value / 0.5
        start = (220, 92, 92)
        end = (238, 188, 79)
    else:
        ratio = (value - 0.5) / 0.5
        start = (238, 188, 79)
        end = (59, 159, 117)
    rgb = tuple(round(start[i] + (end[i] - start[i]) * ratio) for i in range(3))
    return "#%02x%02x%02x" % rgb


def plot_agentic(agentic_rows):
    category_runs, audit_rows = index_agentic(agentic_rows)
    image = Image.new("RGB", (2600, 1500), "white")
    draw = ImageDraw.Draw(image)
    text_center(draw, (1300, 60), "Agentic Browsing: fração mediana por contexto", font(50, True))
    draw.text((120, 118), "A fração é experimental e não equivale a um escore ponderado de 0 a 100.", font=font(34), fill="#444444")

    left = 520
    top = 280
    row_h = 145
    col_w = 430
    for col_i, (_, _, label) in enumerate(CONTEXTS):
        x0 = left + col_i * col_w
        draw.rectangle((x0, top - 95, x0 + col_w - 12, top - 8), fill="#d9e4f2", outline="#6f7f91", width=2)
        text_center(draw, (x0 + (col_w - 12) / 2, top - 52), label, font(33, True))

    for row_i, site in enumerate(SITE_ORDER):
        y0 = top + row_i * row_h
        site_label = SITE_SHORT[site]
        label_y = y0 + (22 if "\n" in site_label else 46)
        draw.multiline_text((80, label_y), site_label, font=font(36, row_i == 0), fill="#202124", spacing=2)
        for col_i, (page, profile, _) in enumerate(CONTEXTS):
            values = list(category_runs[(site, page, profile)].values())
            value = statistics.median(values)
            x0 = left + col_i * col_w
            draw.rectangle((x0, y0, x0 + col_w - 12, y0 + row_h - 12), fill=heat_color(value), outline="#ffffff", width=3)
            text_center(draw, (x0 + (col_w - 12) / 2, y0 + 48), f"{value:.2f}".replace(".", ","), font(44, True), fill="#111111")
            tree = audit_total_status(audit_rows[(site, page, profile, "agent-accessibility-tree")])
            llms = audit_total_status(audit_rows[(site, page, profile, "llms-txt")])
            text_center(draw, (x0 + (col_w - 12) / 2, y0 + 102), f"Árvore {tree} | llms.txt {llms}", font(25), fill="#222222")

    draw.text((80, 1320), "N/A = auditoria não aplicável. As três verificações WebMCP foram N/A em todas as execuções.", font=font(31), fill="#444444")
    image.save(FIG_DIR / "Figura_5_Agentic_Browsing.png", dpi=(240, 240))


def parse_markdown_table(path: Path):
    lines = path.read_text(encoding="utf-8").splitlines()
    table_lines = [line for line in lines if line.startswith("|")]
    header = [cell.strip() for cell in table_lines[0].strip("|").split("|")]
    rows = [[cell.strip() for cell in line.strip("|").split("|")] for line in table_lines[2:]]
    return header, rows


def wrap_cell(value: str, width_px: int, font_obj):
    def split_token(token: str) -> list[str]:
        pieces: list[str] = []
        current = ""
        for character in token:
            candidate = current + character
            if current and font_obj.getlength(candidate) > width_px:
                pieces.append(current)
                current = character
            else:
                current = candidate
        if current:
            pieces.append(current)
        return pieces or [""]

    lines: list[str] = []
    for paragraph in value.split("\n"):
        current = ""
        for word in paragraph.split():
            candidate = word if not current else f"{current} {word}"
            if font_obj.getlength(candidate) <= width_px:
                current = candidate
                continue
            if current:
                lines.append(current)
                current = ""
            if font_obj.getlength(word) <= width_px:
                current = word
                continue
            if word.startswith(("http://", "https://")):
                pieces = split_token(word)
                lines.extend(pieces[:-1])
                current = pieces[-1]
            else:
                current = word
        lines.append(current)
    return lines or [""]


def assert_tokens_fit(values: list[list[str]], col_widths: list[int], font_obj) -> None:
    for row in values:
        for index, value in enumerate(row):
            for paragraph in value.split("\n"):
                for word in paragraph.split():
                    if word.startswith(("http://", "https://")):
                        continue
                    if font_obj.getlength(word) > col_widths[index] - 18:
                        raise ValueError(f"Conteúdo não cabe sem fragmentação: {word}")


def render_table(
    path: Path,
    output: Path,
    rows_slice: slice,
    widths: list[float],
    font_size: int = 27,
    header_font_size: int | None = None,
    compact: bool = False,
):
    header, all_rows = parse_markdown_table(path)
    rows = all_rows[rows_slice]
    if compact:
        header_map = {
            "Contexto": "Perfil",
            "Performance": "Performance",
            "Accessibility": "Accessibility",
            "Best Practices": "Best Practices",
            "Speed Index (ms)": "Speed Index (ms)",
        }
        header = [header_map.get(value, value) for value in header]
        compact_rows = []
        for row in rows:
            page, profile = row[0].split(" - ")
            row = row[:]
            row[0] = profile.capitalize()
            row[1] = SITE_SHORT.get(row[1], row[1])
            compact_rows.append(row)
        rows = compact_rows
    canvas_w = 1900
    left = 20
    usable_w = canvas_w - 2 * left
    col_widths = [int(usable_w * w / sum(widths)) for w in widths]
    col_widths[-1] += usable_w - sum(col_widths)
    f = font(font_size)
    fb = font(header_font_size or font_size, True)
    assert_tokens_fit(rows, col_widths, f)
    assert_tokens_fit([header], col_widths, fb)
    prepared = []
    for row in rows:
        wrapped = [wrap_cell(value, col_widths[i] - 18, f) for i, value in enumerate(row)]
        if compact:
            row_h = max(58, 8 + max(len(lines) for lines in wrapped) * f.size)
        else:
            row_h = max(70, 18 + max(len(lines) for lines in wrapped) * (f.size + 7))
        prepared.append((wrapped, row_h))
    header_lines = [wrap_cell(value, col_widths[i] - 18, fb) for i, value in enumerate(header)]
    if compact:
        header_h = max(60, 8 + max(len(lines) for lines in header_lines) * fb.size)
    else:
        header_h = max(72, 18 + max(len(lines) for lines in header_lines) * (fb.size + 7))
    canvas_h = header_h + sum(h for _, h in prepared) + 4
    image = Image.new("RGB", (canvas_w, canvas_h), "white")
    draw = ImageDraw.Draw(image)
    draw.rectangle((left, 0, left + usable_w, header_h), fill="#d9e4f2", outline="#6f7f91", width=2)
    x = left
    for i, value in enumerate(header):
        draw.rectangle((x, 0, x + col_widths[i], header_h), outline="#6f7f91", width=2)
        lines = header_lines[i]
        text_y = 4 if compact else 9
        for line in lines:
            draw.text((x + 8, text_y), line, font=fb, fill="#1f2933")
            text_y += fb.size if compact else fb.size + 4
        x += col_widths[i]
    y = header_h
    for row_i, (wrapped, row_h) in enumerate(prepared):
        fill = "#f7f9fb" if row_i % 2 else "white"
        x = left
        for col_i, lines in enumerate(wrapped):
            draw.rectangle((x, y, x + col_widths[col_i], y + row_h), fill=fill, outline="#9aa5b1", width=1)
            text_y = y + (4 if compact else 8)
            for line in lines:
                draw.text((x + 8, text_y), line, font=f, fill="#202124")
                text_y += f.size if compact else f.size + 5
            x += col_widths[col_i]
        y += row_h
    image.save(output, dpi=(300, 300))


def render_tables():
    table_1 = FIG_DIR / "Tabela_1_URLs_Auditadas.md"
    table_2 = FIG_DIR / "Tabela_2_Categorias_Lighthouse.md"
    table_3 = FIG_DIR / "Tabela_3_Metricas_Lighthouse.md"
    table_4 = FIG_DIR / "Tabela_4_Agentic_Browsing.md"
    render_table(table_1, FIG_DIR / "Tabela_1_URLs_Auditadas.png", slice(None), [1.15, 0.55, 4.3], font_size=38, header_font_size=42)
    render_table(table_2, FIG_DIR / "Tabela_2A_Categorias_Iniciais.png", slice(0, 14), [0.55, 0.76, 0.78, 0.92, 0.98, 0.7], font_size=42, header_font_size=36, compact=True)
    render_table(table_2, FIG_DIR / "Tabela_2B_Categorias_Internas.png", slice(14, 28), [0.55, 0.76, 0.78, 0.92, 0.98, 0.7], font_size=42, header_font_size=36, compact=True)
    render_table(table_3, FIG_DIR / "Tabela_3A_Metricas_Iniciais.png", slice(0, 14), [0.68, 0.78, 0.82, 0.82, 1.0, 0.7, 0.76], font_size=31, header_font_size=36, compact=True)
    render_table(table_3, FIG_DIR / "Tabela_3B_Metricas_Internas.png", slice(14, 28), [0.68, 0.78, 0.82, 0.82, 1.0, 0.7, 0.76], font_size=31, header_font_size=36, compact=True)
    render_table(table_4, FIG_DIR / "Tabela_4_Agentic_Browsing.png", slice(None), [0.92, 0.9, 0.9, 0.9, 0.9, 0.75, 0.65], font_size=30, header_font_size=25)


def main():
    FIG_DIR.mkdir(parents=True, exist_ok=True)
    rows = read_csv(SUMMARY)
    manifest = read_csv(MANIFEST)
    agentic_rows = read_csv(AGENTIC_DETAIL)
    idx = index_summary(rows)
    write_markdown_tables(idx, manifest)
    write_agentic_table(agentic_rows)
    plot_categories(idx)
    plot_loading_metrics(idx)
    plot_tbt_cls(idx)
    plot_agentic(agentic_rows)
    render_tables()


if __name__ == "__main__":
    main()
