#!/usr/bin/env python3
from __future__ import annotations

import csv
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SUMMARY = ROOT / "dados" / "resumo-medianas-iqr.csv"
COMPARISON = ROOT / "dados" / "comparacao-mediana-veiculos-comparadores.csv"
OUTPUT = ROOT / "dados" / "resumo-para-redacao.md"
TABLE_OUTPUT = ROOT / "dados" / "tabela-performance.csv"

LABELS = {
    "performance": "Performance",
    "accessibility": "Accessibility",
    "best_practices": "Best Practices",
    "seo": "SEO",
    "fcp_ms": "FCP (ms)",
    "lcp_ms": "LCP (ms)",
    "speed_index_ms": "Speed Index (ms)",
    "tbt_ms": "TBT (ms)",
    "cls": "CLS",
}
SCORES = ["performance", "accessibility", "best_practices", "seo"]
CONTEXTS = [
    ("inicial", "mobile"),
    ("inicial", "desktop"),
    ("interna", "mobile"),
    ("interna", "desktop"),
]


def fmt(value: float, metric: str) -> str:
    if metric == "cls":
        return f"{value:.3f}"
    if metric.endswith("_ms"):
        return f"{value:.0f}"
    return f"{value:.0f}" if abs(value - round(value)) < 0.05 else f"{value:.1f}"


def main() -> None:
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    with SUMMARY.open(encoding="utf-8", newline="") as handle:
        summaries = list(csv.DictReader(handle))
    with COMPARISON.open(encoding="utf-8", newline="") as handle:
        comparisons = list(csv.DictReader(handle))

    nn_summary = {
        (row["tipo_pagina"], row["perfil"], row["metrica"]): row
        for row in summaries
        if row["veiculo"] == "Nintendista News"
    }
    nn_comp = {
        (row["tipo_pagina"], row["perfil"], row["metrica"]): row
        for row in comparisons
        if row["veiculo"] == "Nintendista News"
    }

    performance_by_vehicle = {
        (row["veiculo"], row["tipo_pagina"], row["perfil"]): row
        for row in summaries
        if row["metrica"] == "performance"
    }
    vehicles = [
        "Nintendista News",
        "Coelho News",
        "Universo Nintendo",
        "A Casa do Cogumelo",
        "Nintendo Blast",
        "Project N",
        "Nintendo Boy",
    ]
    table_rows = []
    for vehicle in vehicles:
        table_row = {"Veículo": vehicle}
        for page_type, profile, _ in [
            ("inicial", "mobile", "Inicial mobile"),
            ("inicial", "desktop", "Inicial desktop"),
            ("interna", "mobile", "Interna mobile"),
            ("interna", "desktop", "Interna desktop"),
        ]:
            row = performance_by_vehicle[(vehicle, page_type, profile)]
            table_row[_] = f"{float(row['mediana']):.0f} [{float(row['q1']):.0f}–{float(row['q3']):.0f}]"
        table_rows.append(table_row)
    with TABLE_OUTPUT.open("w", encoding="utf-8", newline="") as handle:
        columns = ["Veículo", "Inicial mobile", "Inicial desktop", "Interna mobile", "Interna desktop"]
        writer = csv.DictWriter(handle, fieldnames=columns)
        writer.writeheader()
        writer.writerows(table_rows)

    lines = [
        "# Resumo factual para redação",
        "",
        "Valores calculados automaticamente a partir dos relatórios JSON. Escores em escala de 0 a 100. O intervalo entre colchetes corresponde a Q1–Q3 das cinco repetições.",
        "",
        "| Página | Perfil | Métrica | Nintendista News, mediana [Q1–Q3] | Mediana das medianas dos veículos comparadores | Diferença |",
        "|---|---|---|---:|---:|---:|",
    ]
    for page_type, profile in CONTEXTS:
        for metric in SCORES:
            summary = nn_summary[(page_type, profile, metric)]
            comp = nn_comp[(page_type, profile, metric)]
            value = float(summary["mediana"])
            q1 = float(summary["q1"])
            q3 = float(summary["q3"])
            group = float(comp["mediana_concorrentes"])
            diff = float(comp["diferenca"])
            lines.append(
                f"| {page_type.capitalize()} | {profile.capitalize()} | {LABELS[metric]} | "
                f"{fmt(value, metric)} [{fmt(q1, metric)}–{fmt(q3, metric)}] | {fmt(group, metric)} | {diff:+.1f} |"
            )

    lines.extend(["", "## Métricas temporais e estabilidade do Nintendista News", ""])
    for page_type, profile in CONTEXTS:
        lines.append(f"### {page_type.capitalize()} — {profile}")
        lines.append("")
        for metric in ["fcp_ms", "lcp_ms", "speed_index_ms", "tbt_ms", "cls"]:
            summary = nn_summary[(page_type, profile, metric)]
            comp = nn_comp[(page_type, profile, metric)]
            lines.append(
                f"- {LABELS[metric]}: {fmt(float(summary['mediana']), metric)} "
                f"[Q1 {fmt(float(summary['q1']), metric)}; Q3 {fmt(float(summary['q3']), metric)}]; "
                f"mediana dos veículos comparadores {fmt(float(comp['mediana_concorrentes']), metric)}; "
                f"diferença {float(comp['diferenca']):+.3f}."
            )
        lines.append("")

    OUTPUT.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
    print(OUTPUT)
    print(TABLE_OUTPUT)


if __name__ == "__main__":
    main()
