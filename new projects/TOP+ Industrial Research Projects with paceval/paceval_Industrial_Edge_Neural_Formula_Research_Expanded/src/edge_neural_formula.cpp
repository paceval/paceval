// Industrial Edge Neural Formula Execution - reproducible synthetic trained MLP study.
// paceval executes normalization, exported trained inference, downstream score graphs.
// Native C++ is an independent reference, data/controller and decision-policy host.
// The model is illustrative, not a validated fault diagnostic or safety component.
#include "paceval_main.h"
#include <algorithm>
#include <array>
#include <cmath>
#include <cstdlib>
#include <filesystem>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <limits>
#include <map>
#include <numeric>
#include <sstream>
#include <stdexcept>
#include <string>
#include <vector>
using namespace std;
namespace fs=std::filesystem;
static void ck(bool b,const string&m){if(!b)throw runtime_error(m);}
static string ss(double x){ostringstream os;os<<setprecision(17)<<x;return os.str();}
static vector<string> split(const string&s,char d=','){stringstream st(s);string a;vector<string>v;while(getline(st,a,d))v.push_back(a);return v;}
static double parse(const string&s){size_t j=0;double v=stod(s,&j);ck(j==s.size()&&isfinite(v),"nonfinite or invalid input "+s);return v;}
static string join_add(const vector<string>&p){string t="(";for(size_t i=0;i<p.size();i++){if(i)t+="+";t+=p[i];}return t+")";}
static double sigmoid(double v){return (v>=0)?1/(1+exp(-v)):exp(v)/(1+exp(v));}
static string sig(const string&v){return "(1/(1+exp(-("+v+"))))";}
constexpr int INPUTS=8, L1=8,L2=4,VERS=2;
struct Row {string split;int bearing,condition,label;array<double,INPUTS>raw{};};
struct Weights{double a[INPUTS][L1]{},b[L1]{},c[L1][L2]{},d[L2]{},e[L2]{},f=0;};
struct Dataset{vector<Row>samples;array<double,INPUTS>mu{},sd{};array<Weights,VERS>w{};};
static Dataset load(const fs::path&root){
 Dataset d;string line;
 {ifstream f(root/"examples/normalization.csv");ck(bool(f),"missing normalization.csv");getline(f,line);if(!line.empty()&&line.back()=='\r')line.pop_back();ck(line=="feature,mean,std","wrong normalization schema");int i=0;while(getline(f,line)){if(!line.empty()&&line.back()=='\r')line.pop_back();auto v=split(line);ck(v.size()==3&&i<INPUTS,"bad normalization row");d.mu[i]=parse(v[1]);d.sd[i]=parse(v[2]);ck(d.sd[i]>0,"nonpositive normalization spread");++i;}ck(i==INPUTS,"missing normalization values");}
 {ifstream f(root/"examples/frozen_network_weights.csv");ck(bool(f),"missing weights.csv");getline(f,line);if(!line.empty()&&line.back()=='\r')line.pop_back();ck(line=="version,layer,neuron,input,weight","wrong weights schema");int entries[VERS]={0,0};while(getline(f,line)){if(!line.empty()&&line.back()=='\r')line.pop_back();auto v=split(line);ck(v.size()==5,"bad weight row");int k=v[0]=="v1"?0:v[0]=="v2"?1:-1,layer=stoi(v[1]),j=stoi(v[2]),i=stoi(v[3]);ck(k>=0&&layer>=1&&layer<=3,"bad weight label");double val=parse(v[4]);Weights&w=d.w[k];if(layer==1){ck(j>=0&&j<L1&&i>=-1&&i<INPUTS,"L1 idx");if(i<0)w.b[j]=val;else w.a[i][j]=val;}else if(layer==2){ck(j>=0&&j<L2&&i>=-1&&i<L1,"L2 idx");if(i<0)w.d[j]=val;else w.c[i][j]=val;}else{ck(j==0&&i>=-1&&i<L2,"out idx");if(i<0)w.f=val;else w.e[i]=val;}entries[k]++;}ck(entries[0]==113&&entries[1]==113,"weight count mismatch");}
 {ifstream f(root/"examples/synthetic_bearing_features.csv");ck(bool(f),"missing synthetic inputs");getline(f,line);if(!line.empty()&&line.back()=='\r')line.pop_back();ck(line.rfind("split,virtual_bearing_id,operating_condition,synthetic_fault_label",0)==0,"bad feature header");while(getline(f,line)){if(!line.empty()&&line.back()=='\r')line.pop_back();auto v=split(line);ck(v.size()==12,"feature row needs 12 fields");Row r;r.split=v[0];r.bearing=stoi(v[1]);r.condition=stoi(v[2]);r.label=stoi(v[3]);ck(r.label==0||r.label==1,"bad synthetic label");for(int k=0;k<INPUTS;k++)r.raw[k]=parse(v[4+k]);d.samples.push_back(r);}ck(d.samples.size()==1536,"unexpected number of synthetic examples");}
 return d;
}
struct Graph{string id,ver,domain,expr,unit;PACEVAL_HANDLE h=nullptr;int nvars;string vars;};
class Engine {
 vector<Graph> graphs;
 size_t total_batch_calls=0,total_scalar_calls=0,total_outputs=0;
 void make(Graph&g){g.h=paceval_CreateComputation(g.expr.c_str(),(unsigned long)g.nvars,g.vars.c_str(),false,nullptr);if(!g.h||paceval_GetIsError(g.h)){char a[256]{},b[256]{};if(g.h)paceval_CreateErrorInformationText(g.h,a,b);throw runtime_error("paceval failed to create "+g.id+" ("+a+" / "+b+"): "+g.expr.substr(0,120));}}
public:
 Engine(){ck(paceval_InitializeLibrary(nullptr),"paceval_InitializeLibrary failed");}
 ~Engine(){for(auto&g:graphs)if(g.h)paceval_DeleteComputation(g.h);paceval_FreeLibrary();}
 int add(string id,string ver,string domain,string expr,string unit,int nv,string vars){Graph g{move(id),move(ver),move(domain),move(expr),move(unit),nullptr,nv,move(vars)};make(g);graphs.push_back(move(g));return (int)graphs.size()-1;}
 const Graph& graph(int i)const{return graphs.at(i);}
 const vector<Graph>& list()const{return graphs;}
 vector<double> batch(const vector<int>&ids,const vector<double>&rows,int nv){ck(!ids.empty()&&nv>0&&rows.size()%nv==0,"bad batch dimensions");size_t N=rows.size()/nv;vector<PACEVAL_HANDLE>h;for(int id:ids){const auto&g=graph(id);ck(g.nvars==nv&&g.vars==graph(ids[0]).vars,"mixed batch variable schema");h.push_back(g.h);}vector<double>copy=rows;vector<double>out(ids.size()*N,numeric_limits<double>::quiet_NaN());vector<int>err(out.size(),-1);bool has_error=paceval_dGetMultipleComputationsResultsExt(h.data(),(unsigned long)h.size(),copy.data(),(unsigned long)N,out.data(),nullptr,nullptr,err.data());ck(!has_error,"paceval multi-result batch failed");for(size_t j=0;j<out.size();j++)ck(err[j]==0&&isfinite(out[j]),"paceval invalid output at index "+to_string(j)+" code "+to_string(err[j]));total_batch_calls++;total_outputs+=out.size();return out;}
 double scalar(int id,const vector<double>&vars){auto g=graph(id);ck((int)vars.size()==g.nvars,"wrong scalar size");auto copy=vars;double out=paceval_dGetComputationResult(g.h,copy.data(),nullptr,nullptr);ck(!paceval_GetIsError(g.h)&&isfinite(out),"paceval scalar failed "+g.id);total_scalar_calls++;total_outputs++;return out;}
 size_t batches()const{return total_batch_calls;}size_t scalars()const{return total_scalar_calls;}size_t outputs()const{return total_outputs;}
};
static double nn_native(const Weights&w,const array<double,8>&x){double a[8],b[4];for(int j=0;j<8;j++){double z=w.b[j];for(int i=0;i<8;i++)z+=w.a[i][j]*x[i];a[j]=sigmoid(z);}for(int j=0;j<4;j++){double z=w.d[j];for(int i=0;i<8;i++)z+=w.c[i][j]*a[i];b[j]=sigmoid(z);}double z=w.f;for(int i=0;i<4;i++)z+=w.e[i]*b[i];return sigmoid(z);}
static string affine(const vector<string>&prior,const vector<double>&v,double bias){vector<string>terms={"("+ss(bias)+")"};for(size_t i=0;i<prior.size();i++)terms.push_back("("+ss(v[i])+"*"+prior[i]+")");return join_add(terms);}
struct Registry{vector<int>norm;array<vector<int>,VERS>l1,l2;array<int,VERS>out,fused;array<vector<int>,VERS>post;vector<string>postids;size_t flattened_chars=0;};
static Registry setup(Engine&e,const Dataset&d){Registry r;
 vector<string>fvars,xvars,hvars,bvars;
 for(int k=0;k<8;k++){fvars.push_back("f"+to_string(k));xvars.push_back("x"+to_string(k));hvars.push_back("h"+to_string(k));}for(int k=0;k<4;k++)bvars.push_back("b"+to_string(k));
 auto spaced=[](vector<string>a){string s;for(auto&x:a){if(!s.empty())s+=" ";s+=x;}return s;};
 for(int i=0;i<8;i++){string ex="((f"+to_string(i)+"-"+ss(d.mu[i])+")/"+ss(d.sd[i])+")";r.norm.push_back(e.add("normalize_feature_"+to_string(i),"shared","preprocessing",ex,"dimensionless",8,spaced(fvars)));}
 for(int ver=0;ver<2;ver++){
  auto&w=d.w[ver];string v="v"+to_string(ver+1);
  vector<string>layer1,layer2;
  for(int j=0;j<8;j++){vector<double>weights;for(int i=0;i<8;i++)weights.push_back(w.a[i][j]);string ex=sig(affine(xvars,weights,w.b[j]));r.l1[ver].push_back(e.add("mlp_"+v+"_layer1_n"+to_string(j),v,"neural",ex,"activation",8,spaced(xvars)));layer1.push_back(ex);}
  for(int j=0;j<4;j++){vector<double>weights;for(int i=0;i<8;i++)weights.push_back(w.c[i][j]);string ex=sig(affine(hvars,weights,w.d[j]));r.l2[ver].push_back(e.add("mlp_"+v+"_layer2_n"+to_string(j),v,"neural",ex,"activation",8,spaced(hvars)));layer2.push_back(ex);}
  vector<double>weights(w.e,w.e+4);string ex=sig(affine(bvars,weights,w.f));r.out[ver]=e.add("mlp_"+v+"_output",v,"neural",ex,"uncalibrated_score",4,spaced(bvars));
  // Independent automatic algebraic export: recursive composition of frozen weight matrices.
  vector<string>fusion1,fusion2;
  for(int j=0;j<8;j++){vector<double>a;for(int i=0;i<8;i++)a.push_back(w.a[i][j]);fusion1.push_back(sig(affine(xvars,a,w.b[j])));}
  for(int j=0;j<4;j++){vector<double>a;for(int i=0;i<8;i++)a.push_back(w.c[i][j]);fusion2.push_back(sig(affine(fusion1,a,w.d[j])));}
  string full=sig(affine(fusion2,weights,w.f));r.flattened_chars+=full.size();r.fused[ver]=e.add("mlp_"+v+"_flattened_output",v,"fused_neural",full,"uncalibrated_score",8,spaced(xvars));
 }
 // Operational score formulas. This is a rule layer, NOT a learned probability calibration.
 r.postids={"decision_margin","absolute_margin","review_band_margin","operating_correction","advisory_index","normalized_shift_distance","anomaly_energy","inspection_priority","sensitivity_to_score","sensitivity_to_speed","sensitivity_to_temperature","score_revision_delta"};
 const string pv="score threshold review_width x0 x1 x2 x3 x4 x5 x6 x7 peer_score";
 for(int ver=0;ver<2;ver++){
 string v="v"+to_string(ver+1);
 // Explicit formula revision with identical mathematical structure, version-specific documented coefficient.
 string a=ver==0?"0.08":"0.11",b=ver==0?"0.035":"0.025";
 vector<string>terms={"(score-0.5)","("+a+"*x0)","(-"+b+"*x7)","(0.02*x6)"};
 string correction=join_add(terms);
 vector<pair<string,string>> forms={
  {"decision_margin","(score-threshold)"},
  {"absolute_margin","sqrt((score-threshold)^2)"},
  {"review_band_margin","(sqrt((score-threshold)^2)-review_width)"},
  {"operating_correction",correction},
  {"advisory_index",sig("(3*"+correction+")")},
  {"normalized_shift_distance","sqrt((x0^2+x1^2+x2^2+x3^2+x4^2+x5^2+x6^2+x7^2)/8)"},
  {"anomaly_energy","((x0^2+x2^2+x3^2)/3)"},
  {"inspection_priority","(0.7*score+0.2*"+sig("(3*"+correction+")")+"+0.1*sqrt((score-threshold)^2))"},
  {"sensitivity_to_score","(3*"+sig("(3*"+correction+")")+"*(1-"+sig("(3*"+correction+")")+"))"},
  {"sensitivity_to_speed","(-3*"+b+"*"+sig("(3*"+correction+")")+"*(1-"+sig("(3*"+correction+")")+"))"},
  {"sensitivity_to_temperature","(0.06*"+sig("(3*"+correction+")")+"*(1-"+sig("(3*"+correction+")")+"))"},
  {"score_revision_delta","(score-peer_score)"}
 };
 for(auto &p:forms)r.post[ver].push_back(e.add(p.first+"_"+v,v,"decision_math",p.second,"unit_interval_or_normalized",12,pv));
 }
 return r;
}
struct Prediction{double p=0,flat=0,ref=0,advisory=0,priority=0,margin=0,review=0,shift=0,sensitivity=0;string action;};
static vector<Prediction> execute(Engine&e,const Dataset&data,const Registry&r,int version,int batch_size){
 const size_t N=data.samples.size();
 vector<array<double,8>> nx(N);vector<Prediction>pred(N);
 // Normalization is executed by genuine persistent paceval graphs in batches, not copied from native.
 for(size_t off=0;off<N;off+=batch_size){size_t n=min(size_t(batch_size),N-off);vector<double>raw;raw.reserve(n*8);for(size_t j=off;j<off+n;j++)for(double x:data.samples[j].raw)raw.push_back(x);auto z=e.batch(r.norm,raw,8);for(size_t j=0;j<n;j++)for(int f=0;f<8;f++)nx[off+j][f]=z[f*n+j];}
 // Independent native forward pass is used only for numerical correctness checks.
 for(size_t i=0;i<N;i++){
  array<double,8>x{};
  for(int j=0;j<8;j++)x[j]=(data.samples[i].raw[j]-data.mu[j])/data.sd[j];
  pred[i].ref=nn_native(data.w[version],x);
 }
 // Layer-wise export: use exactly the intermediate variable strategy described in the source paper.
 for(size_t off=0;off<N;off+=batch_size){size_t n=min(size_t(batch_size),N-off);vector<double>x;for(size_t j=off;j<off+n;j++)x.insert(x.end(),nx[j].begin(),nx[j].end());
  auto h=e.batch(r.l1[version],x,8);vector<double>a(n*8);for(size_t i=0;i<n;i++)for(int j=0;j<8;j++)a[i*8+j]=h[j*n+i];auto b=e.batch(r.l2[version],a,8);vector<double>c(n*4);for(size_t i=0;i<n;i++)for(int j=0;j<4;j++)c[i*4+j]=b[j*n+i];auto v=e.batch({r.out[version]},c,4);
  for(size_t j=0;j<n;j++){pred[off+j].p=v[j];ck(abs(v[j]-pred[off+j].ref)<2e-11,"native vs paceval MLP mismatch at "+to_string(off+j));}
  auto flattened=e.batch({r.fused[version]},x,8);for(size_t j=0;j<n;j++){pred[off+j].flat=flattened[j];ck(abs(flattened[j]-pred[off+j].p)<2e-11,"flattened vs layerwise mismatch at "+to_string(off+j));}
  vector<double>posts;posts.reserve(n*12);for(size_t j=0;j<n;j++){auto&nrm=nx[off+j];posts.push_back(pred[off+j].p);posts.push_back(.5);posts.push_back(.08);for(double y:nrm)posts.push_back(y);posts.push_back(pred[off+j].flat);}
  auto post=e.batch(r.post[version],posts,12);
  for(size_t j=0;j<n;j++){auto &p=pred[off+j];p.margin=post[0*n+j];p.review=post[2*n+j];p.advisory=post[4*n+j];p.shift=post[5*n+j];p.priority=post[7*n+j];p.sensitivity=post[8*n+j];p.action=(p.review<0?"REVIEW":p.margin>=0?"ADVISE_INSPECTION":"MONITOR");ck(isfinite(p.advisory)&&p.advisory>=0&&p.advisory<=1,"bad advisory index");}
 }
 return pred;
}
static void save_results(const fs::path&root,const Dataset&d,Engine&e,const Registry&r,int batch_size){
 fs::create_directories(root/"results");
 {ofstream o(root/"results/graph_registry.csv");o<<"id,version,domain,unit,expression\n";for(auto&g:e.list())o<<g.id<<","<<g.ver<<","<<g.domain<<","<<g.unit<<",\""<<g.expr<<"\"\n";}
 {ofstream o(root/"results/math_execution_inventory.csv");o<<"quantity,execution_owner,paceval_graph_id,api_path,independent_reference,status\n";for(auto&g:e.list())o<<g.domain<<",paceval,"<<g.id<<",dGetMultipleComputationsResultsExt,high_precision_or_native,executed\n";
  o<<"training_and_Adam_updates,Python_orchestration,,numpy_reference,not_applicable,executed_offline\n";
  o<<"input_CSV_decoding,C++_host,,std_library,CSV_parsing,executed\n";
  o<<"discrete_alert_selection,C++_host,,comparison_controller,decision_rules,executed\n";}
 array<vector<Prediction>,2>pr;
 for(int v=0;v<2;v++)pr[v]=execute(e,d,r,v,batch_size);
 {ofstream o(root/"results/inference_results.csv");o<<"split,virtual_bearing_id,operating_condition,synthetic_fault_label,model_version,paceval_layered_score,paceval_flattened_score,native_cpp_score,decision_margin,review_band_margin,advisory_index,normalized_shift_distance,inspection_priority,sensitivity_to_score,advisory_action\n";for(int ver=0;ver<2;ver++)for(size_t i=0;i<d.samples.size();i++){auto&x=d.samples[i];auto&p=pr[ver][i];o<<x.split<<","<<x.bearing<<","<<x.condition<<","<<x.label<<",v"<<ver+1<<","<<setprecision(17)<<p.p<<","<<p.flat<<","<<p.ref<<","<<p.margin<<","<<p.review<<","<<p.advisory<<","<<p.shift<<","<<p.priority<<","<<p.sensitivity<<","<<p.action<<"\n";}}
 {ofstream o(root/"results/split_metrics.csv");o<<"version,split,sample_count,accuracy,precision,recall,negative_false_alarm_rate,review_fraction,mean_score,mean_shift_distance\n";for(int ver=0;ver<2;ver++)for(string sp:{"train","validation","test","shift_test"}){int n=0,tp=0,fp=0,tn=0,fn=0,review=0;double sum=0,shift=0;for(size_t i=0;i<d.samples.size();i++)if(d.samples[i].split==sp){n++;auto&p=pr[ver][i];int prediction=p.p>=.5;if(prediction&&d.samples[i].label)tp++;if(prediction&&!d.samples[i].label)fp++;if(!prediction&&!d.samples[i].label)tn++;if(!prediction&&d.samples[i].label)fn++;if(p.action=="REVIEW")review++;sum+=p.p;shift+=p.shift;}ck(n>0,"empty split");o<<"v"<<ver+1<<","<<sp<<","<<n<<","<<setprecision(12)<<double(tp+tn)/n<<","<<double(tp)/(tp+fp?tp+fp:1)<<","<<double(tp)/(tp+fn?tp+fn:1)<<","<<double(fp)/(fp+tn?fp+tn:1)<<","<<double(review)/n<<","<<sum/n<<","<<shift/n<<"\n";}}
 {ofstream o(root/"results/model_revision.csv");o<<"row_index,split,score_v1,score_v2,delta_v2_minus_v1,action_v1,action_v2,action_changed\n";for(size_t i=0;i<d.samples.size();i++)o<<i<<","<<d.samples[i].split<<","<<setprecision(17)<<pr[0][i].p<<","<<pr[1][i].p<<","<<pr[1][i].p-pr[0][i].p<<","<<pr[0][i].action<<","<<pr[1][i].action<<","<<(pr[0][i].action!=pr[1][i].action)<<"\n";}
 // 3-D plot input is generated using actual paceval expressions, not interpolated or re-computed externally.
 {ofstream o(root/"results/threshold_surface.csv");o<<"model_version,score,threshold,decision_margin,review_band_margin,advisory_index\n";for(int v=0;v<2;v++){vector<double>rows;for(int s=0;s<=40;s++)for(int t=0;t<=40;t++){double score=.01+.98*s/40.0,threshold=.2+.6*t/40.0;rows.insert(rows.end(),{score,threshold,.08,0,0,0,0,0,0,0,0,score});}auto a=e.batch({r.post[v][0],r.post[v][2],r.post[v][4]},rows,12);int n=41*41;for(int s=0;s<=40;s++)for(int t=0;t<=40;t++){int i=s*41+t;o<<"v"<<v+1<<","<<setprecision(12)<<rows[i*12]<<","<<rows[i*12+1]<<","<<a[i]<<","<<a[n+i]<<","<<a[2*n+i]<<"\n";}}}
 // Dynamic rule response surface, evaluated by the real paceval graph (not a plotted surrogate).
 {ofstream o(root/"results/advisory_surface.csv");o<<"model_version,normalized_vibration,normalized_speed,advisory_index\n";
 for(int v=0;v<2;v++){vector<double>rows;for(int a=0;a<=40;a++)for(int b=0;b<=40;b++){
  double vib=-2+4*a/40.0,speed=-2+4*b/40.0;
  rows.insert(rows.end(),{0.5,0.5,0.08,vib,0,0,0,0,0,0,speed,0.5});}
 auto got=e.batch({r.post[v][4]},rows,12);
 for(size_t i=0;i<got.size();i++)o<<"v"<<(v+1)<<","<<setprecision(12)<<rows[i*12+3]<<","<<rows[i*12+10]<<","<<got[i]<<"\n";}}
 // Scalar API probe proving persistent scalar handles as well as multi-calculation batch.
 vector<double>raw(d.samples[0].raw.begin(),d.samples[0].raw.end());double scalar=e.scalar(r.norm[0],raw);ck(abs(scalar-(d.samples[0].raw[0]-d.mu[0])/d.sd[0])<1e-12,"scalar normalization test failed");
 {ofstream o(root/"results/sdk_run_summary.json");o<<"{\n  \"graph_count\": "<<e.list().size()<<",\n  \"samples\": "<<d.samples.size()<<",\n  \"model_versions\": 2,\n  \"batch_calls\": "<<e.batches()<<",\n  \"scalar_calls\": "<<e.scalars()<<",\n  \"graph_outputs\": "<<e.outputs()<<",\n  \"flattened_formula_characters_total\": "<<r.flattened_chars<<",\n  \"real_paceval_sdk\": true,\n  \"source_dataset\": \"synthetic only\"\n}\n";}
 cout<<"PASS. paceval graphs="<<e.list().size()<<" samples="<<d.samples.size()<<" outputs="<<e.outputs()<<" batches="<<e.batches()<<"\n";
}
int main(int argc,char**argv){try{fs::path root=argc>1?argv[1]:".";int batch_size=argc>2?stoi(argv[2]):128;ck(batch_size>=1&&batch_size<=1024,"invalid batch size");auto d=load(root);Engine e;auto reg=setup(e,d);save_results(root,d,e,reg,batch_size);return 0;}catch(exception&x){cerr<<"ERROR: "<<x.what()<<"\n";return 1;}}
