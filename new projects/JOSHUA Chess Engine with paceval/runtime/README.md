# Original paceval Linux x86-64 runtime location

Copy the compatible **original** `libpaceval_linux_sharedLIB.so` from a legally authorized paceval SDK installation to this directory. It was **not present** in the supplied Joshua ZIP or the available local environment and is **not distributed** in this public GitHub package. `paceval_main.h` and `paceval_main.cpp` remain the original SDK interface files under `src/`.

The optional dynamic forwarding adapter `src/paceval_runtime_loader.cpp` calls real `pacevalLibrary_*` exports. It cannot compute a chess evaluation without the authentic SDK runtime. It is not a substitute engine.

You may alternatively set `PACEVAL_RUNTIME=/absolute/path/to/libpaceval_linux_sharedLIB.so` when launching Joshua. Follow the original paceval licensing terms for any redistribution, deployment or commercial use. The developer SDK is described as non-commercial-use-only at the upstream website. Confirm permissions before publishing the shared object in a public repository.

Official information: https://paceval.com/product-demo/
