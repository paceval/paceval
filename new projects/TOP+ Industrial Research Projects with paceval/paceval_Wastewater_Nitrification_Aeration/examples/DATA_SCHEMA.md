# Research CSV schema

Canonical UTF-8 comma-separated CSV, dot decimal, no empty numeric fields, finite decimal literals only. The first column `case_id` is a safe identifier. Subsequent columns follow the declared paceval graph variable list in the exact order.

Input variables and units: `NH4` mg NH4-N/L; `DO` mg O2/L; `Xn` mg VSS/L; `muN` 1/h; `YN` mg VSS per mg N; `KN` mg N/L; `KO` mg O2/L; `tau` h; `aN` mg O2 per mg N (synthetic oxygen stoichiometry); `bX` mg O2/(mg VSS h); `alphaO2` kg O2/kWh electric; `Vol` m3; `Temp`,`Tref` Celsius, temperature *difference* in K; `theta` dimensionless 1/K growth factor base; `KI` mg N/L; `KL` 1/h; `DOsat` mg O2/L; `Nlimit` mg N/L; `DOmin` mg O2/L; `Pmax` kW; `Q` m3/h; `Price` currency/kWh; `Hours` h.

Allowed domains: NH4 >= 0, DO >= 0, Xn >= 0, muN >= 0, YN > 0, KN > 0, KO > 0, tau > 0, KI > 0, alphaO2 > 0, Vol > 0, 0.5 <= theta <= 1.5, -5 <= Temp <= 45, KL >= 0, DOsat > DO, Nlimit >= 0, DOmin >= 0, Pmax > 0, Hours >= 0, Price >= 0. Program additionally rejects nonfinite values, dangerous overflows and unrecognized field counts.

`results/mcp_*observations.csv` are selected **printed decimal transcriptions** of real remote MCP responses; they are not local SDK CSVs and not bit-exact binary snapshots. `results/local_sdk_*.csv` will only be created by a successful local paceval runtime execution. The C++ SDK source calls `paceval_dConvertStringToFloat` after strict literal validation and `paceval_dConvertFloatToString` for numeric output.
