// WP 16: CO2 absorber/stripper process-window screening with original paceval 4.25.
// Graphs compute physical proxy equations, composite margins, decisions, derivatives
// and two simultaneously accessible transfer/regen model versions. C++ owns I/O,
// input-domain validation, batch orchestration, and independent native checks.
// This deliberately reduced-order synthetic study is NOT a rigorous eNRTL,
// packed-column model, product purity prediction, or industrial plant approval.
#include "paceval_main.h"
#include <algorithm>
#include <cmath>
#include <cstdint>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <map>
#include <regex>
#include <sstream>
#include <stdexcept>
#include <string>
#include <vector>
namespace fs=std::filesystem;
namespace {
void require(bool ok,const std::string &msg){if(!ok)throw std::runtime_error(msg);}
void near(double a,double b,double rel=3e-8,double abs=2e-7){require(std::isfinite(a)&&std::isfinite(b)&&std::abs(a-b)<=abs+rel*std::max(std::abs(a),std::abs(b)),"Independent reference mismatch: "+std::to_string(a)+" vs "+std::to_string(b));}
bool literal(const std::string&s){static const std::regex r(R"(^[+-]?(?:[0-9]+(?:\.[0-9]*)?|\.[0-9]+)(?:[eE][+-]?[0-9]+)?$)");return std::regex_match(s,r);}
double parse(const std::string&s){require(literal(s),"Rejected nonliteral CSV numeric token: "+s);int err=-1;long pos=-1;double x=paceval_dConvertStringToFloat(s.c_str(),&err,&pos,false,nullptr,nullptr);require(err==0&&std::isfinite(x),"paceval numeric conversion failed error="+std::to_string(err)+" position="+std::to_string(pos));return x;}
std::string numeric(double x){require(std::isfinite(x),"Cannot serialize nonfinite value");char buffer[512]{};int precision=paceval_dConvertFloatToString(buffer,x);require(precision>0&&buffer[0]!=0&&std::string(buffer).find(',')==std::string::npos,"paceval decimal serialization failed");return buffer;}
std::vector<std::string> split(const std::string &s){std::vector<std::string>a;std::stringstream ss(s);std::string f;while(std::getline(ss,f,','))a.push_back(f);if(!s.empty()&&s.back()==',')a.push_back("");return a;}
std::string join(const std::vector<std::string>&a){std::string r;for(const auto&s:a){if(!r.empty())r+=' ';r+=s;}return r;}
using Rows=std::vector<std::vector<double>>;
struct Engine {
 std::vector<PACEVAL_HANDLE> handles;bool graphMajor=false;uint64_t scalarCalls=0,batchCalls=0,pointEvaluations=0;
 Engine(){require(paceval_InitializeLibrary(nullptr),"Original paceval initialization failed");}
 ~Engine(){for(auto h:handles)if(h)paceval_DeleteComputation(h);paceval_FreeLibrary();}
 PACEVAL_HANDLE create(const std::string &expr,const std::vector<std::string>&names){auto vars=join(names);auto h=paceval_CreateComputation(expr.c_str(),names.size(),vars.c_str(),false,nullptr);require(h&&!paceval_GetIsError(h),"SDK graph creation failed: "+expr);handles.push_back(h);return h;}
 double scalar(PACEVAL_HANDLE h,const std::vector<double> &args){auto x=args;auto y=paceval_dGetComputationResult(h,x.empty()?nullptr:x.data(),nullptr,nullptr);++scalarCalls;require(!paceval_GetIsError(h)&&std::isfinite(y),"SDK scalar evaluation failed");return y;}
 void layout(){auto a=create("x+2*y",{"x","y"});auto b=create("3*x-y",{"x","y"});PACEVAL_HANDLE hs[]={a,b};double x[]={1,2,4,7},out[4]{},lo[4]{},hi[4]{};int err[4]{};
  bool failed=paceval_dGetMultipleComputationsResultsExt(hs,2,x,2,out,lo,hi,err);
  require(!failed&&std::all_of(err,err+4,[](int k){return k==0;}),"SDK batch layout probe failed");
  if(std::abs(out[0]-5)<1e-11&&std::abs(out[1]-18)<1e-11&&std::abs(out[2]-1)<1e-11&&std::abs(out[3]-5)<1e-11)graphMajor=true;
  else if(std::abs(out[0]-5)<1e-11&&std::abs(out[1]-1)<1e-11&&std::abs(out[2]-18)<1e-11&&std::abs(out[3]-5)<1e-11)graphMajor=false;
  else throw std::runtime_error("Unrecognized SDK graph/point layout");
  ++batchCalls;pointEvaluations+=4;
 }
 Rows batch(const std::vector<PACEVAL_HANDLE>&hs,const Rows&x,size_t width){require(!hs.empty()&&!x.empty(),"Empty multi-graph batch");std::vector<double>flat;flat.reserve(x.size()*width);for(const auto&r:x){require(r.size()==width,"Incorrect batch row width");for(auto z:r)require(std::isfinite(z),"Nonfinite batch input");flat.insert(flat.end(),r.begin(),r.end());}
  const size_t n=x.size()*hs.size();std::vector<double>out(n),lo(n),hi(n);std::vector<int>err(n,-1);
  bool failed=paceval_dGetMultipleComputationsResultsExt(const_cast<PACEVAL_HANDLE*>(hs.data()),hs.size(),flat.data(),x.size(),out.data(),lo.data(),hi.data(),err.data());
  require(!failed,"SDK multi-graph batch returned failure");for(int e:err)require(e==0,"SDK batch item error="+std::to_string(e));
  Rows result(x.size(),std::vector<double>(hs.size()));for(size_t i=0;i<x.size();++i)for(size_t g=0;g<hs.size();++g){auto idx=graphMajor?g*x.size()+i:i*hs.size()+g;require(std::isfinite(out[idx]),"Nonfinite domain result");result[i][g]=out[idx];}
  ++batchCalls;pointEvaluations+=n;return result;
 }
};
const std::vector<std::string> VARS={"Fin","Fgas","Kla","Vol","Cstar","Cbulk","S","lean","maxload","Tstrip","Tfeed","cp","hx","wt","dh","hvap","etaMin","qMax","tMax"};
struct Graph{std::string id,version,formula,unit,description;PACEVAL_HANDLE handle;bool executed=false;};
struct Model {
 Engine& engine;std::vector<Graph> graphs;std::map<std::string,size_t> index;
 explicit Model(Engine&e):engine(e){for(int ver=1;ver<=2;++ver){
  const std::string v=ver==1?"V1":"V2";
  const std::string raw="(Kla*Vol*(Cstar-Cbulk))";
  const std::string capacity="(S*(maxload-lean))";
  const std::string potential=ver==1?raw:"("+capacity+"*(1-exp(-"+raw+"/"+capacity+")))";
  const std::string capture="(Fin min ("+capacity+" min "+potential+"))";
  const std::string eta="("+capture+"/Fin)";
  const std::string rich="(lean+"+capture+"/S)";
  const std::string hxeff=ver==1?"hx":"((hx+0.04) min 0.98)";
  const std::string sensible="(S*0.06108/wt*cp*(Tstrip-Tfeed)*(1-"+hxeff+"))";
  const std::string desorb="("+capture+"*dh)";
  const std::string vapor=ver==1?"("+capture+"*hvap)":"("+capture+"*hvap*(1+0.003*(Tstrip-390)))";
  const std::string reboiler="("+sensible+"+"+desorb+"+"+vapor+")";
  const std::string spec="("+reboiler+"/("+capture+"*0.04401*1000))";
  const std::string mEta="("+eta+"-etaMin)";
  const std::string mQ="(qMax-"+spec+")";
  const std::string mL="(("+capacity+"-"+capture+")/S)";
  const std::string mT="(tMax-Tstrip)";
  const std::string guard="(("+mEta+">=0) AND ("+mQ+">=0) AND ("+mL+">=0) AND ("+mT+">=0))";
  const std::string drive="(Vol*(Cstar-Cbulk))";
  const std::string dCapture=ver==1?"((("+raw+"<Fin) AND ("+raw+"<"+capacity+"))*"+drive+")":"(("+potential+"<Fin)*exp(-"+raw+"/"+capacity+")*"+drive+")";
  const std::string dQ="(S*0.06108/wt*cp*(1-"+hxeff+")+"+(ver==1?"0":"("+capture+"*hvap*0.003)")+")/("+capture+"*0.04401*1000)";
  auto add=[&](const std::string&id,const std::string&ex,const std::string&unit,const std::string&purpose){Graph g{v+"_"+id,v,ex,unit,purpose,engine.create(ex,VARS),false};index[g.id]=graphs.size();graphs.push_back(std::move(g));};
  add("TRANSFER_POTENTIAL",raw,"mol/s","Volumetric absorber transfer proxy");
  add("CYCLIC_CAPACITY",capacity,"mol/s","Solvent loading-based capacity");
  add("EFFECTIVE_TRANSFER",potential,"mol/s","Versioned absorber transfer profile");
  add("CAPTURE",capture,"mol/s","Actual bounded CO2 capture rate");
  add("CAPTURE_MASS","("+capture+"*0.04401)","kg/s","Captured CO2 mass flow");
  add("OFFGAS_CO2","(Fin-"+capture+")","mol/s","CO2 remaining in treated gas");
  add("OFFGAS_YCO2","((Fin-"+capture+")/(Fgas-"+capture+"))","mol/mol","CO2 mole fraction assuming binary gas and negligible solvent losses");
  add("CAPTURE_FRACTION",eta,"1","Fractional CO2 recovery");
  add("RICH_LOADING",rich,"mol/mol","CO2 loading leaving absorber");
  add("UNUSED_CAPACITY","("+capacity+"-"+capture+")","mol/s","Remaining solvent uptake capacity");
  add("HX_EFFECTIVENESS",hxeff,"1","Versioned heat-exchanger recovery parameter");
  add("REBOILER_SENSIBLE",sensible,"kW","Net sensible reboiler heat proxy");
  add("REBOILER_DESORPTION",desorb,"kW","CO2 desorption enthalpy contribution");
  add("REBOILER_VAPOR",vapor,"kW","Simplified overhead vapor duty contribution");
  add("REBOILER_TOTAL",reboiler,"kW","Composite stripper reboiler duty");
  add("SPECIFIC_DUTY",spec,"GJ/tCO2","Thermal energy per mass of CO2 captured");
  add("MARGIN_CAPTURE",mEta,"1","Signed minimum recovery margin");
  add("MARGIN_DUTY",mQ,"GJ/tCO2","Signed maximum specific duty margin");
  add("MARGIN_LOADING",mL,"mol/mol","Signed maximum rich solvent loading margin");
  add("MARGIN_STRIP_TEMP",mT,"K","Signed maximum stripper temperature margin");
  add("COMPOSITE_GUARD",guard,"0_or_1","Combined four-constraint screening indicator");
  add("PROCESS_SCORE","(4*"+eta+"-"+spec+"-3*(0 max (-"+mEta+"))-2*(0 max (-"+mQ+")))","index","Illustrative composite operating score");
  add("D_CAPTURE_D_KLA",dCapture,"mol","Piecewise local CO2 recovery-flow sensitivity to kLa");
  add("D_ETA_D_KLA","("+dCapture+"/Fin)","s","Analytic local fractional capture sensitivity to kLa");
  add("D_QSPEC_D_TSTRIP",dQ,"GJ/tCO2/K","Local specific duty sensitivity at fixed captured flow");
 }
 const std::vector<std::string> n={"capA","capB","etaA","etaB","qA","qB","guardA","guardB","scoreA","scoreB","richA","richB"};
 auto add=[&](const std::string&id,const std::string&ex,const std::string&unit,const std::string&purpose){Graph g{id,"V1_vs_V2",ex,unit,purpose,engine.create(ex,n),false};index[g.id]=graphs.size();graphs.push_back(std::move(g));};
 add("DELTA_CAPTURE","(capB-capA)","mol/s","Change of capture between models");
 add("DELTA_RECOVERY","(etaB-etaA)","1","Change of capture fraction");
 add("DELTA_SPECIFIC_DUTY","(qB-qA)","GJ/tCO2","Change of regeneration heat intensity");
 add("DELTA_RICH_LOADING","(richB-richA)","mol/mol","Difference of solvent outlet loading");
 add("COMBINED_GUARD","((guardA=1) AND (guardB=1))","0_or_1","Both models satisfy screening conditions");
 add("DELTA_SCORE","(scoreB-scoreA)","index","Change of composite screening objective");
 }
 Rows evaluate(const std::string&version,const Rows&rows){std::vector<PACEVAL_HANDLE>hs;std::vector<size_t>idx;for(size_t j=0;j<graphs.size();++j)if(graphs[j].version==version){hs.push_back(graphs[j].handle);idx.push_back(j);}require(!idx.empty(),"Unknown model version");auto r=engine.batch(hs,rows,version=="V1_vs_V2"?12:VARS.size());for(auto j:idx)graphs[j].executed=true;return r;}
 std::map<std::string,double> unpack(const std::string &version,const std::vector<double>&values){std::map<std::string,double>m;size_t i=0;for(auto &g:graphs)if(g.version==version){auto id=g.id;if(version!="V1_vs_V2")id=id.substr(3);m[id]=values.at(i++);}return m;}
};
struct Case{std::string id,group;std::vector<double>x;};
void domain(const Case&c){const auto&x=c.x;require(x.size()==VARS.size(),"Incorrect numeric field count");for(double v:x)require(std::isfinite(v),"Nonfinite case input");
 require(x[0]>0&&x[1]>x[0]&&x[2]>0&&x[3]>0&&x[4]>x[5]&&x[5]>=0,"Invalid gas or absorption driving-force domain: "+c.id);
 require(x[6]>0&&x[7]>=0&&x[8]>x[7]&&x[8]<=0.65,"Invalid solvent concentration/loading domain: "+c.id);
 require(x[9]>x[10]&&x[9]>=360&&x[9]<=440&&x[10]>=270,"Invalid temperature domain: "+c.id);
 require(x[11]>0&&x[12]>=0&&x[12]<0.94&&x[13]>0&&x[13]<=1&&x[14]>0&&x[15]>=0,"Invalid solvent/enthalpy domain: "+c.id);
 require(x[16]>0&&x[16]<1&&x[17]>0&&x[18]>=360,"Invalid screening thresholds: "+c.id);
 // Both models have positive capture, positive capacity and positive retentate flow;
 // thus there is no hidden singularity behind a relational condition in a graph.
}
std::vector<Case> load(const fs::path&p){std::ifstream f(p);require(bool(f),"Cannot open research input: "+p.string());std::string line;require(bool(std::getline(f,line)),"Empty CSV input");std::string header="case_id,scenario";for(const auto&v:VARS)header+=","+v;require(line==header,"Unexpected input schema");std::vector<Case>a;size_t lineno=1;while(std::getline(f,line)){++lineno;require(!line.empty(),"Blank data row "+std::to_string(lineno));auto fields=split(line);require(fields.size()==VARS.size()+2,"Wrong CSV width line "+std::to_string(lineno));require(fields[0].size()>=3&&fields[1].size()>0,"Missing case metadata");Case c{fields[0],fields[1],{}};for(size_t i=2;i<fields.size();++i)c.x.push_back(parse(fields[i]));domain(c);a.push_back(std::move(c));}require(a.size()>=500,"Experimental dataset unexpectedly small");return a;}
struct Ref{double raw,cap,capture,eta,rich,sens,des,vap,total,q,y,mEta,mQ,mL,mT,score,dCdK,dqdT;int guard;};
Ref native(const std::vector<double>&x,int ver){double F=x[0],G=x[1],k=x[2],V=x[3],cs=x[4],cb=x[5],S=x[6],lean=x[7],amax=x[8],Ts=x[9],Tf=x[10],cp=x[11],hx=x[12],wt=x[13],dh=x[14],hvap=x[15],emin=x[16],qmax=x[17],tmax=x[18];
 double raw=k*V*(cs-cb),cap=S*(amax-lean),eff=ver==1?raw:cap*(-std::expm1(-raw/cap));double captured=std::min(F,std::min(cap,eff));double eta=captured/F,rich=lean+captured/S;
 double he=ver==1?hx:std::min(0.98,hx+0.04);double sens=S*0.06108/wt*cp*(Ts-Tf)*(1-he),des=captured*dh,vap=captured*hvap*(ver==1?1:1+0.003*(Ts-390));double total=sens+des+vap,q=total/(captured*0.04401*1000);
 double mEta=eta-emin,mQ=qmax-q,mL=(cap-captured)/S,mT=tmax-Ts;int g=mEta>=0&&mQ>=0&&mL>=0&&mT>=0;
 double score=4*eta-q-3*std::max(0.,-mEta)-2*std::max(0.,-mQ);
 double drv=V*(cs-cb);double dCdK=ver==1?((raw<F&&raw<cap)?drv:0):((eff<F)?std::exp(-raw/cap)*drv:0);
 double dqdT=(S*0.06108/wt*cp*(1-he)+(ver==1?0:captured*hvap*0.003))/(captured*0.04401*1000);
 return {raw,cap,captured,eta,rich,sens,des,vap,total,q,(F-captured)/(G-captured),mEta,mQ,mL,mT,score,dCdK,dqdT,g};}
size_t check(const std::vector<double>&x,int v,const std::map<std::string,double>&m){auto r=native(x,v);size_t n=0;
 auto c=[&](const char*k,double z){near(m.at(k),z);++n;};
 c("TRANSFER_POTENTIAL",r.raw);c("CYCLIC_CAPACITY",r.cap);c("CAPTURE",r.capture);c("CAPTURE_MASS",r.capture*0.04401);c("OFFGAS_CO2",x[0]-r.capture);c("OFFGAS_YCO2",r.y);c("CAPTURE_FRACTION",r.eta);c("RICH_LOADING",r.rich);c("UNUSED_CAPACITY",r.cap-r.capture);
 c("REBOILER_SENSIBLE",r.sens);c("REBOILER_DESORPTION",r.des);c("REBOILER_VAPOR",r.vap);c("REBOILER_TOTAL",r.total);c("SPECIFIC_DUTY",r.q);c("MARGIN_CAPTURE",r.mEta);c("MARGIN_DUTY",r.mQ);c("MARGIN_LOADING",r.mL);c("MARGIN_STRIP_TEMP",r.mT);c("COMPOSITE_GUARD",r.guard);c("PROCESS_SCORE",r.score);c("D_CAPTURE_D_KLA",r.dCdK);c("D_ETA_D_KLA",r.dCdK/x[0]);c("D_QSPEC_D_TSTRIP",r.dqdT);
 near(m.at("REBOILER_SENSIBLE")+m.at("REBOILER_DESORPTION")+m.at("REBOILER_VAPOR"),m.at("REBOILER_TOTAL"));++n;
 near(m.at("CAPTURE")+m.at("OFFGAS_CO2"),x[0]);++n;
 near(x[6]*(m.at("RICH_LOADING")-x[7]),m.at("CAPTURE"));++n;
 return n;}
void testOperators(Engine&e){for(auto a:std::vector<std::pair<std::string,double>>{{"((-1) % 10)",-1},{"((-1) mod 10)",9},{"(4 min 5)",4},{"(4 max 5)",5},{"(3 < 4)",1},{"(3 <= 3)",1},{"(3 >= 3)",1},{"(3 = 3)",1},{"(3 <> 4)",1},{"NOT(0)",1},{"(1 AND 1)",1},{"(0 OR 1)",1},{"((3<=3) AND (2>=0))",1}}){auto h=e.create(a.first,{});near(e.scalar(h,{}),a.second,0,1e-12);}
 near(parse("-1.25e-3"),-.00125);for(const char*bad:{"","NaN","Inf","2+3","1,2","1e9999"," 7","--1"}){bool rejected=false;try{(void)parse(bad);}catch(...){rejected=true;}require(rejected,"Unsafe number accepted");}require(!numeric(0.00045).empty(),"SDK numeric format error");}
void selftest(){Engine e;e.layout();testOperators(e);Model m(e);Case c{"SELF","baseline",{8,80,.40,10,5,3,38,.18,.50,393,315,3.8,.80,.30,80,11,.80,4.5,415}};domain(c);for(int v=1;v<=2;++v){std::string name=v==1?"V1":"V2";auto d=m.unpack(name,m.evaluate(name,Rows{c.x})[0]);check(c.x,v,d);near(e.scalar(m.graphs[m.index[name+"_SPECIFIC_DUTY"]].handle,c.x),d.at("SPECIFIC_DUTY"));}auto v1=m.unpack("V1",m.evaluate("V1",Rows{c.x})[0]);auto v2=m.unpack("V2",m.evaluate("V2",Rows{c.x})[0]);Rows comparison{{v1.at("CAPTURE"),v2.at("CAPTURE"),v1.at("CAPTURE_FRACTION"),v2.at("CAPTURE_FRACTION"),v1.at("SPECIFIC_DUTY"),v2.at("SPECIFIC_DUTY"),v1.at("COMPOSITE_GUARD"),v2.at("COMPOSITE_GUARD"),v1.at("PROCESS_SCORE"),v2.at("PROCESS_SCORE"),v1.at("RICH_LOADING"),v2.at("RICH_LOADING")}};auto t=m.unpack("V1_vs_V2",m.evaluate("V1_vs_V2",comparison)[0]);near(t.at("DELTA_CAPTURE"),v2.at("CAPTURE")-v1.at("CAPTURE"));std::cout<<"SELFTEST PASS original paceval SDK 4.25; scalar, multi-graph batch, binary64 conversion, operator semantics and domain chains\n";}
void run(const fs::path&in,const fs::path&out){fs::create_directories(out);Engine e;e.layout();testOperators(e);Model m(e);auto cases=load(in);size_t N=cases.size();
 std::ofstream results(out/"screening.csv"),cmp(out/"model_comparison.csv"),audit(out/"native_audit.csv"),manifest(out/"formula_manifest.csv"),inventory(out/"math_execution_inventory.csv"),evidence(out/"execution_evidence.json");require(bool(results&&cmp&&audit&&manifest&&inventory&&evidence),"Cannot write results");
 results<<"case_id,scenario,model,Fin_mol_s,Fgas_mol_s,kLa_per_s,solvent_mol_s,lean_loading,stripper_K,heat_recovery,capture_mol_s,recovery,rich_loading,offgas_CO2_fraction,reboiler_kW,sensible_kW,desorption_kW,vapor_kW,transfer_mol_s,capacity_mol_s,unused_capacity_mol_s,specific_duty_GJ_tCO2,capture_margin,duty_margin,loading_margin,temp_margin,composite_guard,process_score,d_capture_d_kLa,d_specific_duty_d_Tstrip\n";
 cmp<<"case_id,scenario,capture_V1_mol_s,capture_V2_mol_s,delta_capture_mol_s,recovery_V1,recovery_V2,delta_recovery,duty_V1_GJ_t,duty_V2_GJ_t,delta_duty_GJ_t,rich_loading_V1,rich_loading_V2,delta_rich_loading,guard_V1,guard_V2,both_feasible,delta_score\n";
 audit<<"case_id,scenario,model,native_endvalue_assertions,full_chain_passed\n";
 std::vector<std::map<std::string,double>> values[2];for(int v=1;v<=2;++v)values[v-1].resize(N);
 size_t checks=0,passed[2]{},batchsize=128;
 for(int v=1;v<=2;++v){std::string name=v==1?"V1":"V2";for(size_t start=0;start<N;start+=batchsize){size_t end=std::min(start+batchsize,N);Rows args;for(size_t i=start;i<end;++i)args.push_back(cases[i].x);auto y=m.evaluate(name,args);for(size_t i=start;i<end;++i){auto &c=cases[i];auto d=m.unpack(name,y[i-start]);values[v-1][i]=d;
  if(d.at("COMPOSITE_GUARD")>.5)++passed[v-1];
  results<<c.id<<','<<c.group<<','<<name;for(size_t k:{0,1,2,6,7,9,12})results<<','<<numeric(c.x[k]);
  for(auto col:{"CAPTURE","CAPTURE_FRACTION","RICH_LOADING","OFFGAS_YCO2","REBOILER_TOTAL","REBOILER_SENSIBLE","REBOILER_DESORPTION","REBOILER_VAPOR","TRANSFER_POTENTIAL","CYCLIC_CAPACITY","UNUSED_CAPACITY","SPECIFIC_DUTY","MARGIN_CAPTURE","MARGIN_DUTY","MARGIN_LOADING","MARGIN_STRIP_TEMP","COMPOSITE_GUARD","PROCESS_SCORE","D_CAPTURE_D_KLA","D_QSPEC_D_TSTRIP"})results<<','<<numeric(d.at(col));results<<'\n';
  if(i%31==0||i==0||i==N-1){size_t n=check(c.x,v,d);checks+=n;audit<<c.id<<','<<c.group<<','<<name<<','<<n<<",1\n";}
 }}}
 // Independently constructed parallel input rows feed persistent paceval comparison graphs.
 size_t cc=0;for(size_t start=0;start<N;start+=batchsize){size_t end=std::min(start+batchsize,N);Rows args;for(size_t i=start;i<end;++i){auto&a=values[0][i],&b=values[1][i];args.push_back({a.at("CAPTURE"),b.at("CAPTURE"),a.at("CAPTURE_FRACTION"),b.at("CAPTURE_FRACTION"),a.at("SPECIFIC_DUTY"),b.at("SPECIFIC_DUTY"),a.at("COMPOSITE_GUARD"),b.at("COMPOSITE_GUARD"),a.at("PROCESS_SCORE"),b.at("PROCESS_SCORE"),a.at("RICH_LOADING"),b.at("RICH_LOADING")});}
  auto r=m.evaluate("V1_vs_V2",args);for(size_t i=start;i<end;++i){auto &c=cases[i];auto&a=values[0][i],&b=values[1][i],d=m.unpack("V1_vs_V2",r[i-start]);cmp<<c.id<<','<<c.group;for(double z:{a.at("CAPTURE"),b.at("CAPTURE"),d.at("DELTA_CAPTURE"),a.at("CAPTURE_FRACTION"),b.at("CAPTURE_FRACTION"),d.at("DELTA_RECOVERY"),a.at("SPECIFIC_DUTY"),b.at("SPECIFIC_DUTY"),d.at("DELTA_SPECIFIC_DUTY"),a.at("RICH_LOADING"),b.at("RICH_LOADING"),d.at("DELTA_RICH_LOADING"),a.at("COMPOSITE_GUARD"),b.at("COMPOSITE_GUARD"),d.at("COMBINED_GUARD"),d.at("DELTA_SCORE")})cmp<<','<<numeric(z);cmp<<'\n';
   if(i%77==0){near(d.at("DELTA_CAPTURE"),b.at("CAPTURE")-a.at("CAPTURE"));near(d.at("DELTA_SPECIFIC_DUTY"),b.at("SPECIFIC_DUTY")-a.at("SPECIFIC_DUTY"));cc+=2;}
  }}
 manifest<<"graph_id,version,expression,units,industrial_purpose\n";inventory<<"function_id,domain_quantity,mathematical_definition,units,execution_owner,paceval_graph_id,formula_version,api_path,reference_test,status,host_reason\n";size_t count=0;
 for(const auto&g:m.graphs){if(g.executed)++count;manifest<<g.id<<','<<g.version<<",\""<<g.formula<<"\","<<g.unit<<",\""<<g.description<<"\"\n";inventory<<g.id<<",\""<<g.description<<"\",\""<<g.formula<<"\","<<g.unit<<",paceval,"<<g.id<<','<<g.version<<",paceval_dGetMultipleComputationsResultsExt,native C++ plus mpmath,"<<(g.executed?"executed":"registered_only")<<",\n";}
 inventory<<"CSV_PARSE,Validated numeric ingestion,Binary64 decimal input,1,paceval,,all,paceval_dConvertStringToFloat,literal rejection tests,executed,\n";
 inventory<<"CSV_WRITE,Decimal rendering,Binary64 text output,1,paceval,,all,paceval_dConvertFloatToString,independent CSV parser,executed,\n";
 inventory<<"CASE_ENUMERATION,Operating point generation,Deterministic synthetic design,1,host,,all,Python generator,source audit,executed,Input construction is not process math\n";
 inventory<<"FEASIBILITY_SELECTION,Decision aggregation,Boolean flags and scenario filtering,1,host,,all,C++ control flow,traceability,executed,State and I-O remain host responsibilities\n";
 evidence<<"{\n  \"sdk\": \"original paceval 4.25 plus supplied Linux runtime\",\n  \"case_scope\": \"deterministic synthetic reduced-order amine process-window screening\",\n  \"unique_graphs_created\": "<<m.graphs.size()<<",\n  \"unique_graphs_executed\": "<<count<<",\n  \"scalar_calls_including_operator_tests\": "<<e.scalarCalls<<",\n  \"batch_calls_including_layout_probe\": "<<e.batchCalls<<",\n  \"graph_point_evaluations_including_layout_probe\": "<<e.pointEvaluations<<",\n  \"scenario_count\": "<<N<<",\n  \"model_case_combinations\": "<<N*2<<",\n  \"feasible_V1\": "<<passed[0]<<",\n  \"feasible_V2\": "<<passed[1]<<",\n  \"native_assertions\": "<<checks+cc<<",\n  \"high_precision_verification\": \"see high_precision_audit.json\"\n}\n";
 require(count==m.graphs.size(),"Not all research graphs executed");std::cout<<"RESEARCH PASS: "<<count<<"/"<<m.graphs.size()<<" original SDK graphs, "<<N<<" synthetic cases x two versions, "<<checks+cc<<" native C++ assertions, feasibility V1/V2 "<<passed[0]<<"/"<<passed[1]<<"\n";
}
}
int main(int argc,char**argv){try{if(argc==2&&std::string(argv[1])=="--selftest"){selftest();return 0;}require(argc==4&&std::string(argv[1])=="--run","Usage: carbon_capture --run input/operating_points.csv results/");run(argv[2],argv[3]);return 0;}catch(const std::exception&e){std::cerr<<"ERROR: "<<e.what()<<'\n';return 1;}}
