#!/usr/bin/env python3
"""Tests for markdown_table_converter. Run: python3 tests/test_markdown_table_converter.py

No third-party dependencies. One test module, stdlib unittest only.
"""

import subprocess
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from markdown_table_converter import convert, parse_markdown, split_md_row  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
CLI = ROOT / "src" / "markdown_table_converter.py"


class TestCsvToMarkdown(unittest.TestCase):
    def test_basic_and_numeric_alignment(self):
        out = convert("name,age\nAda,36\nGrace,40\n", "csv", "md")
        self.assertEqual(
            out,
            "| name | age |\n| :--- | ---: |\n| Ada | 36 |\n| Grace | 40 |\n",
        )

    def test_pipe_is_escaped(self):
        out = convert("note\nlikes pipes | here\n", "csv", "md")
        self.assertIn("likes pipes \\| here", out)

    def test_forced_alignment(self):
        out = convert("name\nAda\n", "csv", "md", align="center")
        self.assertIn("| :---: |", out)

    def test_short_row_is_padded(self):
        out = convert("a,b,c\n1,2\n", "csv", "md")
        self.assertIn("| 1 | 2 |  |", out)


class TestJsonToMarkdown(unittest.TestCase):
    def test_missing_key_becomes_empty_cell(self):
        out = convert('[{"a": "1", "b": "2"}, {"a": "3"}]', "json", "md")
        self.assertIn("| 3 |  |", out)

    def test_nested_value_is_json_text(self):
        out = convert('[{"a": {"x": 1}}]', "json", "md")
        self.assertIn('{"x": 1}', out)

    def test_json_must_be_list_of_objects(self):
        with self.assertRaises(ValueError):
            convert('{"a": 1}', "json", "md")


class TestMarkdownBack(unittest.TestCase):
    TABLE = "| name | age | note |\n| :--- | ---: | :--- |\n| Ada | 36 | likes pipes \\| and commas |\n"

    def test_md_to_csv_unescapes_pipe(self):
        out = convert(self.TABLE, "md", "csv")
        self.assertEqual(out, "name,age,note\nAda,36,likes pipes | and commas\n")

    def test_md_to_json_keeps_strings(self):
        out = convert(self.TABLE, "md", "json")
        self.assertIn('"age": "36"', out)

    def test_bad_separator_is_rejected(self):
        with self.assertRaises(ValueError):
            convert("| a |\n| not a separator |\n| 1 |\n", "md", "csv")

    def test_split_row_handles_escaped_pipe(self):
        self.assertEqual(split_md_row("| a \\| b | c |"), ["a | b", "c"])

    def test_parse_markdown_pads_short_rows(self):
        headers, rows = parse_markdown("| a | b |\n| :--- | :--- |\n| 1 |\n")
        self.assertEqual((headers, rows), (["a", "b"], [["1", ""]]))


class TestRoundTripsAndCli(unittest.TestCase):
    def test_csv_round_trip(self):
        original = "name,age,note\nAda,36,likes pipes | and commas\n"
        md = convert(original, "csv", "md")
        self.assertEqual(convert(md, "md", "csv"), original)

    def test_json_round_trip_keeps_string_values(self):
        original = '[{"name": "Ada", "age": "36"}]'
        md = convert(original, "json", "md")
        back = convert(md, "md", "json")
        self.assertIn('"name": "Ada"', back)
        self.assertIn('"age": "36"', back)

    def test_cli_stdin_to_stdout(self):
        result = subprocess.run(
            [sys.executable, str(CLI), "--from", "csv", "--to", "md"],
            input="a,b\n1,2\n", capture_output=True, text=True, check=False,
        )
        self.assertEqual(result.returncode, 0)
        self.assertIn("| a | b |", result.stdout)

    def test_cli_empty_input_exits_2(self):
        result = subprocess.run(
            [sys.executable, str(CLI), "--from", "csv", "--to", "md"],
            input="", capture_output=True, text=True, check=False,
        )
        self.assertEqual(result.returncode, 2)
        self.assertIn("error:", result.stderr)

    def test_cli_bundled_examples_convert(self):
        for args in (
            ("--from", "csv", "--to", "md", "--input", "examples/sample.csv"),
            ("--from", "json", "--to", "md", "--input", "examples/sample.json"),
            ("--from", "md", "--to", "csv", "--input", "examples/sample-table.md"),
        ):
            result = subprocess.run(
                [sys.executable, str(CLI), *args],
                cwd=ROOT, capture_output=True, text=True, check=False,
            )
            self.assertEqual(result.returncode, 0, msg=str(args))
            self.assertTrue(result.stdout.strip())


if __name__ == "__main__":
    unittest.main(verbosity=2)
