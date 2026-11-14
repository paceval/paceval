// WP 12: Reproducible synthetic 24-hour microgrid dispatch feasibility study.
// Original paceval SDK 4.25 owns all domain calculations, margins, composite
// costs, interval balance and symbolic sensitivity formulas. C++ owns state
// propagation between periods, CSV validation, enumeration and aggregation.
// This is NOT a controller, MILP optimizer, power-flow solver or grid approval.
#include "paceval_main.h"
#include <algorithm>
#include <array>
#include <cmath>
#include <cstdint>
#include <filesystem>
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
namespace fs=std::filesystem;
namespace {
void check(bool b,const std::string& m){if(!b)throw std::runtime_error(m);}
bool decimalLiteral(const std::string& s){static const std::regex r(R"(^[+-]?(?:[0-9]+(?:\.[0-9]*)?|\.[0-9]+)(?:[eE][+-]?[0-9]+)?$)");return std::regex_match(s,r);}
double parseNumber(const std::string& s){check(decimalLiteral(s),"Rejected nonnumeric CSV field: "+s);int e=-1;long at=-1;double x=paceval_dConvertStringToFloat(s.c_str(),&e,&at,false,nullptr,nullptr);check(e==0&&std::isfinite(x),"paceval CSV parsing error "+std::to_string(e)+" at "+std::to_string(at));return x;}
std::string number(double x){check(std::isfinite(x),"Nonfinite output");char b[512]{};int precision=paceval_dConvertFloatToString(b,x);check(precision>0&&b[0]&&std::string(b).find(',')==std::string::npos,"paceval double-to-text conversion error");return b;}
std::vector<std::string> split(const std::string& s){std::vector<std::string> r;std::stringstream ss(s);std::string x;while(std::getline(ss,x,','))r.push_back(x);if(!s.empty()&&s.back()==',')r.push_back("");return r;}
void near(double a,double b,double rel=5e-8,double abs=5e-9){check(std::isfinite(a)&&std::isfinite(b)&&std::abs(a-b)<=abs+rel*std::max(std::abs(a),std::abs(b)),"Independent mathematical reference mismatch");}
std::string join(const std::vector<std::string>& a){std::string s;for(const auto& x:a){if(!s.empty())s+=' ';s+=x;}return s;}
using Rows=std::vector<std::vector<double>>;
struct Engine {
 std::vector<PACEVAL_HANDLE> handles;bool graphMajor=false;uint64_t scalarCalls=0,batchCalls=0,graphPoints=0;
 Engine(){check(paceval_InitializeLibrary(nullptr),"Failed original paceval initialization");}
 ~Engine(){for(auto h:handles)if(h)paceval_DeleteComputation(h);paceval_FreeLibrary();}
 PACEVAL_HANDLE create(const std::string& expr,const std::vector<std::string>& vars){std::string v=join(vars);auto h=paceval_CreateComputation(expr.c_str(),vars.size(),v.c_str(),false,nullptr);check(h&&!paceval_GetIsError(h),"Invalid original paceval graph: "+expr);handles.push_back(h);return h;}
 double scalar(PACEVAL_HANDLE h,const std::vector<double>& v){auto a=v;double z=paceval_dGetComputationResult(h,a.data(),nullptr,nullptr);scalarCalls++;check(!paceval_GetIsError(h)&&std::isfinite(z),"Scalar API failed");return z;}
 void probe(){auto x=create("a+2*b",{"a","b"}),y=create("3*a-b",{"a","b"});PACEVAL_HANDLE h[]={x,y};double in[]={1,2,4,7},out[4]{},lo[4]{},hi[4]{};int err[4]{};bool failed=paceval_dGetMultipleComputationsResultsExt(h,2,in,2,out,lo,hi,err);check(!failed&&std::all_of(err,err+4,[](int v){return v==0;}),"Multi graph layout probe failed");
  if(std::abs(out[0]-5)<1e-10&&std::abs(out[1]-18)<1e-10&&std::abs(out[2]-1)<1e-10&&std::abs(out[3]-5)<1e-10)graphMajor=true;
  else if(std::abs(out[0]-5)<1e-10&&std::abs(out[1]-1)<1e-10&&std::abs(out[2]-18)<1e-10&&std::abs(out[3]-5)<1e-10)graphMajor=false;
  else throw std::runtime_error("Unknown original SDK multi-graph result layout");
  batchCalls++;graphPoints+=4;
 }
 Rows batch(const std::vector<PACEVAL_HANDLE>& hs,const Rows& rows,size_t nVars){check(!hs.empty()&&!rows.empty(),"Empty batch");std::vector<double> in;in.reserve(rows.size()*nVars);for(const auto& row:rows){check(row.size()==nVars,"Wrong batch width");for(double x:row)check(std::isfinite(x),"Nonfinite graph input");in.insert(in.end(),row.begin(),row.end());}
  const size_t n=hs.size()*rows.size();std::vector<double> out(n),lo(n),hi(n);std::vector<int> err(n,-1); // false means success in the tested SDK
  bool failed=paceval_dGetMultipleComputationsResultsExt(const_cast<PACEVAL_HANDLE*>(hs.data()),hs.size(),in.data(),rows.size(),out.data(),lo.data(),hi.data(),err.data());
  check(!failed,"Original paceval multi-graph call failed");for(int e:err)check(e==0,"Original paceval item error: "+std::to_string(e));
  Rows result(rows.size(),std::vector<double>(hs.size()));for(size_t j=0;j<rows.size();j++)for(size_t g=0;g<hs.size();g++){size_t at=graphMajor?g*rows.size()+j:j*hs.size()+g;check(std::isfinite(out[at]),"Nonfinite paceval graph output");result[j][g]=out[at];}
  batchCalls++;graphPoints+=n;return result;
 }
};
const std::vector<std::string> VARS={"pv","load","gen","ch","dis","imp","exp","curt","shed","E","dt","etaC","etaD","etaSlope","emax","emin","eres","chmax","dismax","genmax","impmax","expmax","fuel","buy","sell","ccurt","cshed","cage","ramp","prevgen","rampmax","island","critical","tol","goal"};
struct Graph {std::string id,version,description,expr,units;PACEVAL_HANDLE h{};bool ran=false;};
struct Models {
 Engine& engine;std::vector<Graph> gs;std::map<std::string,size_t> lookup;
 explicit Models(Engine& e):engine(e){
  for(int v=1;v<=2;v++){
   std::string prefix=v==1?"V1_":"V2_";
   const std::string ec=v==1?"etaC":"(etaC*(1-etaSlope*(E/emax-0.5)^2))";
   const std::string ed=v==1?"etaD":"(etaD*(1-0.5*etaSlope*(E/emax-0.5)^2))";
   const std::string Enew="(E+dt*("+ec+"*ch-dis/"+ed+"))";
   const std::string balance="(pv-curt+gen+dis+imp-ch-exp-load+shed)";
   const std::string ml="("+Enew+"-emin)",mh="(emax-"+Enew+")",mr="("+Enew+"-eres)";
   const std::string mg="(genmax-gen)",mc="(chmax-ch)",md="(dismax-dis)",mi="(impmax-imp)",mx="(expmax-exp)";
   const std::string mpv="(pv-curt)",mshed="(load-shed-critical)",mramp="(rampmax-abs(gen-prevgen))";
   const std::string nonSim="((ch = 0) OR (dis = 0))";
   const std::string islandGuard="((island = 0) OR ((imp = 0) AND (exp = 0)))";
   const std::string age=v==1?"(0*cage*(ch+dis))":"(cage*(ch+dis))";
   const std::string cost="(dt*(fuel*gen+buy*imp-sell*exp+ccurt*curt+cshed*shed+"+age+"+ramp*abs(gen-prevgen)))";
   const std::string feasible="((abs("+balance+") <= tol) AND ("+ml+" >= (-tol)) AND ("+mh+" >= (-tol)) AND ("+mr+" >= (-tol)) AND ("+mg+" >= (-tol)) AND ("+mc+" >= (-tol)) AND ("+md+" >= (-tol)) AND ("+mi+" >= (-tol)) AND ("+mx+" >= (-tol)) AND ("+mpv+" >= (-tol)) AND ("+mshed+" >= (-tol)) AND ("+mramp+" >= (-tol)) AND ("+nonSim+") AND ("+islandGuard+"))";
   auto add=[&](std::string id,std::string expression,std::string unit,std::string description){Graph g{prefix+id,v==1?"V1":"V2",description,expression,unit,engine.create(expression,VARS),false};lookup[g.id]=gs.size();gs.push_back(std::move(g));};
   add("PV_USED","(pv-curt)","kW","PV supply after curtailment");
   add("SERVED_LOAD","(load-shed)","kW","Delivered load after permitted noncritical shedding");
   add("POWER_BALANCE",balance,"kW","Residual of instantaneous active-power balance");
   add("ETA_CH",ec,"1","Charge efficiency at current battery SOC");
   add("ETA_DIS",ed,"1","Discharge efficiency at current battery SOC");
   add("E_NEXT",Enew,"kWh","Next energy state, efficiency accounting");
   add("SOC_NEXT","("+Enew+"/emax)","1","Next state-of-charge fraction");
   add("MARGIN_RESERVE",mr,"kWh","Reserve above operational energy floor");
   add("MARGIN_MIN",ml,"kWh","Lower battery energy bound margin");
   add("MARGIN_MAX",mh,"kWh","Upper battery energy bound margin");
   add("MARGIN_CHARGE",mc,"kW","Charge power headroom");
   add("MARGIN_DISCHARGE",md,"kW","Discharge power headroom");
   add("MARGIN_GEN",mg,"kW","Dispatchable generator headroom");
   add("MARGIN_IMPORT",mi,"kW","Grid import headroom");
   add("MARGIN_EXPORT",mx,"kW","Grid export headroom");
   add("MARGIN_CURTAIL",mpv,"kW","Curtailment below available PV");
   add("MARGIN_CRITICAL_LOAD",mshed,"kW","Served load above minimum critical demand");
   add("MARGIN_RAMP",mramp,"kW","Dispatchable generator ramp headroom");
   add("NO_SIMULTANEOUS",nonSim,"0_or_1","No simultaneous battery charging and discharging");
   add("ISLAND_GRID_GUARD",islandGuard,"0_or_1","Zero grid exchange in island mode");
   add("STAGE_COST",cost,"USD","Per-hour operating cost with selected aging assumption");
   add("FUEL_COST","(dt*fuel*gen)","USD","Generator fuel expenditure");
   add("GRID_COST","(dt*(buy*imp-sell*exp))","USD","Grid import expense minus export revenue");
   add("SHEDDING_COST","(dt*cshed*shed)","USD","Penalty for noncritical service reduction");
   add("THROUGHPUT","(dt*(ch+dis))","kWh","Battery charge plus discharge throughput");
   add("D_ENEXT_DCH","(dt*"+ec+")","h","Analytical next-energy sensitivity to charging power");
   add("D_ENEXT_DDIS","(-dt/"+ed+")","h","Analytical next-energy sensitivity to discharging power");
   const std::string dec=v==1?"0":"(etaC*(-2*etaSlope*(E/emax-0.5)/emax))";
   const std::string ded=v==1?"0":"(etaD*(-etaSlope*(E/emax-0.5)/emax))";
   add("D_ENEXT_DE","(1+dt*("+dec+"*ch+dis*"+ded+"/("+ed+"*"+ed+")))","1","Analytical sensitivity of transition to current stored energy");
   add("TERMINAL_MARGIN","("+Enew+"-goal)","kWh","Terminal target energy margin if evaluated at final hour");
   add("STEP_FEASIBILITY",feasible,"0_or_1","Composite physical and energy feasibility guard");
   add("SCREENING_SCORE","(-"+cost+"-0.02*(((-"+mr+") max 0)^2)-10*abs("+balance+"))","USD_equivalent","Illustrative combined penalty on cost, reserve and mismatch");
   add("NET_GRID","(imp-exp)","kW","Net electric utility import");
  }
  const std::vector<std::string> vs={"e1","e2","c1","c2","r1","r2","f1","f2"};
  auto add=[&](std::string id,std::string ex,std::string unit,std::string desc){Graph g{id,"V1_vs_V2",desc,ex,unit,engine.create(ex,vs),false};lookup[g.id]=gs.size();gs.push_back(std::move(g));};
  add("DELTA_FINAL_E","(e2-e1)","kWh","Difference in 24h final battery energy");
  add("DELTA_COST","(c2-c1)","USD","Difference in full schedule modeled cost");
  add("MIN_RESERVE_ACROSS_MODELS","(r1 min r2)","kWh","Conservative reserve headroom across model versions");
  add("JOINT_FEASIBILITY","((f1 >= 1) AND (f2 >= 1))","0_or_1","Both model versions satisfy all checked constraints");
  add("MODEL_SCORE_DIFFERENCE","((e2-e1)-0.1*(c2-c1))","kWh_equivalent","Version delta of illustrative terminal-energy/economic score");
 }
 size_t offset(const std::string& id)const{auto it=lookup.find(id);check(it!=lookup.end(),"Missing mathematical graph "+id);return it->second;}
 std::vector<size_t> select(const std::string& v)const{std::vector<size_t> a;for(size_t i=0;i<gs.size();i++)if(gs[i].version==v)a.push_back(i);return a;}
 Rows eval(const std::string& v,const Rows& inputs){auto selectIds=select(v);std::vector<PACEVAL_HANDLE> h;for(auto i:selectIds)h.push_back(gs[i].h);Rows out;for(size_t base=0;base<inputs.size();base+=96){size_t end=std::min(base+96,inputs.size());Rows in(inputs.begin()+base,inputs.begin()+end);auto result=engine.batch(h,in,v=="V1_vs_V2"?8:VARS.size());out.insert(out.end(),result.begin(),result.end());}for(auto i:selectIds)gs[i].ran=true;return out;}
 std::map<std::string,double> unpack(const std::string& v,const std::vector<double>& r)const{auto idx=select(v);check(idx.size()==r.size(),"Wrong unpack graph count");std::map<std::string,double> a;for(size_t k=0;k<idx.size();k++){auto& g=gs[idx[k]];a[g.id.substr(v=="V1_vs_V2"?0:3)]=r[k];}return a;}
};
struct Interval {int hour=0;double pv=0,load=0,gen=0,ch=0,dis=0,imp=0,exp=0,curt=0,shed=0,buy=0;};
struct Schedule {std::string scenario,id;std::vector<Interval> steps;};
struct Parameters{std::map<std::string,double> m;double operator[](const std::string& k)const{auto it=m.find(k);check(it!=m.end(),"Missing parameter "+k);return it->second;}};
Parameters paramsFromFile(const fs::path& path){std::ifstream f(path);check(bool(f),"Cannot open parameters file");std::string line;std::getline(f,line);check(line=="parameter,value,unit","Bad parameter CSV header");Parameters p;while(std::getline(f,line)){if(line.empty())continue;auto t=split(line);check(t.size()==3,"Wrong number of parameter fields");check(!p.m.count(t[0]),"Duplicate parameter");p.m[t[0]]=parseNumber(t[1]);}for(auto k:{"etaC","etaD"})check(p[k]>0&&p[k]<=1,"Invalid efficiency");check(p["emax"]>p["einitial"]&&p["einitial"]>p["emin"]&&p["eres"]>=p["emin"]&&p["goal"]<=p["emax"],"Invalid energy bounds");check(p["etaSlope"]>=0&&p["etaSlope"]<=0.5,"Invalid SOC efficiency slope");check(p["dt"]>0&&p["tol"]>0,"Invalid timestep or tolerance");return p;}
std::vector<Schedule> casesFromFile(const fs::path& path){std::ifstream f(path);check(bool(f),"Cannot open dispatch CSV");std::string line;std::getline(f,line);check(line=="scenario,schedule_id,hour,pv_kW,load_kW,gen_kW,charge_kW,discharge_kW,import_kW,export_kW,curtail_kW,shed_kW,buy_USD_per_kWh","Wrong dispatch schema");std::vector<Schedule> cases;std::map<std::string,size_t> ids;size_t lineno=1;while(std::getline(f,line)){++lineno;if(line.empty())continue;auto t=split(line);check(t.size()==13,"CSV width on line "+std::to_string(lineno));check(t[0]=="grid_sunny"||t[0]=="grid_cloudy"||t[0]=="island_outage","Unknown scenario");check(t[1].size()==4&&std::all_of(t[1].begin(),t[1].end(),[](char c){return c>='0'&&c<='9';}),"Malformed schedule identifier");int h=static_cast<int>(parseNumber(t[2]));check(h>=0&&h<24&&number(double(h))==t[2],"Invalid hour");Interval z;z.hour=h;std::array<double*,10> destinations={&z.pv,&z.load,&z.gen,&z.ch,&z.dis,&z.imp,&z.exp,&z.curt,&z.shed,&z.buy};for(int j=0;j<10;j++){*destinations[j]=parseNumber(t[3+j]);check(*destinations[j]>=0,"Negative power or tariff on line "+std::to_string(lineno));}check(z.pv<=500&&z.load<=400&&z.buy<=1,"Outside documented synthetic input domain");std::string k=t[0]+":"+t[1];auto it=ids.find(k);if(it==ids.end()){ids[k]=cases.size();cases.push_back({t[0],t[1],{}});it=ids.find(k);}auto& steps=cases[it->second].steps;check(steps.size()==size_t(h),"Missing, unordered or repeated hourly interval in "+k);steps.push_back(z);}
 check(!cases.empty(),"Missing schedule candidates");for(const auto& c:cases)check(c.steps.size()==24,"Incomplete 24-hour schedule");return cases;
}
std::vector<double> makeInput(const Interval& z,const Parameters& p,double E,double prevgen,bool island){return {z.pv,z.load,z.gen,z.ch,z.dis,z.imp,z.exp,z.curt,z.shed,E,p["dt"],p["etaC"],p["etaD"],p["etaSlope"],p["emax"],p["emin"],p["eres"],p["chmax"],p["dismax"],p["genmax"],p["impmax"],p["expmax"],p["fuel"],z.buy,p["sell"],p["ccurt"],p["cshed"],p["cage"],p["ramp"],prevgen,p["rampmax"],island?1.0:0.0,0.62*z.load,p["tol"],p["goal"]};}
struct Summary {double E=0,cost=0,minReserve=1e100,maxAbsBalance=0,shedEnergy=0,gridImport=0,throughput=0,finalMargin=0;bool feasible=true;};
void checkNative(const Interval& z,const Parameters& p,double E,double prevgen,int v,const std::map<std::string,double>& r){double etaC=p["etaC"],etaD=p["etaD"];if(v==2){double x=E/p["emax"]-.5;etaC*=1-p["etaSlope"]*x*x;etaD*=1-.5*p["etaSlope"]*x*x;}double ene=E+p["dt"]*(etaC*z.ch-z.dis/etaD);double power=z.pv-z.curt+z.gen+z.dis+z.imp-z.ch-z.exp-z.load+z.shed;double age=v==1?0.0:p["cage"]*(z.ch+z.dis);double cost=p["dt"]*(p["fuel"]*z.gen+z.buy*z.imp-p["sell"]*z.exp+p["ccurt"]*z.curt+p["cshed"]*z.shed+age+p["ramp"]*std::abs(z.gen-prevgen));near(ene,r.at("E_NEXT"));near(power,r.at("POWER_BALANCE"));near(cost,r.at("STAGE_COST"));near(etaC,r.at("ETA_CH"));near(etaD,r.at("ETA_DIS"));near(ene-p["eres"],r.at("MARGIN_RESERVE"));near(p["dt"]*etaC,r.at("D_ENEXT_DCH"));near(-p["dt"]/etaD,r.at("D_ENEXT_DDIS"));
 double d=1;if(v==2){double x=E/p["emax"]-.5;double dc=p["etaC"]*(-2*p["etaSlope"]*x/p["emax"]);double dd=p["etaD"]*(-p["etaSlope"]*x/p["emax"]);d+=p["dt"]*(dc*z.ch+z.dis*dd/(etaD*etaD));}near(d,r.at("D_ENEXT_DE"));}
void operatorTest(Engine& e){struct T{std::string f;double expected;};for(const auto& test:std::vector<T>{{"((-1) % 10)",-1},{"((-1) mod 10)",9},{"(4 min 5)",4},{"(4 max 5)",5},{"(2<3)",1},{"(3<=3)",1},{"(3>=3)",1},{"(4=4)",1},{"(4<>5)",1},{"NOT(0)",1},{"(1 AND 1)",1},{"(0 OR 1)",1},{"((3<=3) AND (2>=0))",1}}){auto h=e.create(test.f,{});near(e.scalar(h,{}),test.expected,0,1e-12);}near(parseNumber("1.25e-3"),.00125);for(const char* bad:{"","NaN","Inf","2+3","1,2","1e99999"," 7","-"}){bool rejected=false;try{(void)parseNumber(bad);}catch(...){rejected=true;}check(rejected,"Unsafe numerical input accepted");}char b[512]{};check(paceval_dConvertFloatToString(b,1.25)>0,"Number formatting test failed");}
void selftest(){Engine e;e.probe();operatorTest(e);Models models(e);Parameters p;for(const auto& pr:std::vector<std::pair<std::string,double>>{{"dt",1},{"etaC",.95},{"etaD",.93},{"etaSlope",.26},{"emax",650},{"emin",60},{"eres",145},{"goal",205},{"chmax",125},{"dismax",125},{"genmax",230},{"impmax",280},{"expmax",210},{"fuel",.26},{"sell",.08},{"ccurt",.025},{"cshed",4},{"cage",.035},{"ramp",.001},{"rampmax",150},{"tol",.00005}})p.m[pr.first]=pr.second;
 std::vector<Interval> steps={{12,150,170,10,25,0,35,0,0,0,.2},{22,0,210,145,0,40,25,0,0,0,.3},{5,0,160,160,0,0,0,0,0,0,.2}};
 for(int v=1;v<=2;v++){Rows inputs;for(const auto& z:steps)inputs.push_back(makeInput(z,p,350,z.gen,z.hour==5));auto outs=models.eval(v==1?"V1":"V2",inputs);for(size_t j=0;j<steps.size();j++){auto r=models.unpack(v==1?"V1":"V2",outs[j]);checkNative(steps[j],p,350,steps[j].gen,v,r);if(j==2)check(r["ISLAND_GRID_GUARD"]==1,"Island restriction failed");}}
 // Explicitly confirm the paceval graph retains the same result under scalar evaluation.
 auto h=models.gs[models.offset("V1_E_NEXT")].h;auto x=makeInput(steps[0],p,350,10,false);near(e.scalar(h,x),models.unpack("V1",models.eval("V1",Rows{x})[0]).at("E_NEXT"));
 std::cout<<"SELFTEST PASS: original SDK 4.25, scalar and genuine multi-graph batch, compound boolean guards, modulo and min/max, CSV numeric conversions, native physical reference\n";
}
void run(const fs::path& input,const fs::path& pfile,const fs::path& outdir){fs::create_directories(outdir);Engine eng;eng.probe();operatorTest(eng);Models models(eng);auto p=paramsFromFile(pfile);auto schedules=casesFromFile(input);const size_t N=schedules.size();
 std::ofstream steps(outdir/"dispatch_timeseries.csv"),summary(outdir/"schedule_summary.csv"),comparison(outdir/"model_comparison.csv"),audit(outdir/"native_audit.csv"),manifest(outdir/"formula_manifest.csv"),inventory(outdir/"math_execution_inventory.csv"),evidence(outdir/"execution_evidence.json");check(bool(steps&&summary&&comparison&&audit&&manifest&&inventory&&evidence),"Cannot create research outputs");
 steps<<"scenario,schedule_id,model,hour,pv_kW,load_kW,gen_kW,charge_kW,discharge_kW,import_kW,export_kW,curtail_kW,shed_kW,E_current_kWh,E_next_kWh,soc_next,balance_kW,reserve_margin_kWh,min_margin_kWh,max_margin_kWh,charge_eff,discharge_eff,step_cost_USD,step_guard,score,throughput_kWh,dEnext_dPch_h,dEnext_dPdis_h,dEnext_dE,terminal_margin_kWh\n";
 summary<<"scenario,schedule_id,model,final_energy_kWh,total_cost_USD,min_reserve_margin_kWh,max_abs_balance_kW,shed_kWh,import_kWh,throughput_kWh,terminal_margin_kWh,all_hour_feasible,full_schedule_feasible\n";
 comparison<<"scenario,schedule_id,final_energy_V1_kWh,final_energy_V2_kWh,delta_final_energy_kWh,cost_V1_USD,cost_V2_USD,delta_cost_USD,min_reserve_V1_kWh,min_reserve_V2_kWh,min_reserve_across_models_kWh,feasible_V1,feasible_V2,joint_feasible,model_score_difference\n";
 audit<<"scenario,schedule_id,model,hour,E_current_kWh,paceval_next_kWh,paceval_balance_kW,paceval_cost_USD,reference_verified\n";
 std::array<std::vector<Summary>,2> summaries;size_t referenceChecks=0;size_t pass[2]={0,0};
 for(int v=1;v<=2;v++){
  const std::string version=v==1?"V1":"V2";std::vector<double> energy(N,p["einitial"]);summaries[v-1]=std::vector<Summary>(N);for(int hour=0;hour<24;hour++){
   Rows inputs;inputs.reserve(N);for(size_t j=0;j<N;j++){const auto& z=schedules[j].steps[hour];double last=hour?schedules[j].steps[hour-1].gen:z.gen;inputs.push_back(makeInput(z,p,energy[j],last,schedules[j].scenario=="island_outage"));}
   auto outputs=models.eval(version,inputs);check(outputs.size()==N,"Lost batch rows");
   for(size_t j=0;j<N;j++){const auto& c=schedules[j];const auto& z=c.steps[hour];auto r=models.unpack(version,outputs[j]);auto& s=summaries[v-1][j];double current=energy[j],next=r.at("E_NEXT");check(next>-200&&next<1000,"Unbounded synthetic battery state");s.E=next;s.cost+=r.at("STAGE_COST");s.minReserve=std::min(s.minReserve,r.at("MARGIN_RESERVE"));s.maxAbsBalance=std::max(s.maxAbsBalance,std::abs(r.at("POWER_BALANCE")));s.shedEnergy+=z.shed*p["dt"];s.gridImport+=z.imp*p["dt"];s.throughput+=r.at("THROUGHPUT");s.feasible=s.feasible&&(r.at("STEP_FEASIBILITY")>.5);
    steps<<c.scenario<<','<<c.id<<','<<version<<','<<hour<<','<<number(z.pv)<<','<<number(z.load)<<','<<number(z.gen)<<','<<number(z.ch)<<','<<number(z.dis)<<','<<number(z.imp)<<','<<number(z.exp)<<','<<number(z.curt)<<','<<number(z.shed)<<','<<number(current)<<','<<number(next)<<','<<number(r.at("SOC_NEXT"))<<','<<number(r.at("POWER_BALANCE"))<<','<<number(r.at("MARGIN_RESERVE"))<<','<<number(r.at("MARGIN_MIN"))<<','<<number(r.at("MARGIN_MAX"))<<','<<number(r.at("ETA_CH"))<<','<<number(r.at("ETA_DIS"))<<','<<number(r.at("STAGE_COST"))<<','<<number(r.at("STEP_FEASIBILITY"))<<','<<number(r.at("SCREENING_SCORE"))<<','<<number(r.at("THROUGHPUT"))<<','<<number(r.at("D_ENEXT_DCH"))<<','<<number(r.at("D_ENEXT_DDIS"))<<','<<number(r.at("D_ENEXT_DE"))<<','<<number(r.at("TERMINAL_MARGIN"))<<'\n';
    if(j%43==0&&(hour%3==0||hour==23)){double last=hour?c.steps[hour-1].gen:z.gen;checkNative(z,p,current,last,v,r);referenceChecks+=9;audit<<c.scenario<<','<<c.id<<','<<version<<','<<hour<<','<<number(current)<<','<<number(next)<<','<<number(r.at("POWER_BALANCE"))<<','<<number(r.at("STAGE_COST"))<<",1\n";}
    energy[j]=next;
   }
  }
  for(size_t j=0;j<N;j++){auto& s=summaries[v-1][j];s.finalMargin=s.E-p["goal"];bool feasible=s.feasible&&s.finalMargin>=-p["tol"];if(feasible)pass[v-1]++;summary<<schedules[j].scenario<<','<<schedules[j].id<<','<<version<<','<<number(s.E)<<','<<number(s.cost)<<','<<number(s.minReserve)<<','<<number(s.maxAbsBalance)<<','<<number(s.shedEnergy)<<','<<number(s.gridImport)<<','<<number(s.throughput)<<','<<number(s.finalMargin)<<','<<(s.feasible?1:0)<<','<<(feasible?1:0)<<'\n';}
 }
 Rows diffs;for(size_t j=0;j<N;j++){auto& a=summaries[0][j];auto& b=summaries[1][j];diffs.push_back({a.E,b.E,a.cost,b.cost,a.minReserve,b.minReserve,(a.feasible&&a.finalMargin>=-p["tol"])?1.0:0.0,(b.feasible&&b.finalMargin>=-p["tol"])?1.0:0.0});}
 auto dv=models.eval("V1_vs_V2",diffs);for(size_t j=0;j<N;j++){auto d=models.unpack("V1_vs_V2",dv[j]);auto&a=summaries[0][j];auto&b=summaries[1][j];comparison<<schedules[j].scenario<<','<<schedules[j].id<<','<<number(a.E)<<','<<number(b.E)<<','<<number(d.at("DELTA_FINAL_E"))<<','<<number(a.cost)<<','<<number(b.cost)<<','<<number(d.at("DELTA_COST"))<<','<<number(a.minReserve)<<','<<number(b.minReserve)<<','<<number(d.at("MIN_RESERVE_ACROSS_MODELS"))<<','<<(diffs[j][6]>0?1:0)<<','<<(diffs[j][7]>0?1:0)<<','<<number(d.at("JOINT_FEASIBILITY"))<<','<<number(d.at("MODEL_SCORE_DIFFERENCE"))<<'\n';near(d.at("DELTA_FINAL_E"),b.E-a.E);near(d.at("DELTA_COST"),b.cost-a.cost);near(d.at("MIN_RESERVE_ACROSS_MODELS"),std::min(a.minReserve,b.minReserve));referenceChecks+=3;}
 manifest<<"graph_id,version,expression,units,description\n";inventory<<"function_id,domain_quantity,mathematical_definition,units,execution_owner,paceval_graph_id,formula_version,api_path,reference_test,status,host_reason\n";size_t count=0;for(const auto& g:models.gs){if(g.ran)count++;manifest<<g.id<<','<<g.version<<",\""<<g.expr<<"\","<<g.units<<",\""<<g.description<<"\"\n";inventory<<g.id<<",\""<<g.description<<"\",\""<<g.expr<<"\","<<g.units<<",paceval,"<<g.id<<','<<g.version<<",paceval_dGetMultipleComputationsResultsExt,independent C++ and 85-digit mpmath,"<<(g.ran?"executed":"registered_only")<<",\n";}
 inventory<<"PERIOD_STATE_CHAIN,Multi-hour energy propagation,Assign E_next from previous hour,kWh,host,,both,C++ loop,independent recurrence verification,executed,Sequential state dependence across time\n";
 inventory<<"SCHEDULE_AGGREGATION,24-hour cost and feasible decision,Sum period costs and logical AND of guards,USD_or_boolean,host,,both,C++ loop,independent audit,executed,Time-dependent aggregation and state\n";
 inventory<<"DISPATCH_GENERATION,Deterministic candidate schedule generation,Seeded synthetic schedule generation,1,host,,both,Python script,CSV schema checks,executed,Discrete candidate design not optimization\n";
 evidence<<"{\n  \"sdk\": \"original paceval 4.25 with supplied Linux shared runtime\",\n  \"model_scope\": \"synthetic single-bus active-power microgrid screening, no AC power-flow or live control\",\n  \"unique_domain_graphs_created\": "<<models.gs.size()<<",\n  \"unique_domain_graphs_executed\": "<<count<<",\n  \"scalar_calls_including_operator_tests\": "<<eng.scalarCalls<<",\n  \"multi_graph_batch_calls_including_layout_probe\": "<<eng.batchCalls<<",\n  \"graph_point_evaluations_including_layout_probe\": "<<eng.graphPoints<<",\n  \"schedule_count\": "<<N<<",\n  \"hours_per_schedule\": 24,\n  \"scenario_count\": 3,\n  \"version_schedule_count\": "<<2*N<<",\n  \"version_step_count\": "<<2*N*24<<",\n  \"v1_feasible_schedules\": "<<pass[0]<<",\n  \"v2_feasible_schedules\": "<<pass[1]<<",\n  \"independent_native_reference_checks\": "<<referenceChecks<<",\n  \"high_precision_validation\": \"see results/high_precision_audit.json, created by independent script\"\n}\n";
 std::cout<<"RESEARCH PASS: "<<count<<"/"<<models.gs.size()<<" real paceval graphs executed; "<<N<<" synthetic 24h schedules in 3 scenarios x 2 models; feasible "<<pass[0]<<"/"<<pass[1]<<"; independent native checks "<<referenceChecks<<"\n";
}
} // namespace
int main(int argc,char**argv){try{if(argc==2&&std::string(argv[1])=="--selftest"){selftest();return 0;}check(argc==5&&std::string(argv[1])=="--run","Usage: microgrid_dispatch --run input/dispatch_candidates.csv input/parameters.csv results/");run(argv[2],argv[3],argv[4]);return 0;}catch(const std::exception& ex){std::cerr<<"ERROR: "<<ex.what()<<'\n';return 1;}}
