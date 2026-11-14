// WP Weather: synthetic meteorological ensemble postprocessing and site-level decision functions.
// Reproducible functionality demonstration, NOT an operational weather forecast or warning service.
// Every published domain kernel below is evaluated by the original paceval SDK, not by the reference.
#include "paceval_main.h"
#include <algorithm>
#include <array>
#include <cmath>
#include <cstdint>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <limits>
#include <map>
#include <regex>
#include <set>
#include <sstream>
#include <stdexcept>
#include <string>
#include <vector>
namespace fs=std::filesystem;
static void demand(bool b,const std::string& why){if(!b)throw std::runtime_error(why);}
static constexpr int NV=26;
static constexpr int K=0,N=1,MEAN=2,SPREAD=3,THR=4,SCALE=5,ELEV=6,DOY=7,LEAD=8,LOSS=9,COST=10,EFF=11,EVENT=12,
  B0=13,B1=14,B2=15,B3=16,B4=17,B5=18,B6=19,B7=20,B8=21,PROB=22,LOGIT=23,QSM=24,RAW=25;
static constexpr char VARS[]="k n mean spread thr scale elev doy lead loss cost eff event b0 b1 b2 b3 b4 b5 b6 b7 b8 prob logit qsm raw";
using Row=std::array<double,NV>;
static std::vector<std::string> split(const std::string& line){std::stringstream s(line);std::vector<std::string> out;std::string v;while(std::getline(s,v,','))out.push_back(v);if(!line.empty()&&line.back()==',')out.emplace_back();return out;}
struct Engine{
 std::vector<PACEVAL_HANDLE> owned;std::set<PACEVAL_HANDLE> used;
 uint64_t scalar_calls=0,batch_calls=0,graph_outputs=0;
 Engine(){demand(paceval_InitializeLibrary(nullptr),"Original paceval SDK failed to initialize");}
 ~Engine(){for(auto h:owned)paceval_DeleteComputation(h);paceval_FreeLibrary();}
 double parse(const std::string& s)const{
  static const std::regex literal(R"(^[+-]?(?:[0-9]+(?:\.[0-9]*)?|\.[0-9]+)(?:[eE][+-]?[0-9]+)?$)");
  demand(std::regex_match(s,literal),"CSV numeric field is not a literal: "+s);
  int err=-1;long pos=-1;double v=paceval_dConvertStringToFloat(s.c_str(),&err,&pos,false,nullptr,nullptr);
  demand(err==PACEVAL_ERR_NO_ERROR&&std::isfinite(v),"paceval numerical CSV conversion error at "+std::to_string(pos));return v;
 }
 std::string fmt(double v)const{
  demand(std::isfinite(v),"Refused non-finite numerical output");char buf[512]={};
  int r=paceval_dConvertFloatToString(buf,v);demand(r>0&&buf[0],"paceval numerical CSV formatting failed");return std::string(buf);
 }
 PACEVAL_HANDLE create(const std::string& expr){
  PACEVAL_HANDLE h=paceval_CreateComputation(expr.c_str(),NV,VARS,false,nullptr);demand(h!=nullptr,"Null paceval graph handle");
  if(paceval_GetIsError(h)){char a[1024]={},b[1024]={};paceval_CreateErrorInformationText(h,a,b);paceval_DeleteComputation(h);throw std::runtime_error("Invalid paceval graph "+expr.substr(0,120)+" : "+a+" "+b);}
  owned.push_back(h);return h;
 }
 double scalar(PACEVAL_HANDLE h,const Row& row){double r=paceval_dGetComputationResult(h,const_cast<double*>(row.data()),nullptr,nullptr);demand(!paceval_GetIsError(h)&&std::isfinite(r),"Scalar graph evaluation failed");used.insert(h);scalar_calls++;graph_outputs++;return r;}
 // The official SDK returns graph-major ordering: output[graph * rows + row].
 std::vector<double> batch(const std::vector<PACEVAL_HANDLE>& graphs,const std::vector<Row>& rows){
  demand(!graphs.empty()&&!rows.empty(),"Empty graph or row batch");std::vector<double> in;in.reserve(rows.size()*NV);
  for(auto const& r:rows)for(double x:r){demand(std::isfinite(x),"Nonfinite graph input");in.push_back(x);}
  auto handles=graphs;std::vector<double> out(graphs.size()*rows.size());std::vector<int> errors(out.size(),-1);
  bool fail=paceval_dGetMultipleComputationsResultsExt(handles.data(),static_cast<unsigned long>(handles.size()),in.data(),static_cast<unsigned long>(rows.size()),out.data(),nullptr,nullptr,errors.data());
  demand(!fail,"paceval multi-graph call failed");
  for(size_t i=0;i<out.size();i++)demand(errors[i]==PACEVAL_ERR_NO_ERROR&&std::isfinite(out[i]),"paceval graph error index "+std::to_string(i)+" code "+std::to_string(errors[i]));
  for(auto h:graphs){used.insert(h);}
  batch_calls++;graph_outputs+=out.size();return out;
 }
 size_t created()const{return owned.size();}size_t executed()const{return used.size();}
};
using Definitions=std::map<std::string,std::string>;
struct Graph{std::string name,formula,version;PACEVAL_HANDLE handle;};
using GraphMap=std::map<std::string,Graph>;
static const std::string RAW_FORM="(k/n)";
static const std::string Q_FORM="((k+0.5)/(n+1))";
static const std::string U_FORM="ln((k+0.5)/(n-k+0.5))";
static const std::string ANOM="((mean-thr)/scale)";
static const std::string DISP="(spread/scale)";
static const std::string SIN="sin(2*pi*doy/365.25)";
static const std::string COS="cos(2*pi*doy/365.25)";
static std::string z_formula(int version){
 std::string z="(b0+b1*"+U_FORM+"+b2*"+ANOM+"+b3*"+DISP+"+b4*(elev/1000)+b5*"+SIN+"+b6*"+COS+"+b7*(lead/72)";
 if(version==2)z+="+b8*(sqr("+ANOM+")/(1+sqr("+ANOM+")))";
 return z+")";
}
static Definitions primary(int version){auto z=z_formula(version),p="sig("+z+")";
 std::string dz="(b2/scale)";
 if(version==2)dz="((b2/scale)+b8*(2*"+ANOM+")/(scale*sqr(1+sqr("+ANOM+"))))";
 return {{"raw_exceedance",RAW_FORM},{"smoothed_exceedance",Q_FORM},{"smoothed_logit",U_FORM},
 {"standardized_anomaly",ANOM},{"normalized_spread",DISP},{"seasonal_sine",SIN},{"seasonal_cosine",COS},
 {"calibration_logit",z},{"calibrated_probability",p},
 {"sensitivity_logit","(b1*"+p+"*(1-"+p+"))"},{"sensitivity_mean","("+dz+"*"+p+"*(1-"+p+"))"},
 {"ensemble_entropy","(-"+Q_FORM+"*ln("+Q_FORM+")-(1-"+Q_FORM+")*ln(1-"+Q_FORM+"))"}};
}
static Definitions secondary(){
 const std::string M="(prob*eff*loss-cost)";
 const std::string A="(("+M+">0) AND (prob>=0) AND (prob<=1))";
 return {{"brier_loss","sqr(prob-event)"},{"raw_brier_loss","sqr(raw-event)"},{"probability_adjustment","(prob-raw)"},
  {"expected_loss_no_action","(prob*loss)"},{"expected_loss_with_action","(prob*(1-eff)*loss+cost)"},
  {"avoided_expected_loss","(prob*eff*loss)"},{"action_margin",M},{"break_even_probability","(cost/(eff*loss))"},
  {"beneficial_action_indicator",A},{"probability_validity_indicator","((prob>=0) AND (prob<=1))"},
  {"risk_probability_over_20","(prob>=0.20)"},{"risk_probability_over_50","(prob>=0.50)"},
  {"normalized_action_margin","("+M+"/(loss+cost))"},{"sensitivity_action_to_probability","(eff*loss)"},
  {"sensitivity_action_to_efficacy","(prob*loss)"},{"sensitivity_action_to_loss","(prob*eff)"},
  {"combined_priority_score","(0.60*(prob*loss)/(loss+cost)+0.40*sig(5*"+M+"/(loss+cost)))"}};
}
static Definitions compound(){return {{"frechet_joint_lower","(0 max (prob+raw-1))"},{"frechet_joint_upper","(prob min raw)"}};}
static GraphMap register_graphs(Engine& e,const Definitions& defs,int version){GraphMap out;for(auto const& [name,formula]:defs)out.emplace(name,Graph{name,formula,"v"+std::to_string(version),e.create(formula)});return out;}
static std::vector<PACEVAL_HANDLE> handles(const GraphMap& g){std::vector<PACEVAL_HANDLE> x;for(auto const& p:g)x.push_back(p.second.handle);return x;}
static std::map<std::string,size_t> indexes(const GraphMap& g){std::map<std::string,size_t> m;size_t i=0;for(auto const& p:g)m[p.first]=i++;return m;}
static uint64_t mix(uint64_t x){x^=x>>30;x*=UINT64_C(0xbf58476d1ce4e5b9);x^=x>>27;x*=UINT64_C(0x94d049bb133111eb);return x^(x>>31);}
static double uni(uint64_t key){return double(mix(key)>>11)*(1.0/9007199254740992.0);}
struct Record {int site=0,window=0,hazard=0;Row r{};};
static constexpr const char* HAZARDS[]={"HEAVY_RAIN_P24","EXTREME_GUST_G06","AIR_FROST_F12"};
static constexpr int WINDOW_HOURS[]={24,6,12};
static constexpr int LEADS[]={24,48,72,96};
static void validate(const Record& rec){auto const& a=rec.r;
 demand(rec.site>=0&&rec.window>=0&&rec.window<4&&rec.hazard>=0&&rec.hazard<3,"Categorical metadata invalid");
 for(double v:a)demand(std::isfinite(v),"Nonfinite input field");
 demand(a[N]==51&&a[K]>=0&&a[K]<=a[N]&&std::floor(a[K])==a[K]&&a[SPREAD]>=0&&a[SCALE]>0,"Ensemble member contract invalid");
 demand(a[DOY]>=1&&a[DOY]<=366&&a[LEAD]>0&&a[LOSS]>0&&a[COST]>=0&&a[EFF]>0&&a[EFF]<=1,"Policy or temporal domain invalid");
 demand(a[EVENT]==0||a[EVENT]==1,"Invalid synthetic event label");
}
static std::array<double,9> coefficients(int h,int version){
 const double offsets[]={-.35,-.60,-.20};
 return {{offsets[h]+(version==2?.08:0),version==1?.83:.91,version==1?.34:.28,
 version==1?-.13:-.11,-.045,.12,-.07,-.09,version==1?0:.11}};
}
static Record generate(int site,int win,int hazard){Record rec;rec.site=site;rec.window=win;rec.hazard=hazard;auto& a=rec.r;a.fill(0.0);
 const int day=1+(site*17+win*47)%365;const double phase=6.283185307179586*day/365.25;
 double base=(hazard==0?16.0+6.0*std::sin(phase+.5):hazard==1?21.0+3.5*std::cos(phase):1.3-5.0*std::cos(phase));
 // For frost a positive hazard-oriented variable means colder: feature = -air_temperature_C.
 double spread=(hazard==0?6.5:hazard==1?4.0:3.8),sum=0,sumsq=0;int exceed=0;double threshold=(hazard==0?20.0:hazard==1?25.0:0.0);
 for(int m=0;m<51;m++){
  double noise=1.85*(uni(UINT64_C(0x345aca115)+uint64_t(site)*35993+uint64_t(win)*3007+uint64_t(hazard)*601+uint64_t(m)*571)-.5);
  double value=base+spread*noise+(uni(UINT64_C(0x9023083)+uint64_t(site)*7789+uint64_t(win)*53+uint64_t(m)*509)-.5)*1.5;
  if(hazard==2)value=-value;
  sum+=value;sumsq+=value*value;exceed+=(value>=threshold);
 }
 double mean=sum/51,sd=std::sqrt(std::max(0.0,sumsq/51-mean*mean));
 double scaling=(hazard==0?12.0:hazard==1?8.0:6.0);
 a[K]=exceed;a[N]=51;a[MEAN]=mean;a[SPREAD]=sd;a[THR]=threshold;a[SCALE]=scaling;
 a[ELEV]=double((site*37)%900)-350.0;a[DOY]=day;a[LEAD]=LEADS[win];
 a[LOSS]=(hazard==0?18000.0:hazard==1?28000.0:13000.0)*(0.7+0.6*uni(site*1447u+hazard*551u+17));
 a[EFF]=0.35+0.45*uni(site*334u+win*31u+hazard*71u+8);
 a[COST]=(hazard==0?1400.0:hazard==1?2500.0:900.0)*(0.60+.85*uni(site*883u+win*107u+hazard*31u+42));
 // Synthetic observations are not a station measurement. Their latent probability uses a known data-generating process.
 const double rawsm=(exceed+0.5)/52.0,logit=std::log(rawsm/(1-rawsm));
 const double truth=-.32+.94*logit+.19*((mean-threshold)/scaling)-.08*(sd/scaling)+.12*std::sin(phase+.5);
 const double p=1.0/(1.0+std::exp(-truth));
 a[EVENT]=(uni(UINT64_C(0x917c119)+uint64_t(site)*98731+uint64_t(win)*8011+uint64_t(hazard)*1709)<p)?1:0;
 return rec;
}
static int strict_integer(const std::string& value){
 static const std::regex digits(R"(^[0-9]+$)");
 demand(std::regex_match(value,digits),"Invalid categorical integer metadata: "+value);
 return std::stoi(value);
}
static void write_inputs(Engine& e,const fs::path& path,int sites){
 std::ofstream f(path);demand(bool(f),"Cannot write input CSV");f<<"site_id,window_id,hazard_id,event_window_hours,k,n,mean_oriented,spread,threshold,scale,elevation_diff_m,day_of_year,lead_hours,asset_loss_units,action_cost_units,mitigation_fraction,synthetic_event\n";
 for(int site=0;site<sites;site++)for(int w=0;w<4;w++)for(int h=0;h<3;h++){
  Record t=generate(site,w,h);f<<site<<','<<w<<','<<h<<','<<WINDOW_HOURS[h];
  for(int j=0;j<=EVENT;j++){f<<','<<e.fmt(t.r[j]);}f<<'\n';
 }
}
static std::vector<Record> load_inputs(Engine& e,const fs::path& path){
 std::ifstream f(path);demand(bool(f),"Cannot read input CSV");std::string header,line;
 demand(bool(std::getline(f,header))&&split(header).size()==17,"Incorrect input CSV header");
 std::vector<Record> v;while(std::getline(f,line)){if(line.empty())continue;auto parts=split(line);demand(parts.size()==17,"Incorrect number of CSV fields");
 Record t;t.site=strict_integer(parts[0]);t.window=strict_integer(parts[1]);t.hazard=strict_integer(parts[2]);int hrs=strict_integer(parts[3]);
 demand(t.hazard>=0&&t.hazard<3&&hrs==WINDOW_HOURS[t.hazard],"Hazard window metadata mismatch");
 for(int j=0;j<=EVENT;j++){t.r[j]=e.parse(parts[j+4]);}validate(t);v.push_back(t);
 }return v;
}
static void set_coefficients(Row& row,int h,int version){auto c=coefficients(h,version);for(int j=0;j<9;j++)row[B0+j]=c[j];}
struct Ref{double raw,q,u,anom,spread,ss,cc,z,p,du,dmean,entropy,brier,raw_brier,adjust,noloss,with_action,avoided,margin,break_even,benefit,valid,risk20,risk50,norm_margin,dp,eff_sens,loss_sens,priority;};
static Ref native(const Row& a,int version){
 Ref t{};t.raw=a[K]/a[N];t.q=(a[K]+.5)/(a[N]+1);t.u=std::log((a[K]+.5)/(a[N]-a[K]+.5));
 t.anom=(a[MEAN]-a[THR])/a[SCALE];t.spread=a[SPREAD]/a[SCALE];t.ss=std::sin(2*std::acos(-1.0)*a[DOY]/365.25);t.cc=std::cos(2*std::acos(-1.0)*a[DOY]/365.25);
 t.z=a[B0]+a[B1]*t.u+a[B2]*t.anom+a[B3]*t.spread+a[B4]*a[ELEV]/1000+a[B5]*t.ss+a[B6]*t.cc+a[B7]*a[LEAD]/72;
 if(version==2)t.z+=a[B8]*t.anom*t.anom/(1+t.anom*t.anom);
 t.p=1/(1+std::exp(-t.z));t.du=a[B1]*t.p*(1-t.p);
 double dz=a[B2]/a[SCALE];if(version==2)dz+=a[B8]*2*t.anom/(a[SCALE]*std::pow(1+t.anom*t.anom,2));
 t.dmean=dz*t.p*(1-t.p);t.entropy=-t.q*std::log(t.q)-(1-t.q)*std::log(1-t.q);
 t.brier=(t.p-a[EVENT])*(t.p-a[EVENT]);t.raw_brier=(t.raw-a[EVENT])*(t.raw-a[EVENT]);t.adjust=t.p-t.raw;
 t.noloss=t.p*a[LOSS];t.with_action=t.p*(1-a[EFF])*a[LOSS]+a[COST];t.avoided=t.p*a[EFF]*a[LOSS];t.margin=t.avoided-a[COST];
 t.break_even=a[COST]/(a[EFF]*a[LOSS]);t.benefit=(t.margin>0)?1:0;t.valid=1;t.risk20=(t.p>=.2);t.risk50=(t.p>=.5);
 t.norm_margin=t.margin/(a[LOSS]+a[COST]);t.dp=a[EFF]*a[LOSS];t.eff_sens=t.p*a[LOSS];t.loss_sens=t.p*a[EFF];
 t.priority=.60*(t.p*a[LOSS])/(a[LOSS]+a[COST])+.40/(1+std::exp(-5*t.margin/(a[LOSS]+a[COST])));
 return t;
}
static void assert_close(double x,double y,const std::string& where){
 demand(std::isfinite(x)&&std::isfinite(y)&&std::abs(x-y)<=2e-10*std::max(1.0,std::abs(y)),"Independent C++ reference mismatch: "+where);
}
struct Acc {uint64_t n=0,event=0,action=0,review=0,none=0;double sum_p=0,sum_raw=0,sum_brier=0,sum_raw_brier=0,sum_margin=0,sum_loss=0;};
struct ReliabilityBin {uint64_t n=0,events=0;double p_sum=0;};
static std::string outcome(double margin,double p){return (margin>0&&p>=.25)?"ACTION_CANDIDATE":(margin>0?"REVIEW":"NO_ACTION");}
static void write_graph_inventory(const fs::path& path,const std::array<GraphMap,2>& p,const std::array<GraphMap,2>& s,const GraphMap& compound){
 std::ofstream f(path);demand(bool(f),"Cannot write graph inventory");
 f<<"function_id,domain_quantity,mathematical_definition,units,execution_owner,paceval_graph_id,formula_version,api_path,reference_test,status,host_reason\n";
 for(int v=0;v<2;v++)for(auto [g,stage]:{std::pair<const GraphMap*,std::string>{&p[v],"first_stage"},{&s[v],"second_stage"}})
  for(auto const& [name,x]:*g){f<<"v"<<v+1<<'_'<<name<<','<<stage<<"_"<<name<<",\""<<x.formula<<"\",defined_per_quantity,paceval,v"<<v+1<<'_'<<name<<",v"<<v+1<<",dGetMultipleComputationsResultsExt,independent_native_cpp_and_python,executed,\n";}
 for(auto const& [name,x]:compound)f<<"shared_"<<name<<",compound_event_bounds,\""<<x.formula<<"\",probability,paceval,shared_"<<name<<",shared,dGetMultipleComputationsResultsExt,independent_native_cpp,executed,\n";
 f<<"host_ensemble_count,ensemble_member_thresholds,validated_51_member_loop,events,host,,all,member_preprocessing,binary_count_checks,executed,stateful_member_loop\n";
 f<<"host_decision,policy_status,interpret_paceval_margin_and_probability,category,host,,all,postprocessing,independent_native_cpp,executed,policy_governance\n";
}
static void conversion_test(Engine& e){for(auto s:{"0","-12.5","1e-7","22.2","4.50000","6.02E+8"}){
  double x=e.parse(s);demand(std::isfinite(e.parse(e.fmt(x))),"Roundtrip conversion not finite");}
 for(auto s:{"","1+2","bad","NaN","Inf","1,5","1e9999","3/2"}){bool denied=false;try{(void)e.parse(s);}catch(...){denied=true;}demand(denied,"Invalid CSV numeric input accepted");}
}
static void operator_test(Engine& e){Row row{};row.fill(1);row[MEAN]=2;row[SPREAD]=3;
 const std::vector<std::pair<std::string,double>> cases={{"(-1) % 10",-1},{"(-1) mod 10",9},{"(4 min 5)",4},{"(4 max 5)",5},
 {"((mean<spread) AND (spread>=3))",1},{"((mean>spread) OR (spread=3))",1},{"NOT(mean=spread)",1},
 {"((mean<=2) AND (spread<>2))",1}};
 for(auto const& x:cases){auto h=e.create(x.first);assert_close(e.scalar(h,row),x.second,x.first);}
}
static void layout_test(Engine& e){Row a{};a.fill(1);Row b=a;a[MEAN]=3;a[SPREAD]=1;b[MEAN]=7;b[SPREAD]=2;
 auto h=e.create("(mean+spread)"),j=e.create("(mean-spread)");auto x=e.batch({h,j},{a,b});
 demand(x.size()==4&&x[0]==4&&x[1]==9&&x[2]==2&&x[3]==5,"Multi-graph output ordering invalid");
 assert_close(e.scalar(h,a),4,"Scalar versus batch");
}
static void invalid_test(Engine& e){(void)e;auto a=generate(1,0,0);a.r[N]=0;bool denied=false;try{validate(a);}catch(...){denied=true;}demand(denied,"Zero ensemble member count accepted");
 a=generate(1,0,2);a.r[EFF]=1.2;denied=false;try{validate(a);}catch(...){denied=true;}demand(denied,"Invalid mitigation efficacy accepted");
}
static void run(Engine& e,int sites,const fs::path& out){
 demand(sites>=12&&sites<=15000,"Synthetic site count out of range");fs::create_directories(out);
 write_inputs(e,out/"synthetic_ensemble_features.csv",sites);auto records=load_inputs(e,out/"synthetic_ensemble_features.csv");
 demand(records.size()==size_t(sites)*12,"Synthetic site-window-hazard input count mismatch");
 std::array<GraphMap,2> pg={register_graphs(e,primary(1),1),register_graphs(e,primary(2),2)};
 std::array<GraphMap,2> sg={register_graphs(e,secondary(),1),register_graphs(e,secondary(),2)};
 GraphMap cg=register_graphs(e,compound(),0);
 write_graph_inventory(out/"math_execution_inventory.csv",pg,sg,cg);
 std::ofstream formula(out/"formula_registry.csv"),audit(out/"audit_samples.csv"),trace(out/"end_to_end_trace.csv"),summary(out/"hazard_window_summary.csv"),joint(out/"compound_bounds_samples.csv");
 demand(bool(formula)&&bool(audit)&&bool(trace)&&bool(summary)&&bool(joint),"Cannot open result files");
 formula<<"graph_id,version,stage,formula\n";for(int v=0;v<2;v++)for(auto [g,stage]:{std::pair<const GraphMap*,std::string>{&pg[v],"primary"},{&sg[v],"secondary"}})
  for(auto const& [name,x]:*g)formula<<"v"<<v+1<<'_'<<name<<",v"<<v+1<<','<<stage<<",\""<<x.formula<<"\"\n";
 for(auto const& [name,x]:cg)formula<<"shared_"<<name<<",shared,compound,\""<<x.formula<<"\"\n";
 audit<<"site,window,hazard,version,k,n,mean,spread,thr,scale,elev,doy,lead,loss,cost,eff,event,b0,b1,b2,b3,b4,b5,b6,b7,b8,raw,q,logit,z,prob,brier,raw_brier,action_margin,break_even,priority,sensitivity_mean,status\n";
 trace<<"site,window,hazard,version,k,n,mean,spread,logit,p,probability_adjustment,brier_loss,margin,break_even,sensitivity_probability,status\n";
 summary<<"hazard,window,version,cases,synthetic_event_frequency,raw_probability_mean,model_probability_mean,brier_score,raw_brier_score,mean_action_margin,mean_expected_loss,action_candidate,review,no_action\n";
 joint<<"site,window,version,hazard_a,hazard_b,p_a,p_b,frechet_lower,frechet_upper\n";
 std::array<std::array<std::array<Acc,2>,4>,3> sums{};
 std::array<std::array<std::array<ReliabilityBin,10>,2>,3> reliability{};
 std::array<std::vector<double>,2> probabilities;for(auto& p:probabilities)p.resize(records.size());
 uint64_t independent_checks=0,model_cases=0,audit_rows=0,trace_rows=0;
 constexpr size_t BATCH=512;
 for(int version=1;version<=2;version++){
  const auto& p=pg[version-1],s=sg[version-1];auto pind=indexes(p),sind=indexes(s);auto ph=handles(p),sh=handles(s);
  for(size_t at=0;at<records.size();at+=BATCH){size_t n=std::min(BATCH,records.size()-at);std::vector<Row> rows;rows.reserve(n);
   for(size_t j=0;j<n;j++){auto r=records[at+j].r;set_coefficients(r,records[at+j].hazard,version);rows.push_back(r);}
   auto pre=e.batch(ph,rows);
   for(size_t j=0;j<n;j++){rows[j][PROB]=pre[pind.at("calibrated_probability")*n+j];rows[j][LOGIT]=pre[pind.at("smoothed_logit")*n+j];rows[j][QSM]=pre[pind.at("smoothed_exceedance")*n+j];rows[j][RAW]=pre[pind.at("raw_exceedance")*n+j];demand(rows[j][PROB]>=0&&rows[j][PROB]<=1,"Probability outside [0,1]");}
   auto post=e.batch(sh,rows);
   for(size_t j=0;j<n;j++){
    auto const& rec=records[at+j];auto const& r=rows[j];auto ref=native(r,version);
    auto P=[&](const char* name){return pre[pind.at(name)*n+j];};auto Q=[&](const char* name){return post[sind.at(name)*n+j];};
    for(auto [name,val]:std::vector<std::pair<const char*,double>>{{"raw_exceedance",ref.raw},{"smoothed_exceedance",ref.q},{"smoothed_logit",ref.u},{"standardized_anomaly",ref.anom},{"normalized_spread",ref.spread},{"seasonal_sine",ref.ss},{"seasonal_cosine",ref.cc},{"calibration_logit",ref.z},{"calibrated_probability",ref.p},{"sensitivity_logit",ref.du},{"sensitivity_mean",ref.dmean},{"ensemble_entropy",ref.entropy}}){assert_close(P(name),val,name);independent_checks++;}
    for(auto [name,val]:std::vector<std::pair<const char*,double>>{{"brier_loss",ref.brier},{"raw_brier_loss",ref.raw_brier},{"probability_adjustment",ref.adjust},{"expected_loss_no_action",ref.noloss},{"expected_loss_with_action",ref.with_action},{"avoided_expected_loss",ref.avoided},{"action_margin",ref.margin},{"break_even_probability",ref.break_even},{"beneficial_action_indicator",ref.benefit},{"probability_validity_indicator",ref.valid},{"risk_probability_over_20",ref.risk20},{"risk_probability_over_50",ref.risk50},{"normalized_action_margin",ref.norm_margin},{"sensitivity_action_to_probability",ref.dp},{"sensitivity_action_to_efficacy",ref.eff_sens},{"sensitivity_action_to_loss",ref.loss_sens},{"combined_priority_score",ref.priority}}){assert_close(Q(name),val,name);independent_checks++;}
    auto& a=sums[rec.hazard][rec.window][version-1];a.n++;a.event+=r[EVENT]>0.5;
    a.sum_p+=P("calibrated_probability");a.sum_raw+=P("raw_exceedance");
    auto& rb=reliability[rec.hazard][version-1][std::min(9,int(P("calibrated_probability")*10))];rb.n++;rb.p_sum+=P("calibrated_probability");rb.events+=r[EVENT]>0.5;a.sum_brier+=Q("brier_loss");a.sum_raw_brier+=Q("raw_brier_loss");a.sum_margin+=Q("action_margin");a.sum_loss+=Q("expected_loss_no_action");
    auto status=outcome(Q("action_margin"),P("calibrated_probability"));a.action+=(status=="ACTION_CANDIDATE");a.review+=(status=="REVIEW");a.none+=(status=="NO_ACTION");
    probabilities[version-1][at+j]=P("calibrated_probability");model_cases++;
    if((at+j)%127==0){audit<<rec.site<<','<<rec.window<<','<<rec.hazard<<','<<version;
     for(int id=0;id<=B8;id++)audit<<','<<e.fmt(r[id]);
     for(double t:{P("raw_exceedance"),P("smoothed_exceedance"),P("smoothed_logit"),P("calibration_logit"),P("calibrated_probability"),Q("brier_loss"),Q("raw_brier_loss"),Q("action_margin"),Q("break_even_probability"),Q("combined_priority_score"),P("sensitivity_mean")})audit<<','<<e.fmt(t);
     audit<<','<<status<<'\n';audit_rows++;
    }
    if(rec.site==0&&rec.window==0){trace<<rec.site<<','<<rec.window<<','<<rec.hazard<<','<<version;
     for(double t:{r[K],r[N],r[MEAN],r[SPREAD],P("smoothed_logit"),P("calibrated_probability"),Q("probability_adjustment"),Q("brier_loss"),Q("action_margin"),Q("break_even_probability"),Q("sensitivity_action_to_probability")})trace<<','<<e.fmt(t);
     trace<<','<<status<<'\n';trace_rows++;
    }
   }
  }
 }
 for(int h=0;h<3;h++)for(int w=0;w<4;w++)for(int v=0;v<2;v++){auto const& a=sums[h][w][v];
  summary<<HAZARDS[h]<<','<<w<<",v"<<v+1<<','<<a.n;
  for(double t:{double(a.event)/a.n,a.sum_raw/a.n,a.sum_p/a.n,a.sum_brier/a.n,a.sum_raw_brier/a.n,a.sum_margin/a.n,a.sum_loss/a.n})summary<<','<<e.fmt(t);
  summary<<','<<a.action<<','<<a.review<<','<<a.none<<'\n';
 }
 // Reliability bins aggregate actual paceval-calculated probabilities and the synthetic labels.
 {std::ofstream rel(out/"reliability_bins.csv");demand(bool(rel),"Cannot write reliability data");
  rel<<"hazard,version,bin_index,cases,mean_probability,synthetic_event_frequency\n";
  for(int h=0;h<3;h++)for(int v=0;v<2;v++)for(int b=0;b<10;b++){
   auto const& r=reliability[h][v][b];if(r.n==0)continue;
   rel<<HAZARDS[h]<<",v"<<v+1<<','<<b<<','<<r.n<<','<<e.fmt(r.p_sum/r.n)<<','<<e.fmt(double(r.events)/r.n)<<'\n';
  }
 }
 // Additional surface data are computed by genuine paceval probability and sensitivity graphs.
 uint64_t surface_rows=0,surface_native_checks=0;
 {std::ofstream f(out/"paceval_probability_surfaces.csv");demand(bool(f),"Cannot write surface data");
  f<<"hazard,version,ensemble_exceedance_fraction,standardized_mean_anomaly,probability,probability_sensitivity_mean\n";
  for(int h=0;h<3;h++)for(int version=1;version<=2;version++){
   auto const& graphs=pg[version-1];std::vector<PACEVAL_HANDLE> hs={graphs.at("calibrated_probability").handle,graphs.at("sensitivity_mean").handle};
   std::vector<Row> batchrows;std::vector<std::pair<double,double>> coordinates;batchrows.reserve(256);coordinates.reserve(256);
   auto flush=[&](){if(batchrows.empty())return;size_t n=batchrows.size();auto v=e.batch(hs,batchrows);
     for(size_t j=0;j<n;j++){auto ref=native(batchrows[j],version);assert_close(v[j],ref.p,"surface probability");assert_close(v[n+j],ref.dmean,"surface sensitivity");surface_native_checks+=2;
       f<<HAZARDS[h]<<",v"<<version<<','<<e.fmt(coordinates[j].first)<<','<<e.fmt(coordinates[j].second)<<','<<e.fmt(v[j])<<','<<e.fmt(v[n+j])<<'\n';surface_rows++;
     }batchrows.clear();coordinates.clear();};
   for(int ik=0;ik<=40;ik++)for(int im=0;im<=40;im++){
    auto r=generate(0,0,h).r;r[K]=std::round(51.0*ik/40.0);double a=-2.0+4.0*im/40.0;r[MEAN]=r[THR]+a*r[SCALE];set_coefficients(r,h,version);
    batchrows.push_back(r);coordinates.emplace_back(r[K]/r[N],a);if(batchrows.size()==256)flush();
   }flush();
  }
 }
 // Matched synthetic hazard pairs: p(A intersection B) is bounded, not inferred by multiplying marginals.
 auto ch=handles(cg);auto ci=indexes(cg);uint64_t compound_pairs=0,compound_checks=0;
 const std::array<std::pair<int,int>,3> pairings={{{0,1},{0,2},{1,2}}};
 for(int version=1;version<=2;version++){
  std::vector<Row> rows;std::vector<std::array<int,4>> info;rows.reserve(BATCH);info.reserve(BATCH);
  auto flush=[&](){if(rows.empty())return;auto vals=e.batch(ch,rows);size_t n=rows.size();
   for(size_t j=0;j<n;j++){double pa=rows[j][PROB],pb=rows[j][RAW],lo=std::max(0.0,pa+pb-1),hi=std::min(pa,pb);
    assert_close(vals[ci.at("frechet_joint_lower")*n+j],lo,"Frechet lower");assert_close(vals[ci.at("frechet_joint_upper")*n+j],hi,"Frechet upper");compound_checks+=2;
    if(compound_pairs%197==0)joint<<info[j][0]<<','<<info[j][1]<<','<<version<<','<<info[j][2]<<','<<info[j][3]<<','<<e.fmt(pa)<<','<<e.fmt(pb)<<','<<e.fmt(lo)<<','<<e.fmt(hi)<<'\n';
    compound_pairs++;
   }rows.clear();info.clear();};
  for(int site=0;site<sites;site++)for(int w=0;w<4;w++)for(auto [a,b]:pairings){
   size_t idx=(size_t(site)*4+w)*3;Row r{};r.fill(1);r[PROB]=probabilities[version-1][idx+a];r[RAW]=probabilities[version-1][idx+b];
   rows.push_back(r);info.push_back({site,w,a,b});if(rows.size()==BATCH)flush();
  }flush();
 }
 formula.close();audit.close();trace.close();summary.close();joint.close();
 std::ofstream evidence(out/"execution_evidence.json");demand(bool(evidence),"Cannot create evidence");
 evidence<<"{\n  \"study\": \"Site-Level Extreme Weather Decision Kernels\",\n  \"scientific_status\": \"synthetic mathematical functionality, not operational weather guidance\",\n  \"runtime\": \"original paceval 4.25 Linux SDK\",\n  \"site_count\": "<<sites<<",\n  \"windows_per_site\": 4,\n  \"hazards_per_window\": 3,\n  \"synthetic_feature_rows\": "<<records.size()<<",\n  \"model_versions\": 2,\n  \"model_point_rows\": "<<model_cases<<",\n  \"unique_graphs_created\": "<<e.created()<<",\n  \"unique_graphs_executed\": "<<e.executed()<<",\n  \"scalar_calls\": "<<e.scalar_calls<<",\n  \"multi_graph_batch_calls\": "<<e.batch_calls<<",\n  \"graph_point_evaluations\": "<<e.graph_outputs<<",\n  \"native_cpp_independent_model_checks\": "<<independent_checks<<",\n  \"compound_pairs_evaluated\": "<<compound_pairs<<",\n  \"compound_independent_checks\": "<<compound_checks<<",\n  \"surface_rows\": "<<surface_rows<<",\n  \"surface_independent_checks\": "<<surface_native_checks<<",\n  \"high_precision_audit_candidate_rows\": "<<audit_rows<<",\n  \"end_to_end_traces\": "<<trace_rows<<"\n}\n";
 std::cout<<"WEATHER RESEARCH COMPLETE sites="<<sites<<" feature_rows="<<records.size()<<" model_cases="<<model_cases<<" graphs="<<e.executed()<<" graph_outputs="<<e.graph_outputs<<" native_checks="<<independent_checks<<" compound_checks="<<compound_checks<<"\n";
}
int main(int argc,char** argv){try{Engine e;
 if(argc>1){std::string mode=argv[1];if(mode=="--test-conversion"){conversion_test(e);std::cout<<"CONVERSION_OK\n";return 0;}
  if(mode=="--test-operators"){operator_test(e);std::cout<<"OPERATORS_OK\n";return 0;}
  if(mode=="--test-layout"){layout_test(e);std::cout<<"BATCH_LAYOUT_OK\n";return 0;}
  if(mode=="--test-invalid"){invalid_test(e);std::cout<<"INVALID_INPUT_OK\n";return 0;}
  if(mode=="--run"){int sites=10000;fs::path out="results";for(int i=2;i<argc;i+=2){demand(i+1<argc,"Missing CLI value");std::string key=argv[i],v=argv[i+1];if(key=="--sites")sites=std::stoi(v);else if(key=="--out")out=v;else throw std::runtime_error("Unknown CLI option "+key);}run(e,sites,out);return 0;}
 }
 std::cout<<"Usage: weather_kernels --run [--sites 10000 --out results] | --test-conversion | --test-operators | --test-layout | --test-invalid\n";return 1;
 }catch(const std::exception& ex){std::cerr<<"ERROR: "<<ex.what()<<'\n';return 2;}}
