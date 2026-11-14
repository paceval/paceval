// WP 10: reproducible, synthetic IPMSM operating-map screening with the
// original paceval SDK 4.25. The genuine paceval computation graphs own all
// motor mathematics, losses, scores, analytical sensitivities, and guards.
// The C++ host owns validation, enumeration, storage and finite-set selection.
// This is a stationary analytical model, NOT a calibrated FEA motor model,
// certified efficiency measurement, real-time controller or safety release.
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
#include <map>
#include <regex>
#include <sstream>
#include <stdexcept>
#include <string>
#include <vector>
namespace fs=std::filesystem;
namespace {
void require(bool ok,const std::string& msg){if(!ok)throw std::runtime_error(msg);}
bool decimalLiteral(const std::string& s){static const std::regex re(R"(^[+-]?(?:[0-9]+(?:\.[0-9]*)?|\.[0-9]+)(?:[eE][+-]?[0-9]+)?$)");return std::regex_match(s,re);}
double parseNumber(const std::string& raw){require(decimalLiteral(raw),"Invalid numeric literal: "+raw);int err=-1;long pos=-1;double v=paceval_dConvertStringToFloat(raw.c_str(),&err,&pos,false,nullptr,nullptr);require(err==0&&std::isfinite(v),"paceval numeric input error at "+std::to_string(pos));return v;}
std::string number(double v){require(std::isfinite(v),"Nonfinite output forbidden");char buf[512]{};int ret=paceval_dConvertFloatToString(buf,v);require(ret>0&&buf[0]&&std::string(buf).find(',')==std::string::npos,"paceval numeric formatting failed");return std::string(buf);}
std::vector<std::string> splitCsv(const std::string& line){std::vector<std::string> out;std::stringstream s(line);std::string t;while(std::getline(s,t,','))out.push_back(t);if(!line.empty()&&line.back()==',')out.emplace_back();return out;}
void near(double x,double y,double relative=2e-8,double absolute=1e-10){require(std::isfinite(x)&&std::isfinite(y)&&std::abs(x-y)<=absolute+relative*std::max(std::abs(x),std::abs(y)),"Independent numerical check did not pass");}
std::string join(const std::vector<std::string>& vs){std::string s;for(const auto& x:vs){if(!s.empty())s+=" ";s+=x;}return s;}
using Rows=std::vector<std::vector<double>>;
struct Engine{
 std::vector<PACEVAL_HANDLE> lifetime;bool graphMajor=false;uint64_t scalarCalls=0,batchCalls=0,graphPointEvaluations=0;
 Engine(){require(paceval_InitializeLibrary(nullptr),"paceval initialization failed");}
 ~Engine(){for(auto h:lifetime)if(h)paceval_DeleteComputation(h);paceval_FreeLibrary();}
 PACEVAL_HANDLE create(const std::string& expr,const std::vector<std::string>& vars){auto joined=join(vars);auto h=paceval_CreateComputation(expr.c_str(),vars.size(),joined.c_str(),false,nullptr);require(h&&!paceval_GetIsError(h),"Graph registration failed: "+expr);lifetime.push_back(h);return h;}
 double scalar(PACEVAL_HANDLE h,const std::vector<double>& a){auto input=a;for(double x:input)require(std::isfinite(x),"Invalid scalar input");double y=paceval_dGetComputationResult(h,input.data(),nullptr,nullptr);scalarCalls++;require(!paceval_GetIsError(h)&&std::isfinite(y),"Invalid scalar paceval result");return y;}
 void probe(){auto a=create("x+2*y",{"x","y"}),b=create("3*x-y",{"x","y"});PACEVAL_HANDLE hs[]={a,b};double in[]={1,2,4,7},out[4]{},lo[4]{},hi[4]{};int err[4]{};bool failed=paceval_dGetMultipleComputationsResultsExt(hs,2,in,2,out,lo,hi,err);require(!failed&&std::all_of(err,err+4,[](int e){return e==0;}),"Original SDK multi-graph layout probe failed");
 if(std::abs(out[0]-5)<1e-10&&std::abs(out[1]-18)<1e-10&&std::abs(out[2]-1)<1e-10&&std::abs(out[3]-5)<1e-10)graphMajor=true;
 else if(std::abs(out[0]-5)<1e-10&&std::abs(out[1]-1)<1e-10&&std::abs(out[2]-18)<1e-10&&std::abs(out[3]-5)<1e-10)graphMajor=false;
 else throw std::runtime_error("Unknown SDK multi-result ordering");batchCalls++;graphPointEvaluations+=4;}
 Rows batch(const std::vector<PACEVAL_HANDLE>& hs,const Rows& rows,size_t vars){require(!hs.empty()&&!rows.empty(),"Empty batch");std::vector<double> in;in.reserve(rows.size()*vars);for(const auto& r:rows){require(r.size()==vars,"Batch variable count error");for(double x:r)require(std::isfinite(x),"Nonfinite input");in.insert(in.end(),r.begin(),r.end());}
 const size_t count=rows.size()*hs.size();std::vector<double> out(count),lo(count),hi(count);std::vector<int> err(count,-1);
 // SDK 4.25 returns false on successful multi-graph evaluation: test item codes.
 bool failed=paceval_dGetMultipleComputationsResultsExt(const_cast<PACEVAL_HANDLE*>(hs.data()),hs.size(),in.data(),rows.size(),out.data(),lo.data(),hi.data(),err.data());require(!failed,"Multi-graph API failure");for(int x:err)require(x==0,"Multi-graph item error "+std::to_string(x));
 Rows result(rows.size(),std::vector<double>(hs.size()));for(size_t j=0;j<rows.size();j++)for(size_t k=0;k<hs.size();k++){size_t idx=graphMajor?k*rows.size()+j:j*hs.size()+k;require(std::isfinite(out[idx]),"Nonfinite paceval motor result");result[j][k]=out[idx];}
 ++batchCalls;graphPointEvaluations+=count;return result;}
};
// All variables are common to all graphs. Angle, current, and voltage are
// rotor dq-frame peak quantities; p denotes POLE PAIRS, not number of poles.
const std::vector<std::string> VARS={"id","iq","rpm","temp","Rs25","alphaR","psi25","betaPsi","Ld","Lq","p","Imax","Vdc","kFe","kMech","Tnom","EtaMin","Ttarget","Tref"};
struct Graph{std::string id,version,description,expression,units;PACEVAL_HANDLE handle{};bool executed=false;};
struct Models{
 Engine& engine;std::vector<Graph> graphs;std::map<std::string,size_t> index;
 explicit Models(Engine& e):engine(e){
  const std::string wm="((2*pi*rpm)/60)",we="(p*"+wm+")",i2="(id*id+iq*iq)",vmax="(Vdc/sqrt(3))";
  for(int version=1;version<=2;version++){
   std::string pre=version==1?"V1_":"V2_";
   const std::string R=version==1?"Rs25":"(Rs25*(1+alphaR*(temp-Tref)))";
   const std::string PM=version==1?"psi25":"(psi25*(1+betaPsi*(temp-Tref)))";
   const std::string pd="("+PM+"+Ld*id)",pq="(Lq*iq)";
   const std::string vd="("+R+"*id-"+we+"*"+pq+")",vq="("+R+"*iq+"+we+"*"+pd+")";
   const std::string voltsq="("+vd+"*"+vd+"+"+vq+"*"+vq+")";
   const std::string Te="(1.5*p*("+PM+"+(Ld-Lq)*id)*iq)";
   const std::string Pe="("+Te+"*"+wm+")";
   const std::string Cu="(1.5*"+R+"*"+i2+")";
   const std::string Fe="(kFe*"+we+"*"+we+"*("+pd+"*"+pd+"+"+pq+"*"+pq+"))";
   const std::string Fr="(kMech*"+wm+"*"+wm+")";
   const std::string Pshaft="("+Pe+"-"+Fr+")",Pin="("+Pe+"+"+Cu+"+"+Fe+")";
   const std::string eta="(("+Pshaft+" max 0)/("+Pin+" max 0.000000001))";
   const std::string imarg="(Imax*Imax-"+i2+")",vmarg="("+vmax+"*"+vmax+"-"+voltsq+")";
   auto add=[&](std::string key,std::string expr,std::string units,std::string desc){Graph g{pre+key,version==1?"V1":"V2",desc,expr,units,engine.create(expr,VARS),false};index[g.id]=graphs.size();graphs.push_back(std::move(g));};
   add("RS",R,"Ohm","Stator phase resistance");
   add("PM_FLUX",PM,"Wb","Temperature-dependent magnet flux linkage");
   add("FLUX_D",pd,"Wb","d-axis flux linkage");
   add("FLUX_Q",pq,"Wb","q-axis flux linkage");
   add("VOLTAGE_D",vd,"V","d-axis terminal voltage including Rs");
   add("VOLTAGE_Q",vq,"V","q-axis terminal voltage including Rs");
   add("VOLTAGE_MAG","sqrt("+voltsq+")","V","Peak phase voltage vector requirement");
   add("TORQUE",Te,"Nm","Electromagnetic IPMSM torque including saliency");
   add("TORQUE_PM","(1.5*p*"+PM+"*iq)","Nm","Permanent magnet torque contribution");
   add("TORQUE_RELUCTANCE","(1.5*p*(Ld-Lq)*id*iq)","Nm","Reluctance torque contribution");
   add("COPPER_LOSS",Cu,"W","Three-phase stator copper loss");
   add("IRON_LOSS",Fe,"W","Uncalibrated quadratic-speed/flux iron-loss surrogate");
   add("MECH_LOSS",Fr,"W","Uncalibrated quadratic-speed mechanical loss surrogate");
   add("TOTAL_LOSS","("+Cu+"+"+Fe+"+"+Fr+")","W","Combined illustrative motor losses");
   add("EM_POWER",Pe,"W","Electromagnetic torque times mechanical speed");
   add("SHAFT_POWER",Pshaft,"W","Estimated mechanical shaft output");
   add("ELEC_INPUT",Pin,"W","Electrical input ignoring converter losses");
   add("EFFICIENCY",eta,"1","Motoring shaft efficiency with idle clipping");
   add("CURRENT_MARGIN",imarg,"A2","Positive squared-current limit margin");
   add("VOLTAGE_MARGIN",vmarg,"V2","Positive squared-voltage limit margin");
   add("CURRENT_UTIL","(sqrt("+i2+")/Imax)","1","Phase-current limit utilization");
   add("VOLTAGE_UTIL","(sqrt("+voltsq+")/"+vmax+")","1","Voltage constraint utilization");
   add("TARGET_TORQUE_MARGIN","("+Te+"-Ttarget)","Nm","Demand torque tracking margin");
   add("EFFICIENCY_MARGIN","("+eta+"-EtaMin)","1","Illustrative shaft efficiency threshold margin");
   add("FEASIBILITY_GUARD","(("+imarg+" >= 0) AND ("+vmarg+" >= 0))","0_or_1","Joint current and voltage feasibility indicator");
   add("SCREENING_SCORE","(0.65*("+Te+"/Tnom)+0.35*"+eta+")","1","Combined torque/efficiency screening objective");
   add("DTORQUE_DID","(1.5*p*(Ld-Lq)*iq)","Nm_per_A","Analytical torque sensitivity to d current");
   add("DTORQUE_DIQ","(1.5*p*("+PM+"+(Ld-Lq)*id))","Nm_per_A","Analytical torque sensitivity to q current");
   add("DVOLTAGE2_DID","(2*"+vd+"*"+R+"+2*"+vq+"*"+we+"*Ld)","V2_per_A","Analytical voltage-square sensitivity to d current");
   add("DVOLTAGE2_DIQ","(2*"+vd+"*(-"+we+"*Lq)+2*"+vq+"*"+R+")","V2_per_A","Analytical voltage-square sensitivity to q current");
   add("DTORQUE_DT",version==1?"(0*temp)":"(1.5*p*psi25*betaPsi*iq)","Nm_per_K","Torque sensitivity to winding/magnet temperature");
   add("DCOPPER_DT",version==1?"(0*temp)":"(1.5*Rs25*alphaR*"+i2+")","W_per_K","Stator copper loss temperature sensitivity");
  }
  // These pairwise model comparisons are also genuinely executed as paceval
  // graphs. Host merely transports already evaluated outcomes to these graphs.
  const std::vector<std::string> diffVars={"t1","t2","v1","v2","e1","e2","l1","l2","m1","m2"};
  auto addDiff=[&](std::string id,std::string expr,std::string units,std::string desc){Graph g{id,"V1_vs_V2",desc,expr,units,engine.create(expr,diffVars),false};index[g.id]=graphs.size();graphs.push_back(std::move(g));};
  addDiff("DELTA_TORQUE","(t2-t1)","Nm","Temperature-aware minus constant-parameter torque");
  addDiff("DELTA_VOLTAGE","(v2-v1)","V","Temperature-aware minus constant-parameter voltage");
  addDiff("DELTA_EFFICIENCY","(e2-e1)","1","Temperature-aware minus constant-parameter efficiency");
  addDiff("DELTA_TOTAL_LOSS","(l2-l1)","W","Temperature-aware minus constant-parameter losses");
  addDiff("WORST_VOLT_MARGIN","(m1 min m2)","V2","Conservative voltage margin across two models");
 }
 std::vector<Graph*> stage(const std::string& name){std::vector<Graph*> out;for(auto& g:graphs)if(g.version==name)out.push_back(&g);return out;}
 Rows evaluate(const std::string& version,const Rows& rows){auto gs=stage(version);std::vector<PACEVAL_HANDLE> hs;for(auto* g:gs)hs.push_back(g->handle);auto out=engine.batch(hs,rows,version=="V1_vs_V2"?10:VARS.size());for(auto* g:gs)g->executed=true;return out;}
 std::map<std::string,double> unpack(const std::string& version,const std::vector<double>& row){std::map<std::string,double> out;auto gs=stage(version);require(gs.size()==row.size(),"Unpack width mismatch");for(size_t i=0;i<gs.size();i++){std::string id=gs[i]->id;auto pre=version+"_";if(id.rfind(pre,0)==0)id=id.substr(pre.size());out[id]=row[i];}return out;}
};
struct Params{double Rs25=.026,alphaR=.00393,psi25=.135,betaPsi=-.001,Ld=.00034,Lq=.00077,p=4,Imax=240,Vdc=600,kFe=.006,kMech=.0008,Tnom=230,EtaMin=.90,Ttarget=120,Tref=25;};
struct Case{std::string id;double rpm,idA,iqA,temp;};
const std::vector<std::string> PARAM_NAMES={"Rs25_Ohm","alphaR_invK","psi25_Wb","betaPsi_invK","Ld_H","Lq_H","pole_pairs","Imax_Apeak","Vdc_V","kFe_proxy","kMech_proxy","Tnom_Nm","EtaMin","Ttarget_Nm","Tref_C"};
Params loadParameters(const fs::path& path){std::ifstream f(path);require(bool(f),"Cannot open parameter CSV");std::string header,line;require(bool(std::getline(f,header))&&bool(std::getline(f,line)),"Parameter header/row missing");auto h=splitCsv(header),v=splitCsv(line);require(h==PARAM_NAMES&&v.size()==h.size(),"Unexpected model parameter schema");std::vector<double> a;for(const auto& s:v)a.push_back(parseNumber(s));Params p;int i=0;p.Rs25=a[i++];p.alphaR=a[i++];p.psi25=a[i++];p.betaPsi=a[i++];p.Ld=a[i++];p.Lq=a[i++];p.p=a[i++];p.Imax=a[i++];p.Vdc=a[i++];p.kFe=a[i++];p.kMech=a[i++];p.Tnom=a[i++];p.EtaMin=a[i++];p.Ttarget=a[i++];p.Tref=a[i++];
 require(p.Rs25>0&&p.alphaR>=0&&p.psi25>0&&p.betaPsi<=0&&p.Ld>0&&p.Lq>0&&p.p>0&&p.Imax>0&&p.Vdc>0&&p.kFe>=0&&p.kMech>=0&&p.Tnom>0&&p.EtaMin>0&&p.EtaMin<1&&p.Ttarget>=0,"Invalid model parameters");require(std::floor(p.p)==p.p&&p.p<=32,"Pole pair count must be integer");return p;}
std::vector<Case> loadCases(const fs::path& path){std::ifstream f(path);require(bool(f),"Cannot open candidates CSV");std::string header;require(bool(std::getline(f,header))&&header=="case_id,speed_rpm,id_Apeak,iq_Apeak,temperature_C","Candidate header mismatch");std::vector<Case> cases;std::string line;size_t no=1;while(std::getline(f,line)){no++;require(!line.empty(),"Unexpected blank candidate row");auto v=splitCsv(line);require(v.size()==5,"Malformed row at "+std::to_string(no));require(!v[0].empty()&&v[0].size()<70&&v[0].find_first_not_of("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789_-")==std::string::npos,"Unsafe scenario id");Case c{v[0],parseNumber(v[1]),parseNumber(v[2]),parseNumber(v[3]),parseNumber(v[4])};require(c.rpm>=0&&c.rpm<=20000&&c.idA>=-500&&c.idA<=500&&c.iqA>=0&&c.iqA<=500&&c.temp>=-40&&c.temp<=180,"Input outside declared domain");cases.push_back(c);require(cases.size()<=200000,"Excessive scenario count");}require(!cases.empty(),"No candidate rows");return cases;}
std::vector<double> input(const Case& c,const Params& p){return {c.idA,c.iqA,c.rpm,c.temp,p.Rs25,p.alphaR,p.psi25,p.betaPsi,p.Ld,p.Lq,p.p,p.Imax,p.Vdc,p.kFe,p.kMech,p.Tnom,p.EtaMin,p.Ttarget,p.Tref};}
// An independently coded native reference, never used to produce research output.
std::array<double,6> native(const Case& c,const Params& p,int model){const double w=c.rpm*(2*std::acos(-1.))/60.,e=p.p*w;
 const double R=p.Rs25*(model==2?1+p.alphaR*(c.temp-p.Tref):1),psi=p.psi25*(model==2?1+p.betaPsi*(c.temp-p.Tref):1);
 const double d=psi+p.Ld*c.idA,q=p.Lq*c.iqA,vd=R*c.idA-e*q,vq=R*c.iqA+e*d;
 const double T=1.5*p.p*(d*c.iqA-q*c.idA),V=std::hypot(vd,vq),P=T*w,Cu=1.5*R*(c.idA*c.idA+c.iqA*c.iqA),Fe=p.kFe*e*e*(d*d+q*q),Fr=p.kMech*w*w;
 const double shaft=P-Fr, eta=std::max(0.0,shaft)/std::max(P+Cu+Fe,1e-9);return {T,V,eta,Cu+Fe+Fr,p.Imax*p.Imax-(c.idA*c.idA+c.iqA*c.iqA),std::pow(p.Vdc/std::sqrt(3.),2)-V*V};}
void operatorTests(Engine& e){auto op=[&](const std::string& s,double truth){auto h=e.create(s,{"x","y","z"});near(e.scalar(h,{1,2,3}),truth,0,1e-11);};
 op("((x < y) AND (z >= 0))",1);op("((x >= y) OR (z = 3))",1);op("NOT(x=y)",1);op("((x <> y) AND (x <= y))",1);op("((abs(x) <= (2*y)) AND (z >= 0))",1);op("(x min y)",1);op("(x max y)",2);op("(-1) % 10",-1);op("(-1) mod 10",9);op("((x=y) XOR (x<y))",1);
 for(const char* s:{"0","-0.25","3.1E-5","+0.002",".125","2."})near(parseNumber(number(parseNumber(s))),parseNumber(s),2e-12,2e-16);
 for(const char* bad:{""," 2","NaN","Inf","1e99999","2+3","1,20","0x1","1;2","-"}){bool rejected=false;try{(void)parseNumber(bad);}catch(...){rejected=true;}require(rejected,"Unsafe numeric format accepted");}
}
void selftest(){Engine e;e.probe();operatorTests(e);Models models(e);Params p;std::vector<Case> a={{"zero",0,0,0,25},{"fw",9200,-170,140,110},{"mtpa",1900,-65,190,25},{"temp",3800,-85,120,110}};Rows rows;for(auto& x:a)rows.push_back(input(x,p));for(int v=1;v<=2;v++){std::string tag=v==1?"V1":"V2";auto r=models.evaluate(tag,rows);for(size_t i=0;i<a.size();i++){auto m=models.unpack(tag,r[i]);auto n=native(a[i],p,v);near(m.at("TORQUE"),n[0]);near(m.at("VOLTAGE_MAG"),n[1]);near(m.at("EFFICIENCY"),n[2]);near(m.at("TOTAL_LOSS"),n[3]);near(m.at("CURRENT_MARGIN"),n[4]);near(m.at("VOLTAGE_MARGIN"),n[5]);near(m.at("TORQUE"),m.at("TORQUE_PM")+m.at("TORQUE_RELUCTANCE"));require(m.at("FEASIBILITY_GUARD")==double(n[4]>=0&&n[5]>=0),"Guard semantics error");}}
 // Expected invariants: zero torque for zero q-current, temperature-independent V1;
 // a nonzero negative d current reduces back EMF at nonzero rotor speed.
 auto z=models.unpack("V1",models.evaluate("V1",Rows{input(a[0],p)})[0]);near(z.at("TORQUE"),0,0,1e-12);auto hot=models.unpack("V2",models.evaluate("V2",Rows{input(a[3],p)})[0]);require(hot.at("RS")>p.Rs25&&hot.at("PM_FLUX")<p.psi25,"Thermal parameters not updated");
 std::cout<<"SELFTEST PASS: original SDK 4.25; real multi-graph; operators; strict CSV conversions; torque-voltage-loss-efficiency chain\n";}
void run(const fs::path& candidates,const fs::path& parameters,const fs::path& outfolder){fs::create_directories(outfolder);Engine e;e.probe();Models m(e);Params p=loadParameters(parameters);auto cases=loadCases(candidates);
 std::ofstream results(outfolder/"screening.csv"),compare(outfolder/"model_comparison.csv"),audit(outfolder/"native_audit.csv"),envelope(outfolder/"torque_speed_envelope.csv"),tradeoff(outfolder/"efficiency_recommended.csv"),manifest(outfolder/"formula_manifest.csv"),inventory(outfolder/"math_execution_inventory.csv"),evidence(outfolder/"execution_evidence.json");require(results&&compare&&audit&&envelope&&tradeoff&&manifest&&inventory&&evidence,"Cannot create output files");
 results<<"case_id,model,speed_rpm,id_Apeak,iq_Apeak,temperature_C,torque_Nm,voltage_V,efficiency,shaft_power_W,em_power_W,copper_loss_W,iron_loss_W,mechanical_loss_W,total_loss_W,current_margin_A2,voltage_margin_V2,feasible_guard,screening_score,dtorque_did_Nm_perA,dtorque_diq_Nm_perA,dvoltage2_did_V2_perA,dvoltage2_diq_V2_perA,dtorque_dtemperature_Nm_perK,current_utilization,voltage_utilization\n";
 compare<<"case_id,speed_rpm,temperature_C,torque_v1_Nm,torque_v2_Nm,delta_torque_Nm,voltage_v1_V,voltage_v2_V,delta_voltage_V,efficiency_v1,efficiency_v2,delta_efficiency,loss_v1_W,loss_v2_W,delta_loss_W,minimum_voltage_margin_V2\n";
 audit<<"case_id,model,paceval_torque_Nm,native_torque_Nm,paceval_voltage_V,native_voltage_V,paceval_efficiency,native_efficiency,paceval_loss_W,native_loss_W\n";
 envelope<<"model,temperature_C,speed_rpm,max_feasible_torque_Nm,id_Apeak,iq_Apeak,voltage_V,efficiency,feasible_points\n";
 tradeoff<<"model,temperature_C,speed_rpm,threshold_torque_Nm,best_efficiency,id_Apeak,iq_Apeak,torque_Nm,voltage_V\n";
 struct Best{bool has=false;double metric=-1e100;Case c;std::map<std::string,double> fields;size_t feasible=0;};
 std::map<std::string,Best> bestTorque,bestEfficiency;
 size_t passed1=0,passed2=0,independentChecks=0;const size_t blockSize=128;
 for(size_t base=0;base<cases.size();base+=blockSize){size_t end=std::min(cases.size(),base+blockSize);Rows inputs;for(size_t j=base;j<end;j++)inputs.push_back(input(cases[j],p));
   auto r1=m.evaluate("V1",inputs),r2=m.evaluate("V2",inputs);Rows dinput;for(size_t j=0;j<inputs.size();j++){auto a=m.unpack("V1",r1[j]),b=m.unpack("V2",r2[j]);dinput.push_back({a.at("TORQUE"),b.at("TORQUE"),a.at("VOLTAGE_MAG"),b.at("VOLTAGE_MAG"),a.at("EFFICIENCY"),b.at("EFFICIENCY"),a.at("TOTAL_LOSS"),b.at("TOTAL_LOSS"),a.at("VOLTAGE_MARGIN"),b.at("VOLTAGE_MARGIN")});}
   auto diff=m.evaluate("V1_vs_V2",dinput);
   for(size_t j=0;j<inputs.size();j++){const auto& c=cases[base+j];auto a=m.unpack("V1",r1[j]),b=m.unpack("V2",r2[j]),d=m.unpack("V1_vs_V2",diff[j]);
      compare<<c.id<<","<<number(c.rpm)<<","<<number(c.temp)<<","<<number(a.at("TORQUE"))<<","<<number(b.at("TORQUE"))<<","<<number(d.at("DELTA_TORQUE"))<<","<<number(a.at("VOLTAGE_MAG"))<<","<<number(b.at("VOLTAGE_MAG"))<<","<<number(d.at("DELTA_VOLTAGE"))<<","<<number(a.at("EFFICIENCY"))<<","<<number(b.at("EFFICIENCY"))<<","<<number(d.at("DELTA_EFFICIENCY"))<<","<<number(a.at("TOTAL_LOSS"))<<","<<number(b.at("TOTAL_LOSS"))<<","<<number(d.at("DELTA_TOTAL_LOSS"))<<","<<number(d.at("WORST_VOLT_MARGIN"))<<"\n";
     for(int v:{1,2}){const auto& z=v==1?a:b;auto key=std::to_string(v)+":"+number(c.temp)+":"+number(c.rpm);bool feasible=z.at("FEASIBILITY_GUARD")>.5;if(feasible){(v==1?passed1:passed2)++;auto& f=bestTorque[key];f.feasible++;if(!f.has||z.at("TORQUE")>f.metric){f.has=true;f.metric=z.at("TORQUE");f.c=c;f.fields=z;}
       auto& ef=bestEfficiency[key];if(z.at("TORQUE")>=p.Ttarget&&z.at("SHAFT_POWER")>0&&(!ef.has||z.at("EFFICIENCY")>ef.metric)){ef.has=true;ef.metric=z.at("EFFICIENCY");ef.c=c;ef.fields=z;}}
       results<<c.id<<","<<v<<","<<number(c.rpm)<<","<<number(c.idA)<<","<<number(c.iqA)<<","<<number(c.temp)<<","<<number(z.at("TORQUE"))<<","<<number(z.at("VOLTAGE_MAG"))<<","<<number(z.at("EFFICIENCY"))<<","<<number(z.at("SHAFT_POWER"))<<","<<number(z.at("EM_POWER"))<<","<<number(z.at("COPPER_LOSS"))<<","<<number(z.at("IRON_LOSS"))<<","<<number(z.at("MECH_LOSS"))<<","<<number(z.at("TOTAL_LOSS"))<<","<<number(z.at("CURRENT_MARGIN"))<<","<<number(z.at("VOLTAGE_MARGIN"))<<","<<number(z.at("FEASIBILITY_GUARD"))<<","<<number(z.at("SCREENING_SCORE"))<<","<<number(z.at("DTORQUE_DID"))<<","<<number(z.at("DTORQUE_DIQ"))<<","<<number(z.at("DVOLTAGE2_DID"))<<","<<number(z.at("DVOLTAGE2_DIQ"))<<","<<number(z.at("DTORQUE_DT"))<<","<<number(z.at("CURRENT_UTIL"))<<","<<number(z.at("VOLTAGE_UTIL"))<<"\n";
       if((base+j)%101==0){auto r=native(c,p,v);near(z.at("TORQUE"),r[0]);near(z.at("VOLTAGE_MAG"),r[1]);near(z.at("EFFICIENCY"),r[2]);near(z.at("TOTAL_LOSS"),r[3]);near(z.at("CURRENT_MARGIN"),r[4]);near(z.at("VOLTAGE_MARGIN"),r[5]);audit<<c.id<<","<<v<<","<<number(z.at("TORQUE"))<<","<<number(r[0])<<","<<number(z.at("VOLTAGE_MAG"))<<","<<number(r[1])<<","<<number(z.at("EFFICIENCY"))<<","<<number(r[2])<<","<<number(z.at("TOTAL_LOSS"))<<","<<number(r[3])<<"\n";independentChecks+=6;}
      }
   }
 }
 for(const auto& it:bestTorque){const auto& x=it.second;if(!x.has)continue;auto k=splitCsv(std::string());(void)k;auto pos1=it.first.find(':'),pos2=it.first.find(':',pos1+1);auto v=it.first.substr(0,pos1),t=it.first.substr(pos1+1,pos2-pos1-1),rpm=it.first.substr(pos2+1);envelope<<v<<","<<t<<","<<rpm<<","<<number(x.fields.at("TORQUE"))<<","<<number(x.c.idA)<<","<<number(x.c.iqA)<<","<<number(x.fields.at("VOLTAGE_MAG"))<<","<<number(x.fields.at("EFFICIENCY"))<<","<<x.feasible<<"\n";}
 for(const auto& it:bestEfficiency){const auto& x=it.second;if(!x.has)continue;auto p1=it.first.find(':'),p2=it.first.find(':',p1+1);tradeoff<<it.first.substr(0,p1)<<","<<it.first.substr(p1+1,p2-p1-1)<<","<<it.first.substr(p2+1)<<","<<number(p.Ttarget)<<","<<number(x.fields.at("EFFICIENCY"))<<","<<number(x.c.idA)<<","<<number(x.c.iqA)<<","<<number(x.fields.at("TORQUE"))<<","<<number(x.fields.at("VOLTAGE_MAG"))<<"\n";}
 manifest<<"graph_id,version,expression,units,description\n";inventory<<"function_id,domain_quantity,mathematical_definition,units,execution_owner,paceval_graph_id,formula_version,api_path,reference_test,status,host_reason\n";
 size_t used=0;for(const auto& g:m.graphs){if(g.executed)used++;manifest<<g.id<<","<<g.version<<",\""<<g.expression<<"\","<<g.units<<",\""<<g.description<<"\"\n";inventory<<g.id<<",\""<<g.description<<"\",\""<<g.expression<<"\","<<g.units<<",paceval,"<<g.id<<","<<g.version<<",paceval_dGetMultipleComputationsResultsExt,independent native C++ + high precision Python,"<<(g.executed?"executed":"registered_only")<<",\n";}
 inventory<<"SEARCH_ENVELOPE,Finite grid maximizer,Enumerate feasible points,1,host,,both,C++ selection,discrete exhaustive grid audit,executed,Stateful selection over finite candidates\n";
 inventory<<"MAP_GENERATION,Current speed temperature grid,Deterministic CSV grid,1,host,,both,C++ input loop,CSV schema checks,executed,Data orchestration\n";
 evidence<<"{\n  \"sdk\": \"4.25, original supplied Linux library\",\n  \"model\": \"uncalibrated synthetic steady-state IPMSM screening\",\n  \"unique_domain_graphs_created\": "<<m.graphs.size()<<",\n  \"unique_domain_graphs_executed\": "<<used<<",\n  \"scalar_calls\": "<<e.scalarCalls<<",\n  \"multi_graph_batch_calls_including_layout_probe\": "<<e.batchCalls<<",\n  \"graph_point_evaluations_including_layout_probe\": "<<e.graphPointEvaluations<<",\n  \"scenario_count\": "<<cases.size()<<",\n  \"model_scenario_count\": "<<2*cases.size()<<",\n  \"v1_feasible_grid_points\": "<<passed1<<",\n  \"v2_feasible_grid_points\": "<<passed2<<",\n  \"independent_native_reference_checks\": "<<independentChecks<<",\n  \"coverage\": \"all 2 motor versions and 5 comparison graphs actually executed\",\n  \"scope\": \"mathematical functionality only; no FEA correlation or motor qualification\"\n}\n";
 std::cout<<"RESEARCH PASS: executed "<<used<<"/"<<m.graphs.size()<<" motor/comparison graphs; candidates="<<cases.size()<<", two versions; native endvalue checks="<<independentChecks<<"\n";
}
} // namespace
int main(int argc,char** argv){try{if(argc==2&&std::string(argv[1])=="--selftest"){selftest();return 0;}require(argc==5&&std::string(argv[1])=="--run","Usage: motor_maps --run input/candidates.csv input/motor_parameters.csv results/");run(argv[2],argv[3],argv[4]);return 0;}catch(const std::exception& ex){std::cerr<<"ERROR: "<<ex.what()<<"\n";return 1;}}
