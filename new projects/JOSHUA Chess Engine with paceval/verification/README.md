# V6 exact validation footprint

This release ships *no newly executed original paceval result*. The original Linux shared library was absent on the build host. The three compiled ELF programs and the original project code are present.

The manager-only tests and the eight-ply fixture replay are process, legality and result-schema checks. They do not call paceval locally and do not measure chess strength. See `../V6_RELEASE_VALIDATION.md` for a full description, and `sha256_executables.txt` for exact ELF file checksums.
