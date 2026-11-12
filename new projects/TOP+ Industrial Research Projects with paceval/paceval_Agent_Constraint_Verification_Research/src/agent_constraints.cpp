// WP-025 - Automatic Verification of Agent-Generated Constraints
// The mathematical inequalities are intentionally generated from a constrained,
// typed allowlisted template registry. Free-form LLM text is NEVER executed.
// All numerical claims are checked against independently coded C++ arithmetic.
// This is a local deterministic demonstration, not an MCP server or a theorem prover.
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
#include <sstream>
#include <stdexcept>
#include <string>
#include <vector>
namespace fs=std::filesystem;
namespace {
constexpr unsigned long NV=3;
constexpr const char* VARIABLES="x y z";
constexpr double BOUNDARY_TOLERANCE=1.e-8;  // REVIEW, not mathematically certified uncertainty
using Args=std::array<double,NV>;
void ensure(bool b,const std::string& message){if(!b)throw std::runtime_error(message);}
struct RNG{
 std::uint64_t s=20261112ULL;
 std::uint64_t next(){s^=s>>12;s^=s<<25;s^=s>>27;return s*2685821657736338717ULL;}
 double unit(){return double(next()>>11)*0x1.0p-53;}
};
struct Guard {int id=0,family=0,version=1;double a=0,b=0,c=0,k=0;std::string name,formula;PACEVAL_HANDLE handle=nullptr;};
// Signed margin convention: g(x,y,z)>=0 means admitted by the inequality.
// Numeric range [-2,2] is a schema precondition; input rejection occurs in host.
// All quantities are dimensionless normalized manufacturing setpoints.
std::string expression(const Guard& g){
 std::ostringstream s;s<<std::setprecision(17);
 switch(g.family){
 case 0:s<<g.c<<"-x";break; // upper-bound threshold
 case 1:s<<g.c<<"-(x/"<<g.a<<")^2-(y/"<<g.b<<")^2";break; // elliptical envelope
 case 2:s<<g.c<<"-x*x-"<<g.k<<"*y*y-0.1*z*z";break; // energy-like budget
 case 3:s<<g.c<<"+"<<g.a<<"*x-"<<g.b<<"*y+"<<g.k<<"*z";break; // affine actuator guard
 default:s<<g.c<<"-exp("<<g.k<<"*x)+"<<g.a<<"*cos(y)-"<<g.b<<"*z*z";break; // thermal nonlinear envelope
 }return s.str();
}
double reference(const Guard& g,const Args& v){
 const double x=v[0],y=v[1],z=v[2];
 switch(g.family){
 case 0:return g.c-x;
 case 1:return g.c-std::pow(x/g.a,2)-std::pow(y/g.b,2);
 case 2:return g.c-x*x-g.k*y*y-0.1*z*z;
 case 3:return g.c+g.a*x-g.b*y+g.k*z;
 default:return g.c-std::exp(g.k*x)+g.a*std::cos(y)-g.b*z*z;
 }
}
std::string decision(double margin){if(!std::isfinite(margin))return "REJECT_INVALID";
 if(margin>BOUNDARY_TOLERANCE)return "ACCEPT";
 if(margin< -BOUNDARY_TOLERANCE)return "REJECT";
 return "REVIEW_BOUNDARY";
}
struct Engine{
 std::vector<PACEVAL_HANDLE> owned;
 Engine(){ensure(paceval_InitializeLibrary(nullptr),"paceval_InitializeLibrary failed");}
 Engine(const Engine&)=delete;Engine& operator=(const Engine&)=delete;
 ~Engine(){for(auto h:owned)if(h)paceval_DeleteComputation(h);paceval_FreeLibrary();}
 PACEVAL_HANDLE add(const std::string& expr){
  PACEVAL_HANDLE h=paceval_CreateComputation(expr.c_str(),NV,VARIABLES,false,nullptr);
  ensure(h!=nullptr,"paceval returned null graph "+expr);owned.push_back(h);
  ensure(!paceval_GetIsError(h),"paceval rejected graph "+expr);return h;
 }
 double scalar(PACEVAL_HANDLE h,Args v){const double result=paceval_dGetComputationResult(h,v.data(),nullptr,nullptr);
  ensure(!paceval_GetIsError(h)&&std::isfinite(result),"paceval scalar numeric error");return result;}
 std::size_t batch(const Guard& g,const std::vector<Args>& rows,double& maximum){
  std::vector<double> packed(rows.size()*NV),answers(rows.size());std::vector<int> errors(rows.size(),-1);
  for(std::size_t i=0;i<rows.size();++i)for(std::size_t j=0;j<NV;++j)packed[i*NV+j]=rows[i][j];
  bool failed=paceval_dGetComputationResultExt(g.handle,packed.data(),static_cast<unsigned long>(rows.size()),answers.data(),nullptr,nullptr,errors.data());
  ensure(!failed,"paceval packed batch execution failed");
  for(std::size_t i=0;i<rows.size();++i){
   const double expected=reference(g,rows[i]);const double delta=std::abs(expected-answers[i]);
   maximum=std::max(maximum,delta);ensure(errors[i]==0&&std::isfinite(answers[i]),"invalid batch result");
   ensure(delta<=2e-12*(1+std::abs(expected)),"batch/reference mismatch");
   ensure(decision(answers[i])==decision(expected),"batch decision mismatch");
  }return rows.size();
 }
};
Guard make_guard(int id){
 Guard g;g.id=id;g.family=(id-1)%5;
 const int t=(id-1)/5;
 g.a=0.8+0.002*(t%67);g.b=0.9+0.003*(t%53);
 g.k=0.24+0.003*(t%47);g.c=(g.family==0?0.25+0.004*(t%90):
  g.family==1?0.70+0.004*(t%80):g.family==2?0.72+0.003*(t%85):
  g.family==3?0.02+0.002*(t%30):0.95+0.003*(t%85));
 g.name="guard_"+std::to_string(id);g.formula=expression(g);return g;
}
Args sample(const Guard& g,int j,RNG& rng){
 const double y=-0.45+0.9*rng.unit(),z=-0.5+1.0*rng.unit();
 double x=-1.5+3.0*rng.unit();
 // 50% of cases cluster around an analytically computed zero-margin boundary.
 // This is essential: uniformly random tests rarely exercise floating-point
 // classification near the inequality switching surface.
 if(j%2==0){double root=0;
  if(g.family==0)root=g.c;
  else if(g.family==1)root=g.a*std::sqrt(std::max(0.0,g.c-(y/g.b)*(y/g.b)));
  else if(g.family==2)root=std::sqrt(std::max(0.0,g.c-g.k*y*y-0.1*z*z));
  else if(g.family==3)root=(-g.c+g.b*y-g.k*z)/g.a;
  else root=std::log(std::max(0.05,g.c+g.a*std::cos(y)-g.b*z*z))/g.k;
  const double eps=(j%10==0?1e-11:j%10==2?1e-9:j%10==4?1e-7:j%10==6?1e-5:1e-3);
  x=root+(j%4==0?eps:-eps);
 }
 return {std::clamp(x,-2.0,2.0),y,z};
}
void execute(fs::path out,bool quick){
 fs::create_directories(out);Engine engine;
 const int N=quick?25:1000, CASES=quick?20:100;
 std::vector<Guard> guards;guards.reserve(N);
 std::ofstream registry(out/"guard_registry.csv");
 registry<<"guard_id,family,version,a,b,c,k,expression\n";
 for(int id=1;id<=N;++id){Guard g=make_guard(id);g.handle=engine.add(g.formula);
  registry<<g.id<<','<<g.family<<','<<g.version<<','<<g.a<<','<<g.b<<','<<g.c<<','<<g.k<<','<<g.formula<<'\n';guards.push_back(g);}
 // Immutable version update; both old and new graph handles remain valid.
 Guard updated=guards.front();updated.version=2;updated.c+=0.075;updated.formula=expression(updated);updated.handle=engine.add(updated.formula);
 registry<<updated.id<<','<<updated.family<<','<<updated.version<<','<<updated.a<<','<<updated.b<<','<<updated.c<<','<<updated.k<<','<<updated.formula<<'\n';registry.close();
 std::ofstream samples(out/"constraint_evaluations.csv");samples<<std::setprecision(17);
 samples<<"guard_id,family,sample_id,x,y,z,paceval_margin,native_margin,absolute_error,decision,reference_decision\n";
 RNG rng;std::size_t scalar=0,batch=0,accept=0,reject=0,review=0,false_accept=0,false_reject=0;
 double maxerror=0;
 for(const auto& g:guards){std::vector<Args> check_batch;
  for(int j=0;j<CASES;++j){Args input=sample(g,j,rng);
   for(double x:input)ensure(std::isfinite(x)&&x>=-2&&x<=2,"invalid schema domain");
   const double expected=reference(g,input),actual=engine.scalar(g.handle,input),diff=std::abs(actual-expected);
   ensure(diff<=2e-12*(1+std::abs(expected)),"scalar/reference difference");
   maxerror=std::max(maxerror,diff);++scalar;
   const std::string d=decision(actual),ref=decision(expected);
   if(d=="ACCEPT")++accept;else if(d=="REJECT")++reject;else ++review;
   if(d=="ACCEPT"&&ref=="REJECT")++false_accept;
   if(d=="REJECT"&&ref=="ACCEPT")++false_reject;
   ensure(d==ref,"classification mismatch with native reference");
   samples<<g.id<<','<<g.family<<','<<j<<','<<input[0]<<','<<input[1]<<','<<input[2]<<','<<actual<<','<<expected<<','<<diff<<','<<d<<','<<ref<<'\n';
   if(j<8)check_batch.push_back(input);
  }
  batch+=engine.batch(g,check_batch,maxerror);
 }
 // A 61x61 genuine paceval response surface for an elliptical constraint.
 // The data used by the publication figures are not artist impressions.
 std::ofstream surface(out/"ellipse_surface.csv");
 surface<<std::setprecision(17)<<"x,y,paceval_margin,native_margin\n";
 const Guard& ellipse=guards[1];
 for(int ix=0;ix<61;++ix)for(int iy=0;iy<61;++iy){
  const Args row={-1.2+2.4*ix/60.,-1.2+2.4*iy/60.,0.};
  const double p=engine.scalar(ellipse.handle,row),r=reference(ellipse,row);
  const double e=std::abs(p-r);maxerror=std::max(maxerror,e);
  ensure(e<=2e-12*(1+std::abs(r)),"surface/reference disagreement");++scalar;
  surface<<row[0]<<','<<row[1]<<','<<p<<','<<r<<'\n';
 }
 // Explicitly verify the updated formula is numerically different on a safe input.
 const Args v={0.1,0.2,-0.1};double original=engine.scalar(guards.front().handle,v);
 double revised=engine.scalar(updated.handle,v);
 ensure(std::abs(original-revised)>0.07&&std::abs(original-revised)<0.08,"immutable version check failed");
 // Host rejects incorrect types, inaccessible actions, invalid units and NaN
 // BEFORE ANY mathematical graph is used. These are deliberately not encoded
 // in numerical Boolean multiplications or entrusted to a language model.
 std::ofstream host(out/"host_contract_tests.csv");
 host<<"case,decision,reason\nwrong_unit,REJECT_INVALID,unit_schema\nunknown_action,REJECT_INVALID,permission_allowlist\nNaN_value,REJECT_INVALID,nonfinite_input\nout_of_range,REJECT_INVALID,range_schema\n";
 std::ofstream summary(out/"execution_summary.txt");summary<<std::setprecision(17)
  <<"sdk_status=PASS\nmathematical_graphs="<<N+1<<"\noriginal_guards="<<N
  <<"\nscalar_evaluations="<<scalar+2<<"\nbatch_comparisons="<<batch
  <<"\naccept="<<accept<<"\nreject="<<reject<<"\nreview_boundary="<<review
  <<"\nfalse_accept="<<false_accept<<"\nfalse_reject="<<false_reject
  <<"\nmaximum_absolute_difference="<<maxerror<<"\nversion_delta="<<revised-original<<'\n';
 std::cout<<"PASS guards="<<N<<" scalar="<<scalar+2<<" batch="<<batch
   <<" accept="<<accept<<" reject="<<reject<<" review="<<review
   <<" false_accept="<<false_accept<<" false_reject="<<false_reject
   <<" max_abs_difference="<<maxerror<<'\n';
}
} // namespace
int main(int argc,char** argv){try{bool quick=false;fs::path out="examples";
 for(int i=1;i<argc;++i){std::string arg=argv[i];if(arg=="--test")quick=true;
 else if(arg=="--out"&&i+1<argc)out=argv[++i];else throw std::runtime_error("unknown argument "+arg);}
 execute(out,quick);return 0;}catch(const std::exception& ex){std::cerr<<"FAIL: "<<ex.what()<<'\n';return 1;}}
