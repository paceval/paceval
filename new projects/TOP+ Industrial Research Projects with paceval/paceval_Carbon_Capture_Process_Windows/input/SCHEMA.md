# Operating point CSV schema

UTF-8, comma-separated values, dot decimal separator, LF line endings. Each record has a string `case_id`, a string `scenario` and nineteen finite decimal numeric literals in this exact order:

| Field | Unit | Domain / interpretation |
|---|---|---|
| Fin | mol CO2/s | Strictly positive inlet CO2 |
| Fgas | mol gas/s | Greater than Fin; total flue-gas molar flow |
| Kla | 1/s | Positive volumetric mass-transfer coefficient |
| Vol | m3 | Positive effective contact volume |
| Cstar, Cbulk | mol/m3 | Cstar greater than Cbulk greater or equal to zero |
| S | mol amine/s | Positive molecular amine circulation |
| lean, maxload | mol CO2/mol amine | 0 <= lean < maxload <= 0.65 |
| Tstrip, Tfeed | K | 360 <= Tstrip <= 440; Tfeed >= 270; Tstrip > Tfeed |
| cp | kJ/(kg K) | Positive representative solution heat capacity |
| hx | fraction | 0 <= hx < 0.94 |
| wt | fraction | 0 < wt <= 1; amine mass fraction |
| dh, hvap | kJ/mol CO2 | Positive desorption and nonnegative overhead heat contribution |
| etaMin | fraction | 0 < etaMin < 1; lower capture target |
| qMax | GJ/tCO2 | Positive thermal-specific-duty cap |
| tMax | K | At least 360; stripper upper temperature |

Non-numeric texts, empty numeric fields, expression-like values such as `2+3`, non-finite tokens, inconsistent field counts and negative or singular domains are rejected before graph evaluation. `paceval_dConvertStringToFloat` handles validated decimal fields and `paceval_dConvertFloatToString` formats exported float data. The supplied values are synthetic research inputs, not experimental solvent measurements.
