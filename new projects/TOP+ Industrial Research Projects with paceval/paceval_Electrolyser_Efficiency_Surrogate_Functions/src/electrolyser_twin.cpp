// WP_049: Reusable electrochemical and operating-cost surrogate kernels
// Actual original paceval 4.25 shared-library graph execution (not a C++ replacement).
// All meaningful stateless domain functions are persistent paceval graphs.
// Host: deterministic electrical load schedule, thermal state orchestration,
// aggregation, CSV, input validation, independent native audit and decisions.
// This is a SYNTHETIC PEM-stack surrogate; no gas crossover or safety qualification.
#include "paceval_main.h"
#include <algorithm>
#include <array>
#include <cmath>
#include <cstdio>
#include <filesystem>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <limits>
#include <stdexcept>
#include <string>
#include <vector>
using namespace std;
namespace fs=std::filesystem;
static void require(bool b,const string&why){if(!b)throw runtime_error(why);}
constexpr int NV=12;
enum V{J,T,P,AGE,TA,DT,W,TARGET,PREVJ,WEIGHT,TBAT,AUXSCALE};
using Row=array<double,NV>;
static constexpr double N_CELL=70., A_CELL=300., F=96485.33212;
static constexpr double M_H2=0.00201588, M_O2=.031998, M_H2O=.01801528;
static constexpr double LHV=120000000., STEP_SEC=60.;
static constexpr const char* VARS="j T p age Ta dt w target prevj weight Tset auxScale";
struct Graph{string id,expression,units,purpose,version;PACEVAL_HANDLE h=nullptr;};
static string coeff(double v){char s[80];snprintf(s,sizeof(s),"%.9g",v);return s;}
static const string E="(1.229-0.00085*(T-25)+0.0043*ln(p))";
static const string ACT="(0.105*ln(1+j/0.17)*exp(-0.004*(T-60)))";
static const string OHM="(0.14*j*age*(1+0.012*(60-T)))";
static const string CONC="(0.032*j/(2.8-j)*(1+0.25*(1-w)))";
static const string ETA_F="(0.985-0.018*exp(-j/0.4)-0.006*(p/22)^2-0.012*(1-w)^2)";
static const string F_DER="(0.018/0.4*exp(-j/0.4))";
static const string I_CURR="(300*j)";
static const string AUX="(auxScale*(0.75+0.0012*(T-Ta)^2+0.45*(j/2)^2+0.007*p))";
static const string DFLOW="(70*300*j*"+ETA_F+"*0.00201588/(2*96485.33212))";
static const string DHFLOW="(70*300*("+ETA_F+"+j*"+F_DER+")*0.00201588/(2*96485.33212))";
static const string D_ACT="(0.105*exp(-0.004*(T-60))/(j+0.17))";
static const string D_OHM="(0.14*age*(1+0.012*(60-T)))";
static const string D_CONC="(0.032*2.8/(2.8-j)^2*(1+0.25*(1-w)))";
static const string DT_ACT="(-0.004*"+ACT+")";
static const string DT_OHM="(-0.14*j*age*0.012)";
static vector<Graph> formulas(){
 vector<Graph>g;
 auto add=[&](string id,string ex,string unit,string purpose,string version="shared"){g.push_back({id,ex,unit,purpose,version,nullptr});};
 add("reversible_voltage",E,"V","empirical_pressure_temperature_reversible_potential");
 add("activation_overpotential",ACT,"V","activation_loss_surrogate");
 add("ohmic_overpotential",OHM,"V","current_density_temperature_age_ohmic_loss");
 add("transport_overpotential",CONC,"V","controlled_transport_correction");
 add("faradaic_factor",ETA_F,"1","synthetic_gas_current_yield_factor");
 add("stack_current",I_CURR,"A","area_times_current_density");
 add("auxiliary_power",AUX,"kW","synthetic_pump_cooling_and_boP_load");
 add("hydrogen_rate",DFLOW,"kg/s","Faraday_law_with_stoichiometric_series_cells");
 add("hydrogen_rate_h", "(3600*"+DFLOW+")","kg/h","hydrogen_production_rate_per_hour");
 add("oxygen_rate","("+DFLOW+"*0.031998/0.00201588/2)","kg/s","ideal_O2_to_H2_stoichiometric_ratio");
 add("water_consumption_rate","("+DFLOW+"*0.01801528/0.00201588)","kg/s","minimum_stoichiometric_consumption");
 add("d_hydrogen_rate_d_j",DHFLOW,"kg/s/(A/cm2)","analytic_hydrogen_production_sensitivity");
 add("d_faradaic_factor_d_j",F_DER,"1/(A/cm2)","analytic_Faradaic_factor_sensitivity");
 add("current_density_lower_margin","(j-0.2)","A/cm2","synthetic_lower_domain_margin");
 add("current_density_upper_margin","(2.5-j)","A/cm2","synthetic_upper_domain_margin");
 add("temperature_lower_margin","(T-30)","degC","synthetic_temperature_lower_margin");
 add("temperature_upper_margin","(85-T)","degC","synthetic_temperature_upper_margin");
 add("pressure_lower_margin","(p-2)","bar","synthetic_pressure_lower_margin");
 add("pressure_upper_margin","(22-p)","bar","synthetic_pressure_upper_margin");
 add("water_lower_margin","(w-0.85)","1","synthetic_water_factor_lower_margin");
 add("j_change_rate_margin","(0.05-(j-prevj)^2/(dt^2))","(A/cm2/s)^2","synthetic_slew_squared_margin_not_regulatory");
 add("d_reversible_voltage_d_T","(-0.00085)","V/degC","analytical_reversible_temperature_derivative");
 add("d_activation_overpotential_d_T",DT_ACT,"V/degC","analytical_activation_temperature_derivative");
 add("d_ohmic_overpotential_d_T",DT_OHM,"V/degC","analytical_ohmic_temperature_derivative");
 for(int version=1;version<=2;version++){
  string s="_v"+to_string(version),vs="v"+to_string(version);
  string voltage="("+E+"+"+ACT+"+"+OHM+(version==2?"+"+CONC:"")+")";
  string dVdj="("+D_ACT+"+"+D_OHM+(version==2?"+"+D_CONC:"")+")";
  string dVdT="(-0.00085+"+DT_ACT+"+"+DT_OHM+")";
  string stackPower="(70*300*j*"+voltage+"/1000)";
  string totalPower="("+stackPower+"+"+AUX+")";
  string h2Power="("+DFLOW+"*120000000/1000)";
  string eta="("+h2Power+"/"+totalPower+")";
  string heat="(70*300*j*("+voltage+"-1.48)/1000)"; // signed thermoneutral stack heat proxy, kW
  string nextT="(T+dt*("+heat+"-0.22*(T-Ta)-0.15*(T-Tset))/1200)";
  string loss="("+totalPower+"-"+h2Power+")"; // not equivalent to physical stack heat!
  string dPdJ="(70*300/1000*("+voltage+"+j*"+dVdj+")+auxScale*0.45*j/2)";
  string dEtaDj="(120000000/1000*("+DHFLOW+"*"+totalPower+"-"+DFLOW+"*"+dPdJ+")/"+totalPower+"^2)";
  add("cell_voltage"+s,voltage,"V","reversible_plus_loss_terms",vs);
  add("stack_voltage"+s,"(70*"+voltage+")","V","series_cell_stack_voltage",vs);
  add("stack_power"+s,stackPower,"kW","real_stack_electrical_power",vs);
  add("total_system_power"+s,totalPower,"kW","stack_and_auxiliary_power",vs);
  add("chemical_lhv_power"+s,h2Power,"kW_LHV","hydrogen_LHV_equivalent_energy_rate",vs);
  add("system_lhv_efficiency"+s,eta,"1","system_LHV_efficiency_from_mass_flow",vs);
  add("specific_electricity"+s,"("+totalPower+"/(3600*"+DFLOW+"))","kWh/kg","system_electric_energy_per_kg_H2",vs);
  add("lhv_power_gap"+s,loss,"kW","electrical_power_minus_LHV_rate_not_heat",vs);
  add("thermoneutral_heat_proxy"+s,heat,"kW","signed_stack_heat_proxy_neglects_detailed_thermal_physics",vs);
  add("next_stack_temperature"+s,nextT,"degC","lumped_explicit_temperature_state_step",vs);
  add("d_voltage_d_j"+s,dVdj,"V/(A/cm2)","fixed_state_analytical_current_density_sensitivity",vs);
  add("d_voltage_d_T"+s,dVdT,"V/degC","fixed_state_analytical_temperature_sensitivity",vs);
  add("d_stack_power_d_j"+s,"(70*300/1000*("+voltage+"+j*"+dVdj+"))","kW/(A/cm2)","fixed_state_stack_power_sensitivity",vs);
  add("d_system_power_d_j"+s,dPdJ,"kW/(A/cm2)","system_power_sensitivity_including_auxiliary",vs);
  add("d_system_efficiency_d_j"+s,dEtaDj,"1/(A/cm2)","fully_composed_LHV_efficiency_sensitivity",vs);
  add("target_efficiency_residual"+s,"("+eta+"-target)","1","efficiency_target_residual",vs);
  add("efficiency_lower_margin"+s,"("+eta+"-0.57)","1","synthetic_non_regulatory_efficiency_margin",vs);
  add("stack_voltage_upper_margin"+s,"(150-70*"+voltage+")","V","synthetic_upper_voltage_margin",vs);
  add("power_upper_margin"+s,"(82-"+totalPower+")","kW","synthetic_operational_power_margin",vs);
  add("production_lower_margin"+s,"(3600*"+DFLOW+"-0.3)","kg/h","hypothetical_hydrogen_rate_margin",vs);
  add("power_identity_residual"+s,"("+totalPower+"-"+stackPower+"-"+AUX+")","kW","direct_algebraic_stack_auxiliary_power_identity",vs);
  add("lhv_specific_identity_residual"+s,"("+eta+"*"+totalPower+"-"+h2Power+")","kW","direct_algebraic_LHV_power_identity",vs);
  for(int k=1;k<=10;k++){
   string cost="("+coeff(.36+.012*k)+"*("+eta+"-target)^2+"+coeff(.012+.003*k)+"*("+totalPower+"/82)^2+"+coeff(.013+.002*k)+"*((T-Tset)/25)^2+"+coeff(.007+.002*k)+"*(j-prevj)^2+"+coeff(.010+.001*k)+"*(w-1)^2+weight*(1-"+eta+")^2)";
   string id="composite_cost"+s+"_"+(k<10?"0":"")+to_string(k);
   add(id,cost,"normalized_index","versioned_synthetic_energy_thermal_slew_water_quality_score",vs);
  }
 }
 // The fixed-state model difference must be computed by paceval, not native C++.
 add("version2_minus_version1_voltage",CONC,"V","controlled_concentration_overpotential_model_revision","v2-v1");
 add("version2_minus_version1_power","(70*300*j*"+CONC+"/1000)","kW","full_stack_power_change_at_fixed_state","v2-v1");
 return g;
}
struct Engine{
 vector<Graph>g;size_t batchCalls=0,batchOutputs=0,scalars=0;
 Engine(){require(paceval_InitializeLibrary(nullptr),"paceval_InitializeLibrary failed");g=formulas();try{for(auto &x:g){x.h=paceval_CreateComputation(x.expression.c_str(),NV,VARS,false,nullptr);if(!x.h||paceval_GetIsError(x.h)){char a[512]={},b[512]={};if(x.h)paceval_CreateErrorInformationText(x.h,a,b);throw runtime_error("paceval graph create failed ["+x.id+"]: "+a+" "+b+" expr="+x.expression);}}}catch(...){for(auto&x:g)if(x.h)paceval_DeleteComputation(x.h);paceval_FreeLibrary();throw;}}
 ~Engine(){for(auto&x:g)if(x.h)paceval_DeleteComputation(x.h);paceval_FreeLibrary();}
 int idx(const string&s)const{for(size_t j=0;j<g.size();j++)if(g[j].id==s)return int(j);throw runtime_error("unknown graph "+s);}
 void valid(const Row&r)const{for(double x:r)require(isfinite(x),"nonfinite input");require(r[J]>=.2&&r[J]<=2.5&&r[T]>=30&&r[T]<=85&&r[P]>=2&&r[P]<=22&&r[AGE]>=1&&r[AGE]<=1.3&&r[TA]>=-10&&r[TA]<=45&&r[DT]>0&&r[DT]<=120&&r[W]>=.85&&r[W]<=1.10&&r[TARGET]>.45&&r[TARGET]<.95&&r[PREVJ]>=.2&&r[PREVJ]<=2.5&&r[WEIGHT]>=0&&r[WEIGHT]<=1&&r[TBAT]>=30&&r[TBAT]<=85&&r[AUXSCALE]>=.8&&r[AUXSCALE]<=1.4,"outside declared synthetic model domain");}
 vector<double> batch(const vector<Row>&rows,const vector<int>&ids){require(!rows.empty()&&!ids.empty(),"empty batch");vector<double>in;in.reserve(rows.size()*NV);for(auto&r:rows){valid(r);in.insert(in.end(),r.begin(),r.end());}vector<PACEVAL_HANDLE>hs;for(int i:ids)hs.push_back(g.at(i).h);vector<double>out(rows.size()*ids.size(),NAN);vector<int>err(out.size(),-1);
  bool fail=paceval_dGetMultipleComputationsResultsExt(hs.data(),hs.size(),in.data(),rows.size(),out.data(),nullptr,nullptr,err.data());require(!fail,"original paceval multi-graph batch failure");for(size_t k=0;k<out.size();k++)require(err[k]==0&&isfinite(out[k]),"paceval result error index="+to_string(k)+" err="+to_string(err[k]));batchCalls++;batchOutputs+=out.size();return out;}
 double scalar(int gi,Row r){valid(r);double v=paceval_dGetComputationResult(g.at(gi).h,r.data(),nullptr,nullptr);require(!paceval_GetIsError(g[gi].h)&&isfinite(v),"scalar paceval error");scalars++;return v;}
};
struct Scenario{
 int id,profile,version;double pressure,T=55,Ta=25,age=1.,prevj=.85;
 double totalKg=0,energyKWh=0,chemKWh=0,waterKg=0,oxygenKg=0,score=0,minEta=1,maxT=-1,maxPower=0,minCell=10,maxCell=0,maxAlgebraError=0;size_t lowEfficiencySteps=0;
};
static vector<Scenario> cases(){vector<Scenario>v;int id=0;for(int profile=0;profile<3;profile++)for(double pressure:{3.,10.,20.})for(int version:{1,2}){Scenario a;a.id=++id;a.profile=profile;a.version=version;a.pressure=pressure;a.Ta=25.;a.age=profile==2?1.10:1.0;v.push_back(a);}return v;}
// Deterministic synthetic available-renewable-electricity load commands.
static double schedule(int type,int k){int x=k%60;if(type==0){if(x<20)return 1.25;if(x<36)return 1.80;if(x<46)return .60;return 1.05;}if(type==1){if(x<10)return .45;if(x<22)return .95;if(x<37)return 1.55;if(x<49)return 2.25;return .73;}if(x<12)return .35;if(x<26)return 1.95;if(x<38)return 2.35;if(x<50)return .50;return 1.35;}
static Row makeRow(const Scenario&s,int k){return {schedule(s.profile,k),s.T,s.pressure,s.age,s.Ta,STEP_SEC,0.98,0.71,s.prevj,0.025,65.0,1.0};}
static double nativeV(const Row&r,int ver){double j=r[J],t=r[T],p=r[P],age=r[AGE],w=r[W];double er=1.229-.00085*(t-25)+.0043*log(p),a=.105*log(1+j/.17)*exp(-.004*(t-60)),o=.14*j*age*(1+.012*(60-t)),c=.032*j/(2.8-j)*(1+.25*(1-w));return er+a+o+(ver==2?c:0);}
static double nativeF(const Row&r){double j=r[J],p=r[P],w=r[W];return .985-.018*exp(-j/.4)-.006*pow(p/22,2)-.012*pow(1-w,2);}
struct Native{double nextTemp,voltage,sysPower,hydrogenRate,efficiency,heatProxy,aux,stackPower;};
static Native native(const Row&r,int v){double j=r[J],volt=nativeV(r,v),aux=r[AUXSCALE]*(.75+.0012*pow(r[T]-r[TA],2)+.45*pow(j/2,2)+.007*r[P]);double ps=70*300*j*volt/1000,pt=ps+aux,rate=70*300*j*nativeF(r)*M_H2/(2*F);double heat=70*300*j*(volt-1.48)/1000;double nt=r[T]+r[DT]*(heat-.22*(r[T]-r[TA])-.15*(r[T]-r[TBAT]))/1200;return {nt,volt,pt,rate,rate*LHV/(pt*1000),heat,aux,ps};}
static void audit(double got,double expected,const string&name,size_t&checks,double&worst){double e=abs(got-expected)/(1+abs(expected));worst=max(worst,e);checks++;require(e<3e-10,"independent native audit failure: "+name+" relative scaled="+to_string(e));}
static void run(const fs::path&root,int steps){require(steps>=24&&steps<=1000,"steps outside 24..1000");fs::create_directories(root/"results");fs::create_directories(root/"examples");Engine eng;vector<Scenario>sc=cases();
 {ofstream f(root/"results/formula_registry.csv");f<<"graph_id,version,purpose,units,paceval_formula\n";for(auto&x:eng.g)f<<x.id<<","<<x.version<<","<<x.purpose<<","<<x.units<<",\""<<x.expression<<"\"\n";}
 {ofstream f(root/"results/math_execution_inventory.csv");f<<"function_id,domain_quantity,mathematical_definition,units,execution_owner,paceval_graph_id,formula_version,api_path,reference_test,status,host_reason\n";for(auto&x:eng.g)f<<x.id<<","<<x.purpose<<",\""<<x.expression<<"\","<<x.units<<",paceval,"<<x.id<<","<<x.version<<",GetMultipleComputationsResultsExt;GetComputationResult,independent_native_plus_80_digit,executed,\n";
 f<<"load_schedule,renewable_power_load_command,deterministic_piecewise_j,A/cm2,host,,shared,orchestration,python_reference,executed,time_program\n";
 f<<"thermal_state_loop,thermal_state_management,advance_using_paceval_next_temperature,degC,host,,v1-v2,state_orchestration,python_reference,executed,state_carry_only\n";
 f<<"integral_aggregation,energy_and_hydrogen_mass_totals,left_riemann_sums,kWh;kg,host,,v1-v2,accumulation,python_reference,executed,history_dependent_reporting\n";
 f<<"operating_selection,accept_review_flag,threshold_comparison,1,host,,shared,application_decision,probe_audit,executed,not_a_physical_safety_certification\n";}
 ofstream tr(root/"examples/trace_samples.csv");tr<<setprecision(17)<<"scenario_id,profile,version,pressure_bar,step,time_s,current_density_A_cm2,temperature_C,cell_voltage_V,system_power_kW,hydrogen_kg_s,hydrogen_kg_h,efficiency_LHV,auxiliary_power_kW,stack_power_kW,thermoneutral_heat_proxy_kW,cumulative_H2_kg\n";
 ofstream pr(root/"results/executed_graph_probes.csv");pr<<setprecision(17)<<"graph_id,version,scenario_id,step,j,T,p,age,Ta,dt,w,target,prevj,weight,Tset,auxScale,paceval_value\n";
 vector<string>need={"cell_voltage","system_lhv_efficiency","chemical_lhv_power","total_system_power","stack_power","thermoneutral_heat_proxy","next_stack_temperature","power_identity_residual","lhv_specific_identity_residual","composite_cost","lhv_power_gap","d_system_efficiency_d_j"};
 vector<int>selected;
 for(string suf:{"_v1","_v2"}){for(auto&s:need){string id=s=="composite_cost"?s+suf+"_01":s+suf;selected.push_back(eng.idx(id));}}
 for(string id:{"hydrogen_rate","hydrogen_rate_h","water_consumption_rate","oxygen_rate","auxiliary_power","faradaic_factor","current_density_upper_margin","temperature_upper_margin"})selected.push_back(eng.idx(id));
 auto get=[&](const vector<double>&out,const string&id,size_t ci){auto it=find(selected.begin(),selected.end(),eng.idx(id));require(it!=selected.end(),"missing graph "+id);return out[distance(selected.begin(),it)*sc.size()+ci];};
 vector<int>all;for(size_t g=0;g<eng.g.size();g++)all.push_back(int(g));
 double worst=0;size_t nativeChecks=0,probeRows=0;
 for(int step=0;step<steps;step++){
  vector<Row>rows;for(auto&s:sc)rows.push_back(makeRow(s,step));auto out=eng.batch(rows,selected);
  if(step==0||step==steps/2||step==steps-1){auto full=eng.batch(rows,all);for(size_t gi=0;gi<eng.g.size();gi++)for(size_t ci=0;ci<rows.size();ci++){pr<<eng.g[gi].id<<","<<eng.g[gi].version<<","<<sc[ci].id<<","<<step;for(double x:rows[ci])pr<<","<<x;pr<<","<<full[gi*rows.size()+ci]<<"\n";probeRows++;}}
  for(size_t ci=0;ci<sc.size();ci++){
   Scenario&s=sc[ci];const Row&r=rows[ci];string v=s.version==1?"_v1":"_v2";
   double volt=get(out,"cell_voltage"+v,ci),pSys=get(out,"total_system_power"+v,ci),pStack=get(out,"stack_power"+v,ci),eta=get(out,"system_lhv_efficiency"+v,ci),hRate=get(out,"hydrogen_rate",ci),nT=get(out,"next_stack_temperature"+v,ci),hP=get(out,"thermoneutral_heat_proxy"+v,ci),aux=get(out,"auxiliary_power",ci);
   double pIdentity=get(out,"power_identity_residual"+v,ci),lhvIdentity=get(out,"lhv_specific_identity_residual"+v,ci);
   require(eta>0&&eta<1&&hRate>0&&pSys>0&&nT>=30&&nT<=85,"output violated research assumptions");
   s.totalKg+=hRate*STEP_SEC;s.waterKg+=get(out,"water_consumption_rate",ci)*STEP_SEC;s.oxygenKg+=get(out,"oxygen_rate",ci)*STEP_SEC;
   s.energyKWh+=pSys*STEP_SEC/3600;s.chemKWh+=get(out,"chemical_lhv_power"+v,ci)*STEP_SEC/3600;
   s.score+=get(out,"composite_cost"+v+"_01",ci)*STEP_SEC;
   s.minEta=min(s.minEta,eta);s.maxT=max(s.maxT,nT);s.maxPower=max(s.maxPower,pSys);s.minCell=min(s.minCell,volt);s.maxCell=max(s.maxCell,volt);s.maxAlgebraError=max({s.maxAlgebraError,abs(pIdentity),abs(lhvIdentity)});if(eta<.57)s.lowEfficiencySteps++;
   if(step%4==0||step==steps-1)tr<<s.id<<","<<s.profile<<","<<s.version<<","<<s.pressure<<","<<step<<","<<step*STEP_SEC<<","<<r[J]<<","<<r[T]<<","<<volt<<","<<pSys<<","<<hRate<<","<<hRate*3600<<","<<eta<<","<<aux<<","<<pStack<<","<<hP<<","<<s.totalKg<<"\n";
   if(step<8||step%31==0||step==steps-1){Native ref=native(r,s.version);audit(volt,ref.voltage,"voltage",nativeChecks,worst);audit(pSys,ref.sysPower,"total_power",nativeChecks,worst);audit(eta,ref.efficiency,"efficiency",nativeChecks,worst);audit(hRate,ref.hydrogenRate,"hydrogen",nativeChecks,worst);audit(nT,ref.nextTemp,"temperature",nativeChecks,worst);audit(hP,ref.heatProxy,"heat_proxy",nativeChecks,worst);audit(aux,ref.aux,"aux",nativeChecks,worst);audit(pStack,ref.stackPower,"stack_power",nativeChecks,worst);}
   s.T=nT;s.prevj=r[J];
  }
 }
 tr.close();pr.close();
 ofstream summary(root/"results/scenario_summary.csv");summary<<setprecision(17)<<"scenario_id,profile,version,pressure_bar,steps,dt_s,final_temperature_C,max_temperature_C,total_H2_kg,total_O2_kg,minimum_water_kg,system_electricity_kWh,hydrogen_LHV_energy_kWh,integrated_system_efficiency_LHV,specific_electricity_kWh_kg,min_instant_efficiency_LHV,min_cell_voltage_V,max_cell_voltage_V,max_system_power_kW,integral_composite_score,algebraic_identity_max_kW,low_efficiency_count\n";
 for(auto&s:sc)summary<<s.id<<","<<s.profile<<","<<s.version<<","<<s.pressure<<","<<steps<<","<<STEP_SEC<<","<<s.T<<","<<s.maxT<<","<<s.totalKg<<","<<s.oxygenKg<<","<<s.waterKg<<","<<s.energyKWh<<","<<s.chemKWh<<","<<s.chemKWh/s.energyKWh<<","<<s.energyKWh/s.totalKg<<","<<s.minEta<<","<<s.minCell<<","<<s.maxCell<<","<<s.maxPower<<","<<s.score<<","<<s.maxAlgebraError<<","<<s.lowEfficiencySteps<<"\n";
 summary.close();
 // Entire plotting surface computed by actual paceval multigraph batch.
 vector<Row>surface;for(int ti=0;ti<=24;ti++)for(int ji=0;ji<=26;ji++)surface.push_back({.25+ji*2.15/26.,35.+ti*2.,10.,1.,25.,STEP_SEC,.98,.71,1.0,.025,65.,1.});
 vector<string>surfNames={"cell_voltage_v1","cell_voltage_v2","system_lhv_efficiency_v1","system_lhv_efficiency_v2","total_system_power_v2","hydrogen_rate_h","thermoneutral_heat_proxy_v2","d_system_efficiency_d_j_v2","d_voltage_d_T_v2","composite_cost_v2_01","power_upper_margin_v2","faradaic_factor","lhv_power_gap_v2","version2_minus_version1_voltage"};vector<int>surfIds;for(auto&id:surfNames)surfIds.push_back(eng.idx(id));auto outputs=eng.batch(surface,surfIds);
 ofstream sf(root/"results/parameter_surface.csv");sf<<setprecision(17)<<"current_density_A_cm2,temperature_C,cell_voltage_v1_V,cell_voltage_v2_V,efficiency_v1_LHV,efficiency_v2_LHV,power_v2_kW,hydrogen_rate_kg_h,thermoneutral_heat_proxy_v2_kW,d_efficiency_d_j_v2,d_voltage_d_T_v2,composite_cost_v2_01,power_upper_margin_v2_kW,faradaic_factor,lhv_power_gap_v2_kW,version2_minus_version1_voltage_V\n";
 for(size_t i=0;i<surface.size();i++){sf<<surface[i][J]<<","<<surface[i][T];for(size_t k=0;k<surfIds.size();k++)sf<<","<<outputs[k*surface.size()+i];sf<<"\n";}sf.close();
 // Independent layout/scale check uses scalar original API on a known input.
 Row initial=makeRow(sc.front(),0);audit(eng.scalar(eng.idx("cell_voltage_v2"),initial),nativeV(initial,2),"scalar_cell_voltage",nativeChecks,worst);
 ofstream log(root/"results/sdk_execution.txt");log<<setprecision(17)<<"ORIGINAL paceval SDK execution: SUCCESS\n"<<"registered_and_executed_graphs="<<eng.g.size()<<"\n"<<"multi_graph_batch_calls="<<eng.batchCalls<<"\n"<<"graph_batch_outputs="<<eng.batchOutputs<<"\n"<<"scalar_calls="<<eng.scalars<<"\n"<<"independent_native_checks="<<nativeChecks<<"\n"<<"max_scaled_native_difference="<<worst<<"\n"<<"graph_inventory_probe_rows="<<probeRows<<"\n"<<"scenarios="<<sc.size()<<"\n"<<"simulation_steps="<<steps<<"\n"<<"model_versions=baseline-polarization,transport-corrected\n"<<"synthetic_data_only=true\n"<<"TINC_not_executed=true\n"<<"external_library_not_redistributed=true\n";log.close();
 cout<<"WP049 ORIGINAL PACEVAL PASS graphs="<<eng.g.size()<<" batch_outputs="<<eng.batchOutputs<<" batches="<<eng.batchCalls<<" native="<<nativeChecks<<" scenarios="<<sc.size()<<"\n";
}
int main(int argc,char**argv){try{fs::path root=".";int steps=240;for(int i=1;i<argc;i++){string arg=argv[i];auto need=[&](){require(i+1<argc,"missing parameter value");return string(argv[++i]);};if(arg=="--out")root=need();else if(arg=="--steps")steps=stoi(need());else throw runtime_error("unknown argument: "+arg);}run(root,steps);return 0;}catch(const exception&e){cerr<<"WP049 FAILED: "<<e.what()<<"\n";return 2;}}
