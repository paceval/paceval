# Adaptive paceval graph configuration

`active_graph.tsv` is the initial mathematical V9 graph model. It contains only the enumerated numeric coefficients and a version. Changes are made after matches using the validated model update routine. The match session itself owns its current writable copy under `stockfish_sessions/active_graph.tsv`.

The complete mathematical definition, feature mapping, legal data schema, safeguards, and limitations are documented in [V9 adaptive Stockfish research](../docs/V9_STOCKFISH_MATCH_AND_GRAPH_ADAPTATION.md). Arbitrary expression text in the TSV is intentionally prohibited.
