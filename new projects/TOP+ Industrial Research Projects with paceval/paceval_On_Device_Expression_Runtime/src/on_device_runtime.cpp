// paceval On-Device Reusable Expression Runtime: reproducible Linux research demonstrator.
// Directly includes the official SDK; paceval_main.cpp is compiled by CMake and the
// compatible architecture-specific proprietary runtime is linked at build time.
//
// Boundaries: the C++ host owns model approvals, input validation, graph lifetime,
// model versions, batching, CSV output and independent reference comparisons.
// paceval owns the mathematical expression execution, including its batch API.
// No claim of bounded memory, real-time deadlines, or ARM testing is made here.
#include "paceval_main.h"
#include <algorithm>
#include <array>
#include <cmath>
#include <cstddef>
#include <cstdlib>
#include <filesystem>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <limits>
#include <numeric>
#include <sstream>
#include <stdexcept>
#include <string>
#include <vector>
namespace fs = std::filesystem;
namespace {
constexpr size_t kNVar = 5;
using Input = std::array<double, kNVar>;  // x, a, b, c, d; fixed declared order
constexpr const char* kVars = "x a b c d";
struct Config { size_t models=1000, samples=32, batch=64; fs::path out="results"; bool self_test=false; };
struct Runtime {
 Runtime() { if(!paceval_InitializeLibrary(nullptr)) throw std::runtime_error("paceval_InitializeLibrary failed"); }
 ~Runtime() { paceval_FreeLibrary(); }
 Runtime(const Runtime&)=delete; Runtime& operator=(const Runtime&)=delete;
};
struct OwnedGraph {
 PACEVAL_HANDLE h=nullptr;
 explicit OwnedGraph(PACEVAL_HANDLE graph=nullptr):h(graph){}
 ~OwnedGraph(){if(h) paceval_DeleteComputation(h);}
 OwnedGraph(const OwnedGraph&)=delete; OwnedGraph& operator=(const OwnedGraph&)=delete;
 OwnedGraph(OwnedGraph&& o) noexcept:h(o.h){o.h=nullptr;}
 OwnedGraph& operator=(OwnedGraph&& o) noexcept { if(this!=&o){ if(h) paceval_DeleteComputation(h); h=o.h; o.h=nullptr;} return *this; }
};
void insist(bool p,const std::string& message){if(!p) throw std::runtime_error(message);}
size_t positive(const std::string& v,const char* name,size_t limit){
 if(v.empty() || v[0]=='-') throw std::runtime_error(std::string("invalid ")+name);
 size_t used=0; auto x=std::stoull(v,&used); if(used!=v.size()||x<1||x>limit) throw std::runtime_error(std::string("invalid ")+name); return static_cast<size_t>(x);
}
Config parse(int argc,char** argv){
 Config c;
 for(int i=1;i<argc;++i){std::string s=argv[i];
  if(s=="--self-test") {c.self_test=true;continue;}
  if(i+1>=argc) throw std::runtime_error("missing argument for "+s);
  std::string v=argv[++i];
  if(s=="--models") c.models=positive(v,"models",10000);
  else if(s=="--samples") c.samples=positive(v,"samples",1000000);
  else if(s=="--batch") c.batch=positive(v,"batch",4096);
  else if(s=="--out") c.out=v;
  else throw std::runtime_error("unknown argument: "+s);
 }
 if(c.out.empty())throw std::runtime_error("empty output path");
 if(c.models*c.samples > 1500000) throw std::runtime_error("requested output exceeds 1.5 million result rows");
 return c;
}
// Explicitly bounded synthetic inputs; no real sensor units or calibration are implied.
Input input_for(size_t index,size_t model_id){
 double x=0.025+3.6*(static_cast<double>(index%32)/31.0); // 32-point bounded sweep; repeats for larger workloads
 double a=0.45+0.015*(model_id%11);
 double b=0.32+0.008*(model_id%13);
 double c=0.17+0.007*(model_id%17);
 double d=0.21+0.009*(model_id%7);
 return {x,a,b,c,d};
}
// Five distinct mathematical families. The per-model numerical literal gives
// every version a distinct mathematical expression without imposing engine limits.
std::string make_formula(int family,double offset){
 std::ostringstream o; o<<std::fixed<<std::setprecision(9)<<offset;
 const char* base[] = {
 "a*sin(b*x)+c*exp(-(d*x))",
 "a*cos(b*x)+c/(1+d*x*x)",
 "a*x*x+b*x+c*exp(-(d*x))",
 "a*tanh(b*x)+c*sin(d*x)",
 "a*ln(1+b*x*x)+c*sqrt(1+d*x*x)"
 };
 return std::string("(")+base[family]+")+("+o.str()+")";
}
// Separate native C++ math oracle; paceval output must agree point-wise.
double native_value(int family,double offset,const Input& v){
 double x=v[0],a=v[1],b=v[2],c=v[3],d=v[4];
 switch(family){
  case 0:return a*std::sin(b*x)+c*std::exp(-d*x)+offset;
  case 1:return a*std::cos(b*x)+c/(1+d*x*x)+offset;
  case 2:return a*x*x+b*x+c*std::exp(-d*x)+offset;
  case 3:return a*std::tanh(b*x)+c*std::sin(d*x)+offset;
  case 4:return a*std::log(1+b*x*x)+c*std::sqrt(1+d*x*x)+offset;
 }
 throw std::runtime_error("unknown family");
}
OwnedGraph create(const std::string& formula,bool tinc=false){
 OwnedGraph o(paceval_CreateComputation(formula.c_str(),static_cast<unsigned long>(kNVar),kVars,tinc,nullptr));
 insist(o.h!=nullptr,"paceval returned a null graph");
 insist(!paceval_GetIsError(o.h),"paceval could not create graph for: "+formula);
 return o;
}
bool near(double a,double b){return std::isfinite(a)&&std::isfinite(b)&&std::abs(a-b)<=2.0e-11*(1+std::abs(b));}
// vector inputs are laid out sample-major: [x,a,b,c,d] repeated for each input.
std::vector<double> batch_eval(PACEVAL_HANDLE handle,const std::vector<Input>& in,size_t batch){
 std::vector<double> outputs(in.size());
 std::vector<double> vars(batch*kNVar); std::vector<double> results(batch);
 std::vector<int> errors(batch);
 for(size_t start=0; start<in.size(); start+=batch){
  size_t n=std::min(batch,in.size()-start);
  for(size_t j=0;j<n;++j){for(size_t k=0;k<kNVar;++k){
    insist(std::isfinite(in[start+j][k]),"nonfinite input rejected before paceval evaluation");
    vars[j*kNVar+k]=in[start+j][k];
  }}
  bool batch_has_error=paceval_dGetComputationResultExt(handle,vars.data(),static_cast<unsigned long>(n),results.data(),nullptr,nullptr,errors.data());
  insist(!batch_has_error,"paceval batch evaluation reported failure");
  for(size_t j=0;j<n;++j){
   insist(errors[j]==0 && std::isfinite(results[j]),"invalid paceval batch result");
   outputs[start+j]=results[j];
  }
 }
 return outputs;
}
void csv_header(std::ofstream& f,const std::string& h){insist(f.good(),"cannot open output");f<<h<<'\n';f<<std::setprecision(17);}
void run_native_selftest(){
 insist(near(native_value(0,0,{0,1,1,0,1}),0),"zero sinusoid");
 insist(near(native_value(2,0,{2,1,2,3,4}),4+4+3*std::exp(-8)),"quadratic");
 for(int family=0;family<5;++family){auto f=make_formula(family,0.125);insist(f.size()>20,"formula generation");}
 std::cout<<"PASS native self-test\n";
}
void run(const Config& cfg){
 fs::create_directories(cfg.out);
 run_native_selftest();
 Runtime runtime;
 std::ofstream models(cfg.out/"models.csv");csv_header(models,"id,family,version,offset,formula");
 std::ofstream values(cfg.out/"evaluations.csv");csv_header(values,"model_id,family,version,sample,x,a,b,c,d,paceval_value,native_value,abs_error");
 std::ofstream updates(cfg.out/"model_update.csv");csv_header(updates,"model_id,sample,previous_version,new_version,previous_score,updated_score,expected_delta,abs_error");
 std::ofstream tinc(cfg.out/"tinc_samples.csv");csv_header(tinc,"sample,x,a,b,c,d,result,lower,upper,native_value");
 std::ofstream meta(cfg.out/"run_summary.txt");insist(meta.good(),"cannot create run_summary");
 meta<<"study=on_device_reusable_expression_runtime\nmodels="<<cfg.models<<"\nsamples_per_model="<<cfg.samples<<"\n";
 meta<<"batch_size="<<cfg.batch<<"\nsynthetic=true\n";
#if defined(__x86_64__)
 meta<<"architecture=x86_64\n";
#elif defined(__aarch64__)
 meta<<"architecture=aarch64\n";
#else
 meta<<"architecture=other\n";
#endif
 std::vector<OwnedGraph> graphs; graphs.reserve(cfg.models);
 double max_diff=0; size_t checks=0;
 for(size_t i=0;i<cfg.models;++i){
  int family=static_cast<int>(i%5);
  double offset=static_cast<double>(i+1)/10000.0;
  auto formula=make_formula(family,offset);
  auto graph=create(formula);
  models<<i<<','<<family<<",1,"<<offset<<','<<formula<<'\n';
  graphs.push_back(std::move(graph));
  std::vector<Input> in; in.reserve(cfg.samples);
  for(size_t s=0;s<cfg.samples;++s) in.push_back(input_for(s,i));
  auto out=batch_eval(graphs.back().h,in,cfg.batch);
  for(size_t s=0;s<cfg.samples;++s){
   double ref=native_value(family,offset,in[s]);
   double err=std::abs(out[s]-ref); max_diff=std::max(max_diff,err);
   insist(near(out[s],ref),"numerical comparison failed model "+std::to_string(i));
   values<<i<<','<<family<<",1,"<<s;
   for(double x:in[s])values<<','<<x;
   values<<','<<out[s]<<','<<ref<<','<<err<<'\n';
   ++checks;
  }
 }
 // Update one model: old version's object is deleted after the new graph compiles.
 // No external strings are accepted: this synthetic catalog is an approved-only example.
 size_t id=std::min(size_t(17),cfg.models-1);
 int family=static_cast<int>(id%5);
 double old_offset=static_cast<double>(id+1)/10000.0;
 double new_offset=old_offset+0.125;
 OwnedGraph new_graph=create(make_formula(family,new_offset));
 size_t update_n=std::min<size_t>(16,cfg.samples);
 std::vector<Input> input; input.reserve(update_n);
 for(size_t s=0;s<update_n;++s)input.push_back(input_for(s,id));
 auto old_out=batch_eval(graphs[id].h,input,cfg.batch);
 auto new_out=batch_eval(new_graph.h,input,cfg.batch);
 for(size_t s=0;s<update_n;++s){
  double delta=new_out[s]-old_out[s];
  insist(near(delta,0.125),"version update delta mismatch");
  updates<<id<<','<<s<<",1,2,"<<old_out[s]<<','<<new_out[s]<<",0.125,"<<std::abs(delta-0.125)<<'\n';
 }
 graphs[id]=std::move(new_graph);
 // Optional pointwise TINC audit: the independent high-precision script checks
 // interval containment; this C++ code does not assert universal TINC guarantees.
 OwnedGraph tg=create(make_formula(0,0.0001),true);
 for(size_t s=0;s<24;++s){
  auto v=input_for(s,0);double low=0,high=0;
  double p=paceval_dGetComputationResult(tg.h,v.data(),&low,&high);
  insist(!paceval_GetIsError(tg.h)&&std::isfinite(p)&&std::isfinite(low)&&std::isfinite(high)&&low<=high,"invalid TINC result");
  double ref=native_value(0,0.0001,v);insist(near(p,ref),"TINC point value mismatch");
  tinc<<s;for(double x:v)tinc<<','<<x;
  tinc<<','<<p<<','<<low<<','<<high<<','<<ref<<'\n';
 }
 // Release all graph handles before unloading paceval binary.
 graphs.clear();
 meta<<"evaluations="<<checks<<"\nmax_native_abs_error="<<std::setprecision(17)<<max_diff<<"\n";
 meta<<"version_change_id="<<id<<"\nversion_update_samples="<<update_n<<"\ntinc_samples=24\n";
 std::cout<<"PASS: "<<cfg.models<<" formula graphs, "<<checks<<" validations, "<<update_n<<" version checks, 24 interval samples\n";
}
} // namespace
int main(int argc,char**argv){try{Config c=parse(argc,argv);if(c.self_test)run_native_selftest();else run(c);return 0;}catch(const std::exception& e){std::cerr<<"FAIL: "<<e.what()<<'\n';return 1;}}
