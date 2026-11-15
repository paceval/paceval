# Original paceval runtime (not included)

Use your existing authorized Linux x86-64 `libpaceval_linux_sharedLIB.so`. Place it next to flat-deployed `joshua` or in this `runtime/` folder for GitHub checkouts, or set the absolute `PACEVAL_RUNTIME` environment variable. The public GitHub ZIP excludes the proprietary runtime; the C++ API and loader are not substitutes for it. Stockfish must be installed separately. The repository contains no reimplementation of the paceval engine. Check the original SDK license before redistribution.
