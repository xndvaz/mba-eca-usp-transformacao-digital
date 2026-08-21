#!/usr/bin/env python3
from __future__ import annotations

import csv
import html
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "dados" / "comparacao-mediana-veiculos-comparadores.csv"
OUTPUT = ROOT / "figuras-geradas" / "comparacao-escores-lighthouse.svg"

METRICS = [
    ("performance", "Performance"),
    ("accessibility", "Accessibility"),
    ("best_practices", "Best Practices"),
    ("seo", "SEO"),
]
CONTEXTS = [
    ("inicial", "mobile", "Inicial\nmobile"),
    ("inicial", "desktop", "Inicial\ndesktop"),
    ("interna", "mobile", "Interna\nmobile"),
    ("interna", "desktop", "Interna\ndesktop"),
]


def main() -> None:
    with SOURCE.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    values: dict[tuple[str, str, str], tuple[float, float]] = {}
    for row in rows:
        if row["veiculo"] != "Nintendista News":
            continue
        key = (row["tipo_pagina"], row["perfil"], row["metrica"])
        values[key] = (float(row["mediana_veiculo"]), float(row["mediana_concorrentes"]))

    width, height = 1400, 980
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        '<rect width="100%" height="100%" fill="#ffffff"/>',
        '<style>text{font-family:Arial,sans-serif;fill:#202124}.title{font-size:28px;font-weight:700}.panel{font-size:22px;font-weight:700}.axis{font-size:15px}.value{font-size:14px;font-weight:700}.legend{font-size:17px}</style>',
        '<text x="700" y="42" text-anchor="middle" class="title">Nintendista News e mediana dos veículos comparadores</text>',
        '<rect x="470" y="64" width="24" height="16" fill="#1b5eaa"/><text x="504" y="78" class="legend">Nintendista News</text>',
        '<rect x="735" y="64" width="24" height="16" fill="#9aa0a6"/><text x="769" y="78" class="legend">Mediana dos seis veículos comparadores</text>',
    ]
    panel_w, panel_h = 610, 380
    positions = [(70, 120), (720, 120), (70, 560), (720, 560)]
    for (metric, label), (px, py) in zip(METRICS, positions):
        parts.append(f'<text x="{px + panel_w / 2}" y="{py}" text-anchor="middle" class="panel">{html.escape(label)}</text>')
        chart_x, chart_y = px + 60, py + 35
        chart_w, chart_h = panel_w - 80, panel_h - 80
        for tick in range(0, 101, 20):
            y = chart_y + chart_h - chart_h * tick / 100
            parts.append(f'<line x1="{chart_x}" y1="{y:.1f}" x2="{chart_x + chart_w}" y2="{y:.1f}" stroke="#e5e7eb"/>')
            parts.append(f'<text x="{chart_x - 10}" y="{y + 5:.1f}" text-anchor="end" class="axis">{tick}</text>')
        group_w = chart_w / 4
        bar_w = 34
        for idx, (page_type, profile, context_label) in enumerate(CONTEXTS):
            nn, group = values[(page_type, profile, metric)]
            center = chart_x + group_w * (idx + 0.5)
            for value, offset, color in [(nn, -bar_w, "#1b5eaa"), (group, 0, "#9aa0a6")]:
                bar_h = chart_h * value / 100
                x = center + offset
                y = chart_y + chart_h - bar_h
                parts.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="{bar_w}" height="{bar_h:.1f}" fill="{color}"/>')
                label_value = f"{value:.0f}" if abs(value - round(value)) < 0.05 else f"{value:.1f}"
                parts.append(f'<text x="{x + bar_w / 2:.1f}" y="{y - 6:.1f}" text-anchor="middle" class="value">{label_value}</text>')
            first, second = context_label.split("\n")
            parts.append(f'<text x="{center:.1f}" y="{chart_y + chart_h + 22:.1f}" text-anchor="middle" class="axis">{first}</text>')
            parts.append(f'<text x="{center:.1f}" y="{chart_y + chart_h + 40:.1f}" text-anchor="middle" class="axis">{second}</text>')
        parts.append(f'<line x1="{chart_x}" y1="{chart_y + chart_h}" x2="{chart_x + chart_w}" y2="{chart_y + chart_h}" stroke="#5f6368"/>')
    parts.append('</svg>')
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text("\n".join(parts), encoding="utf-8")
    print(OUTPUT)


if __name__ == "__main__":
    main()
