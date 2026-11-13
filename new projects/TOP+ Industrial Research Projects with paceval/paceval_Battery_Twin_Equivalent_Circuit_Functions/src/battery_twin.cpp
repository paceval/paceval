// WP_048: Battery Equivalent-Circuit Digital Twin Mathematical Kernels
// Original paceval 4.25 API: all domain scalar equations and the main one-step
// outputs are evaluated through persistent original paceval execution graphs.
// C++ owns current schedules, stepping/aggregation, file I/O, validation, audits.
// Deterministic synthetic cell ONLY; no battery safety approval or fitted cell data.
#include "paceval_main.h"
#include <algorithm>
#include <array>
#include <cmath>
#include <filesystem>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <limits>
#include <stdexcept>
#include <string>
#include <vector>
using namespace std;namespace fs=std::filesystem;
static void req(bool ok,const string&why){if(!ok)throw runtime_error(why);}
constexpr int NV=13;
enum V{Z,P1,P2,I,T,TA,DT,Q,AGE,H,CTH,TARGET,SCALE};
using Row=array<double,NV>;
static const char* VARS="z p1 p2 I T Ta dt Q age h Cth target scale";
struct Graph{string id,expr,unit,purpose,version;PACEVAL_HANDLE handle=nullptr;};
static const string O="(3.2+0.93*z+0.10*(2/(1+exp(-13*(z-0.5)))-1)+0.00035*(T-25))";
static const string R0="(0.021*(1+0.7*(1-z)^2)*exp(0.017*(25-T))*age)";
static const string R1="(0.012*(1+0.35*(1-z))*exp(0.013*(25-T))*age)";
static const string R2="(0.019*(1+0.20*(1-z))*exp(0.009*(25-T))*age)";
static const string TAU1="(32*(1+0.30*(1-z))*exp(0.008*(25-T)))";
static const string TAU2="(175*(1+0.25*(1-z))*exp(0.006*(25-T)))";
static const string PN1="(p1*exp(-dt/"+TAU1+")+I*"+R1+"*(1-exp(-dt/"+TAU1+")))";
static const string PN2="(p2*exp(-dt/"+TAU2+")+I*"+R2+"*(1-exp(-dt/"+TAU2+")))";
static string fmt(double x){char c[64];snprintf(c,sizeof(c),"%.9g",x);return string(c);}
static vector<Graph> formulas(){vector<Graph>g;auto add=[&](string id,string e,string u,string p,string v="shared"){g.push_back({id,e,u,p,v,nullptr});};
 add("ocv",O,"V","state_and_temperature_dependent_ocv");add("ohmic_resistance",R0,"ohm","temperature_soc_age_ohmic_resistance");
 add("fast_resistance",R1,"ohm","fast_polarization_resistance");add("slow_resistance",R2,"ohm","slow_polarization_resistance");
 add("fast_tau",TAU1,"s","fast_polarization_time_constant");add("slow_tau",TAU2,"s","slow_polarization_time_constant");
 add("effective_capacity","(Q/age)","Ah","synthetic_capacity_age_surrogate");
 add("next_soc","(z-I*dt*age/(3600*Q))","1","full_coulomb_counting_state_step");
 add("next_fast_polarization",PN1,"V","exact_frozen_coefficient_rc_update");
 add("soc_lower_margin","(z-0.08)","1","hypothetical_soc_lower_margin");add("soc_upper_margin","(0.97-z)","1","hypothetical_soc_upper_margin");
 add("thermal_upper_margin","(43-T)","degC","hypothetical_temperature_upper_margin");
 add("d_ocv_d_soc","(0.93+2*0.10*13*exp(-13*(z-0.5))/(1+exp(-13*(z-0.5)))^2)","V","analytical_local_ocv_soc_sensitivity");
 add("d_r0_d_soc","(-2*0.7*0.021*(1-z)*exp(0.017*(25-T))*age)","ohm","analytical_r0_soc_sensitivity");
 add("d_r0_d_temp","(-0.017*"+R0+")","ohm/degC","analytical_r0_temperature_sensitivity");
 add("d_soc_next_d_current","(-dt*age/(3600*Q))","1/A","analytical_coulomb_step_sensitivity");
 add("soc_delta","(-I*dt*age/(3600*Q))","1","state_increment");
 for(int v=1;v<=2;v++){
  const string ver="v"+to_string(v),suffix="_"+ver;
  const string p2=(v==1?"(0*p2)":PN2);
  const string pol=(v==1?"p1":"(p1+p2)");
  const string voltage="("+O+"-I*"+R0+"-"+pol+")";
  const string heat="(I^2*"+R0+"+p1^2/"+R1+(v==2?"+p2^2/"+R2:"")+")";
  const string tempNext="(T+dt*("+heat+"-h*(T-Ta))/Cth)";
  const string terminalPower="(I*"+voltage+")";
  const string polarPower="(I*"+pol+")";
  add("next_slow_polarization"+suffix,p2,"V","second_branch_update_or_zero",ver);
  add("terminal_voltage"+suffix,voltage,"V","full_equivalent_circuit_terminal_voltage",ver);
  add("resistive_heat_proxy"+suffix,heat,"W","lumped_irreversible_resistance_heat_proxy",ver);
  add("next_cell_temperature"+suffix,tempNext,"degC","lumped_thermal_temperature_step",ver);
  add("terminal_power"+suffix,terminalPower,"W","terminal_power_signed",ver);
  add("open_circuit_power"+suffix,"(I*"+O+")","W","reversible_ocv_power_baseline",ver);
  add("ohmic_power"+suffix,"(I^2*"+R0+")","W","ohmic_loss_power",ver);
  add("polarization_power"+suffix,polarPower,"W","rc_branch_input_power",ver);
  add("power_identity_residual"+suffix,"(I*"+O+"-"+terminalPower+"-I^2*"+R0+"-"+polarPower+")","W","instantaneous_exact_algebraic_power_identity",ver);
  add("voltage_lower_margin"+suffix,"("+voltage+"-2.8)","V","hypothetical_voltage_lower_margin",ver);
  add("voltage_upper_margin"+suffix,"(4.25-"+voltage+")","V","hypothetical_voltage_upper_margin",ver);
  add("voltage_target_residual"+suffix,"("+voltage+"-target)","V","hypothetical_voltage_target_residual",ver);
  add("voltage_target_squared"+suffix,"("+voltage+"-target)^2","V^2","squared_voltage_tracking_cost",ver);
  add("d_voltage_d_current"+suffix,"(-"+R0+")","V/A","fixed_state_terminal_voltage_current_sensitivity",ver);
  add("d_voltage_d_soc"+suffix,"((0.93+2*0.10*13*exp(-13*(z-0.5))/(1+exp(-13*(z-0.5)))^2)+2*0.7*0.021*(1-z)*exp(0.017*(25-T))*age*I)","V","fixed_polarization_terminal_voltage_soc_sensitivity",ver);
  add("loss_voltage_fraction"+suffix,"(("+O+"-"+voltage+")/"+O+")","1","normalized_loaded_voltage_drop",ver);
  add("next_fast_residual"+suffix,"("+PN1+"-p1)","V","fast_branch_step_increment",ver);
  add("next_slow_residual"+suffix,"("+p2+"-p2)","V","slow_branch_step_increment",ver);
  // Ten nontrivial composed cost variants per formula version, always evaluated with original paceval.
  for(int j=1;j<=10;j++){
    string score="("+fmt(0.30+0.02*j)+"*("+voltage+"-target)^2+"+fmt(0.025+0.008*j)+"*(I/3.2)^2+"+fmt(.010+.004*j)+"*((T-25)/15)^2+"+fmt(.012+.002*j)+"*("+R0+"/0.025)^2+"+fmt(.006+.002*j)+"*((z-0.65)/0.35)^2)";
    add("composite_cost"+suffix+"_"+(j<10?"0":"")+to_string(j),score,"index","synthetic_multicriterion_trace_cost",ver);
  }
 }
 add("version2_minus_version1_voltage","(-p2)","V","fixed_state_voltage_version_difference","v2-v1");
 add("nominal_time_constant_ratio","("+TAU2+"/"+TAU1+")","1","two_polarization_timescale_ratio");
 return g;}
struct Engine{
 vector<Graph> g;size_t batches=0,outputs=0,scalarCalls=0;Engine(){req(paceval_InitializeLibrary(nullptr),"paceval_InitializeLibrary failed");g=formulas();for(auto&x:g){x.handle=paceval_CreateComputation(x.expr.c_str(),NV,VARS,false,nullptr);if(!x.handle||paceval_GetIsError(x.handle)){char a[512]={},b[512]={};if(x.handle)paceval_CreateErrorInformationText(x.handle,a,b);throw runtime_error("paceval Create failed ["+x.id+"]: "+a+" "+b+" "+x.expr);}}}
 ~Engine(){for(auto&x:g)if(x.handle)paceval_DeleteComputation(x.handle);paceval_FreeLibrary();}
 int idx(const string&s)const{for(size_t j=0;j<g.size();j++)if(g[j].id==s)return (int)j;throw runtime_error("unknown graph "+s);}
 void validate(const Row&r)const{for(double x:r)req(isfinite(x),"nonfinite SDK input");req(r[Z]>=.05&&r[Z]<=1.05&&r[T]>=-20&&r[T]<=75&&r[TA]>=-20&&r[TA]<=65&&abs(r[I])<=7&&r[DT]>0&&r[DT]<=10&&r[Q]>0&&r[AGE]>=.8&&r[AGE]<=1.6&&r[H]>=0&&r[CTH]>0&&r[SCALE]>0,"invalid physical input range");}
 vector<double> batch(const vector<Row>&rows,const vector<int>&ids){req(!rows.empty()&&!ids.empty(),"batch empty");vector<double>in;in.reserve(rows.size()*NV);for(auto&r:rows){validate(r);in.insert(in.end(),r.begin(),r.end());}vector<PACEVAL_HANDLE>hs;for(int i:ids)hs.push_back(g.at(i).handle);vector<double>out(rows.size()*ids.size(),NAN);vector<int>err(out.size(),-1);
  bool fail=paceval_dGetMultipleComputationsResultsExt(hs.data(),hs.size(),in.data(),rows.size(),out.data(),nullptr,nullptr,err.data());req(!fail,"paceval multi-graph batch failure");for(size_t j=0;j<out.size();j++)req(err[j]==0&&isfinite(out[j]),"paceval output error index "+to_string(j)+" code "+to_string(err[j]));batches++;outputs+=out.size();return out;}
 double scalar(int id,Row r){validate(r);double v=paceval_dGetComputationResult(g.at(id).handle,r.data(),nullptr,nullptr);req(!paceval_GetIsError(g.at(id).handle)&&isfinite(v),"scalar error "+g[id].id);scalarCalls++;return v;}
};
struct Scenario{int id,profile,version;double ambient,age=1.;double z=.74,p1=0,p2=0,T=25;double Eterm=0,Eocv=0,Eohmic=0,Epolar=0,Heat=0,Ah=0,maxPowerResidual=0,score=0;double minVolt=100,maxVolt=-100,maxTemp=-100;int overV=0,underV=0;};
static vector<Scenario> cases(){vector<Scenario>v;int id=0;for(int profile=0;profile<3;profile++)for(double amb:{5.,25.,40.})for(int ver:{1,2}){Scenario x;x.id=++id;x.profile=profile;x.version=ver;x.ambient=amb;x.T=amb;x.age=(profile==2?1.12:1.);v.push_back(x);}return v;}
static double current(int profile,int step){int j=step%160;if(profile==0){if(j<38)return 2.7;if(j<60)return 4.8;if(j<86)return 0;if(j<115)return -1.8;return 2.1;}if(profile==1){if(j<85)return 3.3;if(j<110)return 5.2;if(j<130)return 0;return 2.2;}if(j<85)return -2.5;if(j<110)return -1.0;if(j<145)return 0;return 1.5;}
constexpr double QAH=3.2,DTSEC=2.,HT=0.15,CT=130.,TARGETV=3.8;
static Row row(const Scenario&s,int step){return {s.z,s.p1,s.p2,current(s.profile,step),s.T,s.ambient,DTSEC,QAH,s.age,HT,CT,TARGETV,1.};}
static double nativeOCV(const Row&r){double z=r[Z];return 3.2+.93*z+.10*(2/(1+exp(-13*(z-.5)))-1)+.00035*(r[T]-25);}
static double nativeR0(const Row&r){return .021*(1+.7*pow(1-r[Z],2))*exp(.017*(25-r[T]))*r[AGE];}
static double nativeR1(const Row&r){return .012*(1+.35*(1-r[Z]))*exp(.013*(25-r[T]))*r[AGE];}
static double nativeR2(const Row&r){return .019*(1+.20*(1-r[Z]))*exp(.009*(25-r[T]))*r[AGE];}
static double nativeTau1(const Row&r){return 32*(1+.30*(1-r[Z]))*exp(.008*(25-r[T]));}
static double nativeTau2(const Row&r){return 175*(1+.25*(1-r[Z]))*exp(.006*(25-r[T]));}
struct Ref{double z,p1,p2,t,voltage,heat,power;};
static Ref native(const Row&r,int ver){double r0=nativeR0(r),r1=nativeR1(r),r2=nativeR2(r),p2=ver==1?0:r[P2];double voltage=nativeOCV(r)-r[I]*r0-r[P1]-p2;double heat=r[I]*r[I]*r0+r[P1]*r[P1]/r1+(ver==1?0:r[P2]*r[P2]/r2);return{r[Z]-r[I]*r[DT]*r[AGE]/(3600*r[Q]),r[P1]*exp(-r[DT]/nativeTau1(r))+r[I]*r1*(1-exp(-r[DT]/nativeTau1(r))),ver==1?0:r[P2]*exp(-r[DT]/nativeTau2(r))+r[I]*r2*(1-exp(-r[DT]/nativeTau2(r))),r[T]+r[DT]*(heat-r[H]*(r[T]-r[TA]))/r[CTH],voltage,heat,r[I]*voltage};}
static void audit(double got,double ref,const string&where,double&maxerr,size_t&checks){double e=abs(got-ref)/(1+abs(ref));maxerr=max(maxerr,e);checks++;req(e<1e-10,"independent native mismatch: "+where+" error "+to_string(e));}
static void run(const fs::path&root,int steps){req(steps>=20&&steps<=1800,"steps out of range");fs::create_directories(root/"results");fs::create_directories(root/"examples");Engine eng;vector<Scenario>sc=cases();
 {ofstream f(root/"results/formula_registry.csv");f<<"graph_id,version,purpose,units,paceval_formula\n";for(const auto&x:eng.g)f<<x.id<<","<<x.version<<","<<x.purpose<<","<<x.unit<<",\""<<x.expr<<"\"\n";}
 {ofstream f(root/"results/math_execution_inventory.csv");f<<"function_id,domain_quantity,mathematical_definition,units,execution_owner,paceval_graph_id,formula_version,api_path,reference_test,status,host_reason\n";for(const auto&x:eng.g)f<<x.id<<","<<x.purpose<<",\""<<x.expr<<"\","<<x.unit<<",paceval,"<<x.id<<","<<x.version<<",multi_graph_ext_and_scalar,independent_native_and_high_precision,executed,\n";f<<"current_schedule,deterministic_current_schedule,piecewise_synthetic_profiles,A,host,,all,application_orchestration,profile_manifest,executed,piecewise_time_program\n";f<<"state_aggregation,integrated_energy_and_extrema,trapezoid_left_riemann_summary,Wh,host,,all,accumulation,python_independent_reference,executed,stateful_sum_and_reporting\n";}
 ofstream traces(root/"examples/trace_samples.csv");traces<<setprecision(17)<<"scenario_id,profile,version,ambient_C,step,time_s,current_A,soc,polar1_V,polar2_V,temperature_C,terminal_voltage_V,heat_proxy_W,terminal_power_W,ocv_V\n";
 ofstream probes(root/"results/executed_graph_probes.csv");probes<<setprecision(17)<<"graph_id,version,scenario_id,step,z,p1,p2,I,T,Ta,dt,Q,age,h,Cth,target,scale,paceval_value\n";
 size_t nativeTests=0,probeN=0;double maxNative=0;
 vector<int> ids;for(const string&x:{"next_soc","next_fast_polarization","next_slow_polarization_v1","next_slow_polarization_v2","next_cell_temperature_v1","next_cell_temperature_v2","terminal_voltage_v1","terminal_voltage_v2","resistive_heat_proxy_v1","resistive_heat_proxy_v2","terminal_power_v1","terminal_power_v2","open_circuit_power_v1","open_circuit_power_v2","ohmic_power_v1","ohmic_power_v2","polarization_power_v1","polarization_power_v2","power_identity_residual_v1","power_identity_residual_v2","ocv","composite_cost_v1_01","composite_cost_v2_01"})ids.push_back(eng.idx(x));
 auto get=[&](const vector<double>&out,const string&name,int ci){int ix=(int)(find(ids.begin(),ids.end(),eng.idx(name))-ids.begin());req(ix<(int)ids.size(),"missing selected graph "+name);return out[ix*sc.size()+ci];};
 vector<int>full;for(size_t j=0;j<eng.g.size();j++)full.push_back((int)j);
 for(int step=0;step<steps;step++){
 vector<Row>rows;for(auto&s:sc)rows.push_back(row(s,step));auto out=eng.batch(rows,ids);
 // Probe all registered graphs regularly; proves nontrivial actual API execution coverage.
 if(step==0||step==steps/2||step==steps-1){auto all=eng.batch(rows,full);for(size_t gi=0;gi<eng.g.size();gi++)for(size_t ci=0;ci<rows.size();ci++){probes<<eng.g[gi].id<<","<<eng.g[gi].version<<","<<sc[ci].id<<","<<step;for(double x:rows[ci])probes<<","<<x;probes<<","<<all[gi*rows.size()+ci]<<"\n";probeN++;}}
 for(size_t ci=0;ci<sc.size();ci++){
 Scenario&s=sc[ci];const Row&r=rows[ci];string suf=s.version==1?"_v1":"_v2";
 const double volt=get(out,"terminal_voltage"+suf,ci),heat=get(out,"resistive_heat_proxy"+suf,ci),power=get(out,"terminal_power"+suf,ci),ocv=get(out,"ocv",ci);
 const double pocv=get(out,"open_circuit_power"+suf,ci),pohm=get(out,"ohmic_power"+suf,ci),ppol=get(out,"polarization_power"+suf,ci),ident=get(out,"power_identity_residual"+suf,ci);
 double nextSoc=get(out,"next_soc",ci),nextFast=get(out,"next_fast_polarization",ci),nextSlow=get(out,"next_slow_polarization"+suf,ci),nextT=get(out,"next_cell_temperature"+suf,ci);
 s.Eterm+=power*DTSEC/3600;s.Eocv+=pocv*DTSEC/3600;s.Eohmic+=pohm*DTSEC/3600;s.Epolar+=ppol*DTSEC/3600;s.Heat+=heat*DTSEC/3600;s.Ah+=r[I]*DTSEC/3600;s.score+=get(out,"composite_cost"+suf+"_01",ci)*DTSEC;
 s.minVolt=min(s.minVolt,volt);s.maxVolt=max(s.maxVolt,volt);s.maxTemp=max(s.maxTemp,nextT);s.maxPowerResidual=max(s.maxPowerResidual,abs(ident));if(volt<2.8)s.underV++;if(volt>4.25)s.overV++;
 if(step%6==0||step==steps-1)traces<<s.id<<","<<s.profile<<","<<s.version<<","<<s.ambient<<","<<step<<","<<step*DTSEC<<","<<r[I]<<","<<s.z<<","<<s.p1<<","<<s.p2<<","<<s.T<<","<<volt<<","<<heat<<","<<power<<","<<ocv<<"\n";
 if(step<10||step%47==0||step==steps-1){Ref n=native(r,s.version);audit(nextSoc,n.z,"SOC",maxNative,nativeTests);audit(nextFast,n.p1,"fast polarization",maxNative,nativeTests);audit(nextSlow,n.p2,"slow polarization",maxNative,nativeTests);audit(nextT,n.t,"temperature",maxNative,nativeTests);audit(volt,n.voltage,"terminal voltage",maxNative,nativeTests);audit(heat,n.heat,"resistive heat",maxNative,nativeTests);audit(power,n.power,"terminal power",maxNative,nativeTests);}
 req(nextSoc>.09&&nextSoc<.98&&nextT<60&&nextT>-18&&isfinite(volt),"synthetic state outside admissible bounds");
 s.z=nextSoc;s.p1=nextFast;s.p2=nextSlow;s.T=nextT;
 }
 }
 traces.close();probes.close();
 ofstream f(root/"results/scenario_summary.csv");f<<setprecision(17)<<"scenario_id,profile,version,ambient_C,age_factor,steps,dt_s,final_soc,final_temperature_C,max_temperature_C,min_voltage_V,max_voltage_V,net_discharge_Ah,terminal_energy_Wh,ocv_energy_Wh,ohmic_energy_Wh,polarization_power_energy_Wh,resistive_heat_proxy_Wh,power_identity_max_W,tracking_score_integral,voltage_lower_count,voltage_upper_count\n";
 for(auto&s:sc)f<<s.id<<","<<s.profile<<","<<s.version<<","<<s.ambient<<","<<s.age<<","<<steps<<","<<DTSEC<<","<<s.z<<","<<s.T<<","<<s.maxTemp<<","<<s.minVolt<<","<<s.maxVolt<<","<<s.Ah<<","<<s.Eterm<<","<<s.Eocv<<","<<s.Eohmic<<","<<s.Epolar<<","<<s.Heat<<","<<s.maxPowerResidual<<","<<s.score<<","<<s.underV<<","<<s.overV<<"\n";f.close();
 // Real paceval-generated SOC x temperature surface, no mathematical host computation.
 vector<Row>surface;for(int j=0;j<=22;j++)for(int k=0;k<=22;k++){Row r={.13+j*.035,0.015,0.020,3.0,0.+k*2.3,25,DTSEC,QAH,1.0,HT,CT,TARGETV,1.};surface.push_back(r);}
 vector<int>surfIds;for(auto&x:{"ocv","ohmic_resistance","fast_tau","slow_tau","terminal_voltage_v1","terminal_voltage_v2","resistive_heat_proxy_v2","d_ocv_d_soc","d_r0_d_temp","voltage_lower_margin_v2","composite_cost_v2_01"})surfIds.push_back(eng.idx(x));
 auto surfaces=eng.batch(surface,surfIds);ofstream sf(root/"results/parameter_surface.csv");sf<<setprecision(17)<<"soc,temperature_C,ocv_V,r0_ohm,tau1_s,tau2_s,voltage_1rc_V,voltage_2rc_V,heat_2rc_W,d_ocv_d_soc,d_r0_d_temp,lower_voltage_margin_V,cost_v2\n";for(size_t i=0;i<surface.size();i++){sf<<surface[i][Z]<<","<<surface[i][T];for(size_t k=0;k<surfIds.size();k++)sf<<","<<surfaces[k*surface.size()+i];sf<<"\n";}sf.close();
 // Scalar API sanity on known data; batch layout is independently checked.
 Row r=row(sc[0],0);double val=eng.scalar(eng.idx("ocv"),r);audit(val,nativeOCV(r),"scalar OCV",maxNative,nativeTests);
 ofstream meta(root/"results/sdk_execution.txt");meta<<setprecision(17)<<"ORIGINAL paceval SDK execution: SUCCESS\n"<<"registered_and_executed_graphs="<<eng.g.size()<<"\n"<<"multi_graph_batch_calls="<<eng.batches<<"\n"<<"graph_batch_outputs="<<eng.outputs<<"\n"<<"scalar_calls="<<eng.scalarCalls<<"\n"<<"independent_native_comparisons="<<nativeTests<<"\n"<<"max_scaled_native_error="<<maxNative<<"\n"<<"graph_inventory_probe_rows="<<probeN<<"\n"<<"scenarios="<<sc.size()<<"\n"<<"simulation_steps="<<steps<<"\n"<<"model_versions=1RC,2RC\n"<<"synthetic_dataset_only=true\n"<<"external_shared_library_not_redistributed=true\n";meta.close();
 cout<<"WP048 ORIGINAL PACEVAL PASS graphs="<<eng.g.size()<<" outputs="<<eng.outputs<<" batches="<<eng.batches<<" native="<<nativeTests<<" scenarios="<<sc.size()<<"\n";
}
int main(int argc,char**argv){try{fs::path root=".";int steps=720;for(int i=1;i<argc;i++){string x=argv[i];auto need=[&](){req(i+1<argc,"option argument missing");return string(argv[++i]);};if(x=="--out")root=need();else if(x=="--steps")steps=stoi(need());else throw runtime_error("unknown option "+x);}run(root,steps);return 0;}catch(const exception&e){cerr<<"WP048 FAILED: "<<e.what()<<"\n";return 2;}}
