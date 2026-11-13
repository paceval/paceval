// WP_042 Wind-Turbine Digital Twin Coefficient Functions, original paceval SDK execution.
// Synthetic surrogate coefficient maps + deterministic, reduced-order rotor dynamics.
// NOT a measured or certified turbine performance curve and NOT full aeroelastic OpenFAST.
// Mathematical coefficient, power, torque, sensitivities, diagnostics and state
// update functions are all real persistent paceval graphs, evaluated in batches.
// C++ handles stateful time integration, sampling, event policies and I/O only.
#include "paceval_main.h"
#include <algorithm>
#include <array>
#include <cmath>
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
static void req(bool b,const string& msg){if(!b)throw runtime_error(msg);}
static constexpr size_t N=12;
using In=array<double,N>;
static const string VARS="v omega beta rho radius inertia dt drag torque_reference omega_ref rating eta";
struct Formula{string id,formula,units,scope;PACEVAL_HANDLE h=nullptr;};
static vector<Formula> makeFormulas(){
 const string L="(omega*radius/v)";
 const string C="(0.475*exp(-(("+L+"-7.6)/3.1)^2)*exp(-beta/22))";
 const string C2="("+C+"*(1+0.015*sin(0.5*"+L+")*exp(-beta/25)))";
 const string CT="(0.03+0.78*exp(-(("+L+"-7.0)/6)^2)*exp(-beta/30))";
 const string A="(3.141592653589793*radius^2)";
 const string AIR="(0.5*rho*"+A+"*v^3)";
 const string P="("+AIR+"*"+C+")";
 const string P2="("+AIR+"*"+C2+")";
 const string DCDL="("+C+"*(-2*("+L+"-7.6)/(3.1^2)))";
 const string DCDB="(-"+C+"/22)";
 // The generator torque is computed FROM delivered rated power, so that energy
 // extraction, electrical power and rotor deceleration remain mutually consistent.
 const string GQraw="(torque_reference*(omega/omega_ref)^2)";
 const string ELEC="(eta*"+GQraw+"*omega)";
 const string SOFT="(0.5*("+ELEC+"+rating-sqrt(("+ELEC+"-rating)^2+1500^2)))";
 const string GQ="("+SOFT+"/(eta*omega))";
 const string ALPHA="(("+P+"/omega-"+GQ+"-drag*omega)/inertia)";
 vector<Formula> out;
 auto add=[&](string id,string exp,string units,string scope){out.push_back({id,exp,units,scope,nullptr});};
 add("tip_speed_ratio",L,"1","operating_point");
 add("cp_base",C,"1","surrogate_coefficient");
 add("cp_version_2",C2,"1","versioned_surrogate_coefficient");
 add("ct_base",CT,"1","surrogate_thrust_coefficient");
 add("rotor_area",A,"m2","geometry");
 add("wind_incident_power",AIR,"W","energy_flux");
 add("aerodynamic_power",P,"W","energy_flux");
 add("aerodynamic_power_v2",P2,"W","versioned_energy_flux");
 add("aerodynamic_torque","("+P+"/omega)","N m","rotor_momentum");
 add("aerodynamic_torque_v2","("+P2+"/omega)","N m","versioned_rotor_momentum");
 add("axial_thrust","(0.5*rho*"+A+"*v^2*"+CT+")","N","rotor_loading");
 add("dcp_dlambda",DCDL,"1","analytical_sensitivity");
 add("dcp_dbeta",DCDB,"1/deg","analytical_sensitivity");
 add("dP_dv_fixed_omega","(0.5*rho*"+A+"*v^2*(3*"+C+"-"+L+"*"+DCDL+"))","W/(m/s)","analytical_sensitivity");
 add("dP_domega","("+AIR+"*"+DCDL+"*radius/v)","W/(rad/s)","analytical_sensitivity");
 add("dP_dbeta","("+AIR+"*"+DCDB+")","W/deg","analytical_sensitivity");
 add("generator_reaction_torque",GQ,"N m","synthetic_control_model");
 add("generator_mechanical_power","("+SOFT+"/eta)","W","synthetic_control_model");
 add("generator_unconstrained_electrical_power",ELEC,"W","synthetic_control_model");
 add("soft_rated_generator_power",SOFT,"W","smooth_rating_proxy");
 add("generator_heat_loss","("+SOFT+"*(1/eta-1))","W","loss_proxy");
 add("rotor_angular_acceleration",ALPHA,"rad/s2","state_derivative");
 add("rotor_euler_next_omega","(omega+dt*"+ALPHA+")","rad/s","state_update");
 add("betz_margin","(16/27-"+C+")","1","physical_upper_bound_margin");
 add("rating_margin","(rating-"+SOFT+")","W","operating_margin");
 add("lower_wind_margin","(v-3)","m/s","operating_margin");
 add("upper_wind_margin","(25-v)","m/s","operating_margin");
 add("cp_revision_delta","("+C2+"-"+C+")","1","formula_version_difference");
 add("aero_power_revision_delta","("+P2+"-"+P+")","W","formula_version_difference");
 add("rotor_accel_revision_v2","(("+P2+"/omega-"+GQ+"-drag*omega)/inertia)","rad/s2","versioned_state_derivative");
 add("rotor_euler_next_omega_v2","(omega+dt*("+P2+"/omega-"+GQ+"-drag*omega)/inertia)","rad/s","versioned_state_update");
 return out;
}
static constexpr size_t G=31;
struct Stats{uint64_t calls=0,outputs=0,audits=0;double maxError=0;};
class Engine{
 public:
 vector<Formula> f;vector<PACEVAL_HANDLE> hs;Stats stats;
 Engine(){req(paceval_InitializeLibrary(nullptr),"could not initialize original paceval runtime");f=makeFormulas();req(f.size()==G,"unexpected formula registry size");
 for(auto&x:f){x.h=paceval_CreateComputation(x.formula.c_str(),(unsigned long)N,VARS.c_str(),false,nullptr);if(!x.h||paceval_GetIsError(x.h)){char message[256]={0},detail[256]={0};if(x.h)paceval_CreateErrorInformationText(x.h,message,detail);throw runtime_error("Cannot build graph: "+x.id+" / "+message+" / "+detail+" / "+x.formula);}hs.push_back(x.h);}}
 ~Engine(){for(auto h:hs)if(h)paceval_DeleteComputation(h);paceval_FreeLibrary();}
 vector<double> evaluate(const vector<In>& in,bool audit=true){req(!in.empty(),"Empty graph batch");vector<double> flat;flat.reserve(N*in.size());
 for(auto&x:in){for(double z:x)req(isfinite(z),"Nonfinite parameter");req(x[0]>=3&&x[0]<=25&&x[1]>=0.25&&x[1]<=3&&x[2]>=0&&x[2]<=30&&x[3]>=1&&x[3]<=1.4&&x[4]>=40&&x[4]<=90&&x[5]>0&&x[6]>0&&x[7]>=0&&x[8]>=0&&x[9]>0&&x[10]>0&&x[11]>0&&x[11]<=1,"Out-of-domain graph input");flat.insert(flat.end(),x.begin(),x.end());}
 vector<double> values(G*in.size(),numeric_limits<double>::quiet_NaN());vector<int> err(values.size(),-1);
 // In this original SDK revision, FALSE is the successful batch return status.
 bool failed=paceval_dGetMultipleComputationsResultsExt(hs.data(),(unsigned long)hs.size(),flat.data(),(unsigned long)in.size(),values.data(),nullptr,nullptr,err.data());req(!failed,"paceval multi-graph batch API failure");
 for(size_t k=0;k<values.size();++k)req(err[k]==0&&isfinite(values[k]),"paceval result error at flat index "+to_string(k));
 ++stats.calls;stats.outputs+=values.size();
 if(audit){size_t stride=max(size_t(1),in.size()/25);for(size_t i=0;i<in.size();i+=stride){const In&x=in[i];double lambda=x[1]*x[4]/x[0];double cp=0.475*exp(-pow((lambda-7.6)/3.1,2))*exp(-x[2]/22);double cp2=cp*(1+0.015*sin(0.5*lambda)*exp(-x[2]/25));double ct=0.03+0.78*exp(-pow((lambda-7)/6,2))*exp(-x[2]/30);double air=0.5*x[3]*3.141592653589793*x[4]*x[4]*x[0]*x[0]*x[0];double p=air*cp;double raw=x[11]*x[8]*pow(x[1]/x[9],2)*x[1];double rated=0.5*(raw+x[10]-sqrt(pow(raw-x[10],2)+1500*1500));double tq=rated/(x[11]*x[1]);double alpha=(p/x[1]-tq-x[7]*x[1])/x[5];
 const vector<pair<int,double>> oracle{{0,lambda},{1,cp},{2,cp2},{3,ct},{5,air},{6,p},{7,air*cp2},{8,p/x[1]},{16,tq},{21,alpha},{22,x[1]+x[6]*alpha},{23,16.0/27-cp},{27,cp2-cp}};
 for(auto [j,want]:oracle){double got=values[size_t(j)*in.size()+i],delta=abs(got-want)/(1+abs(want));stats.maxError=max(stats.maxError,delta);req(delta<2e-10,"Independent native audit failed for graph "+to_string(j));++stats.audits;}
 req(cp>=0&&cp<16.0/27&&cp2>=0&&cp2<16.0/27,"invalid synthetic Cp bound");}}
 return values;}
};
static In input(double v,double omega,double beta,double dt=1.0){return {v,omega,beta,1.225,63.,4.e7,dt,1.2e5,2.3e6,1.12,5.e6,0.95};}
static double wind(int i){return 9.0+2.25*sin(i*0.025)+1.2*sin(i*0.007+0.7)+0.55*cos(i*0.09);}
static double pitch(double v){return max(0.,(v-10.0)*2.0);}// Exogenous host control policy; NOT paceval aerodynamic mathematics.
static void run(const fs::path&root,int steps,int n,int nSweep){
 req(steps>=10&&steps<=10000&&n>=5&&n<=201&&nSweep>=10&&nSweep<=100000,"Invalid CLI range");fs::create_directories(root/"examples");fs::create_directories(root/"results");Engine engine;
 {ofstream o(root/"examples/formula_registry.csv");o<<"id,expression,units,interpretation\n";for(const auto &f:engine.f)o<<f.id<<",\""<<f.formula<<"\","<<f.units<<",\""<<f.scope<<"\"\n";}
 {ofstream o(root/"results/math_execution_inventory.csv");o<<"function,owner,api,scope\n";for(const auto &f:engine.f)o<<f.id<<",paceval,paceval_dGetMultipleComputationsResultsExt,"<<f.scope<<"\n";
 o<<"chronological_time_steps,C++ host,deterministic_Euler_orchestrator,stateful_sequential_execution\n";
 o<<"wind_and_pitch_inputs,C++ host,analytic_synthetic_trace,exogenous_weather_and_pitch_policy\n";
 o<<"energy_accumulation,C++ host,time_integral_sum,deterministic_scalar_reduction\n";
 o<<"high_precision_oracle,Python_mpmath,independent_validation,not_paceval_execution\n";
 o<<"aeroelastic_FSI_and_certified_curve,NOT_IMPLEMENTED,requires_OpenFAST_or_equivalent,not_claimed\n";}
 const int B=128;ofstream o(root/"examples/paceval_coefficient_surface.csv");o<<"tip_speed_ratio,pitch_deg,wind_ms,omega_rad_s,Cp_base,Cp_v2,Ct,rotor_power_W,aero_torque_Nm,thrust_N,dCp_dlambda,dCp_dbeta,dP_dv_fixedomega_W_per_ms,dP_domega_W_per_rad_s,betz_margin\n"<<setprecision(16);
 vector<In> buffer;for(int j=0;j<n;++j)for(int i=0;i<n;++i){double lam=3.+11.*i/(n-1),beta=20.*j/(n-1),v=10;buffer.push_back(input(v,lam*v/63.,beta));if(buffer.size()==B||(i==n-1&&j==n-1)){auto res=engine.evaluate(buffer);for(size_t k=0;k<buffer.size();++k){const In&x=buffer[k];o<<x[1]*x[4]/x[0]<<','<<x[2]<<','<<x[0]<<','<<x[1];for(int idx: {1,2,3,6,8,10,11,12,13,14,23})o<<','<<res[size_t(idx)*buffer.size()+k];o<<'\n';}buffer.clear();}}o.close();
 ofstream s(root/"examples/paceval_operating_sweep.csv");s<<"sample,wind_ms,omega_rad_s,pitch_deg,lambda,Cp_base,Cp_v2,Ct,rotor_power_W,rotor_power_v2_W,gen_power_W,soft_rated_power_W,thrust_N,accel_rad_s2,version_power_delta_W\n"<<setprecision(16);
 for(int offset=0;offset<nSweep;offset+=B){vector<In> inputs;for(int j=offset;j<min(offset+B,nSweep);++j){double v=4+14*((j*37)%nSweep+0.5)/nSweep,lam=4.+5.0*((j*73+11)%nSweep+0.5)/nSweep;double beta=18.*((j*47+19)%nSweep+0.5)/nSweep;inputs.push_back(input(v,v*lam/63.,beta));}auto res=engine.evaluate(inputs);for(size_t k=0;k<inputs.size();++k){const auto &x=inputs[k];s<<offset+k<<','<<x[0]<<','<<x[1]<<','<<x[2];for(int id:{0,1,2,3,6,7,18,19,10,21,28})s<<','<<res[size_t(id)*inputs.size()+k];s<<'\n';}}
 s.close();
 ofstream tr(root/"examples/paceval_rotor_time_series.csv");tr<<"version,step,time_s,wind_ms,pitch_deg,omega_rad_s,lambda,Cp,rotor_power_W,rotor_torque_Nm,generator_torque_Nm,grid_power_W,thrust_N,angular_accel_rad_s2,omega_next_rad_s,cumulative_energy_kWh\n"<<setprecision(16);
 array<double,2> omega{1.10,1.10};array<double,2> energies{0,0};double maxV=0,minV=100,maxOmega=0,minOmega=10;
 for(int step=0;step<steps;++step){double v=wind(step),b=pitch(v);vector<In> q{input(v,omega[0],b),input(v,omega[1],b)};auto res=engine.evaluate(q,false);maxV=max(maxV,v);minV=min(minV,v);
 for(int model=0;model<2;++model){double lam=res[0*q.size()+model],cp=res[(model==0?1:2)*q.size()+model],p=res[(model==0?6:7)*q.size()+model],tor=res[(model==0?8:9)*q.size()+model],gen=res[16*q.size()+model],grid=res[19*q.size()+model],thrust=res[10*q.size()+model],acc=res[(model==0?21:29)*q.size()+model],next=res[(model==0?22:30)*q.size()+model];req(next>0.3&&next<2.6,"rotor integration outside valid operating domain");energies[model]+=grid/(3.6e6);tr<<model+1<<','<<step<<','<<step<<','<<v<<','<<b<<','<<omega[model]<<','<<lam<<','<<cp<<','<<p<<','<<tor<<','<<gen<<','<<grid<<','<<thrust<<','<<acc<<','<<next<<','<<energies[model]<<'\n';omega[model]=next;maxOmega=max(maxOmega,next);minOmega=min(minOmega,next);}}
 tr.close();
 ofstream summary(root/"results/execution_summary.json");summary<<fixed<<setprecision(10);
 summary<<"{\n \"project\": \"WP_042\",\n \"model_provenance\": \"explicitly synthetic wind and rotor coefficient functions\",\n \"full_aeroelastic_simulation\": false,\n \"paceval_graphs\": "<<engine.f.size()<<",\n \"batch_calls\": "<<engine.stats.calls<<",\n \"batch_graph_outputs\": "<<engine.stats.outputs<<",\n \"native_audit_values\": "<<engine.stats.audits<<",\n \"max_native_scaled_error\": "<<engine.stats.maxError<<",\n \"coefficient_surface_points\": "<<n*n<<",\n \"operating_sweep_points\": "<<nSweep<<",\n \"dynamic_steps_per_version\": "<<steps<<",\n \"timestep_seconds\": 1.0,\n \"wind_range_m_s\": ["<<minV<<","<<maxV<<"],\n \"rotor_omega_range_rad_s\": ["<<minOmega<<","<<maxOmega<<"],\n \"energy_version1_kWh\": "<<energies[0]<<",\n \"energy_version2_kWh\": "<<energies[1]<<"\n}\n";
 cerr<<"PACEVAL ORIGINAL SDK SUCCESS graphs="<<engine.f.size()<<" batch_calls="<<engine.stats.calls<<" outputs="<<engine.stats.outputs<<" audits="<<engine.stats.audits<<" energy(kWh)="<<energies[0]<<","<<energies[1]<<"\n";
}
int main(int argc,char**argv){try{string out=".";int steps=720,n=61,sweep=4800;for(int i=1;i<argc;++i){string s=argv[i];auto val=[&](){req(++i<argc,"missing option value");return string(argv[i]);};if(s=="--out")out=val();else if(s=="--steps")steps=stoi(val());else if(s=="--surface")n=stoi(val());else if(s=="--sweep")sweep=stoi(val());else throw runtime_error("Unknown CLI option "+s);}run(fs::path(out),steps,n,sweep);return 0;}catch(const exception&e){cerr<<"ERROR "<<e.what()<<'\n';return 2;}}
