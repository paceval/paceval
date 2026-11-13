// Industrial Mathematical Models via paceval MCP: local SDK reproduction path.
// The remote MCP tests are independently recorded under results/live_mcp_*.json.
// Mathematical output comes from original paceval graph handles, not a C++ emulator.
#include "paceval_main.h"
#include <algorithm>
#include <array>
#include <cmath>
#include <filesystem>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <limits>
#include <map>
#include <sstream>
#include <stdexcept>
#include <string>
#include <vector>
using namespace std; namespace fs=std::filesystem;
static void require(bool c, const string& msg){if(!c) throw runtime_error(msg);}
static string read_text(const fs::path& p){ifstream f(p); require(bool(f),"Cannot read: "+p.string());string s((istreambuf_iterator<char>(f)),istreambuf_iterator<char>());while(!s.empty()&&(s.back()=='\r'||s.back()=='\n'))s.pop_back();return s;}
static vector<string> split(const string& s){stringstream ss(s); string t;vector<string> v;while(getline(ss,t,','))v.push_back(t);return v;}
static double finite(const string& t){size_t pos;double x=stod(t,&pos);require(pos==t.size()&&isfinite(x),"Invalid finite scalar: "+t);return x;}
struct Sample{string id, scenario;double x,y,z,T,target,tol,raw;};
static vector<Sample> load(const fs::path& p){ifstream f(p);require(bool(f),"Missing sample CSV");string line;getline(f,line);if(!line.empty()&&line.back()=='\r')line.pop_back();require(line=="case_id,x,y,z,temp,target,tol,raw,scenario","Unexpected dataset schema");vector<Sample>a;while(getline(f,line)){if(!line.empty()&&line.back()=='\r')line.pop_back();if(line.empty())continue;auto c=split(line);require(c.size()==9,"Invalid row width");Sample s{c[0],c[8],finite(c[1]),finite(c[2]),finite(c[3]),finite(c[4]),finite(c[5]),finite(c[6]),finite(c[7])};require(s.x>=0&&s.x<=1&&s.y>=0&&s.y<=1&&s.z>=0&&s.z<=1&&s.T>=0&&s.T<=50&&s.tol>0,"Out-of-domain input");a.push_back(s);}require(a.size()>100,"Dataset too small");return a;}
struct Graph{string id, owner, variables, file;int nvars;PACEVAL_HANDLE h=nullptr;};
class Paceval{
 vector<Graph> gs;long long outputs_=0,batches_=0;
public:
 Paceval(){require(paceval_InitializeLibrary(nullptr),"paceval_InitializeLibrary failed");}
 ~Paceval(){for(auto&g:gs)if(g.h)paceval_DeleteComputation(g.h);paceval_FreeLibrary();}
 int add(const fs::path&root,const string&id,const string&filename,const string&vars,int nvars){Graph g{id,"paceval",vars,filename,nvars,nullptr};string expr=read_text(root/"generated"/filename);g.h=paceval_CreateComputation(expr.c_str(),(unsigned long)nvars,vars.c_str(),false,nullptr);if(!g.h || paceval_GetIsError(g.h)){char t[256]={},u[256]={};if(g.h)paceval_CreateErrorInformationText(g.h,t,u);throw runtime_error("paceval failed to create "+id+" :"+t+" :"+u);}gs.push_back(move(g));return (int)gs.size()-1;}
 vector<double> multi(const vector<int>& idx,const vector<double>&packed,size_t n,const string&vars,int nvars){require(!idx.empty()&&packed.size()==n*size_t(nvars),"Wrong API batch layout");vector<PACEVAL_HANDLE> handles;for(int i:idx){require(gs.at(i).nvars==nvars&&gs.at(i).variables==vars,"Inconsistent graph variable order");handles.push_back(gs[i].h);}vector<double> inputs=packed,outs(idx.size()*n,numeric_limits<double>::quiet_NaN());vector<int> errors(idx.size()*n,-1);bool failed=paceval_dGetMultipleComputationsResultsExt(handles.data(),(unsigned long)handles.size(),inputs.data(),(unsigned long)n,outs.data(),nullptr,nullptr,errors.data());require(!failed,"Multi-computation API failure");for(size_t i=0;i<outs.size();i++)require(errors[i]==0&&isfinite(outs[i]),"Unsuccessful/nonfinite result: "+to_string(i));outputs_+=(long long)outs.size();batches_++;return outs;}
 const vector<Graph>& graphs()const{return gs;}long long outputs()const{return outputs_;}long long batches()const{return batches_;}
};
static double indexed(const vector<double>&outs,size_t n,size_t graph,size_t row){return outs.at(graph*n+row);} // graph-major verified on the remote service and locally
int main(int argc,char**argv){try{
 require(argc>=2,"Usage: industrial_mcp_paceval PROJECT_ROOT [--verify-only]");fs::path root=argv[1];bool check_only=argc>2&&string(argv[2])=="--verify-only";auto samples=load(root/"examples/synthetic_machine_cases.csv");Paceval engine;
 const string core="x y z temp",down="v1 v2 x y z temp target tol raw";
 vector<int> primary;for(string v:{"v1","v2"})for(string item:{"field","temp_sensitivity","x_sensitivity"})primary.push_back(engine.add(root,item+"_"+v,item+"_"+v+".txt",core,4));
 vector<int> modules;for(int i=1;i<=8;i++){ostringstream os;os<<"modular_block_"<<setfill('0')<<setw(2)<<i<<"_v2.txt";modules.push_back(engine.add(root,"rbf_module_"+to_string(i),os.str(),core,4));}
 const vector<string> down_names={"revision_delta","target_residual","quality_score","quality_margin","version_margin","governance_score","temperature_guard","corrected_measurement"};vector<int> downstream;for(auto& name:down_names)downstream.push_back(engine.add(root,name,name+".txt",down,9));
 struct R{Sample s;array<double,6>p{};array<double,8>q{};double modular=0;string decision;};vector<R> records;records.reserve(samples.size());for(auto&s:samples)records.push_back({s,{}, {},0.0,""});
 const int BATCH=64;double maximum_modular_gap=0;
 for(size_t offset=0;offset<records.size();offset+=BATCH){size_t n=min(size_t(BATCH),records.size()-offset);vector<double> input;input.reserve(4*n);for(size_t j=0;j<n;j++){auto&s=records[offset+j].s;input.insert(input.end(),{s.x,s.y,s.z,s.T});}
 auto main=engine.multi(primary,input,n,core,4);auto blocks=engine.multi(modules,input,n,core,4);
 vector<double> downinput;downinput.reserve(9*n);
 for(size_t j=0;j<n;j++){auto& rec=records[offset+j];for(size_t k=0;k<6;k++)rec.p[k]=indexed(main,n,k,j);double sum=0;for(size_t k=0;k<8;k++)sum+=indexed(blocks,n,k,j);rec.modular=sum;maximum_modular_gap=max(maximum_modular_gap,abs(sum-rec.p[3]));require(abs(sum-rec.p[3])<2e-11,"Monolithic/modular execution mismatch");auto&s=rec.s;downinput.insert(downinput.end(),{rec.p[0],rec.p[3],s.x,s.y,s.z,s.T,s.target,s.tol,s.raw});}
 auto post=engine.multi(downstream,downinput,n,down,9);
 for(size_t j=0;j<n;j++){auto&rec=records[offset+j];for(size_t k=0;k<8;k++)rec.q[k]=indexed(post,n,k,j);
 auto &q=rec.q;require(abs(q[0]-(rec.p[3]-rec.p[0]))<1e-11,"Version-delta graph inconsistent");require(abs(q[1]-(rec.p[3]-rec.s.target))<1e-11,"Target residual inconsistent");require(abs(q[2]+q[3]-1)<1e-11,"Quality score/margin inconsistent");rec.decision=(q[3]>=0&&q[4]>=0&&q[6]>=0)?"ACCEPT":(q[3]>=-0.60&&q[6]>=0?"REVIEW":"REJECT");}
 }
 if(!check_only){fs::create_directories(root/"results");ofstream f(root/"results/local_sdk_results.csv");f<<"case_id,scenario,x,y,z,temp,target,tolerance,raw,correction_v1,temperature_sensitivity_v1,x_sensitivity_v1,correction_v2,temperature_sensitivity_v2,x_sensitivity_v2,modular_v2,version_delta,target_residual,quality_score,quality_margin,version_margin,governance_score,temperature_guard,corrected_measurement,decision\n";
 for(auto&r:records){auto&s=r.s;f<<s.id<<","<<s.scenario<<","<<setprecision(17)<<s.x<<","<<s.y<<","<<s.z<<","<<s.T<<","<<s.target<<","<<s.tol<<","<<s.raw;for(double v:r.p)f<<","<<v;f<<","<<r.modular;for(double v:r.q)f<<","<<v;f<<","<<r.decision<<"\n";}
 ofstream o(root/"results/math_execution_inventory.csv");o<<"function_id,execution_owner,graph_or_host_role,input_schema,provenance\n";for(auto&g:engine.graphs())o<<g.id<<",paceval,real_persistent_graph,\""<<g.variables<<"\","<<g.file<<"\n";o<<"decision_selection,C++ host,interpret_policy_margins,graph_outputs,source_code\n";o<<"validation,C++ host,check_domains_and_batch_shapes,CSV_fields,source_code\n";
 ofstream js(root/"results/local_sdk_summary.json");int ac=0,rv=0,rj=0;for(auto&r:records){ac+=r.decision=="ACCEPT";rv+=r.decision=="REVIEW";rj+=r.decision=="REJECT";}js<<"{\n  \"original_sdk\": \"paceval 4.25\",\n  \"source\": \"synthetic only\",\n  \"graph_count\": "<<engine.graphs().size()<<",\n  \"model_versions\": 2,\n  \"data_records\": "<<records.size()<<",\n  \"batch_calls\": "<<engine.batches()<<",\n  \"computed_graph_outputs\": "<<engine.outputs()<<",\n  \"model_accept\": "<<ac<<",\n  \"model_review\": "<<rv<<",\n  \"model_reject\": "<<rj<<",\n  \"max_modular_gap\": "<<setprecision(17)<<maximum_modular_gap<<",\n  \"tinc_certification\": false,\n  \"performance_comparison\": false\n}\n";
 }
 cout<<"PASS real original paceval graphs="<<engine.graphs().size()<<" input_records="<<records.size()<<" graph_outputs="<<engine.outputs()<<" decisions="<<records.size()<<" modular_max_gap="<<setprecision(3)<<maximum_modular_gap<<"\n";
 return 0;
 }catch(exception&e){cerr<<"ERROR: "<<e.what()<<"\n";return 1;}
}
