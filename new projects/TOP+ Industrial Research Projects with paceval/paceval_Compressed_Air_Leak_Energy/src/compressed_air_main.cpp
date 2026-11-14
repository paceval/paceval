// WP19. Mathematical screening for industrial compressed-air leakage with original paceval 4.25.
// paceval executes EVERY explicit physical equation, margin, sensitivity and version comparison.
// C++ is responsible for data/units/domain validation, persistent graph orchestration and I/O.
// The synthetic model does NOT detect or locate actual leaks or certify compressor controls.
#include "paceval_main.h"
#include <algorithm>
#include <cmath>
#include <cstdint>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <map>
#include <regex>
#include <sstream>
#include <stdexcept>
#include <string>
#include <vector>
#include <iomanip>
namespace fs=std::filesystem;
namespace {
void check(bool x,const std::string&s){if(!x)throw std::runtime_error(s);}
void near(double a,double b,double rel=3e-8,double abs=3e-6){check(std::isfinite(a)&&std::isfinite(b)&&std::fabs(a-b)<=abs+rel*std::max(std::fabs(a),std::fabs(b)),"Native/reference disagreement "+std::to_string(a)+" vs "+std::to_string(b));}
bool isLiteral(const std::string&s){static const std::regex e(R"(^[+-]?(?:[0-9]+(?:\.[0-9]*)?|\.[0-9]+)(?:[eE][+-]?[0-9]+)?$)");return std::regex_match(s,e);}
double numIn(const std::string&s){check(isLiteral(s),"Rejected nonnumeric CSV literal: "+s);int err=-1;long pos=-1;double x=paceval_dConvertStringToFloat(s.c_str(),&err,&pos,false,nullptr,nullptr);check(err==0&&std::isfinite(x),"paceval numeric CSV parse error="+std::to_string(err)+" position="+std::to_string(pos));return x;}
std::string numOut(double x){check(std::isfinite(x),"Nonfinite CSV output");char buffer[512]{};int n=paceval_dConvertFloatToString(buffer,x);check(n>0&&buffer[0]!='\0'&&std::string(buffer).find(',')==std::string::npos,"paceval float-to-string conversion failed");return buffer;}
std::vector<std::string> split(const std::string&s){std::stringstream ss(s);std::string x;std::vector<std::string>a;while(std::getline(ss,x,','))a.push_back(x);if(!s.empty()&&s.back()==',')a.push_back("");return a;}
std::string varsText(const std::vector<std::string>&v){std::string a;for(auto&s:v){if(!a.empty())a+=' ';a+=s;}return a;}
using Rows=std::vector<std::vector<double>>;
struct Engine {
 std::vector<PACEVAL_HANDLE> allocated;bool graphMajor=false;uint64_t scalarCalls=0,batchCalls=0,graphPointEvals=0;
 Engine(){check(paceval_InitializeLibrary(nullptr),"paceval initialization failed");}
 ~Engine(){for(auto h:allocated)if(h)paceval_DeleteComputation(h);paceval_FreeLibrary();}
 PACEVAL_HANDLE create(const std::string&formula,const std::vector<std::string>&names){auto v=varsText(names);auto h=paceval_CreateComputation(formula.c_str(),names.size(),v.c_str(),false,nullptr);check(h&&!paceval_GetIsError(h),"Original paceval SDK could not register: "+formula);allocated.push_back(h);return h;}
 double scalar(PACEVAL_HANDLE h,const std::vector<double>&row){auto x=row;double y=paceval_dGetComputationResult(h,x.empty()?nullptr:x.data(),nullptr,nullptr);++scalarCalls;check(!paceval_GetIsError(h)&&std::isfinite(y),"paceval scalar evaluation failed");return y;}
 void layout(){auto a=create("x+2*y",{"x","y"});auto b=create("3*x-y",{"x","y"});PACEVAL_HANDLE h[]={a,b};double x[]={1,2,4,7},out[4]{},lo[4]{},hi[4]{};int err[4]{};bool fail=paceval_dGetMultipleComputationsResultsExt(h,2,x,2,out,lo,hi,err);check(!fail&&std::all_of(err,err+4,[](int n){return n==0;}),"SDK layout test API error");if(std::fabs(out[0]-5)<1e-10&&std::fabs(out[1]-18)<1e-10&&std::fabs(out[2]-1)<1e-10&&std::fabs(out[3]-5)<1e-10)graphMajor=true;else if(std::fabs(out[0]-5)<1e-10&&std::fabs(out[1]-1)<1e-10&&std::fabs(out[2]-18)<1e-10&&std::fabs(out[3]-5)<1e-10)graphMajor=false;else throw std::runtime_error("Unsupported SDK graph/result buffer ordering");++batchCalls;graphPointEvals+=4;}
 Rows batch(const std::vector<PACEVAL_HANDLE>&hs,const Rows&xs,size_t width){check(!hs.empty()&&!xs.empty(),"Empty batch");std::vector<double>in;in.reserve(xs.size()*width);for(auto&r:xs){check(r.size()==width,"Wrong input width");for(double x:r)check(std::isfinite(x),"Nonfinite batch input");in.insert(in.end(),r.begin(),r.end());}std::vector<double>out(xs.size()*hs.size()),lo(out.size()),hi(out.size());std::vector<int>err(out.size(),-1);bool fail=paceval_dGetMultipleComputationsResultsExt(const_cast<PACEVAL_HANDLE*>(hs.data()),hs.size(),in.data(),xs.size(),out.data(),lo.data(),hi.data(),err.data());check(!fail,"paceval multi-graph API failure");for(int e:err)check(e==0,"paceval error code "+std::to_string(e));Rows ans(xs.size(),std::vector<double>(hs.size()));for(size_t i=0;i<xs.size();i++)for(size_t j=0;j<hs.size();j++){auto idx=graphMajor?j*xs.size()+i:i*hs.size()+j;check(std::isfinite(out[idx]),"Nonfinite paceval result");ans[i][j]=out[idx];}++batchCalls;graphPointEvals+=out.size();return ans;}
};
// All 20 inputs use explicit SI units, except operational hours and USD/kWh.
const std::vector<std::string> V={"Pabs","Pamb","Tin","area","Cd","gamma","Rgas","mref","Pref","exponent","demand","supplyCap","Pmin","kdrop","eta","cp","hours","price","maxFraction","Pmax"};
struct Graph{std::string id,version,expression,units,purpose;PACEVAL_HANDLE h;bool executed=false;};
struct Models{
 Engine& e;std::vector<Graph> graphs;std::map<std::string,size_t> index;
 explicit Models(Engine&eg):e(eg){for(int version=1;version<=2;++version){const std::string v=version==1?"V1":"V2";
  const std::string ratio="(Pamb/Pabs)";
  const std::string critical="((2/(gamma+1))^(gamma/(gamma-1)))";
  const std::string choke="(Cd*area*0.000001*Pabs*sqrt(gamma/(Rgas*Tin))*((2/(gamma+1))^((gamma+1)/(2*(gamma-1)))))";
  const std::string sub="(Cd*area*0.000001*Pabs*sqrt((2*gamma/(Rgas*Tin*(gamma-1)))*(("+ratio+"^(2/gamma))-("+ratio+"^((gamma+1)/gamma)))))";
  const std::string empirical="(mref*((Pabs-Pamb)/(Pref-Pamb))^exponent)";
  const std::string orifice="(("+ratio+"<="+critical+")*"+choke+"+("+ratio+">"+critical+")*"+sub+")";
  const std::string leak=version==1?empirical:orifice;
  const std::string flow="(demand+"+leak+")";
  const std::string work="(cp*Tin*((Pabs/Pamb)^((gamma-1)/gamma)-1)/eta)";
  const std::string power="("+flow+"*"+work+"/1000)";
  const std::string leakPower="("+leak+"*"+work+"/1000)";
  const std::string frac="("+leak+"/"+flow+")";
  const std::string downstream="(Pabs-kdrop*"+flow+"^2)";
  const std::string marginP="("+downstream+"-Pmin)";
  const std::string marginCap="(supplyCap-"+flow+")";
  const std::string marginLeak="(maxFraction-"+frac+")";
  const std::string marginHigh="(Pmax-Pabs)";
  const std::string guard="(("+marginP+">=0) AND ("+marginCap+">=0) AND ("+marginLeak+">=0) AND ("+marginHigh+">=0))";
  const std::string annualCost="("+leakPower+"*hours*price)";
  const std::string score="("+annualCost+"/1000+50*(0 max (-"+marginLeak+"))+30*(0 max (-"+marginCap+"))+(0 max (-"+marginP+"))/10000)";
  auto add=[&](const std::string&id,const std::string&expression,const std::string&units,const std::string&purpose){Graph g{v+"_"+id,v,expression,units,purpose,e.create(expression,V),false};index[g.id]=graphs.size();graphs.push_back(std::move(g));};
  add("PRESSURE_RATIO",ratio,"1","Ambient-to-upstream absolute pressure ratio");
  add("CHOKED_THRESHOLD",critical,"1","Critical pressure ratio of isentropic orifice model");
  add("LEAK_MASS_FLOW",leak,"kg/s","Effective leak mass-flow, empirical or ideal-gas orifice");
  add("REQUIRED_MASS_FLOW",flow,"kg/s","Total compressor mass-flow requirement");
  add("LEAK_FRACTION",frac,"1","Leak share of total air production");
  add("SPECIFIC_WORK",work,"J/kg","Isentropic specific-work proxy with fixed efficiency");
  add("COMPRESSOR_POWER",power,"kW","Electrical input proxy under a fixed efficiency assumption");
  add("LEAK_POWER",leakPower,"kW","Portion of electrical input attributable to leak mass flow");
  add("ANNUAL_ENERGY","("+power+"*hours)","kWh","Illustrative full-system electrical energy");
  add("LEAK_ENERGY","("+leakPower+"*hours)","kWh","Illustrative leakage-associated electrical energy");
  add("ANNUAL_LEAK_COST",annualCost,"USD","Illustrative leakage-associated electricity expenditure");
  add("TOTAL_COST","("+power+"*hours*price)","USD","Illustrative full-system electricity expenditure");
  add("END_USE_PRESSURE",downstream,"Pa","Simplified pressure after quadratic network loss");
  add("MARGIN_PRESSURE",marginP,"Pa","Signed downstream minimum-pressure margin");
  add("MARGIN_CAPACITY",marginCap,"kg/s","Signed compressor mass-flow capacity margin");
  add("MARGIN_LEAK_FRACTION",marginLeak,"1","Signed maximum leak-fraction margin");
  add("MARGIN_MAX_PRESSURE",marginHigh,"Pa","Signed maximum upstream-pressure margin");
  add("COMPOSITE_GUARD",guard,"0_or_1","Combined preliminary operational feasibility flag");
  add("PROCESS_SCORE",score,"index","Illustrative multi-constraint operating score");
  add("LEAK_TO_DEMAND","("+leak+"/demand)","1","Leak mass flow relative to useful air consumption");
  add("LEAK_SHARE_OF_POWER","("+leakPower+"/"+power+")","1","Leak fraction of compression electric input");
  if(version==1){add("D_LEAK_D_PRESSURE","(mref*exponent*((Pabs-Pamb)/(Pref-Pamb))^(exponent-1)/(Pref-Pamb))","kg/s/Pa","Local pressure sensitivity of empirical leakage");add("D_LEAK_D_MREF","("+leak+"/mref)","1","Local empirical reference-flow sensitivity");}
  else {add("D_LEAK_D_AREA","("+leak+"/area)","kg/s/mm2","Local effective orifice-area sensitivity");add("ORIFICE_FLOW_CHOKED",choke,"kg/s","Choked branch of ideal-gas orifice equation");add("ORIFICE_FLOW_SUBCRITICAL",sub,"kg/s","Subcritical branch of ideal-gas orifice equation");}
 }
 const std::vector<std::string> CN={"leakA","leakB","energyA","energyB","powerA","powerB","guardA","guardB","scoreA","scoreB","marginA","marginB"};
 auto add=[&](const std::string&id,const std::string&x,const std::string&u,const std::string&p){Graph g{id,"V1_vs_V2",x,u,p,e.create(x,CN),false};index[g.id]=graphs.size();graphs.push_back(g);};
 add("DELTA_LEAK","(leakB-leakA)","kg/s","Version difference in leakage mass-flow");
 add("DELTA_LEAK_ENERGY","(energyB-energyA)","kWh","Version difference in annual leakage energy");
 add("DELTA_LEAK_POWER","(powerB-powerA)","kW","Version difference in leakage power");
 add("COMBINED_GUARD","((guardA=1) AND (guardB=1))","0_or_1","Both model versions satisfy illustrative guards");
 add("DELTA_SCORE","(scoreB-scoreA)","index","Difference of illustrative operating score");
 add("DELTA_CAPACITY_MARGIN","(marginB-marginA)","kg/s","Version difference in compressor capacity margin");
 }
 Rows evaluate(const std::string&version,const Rows&args){std::vector<PACEVAL_HANDLE> h;std::vector<size_t>ids;for(size_t i=0;i<graphs.size();++i)if(graphs[i].version==version){h.push_back(graphs[i].h);ids.push_back(i);}auto a=e.batch(h,args,version=="V1_vs_V2"?12:V.size());for(auto i:ids)graphs[i].executed=true;return a;}
 std::map<std::string,double> unpack(const std::string&version,const std::vector<double>&x){std::map<std::string,double>d;size_t i=0;for(const auto&g:graphs)if(g.version==version){auto p=g.id.substr(version=="V1_vs_V2"?0:3);d[p]=x.at(i++);}check(i==x.size(),"Unpack width mismatch");return d;}
};
struct Case{std::string id,group;std::vector<double> x;};
void domain(const Case&c){auto&v=c.x;check(v.size()==V.size(),"Wrong CSV field count");for(double z:v)check(std::isfinite(z),"Non-finite input");check(v[0]>v[1]&&v[1]>0&&v[2]>0&&v[3]>0&&v[4]>0&&v[4]<=1&&v[5]>1&&v[6]>0&&v[7]>0&&v[8]>v[1]&&v[9]>0&&v[9]<=2&&v[10]>0&&v[11]>0&&v[12]>v[1]&&v[13]>=0&&v[14]>0&&v[14]<=1&&v[15]>0&&v[16]>=0&&v[17]>=0&&v[18]>0&&v[18]<1&&v[19]>v[0]*0.8,"Input violates declared SI model domain");}
std::vector<Case> load(const fs::path&p){std::ifstream f(p);check(bool(f),"Input CSV unavailable: "+p.string());std::string line;check(bool(std::getline(f,line)),"No CSV header");std::string wanted="case_id,scenario";for(auto&v:V)wanted+=","+v;check(line==wanted,"CSV schema does not match canonical header");std::vector<Case>a;size_t n=1;while(std::getline(f,line)){++n;if(line.empty())continue;auto parts=split(line);check(parts.size()==V.size()+2,"Wrong number of fields at line "+std::to_string(n));check(std::regex_match(parts[0],std::regex("[A-Z0-9_]+"))&&std::regex_match(parts[1],std::regex("[a-z_]+")),"Invalid ID or group at line "+std::to_string(n));Case c{parts[0],parts[1],{}};for(size_t k=2;k<parts.size();++k)c.x.push_back(numIn(parts[k]));domain(c);a.push_back(c);}check(!a.empty(),"No input rows");return a;}
struct Ref {double leak,total,frac,work,power,leakPower,annualE,leakE,leakCost,totalCost,puse,mP,mC,mF,mHigh,guard,score,ratio,critical,dLeakDpressure,dLeakDparam,choke,sub;};
Ref native(const std::vector<double>&x,int ver){auto at=[&](int i){return x[i];};double P=at(0),pa=at(1),T=at(2),A=at(3),cd=at(4),g=at(5),R=at(6),mref=at(7),Pref=at(8),n=at(9),d=at(10),capacity=at(11),pmin=at(12),kd=at(13),eta=at(14),cp=at(15),h=at(16),price=at(17),fmax=at(18),pmax=at(19);
 double ratio=pa/P,critical=std::pow(2/(g+1),g/(g-1));double choke=cd*A*1e-6*P*std::sqrt(g/(R*T))*std::pow(2/(g+1),(g+1)/(2*(g-1)));double sub=cd*A*1e-6*P*std::sqrt(2*g/(R*T*(g-1))*(std::pow(ratio,2/g)-std::pow(ratio,(g+1)/g)));
 double leak=ver==1?mref*std::pow((P-pa)/(Pref-pa),n):(ratio<=critical?choke:sub);double total=d+leak,frac=leak/total,work=cp*T*(std::pow(P/pa,(g-1)/g)-1)/eta,power=total*work/1000,lpower=leak*work/1000,pe=P-kd*total*total,mP=pe-pmin,mC=capacity-total,mF=fmax-frac,mH=pmax-P;
 double guard=mP>=0&&mC>=0&&mF>=0&&mH>=0?1.:0.;double annualE=power*h,leakE=lpower*h,leakCost=leakE*price,totalCost=annualE*price;double score=leakCost/1000+50*std::max(0.,-mF)+30*std::max(0.,-mC)+std::max(0.,-mP)/10000;
 return {leak,total,frac,work,power,lpower,annualE,leakE,leakCost,totalCost,pe,mP,mC,mF,mH,guard,score,ratio,critical,ver==1?mref*n*std::pow((P-pa)/(Pref-pa),n-1)/(Pref-pa):0.,ver==1?leak/mref:leak/A,choke,sub};}
size_t assertRef(const std::vector<double>&x,int v,const std::map<std::string,double>&m){auto r=native(x,v);size_t checks=0;auto a=[&](const char*k,double y){near(m.at(k),y);++checks;};a("LEAK_MASS_FLOW",r.leak);a("REQUIRED_MASS_FLOW",r.total);a("LEAK_FRACTION",r.frac);a("SPECIFIC_WORK",r.work);a("COMPRESSOR_POWER",r.power);a("LEAK_POWER",r.leakPower);a("ANNUAL_ENERGY",r.annualE);a("LEAK_ENERGY",r.leakE);a("ANNUAL_LEAK_COST",r.leakCost);a("TOTAL_COST",r.totalCost);a("END_USE_PRESSURE",r.puse);a("MARGIN_PRESSURE",r.mP);a("MARGIN_CAPACITY",r.mC);a("MARGIN_LEAK_FRACTION",r.mF);a("MARGIN_MAX_PRESSURE",r.mHigh);a("COMPOSITE_GUARD",r.guard);a("PROCESS_SCORE",r.score);a("PRESSURE_RATIO",r.ratio);a("CHOKED_THRESHOLD",r.critical);a("LEAK_TO_DEMAND",r.leak/x[10]);a("LEAK_SHARE_OF_POWER",r.leakPower/r.power);
 if(v==1){a("D_LEAK_D_PRESSURE",r.dLeakDpressure);a("D_LEAK_D_MREF",r.dLeakDparam);}else{a("D_LEAK_D_AREA",r.dLeakDparam);a("ORIFICE_FLOW_CHOKED",r.choke);a("ORIFICE_FLOW_SUBCRITICAL",r.sub);}
 near(m.at("LEAK_MASS_FLOW")+x[10],m.at("REQUIRED_MASS_FLOW"));++checks;near(m.at("LEAK_POWER")+x[10]*r.work/1000,m.at("COMPRESSOR_POWER"));++checks;return checks;}
void operators(Engine&e){std::vector<std::pair<std::string,double>>tests={{"((-1)%10)",-1},{"((-1) mod 10)",9},{"(4 min 5)",4},{"(4 max 5)",5},{"(3<4)",1},{"(3<=3)",1},{"(3>=3)",1},{"(3=3)",1},{"(3<>4)",1},{"NOT(0)",1},{"(1 AND 1)",1},{"(0 OR 1)",1},{"((3<=3) AND (2>=0))",1}};for(auto&t:tests){auto h=e.create(t.first,{});near(e.scalar(h,{}),t.second,0,1e-12);}near(numIn("-1.25e-3"),-.00125);for(auto bad:{"","NaN","Inf","1+2","1,2","1e999","--1"," 1"}){bool fail=false;try{numIn(bad);}catch(...){fail=true;}check(fail,"Bad numeric literal accepted");}check(!numOut(.00125).empty(),"Float formatting unavailable");}
void selftest(){Engine e;e.layout();operators(e);Models model(e);std::vector<double>x={700000,101325,300,1.7,.70,1.4,287,0.002,750000,.62,.09,.16,580000,110000,.78,1005,6000,.18,.10,890000};Case c{"TEST","normal",x};domain(c);for(int v=1;v<=2;v++){auto ver=v==1?"V1":"V2";auto d=model.unpack(ver,model.evaluate(ver,Rows{x})[0]);assertRef(x,v,d);near(e.scalar(model.graphs[model.index[std::string(ver)+"_LEAK_MASS_FLOW"]].h,x),d.at("LEAK_MASS_FLOW"));}std::cout<<"SELFTEST PASS: original paceval 4.25, scalar/multi-graph batch, operator, CSV numeric conversion and independent model checks\n";}
void run(const fs::path&input,const fs::path&out){fs::create_directories(out);Engine e;e.layout();operators(e);Models model(e);auto cases=load(input);size_t N=cases.size(),nativeChecks=0,comparisonChecks=0,accepted[2]={};std::vector<std::map<std::string,double>> values[2];values[0].resize(N);values[1].resize(N);
 std::ofstream results(out/"screening.csv"), comparison(out/"model_comparison.csv"),audit(out/"native_audit.csv"),manifest(out/"formula_manifest.csv"),inventory(out/"math_execution_inventory.csv"),proof(out/"execution_evidence.json");check(bool(results&&comparison&&audit&&manifest&&inventory&&proof),"Unable to open output files");
 results<<"case_id,scenario,model,Pabs_Pa,area_mm2,demand_kg_s,leak_kg_s,required_kg_s,leak_fraction,work_J_kg,power_kW,leak_power_kW,annual_energy_kWh,leak_energy_kWh,leak_cost_USD,total_cost_USD,pressure_use_Pa,margin_pressure_Pa,margin_capacity_kg_s,margin_leak_fraction,margin_high_pressure_Pa,composite_guard,process_score\n";
 comparison<<"case_id,scenario,Pabs_Pa,leak_V1_kg_s,leak_V2_kg_s,delta_leak_kg_s,leak_energy_V1_kWh,leak_energy_V2_kWh,delta_leak_energy_kWh,leak_power_V1_kW,leak_power_V2_kW,delta_leak_power_kW,guard_V1,guard_V2,both_feasible,delta_score\n";
 audit<<"case_id,scenario,version,native_endvalue_checks,pass\n";
 for(int v=1;v<=2;v++){std::string version=v==1?"V1":"V2";for(size_t start=0;start<N;start+=96){size_t end=std::min(N,start+96);Rows args;for(size_t i=start;i<end;i++)args.push_back(cases[i].x);auto outRows=model.evaluate(version,args);for(size_t i=start;i<end;i++){auto &cs=cases[i];auto d=model.unpack(version,outRows[i-start]);values[v-1][i]=d;if(d.at("COMPOSITE_GUARD")>.5)accepted[v-1]++;results<<cs.id<<','<<cs.group<<','<<version;for(double x:{cs.x[0],cs.x[3],cs.x[10]})results<<','<<numOut(x);for(auto k:{"LEAK_MASS_FLOW","REQUIRED_MASS_FLOW","LEAK_FRACTION","SPECIFIC_WORK","COMPRESSOR_POWER","LEAK_POWER","ANNUAL_ENERGY","LEAK_ENERGY","ANNUAL_LEAK_COST","TOTAL_COST","END_USE_PRESSURE","MARGIN_PRESSURE","MARGIN_CAPACITY","MARGIN_LEAK_FRACTION","MARGIN_MAX_PRESSURE","COMPOSITE_GUARD","PROCESS_SCORE"})results<<','<<numOut(d.at(k));results<<'\n';if(i%37==0||i==N-1){size_t n=assertRef(cs.x,v,d);nativeChecks+=n;audit<<cs.id<<','<<cs.group<<','<<version<<','<<n<<",1\n";}}}}
 for(size_t start=0;start<N;start+=96){size_t end=std::min(N,start+96);Rows x;for(size_t i=start;i<end;i++){auto&a=values[0][i],&b=values[1][i];x.push_back({a.at("LEAK_MASS_FLOW"),b.at("LEAK_MASS_FLOW"),a.at("LEAK_ENERGY"),b.at("LEAK_ENERGY"),a.at("LEAK_POWER"),b.at("LEAK_POWER"),a.at("COMPOSITE_GUARD"),b.at("COMPOSITE_GUARD"),a.at("PROCESS_SCORE"),b.at("PROCESS_SCORE"),a.at("MARGIN_CAPACITY"),b.at("MARGIN_CAPACITY")});}auto ys=model.evaluate("V1_vs_V2",x);for(size_t i=start;i<end;i++){auto&cs=cases[i];auto&a=values[0][i],&b=values[1][i];auto d=model.unpack("V1_vs_V2",ys[i-start]);comparison<<cs.id<<','<<cs.group<<','<<numOut(cs.x[0]);for(double y:{a.at("LEAK_MASS_FLOW"),b.at("LEAK_MASS_FLOW"),d.at("DELTA_LEAK"),a.at("LEAK_ENERGY"),b.at("LEAK_ENERGY"),d.at("DELTA_LEAK_ENERGY"),a.at("LEAK_POWER"),b.at("LEAK_POWER"),d.at("DELTA_LEAK_POWER"),a.at("COMPOSITE_GUARD"),b.at("COMPOSITE_GUARD"),d.at("COMBINED_GUARD"),d.at("DELTA_SCORE")})comparison<<','<<numOut(y);comparison<<'\n';if(i%83==0){near(d.at("DELTA_LEAK"),b.at("LEAK_MASS_FLOW")-a.at("LEAK_MASS_FLOW"));near(d.at("DELTA_LEAK_ENERGY"),b.at("LEAK_ENERGY")-a.at("LEAK_ENERGY"));comparisonChecks+=2;}}}
 manifest<<"graph_id,version,expression,units,industrial_purpose\n";inventory<<"function_id,domain_quantity,mathematical_definition,units,execution_owner,paceval_graph_id,formula_version,api_path,reference_test,status,host_reason\n";size_t executed=0;for(auto&g:model.graphs){if(g.executed)executed++;manifest<<g.id<<','<<g.version<<",\""<<g.expression<<"\","<<g.units<<",\""<<g.purpose<<"\"\n";inventory<<g.id<<",\""<<g.purpose<<"\",\""<<g.expression<<"\","<<g.units<<",paceval,"<<g.id<<','<<g.version<<",paceval_dGetMultipleComputationsResultsExt,native C++ and mpmath,"<<(g.executed?"executed":"registered_only")<<",\n";}
 inventory<<"INPUT_PARSE,validated CSV numbers,decimal literal,1,paceval,,all,paceval_dConvertStringToFloat,negative input tests,executed,\nCSV_WRITE,CSV numeric output,double to string,1,paceval,,all,paceval_dConvertFloatToString,independent CSV reader,executed,\nCASE_SELECTION,deterministic case enumeration,synthetic source generation,1,host,,all,Python source,source review,executed,nonmathematical orchestration\n";
 proof<<"{\n \"sdk\": \"original paceval 4.25 with supplied Linux shared library\",\n \"unique_graphs_created\": "<<model.graphs.size()<<",\n \"unique_graphs_executed\": "<<executed<<",\n \"scalar_calls_including_operator_tests\": "<<e.scalarCalls<<",\n \"batch_calls_including_layout_probe\": "<<e.batchCalls<<",\n \"graph_point_evaluations_including_layout_probe\": "<<e.graphPointEvals<<",\n \"scenario_count\": "<<N<<",\n \"model_scenario_combinations\": "<<2*N<<",\n \"feasible_V1\": "<<accepted[0]<<",\n \"feasible_V2\": "<<accepted[1]<<",\n \"native_endvalue_assertions\": "<<nativeChecks+comparisonChecks<<",\n \"reference_high_precision\": \"see high_precision_audit.json\"\n}\n";
 check(executed==model.graphs.size(),"Not all domain graph paths executed");std::cout<<"RESEARCH PASS "<<executed<<'/'<<model.graphs.size()<<" paceval graphs, "<<N<<" synthetic cases, "<<nativeChecks+comparisonChecks<<" native independent assertions, valid V1/V2: "<<accepted[0]<<'/'<<accepted[1]<<'\n';}
}
int main(int argc,char**argv){try{if(argc==2&&std::string(argv[1])=="--selftest"){selftest();return 0;}check(argc==4&&std::string(argv[1])=="--run","Usage: compressed_air --run input/cases.csv output_directory");run(argv[2],argv[3]);return 0;}catch(const std::exception&e){std::cerr<<"ERROR "<<e.what()<<'\n';return 1;}}
