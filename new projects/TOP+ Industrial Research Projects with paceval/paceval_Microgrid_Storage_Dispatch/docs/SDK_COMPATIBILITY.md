# Original paceval 4.25 SDK and actual Linux integration

This build uses the user-supplied original SDK sources dated 14 November 2026. The `src/paceval_main.h` file is byte-for-byte identical to the supplied header. The file `src/paceval_main.cpp` is byte-identical except for the minimal include path adjustment `../source_public/inc/paceval_main.h` to `paceval_main.h`. Copyright and AGPL notices are retained.

The user-supplied compatible runtime is an x86-64 ELF shared object with exported `pacevalLibrary_CreateComputation` and `pacevalLibrary_dGetMultipleComputationsResultsExt` symbols. The binary is **not** included in the published ZIP. The public wrapper `paceval_CreateComputation` and compiled `paceval_main.cpp` call into the original shared runtime, while `paceval_dGetComputationResult` and `paceval_dGetMultipleComputationsResultsExt` execute the mathematical functions.

Actual scalar results, multi-graph batch layout, error types, the observed boolean return convention, converter functions and parser operator syntax were confirmed against the supplied SDK by executing an automated CTest case. For this tested version, the multi-graph call returns `false` with `errorTypes_out == 0` on success; this is an observed SDK-specific behavior, not an assumption that applies to all APIs or future versions. The result-memory ordering is established with a deterministic numeric probe, not guessed.

All analytical model graphs are registered once and reused. Each production batch input row is a dense array of validated finite double values with consistent variable ordering. Returned nonfinite values or nonzero item errors cause the program to fail, rather than silently produce default values. The graph output CSV is formatted using the original `paceval_dConvertFloatToString` converter. The input CSV uses a strict decimal-literal grammar before calling original `paceval_dConvertStringToFloat`, because that API can also evaluate formula expressions and is not alone a safe general CSV literal parser.

TINC is not claimed in this project: robust interval certification would require separately defined uncertain parameter ranges, an interval arithmetic design and independent inclusion tests. The current reported outcomes are pointwise double-precision evaluations with independent numerical verification.

Original API: https://paceval.com/api/ . Product brief: https://paceval.com/product-brief/ .
