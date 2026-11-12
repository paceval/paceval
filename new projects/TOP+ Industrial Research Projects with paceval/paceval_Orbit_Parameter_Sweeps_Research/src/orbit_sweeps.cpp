// WP-022 | Copyright (c) 2026 demonstration host.
// This file is original project-specific code. The official paceval_main.cpp/.h
// retain upstream copyright and license headers. Runtime shared library is
// deliberately external and must match the provided public SDK ABI.
//
// RESEARCH CONTRACT: simplified ECI Earth orbit propagator, point-mass gravity,
// J2 zonal correction, optional co-rotating exponential-density drag.
// All coordinates: km, velocities: km/s, times: seconds, accelerations: km/s^2.
// The host owns RK4, orbital states, scenario generation, numerical validation,
// event checks and CSV export. paceval owns all three accelerations through
// persistent reusable mathematical expression graphs. No ephemeris / SGP4 / high-
// fidelity operational orbit propagation is claimed.
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
namespace fs=std::filesystem;
namespace {
constexpr double MU=398600.4418;       // Earth GM, km^3/s^2 (declared model constant)
constexpr double RE=6378.137;          // Earth equatorial radius, km
constexpr double J2=1.08262668e-3;    // unnormalized J2, dimensionless
constexpr double OMEGA=7.2921150e-5; // Earth rotation, radians/s
constexpr double RHO400=4e-12;        // Illustrative density at 400 km, kg/m^3
constexpr double H=60.0;              // Fixed density scale height, km (illustrative)
constexpr double BALLISTIC=0.02;     // Cd*A/m, m^2/kg
constexpr double PI=3.14159265358979323846;
constexpr int NV=13;
constexpr double TOL=2e-9;
void check(bool condition,const std::string& why){if(!condition)throw std::runtime_error(why);}
using V=std::array<double,6>;
struct Parameters {double mu_scale=1,j2_scale=1,drag_scale=0,inc_deg=51.6;};
struct Scenario {const char* id; Parameters p;};
const std::array<Scenario,10> SCENARIOS{{
 {"two_body",{1,0,0,51.6}}, {"half_J2",{1,0.5,0,51.6}},
 {"nominal_J2",{1,1,0,51.6}}, {"high_J2",{1,1.5,0,51.6}},
 {"drag_only",{1,0,10,51.6}}, {"J2_drag",{1,1,1,51.6}},
 {"J2_drag_x10",{1,1,10,51.6}}, {"J2_drag_x100",{1,1,100,51.6}},
 {"gravity_low",{0.9999,1,0,51.6}}, {"gravity_high",{1.0001,1,0,51.6}}
}};
// Input variable ordering is part of the ABI. Never reorder one component.
const char* VARS="x y z vx vy vz mu re j2 ball rho scale omega";
std::string squared(const std::string& v){return "("+v+"*"+v+")";}
std::array<std::string,3> make_expressions(){
 const std::string r2="(x*x+y*y+z*z)";
 const std::string r="sqrt"+r2;
 const std::string invr3="(1/("+r2+"*"+r+"))";
 const std::string pre="(1.5*j2*mu*re*re/("+r2+"*"+r2+"*"+r+"))";
 const std::string zsq="(z*z/"+r2+")";
 const std::string vrx="(vx+omega*y)",vry="(vy-omega*x)",vrz="vz";
 const std::string speed="sqrt("+squared(vrx)+"+"+squared(vry)+"+"+squared(vrz)+")";
 // rho is density at the reference altitude (400 km). Since v is in km/s,
 // the SI aerodynamic acceleration converts to km/s^2 with factor 1000/2.
 const std::string drag="(500*ball*rho*scale*exp(-("+r+"-re-400)/60)*"+speed+")";
 const std::array<std::string,3> coord{{"x","y","z"}};
 const std::array<std::string,3> vr{{vrx,vry,vrz}};
 std::array<std::string,3> result;
 for(int a=0;a<3;++a){
  const std::string j2factor=(a==2?"(5*"+zsq+"-3)":"(5*"+zsq+"-1)");
  result[a]="(-mu*"+coord[a]+"*"+invr3+"+"+pre+"*"+coord[a]+"*"+j2factor+"-"+drag+"*"+vr[a]+")";
 }
 return result;
}
// Independent native right-hand side, intentionally not parsed from the
// paceval expression string. The equivalence is checked at every RK4 stage.
std::array<double,3> native_accel(const V& s,const Parameters& p){
 double x=s[0],y=s[1],z=s[2];
 double r2=x*x+y*y+z*z,r=std::sqrt(r2);
 check(r>RE+100,"Orbit left supported altitude domain");
 double mu=MU*p.mu_scale,j2=J2*p.j2_scale;
 double f=-mu/(r2*r);
 double j=1.5*j2*mu*RE*RE/(r2*r2*r), q=5*z*z/r2;
 double vx=s[3]+OMEGA*y,vy=s[4]-OMEGA*x,vz=s[5];
 double rel=std::hypot(std::hypot(vx,vy),vz);
 double rho=RHO400*std::exp(-(r-RE-400.0)/H);
 double d=500.0*BALLISTIC*rho*p.drag_scale*rel;
 return {f*x+j*x*(q-1)-d*vx,f*y+j*y*(q-1)-d*vy,f*z+j*z*(q-3)-d*vz};
}
class Engine{
 bool ready=false;std::array<PACEVAL_HANDLE,3> handles{{nullptr,nullptr,nullptr}};
public:
 Engine(){
  ready=paceval_InitializeLibrary(nullptr);check(ready,"paceval_InitializeLibrary failed");
  const auto expressions=make_expressions();
  for(int k=0;k<3;++k){
   handles[k]=paceval_CreateComputation(expressions[k].c_str(),NV,VARS,false,nullptr);
   check(handles[k]!=nullptr,"paceval graph creation returned null for component "+std::to_string(k));
   check(!paceval_GetIsError(handles[k]),"paceval graph creation error in component "+std::to_string(k));
  }
 }
 Engine(const Engine&)=delete;Engine& operator=(const Engine&)=delete;
 ~Engine(){for(auto h:handles)if(h)paceval_DeleteComputation(h);if(ready)paceval_FreeLibrary();}
 std::array<double,NV> vars(const V& s,const Parameters& p)const {
  return {{s[0],s[1],s[2],s[3],s[4],s[5],MU*p.mu_scale,RE,J2*p.j2_scale,BALLISTIC,RHO400,p.drag_scale,OMEGA}};
 }
 std::array<double,3> accel(const V& s,const Parameters& p,double& max_diff,std::size_t& count){
  auto v=vars(s,p);auto ref=native_accel(s,p);std::array<double,3> a{};
  for(int j=0;j<3;++j){
   a[j]=paceval_dGetComputationResult(handles[j],v.data(),nullptr,nullptr);
   check(!paceval_GetIsError(handles[j]),"paceval acceleration failure");
   check(std::isfinite(a[j]),"Nonfinite paceval acceleration");
   double delta=std::abs(a[j]-ref[j]);max_diff=std::max(max_diff,delta);
   check(delta<=TOL*(1+std::abs(ref[j])),"paceval/native acceleration disagreement");
   ++count;
  }
  return a;
 }
 // A separate 32-state batch verifies the exact same reusable components,
 // across different eccentric/anomaly-like states and parameter settings.
 void batch_audit(double& max_diff,std::size_t& count){
  constexpr int B=32;std::vector<double> input(B*NV),output(B);
  std::vector<int> errors(B,0);std::array<V,B> states;std::array<Parameters,B> ps;
  for(int k=0;k<B;++k){
   double th=2*PI*k/B, rad=RE+420.0+3*k;
   states[k]={{rad*std::cos(th),rad*std::sin(th),rad*0.1*std::sin(2*th),-7.3*std::sin(th),7.3*std::cos(th),0.8*std::cos(th)}};
   ps[k]={1.0,0.25+(k%5)*0.25,(k%4)*10.0,51.6};
   auto v=vars(states[k],ps[k]);std::copy(v.begin(),v.end(),input.begin()+k*NV);
  }
  for(int j=0;j<3;++j){
   std::fill(errors.begin(),errors.end(),0);
   const bool failed=paceval_dGetComputationResultExt(handles[j],input.data(),B,output.data(),nullptr,nullptr,errors.data());
   check(!failed,"paceval batch API returned error");
   for(int k=0;k<B;++k){
    check(errors[k]==PACEVAL_ERR_NO_ERROR,"paceval per-sample batch error");
    double ref=native_accel(states[k],ps[k])[j],delta=std::abs(output[k]-ref);
    max_diff=std::max(max_diff,delta);
    check(std::isfinite(output[k])&&delta<=TOL*(1+std::abs(ref)),"batch mismatch");
    ++count;
   }
  }
 }
};
double norm3(const V& s,int shift=0){return std::hypot(std::hypot(s[shift],s[shift+1]),s[shift+2]);}
double specific_energy(const V&s,const Parameters&p){
 double r=norm3(s),v=norm3(s,3),mu=MU*p.mu_scale;
 double p2=(3*s[2]*s[2]/(r*r)-1)/2;
 return v*v/2-mu/r+mu*J2*p.j2_scale*RE*RE*p2/(r*r*r);
}
double angular_h(const V&s){
 double hx=s[1]*s[5]-s[2]*s[4],hy=s[2]*s[3]-s[0]*s[5],hz=s[0]*s[4]-s[1]*s[3];
 return std::hypot(std::hypot(hx,hy),hz);
}
// Node longitude is not defined for equatorial orbits. Every scenario in this
// controlled pilot has a 51.6 deg inclined initial state, so atan2 is valid.
double node_deg(const V&s){
 double hx=s[1]*s[5]-s[2]*s[4],hy=s[2]*s[3]-s[0]*s[5];
 return std::atan2(hx,-hy)*180/PI;
}
V initial(const Parameters&p){
 double inc=p.inc_deg*PI/180.0,r=RE+500;
 double v=std::sqrt(MU*p.mu_scale/r);
 return {{r,0,0,0,v*std::cos(inc),v*std::sin(inc)}};
}
V rhs(Engine& e,const V&s,const Parameters&p,double& max_diff,std::size_t& count){
 auto a=e.accel(s,p,max_diff,count);
 return {{s[3],s[4],s[5],a[0],a[1],a[2]}};
}
V rhs_native(const V&s,const Parameters&p){
 auto a=native_accel(s,p);return {{s[3],s[4],s[5],a[0],a[1],a[2]}};
}
V add(const V&s,const V&k,double f){V a;for(int i=0;i<6;++i)a[i]=s[i]+f*k[i];return a;}
V rk4_paceval(Engine& e,const V&s,const Parameters&p,double dt,double& max_diff,std::size_t& count){
 auto a=rhs(e,s,p,max_diff,count);
 auto b=rhs(e,add(s,a,dt/2),p,max_diff,count);
 auto c=rhs(e,add(s,b,dt/2),p,max_diff,count);
 auto d=rhs(e,add(s,c,dt),p,max_diff,count);
 V out;for(int i=0;i<6;++i)out[i]=s[i]+dt*(a[i]+2*b[i]+2*c[i]+d[i])/6;
 return out;
}
V rk4_native(const V&s,const Parameters&p,double dt){
 auto a=rhs_native(s,p),b=rhs_native(add(s,a,dt/2),p);
 auto c=rhs_native(add(s,b,dt/2),p),d=rhs_native(add(s,c,dt),p);
 V out;for(int i=0;i<6;++i)out[i]=s[i]+dt*(a[i]+2*b[i]+2*c[i]+d[i])/6;
 return out;
}
struct Outcome{double altitude=0,raan=0,energy_change=0,max_pos=0,max_vel=0,max_energy_rel=0;};
Outcome run(Engine& e,const std::string& path,const Parameters& p,int steps,double dt,
            double& max_accel,std::size_t& count){
 V s=initial(p),reference=s;double e0=specific_energy(s,p),h0=angular_h(s);
 double emax=0,pmax=0,vmax=0;
 std::ofstream out(path);check(bool(out),"Cannot create "+path);
 out<<"step,time_s,x_km,y_km,z_km,vx_km_s,vy_km_s,vz_km_s,altitude_km,raan_deg,specific_energy_km2_s2,h_km2_s,position_difference_km,velocity_difference_km_s\n";
 out<<std::setprecision(17);
 for(int step=0;step<=steps;++step){
  double r=norm3(s),energy=specific_energy(s,p),dh=angular_h(s);
  double pos=std::hypot(std::hypot(s[0]-reference[0],s[1]-reference[1]),s[2]-reference[2]);
  double vel=std::hypot(std::hypot(s[3]-reference[3],s[4]-reference[4]),s[5]-reference[5]);
  pmax=std::max(pmax,pos);vmax=std::max(vmax,vel);
  emax=std::max(emax,std::abs((energy-e0)/e0));
  check(pos<1e-4 && vel<1e-7,"Trajectory differs from independent native integrator");
  // Only conservative (drag-free) cases may claim energy conservation.
  if(p.drag_scale==0){check(std::abs((energy-e0)/e0)<3e-6,"Conservative energy drift exceeded bound");
   if(p.j2_scale==0)check(std::abs((dh-h0)/h0)<3e-6,"Two-body angular momentum drift exceeded bound");}
  out<<step<<','<<step*dt;
  for(double val:s)out<<','<<val;
  out<<','<<r-RE<<','<<node_deg(s)<<','<<energy<<','<<dh<<','<<pos<<','<<vel<<'\n';
  if(step<steps){s=rk4_paceval(e,s,p,dt,max_accel,count);reference=rk4_native(reference,p,dt);}
 }
 check(bool(out),"Trajectory CSV writing failed");
 Outcome v;v.altitude=norm3(s)-RE;v.raan=node_deg(s);v.energy_change=specific_energy(s,p)-e0;
 v.max_pos=pmax;v.max_vel=vmax;v.max_energy_rel=emax;return v;
}
std::string dest(int argc,char**argv){
 std::string path="examples";
 for(int i=1;i<argc;++i){if(std::string(argv[i])=="--out"&&i+1<argc)path=argv[++i];
 else throw std::runtime_error("Usage: orbit_sweeps [--out OUTPUT_DIRECTORY]");}
 fs::create_directories(path);return path;
}
}
int main(int argc,char**argv){
 try{
  auto folder=dest(argc,argv);Engine engine;
  double max_accel=0;std::size_t nscalar=0,nbatch=0;
  engine.batch_audit(max_accel,nbatch);
  std::ofstream summary(folder+"/scenario_summary.csv");check(bool(summary),"Cannot open summary CSV");
  summary<<"scenario,mu_scale,j2_scale,drag_scale,final_altitude_km,final_raan_deg,energy_change_km2_s2,max_position_error_km,max_velocity_error_km_s,max_relative_energy_drift\n";
  summary<<std::setprecision(17);
  for(const auto& x:SCENARIOS){
   auto v=run(engine,folder+"/orbit_"+x.id+".csv",x.p,360,60,max_accel,nscalar);
   summary<<x.id<<','<<x.p.mu_scale<<','<<x.p.j2_scale<<','<<x.p.drag_scale<<','<<v.altitude<<','<<v.raan<<','<<v.energy_change<<','<<v.max_pos<<','<<v.max_vel<<','<<v.max_energy_rel<<'\n';
   std::cout<<x.id<<": altitude="<<v.altitude<<" km, RAAN="<<v.raan<<" deg\n";
  }
  check(bool(summary),"Summary writing failed");summary.close();
  std::ofstream grid(folder+"/parameter_surface.csv");check(bool(grid),"Cannot open sweep CSV");
  grid<<"i,j,j2_scale,drag_scale,final_altitude_km,final_raan_deg,energy_change_km2_s2\n";
  grid<<std::setprecision(17);
  for(int i=0;i<7;++i)for(int j=0;j<7;++j){
   Parameters p{1.0,1.5*i/6,100.0*j/6,51.6};
   auto v=run(engine,folder+"/scratch_surface.csv",p,60,60,max_accel,nscalar);
   grid<<i<<','<<j<<','<<p.j2_scale<<','<<p.drag_scale<<','<<v.altitude<<','<<v.raan<<','<<v.energy_change<<'\n';
  }
  grid.close();fs::remove(folder+"/scratch_surface.csv");
  // A two-body analytic circular-orbit oracle is deliberately independent
  // of both paceval and the native acceleration/integrator implementation.
  Parameters tb{1,0,0,51.6};V state=initial(tb);double n=std::sqrt(MU/std::pow(RE+500,3));
  double max_two_body_oracle=0;
  for(int step=0;step<240;++step){
   double t=step*60.0,r=RE+500.0,theta=n*t,inc=51.6*PI/180;
   V exact{{r*std::cos(theta),r*std::sin(theta)*std::cos(inc),r*std::sin(theta)*std::sin(inc),
    -r*n*std::sin(theta),r*n*std::cos(theta)*std::cos(inc),r*n*std::cos(theta)*std::sin(inc)}};
   double error=0;for(int k=0;k<3;++k)error+=std::pow(state[k]-exact[k],2);
   max_two_body_oracle=std::max(max_two_body_oracle,std::sqrt(error));
   state=rk4_paceval(engine,state,tb,60,max_accel,nscalar);
  }
  check(max_two_body_oracle<0.1,"Two-body analytical oracle discrepancy exceeded 100 m");
  std::ofstream audit(folder+"/audit_summary.txt");
  audit<<std::setprecision(17)<<"Research status: SDK executed; all checks passed\n"
       <<"Reusable paceval graphs: 3\n"
       <<"Scalar acceleration component audits: "<<nscalar<<"\n"
       <<"Batch component audits: "<<nbatch<<"\n"
       <<"Largest absolute component discrepancy (km/s^2): "<<max_accel<<"\n"
       <<"Circular two-body analytic position oracle max difference (km): "<<max_two_body_oracle<<"\n"
       <<"Scenario propagation: 10 scenarios, 6 hours, fixed RK4 60 s\n"
       <<"Parameter surface: 49 scenarios, 1 hour, fixed RK4 60 s\n"
       <<"Atmosphere: fixed-scale exponential density; not validated operational model\n";
  check(bool(audit),"Audit summary write failed");
  std::cout<<"PASS graphs=3 scalar_audits="<<nscalar<<" batch_audits="<<nbatch
           <<" maximum_component_difference="<<max_accel
           <<" analytic_position_error_km="<<max_two_body_oracle<<"\n";
  return 0;
 }catch(const std::exception& e){std::cerr<<"FAIL: "<<e.what()<<'\n';return 1;}
}
