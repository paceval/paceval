// Independently reproducible industrial additive-manufacturing thermal-window demonstrator.
// Uses ORIGINAL paceval SDK 4.x. The host validates I/O, owns graph lifetime and decisions.
// The mathematical core, composite process-window margins and flags execute via real paceval graphs.
// NOT a verified physical LPBF solver, defect predictor or industrial machine controller.
#include "paceval_main.h"
#include "generated_formulas.h"
#include <array>
#include <cmath>
#include <cstring>
#include <cstdlib>
#include <fstream>
#include <iostream>
#include <limits>
#include <stdexcept>
#include <string>
#include <vector>
#include <sstream>
#include <regex>
#include <algorithm>

namespace {
constexpr size_t V=18;
constexpr size_t G=kGraphs.size();
constexpr const char* Names="P v k rho cp eta T0 r0 Tliq Tvap beta gamma xs ys zs xd yd zd";
constexpr const char* CsvHeader="P,v,k,rho,cp,eta,T0,r0,Tliq,Tvap,beta,gamma,xs,ys,zs,xd,yd,zd";
using Row=std::array<double,V>;
struct Graphs {
  std::vector<PACEVAL_HANDLE> handles;
  ~Graphs(){for(auto h:handles) if(h) paceval_DeleteComputation(h);}
};
void insist(bool condition,const std::string& reason){if(!condition) throw std::runtime_error(reason);}
// Strict grammar prevents paceval's expression-capable string converter from evaluating CSV formulas.
bool isDecimalLiteral(const std::string& text){
  static const std::regex pattern(R"(^[+-]?(?:[0-9]+(?:\.[0-9]*)?|\.[0-9]+)(?:[eE][+-]?[0-9]+)?$)");
  return std::regex_match(text,pattern);
}
// SDK converter is the real parser for numeric scientific data, after a literal-only guard.
double parseNumeric(const std::string& text,const std::string& location){
  insist(text.size()<128 && isDecimalLiteral(text),"Invalid numeric CSV literal at "+location+": "+text);
  int errorType=-1; long errorPosition=-1; double low=0,high=0;
  double result=paceval_dConvertStringToFloat(text.c_str(),&errorType,&errorPosition,false,&low,&high);
  insist(errorType==0 && std::isfinite(result),"paceval numeric converter failure at "+location+" (error "+std::to_string(errorType)+", position "+std::to_string(errorPosition)+")");
  return result;
}
std::string formatNumeric(double value){
  insist(std::isfinite(value),"Attempt to format nonfinite numerical result");
  // Original function has no buffer-length argument. Reserve generous space and limit input domain.
  std::array<char,4096> buffer{};
  int precision=paceval_dConvertFloatToString(buffer.data(),value);
  insist(precision>0,"paceval numerical output conversion failed");
  const auto terminator=std::find(buffer.begin(),buffer.end(),'\0');
  insist(terminator!=buffer.end() && terminator!=buffer.begin(),"Unterminated numerical output");
  const std::string s(buffer.data(),static_cast<size_t>(terminator-buffer.begin()));
  insist(isDecimalLiteral(s),"Unexpected locale/format from paceval output converter: "+s);
  return s;
}
void domain(const Row& a){
  for(double v:a) insist(std::isfinite(v),"Nonfinite model input");
  insist(a[0]>0&&a[1]>=0&&a[2]>0&&a[3]>0&&a[4]>0,"Invalid power/speed/material parameter");
  insist(a[5]>=0&&a[5]<=1&&a[7]>0&&a[8]>a[6]&&a[9]>a[8],"Invalid absorptivity, radius or temperature thresholds");
  insist(a[10]>0&&a[11]>0,"Invalid anisotropy dimensions");
  insist(a[14]>=0 && a[17]>=0,"Probe depth must be nonnegative");
  // Avoid uncontrolled extremely large/small domains in the analytical surrogate and string converter.
  insist(a[0]<=1e5 && a[1]<=100 && a[2]<1e5 && a[3]<1e7 && a[4]<1e7 && a[7]>1e-12,"Input beyond documented test domain");
}
std::vector<Row> readCsv(const std::string& filename){
  std::ifstream in(filename);insist(in.good(),"Cannot open input CSV: "+filename);
  std::string line;insist(static_cast<bool>(std::getline(in,line)),"Empty CSV");
  if(!line.empty()&&line.back()=='\r')line.pop_back();
  insist(line==CsvHeader,"CSV header/schema mismatch");
  std::vector<Row> result;size_t lineNumber=1;
  while(std::getline(in,line)){
    ++lineNumber;if(!line.empty()&&line.back()=='\r')line.pop_back();
    insist(!line.empty(),"Empty data line "+std::to_string(lineNumber));
    std::stringstream s(line);std::string field;std::vector<std::string> fields;
    while(std::getline(s,field,','))fields.push_back(field);
    insist(fields.size()==V && line.back()!=',',"CSV field count mismatch at line "+std::to_string(lineNumber));
    Row r{};for(size_t j=0;j<V;++j)r[j]=parseNumeric(fields[j],std::to_string(lineNumber)+":"+std::to_string(j+1));
    domain(r);result.push_back(r);
  }
  insist(!result.empty() && result.size()<=100000,"Dataset empty or exceeds documented maximum rows");
  return result;
}
// INDEPENDENT C++ mathematical reference: not used to generate paceval results.
double referenceTemperature(const Row& a,bool atDepth,bool anisotropic){
  double x=atDepth?a[15]:a[12],y=atDepth?a[16]:a[13],z=atDepth?a[17]:a[14];
  const double by=anisotropic?a[10]:1.0, bz=anisotropic?a[11]:1.0;
  const double radius=std::hypot(std::hypot(x,y/by),std::hypot(z/bz,a[7]));
  const double diffusivity=a[2]/(a[3]*a[4]);
  const double amplitude=a[5]*a[0]/(2*std::acos(-1.0)*a[2]*radius);
  return a[6]+amplitude*std::exp((-a[1]*(x+radius))/(2*diffusivity));
}
void numericVerification(const Row& a,const std::vector<double>& outputs){
  const double ts=referenceTemperature(a,false,false),td=referenceTemperature(a,true,false);
  const double ts2=referenceTemperature(a,false,true),td2=referenceTemperature(a,true,true);
  const std::vector<double> expected{
    ts,td,ts2,td2,std::min(td-a[8],a[9]-ts),std::min(td2-a[8],a[9]-ts2),
    double((td>=a[8])&&(ts<=a[9])),double((td2>=a[8])&&(ts2<=a[9])),
    (td-a[6])/a[0],-(ts-a[6])*(a[12]+std::sqrt(a[12]*a[12]+a[13]*a[13]+a[14]*a[14]+a[7]*a[7]))*a[3]*a[4]/(2*a[2]),
    td2-td,a[2]/(a[3]*a[4])};
  insist(outputs.size()==expected.size(),"Reference length mismatch");
  for(size_t j=0;j<expected.size();++j){
    insist(std::isfinite(outputs[j]),"Nonfinite paceval result");
    const double allowed=2e-9*(1+std::abs(expected[j]));
    insist(std::abs(outputs[j]-expected[j])<=allowed,"Independent numerical verification failed for "+std::string(kGraphs[j].id));
  }
}
void createGraphs(Graphs& g,bool interval=true){for(const auto& item:kGraphs){
    PACEVAL_HANDLE h=paceval_CreateComputation(item.formula,static_cast<unsigned long>(V),Names,interval,nullptr);
    insist(h!=nullptr && !paceval_GetIsError(h),"Graph registration failed for "+std::string(item.id));
    g.handles.push_back(h);
  }
  return;
}
void conversionTest(){
  for(const char* value:{"0","-0.125","1e-15","+4.2E+12","1.2345"}){
    auto parsed=parseNumeric(value,"conversion_selftest");
    auto output=formatNumeric(parsed);insist(isDecimalLiteral(output),"Roundtrip text grammar failed");
  }
  for(const char* value:{"","1+2","NaN","Inf","3,14","1e9999",".e4","4/5"," 3.14","1_000"}){
    bool rejected=false;try{(void)parseNumeric(value,"negative_selftest");}catch(const std::exception&){rejected=true;}
    insist(rejected,"Unsafe CSV token not rejected: "+std::string(value));
  }
  // Native format conversion precision is NOT presumed to provide IEEE754 bitwise archival roundtrip.
}
void operatorTest(){
  constexpr const char* expressions[]={"(-1) % 10","(-1) mod 10","4 min 5","4 max 5","((x <= (2*y)) AND (z >= 0))","((NOT(x = y)) OR (z <> 0))","((x = y) XOR (z <> 0))"};
  constexpr double targets[]={-1,9,4,5,1,0,1};
  for(size_t i=0;i<7;++i){
    PACEVAL_HANDLE h=paceval_CreateComputation(expressions[i],3,"x y z",false,nullptr);
    insist(h!=nullptr&&!paceval_GetIsError(h),"Operator graph registration failed");
    double values[3]{1,1,0};double result=paceval_dGetComputationResult(h,values,nullptr,nullptr);
    insist(!paceval_GetIsError(h),"Operator evaluation error");
    const double expected=(i==5?0:targets[i]);
    insist(result==expected,"Operator semantics assertion failed");
    paceval_DeleteComputation(h);
  }
}
int run(const std::string& root,bool testsOnly){
  insist(paceval_InitializeLibrary(nullptr),"Cannot initialize original paceval SDK");
  try{
    conversionTest();operatorTest();
    if(!testsOnly){
      std::vector<Row> rows=readCsv(root+"/data/synthetic_process_inputs.csv");
      Graphs graphs; createGraphs(graphs,true);
      std::vector<double> input;input.reserve(rows.size()*V);for(const Row& r:rows)input.insert(input.end(),r.begin(),r.end());
      // First test scalar API vs single-graph batch for the first two scenarios.
      std::vector<double> scalar(2);for(size_t i=0;i<2;++i){
        double vals[V];std::copy(rows[i].begin(),rows[i].end(),vals);
        scalar[i]=paceval_dGetComputationResult(graphs.handles[0],vals,nullptr,nullptr);
        insist(!paceval_GetIsError(graphs.handles[0]),"Scalar API failed");
      }
      std::vector<double> solo(rows.size()),lolo(rows.size()),hihi(rows.size());std::vector<int> errSolo(rows.size());
      bool err=paceval_dGetComputationResultExt(graphs.handles[0],input.data(),static_cast<unsigned long>(rows.size()),solo.data(),lolo.data(),hihi.data(),errSolo.data());
      insist(!err,"Single graph batch reported error");
      for(size_t i=0;i<2;++i)insist(std::abs(scalar[i]-solo[i])<1e-8,"Scalar vs batch discrepancy");
      for(int e:errSolo)insist(e==0,"Single graph batch per-point error");
      // Full multi-graph batch. The output layout is explicitly checked before decoding.
      const size_t len=rows.size()*G;
      std::vector<double> result(len),lower(len),upper(len);std::vector<int> errs(len);
      bool multiError=paceval_dGetMultipleComputationsResultsExt(graphs.handles.data(),static_cast<unsigned long>(G),input.data(),static_cast<unsigned long>(rows.size()),result.data(),lower.data(),upper.data(),errs.data());
      insist(!multiError,"Multi-graph batch reported error");
      bool graphMajor=true,pointMajor=true;
      for(size_t i=0;i<std::min(size_t(3),rows.size());++i){
        graphMajor &= std::abs(result[i]-solo[i])<1e-8;
        pointMajor &= std::abs(result[i*G]-solo[i])<1e-8;
      }
      insist(graphMajor||pointMajor,"Unrecognized multi-graph output layout");
      const auto ix=[&](size_t i,size_t g){return graphMajor?g*rows.size()+i:i*G+g;};
      for(size_t i=0;i<len;++i){
        insist(errs[i]==0,"Per-point paceval error in multi-graph batch");
        insist(std::isfinite(result[i]),"Nonfinite paceval result");
        insist(std::isfinite(lower[i])&&std::isfinite(upper[i])&&lower[i]<=result[i]&&result[i]<=upper[i],"Invalid paceval interval enclosure");
      }
      const std::string outpath=root+"/results/local_sdk_thermal_window.csv";
      std::ofstream out(outpath);insist(out.good(),"Cannot create local SDK results CSV");
      out<<"P_W,v_m_per_s";for(const auto& item:kGraphs)out<<","<<item.id;
      out<<",window_margin_v1_lower,window_margin_v1_upper\n";
      for(size_t i=0;i<rows.size();++i){
        std::vector<double> computed;computed.reserve(G);
        for(size_t g=0;g<G;++g)computed.push_back(result[ix(i,g)]);
        numericVerification(rows[i],computed);
        out<<formatNumeric(rows[i][0])<<","<<formatNumeric(rows[i][1]);
        for(double number:computed)out<<","<<formatNumeric(number);
        out<<","<<formatNumeric(lower[ix(i,4)])<<","<<formatNumeric(upper[ix(i,4)])<<"\n";
      }
      insist(out.good(),"SDK CSV write failure");
      std::cout<<"Original SDK scalar, multi-graph batch, CSV conversions, operator tests and native reference: PASS. Scenario count: "<<rows.size()<<".\n";
    }else{std::cout<<"Original SDK operator and conversion tests: PASS.\n";}
  }catch(...){paceval_FreeLibrary();throw;}
  insist(paceval_FreeLibrary(),"paceval_FreeLibrary failed");
  return 0;
}
}
int main(int argc,char** argv){
  try{const std::string root=(argc>1?argv[1]:".");const bool testsOnly=(argc>2 && std::string(argv[2])=="--selftest");return run(root,testsOnly);}
  catch(const std::exception& ex){std::cerr<<"Thermal window research error: "<<ex.what()<<'\n';return 2;}
}
