// paceval Collider Research Demonstrator (C++17)
// Scientific target: massless two-body invariant m^2 and a synthetic event weight.
// Real paceval results require the original vendor runtime, never the test fixture.
#include <algorithm>
#include <array>
#include <chrono>
#include <cmath>
#include <cstdint>
#include <cstdlib>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <limits>
#include <sstream>
#include <stdexcept>
#include <string>
#include <vector>
#ifdef _WIN32
#  define NOMINMAX
#  include <windows.h>
#else
#  include <dlfcn.h>
#endif

using Clock = std::chrono::steady_clock;
static double elapsed(Clock::time_point t) {return std::chrono::duration<double, std::milli>(Clock::now()-t).count();}
static void require(bool v, const std::string &message) {if (!v) throw std::runtime_error(message);}

static constexpr int NV=8;
static constexpr const char* VARIABLES="pt1 pt2 deta dphi a b c d";
static constexpr const char* DIRECT="2*pt1*pt2*(cosh(deta)-cos(dphi))";
static constexpr const char* STABLE="4*pt1*pt2*(sinh(deta/2)^2+sin(dphi/2)^2)";
// Clearly artificial: NOT a CMS detector calibration or experimentally measured weight.
static constexpr const char* WEIGHT="(1+a*exp(-abs(deta))*cos(dphi)+b*ln(1+pt1/100)+c*sin(pt2/30)^2)*(1+d*tanh((pt1+pt2-100)/60))";
static const std::string FUSED=std::string("(")+STABLE+")*("+WEIGHT+")";
using Sample=std::array<double,NV>;

static double native_direct(const Sample&v) {return 2*v[0]*v[1]*(std::cosh(v[2])-std::cos(v[3]));}
static double native_stable(const Sample&v) {double x=std::sinh(v[2]*0.5),y=std::sin(v[3]*0.5); return 4*v[0]*v[1]*(x*x+y*y);}
static double native_weight(const Sample&v) {double x=std::sin(v[1]/30); return (1+v[4]*std::exp(-std::abs(v[2]))*std::cos(v[3])+v[5]*std::log1p(v[0]/100)+v[6]*x*x)*(1+v[7]*std::tanh((v[0]+v[1]-100)/60));}
static long double extended_reference(const Sample&v) {long double x=std::sinh((long double)v[2]/2),y=std::sin((long double)v[3]/2);return 4*(long double)v[0]*(long double)v[1]*(x*x+y*y);}
static uint64_t next_rand(uint64_t &s) {s^=s>>12; s^=s<<25; s^=s>>27; return s*UINT64_C(2685821657736338717);}
static double unit(uint64_t&s){return (next_rand(s)>>11)*(1.0/9007199254740992.0);}
static Sample make_sample(size_t i,uint64_t &rng) {
  const double u=unit(rng), v=unit(rng);
  // 20% near collinear, 80% representative synthetic angular differences.
  const double angle=(i%5==0)?std::pow(10.,-13+11*u):2.2*u;
  const double phi=(i%5==0)?std::pow(10.,-13+11*v):(6.0*v-3.0);
  return Sample{{20+180*unit(rng),20+180*unit(rng),angle,phi,
               0.015+0.01*unit(rng),-0.01+0.02*unit(rng),0.007+0.003*unit(rng),
               -0.01+0.02*unit(rng)}};
}
struct Options {std::string lib, csv="results/benchmark.csv", inputCSV;size_t events=120000,batch=16384;bool selftest=false,requirePaceval=false;};
static size_t as_count(const std::string&s){size_t used=0;auto value=std::stoull(s,&used);require(used==s.size()&&value>0&&value<=10000000,"invalid count: "+s);return(size_t)value;}
static Options options(int argc,char**argv){Options o;for(int i=1;i<argc;++i){std::string a=argv[i];auto val=[&](){require(i+1<argc,"missing value after "+a);return std::string(argv[++i]);};
  if(a=="--library")o.lib=val();else if(a=="--input-csv")o.inputCSV=val();else if(a=="--events")o.events=as_count(val());else if(a=="--batch")o.batch=as_count(val());else if(a=="--csv")o.csv=val();else if(a=="--self-test")o.selftest=true;else if(a=="--require-paceval")o.requirePaceval=true;
  else if(a=="--help"){std::cout<<"Usage: collider [--library path] [--events N] [--batch N] [--csv path] [--input-csv path] [--self-test] [--require-paceval]\n";std::exit(0);}else throw std::runtime_error("unknown option: "+a);
 }return o;}

class DynamicLibrary {
#ifdef _WIN32
 HMODULE h=nullptr;
#else
 void*h=nullptr;
#endif
 public:
 explicit DynamicLibrary(const std::string &file){
#ifdef _WIN32
 h=LoadLibraryA(file.c_str());
#else
 h=dlopen(file.c_str(),RTLD_NOW|RTLD_LOCAL);
#endif
 require(h!=nullptr,"cannot load dynamic library: "+file);
 }
 ~DynamicLibrary(){if(h){
#ifdef _WIN32
 FreeLibrary(h);
#else
 dlclose(h);
#endif
 }}
 DynamicLibrary(const DynamicLibrary&)=delete;DynamicLibrary&operator=(const DynamicLibrary&)=delete;
 void* find(const char*name)const{
#ifdef _WIN32
 return reinterpret_cast<void*>(GetProcAddress(h,name));
#else
 return dlsym(h,name);
#endif
 }
 template<typename T>T symbol(const char*name)const{auto x=find(name);require(x!=nullptr,std::string("symbol unavailable: ")+name);return reinterpret_cast<T>(x);}
};

// Foreign-function signatures as published at https://paceval.com/api/
// The FFI symbols live in the paceval shared runtime; no replacement engine is used.
class Paceval {
 DynamicLibrary library;
 using Init=bool (*)(const char*);
 using Free=bool (*)();
 using Create=void* (*)(const char*,unsigned long,const char*,bool,void*);
 using Delete=bool (*)(void*);
 using IsError=bool (*)(void*);
 using ErrorInfo=int (*)(void*,char*,long*);
 using Batch=bool (*)(void*,double*,unsigned long,double*,double*,double*,int*);
 using Multi=bool (*)(void**,unsigned long,double*,unsigned long,double*,double*,double*,int*);
 using Single=double (*)(void*,double*,double*,double*);
 Init init;Free release;Create create;Delete destroy;IsError isError;ErrorInfo errorInfo;Batch batch;Multi multi;Single single;
 std::vector<void*>handles;
 bool initialized=false;
 public:
 bool fixture=false;
 explicit Paceval(const std::string &file):library(file),
  init(library.symbol<Init>("pacevalLibrary_Initialize")),
  release(library.symbol<Free>("pacevalLibrary_Free")),
  create(library.symbol<Create>("pacevalLibrary_CreateComputation")),
  destroy(library.symbol<Delete>("pacevalLibrary_DeleteComputation")),
  isError(library.symbol<IsError>("pacevalLibrary_GetIsError")),
  errorInfo(library.symbol<ErrorInfo>("pacevalLibrary_GetErrorInformation")),
  batch(library.symbol<Batch>("pacevalLibrary_dGetComputationResultExt")),
  multi(library.symbol<Multi>("pacevalLibrary_dGetMultipleComputationsResultsExt")),
  single(library.symbol<Single>("pacevalLibrary_dGetComputationResult")) {
    fixture=library.find("paceval_mock_fixture_marker")!=nullptr;
    require(init(nullptr),"paceval initialize failed");initialized=true;
 }
 ~Paceval(){for(auto it=handles.rbegin();it!=handles.rend();++it)destroy(*it);if(initialized)release();}
 Paceval(const Paceval&)=delete;Paceval&operator=(const Paceval&)=delete;
 std::string error(void*h)const{char token[256]={};long pos=-1;int err=errorInfo(h,token,&pos);return "code="+std::to_string(err)+" op="+token+" pos="+std::to_string(pos);}
 void*make(const std::string&formula,bool tinc=false){auto h=create(formula.c_str(),NV,VARIABLES,tinc,nullptr);require(h!=nullptr,"paceval CreateComputation returned null");handles.push_back(h);require(!isError(h),"paceval formula error: "+formula+" : "+error(h));return h;}
 void eval(void*h,std::vector<double>&inputs,size_t n,std::vector<double>&out,std::vector<int>&errors,std::vector<double>*lo=nullptr,std::vector<double>*hi=nullptr)const{
  out.resize(n);errors.resize(n);if(lo)lo->resize(n);if(hi)hi->resize(n);
  bool apiError=batch(h,inputs.data(),(unsigned long)n,out.data(),lo?lo->data():nullptr,hi?hi->data():nullptr,errors.data());
  require(!apiError,"paceval reported batch error: "+error(h));
  for(size_t i=0;i<n;++i)require(errors[i]==0,"paceval batch error item="+std::to_string(i)+" type="+std::to_string(errors[i])+" : "+error(h));
  require(!isError(h),"paceval batch state error: "+error(h));
 }
 void evalmulti(std::vector<void*> &h,std::vector<double>&inputs,size_t n,std::vector<double>&out,std::vector<int>&errors)const{
  out.resize(n*h.size());errors.resize(n*h.size());
  bool apiError=multi(h.data(),(unsigned long)h.size(),inputs.data(),(unsigned long)n,out.data(),nullptr,nullptr,errors.data());
  require(!apiError,"paceval reported multi-graph API error");
  for(size_t i=0;i<errors.size();++i)require(errors[i]==0,"paceval multi error item="+std::to_string(i)+" type="+std::to_string(errors[i]));
  for(auto x:h)require(!isError(x),"paceval multi state error: "+error(x));
 }
 std::array<double,3> tinc_one(void*h,const Sample &v)const{auto input=v;double lo=std::numeric_limits<double>::quiet_NaN(),hi=lo;auto output=single(h,input.data(),&lo,&hi);require(!isError(h),"paceval TINC failed: "+error(h));return {{output,lo,hi}};}
};

// Optional collider event input. Four required columns (pt1,pt2,deta,dphi), four
// optional synthetic-weight parameters (a,b,c,d). Input is never treated as calibrated data.
// No ROOT dependency: a NanoAOD/RDataFrame preselection may export these columns.
static std::vector<Sample> read_samples(const std::string &path,size_t limit){
 std::ifstream f(path);require(f.good(),"cannot read input CSV: "+path);
 std::string line;std::vector<Sample> rows;rows.reserve(std::min(limit,size_t(200000)));
 size_t rowNo=0;
 while(std::getline(f,line)&&rows.size()<limit){++rowNo;if(line.empty()||line[0]=='#')continue;
  std::vector<std::string> fields;std::istringstream stream(line);std::string val;
  while(std::getline(stream,val,','))fields.push_back(val);
  if(rowNo==1 && fields.size()>=4 && fields[0]=="pt1" && fields[1]=="pt2")continue;
  require(fields.size()==4||fields.size()==8,"CSV requires 4 or 8 numeric columns at line "+std::to_string(rowNo));
  Sample x{{0.,0.,0.,0.,0.02,0.005,0.01,0.01}};
  for(size_t j=0;j<fields.size();++j){size_t used=0;
   try{x[j]=std::stod(fields[j],&used);}catch(const std::exception&){throw std::runtime_error("invalid numeric CSV input at line "+std::to_string(rowNo));}
   require(used==fields[j].find_last_not_of(" \t\r")+1 && std::isfinite(x[j]),"invalid/nonfinite CSV value line "+std::to_string(rowNo));
  }
  require(x[0]>0&&x[1]>0,"CSV transverse momenta must be positive at line "+std::to_string(rowNo));
  rows.push_back(x);
 }
 require(!rows.empty(),"empty input CSV: "+path);return rows;
}

struct Check {size_t compared=0,failed=0;double maxRelative=0;};
static void audit(double got,double expected,Check&check,double rel=2e-9,double abs=1e-28){
 ++check.compared;
 double diff=std::abs(got-expected), denom=std::max(std::abs(expected),1e-30);
 check.maxRelative=std::max(check.maxRelative,diff/denom);
 if(!std::isfinite(got)||diff>abs+rel*std::abs(expected))++check.failed;
}
static void self_tests(){
 auto approx=[](double a,double b,double rel=1e-11){return std::abs(a-b)<=rel*std::max({std::abs(a),std::abs(b),1e-30});};
 Sample t{{50,60,0.3,0.4,0.02,0.005,0.01,0.01}};
 require(approx(native_direct(t),native_stable(t)),"mass identity failed");
 require(native_weight(t)>0,"weight positive test failed");
 for(int k=2;k<=13;++k){t[2]=t[3]=std::pow(10.,-k);require(approx(native_stable(t),(double)extended_reference(t),5e-13),"stable formula vs extended precision failed");}
 t[2]=0;t[3]=0;require(native_stable(t)==0&&native_direct(t)==0,"collinear zero not zero");
 uint64_t s=20261110;for(size_t i=0;i<2500;++i){auto v=make_sample(i,s);require(std::isfinite(native_stable(v))&&std::isfinite(native_weight(v)),"nonfinite synthetic sample");require(native_stable(v)>=0,"negative invariant mass squared");}
 std::cout<<"SELFTEST PASS: formula identity, high precision spot checks, kinematic edges, 2500 synthetic samples\n";
}
static void write_csv_header(const std::string&file){std::ofstream f(file);require(f.good(),"cannot write "+file);f<<"backend,method,events,batch,init_ms,pack_ms,eval_ms,audit_failures,max_relative_difference,checksum\n";}
static void add_csv(const std::string&file,const std::string&backend,const std::string&method,size_t n,size_t batch,double setup,double pack,double compute,const Check&audit,double checksum){std::ofstream f(file,std::ios::app);require(f.good(),"cannot append "+file);f<<std::setprecision(12)<<backend<<','<<method<<','<<n<<','<<batch<<','<<setup<<','<<pack<<','<<compute<<','<<audit.failed<<','<<audit.maxRelative<<','<<checksum<<'\n';}
static void report(const std::string&name,double ms,double checksum){std::cout<<std::setw(34)<<std::left<<name<<std::fixed<<std::setprecision(3)<<std::setw(12)<<ms<<" ms; checksum="<<std::setprecision(12)<<checksum<<'\n';}

int main(int argc,char **argv){try{
 auto opt=options(argc,argv);self_tests();if(opt.selftest)return 0;
 require(opt.batch<=1000000,"batch too large");
 std::cout<<"Collider Research Demonstrator / deterministic synthetic events\n";
 std::vector<Sample> events;
 if(!opt.inputCSV.empty())events=read_samples(opt.inputCSV,opt.events);
 else {events.reserve(opt.events);uint64_t rng=20261110;for(size_t i=0;i<opt.events;++i)events.push_back(make_sample(i,rng));}
 opt.events=events.size();
 std::cout<<"Events="<<opt.events<<" Batch="<<opt.batch
          <<(opt.inputCSV.empty()?" seed=20261110 (synthetic)":" CSV="+opt.inputCSV)<<"\n";
 if(opt.requirePaceval)require(!opt.lib.empty(),"--require-paceval needs --library with actual paceval runtime");
 // Warm the native transcendental functions before taking measurements.
 volatile double warmup=0;for(size_t i=0;i<std::min(opt.events,size_t(512));++i){warmup+=native_direct(events[i])+native_stable(events[i])+native_weight(events[i]);}
 (void)warmup;
 std::vector<double> refStable(opt.events),refWeight(opt.events),refDirect(opt.events),refFused(opt.events);
 auto t=Clock::now();double cs1=0,cs2=0,cs3=0;
 for(size_t i=0;i<opt.events;++i){refDirect[i]=native_direct(events[i]);cs1+=refDirect[i];}double direct_ms=elapsed(t);
 t=Clock::now();for(size_t i=0;i<opt.events;++i){refStable[i]=native_stable(events[i]);cs2+=refStable[i];}double stable_ms=elapsed(t);
 t=Clock::now();for(size_t i=0;i<opt.events;++i){refWeight[i]=native_weight(events[i]);cs3+=refWeight[i];}double weight_ms=elapsed(t);
 t=Clock::now();double cs4=0;for(size_t i=0;i<opt.events;++i){refFused[i]=native_stable(events[i])*native_weight(events[i]);cs4+=refFused[i];}double fused_ms=elapsed(t);
 // Parameter-scan baseline: five independent systematic variations, no detector claim.
 t=Clock::now();double nativeScanChecksum=0;
 for(int v=0;v<5;++v){double scale=0.8+0.1*v;
   for(const auto &base:events){auto x=base;for(int j=4;j<8;++j)x[j]*=scale;nativeScanChecksum+=native_weight(x);}}
 double nativeScanMs=elapsed(t);
 report("C++ direct mass2",direct_ms,cs1);report("C++ stable mass2",stable_ms,cs2);report("C++ synthetic weight",weight_ms,cs3);report("C++ fused mass2*weight",fused_ms,cs4);report("C++ weight x 5 variations",nativeScanMs,nativeScanChecksum);
 write_csv_header(opt.csv);const Check zero{};
 add_csv(opt.csv,"native","mass_direct",opt.events,opt.batch,0,0,direct_ms,zero,cs1);
 add_csv(opt.csv,"native","mass_stable",opt.events,opt.batch,0,0,stable_ms,zero,cs2);
 add_csv(opt.csv,"native","synthetic_weight",opt.events,opt.batch,0,0,weight_ms,zero,cs3);
 add_csv(opt.csv,"native","fused_mass_weight",opt.events,opt.batch,0,0,fused_ms,zero,cs4);
 add_csv(opt.csv,"native","weight_5_variations",opt.events*5,opt.batch,0,0,nativeScanMs,zero,nativeScanChecksum);
 // Mathematical edge-case report with extended precision on this machine.
 size_t catastrophic=0, lostPositive=0, thresholdFlips=0;
 for(size_t k=0;k<opt.events;++k){long double exact=extended_reference(events[k]);long double directError=std::abs((long double)refDirect[k]-exact);long double stableError=std::abs((long double)refStable[k]-exact);if(directError>1e-6L*std::abs(exact)&&stableError<1e-6L*std::abs(exact))catastrophic++;
   if(refDirect[k]<=0 && refStable[k]>0) lostPositive++;
   if((refDirect[k]>1e-10)!=(refStable[k]>1e-10)) thresholdFlips++;}
 std::cout<<"Numerical: "<<catastrophic<<" inputs show >1e-6 relative error in direct but not stable formula (long-double reference, mantissa bits="<<std::numeric_limits<long double>::digits<<")\n";
 std::cout<<"Selections: direct loses positive m2 in "<<lostPositive<<" events; threshold m2>1e-10 differs in "<<thresholdFlips<<" events\n";
 if(opt.lib.empty()){std::cout<<"PACEVAL UNAVAILABLE: specify --library <actual libpaceval_linux_sharedLIB.so>\n";std::cout<<"Native baseline and self-tests finished; no paceval performance claim.\n";return 0;}
 Paceval p(opt.lib);if(opt.requirePaceval)require(!p.fixture,"--require-paceval rejects the mock test fixture");std::cout<<"Backend: "<<(p.fixture?"MOCK FIXTURE (NO PERFORMANCE CLAIM)":"REAL paceval runtime")<<"\n";
 t=Clock::now();void* h0=p.make(DIRECT),* h1=p.make(STABLE),* h2=p.make(WEIGHT),* h3=p.make(FUSED);double setup_ms=elapsed(t);
 std::cout<<"Created 4 reusable graphs in "<<setup_ms<<" ms.\n";
 std::vector<double> input;input.resize(opt.batch*NV);
 // Untimed warmup: eliminate lazy graph initialization from the steady-state estimate.
 {
   size_t wn=std::min(opt.events,opt.batch);
   for(size_t j=0;j<wn;++j)std::copy(events[j].begin(),events[j].end(),input.begin()+j*NV);
   std::vector<double> work;std::vector<int> workErrors;
   p.eval(h0,input,wn,work,workErrors);p.eval(h1,input,wn,work,workErrors);
   p.eval(h2,input,wn,work,workErrors);p.eval(h3,input,wn,work,workErrors);
   std::vector<void*> workHandles{h0,h1,h2};p.evalmulti(workHandles,input,wn,work,workErrors);
 }
 
 std::vector<double> out, outs, outw, outf, multi;
 std::vector<int> errors;Check audit0,audit1,audit2,audit3,auditMulti;
 double pack_ms=0, p0_ms=0,p1_ms=0,p2_ms=0,p3_ms=0,multi_ms=0,s0=0,s1=0,s2=0,s3=0,sm=0;
 std::vector<void*> handles{h0,h1,h2};
 for(size_t offset=0;offset<opt.events;offset+=opt.batch){size_t n=std::min(opt.batch,opt.events-offset);
   t=Clock::now();for(size_t j=0;j<n;++j)std::copy(events[offset+j].begin(),events[offset+j].end(),input.begin()+j*NV);pack_ms+=elapsed(t);
   t=Clock::now();p.eval(h0,input,n,out,errors);p0_ms+=elapsed(t);
   for(size_t j=0;j<n;++j){audit(out[j],refDirect[offset+j],audit0,2e-8);s0+=out[j];}
   t=Clock::now();p.eval(h1,input,n,outs,errors);p1_ms+=elapsed(t);
   for(size_t j=0;j<n;++j){audit(outs[j],refStable[offset+j],audit1,2e-8);s1+=outs[j];}
   t=Clock::now();p.eval(h2,input,n,outw,errors);p2_ms+=elapsed(t);
   for(size_t j=0;j<n;++j){audit(outw[j],refWeight[offset+j],audit2,2e-8);s2+=outw[j];}
   t=Clock::now();p.eval(h3,input,n,outf,errors);p3_ms+=elapsed(t);
   for(size_t j=0;j<n;++j){audit(outf[j],refFused[offset+j],audit3,2e-8);s3+=outf[j];}
   t=Clock::now();p.evalmulti(handles,input,n,multi,errors);multi_ms+=elapsed(t);
   for(size_t k=0;k<3;++k)for(size_t j=0;j<n;++j){double reference=(k==0?refDirect[offset+j]:(k==1?refStable[offset+j]:refWeight[offset+j]));audit(multi[k*n+j],reference,auditMulti,2e-8);sm+=multi[k*n+j];}
 }
 report("paceval direct mass2 batch",p0_ms,s0);report("paceval stable mass2 batch",p1_ms,s1);report("paceval weight batch",p2_ms,s2);report("paceval fused batch",p3_ms,s3);report("paceval multi-graph batch",multi_ms,sm);
 std::cout<<"Three-graph paceval consolidation factor (separate/multi): "<<std::fixed<<std::setprecision(3)<<(p0_ms+p1_ms+p2_ms)/multi_ms<<"x (same three results)\n";
 std::cout<<"Audit mismatches direct/stable/weight/fused/multi: "<<audit0.failed<<'/'<<audit1.failed<<'/'<<audit2.failed<<'/'<<audit3.failed<<'/'<<auditMulti.failed<<"\n";
 std::string backend=p.fixture?"mock_fixture":"real_paceval";
 add_csv(opt.csv,backend,"mass_direct",opt.events,opt.batch,setup_ms,pack_ms,p0_ms,audit0,s0);
 add_csv(opt.csv,backend,"mass_stable",opt.events,opt.batch,setup_ms,pack_ms,p1_ms,audit1,s1);
 add_csv(opt.csv,backend,"synthetic_weight",opt.events,opt.batch,setup_ms,pack_ms,p2_ms,audit2,s2);
 add_csv(opt.csv,backend,"fused_mass_weight",opt.events,opt.batch,setup_ms,pack_ms,p3_ms,audit3,s3);
 add_csv(opt.csv,backend,"three_graph_multi",opt.events,opt.batch,setup_ms,pack_ms,multi_ms,auditMulti,sm);
 // Same validated graph reused for five parameter scenarios, no graph rebuild.
 Check scanAudit;double scanEvalMs=0,scanPackMs=0,scanChecksum=0;
 for(int v=0;v<5;++v){double scale=0.8+0.1*v;
   for(size_t offset=0;offset<opt.events;offset+=opt.batch){size_t n=std::min(opt.batch,opt.events-offset);
     t=Clock::now();for(size_t j=0;j<n;++j){auto x=events[offset+j];for(int a=4;a<8;++a)x[a]*=scale;std::copy(x.begin(),x.end(),input.begin()+j*NV);}scanPackMs+=elapsed(t);
     t=Clock::now();p.eval(h2,input,n,outw,errors);scanEvalMs+=elapsed(t);
     for(size_t j=0;j<n;++j){auto x=events[offset+j];for(int a=4;a<8;++a)x[a]*=scale;
       audit(outw[j],native_weight(x),scanAudit,2e-8);scanChecksum+=outw[j];}
   }
 }
 report("paceval weight x 5 variations",scanEvalMs,scanChecksum);
 std::cout<<"Systematics: graph reused 5 times; mismatches="<<scanAudit.failed<<", repack_ms="<<scanPackMs<<"\n";
 add_csv(opt.csv,backend,"weight_5_variations",opt.events*5,opt.batch,0,scanPackMs,scanEvalMs,scanAudit,scanChecksum);
 // Optimized systematic scan: flatten all 5 variations into the same batch evaluation.
 // Uses the very same handle h2, which is created only ONCE.
 const size_t scenarioCount=5;
 require(opt.batch<=1000000/scenarioCount,"batch too large for flattened scan");
 std::vector<double> flatInput(opt.batch*scenarioCount*NV);
 std::vector<double> flatOut;std::vector<int> flatErrors;Check flatAudit;
 double flatPackMs=0,flatEvalMs=0,flatChecksum=0;
 for(size_t offset=0;offset<opt.events;offset+=opt.batch){size_t n=std::min(opt.batch,opt.events-offset);
   t=Clock::now();
   for(size_t v=0;v<scenarioCount;++v){double scale=0.8+0.1*double(v);
     for(size_t j=0;j<n;++j){Sample x=events[offset+j];for(int a=4;a<8;++a)x[a]*=scale;
       std::copy(x.begin(),x.end(),flatInput.begin()+(v*n+j)*NV);}}
   flatPackMs+=elapsed(t);
   t=Clock::now();p.eval(h2,flatInput,n*scenarioCount,flatOut,flatErrors);flatEvalMs+=elapsed(t);
   for(size_t v=0;v<scenarioCount;++v){double scale=0.8+0.1*double(v);
     for(size_t j=0;j<n;++j){Sample x=events[offset+j];for(int a=4;a<8;++a)x[a]*=scale;
       double got=flatOut[v*n+j];audit(got,native_weight(x),flatAudit,2e-8);flatChecksum+=got;}}
 }
 report("paceval 5 systematics flattened",flatEvalMs,flatChecksum);
 std::cout<<"Systematics flattened: accuracy mismatches="<<flatAudit.failed
          <<", eval speed factor vs sequential="<<std::fixed<<std::setprecision(3)<<scanEvalMs/flatEvalMs
          <<"x, pack_ms="<<flatPackMs<<"\n";
 add_csv(opt.csv,backend,"weight_5_variations_flat",opt.events*scenarioCount,opt.batch*scenarioCount,0,flatPackMs,flatEvalMs,flatAudit,flatChecksum);
 // TINC is a separate diagnostic study. 80-bit inclusion is NOT proof of rigour.
 t=Clock::now();void* hTincStable=p.make(STABLE,true),*hTincDirect=p.make(DIRECT,true);double tincSetup=elapsed(t);
 size_t includedStable=0,includedDirect=0,invalid=0;
 auto slash=opt.csv.find_last_of("/\\");
 std::string intervalCSV=(slash==std::string::npos?std::string():opt.csv.substr(0,slash+1))+"tinc_samples.csv";
 std::ofstream intervals(intervalCSV);require(intervals.good(),"cannot write TINC samples");
 intervals<<"backend,formula,angle,pt1,pt2,deta,dphi,result,lower,upper,extended_reference,contains_extended,status\n";
 std::cout<<"TINC samples (long-double check, NOT rigorous certification):\n";
 for(int k=2;k<=13;++k){Sample v{{50,60,std::pow(10.,-k),std::pow(10.,-k),0.02,0.005,0.01,0.01}};
   const long double ref=extended_reference(v);
   for(int which=0;which<2;++which){bool stable=(which==0);
     const double missing=std::numeric_limits<double>::quiet_NaN();std::array<double,3> result{{missing,missing,missing}};std::string status="OK";
     try{result=p.tinc_one(stable?hTincStable:hTincDirect,v);}catch(const std::exception&e){status="API_ERROR";std::cerr<<"TINC "<<(stable?"stable":"direct")<<" angle=1e-"<<k<<" : "<<e.what()<<'\n';}
     bool valid=std::isfinite(result[1])&&std::isfinite(result[2])&&result[1]<=result[2];
     bool contains=valid&&(long double)result[1]<=ref&&(long double)result[2]>=ref;
     if(stable)includedStable+=contains;else includedDirect+=contains;invalid+=!valid;
     intervals<<std::setprecision(17)<<backend<<','<<(stable?"stable":"direct")<<','<<v[2]<<','<<v[0]<<','<<v[1]<<','<<v[2]<<','<<v[3]<<','
              <<result[0]<<','<<result[1]<<','<<result[2]<<','<<std::setprecision(21)<<ref<<','<<(contains?1:0)<<','<<status<<'\n';
   }
 }
 std::cout<<"TINC: stable inclusion="<<includedStable<<"/12, direct inclusion="<<includedDirect<<"/12, invalid="<<invalid<<"; setup_ms="<<tincSetup<<"\n";
 std::cout<<"TINC interval data: "<<intervalCSV<<" (validate against an independent high-precision reference)\n";
 std::cout<<"Saved CSV: "<<opt.csv<<"\n";
 return (audit0.failed||audit1.failed||audit2.failed||audit3.failed||auditMulti.failed||scanAudit.failed||flatAudit.failed)?2:0;
 }catch(const std::exception&e){std::cerr<<"ERROR: "<<e.what()<<'\n';return 1;}}
