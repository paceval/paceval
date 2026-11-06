// Braneworld v1.4: AdS5 linear tensor-mode wave operator in a moving-domain coordinate.
// Physical scope: a 1+1D spatial Fourier component, idealized homogeneous Neumann
// tensor junction BC and OPTIONAL phenomenological boundary source. NOT a full
// retarded localized 3D gravitational wave prediction or evidence for observable FTL.
// All core PDE right-hand-side algebra is evaluated with REUSED PACEVAL GRAPHS.
// Runtime dependencies: C++17 standard library and paceval SDK; no other libraries.
#include "paceval_runtime.hpp"
#include <algorithm>
#include <chrono>
#include <array>
#include <cmath>
#include <cstdlib>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <numeric>
#include <sstream>
#include <string>
#include <vector>

namespace {
struct Config {
 std::string lib="sdk/libpaceval.so",file="results/wave_v14.csv",mode="pulse";
 int ny=161;double maxy=3.0,dt=0.003,tmax=1.5;
 double rho0=0.1,w=0,k=0,pulse_start=0.15,pulse_duration=0.30,amp=0.04;
};
Config parse(int argc,char**argv){Config c;
 for(int i=1;i<argc;i++){
  const std::string a=argv[i];
  auto val=[&](){pv::require(i+1<argc,"missing argument after "+a);return std::string(argv[++i]);};
  if(a=="--lib")c.lib=val();else if(a=="--out")c.file=val();
  else if(a=="--mode")c.mode=val();else if(a=="--ny")c.ny=std::atoi(val().c_str());
  else if(a=="--maxy")c.maxy=std::stod(val());else if(a=="--dt")c.dt=std::stod(val());
  else if(a=="--tmax")c.tmax=std::stod(val());else if(a=="--rho0")c.rho0=std::stod(val());
  else if(a=="--w")c.w=std::stod(val());else if(a=="--k")c.k=std::stod(val());
  else if(a=="--pulse-start")c.pulse_start=std::stod(val());
  else if(a=="--pulse-duration")c.pulse_duration=std::stod(val());
  else if(a=="--amp")c.amp=std::stod(val());
  else throw std::runtime_error("unknown argument "+a);
 }
 pv::require(c.ny>=21 && c.maxy>0 && c.dt>0 && c.tmax>0 && c.rho0>0 && c.w>=-1,
             "invalid model/grid inputs");
 pv::require(c.mode=="pulse"||c.mode=="static"||c.mode=="moving-constant",
             "mode: pulse|static|moving-constant");
 const double dy=c.maxy/(c.ny-1);
 pv::require(c.dt<0.35*dy,"conservative explicit CFL condition violated; decrease --dt");
 return c;
}
struct Back {double ln_a,z,v;};
struct Fields {std::vector<double> u,q;};
class Waves {
 Config c_;pv::Runtime& p_;std::size_t hg_,du_,dq_;
 double dy_;
 std::vector<double> args_,du_values_,dq_values_;
 double H(double la) {return p_.eval(hg_,{la,c_.rho0,c_.w});}
 double aRate(double ln_a) {
  const double h=H(ln_a);return std::exp(ln_a)*h/std::sqrt(1+h*h);
 }
 Back at(double la) {
  if(c_.mode=="static")return {0,1,0};
  const double h=H(la);return {la,std::exp(-la),-h/std::sqrt(1+h*h)};
 }
 double integrateLogA(double la,double dt) {
  if(c_.mode=="static"||dt==0)return la;
  double k1=aRate(la),k2=aRate(la+0.5*dt*k1);
  double k3=aRate(la+0.5*dt*k2),k4=aRate(la+dt*k3);
  return la+dt*(k1+2*k2+2*k3+k4)/6;
 }
 double drive(double T)const {
  if(c_.mode!="pulse"||T<=c_.pulse_start||T>=c_.pulse_start+c_.pulse_duration)return 0;
  constexpr double pi=3.1415926535897932384626433832795;
  const double x=pi*(T-c_.pulse_start)/c_.pulse_duration;
  return c_.amp*std::sin(x)*std::sin(x);
 }
 Fields rhs(const Fields &f,Back b,double T) {
  const int n=c_.ny;
  Fields out;out.u.resize(n);out.q.resize(n);
  args_.resize(static_cast<std::size_t>(n)*11);
  const double j=drive(T);
  for(int i=0;i<n;++i) {
    double um=i?f.u[i-1]:f.u[1]-2*dy_*(j-b.v*f.q[0]);
    double up=i<n-1?f.u[i+1]:f.u[n-2];
    // One-sided derivative at y=0, centered in the graph everywhere else.
    double qm=i?f.q[i-1]:3*f.q[0]-3*f.q[1]+f.q[2];
    double qp=i<n-1?f.q[i+1]:f.q[n-2];
    auto base=static_cast<std::size_t>(i)*11;
    const double v[]={f.u[i],f.q[i],um,up,qm,qp,b.z+i*dy_,b.v,c_.k,dy_,0.0};
    for(int j2=0;j2<11;++j2)args_[base+j2]=v[j2];
  }
  p_.evaluate(du_,args_,11,du_values_);
  p_.evaluate(dq_,args_,11,dq_values_);
  out.u=du_values_;out.q=dq_values_;return out;
 }
 static Fields increment(const Fields &f,const Fields &k,double step) {
   Fields r=f;for(std::size_t i=0;i<r.u.size();++i){r.u[i]+=step*k.u[i];r.q[i]+=step*k.q[i];}
   return r;
 }
 double energy(const Fields& f,Back b)const {
  double en=0;
  for(int i=0;i<c_.ny;++i){
   const double u_y=(i==0?(f.u[1]-f.u[0])/dy_:
                     (i==c_.ny-1?(f.u[i]-f.u[i-1])/dy_:(f.u[i+1]-f.u[i-1])/(2*dy_)));
   const double dens=0.5*(f.q[i]*f.q[i]+u_y*u_y+c_.k*c_.k*f.u[i]*f.u[i])/
                     std::pow(b.z+i*dy_,3);
   en+=(i==0||i==c_.ny-1?.5:1.0)*dens*dy_;
  }
  return en;
 }
public:
 Waves(Config c,pv::Runtime& p):c_(std::move(c)),p_(p),dy_(c_.maxy/(c_.ny-1)) {
  const std::string r="(rho0*exp(((0-3)*(1+w))*t))", h="sqrt(("+r+"/6)*(2+("+r+"/6)))";
  hg_=p_.graph(h,"t rho0 w",3);
  // PDE in y=z-zbrane(T).  q := (partial_T h)|z, u := h(T,y).
  // u_T=q+v*u_y, q_T=u_yy-3*u_y/z-k^2*u+v*q_y.
  // ghost: u_y+v*q=J(T) at the moving brane y=0.
  const std::string vars="u q um up qm qp z v k dy damp";
  const std::string uy="((up-um)/(2*dy))",uyy="((up-(2*u)+um)/(dy*dy))";
  du_=p_.graph("(q+v*"+uy+")",vars,11);
  dq_=p_.graph("("+uyy+"-(3/z)*"+uy+"-k*k*u+v*((qp-qm)/(2*dy))-damp*q)",vars,11);
 }
 void run(){
  const int nt=static_cast<int>(std::ceil(c_.tmax/c_.dt));const double dt=c_.tmax/nt;
  Fields f;f.u.assign(c_.ny,0);f.q.assign(c_.ny,0);
  if(c_.mode!="pulse")std::fill(f.u.begin(),f.u.end(),1.0);
  std::ofstream file(c_.file);
  pv::require(file.good(),"cannot create output "+c_.file);
  file<<std::setprecision(17);
  file<<"T,a,z_brane,v,source,h_brane,h_yquart,h_yhalf,h_ythreequart,h_edge,energy,reference,error\n";
  double la=0,maxerror=0,maxabs=0;
  auto printRow=[&](int step){
    const double T=step*dt;Back b=at(la);
    const double ref=(c_.mode=="static"?std::cos(c_.k*T):(c_.mode=="moving-constant"?1.0:0.0));
    double error=0;if(c_.mode!="pulse")for(double x:f.u)error=std::max(error,std::abs(x-ref));
    maxerror=std::max(maxerror,error);for(double x:f.u)maxabs=std::max(maxabs,std::abs(x));
    file<<T<<','<<std::exp(b.ln_a)<<','<<b.z<<','<<b.v<<','<<drive(T)<<','
        <<f.u[0]<<','<<f.u[c_.ny/4]<<','<<f.u[c_.ny/2]<<','
        <<f.u[(3*c_.ny)/4]<<','<<f.u[c_.ny-1]<<','<<energy(f,b)<<','<<ref<<','<<error<<'\n';
  };
  printRow(0);
  for(int n=0;n<nt;++n){
    const double T=n*dt;const Back b0=at(la);
    double amid=integrateLogA(la,0.5*dt),aend=integrateLogA(la,dt);
    Back bm=at(amid),be=at(aend);
    const Fields k1=rhs(f,b0,T);
    const Fields k2=rhs(increment(f,k1,.5*dt),bm,T+.5*dt);
    const Fields k3=rhs(increment(f,k2,.5*dt),bm,T+.5*dt);
    const Fields k4=rhs(increment(f,k3,dt),be,T+dt);
    for(int i=0;i<c_.ny;++i){
      f.u[i]+=dt*(k1.u[i]+2*k2.u[i]+2*k3.u[i]+k4.u[i])/6;
      f.q[i]+=dt*(k1.q[i]+2*k2.q[i]+2*k3.q[i]+k4.q[i])/6;
      pv::require(std::isfinite(f.u[i])&&std::isfinite(f.q[i]),"wave solution nonfinite");
    }
    la=aend;
    if((n+1)%std::max(1,nt/150)==0 || n+1==nt)printRow(n+1);
  }
  std::cout<<std::setprecision(16)<<"WAVE_V14 mode="<<c_.mode<<" ny="<<c_.ny
           <<" dt="<<dt<<" tmax="<<c_.tmax<<" rho0="<<c_.rho0<<" k="<<c_.k
           <<" max_abs="<<maxabs<<" max_control_error="<<maxerror
           <<" brane_final="<<f.u[0]<<" energy_final="<<energy(f,at(la))
           <<" paceval_scalar="<<p_.scalarCalls()<<" paceval_batch="<<p_.batchCalls()
           <<" paceval_points="<<p_.evaluatedPoints()<<"\n";
 }
};
}
int main(int argc,char**argv){
 try{const Config c=parse(argc,argv);pv::Runtime runtime(c.lib);Waves(c,runtime).run();return 0;}
 catch(const std::exception&ex){std::cerr<<"ERROR v1.4: "<<ex.what()<<'\n';return 2;}
}
