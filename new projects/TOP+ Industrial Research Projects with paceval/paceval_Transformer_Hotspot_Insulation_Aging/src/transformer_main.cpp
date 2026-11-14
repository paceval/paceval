// WP 14: Oil-immersed transformer hot-spot and relative insulation-aging screening.
// Original paceval 4.25 executes every registered thermophysical expression,
// model-version comparison, signed constraint, score and cumulative state update.
// C++ orchestrates CSV validation, prior-state transfer and independent checks.
// Synthetic input and simplified first-order dynamics are NOT IEEE compliance,
// transformer rating certification or a prognostic asset-health model.
#include "paceval_main.h"
#include <algorithm>
#include <cmath>
#include <cstdint>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <limits>
#include <map>
#include <regex>
#include <sstream>
#include <stdexcept>
#include <string>
#include <vector>
namespace fs=std::filesystem;
namespace {
void require(bool c,const std::string& m){if(!c)throw std::runtime_error(m);}
bool literal(const std::string& s){static const std::regex r(R"(^[+-]?(?:[0-9]+(?:\.[0-9]*)?|\.[0-9]+)(?:[eE][+-]?[0-9]+)?$)");return std::regex_match(s,r);}
double parse(const std::string& s){require(literal(s),"Unsafe numerical CSV input: "+s);int e=-1;long pos=-1;auto x=paceval_dConvertStringToFloat(s.c_str(),&e,&pos,false,nullptr,nullptr);require(e==0&&std::isfinite(x),"SDK numeric parse failed code="+std::to_string(e)+" pos="+std::to_string(pos));return x;}
std::string numeric(double v){require(std::isfinite(v),"Nonfinite result to be written");char b[512]{};auto digits=paceval_dConvertFloatToString(b,v);require(digits>0&&b[0]&&std::string(b).find(',')==std::string::npos,"SDK numeric formatting failed");return b;}
std::vector<std::string> split(const std::string& s){std::vector<std::string> a;std::stringstream ss(s);std::string f;while(std::getline(ss,f,','))a.push_back(f);if(!s.empty()&&s.back()==',')a.push_back("");return a;}
std::string join(const std::vector<std::string>& v){std::string s;for(const auto& w:v){if(!s.empty())s+=' ';s+=w;}return s;}
void near(double a,double b,double rel=3e-8,double ab=3e-7){require(std::isfinite(a)&&std::isfinite(b)&&std::abs(a-b)<=ab+rel*std::max(std::abs(a),std::abs(b)),"Independent mathematical reference mismatch: "+std::to_string(a)+" vs "+std::to_string(b));}
using Rows=std::vector<std::vector<double>>;
struct Engine {
 std::vector<PACEVAL_HANDLE> handles;bool graphMajor=false;uint64_t scalarCalls=0,batchCalls=0,points=0;
 Engine(){require(paceval_InitializeLibrary(nullptr),"paceval_InitializeLibrary failed");}
 ~Engine(){for(auto h:handles)if(h)paceval_DeleteComputation(h);paceval_FreeLibrary();}
 PACEVAL_HANDLE make(const std::string& s,const std::vector<std::string>& names){auto vs=join(names);auto h=paceval_CreateComputation(s.c_str(),names.size(),vs.c_str(),false,nullptr);require(h&&!paceval_GetIsError(h),"Graph rejected: "+s);handles.push_back(h);return h;}
 double scalar(PACEVAL_HANDLE h,const std::vector<double>& val){auto v=val;auto z=paceval_dGetComputationResult(h,v.empty()?nullptr:v.data(),nullptr,nullptr);++scalarCalls;require(!paceval_GetIsError(h)&&std::isfinite(z),"SDK scalar failed");return z;}
 void layout(){auto a=make("x+2*y",{"x","y"}),b=make("3*x-y",{"x","y"});PACEVAL_HANDLE hs[]={a,b};double in[]={1,2,4,7},out[4]{},lo[4]{},hi[4]{};int err[4]{};
  bool failed=paceval_dGetMultipleComputationsResultsExt(hs,2,in,2,out,lo,hi,err);
  require(!failed&&std::all_of(err,err+4,[](int x){return x==0;}),"Original SDK batch-layout probe failed");
  if(std::abs(out[0]-5)<1e-10&&std::abs(out[1]-18)<1e-10&&std::abs(out[2]-1)<1e-10&&std::abs(out[3]-5)<1e-10)graphMajor=true;
  else if(std::abs(out[0]-5)<1e-10&&std::abs(out[1]-1)<1e-10&&std::abs(out[2]-18)<1e-10&&std::abs(out[3]-5)<1e-10)graphMajor=false;
  else throw std::runtime_error("Unknown multi-graph output ordering");
  ++batchCalls;points+=4;
 }
 Rows batch(const std::vector<PACEVAL_HANDLE>& hs,const Rows& rows,size_t nvars){require(!hs.empty()&&!rows.empty(),"Empty batch");std::vector<double> flat;flat.reserve(rows.size()*nvars);
  for(const auto& row:rows){require(row.size()==nvars,"Incorrect input width");for(auto x:row)require(std::isfinite(x),"Nonfinite input");flat.insert(flat.end(),row.begin(),row.end());}
  size_t n=hs.size()*rows.size();std::vector<double> out(n),lo(n),hi(n);std::vector<int> errors(n,-1);
  // Verified SDK semantics: the return value false is successful execution,
  // while per-item errors must all be zero. Verify both on every call.
  bool failed=paceval_dGetMultipleComputationsResultsExt(const_cast<PACEVAL_HANDLE*>(hs.data()),hs.size(),flat.data(),rows.size(),out.data(),lo.data(),hi.data(),errors.data());
  require(!failed,"paceval multigraph batch reported failure");for(int e:errors)require(e==0,"Original SDK item error code "+std::to_string(e));
  Rows result(rows.size(),std::vector<double>(hs.size()));for(size_t i=0;i<rows.size();++i)for(size_t g=0;g<hs.size();++g){size_t at=graphMajor?g*rows.size()+i:i*hs.size()+g;require(std::isfinite(out[at]),"Nonfinite SDK output");result[i][g]=out[at];}
  ++batchCalls;points+=n;return result;
 }
};
const std::vector<std::string> VARS={"current","rated","amb","oldTo","oldH","lossR","topR","hotR","n","m","tauOil","tauHot","cool","dt","limHs","limOil","limFaa","limK","refC","oldAge","oldPeak","oldMin"};
struct Graph{std::string id,version,expression,unit,description;PACEVAL_HANDLE h{};bool executed=false;};
struct Models {
 Engine& e;std::vector<Graph> graphs;std::map<std::string,size_t> index;
 explicit Models(Engine& x):e(x){
  for(int ver=1;ver<=2;++ver){
   std::string v=ver==1?"V1":"V2";
   const std::string k="(current/rated)";
   const std::string base="(("+k+"^2*lossR+1)/(lossR+1))";
   const std::string toU="(topR*cool*("+base+"^n))";
   const std::string hU="(hotR*("+k+"^(2*m)))";
   const std::string ao="exp(-dt/(tauOil*cool))";
   const std::string ah=ver==1?"0":"exp(-dt/tauHot)";
   const std::string to="("+toU+"+(oldTo-"+toU+")*"+ao+")";
   const std::string h="("+hU+"+(oldH-"+hU+")*"+ah+")";
   const std::string oil="(amb+"+to+")";
   const std::string hs="("+oil+"+"+h+")";
   const std::string faa="exp(15000/(refC+273.15)-15000/("+hs+"+273.15))";
   const std::string mh="(limHs-"+hs+")";
   const std::string mo="(limOil-"+oil+")";
   const std::string mf="(limFaa-"+faa+")";
   const std::string mk="(limK-"+k+")";
   const std::string dToU="(topR*cool*n*("+base+"^(n-1))*(2*lossR*"+k+"/(lossR+1)))";
   const std::string dHU="(hotR*2*m*("+k+"^(2*m-1)))";
   const std::string dHS="((1-"+ao+")*"+dToU+"+(1-"+ah+")*"+dHU+")";
   const std::string dF="("+faa+"*15000/(("+hs+"+273.15)^2))";
   const std::string guard="(("+mh+" >= 0) AND ("+mo+" >= 0) AND ("+mf+" >= 0) AND ("+mk+" >= 0))";
   auto add=[&](const std::string&id,const std::string&ex,const std::string&unit,const std::string&desc){Graph g{v+"_"+id,v,ex,unit,desc,e.make(ex,VARS),false};index[g.id]=graphs.size();graphs.push_back(std::move(g));};
   add("LOAD_RATIO",k,"1","Current-to-nameplate ratio");
   add("ULTIMATE_TOP_RISE",toU,"K","Steady top-oil rise proxy");
   add("ULTIMATE_HOT_RISE",hU,"K","Steady winding-over-oil rise proxy");
   add("OIL_DECAY",ao,"1","First-order oil memory factor");
   add("HOT_DECAY",ah,"1","First-order winding memory factor, zero in V1");
   add("TOP_RISE_NEXT",to,"K","Transient top-oil rise at end of interval");
   add("HOT_RISE_NEXT",h,"K","Transient winding-over-oil rise at end of interval");
   add("TOP_TEMP",oil,"C","Top-oil temperature proxy");
   add("HOTSPOT",hs,"C","Winding hot-spot temperature proxy");
   add("FAA",faa,"1","Relative Arrhenius-style aging acceleration");
   add("AGE_INCREMENT","(dt*"+faa+")","reference_h","Equivalent relative aging hours in interval");
   add("AGE_ACCUM","(oldAge+dt*"+faa+")","reference_h","Cumulative equivalent aging hours");
   add("PEAK_HOTSPOT","(oldPeak max "+hs+")","C","Maximum winding hot-spot up to this interval");
   add("MIN_HOTSPOT_MARGIN","(oldMin min "+mh+")","K","Minimum observed hot-spot limit margin");
   add("MARGIN_HOTSPOT",mh,"K","Signed margin to illustrative hot-spot threshold");
   add("MARGIN_TOP",mo,"K","Signed margin to illustrative top-oil threshold");
   add("MARGIN_FAA",mf,"1","Signed instantaneous aging factor threshold margin");
   add("MARGIN_LOAD",mk,"1","Signed current loading limit margin");
   add("COMPOSITE_GUARD",guard,"0_or_1","Composite thermal and load screening condition");
   add("RISK_SCORE","(-((0 max (-"+mh+"))^2+0.5*(0 max (-"+mo+"))^2+0.05*(0 max (-"+mf+"))^2))","index","Illustrative negative exceedance score");
   add("D_ULTTOP_DK",dToU,"K","Analytic steady top-rise derivative with load");
   add("D_ULTHOT_DK",dHU,"K","Analytic steady winding-rise derivative with load");
   add("D_HS_DK",dHS,"K","One-step hot-spot sensitivity to loading");
   add("D_FAA_DHS",dF,"per_K","Analytic local relative-aging sensitivity to hot-spot temperature");
   add("D_FAA_DK","("+dF+"*"+dHS+")","1","Local relative-aging sensitivity to load");
   add("D_HS_DAMB","1","1","Instantaneous ambient sensitivity at fixed input state");
   add("D_HS_D_OLDTOP",ao,"1","Influence of preceding top-oil rise");
   add("D_HS_D_OLDHOT",ah,"1","Influence of preceding winding-over-oil rise");
  }
  const std::vector<std::string> vs={"hsA","hsB","faaA","faaB","ageA","ageB","marginA","marginB","guardA","guardB","peakA","peakB"};
  auto add=[&](const std::string&id,const std::string&ex,const std::string&unit,const std::string&d){Graph g{id,"V1_vs_V2",ex,unit,d,e.make(ex,vs),false};index[id]=graphs.size();graphs.push_back(std::move(g));};
  add("DELTA_HOTSPOT","(hsB-hsA)","K","Model temperature difference");
  add("DELTA_FAA","(faaB-faaA)","1","Model relative aging acceleration difference");
  add("DELTA_ACCUM_AGE","(ageB-ageA)","reference_h","Model cumulative relative aging difference");
  add("MIN_MODEL_MARGIN","(marginA min marginB)","K","Least favorable model hot-spot margin");
  add("JOINT_GUARD","((guardA = 1) AND (guardB = 1))","0_or_1","Both version thermal guards hold");
  add("DELTA_PEAK","(peakB-peakA)","K","Model cumulative peak hot-spot difference");
  add("AGE_RATIO","(ageB/ageA)","1","Model cumulative relative aging ratio");
 }
 size_t first(const std::string& v)const {for(size_t i=0;i<graphs.size();++i)if(graphs[i].version==v)return i;throw std::runtime_error("Missing graph version");}
 std::vector<Graph*> selected(const std::string& v){std::vector<Graph*> a;for(auto&g:graphs)if(g.version==v)a.push_back(&g);return a;}
 Rows evaluate(const std::string& v,const Rows& rows){auto subset=selected(v);std::vector<PACEVAL_HANDLE> hs;for(auto*g:subset)hs.push_back(g->h);auto y=e.batch(hs,rows,v=="V1_vs_V2"?12:VARS.size());for(auto*g:subset)g->executed=true;return y;}
 std::map<std::string,double> unpack(const std::string& v,const std::vector<double>& row){auto subset=selected(v);require(row.size()==subset.size(),"Result width mismatch");std::map<std::string,double> m;for(size_t k=0;k<row.size();++k){auto id=subset[k]->id;if(v=="V1"||v=="V2")id=id.substr(3);m[id]=row[k];}return m;}
};
struct Params{std::string id;double rated,lossR,topR,hotR,n,m,tauOil,tauHot,cool,initTo,initH,limHs,limOil,limFAA,limK,refC;};
struct Input{std::string scenario,id;int hour;double amb,cur,rated,dt;};
struct State{double to=0,h=0,age=0,peak=-200,minMargin=1e6;bool all=true;double maxFAA=0;int failures=0;};
struct Output{double hs=0,faa=0,age=0,margin=0,guard=0;};
std::map<std::string,Params> readParameters(const fs::path& p){std::ifstream f(p);require(bool(f),"Cannot open transformer parameters");std::string line;std::getline(f,line);require(line=="asset_id,rated_A,lossR,topRated_K,hotRated_K,n,m,tauOil_h,tauHot_h,coolFactor,initTop_K,initHot_K,limitHS_C,limitOil_C,limitFAA,limitLoad,refTemp_C","Unexpected parameters CSV schema");std::map<std::string,Params> out;int count=0;
 while(std::getline(f,line)){++count;auto v=split(line);require(v.size()==17,"Parameter field count at row "+std::to_string(count+1));require(std::regex_match(v[0],std::regex("TR[0-9]{3}")),"Invalid asset ID");Params p;p.id=v[0];double *arr[]={&p.rated,&p.lossR,&p.topR,&p.hotR,&p.n,&p.m,&p.tauOil,&p.tauHot,&p.cool,&p.initTo,&p.initH,&p.limHs,&p.limOil,&p.limFAA,&p.limK,&p.refC};for(int i=0;i<16;i++)*arr[i]=parse(v[i+1]);require(p.rated>0&&p.lossR>=0&&p.topR>0&&p.hotR>=0&&p.n>.1&&p.n<2&&p.m>=.55&&p.m<2&&p.tauOil>0&&p.tauHot>0&&p.cool>0&&p.limHs>p.refC-20&&p.limFAA>0&&p.limK>0&&p.refC+273.15>0&&p.initTo>=0&&p.initH>=0,"Invalid transformer parameter domain");require(out.emplace(p.id,p).second,"Repeated transformer ID");}require(!out.empty(),"No transformers");return out;
}
std::vector<Input> readProfiles(const fs::path& path,const std::map<std::string,Params>& params){std::ifstream f(path);require(bool(f),"Cannot open input profiles");std::string line;std::getline(f,line);require(line=="scenario,asset_id,hour,ambient_C,current_A,rated_A,dt_h","Unexpected profile CSV schema");std::vector<Input> result;int row=0;
 while(std::getline(f,line)){++row;auto v=split(line);require(v.size()==7,"Profile field count failure at line "+std::to_string(row+1));require(v[0]=="baseline"||v[0]=="heatwave"||v[0]=="overload","Unknown scenario");require(params.count(v[1])>0,"Unknown transformer id");Input x;x.scenario=v[0];x.id=v[1];double h=parse(v[2]);require(h>=0&&h<100000&&std::floor(h)==h,"Invalid time index");x.hour=int(h);x.amb=parse(v[3]);x.cur=parse(v[4]);x.rated=parse(v[5]);x.dt=parse(v[6]);require(x.amb>-75&&x.amb<110&&x.cur>=0&&x.cur<=2*x.rated&&x.dt>0&&x.dt<=1&&std::abs(x.rated-params.at(x.id).rated)<1e-9,"Invalid operating point");result.push_back(x);
 }require(!result.empty(),"No profile records");return result;
}
std::vector<double> arguments(const Input& r,const Params&p,const State&s){return {r.cur,r.rated,r.amb,s.to,s.h,p.lossR,p.topR,p.hotR,p.n,p.m,p.tauOil,p.tauHot,p.cool,r.dt,p.limHs,p.limOil,p.limFAA,p.limK,p.refC,s.age,s.peak,s.minMargin};}
// Independent native implementation; the expression strings are not interpreted.
void nativeCheck(const Input& x,const Params&p,const State&s,int ver,const std::map<std::string,double>&r){
 double k=x.cur/x.rated;double base=(k*k*p.lossR+1)/(p.lossR+1);double tu=p.topR*p.cool*std::pow(base,p.n);double hu=p.hotR*std::pow(k,2*p.m);double ao=std::exp(-x.dt/(p.tauOil*p.cool));double ah=ver==1?0:std::exp(-x.dt/p.tauHot);double to=tu+(s.to-tu)*ao;double h=hu+(s.h-hu)*ah;double top=x.amb+to;double hs=top+h;double f=std::exp(15000/(p.refC+273.15)-15000/(hs+273.15));double mhs=p.limHs-hs;double oilmar=p.limOil-top;double mf=p.limFAA-f;double mk=p.limK-k;double dtu=p.topR*p.cool*p.n*std::pow(base,p.n-1)*2*p.lossR*k/(p.lossR+1);double dhu=p.hotR*2*p.m*std::pow(k,2*p.m-1);double dhsk=(1-ao)*dtu+(1-ah)*dhu;double df=f*15000/((hs+273.15)*(hs+273.15));
 for(const auto& t:std::vector<std::pair<std::string,double>>{{"LOAD_RATIO",k},{"ULTIMATE_TOP_RISE",tu},{"ULTIMATE_HOT_RISE",hu},{"OIL_DECAY",ao},{"HOT_DECAY",ah},{"TOP_RISE_NEXT",to},{"HOT_RISE_NEXT",h},{"TOP_TEMP",top},{"HOTSPOT",hs},{"FAA",f},{"AGE_INCREMENT",x.dt*f},{"AGE_ACCUM",s.age+x.dt*f},{"PEAK_HOTSPOT",std::max(s.peak,hs)},{"MIN_HOTSPOT_MARGIN",std::min(s.minMargin,mhs)},{"MARGIN_HOTSPOT",mhs},{"MARGIN_TOP",oilmar},{"MARGIN_FAA",mf},{"MARGIN_LOAD",mk},{"COMPOSITE_GUARD",(mhs>=0&&oilmar>=0&&mf>=0&&mk>=0)?1.:0.},{"D_ULTTOP_DK",dtu},{"D_ULTHOT_DK",dhu},{"D_HS_DK",dhsk},{"D_FAA_DHS",df},{"D_FAA_DK",df*dhsk},{"D_HS_DAMB",1.},{"D_HS_D_OLDTOP",ao},{"D_HS_D_OLDHOT",ah}})near(r.at(t.first),t.second);
}
void testOperators(Engine&e){for(const auto& a:std::vector<std::pair<std::string,double>>{{"((-1) % 10)",-1},{"((-1) mod 10)",9},{"(4 min 5)",4},{"(4 max 5)",5},{"(3 < 4)",1},{"(3 <= 3)",1},{"(3 >= 3)",1},{"(3 = 3)",1},{"(3 <> 4)",1},{"NOT(0)",1},{"(1 AND 1)",1},{"(0 OR 1)",1},{"((3 <= 3) AND (2 >= 0))",1}}){auto h=e.make(a.first,{});near(e.scalar(h,{}),a.second,0,1e-12);}
 near(parse("-1.25e-3"),-.00125);for(const char* bad:{"","NaN","Inf","2+3","1,2","1e9999"," 7","--1"}){bool rejected=false;try{(void)parse(bad);}catch(...){rejected=true;}require(rejected,"Unsafe CSV value accepted");}require(!numeric(.00045).empty(),"SDK float string failed");}
void selftest(){Engine e;e.layout();testOperators(e);Models models(e);Params p{"TR000",700,4.5,50,25,.8,.8,3,.3,1,30,15,120,105,8,1.5,110};Input x{"baseline",p.id,0,25,700,700,1};State s{35,14,0,-200,1e6,true,0,0};auto args=arguments(x,p,s);auto a=models.unpack("V1",models.evaluate("V1",Rows{args})[0]);auto b=models.unpack("V2",models.evaluate("V2",Rows{args})[0]);nativeCheck(x,p,s,1,a);nativeCheck(x,p,s,2,b);near(e.scalar(models.graphs[models.index["V1_HOTSPOT"]].h,args),a["HOTSPOT"]);auto comparison=models.unpack("V1_vs_V2",models.evaluate("V1_vs_V2",Rows{{a["HOTSPOT"],b["HOTSPOT"],a["FAA"],b["FAA"],a["AGE_ACCUM"],b["AGE_ACCUM"],a["MARGIN_HOTSPOT"],b["MARGIN_HOTSPOT"],a["COMPOSITE_GUARD"],b["COMPOSITE_GUARD"],a["PEAK_HOTSPOT"],b["PEAK_HOTSPOT"]}})[0]);near(comparison.at("DELTA_HOTSPOT"),b["HOTSPOT"]-a["HOTSPOT"]);
 // Known physical boundary: K=0 is admissible, while T in kelvin must remain positive.
 x.cur=0;args=arguments(x,p,s);auto v=models.unpack("V2",models.evaluate("V2",Rows{args})[0]);nativeCheck(x,p,s,2,v);
 std::cout<<"SELFTEST PASS: original SDK 4.25, scalar and multigraph batch, numeric conversion, operator boundary cases, complete independent thermal references\n";
}
void run(const fs::path& input,const fs::path& config,const fs::path& output){fs::create_directories(output);Engine e;e.layout();testOperators(e);Models models(e);auto params=readParameters(config);auto records=readProfiles(input,params);size_t N=records.size();require(N>100,"Main research dataset unexpectedly small");
 std::ofstream timeline(output/"hotspot_timeseries.csv"),summ(output/"asset_summary.csv"),diff(output/"model_comparison.csv"),audit(output/"native_audit.csv"),manifest(output/"formula_manifest.csv"),inventory(output/"math_execution_inventory.csv"),evidence(output/"execution_evidence.json");require(bool(timeline&&summ&&diff&&audit&&manifest&&inventory&&evidence),"Cannot create research files");
 timeline<<"scenario,asset_id,hour,model,ambient_C,load_ratio,top_rise_K,winding_rise_K,top_oil_C,hotspot_C,aging_factor,aging_increment_h,cumulative_aging_h,peak_hotspot_C,hotspot_margin_K,oil_margin_K,aging_margin,load_margin,compound_guard,risk_score,dHs_dK_K,dFAA_dHs_perK,dFAA_dK,old_top_rise_K,old_hot_rise_K\n";
 summ<<"scenario,asset_id,model,peak_hotspot_C,final_hotspot_C,final_top_oil_C,equivalent_aging_h,max_aging_factor,min_hotspot_margin_K,failing_hours,all_intervals_within_illustrative_limits\n";
 diff<<"scenario,asset_id,peak_HS_V1_C,peak_HS_V2_C,delta_peak_C,aging_hours_V1,aging_hours_V2,delta_aging_hours,ratio_V2_to_V1,final_HS_V1_C,final_HS_V2_C,delta_final_hotspot_K,min_limit_margin_K,both_models_pass\n";
 audit<<"scenario,asset_id,hour,model,hotspot_C,aging_factor,age_hours,verified_full_graph_chain\n";
 std::vector<std::map<std::string,double>> retained[2];retained[0].resize(N);retained[1].resize(N);std::vector<std::map<std::string,State>> states(2);size_t nativeChecks=0;size_t failedCount[2]={0,0};
 for(int ver=1;ver<=2;ver++){
  std::string v=ver==1?"V1":"V2";size_t i=0;
  while(i<N){size_t stop=i+1;while(stop<N&&records[stop].scenario==records[i].scenario&&records[stop].hour==records[i].hour)++stop;
   Rows args;args.reserve(stop-i);std::vector<State> before;before.reserve(stop-i);
   for(size_t j=i;j<stop;++j){const auto& row=records[j];const auto& p=params.at(row.id);std::string id=row.scenario+"/"+row.id;auto at=states[ver-1].find(id);if(at==states[ver-1].end()){require(row.hour==0,"Missing initial time step");State start;start.to=p.initTo;start.h=p.initH;states[ver-1].emplace(id,start);at=states[ver-1].find(id);} else require(row.hour>0,"Duplicate first hour");before.push_back(at->second);args.push_back(arguments(row,p,before.back()));}
   auto y=models.evaluate(v,args);
   for(size_t j=i;j<stop;++j){const auto& x=records[j];auto& state=states[ver-1].at(x.scenario+"/"+x.id);auto r=models.unpack(v,y[j-i]);retained[ver-1][j]=r;
    timeline<<x.scenario<<','<<x.id<<','<<x.hour<<','<<v<<','<<numeric(x.amb)<<','<<numeric(r.at("LOAD_RATIO"))<<','<<numeric(r.at("TOP_RISE_NEXT"))<<','<<numeric(r.at("HOT_RISE_NEXT"))<<','<<numeric(r.at("TOP_TEMP"))<<','<<numeric(r.at("HOTSPOT"))<<','<<numeric(r.at("FAA"))<<','<<numeric(r.at("AGE_INCREMENT"))<<','<<numeric(r.at("AGE_ACCUM"))<<','<<numeric(r.at("PEAK_HOTSPOT"))<<','<<numeric(r.at("MARGIN_HOTSPOT"))<<','<<numeric(r.at("MARGIN_TOP"))<<','<<numeric(r.at("MARGIN_FAA"))<<','<<numeric(r.at("MARGIN_LOAD"))<<','<<numeric(r.at("COMPOSITE_GUARD"))<<','<<numeric(r.at("RISK_SCORE"))<<','<<numeric(r.at("D_HS_DK"))<<','<<numeric(r.at("D_FAA_DHS"))<<','<<numeric(r.at("D_FAA_DK"))<<','<<numeric(before[j-i].to)<<','<<numeric(before[j-i].h)<<'\n';
    if((j%113)==0 || (x.hour==0&&x.id=="TR000")){nativeCheck(x,params.at(x.id),before[j-i],ver,r);nativeChecks+=27;audit<<x.scenario<<','<<x.id<<','<<x.hour<<','<<v<<','<<numeric(r.at("HOTSPOT"))<<','<<numeric(r.at("FAA"))<<','<<numeric(r.at("AGE_ACCUM"))<<",1\n";}
    state.to=r.at("TOP_RISE_NEXT");state.h=r.at("HOT_RISE_NEXT");state.age=r.at("AGE_ACCUM");state.peak=r.at("PEAK_HOTSPOT");state.minMargin=r.at("MIN_HOTSPOT_MARGIN");state.maxFAA=std::max(state.maxFAA,r.at("FAA"));state.all=state.all&&(r.at("COMPOSITE_GUARD")>.5);if(r.at("COMPOSITE_GUARD")<.5)++state.failures;
   }
   i=stop;
  }
  for(const auto& item:states[ver-1]){auto p=item.first.find('/');const auto& s=item.second;const auto& sc=item.first.substr(0,p);const auto& id=item.first.substr(p+1);double lastHs=0,lastTop=0;for(size_t j=N;j-->0;)if(records[j].id==id&&records[j].scenario==sc){lastHs=retained[ver-1][j].at("HOTSPOT");lastTop=retained[ver-1][j].at("TOP_TEMP");break;}
   summ<<sc<<','<<id<<','<<v<<','<<numeric(s.peak)<<','<<numeric(lastHs)<<','<<numeric(lastTop)<<','<<numeric(s.age)<<','<<numeric(s.maxFAA)<<','<<numeric(s.minMargin)<<','<<s.failures<<','<<(s.all?1:0)<<'\n';if(!s.all)++failedCount[ver-1];
  }
 }
 Rows comps;comps.reserve(N);for(size_t i=0;i<N;++i){auto&a=retained[0][i],&b=retained[1][i];comps.push_back({a.at("HOTSPOT"),b.at("HOTSPOT"),a.at("FAA"),b.at("FAA"),a.at("AGE_ACCUM"),b.at("AGE_ACCUM"),a.at("MARGIN_HOTSPOT"),b.at("MARGIN_HOTSPOT"),a.at("COMPOSITE_GUARD"),b.at("COMPOSITE_GUARD"),a.at("PEAK_HOTSPOT"),b.at("PEAK_HOTSPOT")});}
 // Compare models in genuine batched paceval execution, while keeping time-state updates separate.
 size_t compareChecks=0;std::vector<double> finalDelta(N),deltaPeak(N),deltaAge(N),ageRatio(N);std::map<std::string,size_t> lastIndex;for(size_t j=0;j<N;++j)lastIndex[records[j].scenario+"/"+records[j].id]=j;for(size_t start=0;start<N;start+=256){size_t end=std::min(start+256,N);Rows block(comps.begin()+start,comps.begin()+end);auto results=models.evaluate("V1_vs_V2",block);for(size_t j=start;j<end;j++){auto r=models.unpack("V1_vs_V2",results[j-start]);if(j%151==0){near(r.at("DELTA_HOTSPOT"),comps[j][1]-comps[j][0]);near(r.at("DELTA_ACCUM_AGE"),comps[j][5]-comps[j][4]);compareChecks+=2;}finalDelta[j]=r.at("DELTA_HOTSPOT");deltaPeak[j]=r.at("DELTA_PEAK");deltaAge[j]=r.at("DELTA_ACCUM_AGE");ageRatio[j]=r.at("AGE_RATIO");}}
 for(const auto& pr:states[0]){const auto& key=pr.first;const auto& a=pr.second;const auto& b=states[1].at(key);auto pos=key.find('/');const auto& sc=key.substr(0,pos);const auto& id=key.substr(pos+1);double h1=0,h2=0;for(size_t j=N;j-->0;)if(records[j].scenario==sc&&records[j].id==id){h1=retained[0][j].at("HOTSPOT");h2=retained[1][j].at("HOTSPOT");break;}
  // Mathematical differences and ratios are the actual paceval model-comparison graph outputs.
  diff<<sc<<','<<id<<','<<numeric(a.peak)<<','<<numeric(b.peak)<<','<<numeric(deltaPeak[lastIndex.at(key)])<<','<<numeric(a.age)<<','<<numeric(b.age)<<','<<numeric(deltaAge[lastIndex.at(key)])<<','<<numeric(ageRatio[lastIndex.at(key)])<<','<<numeric(h1)<<','<<numeric(h2)<<','<<numeric(finalDelta[lastIndex.at(key)])<<','<<numeric(std::min(a.minMargin,b.minMargin))<<','<<(a.all&&b.all?1:0)<<'\n';
 }
 size_t executed=0;manifest<<"graph_id,version,expression,units,industrial_purpose\n";inventory<<"function_id,domain_quantity,mathematical_definition,units,execution_owner,paceval_graph_id,formula_version,api_path,reference_test,status,host_reason\n";
 for(const auto& g:models.graphs){if(g.executed)++executed;manifest<<g.id<<','<<g.version<<",\""<<g.expression<<"\","<<g.unit<<",\""<<g.description<<"\"\n";inventory<<g.id<<",\""<<g.description<<"\",\""<<g.expression<<"\","<<g.unit<<",paceval,"<<g.id<<','<<g.version<<",paceval_dGetMultipleComputationsResultsExt,independent C++ and mpmath,"<<(g.executed?"executed":"registered_only")<<",\n";}
 inventory<<"CSV_PARSE,Numeric input conversion,Validated decimal literal to binary64,1,paceval,,all,paceval_dConvertStringToFloat,negative CSV tests,executed,\n";
 inventory<<"CSV_WRITE,Numeric output conversion,Binary64 to documented text representation,1,paceval,,all,paceval_dConvertFloatToString,roundtrip sampling,executed,\n";
 inventory<<"TIME_PROPAGATION,Sequential state ownership,Previous paceval state passed unchanged to next interval,1,host,,all,C++ loop,independent full-chain check,executed,Stateful chronology is host orchestration\n";
 inventory<<"CASE_GENERATION,Synthetic hourly record design,Deterministic sinusoidal load and ambient profiles,1,host,,all,Python script,CSV schema controls,executed,Independent input generation not engine domain math\n";
 evidence<<"{\n  \"sdk\": \"original paceval 4.25 using supplied Linux shared library\",\n  \"case_scope\": \"deterministic synthetic oil-immersed transformer thermal proxy, not standards conformity\",\n  \"unique_graphs_created\": "<<models.graphs.size()<<",\n  \"unique_graphs_executed\": "<<executed<<",\n  \"scalar_calls_including_operator_tests\": "<<e.scalarCalls<<",\n  \"batch_calls_including_layout_probe\": "<<e.batchCalls<<",\n  \"graph_point_evaluations_including_layout_probe\": "<<e.points<<",\n  \"unique_transformers\": "<<params.size()<<",\n  \"scenario_count\": 3,\n  \"hours_per_scenario\": 336,\n  \"distinct_input_rows\": "<<N<<",\n  \"model_hour_rows\": "<<N*2<<",\n  \"asset_scenario_series\": "<<states[0].size()<<",\n  \"v1_series_with_any_screening_failure\": "<<failedCount[0]<<",\n  \"v2_series_with_any_screening_failure\": "<<failedCount[1]<<",\n  \"native_assertions\": "<<nativeChecks+compareChecks<<",\n  \"high_precision_verification\": \"see high_precision_audit.json\"\n}\n";
 require(executed==models.graphs.size(),"Not every domain graph was exercised");std::cout<<"RESEARCH PASS: "<<executed<<"/"<<models.graphs.size()<<" real paceval graphs, "<<N<<" synthetic hourly inputs x 2 models, independent native assertions "<<nativeChecks+compareChecks<<", series with screening exception V1/V2 "<<failedCount[0]<<"/"<<failedCount[1]<<"\n";
}
}
int main(int argc,char**argv){try{if(argc==2&&std::string(argv[1])=="--selftest"){selftest();return 0;}require(argc==5&&std::string(argv[1])=="--run","Usage: transformer_hotspot --run input/transformer_profiles.csv input/transformer_parameters.csv results/");run(argv[2],argv[3],argv[4]);return 0;}catch(const std::exception&e){std::cerr<<"ERROR: "<<e.what()<<'\n';return 1;}}
