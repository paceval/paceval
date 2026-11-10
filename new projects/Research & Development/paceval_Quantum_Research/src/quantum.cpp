// paceval Quantum Research: reproducible classical numerical demonstrator (C++17)
// Quantum hardware is not simulated as an accelerator. All computations are classical.
// Uses the original paceval_main.h/.cpp SDK implementation (API 4.25).
// The original Linux paceval runtime is linked externally at build time.
// No simulated paceval backend, manually resolved function pointers or speed claim.
// Copyright and AGPL notices for SDK files remain in those original sources.
#include <algorithm>
#include <array>
#include <chrono>
#include <cmath>
#include <cstdint>
#include <cstdlib>
#include <cstring>
#include "paceval_main.h"
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
struct Options{std::string csv="quantum_results.csv",input;size_t events=60000,batch=8192;bool selftest=false;};
static size_t positive(const std::string&x){size_t k=0;auto n=std::stoull(x,&k);ensure(k==x.size()&&n>0&&n<=2000000,"invalid positive integer: "+x);return(size_t)n;}
static Options parse(int argc,char**argv){Options o;for(int i=1;i<argc;++i){std::string x=argv[i];auto arg=[&](){ensure(i+1<argc,"missing argument: "+x);return std::string(argv[++i]);};
 if(x=="--events")o.events=positive(arg());else if(x=="--batch")o.batch=positive(arg());else if(x=="--csv")o.csv=arg();else if(x=="--input-csv")o.input=arg();else if(x=="--self-test")o.selftest=true;
 else if(x=="--help"){std::cout<<"Usage: quantum [--events 60000] [--batch 8192] [--input-csv file.csv] [--csv output.csv] [--self-test]\n";std::exit(0);}else throw std::runtime_error("unknown argument: "+x);
 }return o;}
// -----------------------------------------------------------------------------
// Official paceval SDK integration (v4.25)
//
// `paceval_main.h` declares typed functions. Its partner `paceval_main.cpp`
// forwards calls to the original `pacevalLibrary_*` entry points in the
// externally linked Linux .so. The forwarding source is not the engine itself.
//
// All graphs use exactly the same nine variables in the same order; this is
// mandatory for the multi-graph batch operation. The user-facing class owns
// every HANDLE and frees it *before* paceval_FreeLibrary() even on exceptions.
// Check both graph status and per-event batch errors; never infer correctness
// from merely receiving a finite number or from an API call returning false.
// -----------------------------------------------------------------------------
class Paceval {
    std::vector<PACEVAL_HANDLE> owned_;
    bool initialized_ = false;
public:
    Paceval() {
        ensure(paceval_InitializeLibrary(nullptr),
               "Original paceval runtime initialization failed (library/license)");
        initialized_ = true;
    }
    ~Paceval() {
        for (auto it = owned_.rbegin(); it != owned_.rend(); ++it)
            paceval_DeleteComputation(*it);
        if (initialized_) paceval_FreeLibrary();
    }
    Paceval(const Paceval&) = delete;
    Paceval& operator=(const Paceval&) = delete;

    std::string err(PACEVAL_HANDLE graph) const {
        char token[PACEVAL_MAXERR + 1]{};
        long pos = -1;
        int code = paceval_GetErrorInformation(graph, token, &pos);
        return "code="+std::to_string(code)+" token="+token+
               " pos="+std::to_string(pos);
    }
    PACEVAL_HANDLE graph(const std::string& expression, bool interval = false) {
        PACEVAL_HANDLE handle = paceval_CreateComputation(
            expression.c_str(), static_cast<unsigned long>(NV), VARS,
            interval, nullptr);
        ensure(handle != nullptr, "paceval_CreateComputation returned null for "+expression);
        owned_.push_back(handle); // Take ownership before error checking.
        ensure(!paceval_GetIsError(handle),
               "paceval graph construction failed: "+err(handle)+" formula="+expression);
        return handle;
    }
    void eval(PACEVAL_HANDLE graph, std::vector<double>& inputs, size_t count,
              std::vector<double>& outputs, std::vector<int>& errors) const {
        // Input ordering: event0 nine doubles; event1 nine doubles; ...
        ensure(count>0 && inputs.size()>=count*NV, "invalid paceval batch input");
        outputs.resize(count); errors.resize(count);
        const bool api_error = paceval_dGetComputationResultExt(
            graph, inputs.data(), static_cast<unsigned long>(count),
            outputs.data(), nullptr, nullptr, errors.data());
        ensure(!api_error, "paceval batch API error: "+err(graph));
        ensure(!paceval_GetIsError(graph), "paceval batch graph error: "+err(graph));
        for(size_t j=0;j<count;++j)
            ensure(errors[j]==0 && std::isfinite(outputs[j]),
                   "paceval batch failed for element "+std::to_string(j));
    }
    void evalMulti(std::vector<PACEVAL_HANDLE>& graphs,
                   std::vector<double>& inputs, size_t count,
                   std::vector<double>& outputs, std::vector<int>& errors) const {
        ensure(!graphs.empty() && count>0 && inputs.size()>=count*NV,
               "invalid paceval multi-graph input");
        outputs.resize(graphs.size()*count); errors.resize(graphs.size()*count);
        const bool api_error = paceval_dGetMultipleComputationsResultsExt(
            graphs.data(), static_cast<unsigned long>(graphs.size()),
            inputs.data(), static_cast<unsigned long>(count),
            outputs.data(), nullptr, nullptr, errors.data());
        ensure(!api_error, "paceval multi-graph batch API returned an error");
        // Outputs are graph-major: [g0 event0..eventN, g1 event0..eventN, ...].
        for(PACEVAL_HANDLE graph:graphs)
            ensure(!paceval_GetIsError(graph),
                   "paceval multi-graph status error: "+err(graph));
        for(size_t j=0;j<errors.size();++j)
            ensure(errors[j]==0 && std::isfinite(outputs[j]),
                   "paceval multi-graph output error at index "+std::to_string(j));
    }
    std::array<double,3> tinc(PACEVAL_HANDLE graph, const Sample& s) const {
        Sample input = s; // SDK expects mutable double[] not const double*.
        double lo = std::numeric_limits<double>::quiet_NaN();
        double hi = lo;
        const double value = paceval_dGetComputationResult(
            graph, input.data(), &lo, &hi);
        ensure(!paceval_GetIsError(graph), "paceval TINC evaluation failed: "+err(graph));
        ensure(std::isfinite(value) && std::isfinite(lo) && std::isfinite(hi) && lo<=hi,
               "paceval returned invalid TINC point interval");
        return {{value,lo,hi}};
    }
};
// Fixed-seed xorshift64* random source produces reproducible synthetic fixtures.
// No values are obtained from experimental superconducting quantum hardware.
static uint64_t rngNext(uint64_t &state){state^=state>>12;state^=state<<25;state^=state>>27;return state*UINT64_C(2685821657736338717);}
static double rnd(uint64_t&s){return (rngNext(s)>>11)*(1.0/9007199254740992.0);}
static Sample make_sample(size_t i,uint64_t &s){
 const double t=16*(double(i%2048)+0.2*rnd(s))/2048;Sample v{{t,0.9,8.0,0.37,0.32,0.,512.,-PI+2*PI*rnd(s),-PI+2*PI*rnd(s)}};
 // Deterministic synthetic counts; finite sampling, NOT a real quantum device measurement.
 std::mt19937_64 g(rngNext(s));std::binomial_distribution<int> bin((int)v[6],prob(v));v[5]=double(bin(g));return v;
}
// Read nine-column, dimensionally consistent input rows. The evaluation
// domain excludes exact p=0 or p=1 because the log-likelihood formula uses
// finite logarithms rather than a special boundary-limit implementation.
static std::vector<Sample> read_csv(const std::string &path,size_t limit){std::ifstream f(path);ensure((bool)f,"cannot open input CSV: "+path);std::vector<Sample>v;std::string line;size_t lineNum=0;
 while(std::getline(f,line)&&v.size()<limit){++lineNum;if(line.empty()||line[0]=='#')continue;
  if(line.rfind("t,contrast,tau,freq,phase,hits,trials,theta1,theta2",0)==0)continue;
  std::stringstream ss(line);std::string token;Sample row{};size_t j=0;
  while(std::getline(ss,token,',')){ensure(j<NV,"too many CSV columns at "+std::to_string(lineNum));size_t used=0;row[j]=std::stod(token,&used);ensure(used==token.find_last_not_of(" \t\r")+1&&std::isfinite(row[j]),"invalid CSV value "+std::to_string(lineNum));++j;}
  ensure(j==NV,"expected 9 CSV columns at "+std::to_string(lineNum));ensure(row[0]>=0&&row[1]>=0&&row[1]<=1&&row[2]>0&&row[6]>0&&row[5]>=0&&row[5]<=row[6],"invalid model domain in CSV");
  ensure(prob(row)>0&&prob(row)<1,"probability outside open (0,1) for log-likelihood; change input/model");v.push_back(row);
 }ensure(!v.empty(),"CSV has no input rows");return v;}
// Native controls are completely independent of paceval. In particular the
// CNOT calculation is based on four real amplitudes, not the Fourier identity.
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
// Internal CSV timings are retained only for engineering reproducibility.
// No speedup assertion is made in this feasibility report or the README.
static void record(std::ofstream &f,const std::string &kind,size_t events,size_t batch,double setup,double pack,double runtime,const Audit&a,double sum){f<<std::setprecision(15)<<kind<<','<<events<<','<<batch<<','<<setup<<','<<pack<<','<<runtime<<','<<a.n<<','<<a.fail<<','<<a.worstAbs<<','<<sum<<'\n';}
static void output(const std::string &name,double time,size_t failures=0){std::cout<<std::left<<std::setw(40)<<name<<std::fixed<<std::setprecision(4)<<std::setw(12)<<time<<" ms";if(failures)std::cout<<" FAIL="<<failures;std::cout<<"\n";}
int main(int argc,char**argv){try{
 auto o=parse(argc,argv);selftest();if(o.selftest)return 0;ensure(o.batch<=200000,"batch exceeds supported limit");
 std::vector<Sample>samples;if(!o.input.empty())samples=read_csv(o.input,o.events);else{uint64_t seed=20261110;samples.reserve(o.events);for(size_t i=0;i<o.events;++i)samples.push_back(make_sample(i,seed));}o.events=samples.size();
 std::cout<<"paceval Quantum Research / synthetic Ramsey calibration and analytical two-qubit Fourier models\n"<<"Events="<<o.events<<" batch="<<o.batch<<(o.input.empty()?" deterministic seed=20261110":" CSV="+o.input)<<"\n";
 // Calculate native C++ reference outputs independently. Internal diagnostic timings are not scientific speedup claims.
 std::vector<double>rP(o.events),rL(o.events),rD(o.events),rC(o.events),rF(o.events);std::ofstream csv(o.csv);ensure(csv.good(),"cannot write CSV: "+o.csv);
 csv<<"method,events,batch,setup_ms,pack_ms,eval_ms,compared,failures,max_absolute_error,checksum\n";Audit none;volatile double warm=0;for(size_t i=0;i<std::min(o.events,size_t(1000));++i)warm+=prob(samples[i])+nll(samples[i])+circuit(samples[i]);(void)warm;
 double nativeTime[5];double sums[5]{};std::vector<double>*ref[]={&rP,&rL,&rD,&rC,&rF};double(*fn[])(const Sample&)={prob,nll,deriv,circuit,fourier};
 const char*labels[]={"ramsey_probability","binomial_nll","ramsey_frequency_gradient","circuit_expectation","circuit_fourier"};
 for(int g=0;g<5;++g){auto begin=Clock::now();for(size_t i=0;i<o.events;++i)(*ref[g])[i]=fn[g](samples[i]);nativeTime[g]=ms(begin);sums[g]=std::accumulate(ref[g]->begin(),ref[g]->end(),0.0);record(csv,std::string("native_")+labels[g],o.events,o.batch,0,0,nativeTime[g],none,sums[g]);output(std::string("C++ ")+labels[g],nativeTime[g]);}
 Paceval engine;auto begin=Clock::now();std::vector<PACEVAL_HANDLE> h{engine.graph(RAMSEY),engine.graph(NLL),engine.graph(DERIV),engine.graph(CIRCUIT),engine.graph(FOURIER)};double setup=ms(begin);
 std::cout<<"Original paceval SDK/runtime linked; created 5 reusable expression graphs in "<<setup<<" ms\n";
 std::vector<double>input(o.batch*NV),work,multi;std::vector<int>errors;std::vector<PACEVAL_HANDLE>ramseyGraphs{h[0],h[1],h[2]};
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
 output("paceval_ramsey_multi_3_graphs",multiTime,amulti.fail);record(csv,"paceval_ramsey_multi_3_graphs",o.events,o.batch,setup,pack,multiTime,amulti,multiSum);failed+=amulti.fail;
 std::cout<<"Multi-graph path validated against independent reference outputs.\n";
 // Five fixed synthetic detuning hypotheses reuse the same likelihood graph.
 // Compare individual batches and flattened inputs for correctness, not performance.
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
 std::cout<<"Five frequency hypotheses validated without regenerating computation graphs.\n";
 // Separate pointwise TINC diagnostic. Independent 110-digit rechecking uses Python.
 begin=Clock::now();PACEVAL_HANDLE tRamsey=engine.graph(RAMSEY,true); PACEVAL_HANDLE tCircuit=engine.graph(CIRCUIT,true);double tincSetup=ms(begin);
 auto slash=o.csv.find_last_of("/\\");const std::string dir=slash==std::string::npos?std::string():o.csv.substr(0,slash+1);
 std::ofstream ti(dir+"tinc_samples.csv");ensure(ti.good(),"cannot write tinc_samples.csv");ti<<"formula,sample_index,t,contrast,tau,freq,phase,hits,trials,theta1,theta2,paceval_value,lower,upper,double_reference,contains_double\n";
 size_t enclosed[2]{};size_t invalid=0;for(int i=0;i<12;++i){Sample v=samples[(size_t(i)*o.events)/12];
  for(int w=0;w<2;++w){auto q=engine.tinc(w==0?tRamsey:tCircuit,v);double reference=w==0?prob(v):circuit_statevector(v[7],v[8]);bool valid=std::isfinite(q[1])&&std::isfinite(q[2])&&q[1]<=q[2];bool contains=valid&&q[1]<=reference&&q[2]>=reference;enclosed[w]+=contains;invalid+=!valid;
   ti<<std::setprecision(17)<<(w==0?"ramsey":"circuit")<<','<<i;for(double z:v)ti<<','<<z;ti<<','<<q[0]<<','<<q[1]<<','<<q[2]<<','<<reference<<','<<int(contains)<<'\n';
  }}
 std::cout<<"TINC inclusion against double reference: Ramsey "<<enclosed[0]<<"/12, circuit "<<enclosed[1]<<"/12, invalid="<<invalid<<"; graph setup="<<tincSetup<<" ms\n";
 std::cout<<"Scientific caveat: this pointwise test does not certify rigorous interval arithmetic. Run the bundled 110-digit reference check.\n";
 std::cout<<"Saved "<<o.csv<<" and "<<dir<<"tinc_samples.csv\n";
 ensure(failed==0,"numerical comparisons outside tolerance: "+std::to_string(failed));ensure(invalid==0,"invalid TINC intervals");return 0;
 }catch(const std::exception &e){std::cerr<<"ERROR: "<<e.what()<<"\n";return 1;}}
