// WP026: mathematical bid-quotation kernels with the original paceval C/C++ facade.
// This is a synthetic industrial procurement demonstrator, not a market-equilibrium model.
// paceval computes numerical quotation formulas; the host owns procurement constraints,
// reservation ceilings, deterministic scenarios, audit trails and decision labels.
#include "paceval_main.h"
#include <array>
#include <cmath>
#include <cstdlib>
#include <filesystem>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <sstream>
#include <stdexcept>
#include <string>
#include <vector>
#include <algorithm>
#include <cstdint>
namespace fs=std::filesystem;
namespace {
using Args=std::array<double,6>;
constexpr char VARS[]="cost qty risk discount lead vol";
void require(bool cond,const std::string& message){if(!cond)throw std::runtime_error(message);}
struct Rule {int id,family,variant; double a,b,k;std::string formula;PACEVAL_HANDLE handle=nullptr;};
struct RNG {std::uint64_t state=20261112;std::uint64_t next(){state^=state>>12;state^=state<<25;state^=state>>27;return state*2685821657736338717ULL;}double uniform(){return (next()>>11)*0x1.0p-53;}};
// All values are explicitly dimensional: cost and risk in EUR per item;
// quantity is an item count; lead is days; volatility and discount are dimensionless.
// Five alternative, illustrative quotation approaches are used. None is claimed
// to be an optimal bidding equilibrium or to forecast a competitor's behavior.
double native(const Rule& r,const Args& v){
 const double c=v[0],q=v[1],risk=v[2],d=v[3],l=v[4],vol=v[5];
 switch(r.family){
 case 0:return c*(1+r.a)+risk*(1+r.b*vol)-c*d*r.k*q/(q+100);
 case 1:return c*(1+r.a)+risk*(1+r.b*l*l/900)-c*d*r.k*q/(q+100);
 case 2:return c*(1+r.a)+risk*(1+r.b*std::sqrt(1+vol*vol))-c*d*r.k*q/(q+100);
 case 3:return c*(1+r.a)+risk*(1+r.b*vol)-c*d*r.k*std::log(1+q)/std::log(1001.0);
 default:return c*(1+r.a)+risk*(1+r.b*std::exp(-l/30.0))-c*d*r.k*q/(q+100);
 }
}
std::string formula(const Rule& r){
 std::ostringstream s;s<<std::setprecision(17);
 s<<"cost*(1+"<<r.a<<")+risk*(1+"<<r.b<<"*";
 if(r.family==1)s<<"lead*lead/900";
 else if(r.family==2)s<<"sqrt(1+vol*vol)";
 else if(r.family==4)s<<"exp(-lead/30)";
 else s<<"vol";
 s<<")-cost*discount*"<<r.k<<"*";
 if(r.family==3)s<<"ln(1+qty)/ln(1001)";
 else s<<"qty/(qty+100)";
 return s.str();
}
std::vector<Rule> create_rules(){std::vector<Rule> rules;for(int f=0;f<5;++f)for(int j=0;j<10;++j){
 Rule r;r.id=f*10+j+1;r.family=f;r.variant=j;r.a=0.07+0.008*j+0.003*f;r.b=0.08+0.012*j;r.k=0.40+0.045*j;r.formula=formula(r);rules.push_back(r);
 }return rules;}
class Engine {
 std::vector<PACEVAL_HANDLE> hs;
public:
 Engine(){require(paceval_InitializeLibrary(nullptr),"SDK initialization failed");}
 ~Engine(){for(auto h:hs)if(h)paceval_DeleteComputation(h);paceval_FreeLibrary();}
 PACEVAL_HANDLE add(const std::string& s){auto h=paceval_CreateComputation(s.c_str(),6,VARS,false,nullptr);require(h&&!paceval_GetIsError(h),"graph creation: "+s);hs.push_back(h);return h;}
 double eval(PACEVAL_HANDLE h,Args a){double z=paceval_dGetComputationResult(h,a.data(),nullptr,nullptr);require(!paceval_GetIsError(h)&&std::isfinite(z),"scalar SDK evaluation");return z;}
 std::vector<double> batch(PACEVAL_HANDLE h,const std::vector<Args>& a){
  std::vector<double> packed(a.size()*6),res(a.size());std::vector<int> errors(a.size(),-1);
  for(std::size_t i=0;i<a.size();++i)for(int j=0;j<6;++j)packed[i*6+j]=a[i][j];
  bool failed=paceval_dGetComputationResultExt(h,packed.data(),(unsigned long)a.size(),res.data(),nullptr,nullptr,errors.data());
  require(!failed,"SDK batch failed");for(std::size_t i=0;i<a.size();++i)require(errors[i]==0&&std::isfinite(res[i]),"SDK batch per-result error");return res;
 }
};
struct Offer {Args x;double buyer_max;};
Offer offer(RNG& gen){
 double c=25+175*gen.uniform(),q=10+std::floor(990*gen.uniform());
 double risk=0.25+8*gen.uniform(),discount=0.02+0.18*gen.uniform();
 double lead=1+std::floor(59*gen.uniform()),vol=0.02+0.36*gen.uniform();
 return {{c,q,risk,discount,lead,vol}, c*(1.05+0.30*gen.uniform())};
}
struct Decision {double quote,margin,total;bool eligible;};
Decision decide(double raw,const Offer& o){
 // Procurement policy constraints deliberately remain outside paceval's
 // formula graph. The floor is a hypothetical target gross markup (not ROI).
 double floor=o.x[0]*1.03;
 double quote=std::max(floor,raw);
 bool eligible=quote<=o.buyer_max;
 return {quote,(quote-o.x[0])/quote,quote*o.x[1],eligible};
}
void audit(double got,double ref,double& maxdiff){double d=std::abs(got-ref);maxdiff=std::max(maxdiff,d);require(d<=1e-10*(1+std::abs(ref)),"SDK/native disagreement");}
int run(const fs::path& out){
 fs::create_directories(out);
 Engine engine;auto rules=create_rules();for(auto& r:rules)r.handle=engine.add(r.formula);
 // Versioned expression: one adjusted markup; prior handles remain alive.
 Rule updated=rules[0];updated.id=51;updated.a+=0.025;updated.formula=formula(updated);updated.handle=engine.add(updated.formula);
 std::ofstream registry(out/"policy_registry.csv");registry<<"policy_id,family,version,markup,exposure,discount_weight,expression\n";
 for(const auto& r:rules)registry<<r.id<<","<<r.family+1<<",1,"<<r.a<<","<<r.b<<","<<r.k<<",\""<<r.formula<<"\"\n";
 registry<<"51,1,2,"<<updated.a<<","<<updated.b<<","<<updated.k<<",\""<<updated.formula<<"\"\n";
 std::ofstream os(out/"offers.csv");os<<"request,policy_id,unit_cost_eur,qty,risk_eur_per_item,discount_fraction,lead_days,volatility,buyer_ceiling_eur,formula_unit_bid_eur,final_unit_bid_eur,gross_margin_fraction,total_quote_eur,eligible\n";
 RNG rng;std::array<double,50> sum{},eligible_cnt{},margin_sum{};double maxdiff=0;std::size_t scalar=0,batch=0;
 for(int i=0;i<10000;++i){const auto& r=rules[i%50];Offer o=offer(rng);double result=engine.eval(r.handle,o.x);audit(result,native(r,o.x),maxdiff);++scalar;
 Decision d=decide(result,o);sum[i%50]+=d.quote;eligible_cnt[i%50]+=d.eligible; margin_sum[i%50]+=d.margin;
 os<<std::setprecision(17)<<i+1<<","<<r.id;for(double v:o.x)os<<","<<v;
 os<<","<<o.buyer_max<<","<<result<<","<<d.quote<<","<<d.margin<<","<<d.total<<","<<d.eligible<<"\n";
 }
 std::ofstream summary(out/"policy_summary.csv");summary<<"policy_id,family,mean_unit_bid_eur,eligible_fraction,mean_gross_margin_fraction\n";
 for(int i=0;i<50;++i)summary<<i+1<<","<<rules[i].family+1<<","<<sum[i]/200<<","<<eligible_cnt[i]/200<<","<<margin_sum[i]/200<<"\n";
 std::ofstream surface(out/"bid_surface.csv");surface<<"quantity,volatility,unit_bid_eur\n";
 // Surface uses actual paceval evaluations with fixed remaining parameters.
 for(int i=0;i<=60;++i)for(int j=0;j<=60;++j){Args a={95,10+i*16.5,4.0,0.13,14,0.02+j*0.006};double v=engine.eval(rules[0].handle,a);audit(v,native(rules[0],a),maxdiff);++scalar;
 surface<<a[1]<<","<<a[5]<<","<<std::setprecision(17)<<v<<"\n";}
 std::ofstream versions(out/"formula_version.csv");versions<<"quantity,version_1_eur,version_2_eur\n";
 for(int q=20;q<=1000;q+=20){Args a={95,double(q),4.0,0.13,14,0.2};double a1=engine.eval(rules[0].handle,a),a2=engine.eval(updated.handle,a);audit(a1,native(rules[0],a),maxdiff);audit(a2,native(updated,a),maxdiff);scalar+=2;versions<<q<<","<<a1<<","<<a2<<"\n";}
 RNG batch_r;for(auto& r:rules){std::vector<Args> in;for(int j=0;j<32;++j)in.push_back(offer(batch_r).x);auto v=engine.batch(r.handle,in);for(int j=0;j<32;++j){audit(v[j],native(r,in[j]),maxdiff);++batch;}}
 // A finite execution-based audit is not an auction equilibrium result.
 std::ofstream log(out/"sdk_execution.txt");log<<std::setprecision(17)<<"STATUS PASS\nGRAPH_COUNT 51\nREQUESTS 10000\nSCALAR_CHECKS "<<scalar<<"\nBATCH_CHECKS "<<batch<<"\nSURFACE_POINTS 3721\nMAX_ABS_NUMERICAL_DIFFERENCE_EUR "<<maxdiff<<"\n";
 std::cout<<"PASS 51 graphs 10000 offers "<<scalar<<" scalar "<<batch<<" batch maxdiff="<<maxdiff<<"\n";
 return 0;
}
}
int main(int argc,char**argv){try{fs::path out="examples";for(int i=1;i<argc;++i){if(std::string(argv[i])=="--out"&&i+1<argc)out=argv[++i];}return run(out);}catch(const std::exception& e){std::cerr<<"FAIL "<<e.what()<<"\n";return 1;}}
