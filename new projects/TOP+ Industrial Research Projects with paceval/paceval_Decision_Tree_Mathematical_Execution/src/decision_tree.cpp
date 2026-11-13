// paceval Decision-Tree Mathematical Execution Research
// AGPL-licensed paceval API sources are used unchanged except the relative include path.
// Non-safety-critical synthetic condition and production-quality decision support.
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
#include <map>
#include <random>
#include <sstream>
#include <stdexcept>
#include <string>
#include <vector>
using namespace std;
namespace fs=std::filesystem;
using Vec=array<double,8>;
static const string kVariables="t v p l i d b s";
static void require(bool ok,const string& msg){if(!ok)throw runtime_error(msg);}
static string fnum(double x){ostringstream ss;ss<<setprecision(17)<<x;return ss.str();}
static string quote(const string& s){string v="\"";for(char c:s){if(c=='\"')v+="\"\"";else if(c=='\n')v+=' ';else v+=c;}return v+'"';}
static int col(int depth){return depth;} // t,v,p,l,i,d each used once per root-to-leaf path
static const char* names[]={"t","v","p","l","i","d"};
static double threshold(int ver,int level,int node){
  // Every threshold is inside the documented valid input range; branch-specific thresholds.
  const double centers[6]={53.0,5.4,7.5,49.0,14.2,0.43};
  const double steps[6]={1.25,0.17,0.26,1.4,0.48,0.012};
  int k=(node*5+level*3)%7-3;
  return centers[level]+(ver==2?steps[level]*1.4:0.0)+steps[level]*k;
}
static double leaf_value(int ver,int leaf){
 return 0.13+0.011*(leaf%23)+0.021*(leaf/23)+(ver==2?(leaf%5==0?0.065:0.017):0.0);
}
struct Leaf {int id; string path; double val;};
static vector<Leaf> leaves(int ver){
 vector<Leaf> out;
 auto walk=[&](auto&& self,int depth,int node,int leafid,string path)->void{
  if(depth==6){out.push_back({leafid,path,leaf_value(ver,leafid)});return;}
  string x=names[col(depth)],th=fnum(threshold(ver,depth,node));
  string left="("+x+"<"+th+")",right="("+x+">="+th+")";
  self(self,depth+1,node*2+1,leafid<<1,path.empty()?left:path+" AND "+left);
  self(self,depth+1,node*2+2,(leafid<<1)+1,path.empty()?right:path+" AND "+right);
 };
 walk(walk,0,0,0,"");return out;
}
static string leaf_sum(int ver,int type){
 auto ls=leaves(ver);string s="(";
 for(size_t j=0;j<ls.size();j++){
  if(j)s+='+';
  string amount=type==0?fnum(ls[j].val):(type==1?to_string(ls[j].id):"1");
  s+="(("+ls[j].path+")*("+amount+"))";
 }
 return s+")";
}
static string nested_tree(int ver){
 auto visit=[&](auto&& self,int depth,int node,int leafid)->string{
  if(depth==6)return fnum(leaf_value(ver,leafid));
  string c="("+string(names[col(depth)])+"<"+fnum(threshold(ver,depth,node))+")";
  return "("+c+"*("+self(self,depth+1,node*2+1,leafid<<1)+")+(1-"+c+")*("+self(self,depth+1,node*2+2,(leafid<<1)+1)+"))";
 };
 return visit(visit,0,0,0);
}
static int native_leaf(int ver,const Vec& x){int node=0,id=0;for(int depth=0;depth<6;depth++){bool right=x[depth]>=threshold(ver,depth,node);id=id*2+(right?1:0);node=node*2+(right?2:1);}return id;}
static double native_score(int ver,const Vec& x){
 double b=leaf_value(ver,native_leaf(ver,x));
 return b+0.11*pow(x[1]/12.0,2)+0.035*pow((x[0]-45.0)/55.0,2)+0.04*pow(x[4]/30.0,2)+0.03*x[5]+(ver==2?0.012*pow((x[2]-7.0)/8.0,2):0.0);
}
static bool in_domain(const Vec& a){return isfinite(a[0])&&a[0]>=0&&a[0]<=100&&isfinite(a[1])&&a[1]>=0&&a[1]<=15&&isfinite(a[2])&&a[2]>=0&&a[2]<=16&&isfinite(a[3])&&a[3]>=0&&a[3]<=100&&isfinite(a[4])&&a[4]>=0&&a[4]<=32&&isfinite(a[5])&&a[5]>=0&&a[5]<=1;}
struct Graph {string id,version,purpose,formula,units;PACEVAL_HANDLE handle=nullptr;};
struct Engine {
 vector<Graph> graph;size_t outputs=0,batches=0,scalar=0;
 Engine(){require(paceval_InitializeLibrary(nullptr),"paceval_InitializeLibrary failed");}
 ~Engine(){for(auto&g:graph)if(g.handle)paceval_DeleteComputation(g.handle);paceval_FreeLibrary();}
 int add(const string& id,const string& ver,const string& purpose,const string& formula,const string& units){
  Graph g{id,ver,purpose,formula,units,paceval_CreateComputation(formula.c_str(),8,kVariables.c_str(),false,nullptr)};
  if(!g.handle||paceval_GetIsError(g.handle)){char m[256]{},d[256]{};if(g.handle)paceval_CreateErrorInformationText(g.handle,m,d);throw runtime_error("Graph creation failed ["+id+"] "+m+" "+d);}
  graph.push_back(g);return (int)graph.size()-1;
 }
 vector<double> multi(const vector<int>& ids,const vector<Vec>& rows){
  require(!ids.empty()&&!rows.empty(),"empty API batch");
  vector<PACEVAL_HANDLE> h;h.reserve(ids.size());for(int j:ids)h.push_back(graph.at(j).handle);
  vector<double> x;x.reserve(rows.size()*8);for(auto&r:rows)for(double v:r)x.push_back(v);
  vector<double> out(ids.size()*rows.size(),numeric_limits<double>::quiet_NaN());vector<int>err(out.size(),-1);
  // Documented API layout: graph-major output; observation-major 8-column input.
  bool failed=paceval_dGetMultipleComputationsResultsExt(h.data(),(unsigned long)h.size(),x.data(),(unsigned long)rows.size(),out.data(),nullptr,nullptr,err.data());
  require(!failed,"paceval multi-graph batch failed");
  for(size_t j=0;j<out.size();j++)require(err[j]==0&&isfinite(out[j]),"paceval computation failed code "+to_string(err[j])+" index "+to_string(j));
  outputs+=out.size();batches++;return out;
 }
 double evaluate(int id,Vec x){double out=paceval_dGetComputationResult(graph.at(id).handle,x.data(),nullptr,nullptr);require(isfinite(out)&&!paceval_GetIsError(graph.at(id).handle),"paceval scalar evaluation failed");outputs++;scalar++;return out;}
};
static vector<int> register_tree(Engine& eng,int ver){
 string v="v"+to_string(ver),score=string("(b+0.11*(v/12)^2+0.035*((t-45)/55)^2+0.04*(i/30)^2+0.03*d")+(ver==2?"+0.012*((p-7)/8)^2":"")+")";
 vector<int> ids;
 auto add=[&](const string& suffix,const string& purpose,const string& formula,const string& units){ids.push_back(eng.add(v+"_"+suffix,v,purpose,formula,units));};
 add("masked_tree","64 leaf path predicates * scores",leaf_sum(ver,0),"dimensionless");
 add("nested_tree","Equivalent binary branching expression",nested_tree(ver),"dimensionless");
 add("leaf_index","Decision leaf ID from mutually exclusive path masks",leaf_sum(ver,1),"integer");
 add("coverage","Sum of path membership predicates",leaf_sum(ver,2),"unity");
 add("risk","Combined industrial risk score",score,"dimensionless");
 add("accept_margin","Positive iff below ACCEPT threshold","(0.30-s)","dimensionless");
 add("reject_margin","Positive iff below REJECT threshold","(0.43-s)","dimensionless");
 add("guard_temperature","Temperature guard margin","(87-t)","deg C");
 add("guard_vibration","Vibration guard margin","(10-v)","mm/s");
 add("guard_pressure","Pressure guard margin","(12.5-p)","bar");
 add("guard_load","Load guard margin","(90-l)","percent");
 add("guard_current","Current guard margin","(26-i)","A");
 add("guard_drift","Drift guard margin","(0.8-d)","dimensionless");
 add("sensitivity_temperature","Analytic in-leaf score derivative wrt temperature","(0.07*(t-45)/(55^2))","1/deg C");
 add("sensitivity_vibration","Analytic in-leaf score derivative wrt vibration","(0.22*v/(12^2))","s/mm");
 add("sensitivity_pressure","Analytic in-leaf derivative wrt pressure",ver==2?"(0.024*(p-7)/(8^2))":"(0*p)","1/bar");
 return ids;
}
struct Sample {int id;string group;Vec x;};
static vector<Sample> make_samples(){
 vector<Sample> samples;mt19937_64 g(20261113);
 uniform_real_distribution<double> t(15,91),v(0.0,11.0),p(1.5,13.0),l(8,95),i(1.0,28.0),d(0.01,0.95);
 auto add=[&](string group,Vec r){samples.push_back({int(samples.size()),group,r});};
 for(int j=0;j<1280;j++){Vec r={t(g),v(g),p(g),l(g),i(g),d(g),0,0};add("synthetic_sensor",r);}
 for(int j=0;j<20;j++)for(int k=0;k<20;k++){
  Vec r={20+j*3.2,0.3+k*0.55,7.0,50.0,13.0,0.42,0,0};add("parameter_surface",r);
 }
 for(int ver=1;ver<=2;ver++)for(int lev=0;lev<6;lev++){
  Vec r={54,5.5,7.2,50,14,0.43,0,0};r[lev]=threshold(ver,lev,lev==0?0:(1<<lev)-1);add("threshold_equality",r);
 }
 for(auto&x:samples)require(in_domain(x.x),"invalid generated sample");
 return samples;
}
static string decide(double score,const vector<double>& margins){
 for(double m:margins)if(m<0)return "REJECT";
 if(score<0.30)return "ACCEPT";
 if(score<0.43)return "REVIEW";
 return "REJECT";
}
static void write_outputs(const fs::path& root,Engine& e,const vector<Sample>& samples,const array<vector<int>,2>& models){
 fs::create_directories(root/"results");fs::create_directories(root/"formulas");
 ofstream os(root/"results"/"decision_results.csv");require(bool(os),"file output failure");os<<setprecision(17);
 os<<"sample_id,case_kind,version,t_raw,v_raw,p_raw,load,current,drift,v_corrected,p_corrected,base_score,nested_score,leaf_index,path_coverage,final_score,accept_margin,reject_margin,guard_t,guard_v,guard_p,guard_l,guard_i,guard_d,dscore_dt,dscore_dv,dscore_dp,status\n";
 vector<Vec> raw;raw.reserve(samples.size());for(auto&x:samples)raw.push_back(x.x);
 // Stage A: common sensor correction via real paceval graphs.
 auto corrected=e.multi({0,1},raw);const size_t n=samples.size();
 vector<Vec> stage;stage.reserve(n);
 for(size_t k=0;k<n;k++){Vec x=raw[k];x[1]=corrected[k];x[2]=corrected[n+k];require(in_domain(x),"corrected sample out of range");stage.push_back(x);}
 // Stage B: both model versions, two equivalent tree encodings and path coverage.
 vector<int> first;for(auto&m:models)for(int j=0;j<4;j++)first.push_back(m[j]);
 auto tree=e.multi(first,stage);
 // Stage C: combined score graphs and guards using base returned by paceval.
 for(int ver=1;ver<=2;ver++){
  vector<Vec> combined=stage;
  for(size_t k=0;k<n;k++)combined[k][6]=tree[(ver-1)*4*n+k];
  // Composite risk must be evaluated before margins / sensitivities use its real output.
  auto risk=e.multi({models[ver-1][4]},combined);
  for(size_t k=0;k<n;k++)combined[k][7]=risk[k];
  vector<int> other;for(int j=5;j<16;j++)other.push_back(models[ver-1][j]);
  auto vals=e.multi(other,combined);
  for(size_t k=0;k<n;k++){
   double mask=tree[(ver-1)*4*n+k],nested=tree[((ver-1)*4+1)*n+k],leaf=tree[((ver-1)*4+2)*n+k],coverage=tree[((ver-1)*4+3)*n+k];
   require(abs(mask-nested)<2e-11,"masked/nested mismatch");
   require(abs(coverage-1)<2e-11,"path coverage != 1");
   require(abs(leaf-native_leaf(ver,stage[k]))<1e-8,"leaf ID mismatch");
   require(abs(risk[k]-native_score(ver,stage[k]))<2e-11,"independent C++ score mismatch");
   vector<double> guard;for(int j=2;j<=7;j++)guard.push_back(vals[j*n+k]);
   string status=decide(risk[k],guard);
   auto rawx=samples[k].x,xx=stage[k];
   os<<samples[k].id<<','<<samples[k].group<<",v"<<ver;
   for(int j=0;j<6;j++)os<<','<<rawx[j];
   os<<','<<xx[1]<<','<<xx[2]<<','<<mask<<','<<nested<<','<<leaf<<','<<coverage<<','<<risk[k];
   for(int j=0;j<11;j++)os<<','<<vals[j*n+k];
   os<<','<<status<<'\n';
  }
 }
 // Explicit toy source image, including a<0, b=30, b=10 endpoint ownership.
 ofstream to(root/"results"/"original_tree_example.csv");
 to<<"a,b,paceval_cost,expected_cost\n";
 for(double a:{-2.0,0.0,1.0})for(double b:{9.0,10.0,29.0,30.0}){
  Vec x{};x[0]=a;x[1]=b;
  double pv=e.evaluate(2,x);double expected=a<0?(b<30?8:11):(b<10?7:9);
  require(abs(pv-expected)<1e-12,"original image tree mismatch");
  to<<a<<','<<b<<','<<pv<<','<<expected<<'\n';
 }
 // Graph registry and inventory are created only from successfully created paceval objects.
 ofstream reg(root/"results"/"graph_registry.csv"),inv(root/"results"/"math_execution_inventory.csv");
 reg<<"graph_id,version,purpose,units,formula,executed\n";
 inv<<"function_id,domain_quantity,mathematical_definition,units,execution_owner,paceval_graph_id,formula_version,api_path,reference_test,status,host_reason\n";
 for(const Graph&g:e.graph){reg<<quote(g.id)<<','<<g.version<<','<<quote(g.purpose)<<','<<quote(g.units)<<','<<quote(g.formula)<<",yes\n";
 inv<<quote(g.id)<<','<<quote(g.purpose)<<','<<quote(g.formula)<<','<<quote(g.units)<<",paceval,"<<quote(g.id)<<','<<g.version<<",CreateComputation;dGetMultipleComputationsResultsExt;dGetComputationResult,independent_cpp_and_python,executed,\n";}
 for(auto&pair:vector<pair<string,string>>{{"data_generation","Deterministic input synthesis"},{"decision_state","Discrete ACCEPT/REVIEW/REJECT mapping"},{"tree_structure","Tree data generation and compilation"},{"file_handling","CSV, validation and ownership"}})
 inv<<pair.first<<','<<quote(pair.second)<<",not_a_scalar_formula,dimensionless,host,,all,standard_cpp,independent_script,executed,"<<quote("State, policy or data orchestration")<<'\n';
 ofstream summary(root/"results"/"sdk_execution.txt");
 summary<<"Original paceval 4.25, dynamic Linux shared library, real execution\n";
 summary<<"total_graphs="<<e.graph.size()<<"\ninput_samples="<<samples.size()<<"\nmodel_versions=2\n";
 summary<<"actual_graph_outputs="<<e.outputs<<"\nbatch_calls="<<e.batches<<"\nscalar_api_calls="<<e.scalar<<"\n";
 summary<<"tinc_used=false\nnot_a_runtime_benchmark=true\n";
 cout<<"REAL paceval run OK: graphs="<<e.graph.size()<<" samples="<<samples.size()<<" outputs="<<e.outputs<<" batch_calls="<<e.batches<<"\n";
}
int main(int argc,char**argv){
 try{
  require(argc>=2,"Usage: decision_tree <project-dir> [--invalid]");
  if(argc>2&&string(argv[2])=="--invalid"){Vec x={150,3,4,10,15,0.3,0,0};require(in_domain(x),"Invalid sensor range correctly rejected");}
  fs::path root=fs::absolute(argv[1]);Engine e;
  // Two corrections are themselves paceval expressions, not host calculations.
  e.add("vibration_temperature_correction","common","Physically motivated synthetic vibration compensation","(v*(1+0.002*(t-25)))","mm/s");
  e.add("pressure_temperature_correction","common","Synthetic pressure-temperature correction","(p-0.006*(t-25))","bar");
  // Exact source illustration: four leaves and threshold ownership.
  e.add("original_four_leaf_tree","source_image","Four leaf explicit conditional expression","((t<0) AND (v<30))*(2+6)+((t<0) AND (v>=30))*(2+9)+((t>=0) AND (v<10))*(6+1)+((t>=0) AND (v>=10))*(6+3)","arbitrary cost units");
  auto m1=register_tree(e,1),m2=register_tree(e,2);
  auto samples=make_samples();write_outputs(root,e,samples,{m1,m2});
  return 0;
 }catch(const exception&ex){cerr<<"ERROR: "<<ex.what()<<'\n';return 2;}
}
