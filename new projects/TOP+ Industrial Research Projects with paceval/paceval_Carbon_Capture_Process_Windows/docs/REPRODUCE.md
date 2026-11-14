# Exact reproduction procedure

1. Use a Linux x86-64 host with C++17, CMake and the matching original paceval shared library. The distributed interface headers are in `src/`. Do not distribute the runtime binary.
2. Install Python dependencies from `README.md` and run `python3 scripts/generate_input.py` to regenerate 3,072 deterministic synthetic operating points.
3. Configure, build and run CTest using the commands in the main README. Run the executable with `--run` and the two paths for input and output.
4. Check `results/execution_evidence.json` and `results/math_execution_inventory.csv` for graph creation and execution counts; compare outputs against `results/high_precision_audit.json`.
5. Run `python3 scripts/make_figures.py` and `python3 scripts/check_markdown.py .` before the package is published. The latter scans every `.md` file recursively.
6. Re-run the program with a separate output directory and compare file digests for the central deterministic CSV and JSON files. Repetition results must be tracked separately and must not inflate the main graph count.

The standalone `--selftest` validates the true scalar and multi-graph SDK paths, arithmetic and logical operator boundaries, decimal literal rejection, and normal conversion. The independent high-precision reference imports actual parsed IEEE-754 float inputs. Graphic images are derived from real generated paceval result CSVs.
