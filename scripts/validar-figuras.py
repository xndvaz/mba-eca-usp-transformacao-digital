#!/usr/bin/env python3
"""Compara visualmente as figuras regeneradas com os artefatos publicados."""

from __future__ import annotations

import argparse
from pathlib import Path

from PIL import Image, ImageChops, ImageStat


PNG_FILES = (
    "Figura_2_Categorias_Lighthouse.png",
    "Figura_3_FCP_LCP_Speed_Index.png",
    "Figura_4A_TBT.png",
    "Figura_4B_CLS.png",
    "Figura_5_Agentic_Browsing.png",
    "Tabela_1_URLs_Auditadas.png",
    "Tabela_2A_Categorias_Iniciais.png",
    "Tabela_2B_Categorias_Internas.png",
    "Tabela_3A_Metricas_Iniciais.png",
    "Tabela_3B_Metricas_Internas.png",
    "Tabela_4_Agentic_Browsing.png",
)


def fail(message: str) -> None:
    raise SystemExit(f"ERRO: {message}")


def normalized(image: Image.Image) -> Image.Image:
    width = 400
    height = max(1, round(image.height * width / image.width))
    return image.convert("L").resize((width, height), Image.Resampling.BILINEAR)


def compare(expected_path: Path, actual_path: Path) -> tuple[float, float]:
    with Image.open(expected_path) as expected, Image.open(actual_path) as actual:
        expected.verify()
        actual.verify()
    with Image.open(expected_path) as expected, Image.open(actual_path) as actual:
        if expected.size != actual.size:
            fail(f"dimensão divergente em {actual_path.name}: {actual.size} != {expected.size}")
        difference = ImageChops.difference(normalized(expected), normalized(actual))
        mean = ImageStat.Stat(difference).mean[0]
        histogram = difference.histogram()
        total = sum(histogram)
        changed = sum(histogram[33:]) / total if total else 0.0
        return mean, changed


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--expected", type=Path, required=True)
    parser.add_argument("--actual", type=Path, required=True)
    args = parser.parse_args()

    for name in PNG_FILES:
        expected = args.expected / name
        actual = args.actual / name
        if not expected.is_file() or not actual.is_file():
            fail(f"figura ausente: {name}")
        mean, changed = compare(expected, actual)
        if mean > 3.0 or changed > 0.05:
            fail(f"conteúdo visual divergente em {name}: média={mean:.3f}; fração={changed:.3%}")
        print(f"OK: {name}: média={mean:.3f}; fração={changed:.3%}")


if __name__ == "__main__":
    main()
