// paceval Quantum Research: reproducible classical numerical demonstrator (C++17)
// Quantum hardware is not simulated as an accelerator. All computations are classical.
// Original paceval runtime must be supplied externally. Not a performance simulation.
#include <algorithm>
#include <array>
#include <chrono>
#include <cmath>
#include <cstdint>
#include <cstdlib>
#include <cstring>
#include <dlfcn.h>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <limits>
#include <numeric>
#include <random>
#include <sstream>
#include <stdexcept>
#include <string>
#include <vector>

using Clock=std::chrono::steady_clock;
static double ms(Clock::time_point begin) {return std::chrono::duration<double,std::milli>(Clock::now()-begin).count();}
static void ensure(bool ok,const std::string &why){if(!ok)throw std::runtime_error(why);}
static constexpr size_t NV=9;
static constexpr double PI=3.141592653589793238462643383279502884;
static constexpr const char* VARS="t contrast tau freq phase hits trials theta1 theta2";
// Analytical Ramsey probability, conditional binomial negative log-likelihood,
// derivative with respect to frequency and the exact two-qubit circuit expectation.
// Independent formulas share their input vector, enabling paceval's multi-graph API.
static const std::string RAMSEY="(1+contrast*exp(-t/tau)*cos(6.283185307179586*freq*t+phase))/2";
static const std::string NLL="-(hits*ln("+RAMSEY+")+(trials-hits)*ln(1-("+RAMSEY+")))";
static const std::string DERIV="-3.141592653589793*contrast*t*exp(-t/tau)*sin(6.283185307179586*freq*t+phase)";
static const std::string CIRCUIT="cos(theta1)*cos(theta2)";
static const std::string FOURIER="(cos(theta1-theta2)+cos(theta1+theta2))/2";
using Sample=std::array<double,NV>;
static double prob(const Sample&v){return 0.5*(1+v[1]*std::exp(-v[0]/v[2])*std::cos(2*PI*v[3]*v[0]+v[4]));}
static double nll(const Sample&v){double p=prob(v);return -(v[5]*std::log(p)+(v[6]-v[5])*std::log1p(-p));}
static double deriv(const Sample&v){return -PI*v[1]*v[0]*std::exp(-v[0]/v[2])*std::sin(2*PI*v[3]*v[0]+v[4]);}
static double circuit(const Sample&v){return std::cos(v[7])*std::cos(v[8]);}
static double fourier(const Sample&v){return (std::cos(v[7]-v[8])+std::cos(v[7]+v[8]))/2;}
static double circuit_statevector(double a,double b){
  // |00> -> (Ry(a) tensor Ry(b)) |00> -> CNOT(0 -> 1); expectation I tensor Z.
  double A=std::cos(a/2),B=std::sin(a/2),C=std::cos(b/2),D=std::sin(b/2);
  double p00=A*C,p01=A*D,p10=B*D,p11=B*C; // CNOT swaps amplitudes |10> and |11>
  return p00*p00-p01*p01+p10*p10-p11*p11;
}
struct Options{std::string lib,csv="quantum_results.csv",input;size_t events=60000,batch=8192;bool requirePaceval=false,selftest=false;};
static size_t positive(const std::string&x){size_t k=0;auto n=std::stoull(x,&k);ensure(k==x.size()&&n>0&&n<=2000000,"invalid positive integer: "+x);return(size_t)n;}
static Options parse(int argc,char**argv){Options o;for(int i=1;i<argc;++i){std::string x=argv[i];auto arg=[&](){ensure(i+1<argc,"missing argument: "+x);return std::string(argv[++i]);};
 if(x=="--library")o.lib=arg();else if(x=="--events")o.events=positive(arg());else if(x=="--batch")o.batch=positive(arg());else if(x=="--csv")o.csv=arg();else if(x=="--input-csv")o.input=arg();else if(x=="--require-paceval")o.requirePaceval=true;else if(x=="--self-test")o.selftest=true;
 else if(x=="--help"){std::cout<<"Usage: quantum [--library /path/libpaceval.so] [--events 60000] [--batch 8192] [--input-csv file.csv] [--csv output.csv] [--require-paceval] [--self-test]\n";std::exit(0);}else throw std::runtime_error("unknown argument: "+x);
 }return o;}
class Library{
 void *h=nullptr;
 public:
 explicit Library(const std::string &path){h=dlopen(path.c_str(),RTLD_NOW|RTLD_LOCAL);if(!h){const char *message=dlerror();throw std::runtime_error(std::string("dlopen failed: ")+(message?message:path.c_str()));}}
 ~Library(){if(h)dlclose(h);}
 void *find(const char*name)const{return dlsym(h,name);}
 template<class T>T symbol(const char*name)const{void*p=find(name);ensure(p,std::string("missing symbol: ")+name);return reinterpret_cast<T>(p);}
};
class Paceval{
 Library lib;
 using Init=bool (*)(const char*);using Free=bool (*)();using Create=void* (*)(const char*,unsigned long,const char*,bool,void*);
 using Delete=bool (*)(void*);using Error=bool (*)(void*);using ErrorInfo=int (*)(void*,char*,long*);
 using Batch=bool (*)(void*,double*,unsigned long,double*,double*,double*,int*);
 using Multi=bool (*)(void**,unsigned long,double*,unsigned long,double*,double*,double*,int*);
 using Single=double (*)(void*,double*,double*,double*);
 Init init;Free release;Create create;Delete destroy;Error isError;ErrorInfo errorInfo;Batch batch;Multi multi;Single single;
 std::vector<void*>owned;bool initialized=false;
 public:
 explicit Paceval(const std::string &path):lib(path),init(lib.symbol<Init>("pacevalLibrary_Initialize")),release(lib.symbol<Free>("pacevalLibrary_Free")),create(lib.symbol<Create>("pacevalLibrary_CreateComputation")),destroy(lib.symbol<Delete>("pacevalLibrary_DeleteComputation")),isError(lib.symbol<Error>("pacevalLibrary_GetIsError")),errorInfo(lib.symbol<ErrorInfo>("pacevalLibrary_GetErrorInformation")),batch(lib.symbol<Batch>("pacevalLibrary_dGetComputationResultExt")),multi(lib.symbol<Multi>("pacevalLibrary_dGetMultipleComputationsResultsExt")),single(lib.symbol<Single>("pacevalLibrary_dGetComputationResult")){
  ensure(!lib.find("paceval_mock_fixture_marker"),"mock fixture explicitly rejected");ensure(init(nullptr),"paceval initialization failed");initialized=true;
 }
 ~Paceval(){for(auto p:owned)destroy(p);if(initialized)release();}
 std::string err(void*h)const{char buf[256]={};long pos=-1;auto code=errorInfo(h,buf,&pos);return "code="+std::to_string(code)+" token="+buf+" pos="+std::to_string(pos);}
 void *graph(const std::string &expr,bool tinc=false){auto h=create(expr.c_str(),(unsigned long)NV,VARS,tinc,nullptr);ensure(h,"paceval CreateComputation returned nullptr");owned.push_back(h);ensure(!isError(h),"paceval graph failure: "+err(h)+" expr="+expr);return h;}
 void eval(void*h,std::vector<double>&input,size_t count,std::vector<double>&out,std::vector<int>&errors){out.resize(count);errors.resize(count);
  bool apiError=batch(h,input.data(),(unsigned long)count,out.data(),nullptr,nullptr,errors.data());ensure(!apiError,"paceval batch error "+err(h));ensure(!isError(h),"paceval batch state error "+err(h));for(size_t j=0;j<count;++j)ensure(!errors[j],"paceval item error "+std::to_string(errors[j]));}
 void evalMulti(std::vector<void*>&handles,std::vector<double>&input,size_t count,std::vector<double>&out,std::vector<int>&errors){out.resize(handles.size()*count);errors.resize(handles.size()*count);
  bool apiError=multi(handles.data(),(unsigned long)handles.size(),input.data(),(unsigned long)count,out.data(),nullptr,nullptr,errors.data());ensure(!apiError,"paceval multi API error");for(auto h:handles)ensure(!isError(h),"paceval multi state error "+err(h));for(int error:errors)ensure(!error,"paceval multi item error "+std::to_string(error));}
 std::array<double,3> tinc(void*h,const Sample &s){Sample input=s;double lo=std::numeric_limits<double>::quiet_NaN(),hi=lo;double value=single(h,input.data(),&lo,&hi);ensure(!isError(h),"paceval TINC error: "+err(h));return {{value,lo,hi}};}
};
static uint64_t rngNext(uint64_t &state){state^=state>>12;state^=state<<25;state^=state>>27;return state*UINT64_C(2685821657736338717);}
static double rnd(uint64_t&s){return (rngNext(s)>>11)*(1.0/9007199254740992.0);}
static Sample make_sample(size_t i,uint64_t &s){
 const double t=16*(double(i%2048)+0.2*rnd(s))/2048;Sample v{{t,0.9,8.0,0.37,0.32,0.,512.,-PI+2*PI*rnd(s),-PI+2*PI*rnd(s)}};
 // Deterministic synthetic counts; finite sampling, NOT a real quantum device measurement.
 std::mt19937_64 g(rngNext(s));std::binomial_distribution<int> bin((int)v[6],prob(v));v[5]=double(bin(g));return v;
}
static std::vector<Sample> read_csv(const std::string &path,size_t limit){std::ifstream f(path);ensure((bool)f,"cannot open input CSV: "+path);std::vector<Sample>v;std::string line;size_t lineNum=0;
 while(std::getline(f,line)&&v.size()<limit){++lineNum;if(line.empty()||line[0]=='#')continue;
  if(line.rfind("t,contrast,tau,freq,phase,hits,trials,theta1,theta2",0)==0)continue;
  std::stringstream ss(line);std::string token;Sample row{};size_t j=0;
  while(std::getline(ss,token,',')){ensure(j<NV,"too many CSV columns at "+std::to_string(lineNum));size_t used=0;row[j]=std::stod(token,&used);ensure(used==token.find_last_not_of(" \t\r")+1&&std::isfinite(row[j]),"invalid CSV value "+std::to_string(lineNum));++j;}
  ensure(j==NV,"expected 9 CSV columns at "+std::to_string(lineNum));ensure(row[0]>=0&&row[1]>=0&&row[1]<=1&&row[2]>0&&row[6]>0&&row[5]>=0&&row[5]<=row[6],"invalid model domain in CSV");
  ensure(prob(row)>0&&prob(row)<1,"probability outside open (0,1) for log-likelihood; change input/model");v.push_back(row);
 }ensure(!v.empty(),"CSV has no input rows");return v;}
static void selftest(){
 auto close=[](double a,double b,double tol=5e-13){return std::abs(a-b)<=tol;};
 Sample x{{3.2,0.9,8,0.37,0.32,100,512,0.37,-1.2}};
 ensure(close(circuit(x),fourier(x)),"circuit/Fourier identity");ensure(close(circuit(x),circuit_statevector(x[7],x[8])),"statevector/circuit identity");
 ensure(prob(x)>0&&prob(x)<1&&nll(x)>=0,"probability or likelihood domain");
 double d=1e-5;Sample xp=x,xm=x;xp[3]+=d;xm[3]-=d;ensure(std::abs((prob(xp)-prob(xm))/(2*d)-deriv(x))<5e-8,"Ramsey derivative");
 uint64_t seed=20261110;for(size_t i=0;i<2500;++i){auto v=make_sample(i,seed);ensure(std::abs(circuit(v)-circuit_statevector(v[7],v[8]))<1e-12,"independent statevector test");ensure(std::abs(circuit(v)-fourier(v))<1e-12,"Fourier test");ensure(std::isfinite(nll(v)),"nonfinite log-likelihood");}
 std::cout<<"SELFTEST PASS: Ramsey model, frequency derivative, binomial likelihood, independent CNOT/Ry statevector, 2500 samples\n";
}
struct Audit{size_t n=0,fail=0;double worstAbs=0;};
static void check(double value,double expected,Audit&x,double atol=1e-10,double rtol=2e-10){++x.n;double diff=std::abs(value-expected);x.worstAbs=std::max(x.worstAbs,diff);if(!std::isfinite(value)||diff>atol+rtol*std::abs(expected))++x.fail;}
static void record(std::ofstream &f,const std::string &kind,size_t events,size_t batch,double setup,double pack,double runtime,const Audit&a,double sum){f<<std::setprecision(15)<<kind<<','<<events<<','<<batch<<','<<setup<<','<<pack<<','<<runtime<<','<<a.n<<','<<a.fail<<','<<a.worstAbs<<','<<sum<<'\n';}
static void output(const std::string &name,double time,size_t failures=0){std::cout<<std::left<<std::setw(40)<<name<<std::fixed<<std::setprecision(4)<<std::setw(12)<<time<<" ms";if(failures)std::cout<<" FAIL="<<failures;std::cout<<"\n";}
int main(int argc,char**argv){try{
 auto o=parse(argc,argv);selftest();if(o.selftest)return 0;ensure(o.batch<=200000,"batch exceeds supported limit");
 std::vector<Sample>samples;if(!o.input.empty())samples=read_csv(o.input,o.events);else{uint64_t seed=20261110;samples.reserve(o.events);for(size_t i=0;i<o.events;++i)samples.push_back(make_sample(i,seed));}o.events=samples.size();
 std::cout<<"paceval Quantum Research / synthetic Ramsey calibration and analytical two-qubit Fourier models\n"<<"Events="<<o.events<<" batch="<<o.batch<<(o.input.empty()?" deterministic seed=20261110":" CSV="+o.input)<<"\n";
 // Time scalar optimized C++ baselines independently. The same values are used to audit paceval.
 std::vector<double>rP(o.events),rL(o.events),rD(o.events),rC(o.events),rF(o.events);std::ofstream csv(o.csv);ensure(csv.good(),"cannot write CSV: "+o.csv);
 csv<<"method,events,batch,setup_ms,pack_ms,eval_ms,compared,failures,max_absolute_error,checksum\n";Audit none;volatile double warm=0;for(size_t i=0;i<std::min(o.events,size_t(1000));++i)warm+=prob(samples[i])+nll(samples[i])+circuit(samples[i]);(void)warm;
 double nativeTime[5];double sums[5]{};std::vector<double>*ref[]={&rP,&rL,&rD,&rC,&rF};double(*fn[])(const Sample&)={prob,nll,deriv,circuit,fourier};
 const char*labels[]={"ramsey_probability","binomial_nll","ramsey_frequency_gradient","circuit_expectation","circuit_fourier"};
 for(int g=0;g<5;++g){auto begin=Clock::now();for(size_t i=0;i<o.events;++i)(*ref[g])[i]=fn[g](samples[i]);nativeTime[g]=ms(begin);sums[g]=std::accumulate(ref[g]->begin(),ref[g]->end(),0.0);record(csv,std::string("native_")+labels[g],o.events,o.batch,0,0,nativeTime[g],none,sums[g]);output(std::string("C++ ")+labels[g],nativeTime[g]);}
 if(o.lib.empty()){ensure(!o.requirePaceval,"--require-paceval requires --library");std::cout<<"No paceval library; native numerical tests complete; no paceval benchmark reported.\n";return 0;}
 Paceval engine(o.lib);auto begin=Clock::now();std::vector<void*> h{engine.graph(RAMSEY),engine.graph(NLL),engine.graph(DERIV),engine.graph(CIRCUIT),engine.graph(FOURIER)};double setup=ms(begin);
 std::cout<<"Real paceval runtime loaded; created 5 reusable expression graphs in "<<setup<<" ms\n";
 std::vector<double>input(o.batch*NV),work,multi;std::vector<int>errors;std::vector<void*>ramseyGraphs{h[0],h[1],h[2]};
 size_t warmN=std::min(o.events,o.batch);for(size_t j=0;j<warmN;++j)std::copy(samples[j].begin(),samples[j].end(),input.begin()+j*NV);
 for(auto g:h){engine.eval(g,input,warmN,work,errors);}
 engine.evalMulti(ramseyGraphs,input,warmN,multi,errors);
 double evalTime[5]{},pack=0,sumPace[5]{},multiTime=0,multiSum=0;Audit audits[5],amulti;
 for(size_t off=0;off<o.events;off+=o.batch){size_t n=std::min(o.batch,o.events-off);begin=Clock::now();for(size_t j=0;j<n;++j)std::copy(samples[off+j].begin(),samples[off+j].end(),input.begin()+j*NV);pack+=ms(begin);
  for(int g=0;g<5;++g){begin=Clock::now();engine.eval(h[g],input,n,work,errors);evalTime[g]+=ms(begin);for(size_t j=0;j<n;++j){check(work[j],(*ref[g])[off+j],audits[g]);sumPace[g]+=work[j];}}
  begin=Clock::now();engine.evalMulti(ramseyGraphs,input,n,multi,errors);multiTime+=ms(begin);
  for(size_t g=0;g<3;++g)for(size_t j=0;j<n;++j){check(multi[g*n+j],(*ref[g])[off+j],amulti);multiSum+=multi[g*n+j];}
 }
 size_t failed=0;for(int g=0;g<5;++g){std::string label=std::string("paceval_")+labels[g];output(label,evalTime[g],audits[g].fail);record(csv,label,o.events,o.batch,setup,pack,evalTime[g],audits[g],sumPace[g]);failed+=audits[g].fail;}
 double separate=evalTime[0]+evalTime[1]+evalTime[2];output("paceval_ramsey_multi_3_graphs",multiTime,amulti.fail);record(csv,"paceval_ramsey_multi_3_graphs",o.events,o.batch,setup,pack,multiTime,amulti,multiSum);failed+=amulti.fail;
 std::cout<<"Multi-graph paceval reuse factor (3 separate / multi) = "<<std::setprecision(4)<<separate/multiTime<<"x\n";
 // Five frequency settings around the synthetic source frequency. The graph is never recreated.
 // Variations represent parameter studies, NOT independently calibrated experiments.
 static constexpr size_t SCENARIOS=5;static const double shifts[5]={-0.04,-0.02,0,0.02,0.04};
 double sequentialTime=0,seqSum=0,flatTime=0,flatPack=0,flatSum=0;Audit seqAudit,flatAudit;std::vector<double>flatInput(o.batch*NV*SCENARIOS);
 for(size_t v=0;v<SCENARIOS;++v){for(size_t off=0;off<o.events;off+=o.batch){size_t n=std::min(o.batch,o.events-off);
   for(size_t j=0;j<n;++j){Sample temp=samples[off+j];temp[3]+=shifts[v];std::copy(temp.begin(),temp.end(),input.begin()+j*NV);}
   begin=Clock::now();engine.eval(h[1],input,n,work,errors);sequentialTime+=ms(begin);
   for(size_t j=0;j<n;++j){Sample temp=samples[off+j];temp[3]+=shifts[v];check(work[j],nll(temp),seqAudit);seqSum+=work[j];}
 }}
 for(size_t off=0;off<o.events;off+=o.batch){size_t n=std::min(o.batch,o.events-off);begin=Clock::now();
  for(size_t v=0;v<SCENARIOS;++v)for(size_t j=0;j<n;++j){Sample temp=samples[off+j];temp[3]+=shifts[v];std::copy(temp.begin(),temp.end(),flatInput.begin()+(v*n+j)*NV);}
  flatPack+=ms(begin);
  begin=Clock::now();engine.eval(h[1],flatInput,n*SCENARIOS,work,errors);flatTime+=ms(begin);
  for(size_t v=0;v<SCENARIOS;++v)for(size_t j=0;j<n;++j){Sample temp=samples[off+j];temp[3]+=shifts[v];check(work[v*n+j],nll(temp),flatAudit);flatSum+=work[v*n+j];}
 }
 output("paceval_frequency_scan_5_separate",sequentialTime,seqAudit.fail);output("paceval_frequency_scan_5_flattened",flatTime,flatAudit.fail);
 record(csv,"paceval_frequency_scan_5_separate",o.events*SCENARIOS,o.batch,0,0,sequentialTime,seqAudit,seqSum);record(csv,"paceval_frequency_scan_5_flattened",o.events*SCENARIOS,o.batch*SCENARIOS,0,flatPack,flatTime,flatAudit,flatSum);
 failed+=seqAudit.fail+flatAudit.fail;
 std::cout<<"Flattened frequency-scan factor = "<<std::setprecision(4)<<sequentialTime/flatTime<<"x; no graph regeneration\n";
 // Separate single-value TINC diagnostic. Independent high-precision rechecking is a Python script.
 begin=Clock::now();void *tRamsey=engine.graph(RAMSEY,true),*tCircuit=engine.graph(CIRCUIT,true);double tincSetup=ms(begin);
 auto slash=o.csv.find_last_of("/\\");const std::string dir=slash==std::string::npos?std::string():o.csv.substr(0,slash+1);
 std::ofstream ti(dir+"tinc_samples.csv");ensure(ti.good(),"cannot write tinc_samples.csv");ti<<"formula,sample_index,t,contrast,tau,freq,phase,hits,trials,theta1,theta2,paceval_value,lower,upper,double_reference,contains_double\n";
 size_t enclosed[2]{};size_t invalid=0;for(int i=0;i<12;++i){Sample v=samples[(size_t(i)*o.events)/12];
  for(int w=0;w<2;++w){auto q=engine.tinc(w==0?tRamsey:tCircuit,v);double reference=w==0?prob(v):circuit_statevector(v[7],v[8]);bool valid=std::isfinite(q[1])&&std::isfinite(q[2])&&q[1]<=q[2];bool contains=valid&&q[1]<=reference&&q[2]>=reference;enclosed[w]+=contains;invalid+=!valid;
   ti<<std::setprecision(17)<<(w==0?"ramsey":"circuit")<<','<<i;for(double z:v)ti<<','<<z;ti<<','<<q[0]<<','<<q[1]<<','<<q[2]<<','<<reference<<','<<int(contains)<<'\n';
  }}
 std::cout<<"TINC inclusion against double reference: Ramsey "<<enclosed[0]<<"/12, circuit "<<enclosed[1]<<"/12, invalid="<<invalid<<"; graph setup="<<tincSetup<<" ms\n";
 std::cout<<"Scientific caveat: this pointwise test does not certify rigorous interval arithmetic. Run the bundled 100-digit reference check.\n";
 std::cout<<"Saved "<<o.csv<<" and "<<dir<<"tinc_samples.csv\n";
 ensure(failed==0,"numerical comparisons outside tolerance: "+std::to_string(failed));ensure(invalid==0,"invalid TINC intervals");return 0;
 }catch(const std::exception &e){std::cerr<<"ERROR: "<<e.what()<<"\n";return 1;}}
