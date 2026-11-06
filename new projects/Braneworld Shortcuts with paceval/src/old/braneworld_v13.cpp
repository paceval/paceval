// Braneworld Shortcuts v1.3: independent C++17 numerical reproduction of Python v1.2.
// Research demonstrator: idealized pure AdS5 FLRW-brane null curves, no physical FTL claim.
// SPDX-License-Identifier: MIT (host demonstrator only; paceval SDK is separately licensed)
#include <algorithm>
#include <array>
#include <chrono>
#include <cmath>
#include <cstdint>
#include <cstdlib>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <limits>
#include <stdexcept>
#include <string>
#include <vector>
#include "../sdk/paceval_main.h"
#if defined(_WIN32)
#  define WIN32_LEAN_AND_MEAN
#  include <windows.h>
#else
#  include <dlfcn.h>
#endif

namespace bw {
using Vec = std::array<double,4>; // T,z,x,tau
inline void demand(bool v,const std::string &what) { if (!v) throw std::runtime_error(what); }
inline double rho(double t,double rho0,double w) { return rho0*std::exp(-3.0*(1.0+w)*t); }
inline double nativeH(double t,double rho0,double w) {
    double r=rho(t,rho0,w), u=r/6.0;
    return std::sqrt(u*(2.0+u)); // cancellation resistant: H^2=rho/3+rho^2/36
}
class Paceval {
#if defined(_WIN32)
    HMODULE lib_ = nullptr;
#else
    void* lib_ = nullptr;
#endif
    using Init=bool(*)(const char*); using Free=bool(*)();
    using Create=void*(*)(const char*,unsigned long,const char*,bool,void*);
    using Delete=bool(*)(void*); using Scalar=double(*)(void*,double*,double*,double*);
    using Batch=bool(*)(void*,double*,unsigned long,double*,double*,double*,int*);
    using Error=bool(*)(void*);
    Init init_=nullptr; Free free_=nullptr; Create create_=nullptr; Delete del_=nullptr;
    Scalar scalar_=nullptr; Batch batch_=nullptr; Error err_=nullptr;
    void* h_=nullptr;
    std::uint64_t calls_=0, batchCalls_=0;
    std::vector<double> hGrid_;
    double halfstep_=0,cachedRho_=-1,cachedW_=42;
    void* symbol(const char* raw) {
       const std::string s(raw);
       const std::string n1="pacevalLibrary_"+s, n2="paceval_"+s;
#if defined(_WIN32)
       void* p=reinterpret_cast<void*>(GetProcAddress(lib_,n1.c_str()));
       if(!p) p=reinterpret_cast<void*>(GetProcAddress(lib_,n2.c_str()));
#else
       void* p=dlsym(lib_,n1.c_str()); if(!p) p=dlsym(lib_,n2.c_str());
#endif
       demand(p!=nullptr,"missing paceval symbol: "+s);return p;
    }
public:
    explicit Paceval(const std::string& path,bool tinc=false) {
#if defined(_WIN32)
       lib_=LoadLibraryA(path.c_str());
       demand(lib_!=nullptr,"Cannot LoadLibrary paceval DLL: "+path);
#else
       lib_=dlopen(path.c_str(),RTLD_NOW|RTLD_LOCAL);
       demand(lib_!=nullptr,std::string("Cannot dlopen paceval: ")+(lib_?"":dlerror()));
#endif
       init_=reinterpret_cast<Init>(symbol("Initialize"));
       free_=reinterpret_cast<Free>(symbol("Free"));
       create_=reinterpret_cast<Create>(symbol("CreateComputation"));
       del_=reinterpret_cast<Delete>(symbol("DeleteComputation"));
       scalar_=reinterpret_cast<Scalar>(symbol("dGetComputationResult"));
       batch_=reinterpret_cast<Batch>(symbol("dGetComputationResultExt"));
       err_=reinterpret_cast<Error>(symbol("GetIsError"));
       demand(init_(nullptr),"paceval Initialize failed");
       // Variable ordering is fixed: t, rho0, w. A single reused execution graph
       // computes the Friedmann Hubble parameter at each RK4 stage.
       const std::string r="(rho0*exp(((0-3)*(1+w))*t))";
       const std::string u="("+r+"/6)";
       const std::string expression="sqrt(("+u+")*(2+("+u+")))";
       h_=create_(expression.c_str(),3,"t rho0 w",tinc,nullptr);
       demand(h_ && !err_(h_),"paceval CreateComputation failed for H(t,rho0,w)");
    }
    ~Paceval(){if(h_&&del_)del_(h_);if(init_&&free_)free_();
#if defined(_WIN32)
       if(lib_)FreeLibrary(lib_);
#else
       if(lib_)dlclose(lib_);
#endif
    }
    void prime(double rho0,double w,unsigned steps,double tmax){
       if(!hGrid_.empty()&&cachedRho_==rho0&&cachedW_==w
               && halfstep_==tmax/(2.0*steps))return;
       halfstep_=tmax/(2.0*steps);cachedRho_=rho0;cachedW_=w;
       const size_t n=2*size_t(steps)+1;
       hGrid_.assign(n,0);
       const unsigned long chunk=512;
       std::vector<double> input(chunk*3),out(chunk),lo(chunk),hi(chunk);
       std::vector<int> error(chunk);
       for(size_t offset=0;offset<n;offset+=chunk){
          const unsigned long m=(unsigned long)std::min(size_t(chunk),n-offset);
          for(unsigned long j=0;j<m;++j){
             input[3*j]=(offset+j)*halfstep_;
             input[3*j+1]=rho0;input[3*j+2]=w;
          }
          (void)batch_(h_,input.data(),m,out.data(),lo.data(),hi.data(),error.data());
          ++batchCalls_;
          for(unsigned long j=0;j<m;++j){
             demand(error[j]==0&&std::isfinite(out[j])&&out[j]>0,"paceval grid batch error");
             hGrid_[offset+j]=out[j];
          }
       }
    }
    double hubble(double t,double rho0,double w) {
       if(!hGrid_.empty()&&rho0==cachedRho_&&w==cachedW_&&t>=0){
           const size_t i=(size_t)std::llround(t/halfstep_);
           if(i<hGrid_.size()&&std::abs(t-i*halfstep_)<1e-10)
              return hGrid_[i];
       }
       double v[3]={t,rho0,w},lo=0,hi=0;
       const double h=scalar_(h_,v,&lo,&hi); ++calls_;
       demand(std::isfinite(h)&&h>0&&!err_(h_),"paceval scalar evaluation failed");return h;
    }
    void verifyBatch() {
       const unsigned long count=256;
       std::vector<double> vars(count*3),out(count),lo(count),hi(count);
       std::vector<int> errors(count);
       for(unsigned long i=0;i<count;++i) {
           vars[3*i]=4.0*i/255.0; vars[3*i+1]= (i%3==0?0.1:(i%3==1?1.0:10.0));
           vars[3*i+2]= (i%4==0?-1.0:(i%4==1?-0.5:(i%4==2?0.0:1.0)));
       }
       const bool ok=batch_(h_,vars.data(),count,out.data(),lo.data(),hi.data(),errors.data());
       // API returns a status flag; the authoritative per-point result is errors[].
       (void)ok;
       for(unsigned long i=0;i<count;++i) {
           const double ref=nativeH(vars[3*i],vars[3*i+1],vars[3*i+2]);
           if(errors[i]!=0 || !(std::isfinite(out[i])) ||
              std::abs(out[i]-ref)>5e-11*std::max(1.0,ref)) {
             std::cerr<<std::setprecision(17)<<"TINC/paceval batch mismatch: i="<<i
               <<" t="<<vars[3*i]<<" rho0="<<vars[3*i+1]<<" w="<<vars[3*i+2]
               <<" paceval="<<out[i]<<" native="<<ref<<" lo="<<lo[i]
               <<" hi="<<hi[i]<<" error="<<errors[i]<<"\n";
             throw std::runtime_error("paceval batch/native H mismatch at index "+std::to_string(i));
           }
       }
       std::cout<<"PASS paceval batch API: 256 evaluations against native H\n";
    }
    std::uint64_t scalarCalls() const {return calls_;}
    std::uint64_t batchCalls() const {return batchCalls_;}
};
struct Evaluator {
   Paceval* pv=nullptr;
   void prepare(double rho0,double w,unsigned steps,double tmax)const {if(pv)pv->prime(rho0,w,steps,tmax);}
   double h(double t,double rho0,double w)const {return pv?pv->hubble(t,rho0,w):nativeH(t,rho0,w);}
   Vec rhs(double t,double rho0,double w)const {
      const double H=h(t,rho0,w), aInv=std::exp(-t);
      const double r=rho(t,rho0,w),Q=1.0+r/6.0;
      return {Q*aInv/H,-aInv,aInv/H,1.0/H};
   }
   Vec step(double t,Vec y,double dt,double rho0,double w)const {
      if (dt==0) return y;
      // Standard RK4 collapses to Simpson quadrature because y' depends only on t.
      Vec k1=rhs(t,rho0,w), k2=rhs(t+.5*dt,rho0,w), k4=rhs(t+dt,rho0,w);
      for(int i=0;i<4;++i)y[i]+=dt*(k1[i]+4*k2[i]+k4[i])/6.0;
      return y;
   }
};
struct Config{ unsigned steps=2000; double tmax=4.0; std::string backend="both";
               std::string libpath="sdk/libpaceval.so"; bool tinc=false;
               std::string output="scan_v13.csv";};
struct Result {
 double rho0,w,D,tau_brane,tau_bulk,advance,relative_pct,a_brane,a_bulk,null_residual;
 double side_gap_min,spatial_junction_residual,temporal_junction_residual;
};
struct Stats{int accepted=0,excluded=0,negative=0,desitter=0;double maxNull=0,maxJunction=0,maxAdvance=0;};
inline double F(const Vec&y,double D){const double dz=y[1]-1.0;return y[0]*y[0]-dz*dz-D*D;}
class Solver {
  Config cfg_;Evaluator eval_;
  double dt_;
  std::vector<Vec> nodes_;
public:
  Solver(Config cfg,Evaluator eval):cfg_(cfg),eval_(eval),dt_(cfg.tmax/cfg.steps){}
  bool solve(double rho0,double w,double D,Result &out) {
    demand(rho0>0 && w>=-1 && w<=1 && D>0,"invalid model inputs");
    eval_.prepare(rho0,w,cfg_.steps,cfg_.tmax);
    nodes_.clear();nodes_.reserve(cfg_.steps+1);nodes_.push_back({0,1,0,0});
    for(unsigned i=0;i<cfg_.steps;++i){
       Vec nxt=eval_.step(dt_*i,nodes_.back(),dt_,rho0,w);
       for(double v:nxt)demand(std::isfinite(v),"ODE became nonfinite");
       nodes_.push_back(nxt);
    }
    if(nodes_.back()[2]<=D)return false; // Same log(a)=4 window as Python v1.2
    auto it=std::lower_bound(nodes_.begin()+1,nodes_.end(),D,
                             [](const Vec&v,double d){return v[2]<d;});
    demand(it!=nodes_.end(),"brane receiver bracket failed");
    unsigned ib=unsigned(it-nodes_.begin())-1;
    // Within the bracket integrate each partial step from its left endpoint.
    auto rootInCell=[&](unsigned i,auto fun)->std::pair<double,Vec>{
       double lo=0.0,hi=dt_,t=dt_*i;
       demand(fun(nodes_[i])<=1e-11,"root left bracket positive");
       demand(fun(nodes_[i+1])>=-1e-11,"root right bracket negative");
       for(unsigned k=0;k<47;++k) {
          double mid=.5*(lo+hi);
          Vec y=eval_.step(t,nodes_[i],mid,rho0,w);
          if(fun(y)>0) hi=mid; else lo=mid;
       }
       double delta=.5*(lo+hi);
       return {t+delta,eval_.step(t,nodes_[i],delta,rho0,w)};
    };
    auto br=rootInCell(ib,[&](const Vec&v){return v[2]-D;});
    const Vec &B=br.second;
    std::pair<double,Vec> gr;
    if(w==-1.0){gr=br;}
    else {
       // Model only the past bulk intersection of the target comoving worldline.
       int ig=-1;
       for(unsigned i=0;i<=ib;++i){if(F(nodes_[i+1],D)>=0){ig=int(i);break;}}
       if(ig<0 && F(B,D)>0){ig=int(ib);}
       demand(ig>=0,"no bulk receiver before brane receiver");
       if(unsigned(ig)==ib) {
          double lo=0.0,hi=br.first-ib*dt_,t=ib*dt_;
          for(int k=0;k<47;++k){double mid=(lo+hi)*.5;
            Vec y=eval_.step(t,nodes_[ib],mid,rho0,w);
            if(F(y,D)>0)hi=mid;else lo=mid;
          }
          double sub=.5*(lo+hi);gr={t+sub,eval_.step(t,nodes_[ib],sub,rho0,w)};
       } else gr=rootInCell(unsigned(ig),[&](const Vec&v){return F(v,D);});
    }
    const Vec&G=gr.second;
    // Convexity proves full chord on z>=z_brane for rho>0, w>-1,
    // conditional on the stated RS retained-side convention.
    double minGap=1e200;
    const double T_G=G[0],z_G=G[1];
    // Independent geometric side check using the monotone, cubic-Hermite
    // interpolation T(t). z(t)=exp(-t) is exact. This avoids adding hundreds
    // of thousands of unnecessary paceval calls to root inversions.
    for(unsigned i=0;i<=120;++i){
       const double u=i/120.0,T=u*T_G,zLine=1.0+u*(z_G-1.0);
       auto p=std::lower_bound(nodes_.begin(),nodes_.end(),T,
          [](const Vec&v,double value){return v[0]<value;});
       double tt;
       if(p==nodes_.begin())tt=0.0;
       else if(p==nodes_.end())tt=cfg_.tmax;
       else {
         const unsigned j=unsigned(p-nodes_.begin())-1;
         const double T0=nodes_[j][0],T1=nodes_[j+1][0];
         const double m0=(1+rho(dt_*j,rho0,w)/6.0)*std::exp(-dt_*j)/nativeH(dt_*j,rho0,w);
         const double m1=(1+rho(dt_*(j+1),rho0,w)/6.0)*std::exp(-dt_*(j+1))/nativeH(dt_*(j+1),rho0,w);
         auto hermite=[&](double s){
            const double s2=s*s,s3=s2*s;
            return (2*s3-3*s2+1)*T0 + (s3-2*s2+s)*dt_*m0
                 + (-2*s3+3*s2)*T1 + (s3-s2)*dt_*m1;
         };
         double lo=0,hi=1;
         for(int k=0;k<33;++k){double mid=.5*(lo+hi);
            if(hermite(mid)<T)lo=mid;else hi=mid;
         }
         tt=(j+.5*(lo+hi))*dt_;
       }
       minGap=std::min(minGap,zLine-std::exp(-tt));
    }
    const double r=rho(gr.first,rho0,w),Q=1.0+r/6.0,H=eval_.h(gr.first,rho0,w);
    const double Hdot=-.5*(1.0+w)*r*Q;
    double spatial=-std::sqrt(1.0+H*H)+Q;
    double temporal=-std::sqrt(1.0+H*H)-Hdot/std::sqrt(1.0+H*H)
                   -(-1.0+(2.0+3.0*w)*r/6.0);
    out={rho0,w,D,B[3],G[3],B[3]-G[3],100*(B[3]-G[3])/B[3],
         std::exp(br.first),std::exp(gr.first),F(G,D),minGap,spatial,temporal};
    demand(std::abs(out.null_residual)<1e-8,"bulk null residual too large");
    demand(std::abs(spatial)<1e-9 && std::abs(temporal)<1e-9,"Israel residual too large");
    demand(minGap>=-2e-9,"bulk straight segment outside retained side");
    return true;
  }
};
std::vector<Result> scan(Config cfg,Evaluator eval,const std::string& outFile,Stats&stats) {
   Solver solver(cfg,eval);std::vector<Result> all;
   for(double rho0:{0.1,1.0,10.0})for(double w:{-1.0,-0.9,-0.5,0.0,1.0/3.0,1.0})
       for(double D:{0.1,0.5,1.0}) {
         Result r{};
         if(!solver.solve(rho0,w,D,r)) {++stats.excluded;continue;}
         ++stats.accepted; if(w==-1)++stats.desitter;
         if(w>-1 && r.advance<=0)++stats.negative;
         stats.maxNull=std::max(stats.maxNull,std::abs(r.null_residual));
         stats.maxJunction=std::max(stats.maxJunction,std::max(std::abs(r.spatial_junction_residual),
                                                          std::abs(r.temporal_junction_residual)));
         stats.maxAdvance=std::max(stats.maxAdvance,r.relative_pct);all.push_back(r);
   }
   std::ofstream f(outFile);demand(bool(f),"cannot open "+outFile);
   f<<"rho0,w,D,tau_brane,tau_bulk,advance,relative_pct,a_brane,a_bulk,null_residual,side_gap_min,spatial_junction_residual,temporal_junction_residual\n";
   f<<std::setprecision(17);
   for(const Result& r:all)f<<r.rho0<<','<<r.w<<','<<r.D<<','<<r.tau_brane<<','<<r.tau_bulk<<','
     <<r.advance<<','<<r.relative_pct<<','<<r.a_brane<<','<<r.a_bulk<<','<<r.null_residual<<','
     <<r.side_gap_min<<','<<r.spatial_junction_residual<<','<<r.temporal_junction_residual<<'\n';
   return all;
}
inline const Result& keyCase(const std::vector<Result>&rs) {
   for(const Result&r:rs)if(r.rho0==10 && r.w==-0.5 && r.D==1.0)return r;
   throw std::runtime_error("missing key validation case");
}
void printKey(const Result&r,const Stats&s,const std::string&name) {
 std::cout<<std::setprecision(16)<<name<<": cases="<<s.accepted<<" excluded="<<s.excluded
    <<" deSitter="<<s.desitter<<" nonpositive(w>-1)="<<s.negative<<"\n"
    <<"  rho0=10 w=-0.5 D=1: tau_brane="<<r.tau_brane
    <<" tau_bulk="<<r.tau_bulk<<" delta="<<r.advance
    <<" relative_pct="<<r.relative_pct<<"\n"
    <<"  max |null residual|="<<s.maxNull<<" max |Israel residual|="<<s.maxJunction<<"\n";
 demand(s.accepted==50&&s.excluded==4&&s.desitter==7&&s.negative==0,"unexpected scan count or sign");
 demand(std::abs(r.advance-1.0377148766929376515)<1e-8,"high precision delta mismatch");
 demand(std::abs(r.relative_pct-20.96279244046836157)<1e-6,"high precision percentage mismatch");
}
Config parse(int argc,char**argv){Config c;
#if defined(_WIN32)
 c.libpath="paceval.dll";
#endif
 for(int i=1;i<argc;++i){std::string a(argv[i]);
   auto value=[&](){demand(i+1<argc,"missing value for "+a);return std::string(argv[++i]);};
   if(a=="--backend")c.backend=value();else if(a=="--paceval")c.libpath=value();
   else if(a=="--steps")c.steps=(unsigned)std::stoul(value());
   else if(a=="--output")c.output=value();else if(a=="--tinc")c.tinc=true;
   else throw std::runtime_error("unknown option: "+a);
 }
 demand(c.backend=="native"||c.backend=="paceval"||c.backend=="both","unknown backend");
 demand(c.steps>=32&&c.steps<=500000,"steps 32..500000 required");return c;
}
} // namespace bw
int main(int argc,char**argv){try{
 using namespace bw; Config cfg=parse(argc,argv);
 std::cout<<"Braneworld Shortcuts v1.3: 5D null-curve numerical research DEMONSTRATOR\n"
          <<"Dimensionless model only; no claim of real-world FTL or GW detection\n";
 std::vector<Result> n,p;
 if(cfg.backend=="native"||cfg.backend=="both"){
    Stats s;auto start=std::chrono::steady_clock::now();
    n=scan(cfg,{nullptr},cfg.output=="scan_v13.csv"?"native_scan_v13.csv":cfg.output+".native.csv",s);
    printKey(keyCase(n),s,"NATIVE C++17");
    std::cout<<"  elapsed "<<std::chrono::duration<double>(std::chrono::steady_clock::now()-start).count()<<" seconds\n";
 }
 if(cfg.backend=="paceval"||cfg.backend=="both"){
    Paceval pv(cfg.libpath,cfg.tinc);pv.verifyBatch();
    Stats s;auto start=std::chrono::steady_clock::now();
    p=scan(cfg,{&pv},cfg.output=="scan_v13.csv"?"paceval_scan_v13.csv":cfg.output+".paceval.csv",s);
    printKey(keyCase(p),s,"PACEVAL C++17");
    std::cout<<"  paceval scalar H evaluations="<<pv.scalarCalls()<<" batch calls="<<pv.batchCalls()<<" elapsed "
             <<std::chrono::duration<double>(std::chrono::steady_clock::now()-start).count()<<" seconds\n";
 }
 if(!n.empty()&&!p.empty()){
    demand(n.size()==p.size(),"native and paceval case counts differ");double maxDiff=0;
    for(size_t i=0;i<n.size();++i){
      demand(n[i].rho0==p[i].rho0&&n[i].w==p[i].w&&n[i].D==p[i].D,"case mismatch");
      maxDiff=std::max(maxDiff,std::abs(n[i].advance-p[i].advance));
    }
    std::cout<<"PASS native vs paceval max abs advance difference="<<std::setprecision(12)<<maxDiff<<"\n";
    demand(maxDiff<1e-8,"native vs paceval exceeds tolerance");
 }
 std::cout<<"PASS C++17 reproducibility checks\n";return 0;
}catch(const std::exception&e){std::cerr<<"FAIL: "<<e.what()<<'\n';return 1;}}
