# Data provenance and reproduction

The `mcp_observed_*.csv` files are **literal transcriptions of actual remote paceval MCP 4.26 responses** produced for this study, not an unmodified wire-format export. The independent files are generated from a separately implemented mathematical reference and must **not** be treated as MCP output. The full 30 x 147 graph-point response was checked for reported errors in the remote execution but not saved as a complete raw dump; selected axis values and all 49 aggregate scenarios were archived here.

The model grid, quaternion inputs, formula IDs, remote evaluation totals, scientific assumptions, TINC outcomes (including errors 144) and local execution limitations are specified in JSON and code. All datasets are synthetic. For the actual local SDK numerical output, build and execute `src/satellite_attitude_paceval.cpp` with the original matching shared library, which is not included in this archive.
