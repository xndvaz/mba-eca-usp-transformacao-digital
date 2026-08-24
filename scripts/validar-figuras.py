#!/usr/bin/env python3
"""Compara visualmente as figuras regeneradas com os artefatos publicados."""

from __future__ import annotations

import argparse
from pathlib import Path

from PIL import Image, ImageChops, ImageFilter, ImageStat


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

# Os geradores usam os arquivos DejaVu Sans versionados no repositório. Os
# gráficos mantêm limites estritos. Tabelas admitem maior variação de bordas
# tipográficas, mas uma máscara separada impede perda de texto escuro.
FIGURE_LIMITS = (3.0, 0.05)
TABLE_LIMITS = (8.0, 0.10)
TABLE_MAX_TEXT_STRUCTURE = 0.02
TABLE_MAX_LOCAL_TEXT_STRUCTURE = 0.10
TEXT_TILE_SIZE = 50
TEXT_TILE_MIN_INK = 5
MAX_MEAN_DIFFERENCE, MAX_CHANGED_FRACTION = FIGURE_LIMITS


def fail(message: str) -> None:
    raise SystemExit(f"ERRO: {message}")


def normalized(image: Image.Image) -> Image.Image:
    width = 400
    height = max(1, round(image.height * width / image.width))
    return image.convert("L").resize((width, height), Image.Resampling.BILINEAR)


def text_mask(image: Image.Image) -> Image.Image:
    # O limiar preserva o núcleo e a antialiasing do texto. Linhas longas são
    # removidas por projeção para que grades escuras não escondam texto ausente.
    mask = image.point(lambda pixel: 255 if pixel < 140 else 0)
    pixels = mask.load()
    horizontal = [
        y for y in range(mask.height)
        if sum(pixels[x, y] > 0 for x in range(mask.width)) >= mask.width * 0.6
    ]
    vertical = [
        x for x in range(mask.width)
        if sum(pixels[x, y] > 0 for y in range(mask.height)) >= mask.height * 0.6
    ]
    for y in horizontal:
        for x in range(mask.width):
            pixels[x, y] = 0
    for x in vertical:
        for y in range(mask.height):
            pixels[x, y] = 0
    return mask


def text_structure(expected: Image.Image, actual: Image.Image) -> tuple[float, float]:
    expected_mask = text_mask(expected)
    actual_mask = text_mask(actual)
    expected_neighborhood = expected_mask.filter(ImageFilter.MaxFilter(7))
    actual_neighborhood = actual_mask.filter(ImageFilter.MaxFilter(7))
    missing = ImageChops.subtract(expected_mask, actual_neighborhood)
    extra = ImageChops.subtract(actual_mask, expected_neighborhood)
    unmatched = ImageStat.Stat(missing).sum[0] + ImageStat.Stat(extra).sum[0]
    ink = ImageStat.Stat(expected_mask).sum[0] + ImageStat.Stat(actual_mask).sum[0]
    global_ratio = unmatched / ink if ink else 0.0
    local_ratio = 0.0
    for y in range(0, expected.height, TEXT_TILE_SIZE):
        for x in range(0, expected.width, TEXT_TILE_SIZE):
            box = (
                x,
                y,
                min(x + TEXT_TILE_SIZE, expected.width),
                min(y + TEXT_TILE_SIZE, expected.height),
            )
            tile_ink = (
                ImageStat.Stat(expected_mask.crop(box)).sum[0]
                + ImageStat.Stat(actual_mask.crop(box)).sum[0]
            )
            if tile_ink / 255 < TEXT_TILE_MIN_INK:
                continue
            tile_unmatched = (
                ImageStat.Stat(missing.crop(box)).sum[0]
                + ImageStat.Stat(extra.crop(box)).sum[0]
            )
            local_ratio = max(local_ratio, tile_unmatched / tile_ink)
    return global_ratio, local_ratio


def compare(expected_path: Path, actual_path: Path) -> tuple[float, float, float, float]:
    with Image.open(expected_path) as expected, Image.open(actual_path) as actual:
        expected.verify()
        actual.verify()
    with Image.open(expected_path) as expected, Image.open(actual_path) as actual:
        if expected.size != actual.size:
            fail(f"dimensão divergente em {actual_path.name}: {actual.size} != {expected.size}")
        expected_normalized = normalized(expected)
        actual_normalized = normalized(actual)
        difference = ImageChops.difference(expected_normalized, actual_normalized)
        mean = ImageStat.Stat(difference).mean[0]
        histogram = difference.histogram()
        total = sum(histogram)
        changed = sum(histogram[33:]) / total if total else 0.0
        structure, local_structure = text_structure(expected_normalized, actual_normalized)
        return mean, changed, structure, local_structure


def is_divergent(
    mean: float,
    changed: float,
    structure: float,
    local_structure: float,
    name: str,
) -> bool:
    max_mean, max_changed = TABLE_LIMITS if name.startswith("Tabela_") else FIGURE_LIMITS
    if name.startswith("Tabela_") and structure > TABLE_MAX_TEXT_STRUCTURE:
        return True
    if name.startswith("Tabela_") and local_structure > TABLE_MAX_LOCAL_TEXT_STRUCTURE:
        return True
    return mean > max_mean or changed > max_changed


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--expected", type=Path, required=True)
    parser.add_argument("--actual", type=Path, required=True)
    args = parser.parse_args()

    divergences: list[str] = []
    for name in PNG_FILES:
        expected = args.expected / name
        actual = args.actual / name
        if not expected.is_file() or not actual.is_file():
            fail(f"figura ausente: {name}")
        mean, changed, structure, local_structure = compare(expected, actual)
        metrics = (
            f"média={mean:.3f}; fração={changed:.3%}; "
            f"estrutura textual={structure:.3%}; "
            f"estrutura local={local_structure:.3%}"
        )
        if is_divergent(mean, changed, structure, local_structure, name):
            divergences.append(name)
            print(f"ERRO: conteúdo visual divergente em {name}: {metrics}")
        else:
            print(f"OK: {name}: {metrics}")
    if divergences:
        fail(f"{len(divergences)} artefato(s) visual(is) divergente(s)")


if __name__ == "__main__":
    main()
