// Braneworld v1.5: numerically stable, dimensional, IDEALIZED GEOMETRIC shortcut
// study using a positive pair-integral, with illustrative GW170817 delay scenarios.
// This code DOES NOT infer an empirical AdS-radius bound: it neither propagates
// a localized retarded tensor wave nor models GW/GRB intrinsic emission physics.
// H, stable pair-integrand, and delay chi-square are reusable paceval graphs.
// Only C++17 standard library and paceval (no external numerical libraries).
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
constexpr double speed_km_s=299792.458;
constexpr double mega_parsec_km=3.0856775814913673e19;
struct Config {
 std::string lib="sdk/libpaceval.so", out="results/cosmology_v15.csv";
 unsigned n=500, count=15; bool richardson=false;
 double ellmin=0.01,ellmax=0.535,distance=40.0;
 double h0=67.4, omega_m=0.315,omega_r=9.2e-5;
 double obs_delay=1.74,sigma=0.05,intrinsic_max=10.0;
};
Config parse(int argc,char**argv){Config c;
 for(int i=1;i<argc;++i){
  const std::string a=argv[i];
  auto val=[&](){pv::require(i+1<argc,"missing argument after "+a);return std::string(argv[++i]);};
  if(a=="--lib")c.lib=val();else if(a=="--out")c.out=val();
  else if(a=="--richardson")c.richardson=true;
  else if(a=="--n")c.n=static_cast<unsigned>(std::strtoul(val().c_str(),nullptr,10));
  else if(a=="--count")c.count=static_cast<unsigned>(std::strtoul(val().c_str(),nullptr,10));
  else if(a=="--ellmin")c.ellmin=std::stod(val());
  else if(a=="--ellmax")c.ellmax=std::stod(val());
  else if(a=="--distance")c.distance=std::stod(val());
  else if(a=="--h0")c.h0=std::stod(val());
  else if(a=="--om")c.omega_m=std::stod(val());
  else if(a=="--or")c.omega_r=std::stod(val());
  else if(a=="--obs")c.obs_delay=std::stod(val());
  else if(a=="--sigma")c.sigma=std::stod(val());
  else if(a=="--intrinsic-max")c.intrinsic_max=std::stod(val());
  else throw std::runtime_error("unknown argument "+a);
 }
 pv::require(c.n>=16&&c.n<=8000&&c.count>=1&&c.count<=10000,"invalid grid size");
 pv::require(c.ellmin>0&&c.ellmax>=c.ellmin&&c.distance>0&&c.h0>0,
             "nonpositive length/rate");
 pv::require(c.omega_m>=0&&c.omega_r>=0&&c.omega_m+c.omega_r<=1,
             "nonphysical density fractions");
 pv::require(c.sigma>0&&c.intrinsic_max>=0,"invalid lag uncertainty");
 return c;
}
struct Result {
 double ell,a_emit,z_emit, advance_sec, xgap, S, D, Hbar_today, derivative;
 double chi_fixed,chi_nonneg,chi_free,implied_intrinsic,profile_nonneg;
 double error_estimate=0; unsigned nused=0;
};
class Cosmo {
 Config c_;pv::Runtime&pv_;
 size_t hg_,kg_,cg_;
 double rho0_;
 std::vector<double> hs_;
 double H(double a) {return pv_.eval(hg_,{a,rho0_,c_.omega_m,c_.omega_r});}
 double deriv(double a){return a*a*H(a);}
 double advanceA(double a,double h) {
   const double k1=deriv(a),k2=deriv(a+.5*h*k1),k3=deriv(a+.5*h*k2),k4=deriv(a+h*k3);
   return a+(h/6)*(k1+2*k2+2*k3+k4);
 }
public:
 Cosmo(Config c,pv::Runtime& pv):c_(c),pv_(pv) {
   const std::string r="(r0*(om/(a*a*a)+orr/(a*a*a*a)+(1-om-orr)))";
   hg_=pv_.graph("sqrt(("+r+"/6)*(2+("+r+"/6)))","a r0 om orr",4);
   const std::string Q1="sqrt(1+h1*h1)",Q2="sqrt(1+h2*h2)";
   const std::string dif="((h1*"+Q2+")-(h2*"+Q1+"))";
   // Exact nonnegative kernel cosh(asinh(h1)-asinh(h2))-1.
   kg_=pv_.graph("( ("+dif+"*"+dif+") / ("+Q1+"*"+Q2+"-h1*h2+1) )","h1 h2",2);
   cg_=pv_.graph("((obs-pred-intrinsic)*(obs-pred-intrinsic)/(sigma*sigma))",
                 "obs pred intrinsic sigma",4);
 }
 Result calculate(double ell){
   const double hbar0=ell*c_.h0/speed_km_s;
   rho0_=(6*hbar0*hbar0)/(1+std::sqrt(1+hbar0*hbar0)); // exactly tuned H_today
   const double D=c_.distance/ell;
   const double dx=D/c_.n;
   double a=1.0,T=0,Z=0;
   hs_.clear();hs_.reserve(c_.n);
   for(unsigned i=0;i<c_.n;++i){
     const double amid=advanceA(a,-.5*dx);
     const double hm=H(amid);
     hs_.push_back(hm);
     T+=dx*std::sqrt(1+hm*hm);
     Z+=dx*hm;
     a=advanceA(a,-dx);
     pv::require(a>0 && std::isfinite(a),"scale factor integration failed");
   }
   double Ksum=0,compensation=0;
   std::vector<double> pack;pack.reserve(2*1024);std::vector<double> result;
   auto flush=[&](){
       if(pack.empty())return;
       pv_.evaluate(kg_,pack,2,result,512);
       for(double value:result){
          pv::require(value>=-1e-25,"negative stable pair kernel");
          const double y=std::max(0.0,value)-compensation;
          const double t=Ksum+y;compensation=(t-Ksum)-y;Ksum=t;
       }
       pack.clear();
   };
   for(unsigned i=0;i<c_.n;++i)for(unsigned j=0;j<i;++j){
       pack.push_back(hs_[i]);pack.push_back(hs_[j]);
       if(pack.size()>=2048)flush();
   }
   flush();
   const double S=2*dx*dx*Ksum; // T^2-Z^2-D^2 = double integral of K
   const double gap=S/(std::sqrt(D*D+S)+D); // stable positive bulk reach excess
   const double H_end=H(1.0),Q_end=std::sqrt(1+H_end*H_end);
   const double deriv_bulk=(T*Q_end-Z*H_end)/(D+gap);
   pv::require(deriv_bulk>0,"noncausal bulk distance derivative");
   // First-order inverse receiver-root expansion in tiny gap; a(receiver)=1.
   // Error is O(gap^2) and high-precision residual checks live OUTSIDE this C++.
   const double advance_sec=gap/deriv_bulk *ell*mega_parsec_km/speed_km_s;
   const double implied=c_.obs_delay-advance_sec;
   const double nonneg=std::max(0.0,std::min(c_.intrinsic_max,implied));
   // Unrestricted nuisance profile exactly absorbs observed delay, hence no bound.
   const double chis[3]={pv_.eval(cg_,{c_.obs_delay,advance_sec,0,c_.sigma}),
                         pv_.eval(cg_,{c_.obs_delay,advance_sec,nonneg,c_.sigma}),
                         pv_.eval(cg_,{c_.obs_delay,advance_sec,implied,c_.sigma})};
   pv::require(std::isfinite(advance_sec)&&advance_sec>=0,"invalid geometric advance");
   return {ell,a,1/a-1,advance_sec,gap,S,D,hbar0,deriv_bulk,
           chis[0],chis[1],chis[2],implied,nonneg,0.0,c_.n};
 }
 void run(){
   std::ofstream out(c_.out);pv::require(out.good(),"cannot write CSV "+c_.out);
   out<<std::setprecision(17);
   out<<"ell_Mpc,a_emission,z_emission,geometric_advance_seconds,x_gap,S,D_dimensionless,Hbar_today,"
         "bulk_distance_derivative,chi2_fixed_intrinsic0,chi2_intrinsic_0_to_max,"
         "chi2_intrinsic_unrestricted,unrestricted_implied_intrinsic_sec,profiled_intrinsic_sec,richardson_error_estimate_seconds,N_used\n";
   Result last{};
   for(unsigned i=0;i<c_.count;++i){
      const double f=c_.count==1?1.0:double(i)/(c_.count-1);
      const double ell=c_.ellmin*std::pow(c_.ellmax/c_.ellmin,f);
      Result r;
      if(c_.richardson){
         const unsigned original=c_.n;
         pv::require(original>=32 && original%2==0,"richardson requires even n>=32");
         c_.n=original/2;const Result coarse=calculate(ell);
         c_.n=original;r=calculate(ell);
         r.error_estimate=std::abs(r.advance_sec-coarse.advance_sec)/3.0;
         r.advance_sec=(4*r.advance_sec-coarse.advance_sec)/3.0;
         r.implied_intrinsic=c_.obs_delay-r.advance_sec;
         r.profile_nonneg=std::max(0.0,std::min(c_.intrinsic_max,r.implied_intrinsic));
         r.chi_fixed=pv_.eval(cg_,{c_.obs_delay,r.advance_sec,0,c_.sigma});
         r.chi_nonneg=pv_.eval(cg_,{c_.obs_delay,r.advance_sec,r.profile_nonneg,c_.sigma});
         r.chi_free=pv_.eval(cg_,{c_.obs_delay,r.advance_sec,r.implied_intrinsic,c_.sigma});
         r.nused=original;
      } else r=calculate(ell);
      last=r;
      out<<r.ell<<','<<r.a_emit<<','<<r.z_emit<<','<<r.advance_sec<<','<<r.xgap<<','
         <<r.S<<','<<r.D<<','<<r.Hbar_today<<','<<r.derivative<<','<<r.chi_fixed<<','
         <<r.chi_nonneg<<','<<r.chi_free<<','<<r.implied_intrinsic<<','<<r.profile_nonneg<<','<<r.error_estimate<<','<<r.nused<<'\n';
      std::cout<<std::setprecision(13)<<"COSMO_V15 ell_Mpc="<<r.ell
               <<" advance_seconds="<<r.advance_sec<<" est_error_seconds="<<r.error_estimate<<" chi2_intrinsic0="<<r.chi_fixed
               <<" chi2_intrinsic_0to"<<c_.intrinsic_max<<"="<<r.chi_nonneg
               <<" chi2_intrinsic_free="<<r.chi_free<<"\n";
   }
   std::cout<<"PACEVAL_V15 scalar_calls="<<pv_.scalarCalls()<<" batch_calls="<<pv_.batchCalls()
            <<" evaluated_points="<<pv_.evaluatedPoints()<<" distance_Mpc="<<c_.distance
            <<" grid_N="<<c_.n<<" obs_lag_sec="<<c_.obs_delay<<" sigma_sec="<<c_.sigma<<'\n';
   std::cout<<"WARNING: idealized geometric maximum, NOT a propagated GW signal or physical radius bound.\n";
 }
};
}
int main(int argc,char** argv){
  try{Config c=parse(argc,argv);pv::Runtime engine(c.lib);Cosmo(c,engine).run();return 0;}
  catch(const std::exception&ex){std::cerr<<"ERROR v1.5: "<<ex.what()<<'\n';return 2;}
}
