#pragma once
// Deterministic, auditable exploration for independent self-play experiments.
// Input scores come from the genuine paceval-backed JOSHUA evaluation.
// This file ONLY applies an optional host-side selection policy to those scores.
// It is NOT a learning algorithm, a random number service, or a paceval replacement.
#include <algorithm>
#include <cmath>
#include <cstdint>
#include <string>
#include <vector>
namespace joshua_explore {
struct Choice {std::size_t index=0;std::size_t eligible=1;double regretCp=0.0;};
// Stable FNV-1a: never use std::hash for reproducibility across processes.
inline std::uint64_t stableHash(const std::string &text){
 std::uint64_t h=14695981039346656037ull;
 for(unsigned char c:text){h^=c;h*=1099511628211ull;}return h;
}
inline Choice choose(const std::vector<double>&sortedWhiteScores, int sideToMove,
                     const std::string&positionFen, int ply,
                     double nearBestCp, int explorationPlies, std::uint64_t seed){
 Choice result;
 if(sortedWhiteScores.empty() || (sideToMove!=1 && sideToMove!=-1))return result;
 if(ply<1||ply>explorationPlies||nearBestCp<=0.0 || !std::isfinite(nearBestCp))return result;
 const double best=sortedWhiteScores.front();if(!std::isfinite(best))return result;
 std::size_t eligible=0;
 for(double score:sortedWhiteScores){
   if(!std::isfinite(score))break;
   const double loss=(sideToMove==1?best-score:score-best);
   if(loss<-1e-7 || loss>nearBestCp+1e-7)break;
   ++eligible;
 }
 result.eligible=std::max(std::size_t(1),eligible);
 if(eligible<2)return result;
 // Consecutive game seeds visit different candidates when the position and
 // candidate set match; no global PRNG state or non-reproducible entropy.
 const std::uint64_t h=stableHash(positionFen) ^ (std::uint64_t(unsigned(ply))*0x9e3779b97f4a7c15ull);
 result.index=std::size_t((seed+(h%eligible))%eligible);
 const double selected=sortedWhiteScores[result.index];
 result.regretCp=std::max(0.0,sideToMove==1?best-selected:selected-best);
 return result;
}
} // namespace joshua_explore
