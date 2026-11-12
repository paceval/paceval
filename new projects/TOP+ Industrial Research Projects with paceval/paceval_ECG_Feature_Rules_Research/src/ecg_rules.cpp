// WP032 - Synthetic, non-clinical ECG feature/rule evaluation with the original paceval API.
// All inputs are precomputed, dimensionless standardized ECG features. The C++ host
// does NOT diagnose arrhythmia and does NOT process patient records or certify safety.
#include "paceval_main.h"
#include <array>
#include <algorithm>
#include <cmath>
#include <cstdint>
#include <filesystem>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <sstream>
#include <stdexcept>
#include <string>
#include <vector>
namespace fs=std::filesystem;
namespace {
using X=std::array<double,4>; // r = centered RR mean; d = RR dispersion; q = centered QRS width; a = amplitude surrogate
constexpr char VARIABLES[]="r d q a";
void check(bool ok,const std::string& message){if(!ok)throw std::runtime_error(message);}
struct Rule {int id=0, family=0, version=1;double alpha=0, beta=0;std::string expression; PACEVAL_HANDLE handle=nullptr;};
// Stable score transform. The explicitly bounded feature domain keeps exp safe.
double sigmoid(double z){return 1.0/(1.0+std::exp(-z));}
double native(const Rule& rule,X x){const auto [r,d,q,a]=x;double z=0;
 switch(rule.family){
 case 0:z=rule.alpha*r+rule.beta*d+0.36*q+0.12*a;break;
 case 1:z=rule.alpha*r*d+rule.beta*q*a+0.19*d;break;
 case 2:z=rule.alpha*r*r+rule.beta*d*d+0.22*q*q-0.3;break;
 case 3:z=rule.alpha*std::sin(r)+rule.beta*std::cos(q)+0.17*d*a;break;
 default:z=rule.alpha*std::log(1+r*r)+rule.beta*std::exp(-d*d)+0.18*q*a;break;
 }return sigmoid(z);}
std::string expression(const Rule& rule){std::ostringstream s;s<<std::setprecision(17);
 const std::string A=std::to_string(rule.alpha),B=std::to_string(rule.beta);
 std::string z;
 switch(rule.family){
 case 0:z="("+A+"*r+"+B+"*d+0.36*q+0.12*a)";break;
 case 1:z="("+A+"*r*d+"+B+"*q*a+0.19*d)";break;
 case 2:z="("+A+"*r^2+"+B+"*d^2+0.22*q^2-0.3)";break;
 case 3:z="("+A+"*sin(r)+"+B+"*cos(q)+0.17*d*a)";break;
 default:z="("+A+"*ln(1+r^2)+"+B+"*exp(-d^2)+0.18*q*a)";break;
 }return "1/(1+exp(-"+z+"))";}
class Engine {
 std::vector<PACEVAL_HANDLE> handles;
public:
 Engine(){check(paceval_InitializeLibrary(nullptr),"Cannot initialize paceval runtime");}
 ~Engine(){for(auto h:handles)if(h)paceval_DeleteComputation(h);paceval_FreeLibrary();}
 PACEVAL_HANDLE create(const std::string& expr){auto h=paceval_CreateComputation(expr.c_str(),4,VARIABLES,false,nullptr);
  check(h!=nullptr&&!paceval_GetIsError(h),"paceval graph creation failed: "+expr);handles.push_back(h);return h;}
 double scalar(PACEVAL_HANDLE h,X x){auto y=paceval_dGetComputationResult(h,x.data(),nullptr,nullptr);
  check(!paceval_GetIsError(h)&&std::isfinite(y),"paceval scalar evaluation failed");return y;}
 std::vector<double> batch(PACEVAL_HANDLE h,const std::vector<X>& xs){std::vector<double> packed;packed.reserve(xs.size()*4);
  for(auto x:xs)for(double v:x)packed.push_back(v);
  std::vector<double> values(xs.size());std::vector<int> errors(xs.size(),-1);
  const bool failure=paceval_dGetComputationResultExt(h,packed.data(),static_cast<unsigned long>(xs.size()),values.data(),nullptr,nullptr,errors.data());
  check(!failure,"paceval batch API reported a failure");
  for(size_t i=0;i<xs.size();++i)check(errors[i]==0&&std::isfinite(values[i]),"invalid paceval batch result");return values;}
};
struct RNG {uint64_t state=20261112;uint64_t next(){state^=state>>12;state^=state<<25;state^=state>>27;return state*2685821657736338717ULL;}
 double u(){return (next()>>11)*0x1.0p-53;}};
X sample(RNG& gen){return {-1+2*gen.u(),2*gen.u(),-1+2*gen.u(),-1+2*gen.u()};}
void inputs(X x){for(double v:x)check(std::isfinite(v)&&std::abs(v)<=3,"invalid standardized feature");}
void audit(double actual,double expected,double& maximum){double delta=std::abs(actual-expected);maximum=std::max(maximum,delta);
 check(delta<=2e-11*(1+std::abs(expected)),"independent native C++ reference mismatch");}
std::vector<Rule> models(){std::vector<Rule> v;for(int f=0;f<5;++f)for(int j=0;j<10;++j){Rule r;r.id=f*10+j+1;r.family=f;
 r.alpha=0.28+0.048*j+0.015*f;r.beta=0.16+0.032*j;r.expression=expression(r);v.push_back(r);}return v;}
void run(const fs::path& out,int count){fs::create_directories(out);Engine engine;auto rules=models();
 for(auto& r:rules)r.handle=engine.create(r.expression);
 Rule revision=rules[0];revision.id=51;revision.version=2;revision.alpha+=0.09;revision.expression=expression(revision);revision.handle=engine.create(revision.expression);
 std::ofstream registry(out/"formula_registry.csv");registry<<"id,family,version,alpha,beta,expression\n";
 for(const auto& r:rules)registry<<r.id<<','<<r.family+1<<','<<r.version<<','<<std::setprecision(17)<<r.alpha<<','<<r.beta<<",\""<<r.expression<<"\"\n";
 registry<<revision.id<<','<<revision.family+1<<",2,"<<revision.alpha<<','<<revision.beta<<",\""<<revision.expression<<"\"\n";
 std::ofstream replay(out/"feature_replay.csv");replay<<"record_id,rule_id,rr_mean_ms,rr_sd_ms,qrs_width_ms,amplitude_mv,r,d,q,a,score,review_flag\n";
 RNG rng;double maxDelta=0;int review=0;
 for(int i=0;i<count;++i){const auto& r=rules[i%50];X x=sample(rng);inputs(x);
  // Illustrative feature transforms. The ranges and distributions are not a clinical ECG model.
  const double rrMean=800+100*x[0],rrSd=15+20*x[1],qrs=90+15*x[2],amp=1+0.2*x[3];
  const double score=engine.scalar(r.handle,x);audit(score,native(r,x),maxDelta);
  const int flag=score>=0.65;review+=flag;
  replay<<i+1<<','<<r.id<<','<<std::setprecision(17)<<rrMean<<','<<rrSd<<','<<qrs<<','<<amp;
  for(double v:x)replay<<','<<v;replay<<','<<score<<','<<flag<<'\n';}
 // Batch verifies the same expression on a deterministic independent feature subset.
 int batches=0;for(int k=0;k<50;++k){std::vector<X> xs;for(int j=0;j<32;++j)xs.push_back(sample(rng));
  auto ys=engine.batch(rules[k].handle,xs);for(size_t j=0;j<xs.size();++j){audit(ys[j],native(rules[k],xs[j]),maxDelta);++batches;}}
 // A 61 x 61 surface is genuinely evaluated through paceval, not reconstructed from host formulas.
 std::ofstream surface(out/"ecg_score_surface.csv");surface<<"rr_feature,qrs_feature,score\n";
 for(int i=0;i<=60;++i)for(int j=0;j<=60;++j){X x={-1+2*i/60.0,0.7,-1+2*j/60.0,0};
  double z=engine.scalar(rules[0].handle,x);audit(z,native(rules[0],x),maxDelta);
  surface<<std::setprecision(17)<<x[0]<<','<<x[2]<<','<<z<<'\n';}
 std::ofstream revisions(out/"formula_version_surface.csv");revisions<<"rr_feature,score_v1,score_v2\n";
 for(int i=0;i<=100;++i){X x={-1+2*i/100.0,0.8,0.3,0};double y1=engine.scalar(rules[0].handle,x),y2=engine.scalar(revision.handle,x);
  audit(y1,native(rules[0],x),maxDelta);audit(y2,native(revision,x),maxDelta);revisions<<std::setprecision(17)<<x[0]<<','<<y1<<','<<y2<<'\n';}
 std::ofstream report(out/"execution_summary.txt");report<<"WP032 original paceval runtime integration PASS\n"<<"graphs=51\nrecords="<<count<<"\nscalar_evaluations="<<count+3721+202<<"\nbatch_results="<<batches<<"\nreview_flags="<<review<<"\nmax_abs_native_audit="<<std::setprecision(17)<<maxDelta<<"\n";
 std::cout<<"PASS graphs=51 records="<<count<<" scalar="<<count+3721+202<<" batch="<<batches<<" reviews="<<review<<"\n";
}
}
int main(int argc,char**argv){try{int count=10000;fs::path out="examples";for(int i=1;i<argc;++i){std::string s=argv[i];if(s=="--records"&&i+1<argc)count=std::stoi(argv[++i]);else if(s=="--out"&&i+1<argc)out=argv[++i];else throw std::runtime_error("invalid command line argument: "+s);}check(count>=100&&count<=100000,"records out of range");run(out,count);return 0;}catch(const std::exception&e){std::cerr<<"FAIL: "<<e.what()<<'\n';return 1;}}
