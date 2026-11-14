# SDK compatibility and provenance

The project uses the original user-supplied `paceval_main.h` and `paceval_main.cpp` version 4.25 (original AGPL license headers preserved). The only required change in `paceval_main.cpp` is a relative header include path for the package's `src/` layout.

The tested Linux runtime is an external x86-64 ELF shared library. Build it separately or supply the matching library path via `-DPACEVAL_RUNTIME=...`. The `.so` is intentionally excluded from the GitHub archive. This package contains no substitute implementation of the paceval engine.

The direct C++ API and its FFI wrapper names must not be conflated. Source declarations were checked against the supplied header and the runtime symbols. Multi-graph call success is judged using the observed return status plus per-output item error codes and a known two-graph layout probe. Release results represent only the local Linux SDK path, not paceval MCP execution.
