// WP13. Original paceval Mathematical Engine, model execution in two math groups.
// The principal physical kernels, full network chain, pressure guards, dispatch
// scores, sensitivities, and logical decisions are genuinely evaluated by
// persistent paceval graphs. Host C++ handles I/O, input validation, dispatch
// case selection, and independent verification (never the published outputs).
// Synthetic steady-state research model. NOT operational heat-network software.
#include "paceval_main.h"
#include "generated_formulas.h"
#include <algorithm>
#include <array>
#include <cmath>
#include <cstddef>
#include <fstream>
#include <iostream>
#include <locale>
#include <regex>
#include <sstream>
#include <stdexcept>
#include <string>
#include <vector>

namespace {
void check(bool ok,const std::string& msg){if(!ok)throw std::runtime_error(msg);}
struct Record {std::string id;std::vector<double> variables;};
struct GraphOwner {
 std::vector<PACEVAL_HANDLE> handles;
 ~GraphOwner(){for(PACEVAL_HANDLE h:handles)if(h)paceval_DeleteComputation(h);}
};
bool isDecimal(const std::string& s){
 static const std::regex r(R"(^[+-]?(?:[0-9]+(?:\.[0-9]*)?|\.[0-9]+)(?:[eE][+-]?[0-9]+)?$)");
 return !s.empty() && s.size()<=80 && std::regex_match(s,r);
}
double parseNumber(const std::string& s,const std::string& location){
 // SDK string conversion can parse expressions, so restrict CSV to numeric literals.
 check(isDecimal(s),"CSV literal rejected at "+location);
 int err=-1; long at=-1; double lower=0,upper=0;
 const double x=paceval_dConvertStringToFloat(s.c_str(),&err,&at,false,&lower,&upper);
 check(err==0 && std::isfinite(x),"Original SDK numeric parser rejected "+location+
       " error="+std::to_string(err)+" position="+std::to_string(at));
 return x;
}
std::string formatNumber(double x){
 check(std::isfinite(x),"Refusing nonfinite result formatting");
 // The original API provides no output buffer length parameter. We initialize a
 // conservative buffer and require a terminated valid numeric literal.
 std::array<char,4096> dst{};
 const int digits=paceval_dConvertFloatToString(dst.data(),x);
 check(digits>0,"paceval number->string conversion error");
 auto it=std::find(dst.begin(),dst.end(),'\0');
 check(it!=dst.end() && it!=dst.begin(),"paceval formatter did not terminate");
 const std::string text(dst.data(),static_cast<size_t>(it-dst.begin()));
 check(isDecimal(text),"paceval float text is not canonical decimal");
 return text;
}
void conversionTest(){
 for(const char* literal: {"0","-0.0",".25","-4.125","1e-9","+2.5E+6","3."}){
  const double v=parseNumber(literal,"selftest");check(isDecimal(formatNumber(v)),"Bad format roundtrip");
 }
 for(const char* invalid:{"","NaN","Inf","1+2","pi","0/0","3,14"," 1.0","0x10","1e99999","2_000"}){
  bool failed=false;try{(void)parseNumber(invalid,"negative selftest");}catch(...){failed=true;}
  check(failed,"Unsafe numeric literal passed parser");
 }
 // The SDK format does NOT promise bitwise lossless double conversion.
}
void operatorTest(){
 struct T{const char* expr; double result;};
 const T tests[]={{"(-1) % 10",-1},{"(-1) mod 10",9},{"4 min 5",4},{"4 max 5",5},
                  {"((x <= (2*y)) AND (z >= 0))",1},
                  {"((NOT(x = y)) OR (z <> 0))",0},
                  {"((x = y) XOR (z <> 0))",1}};
 double sample[]={1,1,0};
 for(const auto& t:tests){
  PACEVAL_HANDLE h=paceval_CreateComputation(t.expr,3,"x y z",false,nullptr);
  check(h && !paceval_GetIsError(h),"Operator expression registration failed");
  const double v=paceval_dGetComputationResult(h,sample,nullptr,nullptr);
  check(!paceval_GetIsError(h) && v==t.result,"Operator semantics test failed");
  paceval_DeleteComputation(h);
 }
}
void validate(const std::vector<double>& a,const bool net){
 for(double x:a)check(std::isfinite(x),"Nonfinite physical input rejected");
 if(!net){
  check(a.size()==edge_N,"Edge variable count mismatch");
  const double m=a[0],cp=a[1],Tin=a[2],Amb=a[3],UA=a[4],Tr=a[5],f=a[7],L=a[8],D=a[9],rho=a[10],eta=a[11];
  check(m>0 && m<=500 && cp>100 && cp<10000 && Tin>Tr && Tin<=160 && Amb>=-40 && Amb<=60 && UA>=0 && UA<=1e7,"Edge heat model domain");
  check(f>=0 && f<1 && L>0 && D>0 && rho>0 && rho<2000 && eta>0 && eta<=1 && a[12]>0 && a[13]>=0,"Edge hydraulic domain");
  check((UA/(m*cp))<1,"Research v1 midpoint model outside stated small-loss domain");
 } else {
  check(a.size()==network_N,"Network variable count mismatch");
  check(a[0]>0 && a[1]>0 && a[2]>100 && a[3]>a[8] && a[3]<160 && a[4]>=-40 && a[4]<=60,"Network mass-temperature domain");
  check(a[5]>=0 && a[6]>=0 && a[7]>=0 && a[9]>a[8] && a[10]>=0 && a[11]>0 && a[12]>0 && a[12]<=1 && a[22]>0,"Network physical/dispatch bounds");
  for(const int j:{15,18,21})check(a[static_cast<size_t>(j)]>0,"Network pipe diameter invalid");
  for(const int j:{14,17,20})check(a[static_cast<size_t>(j)]>0,"Network pipe length invalid");
  for(const int j:{13,16,19})check(a[static_cast<size_t>(j)]>=0 && a[static_cast<size_t>(j)]<1,"Network friction factor invalid");
  check(a[5]/((a[0]+a[1])*a[2])<1 && a[6]/(a[0]*a[2])<1 && a[7]/(a[1]*a[2])<1,"Network midpoint domain invalid");
 }
}
std::vector<Record> readCases(const std::string& filename,const std::string& variables,size_t count,bool net){
 std::ifstream in(filename);in.imbue(std::locale::classic());check(bool(in),"Cannot open CSV: "+filename);
 std::string line;check(bool(std::getline(in,line)),"CSV empty");
 if(!line.empty() && line.back()=='\r')line.pop_back();
 std::string expected=net?"scenario_id":"case_id";
 std::istringstream variableStream(variables);std::string name;
 while(variableStream>>name)expected+=","+name;
 check(line==expected,"CSV input header does not match declared graph variable order");
 std::vector<Record> records;size_t row=1;
 while(std::getline(in,line)){
  ++row;if(!line.empty()&&line.back()=='\r')line.pop_back();check(!line.empty(),"Empty CSV row");
  std::stringstream ss(line);std::string field;std::vector<std::string> cells;
  while(std::getline(ss,field,','))cells.push_back(field);
  check(cells.size()==count+1 && line.back()!=',',"CSV field count mismatch at row "+std::to_string(row));
  Record item;item.id=cells[0];check(!item.id.empty() && item.id.size()<50,"Invalid scenario identifier");
  for(size_t k=1;k<cells.size();++k)item.variables.push_back(parseNumber(cells[k],"row "+std::to_string(row)+" col "+std::to_string(k)));
  validate(item.variables,net);records.push_back(item);
 }
 check(!records.empty() && records.size()<=200000,"No rows or excessive input rows");return records;
}
void verifyEdge(const std::vector<double>& a,const std::vector<double>& z){
 const double m=a[0],cp=a[1],Tin=a[2],Tamb=a[3],UA=a[4],Tr=a[5];
 // Independent C++ oracle: only verification, never publication data generation.
 const double outlet=Tamb+(Tin-Tamb)*std::exp(-UA/(m*cp));
 const double loss=(Tin-outlet)*m*cp;
 const double vel=4*m/(a[10]*3.14159265358979323846*a[9]*a[9]);
 const double press=a[7]*(a[8]/a[9])*a[10]*vel*vel/2;
 auto near=[](double x,double y){return std::fabs(x-y)<=2e-9*(1+std::fabs(y));};
 check(near(outlet,z[1]) && near(loss,z[3]) && near(press,z[7]),"Independent physical edge reference failed");
 check(near(z[4]+z[2],m*cp*(Tin-Tr)),"v1 edge heat balance invariant failed");
 check(near(z[5]+z[3],m*cp*(Tin-Tr)),"v2 edge heat balance invariant failed");
 check(z[14]==0 || z[14]==1,"Nonbinary edge guard");
}
void verifyNetwork(const std::vector<double>& a,const std::vector<double>& z){
 const double ma=a[0],mb=a[1],cp=a[2],Ts=a[3],amb=a[4],Tr=a[8];
 auto pipe=[&](double inlet,double ua,double m){return amb+(inlet-amb)*std::exp(-ua/(m*cp));};
 const double trunk=pipe(Ts,a[5],ma+mb),aa=pipe(trunk,a[6],ma),bb=pipe(trunk,a[7],mb);
 const double del=ma*cp*(aa-Tr)+mb*cp*(bb-Tr);
 const double loss=(ma+mb)*cp*(Ts-trunk)-del;
 const auto near=[](double x,double y){return std::fabs(x-y)<=2e-9*(1+std::fabs(y));};
 check(near(z[13],trunk)&&near(z[14],aa)&&near(z[15],bb)&&near(z[16],del),"Independent network temperature/delivery reference failed");
 check(near(z[17],loss),"Independent network heat-loss reference failed");
 check(near(z[3],z[16]+z[17]),"Network energy balance failed");
 check(near(z[20],0),"Network explicit conservation graph failed");
 check(z[12]==0||z[12]==1,"v1 network guard nonbinary");
 check(z[21]==0||z[21]==1,"v2 network guard nonbinary");
 check((z[21]==1)==(z[18]>=0&&z[19]>=0&&z[2]>=0),"Network decision mismatch");
}
template<size_t GraphCount>
void processGroup(const std::string& root,const std::string& group,const std::string& variables,
                  size_t nvars,const std::array<GraphFormula,GraphCount>& formulas){
 const bool net=(group=="network");
 auto rows=readCases(root+"/examples/synthetic_"+(net?"network_dispatch":"edge_grid")+".csv",variables,nvars,net);
 GraphOwner graphs;
 for(const auto& f:formulas){
  const auto h=paceval_CreateComputation(f.expression,static_cast<unsigned long>(nvars),variables.c_str(),true,nullptr);
  check(h && !paceval_GetIsError(h),std::string("Graph creation failure: ")+f.id);
  graphs.handles.push_back(h);
 }
 std::vector<double> input;input.reserve(rows.size()*nvars);
 for(const Record& r:rows)input.insert(input.end(),r.variables.begin(),r.variables.end());
 // Two independent SDK paths test layout: scalar, one-graph batch, multi-graph batch.
 const double scalar=paceval_dGetComputationResult(graphs.handles[0],rows[0].variables.data(),nullptr,nullptr);
 check(!paceval_GetIsError(graphs.handles[0]),"Original scalar graph evaluation failed");
 std::vector<double> single(rows.size()),singleLo(rows.size()),singleHi(rows.size());std::vector<int> singleErr(rows.size());
 const bool singleFail=paceval_dGetComputationResultExt(graphs.handles[0],input.data(),static_cast<unsigned long>(rows.size()),single.data(),singleLo.data(),singleHi.data(),singleErr.data());
 check(!singleFail && !singleErr[0] && std::fabs(scalar-single[0])<1e-10,"Original single-graph batch layout/test failed");
 const size_t total=rows.size()*GraphCount;
 std::vector<double> output(total),lower(total),upper(total);std::vector<int> errs(total);
 const bool multiFail=paceval_dGetMultipleComputationsResultsExt(graphs.handles.data(),static_cast<unsigned long>(GraphCount),input.data(),static_cast<unsigned long>(rows.size()),output.data(),lower.data(),upper.data(),errs.data());
 check(!multiFail,"Original multi-graph batch evaluation failed");
 // SDK builds can expose different matrix output order: determine via first 2 rows.
 bool graphMajor=true,rowMajor=true;
 for(size_t j=0;j<std::min(rows.size(),size_t(3));++j){
  graphMajor=graphMajor && std::fabs(output[j]-single[j])<=1e-8*(1+std::fabs(single[j]));
  rowMajor=rowMajor && std::fabs(output[j*GraphCount]-single[j])<=1e-8*(1+std::fabs(single[j]));
 }
 check(graphMajor||rowMajor,"Unknown SDK batch output layout");
 const auto index=[&](size_t row,size_t g){return graphMajor?g*rows.size()+row:row*GraphCount+g;};
 std::ofstream out(root+"/results/local_sdk_"+group+".csv");out.imbue(std::locale::classic());
 check(bool(out),"Cannot open SDK result file");
 out<<(net?"scenario_id":"case_id");for(const auto& f:formulas)out<<','<<f.id;out<<'\n';
 for(size_t j=0;j<rows.size();++j){
  std::vector<double> z(GraphCount);
  for(size_t k=0;k<GraphCount;++k){size_t offset=index(j,k);
   check(errs[offset]==0,"Per-value graph execution failed");
   check(std::isfinite(output[offset]) && std::isfinite(lower[offset]) && std::isfinite(upper[offset]),"Nonfinite graph output or TINC bound");
   check(lower[offset]<=output[offset] && output[offset]<=upper[offset],"SDK local TINC output ordering failed");
   z[k]=output[offset];
  }
  if(net)verifyNetwork(rows[j].variables,z);else verifyEdge(rows[j].variables,z);
  out<<rows[j].id;for(double v:z)out<<','<<formatNumber(v);out<<'\n';
 }
 check(bool(out),"Cannot finish result CSV");
 std::cout<<group<<": original paceval graphs, independent model tests, CSV output verified ("
          <<rows.size()<<" synthetic scenarios)\n";
}
void run(const std::string& root,bool selftest){
 check(paceval_InitializeLibrary(nullptr),"Original paceval runtime not initialized");
 try{
  conversionTest();operatorTest();
  if(!selftest){
   processGroup(root,"edge",edge_variables,edge_N,edge_graphs);
   processGroup(root,"network",network_variables,network_N,network_graphs);
  }else std::cout<<"Original SDK conversion and operator selftests passed\n";
 }catch(...){paceval_FreeLibrary();throw;}
 check(paceval_FreeLibrary(),"Original paceval runtime did not shut down");
}
} // namespace
int main(int argc,char** argv){
 try{run(argc>1?argv[1]:".",argc>2 && std::string(argv[2])=="--selftest");return 0;}
 catch(const std::exception& e){std::cerr<<"District heating research execution failed: "<<e.what()<<'\n';return 2;}
}
