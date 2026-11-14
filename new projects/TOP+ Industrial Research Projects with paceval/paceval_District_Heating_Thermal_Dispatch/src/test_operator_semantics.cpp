// Independent original SDK operator semantics self-test. Not yet executed.
#include "paceval_main.h"
#include <cmath>
#include <iostream>
int main(){
 if(!paceval_InitializeLibrary(nullptr))return 1;
 struct Case {const char* expression;double expected;};
 const Case cases[]={{"(-1) % 10",-1},{"(-1) mod 10",9},
  {"4 min 5",4},{"4 max 5",5},
  {"((x <= (2*y)) AND (z >= 0))",1},
  {"((NOT(x = y)) OR (z <> 0))",0},
  {"((x = y) XOR (z <> 0))",1}};
 bool ok=true;double values[]={1,1,0};
 for(const auto& c:cases){
  PACEVAL_HANDLE h=paceval_CreateComputation(c.expression,3,"x y z",false,nullptr);
  if(!h || paceval_GetIsError(h)){ok=false;continue;}
  double actual=paceval_dGetComputationResult(h,values,nullptr,nullptr);
  ok=ok&&!paceval_GetIsError(h)&&actual==c.expected;
  paceval_DeleteComputation(h);
 }
 if(!paceval_FreeLibrary())ok=false;
 std::cout<<(ok?"Operator semantics PASS":"Operator semantics FAIL")<<'\n';return ok?0:2;
}
