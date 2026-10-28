#!/bin/sh
# Run every conversion on the bundled examples. Run from the repo root:
#   sh examples/run-example.sh
set -e
cd "$(dirname "$0")/.."
echo "--- CSV -> Markdown ---"
python3 src/markdown_table_converter.py --from csv --to md --input examples/sample.csv
echo "--- JSON -> Markdown ---"
python3 src/markdown_table_converter.py --from json --to md --input examples/sample.json
echo "--- Markdown -> CSV ---"
python3 src/markdown_table_converter.py --from md --to csv --input examples/sample-table.md
echo "--- Markdown -> JSON ---"
python3 src/markdown_table_converter.py --from md --to json --input examples/sample-table.md
