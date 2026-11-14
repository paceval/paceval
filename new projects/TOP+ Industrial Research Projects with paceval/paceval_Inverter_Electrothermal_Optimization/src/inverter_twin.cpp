// WP03: Synthetic SiC inverter electrothermal digital twin, paceval execution.
// The genuine vendor SDK is in paceval_main.{h,cpp}; no mathematical mock is used.
// All production domain equations (loss, thermal residual and derivative, sensitivities,
// quantitative guards, transient state) are persistent paceval graphs.
// C++ controls root bracketing, steps, CSV schema, datasets and decisions.
#include "paceval_main.h"
#include <algorithm>
#include <array>
#include <cmath>
#include <cstddef>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <map>
#include <regex>
#include <set>
#include <sstream>
#include <stdexcept>
#include <string>
#include <vector>
namespace fs = std::filesystem;
static constexpr unsigned NV=11;
static constexpr char VARS[]="i v fs tamb rth tj ripple pmax tmax dt cth";
using Vec=std::array<double,NV>;
void check(bool ok,const std::string& msg){if(!ok)throw std::runtime_error(msg);}
std::vector<std::string> cols(const std::string& s){std::vector<std::string> r;std::stringstream z(s);std::string v;while(std::getline(z,v,','))r.push_back(v);if(!s.empty()&&s.back()==',')r.push_back("");return r;}
std::string trim(const std::string& s){auto i=s.find_first_not_of(" \t\r\n"),j=s.find_last_not_of(" \t\r\n");return i==std::string::npos?"":s.substr(i,j-i+1);}
class Engine {
  std::vector<PACEVAL_HANDLE> owned_;
  std::set<PACEVAL_HANDLE> executed_;
public:
  unsigned long long batchCalls=0,scalarCalls=0,graphPointEvaluations=0;
  Engine(){check(paceval_InitializeLibrary(nullptr),"paceval_InitializeLibrary failed");}
  ~Engine(){for(auto h:owned_)paceval_DeleteComputation(h);paceval_FreeLibrary();}
  Engine(const Engine&)=delete;Engine& operator=(const Engine&)=delete;
  double parse(const std::string& text)const{
    static const std::regex DEC(R"(^[+-]?(?:[0-9]+(?:\.[0-9]*)?|\.[0-9]+)(?:[eE][+-]?[0-9]+)?$)");
    const auto v=trim(text);
    check(std::regex_match(v,DEC),"Rejected nonliteral numeric CSV input: "+v);
    int err=-1;long pos=-1;
    const double d=paceval_dConvertStringToFloat(v.c_str(),&err,&pos,false,nullptr,nullptr);
    check(err==PACEVAL_ERR_NO_ERROR&&std::isfinite(d),"paceval_dConvertStringToFloat error at "+std::to_string(pos));
    return d;
  }
  std::string fmt(double d)const{
    check(std::isfinite(d),"Refusing non-finite CSV output");
    char b[512]={};int n=paceval_dConvertFloatToString(b,d);
    check(n>0&&b[0],"paceval_dConvertFloatToString failed");
    return b;
  }
  PACEVAL_HANDLE make(const std::string& expr){
    auto h=paceval_CreateComputation(expr.c_str(),NV,VARS,false,nullptr);
    check(h!=nullptr,"CreateComputation returned null");
    if(paceval_GetIsError(h)){
      char buf[512]={},more[512]={};paceval_CreateErrorInformationText(h,buf,more);
      paceval_DeleteComputation(h);throw std::runtime_error("Graph syntax: "+expr.substr(0,100)+" :: "+buf+" "+more);
    }
    owned_.push_back(h);return h;
  }
  std::vector<double> batch(const std::vector<PACEVAL_HANDLE>& h,const std::vector<Vec>& rows){
    check(!h.empty()&&!rows.empty(),"Empty graph batch");
    std::vector<double> values;values.reserve(rows.size()*NV);
    for(const auto& r:rows)for(double v:r){check(std::isfinite(v),"Non-finite graph input");values.push_back(v);}
    std::vector<double> out(rows.size()*h.size(),0.0);
    std::vector<int> err(out.size(),-222);
    auto handles=h;
    paceval_dGetMultipleComputationsResultsExt(handles.data(),static_cast<unsigned long>(h.size()),values.data(),static_cast<unsigned long>(rows.size()),out.data(),nullptr,nullptr,err.data());
    for(size_t k=0;k<out.size();++k)
      check(err[k]==PACEVAL_ERR_NO_ERROR&&std::isfinite(out[k]),"Graph cell error index "+std::to_string(k)+", error="+std::to_string(err[k]));
    ++batchCalls;graphPointEvaluations+=out.size();for(auto x:h)executed_.insert(x);
    return out; // Verified graph-major, not row-major.
  }
  double scalar(PACEVAL_HANDLE h,Vec r){
    double v=paceval_dGetComputationResult(h,r.data(),nullptr,nullptr);
    check(!paceval_GetIsError(h)&&std::isfinite(v),"Scalar paceval evaluation failed");
    ++scalarCalls;++graphPointEvaluations;executed_.insert(h);return v;
  }
  size_t created()const{return owned_.size();}
  size_t executed()const{return executed_.size();}
};
// Human-readable, stable formula IDs. Formula versions are independent graphs.
// Synthetic coefficients, NOT a characterized semiconductor device.
struct Graph {std::string id,version,units,expression;PACEVAL_HANDLE h=nullptr;};
std::map<std::string,std::string> formulas(int version){
  const std::string d="(tj-25)";
  const std::string r=version==1?"(0.018*(1+0.0038*"+d+"))":
                "(0.018*(1+0.0036*"+d+"+0.0000012*sqr("+d+")))";
  const std::string pc=version==1?"(sqr(i)*"+r+")":"((sqr(i)+sqr(ripple)/12)*"+r+")";
  const std::string ps=version==1?"(fs*0.0026*(v/800)*(i/100))":
   "(fs*(0.0026*(v/800)^1.04*(i/100)^1.06*(1+0.0009*"+d+")+0.00030*(v/800)*(i/100)*(1+0.0013*"+d+")))";
  const std::string dpdt=version==1?"(sqr(i)*0.018*0.0038)":
    "((sqr(i)+sqr(ripple)/12)*0.018*(0.0036+0.0000024*"+d+")+fs*(0.0026*(v/800)^1.04*(i/100)^1.06*0.0009+0.00030*(v/800)*(i/100)*0.0013))";
  const std::string dpdi=version==1?"(2*i*"+r+"+fs*0.0026*(v/800)/100)":
   "(2*i*"+r+"+fs*(0.0026*(v/800)^1.04*1.06*(i/100)^0.06/100*(1+0.0009*"+d+")+0.00030*(v/800)/100*(1+0.0013*"+d+")))";
  const std::string dpdf=version==1?"(0.0026*(v/800)*(i/100))":
   "(0.0026*(v/800)^1.04*(i/100)^1.06*(1+0.0009*"+d+")+0.00030*(v/800)*(i/100)*(1+0.0013*"+d+"))";
  const std::string pt="("+pc+"+"+ps+")";
  const std::string stability="(1-rth*"+dpdt+")";
  std::map<std::string,std::string> v;
  v["conduction_loss"]=pc;v["switching_loss"]=ps;v["total_loss"]=pt;
  v["thermal_residual"]="(tj-tamb-rth*"+pt+")";
  v["residual_derivative"]=stability;
  v["temperature_margin"]="(tmax-tj)";
  v["loss_margin"]="(pmax-"+pt+")";
  v["feedback_margin"]=stability;
  v["loss_sensitivity_current"]=dpdi;
  v["temperature_sensitivity_current"]="(rth*"+dpdi+"/"+stability+")";
  v["temperature_sensitivity_frequency"]="(rth*"+dpdf+"/"+stability+")";
  v["switching_share"]="("+ps+"/("+pt+" max 0.000000000001))"; // An explicitly defined zero-power regularizer.
  v["stress_score"]="(0.55*sqr("+pt+"/pmax)+0.45*sqr((tj-tamb)/(tmax-tamb)))";
  v["boolean_guard"]="(((tj <= tmax) AND ("+pt+" <= pmax)) AND ("+stability+" > 0))";
  v["thermal_step"]="(tj+dt*("+pt+"-(tj-tamb)/rth)/cth)";
  v["loss_energy_step"]="(dt*"+pt+")";
  return v;
}
struct Case{long id=0;double i=0,v=0,fs=0,tamb=0,rth=0,ripple=0,pmax=220,tmax=170;};
Vec row(const Case& c,double tj,double dt=0,double cth=60){return {c.i,c.v,c.fs,c.tamb,c.rth,tj,c.ripple,c.pmax,c.tmax,dt,cth};}
void validate_case(const Case& c){
  check(c.i>=0&&c.i<=180&&c.v>=350&&c.v<=1000&&c.fs>=0&&c.fs<=35000&&c.tamb>=-10&&c.tamb<=80&&
        c.rth>0&&c.rth<=.4&&c.ripple>=0&&c.ripple<=50&&c.pmax>0&&c.tmax>c.tamb,"Invalid synthetic scenario domain");
}
Case make_case(long k){
  Case c;c.id=k;c.i=double((k*31+17)%181);c.v=450+double((k*193+31)%451);
  c.fs=4000+double((k*1723+41)%22001);c.tamb=18+double((k*53+3)%44);
  const double cooling[6]={.09,.12,.16,.20,.26,.33};c.rth=cooling[(k/17)%6];
  c.ripple=double((k*19+7)%31);c.pmax=220;c.tmax=170;
  if(k%4501==0)c.i=0;
  if(k%5503==0)c.fs=0;
  return c;
}
void generate_inputs(const Engine& engine,const fs::path& csv,long n){
  fs::create_directories(csv.parent_path());std::ofstream o(csv);check(bool(o),"Cannot create input CSV");
  o<<"scenarioId,currentA,dcVoltageV,frequencyHz,ambientC,rthKperW,rippleA,lossLimitW,junctionLimitC\n";
  for(long k=0;k<n;k++){
    auto c=make_case(k);
    o<<k<<','<<engine.fmt(c.i)<<','<<engine.fmt(c.v)<<','<<engine.fmt(c.fs)<<','<<engine.fmt(c.tamb)<<','
      <<engine.fmt(c.rth)<<','<<engine.fmt(c.ripple)<<','<<engine.fmt(c.pmax)<<','<<engine.fmt(c.tmax)<<'\n';
  }
}
std::vector<Case> read_inputs(const Engine& e,const fs::path& p){
  std::ifstream in(p);check(bool(in),"Cannot read numerical CSV input");std::string s;
  check(bool(std::getline(in,s))&&s=="scenarioId,currentA,dcVoltageV,frequencyHz,ambientC,rthKperW,rippleA,lossLimitW,junctionLimitC","Incorrect input CSV schema");
  std::vector<Case> a;long lineno=1;
  while(std::getline(in,s)){
    ++lineno;if(s.empty())continue;auto z=cols(s);check(z.size()==9,"CSV column count at line "+std::to_string(lineno));
    Case c;try{
      check(std::regex_match(z[0],std::regex("[0-9]+")),"Invalid scenario ID");
      c.id=std::stol(z[0]);c.i=e.parse(z[1]);c.v=e.parse(z[2]);c.fs=e.parse(z[3]);
      c.tamb=e.parse(z[4]);c.rth=e.parse(z[5]);c.ripple=e.parse(z[6]);c.pmax=e.parse(z[7]);c.tmax=e.parse(z[8]);validate_case(c);
    }catch(const std::exception& x){throw std::runtime_error("CSV line "+std::to_string(lineno)+": "+x.what());}
    a.push_back(c);
  }check(!a.empty(),"Input CSV is empty");return a;
}
struct Family {int version;std::map<std::string,Graph> graphs;};
Family create_family(Engine& e,int version){Family a;a.version=version;for(const auto& [name,expr]:formulas(version)){
    Graph g;g.id=name;g.version="v"+std::to_string(version);g.expression=expr;
    g.units=name.find("loss")!=std::string::npos?"W":name.find("margin")!=std::string::npos?"model dependent":"dimensioned SI";
    g.h=e.make(expr);a.graphs.emplace(name,g);
  }return a;}
PACEVAL_HANDLE g(const Family& f,const std::string& name){return f.graphs.at(name).h;}
struct Sol {bool valid=false;std::string reason;double tj=0,residual=0;};
std::vector<Sol> solve_batch(Engine& e,const Family& f,const std::vector<Case>& cs){
 const unsigned n=cs.size();std::vector<Sol> r(n);std::vector<double> lo(n),hi(n),x(n);
 std::vector<Vec> rows(n);
 for(unsigned j=0;j<n;j++){lo[j]=cs[j].tamb;hi[j]=250;x[j]=0.5*(lo[j]+hi[j]);rows[j]=row(cs[j],hi[j]);}
 auto bounds=e.batch({g(f,"thermal_residual"),g(f,"residual_derivative")},rows);
 for(unsigned j=0;j<n;j++){
   if(bounds[j]<0){r[j].reason="NO_ROOT_IN_250C_MODEL_DOMAIN";x[j]=lo[j];}
   else if(bounds[n+j]<=0){r[j].reason="NONPOSITIVE_THERMAL_FEEDBACK";x[j]=lo[j];}
   else r[j].reason="SOLVING";
 }
 // Safeguarded Newton with per-point interval updates; only C++ flow control.
 for(unsigned iter=0;iter<22;iter++){
   for(unsigned j=0;j<n;j++)rows[j]=row(cs[j],x[j]);
   const auto v=e.batch({g(f,"thermal_residual"),g(f,"residual_derivative")},rows);
   for(unsigned j=0;j<n;j++){
     if(r[j].reason!="SOLVING")continue;
     const double residual=v[j],der=v[n+j];
     if(std::abs(residual)<1.0e-9){r[j].reason="OK";r[j].valid=true;r[j].tj=x[j];r[j].residual=residual;continue;}
     if(residual>0)hi[j]=x[j];else lo[j]=x[j];
     double proposal=der>1.0e-9?x[j]-residual/der:std::numeric_limits<double>::quiet_NaN();
     if(!std::isfinite(proposal)||proposal<lo[j]||proposal>hi[j])proposal=(lo[j]+hi[j])/2;
     x[j]=proposal;
   }
 }
 for(unsigned j=0;j<n;j++)if(r[j].reason=="SOLVING")r[j].reason="SOLVER_NOT_CONVERGED";
 return r;
}
struct Counters {unsigned long long good=0,noRoot=0,solversFailed=0,accept=0,review=0,reject=0,comparisons=0;};
std::string decide(const double tmargin,const double lmargin,const double stability,const double score){
 if(stability<=0||tmargin < -18||lmargin < -40||score>1.70)return "REJECT";
 if(tmargin>=0&&lmargin>=0&&score<=.88)return "ACCEPT";
 return "REVIEW";
}
void write_registry(const std::vector<Family>& fam,const std::map<std::string,Graph>& compares,const fs::path& dst){
 std::ofstream out(dst);check(bool(out),"Failed creating graph inventory");
 out<<"function_id,domain_quantity,mathematical_definition,units,execution_owner,paceval_graph_id,formula_version,api_path,reference_test,status,host_reason\n";
 auto line=[&out](const Graph& gr,const std::string& quantity){
   const std::map<std::string,std::string> declared={
    {"conduction_loss","W"},{"switching_loss","W"},{"total_loss","W"},
    {"thermal_residual","K"},{"residual_derivative","dimensionless"},
    {"temperature_margin","K"},{"loss_margin","W"},{"feedback_margin","dimensionless"},
    {"loss_sensitivity_current","W/A"},{"temperature_sensitivity_current","K/A"},
    {"temperature_sensitivity_frequency","K/Hz"},{"switching_share","dimensionless"},
    {"stress_score","dimensionless"},{"boolean_guard","0_or_1"},
    {"thermal_step","Celsius"},{"loss_energy_step","J"},
    {"junction_revision_delta","K"},{"loss_revision_delta","W"},
    {"switching_share_revision_delta","dimensionless"}};
   const std::string units=declared.at(quantity);
   out<<gr.id<<','<<quantity<<",\""<<gr.expression<<"\","<<units<<",paceval,"
      <<gr.id<<'_'<<gr.version<<','<<gr.version<<",dGetMultipleComputationsResultsExt,verify_reference.py,executed,\n";
 };
 for(const auto& f:fam)for(const auto& [name,gr]:f.graphs)line(gr,name);
 for(const auto& [name,gr]:compares)line(gr,name);
}
// Stage 2: model version changes are themselves evaluated by paceval graphs.
std::map<std::string,Graph> compare_graphs(Engine& e){
 // The two version outputs are transported into standard variables; their mathematical differences are graphs.
 // i=v1_temperature, v=v2_temperature, fs=v1_loss, tamb=v2_loss, rth=v1_switch_share, tj=v2_switch_share.
 std::map<std::string,std::string> a={{"junction_revision_delta","v-i"},
 {"loss_revision_delta","tamb-fs"},{"switching_share_revision_delta","tj-rth"}};
 std::map<std::string,Graph> out;for(auto& [name,expr]:a){Graph gr;gr.id=name;gr.version="comparison";gr.expression=expr;gr.h=e.make(expr);out.emplace(name,gr);}return out;
}
// A controlled 2D operating surface; every plotted point is evaluated by paceval,
// not interpolated from an independent mathematical implementation.
void surface_run(Engine& e,const std::vector<Family>& fam,const fs::path& dst){
 std::ofstream o(dst);check(bool(o),"Cannot create paceval operating surface");
 o<<"version,currentA,frequencyHz,ambientC,dcVoltageV,rthKperW,solverStatus,junctionTempC,conductionW,switchingW,totalLossW,tempMarginK,lossMarginW,currentSensitivityKperA,frequencySensitivityKperHz,stressScore,switchingShare,booleanGuard\n";
 const std::vector<std::string> fields={"conduction_loss","switching_loss","total_loss","temperature_margin","loss_margin",
     "temperature_sensitivity_current","temperature_sensitivity_frequency","stress_score","switching_share","boolean_guard"};
 for(const auto& f:fam){
  std::vector<Case> cs;
  for(int ff=0;ff<=40;ff++)for(int ii=0;ii<=40;ii++){
    Case a;a.i=20+3.0*ii;a.fs=4000+500.0*ff;a.v=750;a.tamb=35;a.rth=.16;a.ripple=10;
    a.pmax=220;a.tmax=170;a.id=ff*41+ii;cs.push_back(a);
  }
  const size_t chunk=256;
  for(size_t off=0;off<cs.size();off+=chunk){
    std::vector<Case> c(cs.begin()+off,cs.begin()+std::min(off+chunk,cs.size()));
    const auto solved=solve_batch(e,f,c);
    std::vector<Vec> rows;for(size_t j=0;j<c.size();j++)rows.push_back(row(c[j],solved[j].valid?solved[j].tj:c[j].tamb));
    std::vector<PACEVAL_HANDLE> handles;for(const auto& x:fields)handles.push_back(g(f,x));
    auto z=e.batch(handles,rows);
    for(size_t j=0;j<c.size();j++){
      auto &a=c[j];o<<f.version<<','<<e.fmt(a.i)<<','<<e.fmt(a.fs)<<','<<e.fmt(a.tamb)<<','<<e.fmt(a.v)<<','<<e.fmt(a.rth)<<',';
      if(!solved[j].valid){o<<solved[j].reason<<",,,,,,,,,,,\n";continue;}
      o<<"OK,"<<e.fmt(solved[j].tj);
      for(size_t k=0;k<fields.size();k++)o<<','<<e.fmt(z[k*c.size()+j]);
      o<<'\n';
    }
  }
 }
}
void transient_run(Engine& e,const std::vector<Family>& fam,const fs::path& dst){
 std::ofstream o(dst);check(bool(o),"Cannot save transient results");
 o<<"version,profile,cooling,step,timeS,currentA,frequencyHz,junctionTempC,lossW,cumulativeLossJ\n";
 const double cool[2]={.12,.24},dt=.25;int n=480;
 for(const auto& f:fam)for(int profile=0;profile<3;profile++)for(int c=0;c<2;c++){
   Case base;base.i=0;base.v=720;base.fs=12000;base.tamb=28;base.rth=cool[c];base.pmax=220;base.tmax=170;base.ripple=9;
   double t=28,energy=0;
   for(int j=0;j<n;j++){
     const double time=j*dt;
     // Synthetic driving waveform is input data generation, not the semiconductor loss model.
     if(profile==0)base.i=time<30?35:(time<75?105:55);
     if(profile==1)base.i=70+40*std::abs(std::sin(time*0.072));
     if(profile==2)base.i=time<45?45:(time<85?125:65);
     base.fs=profile==1?12000+3000*std::sin(time*.025):(profile==2?18000:10000);
     const auto v=e.batch({g(f,"thermal_step"),g(f,"total_loss"),g(f,"loss_energy_step")},{row(base,t,dt,60)});
     check(v.size()==3&&v[0]>=-10&&v[0]<250,"Transient went outside model domain");
     t=v[0];energy+=v[2];
     o<<f.version<<','<<profile<<','<<c<<','<<j<<','<<e.fmt(time)<<','<<e.fmt(base.i)<<','<<e.fmt(base.fs)<<','
      <<e.fmt(t)<<','<<e.fmt(v[1])<<','<<e.fmt(energy)<<'\n';
   }
 }
}
void run(Engine& engine,long n,const fs::path& dest){
 check(n>=16&&n<=200000,"Count must be 16..200000");fs::create_directories(dest);
 const auto inp=dest/"synthetic_sweep.csv";generate_inputs(engine,inp,n);
 const auto cases=read_inputs(engine,inp);std::vector<Family> fam;
 fam.push_back(create_family(engine,1));fam.push_back(create_family(engine,2));auto comps=compare_graphs(engine);
 std::ofstream out(dest/"inverter_results.csv"),co(dest/"version_comparison.csv"),bad(dest/"solver_rejections.csv"),trace(dest/"end_to_end_trace.csv");
 check(bool(out)&&bool(co)&&bool(bad)&&bool(trace),"Cannot create output files");
 out<<"scenarioId,version,currentA,dcVoltageV,frequencyHz,ambientC,rthKperW,rippleA,lossLimitW,junctionLimitC,solverStatus,junctionTempC,conductionW,switchingW,totalLossW,tempMarginK,lossMarginW,feedbackMargin,lossSensitivityWperA,tempSensitivityKperA,freqSensitivityKperHz,switchingShare,stressScore,booleanGuard,decision\n";
 co<<"scenarioId,junctionRevisionDeltaK,lossRevisionDeltaW,switchShareRevisionDelta\n";
 bad<<"scenarioId,version,reason\n";
 trace<<"scenarioId,version,currentA,dcVoltageV,frequencyHz,ambientC,rthKperW,temperatureC,conductionW,switchingW,thermalResidual,tempMarginK,lossMarginW,stressScore,booleanGuard,hostDecision\n";
 std::map<std::string,Counters> cnt;
 const std::vector<std::string> resultNames={"conduction_loss","switching_loss","total_loss","thermal_residual","residual_derivative","temperature_margin","loss_margin","feedback_margin","loss_sensitivity_current","temperature_sensitivity_current","temperature_sensitivity_frequency","switching_share","stress_score","boolean_guard"};
 const size_t chunk=512;
 for(size_t offset=0;offset<cases.size();offset+=chunk){
   const size_t count=std::min(chunk,cases.size()-offset);std::vector<Case> subset(cases.begin()+offset,cases.begin()+offset+count);
   std::vector<std::vector<Sol>> solutions;
   std::vector<std::vector<std::vector<double>>> processed;
   for(const auto& family:fam){
     solutions.push_back(solve_batch(engine,family,subset));
     std::vector<Vec> vals;std::vector<PACEVAL_HANDLE> handles;
     for(const auto& name:resultNames)handles.push_back(g(family,name));
     for(size_t j=0;j<count;j++){
       // The positive-current check ensures the switching-share 0/0 case is excluded.
       const double t=solutions.back()[j].valid?solutions.back()[j].tj:subset[j].tamb;
       vals.push_back(row(subset[j],t));
     }
     const auto result=engine.batch(handles,vals);
     std::vector<std::vector<double>> rowResult(count,std::vector<double>(resultNames.size()));
     for(size_t k=0;k<handles.size();k++)for(size_t j=0;j<count;j++)rowResult[j][k]=result[k*count+j];
     processed.push_back(std::move(rowResult));
     auto& total=cnt["v"+std::to_string(family.version)];
     for(size_t j=0;j<count;j++){
       const auto& s=solutions.back()[j];const auto& d=processed.back()[j];const auto& c=subset[j];
       if(!s.valid){
         if(s.reason=="NO_ROOT_IN_250C_MODEL_DOMAIN")++total.noRoot;else ++total.solversFailed;
         ++total.reject;bad<<c.id<<','<<family.version<<','<<s.reason<<'\n';
         out<<c.id<<','<<family.version<<','<<engine.fmt(c.i)<<','<<engine.fmt(c.v)<<','<<engine.fmt(c.fs)<<','<<engine.fmt(c.tamb)<<','<<engine.fmt(c.rth)<<','<<engine.fmt(c.ripple)<<','<<engine.fmt(c.pmax)<<','<<engine.fmt(c.tmax)<<','<<s.reason<<",,,,,,,,,,,,,,REJECT\n";
         continue;
       }
       const double res=d[3],Tmargin=d[5],Lmargin=d[6],stability=d[7],score=d[12];
       check(std::abs(res)<2.e-7,"Thermal root residual failed: "+std::to_string(c.id));
       check(std::abs(d[0]+d[1]-d[2])<1.e-7,"Power partition failed");
       check(std::abs(d[13]-std::round(d[13]))<1.e-12,"Boolean decision not binary");
       ++total.good;std::string status=decide(Tmargin,Lmargin,stability,score);
       if(status=="ACCEPT")++total.accept;else if(status=="REVIEW")++total.review;else ++total.reject;
       out<<c.id<<','<<family.version<<','<<engine.fmt(c.i)<<','<<engine.fmt(c.v)<<','<<engine.fmt(c.fs)<<','<<engine.fmt(c.tamb)<<','<<engine.fmt(c.rth)<<','<<engine.fmt(c.ripple)<<','<<engine.fmt(c.pmax)<<','<<engine.fmt(c.tmax)<<",OK,"<<engine.fmt(s.tj);
       // conduction, switching, total, temperature margin, loss margin, feedback margin,
       // analytic current derivative, implicit temperature derivative, frequency derivative,
       // switching share, stress score and 0/1 mathematical guard.
       for(int k:{0,1,2,5,6,7,8,9,10,11,12,13})out<<','<<engine.fmt(d[k]);
       out<<','<<status<<'\n';
       if(c.id==1){
         trace<<c.id<<','<<family.version<<','<<engine.fmt(c.i)<<','<<engine.fmt(c.v)<<','<<engine.fmt(c.fs)<<','<<engine.fmt(c.tamb)<<','<<engine.fmt(c.rth)
              <<','<<engine.fmt(s.tj)<<','<<engine.fmt(d[0])<<','<<engine.fmt(d[1])<<','<<engine.fmt(d[3])<<','<<engine.fmt(d[5])
              <<','<<engine.fmt(d[6])<<','<<engine.fmt(d[12])<<','<<engine.fmt(d[13])<<','<<status<<'\n';
       }
     }
   }
   std::vector<Vec> vv;std::vector<long> ids;
   for(size_t j=0;j<count;j++)if(solutions[0][j].valid&&solutions[1][j].valid){
     const auto& a=processed[0][j],&b=processed[1][j];
     Vec x={solutions[0][j].tj,solutions[1][j].tj,a[2],b[2],a[11],b[11],0,0,0,0,1};
     vv.push_back(x);ids.push_back(subset[j].id);
   }
   if(!vv.empty()){
     std::vector<PACEVAL_HANDLE> handles;for(auto& [name,item]:comps)handles.push_back(item.h);
     const auto z=engine.batch(handles,vv);size_t h=0;
     // map sorted alphabetically, derive indices from the exact sorted formula ids.
     std::map<std::string,size_t> m;for(auto& [name,item]:comps)m[name]=h++;
     for(size_t j=0;j<vv.size();j++){
       co<<ids[j]<<','<<engine.fmt(z[m["junction_revision_delta"]*vv.size()+j])<<','
       <<engine.fmt(z[m["loss_revision_delta"]*vv.size()+j])<<','
       <<engine.fmt(z[m["switching_share_revision_delta"]*vv.size()+j])<<'\n';
     }cnt["combined"].comparisons+=vv.size();
   }
 }
 out.close();co.close();bad.close();
 surface_run(engine,fam,dest/"operating_surface.csv");
 transient_run(engine,fam,dest/"transient_profiles.csv");
 write_registry(fam,comps,dest/"math_execution_inventory.csv");
 std::ofstream summary(dest/"execution_evidence.json");
 summary<<"{\n  \"library\": \"original paceval SDK 4.25 with supplied Linux shared library\",\n"
 <<"  \"synthetic_scenarios\": "<<cases.size()<<",\n"
 <<"  \"created_graphs\": "<<engine.created()<<",\n"
 <<"  \"executed_graphs\": "<<engine.executed()<<",\n"
 <<"  \"multi_graph_batch_calls\": "<<engine.batchCalls<<",\n"
 <<"  \"scalar_calls\": "<<engine.scalarCalls<<",\n"
 <<"  \"graph_point_evaluations\": "<<engine.graphPointEvaluations<<",\n"
 <<"  \"model_counts\": {\n";
 for(int v=1;v<=2;v++){
  auto& a=cnt["v"+std::to_string(v)];
  summary<<"    \"v"<<v<<"\": {\"successfully_solved\": "<<a.good<<", \"root_outside_domain\": "<<a.noRoot
         <<", \"other_solver_failures\": "<<a.solversFailed<<", \"accept\": "<<a.accept
         <<", \"review\": "<<a.review<<", \"reject\": "<<a.reject<<"}"<<(v==1?",":"")<<"\n";
 }
 summary<<"  },\n  \"complete_model_pairs\": "<<cnt["combined"].comparisons<<",\n"
        <<"  \"surface_points_per_version\": 1681,\n"
        <<"  \"transient_cases\": 12,\n  \"transient_samples_per_case\": 480\n}\n";
 std::cout<<"RESULT graphs_created="<<engine.created()<<" graphs_executed="<<engine.executed()<<" batch_calls="<<engine.batchCalls
     <<" graph_point_evaluations="<<engine.graphPointEvaluations<<" scenarios="<<n<<"\n";
 for(int v=1;v<=2;v++){const auto& c=cnt["v"+std::to_string(v)];std::cout<<"v"<<v<<" good="<<c.good<<" accept="<<c.accept<<" review="<<c.review<<" reject="<<c.reject<<" no_root="<<c.noRoot<<"\n";}
}
void test_conversion(){Engine e;for(const std::string s:{"0","-12.5","0.000004","1e-5","+3.25","12.0","900000000"}){
  const double d=e.parse(s);check(std::isfinite(d)&&!e.fmt(d).empty(),"Conversion test failure");
 }for(const std::string s:{""," ","1+2","NaN","Inf","1,2","--1","3 mm","1e9999"}){
  bool rejected=false;try{(void)e.parse(s);}catch(...){rejected=true;}check(rejected,"Unsafe token accepted "+s);
 }std::cout<<"conversion schema tests OK\n";}
void test_operators(){Engine e;const Vec a={1,800,5000,20,.12,100,8,220,170,0,60};
 for(const auto& [expr,expected]:std::vector<std::pair<std::string,double>>{
 {"(-1)%10",-1},{"(-1) mod 10",9},{"4 min 5",4},{"4 max 5",5},
 {"((tj<=tmax) AND (fs>=0))",1},{"((tj>tmax) OR (i=0))",0},
 {"((i<>0) AND (tj>=100))",1},{"NOT(i=0)",1},
 {"(((tj <= tmax) AND ((fs+i) >= (i+fs))) AND ((i min 5) = 1))",1}}){
 auto h=e.make(expr);check(std::abs(e.scalar(h,a)-expected)<1.e-12,"Operator semantics wrong for "+expr);
 }std::cout<<"operator semantics tests OK\n";}
void test_layout(){Engine e;auto ha=e.make("i+v"),hb=e.make("i*v");
 std::vector<Vec> rows={Vec{2,3,0,0,.1,0,0,1,2,0,1},Vec{4,5,0,0,.1,0,0,1,2,0,1},Vec{6,7,0,0,.1,0,0,1,2,0,1}};
 auto o=e.batch({ha,hb},rows);const double expected[6]={5,9,13,6,20,42};
 for(int k=0;k<6;k++)check(std::abs(o[k]-expected[k])<1.e-12,"Graph-major layout failed");
 check(std::abs(e.scalar(hb,rows[1])-20)<1.e-12,"Scalar vs batch failed");
 std::cout<<"scalar and graph-major batch tests OK\n";}
void test_invalid(){Engine e;Case a=make_case(0);a.rth=-.1;bool bad=false;
 try{validate_case(a);}catch(...){bad=true;}check(bad,"Negative thermal resistance accepted");
 for(auto s:{"100/0","1+1","1,2"}){bad=false;try{(void)e.parse(s);}catch(...){bad=true;}check(bad,"Rejected-field test failed");}
 std::cout<<"invalid inputs rejected OK\n";}
int main(int argc,char** argv){
 try{
  std::string mode="--run";long count=100000;fs::path out=fs::path(PROJECT_ROOT)/"results";
  for(int i=1;i<argc;i++){const std::string a=argv[i];
    if(a=="--run"||a=="--test-conversion"||a=="--test-operators"||a=="--test-layout"||a=="--test-invalid")mode=a;
    else if(a=="--count"&&i+1<argc)count=std::stol(argv[++i]);
    else if(a=="--out"&&i+1<argc)out=argv[++i];
    else throw std::runtime_error("Unknown command argument: "+a);
  }
  if(mode=="--test-conversion")test_conversion();else if(mode=="--test-operators")test_operators();
  else if(mode=="--test-layout")test_layout();else if(mode=="--test-invalid")test_invalid();
  else{Engine e;run(e,count,out);}return 0;
 }catch(const std::exception& ex){std::cerr<<"ERROR: "<<ex.what()<<"\n";return 2;}
}
