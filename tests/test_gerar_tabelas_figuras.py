from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "gerar-tabelas-figuras.py"
SPEC = importlib.util.spec_from_file_location("gerar_tabelas_figuras", SCRIPT)
assert SPEC and SPEC.loader
GENERATOR = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(GENERATOR)


class TableWrappingTest(unittest.TestCase):
    def assert_fits(self, value: str, width: int, bold: bool = False) -> None:
        selected_font = GENERATOR.font(46, bold)
        lines = GENERATOR.wrap_cell(value, width, selected_font)
        self.assertTrue(lines)
        for line in lines:
            self.assertLessEqual(selected_font.getlength(line), width)

    def test_headers_fit_their_cells(self) -> None:
        header = ["Accessibility", "Best Practices", "Inicial desktop"]
        widths = [330, 350, 320]
        selected_font = GENERATOR.font(36, bold=True)
        GENERATOR.assert_tokens_fit([header], widths, selected_font)
        for value, width in zip(header, widths):
            lines = GENERATOR.wrap_cell(value, width - 18, selected_font)
            self.assertEqual(" ".join(lines), value)

    def test_headers_do_not_split_words(self) -> None:
        header = ["Perfil", "Veículo", "Performance", "Accessibility", "Best Practices", "SEO"]
        widths = [218, 301, 309, 364, 388, 280]
        selected_font = GENERATOR.font(36, bold=True)
        GENERATOR.assert_tokens_fit([header], widths, selected_font)
        for value, width in zip(header, widths):
            lines = GENERATOR.wrap_cell(value, width - 18, selected_font)
            self.assertEqual(" ".join(lines), value)

    def test_vehicle_names_preserve_explicit_breaks(self) -> None:
        selected_font = GENERATOR.font(46)
        lines = GENERATOR.wrap_cell("Nintendista\nNews", 320, selected_font)
        self.assertEqual(lines, ["Nintendista", "News"])

    def test_long_url_is_split_without_overflow(self) -> None:
        self.assert_fits(
            "https://nintendoboy.com.br/2026/08/sin-reloaded-remaster-do-fps-narrativo.html",
            420,
        )

    def test_body_font_preserves_tokens(self) -> None:
        rows = [["Nintendista\nNews", "1922 [1876-2024]", "0,000 [0,000-0,000]"]]
        widths = [260, 275, 260]
        selected_font = GENERATOR.font(31)
        GENERATOR.assert_tokens_fit(rows, widths, selected_font)
        for row in rows:
            for value, width in zip(row, widths):
                lines = GENERATOR.wrap_cell(value, width - 18, selected_font)
                self.assertEqual(" ".join(lines), value.replace("\n", " "))


if __name__ == "__main__":
    unittest.main()
