# Reproducing the industrial paceval MCP mathematical model demonstrator

This document distinguishes three kinds of evidence: **remote MCP calls actually executed during the present research session**, **original local paceval SDK calls rerunnable from C++**, and **results of the 16,384-component predecessor study reported in the supplied original PDF**. Never describe historical predecessor evidence as a new run.

## Local reproduction

The archive contains `src/paceval_main.cpp` and `src/paceval_main.h` from original paceval SDK 4.25. The C++ file's relative SDK include has been minimally adapted for the directory layout, without replacing the engine. Supply an ABI-compatible Linux shared library outside the repository. Run the README's CMake commands. All 22 graph registrations and 520 cases are exercised by the real paceval API. Output fields are generated through multi-graph batch evaluation, with graph-major output layout checked by the independent reference.

To regenerate inputs and expressions, call `python3 src/model_generator.py`. The coefficient serialisation explicitly emulates JavaScript's `Number.toFixed` rounding, so remote and local model text match on half-way decimal cases. Confirm the SHA-256 manifest with `python3 src/verify_manifest.py .`. The main generator does not require network access.

Run `python3 src/independent_reference.py .` for all scenario output checks and the 80-decimal-place independent oracle. Run `python3 src/verify_live_mcp.py .` to check the previously observed live MCP numerical records. These Python checks are **not new MCP calls**. Figures are produced with `python3 src/make_figures.py .` from recorded outputs.

## Repeating remote MCP calls with a tool-capable AI agent

The user must enable a permitted client connection to `https://mcp.paceval-service.com/mcp` (Streamable HTTP). Discover actual tool names; clients can expose different names. The relevant operations observed in this session were `paceval_create_computation`, `paceval_evaluate_many`, and `paceval_evaluate_multiple_many`.

1. Use a small smoke test expression `x*x+sin(y)` with variable order `x,y`, then evaluate sets `[[2,0],[3,0]]` and check expected results 4 and 9.
2. Regenerate `generated/field_v1.txt` and `generated/field_v2.txt` with `python3 src/model_generator.py`; submit their exact content as two distinct expressions with variable order `x,y,z,temp`. Record new opaque handles.
3. Supply the 16 vectors recorded in `results/live_mcp_main_batch.json` to `paceval_evaluate_multiple_many`. Verify graph-major output orientation and error numbers. Compare the results against the newly computed independent reference, not against model intuition.
4. Register the eight files `generated/modular_block_01_v2.txt` through `modular_block_08_v2.txt`, all with identical `x,y,z,temp` ordering. Evaluate the four vectors in `results/live_mcp_modular_batch.json`, sum modular contributions by record and compare against the new monolithic version-2 handle.
5. Create eight second-stage graphs from the corresponding `generated/*.txt` files, using input order `v1,v2,x,y,z,temp,target,tol,raw`. Supply the first-stage output values as the first two variables. Evaluate the 16 sets through one multi-computation batch and validate output ordering. The source-specified example target is 0.16 and tolerance is 0.03, both dimensionless and synthetic.
6. Record service version, formula SHA-256, input values, error codes, and independently verified output values. Do not assume the old opaque handles remain valid.

The archive contains observed MCP output records, but not a package that can authenticate to or call a third-party MCP service without prior user connection and permission. No service-side authentication or reliability guarantee is implied.

## Licensing, publication and scientific limits

The SDK files carry their upstream AGPL and copyright headers. Review obligations before public redistribution. The external runtime is intentionally excluded. Machine readings, reference instruments, physical units of correction, approval authority, production actuator control and a safety assessment are **not** covered by this synthetic feasibility experiment.
