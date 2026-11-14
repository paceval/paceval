# Original paceval SDK integration

**Original C/C++ SDK version:** paceval_mainVersionString `4`, paceval_subVersionString `25`, as declared in `src/paceval_main.h` supplied by the user on 14 November 2026. The original `paceval_main.cpp` was copied with only the include path changed to `#include "paceval_main.h"` to suit the required in-project `src/` layout. Original header/license notices are preserved.

**External runtime tested:** User-supplied ELF x86-64 `libpaceval_linux_sharedLIB(6).so`. It is linked as an *external imported shared library* using `-DPACEVAL_RUNTIME=...`; the file itself is intentionally excluded from the release package. Some exported runtime function names include `pacevalLibrary_` as the FFI layer; application code uses the official public SDK functions, which are forwarded through the original source file.

**Verified calls:** `paceval_InitializeLibrary`, `paceval_CreateComputation`, `paceval_dGetComputationResult`, `paceval_dGetMultipleComputationsResultsExt`, `paceval_dConvertFloatToString`, `paceval_dConvertStringToFloat`, `paceval_GetIsError`, `paceval_DeleteComputation`, `paceval_FreeLibrary`. The numerical layout probe distinguishes graph-major and point-major result arrangements, rather than assuming one without a test. Every multi-result error slot is checked.

**Availability and boundaries:** No long-double code path is assumed, no replacement engine is included, and no claim about compatibility with another ABI is made. TINC has not been used to certify interval domains. The source code does not silently treat masks as domain guards; physical domains are checked in the host.
