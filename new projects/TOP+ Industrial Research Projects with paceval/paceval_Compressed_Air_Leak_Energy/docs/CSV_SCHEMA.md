# Numeric input/output CSV contract

The canonical input is `input/cases.csv`, UTF-8, with ASCII column names, comma-separated values, `\n` records, a single header and exactly 22 fields: `case_id`, `scenario` and 20 ordered numerical model parameters. `case_id` allows uppercase letters, digits and underscores, while `scenario` allows lowercase letters and underscores. There are no implicit missing values. Numeric fields accept only ASCII decimal literals with optional sign and scientific exponent; `NaN`, `Inf`, arithmetic expressions and localized decimal separators are explicitly rejected.

| Field | Unit | Meaning |
|---|---|---|
| Pabs, Pamb, Pref, Pmin, Pmax | Pa absolute | Upstream, ambient, reference, minimum consumer, maximum upstream pressures |
| Tin | K | Upstream absolute air temperature |
| area | mm2 | Effective leak orifice area |
| Cd | 1 | Effective discharge coefficient |
| gamma | 1 | Isentropic specific-heat ratio |
| Rgas | J/(kg K) | Specific gas constant |
| mref | kg/s | Synthetic mass-flow reference |
| exponent | 1 | Empirical pressure-law exponent |
| demand, supplyCap | kg/s | Useful consumption and maximum compressor flow |
| kdrop | Pa/(kg/s)^2 | Quadratic lumped pressure loss parameter |
| eta | 1 | Combined assumed compressor efficiency |
| cp | J/(kg K) | Assumed constant heat capacity |
| hours | h/year | Illustrative annual operating hours |
| price | USD/kWh | Illustrative electricity tariff |
| maxFraction | 1 | Upper limit of leakage share |

Domain checks are performed in C++ **before any graph invocation**. `paceval_dConvertStringToFloat` parses validated input numbers and `paceval_dConvertFloatToString` generates output numeric text. The latter does not imply bitwise lossless roundtrip, so archived source values are separately hashed. The output files `screening.csv`, `model_comparison.csv`, `native_audit.csv`, `formula_manifest.csv` and `math_execution_inventory.csv` have fixed headers inspectable by an independent CSV parser. All sizes and denominators are validated for positivity. Incorrect field counts or unsafe numeric tokens terminate the run with an error, not a silent fallback.
