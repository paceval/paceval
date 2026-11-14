// Separate real paceval operator boundary/regression tests.
// The SDK must be initialized by the calling executable before this runs.
#include "paceval_main.h"
#include <stdexcept>
#include <string>

void runDedicatedOperatorSemanticsTest(){
 struct Case{const char* formula;double x,y,z,expected;};
 const Case cases[]={
  {"(-1) % 10",1,1,0,-1}, {"(-1) mod 10",1,1,0,9},
  {"4 min 5",1,1,0,4}, {"4 max 5",1,1,0,5},
  {"((x<=2*y) AND (z>=0))",1,1,0,1},
  {"((x<=2*y) AND (z>=0))",2,1,-1,0},
  {"((NOT(x=y)) OR (z<>0))",1,1,0,0},
  {"((NOT(x=y)) OR (z<>0))",2,1,-1,1},
  {"((x=y) XOR (z<>0))",1,1,0,1},
  {"((x=y) XOR (z<>0))",2,1,-1,1}
 };
 for(const auto& c:cases){
  PACEVAL_HANDLE h=paceval_CreateComputation(c.formula,3,"x y z",false,nullptr);
  if(!h||paceval_GetIsError(h))throw std::runtime_error("Operator graph registration failed");
  double args[]={c.x,c.y,c.z};double got=paceval_dGetComputationResult(h,args,nullptr,nullptr);
  bool good=!paceval_GetIsError(h)&&got==c.expected;
  paceval_DeleteComputation(h);
  if(!good)throw std::runtime_error(std::string("Operator semantics unexpected: ")+c.formula);
 }
}
