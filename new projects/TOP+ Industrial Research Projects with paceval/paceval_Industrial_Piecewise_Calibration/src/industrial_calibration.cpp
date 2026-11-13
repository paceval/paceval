// Industrial Piecewise Calibration, a reproducible scientific paceval C++ demonstrator.
// Synthetic mathematical model only. NOT metrologically traceable or safety certified.
// No performance comparisons. Real graphs: interpolation, compensation, uncertainty,
// constraint margins, change-control scores and sensitivity functions.
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
using namespace std;
namespace fs=std::filesystem;
static void ck(bool good,const string& reason){if(!good)throw runtime_error(reason);}
static string fmt(double v){ostringstream os; os<<setprecision(17)<<v;return os.str();}
static double parse(const string&s){size_t n=0;double v=stod(s,&n); ck(n==s.size()&&isfinite(v),"Invalid/nonfinite number: "+s);return v;}
static vector<string> fields(string s){if(!s.empty()&&s.back()=='\r')s.pop_back();stringstream in(s);string t;vector<string>a;while(getline(in,t,','))a.push_back(t);return a;}
static string vars_post="x T d S m ref tol ux ut ud umod";
static double prototype(double x,int v){return .12+.75*x+.09*sin(9*x)+.035*sin(37*x)+.04*exp(-pow((x-.72)/.06,2))+(v==1?(.002*sin(5*x)+.001*x):0);}
struct Row{string scenario;int seq;double x,T,d,ref,tol,ux,ut,ud,umod;};
static vector<Row> read_rows(const fs::path&root){
 ifstream f(root/"examples/synthetic_sensor_inputs.csv");ck(bool(f),"Missing examples/synthetic_sensor_inputs.csv");
 string l;getline(f,l);if(!l.empty()&&l.back()=='\r')l.pop_back();ck(l=="scenario,seq,x,T,drift,reference,tolerance,u_x,u_T,u_d,u_model","Incorrect input columns");
 vector<Row> rows;while(getline(f,l)){if(l.empty())continue;auto c=fields(l);ck(c.size()==11,"Input row needs 11 fields");Row r{c[0],stoi(c[1]),parse(c[2]),parse(c[3]),parse(c[4]),parse(c[5]),parse(c[6]),parse(c[7]),parse(c[8]),parse(c[9]),parse(c[10])};
 ck(r.x>=0&&r.x<=1,"Outside calibrated x domain [0,1]");ck(r.T>=0&&r.T<=60,"Temperature outside [0,60] C");ck(r.d>=-1&&r.d<=1,"Drift outside [-1,1]");ck(r.tol>0&&r.ux>0&&r.ut>0&&r.ud>0&&r.umod>0,"Invalid uncertainty/tolerance");rows.push_back(r);
 }ck(rows.size()>=128,"Insufficient sample rows");return rows;
}
struct Graph{string id,version,category,formula,units,vars;int nvars;PACEVAL_HANDLE h=nullptr;};
class Engine{
 vector<Graph> graph_;size_t eval_outputs_=0,batch_calls_=0,scalar_calls_=0;
public:
 Engine(){ck(paceval_InitializeLibrary(nullptr),"paceval_InitializeLibrary failed");}
 ~Engine(){for(auto&g:graph_)if(g.h)paceval_DeleteComputation(g.h);paceval_FreeLibrary();}
 int add(string id,string version,string category,string formula,string units,string vars,int nv){
  Graph g{move(id),move(version),move(category),move(formula),move(units),move(vars),nv,nullptr};
  g.h=paceval_CreateComputation(g.formula.c_str(),(unsigned long)nv,g.vars.c_str(),false,nullptr);
  if(!g.h||paceval_GetIsError(g.h)){char a[256]{},b[256]{};if(g.h)paceval_CreateErrorInformationText(g.h,a,b);throw runtime_error("paceval graph create error "+g.id+" "+a+" "+b+"; formula "+g.formula.substr(0,90));}
  graph_.push_back(move(g));return (int)graph_.size()-1;
 }
 const Graph&at(int i)const{return graph_.at(i);}
 const vector<Graph>&all()const{return graph_;}
 vector<double> single_batch(int id,const vector<double>&data,int nv){
  ck(data.size()%nv==0,"Single batch input shape");const auto&g=at(id);ck(nv==g.nvars,"Wrong input variable count");size_t n=data.size()/nv;
  vector<double>copy=data,output(n,numeric_limits<double>::quiet_NaN());vector<int>err(n,-1);
  bool fail=paceval_dGetComputationResultExt(g.h,copy.data(),(unsigned long)n,output.data(),nullptr,nullptr,err.data());
  ck(!fail,"paceval single-graph batch failed: "+g.id);
  for(size_t j=0;j<n;j++)ck(err[j]==0&&isfinite(output[j]),"Invalid single graph result: "+g.id);
  eval_outputs_+=n;batch_calls_++;return output;
 }
 vector<double> multi_batch(const vector<int>&ids,const vector<double>&data,int nv){
  ck(!ids.empty()&&data.size()%nv==0,"Multi batch input shape");size_t n=data.size()/nv;
  vector<PACEVAL_HANDLE>h;for(int id:ids){const auto&g=at(id);ck(g.nvars==nv&&g.vars==at(ids.front()).vars,"Mixed graph input schema");h.push_back(g.h);}
  vector<double>copy=data,out(ids.size()*n,numeric_limits<double>::quiet_NaN());vector<int>err(out.size(),-1);
  bool fail=paceval_dGetMultipleComputationsResultsExt(h.data(),(unsigned long)h.size(),copy.data(),(unsigned long)n,out.data(),nullptr,nullptr,err.data());
  ck(!fail,"paceval multi-graph batch failed");for(size_t j=0;j<err.size();j++)ck(err[j]==0&&isfinite(out[j]),"Invalid multi graph output at "+to_string(j)+" code "+to_string(err[j]));
  eval_outputs_+=out.size();batch_calls_++;return out;
 }
 double scalar(int id,vector<double>data){auto&g=at(id);ck(data.size()==(size_t)g.nvars,"Scalar count mismatch");double r=paceval_dGetComputationResult(g.h,data.data(),nullptr,nullptr);ck(!paceval_GetIsError(g.h)&&isfinite(r),"Scalar result invalid");scalar_calls_++;eval_outputs_++;return r;}
 size_t outputs()const{return eval_outputs_;}size_t batches()const{return batch_calls_;}size_t scalars()const{return scalar_calls_;}
};
static string one_segment(int k,int n,int v,bool derivative){
 double lo=double(k)/n,hi=double(k+1)/n,a=prototype(lo,v),b=prototype(hi,v),m=(b-a)*n;
 string cond="((x>="+fmt(lo)+") AND (x"+(k==n-1?"<=":"<")+fmt(hi)+"))";
 return "("+cond+"*("+(derivative?fmt(m):"("+fmt(a)+"+("+fmt(m)+")*(x-"+fmt(lo)+"))")+"))";
}
static string segment_sum(int first,int last,int n,int ver,bool deriv){string s="(";for(int i=first;i<last;i++){if(i>first)s+="+";s+=one_segment(i,n,ver,deriv);}return s+")";}
struct Version{vector<int>interp,slope;vector<int>post;vector<string>names;int monolithic=-1;};
static string expr_value(){return "(S*(1+0.00035*(T-20))+0.0005*(T-20)+0.000075*sin(7*x)*(T-20)+d*(0.001+0.0015*x))";}
static string expr_dx(){return "(m*(1+0.00035*(T-20))+0.000525*cos(7*x)*(T-20)+0.0015*d)";}
static string expr_dt(){return "(0.00035*S+0.0005+0.000075*sin(7*x))";}
static string expr_dd(){return "(0.001+0.0015*x)";}
static string expr_unc(){return "sqrt(("+expr_dx()+"*ux)^2+("+expr_dt()+"*ut)^2+("+expr_dd()+"*ud)^2+umod^2)";}
static string expr_err(){return "("+expr_value()+"-ref)";}
static Version create_model(Engine&e,int n,int b,int v){
 Version r;string vers="v"+to_string(v+1);
 for(int k=0;k<n;k+=b){r.interp.push_back(e.add("interpolant_block_"+to_string(k/b),vers,"interpolation",segment_sum(k,min(n,k+b),n,v,false),"normalized",vars_post,11));
 r.slope.push_back(e.add("slope_block_"+to_string(k/b),vers,"interpolation",segment_sum(k,min(n,k+b),n,v,true),"normalized",vars_post,11));}
 // Postprocessing expressions are complete persistent paceval computations; host only supplies S,m.
 vector<pair<string,string>> defs={{"corrected_value",expr_value()},{"slope_dx",expr_dx()},{"sensitivity_temperature",expr_dt()},
 {"sensitivity_drift",expr_dd()},{"combined_uncertainty",expr_unc()},{"residual",expr_err()},
 {"absolute_residual","abs("+expr_err()+")"},
 {"acceptance_margin","(tol-abs("+expr_err()+")-2*"+expr_unc()+")"},
 {"rejection_margin","(tol-abs("+expr_err()+")+2*"+expr_unc()+")"},
 {"normalized_difference","(abs("+expr_err()+")/(tol+"+expr_unc()+"))"},
 {"expanded_uncertainty","(2*"+expr_unc()+")"},
 {"quality_fraction","(1/(1+abs("+expr_err()+")/(tol+"+expr_unc()+")))"}};
 for(int j=0;j<16;j++){
 double w1=.15+.02*j,w2=.7+.035*j,w3=.03+.002*j,w4=.005+.0005*j;
 string ex="("+fmt(w1)+"*abs("+expr_err()+")+"+fmt(w2)+"*"+expr_unc()+"+"+fmt(w3)+"*abs("+expr_dx()+"*ux)+"+fmt(w4)+"*abs(d))";
 defs.push_back({"governance_score_"+to_string(j+1),ex});
 }
 for(auto&x:defs){r.names.push_back(x.first);r.post.push_back(e.add(x.first,vers,"calibration_quality",x.second,"normalized",vars_post,11));}
 return r;
}
static int block_index(double x,int n,int b){return min(n-1,(int)floor(x*n))/b;}
struct Calc{double S=0,m=0,g=0,dx=0,dt=0,dd=0,u=0,err=0,accept=0,reject=0,quality=0;string decision;array<double,16>governance{};};
static Calc reference(const Row&r,int ver,int n){
 int k=min(n-1,int(floor(r.x*n)));double lo=double(k)/n;
 double a=prototype(lo,ver),b=prototype(double(k+1)/n,ver),m=(b-a)*n,S=a+m*(r.x-lo);
 Calc c;c.S=S;c.m=m;c.g=S*(1+.00035*(r.T-20))+.0005*(r.T-20)+.000075*sin(7*r.x)*(r.T-20)+r.d*(.001+.0015*r.x);
 c.dx=m*(1+.00035*(r.T-20))+.000525*cos(7*r.x)*(r.T-20)+.0015*r.d;
 c.dt=.00035*S+.0005+.000075*sin(7*r.x);c.dd=.001+.0015*r.x;
 c.u=sqrt(pow(c.dx*r.ux,2)+pow(c.dt*r.ut,2)+pow(c.dd*r.ud,2)+pow(r.umod,2));c.err=c.g-r.ref;
 c.accept=r.tol-abs(c.err)-2*c.u;c.reject=r.tol-abs(c.err)+2*c.u;
 c.quality=1/(1+abs(c.err)/(r.tol+c.u));c.decision=c.accept>=0?"ACCEPT":c.reject<0?"REJECT":"REVIEW";return c;
}
static void verify_close(double a,double b,const string&where,double abs_tol=3e-12){ck(isfinite(a)&&isfinite(b)&&abs(a-b)<=abs_tol,"Mismatch at "+where+" actual="+fmt(a)+" oracle="+fmt(b));}
static vector<Calc> evaluate(Engine&e,const Version&v,const vector<Row>&rows,int ver,int n,int b,int batch){
 size_t N=rows.size();vector<Calc>res(N);vector<vector<size_t>>byblock(n/b);
 for(size_t i=0;i<N;i++)byblock[block_index(rows[i].x,n,b)].push_back(i);
 for(int block=0;block<n/b;block++){
  auto&idx=byblock[block];for(size_t start=0;start<idx.size();start+=batch){size_t cnt=min((size_t)batch,idx.size()-start);
   vector<double>packed;packed.reserve(cnt*11);for(size_t j=0;j<cnt;j++){auto&r=rows[idx[start+j]];packed.insert(packed.end(),{r.x,r.T,r.d,0,0,r.ref,r.tol,r.ux,r.ut,r.ud,r.umod});}
   auto s=e.single_batch(v.interp[block],packed,11);auto m=e.single_batch(v.slope[block],packed,11);
   for(size_t j=0;j<cnt;j++){res[idx[start+j]].S=s[j];res[idx[start+j]].m=m[j];}
  }
 }
 // Every complete correction and score is evaluated inside paceval, in multi-graph batches.
 for(size_t start=0;start<N;start+=batch){size_t cnt=min((size_t)batch,N-start);vector<double>p;for(size_t j=0;j<cnt;j++){auto&r=rows[start+j];auto&c=res[start+j];p.insert(p.end(),{r.x,r.T,r.d,c.S,c.m,r.ref,r.tol,r.ux,r.ut,r.ud,r.umod});}
  auto out=e.multi_batch(v.post,p,11);for(size_t j=0;j<cnt;j++){
   auto&c=res[start+j];const auto&row=rows[start+j];size_t nx=cnt;
   c.g=out[0*nx+j];c.dx=out[1*nx+j];c.dt=out[2*nx+j];c.dd=out[3*nx+j];c.u=out[4*nx+j];c.err=out[5*nx+j];c.accept=out[7*nx+j];c.reject=out[8*nx+j];c.quality=out[11*nx+j];
   c.decision=c.accept>=0?"ACCEPT":c.reject<0?"REJECT":"REVIEW";for(int gi=0;gi<16;gi++)c.governance[gi]=out[(12+gi)*nx+j];
   auto native=reference(row,ver,n);verify_close(c.S,native.S,"interpolation");verify_close(c.m,native.m,"slope");verify_close(c.g,native.g,"value");verify_close(c.dx,native.dx,"dx");verify_close(c.dt,native.dt,"dT");verify_close(c.dd,native.dd,"ddrift");verify_close(c.u,native.u,"uncertainty");verify_close(c.err,native.err,"residual");verify_close(c.accept,native.accept,"acceptance");verify_close(c.reject,native.reject,"rejection");verify_close(c.quality,native.quality,"quality");
   ck(c.decision==native.decision,"Decision mismatch");
   for(size_t k=0;k<v.post.size();k++)ck(isfinite(out[k*nx+j]),"Nonfinite score");
  }
 }
 return res;
}
static void generate_surface(const fs::path&root,Engine&e,const vector<Version>&versions,int n,int b,int batch){
 vector<Row>rows;rows.reserve(61*41);
 for(int ix=0;ix<=60;ix++)for(int it=0;it<=40;it++){
  double x=double(ix)/60,T=60.0*it/40;
  double target=prototype(x,0)*(1+.00035*(T-20))+.0005*(T-20)+.000075*sin(7*x)*(T-20);
  rows.push_back({"surface",ix*41+it,x,T,0,target,.0025,.00025,.3,.16,.00035});
 }
 vector<Calc>a=evaluate(e,versions[0],rows,0,n,b,batch),c=evaluate(e,versions[1],rows,1,n,b,batch);
 ofstream o(root/"results/calibration_surface.csv");o<<"version,x,T,corrected_value,reference,combined_uncertainty,acceptance_margin,sensitivity_T,sensitivity_x,decision\n";
 for(int v=0;v<2;v++)for(size_t i=0;i<rows.size();i++){
  auto&r=rows[i];auto&q=(v==0?a:c)[i];o<<"v"<<v+1<<","<<setprecision(17)<<r.x<<","<<r.T<<","<<q.g<<","<<r.ref<<","<<q.u<<","<<q.accept<<","<<q.dt<<","<<q.dx<<","<<q.decision<<"\n";
 }
}
static void save(const fs::path&root,const vector<Row>&rows,const vector<Calc>&a,const vector<Calc>&b,Engine&e,int n,int block){
 fs::create_directories(root/"results");
 {ofstream o(root/"results/calibrated_samples.csv");o<<"scenario,seq,x,T,drift,reference,tolerance,version,interpolant,local_slope,corrected_value,sensitivity_x,sensitivity_T,sensitivity_drift,combined_uncertainty,residual,acceptance_margin,rejection_margin,quality_fraction,decision\n";
  for(int ver=0;ver<2;ver++)for(size_t i=0;i<rows.size();i++){auto&r=rows[i];auto&c=(ver==0?a:b)[i];o<<r.scenario<<","<<r.seq<<","<<setprecision(17)<<r.x<<","<<r.T<<","<<r.d<<","<<r.ref<<","<<r.tol<<",v"<<ver+1<<","<<c.S<<","<<c.m<<","<<c.g<<","<<c.dx<<","<<c.dt<<","<<c.dd<<","<<c.u<<","<<c.err<<","<<c.accept<<","<<c.reject<<","<<c.quality<<","<<c.decision<<"\n";}}
 {ofstream o(root/"results/governance_scores.csv");o<<"version,scenario,seq,score_index,score_value\n";for(int ver=0;ver<2;ver++)for(size_t i=0;i<rows.size();i++)for(int j=0;j<16;j++)o<<"v"<<ver+1<<","<<rows[i].scenario<<","<<rows[i].seq<<","<<(j+1)<<","<<setprecision(17)<<(ver==0?a:b)[i].governance[j]<<"\n";}
 {ofstream o(root/"results/version_differences.csv");o<<"scenario,seq,x,T,corrected_v1,corrected_v2,revision_delta,decision_v1,decision_v2,decision_changed\n";
 for(size_t i=0;i<rows.size();i++)o<<rows[i].scenario<<","<<rows[i].seq<<","<<setprecision(17)<<rows[i].x<<","<<rows[i].T<<","<<a[i].g<<","<<b[i].g<<","<<b[i].g-a[i].g<<","<<a[i].decision<<","<<b[i].decision<<","<<(a[i].decision!=b[i].decision)<<"\n";}
 {ofstream o(root/"results/graph_registry.csv");o<<"graph_id,version,category,expression,formula_characters,unit,input_schema,status\n";
 for(const auto&g:e.all())o<<g.id<<","<<g.version<<","<<g.category<<",\""<<g.formula<<"\","<<g.formula.size()<<","<<g.units<<",\""<<g.vars<<"\",executed\n";}
 {ofstream o(root/"results/math_execution_inventory.csv");o<<"component,execution_engine,role,evidence\n";for(const auto&g:e.all())o<<g.category<<",paceval,"<<g.id<<",real_persistent_graph\n";
 o<<"batch_routing,C++_host,group_data_by_piecewise_block,index_routing\n";
 o<<"synthetic_measurement_input,C++_host,load_and_validate_data,CSV_schema\n";
 o<<"decision_selection,C++_host,select_status_from_paceval_margins,control_flow\n";
 o<<"native_reference,C++_host,independent_numerical_cross_check,assertions\n";}
 {ofstream o(root/"results/scenario_summary.csv");o<<"version,scenario,records,accepted,review,rejected,maximum_abs_residual,maximum_uncertainty\n";
 for(int ver=0;ver<2;ver++)for(string tag:{"machine_axis","precision_sensor","quality_gate","temperature_cycle"}){int ac=0,rv=0,rj=0,num=0;double mr=0,mu=0;for(size_t i=0;i<rows.size();i++)if(rows[i].scenario==tag){const auto&c=(ver==0?a:b)[i];num++;ac+=c.decision=="ACCEPT";rv+=c.decision=="REVIEW";rj+=c.decision=="REJECT";mr=max(mr,abs(c.err));mu=max(mu,c.u);}o<<"v"<<ver+1<<","<<tag<<","<<num<<","<<ac<<","<<rv<<","<<rj<<","<<setprecision(16)<<mr<<","<<mu<<"\n";}}
 {ofstream o(root/"results/sdk_run_summary.json");o<<"{\n  \"sdk\": \"paceval 4.25\",\n  \"original_paceval_used\": true,\n  \"model_versions\": 2,\n  \"intervals_per_version\": "<<n<<",\n  \"segments_per_graph\": "<<block<<",\n  \"sample_count\": "<<rows.size()<<",\n  \"graph_count\": "<<e.all().size()<<",\n  \"batch_calls\": "<<e.batches()<<",\n  \"scalar_calls\": "<<e.scalars()<<",\n  \"graph_outputs\": "<<e.outputs()<<",\n  \"data_origin\": \"synthetic\",\n  \"independent_cpp_numerical_checks\": "<<(rows.size()*2*11)<<",\n  \"performance_comparison\": false,\n  \"tinc_certification\": false\n}\n";}
}
static void run(const fs::path&root,int batch,int n,int seg){ck(batch>0&&batch<=1024,"Batch size must be 1..1024");ck(n>0&&seg>0&&n%seg==0,"Intervals must be divisible by graph size");
 auto rows=read_rows(root);Engine e;vector<Version>v;
 for(int k=0;k<2;k++)v.push_back(create_model(e,n,seg,k));
 // Anchor to the explicit three-point example from the predecessor study.
 int a=e.add("historical_three_point_example","anchor","original_example","(((x>=1.5) AND (x<2.5))*(6-3*(x-1.5))+((x>=2.5) AND (x<=3.5))*(3+22*(x-2.5)))","illustrative","x",1);
 for(auto [x,y]:vector<pair<double,double>>{{1.5,6},{2.0,4.5},{2.5,3},{3,14},{3.5,25}})verify_close(e.scalar(a,{x}),y,"original three-point",1e-13);
 auto A=evaluate(e,v[0],rows,0,n,seg,batch);auto B=evaluate(e,v[1],rows,1,n,seg,batch);
 generate_surface(root,e,v,n,seg,batch);
 save(root,rows,A,B,e,n,seg);cout<<"PASS original paceval SDK. graph_count="<<e.all().size()<<" model_versions=2 rows="<<rows.size()<<" graph_outputs="<<e.outputs()<<" batch_calls="<<e.batches()<<"\n";
}
int main(int argc,char**argv){try{fs::path root=argc>1?argv[1]:".";int batch=argc>2?stoi(argv[2]):128;int n=argc>3?stoi(argv[3]):4096,seg=argc>4?stoi(argv[4]):256;run(root,batch,n,seg);return 0;}catch(exception&e){cerr<<"ERROR: "<<e.what()<<"\n";return 1;}}
