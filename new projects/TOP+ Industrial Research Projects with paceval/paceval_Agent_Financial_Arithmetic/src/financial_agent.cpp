// WP-011: Agent-Assisted Financial Scenario Arithmetic research demonstrator.
// Copyright notices of the official SDK are kept in paceval_main.{h,cpp}.
//
// Trust boundary: the caller chooses ONLY a whitelisted model and typed numbers.
// No caller-controlled formula is accepted, and no trade/payment is performed.
// paceval: creates reusable expression graphs and executes financial arithmetic.
// Host: verifies units and domains; builds deterministic sensitivity sweeps;
//       emits audit records, handles requests, and calculates native references.
#include "paceval_main.h"
#include <algorithm>
#include <array>
#include <cmath>
#include <cstddef>
#include <cstdint>
#include <filesystem>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <limits>
#include <sstream>
#include <stdexcept>
#include <string>
#include <utility>
#include <vector>
namespace fs=std::filesystem;
namespace {
constexpr size_t NV=11;
constexpr size_t SWEEP=16;
constexpr const char* VARIABLE_NAMES="rate years c0 c1 c2 c3 c4 c5 principal final payment";
using Input=std::array<double,NV>;
struct Request {std::string id,model,version,currency,rate_unit,period;Input x{};};
struct Outcome {std::string status,reason;double value=0;bool graph_reused=false;};
struct Spec {const char* id;const char* expr;};
const std::array<Spec,4> MODELS={{{"npv6","c0+c1/(1+rate)+c2/((1+rate)*(1+rate))+c3/((1+rate)*(1+rate)*(1+rate))+c4/((1+rate)*(1+rate)*(1+rate)*(1+rate))+c5/((1+rate)*(1+rate)*(1+rate)*(1+rate)*(1+rate))"},
 {"future_value","principal*exp(years*ln(1+rate))"},
 {"annuity_pv","payment*(1-exp(-(years)*ln(1+rate)))/rate"},
 {"cagr","exp(ln(final/principal)/years)-1"}}};
void insist(bool ok,const std::string&why){if(!ok)throw std::runtime_error(why);}
std::string fmt(double x){std::ostringstream o;o<<std::setprecision(17)<<x;return o.str();}
std::vector<std::string> split(const std::string&s,char sep){std::vector<std::string>f;size_t a=0;while(a<=s.size()){
 size_t b=s.find(sep,a);if(b==std::string::npos)b=s.size();f.push_back(s.substr(a,b-a));if(b==s.size())break;a=b+1;}return f;}
// Strict decimal parsing rejects missing fields, trailing junk, nan/inf and overflow.
double number(const std::string&v){insist(!v.empty()&&v.size()<=60,"missing_or_oversized_number");
 size_t end=0;double x=0;try{x=std::stod(v,&end);}catch(...){throw std::runtime_error("invalid_number");}
 insist(end==v.size()&&std::isfinite(x),"invalid_number");return x;}
Request parse_record(const std::vector<std::string>&f){insist(f.size()==17,"field_count");
 Request q;q.id=f[0];q.model=f[1];q.version=f[2];q.currency=f[3];q.rate_unit=f[4];q.period=f[5];
 insist(!q.id.empty()&&q.id.size()<=48&&q.id.find_first_not_of("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789_-")==std::string::npos,"invalid_request_id");
 for(size_t i=0;i<NV;++i){q.x[i]=number(f[6+i]);}
 return q;}
int model_index(const std::string&name){for(size_t i=0;i<MODELS.size();++i)if(name==MODELS[i].id)return int(i);return -1;}
void validate(const Request&q){
 insist(model_index(q.model)>=0,"unknown_model");
 insist(q.version=="1","unknown_version");
 insist(q.currency=="USD"||q.currency=="EUR","unsupported_currency");
 insist(q.rate_unit=="decimal_per_year","ambiguous_rate_unit");
 insist(q.period=="annual","unsupported_cashflow_frequency");
 const double rate=q.x[0],years=q.x[1];
 insist(rate>=0.001&&rate<=0.3,"rate_out_of_domain");
 insist(years>=1&&years<=30&&std::floor(years)==years,"years_out_of_domain");
 for(size_t j=2;j<=7;++j)insist(std::abs(q.x[j])<=10000000.0,"cashflow_out_of_domain");
 insist(q.x[8]>0&&q.x[8]<=10000000.0,"principal_out_of_domain");
 insist(q.x[9]>0&&q.x[9]<=100000000.0,"final_value_out_of_domain");
 insist(q.x[10]>=0&&q.x[10]<=1000000.0,"payment_out_of_domain");
}
// Independent scalar native reference, deliberately not based on paceval calls.
double native(int model,const Input&x){const double r=x[0],y=x[1];switch(model){
 case 0:{double result=x[2],denom=1;for(size_t j=1;j<6;++j){denom*=1+r;result+=x[j+2]/denom;}return result;}
 case 1:return x[8]*std::pow(1+r,y);
 case 2:return x[10]*(1-std::pow(1+r,-y))/r;
 case 3:return std::pow(x[9]/x[8],1/y)-1;
 }throw std::runtime_error("unknown native model");}
struct Engine {Engine(){insist(paceval_InitializeLibrary(nullptr),"paceval_InitializeLibrary failed");}
 ~Engine(){paceval_FreeLibrary();}Engine(const Engine&)=delete;Engine&operator=(const Engine&)=delete;};
struct Graph {PACEVAL_HANDLE h=nullptr;Graph()=default;explicit Graph(PACEVAL_HANDLE p):h(p){}
 ~Graph(){if(h)paceval_DeleteComputation(h);}Graph(const Graph&)=delete;Graph&operator=(const Graph&)=delete;
 Graph(Graph&&o)noexcept:h(o.h){o.h=nullptr;}
 Graph&operator=(Graph&&o)noexcept{if(this!=&o){if(h)paceval_DeleteComputation(h);h=o.h;o.h=nullptr;}return *this;}};
struct Runtime {
 Engine engine;
 std::vector<Graph> graphs;
 std::array<size_t,4> successful_calls{};
 Runtime(){graphs.reserve(MODELS.size());for(auto &s:MODELS){Graph g(paceval_CreateComputation(s.expr,NV,VARIABLE_NAMES,false,nullptr));
 insist(g.h!=nullptr&&!paceval_GetIsError(g.h),std::string("graph_creation_failed: ")+s.id);graphs.push_back(std::move(g));}}
 std::vector<double> evaluate(int model,const std::vector<Input>&samples,size_t batch){
 insist(model>=0&&model<int(MODELS.size()),"unknown_model");insist(!samples.empty(),"empty_batch");
 std::vector<double> output(samples.size());std::vector<double> inputs(batch*NV),values(batch);
 std::vector<int> errors(batch);for(size_t pos=0;pos<samples.size();pos+=batch){
 size_t n=std::min(batch,samples.size()-pos);for(size_t j=0;j<n;++j)for(size_t k=0;k<NV;++k)inputs[j*NV+k]=samples[pos+j][k];
 // API contract: TRUE reports an error; FALSE means normal completion.
 bool failed=paceval_dGetComputationResultExt(graphs[size_t(model)].h,inputs.data(),(unsigned long)n,values.data(),nullptr,nullptr,errors.data());
 insist(!failed,"paceval_batch_error");for(size_t j=0;j<n;++j){insist(errors[j]==0&&std::isfinite(values[j]),"paceval_nonfinite_or_error");output[pos+j]=values[j];}}
 return output;
 }
};
std::vector<Input> sweep(const Request&q){std::vector<Input> result;result.reserve(SWEEP);
 int m=model_index(q.model);for(size_t i=0;i<SWEEP;++i){Input x=q.x;double delta=(double(i)-7.5)/1000.0;
 if(m==3){x[9]*=(1+delta*4.0);}else{x[0]=std::max(0.001,std::min(0.3,x[0]+delta));}
 result.push_back(x);}return result;}
std::string header(){return "request_id,model,version,currency,rate_unit,period,rate,years,c0,c1,c2,c3,c4,c5,principal,final,payment";}
Request random_request(size_t i){Request r;r.id="TASK_"+std::to_string(1000+i);r.model=MODELS[i%4].id;r.version="1";
 r.currency=i%2?"EUR":"USD";r.rate_unit="decimal_per_year";r.period="annual";
 r.x={0.02+0.001*double(i%60), double(1+i%20), -35000.0+75.0*double(i),
  8000+double(i*3),10000+double(i*2),11000+double(i*4),9000+double(i*5),14000+double(i*6),
  15000+double(i*10),21000+double(i*15),1200+double(i*2)};return r;}
std::string record(const Request&r){std::string s=r.id+","+r.model+","+r.version+","+r.currency+","+r.rate_unit+","+r.period;
 for(double v:r.x){s+=","+fmt(v);}
 return s;}
// The rejected set is crafted, not accidental; every negative case has a named policy.
std::vector<Request> default_requests(){std::vector<Request> a;for(size_t i=0;i<100;++i)a.push_back(random_request(i));
 for(size_t i=0;i<20;++i){auto q=random_request(100+i);q.id="REJECT_"+std::to_string(i);switch(i%10){
 case 0:q.model="unapproved_formula";break;case 1:q.rate_unit="percent";break;
 case 2:q.period="monthly";break;case 3:q.version="2";break;
 case 4:q.currency="MIXED";break;case 5:q.x[0]=-0.5;break;
 case 6:q.x[1]=1.5;break;case 7:q.x[8]=0;break;
 case 8:q.x[10]=-1;break;case 9:q.x[9]=-10;break;}a.push_back(q);}
 return a;}
std::vector<Request> load_requests(const fs::path&p){std::ifstream in(p);insist(in.good(),"cannot_open_requests");
 std::string line;insist(bool(std::getline(in,line))&&line==header(),"invalid_csv_header");std::vector<Request>a;
 while(std::getline(in,line)){insist(line.size()<=4096,"csv_line_too_long");a.push_back(parse_record(split(line,',')));
 insist(a.size()<=100000,"too_many_requests");}insist(!a.empty(),"empty_request_file");return a;}
void write_header(std::ofstream&f,const std::string&line){insist(f.good(),"cannot_open_output");f<<line<<'\n'<<std::setprecision(17);}
void selftest(){for(int m=0;m<4;++m){auto r=random_request(size_t(m));auto samples=sweep(r);insist(samples.size()==SWEEP,"sweep_size");
 for(auto&x:samples)insist(std::isfinite(native(m,x)),"native_not_finite");}
 auto bad=random_request(2);bad.version="2";bool threw=false;try{validate(bad);}catch(...){threw=true;}
 insist(threw,"reject_unsupported_version");std::cout<<"PASS native arithmetic, financial schemas and rejection tests\n";}
void run_dataset(Runtime&rt,const std::vector<Request>&requests,size_t batch,const fs::path&dir){fs::create_directories(dir);
 std::ofstream task(dir/"requests_results.csv"),sens(dir/"sensitivity_results.csv"),models(dir/"models.csv"),update(dir/"model_update.csv"),input(dir/"requests.csv"),tinc(dir/"tinc_samples.csv"),tinc_stress(dir/"tinc_stress_samples.csv");
 write_header(task,"request_id,model,version,status,reason,base_result,input_currency,output_unit,graph_reused");
 write_header(sens,"request_id,model,version,sample,rate,years,principal,final,payment,paceval,native,abs_difference");
 write_header(models,"model,version,formula,variable_signature");
 write_header(update,"model,old_version,new_version,sample,old_value,new_value,native_updated,abs_difference");
 write_header(input,header());
 write_header(tinc,"sample,rate,principal,paceval_value,raw_lower,raw_upper,baseline_value,baseline_lower,baseline_upper");
 write_header(tinc_stress,"sample,rate,principal,paceval_value,raw_lower,raw_upper,baseline_value,baseline_lower,baseline_upper");
 for(auto&s:MODELS)models<<s.id<<",1,"<<s.expr<<",\""<<VARIABLE_NAMES<<"\"\n";
 size_t accepted=0,rejected=0,checks=0;double maxerr=0;
 for(const Request&q:requests){input<<record(q)<<'\n';int m=model_index(q.model);
 try{validate(q);}
 catch(const std::exception&e){task<<q.id<<','<<q.model<<','<<q.version<<",REJECTED,"<<e.what()<<",,"<<q.currency<<",,false\n";++rejected;continue;}
 auto samples=sweep(q);auto ys=rt.evaluate(m,samples,batch);
 double base=rt.evaluate(m,{q.x},batch)[0];double check=native(m,q.x);
 insist(std::abs(base-check)<=1e-9*(1+std::abs(check)),"baseline_mismatch");
 bool reused=rt.successful_calls[size_t(m)]++>0;
 task<<q.id<<','<<q.model<<','<<q.version<<",OK,none,"<<base<<','<<q.currency<<','<<(m==3?"decimal_annual_return":q.currency)<<','<<(reused?"true":"false")<<'\n';
 for(size_t j=0;j<samples.size();++j){double ref=native(m,samples[j]);double err=std::abs(ys[j]-ref);
 insist(err<=1e-9*(1+std::abs(ref)),"numerical_mismatch");maxerr=std::max(maxerr,err);++checks;
 const auto&x=samples[j];sens<<q.id<<','<<q.model<<','<<q.version<<','<<j<<','<<x[0]<<','<<x[1]<<','<<x[8]<<','<<x[9]<<','<<x[10]<<','<<ys[j]<<','<<ref<<','<<err<<'\n';}
 ++accepted;
 }
 insist(accepted>0,"no_accepted_requests");
 insist(accepted+rejected==requests.size(),"request_accounting_failed");
 // Controlled model update: a fresh reviewed NPV v2 graph scales the fifth-year
 // cash flow to 98%, without changing the original v1 graph or other models.
 std::string v2=std::string(MODELS[0].expr);const std::string needle="c5/((1+rate)";
 auto at=v2.find(needle);insist(at!=std::string::npos,"versioning_formula_pattern_missing");v2.replace(at,2,"(0.98*c5)");
 Graph v2g(paceval_CreateComputation(v2.c_str(),NV,VARIABLE_NAMES,false,nullptr));
 insist(v2g.h&&!paceval_GetIsError(v2g.h),"updated_graph_creation_failed");
 auto sample=sweep(random_request(0));auto before=rt.evaluate(0,sample,batch);
 for(size_t i=0;i<SWEEP;++i){double in[NV];for(size_t k=0;k<NV;++k)in[k]=sample[i][k];
 double newer=paceval_dGetComputationResult(v2g.h,in,nullptr,nullptr);
 double known=native(0,sample[i])-0.02*sample[i][7]/std::pow(1+sample[i][0],5);
 double err=std::abs(newer-known);insist(err<=1e-9*(1+std::abs(known)),"update_validation_failed");
 update<<"npv6,1,2,"<<i<<','<<before[i]<<','<<newer<<','<<known<<','<<err<<'\n';}
 // Financial one-period discount: two EXACTLY EQUIVALENT REAL-VALUED
 // formulas with different floating-point evaluation graphs for TINC.
 // For 1+rate > 0 (validated above), exp(-ln(1+rate)) = 1/(1+rate).
 // A direct division may return an overly narrow (even point-valued) raw
 // interval in the tested runtime. The equivalent logarithm/exponential
 // graph supplies a useful TINC interval without host-side widening.
 // Retain BOTH raw outputs for transparent comparison; no fabricated bound.
 Graph direct_tinc(paceval_CreateComputation("principal/(1+rate)",NV,VARIABLE_NAMES,true,nullptr));
 Graph improved_tinc(paceval_CreateComputation("principal*exp(-ln(1+rate))",NV,VARIABLE_NAMES,true,nullptr));
 insist(direct_tinc.h && !paceval_GetIsError(direct_tinc.h),"direct_tinc_graph_creation_failed");
 insist(improved_tinc.h && !paceval_GetIsError(improved_tinc.h),"reformulated_tinc_graph_creation_failed");
 auto write_tinc_sample=[&](std::ofstream&f,size_t sample,double rate,double principal){
   insist(rate>=0.001 && rate<=0.3 && principal>0 && std::isfinite(rate) && std::isfinite(principal),"tinc_input_out_of_domain");
   Input x{};x[0]=rate;x[8]=principal;
   double lo=0,hi=0,base_lo=0,base_hi=0;
   double value=paceval_dGetComputationResult(improved_tinc.h,x.data(),&lo,&hi);
   insist(!paceval_GetIsError(improved_tinc.h) && std::isfinite(value) && std::isfinite(lo) && std::isfinite(hi) && lo<=hi,"invalid_reformulated_tinc_result");
   double baseline=paceval_dGetComputationResult(direct_tinc.h,x.data(),&base_lo,&base_hi);
   insist(!paceval_GetIsError(direct_tinc.h) && std::isfinite(baseline) && std::isfinite(base_lo) && std::isfinite(base_hi) && base_lo<=base_hi,"invalid_direct_tinc_result");
   // Verify the CENTER values against the native (same-input) rational
   // expression; high-precision inclusion is independently tested in Python.
   double native_discount=principal/(1+rate);
   insist(std::abs(value-native_discount)<=1e-9*(1+std::abs(native_discount)),"tinc_reformulation_value_mismatch");
   f<<sample<<','<<rate<<','<<principal<<','<<value<<','<<lo<<','<<hi<<','<<baseline<<','<<base_lo<<','<<base_hi<<'\n';
 };
 // Original fixed cases include the two near-point degeneracies of direct TINC.
 for(size_t i=0;i<24;++i){const auto x=random_request(i).x;write_tinc_sample(tinc,i,x[0],x[8]);}
 // Deterministic broader coverage (the same approved input domain, no RNG
 // library/distribution differences across standard-library implementations).
 std::uint64_t state=123456789ULL;
 for(size_t i=0;i<1500;++i){
   state=state*6364136223846793005ULL+1442695040888963407ULL;
   const double rate=0.001+0.299*(double((state>>12)%1000000ULL)/1000000.0);
   state=state*6364136223846793005ULL+1442695040888963407ULL;
   const double principal=1.0+999999.0*(double((state>>12)%1000000ULL)/1000000.0);
   write_tinc_sample(tinc_stress,i,rate,principal);
 }
 std::cout<<"PASS financial requests="<<requests.size()<<" accepted="<<accepted<<" rejected="<<rejected
 <<" sensitivity_checks="<<checks<<" max_abs_error="<<fmt(maxerr)<<" updated_checks=16\n";
}
void serve(Runtime&rt){std::string line;while(std::getline(std::cin,line)){if(line.size()>4096){std::cout<<"INVALID|REJECTED|input_too_long\n"<<std::flush;continue;}
 auto fields=split(line,'|');std::string id=fields.empty()?"INVALID":fields[0];try{Request q=parse_record(fields);validate(q);
 int m=model_index(q.model);auto ys=rt.evaluate(m,{q.x},1);bool reused=rt.successful_calls[size_t(m)]++>0;
 std::cout<<q.id<<"|OK|"<<fmt(ys[0])<<"|"<<(reused?"true":"false")<<"|"<<q.version<<"\n"<<std::flush;
 }catch(const std::exception&e){std::cout<<id<<"|REJECTED|"<<e.what()<<"\n"<<std::flush;}}}
}
int main(int argc,char**argv){try{
 std::string mode="--demo",input="",out="results";size_t batch=32;
 for(int i=1;i<argc;++i){std::string arg=argv[i];if(arg=="--demo"||arg=="--serve"||arg=="--self-test")mode=arg;
 else if(arg=="--input"&&i+1<argc)input=argv[++i];else if(arg=="--out"&&i+1<argc)out=argv[++i];
 else if(arg=="--batch"&&i+1<argc){std::string v=argv[++i];size_t at=0;unsigned long k=std::stoul(v,&at);insist(at==v.size()&&k>0&&k<=4096,"invalid_batch");batch=k;}
 else throw std::runtime_error("unknown_cli_option: "+arg);}
 if(mode=="--self-test"){selftest();return 0;}
 Runtime rt;if(mode=="--serve"){serve(rt);return 0;}
 selftest();auto requests=input.empty()?default_requests():load_requests(input);
 run_dataset(rt,requests,batch,out);return 0;
 }catch(const std::exception&e){std::cerr<<"FAIL: "<<e.what()<<'\n';return 1;}}
