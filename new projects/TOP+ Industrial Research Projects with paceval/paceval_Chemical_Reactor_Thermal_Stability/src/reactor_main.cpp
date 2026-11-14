// WP04 Chemical Reactor Thermal Stability Screening.
// Genuine paceval graph execution, double precision, SDK 4.25, Linux.
// C++ only orchestrates graph lifetime, input schemas, root bracketing,
// Runge-Kutta time integration, independent audits, selection and I/O.
// This synthetic first-order liquid CSTR model is NOT a process-safety certificate.
#include "paceval_main.h"
#include <array>
#include <algorithm>
#include <cmath>
#include <cstring>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <limits>
#include <map>
#include <regex>
#include <sstream>
#include <stdexcept>
#include <string>
#include <vector>
#include <filesystem>

namespace fs=std::filesystem;
namespace {
constexpr double R=8.31446261815324;
const std::vector<std::string> VAR={"T","C","Cin","Tin","Tc","tau","kref","Ea","Tref","rhoCp","H","UA","V","alpha","Tlim","Rg"};
const std::vector<std::string> JVAR={"a","b","c","d","T","C","Cin","Tin","Tlim","tau"};
std::string join(const std::vector<std::string>& v){std::string s;for(auto &x:v){if(!s.empty())s+=' ';s+=x;}return s;}
void require(bool ok,const std::string& msg){if(!ok)throw std::runtime_error(msg);}
void same(double actual,double expected,double rel=2e-10,double abs=2e-12){
 require(std::isfinite(actual)&&std::isfinite(expected)&&std::abs(actual-expected)<=abs+rel*std::max(std::abs(actual),std::abs(expected)),
 "Numerical check failed: actual="+std::to_string(actual)+" expected="+std::to_string(expected));
}
std::string csvEscape(const std::string& s){return s;}
std::string fmt(double v){
 require(std::isfinite(v),"Nonfinite numeric output");
 char b[512]{};int precision=paceval_dConvertFloatToString(b,v);
 require(precision>0 && b[0],"paceval float-to-text failed");
 // The SDK conversion is a presentation format; binary doubles remain in memory for audits.
 const std::string res(b);require(res.find(',')==std::string::npos && res.find('\n')==std::string::npos,"Unexpected SDK CSV decimal separator");
 return res;
}
bool decimalLiteral(const std::string& s){
 static const std::regex pattern(R"(^[+-]?(?:[0-9]+(?:\.[0-9]*)?|\.[0-9]+)(?:[eE][+-]?[0-9]+)?$)");
 return std::regex_match(s,pattern);
}
double parseDecimal(const std::string& s){
 require(decimalLiteral(s),"Rejected invalid numeric literal: "+s);
 int err=-1;long pos=-1;double v=paceval_dConvertStringToFloat(s.c_str(),&err,&pos,false,nullptr,nullptr);
 require(err==PACEVAL_ERR_NO_ERROR&&std::isfinite(v),"paceval text-to-float failed for: "+s+" err="+std::to_string(err));
 return v;
}
struct Engine{
 std::vector<PACEVAL_HANDLE> handles;
 unsigned long scalarCalls=0,batchCalls=0,pointEvaluations=0,scalarEvaluations=0;
 Engine(){require(paceval_InitializeLibrary(nullptr),"paceval_InitializeLibrary failed");}
 ~Engine(){for(auto h:handles)if(h)paceval_DeleteComputation(h);paceval_FreeLibrary();}
 PACEVAL_HANDLE add(const std::string& expr,const std::vector<std::string>& names){
  PACEVAL_HANDLE h=paceval_CreateComputation(expr.c_str(),names.size(),join(names).c_str(),false,nullptr);
  require(h && !paceval_GetIsError(h),"Cannot create paceval graph: "+expr);
  handles.push_back(h);return h;
 }
 double scalar(PACEVAL_HANDLE h,std::vector<double> v){
  double y=paceval_dGetComputationResult(h,v.data(),nullptr,nullptr);scalarCalls++;scalarEvaluations++;
  require(!paceval_GetIsError(h)&&std::isfinite(y),"paceval scalar evaluation failed");return y;
 }
 // Detect the SDK layout with an independent non-symmetric two-graph probe.
 // The SDK accepts point-major inputs, but we empirically check output orientation.
 bool resultGraphMajor=false;
 void calibrate(){
  auto h1=add("x+2*y",{"x","y"});auto h2=add("3*x-y",{"x","y"});
  double v[]={1,2,4,7}; double out[4]={},lo[4]={},hi[4]={};int e[4]={};PACEVAL_HANDLE hs[]={h1,h2};
  bool ok=paceval_dGetMultipleComputationsResultsExt(hs,2,v,2,out,lo,hi,e);
  // SDK returns false when no error; the error array and individual graph states are authoritative.
  require(!ok,"Multi-graph probe reported an API error");
  for(int z:e) require(z==0,"Multi-graph probe returned a graph error");
  if(std::abs(out[0]-5)<1e-7&&std::abs(out[1]-18)<1e-7&&std::abs(out[2]-1)<1e-7&&std::abs(out[3]-5)<1e-7)resultGraphMajor=true;
  else if(std::abs(out[0]-5)<1e-7&&std::abs(out[1]-1)<1e-7&&std::abs(out[2]-18)<1e-7&&std::abs(out[3]-5)<1e-7)resultGraphMajor=false;
  else throw std::runtime_error("Unsupported SDK multi-graph output arrangement");
  batchCalls++;pointEvaluations+=4;
 }
 std::vector<std::vector<double>> multi(const std::vector<PACEVAL_HANDLE>& hs,const std::vector<std::vector<double>>& vv,size_t nvars){
  require(!hs.empty()&&!vv.empty(),"Empty batch");
  std::vector<double> in;in.reserve(vv.size()*nvars);
  for(auto& row:vv){require(row.size()==nvars,"Bad batch variable count");for(double x:row)require(std::isfinite(x),"Nonfinite input before engine call");in.insert(in.end(),row.begin(),row.end());}
  std::vector<double> raw(hs.size()*vv.size()),lo(raw.size()),hi(raw.size());
  std::vector<int> err(raw.size(),-1);
  bool apiError=paceval_dGetMultipleComputationsResultsExt(const_cast<PACEVAL_HANDLE*>(hs.data()),hs.size(),in.data(),vv.size(),raw.data(),lo.data(),hi.data(),err.data());
  require(!apiError,"paceval multi-graph batch reported an error");
  for(int z:err)require(z==0,"paceval multi-graph batch element error "+std::to_string(z));
  batchCalls++;pointEvaluations+=raw.size();
  std::vector<std::vector<double>> result(vv.size(),std::vector<double>(hs.size()));
  for(size_t j=0;j<vv.size();++j)for(size_t k=0;k<hs.size();++k){
    auto idx=resultGraphMajor?k*vv.size()+j:j*hs.size()+k;
    require(std::isfinite(raw[idx]),"Nonfinite paceval batch result");result[j][k]=raw[idx];
  }
  return result;
 }
};
struct Scenario{
 std::string id;double Tc,UA,Ea,kref,tau,Cin,Tin,V,rhoCp,H,Tref,alpha,Tlim;
 std::vector<double> x(double T,double C)const{return {T,C,Cin,Tin,Tc,tau,kref,Ea,Tref,rhoCp,H,UA,V,alpha,Tlim,R};}
};
std::vector<std::string> splitCsv(const std::string& s){
 std::vector<std::string> v;std::stringstream ss(s);std::string f;
 while(std::getline(ss,f,','))v.push_back(f);
 if(!s.empty()&&s.back()==',')v.push_back("");return v;
}
std::vector<Scenario> readScenarios(const fs::path& path){
 std::ifstream in(path);require(bool(in),"Cannot read input CSV: "+path.string());std::string line;
 require(bool(std::getline(in,line)),"Missing CSV header");
 require(line=="scenario_id,Tc,UA,Ea,kref,tau,Cin,Tin,V,rhoCp,H,Tref,alpha,Tlim","Unexpected input CSV schema");
 std::vector<Scenario> out;size_t row=1;
 while(std::getline(in,line)){++row;require(!line.empty()&&line.back()!='\r',"CRLF not allowed: line "+std::to_string(row));
  auto fields=splitCsv(line);require(fields.size()==14,"Wrong CSV field count, row "+std::to_string(row));
  require(std::regex_match(fields[0],std::regex("[A-Za-z][A-Za-z0-9_]{0,32}")),"Bad scenario ID");
  Scenario s;s.id=fields[0];double* dest[]={&s.Tc,&s.UA,&s.Ea,&s.kref,&s.tau,&s.Cin,&s.Tin,&s.V,&s.rhoCp,&s.H,&s.Tref,&s.alpha,&s.Tlim};
  for(size_t j=1;j<14;++j)try{*dest[j-1]=parseDecimal(fields[j]);}catch(const std::exception&e){throw std::runtime_error("row "+std::to_string(row)+" column "+std::to_string(j+1)+": "+e.what());}
  require(s.Tc>250&&s.Tc<400&&s.Tin>250&&s.Tin<400&&s.Tlim>s.Tin&&s.Tlim<500,"Temperature domain");
  require(s.kref>0&&s.Ea>0&&s.Ea<300000&&s.tau>0&&s.Cin>0&&s.V>0&&s.rhoCp>0&&s.H>0&&s.Tref>0,"Kinetic/volume domain");
  require(s.UA>=0&&s.alpha>=0&&s.alpha<=0.01&&1+s.alpha*(276-s.Tref)>0,"Cooling parameter and positive-UA domain");
  out.push_back(s);
 }
 require(!out.empty()&&out.size()<=10000,"Scenario count out of supported range");return out;
}
// Closed forms below are independently derived from coupled balances.
// All physically significant terms are evaluated by persistent paceval graphs.
struct Native{
 static double rate(const Scenario&s,double T){return s.kref*std::exp((-s.Ea/R)*(1/T-1/s.Tref));}
 static double uaf(const Scenario&s,double T,int ver){return s.UA*(ver==1?1.0:1+s.alpha*(T-s.Tref));}
 static double ceq(const Scenario&s,double T){double k=rate(s,T);return s.Cin/(1+s.tau*k);}
 static double dc(const Scenario&s,double T,double C){return (s.Cin-C)/s.tau-rate(s,T)*C;}
 static double dt(const Scenario&s,double T,double C,int v){return (s.Tin-T)/s.tau+(s.H/s.rhoCp)*rate(s,T)*C-uaf(s,T,v)/(s.rhoCp*s.V)*(T-s.Tc);}
 static double fred(const Scenario&s,double T,int v){return dt(s,T,ceq(s,T),v);}
 static std::array<double,4> jac(const Scenario&s,double T,double C,int v){
  auto k=rate(s,T),kt=k*s.Ea/(R*T*T);
  return {-1/s.tau-k,-C*kt,s.H/s.rhoCp*k,-1/s.tau+s.H/s.rhoCp*C*kt-s.UA/(s.rhoCp*s.V)*(v==1?1.0:1+s.alpha*(2*T-s.Tref-s.Tc))};
 }
};
struct Formula{std::string id,version,units,expr,purpose;PACEVAL_HANDLE h=nullptr;bool executed=false;};
struct Models{
 Engine& engine;std::vector<Formula> formulas;std::map<std::string,size_t> ids;
 explicit Models(Engine& e):engine(e){
  const std::string k="(kref*exp((-Ea/Rg)*((1/T)-(1/Tref))))";
  const std::string ceq="(Cin/(1+(tau*"+k+")))";
  auto add=[&](std::string id,std::string v,std::string units,std::string expr,std::string purpose,const std::vector<std::string>& names=VAR){
   auto h=engine.add(expr,names);ids[id]=formulas.size();formulas.push_back({id,v,units,expr,purpose,h,false});
  };
  add("K_RATE","common","1/s",k,"Arrhenius kinetic constant");
  add("REACTION_RATE","common","mol/(m3 s)",k+"*C","First-order reaction rate");
  add("Q_GEN","common","W","H*V*"+k+"*C","Reaction heat power");
  add("F_C","common","mol/(m3 s)","((Cin-C)/tau)-"+k+"*C","Species-state derivative");
  add("C_EQ","common","mol/m3",ceq,"Steady species concentration");
  add("J11","common","1/s","(-1/tau)-"+k,"Jacobian species sensitivity to species");
  add("J12","common","mol/(m3 s K)","(-C)*"+k+"*(Ea/(Rg*T*T))","Jacobian species sensitivity to heat");
  add("J21","common","K m3/(mol s)","(H/rhoCp)*"+k,"Jacobian heat sensitivity to species");
  add("DK_DT","common","1/(s K)",k+"*(Ea/(Rg*T*T))","Temperature dependence of kinetics");
  add("DQ_DT","common","W/K","H*V*C*"+k+"*(Ea/(Rg*T*T))","Partial thermal sensitivity at fixed concentration");
  add("Q_FLOW","common","W","(rhoCp*V*(Tin-T)/tau)","Sensible enthalpy flow contribution");
  add("CONVERSION","common","1","1-(C/Cin)","Reactant conversion");
  add("DAMKOHLER","common","1","tau*"+k,"First-order residence-time Damkohler number");
  add("DELTA_REM","common","W","UA*alpha*(T-Tref)*(T-Tc)","Cooling duty V2 minus V1");
  add("DELTA_FRED","common","K/s","(-UA*alpha*(T-Tref)*(T-Tc))/(rhoCp*V)","Reduced energy residual V2 minus V1");
  for(int v=1;v<=2;++v){
   std::string tag=v==1?"V1":"V2";
   std::string ua=v==1?"UA":"(UA*(1+(alpha*(T-Tref))))";
   std::string duadT=v==1?"1":"(1+(alpha*((2*T)-Tref-Tc)))";
   std::string loss="("+ua+"*(T-Tc))";
   std::string heat="(((Tin-T)/tau)+((H/rhoCp)*"+k+"*C)-("+loss+"/(rhoCp*V)))";
   std::string red="(((Tin-T)/tau)+((H/rhoCp)*"+k+"*"+ceq+")-("+loss+"/(rhoCp*V)))";
   add(tag+"_Q_REM",tag,"W",loss,"Cooling duty");
   add(tag+"_F_T",tag,"K/s",heat,"Energy-state derivative");
   add(tag+"_F_RED",tag,"K/s",red,"Reduced steady thermal residual");
   add(tag+"_J22",tag,"1/s","(-1/tau)+((H/rhoCp)*C*"+k+"*(Ea/(Rg*T*T)))-((UA/(rhoCp*V))*"+duadT+")","Full thermal Jacobian diagonal");
   add(tag+"_D_T_D_UA",tag,"K/(s (W/K))","(-("+(v==1?std::string("1"):std::string("(1+(alpha*(T-Tref)))"))+"*(T-Tc))/(rhoCp*V))","Partial heat ODE sensitivity to UA");
   add(tag+"_D_T_D_TC",tag,"1/s","("+ua+"/(rhoCp*V))","Partial heat ODE sensitivity to coolant temperature");
  }
  add("J_TRACE","stage2","1/s","a+d","Jacobian trace",JVAR);
  add("J_DET","stage2","1/s2","a*d-b*c","Jacobian determinant",JVAR);
  add("EIG_MAX_RE","stage2","1/s","((a+d)/2)+(sqrt((((a+d)^2)-(4*(a*d-b*c))) max 0)/2)","Largest eigenvalue real part",JVAR);
  add("MARG_TRACE","stage2","1","(-tau*(a+d))","Trace stability margin",JVAR);
  add("MARG_DET","stage2","1","(tau*tau*(a*d-b*c))","Determinant stability margin",JVAR);
  add("MARG_TEMP","stage2","K","Tlim-T","Illustrative temperature threshold margin",JVAR);
  add("SCREEN_SCORE","stage2","1","((((Tlim-T)/(Tlim-Tin)) min (-tau*(a+d))) min (tau*tau*(a*d-b*c)))","Composite screening score with positive margins",JVAR);
  add("SCREEN_GUARD","stage2","0/1","(((a+d)<0) AND ((a*d-b*c)>0) AND (T<=Tlim) AND (C>=0) AND (C<=Cin))","Combined mathematical screening condition",JVAR);
 }
 Formula& at(const std::string&s){return formulas.at(ids.at(s));}
 double eval(const std::string&s,const std::vector<double>& x){auto& f=at(s);double v=engine.scalar(f.h,x);f.executed=true;return v;}
 std::vector<std::vector<double>> batch(const std::vector<std::string>& names,const std::vector<std::vector<double>>& x,size_t nv){
  std::vector<PACEVAL_HANDLE> hs;for(auto& name:names){auto& f=at(name);f.executed=true;hs.push_back(f.h);}return engine.multi(hs,x,nv);
 }
};
std::vector<std::string> stage1Names(int v){
 std::string t=v==1?"V1_":"V2_";
 return {"K_RATE","REACTION_RATE","Q_GEN","F_C","C_EQ","J11","J12","J21","DK_DT","DQ_DT",t+"Q_REM",t+"F_T",t+"F_RED",t+"J22",t+"D_T_D_UA",t+"D_T_D_TC",
 "Q_FLOW","CONVERSION","DAMKOHLER","DELTA_REM","DELTA_FRED"};
}
const std::vector<std::string> stage2Names={"J_TRACE","J_DET","EIG_MAX_RE","MARG_TRACE","MARG_DET","MARG_TEMP","SCREEN_SCORE","SCREEN_GUARD"};
struct Root{std::string sid;int v;double T,C,f,a,b,c,d,tr,det,eig,score,guard;};
std::array<double,10> secondX(double T,double C,const Scenario&s,const std::vector<double>& stage){
 return {stage[5],stage[6],stage[7],stage[13],T,C,s.Cin,s.Tin,s.Tlim,s.tau};
}
Root makeRoot(Models& m,const Scenario&s,int ver,double T){
 auto x=s.x(T,0); // The actual concentration is computed solely by the paceval C_EQ graph.
 x[1]=m.eval("C_EQ",x);
 auto first=m.batch(stage1Names(ver),{x},VAR.size())[0];
 auto sj=secondX(T,x[1],s,first);
 std::vector<std::vector<double>> vx={std::vector<double>(sj.begin(),sj.end())};
 auto second=m.batch(stage2Names,vx,JVAR.size())[0];
 return {s.id,ver,T,x[1],first[12],first[5],first[6],first[7],first[13],second[0],second[1],second[2],second[6],second[7]};
}
std::vector<Root> solveRoots(Models& m,const Scenario&s,int ver){
 constexpr double low=276.0,step=0.5;constexpr int count=269; // 276 ... 410 K
 std::vector<std::vector<double>> xs;xs.reserve(count+1);
 for(int i=0;i<=count;++i)xs.push_back(s.x(low+i*step,0));
 auto vv=m.batch({ver==1?"V1_F_RED":"V2_F_RED"},xs,VAR.size());
 std::vector<Root> roots;std::string id=ver==1?"V1_F_RED":"V2_F_RED";
 for(int i=1;i<=count;++i){
  double fa=vv[i-1][0],fb=vv[i][0];
  if(fa*fb>0&&fa!=0&&fb!=0)continue;
  double a=low+(i-1)*step,b=low+i*step;
  if(fa==0){b=a;}
  else if(fb==0){a=b;}
  else if(fa*fb<0){
    for(int n=0;n<48;++n){double mid=(a+b)/2;double fm=m.eval(id,s.x(mid,0));if(fa*fm<=0){b=mid;fb=fm;}else{a=mid;fa=fm;}}
  }
  double rt=(a+b)/2;
  if(!roots.empty()&&std::abs(roots.back().T-rt)<1e-5)continue;
  auto root=makeRoot(m,s,ver,rt);
  require(std::abs(root.f)<2e-10,"Bisection root did not satisfy reduced residual");
  require(std::abs(m.eval("F_C",s.x(rt,root.C)))<2e-10,"Species steady-state residual failed");
  require(std::abs(m.eval(ver==1?"V1_F_T":"V2_F_T",s.x(rt,root.C)))<2e-10,"Energy steady-state residual failed");
  roots.push_back(root);
 }
 return roots;
}
// Compact test of documented SDK operators and both numeric conversion routines.
void selftest(){
 Engine e;e.calibrate();Models m(e);
 auto operatorTest=[&](std::string ex,double expected){auto h=e.add(ex,{"x","y","z"});same(e.scalar(h,{1,2,0}),expected,0,1e-12);};
 operatorTest("(-1)%10",-1);operatorTest("(-1) mod 10",9);
 operatorTest("(4 min 5)",4);operatorTest("(4 max 5)",5);
 operatorTest("((x<y) AND (x<=y) AND (y>=x) AND (y<>x) AND NOT(z))",1);
 operatorTest("((x=y) OR (x<y))",1);
 operatorTest("((abs(x) <= (2*y)) AND (z >= 0))",1);
 operatorTest("((x=y) XOR (x<y))",1);
 for(auto literal: {"0","-0.125","+1.25e-4","340.125","1E+5",".5","2."}){
  double v=parseDecimal(literal);std::string encoded=fmt(v);require(decimalLiteral(encoded),"SDK encoder did not produce canonical numeric literal");
  same(parseDecimal(encoded),v,1e-13,1e-16);
 }
 for(auto bad:{"","1+2","3,14","NaN","Inf","1e99999","0xFF"," 12","12 ","1;2","a","--3"}){
  bool rejected=false;try{(void)parseDecimal(bad);}catch(...){rejected=true;}
  require(rejected,"Unsafe input accepted: "+std::string(bad));
 }
 Scenario s={"TEST",295,16000,80000,.02,150,3000,300,2,4e6,100000,340,.002,345};
 for(int ver=1;ver<=2;++ver)for(double T:{285.,310.,330.,360.,390.})for(double C:{0.,100.,1000.,2500.}){
  auto x=s.x(T,C);const std::string prefix=ver==1?"V1_":"V2_";
  same(m.eval("K_RATE",x),Native::rate(s,T));
  same(m.eval("F_C",x),Native::dc(s,T,C));
  same(m.eval(prefix+"F_T",x),Native::dt(s,T,C,ver));
  same(m.eval(prefix+"F_RED",x),Native::fred(s,T,ver));
  same(m.eval("Q_FLOW",x),s.rhoCp*s.V*(s.Tin-T)/s.tau);
  same(m.eval("CONVERSION",x),1-C/s.Cin);
  same(m.eval("DAMKOHLER",x),s.tau*Native::rate(s,T));
  same(m.eval("DELTA_FRED",x),Native::fred(s,T,2)-Native::fred(s,T,1));
  auto J=Native::jac(s,T,C,ver);
  for(int i=0;i<3;++i)same(m.eval(std::string("J")+(i==0?"11":i==1?"12":"21"),x),J[i]);
  same(m.eval(prefix+"J22",x),J[3]);
 }
 auto roots=solveRoots(m,s,1);require(roots.size()==3,"Baseline three-equilibrium regression failed");
 require(roots[0].tr<0&&roots[0].det>0 && roots[1].det<0 && roots[2].tr<0&&roots[2].det>0,"Coupled Jacobian stability branches incorrect");
 auto b=m.batch({"K_RATE","F_C","V1_F_T"},{s.x(320,1000),s.x(340,1500),s.x(360,500)},VAR.size());
 same(b[0][0],Native::rate(s,320));same(b[1][1],Native::dc(s,340,1500));same(b[2][2],Native::dt(s,360,500,1));
 std::cout<<"SELFTEST PASS: original SDK, multi-graph layout, operators, numeric CSV literals, native reference, coupled-Jacobian stability, 3-root case\n";
}
// High-precision reference script is separate from this independent native C++ check.
void run(Models& m,const fs::path& input,const fs::path& out){
 fs::create_directories(out);auto scenarios=readScenarios(input);Engine& e=m.engine;
 std::ofstream roots(out/"equilibria.csv"),profile(out/"profile.csv"),surface(out/"scenario_surface.csv"),plane(out/"phase_plane.csv"),traj(out/"trajectories.csv"),audit(out/"native_audit.csv");
 require(roots&&profile&&surface&&plane&&traj&&audit,"Cannot create output CSV files");
 roots<<"scenario_id,model,root_T_K,C_mol_m3,F_reduced_K_s,trace_s_inv,det_s_inv2,max_real_eigen_s_inv,screen_score,screen_guard\n";
 profile<<"model,T_K,Ceq_mol_m3,heat_generation_W,heat_removal_W,reduced_energy_K_s,trace_s_inv,det_s_inv2,dQgen_dT_W_per_K,dT_dUA_K_s_per_W_K,dT_dTc_per_s,Qflow_W,conversion,Damkohler,delta_cooling_W,delta_energy_K_s\n";
 surface<<"scenario_id,model,Tc_K,UA_W_per_K,root_count,stable_count,stable_below_limit_count,lowest_root_K,highest_root_K\n";
 plane<<"model,T_K,C_mol_m3,dC_dt_mol_m3_s,dT_dt_K_s\n";
 traj<<"model,initial_case,time_s,T_K,C_mol_m3\n";
 audit<<"formula,model,T_K,C_mol_m3,paceval_value,native_reference,abs_error\n";
 std::vector<std::string> base1=stage1Names(1),base2=stage1Names(2);
 std::vector<Root> baseRoots1,baseRoots2;size_t rootTotal=0,stableTotal=0,referenceChecks=0;
 Scenario baseline=scenarios.at(scenarios.size()/2); // generator middle is Tc=295 and UA=16000
 for(auto& s:scenarios)for(int ver:{1,2}){
  auto rr=solveRoots(m,s,ver);rootTotal+=rr.size();
  int stable=0,inside=0;
  for(auto& r:rr){
   roots<<r.sid<<","<<r.v<<","<<fmt(r.T)<<","<<fmt(r.C)<<","<<fmt(r.f)<<","<<fmt(r.tr)<<","<<fmt(r.det)<<","<<fmt(r.eig)<<","<<fmt(r.score)<<","<<fmt(r.guard)<<"\n";
   if(r.tr<0&&r.det>0){++stable;if(r.T<=s.Tlim)++inside;}++stableTotal;
  }
  surface<<s.id<<","<<ver<<","<<fmt(s.Tc)<<","<<fmt(s.UA)<<","<<rr.size()<<","<<stable<<","<<inside<<","<<(rr.empty()?"":fmt(rr.front().T))<<","<<(rr.empty()?"":fmt(rr.back().T))<<"\n";
  if(s.id==baseline.id){if(ver==1)baseRoots1=rr;else baseRoots2=rr;}
 }
 require(baseRoots1.size()==3,"Chosen baseline does not yield 3 equilibria");
 for(int ver:{1,2}){
  auto& s=baseline;
  std::string p=ver==1?"V1_":"V2_";
  // Produce an actual multi-graph temperature profile for the scientific figures.
  std::vector<std::vector<double>> inputs;for(int i=0;i<=270;++i)inputs.push_back(s.x(275+0.5*i,0));
  auto eq=m.batch({"C_EQ"},inputs,VAR.size());
  for(size_t j=0;j<inputs.size();++j)inputs[j][1]=eq[j][0];
  auto out1=m.batch(stage1Names(ver),inputs,VAR.size());
  std::vector<std::vector<double>> jinput;
  for(size_t j=0;j<inputs.size();++j){auto js=secondX(inputs[j][0],inputs[j][1],s,out1[j]);jinput.emplace_back(js.begin(),js.end());}
  auto out2=m.batch(stage2Names,jinput,JVAR.size());
  for(size_t j=0;j<inputs.size();++j){
   profile<<ver<<","<<fmt(inputs[j][0])<<","<<fmt(inputs[j][1])<<","<<fmt(out1[j][2])<<","<<fmt(out1[j][10])<<","<<fmt(out1[j][12])<<","<<fmt(out2[j][0])<<","<<fmt(out2[j][1])<<","<<fmt(out1[j][9])<<","<<fmt(out1[j][14])<<","<<fmt(out1[j][15])<<","<<fmt(out1[j][16])<<","<<fmt(out1[j][17])<<","<<fmt(out1[j][18])<<","<<fmt(out1[j][19])<<","<<fmt(out1[j][20])<<"\n";
  }
  // True paceval-computed 2D phase-plane vector field.
  std::vector<std::vector<double>> field;
  for(int i=0;i<=45;++i)for(int j=0;j<=35;++j)field.push_back(s.x(285+i*2.5,j*85));
  const auto vals=m.batch({"F_C",p+"F_T"},field,VAR.size());
  for(size_t i=0;i<field.size();++i)plane<<ver<<","<<fmt(field[i][0])<<","<<fmt(field[i][1])<<","<<fmt(vals[i][0])<<","<<fmt(vals[i][1])<<"\n";
  // Integrator is explicitly the host's job; every RHS evaluation is paceval.
  const auto rhs=[&](double T,double C){
   auto xx=s.x(T,C);return std::array<double,2>{m.eval(p+"F_T",xx),m.eval("F_C",xx)};
  };
  int caseIndex=0;for(auto init:std::vector<std::array<double,2>>{{303,2850},{326,900},{353,100}}){
   double T=init[0],C=init[1],dt=1.0;std::string name="IC"+std::to_string(++caseIndex);
   for(int i=0;i<=700;++i){
    if(i%5==0)traj<<ver<<","<<name<<","<<fmt(i*dt)<<","<<fmt(T)<<","<<fmt(C)<<"\n";
    if(i==700)break;
    auto a=rhs(T,C),b=rhs(T+dt*a[0]/2,C+dt*a[1]/2),c=rhs(T+dt*b[0]/2,C+dt*b[1]/2),d=rhs(T+dt*c[0],C+dt*c[1]);
    double tn=T+dt*(a[0]+2*b[0]+2*c[0]+d[0])/6;
    double cn=C+dt*(a[1]+2*b[1]+2*c[1]+d[1])/6;
    require(tn>=270&&tn<=410&&cn>=-0.001&&cn<=s.Cin+0.001,"RK4 state left calibrated model domain");
    T=tn;C=cn;
   }
  }
  // Native C++ independent direct evaluation at fixed, publicly reproducible points.
  for(double T:{290.,300.,310.,325.,340.,360.,390.})for(double C:{50.,900.,1800.}){
   auto xx=s.x(T,C);const std::array<std::pair<std::string,double>,4> test={{{"K_RATE",Native::rate(s,T)},
    {"F_C",Native::dc(s,T,C)},{p+"F_T",Native::dt(s,T,C,ver)},{p+"F_RED",Native::fred(s,T,ver)}}};
   for(const auto& item:test){double y=m.eval(item.first,xx);same(y,item.second,3e-9,3e-12);
    audit<<item.first<<","<<ver<<","<<fmt(T)<<","<<fmt(C)<<","<<fmt(y)<<","<<fmt(item.second)<<","<<fmt(std::abs(y-item.second))<<"\n";++referenceChecks;
   }
  }
 }
 // Formula inventory and source of truth for executed results.
 std::ofstream inv(out/"math_execution_inventory.csv"),manifest(out/"formula_manifest.csv"),ev(out/"execution_evidence.json");
 inv<<"function_id,domain_quantity,mathematical_definition,units,execution_owner,paceval_graph_id,formula_version,api_path,reference_test,status,host_reason\n";
 manifest<<"graph_id,version,variables,expression,units\n";
 int actual=0;for(const auto &g:m.formulas){
  if(g.executed)++actual;
  inv<<g.id<<","<<g.purpose<<",\""<<g.expr<<"\","<<g.units<<",paceval,"<<g.id<<","<<g.version<<",paceval_dGetMultipleComputationsResultsExt / paceval_dGetComputationResult,native C++ + mpmath,"<<(g.executed?"executed":"registered_only")<<",\n";
  manifest<<g.id<<","<<g.version<<","<<((g.version=="stage2")?join(JVAR):join(VAR))<<",\""<<g.expr<<"\","<<g.units<<"\n";
 }
 inv<<"ROOT_SCAN,Bracket root search,sign-change brackets,K,host,,both,C++ bisection,independent SciPy,executed,Stateful bracketing solver\n";
 inv<<"TIME_RK4,Transient trajectories,Runge Kutta time integration,s,host,,both,C++ RK4,independent solve_ivp,executed,Temporal state integration\n";
 ev<<"{\n  \"engine\": \"original paceval 4.25 SDK and supplied Linux ELF shared object\",\n";
 ev<<"  \"main_run\": {\"unique_graphs_created\": "<<e.handles.size()<<", \"unique_domain_graphs_created\": "<<m.formulas.size()<<", \"unique_domain_graphs_executed\": "<<actual<<", \"scalar_calls\": "<<e.scalarCalls<<", \"batch_calls\": "<<e.batchCalls<<", \"graph_point_evaluations_batch\": "<<e.pointEvaluations<<", \"graph_point_evaluations_scalar\": "<<e.scalarEvaluations<<", \"scenario_count\": "<<scenarios.size()<<", \"model_scenario_count\": "<<scenarios.size()*2<<", \"equilibrium_roots\": "<<rootTotal<<", \"native_reference_checks\": "<<referenceChecks<<"},\n";
 ev<<"  \"dataset_provenance\": \"deterministic synthetic test conditions; not plant or laboratory observations\",\n";
 ev<<"  \"tests\": \"see results/ctest_report.txt for final CTest counts\",\n";
 ev<<"  \"outputs\": [\"equilibria.csv\",\"profile.csv\",\"scenario_surface.csv\",\"phase_plane.csv\",\"trajectories.csv\",\"native_audit.csv\",\"math_execution_inventory.csv\",\"formula_manifest.csv\"]\n}\n";
 std::cout<<"RESEARCH RUN PASS: model graphs="<<m.formulas.size()<<" actually executed="<<actual<<" scenarios="<<scenarios.size()<<" equilibrium roots="<<rootTotal<<" independent C++ function checks="<<referenceChecks<<"\n";
}
}
int main(int argc,char** argv){
 try{
  if(argc==2&&std::string(argv[1])=="--selftest"){selftest();return 0;}
  require(argc==4&&std::string(argv[1])=="--run","Usage: reactor_screening --run input/scenarios.csv results/");
  Engine e;e.calibrate();Models m(e);run(m,argv[2],argv[3]);return 0;
 }catch(const std::exception& ex){std::cerr<<"ERROR: "<<ex.what()<<"\n";return 1;}
}
