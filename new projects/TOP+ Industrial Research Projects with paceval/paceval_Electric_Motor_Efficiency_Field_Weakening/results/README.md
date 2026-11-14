# Generated original research results

`screening.csv` and `model_comparison.csv` contain the complete actual paceval CSV results. `torque_speed_envelope.csv` and `efficiency_recommended.csv` are derived by C++ finite-set selection from the original paceval outputs, with no native motor formula substitution. `formula_manifest.csv` lists actual registered expressions. `math_execution_inventory.csv` identifies function owners and executed paths. `execution_evidence.json` counts graph creation/execution, scenario versions, API batch calls, per-item evaluations and native reference checks.

`native_audit.csv` is the separate native C++ reference trace. `scientific_audit.json` and `high_precision_audit.csv` come from `scripts/verify_high_precision.py` using 90 decimal digits on the recorded original computation outputs. No audit field is claimed as a fresh paceval result.

All data are synthetic model outputs, not machine measurements, and have no manufacturing, automotive functional-safety or operational certification status.
