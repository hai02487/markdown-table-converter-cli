# markdown-table-converter-cli

Convert CSV and JSON tables to GitHub-Flavoured Markdown tables and back again, offline, with no dependencies.

[![CI](https://github.com/hai02487/markdown-table-converter-cli/actions/workflows/ci.yml/badge.svg)](https://github.com/hai02487/markdown-table-converter-cli/actions/workflows/ci.yml) [![Licence: MIT](https://img.shields.io/badge/Licence-MIT-yellow.svg)](LICENSE)

## What it does

`markdown-table-converter` converts one table between three formats,
in both directions:

- CSV to Markdown, JSON to Markdown, Markdown to CSV, Markdown to JSON.
- Pipe characters inside a cell are escaped as `\|` in Markdown
  output and unescaped back on the way out, so a cell can never
  break the table.
- Column alignment is automatic: a column whose non-empty data
  cells are all numbers is right-aligned, everything else is
  left-aligned. Pass `--align left`, `--align right`, or
  `--align center` to force one alignment for all columns.
- It reads from a file or from stdin, and writes to a file or to
  stdout, so it works in pipes: `cat data.csv | ... --from csv --to md`.
- It is Python standard library only. No install step, no packages
  to download, nothing sent anywhere.

## What it does NOT do

- It does not guess types. On the Markdown to JSON leg, values stay
  strings: `"42"` stays `"42"` and never becomes the number 42.
- It does not turn `<br>` back into a newline. A newline inside a
  cell becomes `<br>` in Markdown output, and stays as the literal
  text `<br>` on the way back, because a Markdown table row cannot
  hold a newline.
- It does not read, print, or upload any data beyond the table it
  is given. Everything runs locally, on the input you pass it.
- It does not convert HTML tables, spreadsheets, or databases.
  Those are separate jobs; this tool converts CSV, JSON, and
  Markdown tables only.

## Who it is for

Anyone who keeps data in CSV or JSON and needs it as a readable
Markdown table for a README, a pull request, or docs — and anyone
who needs a Markdown table back out as data, without opening a
browser-based table builder.

## Install

No install step and no dependencies — Python 3.8+ is enough:

```sh
git clone https://github.com/hai02487/markdown-table-converter-cli.git
cd markdown-table-converter-cli
python3 src/markdown_table_converter.py --help
```

## Usage

From a file:

```sh
python3 src/markdown_table_converter.py --from csv --to md --input examples/sample.csv
```

From a pipe, which is the usual way to use it:

```sh
cat data.csv | python3 src/markdown_table_converter.py --from csv --to md
```

Real output on the bundled CSV example (`examples/sample.csv`):

```text
| name | age | note |
| :--- | ---: | :--- |
| Ada | 36 | likes pipes \| and commas |
| Grace | 40 | first programmer |
```

Note the two honest details in that output: the pipe in Ada's
note is escaped so the row stays intact, and the `age` column is
right-aligned because every data cell in it is a number.

Other directions, all verified by running them on the bundled examples:

```sh
python3 src/markdown_table_converter.py --from json --to md --input examples/sample.json
python3 src/markdown_table_converter.py --from md --to csv --input examples/sample-table.md
python3 src/markdown_table_converter.py --from md --to json --input examples/sample-table.md
```

Real output of the Markdown to CSV direction on
`examples/sample-table.md` (the escaped pipe comes back as a
plain pipe, and the CSV writer quotes nothing it does not need to):

```text
name,age,note
Ada,36,likes pipes | and commas
Grace,40,first programmer
```

Empty input is an error, not an empty table: it prints an error
to stderr and exits with code 2. The `--from` and `--to` formats
must be different, and `--delimiter` must be exactly one character
for CSV input or output.

## Example

The main job and one edge case, both in `examples/run-example.sh`
(run it from the repo root: `sh examples/run-example.sh`):

1. Main job: CSV to Markdown, as above, with pipe escaping and
   automatic numeric alignment.
2. Edge case: a JSON list where one object is missing a key.
   `examples/sample.json` has Ada with a `city` and Grace without
   one. JSON to Markdown gives Grace an empty city cell instead
   of failing or inventing a value:

```text
| age | city | name |
| ---: | :--- | :--- |
| 36 | London | Ada |
| 40 |  | Grace |
```

Columns appear in first-seen key order, and a missing key is an
empty cell — nothing is invented to fill it.

## How it is tested

```bash
python3 tests/test_markdown_table_converter.py
```

The tests cover both directions, pipe escaping and unescaping,
automatic and forced alignment, short-row padding, missing JSON
keys, nested JSON values, bad separator rejection, CSV and JSON
round trips, stdin-to-stdout piping, empty-input exit code 2,
and the bundled examples converting successfully.

## Contributing

Small, focused improvements are welcome. Open an issue first for
anything larger than a typo, so the scope can be agreed before
work starts. Every claim in a proposed change must be verifiable:
a command must be runnable, and a conversion rule must be in the
code and covered by a test. Python standard library only — no new
dependency without a reason in the issue.

## Licence

MIT — see [LICENSE](LICENSE). This is original work, written for
this repo.
