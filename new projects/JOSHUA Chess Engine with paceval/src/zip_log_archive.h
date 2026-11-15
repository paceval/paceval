#pragma once
// ZIP-format DEFLATE compression for closed JOSHUA game directories.
// This code writes ZIP32 with UTF-8 names and streaming zlib. It does not
// depend on /usr/bin/zip, Python, or proprietary paceval APIs.
#include <cstdint>
#include <filesystem>
#include <string>
namespace joshua_zip {
namespace fs = std::filesystem;
struct ArchiveResult {std::uint64_t compressed_bytes = 0; std::uint64_t source_bytes = 0; std::size_t files = 0;};
ArchiveResult zipDirectoryAtomically(const fs::path& gameDirectory, const fs::path& finalZip);
std::uint64_t directorySize(const fs::path& directory);
std::uint64_t allocatedBytes(const fs::path& file);
std::uint64_t pruneArchives(const fs::path& archives, std::uint64_t budgetBytes,
                            std::size_t* deleted = nullptr);
}
