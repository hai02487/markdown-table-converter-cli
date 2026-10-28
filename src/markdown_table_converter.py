#!/usr/bin/env python3
"""Convert between CSV, JSON, and GitHub-Flavoured Markdown tables.

Both directions, Python standard library only, stdin/stdout friendly.

Rules, stated plainly so output is predictable:
- Pipe characters inside a cell are escaped as ``\\|`` in Markdown output
  and unescaped back on the way out.
- Newlines inside a cell become ``<br>`` in Markdown output; on the way
  back, ``<br>`` stays as the literal text ``<br>`` (it is not turned
  back into a newline, because a Markdown table row cannot hold one).
- Alignment is automatic unless --align is given: a column whose
  non-empty data cells are all numbers is right-aligned, everything
  else is left-aligned. Numbers are integers, decimals, or a leading
  ``-``/``+`` sign, optionally with thousands commas.
- JSON values are kept as strings on the Markdown -> JSON leg: this
  tool does not guess types, so "42" stays "42" and never becomes 42.
- CSV rows shorter than the header are padded with empty cells; rows
  longer than the header keep their extra cells and the header is
  extended with empty column names for them (Markdown tables need a
  header cell per column).

Usage:
    python3 src/markdown_table_converter.py --from csv --to md < in.csv
    python3 src/markdown_table_converter.py --from json --to md --input data.json
    python3 src/markdown_table_converter.py --from md --to csv --input table.md
"""

import argparse
import csv
import io
import json
import re
import sys

_NUMBER_RE = re.compile(r"^[+-]?(\d{1,3}(,\d{3})+|\d+)(\.\d+)?$")


def escape_cell(value):
    """Escape a cell value for a Markdown table row."""
    return str(value).replace("\\", "\\\\").replace("|", "\\|").replace("\n", "<br>").replace("\r", "")


def split_md_row(line):
    """Split one Markdown table row on unescaped pipes.

    Leading/trailing pipes are separators, not cells. ``\\|`` becomes
    a literal pipe, ``\\\\`` becomes a backslash.
    """
    line = line.strip()
    if line.startswith("|"):
        line = line[1:]
    if line.endswith("|") and not line.endswith("\\|"):
        line = line[:-1]
    cells, current, escaped = [], [], False
    for char in line:
        if escaped:
            current.append(char)
            escaped = False
        elif char == "\\":
            escaped = True
        elif char == "|":
            cells.append("".join(current).strip())
            current = []
        else:
            current.append(char)
    if escaped:
        current.append("\\")
    cells.append("".join(current).strip())
    return cells


def _is_number(value):
    return bool(value) and _NUMBER_RE.match(value.strip()) is not None


def _alignments(headers, rows, align):
    if align in ("left", "right", "center"):
        return [align] * len(headers)
    result = []
    for index in range(len(headers)):
        values = [row[index] for row in rows if index < len(row) and row[index].strip()]
        result.append("right" if values and all(_is_number(v) for v in values) else "left")
    return result


def to_markdown(headers, rows, align="auto"):
    """Render headers + rows as a GitHub-Flavoured Markdown table."""
    headers = [str(h) for h in headers]
    rows = [[str(c) for c in row] for row in rows]
    width = max(len(headers), max((len(r) for r in rows), default=0))
    headers = headers + [""] * (width - len(headers))
    rows = [row + [""] * (width - len(row)) for row in rows]
    alignments = _alignments(headers, rows, align)
    sep_cells = []
    for a in alignments:
        sep_cells.append({ "left": ":---", "right": "---:", "center": ":---:"}[a])
    lines = ["| " + " | ".join(escape_cell(h) for h in headers) + " |",
             "| " + " | ".join(sep_cells) + " |"]
    for row in rows:
        lines.append("| " + " | ".join(escape_cell(c) for c in row) + " |")
    return "\n".join(lines) + "\n"


def parse_markdown(text):
    """Parse a Markdown table into (headers, rows). Raises ValueError."""
    lines = [line for line in text.splitlines() if line.strip()]
    if len(lines) < 2:
        raise ValueError("a Markdown table needs a header row and a separator row")
    headers = split_md_row(lines[0])
    separator = split_md_row(lines[1])
    if len(separator) != len(headers) or not all(
        re.fullmatch(r":?-{3,}:?", cell) for cell in separator
    ):
        raise ValueError("second row is not a valid Markdown separator row")
    rows = []
    for line in lines[2:]:
        row = split_md_row(line)
        if len(row) < len(headers):
            row = row + [""] * (len(headers) - len(row))
        rows.append(row[: len(headers)])
    return headers, rows


def _csv_rows(text, delimiter):
    reader = csv.reader(io.StringIO(text), delimiter=delimiter)
    rows = [row for row in reader if row]
    if not rows:
        raise ValueError("CSV input is empty")
    return rows


def convert(text, from_format, to_format, delimiter=",", align="auto"):
    """Convert one table between csv, json, and md. Returns output text."""
    if not text.strip():
        raise ValueError("input is empty")
    if from_format == "csv":
        rows = _csv_rows(text, delimiter)
        headers, data = rows[0], rows[1:]
    elif from_format == "json":
        data_in = json.loads(text)
        if not isinstance(data_in, list) or not data_in or not all(
            isinstance(item, dict) for item in data_in
        ):
            raise ValueError("JSON input must be a non-empty list of objects")
        headers = []
        for item in data_in:
            for key in item:
                if key not in headers:
                    headers.append(key)
        data = []
        for item in data_in:
            data.append([_json_scalar(item.get(key, "")) for key in headers])
    elif from_format == "md":
        headers, data = parse_markdown(text)
    else:
        raise ValueError(f"unsupported --from value: {from_format}")

    if to_format == "md":
        return to_markdown(headers, data, align)
    if to_format == "csv":
        out = io.StringIO()
        writer = csv.writer(out, delimiter=delimiter, lineterminator="\n")
        writer.writerow(headers)
        writer.writerows(data)
        return out.getvalue()
    if to_format == "json":
        return json.dumps(
            [{headers[i]: row[i] for i in range(len(headers))} for row in data],
            indent=2,
        ) + "\n"
    raise ValueError(f"unsupported --to value: {to_format}")


def _json_scalar(value):
    if isinstance(value, (dict, list)):
        return json.dumps(value)
    if value is None:
        return ""
    if isinstance(value, bool):
        return "true" if value else "false"
    return str(value)


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Convert CSV/JSON <-> GitHub-Flavoured Markdown tables."
    )
    parser.add_argument("--from", dest="from_format", required=True,
                        choices=["csv", "json", "md"],
                        help="input format")
    parser.add_argument("--to", dest="to_format", required=True,
                        choices=["csv", "json", "md"],
                        help="output format")
    parser.add_argument("--input", default="-",
                        help="input file, or - for stdin (default)")
    parser.add_argument("--output", default="-",
                        help="output file, or - for stdout (default)")
    parser.add_argument("--delimiter", default=",",
                        help="CSV delimiter, one character (default: ,)")
    parser.add_argument("--align", default="auto",
                        choices=["auto", "left", "right", "center"],
                        help="Markdown column alignment (default: auto)")
    args = parser.parse_args(argv)
    if args.from_format == args.to_format:
        parser.error("--from and --to must be different")
    if len(args.delimiter) != 1:
        parser.error("--delimiter must be exactly one character")
    try:
        if args.input == "-":
            text = sys.stdin.read()
        else:
            with open(args.input, encoding="utf-8") as handle:
                text = handle.read()
        result = convert(text, args.from_format, args.to_format,
                         delimiter=args.delimiter, align=args.align)
    except (ValueError, json.JSONDecodeError, OSError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    if args.output == "-":
        sys.stdout.write(result)
    else:
        with open(args.output, "w", encoding="utf-8") as handle:
            handle.write(result)
    return 0


if __name__ == "__main__":
    sys.exit(main())
