// Independent original SDK decimal CSV conversion self-test. Not yet executed.
#include "paceval_main.h"
#include <regex>
#include <string>
#include <cmath>
#include <iostream>
#include <array>
static bool safe(const std::string& s){
 static const std::regex r(R"(^[+-]?(?:[0-9]+(?:\.[0-9]*)?|\.[0-9]+)(?:[eE][+-]?[0-9]+)?$)");
 return s.size()<=80 && std::regex_match(s,r);
}
int main(){
 if(!paceval_InitializeLibrary(nullptr))return 1;
 bool ok=true;
 for(const char* s:{"0","-2.25","3.0e-12","5.25e+7",".5"}){
  if(!safe(s)){ok=false;break;}
  int err=-1;long at=-1;double lo=0,hi=0;
  double v=paceval_dConvertStringToFloat(s,&err,&at,false,&lo,&hi);
  std::array<char,4096> buf{};
  const int digits=paceval_dConvertFloatToString(buf.data(),v);
  ok=ok&&(err==0&&std::isfinite(v)&&digits>0&&safe(buf.data()));
 }
 for(const char* s:{"","1+2","NaN","Inf","0x10","1e99999","3,14"," 2"})ok=ok&&!safe(s);
 if(!paceval_FreeLibrary())ok=false;
 std::cout<<(ok?"Conversion/schema PASS":"Conversion/schema FAIL")<<'\n';return ok?0:2;
}
