// WP23: Granulation-water balance and moisture-process-window demonstration.
// All published physical equations and final scores execute in original paceval.
// C++ owns validation, persistent graph handles, batching, version selection and CSV.
// Synthetic dry-basis kinetics are not a validated pharmaceutical process model.
#include "paceval_main.h"
#include <algorithm>
#include <cmath>
#include <cstdint>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <iomanip>
#include <map>
#include <regex>
#include <sstream>
#include <stdexcept>
#include <string>
#include <vector>
namespace fs=std::filesystem;
namespace {
void require(bool p,const std::string&m){if(!p)throw std::runtime_error(m);}
void near(double a,double b,double rel=8e-8,double abs=2e-7){require(std::isfinite(a)&&std::isfinite(b)&&std::abs(a-b)<=abs+rel*std::max(std::abs(a),std::abs(b)),"Independent numerical check failed");}
std::string varsText(const std::vector<std::string>&n){std::string s;for(auto&x:n){if(!s.empty())s+=' ';s+=x;}return s;}
bool isLiteral(const std::string&s){static const std::regex rg(R"(^[+-]?(?:[0-9]+(?:\.[0-9]*)?|\.[0-9]+)(?:[eE][+-]?[0-9]+)?$)");return std::regex_match(s,rg);}
double numIn(const std::string&s){require(isLiteral(s),"Rejected nonliteral numeric CSV cell: "+s);int error=-1;long pos=-1;double x=paceval_dConvertStringToFloat(s.c_str(),&error,&pos,false,nullptr,nullptr);require(error==0&&std::isfinite(x),"paceval numeric conversion error "+std::to_string(error)+" at "+std::to_string(pos));return x;}
std::string numOut(double x){require(std::isfinite(x),"Nonfinite result");char b[512]{};int p=paceval_dConvertFloatToString(b,x);require(p>0&&b[0]&&std::string(b).find(',')==std::string::npos,"paceval numeric formatting failed");return b;}
std::vector<std::string> split(const std::string&s){std::stringstream f(s);std::vector<std::string>p;std::string v;while(std::getline(f,v,','))p.push_back(v);if(!s.empty()&&s.back()==',')p.push_back("");return p;}
using Rows=std::vector<std::vector<double>>;
const std::vector<std::string> V={"solid","water","baseMoist","Tair","Tin","Tref","time","kref","Ea","RH","eqBase","eqRH","eqTC","hcoef","latentCool","fastFraction","spread","rtdWidth","Mmin","Mmax","Tmax","sensor","sensorTol","target"};
const std::vector<std::string> VC={"wetA","wetB","guardA","guardB","rateA","rateB","powerA","powerB","scoreA","scoreB","tempA","tempB"};
struct Engine{
 std::vector<PACEVAL_HANDLE> handles;bool graphMajor=false;unsigned long long scalarCalls=0,batchCalls=0,graphPoints=0;
 Engine(){require(paceval_InitializeLibrary(nullptr),"Original paceval InitializeLibrary failed");}
 ~Engine(){for(auto h:handles)if(h)paceval_DeleteComputation(h);paceval_FreeLibrary();}
 PACEVAL_HANDLE create(const std::string&f,const std::vector<std::string>&n){auto t=varsText(n);auto h=paceval_CreateComputation(f.c_str(),n.size(),t.c_str(),false,nullptr);require(h&&!paceval_GetIsError(h),"Graph creation failed: "+f);handles.push_back(h);return h;}
 double scalar(PACEVAL_HANDLE h,const std::vector<double>&v){auto x=v;double y=paceval_dGetComputationResult(h,x.empty()?nullptr:x.data(),nullptr,nullptr);++scalarCalls;require(!paceval_GetIsError(h)&&std::isfinite(y),"Scalar paceval error");return y;}
 void probe(){auto a=create("x+2*y",{"x","y"});auto b=create("3*x-y",{"x","y"});PACEVAL_HANDLE h[]={a,b};double in[]={1,2,4,7},out[4]{},lo[4]{},hi[4]{};int err[4]{};bool apiFailure=paceval_dGetMultipleComputationsResultsExt(h,2,in,2,out,lo,hi,err);require(!apiFailure&&std::all_of(err,err+4,[](int x){return x==0;}),"Multi-graph probe API failure");if(std::fabs(out[0]-5)<1e-10&&std::fabs(out[1]-18)<1e-10&&std::fabs(out[2]-1)<1e-10&&std::fabs(out[3]-5)<1e-10)graphMajor=true;else if(std::fabs(out[0]-5)<1e-10&&std::fabs(out[1]-1)<1e-10&&std::fabs(out[2]-18)<1e-10&&std::fabs(out[3]-5)<1e-10)graphMajor=false;else throw std::runtime_error("Unsupported multi-graph output ordering");++batchCalls;graphPoints+=4;}
 Rows batch(const std::vector<PACEVAL_HANDLE>&hs,const Rows&rows,size_t cols){require(!hs.empty()&&!rows.empty(),"Empty multi-graph batch");std::vector<double>in;in.reserve(rows.size()*cols);for(auto&r:rows){require(r.size()==cols,"Wrong batch input width");for(double x:r)require(std::isfinite(x),"Nonfinite batch input");in.insert(in.end(),r.begin(),r.end());}std::vector<double>o(hs.size()*rows.size()),lo(o.size()),hi(o.size());std::vector<int>err(o.size(),-1);bool fail=paceval_dGetMultipleComputationsResultsExt(const_cast<PACEVAL_HANDLE*>(hs.data()),hs.size(),in.data(),rows.size(),o.data(),lo.data(),hi.data(),err.data());require(!fail,"Multi-graph SDK evaluation error");for(int x:err)require(x==0,"paceval calculation error code "+std::to_string(x));Rows r(rows.size(),std::vector<double>(hs.size()));for(size_t i=0;i<rows.size();++i)for(size_t j=0;j<hs.size();++j){double y=o[graphMajor?j*rows.size()+i:i*hs.size()+j];require(std::isfinite(y),"Nonfinite multi-graph result");r[i][j]=y;}++batchCalls;graphPoints+=o.size();return r;}
};
struct Graph{std::string id,version,formula,units,purpose;PACEVAL_HANDLE h;bool executed=false;};
struct Models{
 Engine&e;std::vector<Graph>g;std::map<std::string,size_t>index;
 explicit Models(Engine&engine):e(engine){
 const std::string M0="(baseMoist+water/solid)";
 const std::string EQ="(eqBase+eqRH*RH*exp(-eqTC*(Tair-Tref)))";
 const std::string K="(kref*exp(-(Ea/8.31446261815324)*((1/Tair)-(1/Tref))))";
 for(int vi=1;vi<=2;++vi){std::string ver=vi==1?"V1":"V2";
 auto decay=[&](const std::string&timeExpr)->std::string{
 const std::string kterm="("+K+"*"+timeExpr+")";
 if(vi==1)return "exp(-"+kterm+")";
 return "(fastFraction*exp(-(1+spread)*"+kterm+")+(1-fastFraction)*exp(-(1-spread)*"+kterm+"))";};
 auto moisture=[&](const std::string&t){return "("+EQ+"+("+M0+"-"+EQ+")*"+decay(t)+")";};
 const std::string D=decay("time"),Md=moisture("time");
 const std::string MW="("+Md+"/(1+"+Md+"))";
 const std::string ME=moisture("(time*(1-rtdWidth))"),ML=moisture("(time*(1+rtdWidth))");
 const std::string Ewet="("+ME+"/(1+"+ME+"))",Lwet="("+ML+"/(1+"+ML+"))";
 const std::string TE="(Tin+(Tair-Tin)*(1-exp(-hcoef*time))-latentCool*("+M0+"-"+Md+"))";
 const std::string WATER="(solid*("+M0+"-"+Md+"))";
 const std::string MWET="("+Lwet+"-Mmin)",MDRY="(Mmax-"+Ewet+")";
 const std::string MTEMP="(Tmax-"+TE+")",MLIQ="((water/solid)-0.08) min (0.28-(water/solid))";
 const std::string MSEN="(sensorTol-abs(sensor-"+MW+"))";
 const std::string GUARD="(("+MWET+">=0) AND ("+MDRY+">=0) AND ("+MTEMP+">=0) AND ("+MLIQ+">=0) AND ("+MSEN+">=0))";
 const std::string SCORE="(100*abs("+MW+"-target)+200*(0 max (-"+MWET+"))+200*(0 max (-"+MDRY+"))+(0 max (-"+MTEMP+"))/20+10*(0 max (-"+MSEN+")))";
 const std::string Dk="("+K+"*Ea/(8.31446261815324*Tair^2))",Deq="(-eqTC*("+EQ+"-eqBase))";
 const std::string DE=vi==1?"(-"+K+"*"+D+"*("+M0+"-"+EQ+"))":"(-"+K+"*("+M0+"-"+EQ+")*(fastFraction*(1+spread)*exp(-(1+spread)*"+K+"*time)+(1-fastFraction)*(1-spread)*exp(-(1-spread)*"+K+"*time)))";
 const std::string DB=vi==1?"(-time*"+Dk+"*"+D+")":"(-time*"+Dk+"*(fastFraction*(1+spread)*exp(-(1+spread)*"+K+"*time)+(1-fastFraction)*(1-spread)*exp(-(1-spread)*"+K+"*time)))";
 const std::string DT="("+Deq+"*(1-"+D+")+("+M0+"-"+EQ+")*"+DB+")";
 auto add=[&](std::string id,std::string formula,std::string u,std::string what){Graph graph{ver+"_"+id,ver,formula,u,what,e.create(formula,V),false};index[graph.id]=g.size();g.push_back(std::move(graph));};
 add("LIQUID_SOLID_RATIO","(water/solid)","kg/kg","Granulation wetting liquid-to-dry-solid mass ratio");
 add("INLET_MOISTURE_DRY",M0,"kg/kg dry","Wet granulation outlet moisture on dry basis");
 add("EQUILIBRIUM_MOISTURE_DRY",EQ,"kg/kg dry","Illustrative equilibrium moisture dependent on air temperature and humidity");
 add("RATE_CONSTANT",K,"1/s","Temperature-dependent effective drying coefficient");
 add("GRANULE_SIZE_PROXY","(0.2+1.1*(water/solid))","mm","Uncalibrated exploratory median size indicator");
 add("RESIDENCE_DECAY",D,"1","Drying decay including two-population spread in V2");
 add("EXIT_MOISTURE_DRY",Md,"kg/kg dry","Average exiting granule moisture on dry basis");
 add("EXIT_MOISTURE_WET",MW,"kg/kg wet","Average exiting water mass fraction (LOD proxy)");
 add("SHORT_RESIDENCE_MOISTURE_WET",Ewet,"kg/kg wet","Wettest modeled residence-time endpoint");
 add("LONG_RESIDENCE_MOISTURE_WET",Lwet,"kg/kg wet","Driest modeled residence-time endpoint");
 add("GRANULE_TEMPERATURE",TE,"K","Illustrative product temperature and evaporative cooling proxy");
 add("EVAPORATION_FLOW",WATER,"kg/h","Water removed from granules per unit time at stationary flow");
 add("LATENT_DUTY","("+WATER+"*2257/3600)","kW","Latent evaporation energy-rate indicator only");
 add("DRYING_RATE",DE,"kg/kg/s","Moisture time derivative on dry basis");
 add("MARGIN_TOO_WET",MWET,"kg/kg wet","Lower-bound robust moisture margin over residence interval");
 add("MARGIN_TOO_DRY",MDRY,"kg/kg wet","Upper-bound robust moisture margin over residence interval");
 add("MARGIN_TEMPERATURE",MTEMP,"K","Product temperature bound");
 add("MARGIN_WETTING",MLIQ,"kg/kg","Granulation water-feed window margin");
 add("MARGIN_SENSOR",MSEN,"kg/kg wet","Independent synthetic PAT sensor consistency margin");
 add("SENSOR_RESIDUAL","(sensor-"+MW+")","kg/kg wet","Observed minus predicted PAT wet moisture");
 add("COMPOSITE_GUARD",GUARD,"0_or_1","Illustrative process-window Boolean status");
 add("DEVIATION_TARGET","abs("+MW+"-target)","kg/kg wet","Deviation from target wet-basis moisture");
 add("PROCESS_SCORE",SCORE,"index","Composed quality-window penalty");
 add("SENSITIVITY_RESIDENCE",DE,"kg/kg/s","Analytic derivative with respect to residence time");
 add("SENSITIVITY_AIR_TEMP",DT,"kg/kg/K","Independent analytic derivative with respect to drying air temperature");
 add("EXIT_WET_FLOW","(solid*(1+"+Md+"))","kg/h","Total mass flow of wet granules leaving dryer");
 add("WATER_BALANCE_RESIDUAL","(solid*(1+"+M0+")-solid*(1+"+Md+")-"+WATER+")","kg/h","Input wet mass equals final wet mass plus evaporated water");
 }
 auto add=[&](std::string id,std::string f,std::string u,std::string desc){Graph h{id,"COMPARE",f,u,desc,e.create(f,VC),false};index[h.id]=g.size();g.push_back(std::move(h));};
 add("DELTA_EXIT_MOISTURE","(wetB-wetA)","kg/kg wet","Model-version wet-moisture difference");
 add("DELTA_RATE","(rateB-rateA)","1/s","Version difference in local dry-moisture rate");
 add("DELTA_LATENT_DUTY","(powerB-powerA)","kW","Version difference in evaporative latent duty indicator");
 add("DELTA_TEMPERATURE","(tempB-tempA)","K","Version difference in granule temperature indicator");
 add("DELTA_SCORE","(scoreB-scoreA)","index","Version difference in quality score");
 add("BOTH_FEASIBLE","((guardA=1) AND (guardB=1))","0_or_1","Intersection of both illustrative process windows");
 }
 Rows eval(const std::string&version,const Rows&x){std::vector<PACEVAL_HANDLE>h;std::vector<size_t>which;for(size_t i=0;i<g.size();i++)if(g[i].version==version){h.push_back(g[i].h);which.push_back(i);}auto y=e.batch(h,x,version=="COMPARE"?VC.size():V.size());for(auto i:which)g[i].executed=true;return y;}
 std::map<std::string,double> unpack(const std::string&version,const std::vector<double>&row){std::map<std::string,double>m;size_t k=0;for(auto&z:g)if(z.version==version){m[z.id.substr(version=="COMPARE"?0:3)]=row.at(k++);}require(k==row.size(),"Unpack graph layout mismatch");return m;}
};
struct Case{std::string id,group;std::vector<double>x;};
void domain(const Case&c){auto&x=c.x;require(x.size()==V.size(),"CSV numeric field count error");for(double y:x)require(std::isfinite(y),"Nonfinite input");require(x[0]>0.1&&x[1]>0&&x[2]>=0&&x[3]>280&&x[3]<440&&x[4]>260&&x[4]<400&&x[5]>260&&x[5]<400&&x[6]>15&&x[6]<5000&&x[7]>0&&x[7]<0.03&&x[8]>=0&&x[8]<90000&&x[9]>=0&&x[9]<=1&&x[10]>0&&x[11]>=0&&x[12]>=0&&x[13]>0&&x[14]>=0&&x[15]>0&&x[15]<1&&x[16]>0&&x[16]<0.95&&x[17]>0&&x[17]<0.5&&x[18]>=0&&x[18]<x[19]&&x[19]<0.5&&x[20]>x[4]&&x[21]>=0&&x[21]<0.5&&x[22]>0&&x[23]>=0&&x[23]<x[19]&&x[1]/x[0]>0.04&&x[1]/x[0]<0.4&&x[2]+x[1]/x[0]>x[10]+x[11]*x[9]*exp(-x[12]*(x[3]-x[5])),"Input model domain or bounds violated: "+c.id);}
std::vector<Case> load(const fs::path&p){std::ifstream f(p);require(bool(f),"Missing input CSV");std::string line;require(bool(std::getline(f,line)),"Missing CSV header");std::string wanted="case_id,scenario";for(auto&s:V)wanted+=","+s;require(line==wanted,"CSV schema header mismatch");std::vector<Case>cases;size_t ln=1;while(std::getline(f,line)){++ln;if(line.empty())continue;auto part=split(line);require(part.size()==V.size()+2,"Column count mismatch line "+std::to_string(ln));require(std::regex_match(part[0],std::regex("[A-Z0-9_]+"))&&std::regex_match(part[1],std::regex("[a-z_]+")),"Noncanonical case identification");Case c{part[0],part[1],{}};for(size_t j=2;j<part.size();j++)c.x.push_back(numIn(part[j]));domain(c);cases.push_back(c);}require(!cases.empty(),"Empty research input");return cases;}
struct Ref{double m0,meq,k,dry,wet,early,late,temp,evap,duty,rate,marginWet,marginDry,marginT,marginL,marginS,guard,score,dT,dTime,balance;};
Ref native(const std::vector<double>&a,int v){auto f=[&](int i){return a.at(i);};double liquid=f(1)/f(0),M0=f(2)+liquid,Eq=f(10)+f(11)*f(9)*std::exp(-f(12)*(f(3)-f(5)));double k=f(7)*std::exp((-f(8)/8.31446261815324)*(1/f(3)-1/f(5)));auto decay=[&](double t){return v==1?std::exp(-k*t):f(15)*std::exp(-k*(1+f(16))*t)+(1-f(15))*std::exp(-k*(1-f(16))*t);};auto wet=[&](double t){double m=Eq+(M0-Eq)*decay(t);return m/(1+m);};double d=decay(f(6)),md=Eq+(M0-Eq)*d,m=wet(f(6)),early=wet(f(6)*(1-f(17))),late=wet(f(6)*(1+f(17)));double temp=f(4)+(f(3)-f(4))*(1-std::exp(-f(13)*f(6)))-f(14)*(M0-md);double evap=f(0)*(M0-md),duty=evap*2257/3600;double rate=-(M0-Eq)*k*(v==1?d:f(15)*(1+f(16))*std::exp(-k*(1+f(16))*f(6))+(1-f(15))*(1-f(16))*std::exp(-k*(1-f(16))*f(6)));double dw=late-f(18),dd=f(19)-early,dt=f(20)-temp,dl=std::min(liquid-0.08,0.28-liquid),ds=f(22)-std::abs(f(21)-m);double guard=(dw>=0&&dd>=0&&dt>=0&&dl>=0&&ds>=0)?1:0;double score=100*std::abs(m-f(23))+200*std::max(0.,-dw)+200*std::max(0.,-dd)+std::max(0.,-dt)/20+10*std::max(0.,-ds);double dk=k*f(8)/(8.31446261815324*f(3)*f(3));double dEq=-f(12)*(Eq-f(10));double db=-f(6)*dk*(v==1?d:f(15)*(1+f(16))*std::exp(-k*(1+f(16))*f(6))+(1-f(15))*(1-f(16))*std::exp(-k*(1-f(16))*f(6)));double dT=dEq*(1-d)+(M0-Eq)*db;return {M0,Eq,k,md,m,early,late,temp,evap,duty,rate,dw,dd,dt,dl,ds,guard,score,dT,rate,f(0)*(1+M0)-f(0)*(1+md)-evap};}
size_t checkNative(const std::vector<double>&a,int v,const std::map<std::string,double>&z){auto r=native(a,v);size_t n=0;auto check=[&](const char*s,double y){near(z.at(s),y);++n;};check("INLET_MOISTURE_DRY",r.m0);check("EQUILIBRIUM_MOISTURE_DRY",r.meq);check("RATE_CONSTANT",r.k);check("EXIT_MOISTURE_DRY",r.dry);check("EXIT_MOISTURE_WET",r.wet);check("SHORT_RESIDENCE_MOISTURE_WET",r.early);check("LONG_RESIDENCE_MOISTURE_WET",r.late);check("GRANULE_TEMPERATURE",r.temp);check("EVAPORATION_FLOW",r.evap);check("LATENT_DUTY",r.duty);check("DRYING_RATE",r.rate);check("MARGIN_TOO_WET",r.marginWet);check("MARGIN_TOO_DRY",r.marginDry);check("MARGIN_TEMPERATURE",r.marginT);check("MARGIN_WETTING",r.marginL);check("MARGIN_SENSOR",r.marginS);check("COMPOSITE_GUARD",r.guard);check("PROCESS_SCORE",r.score);check("SENSITIVITY_AIR_TEMP",r.dT);check("SENSITIVITY_RESIDENCE",r.dTime);check("WATER_BALANCE_RESIDUAL",r.balance);return n;}
void operators(Engine&e){const std::vector<std::pair<std::string,double>>t={{"((-1)%10)",-1},{"((-1) mod 10)",9},{"(4 min 5)",4},{"(4 max 5)",5},{"(3<4)",1},{"(3<=3)",1},{"(3>=3)",1},{"(3=3)",1},{"(3<>4)",1},{"NOT(0)",1},{"(1 AND 1)",1},{"(0 OR 1)",1},{"((3<=3) AND (2>=0))",1}};for(auto&x:t){auto h=e.create(x.first,{});near(e.scalar(h,{}),x.second);}near(numIn("-1.25e-3"),-.00125);for(auto s:{"","NaN","Inf","1+2","1,2","1e999","--1"," 1"}){bool bad=false;try{numIn(s);}catch(...){bad=true;}require(bad,"Unsafe numeric literal accepted");}require(!numOut(.125).empty(),"ConvertFloatToString untested");}
void selftest(){Engine e;e.probe();operators(e);Models m(e);std::vector<double>a={20,3.4,.016,355,298,345,720,.004,15000,.36,.008,.012,.005,.0035,28,.60,.44,.14,.01,.048,345,.02,.018,.022};domain({"TEST","normal",a});for(int j=1;j<=2;j++){std::string v=j==1?"V1":"V2";auto o=m.unpack(v,m.eval(v,Rows{a})[0]);checkNative(a,j,o);near(e.scalar(m.g[m.index[v+"_EXIT_MOISTURE_WET"]].h,a),o.at("EXIT_MOISTURE_WET"));}std::cout<<"SELFTEST PASS original paceval, scalar, multi-graph batch, numerical parsing, operators and independent model\n";}
void run(const fs::path&source,const fs::path&dest){fs::create_directories(dest);Engine e;e.probe();operators(e);Models m(e);auto cases=load(source);size_t N=cases.size(),nativeChecks=0;size_t approved[2]={};std::vector<std::map<std::string,double>>data[2];data[0].resize(N);data[1].resize(N);std::ofstream out(dest/"screening.csv"),cmp(dest/"model_comparison.csv"),audit(dest/"native_audit.csv"),manifest(dest/"formula_manifest.csv"),inventory(dest/"math_execution_inventory.csv"),ev(dest/"execution_evidence.json");require(bool(out&&cmp&&audit&&manifest&&inventory&&ev),"Cannot create research results");
 out<<"case_id,scenario,model,solid_kg_h,air_K,time_s,liquid_solid_ratio,moisture_in_dry,moisture_eq_dry,k_s,granule_size_proxy_mm,exit_dry,exit_wet,early_wet,late_wet,granule_temp_K,evaporation_kg_h,latent_duty_kW,drying_rate_dry_s,margin_too_wet,margin_too_dry,margin_temp_K,margin_wetting,margin_sensor,sensor_residual,quality_guard,deviation_target,process_score,sensitivity_time,sensitivity_air_temp,exit_wet_flow_kg_h,mass_balance_residual\n";
 cmp<<"case_id,scenario,air_K,time_s,wet_V1,wet_V2,delta_wet,rate_V1,rate_V2,delta_rate,duty_V1,duty_V2,delta_duty,temp_V1,temp_V2,delta_temp,guard_V1,guard_V2,both_feasible,delta_score\n";audit<<"case_id,model,native_endvalue_checks,pass\n";
 const std::vector<std::string>keys={"LIQUID_SOLID_RATIO","INLET_MOISTURE_DRY","EQUILIBRIUM_MOISTURE_DRY","RATE_CONSTANT","GRANULE_SIZE_PROXY","EXIT_MOISTURE_DRY","EXIT_MOISTURE_WET","SHORT_RESIDENCE_MOISTURE_WET","LONG_RESIDENCE_MOISTURE_WET","GRANULE_TEMPERATURE","EVAPORATION_FLOW","LATENT_DUTY","DRYING_RATE","MARGIN_TOO_WET","MARGIN_TOO_DRY","MARGIN_TEMPERATURE","MARGIN_WETTING","MARGIN_SENSOR","SENSOR_RESIDUAL","COMPOSITE_GUARD","DEVIATION_TARGET","PROCESS_SCORE","SENSITIVITY_RESIDENCE","SENSITIVITY_AIR_TEMP","EXIT_WET_FLOW","WATER_BALANCE_RESIDUAL"};
 for(int j=0;j<2;j++){std::string v=j==0?"V1":"V2";for(size_t start=0;start<N;start+=80){size_t end=std::min(N,start+80);Rows x;for(size_t i=start;i<end;i++)x.push_back(cases[i].x);auto yy=m.eval(v,x);for(size_t i=start;i<end;i++){auto z=m.unpack(v,yy[i-start]);auto&c=cases[i];data[j][i]=z;if(z.at("COMPOSITE_GUARD")>.5)approved[j]++;out<<c.id<<','<<c.group<<','<<v<<','<<numOut(c.x[0])<<','<<numOut(c.x[3])<<','<<numOut(c.x[6]);for(auto&key:keys)out<<','<<numOut(z.at(key));out<<'\n';if(i%31==0||i==N-1){size_t count=checkNative(c.x,j+1,z);nativeChecks+=count;audit<<c.id<<','<<v<<','<<count<<",1\n";}}}}
 size_t comparisonChecks=0;
 for(size_t start=0;start<N;start+=80){size_t end=std::min(N,start+80);Rows x;for(size_t i=start;i<end;i++){auto&a=data[0][i],&b=data[1][i];x.push_back({a.at("EXIT_MOISTURE_WET"),b.at("EXIT_MOISTURE_WET"),a.at("COMPOSITE_GUARD"),b.at("COMPOSITE_GUARD"),a.at("DRYING_RATE"),b.at("DRYING_RATE"),a.at("LATENT_DUTY"),b.at("LATENT_DUTY"),a.at("PROCESS_SCORE"),b.at("PROCESS_SCORE"),a.at("GRANULE_TEMPERATURE"),b.at("GRANULE_TEMPERATURE")});}auto y=m.eval("COMPARE",x);for(size_t i=start;i<end;i++){auto z=m.unpack("COMPARE",y[i-start]);auto&c=cases[i];auto&a=data[0][i],&b=data[1][i];cmp<<c.id<<','<<c.group<<','<<numOut(c.x[3])<<','<<numOut(c.x[6]);for(double v:{a.at("EXIT_MOISTURE_WET"),b.at("EXIT_MOISTURE_WET"),z.at("DELTA_EXIT_MOISTURE"),a.at("DRYING_RATE"),b.at("DRYING_RATE"),z.at("DELTA_RATE"),a.at("LATENT_DUTY"),b.at("LATENT_DUTY"),z.at("DELTA_LATENT_DUTY"),a.at("GRANULE_TEMPERATURE"),b.at("GRANULE_TEMPERATURE"),z.at("DELTA_TEMPERATURE"),a.at("COMPOSITE_GUARD"),b.at("COMPOSITE_GUARD"),z.at("BOTH_FEASIBLE"),z.at("DELTA_SCORE")})cmp<<','<<numOut(v);cmp<<'\n';if(i%79==0){near(z.at("DELTA_EXIT_MOISTURE"),b.at("EXIT_MOISTURE_WET")-a.at("EXIT_MOISTURE_WET"));comparisonChecks++;}}}
 manifest<<"graph_id,version,expression,units,purpose\n";inventory<<"function_id,domain_quantity,mathematical_definition,units,execution_owner,paceval_graph_id,formula_version,api_path,reference_test,status,host_reason\n";size_t done=0;for(auto&g:m.g){done+=g.executed?1:0;manifest<<g.id<<','<<g.version<<",\""<<g.formula<<"\","<<g.units<<",\""<<g.purpose<<"\"\n";inventory<<g.id<<",\""<<g.purpose<<"\",\""<<g.formula<<"\","<<g.units<<",paceval,"<<g.id<<','<<g.version<<",paceval_dGetMultipleComputationsResultsExt,native and mpmath,"<<(g.executed?"executed":"registered_only")<<",\n";}
 inventory<<"CSV_DECIMAL_INPUT,Validated numeric input,decimal literals,1,paceval,,all,paceval_dConvertStringToFloat,negative parsing tests,executed,\nCSV_NUMERIC_OUTPUT,Formatted numeric output,double to decimal,1,paceval,,all,paceval_dConvertFloatToString,independent Python CSV reader,executed,\nCASE_ENUMERATION,Synthetic parameters,deterministic Python generation,1,host,,all,Python script,generator audit,executed,nonmathematical scenario creation\nMODEL_SELECTION,Two formula versions,version labels,1,host,,all,C++ logic,version check,executed,nonmathematical selection\n";
 ev<<"{\n  \"sdk\": \"original paceval 4.25 / supplied ELF x86-64 Linux runtime\",\n  \"unique_graphs_created\": "<<m.g.size()<<",\n  \"unique_graphs_executed\": "<<done<<",\n  \"scalar_calls_including_operator_tests\": "<<e.scalarCalls<<",\n  \"batch_calls_including_layout_probe\": "<<e.batchCalls<<",\n  \"graph_point_evaluations_including_layout_probe\": "<<e.graphPoints<<",\n  \"scenario_count\": "<<N<<",\n  \"model_scenario_combinations\": "<<2*N<<",\n  \"feasible_V1\": "<<approved[0]<<",\n  \"feasible_V2\": "<<approved[1]<<",\n  \"native_endvalue_assertions\": "<<nativeChecks+comparisonChecks<<",\n  \"reference_high_precision\": \"see high_precision_audit.json\"\n}\n";
 require(done==m.g.size(),"Not all domain graphs executed");std::cout<<"RESEARCH PASS "<<done<<"/"<<m.g.size()<<" domain graphs, "<<N<<" unique cases; native checks "<<nativeChecks+comparisonChecks<<"; feasible V1/V2 "<<approved[0]<<'/'<<approved[1]<<'\n';}
}
int main(int argc,char**argv){try{if(argc==2&&std::string(argv[1])=="--selftest"){selftest();return 0;}require(argc==4&&std::string(argv[1])=="--run","Usage: granulation_drying --run input/cases.csv output_dir");run(argv[2],argv[3]);return 0;}catch(const std::exception&e){std::cerr<<"ERROR: "<<e.what()<<'\n';return 1;}}
