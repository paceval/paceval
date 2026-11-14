// WP24: hydrogen compression and lumped storage screening, C++17 / original paceval SDK.
// SYNTHETIC ideal-gas assumptions. NOT a pressure-vessel, fueling, or safety qualification model.
#include "paceval_main.h"
#include <algorithm>
#include <array>
#include <cmath>
#include <cstdint>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <iomanip>
#include <map>
#include <regex>
#include <set>
#include <sstream>
#include <stdexcept>
#include <string>
#include <vector>
namespace fs=std::filesystem;
static void must(bool ok,const std::string& msg){if(!ok)throw std::runtime_error(msg);}
static constexpr int NV=31;
enum{PIN=0,POUT,TIN,ETA,GAMMA,CP,MDOT,COOL,COOLEFF,TLIM,PLIM,WMAX,CV,TMASS,TTANK,AMB,TFILL,DT,GASR,VOL,UA,NSTAGE,ISTAGE,PSTART,PEND,TANKLIM,VESSELLIM,COOLMAX,ACCPOWER,ACCCOOL,PZERO};
static const char* NAMES="pin pout tin eta gamma cp mdot cool cooleff tlim plim wmax cv tmass ttank amb tfill dt gasr vol ua nstage istage pstart pend tanklim vessellim coolmax accpower acccool pzero";
using Row=std::array<double,NV>;
struct Engine{
 std::vector<PACEVAL_HANDLE> owned;std::set<PACEVAL_HANDLE> used;uint64_t batches=0,scalars=0,outputs=0;
 Engine(){must(paceval_InitializeLibrary(nullptr),"Cannot initialize real paceval shared library");}
 ~Engine(){for(auto h:owned)paceval_DeleteComputation(h);paceval_FreeLibrary();}
 PACEVAL_HANDLE graph(const std::string& s){PACEVAL_HANDLE h=paceval_CreateComputation(s.c_str(),NV,NAMES,false,nullptr);must(h!=nullptr,"Null paceval handle");if(paceval_GetIsError(h)){char a[2500]={},b[2500]={};paceval_CreateErrorInformationText(h,a,b);paceval_DeleteComputation(h);throw std::runtime_error("Graph creation: "+s.substr(0,110)+" "+a+" "+b);}owned.push_back(h);return h;}
 double scalar(PACEVAL_HANDLE h,const Row& r){double v=paceval_dGetComputationResult(h,const_cast<double*>(r.data()),nullptr,nullptr);must(!paceval_GetIsError(h)&&std::isfinite(v),"paceval scalar error");scalars++;outputs++;used.insert(h);return v;}
 std::vector<double> batch(const std::vector<PACEVAL_HANDLE>& hs,const std::vector<Row>& rows){must(!hs.empty()&&!rows.empty(),"Empty paceval batch");std::vector<double> in;in.reserve(rows.size()*NV);for(const auto& r:rows)for(double v:r){must(std::isfinite(v),"nonfinite graph input");in.push_back(v);}std::vector<double> out(rows.size()*hs.size());std::vector<int> err(out.size(),-1);auto copy=hs;bool failed=paceval_dGetMultipleComputationsResultsExt(copy.data(),(unsigned long)hs.size(),in.data(),(unsigned long)rows.size(),out.data(),nullptr,nullptr,err.data());must(!failed,"paceval batch evaluation failed");for(size_t i=0;i<out.size();i++)must(err[i]==PACEVAL_ERR_NO_ERROR&&std::isfinite(out[i]),"paceval graph batch output error: "+std::to_string(i)+" "+std::to_string(err[i]));for(auto h:hs)used.insert(h);batches++;outputs+=out.size();return out;}
 double number(const std::string& txt)const{static const std::regex literal(R"(^[+-]?(?:[0-9]+(?:\.[0-9]*)?|\.[0-9]+)(?:[eE][+-]?[0-9]+)?$)");must(std::regex_match(txt,literal),"Non-literal numeric CSV value rejected: "+txt);int err=-1;long at=-1;double v=paceval_dConvertStringToFloat(txt.c_str(),&err,&at,false,nullptr,nullptr);must(err==PACEVAL_ERR_NO_ERROR&&std::isfinite(v),"paceval parsing error at "+std::to_string(at));return v;}
 std::string format(double val)const{must(std::isfinite(val),"nonfinite CSV output");char buf[512]={};int result=paceval_dConvertFloatToString(buf,val);must(result>0&&buf[0],"paceval formatting failed");return std::string(buf);}
};
struct Graph{std::string name,formula,version;PACEVAL_HANDLE h;};
using Graphs=std::map<std::string,Graph>;
using Def=std::map<std::string,std::string>;
static Graphs make(Engine& e,const Def& ds,const std::string& version){Graphs out;for(auto& [key,formula]:ds)out.emplace(key,Graph{key,formula,version,e.graph(formula)});return out;}
static std::vector<PACEVAL_HANDLE> handles(const Graphs& g){std::vector<PACEVAL_HANDLE> h;for(auto& [k,x]:g)h.push_back(x.h);return h;}
static std::map<std::string,size_t> positions(const Graphs& g){std::map<std::string,size_t> idx;size_t n=0;for(auto& [k,x]:g)idx[k]=n++;return idx;}
static std::string eta_expr(int v){if(v==1)return "eta";return "(eta-0.027*sqr(pout/pin-2.5)/(1+sqr(pout/pin-2.5))-0.00016*(tin-300))";}
static Def compressor(int v){std::string ee="("+eta_expr(v)+")",xx="((gamma-1)/(gamma*"+ee+"))";
 std::string tt="(tin*(pout/pin)^"+xx+")",ww="(cp*("+tt+"-tin)/1000)",pw="(mdot*"+ww+")",tc="(cool+(1-cooleff)*("+tt+"-cool))",qc="(mdot*cp*("+tt+"-"+tc+")/1000)";
 std::string de=v==1?"0":"(-0.027*2*(pout/pin-2.5)/(pin*sqr(1+sqr(pout/pin-2.5))))";
 std::string dd="("+tt+"*("+xx+"/pout-ln(pout/pin)*(gamma-1)/(gamma*sqr("+ee+"))*"+de+"))";
 return {{"effective_polytropic_efficiency",ee},{"polytropic_exponent",xx},{"stage_outlet_temperature_K",tt},{"specific_work_kJkg",ww},{"stage_power_kW",pw},{"intercooler_outlet_K",tc},{"cooling_duty_kW",qc},{"outlet_temperature_margin_K","(tlim-"+tt+")"},{"outlet_pressure_margin_bar","(plim-pout)"},{"compressor_power_margin_kW","(wmax-"+pw+")"},{"cooler_duty_margin_kW","(coolmax-"+qc+")"},{"temperature_pressure_sensitivity_Kbar",dd},{"temperature_efficiency_sensitivity_K","(-"+tt+"*ln(pout/pin)*(gamma-1)/(gamma*sqr("+ee+")))"},{"cumulative_power_kW","(accpower+"+pw+")"},{"cumulative_cooling_kW","(acccool+"+qc+")"},{"stage_valid","((("+tt+"<=tlim) AND ("+pw+"<=wmax)) AND ((pout<=plim) AND ("+qc+"<=coolmax)))"},{"screening_score","(0.45*"+pw+"/wmax+0.25*"+tt+"/tlim+0.20*"+qc+"/coolmax+0.10*pout/plim)"}};
}
static Def storage(){std::string sl="((mdot*(cp*tfill-cv*ttank)-ua*(ttank-amb))/(tmass*cv))";
 std::string next="(ttank+dt*"+sl+")",mn="(tmass+mdot*dt)",pn="("+mn+"*gasr*"+next+"/(vol*100000))";
 return {{"initial_tank_mass_kg","(pzero*100000*vol/(gasr*ttank))"},{"storage_temperature_slope_Ks",sl},{"next_storage_temperature_K",next},{"next_storage_mass_kg",mn},{"next_storage_pressure_bar",pn},{"storage_temperature_margin_K","(tanklim-"+next+")"},{"storage_pressure_margin_bar","(vessellim-"+pn+")"},{"storage_hydrogen_enthalpy_kW","(mdot*cp*tfill/1000)"},{"storage_wall_heat_transfer_kW","(ua*(ttank-amb)/1000)"},{"storage_min_normalized_margin","(((tanklim-"+next+")/tanklim) min ((vessellim-"+pn+")/vessellim))"},{"storage_valid","(("+next+"<=tanklim) AND ("+pn+"<=vessellim))"},{"storage_temperature_UA_sensitivity","(-dt*(ttank-amb)/(tmass*cv))"},{"storage_pressure_UA_sensitivity","(-"+mn+"*gasr*dt*(ttank-amb)/(vol*100000*tmass*cv))"},{"storage_screening_score","(0.5*"+next+"/tanklim+0.5*"+pn+"/vessellim)"}};
}
static uint64_t scramble(uint64_t x){x^=x>>30;x*=UINT64_C(0xbf58476d1ce4e5b9);x^=x>>27;x*=UINT64_C(0x94d049bb133111eb);return x^(x>>31);}
static double random01(uint64_t v){return double(scramble(v)>>11)/9007199254740992.0;}
static Row sample(size_t k){Row r{};r.fill(0);r[PSTART]=18+22*random01(k*37+5);r[PEND]=120+135*random01(k*71+8);r[PIN]=r[PSTART];r[POUT]=r[PEND];r[TIN]=285+35*random01(k*179+19);r[ETA]=.75+.095*random01(k*137+26);r[GAMMA]=1.405;r[CP]=14300;r[CV]=10176;r[MDOT]=.009+.029*random01(k*31+23);r[COOL]=287+15*random01(k*49+7);r[COOLEFF]=.60+.34*random01(k*17+33);r[TLIM]=430+35*random01(k*97+35);r[PLIM]=275;r[WMAX]=75;r[COOLMAX]=70;r[NSTAGE]=1+int(k%4);r[ISTAGE]=1;r[TANKLIM]=365;r[VESSELLIM]=255;r[AMB]=295;r[TFILL]=305;r[DT]=5;r[GASR]=4124;r[VOL]=7;r[UA]=180;r[TTANK]=296;r[TMASS]=44;r[PZERO]=80;return r;}
static void validate_stage(const Row& r){for(double d:r)must(std::isfinite(d),"non-finite stage input");must(r[PSTART]>0&&r[PIN]>0&&r[POUT]>=r[PIN]&&r[PEND]>=r[PSTART]&&r[PEND]<=275,"invalid pressure domain");must(r[TIN]>=270&&r[TIN]<=900&&r[ETA]>.50&&r[ETA]<1&&r[GAMMA]>1&&r[GAMMA]<1.7&&r[CP]>1000,"invalid gas properties");must(r[COOL]>=270&&r[COOLEFF]>=0&&r[COOLEFF]<=1&&r[MDOT]>0&&r[NSTAGE]>=1&&r[NSTAGE]<=4,"invalid cooling/stages");}
static std::vector<std::string> fields(const std::string& line){std::vector<std::string> v;std::stringstream in(line);std::string s;while(std::getline(in,s,','))v.push_back(s);if(!line.empty()&&line.back()==',')v.push_back("");return v;}
static const int CSV_COLS[]={PSTART,PEND,TIN,ETA,GAMMA,CP,MDOT,COOL,COOLEFF,TLIM,PLIM,WMAX,COOLMAX,NSTAGE};
static void save_input(const Engine& e,const fs::path& p,int n){std::ofstream f(p);must(bool(f),"cannot write scenario inputs");f<<"id,pstart_bar,pend_bar,tin_K,eta_poly,gamma,cp_JkgK,mdot_kgs,cooltemp_K,intercooler_effectiveness,stage_T_limit_K,pressure_limit_bar,stage_power_limit_kW,stage_cool_limit_kW,stages\n";
 for(int i=0;i<n;i++){Row r=sample(i);f<<i;for(int k:CSV_COLS)f<<","<<e.format(r[k]);f<<"\n";}}
static std::vector<Row> load_input(const Engine& e,const fs::path& p){std::ifstream f(p);must(bool(f),"scenario input CSV is missing");std::string s;must(bool(std::getline(f,s))&&fields(s).size()==15,"CSV input header invalid");std::vector<Row> out;int expected=0;while(std::getline(f,s)){if(s.empty())continue;auto parts=fields(s);must(parts.size()==15,"CSV field count invalid");must(parts[0]==std::to_string(expected++),"CSV row IDs not sequential");Row r=sample(out.size());for(int k=0;k<14;k++)r[CSV_COLS[k]]=e.number(parts[k+1]);must(std::round(r[NSTAGE])==r[NSTAGE],"Non-integral stage count");r[PIN]=r[PSTART];r[POUT]=r[PEND];validate_stage(r);out.push_back(r);}return out;}
static bool near(double a,double b,double tol=3e-9){return std::isfinite(a)&&std::isfinite(b)&&std::abs(a-b)<=tol*std::max(1.,std::abs(b));}
static void verify(double a,double b,const std::string& s,double tol=3e-9){must(near(a,b,tol),"Independent numerical comparison failed: "+s+" value="+std::to_string(a)+" expected="+std::to_string(b));}
static double native_eta(const Row& r,int v){if(v==1)return r[ETA];double z=r[POUT]/r[PIN]-2.5;return r[ETA]-.027*z*z/(1+z*z)-.00016*(r[TIN]-300);}
static double native_Tout(const Row& r,int v){double et=native_eta(r,v);return r[TIN]*std::pow(r[POUT]/r[PIN],(r[GAMMA]-1)/(r[GAMMA]*et));}
static double native_cool(const Row& r,int v){return r[COOL]+(1-r[COOLEFF])*(native_Tout(r,v)-r[COOL]);}
static double native_storage_slope(const Row& r){return (r[MDOT]*(r[CP]*r[TFILL]-r[CV]*r[TTANK])-r[UA]*(r[TTANK]-r[AMB]))/(r[TMASS]*r[CV]);}
static void record_formula(std::ofstream& f,const Graphs& gs){for(auto& [k,g]:gs){std::string s=g.formula;for(char& c:s)if(c=='"')c='\'';f<<g.version<<","<<g.name<<",\""<<s<<"\",paceval_dGetMultipleComputationsResultsExt,executed\n";}}
static void selftest(Engine& e){Row r=sample(0);r[PIN]=20;r[POUT]=50;r[TIN]=300;auto p=e.graph("(pin+pout)");verify(e.scalar(p,r),70,"scalar sanity");
 auto batch=e.batch({e.graph("pin*2"),e.graph("pout+5")},{r,r});verify(batch[0],40,"batch graph-major 1");verify(batch[2],55,"batch graph-major 2");
 std::vector<std::pair<std::string,double>> cases={{"((-1) % 10)",-1},{"((-1) mod 10)",9},{"(4 min 5)",4},{"(4 max 5)",5},{"((pin<pout) AND (pout<=50))",1},{"((pin=20) OR (pout<>50))",1},{"NOT((pin>pout))",1},{"((pin>=20) AND (pout>50))",0}};
 for(auto [s,expected]:cases)verify(e.scalar(e.graph(s),r),expected,"operator test: "+s);
 for(const std::string& txt:{"17.25","-4.5","2.75e-4","0","1e10"}){double z=e.number(txt);must(std::isfinite(z),"numeric conversion");(void)e.format(z);}for(const std::string& txt:{"1+2","sqrt(2)","NaN","","1,5","4.3 bar"}){bool denied=false;try{e.number(txt);}catch(...){denied=true;}must(denied,"unsafe numeric literal accepted");}
 for(int v=1;v<=2;v++){auto c=make(e,compressor(v),"SELFTEST");auto k=e.scalar(c.at("stage_outlet_temperature_K").h,r);verify(k,native_Tout(r,v),"polytropic formula unit");
     Row limit=r;limit[POUT]=limit[PIN];verify(e.scalar(c.at("stage_outlet_temperature_K").h,limit),limit[TIN],"unity pressure ratio outlet temperature");verify(e.scalar(c.at("specific_work_kJkg").h,limit),0,"unity pressure ratio work");}
 Row bad=r;bad[ETA]=0;bool denied=false;try{validate_stage(bad);}catch(...){denied=true;}must(denied,"Invalid efficiency must be rejected");
 std::cout<<"PASS original SDK scalar, batch, operators, conversions, and synthetic compression unit tests\n";
}
static void write_inventory(const fs::path& folder,const Graphs& a,const Graphs& b,const Graphs& c,const Graphs& p){
 std::ofstream reg(folder/"formula_registry.csv"),inv(folder/"math_execution_inventory.csv");must(bool(reg)&&bool(inv),"Cannot create graph inventory");reg<<"version,graph_id,formula,api_path,status\n";
 inv<<"function_id,domain_quantity,mathematical_definition,units,execution_owner,paceval_graph_id,formula_version,api_path,reference_test,status,host_reason\n";
 for(const Graphs* d:{&a,&b,&c,&p}){for(auto& [k,g]:*d){std::string s=g.formula;for(char& cc:s)if(cc=='"')cc='\'';reg<<g.version<<","<<g.name<<",\""<<s<<"\",paceval_dGetMultipleComputationsResultsExt,executed\n";inv<<g.name<<","<<g.name<<",\""<<s<<"\",defined_in_source,paceval,"<<g.name<<","<<g.version<<",paceval_batch_or_scalar,independent_CPP,executed,\n";}}
 inv<<"stage_iteration,stage_solver_and_state_management,stateful_loop,NA,host,,both,C++_host,independent_CPP,executed,stage_count_iteration\n";
 inv<<"storage_euler_stepping,update_state_using_paceval_outputs,stateful_loop,NA,host,,both,C++_host,independent_CPP,executed,integrator_orchestration\n";
}
static void generate_and_run(Engine& e,int number,int profiles,const fs::path& root){must(number>=100&&number<=1000000&&profiles>=4&&profiles<=80,"invalid experimental size");fs::create_directories(root);
 const auto input=root/"synthetic_compressor_scenarios.csv";save_input(e,input,number);auto source=load_input(e,input);must(source.size()==size_t(number),"CSV reread failed");
 auto ga=make(e,compressor(1),"V1");auto gb=make(e,compressor(2),"V2");auto stor=make(e,storage(),"COMMON_STORAGE");auto pg=make(e,{{"stage_pressure_target_bar","(pstart*(pend/pstart)^(istage/nstage))"}},"COMMON_PRESSURE");
 std::ofstream data(root/"compression_scenarios.csv"),trace(root/"stage_trace_samples.csv"),ss(root/"compression_summary.csv"),audit(root/"independent_audit_samples.csv"),tank(root/"storage_profiles.csv"),ts(root/"storage_summary.csv");
 must(bool(data)&&bool(trace)&&bool(ss)&&bool(audit)&&bool(tank)&&bool(ts),"Cannot open result CSV");
 data<<"id,version,stages,pressure_in_bar,pressure_out_bar,initial_temperature_K,final_conditioned_temperature_K,total_power_kW,total_cooling_kW,maximum_stage_temperature_K,minimum_stage_temperature_margin_K,minimum_cooler_margin_kW,screening_score,status\n";
 trace<<"id,version,stage,pin_bar,pout_bar,tin_K,tout_K,intercooled_K,power_kW,cooling_kW,stage_T_margin_K,stage_valid,eta_effective,dT_dpout_Kbar,dT_detaeff_K\n";
 ss<<"version,cases,accept,review,reject,average_specific_work_kJkg,average_max_stage_T_K,average_intercooling_kW\n";
 audit<<"id,version,quantity,paceval_value,native_reference,absolute_difference\n";
 tank<<"version,profile,step,time_s,mass_kg,tank_T_K,pressure_bar,temperature_margin_K,pressure_margin_bar,valid,energy_balance_residual_Js\n";
 ts<<"version,profile,steps,initial_pressure_bar,final_pressure_bar,initial_temperature_K,final_temperature_K,max_temperature_K,min_temperature_margin_K,min_pressure_margin_bar,accepted_steps,rejected_steps\n";
 auto gp=pg.at("stage_pressure_target_bar").h;uint64_t referenceChecks=0,processed=0,stageEvaluations=0;int accepted[2]={0,0},review[2]={0,0},rejected[2]={0,0};double totalSpecific[2]={0,0},totalPeak[2]={0,0},totalCooling[2]={0,0};
 const size_t CHUNK=256;
 for(int ver=1;ver<=2;ver++){
  const auto& g=(ver==1?ga:gb);auto names=positions(g);auto hs=handles(g);
  for(size_t start=0;start<source.size();start+=CHUNK){size_t sz=std::min(CHUNK,source.size()-start);std::vector<Row> rows(source.begin()+start,source.begin()+start+sz);
   std::vector<double> maximum(sz,0),minMargin(sz,1e9),minCool(sz,1e9),score(sz,0);std::vector<bool> good(sz,true);
   for(int step=1;step<=4;step++){
    std::vector<Row> active;std::vector<size_t> position;for(size_t j=0;j<sz;j++)if(int(rows[j][NSTAGE])>=step){Row r=rows[j];r[ISTAGE]=step;active.push_back(r);position.push_back(j);}
    if(active.empty())continue;
    auto pvalue=e.batch({gp},active);for(size_t i=0;i<active.size();i++){active[i][POUT]=pvalue[i];validate_stage(active[i]);double pref=active[i][PSTART]*std::pow(active[i][PEND]/active[i][PSTART],double(step)/active[i][NSTAGE]);verify(pvalue[i],pref,"pressure schedule");referenceChecks++;}
    auto out=e.batch(hs,active);size_t n=active.size();auto val=[&](const std::string& k,size_t i){return out.at(names.at(k)*n+i);};
    for(size_t i=0;i<n;i++){auto& r=active[i];size_t j=position[i];size_t id=start+j;double tout=val("stage_outlet_temperature_K",i),cooled=val("intercooler_outlet_K",i),work=val("specific_work_kJkg",i),power=val("stage_power_kW",i),cooling=val("cooling_duty_kW",i),eta=val("effective_polytropic_efficiency",i),tmargin=val("outlet_temperature_margin_K",i),cmargin=val("cooler_duty_margin_kW",i);
     double tref=native_Tout(r,ver),cref=native_cool(r,ver),workref=r[CP]*(tref-r[TIN])/1000,powerref=r[MDOT]*workref,qref=r[MDOT]*r[CP]*(tref-cref)/1000;
     verify(eta,native_eta(r,ver),"eta");verify(tout,tref,"stage T");verify(cooled,cref,"intercooling");verify(work,workref,"specific work");verify(power,powerref,"power");verify(cooling,qref,"cooling");verify(tmargin,r[TLIM]-tref,"temperature margin");verify(cmargin,r[COOLMAX]-qref,"cooling margin");verify(val("cumulative_power_kW",i),r[ACCPOWER]+powerref,"cumulative power");verify(val("cumulative_cooling_kW",i),r[ACCCOOL]+qref,"cumulative cooling");
     bool local=(tout<=r[TLIM]&&power<=r[WMAX]&&r[POUT]<=r[PLIM]&&cooling<=r[COOLMAX]);verify(val("stage_valid",i),local?1.:0.,"logical guard");
     if(id%std::max(1,number/320)==0){Row d=r;double h=1e-4;d[POUT]=r[POUT]+h;double plus=native_Tout(d,ver);d[POUT]=r[POUT]-h;double minus=native_Tout(d,ver);double slope=(plus-minus)/(2*h);verify(val("temperature_pressure_sensitivity_Kbar",i),slope,"sensitivity to stage pressure",3e-6);referenceChecks++;}
     referenceChecks+=11;stageEvaluations++;maximum[j]=std::max(maximum[j],tout);minMargin[j]=std::min(minMargin[j],tmargin);minCool[j]=std::min(minCool[j],cmargin);score[j]+=val("screening_score",i);good[j]=good[j]&&local;
     Row& dst=rows[j];dst[PIN]=r[POUT];dst[TIN]=cooled;dst[ACCPOWER]=val("cumulative_power_kW",i);dst[ACCCOOL]=val("cumulative_cooling_kW",i);
     if(id%std::max(1,number/320)==0){trace<<id<<','<<ver<<','<<step<<','<<e.format(r[PIN])<<','<<e.format(r[POUT])<<','<<e.format(r[TIN])<<','<<e.format(tout)<<','<<e.format(cooled)<<','<<e.format(power)<<','<<e.format(cooling)<<','<<e.format(tmargin)<<','<<e.format(local?1:0)<<','<<e.format(eta)<<','<<e.format(val("temperature_pressure_sensitivity_Kbar",i))<<','<<e.format(val("temperature_efficiency_sensitivity_K",i))<<'\n';}
     if(id%std::max(1,number/90)==0&&step==1){audit<<id<<','<<ver<<",stage_temperature,"<<e.format(tout)<<','<<e.format(tref)<<','<<e.format(std::abs(tout-tref))<<'\n';}
    }
   }
   for(size_t j=0;j<sz;j++){auto& r=rows[j];must(near(r[PIN],r[PEND],1e-10),"Final stage pressure does not match request");bool ok=good[j];std::string status=!ok?"REJECT":(minMargin[j]<18||minCool[j]<9?"REVIEW":"ACCEPT");if(status=="ACCEPT")accepted[ver-1]++;else if(status=="REVIEW")review[ver-1]++;else rejected[ver-1]++;
    data<<start+j<<','<<ver<<','<<int(r[NSTAGE])<<','<<e.format(r[PSTART])<<','<<e.format(r[PEND])<<','<<e.format(source[start+j][TIN])<<','<<e.format(r[TIN])<<','<<e.format(r[ACCPOWER])<<','<<e.format(r[ACCCOOL])<<','<<e.format(maximum[j])<<','<<e.format(minMargin[j])<<','<<e.format(minCool[j])<<','<<e.format(score[j])<<','<<status<<'\n';
    totalSpecific[ver-1]+=r[ACCPOWER]/r[MDOT];totalPeak[ver-1]+=maximum[j];totalCooling[ver-1]+=r[ACCCOOL];processed++;
   }
  }
  ss<<ver<<','<<number<<','<<accepted[ver-1]<<','<<review[ver-1]<<','<<rejected[ver-1]<<','<<e.format(totalSpecific[ver-1]/number)<<','<<e.format(totalPeak[ver-1]/number)<<','<<e.format(totalCooling[ver-1]/number)<<'\n';
 }
 // Rigid one-zone ideal-gas storage-screening exercise. Pressure and temperature are
 // advanced using quantities calculated in genuine paceval storage graphs.
 const auto stidx=positions(stor);const auto sth=handles(stor);uint64_t storageChecks=0,storageSteps=0;int invalidStorage=0;
 for(int ver=1;ver<=2;ver++){
  for(int b=0;b<profiles;b++){
   Row r=sample(size_t(b)*19+17);r[PSTART]=24;r[PEND]=210+12*random01(b*17+2);r[PIN]=r[PSTART];r[NSTAGE]=4;r[COOLEFF]=.68+.22*random01(b*9+21);r[COOL]=292+11*random01(b*7+3);r[MDOT]=.013+.017*random01(b*9+29);
   // Use the compressor's actual evaluated last-stage intercooler outlet as filling-gas temperature.
   auto& comp=(ver==1?ga:gb);for(int k=1;k<=4;k++){r[ISTAGE]=k;r[POUT]=e.scalar(gp,r);double t=e.scalar(comp.at("stage_outlet_temperature_K").h,r);double cooled=e.scalar(comp.at("intercooler_outlet_K").h,r);verify(t,native_Tout(r,ver),"stored-profile feed stage");r[PIN]=r[POUT];r[TIN]=cooled;}
   r[TFILL]=r[TIN];r[PZERO]=78+22*random01(b*7+12);r[TTANK]=293+8*random01(b*11+7);r[AMB]=287+15*random01(b*23+4);r[TANKLIM]=314+30*random01(b*13+6);r[VESSELLIM]=112+58*random01(b*7+37);r[UA]=90+230*random01(b*5+10);r[DT]=4;r[VOL]=7.5;r[GASR]=4124;r[CV]=10176;r[CP]=14300;
   r[TMASS]=e.scalar(stor.at("initial_tank_mass_kg").h,r);double initialP=r[PZERO],initialT=r[TTANK],maxt=r[TTANK],mint=1e9,minp=1e9;int yes=0,no=0;
   for(int k=0;k<180;k++){
    auto outputs=e.batch(sth,{r});auto get=[&](const std::string& s){return outputs[stidx.at(s)];};
    double nativeSlope=native_storage_slope(r),nativeTemp=r[TTANK]+r[DT]*nativeSlope,nativeMass=r[TMASS]+r[MDOT]*r[DT],nativeP=nativeMass*r[GASR]*nativeTemp/(r[VOL]*100000);
    double tn=get("next_storage_temperature_K"),pn=get("next_storage_pressure_bar"),mn=get("next_storage_mass_kg");verify(tn,nativeTemp,"storage T");verify(pn,nativeP,"storage P");verify(mn,nativeMass,"storage M");verify(get("storage_temperature_slope_Ks"),nativeSlope,"storage dTdt");verify(get("storage_temperature_margin_K"),r[TANKLIM]-nativeTemp,"storage T guard");verify(get("storage_pressure_margin_bar"),r[VESSELLIM]-nativeP,"storage pressure guard");
    bool ok=tn<=r[TANKLIM]&&pn<=r[VESSELLIM];verify(get("storage_valid"),ok?1.:0.,"storage logical guard");double balance=r[TMASS]*r[CV]*((tn-r[TTANK])/r[DT])-(r[MDOT]*(r[CP]*r[TFILL]-r[CV]*r[TTANK])-r[UA]*(r[TTANK]-r[AMB]));verify(balance,0,"storage energy balance",1e-7);
    storageChecks+=8;storageSteps++;if(ok)yes++;else{no++;invalidStorage++;}maxt=std::max(maxt,tn);mint=std::min(mint,get("storage_temperature_margin_K"));minp=std::min(minp,get("storage_pressure_margin_bar"));
    tank<<ver<<','<<b<<','<<k<<','<<e.format((k+1)*r[DT])<<','<<e.format(mn)<<','<<e.format(tn)<<','<<e.format(pn)<<','<<e.format(get("storage_temperature_margin_K"))<<','<<e.format(get("storage_pressure_margin_bar"))<<','<<e.format(ok?1:0)<<','<<e.format(balance)<<'\n';
    r[TMASS]=mn;r[TTANK]=tn;
   }
   ts<<ver<<','<<b<<",180,"<<e.format(initialP)<<','<<e.format(r[TMASS]*r[GASR]*r[TTANK]/(r[VOL]*100000))<<','<<e.format(initialT)<<','<<e.format(r[TTANK])<<','<<e.format(maxt)<<','<<e.format(mint)<<','<<e.format(minp)<<','<<yes<<','<<no<<'\n';
  }
 }
 write_inventory(root,ga,gb,stor,pg);
 std::ofstream proof(root/"execution_evidence.json");must(bool(proof),"no execution manifest");proof<<"{\n  \"research\": \"WP24 Hydrogen Compression and Storage Thermal Envelope\",\n  \"sdk_mode\": \"original paceval local C++ SDK (no MCP)\",\n  \"model_versions\": 2,\n  \"compressor_scenarios_per_version\": "<<number<<",\n  \"compressor_model_cases\": "<<processed<<",\n  \"compressor_stage_visits\": "<<stageEvaluations<<",\n  \"storage_profiles_per_version\": "<<profiles<<",\n  \"storage_step_evaluations\": "<<storageSteps<<",\n  \"created_unique_graphs\": "<<e.owned.size()<<",\n  \"executed_unique_graphs\": "<<e.used.size()<<",\n  \"scalar_calls\": "<<e.scalars<<",\n  \"multi_graph_batch_calls\": "<<e.batches<<",\n  \"graph_point_evaluations\": "<<e.outputs<<",\n  \"independent_native_checks\": "<<(referenceChecks+storageChecks)<<",\n  \"storage_limit_exceedance_steps\": "<<invalidStorage<<",\n  \"v1_status\": {\"ACCEPT\": "<<accepted[0]<<", \"REVIEW\": "<<review[0]<<", \"REJECT\": "<<rejected[0]<<"},\n  \"v2_status\": {\"ACCEPT\": "<<accepted[1]<<", \"REVIEW\": "<<review[1]<<", \"REJECT\": "<<rejected[1]<<"}\n}\n";
 std::cout<<"PASS WP24 scenarios="<<number<<" model_cases="<<processed<<" stages="<<stageEvaluations<<" graphs="<<e.used.size()<<" graph_outputs="<<e.outputs<<" native_checks="<<(referenceChecks+storageChecks)<<" storage_steps="<<storageSteps<<"\n";
}
int main(int argc,char** argv){try{Engine e;std::string arg=argc>1?argv[1]:"--run";if(arg=="--selftest"){selftest(e);return 0;}must(arg=="--run","Use --run or --selftest");int n=argc>2?std::stoi(argv[2]):100000;int p=argc>3?std::stoi(argv[3]):16;fs::path out=argc>4?argv[4]:"results";generate_and_run(e,n,p,out);return 0;}catch(const std::exception& x){std::cerr<<"FAIL WP24: "<<x.what()<<"\n";return 1;}}
