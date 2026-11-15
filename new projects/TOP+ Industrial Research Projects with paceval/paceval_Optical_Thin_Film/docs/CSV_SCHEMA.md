# CSV schema and serialization contract

All CSVs use a comma as separator, period decimal point and UTF-8; no spreadsheet formula interpretation is allowed. The reader rejects values not matching a constrained finite numeric literal grammar and then calls the original `paceval_dConvertStringToFloat`. Numeric output uses `paceval_dConvertFloatToString`. **The output textual representation is not assumed to roundtrip all IEEE-754 doubles bit-for-bit.** Exact binary inputs for independent mpmath reference are obtained from the decoded numeric representation.

| Input column | Type and unit | Permitted domain or semantics |
|---|---|---|
| `site_id` | Identifier | `S` and four digits |
| `pixel_x`, `pixel_y` | integer, dimensionless | 0 to 11 each |
| `true_nm` | double, nm | greater than 80 and less than 460 |
| `alpha_per_nm` | double, 1/nm | positive effective absorption parameter |
| `film_n` | double, dimensionless | 1.1 to 1.9 |
| `substrate_n` | double, dimensionless | 1.4 to 2.0 |
| `offset` | double, normalized intensity | 0 to 0.1 |
| `wavelength_nm` | double, nm | 390 to 800 |
| `noise_t` | double, normalized transmission | magnitude less than 0.002 |
| `noise_r` | double, normalized reflectance | magnitude less than 0.001 |

Input rows are grouped in nine sorted wavelengths per site. `results/spectral_samples.csv` contains actual paceval forward outputs, observed synthetic responses, analytical Beer inverses and real Fresnel derivatives. `results/site_summary.csv` contains final fitted thicknesses, objective values and host decisions. `results/objective_profiles.csv`, `results/alias_case.csv` and `results/alias_curve.csv` expose exactly the evidence behind the inverse-search diagrams. `results/math_execution_inventory.csv` records each graph and execution owner.

For byte-level reproduction, the input generator uses seed 20261115 and the same specified Python interpreter. Separate full project re-execution can be checked with file hashes on the generated outputs. Interpret CSV rounded text as a scientific reporting format and retain the original source for high-integrity studies.
