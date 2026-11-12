// WP-024: Reusable Large Quantitative Model Tools.
// An actual paceval C++ SDK integration, not a mocked computational engine.
// All data are synthetic and the 50 tools are pure, bounded mathematical models.
// This local deterministic dispatcher is not a networked MCP server.
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
namespace {
constexpr const char* Variables="x y a b c";
constexpr unsigned long NumVars=5;
using Input=std::array<double,NumVars>;
void require(bool ok,const std::string& msg){if(!ok)throw std::runtime_error(msg);}
// Reproducible, platform-independent pseudorandom state. Use identical inputs
// for paceval and the independent native implementation.
struct RNG {std::uint64_t state=20261112ULL;std::uint64_t next(){state^=state>>12;state^=state<<25;state^=state>>27;return state*2685821657736338717ULL;}double uniform(){return double(next()>>11)*0x1.0p-53;}};
struct Model {int id,family,version;double k;std::string name,expression;PACEVAL_HANDLE handle=nullptr;};
// The following families are intentionally non-equivalent functions, each
// provided in ten distinct versions through an embedded coefficient k.
// Domain contract: x in [0.1,2.9], y in [-1,1], a,b,c in [0.2,1.4].
std::string expr(int fam,double k){std::ostringstream s;s<<std::setprecision(17);s.setf(std::ios::fixed);s.precision(9);
 switch(fam){
 case 0:s<<"a*x*x+b*ln(1+x)+"<<k<<"*c*y";break;
 case 1:s<<"a*exp(-"<<k<<"*x)+b*sin(x+y)+c*x*y";break;
 case 2:s<<"a/(1+"<<k<<"*x*x)+b*sqrt(1+x)+c*cos(y)";break;
 case 3:s<<"(a*x+b*y+c)/(1+"<<k<<"*x*x)+sin(x*y)";break;
 default:s<<"a*ln(1+x*x)+b*exp(-x*y*y)+"<<k<<"*c*x*x";break;
 }return s.str();}
double native(const Model& m,const Input& v){const double x=v[0],y=v[1],a=v[2],b=v[3],c=v[4],k=m.k;
 switch(m.family){
 case 0:return a*x*x+b*std::log(1+x)+k*c*y;
 case 1:return a*std::exp(-k*x)+b*std::sin(x+y)+c*x*y;
 case 2:return a/(1+k*x*x)+b*std::sqrt(1+x)+c*std::cos(y);
 case 3:return (a*x+b*y+c)/(1+k*x*x)+std::sin(x*y);
 default:return a*std::log(1+x*x)+b*std::exp(-x*y*y)+k*c*x*x;
 }}
class Engine {
 std::vector<PACEVAL_HANDLE> owned;
public:
 Engine(){require(paceval_InitializeLibrary(nullptr),"paceval_InitializeLibrary failed");}
 Engine(const Engine&)=delete;Engine& operator=(const Engine&)=delete;
 ~Engine(){for(auto h:owned)if(h)paceval_DeleteComputation(h);paceval_FreeLibrary();}
 PACEVAL_HANDLE create(const std::string& e){auto h=paceval_CreateComputation(e.c_str(),NumVars,Variables,false,nullptr);
  require(h!=nullptr,"paceval returned null graph: "+e);owned.push_back(h);require(!paceval_GetIsError(h),"paceval rejected graph: "+e);return h;}
 double eval(PACEVAL_HANDLE h,const Input& v){Input copy=v;double result=paceval_dGetComputationResult(h,copy.data(),nullptr,nullptr);
  require(!paceval_GetIsError(h)&&std::isfinite(result),"paceval scalar evaluation failed");return result;}
 void batch(const Model& m,const std::vector<Input>& rows,std::size_t& count,double& maxerr){
  std::vector<double> packed(rows.size()*NumVars),results(rows.size());std::vector<int> errors(rows.size(),-1);
  for(std::size_t i=0;i<rows.size();++i)for(std::size_t j=0;j<NumVars;++j)packed[i*NumVars+j]=rows[i][j];
  const bool failed=paceval_dGetComputationResultExt(m.handle,packed.data(),static_cast<unsigned long>(rows.size()),results.data(),nullptr,nullptr,errors.data());
  require(!failed,"paceval batch API reported error");
  for(std::size_t i=0;i<rows.size();++i){require(errors[i]==0&&std::isfinite(results[i]),"invalid batch result");
   const double target=native(m,rows[i]);const double diff=std::abs(target-results[i]);maxerr=std::max(maxerr,diff);
   require(diff<=1e-10*(1+std::abs(target)),"batch/reference mismatch");++count;}
 }
};
Input sample(RNG& r){return {0.1+2.8*r.uniform(),-1+2*r.uniform(),0.2+1.2*r.uniform(),0.2+1.2*r.uniform(),0.2+1.2*r.uniform()};}
void run(const std::filesystem::path& dir,bool quick){
 std::filesystem::create_directories(dir);Engine engine;std::vector<Model> tools;
 for(int id=0;id<50;++id){const int fam=id/10;const double k=0.11+0.07*(id%10);
  Model m{id+1,fam,1,k,"model_"+std::to_string(id+1),expr(fam,k),nullptr};m.handle=engine.create(m.expression);tools.push_back(m);}
 // A formula change is an immutable new graph; old graph still usable.
 Model updated=tools[0];updated.version=2;updated.k=0.93;updated.expression=expr(updated.family,updated.k);updated.handle=engine.create(updated.expression);
 std::ofstream registry(dir/"tool_registry.csv");registry<<"tool_id,family,version,k,expression\n";
 for(const auto& m:tools)registry<<m.id<<','<<m.family<<','<<m.version<<','<<std::setprecision(17)<<m.k<<','<<m.expression<<'\n';
 registry<<updated.id<<','<<updated.family<<','<<updated.version<<','<<updated.k<<','<<updated.expression<<'\n';registry.close();
 std::ofstream output(dir/"requests.csv");output<<"request_id,tool_id,family,x,y,a,b,c,paceval,native,abs_error,composed_value\n";
 RNG rng;double maxerr=0;std::size_t scalar=0,composed=0,batch_checked=0;
 const int N=quick?400:10000;
 for(int i=0;i<N;++i){auto& m=tools[static_cast<std::size_t>(i%50)];Input v=sample(rng);
  const double actual=engine.eval(m.handle,v),expected=native(m,v),diff=std::abs(actual-expected);
  require(diff<=1e-10*(1+std::abs(expected)),"scalar/reference mismatch");maxerr=std::max(maxerr,diff);++scalar;
  // Tool composition: use a previous tool's bounded result as an input to a
  // different graph; this is a separate actual paceval evaluation.
  double composed_value=std::numeric_limits<double>::quiet_NaN();
  if(i%5==0){const Model& second=tools[(static_cast<std::size_t>(i)+17)%tools.size()];Input w=v;
   w[1]=std::tanh(actual);composed_value=engine.eval(second.handle,w);const double n=native(second,w);
   const double d=std::abs(composed_value-n);maxerr=std::max(maxerr,d);
   require(d<=1e-10*(1+std::abs(n)),"composed tool/reference mismatch");++scalar;++composed;}
  output<<i+1<<','<<m.id<<','<<m.family;
  for(double x:v)output<<','<<std::setprecision(17)<<x;
  output<<','<<actual<<','<<expected<<','<<diff<<',';
  if(std::isfinite(composed_value))output<<composed_value;
  output<<'\n';
 }
 output.close();
 // Each graph is audited with exactly 32 independently generated inputs.
 for(const auto& m:tools){std::vector<Input> batch;batch.reserve(32);for(int j=0;j<32;++j)batch.push_back(sample(rng));engine.batch(m,batch,batch_checked,maxerr);}
 // Separate 3D response surface with one fixed model (tool 23) and nonconstant x,y.
 std::ofstream surface(dir/"response_surface.csv");surface<<"x,y,paceval,native,abs_error\n";
 const Model& surf=tools[22];for(int ix=0;ix<=60;++ix)for(int iy=0;iy<=60;++iy){
  Input v{0.1+2.8*ix/60.0,-1+2.0*iy/60.0,0.9,0.8,0.7};
  const double p=engine.eval(surf.handle,v),n=native(surf,v),d=std::abs(p-n);require(d<=1e-10*(1+std::abs(n)),"surface mismatch");
  surface<<std::setprecision(17)<<v[0]<<','<<v[1]<<','<<p<<','<<n<<','<<d<<'\n';maxerr=std::max(maxerr,d);++scalar;}
 surface.close();
 // Verify old and updated graph are simultaneously alive and distinct.
 Input probe{1.2,0.4,1.1,0.9,0.8};const double oldv=engine.eval(tools[0].handle,probe),newv=engine.eval(updated.handle,probe);
 require(std::abs(oldv-newv)>1e-5,"formula-version test did not change result");
 require(std::abs(newv-native(updated,probe))<1e-10,"updated graph reference mismatch");
 std::ofstream version(dir/"version_audit.csv");version<<"tool_id,old_version,new_version,old_result,new_result,delta\n1,1,2,"<<std::setprecision(17)<<oldv<<','<<newv<<','<<newv-oldv<<'\n';version.close();scalar+=2;
 std::ofstream report(dir/"sdk_execution.txt");report<<std::setprecision(17)<<"sdk_executed=true\nmodels=50\npersistent_graphs=51\nscripted_requests="<<N<<"\ncompositions="<<composed<<"\nscalar_evaluations="<<scalar<<"\nbatch_checked="<<batch_checked<<"\nsurface_points=3721\nmax_abs_difference="<<maxerr<<"\n";
 report.flush();std::cout<<"SDK audit written to "<<dir<<"\n"; // avoid depending on network, unvalidated MCP wire behavior
 std::cout<<"PASS WP024 mathematical tool execution\n";
}
}
int main(int argc,char** argv){try{std::filesystem::path out="examples";bool test=false;
 for(int i=1;i<argc;++i){std::string a=argv[i];if(a=="--test")test=true;else if(a=="--out"&&i+1<argc)out=argv[++i];else throw std::runtime_error("unknown argument: "+a);}
 run(out,test);return 0;}catch(const std::exception& e){std::cerr<<"FAIL: "<<e.what()<<'\n';return 1;}}
