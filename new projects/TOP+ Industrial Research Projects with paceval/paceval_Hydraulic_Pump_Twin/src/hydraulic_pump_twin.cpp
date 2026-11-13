// WP_043 - Hydraulic Pump Efficiency Functions / real paceval mathematical twin.
// Two-parallel-pipe hydraulic network, 20 versioned synthetic efficiency functions.
// REAL ORIGINAL SDK: All mathematical expressions and per-point cost computations use
// persistent paceval graphs and paceval_dGetMultipleComputationsResultsExt.
// C++ owns orchestration, independent audit, time sequence, I/O and the scheduling policy.
// This is not EPANET, measured pump performance or a calibrated water-quality transport solver.
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
#include <sstream>
#include <stdexcept>
#include <string>
#include <vector>
using namespace std;
namespace fs=std::filesystem;
static void check(bool ok,const string &m){if(!ok)throw runtime_error(m);}
static constexpr size_t V=14;
using In=array<double,V>;
static const string VARS="q n h0 a hs ka kb rho etam cin kd va vb tariff";
struct Formula {string id,exp,unit,kind; PACEVAL_HANDLE h=nullptr;};
static string to_s(int x){return to_string(x);}
static vector<Formula> formulas(){
 vector<Formula> out;auto add=[&](string id,string expression,string unit,string kind){out.push_back({id,expression,unit,kind,nullptr});};
 const string ke="(1/(1/sqrt(ka)+1/sqrt(kb))^2)";
 const string ph="(h0*n^2-a*q^2)";
 const string sh="(hs+"+ke+"*q^2)";
 const string qo="(sqrt((h0*n^2-hs)/(a+"+ke+")))";
 const string qa="(q*(1/sqrt(ka))/(1/sqrt(ka)+1/sqrt(kb)))";
 const string qb="(q*(1/sqrt(kb))/(1/sqrt(ka)+1/sqrt(kb)))";
 const string aeta="(0.78-0.20*((q/n-0.145)/0.12)^2)";
 const string hydraulic="(rho*9.81*q*"+ph+"/1000)";
 const string wpower="("+hydraulic+"/etam)";
 const string ea="(cin*exp(-kd*va/"+qa+"))";
 const string eb="(cin*exp(-kd*vb/"+qb+"))";
 add("equivalent_parallel_loss_coefficient",ke,"s2/m5","network");
 add("pump_head",ph,"m","hydraulic");
 add("system_head",sh,"m","hydraulic");
 add("head_residual","("+ph+"-"+sh+")","m","hydraulic");
 add("operating_flow",qo,"m3/s","operating_point");
 add("branch_flow_a",qa,"m3/s","network");
 add("branch_flow_b",qb,"m3/s","network");
 add("branch_headloss_a","(ka*"+qa+"^2)","m","network");
 add("branch_headloss_b","(kb*"+qb+"^2)","m","network");
 add("hydraulic_power",hydraulic,"kW","energy");
 add("base_efficiency",aeta,"1","quality_of_pump_model");
 add("base_wire_to_water_efficiency","("+aeta+"*etam)","1","energy");
 add("base_electrical_power","("+wpower+"/"+aeta+")","kW","energy");
 add("pump_head_dq","(-2*a*q)","s/m2","sensitivity");
 add("system_head_dq","(2*"+ke+"*q)","s/m2","sensitivity");
 add("hydraulic_residual_dq","(-2*(a+"+ke+")*q)","s/m2","sensitivity");
 add("base_efficiency_dq","(-0.40*((q/n-0.145)/0.12)/(0.12*n))","s/m3","sensitivity");
 add("base_power_dq","((rho*9.81/(1000*etam))*(("+ph+"-2*a*q^2)/"+aeta+"-q*"+ph+"*(-0.40*((q/n-0.145)/0.12)/(0.12*n))/("+aeta+"^2)))","kW/(m3/s)","sensitivity");
 add("dissolved_tracer_a",ea,"mg/L","steady_quality_surrogate");
 add("dissolved_tracer_b",eb,"mg/L","steady_quality_surrogate");
 add("outlet_mixed_tracer","(("+qa+"*"+ea+"+"+qb+"*"+eb+")/q)","mg/L","steady_quality_surrogate");
 add("volume_flow_balance","(q-"+qa+"-"+qb+")","m3/s","conservation");
 add("branch_head_balance","(ka*"+qa+"^2-kb*"+qb+"^2)","m","conservation");
 add("head_margin","("+ph+"-hs)","m","operating_domain");
 add("cost_per_hour_base","(tariff*"+wpower+"/"+aeta+")","currency/hour","economic_surrogate");
 add("energy_per_m3","("+wpower+"/"+aeta+"/(3600*q))","kWh/m3","energy");
 for(int v=0;v<20;++v){
   string coeff="(0"+string(v<10?"-":"+")+to_string(abs(v-10))+")";
   const string eta="("+aeta+"*(1+0.0006*"+coeff+"*sin(12*q/n)))";
   add("eta_version_"+to_s(v+1),eta,"1","versioned_synthetic_efficiency");
   add("electric_power_version_"+to_s(v+1),"("+wpower+"/"+eta+")","kW","versioned_energy");
   add("hourly_cost_version_"+to_s(v+1),"(tariff*"+wpower+"/"+eta+")","currency/hour","versioned_cost");
 }
 return out;
}
static constexpr size_t CORE=26;
static constexpr size_t FCOUNT=CORE+60;
struct Statistics {uint64_t calls=0,outputs=0,audits=0;double max_scaled_error=0;};
class Engine {
public:
 vector<Formula> registry;vector<PACEVAL_HANDLE> handles;Statistics stat;
 Engine(){check(paceval_InitializeLibrary(nullptr),"original paceval library failed initialize");registry=formulas();check(registry.size()==FCOUNT,"wrong graph count");
 for(auto &f:registry){f.h=paceval_CreateComputation(f.exp.c_str(),(unsigned long)V,VARS.c_str(),false,nullptr);
  if(!f.h||paceval_GetIsError(f.h)){char msg[256]={0},more[256]={0};if(f.h)paceval_CreateErrorInformationText(f.h,msg,more);throw runtime_error("Cannot build "+f.id+" "+msg+" / "+more+" "+f.exp);}
  handles.push_back(f.h);}}
 ~Engine(){for(auto h:handles)if(h)paceval_DeleteComputation(h);paceval_FreeLibrary();}
 vector<double> eval(const vector<In>& data,bool audit=true){check(!data.empty(),"empty batch");vector<double> flat;flat.reserve(data.size()*V);
 for(const auto& x:data){for(double z:x)check(isfinite(z),"nonfinite input");check(x[0]>0.01&&x[0]<0.4&&x[1]>=0.68&&x[1]<=1.25&&x[2]>30&&x[3]>0&&x[4]>0&&x[5]>100&&x[6]>100&&x[7]>=970&&x[7]<=1030&&x[8]>=0.8&&x[8]<=1&&x[9]>0&&x[10]>=0&&x[11]>0&&x[12]>0&&x[13]>=0,"out of range");flat.insert(flat.end(),x.begin(),x.end());}
 vector<double> val(registry.size()*data.size(),numeric_limits<double>::quiet_NaN());vector<int> err(val.size(),-1);
 // SDK returns FALSE for successful computation; inspect every output error.
 bool failed=paceval_dGetMultipleComputationsResultsExt(handles.data(),(unsigned long)handles.size(),flat.data(),(unsigned long)data.size(),val.data(),nullptr,nullptr,err.data());
 check(!failed,"paceval multi-graph batch failure");for(size_t i=0;i<err.size();++i)check(err[i]==0&&isfinite(val[i]),"bad paceval result idx="+to_string(i));
 stat.calls++;stat.outputs+=val.size();
 if(audit){size_t stride=max(size_t(1),data.size()/14);for(size_t k=0;k<data.size();k+=stride){const auto &x=data[k];double ke=1/pow(1/sqrt(x[5])+1/sqrt(x[6]),2);double hp=x[2]*x[1]*x[1]-x[3]*x[0]*x[0];double hs=x[4]+ke*x[0]*x[0];double qstar=sqrt((x[2]*x[1]*x[1]-x[4])/(x[3]+ke));double qa=x[0]/sqrt(x[5])/(1/sqrt(x[5])+1/sqrt(x[6]));double qb=x[0]-qa;double eta=.78-.20*pow((x[0]/x[1]-.145)/.12,2);double hyd=x[7]*9.81*x[0]*hp/1000;
  const vector<pair<size_t,double>> ref{{0,ke},{1,hp},{2,hs},{3,hp-hs},{4,qstar},{5,qa},{6,qb},{7,x[5]*qa*qa},{8,x[6]*qb*qb},{9,hyd},{10,eta},{11,eta*x[8]},{12,hyd/eta/x[8]},{21,x[0]-qa-qb}};
  for(auto e:ref){double got=val[e.first*data.size()+k];double delta=abs(got-e.second)/(1+abs(e.second));stat.max_scaled_error=max(stat.max_scaled_error,delta);check(delta<5e-10,"native math audit error "+registry[e.first].id);stat.audits++;}
  check(eta>.35&&eta<0.85,"invalid synthetic efficiency");}}
 return val;}
};
static In init(double q=.14,double n=1.0,double tariff=.20){return {q,n,58,1250,15,2800,3700,998.2,.94,1.0,0.012,3.5,5.0,tariff};}
static double item(const vector<double>& v,size_t width,size_t graph,size_t sample){return v[graph*width+sample];}
static void write_registry(const fs::path&root,const Engine &e){
 ofstream file(root/"examples/formula_registry.csv");file<<"graph_id,expression,unit,family\n";for(auto &f:e.registry)file<<f.id<<",\""<<f.exp<<"\","<<f.unit<<","<<f.kind<<"\n";
 ofstream inv(root/"results/math_execution_inventory.csv");inv<<"task,execution_owner,actual_api,role\n";for(auto &f:e.registry)inv<<f.id<<",paceval,paceval_dGetMultipleComputationsResultsExt,"<<f.kind<<"\n";
 inv<<"schedule_speed_and_tariff,C++ host,deterministic_input_profile,stateful\n";
 inv<<"time_integrated_energy_cost,C++ host,chrono_sum,stateful_reduction\n";
 inv<<"reference_hydraulic_math,C++ and Python,independent_oracle,not_paceval\n";
 inv<<"full_pipe_transients_and_calibrated_transport,NOT_IMPLEMENTED,requires_network_solver,scope_limit\n";
 }
static void run(const fs::path&root,int surface,int sweep,int hours){check(surface>=7&&surface<=181&&sweep>=20&&sweep<=80000&&hours>=8&&hours<=240,"invalid CLI");fs::create_directories(root/"examples");fs::create_directories(root/"results");Engine eng;write_registry(root,eng);
 // Sweeps of physically allowable operating points: evaluate all 86 graphs in real batches.
 ofstream out(root/"examples/paceval_operating_sweep.csv");out<<setprecision(16);out<<"sample,q_m3s,speed_ratio,tariff,head_pump_m,head_system_m,residual_m,flow_operating_m3s,efficiency_base,hydraulic_power_kW,electric_power_base_kW,branch_a_m3s,branch_b_m3s,quality_mix_mgL,electric_power_v1_kW,electric_power_v20_kW,energy_kWh_per_m3\n";
 for(int off=0;off<sweep;off+=96){vector<In> inputs;for(int j=off;j<min(off+96,sweep);++j){double n=.76+.46*((j*139+17)%sweep+.5)/sweep;double q=.055+.10*((j*89+7)%sweep+.5)/sweep;auto x=init(q,n,.14+.16*((j*13)%sweep+.5)/sweep);inputs.push_back(x);}auto val=eng.eval(inputs);for(size_t k=0;k<inputs.size();++k){const auto&x=inputs[k];out<<off+k<<","<<x[0]<<","<<x[1]<<","<<x[13];for(size_t g:{1,2,3,4,10,9,12,5,6,20,27,84,25})out<<","<<item(val,inputs.size(),g,k);out<<"\n";}}
 out.close();
 // Operating solution computed inside the paceval graph, then the solution is passed
 // back to the registered graph batch for all versioned cost/quality functions.
 ofstream surf(root/"examples/paceval_operating_surface.csv");surf<<setprecision(16);surf<<"speed_ratio,static_head_m,q_operating_m3s,pump_head_m,system_head_m,eta_base,electric_kW,branch_a_m3s,branch_b_m3s,c_out_mgL,hydraulic_residual_m\n";
 const int BS=96;vector<In> block;
 auto flush=[&](){if(block.empty())return;auto sol=eng.eval(block,false);for(size_t k=0;k<block.size();++k){block[k][0]=item(sol,block.size(),4,k);}
 auto res=eng.eval(block,true);for(size_t k=0;k<block.size();++k){auto &x=block[k];surf<<x[1]<<","<<x[4]<<","<<x[0];for(size_t g:{1,2,10,12,5,6,20,3})surf<<","<<item(res,block.size(),g,k);surf<<"\n";}block.clear();};
 for(int j=0;j<surface;++j){for(int i=0;i<surface;++i){double speed=.78+.4*i/(surface-1),hst=9+13.*j/(surface-1);auto x=init(.12,speed);x[4]=hst;block.push_back(x);if(block.size()==BS)flush();}}
 flush();surf.close();
 // 24/48h trace and 20 independent efficiency versions at physically consistent operating points.
 ofstream trace(root/"examples/paceval_operating_trace.csv");trace<<setprecision(16);trace<<"step,hour,speed_ratio,tariff,solved_flow_m3s,head_m,eta_base,hydraulic_kW,elec_base_kW,elec_version_1_kW,elec_version_20_kW,mixed_concentration_mgL,hourly_cost_base,cumulative_base_energy_kWh,cumulative_version1_energy_kWh,cumulative_version20_energy_kWh\n";
 double energy=0,e1=0,e20=0,cost=0,maxres=0,maxbal=0;
 for(int t=0;t<hours;++t){double n=.97+.12*sin(t*.35)+.055*sin(t*.67+1.0);double tariff=.15+.08*(.5+.5*sin(t*.28+.6));auto x=init(.13,n,tariff);auto sol=eng.eval({x},false);x[0]=sol[4];auto val=eng.eval({x},true);double flow=val[4],res=val[3],hp=val[1],p=val[12],pv1=val[27],pv20=val[84];check(abs(res)<1e-9,"head residual inconsistent");maxres=max(maxres,abs(res));maxbal=max(maxbal,abs(val[21]));energy+=p;e1+=pv1;e20+=pv20;cost+=val[24];trace<<t<<","<<t<<","<<n<<","<<tariff<<","<<flow<<","<<hp<<","<<val[10]<<","<<val[9]<<","<<p<<","<<pv1<<","<<pv20<<","<<val[20]<<","<<val[24]<<","<<energy<<","<<e1<<","<<e20<<"\n";}
 trace.close();
 // One physically consistent operating state is evaluated against all twenty
 // independently registered efficiency, power, and cost mathematical versions.
 ofstream versions(root/"examples/paceval_formula_version_profile.csv");
 versions<<setprecision(16)<<"version,q_operating_m3s,speed_ratio,efficiency,power_kW,cost_per_hour\n";
 auto xv=init(.12,1.0,.21);auto sv=eng.eval({xv},false);xv[0]=sv[4];auto vr=eng.eval({xv},true);
 for(int ver=0;ver<20;++ver){versions<<ver+1<<","<<xv[0]<<","<<xv[1]<<","<<vr[26+3*ver]<<","<<vr[27+3*ver]<<","<<vr[28+3*ver]<<"\n";}
 versions.close();
 // Running state-free API values are published as a deterministic machine-readable record.
 ofstream summary(root/"results/execution_summary.json");summary<<setprecision(12)<<"{\n \"project\":\"WP_043\",\n \"provenance\":\"synthetic pump, network, and steady water-quality surrogates\",\n \"paceval_graphs\":"<<eng.registry.size()<<",\n \"paceval_batch_calls\":"<<eng.stat.calls<<",\n \"paceval_batch_outputs\":"<<eng.stat.outputs<<",\n \"native_audit_values\":"<<eng.stat.audits<<",\n \"max_native_scaled_error\":"<<eng.stat.max_scaled_error<<",\n \"sweep_points\":"<<sweep<<",\n \"operating_surface_points\":"<<surface*surface<<",\n \"hourly_trace_points\":"<<hours<<",\n \"energy_base_kWh\":"<<energy<<",\n \"energy_v1_kWh\":"<<e1<<",\n \"energy_v20_kWh\":"<<e20<<",\n \"cost_base_currency\":"<<cost<<",\n \"max_head_residual_m\":"<<maxres<<",\n \"max_branch_mass_balance_m3s\":"<<maxbal<<"\n}\n";
 cerr<<"ORIGINAL PACEVAL SDK SUCCESS graphs="<<eng.registry.size()<<" batch outputs="<<eng.stat.outputs<<" independent C++ values="<<eng.stat.audits<<" trace energy(kWh)="<<energy<<"\n";
}
int main(int argc,char**argv){try{string root=".";int surface=61,sweep=6000,hours=48;for(int i=1;i<argc;++i){string a=argv[i];auto arg=[&](){check(++i<argc,"missing CLI argument");return string(argv[i]);};if(a=="--out")root=arg();else if(a=="--surface")surface=stoi(arg());else if(a=="--sweep")sweep=stoi(arg());else if(a=="--hours")hours=stoi(arg());else throw runtime_error("unknown argument "+a);}run(root,surface,sweep,hours);return 0;}catch(const exception&e){cerr<<"ERROR: "<<e.what()<<'\n';return 2;}}
