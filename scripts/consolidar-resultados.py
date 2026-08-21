#!/usr/bin/env python3
from __future__ import annotations

import csv
import argparse
import hashlib
import json
import statistics
from collections import defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

METRICS = {
    "performance": ("category", "performance"),
    "accessibility": ("category", "accessibility"),
    "best_practices": ("category", "best-practices"),
    "seo": ("category", "seo"),
    "fcp_ms": ("audit", "first-contentful-paint"),
    "lcp_ms": ("audit", "largest-contentful-paint"),
    "speed_index_ms": ("audit", "speed-index"),
    "tbt_ms": ("audit", "total-blocking-time"),
    "cls": ("audit", "cumulative-layout-shift"),
}

AGENTIC_AUDITS = (
    "agent-accessibility-tree",
    "webmcp-form-coverage",
    "webmcp-registered-tools",
    "webmcp-schema-validity",
    "cumulative-layout-shift",
    "llms-txt",
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def quantile(values: list[float], probability: float) -> float:
    ordered = sorted(values)
    if len(ordered) == 1:
        return ordered[0]
    position = (len(ordered) - 1) * probability
    lower = int(position)
    upper = min(lower + 1, len(ordered) - 1)
    fraction = position - lower
    return ordered[lower] + (ordered[upper] - ordered[lower]) * fraction


def metric_value(report: dict, definition: tuple[str, str]) -> float | None:
    kind, key = definition
    if kind == "category":
        score = (report.get("categories", {}).get(key) or {}).get("score")
        return None if score is None else float(score) * 100
    value = (report.get("audits", {}).get(key) or {}).get("numericValue")
    return None if value is None else float(value)


def main_document_status(report: dict) -> int | None:
    items = ((report.get("audits", {}).get("network-requests") or {}).get("details") or {}).get("items") or []
    documents = [item for item in items if item.get("resourceType") == "Document"]
    if not documents:
        return None
    status = documents[-1].get("statusCode")
    return None if status is None else int(status)


def main() -> None:
    parser = argparse.ArgumentParser(description="Regera os dados derivados a partir dos 140 relatórios Lighthouse.")
    parser.add_argument("--raw-dir", type=Path, required=True, help="Diretório com os 140 arquivos .report.json")
    parser.add_argument("--out", type=Path, required=True, help="Diretório de saída")
    args = parser.parse_args()
    manifest_path = ROOT / "protocolo" / "manifesto-de-urls.csv"
    log_path = ROOT / "protocolo" / "registro-de-execucao.csv"
    raw_dir = args.raw_dir.resolve()
    out = args.out.resolve()
    out.mkdir(parents=True, exist_ok=True)
    with manifest_path.open(encoding="utf-8", newline="") as handle:
        manifest = {row["id"]: row for row in csv.DictReader(handle)}
    with log_path.open(encoding="utf-8", newline="") as handle:
        execution = list(csv.DictReader(handle))

    rows: list[dict[str, str | float]] = []
    agentic_rows: list[dict[str, str | float]] = []
    integrity: list[dict[str, str]] = []
    for entry in execution:
        target = manifest[entry["id"]]
        report_path = raw_dir / Path(entry["arquivo_json"]).name if entry["arquivo_json"] else None
        integrity_row = {
            "id": entry["id"],
            "perfil": entry["perfil"],
            "repeticao": entry["repeticao"],
            "status_execucao": entry["status"],
            "arquivo_json": entry["arquivo_json"],
            "sha256_registrado": entry["sha256_json"],
            "sha256_conferido": "",
            "integridade": "sem_relatorio",
        }
        if not report_path or not report_path.exists():
            integrity.append(integrity_row)
            continue

        checked_hash = sha256(report_path)
        integrity_row["sha256_conferido"] = checked_hash
        integrity_row["integridade"] = "ok" if checked_hash == entry["sha256_json"] else "divergente"
        integrity.append(integrity_row)

        report = json.loads(report_path.read_text(encoding="utf-8"))
        runtime_error = report.get("runtimeError") or {}
        http_status_audit = report.get("audits", {}).get("http-status-code") or {}
        http_status = main_document_status(report)
        valid = (
            not runtime_error
            and http_status_audit.get("score") == 1
            and (http_status is None or 200 <= http_status < 400)
        )
        row: dict[str, str | float] = {
            "id": entry["id"],
            "veiculo": target["veiculo"],
            "tipo_pagina": target["tipo_pagina"],
            "perfil": entry["perfil"],
            "repeticao": entry["repeticao"],
            "inicio": entry["inicio"],
            "termino": entry["termino"],
            "url_solicitada": report.get("requestedUrl", entry["url"]),
            "url_final": report.get("finalDisplayedUrl") or report.get("finalUrl") or "",
            "http_status": "" if http_status is None else str(int(http_status)),
            "lighthouse": report.get("lighthouseVersion", ""),
            "valida": "sim" if valid else "nao",
            "erro": runtime_error.get("code", "") or runtime_error.get("message", ""),
            "arquivo_json": entry["arquivo_json"],
            "sha256_json": checked_hash,
        }
        for name, definition in METRICS.items():
            value = metric_value(report, definition) if valid else None
            row[name] = "" if value is None else value
        rows.append(row)

        if valid:
            agentic_category = report.get("categories", {}).get("agentic-browsing") or {}
            for audit_id in AGENTIC_AUDITS:
                audit = report.get("audits", {}).get(audit_id) or {}
                score = audit.get("score")
                agentic_rows.append({
                    "id": entry["id"],
                    "veiculo": target["veiculo"],
                    "tipo_pagina": target["tipo_pagina"],
                    "perfil": entry["perfil"],
                    "repeticao": entry["repeticao"],
                    "inicio": entry["inicio"],
                    "url_final": report.get("finalDisplayedUrl") or report.get("finalUrl") or "",
                    "categoria_score_fracao": "" if agentic_category.get("score") is None else agentic_category["score"],
                    "categoria_modo": agentic_category.get("categoryScoreDisplayMode", ""),
                    "auditoria": audit_id,
                    "titulo": audit.get("title", ""),
                    "score": "" if score is None else score,
                    "modo": audit.get("scoreDisplayMode", ""),
                    "valor_numerico": "" if audit.get("numericValue") is None else audit["numericValue"],
                    "valor_exibido": audit.get("displayValue", ""),
                    "arquivo_json": entry["arquivo_json"],
                })

    raw_columns = [
        "id", "veiculo", "tipo_pagina", "perfil", "repeticao", "inicio", "termino",
        "url_solicitada", "url_final", "http_status", "lighthouse", "valida", "erro",
        *METRICS.keys(), "arquivo_json", "sha256_json",
    ]
    with (out / "dados-brutos-consolidados.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=raw_columns)
        writer.writeheader()
        writer.writerows(rows)

    grouped: dict[tuple[str, str, str, str], list[float]] = defaultdict(list)
    for row in rows:
        if row["valida"] != "sim":
            continue
        for metric in METRICS:
            if row[metric] != "":
                grouped[(str(row["veiculo"]), str(row["tipo_pagina"]), str(row["perfil"]), metric)].append(float(row[metric]))

    summaries = []
    for (vehicle, page_type, profile, metric), values in sorted(grouped.items()):
        summaries.append({
            "veiculo": vehicle,
            "tipo_pagina": page_type,
            "perfil": profile,
            "metrica": metric,
            "n": len(values),
            "mediana": statistics.median(values),
            "q1": quantile(values, 0.25),
            "q3": quantile(values, 0.75),
            "iqr": quantile(values, 0.75) - quantile(values, 0.25),
            "minimo": min(values),
            "maximo": max(values),
        })
    summary_columns = ["veiculo", "tipo_pagina", "perfil", "metrica", "n", "mediana", "q1", "q3", "iqr", "minimo", "maximo"]
    with (out / "resumo-medianas-iqr.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=summary_columns)
        writer.writeheader()
        writer.writerows(summaries)

    comparison = []
    by_dimension: dict[tuple[str, str, str], list[dict]] = defaultdict(list)
    for item in summaries:
        by_dimension[(item["tipo_pagina"], item["perfil"], item["metrica"])].append(item)
    for (page_type, profile, metric), items in sorted(by_dimension.items()):
        competitors = [float(item["mediana"]) for item in items if item["veiculo"] != "Nintendista News"]
        group_median = statistics.median(competitors) if competitors else None
        for item in items:
            comparison.append({
                "tipo_pagina": page_type,
                "perfil": profile,
                "metrica": metric,
                "veiculo": item["veiculo"],
                "mediana_veiculo": item["mediana"],
                "mediana_concorrentes": "" if group_median is None else group_median,
                "diferenca": "" if group_median is None else float(item["mediana"]) - group_median,
            })
    comparison_columns = ["tipo_pagina", "perfil", "metrica", "veiculo", "mediana_veiculo", "mediana_concorrentes", "diferenca"]
    with (out / "comparacao-mediana-veiculos-comparadores.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=comparison_columns)
        writer.writeheader()
        writer.writerows(comparison)

    with (out / "integridade-relatorios.csv").open("w", encoding="utf-8", newline="") as handle:
        columns = ["id", "perfil", "repeticao", "status_execucao", "arquivo_json", "sha256_registrado", "sha256_conferido", "integridade"]
        writer = csv.DictWriter(handle, fieldnames=columns)
        writer.writeheader()
        writer.writerows(integrity)

    agentic_columns = [
        "id", "veiculo", "tipo_pagina", "perfil", "repeticao", "inicio", "url_final",
        "categoria_score_fracao", "categoria_modo", "auditoria", "titulo", "score",
        "modo", "valor_numerico", "valor_exibido", "arquivo_json",
    ]
    with (out / "agentic-browsing-detalhado.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=agentic_columns)
        writer.writeheader()
        writer.writerows(agentic_rows)

    agentic_grouped: dict[tuple[str, str, str, str], list[dict[str, str | float]]] = defaultdict(list)
    for item in agentic_rows:
        agentic_grouped[(
            str(item["veiculo"]),
            str(item["tipo_pagina"]),
            str(item["perfil"]),
            str(item["auditoria"]),
        )].append(item)

    agentic_summaries: list[dict[str, str | int | float]] = []
    for (vehicle, page_type, profile, audit_id), items in sorted(agentic_grouped.items()):
        applicable = [item for item in items if item["modo"] != "notApplicable" and item["score"] != ""]
        scores = [float(item["score"]) for item in applicable]
        agentic_summaries.append({
            "veiculo": vehicle,
            "tipo_pagina": page_type,
            "perfil": profile,
            "auditoria": audit_id,
            "n_total": len(items),
            "n_aplicavel": len(applicable),
            "n_nao_aplicavel": sum(1 for item in items if item["modo"] == "notApplicable"),
            "n_aprovado": sum(1 for value in scores if value == 1),
            "n_reprovado": sum(1 for value in scores if value == 0),
            "mediana_score": "" if not scores else statistics.median(scores),
            "q1_score": "" if not scores else quantile(scores, 0.25),
            "q3_score": "" if not scores else quantile(scores, 0.75),
        })
    agentic_summary_columns = [
        "veiculo", "tipo_pagina", "perfil", "auditoria", "n_total", "n_aplicavel",
        "n_nao_aplicavel", "n_aprovado", "n_reprovado", "mediana_score", "q1_score", "q3_score",
    ]
    with (out / "agentic-browsing-resumo.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=agentic_summary_columns)
        writer.writeheader()
        writer.writerows(agentic_summaries)

    expected = 140
    valid = sum(1 for row in rows if row["valida"] == "sim")
    report = [
        "# Verificação da coleta Lighthouse",
        "",
        f"- Tentativas registradas: **{len(execution)} de {expected}**",
        f"- Relatórios JSON consolidados: **{len(rows)}**",
        f"- Auditorias válidas: **{valid}**",
        f"- Tentativas sem relatório válido: **{len(execution) - valid}**",
        f"- Arquivos com hash divergente: **{sum(1 for row in integrity if row['integridade'] == 'divergente')}**",
        "",
        "Nenhum valor foi imputado para tentativas com erro.",
    ]
    (out / "verificacao-da-coleta.md").write_text("\n".join(report) + "\n", encoding="utf-8")
    print(
        f"tentativas={len(execution)} json={len(rows)} validas={valid} "
        f"resumo={len(summaries)} agentic={len(agentic_rows)}"
    )


if __name__ == "__main__":
    main()
