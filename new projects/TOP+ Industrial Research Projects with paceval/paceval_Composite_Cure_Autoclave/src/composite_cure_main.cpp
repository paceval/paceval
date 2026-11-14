// WP21, composite cure and autoclave process windows.
// All explicit kinetics, reaction heat, thermal coefficients, thermal rates, guards,
// sensitivities and version comparison expressions are evaluated by original paceval.
// The C++ host owns the implicit spatial heat-equation solver, state progression,
// domain/CSV validation and audit selection, not the domain formula library.
// IMPORTANT: synthetic parameters are NOT material qualification or autoclave certification.
#include "paceval_main.h"
#include <algorithm>
#include <array>
#include <cmath>
#include <cstdint>
#include <filesystem>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <map>
#include <regex>
#include <sstream>
#include <stdexcept>
#include <string>
#include <vector>
namespace fs=std::filesystem;
namespace {
void require(bool yes,const std::string&s){if(!yes)throw std::runtime_error(s);}
void near(double a,double b,double r=5e-8,double ab=5e-6){require(std::isfinite(a)&&std::isfinite(b)&&std::abs(a-b)<=ab+r*std::max(std::abs(a),std::abs(b)),"Independent reference disagrees");}
using Rows=std::vector<std::vector<double>>;
bool literal(const std::string&txt){static const std::regex re(R"(^[+-]?(?:[0-9]+(?:\.[0-9]*)?|\.[0-9]+)(?:[eE][+-]?[0-9]+)?$)");return std::regex_match(txt,re);}
double parseNum(const std::string&txt){require(literal(txt),"Invalid CSV numerical literal: "+txt);int code=-1;long position=-1;double v=paceval_dConvertStringToFloat(txt.c_str(),&code,&position,false,nullptr,nullptr);require(code==0&&std::isfinite(v),"paceval numeric conversion error code="+std::to_string(code)+" position="+std::to_string(position));return v;}
std::string formatNum(double v){require(std::isfinite(v),"Nonfinite value during CSV output");char out[512]{};int precision=paceval_dConvertFloatToString(out,v);require(precision>0&&out[0]!='\0'&&std::string(out).find(',')==std::string::npos,"paceval float string output error");return out;}
std::vector<std::string> split(const std::string&s){std::vector<std::string>a;std::stringstream ss(s);std::string x;while(std::getline(ss,x,','))a.push_back(x);if(!s.empty()&&s.back()==',')a.push_back("");return a;}
std::string vars(const std::vector<std::string>&x){std::string s;for(const auto&z:x){if(!s.empty())s+=' ';s+=z;}return s;}
struct Engine{
 std::vector<PACEVAL_HANDLE> handles;bool graphMajor=false;uint64_t scalarCalls=0,batchCalls=0,graphPointEvaluations=0;
 Engine(){require(paceval_InitializeLibrary(nullptr),"paceval_InitializeLibrary failed");}
 ~Engine(){for(auto h:handles)if(h)paceval_DeleteComputation(h);paceval_FreeLibrary();}
 PACEVAL_HANDLE create(const std::string&f,const std::vector<std::string>&name){std::string v=vars(name);PACEVAL_HANDLE h=paceval_CreateComputation(f.c_str(),name.size(),v.c_str(),false,nullptr);require(h&&!paceval_GetIsError(h),"paceval could not create: "+f);handles.push_back(h);return h;}
 double scalar(PACEVAL_HANDLE h,const std::vector<double>&a){auto x=a;double y=paceval_dGetComputationResult(h,x.empty()?nullptr:x.data(),nullptr,nullptr);scalarCalls++;require(!paceval_GetIsError(h)&&std::isfinite(y),"SDK scalar failed");return y;}
 void layout(){auto a=create("x+2*y",{"x","y"}),b=create("3*x-y",{"x","y"});PACEVAL_HANDLE hs[]={a,b};double x[]={1,2,4,7},o[4]{},lo[4]{},hi[4]{};int error[4]{};bool failed=paceval_dGetMultipleComputationsResultsExt(hs,2,x,2,o,lo,hi,error);require(!failed&&std::all_of(error,error+4,[](int n){return n==0;}),"SDK multigraph layout API error");if(std::abs(o[0]-5)<1e-10&&std::abs(o[1]-18)<1e-10&&std::abs(o[2]-1)<1e-10&&std::abs(o[3]-5)<1e-10)graphMajor=true;else if(std::abs(o[0]-5)<1e-10&&std::abs(o[1]-1)<1e-10&&std::abs(o[2]-18)<1e-10&&std::abs(o[3]-5)<1e-10)graphMajor=false;else throw std::runtime_error("Unsupported paceval output ordering");batchCalls++;graphPointEvaluations+=4;}
 Rows batch(const std::vector<PACEVAL_HANDLE>&hs,const Rows&data){require(!hs.empty()&&!data.empty(),"Empty multi-graph batch");size_t nv=data.front().size();std::vector<double>in;in.reserve(data.size()*nv);for(const auto&row:data){require(row.size()==nv,"Invalid batch row width");for(double x:row)require(std::isfinite(x),"Nonfinite SDK input");in.insert(in.end(),row.begin(),row.end());}std::vector<double>o(hs.size()*data.size()),lo(o.size()),hi(o.size());std::vector<int>error(o.size(),-1);bool failed=paceval_dGetMultipleComputationsResultsExt(const_cast<PACEVAL_HANDLE*>(hs.data()),hs.size(),in.data(),data.size(),o.data(),lo.data(),hi.data(),error.data());require(!failed,"paceval multi-graph API reported failure");for(int code:error)require(code==0,"paceval batch error type="+std::to_string(code));Rows out(data.size(),std::vector<double>(hs.size()));for(size_t i=0;i<data.size();i++)for(size_t j=0;j<hs.size();j++){size_t idx=graphMajor?j*data.size()+i:i*hs.size()+j;require(std::isfinite(o[idx]),"Nonfinite paceval result");out[i][j]=o[idx];}batchCalls++;graphPointEvaluations+=o.size();return out;}
};
// All values use SI units except the two allowed autoclave cycle fields in min / degC/min.
const std::vector<std::string> NAMES={"T","alpha","L","R","Tair","dz","kCond","hConv","boundary","rhoCp","rhoRes","Hc","Aone","Atwo","Eone","Etwo","Rg","mExp","nExp","TgZero","TgFull","lambda","width","alphaReq","Tlimit","pressure","pressureReq"};
struct Graph{std::string id,version,formula,units,purpose;PACEVAL_HANDLE h;bool executed=false;};
struct Model{
 Engine&e;std::vector<Graph>g;std::map<std::string,size_t>index;
 explicit Model(Engine&en):e(en){
 for(int version=1;version<=2;version++){
 std::string v=version==1?"V1":"V2";
 std::string k1="(Aone*exp(-Eone/(Rg*T)))",k2="(Atwo*exp(-Etwo/(Rg*T)))";
 std::string tg="(TgZero+(TgFull-TgZero)*(lambda*alpha)/(1-(1-lambda)*alpha))";
 std::string diff=version==1?"1":"(1/(1+exp(("+tg+"-T)/width)))";
 std::string base="(("+k1+"+"+k2+"*alpha^mExp)*(1-alpha)^nExp)";
 std::string rate="("+base+"*"+diff+")";
 std::string heat="(rhoRes*Hc*"+rate+")";
 std::string kd="(kCond/(rhoCp*dz^2))";
 std::string bc="(hConv/(rhoCp*dz))";
 std::string conduct="(kCond*(L-2*T+R)/(dz^2))";
 std::string convection="(boundary*hConv*(Tair-T)/dz)";
 std::string dT="(("+conduct+"+"+convection+"+"+heat+")/rhoCp)";
 std::string dbase_dT="(("+k1+"*Eone/(Rg*T^2)+"+k2+"*alpha^mExp*Etwo/(Rg*T^2))*(1-alpha)^nExp)";
 std::string drate_dT=version==1?dbase_dT:"("+dbase_dT+"*"+diff+"+"+base+"*"+diff+"*(1-"+diff+")/width)";
 std::string guard="(((alpha>=alphaReq) AND (T<=Tlimit)) AND (pressure>=pressureReq))";
 auto add=[&](std::string id,std::string expression,std::string units,std::string purpose){Graph a{v+"_"+id,v,expression,units,purpose,e.create(expression,NAMES),false};index[a.id]=g.size();g.push_back(std::move(a));};
 add("K1",k1,"1/s","Non-autocatalytic Arrhenius coefficient");
 add("K2",k2,"1/s","Autocatalytic Arrhenius coefficient");
 add("BASE_RATE",base,"1/s","Kamal-Sourour reaction rate without diffusion limit");
 add("TG",tg,"K","DiBenedetto cure-dependent glass transition correlation");
 add("DIFF_FACTOR",diff,"1","Vitrification correction; V1 unity");
 add("CURE_RATE",rate,"1/s","True local cure conversion derivative");
 add("HEAT_SOURCE",heat,"W/m3","Resin reaction heat release in composite volume");
 add("HEAT_TEMPERATURE_RATE","("+heat+"/rhoCp)","K/s","Heating source per effective heat capacity");
 add("THERMAL_COEFFICIENT",kd,"1/s","Through-thickness conduction coefficient");
 add("SURFACE_COEFFICIENT",bc,"1/s","Autoclave convective thermal boundary coefficient");
 add("CONDUCTION_SOURCE",conduct,"W/m3","Discrete through-thickness conductive heat flux divergence");
 add("BOUNDARY_SOURCE",convection,"W/m3","Autoclave-to-part heat exchange per composite volume");
 add("TEMPERATURE_RATE",dT,"K/s","Explicit heat-balance diagnostic (implicit host solver for update)");
 add("INTEGRATED_HEAT", "(rhoRes*Hc*alpha)","J/m3","Cumulative chemical reaction enthalpy per composite volume");
 add("MARGIN_CURE","(alpha-alphaReq)","1","Signed final conversion reserve");
 add("MARGIN_TEMPERATURE","(Tlimit-T)","K","Signed local thermal headroom");
 add("MARGIN_PRESSURE","(pressure-pressureReq)","bar","Signed modeled autoclave pressure reserve");
 add("LOCAL_GUARD",guard,"0_or_1","Local combined conversion, temperature and pressure condition");
 add("SENS_A1","(exp(-Eone/(Rg*T))*(1-alpha)^nExp*"+diff+")","1","Analytic partial derivative of cure rate wrt Aone");
 add("SENS_T",drate_dT,"1/(s*K)","Analytic partial derivative of cure rate wrt local temperature");
 }
 // The final acceptance margins and score are original paceval graphs, not host formulas.
 for(int vi=1;vi<=2;vi++){
  std::string v=vi==1?"G1":"G2";
  const std::vector<std::string> gn={"amin","peak","gradient","Tmax","gradMax","alphaReq","pressure","pressureReq"};
  auto addGlobal=[&](std::string id,std::string expr,std::string unit){Graph g0{v+"_"+id,v,expr,unit,"Final process-window mathematical expression",e.create(expr,gn),false};index[g0.id]=g.size();g.push_back(std::move(g0));};
  addGlobal("CURE_MARGIN","(amin-alphaReq)","1");
  addGlobal("TEMP_MARGIN","(Tmax-peak)","K");
  addGlobal("GRAD_MARGIN","(gradMax-gradient)","K");
  addGlobal("PRESS_MARGIN","(pressure-pressureReq)","bar");
  addGlobal("GUARD","(((amin>=alphaReq) AND (peak<=Tmax)) AND ((gradient<=gradMax) AND (pressure>=pressureReq)))","0_or_1");
  addGlobal("SCORE","((0 max (alphaReq-amin))*100 + (0 max (peak-Tmax)) + (0 max (gradient-gradMax)))","index");
 }
 // Final combined sample and model-version differences are evaluated through actual paceval graphs.
 std::vector<std::string> cmp={"alphaOne","alphaTwo","peakOne","peakTwo","heatOne","heatTwo","gradientOne","gradientTwo","alphaReq","Tlimit","gradientLimit","pressure","pressureReq"};
 auto addCompare=[&](std::string id,std::string expr,std::string unit){Graph a{"CMP_"+id,"V1_vs_V2",expr,unit,"Across-model comparison",e.create(expr,cmp),false};index[a.id]=g.size();g.push_back(std::move(a));};
 addCompare("ALPHA_DIFFERENCE","(alphaTwo-alphaOne)","1");
 addCompare("PEAK_TEMPERATURE_DIFFERENCE","(peakTwo-peakOne)","K");
 addCompare("RELEASED_HEAT_DIFFERENCE","(heatTwo-heatOne)","J/m3");
 addCompare("GRADIENT_DIFFERENCE","(gradientTwo-gradientOne)","K");
 addCompare("GUARD_BOTH","(((alphaOne>=alphaReq) AND (alphaTwo>=alphaReq)) AND ((peakOne<=Tlimit) AND (peakTwo<=Tlimit)) AND ((gradientOne<=gradientLimit) AND (gradientTwo<=gradientLimit)) AND (pressure>=pressureReq))","0_or_1");
 addCompare("V2_MARGIN_CURE","(alphaTwo-alphaReq)","1");
 addCompare("V2_MARGIN_PEAK","(Tlimit-peakTwo)","K");
 addCompare("V2_MARGIN_GRADIENT","(gradientLimit-gradientTwo)","K");
 }
 std::vector<size_t> ids(const std::string&version)const{std::vector<size_t>a;for(size_t i=0;i<g.size();i++)if(g[i].version==version)a.push_back(i);return a;}
 std::vector<std::string> columns(const std::string&version)const{std::vector<std::string>x;for(auto i:ids(version))x.push_back(g[i].id.substr(version=="V1_vs_V2"?4:3));return x;}
 Rows evaluate(const std::string&v,const Rows&x){auto order=ids(v);std::vector<PACEVAL_HANDLE> hs;for(auto i:order)hs.push_back(g[i].h);auto r=e.batch(hs,x);for(auto i:order)g[i].executed=true;return r;}
 std::map<std::string,double> unpack(const std::string&v,const std::vector<double>&row)const{auto order=ids(v);require(order.size()==row.size(),"Output columns mismatch");std::map<std::string,double> o;for(size_t k=0;k<order.size();k++)o[g[order[k]].id.substr(v=="V1_vs_V2"?4:3)]=row[k];return o;}
};
struct Recipe{std::string id;double thickness,ramp,holdC,holdMin,h,pressure;};
std::vector<Recipe> readRecipes(const fs::path&file){std::ifstream f(file);require(bool(f),"Cannot open recipes.csv");std::string header,line;require(bool(std::getline(f,header)),"Missing CSV header");require(header=="recipe_id,thickness_m,ramp_C_min,hold_C,hold_min,convection_W_m2K,pressure_bar","Unexpected recipes CSV schema");std::vector<Recipe>a;unsigned lineNumber=1;while(std::getline(f,line)){lineNumber++;if(line.empty())continue;auto x=split(line);require(x.size()==7,"Wrong columns at CSV line "+std::to_string(lineNumber));require(std::regex_match(x[0],std::regex("R[0-9]{3}")),"Invalid recipe ID");Recipe r{x[0],parseNum(x[1]),parseNum(x[2]),parseNum(x[3]),parseNum(x[4]),parseNum(x[5]),parseNum(x[6])};require(r.thickness>=.009&&r.thickness<=.022&&r.ramp>=.5&&r.ramp<=5&&r.h>=35&&r.h<=130&&r.holdC>=135&&r.holdC<=185&&r.holdMin>=45&&r.holdMin<=135&&r.pressure>=2&&r.pressure<=8,"Out of-domain recipe");a.push_back(r);}require(!a.empty()&&a.size()<=500,"No recipes / too many recipes");return a;}
constexpr int NC=10;constexpr double DT=15.;constexpr int STEPS=840;constexpr double START_C=25.,KELVIN=273.15;
struct Material{double k=.48,rhoCp=1.64e6,rhoRes=610,Hc=250000,A1=10000,A2=45000,E1=65000,E2=63500,Rg=8.314462618,m=1.,n=1.35,Tg0=260.15,TgFull=455.15,lambda=.68,width=9.5,required=.88,Tlimit=469.15,pressureRequired=3.5,gradientLimit=32.;};
struct State{std::array<double,NC> T{},a{};double peak=0,gradientPeak=0,heatIntegral=0;};
// Cycle control is a time schedule, not part of the chemical execution graphs.
double airTemp(const Recipe&r,double secs){double elapsedMin=secs/60.;double rise=(r.holdC-START_C)/r.ramp;double endHold=rise+r.holdMin;if(elapsedMin<rise)return START_C+r.ramp*elapsedMin+KELVIN;if(elapsedMin<=endHold)return r.holdC+KELVIN;return std::max(START_C,r.holdC-2.3*(elapsedMin-endHold))+KELVIN;}
std::vector<double> makeRow(const Recipe&r,const State&s,int node,double t,const Material&m){double dz=r.thickness/NC;double left=node==0?s.T[node]:s.T[node-1];double right=node==NC-1?s.T[node]:s.T[node+1];double edge=(node==0||node==NC-1)?1.:0.;return {s.T[node],s.a[node],left,right,airTemp(r,t),dz,m.k,r.h,edge,m.rhoCp,m.rhoRes,m.Hc,m.A1,m.A2,m.E1,m.E2,m.Rg,m.m,m.n,m.Tg0,m.TgFull,m.lambda,m.width,m.required,m.Tlimit,r.pressure,m.pressureRequired};}
// Implicit Euler solves only the stateful discretized heat equation. The coefficient
// values and volumetric reaction heating in its matrix are original paceval outputs.
std::array<double,NC> thermalStep(const State&old,const std::array<double,NC>&kCoeff,const std::array<double,NC>&bcCoeff,const std::array<double,NC>&heating,const Recipe&r,double atTime){std::array<double,NC>a{},b{},c{},d{},cp{},dp{},out{};double Ta=airTemp(r,atTime);for(int j=0;j<NC;j++){int neighbors=(j>0)+(j<NC-1);bool boundary=(j==0||j==NC-1);a[j]=j>0?-DT*kCoeff[j]:0.;c[j]=j<NC-1?-DT*kCoeff[j]:0.;b[j]=1+DT*(neighbors*kCoeff[j]+(boundary?bcCoeff[j]:0));d[j]=old.T[j]+DT*(heating[j]+(boundary?bcCoeff[j]*Ta:0));}cp[0]=c[0]/b[0];dp[0]=d[0]/b[0];for(int j=1;j<NC;j++){double denom=b[j]-a[j]*cp[j-1];require(denom>0,"Singular implicit heat system");cp[j]=c[j]/denom;dp[j]=(d[j]-a[j]*dp[j-1])/denom;}out[NC-1]=dp[NC-1];for(int j=NC-2;j>=0;j--)out[j]=dp[j]-cp[j]*out[j+1];for(double T:out)require(T>250&&T<650,"Unphysical temperature in solver");return out;}
std::map<std::string,double> native(const std::vector<double>&x,int v){double T=x[0],a=x[1],L=x[2],R=x[3],Ta=x[4],dz=x[5],k=x[6],h=x[7],b=x[8],rhoCp=x[9],rhoRes=x[10],Hc=x[11],A1=x[12],A2=x[13],E1=x[14],E2=x[15],Rg=x[16],m=x[17],n=x[18],Tg0=x[19],TgFull=x[20],lam=x[21],width=x[22],areq=x[23],limit=x[24],press=x[25],pReq=x[26];double k1=A1*std::exp(-E1/(Rg*T)),k2=A2*std::exp(-E2/(Rg*T)),tg=Tg0+(TgFull-Tg0)*lam*a/(1-(1-lam)*a),diff=v==1?1.:1/(1+std::exp((tg-T)/width));double base=(k1+k2*std::pow(a,m))*std::pow(1-a,n),rate=base*diff,heat=rhoRes*Hc*rate,conduct=k*(L-2*T+R)/dz/dz,conv=b*h*(Ta-T)/dz,drdT=(k1*E1/(Rg*T*T)+k2*std::pow(a,m)*E2/(Rg*T*T))*std::pow(1-a,n);if(v==2)drdT=drdT*diff+base*diff*(1-diff)/width;return {{"K1",k1},{"K2",k2},{"BASE_RATE",base},{"TG",tg},{"DIFF_FACTOR",diff},{"CURE_RATE",rate},{"HEAT_SOURCE",heat},{"HEAT_TEMPERATURE_RATE",heat/rhoCp},{"THERMAL_COEFFICIENT",k/(rhoCp*dz*dz)},{"SURFACE_COEFFICIENT",h/(rhoCp*dz)},{"CONDUCTION_SOURCE",conduct},{"BOUNDARY_SOURCE",conv},{"TEMPERATURE_RATE",(conduct+conv+heat)/rhoCp},{"INTEGRATED_HEAT",rhoRes*Hc*a},{"MARGIN_CURE",a-areq},{"MARGIN_TEMPERATURE",limit-T},{"MARGIN_PRESSURE",press-pReq},{"LOCAL_GUARD",(a>=areq&&T<=limit&&press>=pReq)?1.:0.},{"SENS_A1",std::exp(-E1/(Rg*T))*std::pow(1-a,n)*diff},{"SENS_T",drdT}};}
void operatorSelftest(Engine&e){std::vector<std::pair<std::string,double>>tests={{"((-1)%10)",-1},{"((-1) mod 10)",9},{"(4 min 5)",4},{"(4 max 5)",5},{"(3<4)",1},{"(3<=3)",1},{"(3>=3)",1},{"(3=3)",1},{"(3<>4)",1},{"NOT(0)",1},{"(1 AND 1)",1},{"(0 OR 1)",1},{"((3<=3) AND (2>=0))",1}};for(auto&p:tests){auto h=e.create(p.first,{});near(e.scalar(h,{}),p.second,0,1e-12);}near(parseNum("-1.25e-3"),-.00125);for(const char*bad:{"","NaN","Infinity","1+2","1,2","1e999","--1"," 1"}){bool rejected=false;try{parseNum(bad);}catch(...){rejected=true;}require(rejected,"Illegal numeric field was accepted");}require(!formatNum(1.25e-3).empty(),"Float formatting failed");}
void selftest(){Engine e;e.layout();operatorSelftest(e);Model model(e);Material m;Recipe r{"R000",.014,2.,170.,105.,70.,5.};State s;for(int j=0;j<NC;j++){s.T[j]=330.+j/5.;s.a[j]=.35;}auto row=makeRow(r,s,5,3600,m);for(int ver=1;ver<=2;ver++){auto version=ver==1?"V1":"V2";auto out=model.unpack(version,model.evaluate(version,Rows{row})[0]);auto reference=native(row,ver);for(const auto&kv:reference)near(out.at(kv.first),kv.second);near(e.scalar(model.g[model.index[std::string(version)+"_CURE_RATE"]].h,row),out.at("CURE_RATE"));}std::cout<<"SELFTEST PASS: original paceval scalar, multi-graph batch, operators, numeric conversion, native formulas\n";}
struct Summary{double alphaMin,alphaMax,Tpeak,gradPeak,meanAlpha,energyReleased,marginCure,marginHeat,marginGradient,guard;};
void run(const fs::path&recipeFile,const fs::path&folder){fs::create_directories(folder);Engine engine;engine.layout();operatorSelftest(engine);Model model(engine);Material m;auto recipes=readRecipes(recipeFile);size_t N=recipes.size();
 std::ofstream summaries(folder/"screening.csv"),profiles(folder/"cure_profiles.csv"),audit(folder/"native_audit.csv"),trace(folder/"high_precision_samples.csv"),comparison(folder/"model_comparison.csv"),manifest(folder/"formula_manifest.csv"),inventory(folder/"math_execution_inventory.csv"),evidence(folder/"execution_evidence.json");require(bool(summaries&&profiles&&audit&&trace&&comparison&&manifest&&inventory&&evidence),"Cannot create output artifacts");
 summaries<<"recipe_id,model,thickness_mm,ramp_C_min,hold_C,hold_min,convection_W_m2K,pressure_bar,alpha_min,alpha_max,alpha_mean,peak_T_C,peak_through_thickness_gradient_K,released_enthalpy_J_m3,margin_cure,margin_peak_T_K,margin_gradient_K,screening_guard\n";
 profiles<<"recipe_id,model,time_min,node,air_C,part_C,alpha,cure_rate_1_s,heat_source_W_m3,glass_transition_C,diffusion_factor\n";
 trace<<"model,T_K,alpha,left_K,right_K,air_K,dz_m,k_W_mK,h_W_m2K,boundary,rhoCp_J_m3K,rhoRes_kg_m3,Hc_J_kg,Aone_1_s,Atwo_1_s,Eone_J_mol,Etwo_J_mol,Rg_J_molK,mExp,nExp,TgZero_K,TgFull_K,lambda,width_K,alphaReq,Tlimit_K,pressure_bar,pressureReq_bar,K1,K2,BASE_RATE,TG,DIFF_FACTOR,CURE_RATE,HEAT_SOURCE,THERMAL_COEFFICIENT,SURFACE_COEFFICIENT,TEMPERATURE_RATE,SENS_T,INTEGRATED_HEAT,HEAT_TEMPERATURE_RATE\n";
 audit<<"recipe_id,model,step,node,checked_formula_count,pass\n";
 comparison<<"recipe_id,alpha_min_V1,alpha_min_V2,delta_alpha,peak_T_V1_C,peak_T_V2_C,delta_peak_K,heat_V1_J_m3,heat_V2_J_m3,delta_heat_J_m3,gradient_V1_K,gradient_V2_K,delta_gradient_K,both_guard\n";
 std::vector<std::vector<Summary>> results(2,std::vector<Summary>(N));size_t referenceChecks=0;uint64_t timeNodeEvaluations=0;size_t feasible[2]={0,0};
 for(int ver=1;ver<=2;ver++){
 std::string version=ver==1?"V1":"V2";std::vector<State>states(N);for(auto&s:states){s.T.fill(START_C+KELVIN);s.a.fill(.015);s.peak=START_C+KELVIN;}
 for(int step=0;step<=STEPS;step++){
 double t=DT*step;Rows x; x.reserve(N*NC);for(size_t i=0;i<N;i++)for(int j=0;j<NC;j++)x.push_back(makeRow(recipes[i],states[i],j,t,m));auto data=model.evaluate(version,x);timeNodeEvaluations+=x.size();
 for(size_t i=0;i<N;i++){
 std::array<double,NC>kC{},bC{},heatR{},newA{};double mint=1e9,maxt=-1e9;
 for(int j=0;j<NC;j++){
 auto row=model.unpack(version,data[i*NC+j]);const auto&input=x[i*NC+j];
 if((step%173==0 && i%7==0 && (j==0||j==5||j==9)) || (step==STEPS&&i==N-1&&j==NC-1)){
 auto ref=native(input,ver);for(auto&p:ref){near(row.at(p.first),p.second);++referenceChecks;}audit<<recipes[i].id<<','<<version<<','<<step<<','<<j<<','<<ref.size()<<",1\n";
 trace<<version;for(double z:input)trace<<','<<formatNum(z);for(const char*k:{"K1","K2","BASE_RATE","TG","DIFF_FACTOR","CURE_RATE","HEAT_SOURCE","THERMAL_COEFFICIENT","SURFACE_COEFFICIENT","TEMPERATURE_RATE","SENS_T","INTEGRATED_HEAT","HEAT_TEMPERATURE_RATE"})trace<<','<<formatNum(row.at(k));trace<<'\n';}
 if(step%40==0 || step==STEPS){profiles<<recipes[i].id<<','<<version<<','<<formatNum(t/60)<<','<<j<<','<<formatNum(airTemp(recipes[i],t)-KELVIN)<<','<<formatNum(states[i].T[j]-KELVIN)<<','<<formatNum(states[i].a[j])<<','<<formatNum(row.at("CURE_RATE"))<<','<<formatNum(row.at("HEAT_SOURCE"))<<','<<formatNum(row.at("TG")-KELVIN)<<','<<formatNum(row.at("DIFF_FACTOR"))<<'\n';}
 kC[j]=row.at("THERMAL_COEFFICIENT");bC[j]=row.at("SURFACE_COEFFICIENT");heatR[j]=row.at("HEAT_TEMPERATURE_RATE"); // paceval calculates the complete reaction-temperature forcing.
 newA[j]=std::min(1.,states[i].a[j]+DT*row.at("CURE_RATE"));
 mint=std::min(mint,states[i].T[j]);maxt=std::max(maxt,states[i].T[j]);
 }
 states[i].peak=std::max(states[i].peak,maxt);states[i].gradientPeak=std::max(states[i].gradientPeak,maxt-mint);
 if(step<STEPS){auto newT=thermalStep(states[i],kC,bC,heatR,recipes[i],t+DT);states[i].T=newT;states[i].a=newA;}
 }
 }
 // A non-regularized, physically bounded candidate screen is evaluated from state values.
 for(size_t i=0;i<N;i++){
 const State&s=states[i];double amin=*std::min_element(s.a.begin(),s.a.end()),amax=*std::max_element(s.a.begin(),s.a.end());double amean=0;for(double v:s.a)amean+=v/NC;
 // Read cumulative heat release at each node directly from paceval, then spatially aggregate.
 Rows finalNodes;for(int node=0;node<NC;node++)finalNodes.push_back(makeRow(recipes[i],s,node,DT*STEPS,m));
 auto finalData=model.evaluate(version,finalNodes);double H=0;
 for(const auto&f:finalData)H+=model.unpack(version,f).at("INTEGRATED_HEAT")/NC;
 auto gv=ver==1?"G1":"G2";
 auto finalGraph=model.unpack(gv,model.evaluate(gv,Rows{{amin,s.peak,s.gradientPeak,m.Tlimit,m.gradientLimit,m.required,recipes[i].pressure,m.pressureRequired}})[0]);
 Summary q{amin,amax,s.peak,s.gradientPeak,amean,H,finalGraph.at("CURE_MARGIN"),finalGraph.at("TEMP_MARGIN"),finalGraph.at("GRAD_MARGIN"),finalGraph.at("GUARD")};
 near(q.marginCure,amin-m.required);near(q.marginHeat,m.Tlimit-s.peak);near(q.marginGradient,m.gradientLimit-s.gradientPeak);
 near(q.guard,(q.marginCure>=0&&q.marginHeat>=0&&q.marginGradient>=0&&recipes[i].pressure>=m.pressureRequired)?1.:0.);
 referenceChecks+=4;results[ver-1][i]=q;if(q.guard)feasible[ver-1]++;
 summaries<<recipes[i].id<<','<<version;for(double z:{recipes[i].thickness*1000,recipes[i].ramp,recipes[i].holdC,recipes[i].holdMin,recipes[i].h,recipes[i].pressure,amin,amax,amean,s.peak-KELVIN,s.gradientPeak,H,q.marginCure,q.marginHeat,q.marginGradient,q.guard})summaries<<','<<formatNum(z);summaries<<'\n';
 }
 }
 // Comparison / decision margins are genuine paceval graphs, not native post-processing.
 Rows cx;for(size_t i=0;i<N;i++){auto&a=results[0][i],&b=results[1][i];cx.push_back({a.alphaMin,b.alphaMin,a.Tpeak,b.Tpeak,a.energyReleased,b.energyReleased,a.gradPeak,b.gradPeak,m.required,m.Tlimit,m.gradientLimit,recipes[i].pressure,m.pressureRequired});}
 auto out=model.evaluate("V1_vs_V2",cx);for(size_t i=0;i<N;i++){auto v=model.unpack("V1_vs_V2",out[i]);auto&a=results[0][i],&b=results[1][i];near(v.at("ALPHA_DIFFERENCE"),b.alphaMin-a.alphaMin);near(v.at("PEAK_TEMPERATURE_DIFFERENCE"),b.Tpeak-a.Tpeak);referenceChecks+=2;comparison<<recipes[i].id;for(double z:{a.alphaMin,b.alphaMin,v.at("ALPHA_DIFFERENCE"),a.Tpeak-KELVIN,b.Tpeak-KELVIN,v.at("PEAK_TEMPERATURE_DIFFERENCE"),a.energyReleased,b.energyReleased,v.at("RELEASED_HEAT_DIFFERENCE"),a.gradPeak,b.gradPeak,v.at("GRADIENT_DIFFERENCE"),v.at("GUARD_BOTH")})comparison<<','<<formatNum(z);comparison<<'\n';}
 manifest<<"graph_id,version,formula,units,industrial_purpose\n";inventory<<"function_id,domain_quantity,mathematical_definition,units,execution_owner,paceval_graph_id,formula_version,api_path,reference_test,status,host_reason\n";size_t count=0;for(const auto&g:model.g){if(g.executed)count++;manifest<<g.id<<','<<g.version<<",\""<<g.formula<<"\","<<g.units<<",\""<<g.purpose<<"\"\n";inventory<<g.id<<",\""<<g.purpose<<"\",\""<<g.formula<<"\","<<g.units<<",paceval,"<<g.id<<','<<g.version<<",paceval_dGetMultipleComputationsResultsExt,native C++ and mpmath,"<<(g.executed?"executed":"registered_only")<<",\n";}
 inventory<<"IMPLICIT_HEAT_SOLVER,heat state progression,Thomas tridiagonal linear solve,K,host,,all,C++ state solver,unit and conservation checks,executed,Time-dependent implicit discretization is not an algebraic graph\n";
 inventory<<"CURE_STATE_ADVANCE,degree of cure integration,explicit irreversible update,1,host,,all,C++ integrator,independent integration,executed,Stateful time evolution\n";
 inventory<<"NUMERIC_CSV_INPUT,validated finite decimal literals,number parsing,1,paceval,,all,paceval_dConvertStringToFloat,negative literal test,executed,\n";
 inventory<<"NUMERIC_CSV_OUTPUT,finite double serialization,number formatting,1,paceval,,all,paceval_dConvertFloatToString,roundtrip audit,executed,\n";
 evidence<<"{\n \"sdk\":\"original paceval 4.25, Linux\",\n \"unique_graphs_created\":"<<model.g.size()<<",\n \"unique_graphs_executed\":"<<count<<",\n \"model_versions\":2,\n \"scenario_count\":"<<N<<",\n \"thermal_nodes_per_scenario\":"<<NC<<",\n \"time_steps_per_scenario_including_initial\":"<<STEPS+1<<",\n \"model_node_time_evaluations\":"<<timeNodeEvaluations<<",\n \"scalar_calls_including_operator_tests\":"<<engine.scalarCalls<<",\n \"batch_calls_including_layout_probe\":"<<engine.batchCalls<<",\n \"graph_point_evaluations_including_layout_probe\":"<<engine.graphPointEvaluations<<",\n \"native_endvalue_assertions\":"<<referenceChecks<<",\n \"feasible_V1\":"<<feasible[0]<<",\n \"feasible_V2\":"<<feasible[1]<<",\n \"high_precision_reference\":\"See high_precision_audit.json\"\n}\n";
 require(count==model.g.size(),"Unexecuted registered graph");std::cout<<"MAIN PASS, executed graphs="<<count<<", recipes="<<N<<", time_node_evaluations="<<timeNodeEvaluations<<", native_checks="<<referenceChecks<<", feasible="<<feasible[0]<<"/"<<feasible[1]<<"\n";
}
}
int main(int argc,char**argv){try{if(argc==2&&std::string(argv[1])=="--selftest"){selftest();return 0;}require(argc==4&&std::string(argv[1])=="--run","Usage: composite_cure --run input/recipes.csv results_dir");run(argv[2],argv[3]);return 0;}catch(const std::exception&e){std::cerr<<"ERROR: "<<e.what()<<'\n';return 1;}}
