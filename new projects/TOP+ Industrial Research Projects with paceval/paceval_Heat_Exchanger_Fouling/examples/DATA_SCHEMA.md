# Numerical CSV schema

`synthetic_corner_scenarios.csv` has exactly 19 columns: the case identifier followed by 18 parameter columns in the same order as the formula manifest and original paceval execution graph declarations.

- Encoding: UTF-8, comma-separated fields, dot decimal separator, no thousands separators or units inside numeric cells.
- Numerical fields: finite signed decimal literal with optional scientific exponent. No math expressions, names, quotes, blanks, `NaN`, `Inf`, hexadecimal literals or locale-dependent numbers.
- `case_id`: ASCII letters, digits, underscore and hyphen; 1 to 48 characters.
- Units: `Th,Tc` °C; `Ch,Cc` W/K; `Uc` W/m²/K; `A` m²; `Rf,Rremain` m² K/W; `Fc` dimensionless; `D1,D2,Approach` K; `Qtarget` W; `H` h; `Price` EUR/kWh; `Cclean` EUR; `DeltaP,DeltaPmax` Pa.
- Missing data: explicitly rejected, never silently imputed.
- Scientific interpretation: all rows synthetic, with deterministic enumerated levels. Not plant measurement data.
- Exact numeric archive: native binary values are not preserved by the printed remote output; re-read the stored input decimal under the declared parse rules and preserve a binary copy in any future regulated or byte-exact archival study.
