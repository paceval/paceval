# Original SDK and library compatibility evidence

The compiled research package uses the original user-supplied `paceval_main.h` and `paceval_main.cpp` version 4.25. The source C++ wrapper was changed only to include `"paceval_main.h"` from the current `src/` directory instead of the original upstream relative include path. Both source files preserve their original copyright and AGPL notices.

The compatible **external** runtime used in the actual Linux execution was `libpaceval_linux_sharedLIB(6).so`, an ELF64 x86-64 shared object. The runtime file SHA-256 fingerprint is:

`acf63a87df0ee822b467edbca887393d31ec0ea03562e1abf802d2512a5bfb12`

The live ELF symbol check confirmed the corresponding `pacevalLibrary_Initialize`, `pacevalLibrary_CreateComputation`, `pacevalLibrary_dGetMultipleComputationsResultsExt`, `pacevalLibrary_dConvertStringToFloat`, and `pacevalLibrary_dConvertFloatToString` symbols. The source wrapper maps the application-facing `paceval_*` methods to these original library entry points. It is therefore not a simulated or reimplemented paceval engine. Actual successful CMake compilation, CTest and execution provide the integration evidence.

**For reproducibility:** a compatible original Linux library is needed locally at build and run time, and is NOT distributed in this GitHub ZIP. The supplied filename with `(6)` was an uploaded-file disambiguation name, not an official runtime distribution version. The SDK header version is 4.25 and should not be conflated with the `(6)` suffix.
