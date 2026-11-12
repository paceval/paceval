// WP-012 — Auditable Multi-Step AI Computation Chains.
// Direct integration: paceval_main.h in this application, paceval_main.cpp in CMake.
// The externally supplied paceval Linux .so performs EVERY expression evaluation.
// The C++ host alone handles schema and domain checks, immutable formula catalog,
// dependency ordering, numerical reference checks, and hash-linked audit records.
//
// Security model: caller selects a fixed formula ID/version, NEVER free-form code.
// JSONL adapter is a local prototype, not an MCP server or LLM implementation.
// Hash chaining detects edits relative to a separately retained trusted head,
// but does not authenticate the host or make a mutable file tamper-proof.
#include "paceval_main.h"
#include <openssl/sha.h>
#include <array>
#include <algorithm>
#include <cmath>
#include <cstddef>
#include <cctype>
#include <filesystem>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <limits>
#include <set>
#include <sstream>
#include <stdexcept>
#include <string>
#include <utility>
#include <vector>
namespace fs = std::filesystem;
namespace {
constexpr size_t NV = 5;
constexpr const char *VARLIST = "x a t1 t2 t3";
constexpr const char *FORMULA_ID = "CHAIN_LOGRATIO";
constexpr const char *GENESIS = "0000000000000000000000000000000000000000000000000000000000000000";
using Inputs = std::array<double,NV>;
struct Definition {const char *node, *version, *expr;};
// Immutable expressions: version 1.1 changes the FINAL node only. Shared
// intermediate nodes keep the same formula identities and their graph handles.
constexpr std::array<Definition,5> DEFINITIONS = {{{"SQUARE","1.0","x*x"},
 {"LOG1P","1.0","ln(1+t1)"}, {"DENOM","1.0","1+a*x"},
 {"RATIO","1.0","t2/t3"}, {"RATIO","1.1","t2/t3+(0.05*x)"}}};
std::string format(double x){std::ostringstream s;s<<std::setprecision(17)<<x;return s.str();}
void require(bool b,const std::string &s){if(!b)throw std::runtime_error(s);}
std::string digest(const std::string &s){unsigned char out[SHA256_DIGEST_LENGTH];
 SHA256(reinterpret_cast<const unsigned char*>(s.data()),s.size(),out);
 const char*d="0123456789abcdef";std::string h;h.reserve(64);
 for(auto b:out){h.push_back(d[b>>4]);h.push_back(d[b&15]);}return h;}
std::vector<std::string> split(const std::string&s,char c){std::vector<std::string>r;size_t a=0;
 while(a<=s.size()){auto b=s.find(c,a);if(b==std::string::npos)b=s.size();r.push_back(s.substr(a,b-a));
 if(b==s.size()) break;
 a=b+1;}return r;}
std::string parse_id(const std::string &s){require(!s.empty()&&s.size()<=48,"invalid_request_id");
 for(unsigned char c:s) require(std::isalnum(c)||c=='_'||c=='-',"invalid_request_id");
 return s;}
double parse_num(const std::string&s){require(!s.empty()&&s.size()<=45,"invalid_number");
 size_t end=0;double d=0;try{d=std::stod(s,&end);}catch(...){throw std::runtime_error("invalid_number");}
 require(end==s.size()&&std::isfinite(d),"invalid_number");return d;}
struct Request {std::string id, formula, version, unit;double x=0,a=0;};
Request parse(const std::string &line,char delim){require(line.size()<=2048,"request_too_long");
 auto f=split(line,delim);require(f.size()==6,"invalid_field_count");
 Request r;r.id=parse_id(f[0]);r.formula=f[1];r.version=f[2];r.x=parse_num(f[3]);r.a=parse_num(f[4]);r.unit=f[5];return r;}
void validate(const Request&r){require(r.formula==FORMULA_ID,"unknown_formula_id");
 require(r.version=="1.0"||r.version=="1.1","unknown_formula_version");
 require(r.unit=="dimensionless","ambiguous_or_incompatible_unit");
 require(std::abs(r.x)<=4.0,"x_out_of_domain");
 require(std::abs(r.a)<=2.0,"a_out_of_domain");
 require(std::abs(1.0+r.a*r.x)>=0.05,"near_zero_denominator");}
struct Reference {double t1=0,t2=0,t3=0,z=0;};
Reference native(const Request &r){Reference a;a.t1=r.x*r.x;a.t2=std::log1p(a.t1);
 a.t3=1+r.a*r.x;a.z=a.t2/a.t3+(r.version=="1.1"?0.05*r.x:0);return a;}
struct Engine {Engine(){require(paceval_InitializeLibrary(nullptr),"paceval_initialization_failed");}
 ~Engine(){paceval_FreeLibrary();}Engine(const Engine&)=delete;Engine&operator=(const Engine&)=delete;};
struct Graph {PACEVAL_HANDLE h=nullptr;Graph()=default;
 explicit Graph(PACEVAL_HANDLE p):h(p){}~Graph(){if(h)paceval_DeleteComputation(h);}
 Graph(const Graph&)=delete;Graph&operator=(const Graph&)=delete;
 Graph(Graph&&o)noexcept:h(o.h){o.h=nullptr;}
 Graph&operator=(Graph&&o)noexcept{if(this!=&o){if(h)paceval_DeleteComputation(h);h=o.h;o.h=nullptr;}return *this;}};
struct Runtime {
 Engine engine;std::vector<Graph> graphs;
 Runtime(){graphs.reserve(DEFINITIONS.size());for(const auto &d:DEFINITIONS){
   Graph g(paceval_CreateComputation(d.expr,NV,VARLIST,false,nullptr));
   require(g.h&&!paceval_GetIsError(g.h),std::string("graph_creation_failed:")+d.node);
   graphs.push_back(std::move(g));}}
 // Stage-vector evaluation: these are actual paceval batch API calls, not an
 // independent C++ evaluation camouflaged as paceval execution.
 std::vector<double> eval(int graph,const std::vector<Inputs> &samples,size_t batch){
   require(batch>0&&batch<=4096,"invalid_batch_size");std::vector<double> ys(samples.size());
   std::vector<double> in(batch*NV),out(batch);std::vector<int> errors(batch);
   for(size_t off=0;off<samples.size();off+=batch){size_t n=std::min(batch,samples.size()-off);
      for(size_t i=0;i<n;++i)for(size_t k=0;k<NV;++k)in[NV*i+k]=samples[off+i][k];
      // paceval returns TRUE on a batch error (counterintuitive but documented).
      bool failed=paceval_dGetComputationResultExt(graphs[size_t(graph)].h,in.data(),
        static_cast<unsigned long>(n),out.data(),nullptr,nullptr,errors.data());
      require(!failed,"paceval_batch_failure");
      for(size_t i=0;i<n;++i){require(errors[i]==0&&std::isfinite(out[i]),"paceval_value_invalid");ys[off+i]=out[i];}}
   return ys;
 }
};
struct Computed {Request q;std::array<double,4> steps{};};
std::vector<Computed> execute(Runtime &rt,const std::vector<Request>&req,size_t batch){
 std::vector<Computed> r; r.reserve(req.size());for(const auto&q:req){validate(q);r.push_back({q,{}});}
 std::vector<Inputs> in(r.size());for(size_t i=0;i<r.size();++i){in[i][0]=r[i].q.x;in[i][1]=r[i].q.a;}
 auto s1=rt.eval(0,in,batch);for(size_t i=0;i<r.size();++i){r[i].steps[0]=s1[i];in[i][2]=s1[i];}
 auto s2=rt.eval(1,in,batch);for(size_t i=0;i<r.size();++i){r[i].steps[1]=s2[i];in[i][3]=s2[i];}
 auto s3=rt.eval(2,in,batch);for(size_t i=0;i<r.size();++i){r[i].steps[2]=s3[i];in[i][4]=s3[i];}
 for(int version=0;version<2;++version){std::vector<Inputs> subset;std::vector<size_t> idx;
  for(size_t i=0;i<r.size();++i)if(r[i].q.version==(version?"1.1":"1.0")){idx.push_back(i);subset.push_back(in[i]);}
  auto last=rt.eval(3+version,subset,batch);
  for(size_t j=0;j<idx.size();++j)r[idx[j]].steps[3]=last[j];}
 for(const auto &c:r){const Reference n=native(c.q);std::array<double,4> ns={n.t1,n.t2,n.t3,n.z};
  for(size_t k=0;k<4;++k)require(std::abs(c.steps[k]-ns[k])<=1e-11*(1+std::abs(ns[k])),"native_reference_mismatch");}
 return r;
}
std::string csv_header(){return "request_id,formula_id,version,x,a,unit";}
std::string line(const Request&q,char delim){return q.id+delim+q.formula+delim+q.version+delim+format(q.x)+delim+format(q.a)+delim+q.unit;}
Request base(size_t i){Request r;r.id="TASK_"+std::to_string(1000+i);r.formula=FORMULA_ID;
 r.version=i%4==0?"1.1":"1.0";r.x=-3.85+7.7*double(i%100)/99.0;
 r.a=0.07+0.012*double(i%9);r.unit="dimensionless";return r;}
std::vector<std::string> default_cases(){std::vector<std::string> all;
 for(size_t i=0;i<100;++i)all.push_back(line(base(i),','));
 // A second batch of requests with NEW request IDs and repeated mathematics.
 for(size_t i=0;i<10;++i){Request q=base(10+i);q.id="REPLAY_"+std::to_string(i);all.push_back(line(q,','));}
 // Deliberately malformed/unsafe data, including a duplicate identifier.
 for(size_t i=0;i<20;++i){Request q=base(i);q.id="INVALID_"+std::to_string(i);switch(i%10){
 case 0:q.formula="UNTRUSTED_FORMULA";break;case 1:q.version="9.9";break;
 case 2:q.unit="meters";break;case 3:q.x=9;break;case 4:q.a=-5;break;
 case 5:q.x=2;q.a=-0.5;break;case 6:q.id="TASK_1000";break;
 case 7:all.push_back("INVALID_MISSING,CHAIN_LOGRATIO,1.0,0.5,,dimensionless");continue;
 case 8:all.push_back("INVALID_NAN,CHAIN_LOGRATIO,1.0,nan,0.2,dimensionless");continue;
 case 9:all.push_back("INVALID_FIELDS,CHAIN_LOGRATIO,1.0,0.5,0.2,dimensionless,EXTRA");continue;}
 all.push_back(line(q,','));}
 return all;}
std::vector<std::string> read_csv(const fs::path&f){std::ifstream in(f);require(in.good(),"cannot_open_request_csv");
 std::string s;require(bool(std::getline(in,s))&&s==csv_header(),"bad_request_csv_header");
 std::vector<std::string>r;while(std::getline(in,s)){require(s.size()<=2048,"oversized_csv_line");r.push_back(s);
 require(r.size()<=100000,"too_many_requests");}require(!r.empty(),"empty_requests");return r;}
struct Audit {
 std::ofstream f;std::string head=GENESIS;size_t count=0;
 explicit Audit(const fs::path&p):f(p){require(f.good(),"cannot_open_audit");
 f<<"sequence,request_id,kind,step,node_id,version,formula_hash,value,status,reason,previous_hash,record_hash\n";}
 void append(const std::string&id,const std::string&kind,int step,const std::string&node,
   const std::string&ver,const std::string&formula_hash,const std::string&value,
   const std::string&status,const std::string&reason){
   ++count;std::string data=std::to_string(count)+"|"+id+"|"+kind+"|"+std::to_string(step)+"|"+
     node+"|"+ver+"|"+formula_hash+"|"+value+"|"+status+"|"+reason;
   const std::string before=head;head=digest(head+"|"+data);
   f<<count<<','<<id<<','<<kind<<','<<step<<','<<node<<','<<ver<<','<<formula_hash<<','<<value
     <<','<<status<<','<<reason<<','<<before<<','<<head<<'\n';
 }
};
std::string schemahash(){return digest("request_id,formula_id,version,x,a,unit");}
void export_models(const fs::path&p){std::ofstream f(p);require(f.good(),"cannot_open_models");
 f<<"formula_id,node_id,version,expression,variables,sha256\n";
 for(const auto&d:DEFINITIONS){const std::string str=std::string(d.node)+"|"+d.version+"|"+d.expr+"|"+VARLIST;
 f<<FORMULA_ID<<','<<d.node<<','<<d.version<<','<<d.expr<<",\""<<VARLIST<<"\","<<digest(str)<<'\n';}}
std::string modelhash(int id){const auto&d=DEFINITIONS[size_t(id)];return digest(std::string(d.node)+"|"+d.version+"|"+d.expr+"|"+VARLIST);}
void write_tinc(const fs::path&path){
 // Optional sample-specific interval diagnostic: checked with independent
 // high precision; NOT asserted to be a universal enclosure certificate.
 Graph tmp(paceval_CreateComputation("ln(1+x*x)",NV,VARLIST,true,nullptr));
 require(tmp.h&&!paceval_GetIsError(tmp.h),"tinc_graph_creation_error");
 std::ofstream out(path);out<<"sample,x,a,value,low,high\n"<<std::setprecision(17);
 for(size_t i=0;i<24;++i){double x=-1.2+0.1*double(i);double input[NV]={x,0,0,0,0};double lo=0,hi=0;
 double v=paceval_dGetComputationResult(tmp.h,input,&lo,&hi);
 require(!paceval_GetIsError(tmp.h)&&std::isfinite(v)&&std::isfinite(lo)&&std::isfinite(hi)&&lo<=hi,"invalid_tinc");
 out<<i<<','<<x<<",0,"<<v<<','<<lo<<','<<hi<<'\n';}}
void summary(const fs::path&dir,const std::string&head,size_t n){std::ofstream f(dir/"audit_head.txt");
 require(f.good(),"cannot_write_head");f<<"SHA256-CHAIN-V1\n"<<n<<"\n"<<head<<"\n";}
void demo(Runtime&rt,const std::vector<std::string>&lines,size_t batch,const fs::path&dir){
 fs::create_directories(dir);export_models(dir/"models.csv");
 std::ofstream requests(dir/"requests.csv"),results(dir/"results.csv"),steps(dir/"steps.csv"),rejections(dir/"rejections.csv");
 require(requests.good()&&results.good()&&steps.good()&&rejections.good(),"cannot_open_result_file");
 requests<<csv_header()<<'\n';
 results<<"request_id,formula_id,version,status,reason,x,a,result,graph_reused\n";
 steps<<"request_id,version,step,node_id,formula_sha256,value,native_reference,abs_error\n";
 rejections<<"request_id,reason\n";
 for(auto&s:lines)requests<<s<<'\n';
 std::set<std::string>seen;std::vector<Request>accepted;std::vector<std::string>accepted_raw;
 std::vector<std::pair<std::string,std::string>> rejected;std::vector<std::string>rejected_raw;
 for(const auto&l:lines){try{Request q=parse(l,',');require(seen.insert(q.id).second,"duplicate_request_id");validate(q);
  accepted.push_back(q);accepted_raw.push_back(l);}catch(const std::exception&e){auto fields=split(l,',');std::string id=fields.empty()?"UNKNOWN":fields[0];
  if(id.empty())id="UNKNOWN";
  rejected.push_back({id,e.what()});rejected_raw.push_back(l);}}
 auto evaluated=execute(rt,accepted,batch);Audit audit(dir/"audit_steps.csv");size_t reused=0;std::set<std::string>used;
 for(size_t case_index=0;case_index<evaluated.size();++case_index){const auto &r=evaluated[case_index];
  audit.append(r.q.id,"INPUT",0,"REQUEST",r.q.version,schemahash(),digest(accepted_raw[case_index]),"OK","none");
  const auto ref=native(r.q);const std::array<double,4> a={ref.t1,ref.t2,ref.t3,ref.z};
  bool reuse=!used.insert(r.q.version).second;if(reuse)++reused;
  results<<r.q.id<<','<<r.q.formula<<','<<r.q.version<<",OK,none,"<<format(r.q.x)<<','<<format(r.q.a)<<','<<format(r.steps[3])<<','<<(reuse?"true":"false")<<'\n';
  for(size_t j=0;j<4;++j){int id=j==3?(r.q.version=="1.1"?4:3):int(j);
    const auto&d=DEFINITIONS[size_t(id)];const auto err=std::abs(r.steps[j]-a[j]);
    steps<<r.q.id<<','<<r.q.version<<','<<(j+1)<<','<<d.node<<','<<modelhash(id)<<','
      <<format(r.steps[j])<<','<<format(a[j])<<','<<format(err)<<'\n';
    audit.append(r.q.id,"STEP",int(j+1),d.node,d.version,modelhash(id),format(r.steps[j]),"OK","none");}
  audit.append(r.q.id,"RESULT",5,"FINAL",r.q.version,modelhash(r.q.version=="1.1"?4:3),format(r.steps[3]),"OK","none");
 }
 for(size_t bad_index=0;bad_index<rejected.size();++bad_index){const auto&bad=rejected[bad_index];results<<bad.first<<","<<FORMULA_ID<<",,REJECTED,"<<bad.second<<",,,,false\n";
  rejections<<bad.first<<','<<bad.second<<'\n';audit.append(bad.first,"REJECT",0,"NONE","NONE","NONE",digest(rejected_raw[bad_index]),"REJECTED",bad.second);}
 // A change from v1.0 to v1.1 changes only the final graph; both remain.
 std::ofstream versions(dir/"version_comparison.csv");versions<<"sample,x,a,version_1_0,version_1_1,expected_difference\n";
 for(size_t i=0;i<16;++i){Request q=base(i);q.version="1.0";auto l=execute(rt,{q},batch)[0];
 q.version="1.1";auto v=execute(rt,{q},batch)[0];
 versions<<i<<','<<format(q.x)<<','<<format(q.a)<<','<<format(l.steps[3])<<','<<format(v.steps[3])<<','<<format(0.05*q.x)<<'\n';}
 // Audit head retained separately to permit future external anchoring.
 summary(dir,audit.head,audit.count);write_tinc(dir/"tinc_samples.csv");
 std::cout<<"PASS accepted="<<accepted.size()<<" rejected="<<rejected.size()<<" graph_reused="<<reused
  <<" step_results="<<accepted.size()*4<<" audit_records="<<audit.count<<" audit_head="<<audit.head<<"\n";
}
void serve(Runtime&rt,const fs::path&dir){fs::create_directories(dir);export_models(dir/"models.csv");
 Audit audit(dir/"audit_steps.csv");std::set<std::string> ids,used;std::string request;
 while(std::getline(std::cin,request)){
  std::string rid="INVALID";auto fields=split(request,'|');if(!fields.empty()&&!fields[0].empty()) {
   try {rid=parse_id(fields[0]);}catch(...) {rid="INVALID";}}
  try{Request q=parse(request,'|');require(ids.insert(q.id).second,"duplicate_request_id");validate(q);
   auto computed=execute(rt,{q},1)[0];const bool reused=!used.insert(q.version).second;
   const std::string normalized=line(q,','); // placeholder
   audit.append(q.id,"INPUT",0,"REQUEST",q.version,schemahash(),digest(normalized),"OK","none");
   for(size_t j=0;j<4;++j){int id=j==3?(q.version=="1.1"?4:3):int(j);
    const auto&d=DEFINITIONS[size_t(id)];audit.append(q.id,"STEP",int(j+1),d.node,d.version,modelhash(id),format(computed.steps[j]),"OK","none");}
   audit.append(q.id,"RESULT",5,"FINAL",q.version,modelhash(q.version=="1.1"?4:3),format(computed.steps[3]),"OK","none");
   summary(dir,audit.head,audit.count);
   std::cout<<q.id<<"|OK|"<<format(computed.steps[3])<<'|'<<(reused?"true":"false")<<'|'<<audit.head<<'\n'<<std::flush;
  }catch(const std::exception&e){std::string safe=e.what();audit.append(rid,"REJECT",0,"NONE","NONE","NONE",digest(request),"REJECTED",safe);
   summary(dir,audit.head,audit.count);
   std::cout<<rid<<"|REJECTED|"<<safe<<"|"<<audit.head<<'\n'<<std::flush;}}
}
void selftest(){auto a=base(5);auto v=native(a);require(std::isfinite(v.z),"bad_native");
 Request bad=a;bad.a=-0.5;bad.x=2;try{validate(bad);throw std::runtime_error("domain_test_did_not_reject");}
 catch(const std::runtime_error&e){require(std::string(e.what())=="near_zero_denominator","domain_test_failed");}
 require(digest("abc")=="ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad","sha256_known_answer_failed");
 std::cout<<"PASS native math, SHA256 known answer and domain validator\n";}
}
int main(int argc,char**argv){try{std::string mode="--demo",input,out="results";size_t batch=37;
 for(int i=1;i<argc;++i){const std::string s=argv[i];if(s=="--demo"||s=="--serve"||s=="--self-test")mode=s;
 else if(s=="--out"&&i+1<argc)out=argv[++i];else if(s=="--input"&&i+1<argc)input=argv[++i];
 else if(s=="--batch"&&i+1<argc){std::string v=argv[++i];size_t idx=0;auto n=std::stoul(v,&idx);
 require(idx==v.size()&&n>0&&n<=4096,"invalid_batch");batch=n;}
 else throw std::runtime_error("unknown_argument:"+s);}
 if(mode=="--self-test"){selftest();return 0;}
 Runtime rt;if(mode=="--serve"){serve(rt,out);return 0;}
 auto lines=input.empty()?default_cases():read_csv(input);demo(rt,lines,batch,out);return 0;
 }catch(const std::exception&e){std::cerr<<"FAIL "<<e.what()<<'\n';return 1;}}
