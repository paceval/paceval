# Synthetic input CSV contract

Both input files use UTF-8, one comma delimiter, a period as decimal separator, one unique `case_id` and 23 numeric literal columns in the exact order of `src/generated_formulas.h`. The C++ loader rejects empty cells, expressions, NaN/Infinity, mismatched column counts and invalid domains **before** calling the original SDK `paceval_dConvertStringToFloat`. No confidential plant data occur.

Units: `Q` m^3/s, `T` K, `rA`/`rB` and `LA`/`LB` m, `K` Pa s^n, `n` dimensionless in (0,1], `E` J/mol, `Rg` J/(mol K), `Tref` K, `etaZero` Pa s, `tauStar` Pa, `MachineMax` and `CavityReq` Pa, `ShearMax` 1/s, `Tmin`/`Tmax` K, `Pheater`/`Pinject` W, `Theat`/`Tinject` s, `Emax` J. The selected data are illustrative values, not calibrated properties of a named polymer. No injection-machine or material claim is made.

Physical scope: straight, isothermal, steady, fully developed, circular laminar conduit segments with an ideal power-law fluid and a constant reference cavity pressure. Entry, fountain flow, gate contraction, 3D cavity flow, compressibility and solidification are intentionally not simulated. The Cross-Arrhenius curve is a diagnostic rheology proxy and is not a measured Cross-WLF card.
