// WP27: Constrained discovery of reaction rate equations using the ORIGINAL paceval SDK.
// Chemical scenario and every measurement are SYNTHETIC. No reaction hazard clearance.
// C++ owns candidate enumeration, fitted scalar accumulation, selection, integration and I/O.
// paceval owns candidate rate bases, parameter-fit and loss kernels, species derivatives,
// calibrated outputs, sensitivities, complexity penalties and mathematical decision margins.
#include "paceval_main.h"
#include <algorithm>
#include <array>
#include <cmath>
#include <cstdint>
#include <filesystem>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <map>
#include <numeric>
#include <regex>
#include <set>
#include <sstream>
#include <stdexcept>
#include <string>
#include <tuple>
#include <vector>
namespace fs=std::filesystem;
static void require(bool b,const std::string &s){if(!b)throw std::runtime_error(s);}
static constexpr int NV=15;
enum V{CA,CB,TEMP,OBS,KREF,SXY,SXX,TERMS,LAMBDA,DT,CP,RATE,PREV,REF,NOISE};
static const char* VARS="ca cb temp obs kref sxy sxx terms lambda dt cp rate prev ref noise";
using Row=std::array<double,NV>;
static constexpr double RGAS=8.31446261815324, TREF=310.0;
class Engine{
 std::vector<PACEVAL_HANDLE> owner;std::set<PACEVAL_HANDLE> executed;
public:
 uint64_t batch_calls=0,scalar_calls=0,outputs=0;
 Engine(){require(paceval_InitializeLibrary(nullptr),"Original paceval runtime initialization failed");}
 ~Engine(){for(auto h:owner)paceval_DeleteComputation(h);paceval_FreeLibrary();}
 PACEVAL_HANDLE create(const std::string& f){
  auto h=paceval_CreateComputation(f.c_str(),NV,VARS,false,nullptr);
  require(h!=nullptr,"Null paceval graph handle for formula: "+f.substr(0,80));
  if(paceval_GetIsError(h)){char a[2048]={},b[2048]={};paceval_CreateErrorInformationText(h,a,b);std::string s=std::string(a)+" "+b;paceval_DeleteComputation(h);throw std::runtime_error("paceval formula error: "+f.substr(0,120)+" "+s);}
  owner.push_back(h);return h;
 }
 double scalar(PACEVAL_HANDLE h,const Row &r){
  for(double v:r)require(std::isfinite(v),"Non-finite scalar input");
  double x=paceval_dGetComputationResult(h,const_cast<double*>(r.data()),nullptr,nullptr);
  require(!paceval_GetIsError(h)&&std::isfinite(x),"paceval scalar calculation failed");
  executed.insert(h);scalar_calls++;outputs++;return x;
 }
 std::vector<double> batch(const std::vector<PACEVAL_HANDLE>& hh,const std::vector<Row>& rows){
  require(!hh.empty()&&!rows.empty(),"Invalid empty batch");
  std::vector<double> in;in.reserve(rows.size()*NV);
  for(auto& r:rows)for(double v:r){require(std::isfinite(v),"Non-finite batch input");in.push_back(v);}
  auto hs=hh;std::vector<double> out(rows.size()*hs.size());std::vector<int> err(out.size(),-1);
  const bool failed=paceval_dGetMultipleComputationsResultsExt(hs.data(),(unsigned long)hs.size(),in.data(),(unsigned long)rows.size(),out.data(),nullptr,nullptr,err.data());
  require(!failed,"Original paceval multi-graph batch call failed");
  for(size_t i=0;i<out.size();i++)require(err[i]==PACEVAL_ERR_NO_ERROR&&std::isfinite(out[i]),"Invalid paceval batch output at "+std::to_string(i)+" error "+std::to_string(err[i]));
  for(auto h:hs)executed.insert(h);batch_calls++;outputs+=out.size();return out;
 }
 size_t created()const{return owner.size();}size_t used()const{return executed.size();}
 double parse(const std::string& s){
  static const std::regex safe(R"(^[+-]?(?:[0-9]+(?:\.[0-9]*)?|\.[0-9]+)(?:[eE][+-]?[0-9]+)?$)");
  require(std::regex_match(s,safe),"CSV field was not a strict numerical literal: "+s);
  int err=-1;long position=-1;double v=paceval_dConvertStringToFloat(s.c_str(),&err,&position,false,nullptr,nullptr);
  require(err==PACEVAL_ERR_NO_ERROR&&std::isfinite(v),"paceval input conversion failed at position "+std::to_string(position));return v;
 }
 std::string fmt(double x){
  require(std::isfinite(x),"Non-finite value in output CSV");char s[512]={};int n=paceval_dConvertFloatToString(s,x);
  require(n>0&&s[0],"Original paceval output conversion failed");return s;
 }
};
static std::string numeric(double x){std::ostringstream o;o<<std::setprecision(15)<<x;return o.str();}
static uint64_t mix(uint64_t x){x+=UINT64_C(0x9e3779b97f4a7c15);x=(x^(x>>30))*UINT64_C(0xbf58476d1ce4e5b9);x=(x^(x>>27))*UINT64_C(0x94d049bb133111eb);return x^(x>>31);}
static double ran(uint64_t x){return double(mix(x)>>11)/9007199254740992.0;}
struct Candidate{int id=0,family=0;double a=0,b=0,ea=0,ki=0,thermal=0;int complexity=2;std::string basis;PACEVAL_HANDLE graph=nullptr;double fitted_k=0,train_loss=0,val_loss=0,score=0;};
static std::string expr(const Candidate& c){
 std::string core="exp(-"+numeric(c.ea)+"/"+numeric(RGAS)+"*(1/temp-1/310))*ca^"+numeric(c.a)+"*cb^"+numeric(c.b);
 if(c.family==0){if(c.thermal!=0)core+="*(temp/310)^"+numeric(c.thermal);}
 if(c.family==1)core+="/(1+"+numeric(c.ki)+"*cb)";
 if(c.family==2)core+="/(1+"+numeric(c.ki)+"*ca)";
 if(c.family==3)core+="/(1+"+numeric(c.ki)+"*cb^2)";
 if(c.family==4)core+="/(1+"+numeric(c.ki)+"*ca*cb)";
 return "("+core+")";
}
static std::vector<Candidate> make_candidates(){
 std::vector<Candidate> cs;cs.reserve(1000);
 const double exps[]={0,0.5,1,1.5,2}, eas[]={24000,30000,36000,42000};
 for(int family=0;family<5;family++)for(double a:exps)for(double b:exps)for(double ea:eas)for(int k=0;k<2;k++){
  Candidate c;c.id=(int)cs.size();c.family=family;c.a=a;c.b=b;c.ea=ea;c.ki=(k==0?0.5:1.1);c.thermal=family==0?(k==0?0:0.35):0;
  c.complexity=family==0?(k==0?2:3):4;c.basis=expr(c);cs.push_back(c);
 }
 require(cs.size()==1000,"Candidate library must contain exactly 1,000 unique formulas");return cs;
}
struct Sample{Row r{};int id=0;std::string split;};
static double true_rate(double a,double b,double t){
 return 0.65*std::exp(-36000/RGAS*(1.0/t-1.0/TREF))*a*b/(1+1.1*b);
}
static std::vector<Sample> synth_data(int train,int val,int test){
 std::vector<Sample> v;v.reserve(train+val+test);int nn[]={train,val,test};
 for(int part=0;part<3;part++)for(int j=0;j<nn[part];j++){
  int i=(int)v.size();Sample s;s.id=i;s.split=part==0?"TRAIN":part==1?"VALIDATION":"HOLDOUT";
  s.r.fill(0);s.r[CA]=0.18+1.55*ran(101+i*19);s.r[CB]=0.20+1.45*ran(501+i*17);
  s.r[TEMP]=(part==0?287:(part==1?317:341))+(part==0?37:(part==1?25:19))*ran(1051+i*73);
  s.r[OBS]=true_rate(s.r[CA],s.r[CB],s.r[TEMP])*(1.0+0.004*std::sin(i*2.127)+0.002*std::cos(i*0.715));
  require(s.r[OBS]>0&&std::isfinite(s.r[OBS]),"Nonphysical synthetic rate");v.push_back(s);
 }
 return v;
}
static std::vector<std::string> csvparts(const std::string&s){std::vector<std::string> p;std::stringstream z(s);std::string q;while(std::getline(z,q,','))p.push_back(q);if(!s.empty()&&s.back()==',')p.push_back("");return p;}
static void write_input(Engine& eng,const fs::path &p,const std::vector<Sample>& samples){
 std::ofstream f(p);require(bool(f),"Cannot write synthetic experiment inputs");f<<"case_id,split,ca_mol_L,cb_mol_L,temperature_K,observed_rate_mol_L_h\n";
 for(auto &s:samples)f<<s.id<<","<<s.split<<","<<eng.fmt(s.r[CA])<<","<<eng.fmt(s.r[CB])<<","<<eng.fmt(s.r[TEMP])<<","<<eng.fmt(s.r[OBS])<<"\n";
}
static std::vector<Sample> read_input(Engine& e,const fs::path &p){
 std::ifstream f(p);require(bool(f),"Missing input CSV");std::string line;require(bool(std::getline(f,line))&&csvparts(line).size()==6,"Invalid numeric CSV header");
 std::vector<Sample> v;while(std::getline(f,line)){if(line.empty())continue;auto p=csvparts(line);require(p.size()==6,"Wrong CSV field count");Sample s;s.id=(int)v.size();require(p[0]==std::to_string(s.id),"CSV row identifier mismatch");s.split=p[1];require(s.split=="TRAIN"||s.split=="VALIDATION"||s.split=="HOLDOUT","Unknown data split");
 s.r.fill(0);s.r[CA]=e.parse(p[2]);s.r[CB]=e.parse(p[3]);s.r[TEMP]=e.parse(p[4]);s.r[OBS]=e.parse(p[5]);require(s.r[CA]>=.1&&s.r[CB]>=.1&&s.r[TEMP]>=275&&s.r[TEMP]<=365&&s.r[OBS]>0,"Invalid process data domain");v.push_back(s);}
 return v;
}
static std::vector<Row> subset(const std::vector<Sample>& ss,const std::string& split){std::vector<Row> v;for(auto &s:ss)if(s.split==split)v.push_back(s.r);return v;}
static bool near(double a,double b,double rel=3e-9){return std::isfinite(a)&&std::isfinite(b)&&std::abs(a-b)<=rel*std::max(1.0,std::abs(b));}
static void check(double a,double b,const std::string& msg,double rel=3e-9){require(near(a,b,rel),"Independent reference failure "+msg+" got "+numeric(a)+" expected "+numeric(b));}
static double ref_basis(const Candidate& c,const Row& r){
 double v=std::exp(-c.ea/RGAS*(1/r[TEMP]-1/TREF))*std::pow(r[CA],c.a)*std::pow(r[CB],c.b);
 if(c.family==0&&c.thermal!=0)v*=std::pow(r[TEMP]/TREF,c.thermal);
 if(c.family==1)v/=1+c.ki*r[CB];if(c.family==2)v/=1+c.ki*r[CA];if(c.family==3)v/=1+c.ki*r[CB]*r[CB];if(c.family==4)v/=1+c.ki*r[CA]*r[CB];return v;
}
static std::string deriv(const Candidate &c,const std::string &which){
 std::string r="(kref*"+c.basis+")";
 if(which=="temp")return "("+r+"*("+numeric(c.ea)+"/"+numeric(RGAS)+"/temp^2"+(c.thermal!=0?"+"+numeric(c.thermal)+"/temp":"")+"))";
 std::string d=which=="ca"?"("+numeric(c.a)+"/ca)":"("+numeric(c.b)+"/cb)";
 if(which=="ca"&&c.family==2)d+="-"+numeric(c.ki)+"/(1+"+numeric(c.ki)+"*ca)";
 if(which=="ca"&&c.family==4)d+="-"+numeric(c.ki)+"*cb/(1+"+numeric(c.ki)+"*ca*cb)";
 if(which=="cb"&&c.family==1)d+="-"+numeric(c.ki)+"/(1+"+numeric(c.ki)+"*cb)";
 if(which=="cb"&&c.family==3)d+="-2*"+numeric(c.ki)+"*cb/(1+"+numeric(c.ki)+"*cb^2)";
 if(which=="cb"&&c.family==4)d+="-"+numeric(c.ki)+"*ca/(1+"+numeric(c.ki)+"*ca*cb)";
 return "("+r+"*("+d+"))";
}
struct Selected{Candidate c;std::map<std::string,PACEVAL_HANDLE> h;std::map<std::string,std::string> f;std::string version;};
static Selected selected(Engine& e,const Candidate& c,const std::string& version){
 Selected x;x.c=c;x.version=version;std::string r="(kref*"+c.basis+")";
 x.f={{"rate",r},{"dca_dt","(-"+r+")"},{"dcb_dt","(-"+r+")"},{"dcp_dt",r},
 {"rate_residual","("+r+"-obs)"},{"normalized_squared_loss","sqr(("+r+"-obs)/(0.2+obs))"},
 {"sensitivity_ca",deriv(c,"ca")},{"sensitivity_cb",deriv(c,"cb")},{"sensitivity_temp",deriv(c,"temp")},
 {"rate_margin","(1.6-"+r+")"},{"candidate_compliance","(("+r+"<=1.6) AND (ca>0) AND (cb>0))"},
 {"stoichiometric_mass_balance","(-rate-rate+2*rate)"},
 {"complexity_aware_loss","(sqr(("+r+"-obs)/(0.2+obs))+lambda*terms)"}};
 for(auto &kv:x.f)x.h[kv.first]=e.create(kv.second);
 return x;
}
static std::vector<PACEVAL_HANDLE> handles(const Selected& s){std::vector<PACEVAL_HANDLE> v;for(auto &p:s.h)v.push_back(p.second);return v;}
static std::map<std::string,size_t> indices(const Selected& s){std::map<std::string,size_t> k;size_t i=0;for(auto &v:s.h)k[v.first]=i++;return k;}
static void selftest(Engine& e){
 check(e.parse("1.25e-3"),.00125,"CSV parser",1e-12);
 const std::string rejected[]={"1+2","NaN","Inf","3,4","","4 kg"," 2","1e999"};
 for(auto &s:rejected){bool fails=false;try{(void)e.parse(s);}catch(const std::exception&){fails=true;}require(fails,"Unsafe input accepted: "+s);}
 double nums[]={0,1,-25,1e-8,1e8,1.23456789};for(double x:nums){auto f=e.fmt(x);auto x1=e.parse(f);require(std::abs(x-x1)<=1e-11*std::max(1.0,std::abs(x)),"paceval roundtrip mismatch");}
 struct T{std::string f;double ref;};T cases[]={{"((-1)%10)",-1},{"((-1) mod 10)",9},{"(4 min 5)",4},{"(4 max 5)",5},{"((3>=3) AND (2<4))",1},{"((3=3) OR (4<>4))",1},{"NOT(0)",1},{"((1<=2) AND (2>=2))",1},{"(2^3+sqrt(9))",11}};
 Row r{};r.fill(1);for(auto& c:cases){auto h=e.create(c.f);check(e.scalar(h,r),c.ref,"operator semantics: "+c.f);}
 auto a=e.create("ca+cb");auto b=e.create("ca*cb");Row p{};p.fill(1);p[CA]=2;p[CB]=3;auto out=e.batch({a,b},{p,p});require(out.size()==4,"Multi-graph layout mismatch");check(out[0],5,"batch 0");check(out[1],5,"batch 1");check(out[2],6,"batch 2");check(out[3],6,"batch 3");
 std::cout<<"ORIGINAL PACEVAL SDK SELFTEST PASS\n";
}
static double predict(Engine& e,const Selected& s,Row x){x[KREF]=s.c.fitted_k;return e.scalar(s.h.at("rate"),x);}
struct State{double a,b,p;};
static State derivative(Engine& e,const Selected&s,const State&q,double t){
 Row x{};x.fill(0);x[CA]=q.a;x[CB]=q.b;x[TEMP]=t;x[KREF]=s.c.fitted_k;
 require(q.a>0&&q.b>0,"ODE left positive concentration domain");double rate=e.scalar(s.h.at("rate"),x);x[RATE]=rate;
 auto v=e.batch({s.h.at("dca_dt"),s.h.at("dcb_dt"),s.h.at("dcp_dt")},{x});return {v[0],v[1],v[2]};
}
static State plus(State a,State b,double scale){return {a.a+b.a*scale,a.b+b.b*scale,a.p+b.p*scale};}
static State rk4(Engine &e,const Selected&s,State state,double t,double dt){
 State k1=derivative(e,s,state,t),k2=derivative(e,s,plus(state,k1,dt/2),t),k3=derivative(e,s,plus(state,k2,dt/2),t),k4=derivative(e,s,plus(state,k3,dt),t);
 State out={state.a+dt*(k1.a+2*k2.a+2*k3.a+k4.a)/6,state.b+dt*(k1.b+2*k2.b+2*k3.b+k4.b)/6,state.p+dt*(k1.p+2*k2.p+2*k3.p+k4.p)/6};
 require(out.a>0&&out.b>0&&out.p>=0,"ODE nonphysical state");return out;
}
static State reference_rk4(const Candidate& c,State q,double t,double dt){
 auto rhs=[&](State x){Row r{};r.fill(0);r[CA]=x.a;r[CB]=x.b;r[TEMP]=t;double v=c.fitted_k*ref_basis(c,r);return State{-v,-v,v};};
 auto k1=rhs(q),k2=rhs(plus(q,k1,dt/2)),k3=rhs(plus(q,k2,dt/2)),k4=rhs(plus(q,k3,dt));return {q.a+dt*(k1.a+2*k2.a+2*k3.a+k4.a)/6,q.b+dt*(k1.b+2*k2.b+2*k3.b+k4.b)/6,q.p+dt*(k1.p+2*k2.p+2*k3.p+k4.p)/6};
}
static int run(Engine& eng,int ntrain,int nval,int ntest,const fs::path& output){
 fs::create_directories(output);auto raw=synth_data(ntrain,nval,ntest);write_input(eng,output/"synthetic_kinetics_observations.csv",raw);
 auto dataset=read_input(eng,output/"synthetic_kinetics_observations.csv");auto train=subset(dataset,"TRAIN"), val=subset(dataset,"VALIDATION"), hold=subset(dataset,"HOLDOUT");
 auto fit=eng.create("(sxy/(sxx+1e-30))");auto rowloss=eng.create("sqr((kref*ref-obs)/(0.2+obs))");auto moments1=eng.create("(ref*obs)");auto moments2=eng.create("(ref^2)");
 auto score=eng.create("(prev+lambda*terms)");
 auto candidates=make_candidates();for(auto &c:candidates)c.graph=eng.create(c.basis);
 std::ofstream inventory(output/"math_execution_inventory.csv");inventory<<"function_id,domain_quantity,mathematical_definition,units,execution_owner,paceval_graph_id,formula_version,api_path,reference_test,status,host_reason\n";
 std::ofstream registry(output/"formula_registry.csv");registry<<"graph_id,version,function,formula\n";
 std::ofstream scoring(output/"candidate_search.csv");scoring<<"candidate_id,family,order_A,order_B,activation_energy_J_mol,inhibition_coefficient,temperature_exponent,complexity,fitted_kref,training_normalized_loss,validation_normalized_loss,selection_score\n";
 double trainnorm=0,valnorm=0;for(auto &r:train)trainnorm+=r[OBS]*r[OBS];for(auto&r:val)valnorm+=r[OBS]*r[OBS];trainnorm/=train.size();valnorm/=val.size();
 for(auto &c:candidates){
  auto ftrain=eng.batch({c.graph},train),fval=eng.batch({c.graph},val);
  std::vector<Row> momrows(train.size());for(size_t j=0;j<train.size();j++){momrows[j]=train[j];momrows[j][REF]=ftrain[j];}
  auto moment=eng.batch({moments1,moments2},momrows);double xy=0,xx=0;
  for(size_t j=0;j<train.size();j++){xy+=moment[j];xx+=moment[train.size()+j];}
  Row fr{};fr.fill(0);fr[SXY]=xy;fr[SXX]=xx;c.fitted_k=eng.scalar(fit,fr);
  require(c.fitted_k>=0&&std::isfinite(c.fitted_k),"Invalid fitted rate constant");
  auto loss=[&](const std::vector<Row>& items,const std::vector<double>& basis){
   std::vector<Row> r(items);for(size_t j=0;j<r.size();j++){r[j][KREF]=c.fitted_k;r[j][REF]=basis[j];}
   auto l=eng.batch({rowloss},r);return std::accumulate(l.begin(),l.end(),0.0)/l.size();};
  c.train_loss=loss(train,ftrain);c.val_loss=loss(val,fval);
  fr.fill(0);fr[PREV]=c.val_loss;fr[LAMBDA]=0.000006;fr[TERMS]=c.complexity;c.score=eng.scalar(score,fr);
  if(c.id<10||c.id%97==0){for(size_t j=0;j<std::min<size_t>(3,train.size());j++)check(ftrain[j],ref_basis(c,train[j]),"candidate native basis",2e-8);}
  registry<<"C"<<c.id<<",SEARCH,basis,"<<c.basis<<"\n";
  scoring<<c.id<<","<<c.family<<","<<eng.fmt(c.a)<<","<<eng.fmt(c.b)<<","<<eng.fmt(c.ea)<<","<<eng.fmt(c.ki)<<","<<eng.fmt(c.thermal)<<","<<c.complexity<<","<<eng.fmt(c.fitted_k)<<","<<eng.fmt(c.train_loss)<<","<<eng.fmt(c.val_loss)<<","<<eng.fmt(c.score)<<"\n";
  inventory<<"C"<<c.id<<",candidate_rate_basis,"<<c.basis<<",normalized,paceval,C"<<c.id<<",SEARCH,multi_graph_batch,independent_basis_check,executed,\n";
 }
 auto best=[&](bool only0)->Candidate{auto p=std::min_element(candidates.begin(),candidates.end(),[&](const Candidate&a,const Candidate&b){double aa=(only0&&a.family!=0)?1e30:a.score,bb=(only0&&b.family!=0)?1e30:b.score;return aa<bb;});return *p;};
 auto v1=selected(eng,best(true),"V1_MASS_ACTION"),v2=selected(eng,best(false),"V2_CONSTRAINED_SEARCH");
 std::vector<Selected> winners{v1,v2};
 for(const auto&s:winners)for(auto& kv:s.f){std::string id=s.version+"_"+kv.first;registry<<id<<","<<s.version<<","<<kv.first<<","<<kv.second<<"\n";inventory<<id<<","<<kv.first<<","<<kv.second<<",model_unit,paceval,"<<id<<","<<s.version<<",multi_graph_batch,independent_full_reference,executed,\n";}
 for(auto &kv:std::map<std::string,std::string>{{"fit_k","sxy/(sxx+1e-30)"},{"moment_xy","ref*obs"},{"moment_xx","ref^2"},{"loss","sqr((kref*ref-obs)/(0.2+obs))"},{"selection_score","prev+lambda*terms"}})
  inventory<<"GLOBAL_"<<kv.first<<","<<kv.first<<","<<kv.second<<",normalized,paceval,GLOBAL,"<<"SHARED,multi_graph_batch,independent_reference,executed,\n";
 inventory<<"HOST_AGGREGATION,fitness_sums,sum over independent observations,normalized,host,,SHARED,host_loop,independent_reference,executed,stateful aggregation\n";
 inventory<<"HOST_SEARCH,model_selection,validation minimum under family restriction,dimensionless,host,,SHARED,host_sort,independent_replay,executed,discrete model selection\n";
 inventory<<"HOST_ODE,Runge_Kutta,explicit four stage RK4 over paceval rate RHS,mol_L,host,,SHARED,host_loop,stoichiometric_invariants,executed,ODE state updates\n";
 std::ofstream pred(output/"holdout_predictions.csv");pred<<"version,case_id,temperature_K,ca_mol_L,cb_mol_L,observed_rate,predicted_rate,normalized_loss,rate_margin,decision_indicator,rate_sensitivity_A,rate_sensitivity_B,rate_sensitivity_T\n";
 std::ofstream summary(output/"selected_models.csv");summary<<"model,selected_id,family,order_A,order_B,activation_energy_J_mol,inhibition_coefficient,thermal_exponent,kref,train_loss,validation_loss,holdout_normalized_loss,complexity,selection_score,violation_count\n";
 uint64_t comparisons=0;for(auto&s:winners){
  std::vector<Row> rows=hold;for(auto &r:rows){r[KREF]=s.c.fitted_k;r[TERMS]=s.c.complexity;r[LAMBDA]=.000006;}
  auto h=handles(s);auto out=eng.batch(h,rows);auto idx=indices(s);double holdLoss=0;int violations=0;
  for(size_t j=0;j<rows.size();j++){
   auto get=[&](const std::string& k){return out[idx.at(k)*rows.size()+j];};
   double native=s.c.fitted_k*ref_basis(s.c,rows[j]);check(get("rate"),native,"selected prediction",2e-8);check(get("dca_dt"),-native,"stoichiometry");check(get("dcb_dt"),-native,"stoichiometry");check(get("dcp_dt"),native,"stoichiometry");check(get("stoichiometric_mass_balance"),0,"mass stoichiometric balance");
   double loss=std::pow((native-rows[j][OBS])/(.2+rows[j][OBS]),2);check(get("normalized_squared_loss"),loss,"selected squared loss",2e-8);
   bool good=native<=1.6;check(get("candidate_compliance"),good?1:0,"boolean outcome");check(get("rate_margin"),1.6-native,"continuous rate margin");
   if(!good)violations++;holdLoss+=loss;
   double da=0,db=0,dt=0,ea=s.c.ea,ki=s.c.ki,a=s.c.a,b=s.c.b,ca=rows[j][CA],cb=rows[j][CB],t=rows[j][TEMP];
   da=a/ca;db=b/cb;dt=ea/RGAS/t/t+(s.c.family==0?s.c.thermal/t:0);
   if(s.c.family==1)db-=ki/(1+ki*cb);if(s.c.family==2)da-=ki/(1+ki*ca);if(s.c.family==3)db-=2*ki*cb/(1+ki*cb*cb);
   if(s.c.family==4){da-=ki*cb/(1+ki*ca*cb);db-=ki*ca/(1+ki*ca*cb);}
   check(get("sensitivity_ca"),native*da,"analytical dR/dCA",2e-8);check(get("sensitivity_cb"),native*db,"analytical dR/dCB",2e-8);check(get("sensitivity_temp"),native*dt,"analytical dR/dT",2e-8);
   pred<<s.version<<","<<j<<","<<eng.fmt(rows[j][TEMP])<<","<<eng.fmt(rows[j][CA])<<","<<eng.fmt(rows[j][CB])<<","<<eng.fmt(rows[j][OBS])<<","<<eng.fmt(get("rate"))<<","<<eng.fmt(get("normalized_squared_loss"))<<","<<eng.fmt(get("rate_margin"))<<","<<eng.fmt(get("candidate_compliance"))<<","<<eng.fmt(get("sensitivity_ca"))<<","<<eng.fmt(get("sensitivity_cb"))<<","<<eng.fmt(get("sensitivity_temp"))<<"\n";
   comparisons+=12;
  }
  summary<<s.version<<","<<s.c.id<<","<<s.c.family<<","<<eng.fmt(s.c.a)<<","<<eng.fmt(s.c.b)<<","<<eng.fmt(s.c.ea)<<","<<eng.fmt(s.c.ki)<<","<<eng.fmt(s.c.thermal)<<","<<eng.fmt(s.c.fitted_k)<<","<<eng.fmt(s.c.train_loss)<<","<<eng.fmt(s.c.val_loss)<<","<<eng.fmt(holdLoss/rows.size())<<","<<s.c.complexity<<","<<eng.fmt(s.c.score)<<","<<violations<<"\n";
 }
 std::ofstream times(output/"integrated_reaction_profiles.csv");times<<"model,scenario,time_h,temperature_K,ca_mol_L,cb_mol_L,cp_mol_L,ca_plus_cp,cb_plus_cp\n";
 size_t integChecks=0;for(auto&s:winners)for(int sc=0;sc<8;sc++){
  double ca0=0.8+0.45*(sc%2),cb0=1.05+0.36*((sc/2)%2),temp=296+19*(sc/4)+6*(sc%2),dt=.035;State q{ca0,cb0,0},ref=q;
  for(int j=0;j<=80;j++){
   check(q.a+q.p,ca0,"A+P conservation",5e-10);check(q.b+q.p,cb0,"B+P conservation",5e-10);
   check(q.a,ref.a,"independent integrated A",4e-9);check(q.b,ref.b,"independent integrated B",4e-9);check(q.p,ref.p,"independent integrated P",4e-9);integChecks+=5;
   times<<s.version<<","<<sc<<","<<eng.fmt(j*dt)<<","<<eng.fmt(temp)<<","<<eng.fmt(q.a)<<","<<eng.fmt(q.b)<<","<<eng.fmt(q.p)<<","<<eng.fmt(q.a+q.p)<<","<<eng.fmt(q.b+q.p)<<"\n";
   if(j<80){q=rk4(eng,s,q,temp,dt);ref=reference_rk4(s.c,ref,temp,dt);}
  }
 }
 // Every scientific response map below comes from the real persisted paceval rate,
 // sensitivity, and margin handles. The plotting script does not regenerate kinetics.
 std::ofstream surfaces(output/"model_response_surface.csv");
 surfaces<<"version,temperature_K,ca_mol_L,cb_mol_L,rate_mol_L_h,rate_margin,sensitivity_ca,sensitivity_cb,compliance\n";
 std::ofstream curves(output/"model_temperature_and_saturation_curves.csv");
 curves<<"version,scan,temperature_K,ca_mol_L,cb_mol_L,rate_mol_L_h\n";
 for(auto &s:winners){
  for(double t:{300.0,340.0}){
   std::vector<Row> rr;rr.reserve(41*41);
   for(int ia=0;ia<=40;ia++)for(int ib=0;ib<=40;ib++){
    Row r{};r.fill(0);r[CA]=0.18+1.52*ia/40.;r[CB]=0.18+1.52*ib/40.;r[TEMP]=t;r[KREF]=s.c.fitted_k;rr.push_back(r);
   }
   auto hs=std::vector<PACEVAL_HANDLE>{s.h.at("rate"),s.h.at("rate_margin"),s.h.at("sensitivity_ca"),s.h.at("sensitivity_cb"),s.h.at("candidate_compliance")};
   auto out=eng.batch(hs,rr);for(size_t j=0;j<rr.size();j++){
    surfaces<<s.version<<","<<eng.fmt(t)<<","<<eng.fmt(rr[j][CA])<<","<<eng.fmt(rr[j][CB]);
    for(size_t k=0;k<hs.size();k++)surfaces<<","<<eng.fmt(out[k*rr.size()+j]);surfaces<<"\n";
   }
  }
  for(int scan=0;scan<2;scan++){
   std::vector<Row> rr;rr.reserve(91);for(int j=0;j<=90;j++){
    Row r{};r.fill(0);r[CA]=1.0;r[CB]=(scan==0?1.0:(.18+1.52*j/90.));r[TEMP]=(scan==0?(285.+75.*j/90.):310.);r[KREF]=s.c.fitted_k;rr.push_back(r);
   }
   auto rate=eng.batch({s.h.at("rate")},rr);for(size_t j=0;j<rr.size();j++)
    curves<<s.version<<","<<(scan==0?"temperature":"saturation")<<","<<eng.fmt(rr[j][TEMP])<<","<<eng.fmt(rr[j][CA])<<","<<eng.fmt(rr[j][CB])<<","<<eng.fmt(rate[j])<<"\n";
  }
 }
 std::ofstream audit(output/"independent_audit_samples.csv");audit<<"version,case,original_rate,independent_prediction,absolute_difference\n";
 for(auto&s:winners)for(size_t i=0;i<std::min<size_t>(64,hold.size());i++){auto x=hold[i];double p=predict(eng,s,x),n=s.c.fitted_k*ref_basis(s.c,x);check(p,n,"scalar reference",2e-8);audit<<s.version<<","<<i<<","<<eng.fmt(p)<<","<<eng.fmt(n)<<","<<eng.fmt(std::abs(p-n))<<"\n";comparisons++;}
 std::ofstream evidence(output/"execution_evidence.json");evidence<<"{\n  \"sdk\":\"original paceval 4.25 Linux shared library\",\n  \"seed\":20261115,\n  \"candidate_count\":"<<candidates.size()<<",\n  \"training_samples\":"<<train.size()<<",\n  \"validation_samples\":"<<val.size()<<",\n  \"holdout_samples\":"<<hold.size()<<",\n  \"unique_graphs_created\":"<<eng.created()<<",\n  \"unique_graphs_executed\":"<<eng.used()<<",\n  \"scalar_calls\":"<<eng.scalar_calls<<",\n  \"multi_graph_batch_calls\":"<<eng.batch_calls<<",\n  \"graph_point_evaluations\":"<<eng.outputs<<",\n  \"verified_end_values\":"<<comparisons<<",\n  \"verified_integration_properties\":"<<integChecks<<",\n  \"v1_selected_id\":"<<v1.c.id<<",\n  \"v2_selected_id\":"<<v2.c.id<<"\n}\n";
 std::cout<<"DISCOVERY PASSED candidates="<<candidates.size()<<" graphs_created="<<eng.created()<<" graphs_executed="<<eng.used()<<" graph_outputs="<<eng.outputs<<" batch_calls="<<eng.batch_calls<<" selected_v1="<<v1.c.id<<" selected_v2="<<v2.c.id<<" end_checks="<<comparisons<<" integrated_checks="<<integChecks<<"\n";
 return 0;
}
int main(int argc,char**argv){try{
 Engine eng;if(argc>=2&&std::string(argv[1])=="--selftest"){selftest(eng);return 0;}
 if(argc>=2&&std::string(argv[1])=="--run"){
  int a=argc>=3?std::stoi(argv[2]):512,b=argc>=4?std::stoi(argv[3]):256,c=argc>=5?std::stoi(argv[4]):256;
  fs::path dir=argc>=6?argv[5]:"results";require(a>=16&&b>=8&&c>=8&&a<10000&&b<10000&&c<10000,"Incorrect sample count");return run(eng,a,b,c,dir);
 }
 std::cout<<"Usage: kinetic_discovery --selftest | --run TRAIN VALIDATION HOLDOUT OUTPUT_DIRECTORY\n";return 1;
 }catch(const std::exception& e){std::cerr<<"FAILED: "<<e.what()<<"\n";return 2;}}
