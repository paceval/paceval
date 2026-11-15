// SDK-independent exhaustive checks for the deterministic exploration policy.
#include "selfplay_exploration.h"
#include <cassert>
#include <iostream>
#include <vector>
#include <set>
int main(){
 const std::vector<double> white={50.0,49.0,35.0,-10.0};
 std::set<std::size_t> chosen;
 for(std::uint64_t seed=101;seed<117;seed++){
   const auto x=joshua_explore::choose(white,1,"start w - - 0 1",2,20.0,14,seed);
   assert(x.index<3 && x.eligible==3 && x.regretCp>=0 && x.regretCp<=20.0);
   chosen.insert(x.index);
   const auto copy=joshua_explore::choose(white,1,"start w - - 0 1",2,20.0,14,seed);
   assert(copy.index==x.index);
 }
 assert(chosen.size()==3);
 assert(joshua_explore::choose(white,1,"x",15,20.0,14,99).index==0);
 assert(joshua_explore::choose(white,1,"x",1,0.0,14,99).index==0);
 const std::vector<double> black={-50,-49,-35,10};
 chosen.clear();for(std::uint64_t seed=21;seed<27;seed++){
   auto x=joshua_explore::choose(black,-1,"x b - - 0 1",3,20.0,14,seed);
   assert(x.index<3&&x.regretCp<=20.0);chosen.insert(x.index);
 }
 assert(chosen.size()==3);
 assert(joshua_explore::choose(std::vector<double>{25,3},1,"x",2,10,14,99).index==0);
 std::cout<<"V8_EXPLORATION_POLICY_TEST_PASS reproducible nearbest white_black seed_rotation bounds\n";
}
