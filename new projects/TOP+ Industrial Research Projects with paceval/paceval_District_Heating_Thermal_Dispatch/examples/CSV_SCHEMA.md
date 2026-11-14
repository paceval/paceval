# Canonical CSV schemas (English)

- UTF-8, comma-separated columns, dot as decimal separator, LF line endings.
- All numeric cells must be finite signed decimal literals or decimal exponents. Formulas, NaN, Inf, spaces and decimal commas are rejected before original SDK numeric conversion.
- `synthetic_edge_grid.csv`: `case_id` plus 14 variables declared in `formula_manifest.json` under `edge`; outlet temperatures degrees Celsius, cp J/(kg K), mass flow kg/s, UA W/K, f dimensionless, L/D metres, rho kg/m3, pump efficiency dimensionless, dpmax Pa, Qreq W.
- `synthetic_network_dispatch.csv`: `scenario_id` plus 23 network variables; demand W, pressure limit expressed as Pmax [W] for pump operation, pipe UA in W/K, pipe lengths and diameters in metres, branch mass flows kg/s.
- `mcp_edge_observed.csv` and `mcp_network_observed.csv`: selected decimal values returned by actual remote MCP batches, not directly exported original SDK CSV. They are rounded text evidence, not bitwise lossless binary64 recordings.
- Units: supply and return temperatures in degrees Celsius with differences in K; Q and pressure in W and Pa respectively. The synthetic demand is a requirement at the two connected consumers.
- Invalid domains include m<=0, cp<=0, D<=0, rho<=0, eta<=0, Tin<=Tr, or unbounded/inconsistent temperatures. Zero-flow pipes are out of scope of this steady-flow kernel.
