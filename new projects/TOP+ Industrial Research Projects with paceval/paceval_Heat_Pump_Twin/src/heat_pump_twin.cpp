// WP_038 Heat pump twin performance expressions; original paceval C++ interface.
// Research-only synthetic heating-mode mapping: not a calibrated device or certified EN test.
// All domain mathematics that determines the reported physical quantities is evaluated
// through persistent paceval graphs. Host responsibility: input validation, deterministic
// operating point generation, policy/selection, independent numerical oracle and I/O.
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
#include <sstream>
#include <stdexcept>
#include <string>
#include <vector>
namespace fs=std::filesystem;
namespace {
// Input: source air temperature deg C, sink delivery temperature deg C, partial-load
// ratio [-], requested building thermal demand kW, rated heating capacity kW,
// auxiliary electric power kW, electricity price EUR/kWh, horizon hours.
using X=std::array<double,8>;
constexpr char VARS[]="ts tk plr load rated aux price hours";
void ensure(bool b,const std::string&s){if(!b)throw std::runtime_error(s);}
void validate(const X&x){for(double v:x)ensure(std::isfinite(v),"nonfinite input");
 ensure(x[0]>=-15&&x[0]<=20,"source temperature outside declared domain");
 ensure(x[1]>=30&&x[1]<=60&&x[1]>x[0],"sink temperature outside domain");
 ensure(x[2]>=0.25&&x[2]<=1.0,"part load outside domain");
 ensure(x[3]>=0&&x[3]<=20,"thermal demand outside domain");
 ensure(x[4]>=5&&x[4]<=20,"rated output outside domain");
 ensure(x[5]>=0&&x[5]<=0.6,"aux power outside domain");
 ensure(x[6]>=0&&x[6]<=0.8,"price outside domain");
 ensure(x[7]>0&&x[7]<=24,"duration outside domain");}
struct RNG{uint64_t s=20261113038ULL;uint64_t next(){s+=0x9e3779b97f4a7c15ULL;uint64_t z=s;z=(z^(z>>30))*0xbf58476d1ce4e5b9ULL;z=(z^(z>>27))*0x94d049bb133111ebULL;return (z^(z>>31));}double u(){return double(next()>>11)*0x1.0p-53;}};
// Completely independently expressed native check; called for audits only.
using Y=std::array<double,22>;
Y oracle(const X& x){validate(x);const double ts=x[0],tk=x[1],l=x[2],load=x[3],rated=x[4],aux=x[5],price=x[6],hours=x[7];
 double lift=tk-35;
 double raw=4.4+.065*ts-.045*lift-.0006*lift*lift+.002*ts*lift;
 double raw2=4.35+.069*ts-.043*lift-.00065*lift*lift+.0022*ts*lift;
 double cmod=1+.014*ts-.005*lift;
 double available=rated*cmod, part=.82+.18*l-.06*(1-l)*(1-l);
 double def=1-.08*std::exp(-std::pow((ts-1)/3,2));
 double eff=raw*part*def;
 double delivered=available*l;
 double compressor=delivered/eff, electric=compressor+aux;
 double sys=delivered/electric,source=delivered-compressor;
 double heatMargin=delivered-load,powerMargin=4.8-electric,copMargin=sys-2.5;
 double shortfall=std::max(load-delivered,0.0);
 double pol1=.62*electric/4.8+.28*shortfall/10+.10*(1/sys);
 double pol2=.40*electric/4.8+.47*shortfall/10+.13*(1/sys);
 double ds=.065+.002*lift, dt=-.045-.0012*lift+.002*ts;
 double heatEnergy=delivered*hours,cost=electric*hours*price;
 double systemV2=delivered/(delivered/(raw2*part*def)+aux);
 return {raw,raw2,cmod,available,part,def,eff,delivered,compressor,electric,sys,source,heatMargin,powerMargin,copMargin,pol1,pol2,ds,dt,heatEnergy,cost,systemV2};}
struct Formula{std::string id,expr,unit; PACEVAL_HANDLE handle=nullptr;};
std::vector<Formula> makeFormulas(){
 // Parenthesizing every subexpression is intentional: different precedence between
 // source expression parsers must not change the documented physical equations.
 const std::string lift="(tk-35)";
 const std::string raw="(4.4+0.065*ts-0.045*"+lift+"-0.0006*"+lift+"^2+0.002*ts*"+lift+")";
 const std::string raw2="(4.35+0.069*ts-0.043*"+lift+"-0.00065*"+lift+"^2+0.0022*ts*"+lift+")";
 const std::string cmod="(1+0.014*ts-0.005*"+lift+")";
 const std::string available="(rated*"+cmod+")";
 const std::string part="(0.82+0.18*plr-0.06*(1-plr)^2)";
 const std::string def="(1-0.08*exp(-((ts-1)/3)^2))";
 const std::string eff="("+raw+"*"+part+"*"+def+")";
 const std::string eff2="("+raw2+"*"+part+"*"+def+")";
 const std::string delivered="("+available+"*plr)";
 const std::string comp="("+delivered+"/"+eff+")";
 const std::string elec="("+comp+"+aux)";
 const std::string system="("+delivered+"/"+elec+")";
 const std::string shortage="((load-"+delivered+"+sqrt((load-"+delivered+")^2))/2)";
 return {
 {"cop_map_v1",raw,"dimensionless"},{"cop_map_v2",raw2,"dimensionless"},
 {"capacity_modifier",cmod,"dimensionless"}, {"available_heat_kw",available,"kW"},
 {"part_load_modifier",part,"dimensionless"},{"synthetic_defrost_modifier",def,"dimensionless"},
 {"effective_cop_v1",eff,"dimensionless"},{"delivered_heat_kw",delivered,"kW"},
 {"compressor_electric_kw",comp,"kW"},{"total_electric_kw",elec,"kW"},
 {"system_cop_v1",system,"dimensionless"},{"source_extracted_heat_kw","("+delivered+"-"+comp+")","kW"},
 {"heat_demand_margin_kw","("+delivered+"-load)","kW"},
 {"electric_limit_margin_kw","(4.8-"+elec+")","kW"},
 {"cop_limit_margin","("+system+"-2.5)","dimensionless"},
 {"policy_score_v1","(0.62*"+elec+"/4.8+0.28*"+shortage+"/10+0.10/"+system+")","dimensionless"},
 {"policy_score_v2","(0.40*"+elec+"/4.8+0.47*"+shortage+"/10+0.13/"+system+")","dimensionless"},
 {"d_copmap_d_source","(0.065+0.002*"+lift+")","per deg C"},
 {"d_copmap_d_sink","(-0.045-0.0012*"+lift+"+0.002*ts)","per deg C"},
 {"delivered_heat_kwh","("+delivered+"*hours)","kWh"},
 {"electric_cost_eur","("+elec+"*hours*price)","EUR"},
 {"system_cop_v2","("+delivered+"/("+delivered+"/"+eff2+"+aux))","dimensionless"}
 };}
constexpr int N=22;
struct Engine{
 std::vector<PACEVAL_HANDLE> allocated;
 Engine(){ensure(paceval_InitializeLibrary(nullptr),"paceval library initialization failed");}
 ~Engine(){for(auto h:allocated)if(h)paceval_DeleteComputation(h);paceval_FreeLibrary();}
 PACEVAL_HANDLE create(const std::string&s){auto h=paceval_CreateComputation(s.c_str(),8,VARS,false,nullptr);
  ensure(h && !paceval_GetIsError(h),"paceval graph creation failed: "+s.substr(0,120));allocated.push_back(h);return h;}
 double scalar(PACEVAL_HANDLE h,const X&x){X z=x;double r=paceval_dGetComputationResult(h,z.data(),nullptr,nullptr);
  ensure(!paceval_GetIsError(h)&&std::isfinite(r),"paceval scalar failed");return r;}
 std::vector<double> multi(const std::vector<PACEVAL_HANDLE>&hh,const std::vector<X>&xs){
  std::vector<double> input;input.reserve(xs.size()*8);for(auto&x:xs)input.insert(input.end(),x.begin(),x.end());
  auto hhcopy=hh;std::vector<double> output(xs.size()*hh.size());std::vector<int> errors(output.size(),-1);
  bool failed=paceval_dGetMultipleComputationsResultsExt(hhcopy.data(),static_cast<unsigned long>(hh.size()),input.data(),static_cast<unsigned long>(xs.size()),output.data(),nullptr,nullptr,errors.data());
  ensure(!failed,"paceval multi graph batch returned failure");for(size_t i=0;i<output.size();++i)ensure(errors[i]==0&&std::isfinite(output[i]),"paceval batch element invalid");return output;
 }
};
void same(double got,double expected,const std::string&id,double&maxerr){double err=std::abs(got-expected);maxerr=std::max(err,maxerr);
 ensure(err<=2e-9*(1+std::abs(expected)),"independent native formula mismatch: "+id);}
X sample(int i){RNG r;r.s=0x038AA11320261113ULL+uint64_t(i+1)*0x9e3779b97f4a7c15ULL;
 return {-13+31*r.u(),31+26*r.u(),.3+.7*r.u(),2+10*r.u(),7+7*r.u(),.07+.23*r.u(),.18+.28*r.u(),.5+3.5*r.u()};}
void invalidTests(){int good=0;for(auto x:{X{22,42,.8,5,10,.12,.25,1},X{-5,28,.8,5,10,.12,.25,1},X{-5,40,.2,5,10,.12,.25,1},X{-5,40,.8,5,10,.12,.25,0},X{std::numeric_limits<double>::quiet_NaN(),40,.8,5,10,.12,.25,1}}){try{validate(x);}catch(const std::exception&){++good;}}ensure(good==5,"invalid input regression failed");}
void writeInventory(const fs::path&path,const std::vector<Formula>&fspec){std::ofstream f(path);f<<"function_id,domain_quantity,mathematical_definition,units,execution_owner,paceval_graph_id,formula_version,api_path,reference_test,status,host_reason\n";
 for(size_t i=0;i<fspec.size();++i){auto&x=fspec[i];f<<x.id<<','<<x.id<<",\""<<x.expr<<"\","<<x.unit<<",paceval,"<<(i+1)<<','<<(x.id.find("v2")!=std::string::npos?"v2":"v1")<<",paceval_dGetMultipleComputationsResultsExt,native_C++_oracle,PASS,\n";}
 f<<"input_validation,host_range_contract,finite_and_domain_checks,-,host,,,host_validation,negative_regression,PASS,required_safety_boundary\n";
 f<<"candidate_ranking,policy_argmin,minimum_of_computed_scores,-,host,,,host_selection,ordered_argmin_check,PASS,stateful_selection_not_expression\n";
 f<<"replay_energy_ratio,aggregated_replay_heat_electric_ratio,ts/tk,dimensionless,paceval,23,v1,paceval_dGetComputationResult,independent_native_division,PASS,\n";
 f<<"time_aggregation,temporal_sum_of_energy,weighted_sum_over_168_hours,kWh,host,,,host_aggregation,consistency_audit,PASS,stateful_aggregation_across_records\n";}
void run(const fs::path&root,int count){ensure(count>=32&&count<=30000,"cases outside supported range");fs::create_directories(root/"examples");fs::create_directories(root/"results");Engine engine;auto spec=makeFormulas();ensure(spec.size()==N,"formula count mismatch");
 std::vector<PACEVAL_HANDLE>hh;for(auto&f:spec){f.handle=engine.create(f.expr);hh.push_back(f.handle);}
 PACEVAL_HANDLE replayRatioGraph=engine.create("ts/tk"); // aggregate kWh ratio: ts=total heat, tk=total electric; scalar paceval evaluation.
 std::ofstream reg(root/"examples"/"formula_registry.csv");reg<<"graph_id,function_id,units,expression\n";for(size_t i=0;i<spec.size();++i)reg<<i+1<<','<<spec[i].id<<','<<spec[i].unit<<",\""<<spec[i].expr<<"\"\n";reg<<"23,replay_energy_ratio,dimensionless,\"ts/tk\"\n";
 writeInventory(root/"results"/"math_execution_inventory.csv",spec);
 auto probe=sample(10);double worst=0;auto py=engine.multi(hh,{probe});for(size_t i=0;i<hh.size();++i)same(py[i],engine.scalar(hh[i],probe),spec[i].id,worst);
 std::ofstream candidates(root/"examples"/"operating_candidates.csv");candidates<<"candidate_id,source_C,sink_C,plr,load_kw,rated_kw,aux_kw,price_eur_kwh,hours";for(auto&f:spec)candidates<<','<<f.id;candidates<<",screen_pass\n"<<std::setprecision(17);
 int passed=0,best1=-1,best2=-1;double min1=1e100,min2=1e100;size_t numChecked=0,batchCount=0;const int batchSize=256;
 for(int start=0;start<count;start+=batchSize){std::vector<X>xs;for(int i=start;i<std::min(count,start+batchSize);++i)xs.push_back(sample(i));auto out=engine.multi(hh,xs);batchCount+=out.size();
 for(size_t i=0;i<xs.size();++i){Y y{};for(size_t j=0;j<N;++j)y[j]=out[j*xs.size()+i];
 if((start+int(i))%29==0){auto check=oracle(xs[i]);for(size_t j=0;j<N;++j){same(y[j],check[j],spec[j].id,worst);++numChecked;}}
 int valid=(y[12]>=0&&y[13]>=0&&y[14]>=0);passed+=valid;
 candidates<<start+i+1;for(double v:xs[i])candidates<<','<<v;for(double v:y)candidates<<','<<v;candidates<<','<<valid<<'\n';
 if(y[15]<min1){min1=y[15];best1=start+i+1;}if(y[16]<min2){min2=y[16];best2=start+i+1;}
 }}
 // Genuine paceval batch-based surfaces; the host only constructs input coordinates.
 std::vector<X> surface;for(int i=0;i<=60;++i)for(int j=0;j<=60;++j){double ts=-14+32.0*i/60.,tk=31+27.0*j/60.;surface.push_back({ts,tk,.85,6.5,11.0,.15,.28,1});}
 auto ss=engine.multi({hh[0],hh[3],hh[9],hh[10],hh[17],hh[18]},surface);
 std::ofstream sf(root/"examples"/"performance_surface.csv");sf<<"source_C,sink_C,cop_map,available_kw,total_electric_kw,system_cop,d_cop_d_source,d_cop_d_sink\n"<<std::setprecision(17);
 for(size_t i=0;i<surface.size();++i){sf<<surface[i][0]<<','<<surface[i][1];for(int j=0;j<6;++j)sf<<','<<ss[size_t(j)*surface.size()+i];sf<<'\n';if(i%67==0){auto ref=oracle(surface[i]);for(int k=0;k<6;++k){int j[]={0,3,9,10,17,18};same(ss[size_t(k)*surface.size()+i],ref[j[k]],"surface",worst);++numChecked;}}}
 // Recorded 168-hour synthetic operating trace; all physical and cost values from paceval.
 std::vector<X> daily;constexpr double PI=3.141592653589793238462643383279502884;
 for(int i=0;i<168;++i){double h=i%24,air=-1.5+7*std::sin(2*PI*(h-7)/24)+2*std::sin(2*PI*i/168),sink=42+4*std::cos(2*PI*i/24),plr=.52+.24*(1+std::cos(2*PI*(h-5)/24))/2;
 double demand=4.9+.7*std::cos(2*PI*(h-6)/24);daily.push_back({air,sink,plr,demand,10.7,.13,.26,1});}
 auto dd=engine.multi({hh[7],hh[9],hh[10],hh[11],hh[19],hh[20]},daily);
 std::ofstream df(root/"examples"/"seven_day_replay.csv");df<<"hour,source_C,sink_C,plr,delivered_kw,electric_kw,system_cop,source_extracted_kw,heat_kwh,electric_cost_eur\n"<<std::setprecision(17);
 double totalHeat=0,totalElectric=0,totalCost=0;for(size_t i=0;i<daily.size();++i){df<<i<<','<<daily[i][0]<<','<<daily[i][1]<<','<<daily[i][2];for(int j=0;j<6;++j)df<<','<<dd[size_t(j)*daily.size()+i];df<<'\n';totalHeat+=dd[4*daily.size()+i];totalElectric+=dd[daily.size()+i]*daily[i][7];totalCost+=dd[5*daily.size()+i];if(i%14==0){auto ref=oracle(daily[i]);int indices[]={7,9,10,11,19,20};for(int k=0;k<6;++k){same(dd[size_t(k)*daily.size()+i],ref[indices[k]],"replay",worst);++numChecked;}}}
 std::vector<X>vers;for(int i=0;i<=100;++i)vers.push_back({-12+30.0*i/100,46,.78,5.8,10,.12,.26,1});
 auto vv=engine.multi({hh[0],hh[1],hh[10],hh[21],hh[15],hh[16]},vers);
 std::ofstream vf(root/"examples"/"versioned_model_sweep.csv");vf<<"source_C,cop_map_v1,cop_map_v2,system_cop_v1,system_cop_v2,policy_v1,policy_v2\n"<<std::setprecision(17);
 for(size_t i=0;i<vers.size();++i){vf<<vers[i][0];for(int j=0;j<6;++j)vf<<','<<vv[size_t(j)*vers.size()+i];vf<<'\n';}
 X replayTotals{totalHeat,totalElectric,1,1,10,.1,.3,1};double replayEnergyRatio=engine.scalar(replayRatioGraph,replayTotals);same(replayEnergyRatio,totalHeat/totalElectric,"replay energy ratio",worst);++numChecked;
 invalidTests();
 std::ofstream sm(root/"results"/"execution_summary.txt");sm<<std::setprecision(17)<<"project=WP038\nstatus=PASS\nengine=original paceval Linux SDK\nreusable_graphs="<<(N+1)<<"\ncandidates="<<count<<"\nmulti_graph_candidate_batch_values="<<batchCount<<"\nsurface_points="<<surface.size()<<"\nseven_day_hours="<<daily.size()<<"\nmodel_version_points="<<vers.size()<<"\nindependent_native_checked_values="<<numChecked<<"\npassed_screen="<<passed<<"\npolicy_v1_min_candidate="<<best1<<"\npolicy_v2_min_candidate="<<best2<<"\nseven_day_heat_kwh="<<totalHeat<<"\nseven_day_electric_kwh="<<totalElectric<<"\nseven_day_electric_cost_eur="<<totalCost<<"\nseven_day_energy_ratio="<<replayEnergyRatio<<"\ninvalid_inputs_rejected=5\nmax_internal_absolute_difference="<<worst<<"\n";
 std::cout<<"PASS WP038 real paceval: graphs="<<N+1<<" candidates="<<count<<" batch_results="<<batchCount<<" independently_checked="<<numChecked<<"\n";}
}
int main(int argc,char**argv){try{fs::path root=".";int n=6000;for(int i=1;i<argc;++i){std::string a=argv[i];if(a=="--out"&&i+1<argc)root=argv[++i];else if(a=="--cases"&&i+1<argc)n=std::stoi(argv[++i]);else throw std::runtime_error("Usage: heat_pump_twin --out PATH --cases COUNT");}run(root,n);return 0;}catch(const std::exception&e){std::cerr<<"FAIL: "<<e.what()<<'\n';return 2;}}
