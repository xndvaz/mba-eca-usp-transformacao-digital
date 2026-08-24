from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path

from PIL import Image


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "validar-figuras.py"
SPEC = importlib.util.spec_from_file_location("validar_figuras", SCRIPT)
assert SPEC and SPEC.loader
VALIDATOR = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(VALIDATOR)


class VisualValidationTest(unittest.TestCase):
    def compare_images(self, expected: Image.Image, actual: Image.Image) -> tuple[float, float, float, float]:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            expected_path = root / "expected.png"
            actual_path = root / "actual.png"
            expected.save(expected_path)
            actual.save(actual_path)
            return VALIDATOR.compare(expected_path, actual_path)

    def test_identical_images_pass(self) -> None:
        expected = Image.new("L", (400, 100), 255)
        mean, changed, structure, local = self.compare_images(expected, expected.copy())
        self.assertEqual((mean, changed, structure, local), (0.0, 0.0, 0.0, 0.0))
        self.assertFalse(VALIDATOR.is_divergent(mean, changed, structure, local, "Figura_2.png"))

    def test_sparse_antialiasing_difference_passes(self) -> None:
        expected = Image.new("L", (400, 100), 255)
        actual = expected.copy()
        for x in range(0, actual.width, 24):
            for y in range(actual.height):
                actual.putpixel((x, y), 195)
        mean, changed, structure, local = self.compare_images(expected, actual)
        self.assertLessEqual(mean, VALIDATOR.MAX_MEAN_DIFFERENCE)
        self.assertLessEqual(changed, VALIDATOR.MAX_CHANGED_FRACTION)
        self.assertFalse(VALIDATOR.is_divergent(mean, changed, structure, local, "Figura_2.png"))

    def test_structural_change_is_rejected(self) -> None:
        expected = Image.new("L", (400, 100), 255)
        actual = expected.copy()
        for x in range(40):
            for y in range(actual.height):
                actual.putpixel((x, y), 0)
        mean, changed, structure, local = self.compare_images(expected, actual)
        self.assertGreater(changed, VALIDATOR.MAX_CHANGED_FRACTION)
        self.assertTrue(VALIDATOR.is_divergent(mean, changed, structure, local, "Figura_2.png"))

    def test_global_tone_change_is_rejected_by_mean_only(self) -> None:
        expected = Image.new("L", (400, 100), 255)
        actual = Image.new("L", (400, 100), 251)
        mean, changed, structure, local = self.compare_images(expected, actual)
        self.assertGreater(mean, VALIDATOR.MAX_MEAN_DIFFERENCE)
        self.assertEqual(changed, 0.0)
        self.assertTrue(VALIDATOR.is_divergent(mean, changed, structure, local, "Figura_2.png"))

    def test_local_structural_change_is_rejected_by_fraction_only(self) -> None:
        expected = Image.new("L", (400, 100), 255)
        actual = expected.copy()
        for x in range(24):
            for y in range(actual.height):
                actual.putpixel((x, y), 221)
        mean, changed, structure, local = self.compare_images(expected, actual)
        self.assertLessEqual(mean, VALIDATOR.MAX_MEAN_DIFFERENCE)
        self.assertGreater(changed, VALIDATOR.MAX_CHANGED_FRACTION)
        self.assertTrue(VALIDATOR.is_divergent(mean, changed, structure, local, "Figura_2.png"))

    def test_table_antialiasing_variation_passes_without_losing_text(self) -> None:
        expected = Image.new("L", (400, 100), 255)
        actual = expected.copy()
        for x in range(0, actual.width, 24):
            for line_x in (x, min(x + 1, actual.width - 1)):
                for y in range(actual.height):
                    expected.putpixel((line_x, y), 30)
                    actual.putpixel((line_x, y), 70)
        mean, changed, structure, local = self.compare_images(expected, actual)
        self.assertEqual(structure, 0.0)
        self.assertTrue(VALIDATOR.is_divergent(mean, changed, structure, local, "Figura_2.png"))
        self.assertFalse(VALIDATOR.is_divergent(mean, changed, structure, local, "Tabela_1.png"))

    def test_missing_table_text_is_rejected_even_near_grid_lines(self) -> None:
        expected = Image.new("L", (400, 100), 255)
        for x in range(0, expected.width, 40):
            for y in range(expected.height):
                expected.putpixel((x, y), 100)
        for y in range(4, 84, 8):
            for x in range(8, 38):
                expected.putpixel((x, y), 32)
        actual = expected.copy()
        for y in (4, 12):
            for x in range(8, 38):
                actual.putpixel((x, y), 255)
        mean, changed, structure, local = self.compare_images(expected, actual)
        self.assertLess(mean, VALIDATOR.TABLE_LIMITS[0])
        self.assertLess(changed, VALIDATOR.TABLE_LIMITS[1])
        self.assertGreater(structure, VALIDATOR.TABLE_MAX_TEXT_STRUCTURE)
        self.assertTrue(VALIDATOR.is_divergent(mean, changed, structure, local, "Tabela_1.png"))

    def test_missing_short_cell_is_rejected_by_local_structure(self) -> None:
        expected = Image.new("L", (400, 200), 255)
        for tile_y in range(0, expected.height, 50):
            for tile_x in range(0, expected.width, 50):
                for y in (tile_y + 12, tile_y + 24, tile_y + 36):
                    for x in range(tile_x + 8, tile_x + 28):
                        expected.putpixel((x, y), 32)
        actual = expected.copy()
        for x in range(308, 328):
            actual.putpixel((x, 162), 255)
        mean, changed, structure, local = self.compare_images(expected, actual)
        self.assertLess(structure, VALIDATOR.TABLE_MAX_TEXT_STRUCTURE)
        self.assertGreater(local, VALIDATOR.TABLE_MAX_LOCAL_TEXT_STRUCTURE)
        self.assertTrue(VALIDATOR.is_divergent(mean, changed, structure, local, "Tabela_1.png"))


if __name__ == "__main__":
    unittest.main()
