# Scientific CSV schema

Input files: `synthetic_sensor_snapshots.csv` and `synthetic_state_grid.csv`. Canonical UTF-8, comma delimiters, decimal dot, numeric fields only. The first field `time_h` has units h and is just a snapshot label. The next 18 fields are exactly the paceval variables in the original graph declaration order. No external measurements are claimed.

| Column | Unit | Range for demonstrator | Meaning |
|---|---|---|---|
| S | g substrate/L | 0 to 100 | substrate concentration |
| DO | g O2/L | [0, DOstar) | dissolved oxygen concentration |
| X | g dry biomass/L | 0 to 100 | dry biomass |
| umax | 1/h | positive to 20 | maximum growth parameter |
| Ks | g substrate/L | positive | half-saturation parameter |
| Ko | g O2/L | positive | oxygen half saturation |
| Ki | g substrate/L | positive | substrate inhibition parameter |
| Yxs | g biomass/g substrate | (0, 10] | substrate conversion yield |
| qO2 | g O2/(g biomass·h) | nonnegative | baseline cell-specific uptake |
| qG | g O2/g biomass | nonnegative | growth-linked uptake coefficient |
| kLa | 1/h | (0, 10000] | volumetric transfer coefficient |
| DOstar | g O2/L | (0, 1] | saturated DO input |
| F | L/h | nonnegative | fresh-feed flow |
| V | L | positive | current volume |
| Sfeed | g substrate/L | nonnegative | incoming substrate concentration |
| DOmin | g O2/L | [0,DOstar) | illustrative DO limit |
| tau | h | positive | score conversion horizon |
| OURcap | g O2/L/h | nonnegative | reserved parameter for future guard version |

The `OURcap` field is intentionally reserved and not used in the verified formulas. The host does not pretend that a graph uses it. `DOstar-DO` greater than 1e-9 protects the required-kLa division. Actual input domain rules are enforced in `src/biomanufacturing_pat.cpp`.
