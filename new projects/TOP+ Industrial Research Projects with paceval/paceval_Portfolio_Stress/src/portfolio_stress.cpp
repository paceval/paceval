// paceval Portfolio Stress-Scenario Mathematics: reproducible research demonstrator.
//
// This program is NOT a regulatory capital calculation or a real portfolio risk
// model. It evaluates explicit, synthetic four-factor P&L approximations under
// pre-generated or CSV-provided shocks. 100 independently versioned mathematical
// formulas are prepared as reusable paceval execution graphs.
//
// paceval scope: graph preparation, scalar/batched P&L formula evaluation and a
// small optional TINC point-sample experiment.
// Host scope: scenario generation or CSV import, validation, empirical VaR/ES,
// named stress cases, version updates, CSV export and independent native audit.
//
// Source and SDK facade: compile this file AND paceval_main.cpp together, linking
// an external, compatible architecture-specific paceval .so at CMake build time.
// No dlopen/dlsym reimplementation is used here.
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

namespace fs=std::filesystem;
namespace {
constexpr size_t DIM=4;
constexpr const char* VARS="eq ir fx cr";
using X=std::array<double,DIM>;
struct Config {size_t scenarios=4096,models=100,batch=512;uint64_t seed=20261112;
 fs::path out="results",input="";bool selftest=false;};
struct Scenario {size_t id;std::string type;X x;};
struct Model {size_t id;int family;int version;std::array<double,9> c;std::string expr;};
struct Risk {double var95=0,var975=0,es975=0,worst=0,mean_loss=0;};
void require(bool p,const std::string& what){if(!p)throw std::runtime_error(what);}
size_t positive_size(const std::string&s,const char*opt,size_t upper){
 require(!s.empty() && s[0]!='-',std::string("bad ")+opt);
 size_t stop=0;unsigned long long n=std::stoull(s,&stop);
 require(stop==s.size()&&n>0&&n<=upper,std::string("bad ")+opt);return size_t(n);
}
Config parse(int argc,char**argv){Config c;for(int i=1;i<argc;++i){
 std::string opt=argv[i];if(opt=="--self-test"){c.selftest=true;continue;}
 require(i+1<argc,"missing argument after "+opt);std::string val=argv[++i];
 if(opt=="--scenarios")c.scenarios=positive_size(val,"scenarios",100000);
 else if(opt=="--models")c.models=positive_size(val,"models",100);
 else if(opt=="--batch")c.batch=positive_size(val,"batch",16384);
 else if(opt=="--seed")c.seed=positive_size(val,"seed",1000000000);
 else if(opt=="--input")c.input=val;
 else if(opt=="--out")c.out=val;
 else throw std::runtime_error("unknown option: "+opt);
 }require(!c.out.empty(),"output path is empty");return c;}
// Initialize only once. All computation handles must be destroyed before this
// guard, otherwise the SDK facade could reference an already freed runtime.
struct Engine {Engine(){require(paceval_InitializeLibrary(nullptr),"paceval library initialization failed");}
 ~Engine(){paceval_FreeLibrary();}Engine(const Engine&)=delete;Engine&operator=(const Engine&)=delete;};
struct Graph {PACEVAL_HANDLE h=nullptr;explicit Graph(PACEVAL_HANDLE v=nullptr):h(v){}
 ~Graph(){if(h)paceval_DeleteComputation(h);}Graph(const Graph&)=delete;Graph&operator=(const Graph&)=delete;
 Graph(Graph&&o)noexcept:h(o.h){o.h=nullptr;}
 Graph&operator=(Graph&&o)noexcept{if(this!=&o){if(h)paceval_DeleteComputation(h);h=o.h;o.h=nullptr;}return *this;}};
// c[0:4]=delta exposures for [equity return, interest-rate absolute change,
// FX return, credit-spread absolute change], in synthetic currency/one-unit
// shock. c[4:7]=diagonal gammas; c[7]=equity/FX cross-gamma;
// c[8]=equity drawdown (absolute-return) sensitivity for the nonlinear family.
Model model_for(size_t id){Model m; m.id=id;m.family=int(id%4);m.version=1;
 m.c={180000.0+1300.0*double(id%13),-2100000.0+15000.0*double(id%17),
  90000.0+1250.0*double(id%11),-6800000.0-18000.0*double(id%19),
  280000.0+1250.0*double(id%13),18000000.0+70000.0*double(id%7),
  -12000000.0-90000.0*double(id%9),-400000.0-1500.0*double(id%11),
  35000.0+200.0*double(id%17)};
 return m;}
std::string real(double v){std::ostringstream s;s<<std::setprecision(17)<<v;return "("+s.str()+")";}
std::string expression(const Model&m){const auto&c=m.c;
 // All constants are parenthesized, including negative coefficients: this
 // deliberately avoids precedence ambiguities with unary minus in the SDK.
 std::string e="("+real(c[0])+"*eq+"+real(c[1])+"*ir+"+real(c[2])+"*fx+"+real(c[3])+"*cr";
 if(m.family>=1)e+="+0.5*"+real(c[4])+"*eq*eq+0.5*"+real(c[5])+"*ir*ir";
 if(m.family>=2)e+="+0.5*"+real(c[6])+"*cr*cr+"+real(c[7])+"*eq*fx";
 if(m.family>=3)e+="-"+real(c[8])+"*((-eq)+abs(-eq))/2";
 return e+")";
}
double native(const Model&m,const X&x){const auto&c=m.c;
 double r=c[0]*x[0]+c[1]*x[1]+c[2]*x[2]+c[3]*x[3];
 if(m.family>=1)r+=0.5*c[4]*x[0]*x[0]+0.5*c[5]*x[1]*x[1];
 if(m.family>=2)r+=0.5*c[6]*x[3]*x[3]+c[7]*x[0]*x[2];
 if(m.family>=3)r-=c[8]*std::max(0.0,-x[0]);
 return r;
}
Graph create_graph(const Model&m,bool tinc=false){
 Graph g(paceval_CreateComputation(m.expr.c_str(),DIM,VARS,tinc,nullptr));
 require(g.h!=nullptr,"paceval_CreateComputation returned a null graph");
 require(!paceval_GetIsError(g.h),"paceval graph creation failed for model "+std::to_string(m.id)+" expression="+m.expr);
 return g;
}
struct RNG {std::mt19937_64 gen;explicit RNG(uint64_t seed):gen(seed){}
 double uniform(){uint64_t bits=gen()>>11;return (double(bits)+0.5)/9007199254740992.0;}
 double normal(){static constexpr double PI=3.14159265358979323846;
 return std::sqrt(-2.0*std::log(uniform()))*std::cos(2.0*PI*uniform());}};
std::vector<Scenario> generated(size_t n,uint64_t seed){
 // Synthetic, documented factor dependence; not an empirical covariance model.
 RNG rng(seed);std::vector<Scenario>v;v.reserve(n+6);
 for(size_t i=0;i<n;++i){double a=rng.normal(),b=rng.normal(),c=rng.normal(),d=rng.normal();
 X x={0.025*a,
      0.0015*(0.25*a+std::sqrt(0.9375)*b),
      0.015*(0.35*a+0.20*b+std::sqrt(0.8375)*c),
      0.002*(-0.60*a+0.20*b+0.10*c+std::sqrt(0.59)*d)};
 v.push_back({i,"distribution",x});
 }
 // Separate hypothetical stresses. These are NOT included in empirical VaR/ES.
 const X special[]={ {-0.30,0.015,-0.12,0.025}, {-0.18,-0.010,-0.08,0.014},
 {-0.12,0.020,0.10,0.025}, {0.15,-0.018,0.08,-0.008},
 {-0.35,0.035,-0.20,0.040}, {-0.02,0.010,0.23,0.005}};
 for(const auto&x:special)v.push_back({v.size(),"named_stress",x});
 return v;
}
void validate_x(const X&x){for(size_t j=0;j<DIM;++j){
 require(std::isfinite(x[j]),"nonfinite shock detected");
 const double lim=(j==0||j==2)?0.5:0.06;
 require(std::abs(x[j])<=lim,"out-of-policy shock detected");}}
std::vector<Scenario> load_csv(const fs::path&path){std::ifstream f(path);require(f.good(),"cannot open scenario CSV: "+path.string());
 std::string s;require(bool(std::getline(f,s)),"empty scenario CSV");
 require(s=="scenario_id,type,eq,ir,fx,cr","bad CSV header");
 std::vector<Scenario> rows;size_t line=1;bool seen_stress=false;
 while(std::getline(f,s)){++line;require(!s.empty(),"blank line in CSV");
 require(std::count(s.begin(),s.end(),',')==5,"wrong CSV field count (including trailing delimiters)");
 std::istringstream st(s);std::array<std::string,6> fields;std::string part;size_t k=0;
 while(std::getline(st,part,',')){require(k<fields.size(),"too many CSV fields");fields[k++]=part;}
 require(k==6,"expected six CSV fields, line "+std::to_string(line));
 size_t stop_id=0;unsigned long long j=std::stoull(fields[0],&stop_id);
 require(stop_id==fields[0].size()&&j==rows.size(),"imported IDs must be consecutive, starting at 0");
 require(fields[1]=="distribution"||fields[1]=="named_stress","invalid type");
 if(fields[1]=="named_stress")seen_stress=true;
 else require(!seen_stress,"distribution rows must precede named stresses");
 X x{};for(size_t q=0;q<DIM;++q){size_t stop=0;x[q]=std::stod(fields[q+2],&stop);
 require(stop==fields[q+2].size(),"invalid numeric CSV field");}validate_x(x);
 rows.push_back({rows.size(),fields[1],x});require(rows.size()<=100006,"too many rows");}
 require(rows.size()>=64,"at least 64 imported records required");
 require(std::count_if(rows.begin(),rows.end(),[](const Scenario&z){return z.type=="distribution";})>=64,
 "at least 64 distribution scenarios required");return rows;
}
std::vector<double> evaluate(PACEVAL_HANDLE h,const std::vector<Scenario>&sc,size_t batch){
 std::vector<double> ret(sc.size()),in(batch*DIM),out(batch);std::vector<int> err(batch,0);
 for(size_t pos=0;pos<sc.size();pos+=batch){size_t n=std::min(batch,sc.size()-pos);
 for(size_t j=0;j<n;++j){validate_x(sc[pos+j].x);
 for(size_t k=0;k<DIM;++k)in[j*DIM+k]=sc[pos+j].x[k];}
 // IMPORTANT paceval SDK convention: true here signals an error, not success.
 bool failed=paceval_dGetComputationResultExt(h,in.data(),(unsigned long)n,out.data(),nullptr,nullptr,err.data());
 require(!failed,"paceval batch evaluation reported an error");
 for(size_t j=0;j<n;++j){require(err[j]==0&&std::isfinite(out[j]),"invalid paceval batch result");ret[pos+j]=out[j];}}
 return ret;
}
Risk summarize(const std::vector<double>&pnls){
 require(pnls.size()>=64,"too few losses to estimate risk");
 std::vector<double>loss;loss.reserve(pnls.size());for(double v:pnls){require(std::isfinite(v),"nonfinite PnL");loss.push_back(-v);}
 std::sort(loss.begin(),loss.end());const size_t n=loss.size();
 auto quantile=[&](double p){size_t k=size_t(std::ceil(p*double(n)));return loss[std::max(size_t(1),k)-1];};
 size_t tail=size_t(std::ceil(0.025*double(n)));
 // Published estimator: arithmetic average of the worst ceil(2.5% N) losses.
 // This is NOT a liquidity-horizon-adjusted or regulatory FRTB ES estimator.
 double es=0;for(size_t i=n-tail;i<n;++i)es+=loss[i]/double(tail);
 double mean=std::accumulate(loss.begin(),loss.end(),0.0)/double(n);
 return {quantile(0.95),quantile(0.975),es,loss.back(),mean};
}
void selftest(){
 Model m=model_for(0);X x={-0.1,0.002,-0.03,0.004};
 require(std::abs(native(m,x)-(m.c[0]*x[0]+m.c[1]*x[1]+m.c[2]*x[2]+m.c[3]*x[3]))<1e-10,"linear mismatch");
 m=model_for(3);const auto &c=m.c;
 double expected=c[0]*x[0]+c[1]*x[1]+c[2]*x[2]+c[3]*x[3]
 +0.5*c[4]*x[0]*x[0]+0.5*c[5]*x[1]*x[1]+0.5*c[6]*x[3]*x[3]
 +c[7]*x[0]*x[2]-c[8]*0.1;
 require(std::abs(native(m,x)-expected)<1e-9,"bad nonlinear model");
 auto r=summarize({-1,-2,-3,-4,-5,-6,-7,-8,-9,-10,-11,-12,-13,-14,-15,-16,
 -17,-18,-19,-20,-21,-22,-23,-24,-25,-26,-27,-28,-29,-30,-31,-32,
 -33,-34,-35,-36,-37,-38,-39,-40,-41,-42,-43,-44,-45,-46,-47,-48,
 -49,-50,-51,-52,-53,-54,-55,-56,-57,-58,-59,-60,-61,-62,-63,-64});
 require(r.worst==64&&r.es975==63.5&&r.var95==61&&r.var975==63,"tail convention mismatch");
 auto gen=generated(128,1234),again=generated(128,1234);require(gen[50].x==again[50].x,"RNG not deterministic");
 require(gen.size()==134&&gen[128].type=="named_stress","stress-generator mismatch");
 std::cout<<"PASS native statistics, scenario generation, and formula selftests\n";
}
void output_header(std::ofstream&f,const char*cols){require(f.good(),"unable to open CSV output");f<<cols<<'\n'<<std::setprecision(17);}
void run(const Config&cfg){selftest();fs::create_directories(cfg.out);
 std::vector<Scenario>sc=cfg.input.empty()?generated(cfg.scenarios,cfg.seed):load_csv(cfg.input);
 for(auto&s:sc)validate_x(s.x);
 size_t n=0;while(n<sc.size()&&sc[n].type=="distribution")++n;
 require(n>=64,"at least 64 distribution scenarios required");
 Engine engine;std::vector<Model> models;std::vector<Graph>graphs;
 models.reserve(cfg.models);graphs.reserve(cfg.models);
 for(size_t j=0;j<cfg.models;++j){Model m=model_for(j);m.expr=expression(m);
 graphs.push_back(create_graph(m));models.push_back(std::move(m));}
 std::ofstream in(cfg.out/"factor_shocks.csv");output_header(in,"scenario_id,type,eq,ir,fx,cr");
 for(auto&z:sc)in<<z.id<<','<<z.type<<','<<z.x[0]<<','<<z.x[1]<<','<<z.x[2]<<','<<z.x[3]<<'\n';
 std::ofstream rules(cfg.out/"rules.csv");output_header(rules,"rule_id,family,version,delta_eq,delta_ir,delta_fx,delta_cr,gamma_eq,gamma_ir,gamma_cr,cross_eq_fx,drawdown,formula");
 std::ofstream eval(cfg.out/"evaluations.csv");output_header(eval,"rule_id,scenario_id,paceval_pnl,native_pnl,abs_difference");
 std::ofstream stress(cfg.out/"stress_results.csv");output_header(stress,"rule_id,scenario_id,paceval_pnl,native_pnl");
 std::ofstream metrics(cfg.out/"risk_metrics.csv");output_header(metrics,"rule_id,family,var95_loss,var975_loss,es975_loss,worst_loss,mean_loss");
 std::ofstream update(cfg.out/"rule_update.csv");output_header(update,"rule_id,scenario_id,old_version,new_version,old_pnl,new_pnl,unchanged_other_rule");
 std::ofstream tinc(cfg.out/"tinc_samples.csv");output_header(tinc,"sample,eq,ir,fx,cr,value,raw_lower,raw_upper,host_lower_1ulp,host_upper_1ulp");
 double max_err=0;size_t checks=0;std::vector<double>old_17,base_18;std::vector<double>first16_17;
 for(size_t j=0;j<cfg.models;++j){const Model&m=models[j];
 rules<<j<<','<<m.family<<','<<m.version;for(double c:m.c)rules<<','<<c;rules<<','<<m.expr<<'\n';
 auto all=evaluate(graphs[j].h,sc,cfg.batch);
 std::vector<double>dist;dist.reserve(n);
 for(size_t i=0;i<sc.size();++i){double ref=native(m,sc[i].x);
 double err=std::abs(ref-all[i]);require(err<=1e-8*(1+std::abs(ref)),"mismatch rule="+std::to_string(j));
 max_err=std::max(max_err,err);++checks;
 if(i<n){dist.push_back(all[i]);eval<<j<<','<<i<<','<<all[i]<<','<<ref<<','<<err<<'\n';}
 else stress<<j<<','<<i<<','<<all[i]<<','<<ref<<'\n';}
 Risk r=summarize(dist);metrics<<j<<','<<m.family<<','<<r.var95<<','<<r.var975<<','<<r.es975<<','<<r.worst<<','<<r.mean_loss<<'\n';
 if(j==std::min(size_t(17),cfg.models-1))old_17=all;
 if(j==std::min(size_t(18),cfg.models-1))base_18=all;
 }
 // Rule v2 is built separately and validated before replacing the old object.
 // Other rule objects and their input mappings remain unchanged.
 size_t target=std::min(size_t(17),cfg.models-1);
 Model replacement=models[target];replacement.version=2;replacement.c[0]+=25000.0;
 replacement.expr=expression(replacement);
 Graph replacement_graph=create_graph(replacement);
 auto updated=evaluate(replacement_graph.h,sc,cfg.batch);
 size_t unaffected=std::min(size_t(18),cfg.models-1);
 auto unaffected_now=evaluate(graphs[unaffected].h,sc,cfg.batch);
 require(unaffected_now==base_18,"an unrelated graph changed during version update");
 for(size_t i=0;i<sc.size();++i){double ref=native(replacement,sc[i].x);
 require(std::abs(updated[i]-ref)<=1e-8*(1+std::abs(ref)),"updated rule mismatch");}
 for(size_t i=0;i<std::min(size_t(32),sc.size());++i)
 update<<target<<','<<i<<",1,2,"<<old_17[i]<<','<<updated[i]<<",true\n";
 // Smooth arithmetic TINC experiment, not a regulatory risk interval. The
 // high-precision checker evaluates exact decimal input values independently.
 Graph interval(paceval_CreateComputation("eq*eq+fx*fx",DIM,VARS,true,nullptr));
 require(interval.h && !paceval_GetIsError(interval.h),"TINC graph creation failed");
 for(size_t i=0;i<std::min(size_t(24),n);++i){double low=0,high=0;
 double value=paceval_dGetComputationResult(interval.h,sc[i].x.data(),&low,&high);
 require(!paceval_GetIsError(interval.h)&&std::isfinite(value)&&std::isfinite(low)&&std::isfinite(high)&&low<=high,"invalid TINC sample");
 // This intentionally separate host step expands each reported endpoint by
 // one binary64 ULP. Only observed sample inclusion is tested; neither raw
 // TINC values nor this heuristic are claimed to be universal enclosures.
 double adjusted_low=std::nextafter(low,-std::numeric_limits<double>::infinity());
 double adjusted_high=std::nextafter(high,std::numeric_limits<double>::infinity());
 tinc<<i<<','<<sc[i].x[0]<<','<<sc[i].x[1]<<','<<sc[i].x[2]<<','<<sc[i].x[3]<<','<<value<<','<<low<<','<<high<<','<<adjusted_low<<','<<adjusted_high<<'\n';}
 std::ofstream summary(cfg.out/"validation.json");require(summary.good(),"cannot open validation.json");
 summary<<std::setprecision(17)<<"{\n  \"research_scope\": \"synthetic non-regulatory four-factor portfolio stress study\",\n"
 <<"  \"models\": "<<cfg.models<<",\n  \"distribution_scenarios\": "<<n
 <<",\n  \"named_stress_scenarios\": "<<(sc.size()-n)<<",\n  \"runtime_evaluations\": "<<checks
 <<",\n  \"max_native_absolute_difference\": "<<max_err
 <<",\n  \"risk_estimator\": \"empirical nearest-rank VaR and mean of worst ceil(2.5% N) losses\",\n"
 <<"  \"seed\": "<<cfg.seed<<",\n  \"batch\": "<<cfg.batch
 <<",\n  \"version_update_rule_id\": "<<target
 <<",\n  \"tinc_samples\": "<<std::min(size_t(24),n)<<"\n}\n";
 std::cout<<"PASS: models="<<cfg.models<<", distributions="<<n
 <<", named_stresses="<<(sc.size()-n)<<", evaluated="<<checks
 <<", maximum_native_difference="<<max_err<<", TINC_samples="<<std::min(size_t(24),n)<<"\n";
}
} // namespace
int main(int argc,char**argv){try{Config c=parse(argc,argv);if(c.selftest)selftest();else run(c);return 0;}
 catch(const std::exception&e){std::cerr<<"FAIL: "<<e.what()<<'\n';return 1;}}
