// WP_039 Battery Charging Cost and Aging Terms - real paceval C++ research demonstrator.
// Copyright (c) 2026 paceval research study authors.
// The SDK interface paceval_main.h / paceval_main.cpp retains its original copyright headers.
//
// SCIENTIFIC LIMIT: Cycle and calendar penalties here are dimensionless synthetic
// surrogates, NOT empirically calibrated capacity-fade, SOH, or battery lifetime.
// Time, energy, driving and tariffs are deterministic synthetic experimental data.
//
// MATHEMATICAL EXECUTION: all 23 declared domain functions are paceval computations.
// THE C++ HOST performs time-indexed dynamic programming, discrete state indexing,
// file I/O and independent numerical checks. No pseudo-paceval replacement is used.
#include "paceval_main.h"
#include <algorithm>
#include <array>
#include <cmath>
#include <cstddef>
#include <filesystem>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <limits>
#include <memory>
#include <numeric>
#include <sstream>
#include <stdexcept>
#include <string>
#include <vector>
using namespace std;
namespace fs=std::filesystem;
static void require(bool ok,const string&why){if(!ok)throw runtime_error(why);}
static constexpr int NV=17, NS=36, NT=24, NA=6;
static constexpr double CAP=64.4, ETA=0.92;
static constexpr double SOCLO=0.15, SOCHI=0.92, PMAX=10.;
static constexpr int INITIAL=17, TARGET=28;
// Variables all declared in the same order for every persistent computation graph.
static const char* VARNAMES="p price soc temp dt eta cap cy cal alpha wAge wSmooth pMax socLo socHi co2 drive";
using Input=array<double,NV>;
struct Formula{string id,expression,unit,explanation;PACEVAL_HANDLE h=nullptr;};
static string cyc(){return "cy*(p/10)^2*dt";}
static string mid(){return "(soc-drive/cap+0.5*p*dt*eta/cap)";}
static string cal(){return "cal*"+mid()+"^2*exp(alpha*(temp-25))*dt";}
static string risk(){return "("+cyc()+"+"+cal()+")";}
static string smooth(){return "wSmooth*(p/10)^2*dt";}
static vector<Formula> makeRegistry(){
 const string m=mid(),r=risk(),s=smooth();
 return {
  {"grid_energy", "p*dt", "kWh", "Purchased grid energy per charging slot"},
  {"stored_energy", "p*dt*eta", "kWh", "Stored DC energy under fixed efficiency"},
  {"driving_energy", "drive", "kWh", "Fixed exogenous travel consumption"},
  {"soc_after_drive", "soc-drive/cap", "fraction", "SOC immediately after an exogenous travel event"},
  {"soc_next", "soc-drive/cap+p*dt*eta/cap", "fraction", "Exactly defined state transition"},
  {"soc_mid",m,"fraction","Within-slot SOC proxy after travel"},
  {"tariff_cost","price*p*dt","EUR","Purchased energy times TOU price"},
  {"cycle_risk",cyc(),"risk unit","Uncalibrated C-rate-like quadratic cycle stress"},
  {"calendar_risk",cal(),"risk unit","Uncalibrated SOC and temperature weighted calendar stress"},
  {"total_risk",r,"risk unit","Combined synthetic cycle and calendar stress"},
  {"aging_cost","wAge*"+r,"EUR proxy","Explicit assumed EUR per synthetic risk unit"},
  {"smoothness_cost",s,"EUR proxy","Original quadratic power regularization"},
  {"objective_v1","price*p*dt+wAge*"+r+"+"+s,"EUR proxy","Version 1 complete slot objective"},
  {"objective_v2","price*p*dt+wAge*"+r+"*(1+0.2*"+m+")+"+s,"EUR proxy","Version 2 independently persistent SOC-weighted policy"},
  {"soc_after_drive_margin","soc-drive/cap-socLo","fraction","Post-driving lower bound margin"},
  {"soc_upper_margin","socHi-(soc-drive/cap+p*dt*eta/cap)","fraction","Next-step upper bound margin"},
  {"charger_power_margin","pMax-p","kW","Nameplate charging-power margin"},
  {"grid_carbon_proxy","co2*p*dt","g CO2 proxy","Assumed electricity mix intensity times purchased energy"},
  {"marginal_tariff","price*dt","EUR per kW","Analytic tariff gradient"},
  {"marginal_cycle","wAge*cy*2*p/100*dt","EUR proxy per kW","Analytic quadratic cycle-cost gradient"},
  {"marginal_calendar","wAge*cal*2*"+m+"*(0.5*dt*eta/cap)*exp(alpha*(temp-25))*dt","EUR proxy per kW","Analytic calendar-cost gradient"},
  {"marginal_smooth","wSmooth*2*p/100*dt","EUR proxy per kW","Analytic regularization gradient"},
  {"marginal_objective_v1","price*dt+wAge*cy*2*p/100*dt+wAge*cal*2*"+m+"*(0.5*dt*eta/cap)*exp(alpha*(temp-25))*dt+wSmooth*2*p/100*dt","EUR proxy per kW","Analytic gradient of version 1"}
 };
}
static void checkInput(const Input&x){
 for(double z:x)require(isfinite(z),"nonfinite batch input rejected");
 require(x[0]>=0 && x[0]<=x[12]+1e-9,"charging power violates declared bounds");
 require(x[1]>=0 && x[1]<=2,"electric tariff out of research domain");
 require(x[2]>=0 && x[2]<=1,"SOC not in [0,1]");
 require(x[3]>=0 && x[3]<=60,"cell temperature outside declared domain");
 require(x[4]>0&&x[4]<=1.0,"time step must be positive <=1h");
 require(x[5]>0&&x[5]<=1,"efficiency not in (0,1]");
 require(x[6]>0&&x[6]<=200,"battery capacity invalid");
 require(x[7]>=0&&x[8]>=0&&x[9]>=0&&x[10]>=0&&x[11]>=0,"negative model coefficient");
 require(x[13]>=0&&x[14]<=1&&x[13]<x[14],"inconsistent SOC bounds");
 require(x[15]>=0&&x[16]>=0&&x[16]<=x[6],"invalid carbon intensity or driving energy");
}
// The SDK's batch boolean is documented as an error indicator in the tested Linux
// release; a successful batch reports FALSE. All per-result error codes are checked.
class Engine {
 vector<PACEVAL_HANDLE> owned;
public:
 vector<Formula> formulas;
 size_t calls=0,outputs=0,checks=0;
 double max_scaled_difference=0.0;
 Engine(){require(paceval_InitializeLibrary(nullptr),"original paceval runtime initialization failed");formulas=makeRegistry();for(auto&f:formulas){f.h=paceval_CreateComputation(f.expression.c_str(),NV,VARNAMES,false,nullptr);require(f.h&&!paceval_GetIsError(f.h),"create paceval computation failed: "+f.id+" / "+f.expression);owned.push_back(f.h);}}
 ~Engine(){for(auto h:owned)if(h)paceval_DeleteComputation(h);paceval_FreeLibrary();}
 size_t count()const{return formulas.size();}
 vector<double> batch(const vector<Input>&xs,bool doAudit=true){
  require(!xs.empty(),"empty batch is invalid");vector<double>v;v.reserve(xs.size()*NV);
  for(const auto&x:xs){checkInput(x);v.insert(v.end(),x.begin(),x.end());}
  vector<PACEVAL_HANDLE>handles=owned;const size_t g=handles.size(),n=xs.size();
  vector<double> out(g*n,0.0);vector<int>errors(g*n,-999);
  const bool failed=paceval_dGetMultipleComputationsResultsExt(handles.data(),(unsigned long)g,v.data(),(unsigned long)n,out.data(),nullptr,nullptr,errors.data());
  require(!failed,"original paceval Multi-Graph-Batch API returned failure");
  for(size_t i=0;i<out.size();++i)require(errors[i]==0&&isfinite(out[i]),"paceval individual result invalid / nonfinite");
  ++calls;outputs+=out.size();
  if(doAudit){for(size_t i=0;i<n;i+=max(size_t(1),n/9)){
    const auto expected=nativeReference(xs[i]);
    for(size_t j=0;j<g;++j){double a=out[j*n+i],b=expected[j],scale=1.0+fabs(b);
      double d=fabs(a-b)/scale;max_scaled_difference=max(max_scaled_difference,d);
      require(d<3e-10,"C++ mathematical reference mismatch graph="+formulas[j].id);
      ++checks;
    }
  }}return out;
 }
 static vector<double>nativeReference(const Input&x){
  const double p=x[0],price=x[1],soc=x[2],temp=x[3],dt=x[4],eta=x[5],cap=x[6],cy=x[7],cal=x[8],alpha=x[9],wAge=x[10],wSmooth=x[11],pMax=x[12],socLo=x[13],socHi=x[14],co2=x[15],drive=x[16];
  const double m=soc-drive/cap+0.5*p*dt*eta/cap;
  const double cyc=cy*pow(p/10,2)*dt, ca=cal*m*m*exp(alpha*(temp-25))*dt, risk=cyc+ca;
  const double smooth=wSmooth*pow(p/10,2)*dt;
  const double dc=wAge*cal*2*m*(0.5*dt*eta/cap)*exp(alpha*(temp-25))*dt;
  return {p*dt,p*dt*eta,drive,soc-drive/cap,soc-drive/cap+p*dt*eta/cap,m,
    price*p*dt,cyc,ca,risk,wAge*risk,smooth,
    price*p*dt+wAge*risk+smooth,
    price*p*dt+wAge*risk*(1+0.2*m)+smooth,
    soc-drive/cap-socLo,socHi-(soc-drive/cap+p*dt*eta/cap),pMax-p,
    co2*p*dt,price*dt,wAge*cy*2*p/100*dt,dc,wSmooth*2*p/100*dt,
    price*dt+wAge*cy*2*p/100*dt+dc+wSmooth*2*p/100*dt};
 }
};
struct Row {array<double,23> g{};bool valid=false;};
using Edges=vector<Row>;
static size_t edgeIndex(int t,int s,int a){return (size_t(t)*NS+s)*NA+a;}
static Input inputAt(int profile,int t,int state,int act,double weight){
 const double pi=acos(-1.0);
 double price=0.30;
 switch(profile){
 case 0:price=0.30;break;
 case 1:price=t<7?0.16:(t>=18?0.47:0.32);break;
 case 2:price=0.28+0.12*sin(2*pi*(t+3)/24)+0.055*cos(2*pi*t/7);break;
 case 3:price=t<6?0.42:(t>=18?0.14:0.33);break;
 case 4:price=0.22+0.08*(1+sin(2*pi*(t+2)/8))+0.045*sin(2*pi*t/24);break;
 case 5:price=t<8?0.24:(t>=18?0.26+0.11*(t==20||t==21):0.48);break;
 default:throw runtime_error("unrecognized profile");}
 price=max(0.07,price);
 const double p=2.0*act;const double temp=23.0+6.0*sin(2*pi*(t+3)/24)+profile*0.7;
 const double co2=310+80*sin(2*pi*(t+1)/24)+profile*8;
 const double driving=t==8?5*1.84:(t==18?3*1.84:0.0);
 return {p,price,double(state)/35.,temp,1.0,ETA,CAP,0.020,0.003,0.040,weight,0.020,PMAX,SOCLO,SOCHI,co2,driving};
}
static bool available(int t){return (t<8||t>=18);}
static const char* names[]={"flat","night_discount","wind_variation","evening_discount","short_period_volatile","evening_peak"};
static const double weights[]={0.0,8.0,30.0};
static Edges createEdges(Engine&sdk,int profile,double weight,ofstream* audit){
 Edges edges(NT*NS*NA);const size_t chunk=192;
 vector<Input>in;in.reserve(chunk);vector<size_t>idx;idx.reserve(chunk);
 auto flush=[&](){if(in.empty())return;auto out=sdk.batch(in);size_t n=in.size();
  for(size_t k=0;k<n;++k){Row&row=edges[idx[k]];for(size_t j=0;j<sdk.count();++j)row.g[j]=out[j*n+k];row.valid=true;
    if(audit && idx[k]<1800){auto&x=in[k];(*audit)<<setprecision(16)<<profile<<','<<weight<<','<<idx[k]<<','<<int(idx[k]/(NS*NA))<<','<<int(idx[k]/NA%NS)<<','<<int(idx[k]%NA);
     for(double v:x){(*audit)<<','<<v;}for(double v:row.g){(*audit)<<','<<v;}(*audit)<<'\n';}
  }in.clear();idx.clear();};
 for(int t=0;t<NT;++t)for(int s=0;s<NS;++s)for(int a=0;a<NA;++a){
  size_t ix=edgeIndex(t,s,a);in.push_back(inputAt(profile,t,s,a,weight));idx.push_back(ix);if(in.size()==chunk)flush();}
 flush();return edges;
}
struct Solution {bool feasible=false;double objective=0.0;array<int,NT>actions{};array<int,NT+1>states{};};
static Solution solveDP(const Edges&edges,int version){
 const double INF=numeric_limits<double>::infinity();
 vector<array<double,NS>>dp(NT+1);for(auto&a:dp)a.fill(INF);dp[0][INITIAL]=0.;
 struct Prev{int state=-1,action=-1;};vector<array<Prev,NS>> prev(NT+1);
 for(int t=0;t<NT;++t)for(int s=0;s<NS;++s){
  if(!isfinite(dp[t][s]))continue;
  if(t==8 && s<20)continue; // departure SOC requirement is a host constraint
  for(int a=0;a<NA;++a){if(!available(t)&&a>0)continue;
   const auto&z=edges[edgeIndex(t,s,a)];if(!z.valid)continue;
   if(z.g[14]<-1e-11||z.g[15]<-1e-11||z.g[16]<-1e-11)continue;
   const double end=z.g[4]*35.;long k=lround(end);
   // The continuous physical state is calculated by paceval; host maps to lattice.
   if(k<0||k>=NS||fabs(end-k)>3e-9)continue;
   const double val=dp[t][s]+z.g[version==1?12:13];
   if(val<dp[t+1][k]-1e-12){dp[t+1][k]=val;prev[t+1][k]={s,a};}
  }
 }
 Solution sol;if(!isfinite(dp[NT][TARGET]))return sol;
 sol.feasible=true;sol.objective=dp[NT][TARGET];int state=TARGET;sol.states[NT]=TARGET;
 for(int t=NT;t>0;--t){auto p=prev[t][state];require(p.state>=0&&p.action>=0,"broken dynamic programming reconstruction");sol.actions[t-1]=p.action;state=p.state;sol.states[t-1]=state;}
 require(state==INITIAL,"initial SOC inconsistency");return sol;
}
static void invalidInputTests(){
 Input good=inputAt(0,0,20,1,8.0);int passed=0;
 auto reject=[&](int i,double invalid){Input x=good;x[i]=invalid;try{checkInput(x);}catch(const exception&){++passed;}};
 reject(0,-1);reject(1,-.5);reject(2,1.5);reject(3,-1);reject(4,0);reject(5,0);reject(6,0);reject(10,-1);reject(15,-2);reject(16,-1);reject(0,numeric_limits<double>::quiet_NaN());
 require(passed==11,"invalid-input regression failed");
}
static void run(const fs::path&root,int nprofiles,int nweights,int surfaceN){
 require(nprofiles>=1&&nprofiles<=6&&nweights>=1&&nweights<=3&&surfaceN>=5&&surfaceN<=201,"command-line research bounds exceeded");
 invalidInputTests();fs::create_directories(root/"examples");fs::create_directories(root/"results");
 Engine sdk;const auto&reg=sdk.formulas;const int G=int(reg.size());require(G==23,"unexpected formula registry size");
 {ofstream f(root/"examples/formula_registry.csv");f<<"id,expression,units,scientific_interpretation\n";for(const auto&r:reg)f<<r.id<<",\""<<r.expression<<"\",\""<<r.unit<<"\",\""<<r.explanation<<"\"\n";}
 {ofstream f(root/"results/math_execution_inventory.csv");f<<"function,owner,actual_API,verification,scope\n";
  for(const auto&r:reg)f<<r.id<<",paceval,paceval_dGetMultipleComputationsResultsExt,independent_C++_reference_and_selected_mpmath,synthetic_cost_aging_or_operating_domain\n";
  f<<"charging_availability,C++ host,deterministic_trace,no_calculation_claim,time_slot_control\n";
  f<<"dynamic_programming,C++ host,minimum_cost_state_transition,terminal_and_path_checks,discrete_global_optimization\n";
  f<<"independent_reference,C++ and Python,explicit_native_and_mpmath,scientific_audit,not_a_paceval_execution\n";
  f<<"validated_battery_fade,NOT_EXECUTED,requires_empirical_cell_data,not_claimed,unvalidated_surrogate\n";}
 {ofstream f(root/"examples/fixed_charging_and_driving_trace.csv");f<<"scenario,hour,available,tariff_EUR_per_kWh,cell_temperature_C,grid_intensity_gCO2_per_kWh,drive_discharge_kWh,source\n"<<setprecision(16);
 for(int i=0;i<nprofiles;++i)for(int t=0;t<NT;++t){auto x=inputAt(i,t,INITIAL,0,0);f<<names[i]<<','<<t<<','<<int(available(t))<<','<<x[1]<<','<<x[3]<<','<<x[15]<<','<<x[16]<<",synthetic_fixed_trace\n";}}
 ofstream audit(root/"examples/paceval_transition_audit.csv");audit<<"profile_index,aging_weight,transition_id,hour,soc_lattice,power_action_index";
 const char*vars[]={"p","price","soc","temp","dt","eta","cap","cy","cal","alpha","wAge","wSmooth","pMax","socLo","socHi","co2","drive"};
 for(const char*v:vars){audit<<','<<v;}for(const auto&r:reg){audit<<','<<r.id;}audit<<'\n';
 ofstream summary(root/"examples/optimized_schedule_comparison.csv");summary<<"profile,aging_weight,formula_version,feasible,total_objective_EUR_proxy,electricity_cost_EUR,aging_penalty_EUR_proxy,smoothing_EUR_proxy,synthetic_risk_units,grid_energy_kWh,stored_energy_kWh,driving_energy_kWh,carbon_g_proxy,final_SOC,terminal_SOC_target\n";
 ofstream step(root/"examples/optimized_schedule_timeseries.csv");step<<"profile,aging_weight,formula_version,hour,tariff_EUR_per_kWh,charge_power_kW,available,driving_kWh,SOC_before,SOC_after,pv_grid_kWh,pv_electricity_EUR,pv_aging_EUR_proxy,pv_smoothing_EUR_proxy,pv_risk_units,incremental_objective_EUR_proxy,synthetic_carbon_g\n";
 step<<setprecision(16);summary<<setprecision(16);
 int feasibleCount=0,solutionCount=0;double maxFinalSOCerr=0.,minFinalCost=1e100,maxFinalCost=-1e100;
 for(int i=0;i<nprofiles;++i)for(int w=0;w<nweights;++w){auto edges=createEdges(sdk,i,weights[w],i==0&&w==0?&audit:nullptr);
  for(int version=1;version<=2;++version){auto sol=solveDP(edges,version);++solutionCount;feasibleCount+=sol.feasible;
   require(sol.feasible,"expected optimization scenario is infeasible: "+string(names[i]));
   double sums[7]={0,0,0,0,0,0,0};
   for(int t=0;t<NT;++t){int s=sol.states[t],act=sol.actions[t];auto x=inputAt(i,t,s,act,weights[w]);const auto&z=edges[edgeIndex(t,s,act)].g;
    require(fabs(z[4]-double(sol.states[t+1])/35.)<3e-10,"paceval SOC transition mismatch");
    if(t==8)require(sol.states[t]>=20,"departure requirement not met");
    if(!available(t))require(act==0,"charge outside availability window");
    sums[0]+=z[6];sums[1]+=version==1?z[10]:(z[13]-z[6]-z[11]);sums[2]+=z[11];sums[3]+=z[9];sums[4]+=z[0];sums[5]+=z[1];sums[6]+=z[17];
    step<<names[i]<<','<<weights[w]<<','<<version<<','<<t<<','<<x[1]<<','<<x[0]<<','<<available(t)<<','<<x[16]<<','<<double(s)/35.<<','<<z[4]<<','<<z[0]<<','<<z[6]<<','<<(version==1?z[10]:(z[13]-z[6]-z[11]))<<','<<z[11]<<','<<z[9]<<','<<z[version==1?12:13]<<','<<z[17]<<'\n';
   }
   const double recon=sums[0]+sums[1]+sums[2];
   require(fabs(recon-sol.objective)<2e-9,"objective decomposition failed");
   double driving=8*1.84;
   require(fabs(sums[5]-ETA*sums[4])<2e-9,"roundtrip charging energy mismatch");
   require(fabs(INITIAL/35.*CAP+sums[5]-driving-TARGET/35.*CAP)<2e-9,"physical battery energy balance failed");
   maxFinalSOCerr=max(maxFinalSOCerr,fabs(double(sol.states[NT])/35.-0.8));
   minFinalCost=min(minFinalCost,sol.objective);maxFinalCost=max(maxFinalCost,sol.objective);
   summary<<names[i]<<','<<weights[w]<<','<<version<<",1,"<<sol.objective<<','<<sums[0]<<','<<sums[1]<<','<<sums[2]<<','<<sums[3]<<','<<sums[4]<<','<<sums[5]<<','<<driving<<','<<sums[6]<<','<<double(sol.states[NT])/35.<<",0.8\n";
  }
 }
 audit.close();summary.close();step.close();
 // Full paceval 2D surface, not a Python reimplementation of scientific values.
 {ofstream f(root/"examples/paceval_cost_aging_surface.csv");f<<"power_kW,SOC,tariff_EUR_per_kWh,temperature_C,paceval_total_v1_EUR_proxy,paceval_total_v2_EUR_proxy,paceval_cycle_risk,paceval_calendar_risk,paceval_marginal_cost_EUR_per_kW,paceval_soc_upper_margin\n"<<setprecision(16);
  vector<Input>input;for(int j=0;j<surfaceN;++j)for(int k=0;k<surfaceN;++k){auto x=inputAt(0,1,20,1,8.);x[0]=10.*k/(surfaceN-1);x[1]=.31;x[2]=.20+.65*j/(surfaceN-1);x[3]=28.;x[16]=0;input.push_back(x);}
  const size_t batch=192;for(size_t st=0;st<input.size();st+=batch){size_t n=min(batch,input.size()-st);vector<Input>part(input.begin()+st,input.begin()+st+n);auto out=sdk.batch(part);
    for(size_t k=0;k<n;++k){auto get=[&](int i){return out[size_t(i)*n+k];};f<<part[k][0]<<','<<part[k][2]<<','<<part[k][1]<<','<<part[k][3]<<','<<get(12)<<','<<get(13)<<','<<get(7)<<','<<get(8)<<','<<get(22)<<','<<get(15)<<'\n';}
  }
 }
 // Explicit scalar SDK spot-check also ensures that graph handles are individually reusable.
 int scalarChecks=0;for(size_t i=0;i<sdk.formulas.size();++i){auto x=inputAt(2,3,20,2,30.);double v=paceval_dGetComputationResult(sdk.formulas[i].h,x.data(),nullptr,nullptr);
 require(!paceval_GetIsError(sdk.formulas[i].h)&&isfinite(v),"scalar paceval computation failed");double ref=Engine::nativeReference(x)[i];require(fabs(v-ref)<3e-10*(1+fabs(ref)),"scalar paceval reference mismatch");++scalarChecks;}
 {ofstream f(root/"results/execution_summary.txt");f<<setprecision(16)
 <<"SDK=original_paceval_linux_shared_library\n"<<"PACEVAL_GRAPHS="<<sdk.count()<<"\n"<<"PACEVAL_BATCH_INVOCATIONS="<<sdk.calls<<"\n"<<"PACEVAL_MULTI_GRAPH_BATCH_RESULTS="<<sdk.outputs<<"\n"<<"PACEVAL_SCALAR_SPOT_CHECKS="<<scalarChecks<<"\n"<<"CXX_INDEPENDENT_REFERENCE_VALUES="<<sdk.checks<<"\n"<<"MAX_SCALED_DIFFERENCE="<<sdk.max_scaled_difference<<"\n"<<"FIXED_SYNTHETIC_TARIFF_PROFILES="<<nprofiles<<"\n"<<"SYNTHETIC_AGING_WEIGHTS="<<nweights<<"\n"<<"VERSIONED_COST_FUNCTIONS=2\n"<<"FEASIBLE_OPTIMIZED_SCHEDULES="<<feasibleCount<<"\n"<<"OPTIMIZED_SCHEDULES="<<solutionCount<<"\n"<<"SURFACE_POINTS="<<surfaceN*surfaceN<<"\n"<<"GRID_ENERGY_TO_FINAL_TARGET_KWH=38\n"<<"INITIAL_SOC="<<double(INITIAL)/35.<<"\n"<<"FINAL_SOC_TARGET=0.8\n"<<"TOTAL_DRIVING_ENERGY_KWH="<<8*1.84<<"\n"<<"MAX_FINAL_SOC_ERROR="<<maxFinalSOCerr<<"\n"<<"LOWEST_OBJECTIVE_EUR_PROXY="<<minFinalCost<<"\n"<<"HIGHEST_OBJECTIVE_EUR_PROXY="<<maxFinalCost<<"\n"<<"INVALID_INPUTS_REJECTED=11\n"<<"EMPIRICALLY_CALIBRATED_BATTERY_FADE=false\n"<<"REAL_WORLD_TARIFFS_OR_DRIVING_DATA=false\n";}
 cout<<"PASS original paceval SDK: "<<sdk.count()<<" reusable mathematical graphs, "<<sdk.outputs<<" Multi-Graph-Batch results, "<<feasibleCount<<" verified charging schedules, "<<sdk.checks<<" C++ oracle values, "<<scalarChecks<<" scalar checks\n";
}
int main(int argc,char**argv){try{fs::path out=".";int profiles=6,weightsN=3,surface=61;for(int i=1;i<argc;++i){string x=argv[i];
 if(x=="--out"&&i+1<argc)out=argv[++i];else if(x=="--profiles"&&i+1<argc)profiles=stoi(argv[++i]);else if(x=="--weights"&&i+1<argc)weightsN=stoi(argv[++i]);else if(x=="--surface"&&i+1<argc)surface=stoi(argv[++i]);else throw runtime_error("Usage: battery_charging_aging [--out DIR] [--profiles 1..6] [--weights 1..3] [--surface 5..201]");}
 run(out,profiles,weightsN,surface);return 0;}catch(const exception&e){cerr<<"FAIL "<<e.what()<<'\n';return 1;}}
