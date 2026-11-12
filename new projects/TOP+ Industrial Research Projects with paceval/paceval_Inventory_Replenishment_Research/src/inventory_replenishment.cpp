// WP-023: Inventory replenishment rules, synthetic research pilot.
// Copyright for the official paceval_main.h/.cpp is retained upstream.
// This source intentionally uses the ORIGINAL public paceval C/C++ SDK.
// The host owns discrete inventory state; paceval evaluates reusable formulas.
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
#include <sstream>
#include <stdexcept>
#include <string>
#include <vector>

namespace {
constexpr std::size_t VARS=6;
// ABI variables are mean daily units, standard deviation of daily units,
// lead time (days), review time (days), inventory position (units), and
// daily demand trend (units/day). All scenario inputs are finite and bounded.
constexpr const char* ABI="mu sigma lead review ip trend";
using Args=std::array<double,VARS>;
void check(bool yes, const std::string& reason) { if(!yes) throw std::runtime_error(reason); }
struct RNG {
 std::uint64_t state=20261112ULL;
 std::uint64_t next() {state^=state>>12;state^=state<<25;state^=state>>27;return state*2685821657736338717ULL;}
 double uniform(){return static_cast<double>(next()>>11)*0x1.0p-53;}
};
struct Policy {int id; double z,buffer,trend_scale; int review; bool conditional;};
struct Sku {int id; double mu,sigma,lead,stock,trend;};
// The 30 policies are distinct mathematical contracts: z, buffer, trend
// multiplier, review interval and triggering convention vary deterministically.
std::vector<Policy> policies() {
 std::vector<Policy> result;
 for(int i=0;i<30;++i)
  result.push_back({i+1,0.65+0.105*(i%10),0.1*(i/10),0.1+0.08*(i%5),
     1+(i%3)*3, i%2==0});
 return result;
}
std::vector<Sku> skus(std::size_t n) {
 RNG r;std::vector<Sku> s; s.reserve(n);
 for(std::size_t i=0;i<n;++i) {
  const double mu=8.0+90.0*r.uniform();
  s.push_back({static_cast<int>(i+1),mu, 1.0+0.30*mu*r.uniform(),
           1.0+std::floor(1+7*r.uniform()), 25+8*mu*r.uniform(),
           (r.uniform()-0.5)*0.06*mu});
 }
 return s;
}
// Native formula is separately coded, not a dispatch to the SDK or a parser.
// Order-up-to target includes (L+R) demand, a normal safety-stock proxy,
// a fixed buffer and a simple trend adjustment. No Poisson/normal fit claim.
double native_target(const Policy& p,const Args& a) {
 return a[0]*(a[2]+a[3])+p.z*a[1]*std::sqrt(a[2]+a[3])+
           p.buffer*a[0]+p.trend_scale*a[5]*a[2]-a[4];
}
double native_trigger(const Policy& p,const Args& a) {
 return a[0]*a[2]+p.z*a[1]*std::sqrt(a[2])+p.buffer*a[0]-a[4];
}
// Only simple arithmetic, sqrt and constants enter the paceval expressions.
// Positive-part, pack-size rounding, gates and discrete state updates are
// deliberately implemented by the host and exposed as a contract boundary.
std::string formula(const Policy& p,bool trigger) {
 std::ostringstream o;o<<std::setprecision(17);
 if(trigger) o<<"mu*lead+"<<p.z<<"*sigma*sqrt(lead)+"<<p.buffer<<"*mu-ip";
 else o<<"mu*(lead+review)+"<<p.z<<"*sigma*sqrt(lead+review)+"
       <<p.buffer<<"*mu+"<<p.trend_scale<<"*trend*lead-ip";
 return o.str();
}
class Engine {
 std::vector<PACEVAL_HANDLE> handles;
public:
 Engine(){check(paceval_InitializeLibrary(nullptr),"paceval initialization failed");}
 Engine(const Engine&)=delete;Engine& operator=(const Engine&)=delete;
 ~Engine(){for(auto h:handles) if(h) paceval_DeleteComputation(h);paceval_FreeLibrary();}
 PACEVAL_HANDLE add(const std::string& expr) {
  PACEVAL_HANDLE h=paceval_CreateComputation(expr.c_str(),VARS,ABI,false,nullptr);
  check(h!=nullptr,"paceval null handle: "+expr); handles.push_back(h);
  check(!paceval_GetIsError(h),"paceval graph error: "+expr);return h;
 }
 double eval(PACEVAL_HANDLE h,Args a) {
  double v=paceval_dGetComputationResult(h,a.data(),nullptr,nullptr);
  check(!paceval_GetIsError(h)&&std::isfinite(v),"paceval numerical evaluation failed");return v;
 }
 void audit_batch(PACEVAL_HANDLE h,const std::vector<Args>& rows,
                  const Policy& p,bool trigger,std::size_t& checked,double& maxerr) {
  // API's packed layout: all six variables of sample 0, then sample 1, etc.
  std::vector<double> packed(rows.size()*VARS),res(rows.size());
  std::vector<int> errors(rows.size(),-1);
  for(std::size_t i=0;i<rows.size();++i)
   for(std::size_t j=0;j<VARS;++j) packed[i*VARS+j]=rows[i][j];
  const bool failed=paceval_dGetComputationResultExt(h,packed.data(),
      static_cast<unsigned long>(rows.size()),res.data(),nullptr,nullptr,errors.data());
  check(!failed,"SDK batch evaluation error");
  for(std::size_t i=0;i<rows.size();++i){
   check(errors[i]==0&&std::isfinite(res[i]),"SDK per-sample batch error");
   double reference=trigger?native_trigger(p,rows[i]):native_target(p,rows[i]);
   double d=std::abs(res[i]-reference);maxerr=std::max(maxerr,d);
   check(d<=1e-10*(1+std::abs(reference)),"batch mismatch");++checked;
  }
 }
};
// Policy uses an inventory-position threshold for conditional (s,S) rules.
// Continuous-style order-up-to policies are checked at their declared
// review frequency, NOT continuously at every instant.
double order(const Policy& p, double raw, double threshold_gap) {
 if(p.conditional&&threshold_gap<=0.0) return 0.0;
 return std::ceil(std::max(0.0,raw)); // integer nonnegative units
}
// The simulation uses a frozen deterministic demand path per SKU across
// policies, a fixed integer lead time, lost sales, and a daily review clock.
// It DOES NOT equate fill rate with cycle-service probability.
struct Sim {double fill=0,avg_onhand=0,avg_order=0;int orders=0;};
Sim simulate(const Sku& s,const Policy& p,PACEVAL_HANDLE target,PACEVAL_HANDLE gate,
             Engine& e,int days,bool use_sdk) {
 const int lead=static_cast<int>(s.lead);
 std::vector<double> incoming(days+lead+10,0.0);
 double inventory=std::round(s.stock),demand_total=0,fulfilled=0,stock_total=0,ordered=0;
 int number_of_orders=0;
 RNG random;random.state=20261112ULL+static_cast<std::uint64_t>(s.id)*1000003ULL;
 for(int d=0;d<days;++d){
  inventory+=incoming[d];
  // Deterministic bounded positive demand with SKU-specific state.
  const double seasonal=1.0+0.25*std::sin(2.0*3.141592653589793*(d%30)/30.0);
  const double demand=std::max(0.0,s.mu*seasonal*(0.60+0.8*random.uniform()));
  demand_total+=demand;
  const double served=std::min(inventory,demand);
  fulfilled+=served; inventory-=served; stock_total+=inventory;
  if(d%p.review==0){
   double pipeline=0;for(int future=d+1;future<d+lead+1;++future) pipeline+=incoming[future];
   const Args x={s.mu,s.sigma,s.lead,static_cast<double>(p.review),inventory+pipeline,s.trend};
   const double raw=use_sdk?e.eval(target,x):native_target(p,x);
   const double gap=use_sdk?e.eval(gate,x):native_trigger(p,x);
   const double q=order(p,raw,gap);
   if(q>0){incoming[d+lead]+=q;ordered+=q;++number_of_orders;}
  }
 }
 return {fulfilled/std::max(1.0,demand_total),stock_total/days,ordered/days,number_of_orders};
}
void write_files(const std::filesystem::path& p,const std::vector<Sku>& sk,
                 const std::vector<Policy>& ps,Engine& eng,
                 const std::vector<PACEVAL_HANDLE>& targets,
                 const std::vector<PACEVAL_HANDLE>& gates,
                 std::size_t& scalar,std::size_t& batch,double& maxerr,
                 double& max_fill_error){
 std::ofstream records(p/"scenario_samples.csv"),sim(p/"policy_metrics.csv"),
   surface(p/"replenishment_surface.csv"),versions(p/"policy_registry.csv");
 check(records&&sim&&surface&&versions,"Failed to open output files");
 records<<"policy_id,sku_id,mean_units_per_day,sigma_units_per_day,lead_days,review_days,inventory_position_units,trend_units_per_day,target_minus_position_units,trigger_minus_position_units,order_units\n";
 sim<<"policy_id,sku_id,fill_rate,average_onhand_units,orders_placed,mean_daily_order_units\n";
 surface<<"mean_units_per_day,sigma_units_per_day,order_units,policy_id\n";
 versions<<"policy_id,z_buffer_factor,buffer_in_days,trend_scale,review_days,conditional_trigger,target_formula,trigger_formula\n";
 records<<std::setprecision(17);sim<<std::setprecision(17);surface<<std::setprecision(17);
 for(std::size_t j=0;j<ps.size();++j){
  const auto& pol=ps[j];
  versions<<pol.id<<','<<pol.z<<','<<pol.buffer<<','<<pol.trend_scale<<','<<pol.review<<','<<pol.conditional
          <<",\""<<formula(pol,false)<<"\",\""<<formula(pol,true)<<"\""<<'\n';
  for(std::size_t i=0;i<sk.size();++i){
   const auto& s=sk[i];Args a={s.mu,s.sigma,s.lead,static_cast<double>(pol.review),s.stock,s.trend};
   const double t=eng.eval(targets[j],a),g=eng.eval(gates[j],a);
   const double n=native_target(pol,a),ng=native_trigger(pol,a);
   const double dt=std::abs(t-n),dg=std::abs(g-ng);
   maxerr=std::max({maxerr,dt,dg});
   check(dt<=1e-10*(1+std::abs(n))&&dg<=1e-10*(1+std::abs(ng)),"Scalar/native mismatch");
   scalar+=2;
   // Export a small inspectable subset while auditing the complete workload.
   if(i<60) records<<pol.id<<','<<s.id<<','<<s.mu<<','<<s.sigma<<','<<s.lead<<','<<pol.review<<','<<s.stock<<','<<s.trend<<','<<t<<','<<g<<','<<order(pol,t,g)<<'\n';
  }
  // 32 row packed SDK batch results for each graph, separately audited.
  std::vector<Args> cases;for(std::size_t i=0;i<std::min<std::size_t>(32,sk.size());++i)
   cases.push_back({sk[i].mu,sk[i].sigma,sk[i].lead,static_cast<double>(pol.review),sk[i].stock,sk[i].trend});
  eng.audit_batch(targets[j],cases,pol,false,batch,maxerr);
  eng.audit_batch(gates[j],cases,pol,true,batch,maxerr);
  // Simulation is run with identical frozen demand stream per policy/sku.
  for(std::size_t i=0;i<std::min<std::size_t>(48,sk.size());++i){
   const auto pace=simulate(sk[i],pol,targets[j],gates[j],eng,120,true);
   const auto native=simulate(sk[i],pol,targets[j],gates[j],eng,120,false);
   const double diff=std::max({std::abs(pace.fill-native.fill),
                               std::abs(pace.avg_onhand-native.avg_onhand),
                               std::abs(pace.avg_order-native.avg_order)});
   max_fill_error=std::max(max_fill_error,std::abs(pace.fill-native.fill));
   check(diff<1e-9&&pace.orders==native.orders,"Simulation mismatch");
   sim<<pol.id<<','<<sk[i].id<<','<<pace.fill<<','<<pace.avg_onhand<<','
      <<pace.orders<<','<<pace.avg_order<<'\n';
  }
 }
 const auto& pol=ps[14];
 for(int i=0;i<61;++i)for(int k=0;k<61;++k){
  const double mu=8+1.5*i,sigma=1+0.6*k;
  Args a={mu,sigma,5.0,static_cast<double>(pol.review),170.0,0.0};
  const double t=eng.eval(targets[14],a),g=eng.eval(gates[14],a);
  surface<<mu<<','<<sigma<<','<<order(pol,t,g)<<','<<pol.id<<'\n';
  ++scalar;
 }
}
} // namespace
int main(int argc,char**argv){
 try{
  std::filesystem::path out="results";std::size_t sku_count=3500;
  for(int i=1;i<argc;++i){const std::string x=argv[i];
   if(x=="--test")sku_count=80;
   else if(x=="--skus"&&i+1<argc)sku_count=std::stoull(argv[++i]);
   else if(x=="--out"&&i+1<argc)out=argv[++i];
   else {std::cerr<<"Usage: inventory_replenishment [--test] [--skus 3500] [--out directory]\n";return 2;}}
  check(sku_count>=32&&sku_count<=100000,"Invalid SKU count");
  std::filesystem::create_directories(out);
  const auto sk=skus(sku_count);const auto ps=policies();
  std::size_t scalar=0,batch=0;double maxerr=0,fillerr=0;
  {
   Engine e;std::vector<PACEVAL_HANDLE> targets,gates;
   for(const auto& p:ps){targets.push_back(e.add(formula(p,false)));
                         gates.push_back(e.add(formula(p,true)));}
   write_files(out,sk,ps,e,targets,gates,scalar,batch,maxerr,fillerr);
  }
  std::ofstream f(out/"sdk_execution.txt");
  f<<std::setprecision(17)<<"WP023 paceval SDK synthetic inventory research\n"
   <<"policies=30\npersistent_graphs=60\nscenarios="<<sku_count*30<<"\n"
   <<"scalar_audits="<<scalar<<"\nbatch_audits="<<batch<<"\n"
   <<"maximum_absolute_formula_error_units="<<maxerr<<"\n"
   <<"maximum_absolute_fill_rate_difference="<<fillerr<<"\n"
   <<"simulation_policy_sku_pairs=1440\n"
   <<"synthetic_data_only=true\nno_performance_claims=true\n";
  std::cout<<"PASS WP023 policies=30 graph_handles=60 scenarios="<<sku_count*30
           <<" scalar="<<scalar<<" batch="<<batch<<" max_formula_error="<<maxerr
           <<" max_fillrate_difference="<<fillerr<<'\n';
  return 0;
 }catch(const std::exception& e){std::cerr<<"ERROR: "<<e.what()<<'\n';return 1;}
}
