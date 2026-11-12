// paceval Monte Carlo Pricing: independent mathematical payoff-kernel research
// Direct SDK integration: paceval_main.h is included, and paceval_main.cpp is
// compiled with this translation unit by CMake. External Linux runtime needed.
//
// Scientific boundaries: we exercise synthetic risk-neutral GBM paths with
// deterministic antithetic innovations; these are not historical market data.
// paceval evaluates five explicit DISCOUNTED payoff formulas via persistent
// computation handles; it does NOT generate paths, estimate risk-neutral model
// parameters, perform Monte Carlo statistical reduction, or certify price risk.
//
// Inputs: st, av, mx, k, cap, r, t. av is the average of post-start observation
// prices; mx is the maximum including S0. All values are checked before use.
// Payoff contracts 0: call 1: put 2: capped call 3: Asian call 4: lookback call.
// For the call family, a positive part z+ is expressed as (z+abs(z))/2 because
// this paceval runtime accepts abs() and this algebra is portable to C++.
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
#include <random>
#include <sstream>
#include <stdexcept>
#include <string>
#include <utility>
#include <vector>

namespace fs = std::filesystem;
namespace {
constexpr size_t NV=7;
constexpr const char* VARS="st av mx k cap r t";
constexpr double PI=3.141592653589793238462643383279502884;
constexpr double S0=100.0, RATE=0.03, VOL=0.2, MATURITY=1.0;
using V=std::array<double,NV>;
struct Config {size_t paths=32768, contracts=100, steps=16, batch=4096; uint64_t seed=20261112; fs::path out="results"; bool selftest=false;};
struct Features {double terminal,average,maximum;};
struct Contract {size_t id;int family; double strike,cap;};
void must(bool ok,const std::string& why){if(!ok)throw std::runtime_error(why);}
size_t count(const std::string& s,const char* opt,size_t max){
 must(!s.empty()&&s[0]!='-',std::string("bad ")+opt);
 size_t end=0; unsigned long long n=std::stoull(s,&end);
 must(end==s.size()&&n>0&&n<=max,std::string("bad ")+opt);return size_t(n);
}
Config parse(int argc,char**argv){Config c;for(int i=1;i<argc;++i){
 std::string s=argv[i]; if(s=="--self-test"){c.selftest=true;continue;}
 must(i+1<argc,"missing value for "+s);std::string v=argv[++i];
 if(s=="--paths")c.paths=count(v,"paths",1000000);
 else if(s=="--contracts")c.contracts=count(v,"contracts",100);
 else if(s=="--steps")c.steps=count(v,"steps",256);
 else if(s=="--batch")c.batch=count(v,"batch",16384);
 else if(s=="--seed")c.seed=count(v,"seed",1000000000);
 else if(s=="--out")c.out=v;
 else throw std::runtime_error("unknown option "+s);
 }must((c.paths%2)==0,"paths must be even for antithetic pairs");
 must(!c.out.empty(),"output directory required");return c;}
struct Engine {Engine(){must(paceval_InitializeLibrary(nullptr),"paceval_InitializeLibrary failed");}
 ~Engine(){paceval_FreeLibrary();}Engine(const Engine&)=delete;Engine& operator=(const Engine&)=delete;};
struct Graph {PACEVAL_HANDLE h=nullptr;explicit Graph(PACEVAL_HANDLE x=nullptr):h(x){}
 ~Graph(){if(h)paceval_DeleteComputation(h);}Graph(Graph&& o) noexcept:h(o.h){o.h=nullptr;}
 Graph& operator=(Graph&&o) noexcept{if(this!=&o){if(h)paceval_DeleteComputation(h);h=o.h;o.h=nullptr;}return *this;}
 Graph(const Graph&)=delete;Graph&operator=(const Graph&)=delete;};
const char* formula(int f){
 // The discount factor is deliberately INSIDE the paceval graph. Path generation
 // and reductions remain host functions and are not attributed to paceval.
 switch(f){
 case 0:return "((st-k)+abs(st-k))/2*exp(-(r*t))";
 case 1:return "((k-st)+abs(k-st))/2*exp(-(r*t))";
 case 2:return "(((st-k)+abs(st-k))-((st-k-cap)+abs(st-k-cap)))/2*exp(-(r*t))";
 case 3:return "((av-k)+abs(av-k))/2*exp(-(r*t))";
 case 4:return "((mx-k)+abs(mx-k))/2*exp(-(r*t))";
 default:throw std::runtime_error("unknown payoff family");}
}
const char* label(int f){static const char* l[]={"european_call","european_put","capped_call","asian_call","lookback_call"};return l[f];}
double positive(double z){return (z+std::abs(z))/2.0;}
double native(int f,const V&v){double st=v[0],av=v[1],mx=v[2],k=v[3],cap=v[4],r=v[5],t=v[6];
 const double discount=std::exp(-r*t);
 switch(f){case 0:return positive(st-k)*discount;case 1:return positive(k-st)*discount;
 case 2:return (positive(st-k)-positive(st-k-cap))*discount;
 case 3:return positive(av-k)*discount;case 4:return positive(mx-k)*discount;
 default:throw std::runtime_error("bad native family");}
}
Graph make_graph(int family,bool tinc=false){Graph g(paceval_CreateComputation(formula(family),NV,VARS,tinc,nullptr));
 must(g.h!=nullptr,"null paceval graph");must(!paceval_GetIsError(g.h),std::string("graph failed ")+formula(family));return g;}
// Portable engine-independent RNG sequence: MT19937_64 provides raw words;
// the uniform map and Box-Muller normal transformation are specified here.
struct RNG {std::mt19937_64 gen; explicit RNG(uint64_t seed):gen(seed){}
 double uniform(){uint64_t bits=gen()>>11;return (double(bits)+0.5)/9007199254740992.0;}
 double normal(){return std::sqrt(-2*std::log(uniform()))*std::cos(2*PI*uniform());}
};
std::vector<Features> generate(size_t n,size_t steps,uint64_t seed){
 RNG rng(seed);const double dt=MATURITY/double(steps);
 const double drift=(RATE-0.5*VOL*VOL)*dt,shock=VOL*std::sqrt(dt);
 std::vector<Features> out;out.reserve(n);
 for(size_t i=0;i<n;i+=2){
 double plus=S0,minus=S0,sum_plus=0,sum_minus=0,max_plus=S0,max_minus=S0;
 for(size_t j=0;j<steps;++j){double z=rng.normal();
 plus*=std::exp(drift+shock*z);minus*=std::exp(drift-shock*z);
 sum_plus+=plus;sum_minus+=minus;max_plus=std::max(max_plus,plus);max_minus=std::max(max_minus,minus);}
 out.push_back({plus,sum_plus/double(steps),max_plus});
 out.push_back({minus,sum_minus/double(steps),max_minus});
 }return out;
}
Contract contract(size_t id){return {id,int(id%5), 78.0+double((id*7)%45), 7.0+double((id*3)%16)};}
V values(const Features&p,const Contract&c){return {p.terminal,p.average,p.maximum,c.strike,c.cap,RATE,MATURITY};}
std::vector<double> batch(PACEVAL_HANDLE handle,const std::vector<Features>& paths,const Contract&c,size_t batchsize){
 std::vector<double> result(paths.size());
 std::vector<double> in(batchsize*NV),out(batchsize);
 std::vector<int> error(batchsize);
 for(size_t start=0;start<paths.size();start+=batchsize){size_t n=std::min(batchsize,paths.size()-start);
 for(size_t j=0;j<n;++j){auto x=values(paths[start+j],c);
 for(size_t k=0;k<NV;++k){must(std::isfinite(x[k]),"nonfinite payoff input");in[j*NV+k]=x[k];}}
 // According to the original SDK, true means an error was encountered.
 bool has_error=paceval_dGetComputationResultExt(handle,in.data(),(unsigned long)n,out.data(),nullptr,nullptr,error.data());
 must(!has_error,"paceval batch reported an error");
 for(size_t j=0;j<n;++j){must(error[j]==0&&std::isfinite(out[j]),"paceval sample error");result[start+j]=out[j];}
 }
 return result;
}
double normalcdf(double x){return 0.5*std::erfc(-x/std::sqrt(2.0));}
double black_scholes(int family,double strike){
 must(family<=1,"analytic reference only for European call / put");
 const double s=VOL*std::sqrt(MATURITY);
 double d1=(std::log(S0/strike)+(RATE+0.5*VOL*VOL)*MATURITY)/s,d2=d1-s;
 if(family==0)return S0*normalcdf(d1)-strike*std::exp(-RATE*MATURITY)*normalcdf(d2);
 return strike*std::exp(-RATE*MATURITY)*normalcdf(-d2)-S0*normalcdf(-d1);
}
// A pair of antithetic trajectories is ONE independent statistical observation.
// The standard error is formed from pair-averaged payoffs, never from treating
// the plus and minus samples as independent Monte Carlo observations.
std::pair<double,double> estimate(const std::vector<double>&y){
 must(y.size()%2==0,"expected antithetic pairs");size_t n=y.size()/2;
 double mean=0,m2=0;for(size_t i=0;i<n;++i){double avg=(y[2*i]+y[2*i+1])*0.5;
 double delta=avg-mean;mean+=delta/double(i+1);m2+=delta*(avg-mean);}
 double se= n>1?std::sqrt((m2/double(n-1))/double(n)):0;
 return {mean,se};}
void header(std::ofstream& f,const char* label){must(f.good(),"cannot open output");f<<label<<'\n'<<std::setprecision(17);}
void selftest(){
 V v={120,105,135,100,10,RATE,MATURITY};
 must(std::abs(native(0,v)-20*std::exp(-RATE))<1e-12,"call self test");
 must(std::abs(native(1,v))<1e-12,"put self test");
 must(std::abs(native(2,v)-10*std::exp(-RATE))<1e-12,"cap self test");
 must(std::abs(native(3,v)-5*std::exp(-RATE))<1e-12,"Asian self test");
 must(std::abs(native(4,v)-35*std::exp(-RATE))<1e-12,"lookback self test");
 must(std::abs(black_scholes(0,100)-9.413403383853)<1e-8,"Black-Scholes call reference");
 must(std::abs((black_scholes(0,100)-black_scholes(1,100))-(S0-100*std::exp(-RATE)))<1e-10,"put-call parity");
 auto f1=generate(8,16,1234),f2=generate(8,16,1234);
 must(f1.size()==f2.size()&&f1[3].maximum==f2[3].maximum,"reproducible path generation");
 must(std::all_of(f1.begin(),f1.end(),[](const Features&f){return f.terminal>0&&f.average>0&&f.maximum>=S0;}),"path properties");
 std::cout<<"PASS native self-test\n";
}
void run(const Config&cfg){
 selftest();fs::create_directories(cfg.out);
 auto paths=generate(cfg.paths,cfg.steps,cfg.seed);
 Engine engine;
 std::vector<Graph> graphs;graphs.reserve(5);for(int i=0;i<5;++i)graphs.push_back(make_graph(i));
 std::ofstream contracts(cfg.out/"contracts.csv");header(contracts,"contract_id,family,model_version,strike,cap,formula");
 std::ofstream prices(cfg.out/"prices.csv");header(prices,"contract_id,family,strike,cap,paceval_price,native_price,antithetic_pair_se,analytic_price,analytic_difference,abs_kernel_difference");
 std::ofstream samples(cfg.out/"path_samples.csv");header(samples,"path_id,terminal_price,arithmetic_average,observed_maximum");
 std::ofstream audit(cfg.out/"payoff_audit.csv");header(audit,"contract_id,path_id,family,terminal_price,arithmetic_average,observed_maximum,strike,cap,rate,time,paceval_payoff,native_payoff,abs_error");
 std::ofstream update(cfg.out/"model_update.csv");header(update,"contract_id,path_id,old_strike,new_strike,old_payoff,new_payoff,other_contract_unchanged");
 std::ofstream tinc(cfg.out/"tinc_samples.csv");header(tinc,"sample,family,st,av,mx,k,cap,r,t,value,lower,upper,native");
 std::ofstream report(cfg.out/"validation.txt");must(report.good(),"cannot open validation summary");
 for(size_t i=0;i<std::min(size_t(128),paths.size());++i){auto&p=paths[i];samples<<i<<','<<p.terminal<<','<<p.average<<','<<p.maximum<<'\n';}
 double maxerror=0;size_t checks=0;size_t checked_bs=0;double max_analytic_sigmas=0;
 std::vector<double> cached_first; // reused to prove the contract update is isolated
 for(size_t j=0;j<cfg.contracts;++j){const Contract c=contract(j);
 contracts<<j<<','<<label(c.family)<<",v1,"<<c.strike<<','<<c.cap<<','<<formula(c.family)<<'\n';
 auto outputs=batch(graphs[c.family].h,paths,c,cfg.batch);
 auto est=estimate(outputs);
 double native_mean=0;double native_max_error=0;
 for(size_t i=0;i<paths.size();++i){V v=values(paths[i],c);double ref=native(c.family,v);
 double err=std::abs(outputs[i]-ref);native_mean+=ref/double(paths.size());
 must(err<2e-10*(1+std::abs(ref)),"paceval/native mismatch contract="+std::to_string(j));
 native_max_error=std::max(native_max_error,err);maxerror=std::max(maxerror,err);++checks;
 if(i<3){audit<<j<<','<<i<<','<<label(c.family);
 for(double x:v)audit<<','<<x;
 audit<<','<<outputs[i]<<','<<ref<<','<<err<<'\n';}
 }
 double analytic=std::numeric_limits<double>::quiet_NaN(), diff=analytic;
 if(c.family<=1){analytic=black_scholes(c.family,c.strike);diff=est.first-analytic;
 // Conservative sanity check: model-based MC error allowed to be stochastic.
 // A 6-standard-error rule plus a small absolute floor catches gross mistakes
 // in sufficiently large studies (>=2048 paths); small-sample price outputs
 // remain available without a fragile significance-based hard failure.
 // This is NOT proof of correct random sampling or of a trading model.
 if(cfg.paths>=2048) must(std::abs(diff)<=6*est.second+0.025,"MC price outside analytic sanity envelope");
 ++checked_bs;if(est.second>0)max_analytic_sigmas=std::max(max_analytic_sigmas,std::abs(diff)/est.second);
 }
 prices<<j<<','<<label(c.family)<<','<<c.strike<<','<<c.cap<<','<<est.first<<','<<native_mean<<','<<est.second<<',';
 if(c.family<=1)prices<<analytic<<','<<diff;else prices<<"NA,NA";
 prices<<','<<native_max_error<<'\n';
 if(j==0)cached_first=std::move(outputs);
 }
 // Contract revisions keep shared function handles alive: version v2 changes
 // only the strike for one selected contract; other prices/graph definitions
 // stay unchanged, so no recompilation of mathematical graphs is needed.
 const Contract old=contract(0);Contract changed=old;changed.strike+=4;
 // Explicitly re-evaluate a different contract before/after the revision.
 // Its inputs and its shared graph handle must remain unchanged.
 Contract unchanged=contract(1);
 std::vector<Features> subset(paths.begin(),paths.begin()+std::min(size_t(16),paths.size()));
 auto independent_before=batch(graphs[unchanged.family].h,subset,unchanged,cfg.batch);
 auto revised=batch(graphs[old.family].h,paths,changed,cfg.batch);
 auto independent_after=batch(graphs[unchanged.family].h,subset,unchanged,cfg.batch);
 must(independent_before==independent_after,"unaffected contract changed during revision");
 for(size_t i=0;i<std::min(size_t(16),paths.size());++i){
 must(std::abs(revised[i]-native(changed.family,values(paths[i],changed)))<1e-10,"revision mismatch");
 update<<old.id<<','<<i<<','<<old.strike<<','<<changed.strike<<','<<cached_first[i]<<','<<revised[i]<<",true\n";
 }
 // TINC is a pointwise numerical interval experiment, independently checked
 // by the high-precision script. Samples never imply universal containment.
 Graph tinc_graph(paceval_CreateComputation("st*exp(-(r*t))",NV,VARS,true,nullptr));
 must(tinc_graph.h!=nullptr && !paceval_GetIsError(tinc_graph.h),"discounted underlying TINC graph creation failed");
 for(size_t i=0;i<24;++i){auto c=contract(0);V v=values(paths[i],c);
 // Smooth discounted asset value: independent of the contract strike.
 // Nonsmooth payoff formulas are audited separately in payoff_audit.csv.
 double lo=0,hi=0;double val=paceval_dGetComputationResult(tinc_graph.h,v.data(),&lo,&hi);
 must(!paceval_GetIsError(tinc_graph.h)&&std::isfinite(val)&&std::isfinite(lo)&&std::isfinite(hi)&&lo<=hi,"invalid TINC output");
 tinc<<i<<",discounted_terminal";for(double x:v)tinc<<','<<x;
 tinc<<','<<val<<','<<lo<<','<<hi<<','<<v[0]*std::exp(-v[5]*v[6])<<'\n';
 }
 // All graph RAII owners are destroyed before Engine: destruction order is
 // reverse of construction, ensuring the dynamic mathematical library is live.
 report<<"Research case: reusable payoff kernels in Monte Carlo pricing\n";
 report<<"Synthetic GBM, S0="<<S0<<", rate="<<RATE<<", volatility="<<VOL<<", maturity="<<MATURITY<<"\n";
 report<<"seed="<<cfg.seed<<"\nsteps="<<cfg.steps<<"\npaths="<<cfg.paths<<"\nantithetic_pairs="<<cfg.paths/2<<"\n";
 report<<"contracts="<<cfg.contracts<<"\nmathematical_graphs=5\nbatch="<<cfg.batch<<"\n";
 report<<"payoff_validations="<<checks<<"\nmax_payoff_abs_error="<<std::setprecision(17)<<maxerror<<'\n';
 report<<"european_analytic_checks="<<checked_bs<<"\nmax_analytic_deviation_in_standard_errors="<<max_analytic_sigmas<<'\n';
 report<<"tinc_samples=24\nmodel_update_checks=16\n";
 std::cout<<"PASS "<<checks<<" paceval/native payoff matches across "<<cfg.contracts<<" contracts and "<<cfg.paths<<" paths; "<<checked_bs<<" analytic price checks; 24 TINC point samples\n";
}
} // namespace
int main(int argc,char**argv){try{Config cfg=parse(argc,argv);if(cfg.selftest)selftest();else run(cfg);return 0;}
 catch(const std::exception& e){std::cerr<<"FAIL: "<<e.what()<<'\n';return 1;}}
