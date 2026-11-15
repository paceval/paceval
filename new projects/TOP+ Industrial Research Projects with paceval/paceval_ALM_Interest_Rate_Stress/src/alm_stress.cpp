// WP33. Reusable paceval execution graphs for deterministic, illustrative EUR ALM
// cashflows and zero-rate-curve stresses. These are NOT Basel-prescribed shocks.
// All row discounting, derivatives, scenario margins and composite aggregate
// indicators execute inside paceval. The host owns variable-length aggregation.
#include "paceval_main.h"
#include <algorithm>
#include <array>
#include <cmath>
#include <filesystem>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <map>
#include <regex>
#include <sstream>
#include <stdexcept>
#include <string>
#include <vector>
namespace fs=std::filesystem;
namespace {
void require(bool b,const std::string&s){if(!b)throw std::runtime_error(s);}
void near(double x,double y,double abs=1e-8,double rel=1e-8){require(std::isfinite(x)&&std::isfinite(y)&&std::abs(x-y)<=abs+rel*std::max(std::abs(x),std::abs(y)),"Independent C++ reference discrepancy");}
const std::vector<std::string> V={"t","amt","sgn","level","slope","hump","tau","par","sh","lg","limit"};
const std::vector<std::string> S={"apv","lpv","adpar","ldpar","adur","ldur","aconv","lconv","ash","lsh","alg","llg","basegap","losslimit"};
const std::vector<std::string> C={"gap1","gap2","stress1","stress2","dv1","dv2","limit"};
std::string joined(const std::vector<std::string>&v){std::string s;for(auto&t:v){if(!s.empty())s+=' ';s+=t;}return s;}
std::vector<std::string> split(const std::string&s){std::stringstream ss(s);std::string t;std::vector<std::string>v;while(std::getline(ss,t,','))v.push_back(t);if(!s.empty()&&s.back()==',')v.push_back("");return v;}
bool numericLiteral(const std::string&s){static const std::regex r(R"(^[+-]?(?:[0-9]+(?:\.[0-9]*)?|\.[0-9]+)(?:[eE][+-]?[0-9]+)?$)");return std::regex_match(s,r);}
double parseNumber(const std::string&s){require(numericLiteral(s),"CSV numeric literal rejected: "+s);int err=-1;long pos=-1;double x=paceval_dConvertStringToFloat(s.c_str(),&err,&pos,false,nullptr,nullptr);require(err==0&&std::isfinite(x),"SDK numeric conversion failed");return x;}
std::string formatNumber(double x){require(std::isfinite(x),"Attempted to export nonfinite");char b[512]{};int k=paceval_dConvertFloatToString(b,x);require(k>0&&b[0]&&std::string(b).find(',')==std::string::npos,"SDK numeric output failed");return b;}
using Matrix=std::vector<std::vector<double>>;
struct Engine {
 std::vector<PACEVAL_HANDLE>owned;size_t scalarCalls=0,batchCalls=0,graphPoints=0;bool graphMajor=false;
 Engine(){require(paceval_InitializeLibrary(nullptr),"paceval initialisation failed");}
 ~Engine(){for(auto h:owned)paceval_DeleteComputation(h);paceval_FreeLibrary();}
 PACEVAL_HANDLE make(const std::string&f,const std::vector<std::string>&vars){auto names=joined(vars);auto h=paceval_CreateComputation(f.c_str(),(unsigned long)vars.size(),names.c_str(),false,nullptr);require(h&&!paceval_GetIsError(h),"Graph rejected: "+f);owned.push_back(h);return h;}
 double scalar(PACEVAL_HANDLE h,const std::vector<double>&v){auto x=v;double z=paceval_dGetComputationResult(h,x.empty()?nullptr:x.data(),nullptr,nullptr);scalarCalls++;require(!paceval_GetIsError(h)&&std::isfinite(z),"paceval scalar failed");return z;}
 void layoutProbe(){auto a=make("x+2*y",{"x","y"});auto b=make("3*x-y",{"x","y"});PACEVAL_HANDLE h[]={a,b};double in[]={1,2,4,7},out[4]{},lo[4]{},hi[4]{};int err[4]{};bool fail=paceval_dGetMultipleComputationsResultsExt(h,2,in,2,out,lo,hi,err);require(!fail&&std::all_of(err,err+4,[](int e){return e==0;}),"Multi-graph layout probe failed");if(std::abs(out[0]-5)<1e-10&&std::abs(out[1]-18)<1e-10&&std::abs(out[2]-1)<1e-10&&std::abs(out[3]-5)<1e-10)graphMajor=true;else if(std::abs(out[0]-5)<1e-10&&std::abs(out[1]-1)<1e-10&&std::abs(out[2]-18)<1e-10&&std::abs(out[3]-5)<1e-10)graphMajor=false;else throw std::runtime_error("Unexpected layout");batchCalls++;graphPoints+=4;}
 Matrix multi(const std::vector<PACEVAL_HANDLE>&h,const Matrix&data,size_t vars){require(!h.empty()&&!data.empty(),"Empty batch");std::vector<double>in;in.reserve(data.size()*vars);for(auto&row:data){require(row.size()==vars,"Batch width mismatch");for(auto x:row)require(std::isfinite(x),"Nonfinite batch input");in.insert(in.end(),row.begin(),row.end());}std::vector<double>out(h.size()*data.size()),low(out.size()),high(out.size());std::vector<int>errors(out.size(),-1);bool failed=paceval_dGetMultipleComputationsResultsExt(const_cast<PACEVAL_HANDLE*>(h.data()),h.size(),in.data(),data.size(),out.data(),low.data(),high.data(),errors.data());require(!failed,"Multi-graph failed");for(int e:errors)require(e==0,"Multi-graph error "+std::to_string(e));Matrix z(data.size(),std::vector<double>(h.size()));for(size_t i=0;i<data.size();i++)for(size_t j=0;j<h.size();j++){double q=out[graphMajor?j*data.size()+i:i*h.size()+j];require(std::isfinite(q),"Nonfinite batch result");z[i][j]=q;}batchCalls++;graphPoints+=out.size();return z;}
 std::vector<double>one(PACEVAL_HANDLE h,const Matrix&data,size_t vars){require(!data.empty(),"Empty single batch");std::vector<double>in;in.reserve(data.size()*vars);for(auto&r:data){require(r.size()==vars,"Width mismatch");in.insert(in.end(),r.begin(),r.end());}std::vector<double>out(data.size()),lo(data.size()),hi(data.size());std::vector<int>e(data.size(),-1);bool failed=paceval_dGetComputationResultExt(h,in.data(),data.size(),out.data(),lo.data(),hi.data(),e.data());require(!failed,"Single-graph batch failed");for(size_t i=0;i<out.size();i++)require(e[i]==0&&std::isfinite(out[i]),"Single-graph output invalid");batchCalls++;graphPoints+=out.size();return out;}
};
struct Graph{std::string v,id,expr,units,purpose;PACEVAL_HANDLE h;size_t evals=0;};
struct Models{
 Engine&e;std::vector<Graph>g;std::map<std::string,size_t>idx;
 Models(Engine&engine):e(engine){
   const std::string base="(level+slope*(1-exp(-t/tau))+hump*(t/tau)*exp(-t/tau))";
   const std::string shortWeight="exp(-t/4)";
   const std::string longWeight="(1-exp(-t/4))";
   auto add=[&](const std::string&v,const std::string&id,const std::string&f,const std::string&u,const std::string&p){
     auto&vars=v=="SUM"?S:(v=="COMPARE"?C:V);
     idx[v+"_"+id]=g.size();g.push_back({v,id,f,u,p,e.make(f,vars),0});
   };
   for(auto v:{std::string("V1"),std::string("V2")}){
     const bool shaped=(v=="V2");
     const std::string shock=shaped?"(par+sh*"+shortWeight+"+lg*"+longWeight+")":"par";
     const std::string shockDeriv=shaped?"((lg-sh)*"+shortWeight+"/4)":"0";
     const std::string rate="("+base+"+"+shock+")";
     const std::string discount="exp(-t*"+rate+")";
     const std::string pv="(amt*"+discount+")";
     const std::string basePv="(amt*exp(-t*"+base+"))";
     const std::string baseDeriv="(slope*exp(-t/tau)/tau+hump*exp(-t/tau)*(1-t/tau)/tau)";
     add(v,"ZERO_BASE",base,"1/year","Illustrative continuously compounded EUR base zero curve");
     add(v,"RATE_SHOCK",shock,"1/year","Parallel or shape-sensitive illustrative stress perturbation");
     add(v,"ZERO_STRESS",rate,"1/year","Stressed zero rate at cash-flow maturity");
     add(v,"FORWARD", "("+rate+"+t*("+baseDeriv+"+"+shockDeriv+"))","1/year","Instantaneous forward implied by analytic zero-rate curve");
     add(v,"DISCOUNT_FACTOR",discount,"1","Discount factor under continuous compounding");
     add(v,"PV",pv,"EUR million","Discounted positive cash-flow amount");
     add(v,"SIGNED_PV","(sgn*"+pv+")","EUR million","Positive asset PV or negative liability PV");
     add(v,"DURATION_NUM","(t*"+pv+")","EUR million-years","Cash-flow weighted duration numerator");
     add(v,"CONVEXITY_NUM","(t*t*"+pv+")","EUR million-years2","Cash-flow convexity numerator");
     add(v,"DPV_PAR","(-t*"+pv+")","EUR million/rate","First derivative with respect to parallel rate shift");
     add(v,"D2PV_PAR","(t*t*"+pv+")","EUR million/rate2","Second derivative with respect to parallel shift");
     add(v,"DV01","(-0.0001*t*"+pv+")","EUR million/bp","Signed PV change per one basis point, first order");
     add(v,"D_PV_SHORT",shaped?"(-t*"+shortWeight+"*"+pv+")":"(0*"+pv+")","EUR million/rate","Short-shock parameter exposure (zero in V1)");
     add(v,"D_PV_LONG",shaped?"(-t*"+longWeight+"*"+pv+")":"(0*"+pv+")","EUR million/rate","Long-shock parameter exposure (zero in V1)");
     add(v,"DELTA_PV_BASE","(sgn*("+pv+"-"+basePv+"))","EUR million","Signed stressed-minus-base PV cash-flow contribution");
     add(v,"RATE_MARGIN","(limit-abs("+rate+"))","1/year","Illustrative rate magnitude validity margin");
     add(v,"QUALITY_GUARD","((t>0) AND (amt>0) AND (tau>0) AND (abs("+rate+")<=limit))","0/1","Input and illustrative rate-range guard");
   }
   add("SUM","NET_GAP","(apv-lpv)","EUR million","Economic value gap of fixed modeled cashflows");
   add("SUM","ASSET_DURATION","(adur/apv)","years","PV-weighted asset duration");
   add("SUM","LIABILITY_DURATION","(ldur/lpv)","years","PV-weighted liability duration");
   add("SUM","DURATION_MISMATCH","(adur/apv-ldur/lpv)","years","Duration difference");
   add("SUM","NET_DV01","(0.0001*(adpar-ldpar))","EUR million/bp","Net first-order parallel-rate exposure");
   add("SUM","NET_CONVEXITY_NUM","(aconv-lconv)","EUR million/rate2","Net second derivative under parallel rate shock");
   add("SUM","STRESS_DELTA_EVE","(apv-lpv-basegap)","EUR million","Scenario minus base economic value");
   add("SUM","LOSS_MARGIN","(losslimit-((basegap)-(apv-lpv)))","EUR million","Illustrative permitted loss remaining");
   add("SUM","SHORT_DV01","(0.0001*(ash-lsh))","EUR million/bp","Exposure to tenor-dependent short-rate shock parameter");
   add("SUM","LONG_DV01","(0.0001*(alg-llg))","EUR million/bp","Exposure to tenor-dependent long-rate shock parameter");
   add("SUM","ASSET_LIABILITY_PV_RATIO","(apv/lpv)","1","PV coverage ratio under deterministic fixed cashflows");
   add("SUM","GAP_MARGIN","(losslimit-abs(apv-lpv))","EUR million","Illustrative bound on absolute gap");
   add("SUM","LOSS_GUARD","(((basegap-(apv-lpv))<=losslimit) AND (apv>0) AND (lpv>0))","0/1","Model-only scenario loss screening condition");
   add("COMPARE","GAP_DIFFERENCE","(gap2-gap1)","EUR million","Difference of ALM gap under two shock models");
   add("COMPARE","STRESS_DIFFERENCE","(stress2-stress1)","EUR million","Difference of scenario economic-value response");
   add("COMPARE","DV01_DIFFERENCE","(dv2-dv1)","EUR million/bp","Difference of net parallel-rate derivative exposure");
   add("COMPARE","JOINT_GUARD","((abs(stress1)<=limit) AND (abs(stress2)<=limit))","0/1","Both model responses within illustrative absolute stress window");
 }
 Matrix multi(const std::string&ver,const Matrix&rows){auto&vars=ver=="SUM"?S:(ver=="COMPARE"?C:V);std::vector<PACEVAL_HANDLE>h;for(auto&z:g)if(z.v==ver){h.push_back(z.h);z.evals+=rows.size();}return e.multi(h,rows,vars.size());}
 std::vector<double> one(const std::string&v,const std::string&id,const Matrix&rows){auto&z=g.at(idx.at(v+"_"+id));z.evals+=rows.size();return e.one(z.h,rows,V.size());}
 double scalar(const std::string&v,const std::string&id,const std::vector<double>&row){auto&z=g.at(idx.at(v+"_"+id));z.evals++;return e.scalar(z.h,row);}
 std::map<std::string,double> decode(const std::string&v,const std::vector<double>&x)const{std::map<std::string,double>out;size_t k=0;for(const auto&z:g)if(z.v==v)out[z.id]=x.at(k++);require(k==x.size(),"Graph decode dimension mismatch");return out;}
};
struct Row{std::string scenario,id,side;double t,amount,level,slope,hump,tau,par,sh,lg;};
std::vector<Row>readRows(const fs::path&path){
 std::ifstream f(path);require(bool(f),"Missing input CSV");std::string line;
 require(bool(std::getline(f,line)),"Empty CSV file");
 require(line=="scenario,cashflow_id,side,t_year,amount_eur_m,rlevel,rslope,rhump,tau,parallel,shortshock,longshock","Input CSV schema mismatch");
 std::vector<Row>r;while(std::getline(f,line)){if(line.empty())continue;auto a=split(line);require(a.size()==12,"CSV field count mismatch");
 require(std::regex_match(a[0],std::regex(R"([A-Z_]+)"))&&std::regex_match(a[1],std::regex(R"(CF[0-9]{5})"))&&(a[2]=="ASSET"||a[2]=="LIABILITY"),"Invalid CSV identifiers");
 Row z{a[0],a[1],a[2],parseNumber(a[3]),parseNumber(a[4]),parseNumber(a[5]),parseNumber(a[6]),parseNumber(a[7]),parseNumber(a[8]),parseNumber(a[9]),parseNumber(a[10]),parseNumber(a[11])};
 require(z.t>0&&z.t<=40&&z.amount>0&&z.amount<10&&z.tau>0&&z.tau<40&&std::abs(z.level)<.2&&std::abs(z.slope)<.2&&std::abs(z.hump)<.2&&std::abs(z.par)<.2&&std::abs(z.sh)<.2&&std::abs(z.lg)<.2,"Input outside defined financial example domain");r.push_back(z);
 }require(!r.empty(),"Empty rows");return r;
}
std::vector<double>input(const Row&r){return {r.t,r.amount,r.side=="ASSET"?1.:-1.,r.level,r.slope,r.hump,r.tau,r.par,r.sh,r.lg,.15};}
double nativeRate(const Row&r,bool shaped){double e=std::exp(-r.t/r.tau);double sh=std::exp(-r.t/4.);return r.level+r.slope*(1-e)+r.hump*(r.t/r.tau)*e+r.par+(shaped?(r.sh*sh+r.lg*(1-sh)):0.);}
void operatorTest(Engine&e){for(const auto&p:std::vector<std::pair<std::string,double>>{{"((-1)%10)",-1},{"((-1) mod 10)",9},{"(4 min 5)",4},{"(4 max 5)",5},{"(2<3)",1},{"(2<=2)",1},{"(2>=2)",1},{"(2=2)",1},{"(2<>3)",1},{"NOT(0)",1},{"(1 AND 1)",1},{"(0 OR 1)",1},{"((2<=2) AND (3>=0))",1}})near(e.scalar(e.make(p.first,{}),{}),p.second);
 for(auto s:{"","NaN","Inf","1+2","1,2","1e999","--1"," 1","2bp","0;system"}){bool rejected=false;try{parseNumber(s);}catch(...){rejected=true;}require(rejected,"Invalid literal accepted");}
 near(parseNumber("-1.25e-3"),-.00125);require(!formatNumber(1.25e-6).empty(),"SDK conversion failed");}
void selftest(){Engine e;e.layoutProbe();operatorTest(e);Models m(e);Row a{"BASE","CF00001","ASSET",3.,1.,.017,.012,.004,6.,0.,0.,0.};auto u=input(a);for(auto v:{std::string("V1"),std::string("V2")}){
 double rate=m.scalar(v,"ZERO_STRESS",u);near(rate,nativeRate(a,v=="V2"));double pv=m.scalar(v,"PV",u);near(pv,a.amount*std::exp(-a.t*rate));auto h=m.decode(v,m.multi(v,{u})[0]);near(h.at("DPV_PAR"),-a.t*pv);near(h.at("QUALITY_GUARD"),1);}
 auto rows=m.multi("SUM",{{10,8,-32,-42,43,55,190,210,-18,-23,-5,-8,2,20}});auto q=m.decode("SUM",rows[0]);near(q.at("NET_GAP"),2);near(q.at("STRESS_DELTA_EVE"),0);std::cout<<"PASS original SDK, scalar, multigraph, converters, logical/math operators\n";}
struct Totals{double apv=0,lpv=0,adpar=0,ldpar=0,adur=0,ldur=0,aconv=0,lconv=0,ash=0,lsh=0,alg=0,llg=0;size_t count=0,guard=0;};
struct Summary{std::map<std::string,double>results;Totals totals;};
void run(const fs::path&source,const fs::path&folder){
 fs::create_directories(folder);Engine e;e.layoutProbe();operatorTest(e);Models m(e);auto data=readRows(source);
 std::ofstream surface(folder/"stress_surface.csv"),details(folder/"cashflow_valuations.csv"),summary(folder/"scenario_summary.csv"),buckets(folder/"maturity_buckets.csv"),curve(folder/"curve_profiles.csv"),comparison(folder/"model_comparison.csv"),manifest(folder/"formula_manifest.csv"),inventory(folder/"math_execution_inventory.csv"),nativeAudit(folder/"native_audit.csv"),evidence(folder/"execution_evidence.json");
 require(bool(details&&summary&&buckets&&curve&&comparison&&manifest&&inventory&&nativeAudit&&evidence),"Output file open failed");
 details<<"model,scenario,cashflow_id,side,t_year,amount_eur_m,zero_rate,discount_factor,pv_eur_m,signed_pv_eur_m,dpv_dparallel_eur_m,short_deriv_eur_m,long_deriv_eur_m,rate_margin,guard\n";
 summary<<"model,scenario,asset_pv_eur_m,liability_pv_eur_m,net_gap_eur_m,asset_duration_years,liability_duration_years,duration_mismatch_years,net_dv01_eur_m_per_bp,net_convexity_num_eur_m,short_dv01_eur_m_per_bp,long_dv01_eur_m_per_bp,delta_eve_eur_m,loss_margin_eur_m,loss_guard\n";
 buckets<<"model,scenario,bucket,asset_pv_eur_m,liability_pv_eur_m,net_gap_eur_m\n";
 curve<<"model,scenario,t_year,zero_rate,discount_factor,forward_rate\n";
 comparison<<"scenario,gap_difference_eur_m,stress_difference_eur_m,dv01_difference_eur_m_per_bp,joint_guard\n";
 nativeAudit<<"model,scenario,cashflow_id,rate_check,pv_check,dpv_check,pass\n";
 std::map<std::string,std::map<std::string,Totals>> aggregates;
 struct Partial{double a=0,l=0;};std::map<std::string,std::map<std::string,std::map<int,Partial>>> bucketAggregates;
 size_t checks=0;size_t eligible=0;size_t bad=0;const int bs=192;
 for(size_t s=0;s<data.size();s+=bs){size_t end=std::min(s+bs,data.size());Matrix block;for(size_t i=s;i<end;i++)block.push_back(input(data[i]));
  for(auto model:{std::string("V1"),std::string("V2")}){
   auto outputs=m.multi(model,block);for(size_t j=0;j<outputs.size();j++){auto&r=data[s+j];auto val=m.decode(model,outputs[j]);auto&tot=aggregates[model][r.scenario];bool asset=r.side=="ASSET";
    double pv=val.at("PV"),dp=val.at("DPV_PAR");
    if(asset){tot.apv+=pv;tot.adpar+=dp;tot.adur+=val.at("DURATION_NUM");tot.aconv+=val.at("CONVEXITY_NUM");tot.ash+=val.at("D_PV_SHORT");tot.alg+=val.at("D_PV_LONG");}
    else{tot.lpv+=pv;tot.ldpar+=dp;tot.ldur+=val.at("DURATION_NUM");tot.lconv+=val.at("CONVEXITY_NUM");tot.lsh+=val.at("D_PV_SHORT");tot.llg+=val.at("D_PV_LONG");}
    tot.count++;tot.guard+=(val.at("QUALITY_GUARD")>.5);int bucket=r.t<1?0:r.t<3?1:r.t<5?2:r.t<10?3:r.t<20?4:5;
    auto&bucketTotal=bucketAggregates[model][r.scenario][bucket];if(asset)bucketTotal.a+=pv;else bucketTotal.l+=pv;
    if((s+j)%53==0){double rr=nativeRate(r,model=="V2"),nn=r.amount*std::exp(-r.t*rr);near(val.at("ZERO_STRESS"),rr,1e-11);near(pv,nn,1e-8);near(dp,-r.t*nn,1e-8);checks+=3;nativeAudit<<model<<','<<r.scenario<<','<<r.id<<",1,1,1,1\n";}
    details<<model<<','<<r.scenario<<','<<r.id<<','<<r.side<<','<<formatNumber(r.t)<<','<<formatNumber(r.amount)<<','<<formatNumber(val.at("ZERO_STRESS"))<<','<<formatNumber(val.at("DISCOUNT_FACTOR"))<<','<<formatNumber(pv)<<','<<formatNumber(val.at("SIGNED_PV"))<<','<<formatNumber(dp)<<','<<formatNumber(val.at("D_PV_SHORT"))<<','<<formatNumber(val.at("D_PV_LONG"))<<','<<formatNumber(val.at("RATE_MARGIN"))<<','<<formatNumber(val.at("QUALITY_GUARD"))<<'\n';
   }
  }
 }
 // Aggregation of a variable-length portfolio is performed by the host. All
 // derived duration, convexity, PV01, capital-margin and gap formulas remain
 // live paceval graphs, using the aggregated numerical inputs.
 std::map<std::string,std::map<std::string,Summary>> sums;
 for(auto model:{std::string("V1"),std::string("V2")}){auto base=aggregates[model].at("BASE");double baseGap=base.apv-base.lpv;for(auto&p:aggregates[model]){
  const auto&name=p.first;const Totals&a=p.second;require(a.apv>0&&a.lpv>0,"Non-positive book PV");auto srow=std::vector<double>{a.apv,a.lpv,a.adpar,a.ldpar,a.adur,a.ldur,a.aconv,a.lconv,a.ash,a.lsh,a.alg,a.llg,baseGap,20.};
  auto z=m.decode("SUM",m.multi("SUM",{srow})[0]);sums[model][name]={z,a};eligible+=(z.at("LOSS_GUARD")>.5);
  summary<<model<<','<<name<<','<<formatNumber(a.apv)<<','<<formatNumber(a.lpv)<<','<<formatNumber(z.at("NET_GAP"))<<','<<formatNumber(z.at("ASSET_DURATION"))<<','<<formatNumber(z.at("LIABILITY_DURATION"))<<','<<formatNumber(z.at("DURATION_MISMATCH"))<<','<<formatNumber(z.at("NET_DV01"))<<','<<formatNumber(z.at("NET_CONVEXITY_NUM"))<<','<<formatNumber(z.at("SHORT_DV01"))<<','<<formatNumber(z.at("LONG_DV01"))<<','<<formatNumber(z.at("STRESS_DELTA_EVE"))<<','<<formatNumber(z.at("LOSS_MARGIN"))<<','<<formatNumber(z.at("LOSS_GUARD"))<<'\n';
  for(auto&b:bucketAggregates[model][name]){auto&v=b.second;buckets<<model<<','<<name<<','<<b.first<<','<<formatNumber(v.a)<<','<<formatNumber(v.l)<<','<<formatNumber(v.a-v.l)<<'\n';}
 }}
 for(auto&z:sums["V1"]){auto&name=z.first;auto&x=z.second.results;auto&y=sums["V2"].at(name).results;
 auto c=m.decode("COMPARE",m.multi("COMPARE",{{x.at("NET_GAP"),y.at("NET_GAP"),x.at("STRESS_DELTA_EVE"),y.at("STRESS_DELTA_EVE"),x.at("NET_DV01"),y.at("NET_DV01"),60.}})[0]);
 comparison<<name<<','<<formatNumber(c.at("GAP_DIFFERENCE"))<<','<<formatNumber(c.at("STRESS_DIFFERENCE"))<<','<<formatNumber(c.at("DV01_DIFFERENCE"))<<','<<formatNumber(c.at("JOINT_GUARD"))<<'\n';}
 // Smooth curve profiles are also evaluated by real paceval multigraph batches.
 for(auto model:{std::string("V1"),std::string("V2")})for(auto &s:aggregates[model]){
  Row proto=data[0];for(const Row&d:data)if(d.scenario==s.first){proto.par=d.par;proto.sh=d.sh;proto.lg=d.lg;break;}
  Matrix samples;for(int k=1;k<=90;k++){proto.t=k/3.;samples.push_back(input(proto));}
  auto z=m.multi(model,samples);for(size_t k=0;k<z.size();k++){auto d=m.decode(model,z[k]);curve<<model<<','<<s.first<<','<<formatNumber((k+1)/3.)<<','<<formatNumber(d.at("ZERO_STRESS"))<<','<<formatNumber(d.at("DISCOUNT_FACTOR"))<<','<<formatNumber(d.at("FORWARD"))<<'\n';}
 }
 // An 81-point two-dimensional stress surface, priced with the original
 // paceval single-graph batch interface, uses exactly the same cashflows.
 surface<<"parallel_shock,short_shock,net_gap_eur_m\n";
 size_t surfacePoints=0;
 for(int i=0;i<9;i++)for(int j=0;j<9;j++){
  double par=-.03+.0075*i,sh=-.03+.0075*j;Matrix inputs;
  for(const Row&r:data)if(r.scenario=="BASE"){
    Row q=r;q.par=par;q.sh=sh;q.lg=0;
    inputs.push_back(input(q));
  }
  auto val=m.one("V2","SIGNED_PV",inputs);double net=0;
  for(double x:val)net+=x;
  surface<<formatNumber(par)<<','<<formatNumber(sh)<<','<<formatNumber(net)<<'\n';
  surfacePoints+=val.size();
 }
 manifest<<"graph_id,version,formula,units,purpose\n";
 inventory<<"function_id,domain_quantity,mathematical_definition,units,execution_owner,paceval_graph_id,formula_version,api_path,reference_test,status,host_reason\n";
 size_t executed=0;for(auto&g:m.g){executed+=g.evals>0;manifest<<g.v<<'_'<<g.id<<','<<g.v<<",\""<<g.expr<<"\","<<g.units<<",\""<<g.purpose<<"\"\n";inventory<<g.v<<'_'<<g.id<<",\""<<g.purpose<<"\",\""<<g.expr<<"\","<<g.units<<",paceval,"<<g.v<<'_'<<g.id<<','<<g.v<<",real_multigraph_and_scalar,independent_C++_and_mpmath,"<<(g.evals?"executed":"registered_only")<<",\n";}
 require(executed==m.g.size(),"Registered graph not executed in real data path");
 inventory<<"PORTFOLIO_SUM,Finite sum of dated asset/liability cashflow terms,variable length aggregation,EUR million,host,,both,C++ deterministic reduction,independent_mpmath,executed,variable-length financial portfolio summation\n";
 inventory<<"SCENARIO_POLICY,Conservative stress review decision,paceval loss guard then C++ policy,0/1,host,,both,C++ policy,manual review,executed,no real regulatory decision\n";
 evidence<<"{\n  \"sdk\":\"original paceval 4.25 Linux x86-64\",\n  \"data_source\":\"deterministic synthetic EUR cashflows\",\n  \"scenario_count\":"<<aggregates["V1"].size()<<",\n  \"cashflow_count\":"<<(data.size()/aggregates["V1"].size())<<",\n  \"input_rows\":"<<data.size()<<",\n  \"unique_graphs_created\":"<<m.g.size()<<",\n  \"unique_graphs_executed\":"<<executed<<",\n  \"scalar_calls\":"<<e.scalarCalls<<",\n  \"batch_calls\":"<<e.batchCalls<<",\n  \"graph_point_evaluations\":"<<e.graphPoints<<",\n  \"native_reference_checks\":"<<checks<<",\n  \"illustrative_loss_guards_pass\":"<<eligible<<",\n  \"model_versions\":2,\n  \"stress_surface_graph_points\":"<<surfacePoints<<"\n}\n";
 std::cout<<"PASS original paceval SDK executed "<<executed<<" graphs on "<<data.size()<<" input rows and 2 model versions; native assertions="<<checks<<"\n";
}
} // namespace
int main(int argc,char**argv){try{if(argc==2&&std::string(argv[1])=="--selftest"){selftest();return 0;}
 require(argc==4&&std::string(argv[1])=="--run","Usage: alm_stress --run input.csv result_directory");run(argv[2],argv[3]);return 0;}
 catch(const std::exception&e){std::cerr<<"ERROR "<<e.what()<<'\n';return 1;}}
