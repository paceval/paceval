# Reloadable evaluation graph model

`active_graph.tsv` is a strict two-column tab-separated file. It includes the version number, eight base coefficients, and optionally `feature.<name>` rows for one of the eight V10 nonlinear templates. Never paste a free-form formula into this TSV. In a running Stockfish session the authoritative model is `stockfish_sessions/active_graph.tsv` (not this factory default). Completed game archives preserve all trial and promoted versions. `active_graph_expression.txt`, `active_graph_terms.csv`, and `active_full_graph_catalog.csv` show the **actual paceval-executed** mathematical text in a readable form.

Use the source-compiled C++ runtime to regenerate mathematical graphs, rather than treating the TXT/CSV exports as executable code. Supported names and limits are defined in `src/adaptive_score_graph.h` and checked independently in `scripts/stockfish_match.py`.
