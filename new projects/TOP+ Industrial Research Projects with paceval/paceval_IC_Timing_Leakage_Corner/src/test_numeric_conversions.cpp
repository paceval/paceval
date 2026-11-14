// Exercised only when original ABI-compatible SDK runtime is available.
// This is deliberately separate from syntax-only compilation or MCP evidence.
#include "paceval_main.h"
#include <algorithm>
#include <array>
#include <cmath>
#include <regex>
#include <stdexcept>
#include <string>

namespace {
bool numericalLiteral(const std::string& x){
 static const std::regex pattern(R"(^[+-]?(?:[0-9]+(?:\.[0-9]*)?|\.[0-9]+)(?:[eE][+-]?[0-9]+)?$)");
 return std::regex_match(x,pattern);
}
}
void runDedicatedNumericConverterTest(){
 for(const char* c:{"0","-0.0","+.5","1e-10","5E+22","-8.25","3."}){
  std::string s(c);if(!numericalLiteral(s))throw std::runtime_error("Safe decimal literal rejected");
  int err=-1;long pos=-1;double lo=0,hi=0;
  const double v=paceval_dConvertStringToFloat(c,&err,&pos,false,&lo,&hi);
  if(err!=0 || !std::isfinite(v))throw std::runtime_error("Original paceval string to double conversion failed");
  std::array<char,4096> buf{};
  const int digits=paceval_dConvertFloatToString(buf.data(),v);
  const auto end=std::find(buf.begin(),buf.end(),'\0');
  if(digits<=0 || end==buf.begin() || end==buf.end())throw std::runtime_error("Original paceval double to string failure");
  if(!numericalLiteral(std::string(buf.begin(),end)))throw std::runtime_error("Noncanonical output from original converter");
  // Do not assume roundtrip binary equality; exact binary64 is audited separately.
 }
 for(const char* c:{"1+2","2*pi","NaN","Inf","1,500",""," 3","0xA","1e9999"}){
  // Safety barrier MUST reject before the expression-capable SDK conversion.
  if(numericalLiteral(c)){
   // Overflow literals may pass lexical filtering but must be rejected once the
   // SDK reports an error/nonfinite value.
   int err=-1;long pos=-1;double lo=0,hi=0;
   double v=paceval_dConvertStringToFloat(c,&err,&pos,false,&lo,&hi);
   if(err==0&&std::isfinite(v))throw std::runtime_error("Oversized exponent unexpectedly accepted");
  }
 }
}
