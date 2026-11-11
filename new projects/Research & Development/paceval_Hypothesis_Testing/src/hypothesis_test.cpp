// Reproducible offline hypothesis-evaluation demonstrator using paceval 4.25.
//
// Copyright / licensing of the separate official paceval_main.{h,cpp}
// remain in those SDK files. This application code is a research example.
//
// Boundary of responsibility:
//   C++: deterministic candidate generation, data splits, error metrics,
//        train/validation selection, held-out testing, CSV and reference checks.
//   paceval: creation and repeated batched evaluation of explicit expressions.
// Neither formula discovery nor scientific truth is performed by paceval.
//
// Compile together with the original paceval_main.cpp; link a compatible
// external libpaceval_linux_sharedLIB.so. Never compile the .so into this tree.
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
#include <numeric>
#include <random>
#include <sstream>
#include <stdexcept>
#include <string>
#include <vector>

namespace fs = std::filesystem;

namespace {
constexpr std::size_t FAMILY_COUNT=8;
constexpr std::size_t VAR_COUNT=5;
constexpr double TRUE_A=1.4, TRUE_B=1.8, TRUE_C=0.3, TRUE_D=0.12;
constexpr double ABS_TOL=2e-9, REL_TOL=2e-9;
constexpr std::uint64_t FIXED_SEED=20261111ULL;
const std::array<const char*,FAMILY_COUNT> EXPRESSIONS{{
 "a*sin(b*x)+c*x*x+d",             // family 0: planted ground-truth structure
 "a*cos(b*x)+c*x*x+d",             // alternative harmonic phase
 "a*tanh(b*x)+c*x*x+d",            // saturating nonlinearity
 "a*exp(-b*x*x)+c*x*x+d",          // radial-like exponential
 "a*sin(b*x)+c*x+d",               // competing linear trend
 "a*cos(b*x)+c*x+d",               // cosine with linear trend
 "a*sin(b*x)+c*x*x+d*cos(x)",      // additional harmonic
 "a*ln(1+b*x*x)+c*x*x+d"           // logarithmic, b>0
}};
const std::array<int,FAMILY_COUNT> COMPLEXITY{{10,10,10,11,8,8,13,12}};

void ensure(bool good,const std::string& msg){if(!good)throw std::runtime_error(msg);}
std::ofstream file(const fs::path& p){
 std::ofstream o(p); ensure(o.good(),"Unable to create file: "+p.string());
 o<<std::setprecision(17); return o;
}
struct Candidate {
 std::size_t id=0; int family=0;
 double a=0,b=0,c=0,d=0;
 double train=std::numeric_limits<double>::quiet_NaN();
 double validation=std::numeric_limits<double>::quiet_NaN();
};
struct Observation {std::string split; double x=0,y=0,truth=0;};

// A separate, handwritten native reference evaluator. This must not call
// paceval; both paths are compared at identical *binary double* inputs.
double native(int family,double x,double a,double b,double c,double d){
 switch(family){
 case 0:return a*std::sin(b*x)+c*x*x+d;
 case 1:return a*std::cos(b*x)+c*x*x+d;
 case 2:return a*std::tanh(b*x)+c*x*x+d;
 case 3:return a*std::exp(-b*x*x)+c*x*x+d;
 case 4:return a*std::sin(b*x)+c*x+d;
 case 5:return a*std::cos(b*x)+c*x+d;
 case 6:return a*std::sin(b*x)+c*x*x+d*std::cos(x);
 case 7:return a*std::log(1.0+b*x*x)+c*x*x+d;
 default:throw std::runtime_error("Unknown hypothesis family");
 }
}
double reference_truth(double x){return native(0,x,TRUE_A,TRUE_B,TRUE_C,TRUE_D);}

// The four partitions have independent sample grids, deterministic noise and
// disjoint row identities. Only training and validation influence selection;
// the test and extrapolation partitions are read AFTER the winner is frozen.
std::vector<Observation> partition(const std::string& split,std::size_t n,
                                    double x0,double x1,double shift,int phase){
 std::vector<Observation> out;out.reserve(n);
 for(std::size_t i=0;i<n;++i){
  double x=x0+(x1-x0)*(static_cast<double>(i)+shift)/static_cast<double>(n);
  const double truth=reference_truth(x);
  const double tag=static_cast<double>(i+static_cast<std::size_t>(phase)*1009);
  const double noise=0.006*std::sin(0.731*tag+0.27)*std::sin(1.113*tag+0.45);
  out.push_back({split,x,truth+noise,truth});
 }
 return out;
}
std::vector<Candidate> candidates(std::size_t count){
 ensure(count>=16&&count<=100000,"Candidate count must be 16..100000");
 std::mt19937_64 rng(FIXED_SEED);
 std::uniform_real_distribution<double> amplitude(-2.0,2.0);
 std::uniform_real_distribution<double> frequency(0.2,3.6);
 std::uniform_real_distribution<double> quadratic(-0.65,0.65);
 std::uniform_real_distribution<double> offset(-0.65,0.65);
 std::vector<Candidate> out;out.reserve(count);
 for(std::size_t i=0;i<count;++i){
  Candidate c; c.id=i; c.family=static_cast<int>(i%FAMILY_COUNT);
  c.a=amplitude(rng);c.b=frequency(rng);c.c=quadratic(rng);c.d=offset(rng);
  // The planted hypothesis demonstrates controlled recovery on a known model.
  // It is disclosed, not presented as an unknown scientific discovery.
  if(i==0){c.family=0;c.a=TRUE_A;c.b=TRUE_B;c.c=TRUE_C;c.d=TRUE_D;}
  out.push_back(c);
 }
 return out;
}
std::string instantiated(const Candidate& c){
 std::ostringstream os;os<<std::setprecision(17);
 // The canonical symbolic form is the expression template plus explicit
 // coefficient binding: this uniquely determines a mathematical hypothesis.
 os<<EXPRESSIONS[static_cast<std::size_t>(c.family)]
   <<" {a="<<c.a<<", b="<<c.b<<", c="<<c.c<<", d="<<c.d<<"}";
 return os.str();
}
class Engine {
 bool initialized_=false;
 std::array<PACEVAL_HANDLE,FAMILY_COUNT> graph_{};
 PACEVAL_HANDLE interval_graph_=nullptr;
 void release() noexcept {
  if(interval_graph_){paceval_DeleteComputation(interval_graph_);interval_graph_=nullptr;}
  for(auto& h:graph_){if(h){paceval_DeleteComputation(h);h=nullptr;}}
  if(initialized_){paceval_FreeLibrary();initialized_=false;}
 }
public:
 Engine(){
  ensure(paceval_InitializeLibrary(nullptr),"paceval_InitializeLibrary failed");
  initialized_=true;
  try {
   for(std::size_t i=0;i<FAMILY_COUNT;++i){
    graph_[i]=paceval_CreateComputation(EXPRESSIONS[i],VAR_COUNT,"x a b c d",false,nullptr);
    ensure(graph_[i] && !paceval_GetIsError(graph_[i]),
           "paceval graph creation failed (family "+std::to_string(i)+")");
   }
   interval_graph_=paceval_CreateComputation(EXPRESSIONS[0],VAR_COUNT,"x a b c d",true,nullptr);
   ensure(interval_graph_ && !paceval_GetIsError(interval_graph_),"TINC graph creation failed");
  }catch(...){release();throw;}
 }
 Engine(const Engine&)=delete; Engine& operator=(const Engine&)=delete;
 ~Engine(){release();}
 // Evaluates the candidate with prepared graph, in batches with sample-major
 // input layout: [x,a,b,c,d, x,a,b,c,d, ...]. API boolean means ERROR (true).
 template<class Callback>
 void evaluate(const Candidate& c,const std::vector<Observation>& points,
               std::size_t batch,Callback callback){
  ensure(c.family>=0&&c.family<static_cast<int>(FAMILY_COUNT),"Invalid family");
  ensure(batch>=1&&batch<=4096,"Batch size must be 1..4096");
  std::vector<double> inputs(batch*VAR_COUNT),outputs(batch);
  std::vector<int> errors(batch);
  for(std::size_t pos=0;pos<points.size();pos+=batch){
   const std::size_t n=std::min(batch,points.size()-pos);
   for(std::size_t j=0;j<n;++j){
    const double xx=points[pos+j].x;
    inputs[VAR_COUNT*j+0]=xx;inputs[VAR_COUNT*j+1]=c.a;
    inputs[VAR_COUNT*j+2]=c.b;inputs[VAR_COUNT*j+3]=c.c;
    inputs[VAR_COUNT*j+4]=c.d;
   }
   const bool failed=paceval_dGetComputationResultExt(graph_[static_cast<std::size_t>(c.family)],
          inputs.data(),static_cast<unsigned long>(n),outputs.data(),nullptr,nullptr,errors.data());
   ensure(!failed,"paceval batch reported an error (hypothesis "+std::to_string(c.id)+")");
   for(std::size_t j=0;j<n;++j){
    ensure(errors[j]==PACEVAL_ERR_NO_ERROR && std::isfinite(outputs[j]),
           "Invalid paceval output (hypothesis "+std::to_string(c.id)+")");
    callback(pos+j,outputs[j]);
   }
  }
  ensure(!paceval_GetIsError(graph_[static_cast<std::size_t>(c.family)]),"paceval graph error after batch");
 }
 std::array<double,3> interval(double x){
  double inputs[]={x,TRUE_A,TRUE_B,TRUE_C,TRUE_D};double low=0,high=0;
  const double answer=paceval_dGetComputationResult(interval_graph_,inputs,&low,&high);
  ensure(!paceval_GetIsError(interval_graph_)&&std::isfinite(answer)&&
         std::isfinite(low)&&std::isfinite(high)&&low<=high,"TINC evaluation failed");
  return {{answer,low,high}};
 }
};

// Compare numerical results without conflating their correctness with the
// statistical suitability of a model. Every 113th prediction is checked against
// a separately coded C++ evaluator; additional samples get a 110-digit audit.
struct Audit {std::size_t count=0,violations=0;double max_abs=0;};
double mse(Engine& engine,const Candidate& c,const std::vector<Observation>& data,
           std::size_t batch,Audit& audit,std::ofstream* sampled=nullptr){
 long double sse=0.0L;
 engine.evaluate(c,data,batch,[&](std::size_t j,double actual){
  const long double err=static_cast<long double>(actual)-data[j].y;
  sse+=err*err;
  if((c.id*131+j)%113==0 || (sampled && c.id%211==0 && (j==0||j==data.size()/2||j+1==data.size()))){
   const double independent=native(c.family,data[j].x,c.a,c.b,c.c,c.d);
   const double difference=std::abs(actual-independent);
   const double tolerance=ABS_TOL+REL_TOL*std::abs(independent);
   ++audit.count; audit.max_abs=std::max(audit.max_abs,difference);
   if(difference>tolerance) ++audit.violations;
   if(sampled && c.id%211==0 && (j==0||j==data.size()/2||j+1==data.size())){
    *sampled<<c.id<<','<<c.family<<','<<data[j].x<<','<<c.a<<','<<c.b<<','<<c.c<<','<<c.d
            <<','<<actual<<','<<independent<<'\n';
   }
  }
 });
 return static_cast<double>(sse/data.size());
}

void write_dataset(const fs::path& p,const std::array<std::vector<Observation>,4>& data){
 auto o=file(p);o<<"partition,x,observed_y,noise_free_reference\n";
 for(const auto& group:data)for(const auto& s:group)
  o<<s.split<<','<<s.x<<','<<s.y<<','<<s.truth<<'\n';
}
void write_summary(const fs::path& path,std::size_t count,std::size_t batch,
                   const Candidate& winner,double test,double ood,const Audit& audit){
 auto o=file(path);
 o<<"{\n  \"status\": \"PASS\",\n  \"candidate_count\": "<<count
  <<",\n  \"structural_graphs\": "<<FAMILY_COUNT
  <<",\n  \"graph_strategy\": \"eight parameterized structural templates reused across generated hypotheses\""
  <<",\n  \"batch_size\": "<<batch
  <<",\n  \"training_sample_count\": 120,\n  \"validation_sample_count\": 60"
  <<",\n  \"held_out_test_sample_count\": 60,\n  \"extrapolation_sample_count\": 48"
  <<",\n  \"selection_procedure\": \"top 100 training MSE, then minimum validation MSE; test evaluated once after selection\""
  <<",\n  \"selection_used_test_data\": false"
  <<",\n  \"selected_candidate_id\": "<<winner.id
  <<",\n  \"selected_family\": "<<winner.family
  <<",\n  \"selected_train_mse\": "<<winner.train
  <<",\n  \"selected_validation_mse\": "<<winner.validation
  <<",\n  \"selected_test_mse\": "<<test
  <<",\n  \"selected_extrapolation_mse\": "<<ood
  <<",\n  \"numeric_reference_checks\": "<<audit.count
  <<",\n  \"numeric_reference_violations\": "<<audit.violations
  <<",\n  \"max_abs_cpp_reference_difference\": "<<audit.max_abs
  <<",\n  \"synthetic_data\": true,\n  \"planted_target_disclosed\": true\n}\n";
}

void self_test(){
 ensure(std::abs(native(0,0,TRUE_A,TRUE_B,TRUE_C,TRUE_D)-TRUE_D)<1e-15,"Native f(0) error");
 ensure(std::abs(native(4,1,0,0,1,0)-1.0)<1e-15,"Native linear family error");
 auto c=candidates(100);
 ensure(c.size()==100 && c[0].a==TRUE_A && c[0].family==0,"Generator error");
 for(std::size_t i=0;i<FAMILY_COUNT;++i)ensure(std::isfinite(native(static_cast<int>(i),0.3,1,1,0.1,0.2)),"Bad family");
 ensure(partition("training",120,-2.4,2.4,0.37,0).size()==120,"Data split failure");
 std::cout<<"Self-test PASS (native formulas, generator, partitions)\n";
}

int run(std::size_t count,std::size_t batch,const fs::path& output){
 fs::create_directories(output);
 const auto data=std::array<std::vector<Observation>,4>{{
  partition("training",120,-2.4,2.4,0.37,0),
  partition("validation",60,-2.35,2.35,0.19,1),
  partition("test",60,-2.36,2.36,0.73,2),
  partition("extrapolation",48,2.6,3.8,0.47,3)
 }};
 write_dataset(output/"dataset.csv",data);
 Engine engine;
 auto all=candidates(count);
 auto metrics=file(output/"hypotheses.csv");
 metrics<<"candidate_id,family,expression_with_coefficients,a,b,c,d,complexity,training_mse\n";
 auto audit_file=file(output/"audit_samples.csv");
 audit_file<<"candidate_id,family,x,a,b,c,d,paceval_value,cpp_reference\n";
 Audit audit;
 for(Candidate& c:all){
  c.train=mse(engine,c,data[0],batch,audit,&audit_file);
  metrics<<c.id<<','<<c.family<<','<<'"'<<instantiated(c)<<'"'<<','<<c.a<<','<<c.b<<','<<c.c<<','<<c.d
         <<','<<COMPLEXITY[static_cast<std::size_t>(c.family)]<<','<<c.train<<'\n';
 }
 ensure(audit.violations==0,"Independent native numerical reference mismatches");
 const std::size_t shortlist_count=std::min<std::size_t>(100,all.size());
 std::vector<std::size_t> ids(all.size());std::iota(ids.begin(),ids.end(),0);
 std::partial_sort(ids.begin(),ids.begin()+static_cast<std::ptrdiff_t>(shortlist_count),ids.end(),
   [&](std::size_t i,std::size_t j){return all[i].train==all[j].train ? i<j : all[i].train<all[j].train;});
 auto shortlist=file(output/"shortlist.csv");
 shortlist<<"train_rank,candidate_id,family,training_mse,validation_mse,complexity\n";
 for(std::size_t k=0;k<shortlist_count;++k){
  Candidate& c=all[ids[k]];
  c.validation=mse(engine,c,data[1],batch,audit);
  shortlist<<k+1<<','<<c.id<<','<<c.family<<','<<c.train<<','<<c.validation<<','
           <<COMPLEXITY[static_cast<std::size_t>(c.family)]<<'\n';
 }
 const auto win_it=std::min_element(ids.begin(),ids.begin()+static_cast<std::ptrdiff_t>(shortlist_count),
 [&](std::size_t i,std::size_t j){
  if(all[i].validation==all[j].validation){
   if(COMPLEXITY[static_cast<std::size_t>(all[i].family)] != COMPLEXITY[static_cast<std::size_t>(all[j].family)])
    return COMPLEXITY[static_cast<std::size_t>(all[i].family)]<COMPLEXITY[static_cast<std::size_t>(all[j].family)];
   return i<j;
  }
  return all[i].validation<all[j].validation;
 });
 const Candidate best=all[*win_it];
 // The held-out test and OOD sets are accessed here for the first time.
 const double test=mse(engine,best,data[2],batch,audit);
 const double ood=mse(engine,best,data[3],batch,audit);
 auto prediction=file(output/"selected_predictions.csv");
 prediction<<"partition,x,observed_y,noise_free_truth,paceval_prediction,cpp_prediction\n";
 for(const auto& group:data)engine.evaluate(best,group,batch,[&](std::size_t j,double result){
  prediction<<group[j].split<<','<<group[j].x<<','<<group[j].y<<','<<group[j].truth<<','<<result<<','
            <<native(best.family,group[j].x,best.a,best.b,best.c,best.d)<<'\n';
 });
 // TINC is audited separately; it is a finite sample observation, not a proof
 // of universal guaranteed enclosures or model correctness.
 auto tinc=file(output/"tinc_samples.csv");
 tinc<<"x,a,b,c,d,paceval_value,lower_bound,upper_bound\n";
 for(int j=0;j<24;++j){
  const double x=-1.7+3.4*(j+0.39)/24.0;
  const auto r=engine.interval(x);
  tinc<<x<<','<<TRUE_A<<','<<TRUE_B<<','<<TRUE_C<<','<<TRUE_D<<','
      <<r[0]<<','<<r[1]<<','<<r[2]<<'\n';
 }
 write_summary(output/"validation.json",count,batch,best,test,ood,audit);
 std::cout<<std::setprecision(12)
  <<"PASS: "<<count<<" distinct coefficient-bound mathematical hypotheses, "<<FAMILY_COUNT<<" reused paceval graphs\n"
  <<"Train shortlist: "<<shortlist_count<<"; selected #"<<best.id<<" family "<<best.family<<"\n"
  <<"Train MSE="<<best.train<<" validation MSE="<<best.validation
  <<" held-out MSE="<<test<<" OOD MSE="<<ood<<"\n"
  <<"Native C++ checks="<<audit.count<<" violations="<<audit.violations<<" max_abs="<<audit.max_abs<<"\n"
  <<"Outputs: "<<output<<"\n";
 return 0;
}
} // namespace

int main(int argc,char** argv){
 try {
  std::size_t count=10000,batch=256;
  fs::path output="results";
  bool self=false;
  for(int i=1;i<argc;++i){
   const std::string arg=argv[i];
   if(arg=="--self-test")self=true;
   else if(arg=="--candidates"&&i+1<argc)count=static_cast<std::size_t>(std::stoull(argv[++i]));
   else if(arg=="--batch"&&i+1<argc)batch=static_cast<std::size_t>(std::stoull(argv[++i]));
   else if(arg=="--output"&&i+1<argc)output=argv[++i];
   else throw std::runtime_error("Unknown/missing argument: "+arg);
  }
  if(self){self_test();return 0;}
  return run(count,batch,output);
 }catch(const std::exception& e){std::cerr<<"ERROR: "<<e.what()<<'\n';return 2;}
}
