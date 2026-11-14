// WP15: industrial heat-exchanger fouling and duty mathematical research.
// Main numerical quantities are executed with original SDK persistent paceval
// graphs. C++ owns CSV schema, domains, graph lifetime, row transport,
// version selection and independent reference checks.
// Neither a qualified plant controller nor an empirical fouling estimator.
#include "paceval_main.h"
#include "generated_formulas.h"
#include <array>
#include <algorithm>
#include <cmath>
#include <fstream>
#include <iostream>
#include <locale>
#include <regex>
#include <sstream>
#include <stdexcept>
#include <string>
#include <vector>
namespace {
void require(bool v,const std::string& what){ if(!v) throw std::runtime_error(what); }
struct Case{std::string id;std::vector<double> a;};
struct HandleGuard{std::vector<PACEVAL_HANDLE> h;~HandleGuard(){for(auto p:h)if(p)paceval_DeleteComputation(p);}};
bool literal(const std::string& s){
 static const std::regex r(R"(^[+-]?(?:[0-9]+(?:\.[0-9]*)?|\.[0-9]+)(?:[eE][+-]?[0-9]+)?$)");
 return !s.empty()&&s.size()<=80&&std::regex_match(s,r);
}
double number(const std::string& s,const std::string& where){
 // The original API can evaluate formulas during StringToFloat conversion.
 // Restrict CSV inputs to a finite literal grammar BEFORE invoking the API.
 require(literal(s),"Illegal CSV numeric literal at "+where);
 int code=-1;long pos=-1;double low=0,up=0;
 const double result=paceval_dConvertStringToFloat(s.c_str(),&code,&pos,false,&low,&up);
 require(code==0&&std::isfinite(result),"paceval numeric parse error at "+where+" type="+std::to_string(code)+" pos="+std::to_string(pos));
 return result;
}
std::string numericalText(double x){
 require(std::isfinite(x),"Nonfinite CSV output");
 std::array<char,4096> data{}; const int p=paceval_dConvertFloatToString(data.data(),x);
 require(p>0,"paceval numeric output conversion failed");
 auto end=std::find(data.begin(),data.end(),'\0');
 require(end!=data.end()&&end!=data.begin(),"paceval conversion produced no termination");
 std::string result(data.begin(),end);
 require(literal(result),"paceval conversion produced noncanonical CSV numeric text");
 return result;
}
void domains(const std::vector<double>& a){
 require(a.size()==variable_count,"Variable count mismatch");
 for(double x:a)require(std::isfinite(x),"Nonfinite input");
 const double Th=a[0],Tc=a[1],Ch=a[2],Cc=a[3],Uc=a[4],A=a[5],Rf=a[6],Fc=a[7];
 const double D1=a[8],D2=a[9],target=a[10],remainder=a[11],H=a[12],Price=a[13],Cclean=a[14],approach=a[15];
 require(Th>Tc&&Th-Tc>=1&&Th<=350&&Tc>=-60,"Invalid or reversed inlet temperatures");
 require(Ch>100&&Cc>100&&Ch<1e8&&Cc<1e8,"Heat capacity rates outside research domain");
 require(Uc>0&&Uc<2e5&&A>0&&A<1e5&&Rf>=0&&Rf<0.05,"Conductance/fouling domain");
 require(Fc>0&&Fc<=1&&D1>0&&D2>0&&D1<500&&D2<500,"LMTD terminal domain");
 // v1 main batch intentionally uses unequal terminal differences; the separate
 // equal/near-equal branch is tested on a dedicated graph in --selftest.
 require(std::abs(D1-D2)>1e-5,"Main-batch v1 direct LMTD requires separated terminal differences; use equal-terminal series branch");
 require(target>=0&&remainder>=0&&remainder<0.05&&H>=0&&Price>=0&&Cclean>=0&&approach>=0&&a[16]>=0&&a[17]>0,"Decision input domain");
 require(std::abs(Ch-Cc)/std::max(Ch,Cc)>1e-3,"Main-batch v2 requires unequal heat capacities; use balanced-capacity graph in dedicated branch");
}
std::vector<Case> readInput(const std::string& path){
 std::ifstream in(path);in.imbue(std::locale::classic());require(bool(in),"CSV not readable: "+path);
 std::string line;require(bool(std::getline(in,line)),"Missing CSV header");if(!line.empty()&&line.back()=='\r')line.pop_back();
 std::string header="case_id";std::istringstream columns(variable_list);std::string col;
 while(columns>>col){header+=","+col;}require(header==line,"CSV schema/order incompatible with paceval graph variables");
 std::vector<Case> out;unsigned row=1;
 while(std::getline(in,line)){
  ++row;if(!line.empty()&&line.back()=='\r')line.pop_back();require(!line.empty(),"Blank CSV data row");
  std::stringstream ss(line);std::string part;std::vector<std::string> cells;
  while(std::getline(ss,part,','))cells.push_back(part);
  require(cells.size()==variable_count+1&&line.back()!=',',"Bad CSV field count at "+std::to_string(row));
  Case r;r.id=cells[0];require(std::regex_match(r.id,std::regex("[A-Za-z0-9_-]{1,48}")),"Bad identifier");
  for(size_t k=1;k<cells.size();++k)r.a.push_back(number(cells[k],"row "+std::to_string(row)+" column "+std::to_string(k)));
  domains(r.a);out.push_back(r);require(out.size()<=250000,"Excessive rows");
 }
 require(!out.empty(),"No input cases");return out;
}
double referenceQ(const std::vector<double>& a,double r){
 // Independent native C++ reference used only for verification.
 const double Ch=a[2],Cc=a[3],cmin=std::min(Ch,Cc),cmax=std::max(Ch,Cc);
 const double n=(a[5]/(1.0/a[4]+r))/cmin;
 const double cr=cmin/cmax;
 const double z=std::exp(-n*(1-cr));
 const double epsilon=(1-z)/(1-cr*z);
 return epsilon*cmin*(a[0]-a[1]);
}
void referenceCheck(const std::vector<double>& a,const std::vector<double>& z){
 auto close=[](double x,double y){return std::abs(x-y)<=5e-10*(1+std::abs(y));};
 const double Q=referenceQ(a,a[6]);
 require(close(z[8],Q),"Independent counterflow Q reference failed");
 const double ht=a[0]-Q/a[2],ct=a[1]+Q/a[3];
 require(close(z[10],ht)&&close(z[11],ct),"Independent outlet reference failed");
 require(close(z[15],0.0),"Energy-balance residual failed");
 const double pinch=std::min(a[0]-ct,ht-a[1]);
 require(close(z[12],pinch),"Pinch reference mismatch");
 const bool operation=(Q>=a[10]&&pinch>=a[15]&&a[16]<=a[17]);
 require(z[20]==(operation?1.0:0.0),"Operational math guard mismatch");
 const auto loss=[&](double p){return a[13]*a[12]*std::max(0.0,a[10]-p)/1000.0;};
 const double score=loss(Q)-(a[14]+loss(referenceQ(a,a[11])));
 require(close(z[18],score),"Independent cleaning score mismatch");
 require(z[19]==((score>0&&a[6]>a[11])?1.0:0.0),"Cleaning guard mismatch");
}
void testConversion(){
 for(const auto* val:{"0","-0","+3.25","1.25e-9","1e8",".125","42."}){
  const double x=number(val,"selftest"); require(literal(numericalText(x)),"Bad roundtrip");
 }
 for(const auto* val:{"","1+2","NaN","Infinity","0x10"," 1","3,14","1e9999","2_000","1/0"}){
  require(!literal(val),"Numeric schema allows expression/invalid text");
 }
}
void testOperators(){
 struct Test{const char* expr;double want;};
 const Test t[]={{"(-1) % 10",-1},{"(-1) mod 10",9},{"4 min 5",4},{"4 max 5",5},
 {"((x <= (2*y)) AND (z >= 0))",1},{"((NOT(x = y)) OR (z <> 0))",0},{"((x = y) XOR (z <> 0))",1}};
 for(const auto& z:t){
  PACEVAL_HANDLE handle=paceval_CreateComputation(z.expr,3,"x y z",false,nullptr);
  require(handle&&!paceval_GetIsError(handle),"Operator graph not created");
  double v[]={1,1,0};double got=paceval_dGetComputationResult(handle,v,nullptr,nullptr);
  require(!paceval_GetIsError(handle)&&got==z.want,"Operator selftest failed");
  paceval_DeleteComputation(handle);
 }
}
void testSpecialLimits(){
 // Test exact equal LMTD, near equal and equal capacity rate separately, because
 // a direct log ratio and generic ε formula can be ill-conditioned at equality.
 const double base[]={125,35,12000,12000,950,32,.0003,.95,30,30,550000,.00002,160,.24,3400,5,18000,25000};
 std::vector<double> a(base,base+variable_count);
 for(int idx:{2,4,23}){
  const auto& graph=model_graphs[size_t(idx)];
  PACEVAL_HANDLE h=paceval_CreateComputation(graph.expression,variable_count,variable_list,false,nullptr);
  require(h&&!paceval_GetIsError(h),"Special-limit graph creation failed");
  double answer=paceval_dGetComputationResult(h,a.data(),nullptr,nullptr);
  require(!paceval_GetIsError(h)&&std::isfinite(answer),"Special-limit graph evaluation failed");
  if(idx==2)require(std::abs(answer-30)<1e-10,"Exact LMTD limit incorrect");
  if(idx==23){
   const double ntu=a[5]/(1/a[4]+a[6])/a[2];
   require(std::abs(answer-ntu/(1+ntu))<1e-10,"Equal-rate ε limit incorrect");
  }
  paceval_DeleteComputation(h);
 }
}
void run(const std::string& root,bool selftest){
 require(paceval_InitializeLibrary(nullptr),"Original paceval runtime missing or incompatible");
 try{
  testConversion();testOperators();testSpecialLimits();
  if(!selftest){
   auto rows=readInput(root+"/examples/synthetic_corner_scenarios.csv");
   HandleGuard g;
   for(const auto& graph:model_graphs){
    const auto p=paceval_CreateComputation(graph.expression,variable_count,variable_list,false,nullptr);
    require(p&&!paceval_GetIsError(p),std::string("Cannot register ")+graph.id);
    g.h.push_back(p);
   }
   std::vector<double> inputs;inputs.reserve(rows.size()*variable_count);
   for(const auto& r:rows)inputs.insert(inputs.end(),r.a.begin(),r.a.end());
   double scalar=paceval_dGetComputationResult(g.h[0],rows[0].a.data(),nullptr,nullptr);
   require(!paceval_GetIsError(g.h[0]),"Scalar API failed");
   std::vector<double> one(rows.size());std::vector<int> oneErr(rows.size());
   bool err=paceval_dGetComputationResultExt(g.h[0],inputs.data(),static_cast<unsigned long>(rows.size()),one.data(),nullptr,nullptr,oneErr.data());
   require(!err && oneErr[0]==0 && std::abs(scalar-one[0])<1e-8,"Single graph batch API failed");
   const size_t ng=g.h.size(),total=ng*rows.size();
   std::vector<double> z(total);std::vector<int> codes(total);
   err=paceval_dGetMultipleComputationsResultsExt(g.h.data(),static_cast<unsigned long>(ng),inputs.data(),static_cast<unsigned long>(rows.size()),z.data(),nullptr,nullptr,codes.data());
   require(!err,"Multiple graphs batch API failed");
   bool graphMajor=true,rowMajor=true;
   for(size_t j=0;j<std::min<size_t>(3,rows.size());++j){
    graphMajor &= std::abs(z[j]-one[j])<=1e-8*(1+std::abs(one[j]));
    rowMajor &= std::abs(z[j*ng]-one[j])<=1e-8*(1+std::abs(one[j]));
   }
   require(graphMajor||rowMajor,"Unknown graph batch result layout");
   auto offset=[&](size_t row,size_t graph){return graphMajor?graph*rows.size()+row:row*ng+graph;};
   std::ofstream result(root+"/results/local_sdk_reproduction.csv");result.imbue(std::locale::classic());require(bool(result),"Cannot write result");
   result<<"case_id";for(const auto& graph:model_graphs)result<<','<<graph.id;result<<'\n';
   for(size_t j=0;j<rows.size();++j){
    std::vector<double> ans(ng);for(size_t k=0;k<ng;++k){
     const size_t at=offset(j,k);require(codes[at]==0&&std::isfinite(z[at]),"Graph error/nonfinite result");ans[k]=z[at];
    }
    referenceCheck(rows[j].a,ans);
    result<<rows[j].id;for(double x:ans)result<<','<<numericalText(x);result<<'\n';
   }
   require(bool(result),"Output flush failure");
   std::cout<<"49 synthetic cases evaluated with original paceval SDK.\n";
  }
 }catch(...){paceval_FreeLibrary();throw;}
 require(paceval_FreeLibrary(),"Cannot finalize original SDK");
}
}
int main(int argc,char** argv){
 try {run(argc>1?argv[1]:".",argc>2&&std::string(argv[2])=="--selftest");return 0;}
 catch(const std::exception& e){std::cerr<<"Research execution failed: "<<e.what()<<'\n';return 2;}
}
