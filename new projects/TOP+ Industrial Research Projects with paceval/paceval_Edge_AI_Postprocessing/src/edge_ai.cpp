// paceval Edge-AI Postprocessing Research -- demonstrator (C++17)
//
// PURPOSE AND LIMITATIONS
//   This is an OFFLINE numerical proof of feasibility. The three input traces
//   are *synthetic precomputed inference outputs*, not actual measurements or
//   results from an ONNX, OpenVINO or LiteRT model. Nothing here trains or
//   executes a neural network, and the score is not a calibrated probability.
//
// RESPONSIBILITIES
//   paceval: 50 separately versioned scalar scoring expressions + their 50
//            threshold-margin expressions, batch/multi-graph evaluation,
//            and two optional pointwise TINC-enabled graphs.
//   C++ host: CSV ingestion, input envelope, formula version manifest,
//             threshold / EMA / hysteresis decisions, test oracle and export.
//
// INTEGRATION
//   The ORIGINAL vendor SDK paceval_main.h/.cpp is compiled directly into this
//   application and linked against an externally supplied Linux .so. No
//   handwritten ABI, dlopen/dlsym adapter, REST or MCP protocol is involved.
//
// NUMERICS
//   Variables and output layouts are explicit; all comparisons are checked.
//   Selected TINC results are independently audited by Python with mpmath.
//   Pointwise enclosure on test cases is NOT a general mathematical warranty.

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
#include <set>
#include <sstream>
#include <stdexcept>
#include <string>
#include <vector>

namespace edge {
namespace fs = std::filesystem;
constexpr std::size_t NV = 8;
constexpr std::size_t NF = 50;
constexpr double EMA_ALPHA = 0.25;
constexpr double HYSTERESIS = 0.025;
// Crucial contract: the order below is used in the CSV, native reference,
// high-precision reference, and every paceval execution graph.
static constexpr const char* VARIABLE_NAMES = "p1 p2 x quality a b eps threshold";
enum Col {P1,P2,X,QUALITY,A,B,EPS,THRESHOLD};
using Values = std::array<double,NV>;
struct Sample {std::string trace; std::size_t step=0; Values v{};};
struct Formula {std::string id; int family=0; int revision=0; double weight=0; std::string expr,margin;};
struct Result {double score=0,margin=0,ema=0; int state=0;};
struct Audit {std::size_t n=0, failed=0; double max_abs=0;
    void compare(double value,double reference){
        ++n; double e=std::abs(value-reference);
        max_abs=std::max(max_abs,e);
        if(!std::isfinite(value) || e>3e-11*(1+std::max(std::abs(reference),std::abs(value)))) ++failed;
    }
};
void require(bool valid,const std::string& msg) {if(!valid) throw std::runtime_error(msg);}

// Simple CSV deliberately prohibits quoted commas and whitespace in IDs.
// The example data are machine-generated; failing closed is preferable to
// silently changing the semantics of an edge inference trace.
std::vector<std::string> cells(const std::string& s){
    std::vector<std::string> out; std::istringstream in(s);std::string token;
    while(std::getline(in,token,',')) { if(!token.empty() && token.back()=='\r') token.pop_back(); out.push_back(token); }
    return out;
}
double parse(const std::string& s){
    std::size_t idx=0;double val=0;
    try{val=std::stod(s,&idx);}catch(...){throw std::runtime_error("Invalid numeric token: "+s);}
    require(idx==s.size() && std::isfinite(val),"Invalid or nonfinite number: "+s);
    return val;
}
int parse_int(const std::string& s){
    std::size_t idx=0;int val=0;
    try{val=std::stoi(s,&idx);}catch(...){throw std::runtime_error("Invalid integer: "+s);}
    require(idx==s.size(),"Invalid integer token"); return val;
}
void check_domain(const Values& v){
    for(double z:v)require(std::isfinite(z),"Nonfinite inference input");
    require(v[P1]>=0 && v[P1]<=1 && v[P2]>=0 && v[P2]<=1,"Model channels must be in [0,1]");
    require(v[X]>=-4 && v[X]<=4,"Normalized feature x is outside [-4,4]");
    require(v[QUALITY]>=0 && v[QUALITY]<=1,"Quality is outside [0,1]");
    require(v[A]>=0 && v[A]<=0.3 && v[B]>=0.1 && v[B]<=2.5,"Calibration parameters out of domain");
    require(v[EPS]>=0.001 && v[EPS]<=0.05,"Regularizer eps outside [0.001,0.05]");
    require(v[THRESHOLD]>=-0.25 && v[THRESHOLD]<=1.5,"Threshold outside [-0.25,1.5]");
    require(v[P1]+v[P2]+v[EPS]>=0.001,"Denominator cannot be zero");
}
// family 0 is the exact illustrative formula of the supplied whitepaper,
// when the weight is zero. Families 1..4 add explicitly delimited domain
// corrections. These terms are synthetic stress-test choices, not validated
// quality-calibration methods for a particular network or sensor.
std::string family_term(int family){
    switch(family){
    case 0:return "quality-0.5";
    case 1:return "(p1-p2)*quality";
    case 2:return "x^2/(1+x^2)";
    case 3:return "(p1-p2)^2";
    case 4:return "sin(x)*quality";
    }
    throw std::runtime_error("Unsupported formula family");
}
std::string score_expression(int family,double weight){
    const std::string base="p1/(p1+p2+eps)+a*tanh(b*x)";
    if(weight==0)return base;
    std::ostringstream os;os<<std::fixed<<std::setprecision(9)<<weight;
    return base+"+("+os.str()+")*("+family_term(family)+")";
}
std::vector<Formula> read_catalog(const fs::path& path){
    std::ifstream in(path);require(in.good(),"Cannot read formula manifest: "+path.string());
    std::vector<Formula> forms;std::string line;std::set<std::string> ids;
    while(std::getline(in,line)){
        if(line.empty()||line[0]=='#'||line.rfind("version_id,",0)==0)continue;
        auto f=cells(line);require(f.size()==4,"Manifest must have four columns");
        Formula v;v.id=f[0];v.family=parse_int(f[1]);v.revision=parse_int(f[2]);v.weight=parse(f[3]);
        require(!v.id.empty() && v.id.find_first_of(" /\\,\t\r") == std::string::npos,"Invalid version ID");
        require(ids.insert(v.id).second,"Duplicate formula version ID");
        require(v.family>=0&&v.family<=4&&v.revision>=0&&v.revision<=9,"Unsupported formula family or revision");
        require(v.weight>=0&&v.weight<=0.1,"Formula weight is outside the audited interval");
        v.expr=score_expression(v.family,v.weight);
        v.margin="("+v.expr+")-threshold";
        forms.push_back(v);
    }
    require(forms.size()==NF,"Exactly 50 versioned formulas are required in this reference pilot");
    return forms;
}
std::vector<Sample> read_traces(const fs::path& dir,std::size_t limit_per_trace){
    std::vector<Sample> all;
    for(const std::string name:{"vision","vibration","thermal"}){
        fs::path path=dir/("trace_"+name+".csv");
        std::ifstream in(path);require(in.good(),"Cannot open required trace "+path.string());
        std::string line;std::size_t n=0;std::set<std::size_t> steps;
        while(n<limit_per_trace&&std::getline(in,line)){
            if(line.empty()||line[0]=='#'||line.rfind("trace_id,",0)==0)continue;
            auto c=cells(line);require(c.size()==10,"Trace must have trace_id,step,eight numeric columns");
            Sample s;s.trace=c[0];require(s.trace==name,"Trace name mismatch: "+name);
            const int step=parse_int(c[1]);require(step>=0&&static_cast<std::size_t>(step)==n,"Trace steps must start at 0 and be contiguous");
            s.step=static_cast<std::size_t>(step);require(steps.insert(s.step).second,"Duplicate step");
            for(std::size_t j=0;j<NV;++j)s.v[j]=parse(c[j+2]);
            check_domain(s.v);all.push_back(s);++n;
        }
        require(n>0,"Trace contains no rows: "+name);
    }
    return all;
}
double correction(int f,const Values&v){
    switch(f){
      case 0:return v[QUALITY]-0.5;
      case 1:return (v[P1]-v[P2])*v[QUALITY];
      case 2:return v[X]*v[X]/(1+v[X]*v[X]);
      case 3:return (v[P1]-v[P2])*(v[P1]-v[P2]);
      case 4:return std::sin(v[X])*v[QUALITY];
    }throw std::runtime_error("Invalid family");
}
// Independently implemented oracle: no paceval calls and no formula parsing.
double native_score(const Formula& f,const Values&v){
    return v[P1]/(v[P1]+v[P2]+v[EPS]) + v[A]*std::tanh(v[B]*v[X]) + f.weight*correction(f.family,v);
}
void native_self_test(){
    std::vector<Formula> f={{"base",0,0,0,"",""},{"correction",2,4,0.02,"",""}};
    Values v{{0,0,0,0.5,0.1,1.0,0.01,0.5}};check_domain(v);
    require(native_score(f[0],v)==0,"Zero-channel baseline identity failed");
    v[P1]=0.4;v[P2]=0.4;v[X]=0;
    require(std::abs(native_score(f[0],v)-0.4/0.81)<1e-15,"Normalization identity failed");
    v[X]=4;check_domain(v);require(std::isfinite(native_score(f[1],v)),"Extreme feature produced nonfinite score");
    v[P1]=-0.1;bool rejected=false;
    try{check_domain(v);}catch(...){rejected=true;}
    require(rejected,"Out-of-domain p1 not rejected");
    std::cout<<"PASS native self tests: zero channels, regularization, domain, finite extremes\n";
}
// RAII: computation objects outlive all batches, then are released in reverse
// creation order; the engine is freed LAST even if an exception is thrown.
class Runtime{
    bool initialized=false;
    std::vector<PACEVAL_HANDLE> owned;
public:
    Runtime(){require(paceval_InitializeLibrary(nullptr),"paceval_InitializeLibrary failed");initialized=true;}
    Runtime(const Runtime&)=delete;Runtime&operator=(const Runtime&)=delete;
    ~Runtime(){for(auto it=owned.rbegin();it!=owned.rend();++it)paceval_DeleteComputation(*it);
        if(initialized)paceval_FreeLibrary();}
    std::string error(PACEVAL_HANDLE h){char msg[PACEVAL_MAXERR+1]{};long pos=0;
        int code=paceval_GetErrorInformation(h,msg,&pos);
        return std::to_string(code)+" at "+std::to_string(pos)+" near "+msg;}
    PACEVAL_HANDLE make(const std::string& expr,bool interval=false){
        PACEVAL_HANDLE h=paceval_CreateComputation(expr.c_str(),static_cast<unsigned long>(NV),VARIABLE_NAMES,interval,nullptr);
        require(h!=nullptr,"Graph creation failed for: "+expr);owned.push_back(h);
        require(!paceval_GetIsError(h),"Invalid graph: "+error(h));return h;
    }
    // The SDK documents sample-major variables and GRAPH-MAJOR result arrays.
    // Return TRUE of the batch API denotes errors, NOT success.
    void batch(const std::vector<PACEVAL_HANDLE>& graphs,std::vector<double>&vars,
               std::size_t samples,std::vector<double>&results){
        require(vars.size()==samples*NV,"Unexpected input array size");
        auto mutable_graphs=graphs;
        results.assign(graphs.size()*samples,0.0);
        std::vector<int> errors(results.size(),-1);
        const bool failed=paceval_dGetMultipleComputationsResultsExt(
            mutable_graphs.data(),static_cast<unsigned long>(graphs.size()),vars.data(),
            static_cast<unsigned long>(samples),results.data(),nullptr,nullptr,errors.data());
        require(!failed,"paceval batch call reported an error");
        for(std::size_t k=0;k<results.size();++k)
            require(errors[k]==PACEVAL_ERR_NO_ERROR&&std::isfinite(results[k]),"Invalid batch result at index "+std::to_string(k));
        for(auto h:graphs)require(!paceval_GetIsError(h),"Graph runtime error: "+error(h));
    }
    std::array<double,3> interval(PACEVAL_HANDLE h,const Values&values){
        Values mutable_vars=values;double lo=0,hi=0;
        const double val=paceval_dGetComputationResult(h,mutable_vars.data(),&lo,&hi);
        require(!paceval_GetIsError(h),"Interval evaluation failed: "+error(h));
        require(std::isfinite(val)&&std::isfinite(lo)&&std::isfinite(hi)&&lo<=hi,"Malformed TINC response");
        return {{val,lo,hi}};
    }
};
struct HostState {double ema=0;bool initialized=false;int latched=0;};
Result apply_host(const Sample&s,double score,double margin,HostState&st){
    if(!st.initialized){st.ema=score;st.initialized=true;}else st.ema=EMA_ALPHA*score+(1-EMA_ALPHA)*st.ema;
    // Host-owned hysteresis: a *synthetic* alert proxy, never an actuator or
    // a calibrated safety decision. Do not give threshold logic to paceval.
    if(st.ema>=s.v[THRESHOLD]+HYSTERESIS)st.latched=1;
    else if(st.ema<=s.v[THRESHOLD]-HYSTERESIS)st.latched=0;
    return {score,margin,st.ema,st.latched};
}
void run(const std::vector<Sample>&data,const std::vector<Formula>&catalog,
         const fs::path&output,const fs::path&tinc_path,std::size_t batch_size){
    require(batch_size>=1&&batch_size<=65536,"Batch must be in [1,65536]");
    Runtime engine;
    std::vector<PACEVAL_HANDLE> graphs;graphs.reserve(2*catalog.size());
    for(const auto&f:catalog){graphs.push_back(engine.make(f.expr));graphs.push_back(engine.make(f.margin));}
    // TINC-enabled graphs are separate handles and are not reused as normal
    // outputs. No interval guarantee is inferred without independent audit.
    PACEVAL_HANDLE tin0=engine.make(catalog[0].expr,true);
    PACEVAL_HANDLE tin1=engine.make(catalog[35].margin,true);
    std::ofstream out(output);require(out.good(),"Cannot open score CSV output");
    out<<"trace_id,step,version_id,family,revision,weight,p1,p2,x,quality,a,b,eps,threshold,score,margin,ema,latched\n";
    out<<std::setprecision(17);
    std::map<std::string,HostState> states;Audit audit;
    // Samples are stored per trace in temporal order. Each formula version
    // owns an independent EMA/hysteresis state, never shared between traces.
    for(std::size_t start=0;start<data.size();start+=batch_size){
        const std::size_t n=std::min(batch_size,data.size()-start);
        std::vector<double> vars;vars.reserve(n*NV);
        for(std::size_t j=0;j<n;++j)for(double v:data[start+j].v)vars.push_back(v);
        std::vector<double> values;engine.batch(graphs,vars,n,values);
        for(std::size_t j=0;j<n;++j){
            const Sample&s=data[start+j];
            for(std::size_t k=0;k<catalog.size();++k){
                const Formula&f=catalog[k];
                // graph-major: [2*k] score, [2*k+1] margin, n samples each.
                double score=values[(2*k)*n+j],margin=values[(2*k+1)*n+j];
                double reference=native_score(f,s.v);
                audit.compare(score,reference);audit.compare(margin,reference-s.v[THRESHOLD]);
                HostState&state=states[s.trace+"/"+f.id];
                auto r=apply_host(s,score,margin,state);
                out<<s.trace<<','<<s.step<<','<<f.id<<','<<f.family<<','<<f.revision<<','<<f.weight;
                for(double v:s.v)out<<','<<v;
                out<<','<<r.score<<','<<r.margin<<','<<r.ema<<','<<r.state<<'\n';
            }
        }
    }
    require(audit.failed==0,"Verification failed for "+std::to_string(audit.failed)+" mathematical outputs");
    require(out.good(),"Failed to complete score output");out.close();
    std::ofstream tin(tinc_path);require(tin.good(),"Cannot open TINC CSV output");
    tin<<"trace_id,step,version_id,kind,family,revision,weight,p1,p2,x,quality,a,b,eps,threshold,value,lower,upper\n";
    tin<<std::setprecision(17);
    for(std::size_t j=0;j<24;++j){
        const auto& sample=data[(j*data.size())/24];
        bool margin=(j%2==1);std::size_t k=margin?35:0;
        auto interval=engine.interval(margin?tin1:tin0,sample.v);
        tin<<sample.trace<<','<<sample.step<<','<<catalog[k].id<<','<<(margin?"margin":"score")<<',';
        tin<<catalog[k].family<<','<<catalog[k].revision<<','<<catalog[k].weight;
        for(double v:sample.v)tin<<','<<v;
        tin<<','<<interval[0]<<','<<interval[1]<<','<<interval[2]<<'\n';
    }
    require(tin.good(),"Failed to complete TINC output");
    std::cout<<"PASS edge-ai feasibility: "<<data.size()<<" synthetic trace rows, "<<catalog.size()
             <<" versioned score graphs, "<<catalog.size()<<" margin graphs, 2 TINC graphs\n";
    std::cout<<"PASS native C++ reference: "<<audit.n<<" mathematical comparisons, "<<audit.failed
             <<" tolerance violations, max absolute difference "<<std::setprecision(10)<<audit.max_abs<<'\n';
    std::cout<<"EXPORTED "<<output<<" and "<<tinc_path<<"\n";
}
} // namespace edge

int main(int argc,char**argv){
    try{
        namespace fs=std::filesystem;
        fs::path catalog="../examples/formulas.csv",traces="../examples",output="scores.csv",tinc="tinc_samples.csv";
        std::size_t batch=64,limit=96;
        for(int i=1;i<argc;++i){std::string arg=argv[i];
            if(arg=="--self-test"){edge::native_self_test();return 0;}
            edge::require(i+1<argc,"Missing argument for "+arg);
            const std::string val=argv[++i];
            if(arg=="--catalog")catalog=val;
            else if(arg=="--traces")traces=val;
            else if(arg=="--output")output=val;
            else if(arg=="--tinc")tinc=val;
            else if(arg=="--batch")batch=static_cast<std::size_t>(std::stoul(val));
            else if(arg=="--limit")limit=static_cast<std::size_t>(std::stoul(val));
            else throw std::runtime_error("Unknown option: "+arg);
        }
        edge::require(limit>=1,"--limit must be positive");
        const auto formulas=edge::read_catalog(catalog);
        const auto input=edge::read_traces(traces,limit);
        edge::run(input,formulas,output,tinc,batch);
        return 0;
    }catch(const std::exception&e){std::cerr<<"ERROR: "<<e.what()<<'\n';return 2;}
}
