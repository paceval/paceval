// WP08: IC timing and leakage corner-sweep mathematical research demonstrator.
// Productive semiconductor-domain mathematical evaluation runs through original
// paceval reusable graphs. C++ orchestrates data, graph lifetime, verification,
// safety checks, CSV schema, and path/corner selection. These synthetic models
// do not replace Liberty characterization, static timing analysis, or signoff.
#include "paceval_main.h"
#include "generated_formulas.h"
#include <algorithm>
#include <array>
#include <cmath>
#include <fstream>
#include <iostream>
#include <locale>
#include <regex>
#include <sstream>
#include <stdexcept>
#include <string>
#include <vector>

void runDedicatedNumericConverterTest();
void runDedicatedOperatorSemanticsTest();

namespace {
constexpr size_t N=30;
constexpr size_t G=kGraphs.size();
using Values=std::array<double,N>;
constexpr const char* VariableNames="V T C S t0 aC aS aT aV Vref Tref p q aCT aCS I0 bT bV bTT bVT Treq Tarr Ncells Wire Pcap Pscale Vmin Vmax Tmin Tmax";
constexpr const char* CsvHeader="scenario_id,V,T,C,S,t0,aC,aS,aT,aV,Vref,Tref,p,q,aCT,aCS,I0,bT,bV,bTT,bVT,Treq,Tarr,Ncells,Wire,Pcap,Pscale,Vmin,Vmax,Tmin,Tmax";
struct Record{std::string id;Values a;};
void require(bool ok,const std::string& msg){if(!ok)throw std::runtime_error(msg);}
struct Handles{
 std::vector<PACEVAL_HANDLE> values;
 ~Handles(){for(auto h:values)if(h)paceval_DeleteComputation(h);}
};
bool isLiteral(const std::string& s){
 static const std::regex r(R"(^[+-]?(?:[0-9]+(?:\.[0-9]*)?|\.[0-9]+)(?:[eE][+-]?[0-9]+)?$)");
 return std::regex_match(s,r);
}
double parseSdkNumber(const std::string& s,const std::string& source){
 // Original converter accepts expressions; reject any non-literal *before*
 // invoking it. Numeric CSV fields are never mathematical expression fields.
 require(s.size()<=80&&isLiteral(s),"Unsafe CSV numeric literal at "+source);
 int err=-1;long position=-1;double low=0.0,high=0.0;
 const double d=paceval_dConvertStringToFloat(s.c_str(),&err,&position,false,&low,&high);
 require(err==0&&std::isfinite(d),"paceval text conversion error at "+source+" code "+std::to_string(err)+" offset "+std::to_string(position));
 return d;
}
std::string sdkNumber(double number){
 require(std::isfinite(number),"Cannot serialize nonfinite result");
 // The original API has no buffer length parameter. This buffer is large,
 // initialized, and termination-checked. Do not interpret output as bitwise
 // reversible IEEE-754 binary64 serialization.
 std::array<char,4096> buf{};
 const int digits=paceval_dConvertFloatToString(buf.data(),number);
 require(digits>0,"paceval numeric formatting error");
 const auto term=std::find(buf.begin(),buf.end(),'\0');
 require(term!=buf.end()&&term!=buf.begin(),"paceval formatting output lacks terminator");
 std::string s(buf.data(),static_cast<size_t>(term-buf.begin()));
 require(isLiteral(s),"Noncanonical output decimal text");return s;
}
void validate(const Values& a){
 for(double v:a)require(std::isfinite(v),"Nonfinite domain input");
 const double V=a[0],T=a[1],C=a[2],S=a[3],t0=a[4],aC=a[5],aS=a[6],aT=a[7],aV=a[8],Vref=a[9],p=a[11],q=a[12],I0=a[15],bT=a[16],bV=a[17],bTT=a[18],bVT=a[19],Treq=a[20],Tarr=a[21],Ncells=a[22],Wire=a[23],Pcap=a[24],Pscale=a[25],Vmin=a[26],Vmax=a[27],Tmin=a[28],Tmax=a[29];
 require(V>=0.5&&V<=1.4&&Vref>0.5&&Vref<1.4,"Voltage outside positive modeling domain");
 require(T>=-60&&T<=150&&Tmax>Tmin&&T>=Tmin&&T<=Tmax&&Vmin>0&&Vmax>Vmin&&V>=Vmin&&V<=Vmax,"Invalid defined corner");
 require(C>=0&&C<=150&&S>=0&&S<=400&&t0>=0&&t0<=500,"Invalid load, slew or base delay");
 require(aC>=0&&aC<100&&aS>=0&&aS<10&&aT>=0&&aT<5&&aV>=0&&aV<500,"Delay coefficients out of range");
 require(p>=0&&p<=5&&q>=0&&q<=5&&I0>=0&&I0<1e6,"Exponent or leakage amplitude domain");
 require(std::abs(bT)<=0.2&&std::abs(bV)<=5&&std::abs(bTT)<=0.002&&std::abs(bVT)<=0.02,"Exponential argument safety constraints");
 require(Treq>0&&Treq<=1e7&&Tarr>=0&&Wire>=0&&Ncells>=1&&Ncells<=32&&Ncells==std::floor(Ncells),"Invalid illustrative path constraint");
 require(Pcap>0&&Pcap<1e7&&Pscale>0&&Pscale<1e7,"Invalid leakage budget or score conversion");
}
std::vector<Record> readCases(const std::string& path){
 std::ifstream in(path);in.imbue(std::locale::classic());require(in.good(),"Cannot open CSV: "+path);
 std::string line;require(bool(std::getline(in,line)),"Empty CSV");if(!line.empty()&&line.back()=='\r')line.pop_back();require(line==CsvHeader,"Schema mismatch");
 std::vector<Record> cases;size_t lineno=1;
 while(std::getline(in,line)){
  ++lineno;if(!line.empty()&&line.back()=='\r')line.pop_back();require(!line.empty()&&line.back()!=',',"Empty/malformed row "+std::to_string(lineno));
  std::stringstream ss(line);ss.imbue(std::locale::classic());std::vector<std::string> fields;std::string c;
  while(std::getline(ss,c,','))fields.push_back(c);
  require(fields.size()==N+1,"Field count on row "+std::to_string(lineno));
  Record r;r.id=fields[0];require(std::regex_match(r.id,std::regex("[GS][0-9]{2,3}")),"Invalid scenario ID");
  for(size_t j=0;j<N;++j)r.a[j]=parseSdkNumber(fields[j+1],r.id+":column"+std::to_string(j+2));
  validate(r.a);cases.push_back(r);
 }
 require(!cases.empty()&&cases.size()<=10000,"Empty or oversized input");return cases;
}
void testConverters(){
 for(const char* s:{"0","-0.5","+.6","12.5e-3","8.225E+4","3.","0.000000000000000001"}){
  const auto v=parseSdkNumber(s,"unit_test");require(isLiteral(sdkNumber(v)),"Invalid number roundtrip format");
 }
 for(const char* s:{""," 1.0","1+2","NaN","Inf","2,3","0xFF","1_234","1e9999","2*pi"}){
  bool rejected=false;try{(void)parseSdkNumber(s,"rejection_test");}catch(...){rejected=true;}
  require(rejected,std::string("Unsafe numeric field was accepted: ")+s);
 }
}
void testOperators(){
 const char* expressions[]={"(-1) % 10","(-1) mod 10","4 min 5","4 max 5","((x<=2*y) AND (z>=0))","((NOT(x=y)) OR (z<>0))","((x=y) XOR (z<>0))"};
 const double expected[]={-1,9,4,5,1,0,1};
 for(size_t i=0;i<7;++i){
  PACEVAL_HANDLE h=paceval_CreateComputation(expressions[i],3,"x y z",false,nullptr);
  require(h&&!paceval_GetIsError(h),"Operator graph creation failed");
  double v[3]={1,1,0};const double y=paceval_dGetComputationResult(h,v,nullptr,nullptr);
  const bool good=!paceval_GetIsError(h)&&y==expected[i];paceval_DeleteComputation(h);
  require(good,"Operator semantic test failed");
 }
 // Non-strict equality at the boundary, and negative-operand modulo semantics
 // are checked above. Guard checks are repeated for the real scenario outputs.
}
void createGraphs(Handles& h){
 for(const auto& graph:kGraphs){
  PACEVAL_HANDLE handle=paceval_CreateComputation(graph.formula,static_cast<unsigned long>(N),VariableNames,true,nullptr);
  require(handle&&!paceval_GetIsError(handle),std::string("Graph registration failed: ")+graph.id);
  h.values.push_back(handle);
 }
}
// Independent native C++ oracle, never the productive paceval calculation path.
std::array<double,G> reference(const Values& x){
 const double V=x[0],T=x[1],C=x[2],S=x[3],t0=x[4],aC=x[5],aS=x[6],aT=x[7],aV=x[8],Vref=x[9],Tref=x[10],p=x[11],q=x[12],aCT=x[13],aCS=x[14],I0=x[15],bT=x[16],bV=x[17],bTT=x[18],bVT=x[19],Req=x[20],Arr=x[21],n=x[22],wire=x[23],cap=x[24],scale=x[25],vmin=x[26],vmax=x[27],tmin=x[28],tmax=x[29];
 const double dt=T-Tref,dv=V-Vref,rv=Vref/V;
 const double d1=t0+aC*C+aS*S+aT*dt+aV*std::pow(rv,p);
 const double d2=t0+aC*C*std::pow(rv,q)+aS*S+aT*dt+aV*std::pow(rv,p)+aCT*C*dt+aCS*C*S;
 const double il1=I0*std::exp(bT*dt+bV*dv);
 const double il2=I0*std::exp(bT*dt+bV*dv+bTT*dt*dt+bVT*dt*dv);
 const double p1=V*il1,p2=V*il2;
 const double path1=n*d1+wire,path2=n*d2+wire;
 const double slack1=Req-Arr-path1,slack2=Req-Arr-path2;
 const double margin1=cap-p1,margin2=cap-p2;
 const double score1=std::min(slack1,scale*margin1),score2=std::min(slack2,scale*margin2);
 const bool domain=V>=vmin&&V<=vmax&&T>=tmin&&T<=tmax;
 return {d1,d2,il1,il2,p1,p2,path1,path2,slack1,slack2,margin1,margin2,score1,score2,
         double(slack1>=0&&margin1>=0&&domain),double(slack2>=0&&margin2>=0&&domain),
         -aC*C*q*std::pow(rv,q)/V-aV*p*std::pow(rv,p)/V,aT+aCT*C,
         il2*(bT+2*bTT*dt+bVT*dv),d2-d1,p2-p1,p2/cap};
}
void referenceCheck(const Values& in,const std::array<double,G>& obtained){
 const auto ref=reference(in);
 for(size_t g=0;g<G;++g){
  require(std::isfinite(obtained[g]),"Nonfinite paceval result");
  const double tol=4e-10*(1+std::fabs(ref[g]));
  require(std::fabs(ref[g]-obtained[g])<=tol,std::string("Independent native C++ reference mismatch: ")+kGraphs[g].id);
 }
}
void run(const std::string& root,const std::string& input,const std::string& output){
 const auto rows=readCases(root+"/data/"+input);
 Handles handles;createGraphs(handles);
 std::vector<double> packed;packed.reserve(rows.size()*N);
 for(const auto& r:rows)packed.insert(packed.end(),r.a.begin(),r.a.end());
 // Scalar check is independent of the multi-graph batch layout probe.
 std::array<double,3> single{};const size_t ntest=std::min(size_t(3),rows.size());
 for(size_t j=0;j<ntest;++j){auto v=rows[j].a;single[j]=paceval_dGetComputationResult(handles.values[0],v.data(),nullptr,nullptr);require(!paceval_GetIsError(handles.values[0]),"Scalar evaluation failed");}
 std::vector<double> one(rows.size()),oneLo(rows.size()),oneHi(rows.size());std::vector<int> oneErr(rows.size());
 const bool oneFailed=paceval_dGetComputationResultExt(handles.values[0],packed.data(),static_cast<unsigned long>(rows.size()),one.data(),oneLo.data(),oneHi.data(),oneErr.data());
 require(!oneFailed,"Single graph batch API error");
 for(int e:oneErr)require(e==0,"Per-sample batch result error");
 for(size_t j=0;j<ntest;++j)require(std::abs(single[j]-one[j])<1e-10,"Scalar/batch layout mismatch");
 const size_t count=G*rows.size();
 std::vector<double> val(count),lo(count),hi(count);std::vector<int> err(count);
 const bool failed=paceval_dGetMultipleComputationsResultsExt(handles.values.data(),static_cast<unsigned long>(G),packed.data(),static_cast<unsigned long>(rows.size()),val.data(),lo.data(),hi.data(),err.data());
 require(!failed,"Multi-graph batch failed");
 bool byGraph=true,bySample=true;
 for(size_t j=0;j<ntest;++j){byGraph&=std::abs(val[j]-one[j])<1e-10;bySample&=std::abs(val[j*G]-one[j])<1e-10;}
 require(byGraph||bySample,"Unknown real multi-graph API memory layout");
 auto pos=[&](size_t j,size_t k){return byGraph?k*rows.size()+j:j*G+k;};
 std::ofstream out(root+"/results/"+output);out.imbue(std::locale::classic());require(out.good(),"Cannot open output file");
 out<<"scenario_id";for(const auto& g:kGraphs)out<<","<<g.id;out<<",score_v2_TINC_lower_ps,score_v2_TINC_upper_ps\n";
 for(size_t j=0;j<rows.size();++j){
  std::array<double,G> current{};
  for(size_t k=0;k<G;++k){const auto idx=pos(j,k);require(err[idx]==0,"Per-graph batch result error");require(std::isfinite(lo[idx])&&std::isfinite(hi[idx])&&lo[idx]<=val[idx]&&val[idx]<=hi[idx],"Untrusted or inconsistent local interval");current[k]=val[idx];}
  referenceCheck(rows[j].a,current);
  out<<rows[j].id;
  for(auto d:current)out<<","<<sdkNumber(d);
  const auto idx=pos(j,13);out<<","<<sdkNumber(lo[idx])<<","<<sdkNumber(hi[idx])<<"\n";
 }
 require(out.good(),"CSV write failure");
 std::cout<<"Original SDK passed: "<<rows.size()<<" scenarios, "<<G<<" graphs, full native reference checks; output "<<output<<"\n";
}
}
int main(int argc,char** argv){
 try{
  std::locale::global(std::locale::classic());
  const std::string root=argc>1?argv[1]:".";
  require(paceval_InitializeLibrary(nullptr),"Could not initialize original paceval SDK");
  testConverters();testOperators();
  runDedicatedNumericConverterTest();runDedicatedOperatorSemanticsTest();
  if(argc>2&&std::string(argv[2])=="--selftest"){std::cout<<"Converter/operator selftests passed (original SDK)\n";return 0;}
  run(root,"synthetic_corner_grid_81.csv","local_sdk_grid_regenerated.csv");
  run(root,"synthetic_path_snapshots_16.csv","local_sdk_snapshots_regenerated.csv");
  return 0;
 }catch(const std::exception& e){std::cerr<<"FAIL: "<<e.what()<<"\n";return 1;}
}
