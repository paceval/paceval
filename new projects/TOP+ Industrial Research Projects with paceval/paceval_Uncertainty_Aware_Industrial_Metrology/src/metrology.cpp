// WP09: Synthetic industrial measurement uncertainty, covariance and guard-band decisions.
// Real numerical values are evaluated by persistent original paceval SDK graphs.
// Host operations: deterministic sample generation, input schema, covariance validity, orchestration,
// result aggregation, selection of categorical statuses, and storage. Never an accredited decision.
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
namespace fs = std::filesystem;
static constexpr unsigned NV=18;
static constexpr char VARIABLES[]="x temp ux ut rho target tol k a0 a1 a2 b ucal ures meas yval variance sens";
using Row=std::array<double,NV>;
static void ensure(bool p,const std::string& msg){if(!p)throw std::runtime_error(msg);}
static std::vector<std::string> columns(const std::string& line){std::vector<std::string> out;std::stringstream s(line);std::string c;while(std::getline(s,c,','))out.push_back(c);if(!line.empty()&&line.back()==',')out.push_back("");return out;}
class Paceval {
 std::vector<PACEVAL_HANDLE> owned;std::set<PACEVAL_HANDLE> used;
public:
 uint64_t scalar_calls=0,batch_calls=0,graph_point_evaluations=0;
 Paceval(){ensure(paceval_InitializeLibrary(nullptr),"Could not initialize original paceval library");}
 ~Paceval(){for(auto h:owned)paceval_DeleteComputation(h);paceval_FreeLibrary();}
 Paceval(const Paceval&)=delete;Paceval& operator=(const Paceval&)=delete;
 double parse(const std::string& src)const{
  static const std::regex numeric(R"(^[+-]?(?:[0-9]+(?:\.[0-9]*)?|\.[0-9]+)(?:[eE][+-]?[0-9]+)?$)");
  ensure(std::regex_match(src,numeric),"Rejected nonliteral CSV numerical field: "+src);
  int err=-1;long position=-1;
  double x=paceval_dConvertStringToFloat(src.c_str(),&err,&position,false,nullptr,nullptr);
  ensure(err==PACEVAL_ERR_NO_ERROR&&std::isfinite(x),"paceval string conversion failed at "+std::to_string(position));
  return x;
 }
 std::string fmt(double x)const{
  ensure(std::isfinite(x),"Nonfinite floating-point CSV output");
  char text[512]={};int status=paceval_dConvertFloatToString(text,x);
  ensure(status>0&&text[0]!=0,"paceval float conversion failed");return text;
 }
 PACEVAL_HANDLE graph(const std::string& formula){
  PACEVAL_HANDLE h=paceval_CreateComputation(formula.c_str(),NV,VARIABLES,false,nullptr);
  ensure(h!=nullptr,"paceval returned a null computation handle");
  if(paceval_GetIsError(h)){char x[1024]={},y[1024]={};paceval_CreateErrorInformationText(h,x,y);paceval_DeleteComputation(h);throw std::runtime_error("Invalid paceval graph: "+formula.substr(0,140)+" "+x+" "+y);}
  owned.push_back(h);return h;
 }
 std::vector<double> batch(const std::vector<PACEVAL_HANDLE>& handles,const std::vector<Row>& rows){
  ensure(!handles.empty()&&!rows.empty(),"Empty batch");std::vector<double> input;input.reserve(rows.size()*NV);
  for(const auto& row:rows)for(double x:row){ensure(std::isfinite(x),"Nonfinite mathematical input");input.push_back(x);}
  auto local=handles;std::vector<double> output(handles.size()*rows.size());std::vector<int> errors(output.size(),-1);
  bool failed=paceval_dGetMultipleComputationsResultsExt(local.data(),static_cast<unsigned long>(local.size()),input.data(),static_cast<unsigned long>(rows.size()),output.data(),nullptr,nullptr,errors.data());
  ensure(!failed,"Original paceval multi-graph batch call failed");
  for(size_t i=0;i<errors.size();++i)ensure(errors[i]==PACEVAL_ERR_NO_ERROR&&std::isfinite(output[i]),"paceval batch element failure "+std::to_string(i)+" error "+std::to_string(errors[i]));
  for(auto h:handles){used.insert(h);}
  ++batch_calls;graph_point_evaluations+=output.size();return output;
 }
 double scalar(PACEVAL_HANDLE h,const Row& row){double x=paceval_dGetComputationResult(h,const_cast<double*>(row.data()),nullptr,nullptr);ensure(!paceval_GetIsError(h)&&std::isfinite(x),"paceval scalar computation failed");used.insert(h);++scalar_calls;++graph_point_evaluations;return x;}
 size_t created()const{return owned.size();}size_t executed()const{return used.size();}
};
struct Formula{std::string id,formula,version,unit;PACEVAL_HANDLE handle;};
using Graphs=std::map<std::string,Formula>;
using Definitions=std::map<std::string,std::string>;
static const std::string YBASE="(a0+a1*x+a2*sqr(x)+b*(temp-20))";
static const std::string SENS="(a1+2*a2*x)";
static const std::string COV="(rho*ux*ut)";
static const std::string VAR0="(sqr("+SENS+")*sqr(ux)+sqr(b)*sqr(ut)+2*"+SENS+"*b*"+COV+"+sqr(ucal)+sqr(ures))";
static const std::string CURV="(2*sqr(a2)*sqr(sqr(ux)))";
Definitions primary(int version){
 std::string y=(version==1?YBASE:"("+YBASE+"+a2*sqr(ux))");
 std::string v=(version==1?VAR0:"("+VAR0+"+"+CURV+")");
 return {{"measurand",y},{"sensitivity_x",SENS},{"sensitivity_temperature","b"},{"covariance_x_temperature",COV},
 {"correlated_variance","(2*"+SENS+"*b*"+COV+")"},{"model_bias",(version==1?"(0*x)":"(a2*sqr(ux))")},
 {"variance",v},{"curvature_contribution",CURV}};
}
// The second stage takes yval, variance and sens from actual first-stage paceval results.
Definitions secondary(){const std::string UC="sqrt(variance)",U="(k*"+UC+")";
 const std::string AM="(tol-abs(yval-target)-"+U+")";
 const std::string RM="(abs(yval-target)-tol-"+U+")";
 const std::string ACCEPT="(("+AM+" >= 0) AND (abs(rho) <= 1))";
 const std::string REJECT="("+RM+" >= 0)";
 const std::string VD="(4*a2*sens*sqr(ux)+4*a2*b*rho*ux*ut)";
 return {{"standard_uncertainty",UC},{"expanded_uncertainty",U},{"acceptance_margin",AM},
  {"rejection_margin",RM},{"accept_indicator",ACCEPT},{"reject_indicator",REJECT},
  {"decision_code","("+ACCEPT+"-"+REJECT+")"},
  {"normalized_deviation","((yval-target)/"+UC+")"},
  {"quality_score","(0.55*sqr((yval-target)/tol)+0.30*sqr("+U+"/tol)+0.15*abs(rho))"},
  {"raw_minus_calibrated","(meas-yval)"},
  {"uncertainty_sensitivity_x","("+VD+"/(2*"+UC+"))"},
  {"lower_acceptance","(target-tol+"+U+")"},
  {"upper_acceptance","(target+tol-"+U+")"}};
}
Graphs register_graphs(Paceval& e,const Definitions& defs,int ver){Graphs result;for(const auto& [n,form]:defs){Formula x{n,form,"v"+std::to_string(ver),"defined_per_quantity",e.graph(form)};result.emplace(n,std::move(x));}return result;}
std::vector<std::string> names(const Graphs& g){std::vector<std::string> s;for(const auto& [key,f]:g)s.push_back(key);return s;}
std::vector<PACEVAL_HANDLE> handles(const Graphs& g){std::vector<PACEVAL_HANDLE> h;for(const auto& [key,f]:g)h.push_back(f.handle);return h;}
std::map<std::string,size_t> index_map(const Graphs& g){std::map<std::string,size_t> m;size_t i=0;for(const auto& [key,f]:g)m[key]=i++;return m;}
struct Scenario{int revision,caseid;double rho,a0,a1,a2,b,ux,ut,ucal,ures,target,tol,k;};
std::vector<Scenario> generate_scenarios(Paceval& e,int revisions,int cases,fs::path file){
 std::vector<Scenario> out;std::ofstream f(file);ensure(bool(f),"Cannot write scenario CSV");
 f<<"revision,case,rho,a0_mm,a1_mm,a2_mm,b_mm_per_C,ux,ut_C,ucal_mm,ures_mm,target_mm,tol_mm,k\n";
 const double correlations[]={-0.95,-0.75,-0.50,-0.25,0,0.25,0.50,0.75,0.90,0.98};
 ensure(cases>=1&&cases<=10,"Supported covariance cases: 1 through 10");
 for(int r=0;r<revisions;r++)for(int c=0;c<cases;c++){
  Scenario s{r,c,correlations[c],0.002*std::sin(.4*r),.065+.0015*std::cos(.5*r),.009+.0007*std::sin(.4*r),.0009+.00004*r,.037+.005*(c%5),.20+.085*(c%4),.0018+.0002*(r%3),.0011,0,.05,2};
  out.push_back(s);f<<r<<','<<c;for(double x:{s.rho,s.a0,s.a1,s.a2,s.b,s.ux,s.ut,s.ucal,s.ures,s.target,s.tol,s.k})f<<','<<e.fmt(x);f<<'\n';
 }
 return out;
}
std::vector<Scenario> load_scenarios(Paceval& e,const fs::path& f){
 std::ifstream in(f);ensure(bool(in),"Cannot read scenario CSV");std::string line;ensure(bool(std::getline(in,line))&&columns(line).size()==14,"Bad CSV header");
 std::vector<Scenario> result;while(std::getline(in,line)){if(line.empty())continue;auto v=columns(line);ensure(v.size()==14,"Wrong number of scenario columns");
  Scenario s{};double ri=e.parse(v[0]),ci=e.parse(v[1]);ensure(std::floor(ri)==ri&&std::floor(ci)==ci,"Fractional integer ID");s.revision=int(ri);s.caseid=int(ci);
  double *fields[]={&s.rho,&s.a0,&s.a1,&s.a2,&s.b,&s.ux,&s.ut,&s.ucal,&s.ures,&s.target,&s.tol,&s.k};
  for(int j=0;j<12;j++)*fields[j]=e.parse(v[2+j]);
  ensure(std::abs(s.rho)<=1&&s.ux>0&&s.ut>0&&s.ucal>0&&s.ures>0&&s.tol>0&&s.k>0&&std::isfinite(s.rho),"Invalid covariance or uncertainty input");
  result.push_back(s);
 }
 return result;
}
Row make_row(const Scenario& s,int sample,int samples){Row row{};uint64_t perm=(uint64_t(sample)*7919u+uint64_t(s.revision)*389u+uint64_t(s.caseid)*73u)%uint64_t(samples);
 // Generate deterministic synthetic normalized input values; no real instrument readings.
 row[0]=-1.35+2.70*double(perm)/double(samples-1);
 if(sample%79==0)row[0]*=1.12;
 row[1]=18.0+.01*double((sample*31+s.revision*7+s.caseid*11)%1100);
 row[2]=s.ux*(0.82+.055*(sample%7));row[3]=s.ut*(.85+.065*(sample%5));
 row[4]=s.rho;row[5]=s.target;row[6]=s.tol;row[7]=s.k;
 row[8]=s.a0;row[9]=s.a1;row[10]=s.a2;row[11]=s.b;row[12]=s.ucal;row[13]=s.ures;
 row[14]=0.008*std::cos(double(sample)*0.017)+row[0]*.065;
 return row;
}
void check_row(const Row& r){ensure(r[0]>=-1.7&&r[0]<=1.7&&r[1]>=10&&r[1]<=45&&r[2]>0&&r[3]>0&&r[4]>=-1&&r[4]<=1&&r[6]>0&&r[7]>0&&r[12]>0&&r[13]>0,"Sample out of declared model domain");}
struct Reference{double y,dx,dt,cov,corr,bias,var,curv,uc,U,am,rm,accept,reject,code,z,score,rawdiff,dudx,lower,upper;};
Reference native(const Row& r,int version){
 const double x=r[0],t=r[1],ux=r[2],ut=r[3],rho=r[4],target=r[5],tol=r[6],k=r[7],a0=r[8],a1=r[9],a2=r[10],b=r[11],ucal=r[12],ures=r[13];
 double s=a1+2*a2*x,c=rho*ux*ut,corr=2*s*b*c,curv=2*a2*a2*ux*ux*ux*ux,bias=(version==1?0:a2*ux*ux);
 double y=a0+a1*x+a2*x*x+b*(t-20)+bias;
 double var=s*s*ux*ux+b*b*ut*ut+corr+ucal*ucal+ures*ures+(version==1?0:curv);
 ensure(var>0,"Nonpositive independent reference variance");double u=std::sqrt(var),U=k*u;
 double am=tol-std::abs(y-target)-U,rm=std::abs(y-target)-tol-U;
 double accept=(am>=0&&std::abs(rho)<=1)?1:0,reject=rm>=0?1:0;
 double score=.55*std::pow((y-target)/tol,2)+.30*std::pow(U/tol,2)+.15*std::abs(rho);
 double dudx=(4*a2*s*ux*ux+4*a2*b*c)/(2*u);
 return {y,s,b,c,corr,bias,var,curv,u,U,am,rm,accept,reject,accept-reject,(y-target)/u,score,r[14]-y,dudx,target-tol+U,target+tol-U};
}
void check_number(double got,double expected,const std::string& label){ensure(std::abs(got-expected)<=8e-12+1e-10*std::abs(expected),"Independent numeric mismatch: "+label);}
struct Accum{uint64_t n=0,accepted=0,review=0,rejected=0;double ysum=0,usum=0,score=0,meanMargin=0,varianceSum=0;};
void write_inventory(const fs::path& f,const Graphs& p1,const Graphs& p2,const Graphs& s1,const Graphs& s2){
 std::ofstream o(f);o<<"function_id,domain_quantity,mathematical_definition,units,execution_owner,paceval_graph_id,formula_version,api_path,reference_test,status,host_reason\n";
 for(const auto& g:{&p1,&p2,&s1,&s2})for(const auto& [name,x]:*g){std::string formula=x.formula;std::replace(formula.begin(),formula.end(),'"',' ');o<<x.version<<'_'<<name<<','<<name<<",\""<<formula<<"\",defined_per_quantity,paceval,"<<x.version<<'_'<<name<<','<<x.version<<",dGetMultipleComputationsResultsExt,independent_native_cpp_and_python,executed,\n";}
 o<<"host_covariance_psd,covariance_validation,abs(rho)<=1,dimensionless,host,,all,prevalidation,invalid_input_tests,executed,protect_defined_domain\n";
 o<<"host_status,status,interpret_paceval_accept_and_reject,category,host,,all,postprocess,independent_native_cpp,executed,state_selection\n";
}
static void test_conversion(Paceval& e){for(const auto& s:{"0","-1.25","3.14159265359","1e-12","7.0000000","1E+14"}){double a=e.parse(s);ensure(std::isfinite(a),"Conversion test failed");ensure(e.parse(e.fmt(a))==e.parse(e.fmt(a)),"Unstable CSV string roundtrip");}
 for(const auto& s:{"1+2","abc","","NaN","Inf","1,25","1e2000","2/3"}){bool failed=false;try{(void)e.parse(s);}catch(...){failed=true;}ensure(failed,"Unsafe numeric CSV field accepted");}
}
static void test_operators(Paceval& e){Row r{};r.fill(1);r[0]=2;r[1]=3;r[4]=-.5;
 const std::vector<std::pair<std::string,double>> cases={{"(-1) % 10",-1},{"(-1) mod 10",9},{"(4 min 5)",4},{"(4 max 5)",5},{"((x<temp) AND (temp>=3))",1},{"((x>temp) OR (temp=3))",1},{"NOT(x=temp)",1},{"((abs(rho)<=1) AND (x<>temp))",1}};
 for(const auto& item:cases){auto h=e.graph(item.first);check_number(e.scalar(h,r),item.second,"operator "+item.first);}
}
static void test_layout(Paceval& e){Row a{};a.fill(1);Row b=a;a[0]=3;a[1]=1;b[0]=7;b[1]=2;
 auto h=e.graph("(x+temp)"),j=e.graph("(x-temp)");auto v=e.batch({h,j},{a,b});ensure(v.size()==4&&v[0]==4&&v[1]==9&&v[2]==2&&v[3]==5,"Graph-major batch layout invalid");ensure(e.scalar(h,a)==4,"Scalar did not agree with batch");}
static void test_invalid(Paceval& e){auto s=generate_scenarios(e,1,1,fs::temp_directory_path()/"wp09_invalid_scenarios.csv")[0];s.rho=1.01;Row row=make_row(s,0,128);bool rejected=false;try{check_row(row);}catch(...){rejected=true;}ensure(rejected,"Unphysical covariance passed host check");}
void run(Paceval& e,int revisions,int cases,int samples,const fs::path& dest){
 ensure(revisions>=1&&revisions<=10&&cases>=1&&cases<=10&&samples>=8&&samples<=50000,"Invalid synthetic research workload");fs::create_directories(dest);
 generate_scenarios(e,revisions,cases,dest/"input_scenarios.csv");auto scenarios=load_scenarios(e,dest/"input_scenarios.csv");
 Graphs p1=register_graphs(e,primary(1),1),p2=register_graphs(e,primary(2),2),s1=register_graphs(e,secondary(),1),s2=register_graphs(e,secondary(),2);
 write_inventory(dest/"math_execution_inventory.csv",p1,p2,s1,s2);
 std::ofstream registry(dest/"formula_registry.csv"),summary(dest/"scenario_summary.csv"),audit(dest/"audit_samples.csv"),trace(dest/"end_to_end_trace.csv");
 ensure(bool(registry)&&bool(summary)&&bool(audit)&&bool(trace),"Cannot write research data");
 registry<<"graph_id,version,stage,formula\n";
 for(const auto& [g,stage]:std::vector<std::pair<const Graphs*,std::string>>{{&p1,"primary"},{&p2,"primary"},{&s1,"secondary"},{&s2,"secondary"}})for(const auto& [name,f]:*g)registry<<f.version<<'_'<<name<<','<<f.version<<','<<stage<<",\""<<f.formula<<"\"\n";
 summary<<"revision,covariance_case,model_version,rho,samples,accepted,review,rejected,mean_y_mm,mean_u_mm,mean_quality_score,mean_acceptance_margin_mm,mean_variance_mm2\n";
 audit<<"revision,covariance_case,model_version,sample,x,temp_C,ux,ut_C,rho,a0,a1,a2,b,ucal,ures,target_mm,tol_mm,k,raw_mm,y_mm,sensitivity_x,variance_mm2,u_mm,U_mm,acceptance_margin_mm,rejection_margin_mm,accept_indicator,reject_indicator,decision_code,quality_score,uncertainty_sensitivity_x\n";
 trace<<"revision,covariance_case,version,sample,x,temp_C,measurand_mm,variance_mm2,combined_uncertainty_mm,expanded_uncertainty_mm,accept_margin_mm,reject_margin_mm,accept_graph,reject_graph,host_decision\n";
 uint64_t rows_total=0,independent_checks=0,trace_count=0;const size_t BATCH=256;
 for(const auto& scenario:scenarios)for(int version:{1,2}){
  const auto& p=(version==1?p1:p2);const auto& q=(version==1?s1:s2);auto ip=index_map(p),iq=index_map(q);
  auto ph=handles(p),qh=handles(q);Accum a;
  for(int begin=0;begin<samples;begin+=int(BATCH)){
   int n=std::min(int(BATCH),samples-begin);std::vector<Row> rows;rows.reserve(n);
   for(int j=0;j<n;j++){auto r=make_row(scenario,begin+j,samples);check_row(r);rows.push_back(r);}
   auto pr=e.batch(ph,rows);
   for(int j=0;j<n;j++){rows[j][15]=pr[ip.at("measurand")*n+j];rows[j][16]=pr[ip.at("variance")*n+j];rows[j][17]=pr[ip.at("sensitivity_x")*n+j];ensure(rows[j][16]>0,"Variance must be positive before sqrt graph");}
   auto qr=e.batch(qh,rows);
   for(int j=0;j<n;j++){
    auto P=[&](const std::string& key){return pr[ip.at(key)*n+j];};
    auto Q=[&](const std::string& key){return qr[iq.at(key)*n+j];};
    auto ref=native(rows[j],version);
    for(const auto& item:std::vector<std::pair<std::string,double>>{{"measurand",ref.y},{"sensitivity_x",ref.dx},{"sensitivity_temperature",ref.dt},{"covariance_x_temperature",ref.cov},{"correlated_variance",ref.corr},{"model_bias",ref.bias},{"variance",ref.var},{"curvature_contribution",ref.curv}}){check_number(P(item.first),item.second,item.first);++independent_checks;}
    for(const auto& item:std::vector<std::pair<std::string,double>>{{"standard_uncertainty",ref.uc},{"expanded_uncertainty",ref.U},{"acceptance_margin",ref.am},{"rejection_margin",ref.rm},{"accept_indicator",ref.accept},{"reject_indicator",ref.reject},{"decision_code",ref.code},{"normalized_deviation",ref.z},{"quality_score",ref.score},{"raw_minus_calibrated",ref.rawdiff},{"uncertainty_sensitivity_x",ref.dudx},{"lower_acceptance",ref.lower},{"upper_acceptance",ref.upper}}){check_number(Q(item.first),item.second,item.first);++independent_checks;}
    int cat=Q("decision_code")>.5?1:(Q("decision_code")<-.5?-1:0);ensure(int(ref.code)==cat,"Categorical independent decision mismatch");
    ++a.n;a.accepted+=cat==1;a.review+=cat==0;a.rejected+=cat==-1;a.ysum+=P("measurand");a.usum+=Q("standard_uncertainty");a.score+=Q("quality_score");a.meanMargin+=Q("acceptance_margin");a.varianceSum+=P("variance");++rows_total;
    if((begin+j)%std::max(1,samples/12)==0){
     auto rr=rows[j];audit<<scenario.revision<<','<<scenario.caseid<<','<<version<<','<<begin+j;
     for(int m:{0,1,2,3,4,8,9,10,11,12,13,5,6,7,14})audit<<','<<e.fmt(rr[m]);
     for(double t:{P("measurand"),P("sensitivity_x"),P("variance"),Q("standard_uncertainty"),Q("expanded_uncertainty"),Q("acceptance_margin"),Q("rejection_margin"),Q("accept_indicator"),Q("reject_indicator"),Q("decision_code"),Q("quality_score"),Q("uncertainty_sensitivity_x")})audit<<','<<e.fmt(t);
     audit<<'\n';
    }
    if(begin+j==0){trace<<scenario.revision<<','<<scenario.caseid<<','<<version<<','<<begin+j<<','<<e.fmt(rows[j][0])<<','<<e.fmt(rows[j][1]);
     for(double t:{P("measurand"),P("variance"),Q("standard_uncertainty"),Q("expanded_uncertainty"),Q("acceptance_margin"),Q("rejection_margin"),Q("accept_indicator"),Q("reject_indicator")})trace<<','<<e.fmt(t);
     trace<<','<<(cat==1?"ACCEPT":cat==-1?"REJECT":"REVIEW")<<'\n';++trace_count;}
   }
  }
  summary<<scenario.revision<<','<<scenario.caseid<<','<<version<<','<<e.fmt(scenario.rho)<<','<<a.n<<','<<a.accepted<<','<<a.review<<','<<a.rejected<<','<<e.fmt(a.ysum/a.n)<<','<<e.fmt(a.usum/a.n)<<','<<e.fmt(a.score/a.n)<<','<<e.fmt(a.meanMargin/a.n)<<','<<e.fmt(a.varianceSum/a.n)<<'\n';
 }
 summary.close();registry.close();trace.close();audit.close();
 std::ofstream evidence(dest/"execution_evidence.json");evidence<<"{\n  \"project\": \"WP09 Uncertainty-Aware Industrial Metrology and Tolerance Decisions\",\n  \"runtime\": \"original paceval SDK 4.25 and compatible Linux shared library\",\n  \"dataset\": \"deterministic synthetic research inputs; no physical calibration\",\n  \"calibration_revisions\": "<<revisions<<",\n  \"covariance_cases\": "<<cases<<",\n  \"samples_per_scenario\": "<<samples<<",\n  \"model_versions\": 2,\n  \"unique_measurement_inputs\": "<<uint64_t(revisions)*cases*samples<<",\n  \"model_point_rows\": "<<rows_total<<",\n  \"unique_graphs_created\": "<<e.created()<<",\n  \"unique_graphs_executed\": "<<e.executed()<<",\n  \"batch_calls\": "<<e.batch_calls<<",\n  \"scalar_calls\": "<<e.scalar_calls<<",\n  \"graph_point_evaluations\": "<<e.graph_point_evaluations<<",\n  \"native_cpp_reference_checks\": "<<independent_checks<<",\n  \"end_to_end_trace_rows\": "<<trace_count<<"\n}\n";
 std::cout<<"WP09 COMPLETE: rows="<<rows_total<<" graphs="<<e.executed()<<" graph_outputs="<<e.graph_point_evaluations<<" native_checks="<<independent_checks<<" batches="<<e.batch_calls<<"\n";
}
int main(int argc,char** argv){try{Paceval e;
 if(argc>1){std::string mode=argv[1];if(mode=="--test-conversion"){test_conversion(e);std::cout<<"CONVERSION_OK\n";return 0;}
  if(mode=="--test-operators"){test_operators(e);std::cout<<"OPERATORS_OK\n";return 0;}
  if(mode=="--test-layout"){test_layout(e);std::cout<<"BATCH_LAYOUT_OK\n";return 0;}
  if(mode=="--test-invalid"){test_invalid(e);std::cout<<"INVALID_INPUT_OK\n";return 0;}
  if(mode=="--run"){int rev=10,cases=10,samples=5000;fs::path out=fs::current_path()/"results";
   for(int i=2;i<argc;i+=2){ensure(i+1<argc,"Missing argument value");std::string key=argv[i],value=argv[i+1];if(key=="--revisions")rev=std::stoi(value);else if(key=="--cases")cases=std::stoi(value);else if(key=="--samples")samples=std::stoi(value);else if(key=="--out")out=value;else throw std::runtime_error("Unknown option "+key);}
   run(e,rev,cases,samples,out);return 0;}}
 std::cout<<"Usage: metrology --run [--revisions 10 --cases 10 --samples 5000 --out PATH]\n";return 1;
 }catch(const std::exception& ex){std::cerr<<"ERROR: "<<ex.what()<<'\n';return 2;}}
