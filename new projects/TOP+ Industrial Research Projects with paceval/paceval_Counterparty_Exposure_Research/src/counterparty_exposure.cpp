// WP028: deterministic, synthetic counterparty exposure kernel demonstration.
// paceval evaluates reusable, versioned mathematical exposure expressions.
// Host C++ validates domain contracts, owns scenarios and netting-set grouping,
// records outputs, and independently checks the mathematical expressions.
// NOT SA-CCR, EAD, CVA, ISDA SIMM, a legal netting determination, or a production risk model.
#include "paceval_main.h"
#include <algorithm>
#include <array>
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
using X=std::array<double,6>;
constexpr char VARS[]="v c h s t f";
void check(bool good,const std::string& msg){if(!good)throw std::runtime_error(msg);}
struct Rule{int id=0,family=0,version=1;double a=0,b=0;std::string expression;PACEVAL_HANDLE handle=nullptr;};
// Positive part is defined by a non-negative square root; inputs are bounded to
// avoid overflow. In financial notation this is max(d,0), with no sign of a
// negative counterparty exposure. It is an illustrative *point-in-time* metric.
double pos(double d){return (d+std::sqrt(d*d))*0.5;}
// Input units: v, c, t are EUR millions (the threshold t is an amount),
// h is a collateral haircut in [0,0.5], s is a dimensionless scenario shock,
// f is a synthetic collateral FX conversion in [0.7,1.3].
void valid(const X& x){for(double y:x)check(std::isfinite(y),"non-finite input");
 check(std::abs(x[0])<=25&&x[1]>=0&&x[1]<=20&&x[2]>=0&&x[2]<=0.5&&std::abs(x[3])<=0.5&&x[4]>=0&&x[4]<=3&&x[5]>=0.7&&x[5]<=1.3,"out of range");}
// Separately programmed native model: an internal audit, NOT a claim that the
// model reflects any signed ISDA CSA, enforceable netting or regulatory EAD.
double native(const Rule& r,const X& x){double v=x[0],c=x[1],h=x[2],s=x[3],t=x[4],f=x[5];double d=0;
 switch(r.family){case 0:d=v-c*(1-h)-t;break;
 case 1:d=v*(1+r.a*s)-c*(1-h)-t;break;
 case 2:d=v+r.a*s+r.b*s*s-c*(1-h)-t;break;
 case 3:d=v-c*(1-h)*(f+r.a*s)-t;break;
 default:d=v-c*(1-h)-t;return pos(d)+r.a*std::sqrt(1+s*s)*pos(v);}
 return pos(d);}
std::string expr(const Rule& r){std::ostringstream o;o<<std::setprecision(17);std::string d;
 switch(r.family){case 0:d="v-c*(1-h)-t";break;
 case 1:d="v*(1+"+std::to_string(r.a)+"*s)-c*(1-h)-t";break;
 case 2:d="v+"+std::to_string(r.a)+"*s+"+std::to_string(r.b)+"*s*s-c*(1-h)-t";break;
 case 3:d="v-c*(1-h)*(f+"+std::to_string(r.a)+"*s)-t";break;
 default:d="v-c*(1-h)-t";break;}
 // Different formula versions within the base family use nontrivial distinct
 // algebraic terms without altering the central risk interpretation.
 if(r.family==0)d="v-c*(1-h)-t+"+std::to_string(r.a)+"*s";
 std::string p="(("+d+")+sqrt(("+d+")*("+d+")))/2";
 if(r.family==4){std::string vpos="(v+sqrt(v*v))/2";p+="+"+std::to_string(r.a)+"*sqrt(1+s*s)*"+vpos;}
 return p;}
// family 0 also has scenario shift a*s, and is independently audited as such.
double reference(const Rule& r,const X& x){if(r.family==0)return pos(x[0]-x[1]*(1-x[2])-x[4]+r.a*x[3]);return native(r,x);}
std::vector<Rule> makeRules(){std::vector<Rule> r;for(int family=0;family<5;++family)for(int j=0;j<10;++j){Rule z;z.id=family*10+j+1;z.family=family;z.a=0.05+0.015*j+0.002*family;z.b=1.0+0.12*j;z.expression=expr(z);r.push_back(z);}return r;}
class Engine{std::vector<PACEVAL_HANDLE> all;public:
 Engine(){check(paceval_InitializeLibrary(nullptr),"paceval runtime initialization failed");}
 ~Engine(){for(auto h:all)if(h)paceval_DeleteComputation(h);paceval_FreeLibrary();}
 PACEVAL_HANDLE create(const std::string& formula){auto h=paceval_CreateComputation(formula.c_str(),6,VARS,false,nullptr);check(h&&!paceval_GetIsError(h),"invalid paceval expression: "+formula);all.push_back(h);return h;}
 double scalar(PACEVAL_HANDLE h,const X& x){X in=x;double y=paceval_dGetComputationResult(h,in.data(),nullptr,nullptr);check(!paceval_GetIsError(h)&&std::isfinite(y),"paceval scalar result failed");return y;}
 std::vector<double> batch(PACEVAL_HANDLE h,const std::vector<X>& records){std::vector<double> packed(records.size()*6),out(records.size());std::vector<int> errors(records.size(),-1);
  for(size_t i=0;i<records.size();++i)for(int k=0;k<6;++k)packed[6*i+k]=records[i][k];
  bool failed=paceval_dGetComputationResultExt(h,packed.data(),(unsigned long)records.size(),out.data(),nullptr,nullptr,errors.data());check(!failed,"paceval batch failed");for(size_t i=0;i<records.size();++i)check(!errors[i]&&std::isfinite(out[i]),"batch result invalid");return out;}
};
struct RNG{uint64_t state=20261112;uint64_t next(){state^=state>>12;state^=state<<25;state^=state>>27;return state*2685821657736338717ULL;}double unit(){return (next()>>11)*0x1.0p-53;}};
X draw(RNG& r){return {-6+23*r.unit(),2+10*r.unit(),0.04+0.22*r.unit(),-0.22+0.44*r.unit(),0.05+1.3*r.unit(),0.85+0.3*r.unit()};}
void audit(double got,double ref,double& worst){double delta=std::abs(got-ref);worst=std::max(worst,delta);check(delta<=2e-10*(1+std::abs(ref)),"independent native audit failed");}
void run(const fs::path& dest,int count){fs::create_directories(dest);Engine engine;auto rules=makeRules();for(auto& r:rules)r.handle=engine.create(r.expression);
 Rule revision=rules[11];revision.id=51;revision.version=2;revision.a+=0.03;revision.expression=expr(revision);revision.handle=engine.create(revision.expression);
 std::ofstream registry(dest/"rule_registry.csv");registry<<"rule_id,family,version,a,b,expression\n";
 for(auto& r:rules)registry<<r.id<<","<<r.family+1<<",1,"<<r.a<<","<<r.b<<",\""<<r.expression<<"\"\n";
 registry<<"51,"<<revision.family+1<<",2,"<<revision.a<<","<<revision.b<<",\""<<revision.expression<<"\"\n";
 std::ofstream samples(dest/"exposure_samples.csv");samples<<"update,rule_id,mtm_eur_m,collateral_eur_m,haircut,shock,threshold_eur_m,fx,exposure_eur_m\n";
 std::array<unsigned,50> observed{};std::array<double,50> sum{},peaks{};RNG rng;double worst=0;long long positive=0;int sampled=0;
 for(int i=0;i<count;++i){int k=i%50;const auto& r=rules[k];X x=draw(rng);valid(x);double e=engine.scalar(r.handle,x);
 // Every sampled hundredth row and the first hundred are checked internally.
 if(i<100||i%100==0)audit(e,reference(r,x),worst);
 observed[k]++;sum[k]+=e;peaks[k]=std::max(peaks[k],e);positive+=(e>0);
 if(i%100==0){samples<<i+1<<","<<r.id<<std::setprecision(17);for(auto v:x)samples<<","<<v;samples<<","<<e<<"\n";++sampled;}}
 std::ofstream aggregates(dest/"rule_metrics.csv");aggregates<<"rule_id,family,mean_exposure_eur_m,max_exposure_eur_m\n";
 for(int i=0;i<50;++i)aggregates<<i+1<<","<<rules[i].family+1<<","<<std::setprecision(17)<<sum[i]/observed[i]<<","<<peaks[i]<<"\n";
 std::ofstream surface(dest/"exposure_surface.csv");surface<<"mtm_eur_m,collateral_eur_m,exposure_eur_m\n";long long scalar=count;
 for(int i=0;i<=60;++i)for(int j=0;j<=60;++j){X x={-4+0.4*i,0.25*j,0.12,0.11,0.4,1.0};double e=engine.scalar(rules[0].handle,x);audit(e,reference(rules[0],x),worst);surface<<x[0]<<","<<x[1]<<","<<std::setprecision(17)<<e<<"\n";++scalar;}
 std::ofstream scenario(dest/"stress_scenarios.csv");scenario<<"shock,baseline_eur_m,stressed_eur_m,quadratic_eur_m,addon_eur_m\n";
 for(int k=0;k<=80;++k){X x={9,5,0.12,-0.3+0.0075*k,0.3,1.0};auto a=engine.scalar(rules[0].handle,x),b=engine.scalar(rules[10].handle,x),c=engine.scalar(rules[20].handle,x),d=engine.scalar(rules[40].handle,x);audit(a,reference(rules[0],x),worst);audit(b,reference(rules[10],x),worst);audit(c,reference(rules[20],x),worst);audit(d,reference(rules[40],x),worst);scenario<<x[3]<<","<<a<<","<<b<<","<<c<<","<<d<<"\n";scalar+=4;}
 std::ofstream vers(dest/"formula_revision.csv");vers<<"shock,v1_exposure_eur_m,v2_exposure_eur_m\n";
 for(int k=0;k<=60;++k){X x={7,5,0.1,-0.3+0.01*k,0.2,1.0};auto a=engine.scalar(rules[11].handle,x),b=engine.scalar(revision.handle,x);audit(a,reference(rules[11],x),worst);audit(b,reference(revision,x),worst);vers<<x[3]<<","<<a<<","<<b<<"\n";scalar+=2;}
 RNG br;long long batch=0;for(const auto& r:rules){std::vector<X> xs;for(int i=0;i<32;++i)xs.push_back(draw(br));auto values=engine.batch(r.handle,xs);for(size_t i=0;i<xs.size();++i){audit(values[i],reference(r,xs[i]),worst);++batch;}}
 // Negative domain-contract tests: reject invalid haircut, negative collateral, NaN.
 int rejected=0;for(const X& x:std::vector<X>{{2,4,0.8,0,0,1},{2,-1,0.2,0,0,1},{NAN,1,0.2,0,0,1}}){try{valid(x);}catch(...){rejected++;}}check(rejected==3,"input rejection contract failed");
 std::ofstream log(dest/"sdk_execution.txt");log<<std::setprecision(17)<<"STATUS PASS\nGRAPH_COUNT 51\nMARKET_UPDATES "<<count<<"\nSAMPLED_ROWS "<<sampled<<"\nSCALAR_EVALUATIONS "<<scalar<<"\nBATCH_VERIFIED "<<batch<<"\nPOSITIVE_EXPOSURE_UPDATES "<<positive<<"\nSURFACE_POINTS 3721\nINVALID_INPUT_REJECTIONS "<<rejected<<"\nMAX_ABS_INTERNAL_AUDIT "<<worst<<"\n";
 std::cout<<"PASS "<<count<<" updates, 51 graphs, "<<scalar<<" scalar, "<<batch<<" batch, "<<positive<<" positive\n";}
}
int main(int argc,char** argv){try{fs::path out="examples";int count=1000000;for(int i=1;i<argc;++i){std::string arg=argv[i];if(arg=="--out"&&i+1<argc)out=argv[++i];else if(arg=="--updates"&&i+1<argc)count=std::stoi(argv[++i]);}check(count>0&&count<=2000000,"invalid update count");run(out,count);return 0;}catch(const std::exception& e){std::cerr<<"FAIL "<<e.what()<<"\n";return 1;}}
