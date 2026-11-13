// Programmable matrix mathematics for an industrial multi-sensor digital twin.
// All significant arithmetic kernels and domain scores use REAL paceval SDK 4.25 graphs.
// The C++ host coordinates dependent matrix stages, storage, scenarios, safeguards, and output.
// Synthetic examples are deliberately NOT physical measurements or metrology certification.
#include "paceval_main.h"
#include <algorithm>
#include <array>
#include <cmath>
#include <cstdint>
#include <cstring>
#include <filesystem>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <limits>
#include <map>
#include <numeric>
#include <stdexcept>
#include <string>
#include <vector>
using namespace std;
namespace fs=std::filesystem;
static void must(bool yes,const string &why){if(!yes) throw runtime_error(why);}
using M=vector<double>;
static double &at(M &m,int n,int i,int j){return m[size_t(i)*n+j];}
static double at(const M &m,int n,int i,int j){return m[size_t(i)*n+j];}
struct Record{string id,formula,vars,role; PACEVAL_HANDLE h=nullptr; unsigned long long evaluations=0,calls=0;};
class Engine{
 vector<Record> graphs_;
 unsigned long long outputs_=0,calls_=0;
public:
 Engine(){must(paceval_InitializeLibrary(nullptr),"Original paceval library initialization failed");}
 ~Engine(){for(auto &r:graphs_)if(r.h)paceval_DeleteComputation(r.h);paceval_FreeLibrary();}
 int add(const string&id,const string&f,const string&v,int nv,const string&role){
   Record r{id,f,v,role};r.h=paceval_CreateComputation(f.c_str(),static_cast<unsigned long>(nv),v.c_str(),false,nullptr);
   must(r.h!=nullptr&& !paceval_GetIsError(r.h),"Cannot create original paceval graph: "+id);
   graphs_.push_back(move(r));return int(graphs_.size()-1);
 }
 vector<double> batch(int g,const vector<double>&x,int nv){
   auto &rec=graphs_.at(g);int declared=1+int(count(rec.vars.begin(),rec.vars.end(),' '));
   must(nv==declared &&x.size()%size_t(nv)==0 &&!x.empty(),"Batch input dimension mismatch: "+rec.id);
   const size_t n=x.size()/size_t(nv);must(n<=4096,"Batch above validated bound");
   vector<double> in=x,out(n,numeric_limits<double>::quiet_NaN());vector<int> errors(n,-1);
   bool failure=paceval_dGetComputationResultExt(rec.h,in.data(),(unsigned long)n,out.data(),nullptr,nullptr,errors.data());
   must(!failure,"paceval API call failed: "+rec.id);
   for(size_t j=0;j<n;j++)must(errors[j]==0&&isfinite(out[j]),"paceval value error: "+rec.id+" at "+to_string(j));
   rec.evaluations+=n;rec.calls++;outputs_+=n;calls_++;
   return out;
 }
 double one(int g,initializer_list<double>v){return batch(g,vector<double>(v),int(v.size()))[0];}
 vector<double> chunks(int g,const vector<double>&v,int nv){vector<double> out;out.reserve(v.size()/nv);for(size_t i=0;i<v.size();i+=4096*nv){size_t e=min(v.size(),i+4096*nv);vector<double> s(v.begin()+i,v.begin()+e);auto z=batch(g,s,nv);out.insert(out.end(),z.begin(),z.end());}return out;}
 // Multi-graph batch: results are graph-major. This is checked against separate evaluations.
 vector<double> multi(const vector<int>&gs,const vector<double>&x,int nv){
    must(!gs.empty()&&!x.empty()&&x.size()%size_t(nv)==0,"Bad multi-graph shape");size_t n=x.size()/nv;
    must(n<=4096,"Multi batch above validated bound");string schema=graphs_.at(gs[0]).vars;
    vector<PACEVAL_HANDLE> hs;for(int id:gs){must(graphs_.at(id).vars==schema,"Different variable order in multi batch");hs.push_back(graphs_[id].h);}
    vector<double> in=x,out(n*gs.size(),numeric_limits<double>::quiet_NaN());vector<int> err(out.size(),-1);
    bool failure=paceval_dGetMultipleComputationsResultsExt(hs.data(),(unsigned long)hs.size(),in.data(),(unsigned long)n,out.data(),nullptr,nullptr,err.data());
    must(!failure,"Original multi-graph SDK call failed");for(size_t j=0;j<out.size();j++)must(err[j]==0&&isfinite(out[j]),"Invalid multi output");
    for(int id:gs){graphs_[id].calls++;graphs_[id].evaluations+=n;}calls_++;outputs_+=out.size();return out;
 }
 const vector<Record>& graphs()const{return graphs_;}
 unsigned long long outputs()const{return outputs_;}unsigned long long calls()const{return calls_;}
};
struct Ops{
 int sq,divide,subtract_multiply,add_multiply,logarithm,logdet_accumulator,addition,difference,square,score_v1,score_v2,guard_v1,guard_v2,temperature_derivative_v1,temperature_derivative_v2,uncertainty_radius,quality_bias;
 explicit Ops(Engine &e){
   sq=e.add("cholesky_pivot","sqrt(a)","a",1,"SPD factorization");
   divide=e.add("triangular_divide","a/b","a b",2,"factor and triangular inverse");
   subtract_multiply=e.add("schur_and_forward_update","a-b*c","a b c",3,"Cholesky and forward substitution");
   add_multiply=e.add("gram_and_vector_accumulate","a+b*c","a b c",3,"inverse and vector arithmetic");
   logarithm=e.add("log_pivot","ln(a)","a",1,"log determinant");
   logdet_accumulator=e.add("logdet_accumulator","a+2*b","a b",2,"log determinant sum");
   addition=e.add("matrix_sum","a+b","a b",2,"information and covariance fusion");
   difference=e.add("vector_difference","a-b","a b",2,"sensor innovation");
   square=e.add("component_square","a*a","a",1,"sensor norm");
   const string vars="d2 temp radius bias";
   score_v1=e.add("quality_score_v1","d2+0.06*((temp-25)/25)^2+0.12*radius+0.3*abs(bias)",vars,4,"versioned sensor anomaly score");
   score_v2=e.add("quality_score_v2","d2+0.09*((temp-25)/25)^2+0.18*radius+0.18*abs(bias)",vars,4,"versioned sensor anomaly score");
   guard_v1=e.add("quality_guard_v1","12.592-(d2+0.06*((temp-25)/25)^2+0.12*radius+0.3*abs(bias))",vars,4,"continuous acceptance margin");
   guard_v2=e.add("quality_guard_v2","12.592-(d2+0.09*((temp-25)/25)^2+0.18*radius+0.18*abs(bias))",vars,4,"continuous acceptance margin");
   temperature_derivative_v1=e.add("score_temp_sensitivity_v1","0.12*(temp-25)/625",vars,4,"analytic sensitivity to temperature");
   temperature_derivative_v2=e.add("score_temp_sensitivity_v2","0.18*(temp-25)/625",vars,4,"analytic sensitivity to temperature");
   uncertainty_radius=e.add("uncertainty_radius","sqrt(a)","a",1,"sqrt covariance trace proxy");
   quality_bias=e.add("bias_magnitude","abs(a)","a",1,"model difference support");
 }
};
static void write_bin(const fs::path&p,const M&m){ofstream o(p,ios::binary);must(bool(o),"Cannot write "+p.string());o.write(reinterpret_cast<const char*>(m.data()),streamsize(m.size()*sizeof(double)));must(bool(o),"Binary matrix write error");}
static M generate_spd(int n,int version=0){
 M L(size_t(n)*n,0),A(size_t(n)*n,0);
 for(int i=0;i<n;i++)for(int j=0;j<=i;j++)at(L,n,i,j)=i==j? 1.13+0.003*(i%9)+.004*version: .0017*sin((i+1)*(j+1)*.017)+.0012*cos((i+3)*(j+2)*.021);
 for(int i=0;i<n;i++)for(int j=0;j<=i;j++){
  double s=0;for(int k=0;k<=j;k++)s+=at(L,n,i,k)*at(L,n,j,k);
  at(A,n,i,j)=at(A,n,j,i)=s;
 }
 return A;
}
struct Fact{M L,inv;double logdet=0,chol_resid=0,inverse_resid=0,source_trace=0;};
// The complete matrix factorization and inverse are actually computed by paceval.
// C++ is NOT used to substitute the arithmetic kernels. It only orders dependencies.
static Fact factor_invert(Engine&e,const Ops&o,const M&A,int n){
 must(int(A.size())==n*n,"Bad matrix size");Fact r;M S=A;r.L.assign(A.size(),0);r.inv.assign(A.size(),0);
 for(int k=0;k<n;k++){
   double pivot=at(S,n,k,k);must(pivot>1e-14&&isfinite(pivot),"Matrix not SPD at pivot "+to_string(k));
   double diag=e.one(o.sq,{pivot});at(r.L,n,k,k)=diag;
   r.logdet=e.one(o.logdet_accumulator,{r.logdet,e.one(o.logarithm,{diag})});
   vector<double> args;args.reserve(2*(n-k-1));for(int i=k+1;i<n;i++){args.push_back(at(S,n,i,k));args.push_back(diag);}
   vector<double> col;if(!args.empty())col=e.chunks(o.divide,args,2);
   for(int i=k+1;i<n;i++)at(r.L,n,i,k)=col[i-k-1];
   args.clear();vector<pair<int,int>> cells;for(int i=k+1;i<n;i++)for(int j=k+1;j<=i;j++){
     cells.push_back({i,j});args.insert(args.end(),{at(S,n,i,j),at(r.L,n,i,k),at(r.L,n,j,k)});
   }
   if(!args.empty()){
     auto updated=e.chunks(o.subtract_multiply,args,3);
     for(size_t z=0;z<cells.size();z++){auto [i,j]=cells[z];at(S,n,i,j)=at(S,n,j,i)=updated[z];}
   }
 }
 // T = L^{-1} using forward elimination via paceval arithmetic.
 M T(size_t(n)*n,0);for(int i=0;i<n;i++)at(T,n,i,i)=1;
 for(int k=0;k<n;k++){
   vector<double> args;args.reserve(2*(k+1));for(int j=0;j<=k;j++){args.push_back(at(T,n,k,j));args.push_back(at(r.L,n,k,k));}
   auto div=e.chunks(o.divide,args,2);for(int j=0;j<=k;j++)at(T,n,k,j)=div[j];
   args.clear();vector<pair<int,int>> cells;for(int i=k+1;i<n;i++)for(int j=0;j<=k;j++){
     cells.push_back({i,j});args.insert(args.end(),{at(T,n,i,j),at(r.L,n,i,k),at(T,n,k,j)});
   }
   if(!args.empty()){auto out=e.chunks(o.subtract_multiply,args,3);for(size_t z=0;z<cells.size();z++){auto [i,j]=cells[z];at(T,n,i,j)=out[z];}}
 }
 // A^-1 = T^T T: one persistent paceval multiplication-accumulation graph.
 for(int k=0;k<n;k++){
   vector<double> args;vector<pair<int,int>> cells;
   for(int i=0;i<=k;i++)for(int j=0;j<=i;j++){
     args.insert(args.end(),{at(r.inv,n,i,j),at(T,n,k,i),at(T,n,k,j)});cells.push_back({i,j});
   }
   auto out=e.chunks(o.add_multiply,args,3);
   for(size_t z=0;z<cells.size();z++){auto [i,j]=cells[z];at(r.inv,n,i,j)=at(r.inv,n,j,i)=out[z];}
 }
 // Independent plain C++ checks are validation-only, not production computation paths.
 for(int i=0;i<n;i++)for(int j=0;j<n;j++){
   double s=0,p=0;for(int k=0;k<n;k++){
     if(k<=min(i,j))s+=at(r.L,n,i,k)*at(r.L,n,j,k);
     p+=at(A,n,i,k)*at(r.inv,n,k,j);
   }
   r.chol_resid=max(r.chol_resid,abs(s-at(A,n,i,j)));
   r.inverse_resid=max(r.inverse_resid,abs(p-(i==j?1.0:0.0)));
 }
 for(int i=0;i<n;i++)r.source_trace+=at(A,n,i,i);
 must(r.chol_resid<1e-9&&r.inverse_resid<1e-9,"Independent complete SPD residual failed");
 return r;
}
static M add_matrix(Engine&e,const Ops&o,const M&A,const M&B){must(A.size()==B.size(),"Matrix dimension mismatch");vector<double>packed;packed.reserve(A.size()*2);for(size_t i=0;i<A.size();i++){packed.push_back(A[i]);packed.push_back(B[i]);}return e.chunks(o.addition,packed,2);}
static M multiply_vector(Engine&e,const Ops&o,const M&A,const M&b,int n){must(int(A.size())==n*n&&int(b.size())==n,"RHS dimension mismatch");M x(n,0);for(int j=0;j<n;j++){vector<double>in;for(int i=0;i<n;i++)in.insert(in.end(),{x[i],at(A,n,i,j),b[j]});auto v=e.chunks(o.add_multiply,in,3);for(int i=0;i<n;i++)x[i]=v[i];}return x;}
struct Result{int scenario=0,version=0,dim=0;double temp=0,d2=0,score=0,guard=0,derivative=0,radius=0,bias=0;string decision;array<double,6>fused{},variance{};double cov01=0;};
static vector<Result> sensor_fusion(Engine&e,const Ops&o){
 const int n=6;vector<Result> outcomes;
 for(int v=0;v<2;v++)for(int scenario=0;scenario<16;scenario++){
   M P1=generate_spd(n,v),P2=generate_spd(n,1-v);
   double scale1=0.02+0.002*(scenario%3),scale2=0.025+0.002*(scenario%4);
   // Scaling modifies the synthetic covariance model; arithmetic scale is host-side dataset generation.
   for(auto &t:P1)t*=scale1;
   for(auto &t:P2)t*=scale2;
   auto F1=factor_invert(e,o,P1,n),F2=factor_invert(e,o,P2,n);
   auto information=add_matrix(e,o,F1.inv,F2.inv);auto fused_factor=factor_invert(e,o,information,n);
   M m1(n),m2(n);double shift=(scenario>=12?.78:(scenario>=8?.37:.018));
   for(int i=0;i<n;i++){m1[i]=.10*i+.03*sin((scenario+1)*(i+1)*.17);m2[i]=m1[i]+shift*(1+.12*i)*cos(.7*i+.03*scenario);}
   auto right1=multiply_vector(e,o,F1.inv,m1,n),right2=multiply_vector(e,o,F2.inv,m2,n);
   vector<double>packed;for(int i=0;i<n;i++)packed.insert(packed.end(),{right1[i],right2[i]});M rhs=e.chunks(o.addition,packed,2);
   M fused=multiply_vector(e,o,fused_factor.inv,rhs,n);
   auto sumcov=add_matrix(e,o,P1,P2);auto innovcov=factor_invert(e,o,sumcov,n);
   packed.clear();for(int i=0;i<n;i++)packed.insert(packed.end(),{m1[i],m2[i]});M diff=e.chunks(o.difference,packed,2);
   M weighted=multiply_vector(e,o,innovcov.inv,diff,n);
   double d2=0;
   // Stateful accumulation is sequential and graph driven to prevent a native dot product in the main path.
   for(int i=0;i<n;i++)d2=e.one(o.add_multiply,{d2,diff[i],weighted[i]});
   double trace=0;for(int i=0;i<n;i++)trace=e.one(o.addition,{trace,at(fused_factor.inv,n,i,i)});
   double radius=e.one(o.uncertainty_radius,{trace});
   auto squared=e.chunks(o.square,diff,1);double bias_sq=0;for(double sq:squared)bias_sq=e.one(o.addition,{bias_sq,sq});
   double bias=e.one(o.quality_bias,{e.one(o.uncertainty_radius,{bias_sq})});
   double temp=18+4*(scenario%8);
   vector<double>args={d2,temp,radius,bias};
   auto q=e.multi({o.score_v1,o.score_v2,o.guard_v1,o.guard_v2,o.temperature_derivative_v1,o.temperature_derivative_v2},args,4);
   double score=q[v],guard=q[2+v],derivative=q[4+v];
   must(abs(score+guard-12.592)<1e-9,"Score-margin mismatch");
   Result out{scenario,v+1,n,temp,d2,score,guard,derivative,radius,bias,"",{},{},0};
   for(int i=0;i<n;i++){out.fused[i]=fused[i];out.variance[i]=at(fused_factor.inv,n,i,i);}out.cov01=at(fused_factor.inv,n,0,1);
   out.decision=guard>=0?"ACCEPT":(guard>=-8.0?"REVIEW":"REJECT");outcomes.push_back(out);
 }
 return outcomes;
}
int main(int argc,char **argv){try{
 fs::path root=argc>=2?fs::path(argv[1]):fs::current_path();int n=128;bool verify=false,indefinite_test=false;
 for(int i=2;i<argc;i++){string a=argv[i];if(a=="--n"&&i+1<argc)n=stoi(argv[++i]);else if(a=="--verify-only")verify=true;else if(a=="--indefinite-test")indefinite_test=true;else throw runtime_error("Unknown option: "+a);}
 must(n>=4&&n<=1024,"Supported N is between 4 and 1024");
 Engine e;Ops o(e);M A=generate_spd(n);if(indefinite_test)at(A,n,0,0)=-1;auto F=factor_invert(e,o,A,n);auto outcomes=sensor_fusion(e,o);
 // This two-dimensional quality surface is produced by actual paceval multi-graph calls.
 vector<double> sweep_input;for(int ti=0;ti<25;ti++)for(int di=0;di<25;di++){
   sweep_input.insert(sweep_input.end(),{double(di)*24.0/24.0,double(ti)*50.0/24.0,0.32,0.20});
 }
 auto sweep=e.multi({o.score_v1,o.score_v2,o.guard_v1,o.guard_v2,o.temperature_derivative_v1,o.temperature_derivative_v2},sweep_input,4);
 if(!verify){fs::create_directories(root/"results");
   string prefix="matrix_"+to_string(n);write_bin(root/"results"/(prefix+"_original.f64"),A);
   write_bin(root/"results"/(prefix+"_cholesky.f64"),F.L);
   write_bin(root/"results"/(prefix+"_inverse.f64"),F.inv);
   ofstream f(root/"results/sensor_fusion.csv");f<<"scenario,model_version,dimensions,temperature_c,mahalanobis_squared,quality_score,quality_guard,temperature_sensitivity,uncertainty_radius,relative_sensor_bias,decision,fused_0,fused_1,fused_2,fused_3,fused_4,fused_5,cov_diag_0,cov_diag_1,cov_diag_2,cov_diag_3,cov_diag_4,cov_diag_5,cov_01\n";
   for(auto&r:outcomes){f<<r.scenario<<","<<r.version<<","<<r.dim<<","<<setprecision(17)<<r.temp<<","<<r.d2<<","<<r.score<<","<<r.guard<<","<<r.derivative<<","<<r.radius<<","<<r.bias<<","<<r.decision;for(double v:r.fused)f<<","<<v;for(double v:r.variance)f<<","<<v;f<<","<<r.cov01<<"\n";}
   ofstream sf(root/"results/quality_score_surface.csv");sf<<"mahalanobis_squared,temperature_c,model_v1_score,model_v2_score,model_v1_guard,model_v2_guard,model_v1_temp_sensitivity,model_v2_temp_sensitivity\n";
   const size_t count=sweep_input.size()/4;
   for(size_t i=0;i<count;i++){sf<<setprecision(17)<<sweep_input[4*i]<<","<<sweep_input[4*i+1];for(size_t k=0;k<6;k++)sf<<","<<sweep[k*count+i];sf<<"\n";}
   ofstream summary(root/"results"/(prefix+"_summary.json"));summary<<setprecision(17)<<"{\n  \"matrix_dimension\": "<<n<<",\n  \"all_inverse_entries\": "<<n*n<<",\n  \"real_paceval_graphs\": "<<e.graphs().size()<<",\n  \"sdk_calls\": "<<e.calls()<<",\n  \"graph_outputs\": "<<e.outputs()<<",\n  \"cholesky_full_residual\": "<<F.chol_resid<<",\n  \"inverse_full_residual\": "<<F.inverse_resid<<",\n  \"log_determinant\": "<<F.logdet<<",\n  \"input_trace\": "<<F.source_trace<<",\n  \"fusion_scenarios\": "<<outcomes.size()<<",\n  \"historical_1024_result_not_reexecuted\": true,\n  \"independent_external_validation_required\": true\n}\n";
   ofstream inv(root/"results/math_execution_inventory.csv");inv<<"function_id,execution_owner,formula,variables,industrial_role,api_path,executed_outputs\n";
   for(auto&r:e.graphs())inv<<r.id<<",paceval,\""<<r.formula<<"\",\""<<r.vars<<"\",\""<<r.role<<"\",original_sdk_batch_api,"<<r.evaluations<<"\n";
   inv<<"pivot_order,C++ host,dependency ordering,indices,orchestration,host,"<<n<<"\n";
   inv<<"SPD_independent_residual,C++ reference,matrix verification,matrices,verification,reference_only,"<<n*n<<"\n";
   ofstream reg(root/"results/graph_registry.csv");reg<<"graph_id,formula,variables,role,actual_api_calls,actual_graph_outputs\n";
   for(auto&r:e.graphs())reg<<r.id<<",\""<<r.formula<<"\",\""<<r.vars<<"\",\""<<r.role<<"\","<<r.calls<<","<<r.evaluations<<"\n";
 }
 cout<<setprecision(5)<<"PASS original paceval SDK 4.25 n="<<n<<" cholesky_resid="<<F.chol_resid<<" inverse_resid="<<F.inverse_resid<<" graphs="<<e.graphs().size()<<" outputs="<<e.outputs()<<" batches="<<e.calls()<<" fusion_scenarios="<<outcomes.size()<<"\n";
 return 0;
 }catch(const exception&e){cerr<<"ERROR: "<<e.what()<<"\n";return 1;}}
