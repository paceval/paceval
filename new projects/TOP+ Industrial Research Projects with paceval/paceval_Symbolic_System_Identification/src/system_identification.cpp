// Reproducible offline symbolic system-identification demonstrator using
// official paceval C++ API files and an external compatible Linux runtime.
//
// Research responsibility boundary:
// paceval    : persistent execution graphs, batched RHS evaluation, optional TINC.
// C++ host  : model generator, reference ODE solver, dataset splits, model ranking,
//             RK4 integration, independent native audit, data quality decisions.
// This is an explicitly synthetic, controlled candidate-screening experiment;
// it does not claim discovery of a new physical law or robust noisy-data inference.
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
#include <random>
#include <sstream>
#include <stdexcept>
#include <string>
#include <vector>
namespace fs=std::filesystem;
namespace {
constexpr int NF=7, NV=7; // x, v, u, a, b, c, d
constexpr double DT=0.04;
constexpr int STEPS=120;
constexpr double TOL=2e-9;
constexpr std::uint64_t SEED=20261111ULL;
// Every candidate inside a family shares ONE compiled execution graph.
const std::array<const char*,NF> FORMULA{{
 "a*x+b*v+c*u",                   // 0: linear spring / actuator
 "a*x+b*v+c*u+d*x*x*x",           // 1: Duffing cubic stiffness
 "a*x+b*v+c*u+d*x*x",             // 2: quadratic stiffness
 "a*x+b*v+c*u+d*sin(x)",          // 3: sinusoidal restoring force
 "a*x+b*v+c*u+d*v*v*v",           // 4: cubic damping (servo)
 "a*x+b*v+c*u+d*x*v",             // 5: cross-coupling
 "a*x+b*v+c*u+d*tanh(x)"          // 6: nonlinear saturation
}};
const std::array<const char*,2> NAMES{{"spring_mass","servo_actuator"}};
struct Coef {double a,b,c,d;};
const std::array<Coef,2> TRUE_COEF{{{-1.8,-0.28,1.10,-0.075},{-1.45,-0.62,1.65,-0.16}}};
const std::array<int,2> TRUE_FAMILY{{1,4}};
void req(bool good,const std::string& message){if(!good)throw std::runtime_error(message);}
std::ofstream output(const fs::path& f){std::ofstream o(f);req(o.good(),"Cannot write "+f.string());o<<std::setprecision(17);return o;}
struct Candidate{int id=0, scenario=0, family=0; Coef p{}; double train=0,valid=0;};
struct Point{int scenario,split,trajectory,step; double t,x,v,u,dx,dv;};
struct State{double x,v;};
struct Audit{std::size_t total=0,fail=0;double max_absolute=0;};
// Explicit native mathematical oracle; independent of every paceval call.
double native(int fam,const Coef& p,double x,double v,double u){
 double y=p.a*x+p.b*v+p.c*u;
 switch(fam){case 0: break;case 1:y+=p.d*x*x*x;break;
 case 2:y+=p.d*x*x;break;case 3:y+=p.d*std::sin(x);break;
 case 4:y+=p.d*v*v*v;break;case 5:y+=p.d*x*v;break;
 case 6:y+=p.d*std::tanh(x);break;default:throw std::runtime_error("unknown family");}
 return y;
}
double forcing(int scenario,int trajectory,double t){
 double ph=0.17+0.34*trajectory+0.23*scenario;
 return 0.67*std::sin((0.85+0.11*scenario)*t+ph)+0.21*std::cos(1.47*t-ph*0.41);
}
State initial(int scenario,int trajectory){return {0.12+0.09*trajectory+0.05*scenario,-0.20+0.077*trajectory};}
// Deterministic classical RK4, with exactly the same forcing at each stage.
template<class F> State advance(int scenario,int trajectory,double t,State s,double h,F&& acceleration){
 const auto deriv=[&](double tt,State z){return State{z.v,acceleration(z.x,z.v,forcing(scenario,trajectory,tt))};};
 State a=deriv(t,s),b=deriv(t+h/2,{s.x+h*a.x/2,s.v+h*a.v/2});
 State c=deriv(t+h/2,{s.x+h*b.x/2,s.v+h*b.v/2});
 State d=deriv(t+h,{s.x+h*c.x,s.v+h*c.v});
 return {s.x+h*(a.x+2*b.x+2*c.x+d.x)/6,s.v+h*(a.v+2*b.v+2*c.v+d.v)/6};
}
std::vector<Point> observations(int scenario){
 std::vector<Point> out;out.reserve(7*(STEPS+1));
 // 3 train + 2 validation + 2 held-out trajectories; entire independent
 // trajectories stay together, preventing time-adjacent split leakage.
 for(int tr=0;tr<7;++tr){int split=tr<3?0:(tr<5?1:2);
  State s=initial(scenario,tr);const auto rhs=[&](double x,double v,double u){return native(TRUE_FAMILY[scenario],TRUE_COEF[scenario],x,v,u);};
  for(int step=0;step<=STEPS;++step){
   double t=DT*step,u=forcing(scenario,tr,t);
   out.push_back({scenario,split,tr,step,t,s.x,s.v,u,s.v,rhs(s.x,s.v,u)});
   if(step<STEPS)for(int sub=0;sub<4;++sub)s=advance(scenario,tr,t+DT*sub/4,s,DT/4,rhs);
  }
  // Second-order finite differences of the observed velocity, rather than
  // injecting the exact RHS, produce the acceleration *targets* used in
  // model screening. This is an idealized noise-free measurement scenario.
  auto at=[&](int j)->const Point&{return out[(std::size_t)tr*(STEPS+1)+j];};
  for(int j=0;j<=STEPS;++j){
   double derivative=j==0?(-3*at(0).v+4*at(1).v-at(2).v)/(2*DT):
     (j==STEPS?(3*at(STEPS).v-4*at(STEPS-1).v+at(STEPS-2).v)/(2*DT):
       (at(j+1).v-at(j-1).v)/(2*DT));
   out[(std::size_t)tr*(STEPS+1)+j].dv=derivative;
  }
 }
 return out;
}
std::vector<Candidate> candidates(int scenario,int n){
 req(n>=7&&n<=20000,"candidate count must be 7..20000");
 std::vector<Candidate> v;v.reserve(n);std::mt19937_64 rng(SEED+scenario*191);
 std::uniform_real_distribution<double> perturb(-0.45,0.45),drift(-0.16,0.16);
 for(int id=0;id<n;++id){Candidate q; q.id=id;q.scenario=scenario;
  q.family=id==0?TRUE_FAMILY[scenario]:(id*5+3+scenario)%NF;
  q.p=TRUE_COEF[scenario];
  if(id){q.p.a+=perturb(rng);q.p.b+=perturb(rng)*0.65;
   q.p.c+=perturb(rng)*0.70;q.p.d+=drift(rng);}
  v.push_back(q);
 }
 return v;
}
class Engine{
 bool initialized_=false;std::array<PACEVAL_HANDLE,NF> graphs_{};std::array<PACEVAL_HANDLE,2> intervals_{};
 void close()noexcept{
  for(auto& h:intervals_)if(h){paceval_DeleteComputation(h);h=nullptr;}
  for(auto& h:graphs_)if(h){paceval_DeleteComputation(h);h=nullptr;}
  if(initialized_){paceval_FreeLibrary();initialized_=false;}
 }
public:
 Engine(){req(paceval_InitializeLibrary(nullptr),"paceval initialize failed");initialized_=true;
  try{for(int f=0;f<NF;++f){graphs_[f]=paceval_CreateComputation(FORMULA[f],NV,"x v u a b c d",false,nullptr);
    req(graphs_[f]&&!paceval_GetIsError(graphs_[f]),"paceval graph creation failed "+std::to_string(f));}
   for(int sc=0;sc<2;++sc){
    intervals_[sc]=paceval_CreateComputation(FORMULA[TRUE_FAMILY[sc]],NV,"x v u a b c d",true,nullptr);
    req(intervals_[sc]&&!paceval_GetIsError(intervals_[sc]),"TINC graph creation failed");
   }
  }catch(...){close();throw;}}
 ~Engine(){close();} Engine(const Engine&)=delete; Engine& operator=(const Engine&)=delete;
 double scalar(int family,const Coef& p,double x,double v,double u){
  double args[]{x,v,u,p.a,p.b,p.c,p.d};
  double result=paceval_dGetComputationResult(graphs_.at(family),args,nullptr,nullptr);
  req(std::isfinite(result)&&!paceval_GetIsError(graphs_[family]),"paceval scalar evaluation failed");return result;
 }
 // API layout is sample-major: [x,v,u,a,b,c,d] repeated, one sample per row.
 template<class Fn>void batch(int family,const Coef& p,const std::vector<Point>& pts,int split,
                              int batch_size,Fn callback){
  req(batch_size>=1&&batch_size<=4096,"batch out of range");
  std::vector<double> inputs((std::size_t)batch_size*NV),results(batch_size);
  std::vector<int> errors(batch_size);std::vector<std::size_t> indices;indices.reserve(pts.size());
  for(std::size_t i=0;i<pts.size();++i)if(pts[i].split==split)indices.push_back(i);
  for(std::size_t base=0;base<indices.size();base+=(std::size_t)batch_size){
   std::size_t count=std::min<std::size_t>(batch_size,indices.size()-base);
   for(std::size_t j=0;j<count;++j){const auto& o=pts[indices[base+j]];
    const double row[]{o.x,o.v,o.u,p.a,p.b,p.c,p.d};
    for(int k=0;k<NV;++k)inputs[NV*j+k]=row[k];
   }
   bool failed=paceval_dGetComputationResultExt(graphs_[family],inputs.data(),(unsigned long)count,
                                                results.data(),nullptr,nullptr,errors.data());
   req(!failed,"paceval batch reported graph error");
   for(std::size_t j=0;j<count;++j){req(errors[j]==PACEVAL_ERR_NO_ERROR&&std::isfinite(results[j]),"invalid batch result");
    callback(pts[indices[base+j]],results[j]);}
  }
 }
 std::array<double,3> tinc(int sc,const Coef& p,double x,double v,double u){
  double args[]{x,v,u,p.a,p.b,p.c,p.d},lo=0,hi=0;
  double val=paceval_dGetComputationResult(intervals_[sc],args,&lo,&hi);
  req(!paceval_GetIsError(intervals_[sc])&&std::isfinite(val)&&std::isfinite(lo)&&std::isfinite(hi)&&lo<=hi,"invalid TINC output");
  return {val,lo,hi};
 }
};
void reference_check(double got,double expected,Audit& a){
 ++a.total;double diff=std::abs(got-expected);a.max_absolute=std::max(a.max_absolute,diff);
 if(!std::isfinite(got)||diff>TOL*(1+std::abs(expected)))++a.fail;
}
double mse(Engine& engine,const Candidate& c,const std::vector<Point>& pts,int split,int batch,Audit& audit,
           std::ofstream* samples=nullptr,int* sample_count=nullptr){
 long double sse=0;std::size_t n=0;
 engine.batch(c.family,c.p,pts,split,batch,[&](const Point& o,double r){
  double e=r-o.dv;sse+=(long double)e*e;++n;
  // Fixed systematic check independent of the paceval implementation.
  if((c.id*37+o.trajectory*13+o.step)%151==0){reference_check(r,native(c.family,c.p,o.x,o.v,o.u),audit);}
  if(samples&&sample_count&&*sample_count<72&&c.id%17==0&&o.step%41==0){
   double nr=native(c.family,c.p,o.x,o.v,o.u);
   *samples<<c.scenario<<','<<c.id<<','<<c.family<<','<<o.x<<','<<o.v<<','<<o.u<<','<<c.p.a<<','<<c.p.b<<','<<c.p.c<<','<<c.p.d<<','<<r<<','<<nr<<'\n';
   ++*sample_count;
  }
 });
 req(n>0,"empty partition");return (double)(sse/n);
}
void self_test(){
 Coef p{-2,-0.3,1.2,-0.1};
 req(std::abs(native(0,p,1,2,3)-0.9999999999999996)<1e-10,"linear oracle incorrect");
 req(std::abs(native(1,p,1,2,3)-0.9)<1e-10,"cubic oracle incorrect");
 req(std::abs(native(4,p,1,2,3)-0.2)<1e-10,"cubic damping oracle incorrect");
 for(int sc=0;sc<2;++sc){auto pts=observations(sc);req(pts.size()==7*(STEPS+1),"dataset size");
  for(const auto& o:pts)req(std::isfinite(o.x)&&std::isfinite(o.v)&&std::isfinite(o.dv),"nonfinite observation");
  auto c1=candidates(sc,128),c2=candidates(sc,128);for(std::size_t i=0;i<c1.size();++i)
   req(c1[i].family==c2[i].family&&c1[i].p.a==c2[i].p.a,"candidate seed not deterministic");
 }
 std::cout<<"Native self-test passed\n";
}
void run(const fs::path& folder,int n,int batch){
 fs::create_directories(folder);Engine engine;Audit audit;
 auto data=output(folder/"observations.csv");data<<"scenario,split,trajectory,step,t,x,v,u,dx,dv\n";
 auto candidates_file=output(folder/"candidates.csv");candidates_file<<"scenario,id,family,a,b,c,d,train_mse,validation_mse\n";
 auto ranking=output(folder/"selection.csv");ranking<<"scenario,id,family,train_mse,validation_mse,test_derivative_mse,test_rollout_rmse_x,test_rollout_rmse_v\n";
 auto trace=output(folder/"heldout_trajectories.csv");trace<<"scenario,trajectory,t,x_truth,v_truth,x_paceval,v_paceval\n";
 auto samples=output(folder/"audit_samples.csv");samples<<"scenario,id,family,x,v,u,a,b,c,d,paceval,native\n";
 auto tinc=output(folder/"tinc_samples.csv");tinc<<"scenario,family,x,v,u,a,b,c,d,paceval,lower,upper\n";
 auto variants=output(folder/"model_updates.csv");variants<<"scenario,step,original,new_version,delta\n";
 auto summary=output(folder/"validation.json");summary<<"{\n  \"seed\": "<<SEED<<", \"timestep\": "<<DT<<", \"candidates_per_system\": "<<n<<",\n  \"systems\": [\n";
 for(int sc=0;sc<2;++sc){
  auto obs=observations(sc);auto pool=candidates(sc,n);
  for(const auto&o:obs)data<<NAMES[sc]<<','<<o.split<<','<<o.trajectory<<','<<o.step<<','<<o.t<<','<<o.x<<','<<o.v<<','<<o.u<<','<<o.dx<<','<<o.dv<<'\n';
  int saved=0;
  for(auto& c:pool)c.train=mse(engine,c,obs,0,batch,audit,&samples,&saved);
  // Selection has *two* stages; no held-out labels or trajectory error
  // enters the fitting or shortlist phase.
  std::vector<int> order(n);for(int k=0;k<n;++k)order[k]=k;
  std::stable_sort(order.begin(),order.end(),[&](int i,int j){return pool[i].train<pool[j].train;});
  const std::size_t finalists=std::min<std::size_t>(32,order.size());
  int selected=-1;double best=std::numeric_limits<double>::infinity();
  for(std::size_t k=0;k<finalists;++k){auto& cand=pool[order[k]];
   cand.valid=mse(engine,cand,obs,1,batch,audit);
   if(cand.valid<best){best=cand.valid;selected=order[k];}
  }
  req(selected>=0,"no selected model");const auto winner=pool[selected];
  for(const auto& c:pool)candidates_file<<NAMES[sc]<<','<<c.id<<','<<c.family<<','<<c.p.a<<','<<c.p.b<<','<<c.p.c<<','<<c.p.d<<','<<c.train<<','<<(std::isfinite(c.valid)?std::to_string(c.valid):"not_selected")<<'\n';
  double test_mse=mse(engine,winner,obs,2,batch,audit);
  long double errx=0,errv=0;int count=0;
  for(int tr=5;tr<7;++tr){
   State s=initial(sc,tr);const auto rhs=[&](double x,double v,double u){return engine.scalar(winner.family,winner.p,x,v,u);};
   for(int step=0;step<=STEPS;++step){const auto& o=obs[(std::size_t)tr*(STEPS+1)+step];
    double ex=s.x-o.x,ev=s.v-o.v;errx+=(long double)ex*ex;errv+=(long double)ev*ev;++count;
    trace<<NAMES[sc]<<','<<tr<<','<<o.t<<','<<o.x<<','<<o.v<<','<<s.x<<','<<s.v<<'\n';
    if(step<STEPS)s=advance(sc,tr,o.t,s,DT,rhs);
   }
  }
  double rmsex=std::sqrt((double)(errx/count)),rmsev=std::sqrt((double)(errv/count));
  ranking<<NAMES[sc]<<','<<winner.id<<','<<winner.family<<','<<winner.train<<','<<winner.valid<<','<<test_mse<<','<<rmsex<<','<<rmsev<<'\n';
  // Evaluate a candidate formula update by changing coefficients with the
  // *same graph*. It is a new externally managed model version, not a mutation
  // of the paceval executable computation structure.
  Coef changed=winner.p;changed.d+=0.035;
  for(int step=0;step<10;++step){const auto&o=obs[(std::size_t)5*(STEPS+1)+step];
   double old=engine.scalar(winner.family,winner.p,o.x,o.v,o.u),now=engine.scalar(winner.family,changed,o.x,o.v,o.u);
   variants<<NAMES[sc]<<','<<step<<','<<old<<','<<now<<','<<now-old<<'\n';
  }
  // The TINC investigation is a finite pointwise audit, not a universal
  // proof of correctly outward-rounded interval enclosures.
  for(int j=0;j<12;++j){const auto& o=obs[(std::size_t)j*19%obs.size()];
   const auto t=engine.tinc(sc,TRUE_COEF[sc],o.x,o.v,o.u);
   tinc<<NAMES[sc]<<','<<TRUE_FAMILY[sc]<<','<<o.x<<','<<o.v<<','<<o.u<<','<<TRUE_COEF[sc].a<<','<<TRUE_COEF[sc].b<<','<<TRUE_COEF[sc].c<<','<<TRUE_COEF[sc].d<<','<<t[0]<<','<<t[1]<<','<<t[2]<<'\n';
  }
  req(audit.fail==0,"native comparison tolerance failed");
  if(sc)summary<<",\n";
  summary<<"    {\"name\": \""<<NAMES[sc]<<"\", \"ground_truth_family\": "<<TRUE_FAMILY[sc]
         <<", \"selected_id\": "<<winner.id<<", \"selected_family\": "<<winner.family
         <<", \"training_mse\": "<<winner.train<<", \"validation_mse\": "<<winner.valid
         <<", \"heldout_derivative_mse\": "<<test_mse<<", \"heldout_trajectory_rmse_x\": "<<rmsex
         <<", \"heldout_trajectory_rmse_v\": "<<rmsev<<"}";
  std::cout<<NAMES[sc]<<": "<<n<<" candidates; selected id="<<winner.id<<" family="<<winner.family
           <<"; heldout x-RMSE="<<rmsex<<" v-RMSE="<<rmsev<<"\n";
 }
 summary<<"\n  ],\n  \"native_cross_checks\": "<<audit.total<<", \"native_mismatches\": "<<audit.fail
        <<", \"max_native_absolute_difference\": "<<audit.max_absolute<<"\n}\n";
 req(audit.fail==0,"native reference mismatch");
 std::cout<<"Cross-checks "<<audit.total<<"; violations "<<audit.fail<<"\n";
}
}
int main(int argc,char**argv){
 try{
  int n=1000,batch=128;fs::path folder="results";bool st=false;
  for(int i=1;i<argc;++i){std::string a=argv[i];
   if(a=="--self-test")st=true;
   else if(a=="--candidates"&&i+1<argc)n=std::stoi(argv[++i]);
   else if(a=="--batch"&&i+1<argc)batch=std::stoi(argv[++i]);
   else if(a=="--output"&&i+1<argc)folder=argv[++i];
   else throw std::runtime_error("usage: system_identification [--self-test] [--candidates N] [--batch B] [--output DIRECTORY]");
  }
  if(st)self_test();else {req(batch>0&&batch<=4096,"batch must be 1..4096");run(folder,n,batch);}return 0;
 }catch(const std::exception& e){std::cerr<<"ERROR: "<<e.what()<<"\n";return 1;}
}
