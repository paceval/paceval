// WP_044 -- Parameterized Bulk-Wave Evaluation Kernels with paceval.
// Original paceval SDK header and interface source are included beside this file;
// the external proprietary/shared runtime is linked separately and NOT redistributed.
// SCIENTIFIC BOUNDARY: idealized scalar/tensor-mode-equation numerical verification
// on a finite z-interval in conformal AdS5 coordinates. NOT a new gravitational
// wave signal, 5D transport proof, brane detection, or nonlinear Einstein solver.
// All tested finite-difference RHS, forcing, energy density, flux, and diagnostic
// mathematical formulas are persistent paceval graphs (including two revisions).
// C++ owns the time stepping, boundary state, arrays, reductions and I/O.
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
#include <numeric>
#include <sstream>
#include <stdexcept>
#include <string>
#include <vector>
using namespace std;
namespace fs=std::filesystem;
static void require(bool x,const string&msg){if(!x)throw runtime_error(msg);}
static constexpr double PI=3.1415926535897932384626433832795;
static constexpr size_t NV=16;
using Row=array<double,NV>;
static const string VARS="z left h right vel k q dx t omega m amp dt delta forced target";
struct Expression{string name,expr,units,role;PACEVAL_HANDLE h=nullptr;};
enum Id : int {GRAD=0,LAP,OP,SPECTRAL,SOURCE,RHS,RHS_V2,ENERGY,FLUX,EXACT_ZERO,VEL_ZERO,EXACT_MMS,VEL_MMS,ERROR_SIGNED,ERROR_SQUARED,ERROR_ABS,PARTIAL_K,PARTIAL_Q,PARTIAL_DELTA,UPDATE_H,UPDATE_V,MASS_TERM,FORCING_POWER,WEIGHTED_RESIDUAL,SOURCE_Q_SENS,CONTINUUM_MMS_RHS,ENERGY_V2,VERSION_DELTA,NUM_GRAPHS};
static vector<Expression> formulas(){
 const string gd="((right-left)/(2*dx))";
 const string la="((right-2*h+left)/(dx^2))";
 const string op="("+la+"-3/z*"+gd+")";
 const string mass="((k^2+q)*h)";
 const string s="(forced*((k^2+q-omega^2+m^2)*z^2*sin(m*z)+4*sin(m*z)-m*z*cos(m*z))*cos(omega*t))";
 const string r="("+op+"-"+mass+"+"+s+")";
 const string rv="("+r+"-delta*h)";
 const string zero="(amp*(1+0.08*z^4)*cos(omega*t))";
 const string mms="(amp*z^2*sin(m*z)*cos(omega*t))";
 // The amplitude 'amp' is part of the forcing too: otherwise the manufactured
 // solution would be exact only for unit amplitude. Every graph uses this same S.
 const string source="(amp*"+s+")";
 const string rhs="("+op+"-"+mass+"+"+source+")";
 const string rhs2="("+rhs+"-delta*h)";
 vector<Expression> f;
 auto add=[&](const string&a,const string&b,const string&u,const string&r){f.push_back({a,b,u,r,nullptr});};
 add("first_difference_z",gd,"field/z","spatial_derivative");
 add("second_difference_z",la,"field/z2","spatial_derivative");
 add("ads5_radial_operator",op,"field/z2","warped_radial_operator");
 add("fourier_momentum", "(-k^2*h)","field/t2","fourier_spatial_term");
 add("manufactured_source",source,"field/t2","verified_forcing_only");
 add("wave_acceleration_v1",rhs,"field/t2","full_paceval_rhs");
 add("wave_acceleration_v2",rhs2,"field/t2","versioned_full_paceval_rhs");
 add("weighted_energy_density","(0.5*(vel^2+"+gd+"^2+(k^2+q)*h^2)/z^3)","normalized_energy/z","energy_diagnostic");
 add("weighted_energy_flux","(-vel*"+gd+"/z^3)","energy_flux","boundary_flux_diagnostic");
 add("exact_zero_mode",zero,"field","analytical_mode");
 add("exact_zero_mode_velocity","(-omega*amp*(1+0.08*z^4)*sin(omega*t))","field/t","analytical_mode");
 add("exact_manufactured_mode",mms,"field","manufactured_solution");
 add("exact_manufactured_velocity","(-omega*amp*z^2*sin(m*z)*sin(omega*t))","field/t","manufactured_solution");
 add("signed_solution_error","(h-target)","field","independent_reference");
 add("squared_solution_error","((h-target)^2)","field2","independent_reference");
 add("absolute_solution_error","(abs(h-target))","field","independent_reference");
 add("rhs_sensitivity_k","(-2*k*h+2*k*amp*forced*z^2*sin(m*z)*cos(omega*t))","field/t2/k","analytic_parameter_sensitivity");
 add("rhs_sensitivity_q","(-h+amp*forced*z^2*sin(m*z)*cos(omega*t))","field/t2/q","analytic_parameter_sensitivity");
 add("rhs_sensitivity_delta","(-h)","field/t2/delta","analytic_version_sensitivity");
 add("euler_update_field","(h+dt*vel)","field","explicit_update_diagnostic");
 add("euler_update_velocity","(vel+dt*"+rhs+")","field/t","explicit_update_diagnostic");
 add("total_versioned_potential","((k^2+q+delta)*h)","field/t2","model_potential");
 add("forcing_power_density","(vel*"+source+"/z^3)","energy/t","energy_source_diagnostic");
 add("weighted_rhs_residual","(abs("+rhs+"-target)/z^3)","field/t2","reference_operator_residual");
 add("source_sensitivity_q","(amp*forced*z^2*sin(m*z)*cos(omega*t))","field/t2/q","source_parameter_sensitivity");
 add("continuum_rhs_manufactured","(-omega^2*"+mms+")","field/t2","manufactured_reference_rhs");
 add("weighted_energy_density_v2","(0.5*(vel^2+"+gd+"^2+(k^2+q+delta)*h^2)/z^3)","normalized_energy/z","versioned_energy");
 add("versioned_rhs_difference","(-delta*h)","field/t2","formula_version_difference");
 require(f.size()==NUM_GRAPHS,"Bad graph registry size");return f;
}
struct Counters{uint64_t calls=0,outputs=0,oracle=0;double maxdiff=0;};
class Engine{
 public:
 vector<Expression> expr; Counters count;
 Engine(){require(paceval_InitializeLibrary(nullptr),"paceval original runtime initialize failed");expr=formulas();for(auto &e:expr){e.h=paceval_CreateComputation(e.expr.c_str(),(unsigned long)NV,VARS.c_str(),false,nullptr);if(!e.h||paceval_GetIsError(e.h)){char s[256]={0},d[256]={0};if(e.h)paceval_CreateErrorInformationText(e.h,s,d);throw runtime_error("Cannot create paceval graph "+e.name+": "+s+" / "+d+" / "+e.expr);}}}
 ~Engine(){for(auto&e:expr)if(e.h)paceval_DeleteComputation(e.h);paceval_FreeLibrary();}
 vector<double> calc(const vector<Row>&x,const vector<int>&ids){require(!x.empty()&&!ids.empty(),"empty paceval batch");vector<double> flat;flat.reserve(x.size()*NV);
 for(const auto&r:x){for(double v:r)require(isfinite(v),"nonfinite paceval input");require(r[0]>=1&&r[0]<=2&&r[7]>0&&r[7]<=.2&&r[5]>0&&r[5]<=10&&r[6]>=0&&r[6]<=3&&r[9]>0&&r[10]>=0&&r[10]<=5&&r[11]>0&&r[11]<=3&&r[12]>=0&&r[12]<=1&&r[13]>=0&&r[13]<=1&&r[14]>=0&&r[14]<=1,"out-of-contract input");flat.insert(flat.end(),r.begin(),r.end());}
 vector<PACEVAL_HANDLE> h;for(int j:ids){require(j>=0&&j<NUM_GRAPHS,"invalid graph id");h.push_back(expr[j].h);}vector<double>v(x.size()*ids.size(),numeric_limits<double>::quiet_NaN());vector<int>err(v.size(),-1);
 // This paceval SDK returns FALSE for a successful batch call; check each error code.
 bool failed=paceval_dGetMultipleComputationsResultsExt(h.data(),(unsigned long)h.size(),flat.data(),(unsigned long)x.size(),v.data(),nullptr,nullptr,err.data());require(!failed,"paceval multi-graph batch reported failure");for(size_t i=0;i<v.size();++i)require(err[i]==0&&isfinite(v[i]),"paceval graph error at "+to_string(i));++count.calls;count.outputs+=v.size();return v;}
};
struct Mode{string name;int kind;double k,q,m,omega,amp,delta,forced;};
static Mode makeMode(int kind){
 if(kind==0)return {"zero_radial",0,1.4,.0,0,1.4,.38,0,0};
 if(kind==1){double k=1.1,q=.30,m=2.0;return {"bessel_J2",1,k,q,m,sqrt(k*k+q+m*m),.80,0,0};}
 if(kind==2)return {"manufactured_forced",2,1.3,.25,1.8,2.05,.25,0,1};
 if(kind==3){double k=1.4,q=0,delta=.55;return {"zero_radial_revision",3,k,q,0,sqrt(k*k+delta),.38,delta,0};}
 throw runtime_error("unknown scenario");
}
static double profile(const Mode&s,double z){if(s.kind==0||s.kind==3)return s.amp*(1+.08*pow(z,4));if(s.kind==1)return s.amp*z*z*std::cyl_bessel_j(2,s.m*z);return s.amp*z*z*sin(s.m*z);}
static double exact(const Mode&s,double z,double t){return profile(s,z)*cos(s.omega*t);}
static double exactv(const Mode&s,double z,double t){return -s.omega*profile(s,z)*sin(s.omega*t);}
static double source(const Mode&s,double z,double t){if(!s.forced)return 0.;double m=s.m;return s.amp*((s.k*s.k+s.q-s.omega*s.omega+m*m)*z*z*sin(m*z)+4*sin(m*z)-m*z*cos(m*z))*cos(s.omega*t);}
static double referenceRHS(const Row&r,bool revised){double z=r[0],l=r[1],h=r[2],rr=r[3],dx=r[7],k=r[5],q=r[6],delta=revised?r[13]:0.;return (rr-2*h+l)/(dx*dx)-3/z*(rr-l)/(2*dx)-(k*k+q+delta)*h+source({"",2,r[5],r[6],r[10],r[9],r[11],r[13],r[14]},z,r[8]);}
static Row row(double z,double left,double h,double right,double v,const Mode&s,double dx,double t,double dt,double target){return {z,left,h,right,v,s.k,s.q,dx,t,s.omega,s.m,s.amp,dt,s.delta,s.forced,target};}
struct State{vector<double>h,v;};
struct SimResult{double l2=0,linf=0,energy=0,fluxLeft=0,fluxRight=0,time=0;int n=0,steps=0;};
static void impose(State&s,const Mode&m,double z0,double dx,double t){const size_t n=s.h.size();s.h[0]=exact(m,z0,t);s.v[0]=exactv(m,z0,t);s.h[n-1]=exact(m,z0+(n-1)*dx,t);s.v[n-1]=exactv(m,z0+(n-1)*dx,t);}
static Row nodeRow(const State&s,const Mode&m,double z0,double dx,double t,double dt,size_t j){double z=z0+j*dx;return row(z,s.h[j-1],s.h[j],s.h[j+1],s.v[j],m,dx,t,dt,exact(m,z,t));}
struct Deriv{vector<double> dh,dv;};
static Deriv derivatives(Engine&e_unused)=delete;
static Deriv derivatives(Engine&eng,const State&s,const Mode&m,double z0,double dx,double t,double dt,bool doAudit){size_t n=s.h.size();vector<Row>rs;rs.reserve(n-2);for(size_t i=1;i+1<n;i++)rs.push_back(nodeRow(s,m,z0,dx,t,dt,i));vector<double> out=eng.calc(rs,{m.delta>0?RHS_V2:RHS});Deriv d{vector<double>(n,0),vector<double>(n,0)};for(size_t i=1;i+1<n;i++){d.dh[i]=s.v[i];d.dv[i]=out[i-1];}
 if(doAudit){for(size_t i=1;i+1<n;i+=max(size_t(1),(n-2)/8)){double oracle=referenceRHS(rs[i-1],m.delta>0);double err=abs(d.dv[i]-oracle)/(1+abs(oracle));eng.count.maxdiff=max(eng.count.maxdiff,err);require(err<5e-10,"native RHS audit mismatch");++eng.count.oracle;}}return d;}
static State add(const State&s,const Deriv&d,double a){State q=s;for(size_t i=1;i+1<s.h.size();++i){q.h[i]+=a*d.dh[i];q.v[i]+=a*d.dv[i];}return q;}
static SimResult simulate(Engine&eng,const Mode&m,int n,double tmax,double courant,ofstream&wave,ofstream&diag){require(n>=17&&n<=513,"invalid grid");double z0=1.,dx=1./(n-1);int steps=(int)ceil(tmax/(courant*dx));double dt=tmax/steps;State s;s.h.resize(n);s.v.resize(n);for(int i=0;i<n;i++){double z=z0+i*dx;s.h[i]=exact(m,z,0);s.v[i]=exactv(m,z,0);}int saveEvery=max(1,steps/15);
 auto monitor=[&](int step,double t){vector<Row>rs;rs.reserve(n-2);for(int j=1;j<n-1;j++)rs.push_back(nodeRow(s,m,z0,dx,t,dt,j));vector<int>ids{ENERGY,FLUX,ERROR_SQUARED,ERROR_ABS,SOURCE,FORCING_POWER};auto v=eng.calc(rs,ids);size_t nodes=rs.size();double en=0,err=0,mx=0,src=0;for(size_t i=0;i<nodes;i++){en+=v[0*nodes+i]*dx;err+=v[2*nodes+i]*dx;mx=max(mx,v[3*nodes+i]);src+=v[5*nodes+i]*dx;}
 double fl=v[1*nodes],fr=v[1*nodes+nodes-1];diag<<m.name<<','<<n<<','<<step<<','<<t<<','<<en<<','<<sqrt(err)<<','<<mx<<','<<fl<<','<<fr<<','<<src<<'\n';
 if(step%saveEvery==0||step==steps){for(int j=0;j<n;j++){double z=z0+j*dx;wave<<m.name<<','<<n<<','<<step<<','<<t<<','<<z<<','<<s.h[j]<<','<<s.v[j]<<','<<exact(m,z,t)<<','<<s.h[j]-exact(m,z,t)<<'\n';}}};
 monitor(0,0);
 for(int step=0;step<steps;step++){double t=step*dt;Deriv k1=derivatives(eng,s,m,z0,dx,t,dt,step%max(1,steps/8)==0);State a=add(s,k1,.5*dt);impose(a,m,z0,dx,t+.5*dt);Deriv k2=derivatives(eng,a,m,z0,dx,t+.5*dt,dt,false);State b=add(s,k2,.5*dt);impose(b,m,z0,dx,t+.5*dt);Deriv k3=derivatives(eng,b,m,z0,dx,t+.5*dt,dt,false);State c=add(s,k3,dt);impose(c,m,z0,dx,t+dt);Deriv k4=derivatives(eng,c,m,z0,dx,t+dt,dt,false);
 for(int j=1;j<n-1;j++){s.h[j]+=dt/6*(k1.dh[j]+2*k2.dh[j]+2*k3.dh[j]+k4.dh[j]);s.v[j]+=dt/6*(k1.dv[j]+2*k2.dv[j]+2*k3.dv[j]+k4.dv[j]);require(isfinite(s.h[j])&&abs(s.h[j])<1e4&&isfinite(s.v[j]),"unstable integration or nonfinite state");}impose(s,m,z0,dx,t+dt);if((step+1)%saveEvery==0||step+1==steps)monitor(step+1,(step+1)*dt);}
 double e=0,mx=0;for(int j=1;j<n-1;j++){double x=s.h[j]-exact(m,z0+j*dx,tmax);e+=x*x*dx;mx=max(mx,abs(x));}return {sqrt(e),mx,0,0,0,tmax,n,steps};}
static void run(const fs::path&root, int n0, double tmax,double courant){require(n0>=17&&n0<=129&&n0%2==1&&tmax>.03&&tmax<=1&&courant>.1&&courant<=.6,"invalid run options");fs::create_directories(root/"examples");fs::create_directories(root/"results");Engine eng;
 {ofstream f(root/"examples/formula_registry.csv");f<<"id,expression,units,scope\n";for(auto&e:eng.expr)f<<e.name<<",\""<<e.expr<<"\","<<e.units<<","<<e.role<<'\n';}
 {ofstream f(root/"results/math_execution_inventory.csv");f<<"function,execution_owner,execution_api,purpose\n";for(auto&e:eng.expr)f<<e.name<<",paceval,paceval_dGetMultipleComputationsResultsExt,"<<e.role<<'\n';f<<"stateful_RK4_time_integration,C++_host,deterministic_four_stage_RK4,sequential_temporal_state\nexact_bessel_J2_reference,C++_host,std::cyl_bessel_j,initial_and_boundary_conditions_only\ninitial_and_boundary_reference,C++_host,analytic_reference,verification_inputs\nerror_norm_reduction,C++_host,deterministic_quadrature,reduction_of_paceval_error_values\nindependent_high_precision_check,Python_mpmath,independent_validation,not_paceval_graph\nnonlinear_gravity_and_gravitational_signal,NOT_IMPLEMENTED,requires_fully_physical_model,not_claimed\n";}
 ofstream wave(root/"examples/field_time_series.csv"),diag(root/"examples/energy_and_error_diagnostics.csv"),resid(root/"examples/spatial_operator_residuals.csv");wave<<"mode,n,step,t,z,h,velocity,exact_h,error\n";diag<<"mode,n,step,t,weighted_energy,l2_error,linf_error,flux_left_proxy,flux_right_proxy,source_power\n";resid<<"mode,n,z,discrete_acceleration,continuum_acceleration,residual,source\n";wave<<setprecision(16);diag<<setprecision(16);resid<<setprecision(16);
 vector<int>sizes{n0,2*n0-1,4*n0-3};vector<Mode>modes;for(int kind=0;kind<4;kind++)modes.push_back(makeMode(kind));
 ofstream conv(root/"examples/grid_convergence.csv");conv<<"mode,n,dx,steps,final_time,l2_error,linf_error,observed_order\n"<<setprecision(16);
 uint64_t scalarAudits=0;double largestError=0;
 for(const auto&m:modes){double last=0;for(int n:sizes){auto result=simulate(eng,m,n,tmax,courant,wave,diag);double dx=1./(n-1);double order=last>0?log(last/result.l2)/log(2.):0;conv<<m.name<<','<<n<<','<<dx<<','<<result.steps<<','<<tmax<<','<<result.l2<<','<<result.linf<<','<<order<<'\n';require(result.l2<.12,"large final-field error");largestError=max(largestError,result.l2);last=result.l2;
 // Sample the exact trajectory and evaluate the discrete operator with REAL paceval.
 vector<Row> rows;for(int i=1;i<n-1;i++){double z=1+i*dx,tt=.19;rows.push_back(row(z,exact(m,z-dx,tt),exact(m,z,tt),exact(m,z+dx,tt),exactv(m,z,tt),m,dx,tt,.01,-m.omega*m.omega*exact(m,z,tt)));}
 auto rr=eng.calc(rows,{m.delta>0?RHS_V2:RHS,SOURCE});for(int j=0;j<n-2;j++){double z=1+(j+1)*dx,target=-m.omega*m.omega*exact(m,z,.19);double res=rr[j]-target;if((j%max(1,(n-2)/50))==0)resid<<m.name<<','<<n<<','<<z<<','<<rr[j]<<','<<target<<','<<res<<','<<rr[rows.size()+j]<<'\n';++scalarAudits;}
 cerr<<"CASE "<<m.name<<" n="<<n<<" steps="<<result.steps<<" l2="<<result.l2<<" order="<<order<<'\n';}}
 wave.close();diag.close();resid.close();conv.close();
 // All 28 persistent graphs are actually executed in a multi-graph 3D study.
 ofstream survey(root/"examples/parameterized_kernel_surface.csv");survey<<"k,q,z,rhs_v1,rhs_v2,spatial_operator,source,energy_density,flux,drhs_dk,drhs_dq,version_delta,exact_zero,exact_mms\n"<<setprecision(16);
 vector<Row> batch;batch.reserve(256);auto flush=[&](){if(batch.empty())return;vector<int>ids;for(int i=0;i<NUM_GRAPHS;i++)ids.push_back(i);auto v=eng.calc(batch,ids);size_t n=batch.size();for(size_t i=0;i<n;i++){const Row&r=batch[i];survey<<r[5]<<','<<r[6]<<','<<r[0];for(int j: {RHS,RHS_V2,OP,SOURCE,ENERGY,FLUX,PARTIAL_K,PARTIAL_Q,VERSION_DELTA,EXACT_ZERO,EXACT_MMS})survey<<','<<v[size_t(j)*n+i];survey<<'\n';
 // independent direct RHS oracle for sparse surface samples
 if(i%31==0){double native=referenceRHS(r,false),got=v[size_t(RHS)*n+i];double d=abs(native-got)/(1+abs(native));eng.count.maxdiff=max(eng.count.maxdiff,d);require(d<1e-10,"independent full graph audit failed");++eng.count.oracle;}}
 batch.clear();};
 // Sweep the SAME fixed analytical probe field at different k and q values.
 // Disable its manufactured forcing in this study, otherwise the source term
 // cancels the very k/q dependence we want to visualize independently.
 for(int iz=0;iz<33;iz++){
   for(int iq=0;iq<21;iq++){
     for(int ik=0;ik<11;ik++){
       const double z=1.+iz/32.,k=.55+2.2*ik/10.,q=.1+1.1*iq/20.,dx=.015,t=.23;
       Mode m=makeMode(2);m.k=k;m.q=q;m.delta=.4;m.omega=2.05;m.forced=0;
       const double h=exact(m,z,t),vel=exactv(m,z,t);
       batch.push_back(row(z,exact(m,z-dx,t),h,exact(m,z+dx,t),vel,m,dx,t,.004,-m.omega*m.omega*h));
       if(batch.size()==256)flush();
     }
   }
 }
 flush();survey.close();
 // Fixed manufactured-mode high precision and exact-mode scalar API smoke check.
 {Mode m=makeMode(2);double z=1.4,t=.27,dx=.025;Row r=row(z,exact(m,z-dx,t),exact(m,z,t),exact(m,z+dx,t),exactv(m,z,t),m,dx,t,.002,exact(m,z,t));auto v=eng.calc({r},{EXACT_MMS,VEL_MMS,SOURCE,RHS});double x=exact(m,z,t);require(abs(v[0]-x)<1e-12,"paceval exact analytic formula mismatch");require(abs(v[1]-exactv(m,z,t))<1e-12,"velocity mismatch");require(abs(v[2]-source(m,z,t))<1e-12,"source mismatch");scalarAudits+=3;}
 {ofstream summary(root/"results/execution_summary.json");summary<<fixed<<setprecision(12)<<"{\n  \"project\": \"WP_044\",\n  \"model_scope\": \"idealized linear AdS5 conformal-coordinate Fourier-mode PDE\",\n  \"external_real_paceval_library\": true,\n  \"paceval_persistent_graphs\": "<<eng.expr.size()<<",\n  \"multi_graph_batch_calls\": "<<eng.count.calls<<",\n  \"paceval_batch_outputs\": "<<eng.count.outputs<<",\n  \"host_native_oracle_checks\": "<<eng.count.oracle<<",\n  \"sampled_continuum_operator_checks\": "<<scalarAudits<<",\n  \"max_oracle_scaled_difference\": "<<eng.count.maxdiff<<",\n  \"time_duration\": "<<tmax<<",\n  \"grid_sizes\": ["<<sizes[0]<<","<<sizes[1]<<","<<sizes[2]<<"],\n  \"mode_count\": "<<modes.size()<<",\n  \"parameter_surface_points\": "<<33*21*11<<",\n  \"max_final_L2_error\": "<<largestError<<",\n  \"gravitational_wave_detection\": false,\n  \"nonlinear_einstein_equations_solved\": false\n}\n";}
 cerr<<"ORIGINAL PACEVAL SUCCESS graphs="<<eng.expr.size()<<" batch_calls="<<eng.count.calls<<" outputs="<<eng.count.outputs<<" independent_cpp_audits="<<eng.count.oracle<<" maximum_scaled_difference="<<eng.count.maxdiff<<'\n';}
int main(int argc,char**argv){try{string out=".";int n0=25;double t=.6,courant=.30;for(int i=1;i<argc;i++){string arg=argv[i];auto v=[&](){require(++i<argc,"missing command option value");return string(argv[i]);};if(arg=="--out")out=v();else if(arg=="--n0")n0=stoi(v());else if(arg=="--time")t=stod(v());else if(arg=="--courant")courant=stod(v());else throw runtime_error("Unknown option "+arg);}run(fs::path(out),n0,t,courant);return 0;}catch(const exception&e){cerr<<"ERROR "<<e.what()<<'\n';return 2;}}
