// Braneworld v1.4b: finite-difference, 2D planar pulse propagator in AdS5.
// Axis x>=0 is ONE brane coordinate (uniform in other two brane directions).
// This is NOT a fully localized 3+1D tensor source, observational GW waveform,
// or proof that the predicted geometric earliest-null front is detectable.
// Reusable paceval graphs evaluate ALL interior/moving-boundary PDE RHS values.
// Dependencies: C++17 standard library and paceval shared library ONLY.
#include "paceval_runtime.hpp"
#include <algorithm>
#include <cmath>
#include <cstdlib>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <string>
#include <vector>
namespace {
struct Opt {
 std::string lib="sdk/libpaceval.so",file="results/planar_v14.csv",mode="pulse";
 int nx=61,ny=61; double xmax=2,ymax=2,dt=.004,tmax=1.7;
 double rho0=10,w=-.5,src_start=.02,src_duration=.10,src_radius=.12,amplitude=.04,receiver=1;
};
Opt read(int argc,char**argv) {
 Opt c;
 for(int i=1;i<argc;++i) {
  const std::string a=argv[i];auto v=[&](){pv::require(i+1<argc,"missing value "+a);return std::string(argv[++i]);};
  if(a=="--lib")c.lib=v();else if(a=="--out")c.file=v();
  else if(a=="--nx")c.nx=std::atoi(v().c_str());else if(a=="--ny")c.ny=std::atoi(v().c_str());
  else if(a=="--dt")c.dt=std::stod(v());else if(a=="--tmax")c.tmax=std::stod(v());
  else if(a=="--xmax")c.xmax=std::stod(v());else if(a=="--ymax")c.ymax=std::stod(v());
  else if(a=="--rho0")c.rho0=std::stod(v());else if(a=="--w")c.w=std::stod(v());
  else if(a=="--mode")c.mode=v();else if(a=="--receiver")c.receiver=std::stod(v());
  else if(a=="--src-radius")c.src_radius=std::stod(v());
  else if(a=="--src-start")c.src_start=std::stod(v());
  else if(a=="--src-duration")c.src_duration=std::stod(v());
  else if(a=="--amp")c.amplitude=std::stod(v());
  else throw std::runtime_error("Unknown option "+a);
 }
 pv::require(c.nx>=9&&c.ny>=9&&c.xmax>0&&c.ymax>0&&c.tmax>0&&c.dt>0,"invalid mesh");
 pv::require(c.rho0>0&&c.w>=-1&&c.w<=1,"invalid brane");
 pv::require(c.src_radius>0&&c.src_radius<c.receiver&&c.receiver<c.xmax,"invalid source/receiver");
 pv::require(c.mode=="pulse"||c.mode=="constant","mode pulse or constant");
 // Conservative dt required for 2D plus moving-grid advection.
 pv::require(c.dt<0.14*std::min(c.xmax/(c.nx-1),c.ymax/(c.ny-1)),"2D CFL guard: reduce --dt");
 return c;
}
struct BG{double la,z,v,Q;};
struct State{std::vector<double> u,q;};
class Experiment {
 Opt c_;pv::Runtime&p_;size_t h_,g1_,g2_;
 int n_;double dx_,dy_;
 std::vector<double> packed_,f1_,f2_;
 double H(double la){return p_.eval(h_,{la,c_.rho0,c_.w});}
 double rate(double la){const double hh=H(la);return std::exp(la)*hh/std::sqrt(1+hh*hh);}
 double logaStep(double la,double dt){
   const double k1=rate(la),k2=rate(la+dt*k1*.5),k3=rate(la+dt*k2*.5),k4=rate(la+dt*k3);
   return la+dt*(k1+2*k2+2*k3+k4)/6;
 }
 BG bg(double la){const double hh=H(la),Q=std::sqrt(1+hh*hh);
            return {la,std::exp(-la),-hh/Q,Q};}
 double drive(double T,double x)const {
  if(c_.mode!="pulse"||T<=c_.src_start||T>=c_.src_start+c_.src_duration||x>=c_.src_radius)return 0;
  constexpr double PI=3.14159265358979323846264338;
  const double a=std::sin(PI*(T-c_.src_start)/c_.src_duration);
  const double b=std::cos(.5*PI*x/c_.src_radius);
  return c_.amplitude*a*a*b*b;
 }
 int index(int ix,int iy)const{return ix*c_.ny+iy;}
 State rhs(const State& a,BG b,double T){
   packed_.resize(static_cast<std::size_t>(n_)*12);
   for(int ix=0;ix<c_.nx;++ix)for(int iy=0;iy<c_.ny;++iy){
       const int idx=index(ix,iy);
       const double u=a.u[idx],q=a.q[idx];
       const double x=ix*dx_;
       const double jm=drive(T,x);
       const double um=iy? a.u[idx-1] : a.u[index(ix,1)]-2*dy_*(jm-b.v*q);
       const double up=iy<c_.ny-1?a.u[idx+1]:a.u[index(ix,c_.ny-2)];
       const double qm=iy?a.q[idx-1]:3*q-3*a.q[index(ix,1)]+a.q[index(ix,2)];
       const double qp=iy<c_.ny-1?a.q[idx+1]:a.q[index(ix,c_.ny-2)];
       const double xm=ix?a.u[index(ix-1,iy)]:a.u[index(1,iy)];
       const double xp=ix<c_.nx-1?a.u[index(ix+1,iy)]:a.u[index(c_.nx-2,iy)];
       const double values[]={u,q,um,up,qm,qp,b.z+iy*dy_,b.v,dy_,xm,xp,dx_};
       const size_t base=static_cast<size_t>(idx)*12;
       for(int k=0;k<12;++k)packed_[base+k]=values[k];
   }
   p_.evaluate(g1_,packed_,12,f1_);
   p_.evaluate(g2_,packed_,12,f2_);
   return {f1_,f2_};
 }
 static State add(const State&a,const State&b,double dt){
    State out=a;for(std::size_t i=0;i<a.u.size();++i){out.u[i]+=dt*b.u[i];out.q[i]+=dt*b.q[i];}
    return out;
 }
public:
 Experiment(Opt c,pv::Runtime&p):c_(c),p_(p),n_(c.nx*c.ny),dx_(c.xmax/(c.nx-1)),dy_(c.ymax/(c.ny-1)){
    const std::string r="(rho0*exp(((0-3)*(1+w))*t))";
    h_=p_.graph("sqrt(("+r+"/6)*(2+("+r+"/6)))","t rho0 w",3);
    const std::string vars="u q um up qm qp z v dy xm xp dx";
    const std::string uy="((up-um)/(2*dy))";
    g1_=p_.graph("(q+v*"+uy+")",vars,12);
    g2_=p_.graph("((up-2*u+um)/(dy*dy)+(xp-2*u+xm)/(dx*dx)-(3/z)*"+uy+"+v*((qp-qm)/(2*dy)))",vars,12);
 }
 void run(){
   const int nt=static_cast<int>(std::ceil(c_.tmax/c_.dt)),rec=static_cast<int>(std::round(c_.receiver/dx_));
   const double dt=c_.tmax/nt;
   const double pos=rec*dx_;
   State s;s.u.assign(n_,c_.mode=="constant"?1:0);s.q.assign(n_,0);
   std::ofstream f(c_.file);pv::require(f.good(),"cannot write "+c_.file);
   f<<std::setprecision(17);
   f<<"T,a,z_brane,v,brane_comoving_x,source_at0,receiver_x,field_source,field_receiver,"
       "field_receiver_deeper,field_xhalf,field_xmax,maxabs_field\n";
   double la=0,photon_x=0,maxconsterr=0,maxabs=0;
   auto output=[&](int it){
     const BG b=bg(la);const double T=it*dt;
     double mx=0;for(double u:s.u)mx=std::max(mx,std::abs(u));maxabs=std::max(maxabs,mx);
     if(c_.mode=="constant")for(double u:s.u)maxconsterr=std::max(maxconsterr,std::abs(u-1));
     f<<T<<','<<std::exp(la)<<','<<b.z<<','<<b.v<<','<<photon_x<<','<<drive(T,0)<<','<<pos<<','
      <<s.u[index(0,0)]<<','<<s.u[index(rec,0)]<<','<<s.u[index(rec,c_.ny/4)]<<','
      <<s.u[index(c_.nx/2,0)]<<','<<s.u[index(c_.nx-1,0)]<<','<<mx<<'\n';
   };
   output(0);
   for(int i=0;i<nt;++i){
     BG b0=bg(la);const double lam=logaStep(la,dt/2),lan=logaStep(la,dt);
     BG bm=bg(lam),bn=bg(lan);
     const auto k1=rhs(s,b0,i*dt);
     const auto k2=rhs(add(s,k1,dt/2),bm,(i+.5)*dt);
     const auto k3=rhs(add(s,k2,dt/2),bm,(i+.5)*dt);
     const auto k4=rhs(add(s,k3,dt),bn,(i+1)*dt);
     for(int j=0;j<n_;++j){
       s.u[j]+=dt*(k1.u[j]+2*k2.u[j]+2*k3.u[j]+k4.u[j])/6;
       s.q[j]+=dt*(k1.q[j]+2*k2.q[j]+2*k3.q[j]+k4.q[j])/6;
       pv::require(std::isfinite(s.u[j])&&std::isfinite(s.q[j]),"nonfinite 2D solution");
     }
     photon_x+=dt*((1/b0.Q)+4*(1/bm.Q)+(1/bn.Q))/6;
     la=lan;
     if((i+1)%std::max(1,nt/250)==0 || i==nt-1)output(i+1);
   }
   std::cout<<std::setprecision(16)<<"PLANAR_V14 mode="<<c_.mode<<" nx="<<c_.nx
        <<" ny="<<c_.ny<<" dt="<<dt<<" receiver_x="<<pos<<" max_const_error="<<maxconsterr
        <<" max_abs_field="<<maxabs<<" receiver_final="<<s.u[index(rec,0)]
        <<" photon_x="<<photon_x<<" paceval_points="<<p_.evaluatedPoints()
        <<" paceval_batch="<<p_.batchCalls()<<"\n";
 }
};
}
int main(int argc,char**argv){
 try{Opt c=read(argc,argv);pv::Runtime p(c.lib);Experiment(c,p).run();return 0;}
 catch(const std::exception&ex){std::cerr<<"ERROR v1.4 planar: "<<ex.what()<<'\n';return 2;}
}
