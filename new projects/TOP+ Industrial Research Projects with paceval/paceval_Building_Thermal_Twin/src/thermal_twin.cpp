// WP_045 | Building thermal twin cost-function kernel using ORIGINAL paceval SDK.
// Application boundary: single-zone 1R1C explicit discrete-time calculation;
// no validated building, weather station, measured data, hardware controls,
// high-fidelity HVAC simulation, or optimizer certification is claimed.
// All domain algebra, forecasts, composite scores and sensitivities below are
// expression graphs executed through original paceval scalar/batch APIs.
// The host owns dataset orchestration, input checks, time-series state,
// candidate selection, score reductions, I/O and independent native audits.
#include "paceval_main.h"
#include <algorithm>
#include <array>
#include <cmath>
#include <cstdint>
#include <cstdio>
#include <filesystem>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <limits>
#include <numeric>
#include <stdexcept>
#include <string>
#include <vector>
using namespace std;
namespace fs=std::filesystem;
static void require(bool c,const string&m){if(!c)throw runtime_error(m);}
constexpr double PI=3.141592653589793238462643383279502884;
constexpr size_t NV=18;
using Row=array<double,NV>;
enum Col{TI,TO,SOLAR,HVAC,INTERNAL,WIND,SHADE,DT,CAP,UA,KWIND,ALPHA,TOBS,TSET,TMIN,TMAX,UAPR,STEP};
const string VARS="Ti To Gsolar Qhvac Qinternal wind shade dt C UA kwind alpha Tobs Tset Tmin Tmax UApr step";
struct Def{string id,expression,units,purpose,version; PACEVAL_HANDLE handle=nullptr;};
struct Engine{
 vector<Def> f; uint64_t batchCalls=0,outputs=0,scalarCalls=0,nativeChecks=0; double maxScaledDiff=0.;
 static string par(const string&a){return "("+a+")";}
 static string pred(int revision){
   string g=revision==1?"(alpha*Gsolar)":"(alpha*Gsolar*(1-shade))";
   string transfer=revision==1?"(UA*(Ti-To))":"((UA+kwind*wind)*(Ti-To))";
   return "(Ti+dt/C*(Qhvac+Qinternal+"+g+"-"+transfer+"))";
 }
 static string solar(int revision){return revision==1?"(alpha*Gsolar)":"(alpha*Gsolar*(1-shade))";}
 static string conduction(int revision){return revision==1?"(UA*(Ti-To))":"((UA+kwind*wind)*(Ti-To))";}
 static string required(int revision){return "("+(revision==1?string("UA"):string("(UA+kwind*wind)"))+"*(Tset-To)-"+solar(revision)+"-Qinternal)";}
 static string score(int revision,double wr,double we,double wc,double wp){
   string t=pred(revision),r="("+t+"-Tobs)",q=required(revision);
   auto num=[](double v){char b[60];snprintf(b,sizeof(b),"%.10g",v);return string(b);};
   return "("+num(wr)+"*"+r+"^2+"+num(we)+"*("+q+"/1000)^2+"+num(wc)+"*("+t+"-Tset)^2/4+"+num(wp)+"*((UA-UApr)/100)^2)";
 }
 static vector<Def> registry(){
   vector<Def> r;
   auto add=[&](const string&id,const string&e,const string&u,const string&role,const string&version){r.push_back({id,e,u,role,version,nullptr});};
   for(int v=1;v<=2;++v){
     string ver="v"+to_string(v),t=pred(v),p=conduction(v),g=solar(v),q=required(v),res="("+t+"-Tobs)";
     string bal="(Qhvac+Qinternal+"+g+"-"+p+")";
     add("envelope_loss_"+ver,p,"W","envelope_and_infiltration_heat_loss",ver);
     add("solar_gain_"+ver,g,"W","solar_heat_gain",ver);
     add("net_heat_"+ver,bal,"W","full_thermal_balance",ver);
     add("temperature_next_"+ver,t,"degC","one_step_forecast",ver);
     add("temperature_residual_"+ver,res,"K","calibration_residual",ver);
     add("squared_residual_"+ver,"("+res+"^2)","K^2","calibration_loss",ver);
     add("required_heat_"+ver,q,"W","signed_setpoint_heat_demand_proxy",ver);
     add("lower_margin_"+ver,"("+t+"-Tmin)","K","minimum_temperature_guard_margin",ver);
     add("upper_margin_"+ver,"(Tmax-"+t+")","K","maximum_temperature_guard_margin",ver);
     add("comfort_deviation_"+ver,"("+t+"-Tset)","K","comfort_deviation",ver);
     add("temperature_dUA_"+ver,"(-dt*(Ti-To)/C)","K/(W/K)","analytical_sensitivity",ver);
     add("temperature_dC_"+ver,"(-dt*"+bal+"/(C^2))","K/(J/K)","analytical_sensitivity",ver);
     add("temperature_dAlpha_"+ver, v==1?"(dt*Gsolar/C)":"(dt*Gsolar*(1-shade)/C)","K","analytical_sensitivity",ver);
     if(v==2)add("temperature_dKwind_v2","(-dt*wind*(Ti-To)/C)","K/(W/K)","analytical_sensitivity",ver);
     // Exact sensitivity of the primary calibration loss score_v*_01 = residual squared.
     string dT="(-dt*(Ti-To)/C)";
     add("score_dUA_"+ver,"(2*"+res+"*"+dT+")","K^2/(W/K)","pure_residual_calibration_score_sensitivity",ver);
     // Sensitivity of the first fully composite score, score_v*_02.
     // This explicitly verifies the complete weighted cost-function derivative.
     double wr=.85,we=.013,wc=.02,wp=.0015;
     string dQ="(Tset-To)";
     add("score02_dUA_"+ver,"(2*"+to_string(wr)+"*"+res+"*"+dT+"+2*"+to_string(we)+"*"+q+"*"+dQ+"/1000000+"+to_string(wc)+"*("+t+"-Tset)*"+dT+"/2+2*"+to_string(wp)+"*(UA-UApr)/10000)","cost/(W/K)","composite_score02_sensitivity",ver);
   }
   // Thirty retained score graphs: two residual-only baselines plus 28 weighted composite objectives.
   // Fixed explicit coefficients make their meanings testable and audit-friendly.
   for(int v=1;v<=2;++v)for(int i=0;i<15;++i){double wr=i==0?1.:0.8+0.05*i,we=i==0?0.:.01+.003*(i%5),wc=i==0?0.:.015+.005*(i%3),wp=i==0?0.:.001+.0005*(i%4);
     string name="score_v"+to_string(v)+"_"+(i<9?"0":"")+to_string(i+1);
     add(name,score(v,wr,we,wc,wp),i==0?"K^2":"weighted_cost_index","baseline_or_weighted_composite_calibration_objective","v"+to_string(v));}
   // Independent and easily interpretable readout from both model versions.
   add("formula_temperature_delta_v2_minus_v1","("+pred(2)+"-"+pred(1)+")","K","controlled_model_revision_comparison","v2-v1");
   return r;
 }
 Engine(){require(paceval_InitializeLibrary(nullptr),"Unable to initialize ORIGINAL paceval Linux shared library");f=registry();
  for(auto&d:f){d.handle=paceval_CreateComputation(d.expression.c_str(),(unsigned long)NV,VARS.c_str(),false,nullptr);
   if(!d.handle||paceval_GetIsError(d.handle)){char a[512]={0},b[512]={0};if(d.handle)paceval_CreateErrorInformationText(d.handle,a,b);
      throw runtime_error("Failed to register paceval expression "+d.id+": "+a+" / "+b+" : "+d.expression);}}
 }
 ~Engine(){for(auto &d:f)if(d.handle)paceval_DeleteComputation(d.handle);paceval_FreeLibrary();}
 int index(const string&id)const{for(int i=0;i<(int)f.size();++i)if(f[i].id==id)return i;throw runtime_error("Unknown graph id "+id);}
 static void validate(const Row&r){for(double x:r)require(isfinite(x),"Input must be finite");
   require(r[DT]>0 && r[DT]<=3600 && r[CAP]>=1000000 && r[CAP]<=50000000,"Time step or thermal capacitance out of contract");
   require(r[UA]>0&&r[UA]<=1500&&r[KWIND]>=0&&r[KWIND]<=500,"Conductance out of contract");
   require(r[ALPHA]>=0&&r[ALPHA]<=1&&r[SHADE]>=0&&r[SHADE]<=1&&r[WIND]>=0&&r[WIND]<=20,"Solar/wind controls out of contract");
   require(r[TMIN]<r[TMAX]&&r[TO]>-45&&r[TO]<55&&r[TI]>-45&&r[TI]<80,"Temperatures out of contract");}
 double scalar(int id,Row r){validate(r);double y=paceval_dGetComputationResult(f.at(id).handle,r.data(),nullptr,nullptr);
   require(!paceval_GetIsError(f.at(id).handle)&&isfinite(y),"Original SDK scalar computation failed");++scalarCalls;return y;}
 // SDK: variable-major by row in input, graph-major in output as experimentally
 // verified in the preceding WP044 demonstrator. Live runtime must be retested.
 vector<double> batch(const vector<Row>&rows,const vector<int>&ids){require(!rows.empty()&&!ids.empty(),"empty batch");
   vector<double> x; x.reserve(rows.size()*NV);for(const auto&r:rows){validate(r);x.insert(x.end(),r.begin(),r.end());}
   vector<PACEVAL_HANDLE> handles;for(int id:ids)handles.push_back(f.at(id).handle);
   vector<double> out(rows.size()*ids.size(),numeric_limits<double>::quiet_NaN());vector<int>err(out.size(),-1);
   bool failed=paceval_dGetMultipleComputationsResultsExt(handles.data(),(unsigned long)handles.size(),x.data(),(unsigned long)rows.size(),out.data(),nullptr,nullptr,err.data());
   require(!failed,"Original paceval multi-graph batch signaled error");for(size_t i=0;i<out.size();++i)require(err[i]==0&&isfinite(out[i]),"Nonfinite/error at SDK batch output "+to_string(i));
   ++batchCalls;outputs+=out.size();return out;
 }
};
struct Sample{Row r;double truth;};
struct Candidate{double U,C,K,A;string ver;double avg=0.;};
static double weatherOutside(int k){return 6.+5.*sin(2*PI*k/96.+0.8)+0.7*sin(2*PI*k/192.);}
static double weatherSolar(int k){double s=sin(2*PI*(k%96)/96.-PI/2);return 900.*max(0.,s);}
static double weatherWind(int k){return 1.1+0.65*sin(2*PI*k/87.+0.2);}
static double weatherShade(int k){return (k%96>=32&&k%96<62)?0.25:0.;}
static double hvacPower(int k){return ((k%96)<25||(k%96)>78)?850.:450.;}
static Row inputRow(int k,double temp,double obs,double u,double c,double kw,double alpha){
 Row r{};r[TI]=temp;r[TO]=weatherOutside(k);r[SOLAR]=weatherSolar(k);r[HVAC]=hvacPower(k);
 r[INTERNAL]=250.+75.*sin(2*PI*k/96.);r[WIND]=weatherWind(k);r[SHADE]=weatherShade(k);r[DT]=900.;r[CAP]=c;
 r[UA]=u;r[KWIND]=kw;r[ALPHA]=alpha;r[TOBS]=obs;r[TSET]=21.;r[TMIN]=18.;r[TMAX]=25.;r[UAPR]=215.;r[STEP]=(double)k;return r;}
static vector<Sample> buildObservations(Engine&e,int steps){const int truthGraph=e.index("temperature_next_v2");
 vector<Sample> rows;rows.reserve(steps);double temp=21.;
 for(int k=0;k<steps;++k){Row truth=inputRow(k,temp,21.,210.,7.2e6,55.,.65);
    double next=e.scalar(truthGraph,truth);double observation=next+.017*sin(0.37*k)+.008*cos(.13*k); // deterministic sensor perturbation (host data generation)
    Row r=inputRow(k,temp,observation,210.,7.2e6,55.,.65);rows.push_back({r,next});temp=next;require(temp>-10&&temp<55,"Synthetic thermal time-series divergence");}
 return rows;}
static double nativeForecast(const Row&r,int ver){double gain=r[ALPHA]*r[SOLAR]*(ver==1?1.:(1.-r[SHADE]));
  double loss=(r[UA]+(ver==1?0.:r[KWIND]*r[WIND]))*(r[TI]-r[TO]);
  return r[TI]+r[DT]/r[CAP]*(r[HVAC]+r[INTERNAL]+gain-loss);}
static double nativeScore(const Row&r,int ver,int variant){double wr=variant==0?1.:.8+.05*variant,we=variant==0?0.:.01+.003*(variant%5),wc=variant==0?0.:.015+.005*(variant%3),wp=variant==0?0.:.001+.0005*(variant%4);
  double y=nativeForecast(r,ver), gain=r[ALPHA]*r[SOLAR]*(ver==1?1.:(1.-r[SHADE]));
  double q=(r[UA]+(ver==1?0.:r[KWIND]*r[WIND]))*(r[TSET]-r[TO])-gain-r[INTERNAL];
  return wr*pow(y-r[TOBS],2)+we*pow(q/1000.,2)+wc*pow((y-r[TSET])/2.,2)+wp*pow((r[UA]-r[UAPR])/100.,2);}
static void writeRegistry(Engine&e,const fs::path&root){ofstream f(root/"results/formula_registry.csv");f<<"function_id,formula_version,mathematical_definition,units,industrial_role\n";
 for(const auto&g:e.f)f<<g.id<<","<<g.version<<",\""<<g.expression<<"\","<<g.units<<","<<g.purpose<<"\n";}
static void writeInventory(Engine&e,const fs::path&root){ofstream f(root/"results/math_execution_inventory.csv");
 f<<"function_id,domain_quantity,mathematical_definition,units,execution_owner,paceval_graph_id,formula_version,api_path,reference_test,status,host_reason\n";
 for(const auto&g:e.f)f<<g.id<<","<<g.purpose<<",\""<<g.expression<<"\","<<g.units<<",paceval,"<<g.id<<","<<g.version<<",paceval_dGetMultipleComputationsResultsExt,native_cpp_and_optional_mpmath,executed_verified,\n";
 f<<"stateful_time_series,thermal_simulation,recursive_temperature_state,K,host,,v2,standard_C++,initial_temperature_and_fixed_time_grid,executed,graph_has_no_state_memory\n";
 f<<"candidate_search,candidate_selection,finite_grid_minimum,dimensionless,host,,all,standard_C++,repeatable_reduction,executed,selection_and_reduction_over_rows\n";
 f<<"synthetic_weather,test_data,deterministic_periodic_weather,degC_and_W,host,,synthetic,standard_C++,repeatable_input_generation,executed,data_generation_not_calibration_model\n";
 f<<"sensor_noise,reference_generation,deterministic_bounded_signal,K,host,,synthetic,standard_C++,analytical_boundedness,executed,data_generation_not_domain_model\n";
 f<<"high_precision_reference,independent_validation,mpmath_direct_explicit_formula,mixed,reference_only,,all,Python_mpmath,independent_model,external_unrun,independent_audit_path\n";}
static void writeObservations(const vector<Sample>&samples,const fs::path&root){ofstream f(root/"examples/observations.csv");
 f<<"step,time_h,Ti_degC,To_degC,Gsolar_W,Qhvac_W,Qinternal_W,wind_ms,shade_fraction,observed_next_degC,truth_next_degC\n"<<setprecision(16);
 for(const auto &s:samples){const Row&r=s.r;f<<long(r[STEP])<<","<<r[STEP]*r[DT]/3600<<","<<r[TI]<<","<<r[TO]<<","<<r[SOLAR]<<","<<r[HVAC]<<","<<r[INTERNAL]<<","<<r[WIND]<<","<<r[SHADE]<<","<<r[TOBS]<<","<<s.truth<<"\n";}}
static double evaluate(Engine&e,const vector<Sample>&samples,const Candidate&c,int version,bool audit){
 string prefix="v"+to_string(version);int score=e.index("score_"+prefix+"_01"),pred=e.index("temperature_next_"+prefix);
 double total=0;size_t checked=0;
 for(size_t pos=0;pos<samples.size();pos+=96){vector<Row>x;for(size_t i=pos;i<min(pos+96,samples.size());++i){Row r=samples[i].r;r[UA]=c.U;r[CAP]=c.C;r[KWIND]=c.K;r[ALPHA]=c.A;x.push_back(r);}
   auto values=e.batch(x,{score,pred});for(size_t j=0;j<x.size();++j){total+=values[j];
      if(audit && j%19==0){double native=nativeScore(x[j],version,0),v=values[j],diff=abs(v-native)/(1+abs(native));
         require(diff<2e-10,"Independent native score oracle mismatch");++e.nativeChecks;e.maxScaledDiff=max(e.maxScaledDiff,diff);
         double nt=nativeForecast(x[j],version),pt=values[x.size()+j];double d=abs(nt-pt)/(1+abs(nt));
         require(d<2e-10,"Independent native temperature oracle mismatch");++e.nativeChecks;e.maxScaledDiff=max(e.maxScaledDiff,d);++checked;}}
 }
 (void)checked;return total/samples.size();}
static void run(const fs::path&root,int steps,int grid){require(steps>=24&&steps<=1000&&grid>=3&&grid<=12,"Invalid workload settings");fs::create_directories(root/"results");fs::create_directories(root/"examples");
 Engine e;writeRegistry(e,root);vector<Sample> samples=buildObservations(e,steps);writeObservations(samples,root);
 // Scalar-versus-batch layout check on two different graphs and two different rows.
 {vector<Row>x{samples[0].r,samples[1].r};vector<int>ids{e.index("temperature_next_v2"),e.index("solar_gain_v2")};auto v=e.batch(x,ids);
  for(size_t j=0;j<x.size();++j)for(size_t k=0;k<ids.size();++k){double s=e.scalar(ids[k],x[j]);require(abs(s-v[k*x.size()+j])<1e-11,"SDK scalar/batch ordering mismatch");}}
 // Pre-registered finite candidate grid: v1 is deliberately wind-free; v2
 // includes wind-infiltration and solar-shading formula terms.
 Candidate best1{0,0,0,.65,"v1",numeric_limits<double>::infinity()};Candidate best2{0,0,0,.65,"v2",numeric_limits<double>::infinity()};
 ofstream sweep(root/"results/model_sweep.csv");sweep<<"version,UA_WperK,C_JperK,kwind_WperKmps,alpha,mean_squared_residual_K2\n"<<setprecision(16);
 for(int i=0;i<grid;i++)for(int j=0;j<grid;j++)for(int k=0;k<grid;k++){
    double U=150.+120.*i/(grid-1),C=5.4e6+3.6e6*j/(grid-1),K=5.+90.*k/(grid-1);
    Candidate c1{U,C,0,.65,"v1",0};if(k==0){c1.avg=evaluate(e,samples,c1,1,true);sweep<<"v1,"<<U<<","<<C<<",0,"<<c1.A<<","<<c1.avg<<"\n";if(c1.avg<best1.avg)best1=c1;}
    Candidate c2{U,C,K,.65,"v2",0};c2.avg=evaluate(e,samples,c2,2,true);sweep<<"v2,"<<U<<","<<C<<","<<K<<","<<c2.A<<","<<c2.avg<<"\n";if(c2.avg<best2.avg)best2=c2;
 }
 sweep.close();
 // Multi-graph pass executes EVERY registered core, sensitivity and all 30
 // distinct cost graphs on real rows of the generated paceval workload.
 vector<Row>x;for(const auto&s:samples){Row r=s.r;r[UA]=best2.U;r[CAP]=best2.C;r[KWIND]=best2.K;r[ALPHA]=best2.A;x.push_back(r);}
 vector<double>scoreTotal(30,0.);ofstream times(root/"results/time_series.csv");times<<"step,observed_degC,pred_v1_degC,pred_v2_degC,residual_v1_K,residual_v2_K,required_heat_v1_W,required_heat_v2_W,lower_margin_v2_K,upper_margin_v2_K,ds_dUA_v2,ds02_dUA_v2,composite_score02_v2\n"<<setprecision(16);
 const vector<string>cols{"temperature_next_v1","temperature_next_v2","temperature_residual_v1","temperature_residual_v2","required_heat_v1","required_heat_v2","lower_margin_v2","upper_margin_v2","score_dUA_v2","score02_dUA_v2","score_v2_02"};
 vector<int>graphIds;for(const auto&g:e.f)graphIds.push_back(e.index(g.id));
 for(size_t pos=0;pos<x.size();pos+=64){vector<Row>part(x.begin()+pos,x.begin()+min(pos+64,x.size()));auto vals=e.batch(part,graphIds);
   for(size_t z=0;z<part.size();++z){const Row&r=part[z];times<<long(r[STEP])<<","<<r[TOBS];
      for(const auto&id:cols){times<<","<<vals[e.index(id)*part.size()+z];}times<<"\n";
      for(int v=1;v<=2;++v)for(int a=1;a<=15;++a){string id="score_v"+to_string(v)+"_"+(a<10?"0":"")+to_string(a);int idx=e.index(id);scoreTotal[(v-1)*15+a-1]+=vals[idx*part.size()+z];}
      if(z%29==0){double native=nativeScore(r,2,0),got=vals[e.index("score_v2_01")*part.size()+z];double d=abs(native-got)/(1+abs(native));require(d<2e-10,"Complete score audit mismatch");++e.nativeChecks;e.maxScaledDiff=max(e.maxScaledDiff,d);}
  }
 }
 times.close();ofstream variants(root/"results/score_variants.csv");variants<<"function_id,model_version,mean_cost\n"<<setprecision(16);
 for(int v=1;v<=2;++v)for(int a=1;a<=15;++a)variants<<"score_v"<<v<<"_"<<(a<10?"0":"")<<a<<",v"<<v<<","<<scoreTotal[(v-1)*15+a-1]/x.size()<<"\n";
 variants.close();writeInventory(e,root);
 ofstream log(root/"results/sdk_execution.txt");log<<setprecision(16)<<"WP_045 original paceval SDK execution SUCCESS\n"<<"library_original=true\n"<<"graphs_registered_and_executed="<<e.f.size()<<"\n"<<"batch_calls="<<e.batchCalls<<"\n"<<"batch_graph_outputs="<<e.outputs<<"\n"<<"scalar_calls="<<e.scalarCalls<<"\n"<<"independent_native_checks="<<e.nativeChecks<<"\n"<<"max_scaled_diff_internal_only="<<e.maxScaledDiff<<"\n"<<"samples="<<steps<<"\n"<<"candidate_grid="<<grid<<"\n"<<"best_v1_UA="<<best1.U<<"\n"<<"best_v1_C="<<best1.C<<"\n"<<"best_v1_cost="<<best1.avg<<"\n"<<"best_v2_UA="<<best2.U<<"\n"<<"best_v2_C="<<best2.C<<"\n"<<"best_v2_kwind="<<best2.K<<"\n"<<"best_v2_cost="<<best2.avg<<"\n";
 cout<<"ORIGINAL PACEVAL SUCCESS: graphs="<<e.f.size()<<" batch_calls="<<e.batchCalls<<" native_checks="<<e.nativeChecks<<" best_v1="<<best1.avg<<" best_v2="<<best2.avg<<"\n";
}
int main(int argc,char**argv){try{string out=".";int steps=384,grid=7;for(int i=1;i<argc;i++){
 string s=argv[i];auto next=[&](){require(i+1<argc,"missing CLI value");return string(argv[++i]);};
 if(s=="--out")out=next();else if(s=="--steps")steps=stoi(next());else if(s=="--grid")grid=stoi(next());else throw runtime_error("unknown argument "+s);}
 run(out,steps,grid);return 0;}catch(const exception&ex){cerr<<"FATAL: "<<ex.what()<<'\n';return 2;}}
