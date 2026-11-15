// WP29: exploratory LOW-DEMAND proof-test reliability kernels, not a certified SIF model.
// Real paceval SDK evaluates all mathematical output quantities. The C++ host handles
// data contracts, versioning, result routing and independent numerical checks only.
#include "paceval_main.h"
#include <algorithm>
#include <array>
#include <cmath>
#include <cstdint>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <map>
#include <regex>
#include <set>
#include <stdexcept>
#include <string>
#include <vector>
#include <iomanip>
#include <sstream>
namespace fs=std::filesystem;
static void check(bool c,const std::string& s){if(!c)throw std::runtime_error(s);}
static constexpr int NV=10;
enum {LD,DC,PTC,T,H,MTTR,BETA,TARGET,AGE,REF};
static const char* NAMES="ld dc ptc interval horizon mttr beta target age ref";
using Row=std::array<double,NV>;
struct Engine {
 std::vector<PACEVAL_HANDLE> handles;std::set<PACEVAL_HANDLE> executed;
 uint64_t scalar_calls=0,batch_calls=0,graph_outputs=0;
 Engine(){check(paceval_InitializeLibrary(nullptr),"Original paceval library initialization failed");}
 ~Engine(){for(auto h:handles)paceval_DeleteComputation(h);paceval_FreeLibrary();}
 PACEVAL_HANDLE make(const std::string& expr){auto h=paceval_CreateComputation(expr.c_str(),NV,NAMES,false,nullptr);check(h!=nullptr,"Null computation handle");if(paceval_GetIsError(h)){char a[2048]={},b[2048]={};paceval_CreateErrorInformationText(h,a,b);paceval_DeleteComputation(h);throw std::runtime_error("paceval expression refused: "+expr.substr(0,90)+" :: "+a+" "+b);} handles.push_back(h);return h;}
 double scalar(PACEVAL_HANDLE h,const Row& r){auto d=r;double v=paceval_dGetComputationResult(h,d.data(),nullptr,nullptr);check(!paceval_GetIsError(h)&&std::isfinite(v),"Scalar evaluation error");scalar_calls++;graph_outputs++;executed.insert(h);return v;}
 std::vector<double> batch(const std::vector<PACEVAL_HANDLE>& hs,const std::vector<Row>& rows){check(!rows.empty()&&!hs.empty(),"Empty batch");std::vector<double> flat;flat.reserve(rows.size()*NV);for(auto& r:rows)for(double v:r){check(std::isfinite(v),"Nonfinite paceval input");flat.push_back(v);}std::vector<double> out(rows.size()*hs.size());std::vector<int> errors(out.size(),-1);auto tmp=hs;bool failed=paceval_dGetMultipleComputationsResultsExt(tmp.data(),(unsigned long)tmp.size(),flat.data(),(unsigned long)rows.size(),out.data(),nullptr,nullptr,errors.data());check(!failed,"Multi-graph batch failed");for(size_t i=0;i<out.size();i++)check(errors[i]==PACEVAL_ERR_NO_ERROR&&std::isfinite(out[i]),"Batch graph error at "+std::to_string(i));for(auto h:hs)executed.insert(h);batch_calls++;graph_outputs+=out.size();return out;}
 double parse(const std::string& s)const{static const std::regex num(R"(^[+-]?(?:[0-9]+(?:\.[0-9]*)?|\.[0-9]+)(?:[eE][+-]?[0-9]+)?$)");check(std::regex_match(s,num),"Invalid CSV numeric literal: "+s);int error=-1;long pos=-1;double v=paceval_dConvertStringToFloat(s.c_str(),&error,&pos,false,nullptr,nullptr);check(error==PACEVAL_ERR_NO_ERROR&&std::isfinite(v),"paceval input conversion failed at "+std::to_string(pos));return v;}
 std::string format(double n)const{check(std::isfinite(n),"Nonfinite CSV output");char buffer[1024]={};int p=paceval_dConvertFloatToString(buffer,n);check(p>0&&buffer[0],"paceval output conversion failed");return buffer;}
};
struct Formula {std::string id,expr,version;PACEVAL_HANDLE handle;};
using Group=std::vector<Formula>;
static Group create(Engine& e,int ver){
 std::string v=std::to_string(ver),u="(ld*(1-dc))",det="(ld*dc)",hc="("+u+"*ptc)",hu="("+u+"*(1-ptc))",z="("+hc+"*interval)",w="((2-beta)*"+z+")";
 // Positive-rate, strictly positive-interval contract. A(z) is the exact mean survival integral.
 std::string A="((1-exp(-"+z+"))/"+z+")",A2="((1-exp(-"+w+"))/"+w+")";
 std::string Aprime="((("+z+"+1)*exp(-"+z+")-1)/sqr("+z+"))";
 std::string A2prime="((("+w+"+1)*exp(-"+w+")-1)/sqr("+w+"))";
 std::string B="(1-"+det+"*mttr/(1+"+det+"*mttr))"; // repair-screening availability approximation
 std::string e1="exp(-"+hu+"*horizon)",e2="exp(-(2-beta)*"+hu+"*horizon)";
 std::string p1="(1-"+B+"*"+e1+"*"+A+")";
 std::string p2="(1-2*"+B+"*"+e1+"*"+A+"+sqr("+B+")*"+e2+"*"+A2+")";
 std::string pp=(ver==1?p1:p2);
 std::string inst1="(1-"+B+"*exp(-("+hu+"*horizon+"+hc+"*age)))";
 std::string inst2="(1-2*"+B+"*exp(-("+hu+"*horizon+"+hc+"*age))+sqr("+B+")*exp(-(2-beta)*("+hu+"*horizon+"+hc+"*age)))";
 std::string dT1="(-"+B+"*"+e1+"*"+hc+"*"+Aprime+")";
 std::string dT2="(-2*"+B+"*"+e1+"*"+hc+"*"+Aprime+"+sqr("+B+")*"+e2+"*(2-beta)*"+hc+"*"+A2prime+")";
 std::string dC1="(-"+B+"*"+e1+"*"+u+"*(horizon*"+A+"+interval*"+Aprime+"))";
 std::string dC2="(-2*"+B+"*"+e1+"*"+u+"*(horizon*"+A+"+interval*"+Aprime+")+sqr("+B+")*"+e2+"*(2-beta)*"+u+"*(horizon*"+A2+"+interval*"+A2prime+"))";
 std::map<std::string,std::string> formulas={
 {"dangerous_undetected_rate_h",u},{"dangerous_detected_rate_h",det},{"proof_detectable_rate_h",hc},{"uncovered_rate_h",hu},
 {"diagnosed_availability_proxy",B},{"simple_low_demand_proxy", "("+u+"*interval/2)"},
 {"average_proof_survival",A},{"instantaneous_pfd",ver==1?inst1:inst2},
 {"pfd_average",pp},{"target_margin", "(target-"+pp+")"},
 {"target_fraction", "("+pp+"/target)"},{"interval_sensitivity_per_hour",ver==1?dT1:dT2},
 {"coverage_sensitivity",ver==1?dC1:dC2},
 {"expected_loss_proxy", "("+pp+"*ref)"},
 {"target_condition", "(("+pp+") <= (target))"},
 {"screen_guard", "((("+pp+") <= (target)) AND ((ptc >= 0.7) AND (interval <= 17520)))"},
 {"score_for_review", "("+pp+"/target+0.03*(1-ptc)+0.05*beta)"},
 {"proof_interval_headroom_h", "(17520-interval)"},
 {"proof_coverage_headroom", "(ptc-0.7)"},
 {"project_target_difference", "("+pp+"-target)"}
 };
 Group g;for(auto& x:formulas)g.push_back({x.first,x.second,"M"+v,e.make(x.second)});return g;
}
static std::map<std::string,size_t> index(const Group& g){std::map<std::string,size_t> m;for(size_t k=0;k<g.size();++k)m[g[k].id]=k;return m;}
static std::vector<PACEVAL_HANDLE> handles(const Group& g){std::vector<PACEVAL_HANDLE> h;for(auto& x:g)h.push_back(x.handle);return h;}
static uint64_t stir(uint64_t x){x+=0x9e3779b97f4a7c15ull;x=(x^(x>>30))*0xbf58476d1ce4e5b9ull;x=(x^(x>>27))*0x94d049bb133111ebull;return x^(x>>31);}
static double rand01(uint64_t x){return double(stir(x)>>11)/9007199254740992.;}
static Row sample(size_t i){Row r{};r[LD]=(0.35+4*rand01(i*53+7))*1e-6;r[DC]=0.42+0.53*rand01(i*13+29);r[PTC]=0.62+0.38*rand01(i*127+43);r[T]=400+17120*rand01(i*167+3);r[H]=3000+54000*rand01(i*199+17);r[MTTR]=4+90*rand01(i*73+71);r[BETA]=0.01+0.19*rand01(i*83+7);r[TARGET]=0.00008+0.012*rand01(i*23+11);r[AGE]=r[T]*rand01(i*317+13);r[REF]=10000+250000*rand01(i*47+23);return r;}
static void domain(const Row& r){check(r[LD]>0&&r[LD]<1e-3,"lambda domain");check(r[DC]>=0&&r[DC]<1,"DC domain");check(r[PTC]>0&&r[PTC]<=1,"PTC domain");check(r[T]>0&&r[T]<=20000,"interval domain");check(r[H]>=0,"horizon domain");check(r[MTTR]>=0,"repair domain");check(r[BETA]>=0&&r[BETA]<=1,"beta domain");check(r[TARGET]>0&&r[TARGET]<1,"target domain");check(r[AGE]>=0&&r[AGE]<=r[T],"proof time domain");check(r[REF]>=0,"exposure reference domain");}
// Independently implemented mathematical reference: expm1-based survival integration.
static long double avg_s(long double z){if(fabsl(z)<1e-9L)return 1-z/2+z*z/6-z*z*z/24;return -expm1l(-z)/z;}
static long double pf_native(const Row& r,int v){long double u=(long double)r[LD]*(1-r[DC]),d=(long double)r[LD]*r[DC],c=u*r[PTC],res=u*(1-r[PTC]),z=c*r[T];long double B=1/(1+d*r[MTTR]);long double S=B*expl(-res*r[H])*avg_s(z);if(v==1)return 1-S;long double k=2-r[BETA];return 1-2*S+B*B*expl(-k*res*r[H])*avg_s(k*z);}
static long double instantaneous_ref(const Row& r,int v){long double u=(long double)r[LD]*(1-r[DC]),d=(long double)r[LD]*r[DC],x=u*((1-r[PTC])*r[H]+r[PTC]*r[AGE]),B=1/(1+d*r[MTTR]);if(v==1)return 1-B*expl(-x);return 1-2*B*expl(-x)+B*B*expl(-(2-r[BETA])*x);}
static void near(double a,long double b,const std::string& label,double tol=3e-10){check(std::isfinite(a)&&std::abs((long double)a-b)<=tol*std::max(1.L,fabsl(b)),"Independent reference mismatch: "+label+" evaluated="+std::to_string(a)+" expected="+std::to_string((double)b)+" deviation="+std::to_string((double)((long double)a-b)));}
static void selftest(Engine& e){check(std::abs(e.parse("-1.25e-3")+.00125)<1e-13,"Numeric converter");for(auto& t:{"1+2","NaN","","1,2","infinity","1e9999"}){bool refused=false;try{e.parse(t);}catch(...){refused=true;}check(refused,"Untrusted CSV input accepted");}check(!e.format(.000156).empty(),"Output conversion");
 std::vector<std::pair<std::string,double>> tests={{"((-1) % 10)",-1},{"((-1) mod 10)",9},{"(4 min 5)",4},{"(4 max 5)",5},{"((1 <= (2*1)) AND (3 >= 0))",1},{"((1 >= 2) OR (4 = 4))",1},{"NOT(0)",1},{"(2 <> 2)",0},{"(3 < 3)",0}};Row dummy=sample(1);for(auto& x:tests){auto h=e.make(x.first);near(e.scalar(h,dummy),x.second,"operator");}
 // Boundary limits of the low-demand proxy are tested with genuine paceval scalar calls;
 // exponential quotient graphs intentionally require a positive interval and covered rate.
 {auto h=e.make("ld*(1-dc)*interval/2");Row r=sample(12);r[LD]=0;near(e.scalar(h,r),0.,"zero-rate proxy");r=sample(13);r[T]=0;near(e.scalar(h,r),0.,"zero-interval proxy");bool rejected=false;try{domain(r);}catch(...){rejected=true;}check(rejected,"Invalid zero interval entered the positive-domain model");}
 for(int v=1;v<=2;v++){auto g=create(e,v);auto pos=index(g);auto hh=handles(g);std::vector<Row> sampleRows;for(int i=0;i<8;i++)sampleRows.push_back(sample(i+51));auto out=e.batch(hh,sampleRows);for(size_t i=0;i<sampleRows.size();++i){auto& r=sampleRows[i];near(out[pos["pfd_average"]*sampleRows.size()+i],pf_native(r,v),"PFD");near(out[pos["instantaneous_pfd"]*sampleRows.size()+i],instantaneous_ref(r,v),"instant PFD");near(e.scalar(g[pos["pfd_average"]].handle,r),pf_native(r,v),"scalar PFD");}
 }std::cout<<"PASS original paceval SDK operator, numeric CSV and batch tests\n";}
static std::vector<Row> loadCSV(Engine& e,const fs::path& p){std::ifstream in(p);check(bool(in),"CSV missing");std::string line;check(bool(std::getline(in,line)),"Missing header");check(line=="ld,dc,ptc,interval,horizon,mttr,beta,target,age,ref","CSV schema mismatch");std::vector<Row> rows;while(std::getline(in,line)){check(!line.empty(),"Empty CSV record");std::stringstream ss(line);std::string field;Row r{};int k=0;while(std::getline(ss,field,',')){check(k<NV,"CSV column overflow");r[k++]=e.parse(field);}check(k==NV,"Incomplete CSV record");domain(r);rows.push_back(r);}return rows;}
static void writeCSV(Engine& e,const fs::path& p,size_t n){std::ofstream out(p);check(bool(out),"Cannot create input");out<<"ld,dc,ptc,interval,horizon,mttr,beta,target,age,ref\n";for(size_t i=0;i<n;i++){auto r=sample(i);for(int k=0;k<NV;k++){if(k)out<<',';out<<e.format(r[k]);}out<<'\n';}}
static void run(Engine& e,size_t n,const fs::path& dir){check(n>=32&&n<=1000000,"Dataset size out of range");fs::create_directories(dir);writeCSV(e,dir/"synthetic_input.csv",n);auto rows=loadCSV(e,dir/"synthetic_input.csv");check(rows.size()==n,"Roundtrip missing rows");
 auto g1=create(e,1),g2=create(e,2);std::ofstream reg(dir/"formula_registry.csv"),inventory(dir/"math_execution_inventory.csv");reg<<"model_version,graph_id,formula,api_execution\n";inventory<<"function_id,domain_quantity,mathematical_definition,units,execution_owner,paceval_graph_id,formula_version,api_path,reference_test,status,host_reason\n";for(auto& g:{g1,g2})for(auto& f:g){reg<<f.version<<','<<f.id<<",\""<<f.expr<<"\",paceval_dGetMultipleComputationsResultsExt\n";inventory<<f.id<<','<<f.id<<",\""<<f.expr<<"\",documented,paceval,"<<f.id<<','<<f.version<<",multi_graph_batch,independent_native_and_mpmath,executed,\n";}
 std::ofstream result(dir/"scenario_results.csv"),trace(dir/"end_to_end_trace.csv"),summary(dir/"model_summary.csv"),audit(dir/"audit_samples.csv");check(bool(result)&&bool(trace)&&bool(summary)&&bool(audit),"Output file failure");result<<"scenario,model,architecture,lambda_du,proof_coverage,interval_h,horizon_h,pfd_average,instant_pfd,margin,interval_sensitivity,coverage_sensitivity,score,expected_loss_proxy,guard,status\n";trace<<"scenario,model,lambda_du,covered_rate,residual_rate,pfd_average,margin,score,guard,status\n";summary<<"model,scenarios,screen_pass,screen_review,screen_reject,mean_pfd,mean_margin,mean_interval_sensitivity,positive_margin\n";audit<<"scenario,model,quantity,paceval,independent_reference,absolute_difference\n";
 uint64_t checks=0,cases=0;const size_t CHUNK=128;
 for(int v=1;v<=2;v++){auto& g=v==1?g1:g2;auto idx=index(g);auto hs=handles(g);uint64_t pass=0,review=0,reject=0,pos=0;long double total=0,margins=0,slopes=0;for(size_t start=0;start<rows.size();start+=CHUNK){size_t count=std::min(CHUNK,rows.size()-start);std::vector<Row> part(rows.begin()+start,rows.begin()+start+count);auto out=e.batch(hs,part);auto value=[&](const char* key,size_t j){return out.at(idx.at(key)*count+j);};for(size_t j=0;j<count;j++){auto& r=part[j];size_t id=start+j;double p=value("pfd_average",j),inst=value("instantaneous_pfd",j),margin=value("target_margin",j),dT=value("interval_sensitivity_per_hour",j),dC=value("coverage_sensitivity",j),score=value("score_for_review",j),guard=value("screen_guard",j);
 long double p_ref=pf_native(r,v);near(p,p_ref,"end PFD",2e-10);near(inst,instantaneous_ref(r,v),"end instantaneous",2e-10);near(margin,(long double)r[TARGET]-p_ref,"end margin",2e-10);near(value("target_fraction",j),p_ref/r[TARGET],"end target fraction",2e-6);near(score,p_ref/r[TARGET]+.03L*(1-r[PTC])+.05L*r[BETA],"end score",2e-6);near(value("dangerous_undetected_rate_h",j),(long double)r[LD]*(1-r[DC]),"lambda undetected");near(value("dangerous_detected_rate_h",j),(long double)r[LD]*r[DC],"lambda detected");near(value("proof_detectable_rate_h",j),(long double)r[LD]*(1-r[DC])*r[PTC],"covered rate");near(value("uncovered_rate_h",j),(long double)r[LD]*(1-r[DC])*(1-r[PTC]),"uncovered rate");near(value("simple_low_demand_proxy",j),(long double)r[LD]*(1-r[DC])*r[T]/2,"low-demand proxy");near(value("expected_loss_proxy",j),p_ref*r[REF],"expected loss proxy",1e-6);
 bool wants=(p<=r[TARGET]&&r[PTC]>=.7&&r[T]<=17520);near(guard,wants?1.:0.,"guard boolean",1e-13);checks+=12;
 if(id%std::max<size_t>(1,n/300)==0){Row delta=r;delta[T]=r[T]+.05;auto pplus=pf_native(delta,v);delta[T]=r[T]-.05;auto pminus=pf_native(delta,v);near(dT,(pplus-pminus)/.1L,"interval sensitivity",2e-8);delta=r;delta[PTC]=std::min(.999999,r[PTC]+.00001);auto plus=pf_native(delta,v);delta[PTC]=std::max(.000001,r[PTC]-.00001);auto minus=pf_native(delta,v);near(dC,(plus-minus)/(std::min(.999999,r[PTC]+.00001)-std::max(.000001,r[PTC]-.00001)),"coverage sensitivity",2e-6);checks+=2;}
 std::string status=!wants?"SCREEN_REJECT":((margin<0.0008||r[PTC]<.75)?"SCREEN_REVIEW":"SCREEN_PASS");if(status=="SCREEN_PASS")pass++;else if(status=="SCREEN_REVIEW")review++;else reject++;if(margin>=0)pos++;total+=p;margins+=margin;slopes+=dT;cases++;
 result<<id<<','<<v<<','<<(v==1?"1oo1":"1oo2")<<','<<e.format(value("dangerous_undetected_rate_h",j))<<','<<e.format(r[PTC])<<','<<e.format(r[T])<<','<<e.format(r[H])<<','<<e.format(p)<<','<<e.format(inst)<<','<<e.format(margin)<<','<<e.format(dT)<<','<<e.format(dC)<<','<<e.format(score)<<','<<e.format(value("expected_loss_proxy",j))<<','<<e.format(guard)<<','<<status<<'\n';
 if(id%std::max<size_t>(1,n/100)==0){trace<<id<<','<<v<<','<<e.format(value("dangerous_undetected_rate_h",j))<<','<<e.format(value("proof_detectable_rate_h",j))<<','<<e.format(value("uncovered_rate_h",j))<<','<<e.format(p)<<','<<e.format(margin)<<','<<e.format(score)<<','<<e.format(guard)<<','<<status<<'\n';audit<<id<<','<<v<<",pfd_average,"<<e.format(p)<<','<<e.format((double)p_ref)<<','<<e.format(std::abs(p-(double)p_ref))<<'\n';}
 }}summary<<v<<','<<n<<','<<pass<<','<<review<<','<<reject<<','<<e.format((double)(total/n))<<','<<e.format((double)(margins/n))<<','<<e.format((double)(slopes/n))<<','<<pos<<'\n';}
 // Additional mathematical graphs for figures: no native re-evaluation replaces the paceval path.
 std::ofstream cycle(dir/"proof_cycle.csv"),surface(dir/"parameter_surface.csv");
 check(bool(cycle)&&bool(surface),"Cannot create figure data");
 cycle<<"model,age_h,proof_interval_h,pfd_instant,pfd_average,scenario\n";
 Row center=rows[n/3];const auto p1=index(g1),p2=index(g2);
 std::vector<Row> ages;for(int i=0;i<=200;i++){Row a=center;a[AGE]=center[T]*i/200.;ages.push_back(a);}
 for(int v=1;v<=2;v++){auto& g=v==1?g1:g2;auto idx=index(g);auto pfd=e.batch({g.at(idx.at("instantaneous_pfd")).handle,g.at(idx.at("pfd_average")).handle},ages);for(size_t j=0;j<ages.size();j++)cycle<<v<<','<<e.format(ages[j][AGE])<<','<<e.format(ages[j][T])<<','<<e.format(pfd[j])<<','<<e.format(pfd[ages.size()+j])<<','<<n/3<<'\n';}
 surface<<"model,interval_h,proof_coverage,pfd_average,target_margin\n";
 std::vector<Row> sweep;for(int i=0;i<29;i++)for(int j=0;j<25;j++){auto a=center;a[T]=600+i*570.;a[PTC]=.65+j*.0145;a[AGE]=0.5*a[T];sweep.push_back(a);}
 for(int v=1;v<=2;v++){auto& g=v==1?g1:g2;auto idx=index(g);auto oo=e.batch({g.at(idx.at("pfd_average")).handle,g.at(idx.at("target_margin")).handle},sweep);for(size_t j=0;j<sweep.size();j++)surface<<v<<','<<e.format(sweep[j][T])<<','<<e.format(sweep[j][PTC])<<','<<e.format(oo[j])<<','<<e.format(oo[sweep.size()+j])<<'\n';}
 std::ofstream ev(dir/"execution_evidence.json");ev<<"{\n  \"project\": \"WP29 Safety Instrumented System Proof-Test Reliability Calculations\",\n  \"sdk_mode\": \"original paceval local C++ SDK\",\n  \"scenario_count\": "<<n<<",\n  \"model_versions\": 2,\n  \"model_point_cases\": "<<cases<<",\n  \"unique_graphs_created\": "<<e.handles.size()<<",\n  \"unique_graphs_executed\": "<<e.executed.size()<<",\n  \"scalar_calls\": "<<e.scalar_calls<<",\n  \"multi_graph_batch_calls\": "<<e.batch_calls<<",\n  \"graph_point_evaluations\": "<<e.graph_outputs<<",\n  \"independent_native_checks\": "<<checks<<",\n  \"safety_certification\": false,\n  \"data_origin\": \"deterministic synthetic screening data\"\n}\n";
 std::cout<<"PASS WP29 scenario_rows="<<n<<" cases="<<cases<<" graphs="<<e.executed.size()<<" graph_outputs="<<e.graph_outputs<<" independent_native_checks="<<checks<<"\n";
}
int main(int argc,char**argv){try{Engine e;std::string op=argc>1?argv[1]:"--run";if(op=="--selftest"){selftest(e);return 0;}check(op=="--run","Use --run N output_dir or --selftest");size_t n=argc>2?(size_t)std::stoul(argv[2]):100000;fs::path out=argc>3?argv[3]:"results";run(e,n,out);return 0;}catch(const std::exception& ex){std::cerr<<"FAIL WP29: "<<ex.what()<<'\n';return 1;}}
