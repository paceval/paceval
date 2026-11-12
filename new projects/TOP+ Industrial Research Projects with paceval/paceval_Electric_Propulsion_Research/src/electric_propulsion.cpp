// WP030 - electric-propulsion mathematical performance-map demonstrator.
// Original paceval API builds and evaluates persistent mathematical graph handles.
// The application owns the deterministic synthetic inputs, validation, controls,
// plots/CSV output and independent reference arithmetic. NO plasma simulation,
// calibrated thruster test bench, mission optimization, or lifetime model.
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
constexpr double G0=9.80665;  // conventional standard gravity in m/s^2
// Inputs: P in watts and total propellant flow in mg/s (anode + cathode).
using X=std::array<double,2>;
constexpr char VARS[]="p m";
void require(bool b,const std::string& msg){if(!b)throw std::runtime_error(msg);}
void contract(X x){require(std::isfinite(x[0])&&std::isfinite(x[1]),"non-finite inputs");
 require(x[0]>=500&&x[0]<=3000&&x[1]>=2&&x[1]<=8,"out-of-range operating point");}
struct Rule {int id=0,family=0,version=1;double base=0,peak=0;std::string expression;PACEVAL_HANDLE handle=nullptr;};
// A deliberately SYNTHETIC smooth local efficiency map, not a fitted Hall-thruster map.
// eta is the total jet-power / total input-electric-power ratio. Both power and
// flow denominators remain strictly positive over the declared operating region.
double efficiency(double p,double m,double base,double peak){
 const double dp=(p-1700)/900, dm=(m-4.5)/2;
 return base+peak*std::exp(-(dp*dp+dm*dm));}
double oracle(const Rule& r,X x){
 const double p=x[0], m=x[1],mdot=m*1e-6;
 const double eta=efficiency(p,m,r.base,r.peak);
 const double thrust=std::sqrt(2*eta*p*mdot);  // newtons, derived from jet-power identity
 switch(r.family){
 case 0:return eta;
 case 1:return 1000*thrust;              // mN
 case 2:return thrust/(mdot*G0);         // seconds
 case 3:return thrust*1e6/p;            // mN/kW
 default:return p*(1-eta);              // W; complementary energy proxy, NOT hardware thermal map
 }}
std::string expr(const Rule& r){
 std::ostringstream o;o<<std::setprecision(17);
 o<<"("<<r.base<<"+"<<r.peak<<"*exp(-(((p-1700)/900)^2+((m-4.5)/2)^2)))";
 const std::string e=o.str();
 switch(r.family){
 case 0:return e;
 case 1:return "1000*sqrt(2*"+e+"*p*m*0.000001)";
 case 2:return "sqrt(2*"+e+"*p*m*0.000001)/(m*0.000001*9.80665)";
 case 3:return "1000000*sqrt(2*"+e+"*p*m*0.000001)/p";
 default:return "p*(1-"+e+")";
 }}
std::vector<Rule> defineRules(){std::vector<Rule> rules;
 for(int family=0;family<5;++family)for(int j=0;j<10;++j){
  Rule r;r.id=family*10+j+1;r.family=family;r.base=0.33+0.005*j;
  r.peak=0.17-0.003*j;r.expression=expr(r);rules.push_back(r);}
 return rules;}
class Paceval {
 std::vector<PACEVAL_HANDLE> active;
public:
 Paceval(){require(paceval_InitializeLibrary(nullptr),"paceval_InitializeLibrary failed");}
 ~Paceval(){for(auto h:active)if(h)paceval_DeleteComputation(h);paceval_FreeLibrary();}
 PACEVAL_HANDLE create(const std::string& f){
  auto h=paceval_CreateComputation(f.c_str(),2,VARS,false,nullptr);
  require(h!=nullptr && !paceval_GetIsError(h),"paceval CreateComputation failed: "+f);
  active.push_back(h);return h;
 }
 double value(PACEVAL_HANDLE h,X x){
  double y=paceval_dGetComputationResult(h,x.data(),nullptr,nullptr);
  require(!paceval_GetIsError(h)&&std::isfinite(y)&&y>=0,"paceval scalar result invalid");return y;
 }
 std::vector<double> batch(PACEVAL_HANDLE h,const std::vector<X>& xs){
  std::vector<double> packed(xs.size()*2),result(xs.size());
  std::vector<int> status(xs.size(),-1);
  for(size_t i=0;i<xs.size();++i){packed[2*i]=xs[i][0];packed[2*i+1]=xs[i][1];}
  bool failure=paceval_dGetComputationResultExt(h,packed.data(),(unsigned long)xs.size(),result.data(),nullptr,nullptr,status.data());
  require(!failure,"paceval batch call failed");
  for(size_t i=0;i<xs.size();++i)require(status[i]==0&&std::isfinite(result[i])&&result[i]>=0,"invalid batch entry");
  return result;
 }
};
struct RNG {uint64_t state=20261112;uint64_t next(){state^=state>>12;state^=state<<25;state^=state>>27;return state*2685821657736338717ULL;}double unit(){return (next()>>11)*0x1.0p-53;}};
X sample(RNG& r){return {500+2500*r.unit(),2+6*r.unit()};}
void compare(double actual,double ref,double& worst){
 const double diff=std::abs(actual-ref);worst=std::max(worst,diff);
 require(diff<=1e-9*(1+std::abs(ref)),"independent native formula check failed");}
void run(fs::path out,int n){
 fs::create_directories(out);Paceval engine;auto rules=defineRules();
 for(auto& r:rules)r.handle=engine.create(r.expression);
 Rule revision=rules[10];revision.id=51;revision.version=2;revision.base+=0.025;
 revision.expression=expr(revision);revision.handle=engine.create(revision.expression);
 std::ofstream reg(out/"rule_registry.csv");reg<<"rule_id,family,version,eta_base,eta_peak,formula\n";
 for(const auto& r:rules)reg<<r.id<<','<<r.family+1<<','<<r.version<<','<<r.base<<','<<r.peak<<",\""<<r.expression<<"\"\n";
 reg<<revision.id<<","<<revision.family+1<<",2,"<<revision.base<<","<<revision.peak<<",\""<<revision.expression<<"\"\n";
 std::ofstream replay(out/"performance_replay.csv");
 replay<<"update,rule_id,family,power_w,flow_mg_s,value,valid_operating_point\n";
 std::array<double,50> sums{};std::array<int,50> counts{};
 RNG rng;double worst=0;long long scalar=n;int recorded=0;
 for(int i=0;i<n;++i){const Rule& r=rules[i%50];X x=sample(rng);contract(x);
  double y=engine.value(r.handle,x);compare(y,oracle(r,x),worst);
  sums[i%50]+=y;counts[i%50]++;
  if(i<120||i%17==0){replay<<i+1<<','<<r.id<<','<<r.family+1<<','<<std::setprecision(17)<<x[0]<<','<<x[1]<<','<<y<<",1\n";recorded++;}
 }
 std::ofstream families(out/"rule_summary.csv");families<<"rule_id,family,mean_metric\n";
 for(int i=0;i<50;++i)families<<rules[i].id<<','<<rules[i].family+1<<','<<std::setprecision(17)<<sums[i]/counts[i]<<'\n';
 std::ofstream surfaces[5];const char* names[5]={"efficiency","thrust","specific_impulse","thrust_to_power","waste_power"};
 for(int k=0;k<5;++k){surfaces[k].open(out/(std::string(names[k])+"_surface.csv"));surfaces[k]<<"power_w,flow_mg_s,value\n";}
 for(int i=0;i<=60;++i)for(int j=0;j<=60;++j){X x={500+2500*i/60.0,2+6*j/60.0};for(int k=0;k<5;++k){
  const Rule& r=rules[k*10];double y=engine.value(r.handle,x);compare(y,oracle(r,x),worst);
  surfaces[k]<<std::setprecision(17)<<x[0]<<','<<x[1]<<','<<y<<'\n';scalar++;}}
 std::ofstream versions(out/"formula_revision.csv");versions<<"power_w,thrust_original_mn,thrust_revised_mn\n";
 for(int i=0;i<=80;++i){X x={500+2500*i/80.0,4.5};double a=engine.value(rules[10].handle,x),b=engine.value(revision.handle,x);
 compare(a,oracle(rules[10],x),worst);compare(b,oracle(revision,x),worst);
 versions<<std::setprecision(17)<<x[0]<<','<<a<<','<<b<<'\n';scalar+=2;}
 RNG rb;long long batchCount=0;
 for(const auto& r:rules){std::vector<X> xs;for(int j=0;j<32;++j)xs.push_back(sample(rb));
  auto ys=engine.batch(r.handle,xs);for(size_t i=0;i<xs.size();++i){compare(ys[i],oracle(r,xs[i]),worst);batchCount++;}}
 int rejected=0;for(X x:std::vector<X>{{NAN,4},{100,4},{1500,0},{3500,4}}){try{contract(x);}catch(...){rejected++;}}
 require(rejected==4,"host invalid-input rejection failed");
 std::ofstream log(out/"sdk_execution.txt");
 log<<std::setprecision(17)<<"STATUS PASS\nGRAPH_COUNT 51\nREPLAY_UPDATES "<<n
 <<"\nREPLAY_SAMPLED_ROWS "<<recorded<<"\nSCALAR_EVALUATIONS "<<scalar
 <<"\nBATCH_VERIFIED "<<batchCount<<"\nSURFACE_POINTS_PER_METRIC 3721\nSURFACE_METRICS 5"
 <<"\nREJECTED_INVALID_INPUTS "<<rejected<<"\nINTERNAL_MAX_DIFFERENCE "<<worst<<'\n';
 std::cout<<"PASS: "<<n<<" synthetic operating points, 51 paceval graphs, "<<scalar<<" scalar evaluations, "<<batchCount<<" batch checks\n";
}
}
int main(int argc,char**argv){try{fs::path out="examples";int n=10000;
 for(int i=1;i<argc;++i){std::string arg=argv[i];if(arg=="--out"&&i+1<argc)out=argv[++i];else if(arg=="--updates"&&i+1<argc)n=std::stoi(argv[++i]);else throw std::runtime_error("Unknown argument: "+arg);}
 require(n>=50&&n<=250000,"invalid replay count");run(out,n);return 0;
 }catch(const std::exception& e){std::cerr<<"FAIL: "<<e.what()<<'\n';return 1;}}
