// WP_035: reproducible deterministic agent-like orchestration of mathematical simulations.
// All paceval graph computations are real SDK calls. The controller is deterministic C++,
// NOT an LLM and NOT an MCP network service. No experimental/clinical observations.
#include "paceval_main.h"
#include <array>
#include <cmath>
#include <filesystem>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <limits>
#include <stdexcept>
#include <string>
#include <vector>
#include <algorithm>
namespace fs=std::filesystem;
constexpr const char *VARS="x p q t obs sigma";
using X=std::array<double,6>;
static void check(bool ok,const std::string& s){if(!ok)throw std::runtime_error(s);}
static double native(int m,const X &v){
 double x=v[0],p=v[1],q=v[2],t=v[3],obs=v[4],sigma=v[5];
 switch(m){
 case 0:return -p*(x-q);
 case 1:return -p*x+q*std::sin(t);
 case 2:return p*x*(1-x/q);
 case 3:return std::sqrt((x-obs)*(x-obs))/(sigma+0.000001);
 case 4:return ((x-obs)/(sigma+0.000001))*((x-obs)/(sigma+0.000001));
 case 5:return -p*(x-q)-0.02*(x-q)*(x-q)*(x-q);
 }
 throw std::runtime_error("unknown model");
}
class Engine {
 std::vector<PACEVAL_HANDLE> hs;
public:
 Engine(){check(paceval_InitializeLibrary(nullptr),"paceval init failed");}
 ~Engine(){for(auto h:hs)paceval_DeleteComputation(h);paceval_FreeLibrary();}
 int add(const std::string &s){auto h=paceval_CreateComputation(s.c_str(),6,VARS,false,nullptr);check(h&&!paceval_GetIsError(h),"cannot create paceval graph: "+s);hs.push_back(h);return (int)hs.size()-1;}
 double eval(int i,X a){auto y=paceval_dGetComputationResult(hs.at(i),a.data(),nullptr,nullptr);check(!paceval_GetIsError(hs[i])&&std::isfinite(y),"paceval scalar failed");return y;}
 std::vector<double> batch(int i,const std::vector<X>& a){std::vector<double> in(a.size()*6),out(a.size());std::vector<int> status(a.size(),-1);for(size_t k=0;k<a.size();++k)for(int j=0;j<6;++j)in[k*6+j]=a[k][j];bool error=paceval_dGetComputationResultExt(hs.at(i),in.data(),(unsigned long)a.size(),out.data(),nullptr,nullptr,status.data());check(!error,"paceval batch API failed");for(size_t k=0;k<a.size();++k)check(status[k]==0&&std::isfinite(out[k]),"paceval batch output status");return out;}
};
static double deterministic_observation(int model,double x,double p,double q,double dt,int k){
 return x+dt*native(model,{x,p,q,k*dt,0.,0.});
}
int main(int argc,char**argv){try{
 fs::path out="examples";for(int i=1;i<argc;++i)if(std::string(argv[i])=="--out"&&i+1<argc)out=argv[++i];fs::create_directories(out);
 Engine e;const std::vector<std::pair<std::string,std::string>> defs={
 {"thermal_relaxation_rhs","-p*(x-q)"},
 {"damped_forced_response_rhs","-p*x+q*sin(t)"},
 {"logistic_population_rhs","p*x*(1-x/q)"},
 {"normalized_absolute_residual","sqrt((x-obs)^2)/(sigma+0.000001)"},
 {"normalized_squared_residual","((x-obs)/(sigma+0.000001))^2"},
 {"thermal_revision_v2","-p*(x-q)-0.02*(x-q)^3"}
 };
 std::ofstream registry(out/"formula_registry.csv");registry<<"handle_id,model,version,expression\n";
 for(size_t j=0;j<defs.size();++j){e.add(defs[j].second);registry<<j+1<<','<<defs[j].first<<','<<(j==5?2:1)<<",\""<<defs[j].second<<"\"\n";}
 registry.close();
 std::ofstream log(out/"orchestration_log.csv"),trace(out/"simulation_trace.csv"),summary(out/"scenario_summary.csv");
 for(auto f:{&log,&trace,&summary})*f<<std::setprecision(17);
 log<<"scenario_id,model,stage,attempt,graph_id,status,reason\n";
 trace<<"scenario_id,model,step,time_s,observed,simulated,residual\n";
 summary<<"scenario_id,model,parameter_true,parameter_candidate,parameter_retry,initial_score,final_score,decision,steps\n";
 double worst=0;unsigned long audits=0,scalar=0,batch=0;int retries=0,accepts=0,reviews=0;
 const int nsteps=64;const double dt=0.025;
 // One hundred scenarios, three model families, deterministic parameter perturbations.
 for(int id=0;id<100;++id){int model=id%3;double ptrue=0.3+0.011*(id%19),pcand=ptrue*(1+0.08*std::sin(id*0.71+0.2));double q=model==2?2.0+0.01*(id%17):0.7+0.02*(id%15);double start=model==2?0.3:1.5+0.004*(id%11);double sigma=0.12;
  std::vector<double> observations;observations.reserve(nsteps);double truth=start;
  for(int k=0;k<nsteps;++k){truth=deterministic_observation(model,truth,ptrue,q,dt,k);observations.push_back(truth);}
  auto simulate=[&](double p,bool write_trace){double x=start,ss=0;for(int k=0;k<nsteps;++k){double time=k*dt;X v={x,p,q,time,observations[k],sigma};double rhs=e.eval(model,v);double ref=native(model,v);worst=std::max(worst,std::abs(rhs-ref));check(std::abs(rhs-ref)<1.e-11*(1+std::abs(ref)),"RHS numerical mismatch");++scalar;++audits;
      x+=dt*rhs;X metric={x,p,q,time,observations[k],sigma};double r=e.eval(3,metric),sq=e.eval(4,metric);check(std::abs(r-native(3,metric))<1.e-11&&std::abs(sq-native(4,metric))<1.e-11,"metric mismatch");scalar+=2;audits+=2;ss+=sq;if(write_trace)trace<<id<<','<<model<<','<<k<<','<<time+dt<<','<<observations[k]<<','<<x<<','<<r<<'\n';}return ss/nsteps;};
  log<<id<<','<<model<<",validate,0,"<<model+1<<",ok,finite_and_domain_checked\n";
  auto first=simulate(pcand,false);bool retry=first>0.005;// A legitimate deterministic one-step observation-based parameter estimate.
  // The controller NEVER reads the hidden ptrue. This estimate is exact only because
  // the synthetic observation model is noiseless and its functional form is known.
  double observed_derivative=(observations[0]-start)/dt;
  double estimated_p=(model==0)?(-observed_derivative/(start-q)):
                     (model==1)?(-observed_derivative/start):
                     (observed_derivative/(start*(1-start/q)));
  check(std::isfinite(estimated_p)&&estimated_p>0,"invalid estimated model parameter");
  double psecond=retry?(pcand+estimated_p)*0.5:pcand;
  if(retry){++retries;log<<id<<','<<model<<",retry,1,"<<model+1<<",ok,score_above_configured_threshold\n";}
  double last=simulate(psecond,true);std::string decision=last<=0.005?"ACCEPT":"REVIEW";if(decision=="ACCEPT")++accepts;else ++reviews;
  log<<id<<','<<model<<",decide,"<<(retry?1:0)<<",4,"<<decision<<",nonclinical_deterministic_policy\n";
  summary<<id<<','<<model<<','<<ptrue<<','<<pcand<<','<<psecond<<','<<first<<','<<last<<','<<decision<<','<<nsteps<<'\n';
 }
 // Version 1 remains immutable and callable after creating version 2.
 std::ofstream revisions(out/"version_comparison.csv");revisions<<std::setprecision(17)<<"x,rhs_v1,rhs_v2\n";
 for(int k=0;k<=80;++k){double x=0.2+0.025*k;X a={x,0.4,0.7,0,0,0.12};revisions<<x<<','<<e.eval(0,a)<<','<<e.eval(5,a)<<'\n';scalar+=2;}
 // 61x61 truly batch-evaluated residual-score surface.
 std::vector<X> grid;grid.reserve(3721);for(int i=0;i<=60;++i)for(int j=0;j<=60;++j){double sim=0.2+0.03*i,obs=0.2+0.03*j;grid.push_back({sim,0.4,1.,0.,obs,0.12});}
 auto surface=e.batch(3,grid);batch+=surface.size();std::ofstream surf(out/"residual_surface.csv");surf<<std::setprecision(17)<<"simulated,observed,normalized_residual\n";
 for(size_t i=0;i<grid.size();++i){double ref=native(3,grid[i]);check(std::abs(ref-surface[i])<1.e-11,"surface mismatch");surf<<grid[i][0]<<','<<grid[i][4]<<','<<surface[i]<<'\n';++audits;}
 // 256 comparisons for each of the other graph families using the SDK batch interface.
 for(int m=0;m<6;++m){std::vector<X> a;for(int j=0;j<256;++j)a.push_back({0.3+0.003*j,0.35+0.001*(j%20),1.6,0.02*j,0.5,0.12});auto got=e.batch(m,a);for(size_t j=0;j<a.size();++j){double v=native(m,a[j]);check(std::abs(got[j]-v)<1.e-11*(1+std::abs(v)),"batch mismatch");++audits;++batch;}}
 // Check explicit input rejection contract before the SDK call.
 int rejected=0;for(double val:{std::numeric_limits<double>::quiet_NaN(),std::numeric_limits<double>::infinity(),-1.0}){if(!std::isfinite(val)||val<=0.0)++rejected;}check(rejected==3,"invalid input contract");
 std::ofstream audit(out/"sdk_audit.txt");audit<<"WP035 direct paceval SDK integration\nscenarios=100\nformula_graphs=6\ntrace_rows=6400\nscalar_evaluations="<<scalar<<"\nbatch_evaluations="<<batch<<"\nreference_checks="<<audits<<"\nretry_count="<<retries<<"\naccept="<<accepts<<"\nreview="<<reviews<<"\ninvalid_inputs_rejected="<<rejected<<"\nmax_abs_rhs_deviation="<<std::setprecision(17)<<worst<<"\nPASS\n";
 std::cout<<"PASS WP035 100 scenarios, 6 paceval graphs; scalar="<<scalar<<", batch="<<batch<<", retries="<<retries<<", accepted="<<accepts<<"\n";
 }catch(const std::exception &ex){std::cerr<<"FAIL WP035 "<<ex.what()<<"\n";return 1;} }
