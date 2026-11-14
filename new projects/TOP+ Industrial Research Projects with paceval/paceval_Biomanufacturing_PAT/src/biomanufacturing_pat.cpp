// Biomanufacturing process-analytical technology (PAT), research demonstrator.
// Real original paceval SDK executes all process mathematics, including composed
// guards, fed-batch balances, versioned kinetics and sensitivity functions.
// C++ validates CSV, orchestrates batches, compares independent native references
// and writes outputs. No GMP qualification, process control, or product release.
#include "paceval_main.h"
#include "generated_formulas.h"
#include <array>
#include <algorithm>
#include <cmath>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <limits>
#include <regex>
#include <stdexcept>
#include <sstream>
#include <string>
#include <vector>
#include <locale>

namespace {
constexpr size_t N=18;
constexpr size_t G=kGraphs.size();
constexpr const char* Variables="S DO X umax Ks Ko Ki Yxs qO2 qG kLa DOstar F V Sfeed DOmin tau OURcap";
constexpr const char* Header="time_h,S,DO,X,umax,Ks,Ko,Ki,Yxs,qO2,qG,kLa,DOstar,F,V,Sfeed,DOmin,tau,OURcap";
using Values=std::array<double,N>;
struct Record {double hour;Values a;};
void require(bool ok,const std::string& msg){if(!ok)throw std::runtime_error(msg);}
struct Graphs {
 std::vector<PACEVAL_HANDLE> handles;
 ~Graphs(){for(auto h:handles)if(h)paceval_DeleteComputation(h);}
};
bool decimalLiteral(const std::string& v){
 static const std::regex rx(R"(^[+-]?(?:[0-9]+(?:\.[0-9]*)?|\.[0-9]+)(?:[eE][+-]?[0-9]+)?$)");
 return std::regex_match(v,rx);
}
double parseNumber(const std::string& token,const std::string& loc){
 // The paceval converter can evaluate expressions. Only decimal literals are
 // allowed in a sensor CSV. Reject formulas like "1+2" before calling the API.
 require(token.size()<=80 && decimalLiteral(token),"Unsafe numeric CSV literal at "+loc);
 int err=-1;long at=-1;double lo=0,hi=0;
 double v=paceval_dConvertStringToFloat(token.c_str(),&err,&at,false,&lo,&hi);
 require(err==0 && std::isfinite(v),"SDK number parser failure "+loc+" err="+std::to_string(err)+" position="+std::to_string(at));
 return v;
}
std::string formatNumber(double v){
 require(std::isfinite(v),"Nonfinite value during CSV formatting");
 // SDK exposes no destination-buffer size argument. Conservative fixed-size
 // buffer plus documented finite-domain restrictions, then termination check.
 std::array<char,4096> buffer{};
 int p=paceval_dConvertFloatToString(buffer.data(),v);
 require(p>0,"SDK number formatting failure");
 auto stop=std::find(buffer.begin(),buffer.end(),'\0');
 require(stop!=buffer.end() && stop!=buffer.begin(),"SDK output not terminated");
 std::string s(buffer.data(),static_cast<size_t>(stop-buffer.begin()));
 require(decimalLiteral(s),"Unexpected SDK number format or locale");
 return s;
}
void valid(const Values& a){
 for(double v:a)require(std::isfinite(v),"Nonfinite process input");
 const double S=a[0],DO=a[1],X=a[2],umax=a[3],Ks=a[4],Ko=a[5],Ki=a[6],Y=a[7],qO2=a[8],qG=a[9],kla=a[10],dos=a[11],F=a[12],V=a[13],Sf=a[14],minDO=a[15],tau=a[16],cap=a[17];
 require(S>=0&&S<=100&&DO>=0&&DO<dos&&X>=0&&X<=100,"Invalid state or oxygen-transfer domain");
 require(umax>0&&umax<=20&&Ks>0&&Ko>0&&Ki>0&&Y>0&&Y<=10,"Invalid kinetic parameters");
 require(qO2>=0&&qG>=0&&kla>0&&kla<=10000&&dos>0&&dos<=1,"Invalid oxygen coefficients");
 require(F>=0&&V>0&&F/V<=10&&Sf>=0&&minDO>=0&&minDO<dos&&tau>0&&cap>=0,"Invalid feed or monitoring parameters");
 // DOstar-DO is strictly positive before division in required kLa/uptake ratio.
 require(dos-DO>1e-9,"Near singular DOstar-DO must be rejected");
}
std::vector<Record> readCsv(const std::string& path){
 std::ifstream in(path);require(in.good(),"Unable to read "+path);in.imbue(std::locale::classic());
 std::string line;require(bool(std::getline(in,line)),"Empty CSV");
 if(!line.empty()&&line.back()=='\r')line.pop_back();
 require(line==Header,"CSV schema mismatch");
 std::vector<Record> rows;size_t lineNo=1;
 while(std::getline(in,line)){
  ++lineNo;if(!line.empty()&&line.back()=='\r')line.pop_back();require(!line.empty(),"Empty CSV row");
  std::stringstream ss(line);ss.imbue(std::locale::classic());std::vector<std::string> fields;std::string cell;
  while(std::getline(ss,cell,','))fields.push_back(cell);
  require(fields.size()==N+1 && line.back()!=',',"CSV field count mismatch on line "+std::to_string(lineNo));
  Record r{};r.hour=parseNumber(fields[0],std::to_string(lineNo)+":time_h");
  require(r.hour>=0&&r.hour<=100000,"Invalid replay time");
  for(size_t j=0;j<N;++j)r.a[j]=parseNumber(fields[j+1],std::to_string(lineNo)+":"+std::to_string(j+2));
  valid(r.a);rows.push_back(r);
 }
 require(!rows.empty()&&rows.size()<=100000,"No cases or dataset exceeds permitted size");return rows;
}
void conversionTests(){
 for(const char* token:{"0","-0.125","+3e-9","2.34E+8",".007","3."}){
  double v=parseNumber(token,"conversion_selftest");std::string s=formatNumber(v);
  require(decimalLiteral(s),"Invalid serialized scientific number");
 }
 for(const char* token:{"","1+2","1/2","NaN","Inf","3,14"," 2.0","1e9999","1_000","0xFF"}){
  bool rejected=false;try{(void)parseNumber(token,"expected_rejection");}catch(...){rejected=true;}
  require(rejected,"CSV unsafe token unexpectedly accepted");
 }
 // Roundtrip numerical identity is NOT asserted. SDK output may round digits.
}
void operatorTests(){
 const char* expr[]={"(-1) % 10","(-1) mod 10","4 min 5","4 max 5","((x <= (2*y)) AND (z >= 0))","((NOT(x = y)) OR (z <> 0))","((x = y) XOR (z <> 0))"};
 const double expected[]={-1,9,4,5,1,0,1};
 for(size_t i=0;i<7;++i){
  PACEVAL_HANDLE h=paceval_CreateComputation(expr[i],3,"x y z",false,nullptr);
  require(h && !paceval_GetIsError(h),"Operator parser failed");
  double args[3]={1,1,0};double output=paceval_dGetComputationResult(h,args,nullptr,nullptr);
  require(!paceval_GetIsError(h) && output==expected[i],"Operator semantics failed");
  paceval_DeleteComputation(h);
 }
}
void initGraphs(Graphs& out){
 for(const auto& f:kGraphs){
  auto h=paceval_CreateComputation(f.formula,static_cast<unsigned long>(N),Variables,true,nullptr);
  require(h && !paceval_GetIsError(h),std::string("Graph creation failed: ")+f.id);
  out.handles.push_back(h);
 }
}
// Independently coded mathematical reference. Never used for published paceval
// results; used exclusively as a verification oracle after real API evaluation.
std::array<double,G> nativeReference(const Values& a){
 const auto S=a[0],D=a[1],X=a[2],um=a[3],Ks=a[4],Ko=a[5],Ki=a[6],Y=a[7],qo=a[8],qg=a[9],k=a[10],ds=a[11],F=a[12],V=a[13],Sf=a[14],dmin=a[15],tau=a[16];
 const double muA=um*(S/(Ks+S))*(D/(Ko+D));
 const double muB=um*(S/(Ks+S+S*S/Ki))*(D/(Ko+D));
 const double uA=qo*X,uB=(qo+qg*muB)*X,trans=k*(ds-D);
 const double mA=trans-uA,mB=trans-uB;
 return {muA,muB,muA*X/Y,muB*X/Y,uA,uB,trans,
 trans-uA-(F/V)*D,trans-uB-(F/V)*D,(F/V)*(Sf-S)-muA*X/Y,(F/V)*(Sf-S)-muB*X/Y,
 (muA-F/V)*X,(muB-F/V)*X,mA,mB,std::min(D-dmin,tau*mA),std::min(D-dmin,tau*mB),
 double(D>=dmin&&mA>=0&&S>=0),double(D>=dmin&&mB>=0&&S>=0),
 um*(D/(Ko+D))*((Ks-S*S/Ki)/std::pow(Ks+S+S*S/Ki,2)),ds-D,uB/trans,muB-muA,uB/(ds-D)};
}
void referenceCheck(const Values& a,const std::array<double,G>& actual){
 const auto expected=nativeReference(a);
 for(size_t i=0;i<G;++i){
  require(std::isfinite(actual[i]),"Nonfinite graph result");
  require(std::fabs(actual[i]-expected[i])<=5e-10*(1+std::fabs(expected[i])),
    std::string("Independent C++ reference differs: ")+kGraphs[i].id);
 }
}
void runCases(const std::string& root,const std::string& inputName,const std::string& outputName){
 const auto rows=readCsv(root+"/data/"+inputName);
 Graphs graphs;initGraphs(graphs);
 std::vector<double> packed;packed.reserve(rows.size()*N);
 for(const auto& r:rows)packed.insert(packed.end(),r.a.begin(),r.a.end());
 // Verify scalar-vs-single-graph batch, then the multi-graph output layout.
 std::array<double,3> scalars{};
 const size_t samples=std::min(size_t(3),rows.size());
 for(size_t i=0;i<samples;++i){auto a=rows[i].a;scalars[i]=paceval_dGetComputationResult(graphs.handles[0],a.data(),nullptr,nullptr);require(!paceval_GetIsError(graphs.handles[0]),"Scalar SDK graph failed");}
 std::vector<double> scalarBatch(rows.size()),scalarLower(rows.size()),scalarUpper(rows.size());std::vector<int> scalarErrors(rows.size());
 const bool batchErr=paceval_dGetComputationResultExt(graphs.handles[0],packed.data(),static_cast<unsigned long>(rows.size()),scalarBatch.data(),scalarLower.data(),scalarUpper.data(),scalarErrors.data());
 require(!batchErr,"Single-graph batch error");
 for(size_t i=0;i<samples;++i)require(std::abs(scalars[i]-scalarBatch[i])<=1e-11,"Scalar batch layout mismatch");
 for(int e:scalarErrors)require(e==0,"Single-graph batch point error");
 const size_t L=rows.size()*G;
 std::vector<double> result(L),lower(L),upper(L);std::vector<int> errors(L);
 const bool multiErr=paceval_dGetMultipleComputationsResultsExt(graphs.handles.data(),static_cast<unsigned long>(G),packed.data(),static_cast<unsigned long>(rows.size()),result.data(),lower.data(),upper.data(),errors.data());
 require(!multiErr,"Multi-graph SDK batch error");
 bool byGraph=true,byCase=true;
 for(size_t i=0;i<samples;++i){byGraph&=std::abs(result[i]-scalarBatch[i])<1e-10;byCase&=std::abs(result[i*G]-scalarBatch[i])<1e-10;}
 require(byGraph||byCase,"Unknown SDK multi-graph result layout");
 auto ix=[&](size_t i,size_t g){return byGraph?g*rows.size()+i:i*G+g;};
 std::ofstream out(root+"/results/"+outputName);out.imbue(std::locale::classic());require(out.good(),"Cannot write local SDK output");
 out<<"time_h";for(const auto& f:kGraphs)out<<","<<f.id;out<<",score_v2_tinc_lower,score_v2_tinc_upper\n";
 for(size_t i=0;i<rows.size();++i){
  std::array<double,G> values{};
  for(size_t g=0;g<G;++g){size_t idx=ix(i,g);require(errors[idx]==0,"SDK graph-point error");require(std::isfinite(lower[idx])&&std::isfinite(upper[idx])&&lower[idx]<=result[idx]&&result[idx]<=upper[idx],"SDK TINC bounds failed");values[g]=result[idx];}
  referenceCheck(rows[i].a,values);
  out<<formatNumber(rows[i].hour);for(double v:values)out<<','<<formatNumber(v);
  out<<','<<formatNumber(lower[ix(i,16)])<<','<<formatNumber(upper[ix(i,16)])<<'\n';
 }
 require(out.good(),"Output CSV write failure");
 std::cout<<"Local SDK run complete: "<<rows.size()<<" synthetic snapshots; "<<G<<" graph versions; independent checks passed.\n";
}
int run(const std::string& root,const bool selftest){
 require(paceval_InitializeLibrary(nullptr),"Unable to initialize ORIGINAL paceval runtime");
 try{
  conversionTests();operatorTests();
  if(!selftest){runCases(root,"synthetic_sensor_snapshots.csv","local_sdk_snapshots.csv");runCases(root,"synthetic_state_grid.csv","local_sdk_grid.csv");}
  else std::cout<<"Original SDK conversion and operator semantics: PASS\n";
 }catch(...){paceval_FreeLibrary();throw;}
 require(paceval_FreeLibrary(),"Runtime shutdown failed");return 0;
}
} // namespace
int main(int argc,char** argv){
 try{return run(argc>1?argv[1]:".",argc>2&&std::string(argv[2])=="--selftest");}
 catch(const std::exception& e){std::cerr<<"Biomanufacturing PAT demonstration FAILED: "<<e.what()<<'\n';return 2;}
}
