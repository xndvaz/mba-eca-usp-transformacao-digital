#!/usr/bin/env python3
"""Valida contagens, integridade, ausência de segredos locais e regeneração dos dados."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
EXPECTED_REPORTS = 140
EXPECTED_URLS = 14
DERIVED = (
    "dados-brutos-consolidados.csv",
    "resumo-medianas-iqr.csv",
    "comparacao-mediana-veiculos-comparadores.csv",
    "agentic-browsing-detalhado.csv",
    "agentic-browsing-resumo.csv",
)
FORBIDDEN_MARKERS = (
    b"/Users/xndvaz/",
    b"xndvaz@gmail.com",
    b"Authorization:",
    b"Set-Cookie:",
    b"Cookie:",
    b"-----BEGIN OPENSSH PRIVATE KEY-----",
    b"-----BEGIN RSA PRIVATE KEY-----",
    b"github_pat_",
    b"ghp_",
    b"gho_",
    b"ghu_",
    b"ghs_",
    b"ghr_",
    b"sk-proj-",
    b"sk-svcacct-",
)

# Ocorrência falsa positiva confirmada dentro de um identificador publicitário
# público do Google. A exceção é vinculada ao nome, ao hash integral do JSON e
# a uma única ocorrência; qualquer mudança no arquivo volta a bloquear o pacote.
KNOWN_FALSE_POSITIVE = {
    "file": "boy_article__desktop__r03.report.json",
    "sha256": "4ceaa2d7e8c93ea2eb823ba87e94a26b4484dd4fe16b9bdbec66a1dbd3647658",
    "marker": b"ghu_",
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def fail(message: str) -> None:
    raise SystemExit(f"ERRO: {message}")


def validate_raw(raw_dir: Path) -> None:
    reports = sorted(raw_dir.glob("*.report.json"))
    if len(reports) != EXPECTED_REPORTS:
        fail(f"esperados {EXPECTED_REPORTS} JSON; encontrados {len(reports)}")

    expected_hashes = {
        Path(row["arquivo_json"]).name: row["sha256_conferido"]
        for row in rows(ROOT / "integridade" / "integridade-relatorios.csv")
    }
    if len(expected_hashes) != EXPECTED_REPORTS:
        fail("o manifesto de integridade não contém 140 entradas distintas")
    compact_hashes = {
        row["arquivo"]: row["sha256"]
        for row in rows(ROOT / "integridade" / "sha256-relatorios-json.csv")
    }
    if compact_hashes != expected_hashes:
        fail("o manifesto compacto de hashes diverge do manifesto de integridade")

    for report in reports:
        content = report.read_bytes()
        for marker in FORBIDDEN_MARKERS:
            if marker in content:
                is_known_false_positive = (
                    report.name == KNOWN_FALSE_POSITIVE["file"]
                    and marker == KNOWN_FALSE_POSITIVE["marker"]
                    and content.count(marker) == 1
                    and sha256(report) == KNOWN_FALSE_POSITIVE["sha256"]
                )
                if is_known_false_positive:
                    continue
                fail(f"marcador sensível {marker!r} localizado em {report.name}")
        try:
            payload = json.loads(content)
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            fail(f"JSON inválido em {report.name}: {exc}")
        if payload.get("lighthouseVersion") != "13.4.1":
            fail(f"versão inesperada do Lighthouse em {report.name}")
        expected = expected_hashes.get(report.name)
        if not expected or sha256(report) != expected:
            fail(f"hash divergente em {report.name}")


def rebuild_and_compare(raw_dir: Path) -> None:
    with tempfile.TemporaryDirectory(prefix="lighthouse-rebuild-") as tmp:
        out = Path(tmp)
        subprocess.run(
            [
                sys.executable,
                str(ROOT / "scripts" / "consolidar-resultados.py"),
                "--raw-dir",
                str(raw_dir),
                "--out",
                str(out),
            ],
            check=True,
        )
        for name in DERIVED:
            if (out / name).read_bytes() != (ROOT / "dados" / name).read_bytes():
                fail(f"dados regenerados divergem de dados/{name}")
        if (out / "integridade-relatorios.csv").read_bytes() != (
            ROOT / "integridade" / "integridade-relatorios.csv"
        ).read_bytes():
            fail("manifesto de integridade regenerado diverge do publicado")
        if (out / "sha256-relatorios-json.csv").read_bytes() != (
            ROOT / "integridade" / "sha256-relatorios-json.csv"
        ).read_bytes():
            fail("manifesto compacto de hashes regenerado diverge do publicado")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--raw-dir", type=Path, required=True)
    parser.add_argument("--rebuild", action="store_true")
    args = parser.parse_args()

    if len(rows(ROOT / "protocolo" / "manifesto-de-urls.csv")) != EXPECTED_URLS:
        fail("o manifesto não contém 14 URLs")
    if len(rows(ROOT / "protocolo" / "registro-de-execucao.csv")) != EXPECTED_REPORTS:
        fail("o registro não contém 140 execuções")
    if len(rows(ROOT / "dados" / "dados-brutos-consolidados.csv")) != EXPECTED_REPORTS:
        fail("os dados consolidados não contêm 140 auditorias")
    integrity = rows(ROOT / "integridade" / "integridade-relatorios.csv")
    if len(integrity) != EXPECTED_REPORTS or any(row["integridade"] != "ok" for row in integrity):
        fail("o manifesto de integridade está incompleto ou contém divergência")
    if len(rows(ROOT / "integridade" / "sha256-relatorios-json.csv")) != EXPECTED_REPORTS:
        fail("o manifesto compacto de hashes não contém 140 entradas")

    validate_raw(args.raw_dir.resolve())
    if args.rebuild:
        rebuild_and_compare(args.raw_dir.resolve())

    print("OK: 14 URLs, 140 auditorias e integridade confirmada")


if __name__ == "__main__":
    main()
