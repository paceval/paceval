# Canonical CSV schema and source provenance

`input/cases.csv` contains `case_id` (`CASE#####`), `scenario` (`normal`, `humid`, `hot`, `short_residence`) followed by exactly 24 numeric columns in this order:

`solid,water,baseMoist,Tair,Tin,Tref,time,kref,Ea,RH,eqBase,eqRH,eqTC,hcoef,latentCool,fastFraction,spread,rtdWidth,Mmin,Mmax,Tmax,sensor,sensorTol,target`

Units respectively: kg/h, kg/h, kg/kg dry, K, K, K, s, 1/s, J/mol, unit fraction, kg/kg dry, kg/kg dry, 1/K, 1/s, K/(kg/kg dry), unit fraction, unit fraction, unit fraction, kg/kg wet, kg/kg wet, K, kg/kg wet, kg/kg wet, kg/kg wet.

All numeric cells must be finite dot-decimal literals with optional signed exponents, never mathematical expressions. Comma is **only** a column delimiter; text fields are limited to named safe ASCII identifiers. A strict regex rejects `NaN`, `Inf`, `1+2`, comma decimals, blank cells, unit suffixes and extraneous whitespace. After lexical validation the exact original paceval `paceval_dConvertStringToFloat` API is used. Every numeric result emitted by C++ uses `paceval_dConvertFloatToString`; its text precision is independently checked, with the original input CSV SHA-256 recorded in `results/high_precision_audit.json`.

The [screening output](../results/screening.csv) stores one record per model/scenario and explicitly labels wet-basis and dry-basis moisture. The [comparison output](../results/model_comparison.csv) contains version deltas computed by paceval itself. The [full manifest](../results/formula_manifest.csv) preserves the exact original SDK expression strings; [execution evidence](../results/execution_evidence.json) contains counts and test information. The [numerical audit](../results/high_precision_audit.json) is technical verification, not a clinical or quality-system record.

Input generated with deterministic Python seed `20261115`. The actual study dataset has 2,880 scenarios. Values are synthetic and do not originate from any pharmaceutical company, published experimental material dataset or calibrated real-time sensor.
