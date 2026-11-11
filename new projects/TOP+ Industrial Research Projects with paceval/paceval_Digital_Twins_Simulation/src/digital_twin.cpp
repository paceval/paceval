// paceval Digital Twins Research: verified thermal digital-twin demonstrator.
// All temperatures are K, time s, heat flows W, conductances W/K,
// thermal capacitances J/K. No real plant or FMI certification is claimed.
// C++17: build with CMake. The paceval binary is supplied externally.
#include <algorithm>
#include <array>
#include <cmath>
#include <cstdint>
#include <cstdlib>
#include "paceval_main.h"
#include <fstream>
#include <iomanip>
#include <iostream>
#include <limits>
#include <memory>
#include <sstream>
#include <stdexcept>
#include <string>
#include <vector>

namespace twin {
using Values = std::array<double,12>;
static constexpr size_t NV = 12;
static constexpr const char* VARIABLES = "t1 t2 tamb power c1 c2 k12 h1 h2 krad gain offset";
// An analytically soluble 1-state thermal system (work package A).
static constexpr const char* SINGLE = "(power-h1*(t1-tamb))/c1";
// Two coupled thermal states, one nonlinear thermal-loss term (work package B).
static constexpr const char* RHS1 = "(power-k12*(t1-t2)-h1*(t1-tamb))/c1";
// Nonlinear fourth-power heat loss is a synthetic surrogate. Temperatures
// MUST be Kelvin, because the 300 K normalization is dimensioned.
static constexpr const char* RHS2 = "(k12*(t1-t2)-h2*(t2-tamb)-krad*((t2/300)^4-(tamb/300)^4))/c2";
// A reusable mathematical sensor adapter and independent energy-balance component.
static constexpr const char* SENSOR = "gain*t2+offset";
static constexpr const char* LOSS2 = "h2*(t2-tamb)+krad*((t2/300)^4-(tamb/300)^4)";

void need(bool condition,const std::string &msg){if(!condition)throw std::runtime_error(msg);}
struct Scenario{std::string id; Values x;};
struct Derivative {double a,b;};
struct State {double t1,t2;};
struct Audit {size_t count=0,fail=0;double largest=0.;void compare(double actual,double expected,double tol=3e-9){
 ++count;double scale=1.+std::max(std::abs(actual),std::abs(expected));double err=std::abs(actual-expected);
 largest=std::max(largest,err);if(!std::isfinite(actual)||err>tol*scale)++fail;
 }};

static double one_rhs(const Values&v){return (v[3]-v[7]*(v[0]-v[2]))/v[4];}
static double nonlinear_loss(const Values&v){return v[8]*(v[1]-v[2])+v[9]*(std::pow(v[1]/300.,4)-std::pow(v[2]/300.,4));}
static double sensor(const Values&v){return v[10]*v[1]+v[11];}
static Derivative two_rhs(const Values&v){double coupling=v[6]*(v[0]-v[1]);
 return {(v[3]-coupling-v[7]*(v[0]-v[2]))/v[4],(coupling-nonlinear_loss(v))/v[5]};}
static double exact_one(const Values&v,double time){need(v[7]>0&&v[4]>0,"thermal parameters must be positive");
 double equilibrium=v[2]+v[3]/v[7];return equilibrium+(v[0]-equilibrium)*std::exp(-v[7]*time/v[4]);}
static double energy_residual(const Values&v,const Derivative &d){
 return v[4]*d.a+v[5]*d.b-(v[3]-v[7]*(v[0]-v[2])-nonlinear_loss(v));}
static Values set_state(Values v,State s){v[0]=s.t1;v[1]=s.t2;return v;}
static bool near(double a,double b,double rel=2e-11){return std::abs(a-b)<=rel*(1.+std::max(std::abs(a),std::abs(b)));}
static Scenario reference_scenario(){return {"analytic_reference",Values{{293.15,293.15,293.15,100.,500.,650.,4.,5.,2.,8.,1.0,0.0}}};}
static bool check_values(const Values&v){for(double x:v)if(!std::isfinite(x))return false;
 return v[0]>200&&v[1]>200&&v[2]>200&&v[0]<700&&v[1]<700&&v[2]<700
   &&v[4]>0&&v[5]>0&&v[6]>=0&&v[7]>0&&v[8]>=0&&v[9]>=0&&v[10]>0;}
static std::vector<Scenario> read_csv(const std::string &file,size_t limit){
 std::ifstream in(file);need(in.good(),"cannot open scenario CSV "+file);
 std::string line;std::vector<Scenario> scenarios;size_t lineno=0;
 while(std::getline(in,line)&&scenarios.size()<limit){++lineno;if(line.empty()||line[0]=='#')continue;
 std::vector<std::string> f;std::istringstream stream(line);std::string field;
 while(std::getline(stream,field,','))f.push_back(field);
 if(!f.empty()&&f[0]=="scenario_id")continue;
 need(f.size()==NV+1,"expected 13 CSV fields at line "+std::to_string(lineno));
 Scenario row;row.id=f[0];need(!row.id.empty(),"empty scenario ID");
 for(size_t k=0;k<NV;++k){size_t used=0;try{row.x[k]=std::stod(f[k+1],&used);}catch(...){throw std::runtime_error("invalid numerical field at line "+std::to_string(lineno));}
 need(used==f[k+1].find_last_not_of(" \r\t")+1,"invalid numeric token at line "+std::to_string(lineno));}
 need(check_values(row.x),"physical parameter validation failed at line "+std::to_string(lineno));
 scenarios.push_back(row);
 }
 need(!scenarios.empty(),"CSV has no scenarios");return scenarios;
}
static std::vector<Scenario> synthetic(size_t n){std::vector<Scenario> r;r.reserve(n);
 for(size_t k=0;k<n;++k){auto s=reference_scenario();s.id="synthetic_"+std::to_string(k);
 s.x[0]=291.+double(k%9)*2.4;s.x[1]=293.+double(k%7)*1.6;
 s.x[2]=289.+double(k%5)*1.2;s.x[3]=60.+double(k%13)*8.;
 s.x[4]=450.+double(k%11)*35.;s.x[5]=550.+double(k%13)*25.;
 s.x[6]=3.+double(k%6)*0.5;s.x[7]=4.+double(k%9)*0.4;
 s.x[8]=1.5+double(k%5)*0.25;s.x[9]=4.+double(k%7)*0.8;
 s.x[10]=0.995+0.0005*double(k%9);s.x[11]=double(k%7)*0.02;
 r.push_back(s);
 }return r;
}

// The host owns integration, state updates, and checks. paceval supplies only
// the explicit mathematical right-hand sides via the same callback interface.
using BatchRhs = void(*)(void*,const std::vector<Scenario>&,const std::vector<State>&,std::vector<Derivative>&);
static void native_batch(void*,const std::vector<Scenario>&models,const std::vector<State>&states,std::vector<Derivative>&out){
 need(models.size()==states.size(),"native batch size mismatch");out.resize(states.size());
 for(size_t i=0;i<states.size();++i)out[i]=two_rhs(set_state(models[i].x,states[i]));
}
// Classical fourth-order Runge--Kutta, independent of the expression engine.
// One "stage" evaluates the two mathematical derivatives over every model
// scenario. The same integrator works with either the native or paceval batch
// callback; paceval is not claimed to integrate ODEs or manage FMU events.
static void rk4_step(void*context,BatchRhs rhs,const std::vector<Scenario>&scenarios,std::vector<State>&state,double dt){
 const size_t n=state.size();std::vector<Derivative> k1,k2,k3,k4;std::vector<State> tmp(n);
 rhs(context,scenarios,state,k1);
 for(size_t i=0;i<n;++i){tmp[i]={state[i].t1+0.5*dt*k1[i].a,state[i].t2+0.5*dt*k1[i].b};}
 rhs(context,scenarios,tmp,k2);
 for(size_t i=0;i<n;++i){tmp[i]={state[i].t1+0.5*dt*k2[i].a,state[i].t2+0.5*dt*k2[i].b};}
 rhs(context,scenarios,tmp,k3);
 for(size_t i=0;i<n;++i){tmp[i]={state[i].t1+dt*k3[i].a,state[i].t2+dt*k3[i].b};}
 rhs(context,scenarios,tmp,k4);
 for(size_t i=0;i<n;++i){state[i].t1+=dt*(k1[i].a+2*k2[i].a+2*k3[i].a+k4[i].a)/6.;
 state[i].t2+=dt*(k1[i].b+2*k2[i].b+2*k3[i].b+k4[i].b)/6.;
 need(std::isfinite(state[i].t1)&&std::isfinite(state[i].t2),"nonfinite state during integration");}
}
static std::vector<State> simulate(void*context,BatchRhs rhs,const std::vector<Scenario>&s,size_t steps,double dt){
 std::vector<State> state;state.reserve(s.size());for(auto &x:s)state.push_back({x.x[0],x.x[1]});
 for(size_t i=0;i<steps;++i) {
  rk4_step(context,rhs,s,state,dt);
 }
 return state;
}
// Separate implementation of one-state RK4 used for the analytic reference.
static double integrate_one(const Values&x,int steps,double dt){double t=x[0];
 auto f=[&](double temperature){Values v=x;v[0]=temperature;return one_rhs(v);};
 for(int i=0;i<steps;++i){double k1=f(t),k2=f(t+0.5*dt*k1),k3=f(t+0.5*dt*k2),k4=f(t+dt*k3);
 t+=dt*(k1+2*k2+2*k3+k4)/6.;}return t;}
static void self_tests(){auto s=reference_scenario();double expected=exact_one(s.x,600);
 need(near(expected,313.100424365568,3e-5),"analytic smoke test");
 double rk4=integrate_one(s.x,600,1.0);need(std::abs(rk4-expected)<1e-8,"one-zone RK4 vs closed form");
 auto r=two_rhs(s.x);need(std::abs(energy_residual(s.x,r))<1e-10,"two-zone first law identity");
 auto cases=synthetic(24);
 for(auto&x:cases){auto deriv=two_rhs(x.x);need(std::abs(energy_residual(x.x,deriv))<1e-10,"energy balance identity");
 need(sensor(x.x)>200,"sensor validity");}
 auto a=simulate(nullptr,native_batch,cases,120,2.0);
 auto b=simulate(nullptr,native_batch,cases,240,1.0);
 for(size_t i=0;i<cases.size();++i){need(near(a[i].t1,b[i].t1,1e-9)&&near(a[i].t2,b[i].t2,1e-9),"RK4 step-halving convergence");}
 std::cout<<"PASS native self-tests: analytic 1-state, 2-zone energy balance, parameter validation, 24-scenario RK4 convergence\n";
}

// ---------------------------------------------------------------------------
// Vendor API integration (paceval SDK 4.25)
//
// The supplied paceval_main.h declares the stable C/C++ functions and
// paceval_main.cpp forwards them to the linked paceval Linux shared library.
// CMake compiles both translation units and links libpaceval_linux_sharedLIB.so.
// No dlopen/dlsym, handwritten ABI signatures, or duplicated vendor API are
// needed here. The SDK source is included with its original license notice.
//
// Graph lifecycle is managed by this RAII class. Every created handle is
// deleted BEFORE paceval_FreeLibrary is invoked. Exceptions cannot leave
// a partially created collection of graphs allocated.
// ---------------------------------------------------------------------------
class Paceval {
    std::vector<PACEVAL_HANDLE> owned_;
    bool initialized_ = false;
public:
    Paceval() {
        need(paceval_InitializeLibrary(nullptr),
             "paceval_InitializeLibrary failed: verify the linked Linux runtime");
        initialized_ = true;
    }
    Paceval(const Paceval&) = delete;
    Paceval& operator=(const Paceval&) = delete;

    ~Paceval() {
        // Reverse creation order is a conservative dependency-safe policy.
        for (auto it = owned_.rbegin(); it != owned_.rend(); ++it)
            paceval_DeleteComputation(*it);
        if (initialized_) paceval_FreeLibrary();
    }

    std::string error(PACEVAL_HANDLE graph) const {
        char token[PACEVAL_MAXERR + 1]{};
        long position = 0;
        const int code = paceval_GetErrorInformation(graph, token, &position);
        return "paceval code " + std::to_string(code) +
               " at expression position " + std::to_string(position) +
               " near '" + token + "'";
    }

    PACEVAL_HANDLE graph(const char* formula, bool use_tinc = false) {
        // One 12-variable declaration is shared by ALL graphs; unused variables
        // are permitted. This is required for multi-graph batch evaluation.
        PACEVAL_HANDLE handle = paceval_CreateComputation(
            formula, static_cast<unsigned long>(NV), VARIABLES, use_tinc, nullptr);
        need(handle != nullptr, std::string("paceval_CreateComputation returned null for: ") + formula);
        owned_.push_back(handle);  // Always own handles before a later check can throw.
        need(!paceval_GetIsError(handle), std::string("graph creation: ") + error(handle));
        return handle;
    }

    void evaluate(PACEVAL_HANDLE handle, std::vector<double>& input, size_t count,
                  std::vector<double>& output, std::vector<int>& errors,
                  std::vector<double>* lower = nullptr,
                  std::vector<double>* upper = nullptr) {
        need(input.size() == count * NV, "paceval batch input size does not match variables");
        output.resize(count);
        errors.resize(count);
        if (lower) lower->resize(count);
        if (upper) upper->resize(count);
        // Input layout: [scenario0 variables 0..11, scenario1 variables 0..11, ...].
        // The API's boolean return reports a failure; per-result error codes
        // must be checked independently (documented by the SDK header).
        const bool api_error = paceval_dGetComputationResultExt(
            handle, input.data(), static_cast<unsigned long>(count), output.data(),
            lower ? lower->data() : nullptr,
            upper ? upper->data() : nullptr, errors.data());
        need(!api_error, "paceval single-graph batch failure: " + error(handle));
        for (size_t i = 0; i < count; ++i)
            need(errors[i] == PACEVAL_ERR_NO_ERROR && std::isfinite(output[i]),
                 "paceval batch result invalid at scenario " + std::to_string(i));
        need(!paceval_GetIsError(handle), "paceval batch graph failure: " + error(handle));
    }

    void evaluate_multi(const std::vector<PACEVAL_HANDLE>& handles,
                        std::vector<double>& input, size_t count,
                        std::vector<double>& output, std::vector<int>& errors) {
        need(!handles.empty(), "paceval needs at least one graph");
        need(input.size() == count * NV, "paceval multi-graph input size mismatch");
        // paceval output is GRAPH-MAJOR: output[g * count + scenario].
        // All graphs must use the same variables in the same order.
        std::vector<PACEVAL_HANDLE> mutable_handles = handles;
        output.resize(count * handles.size());
        errors.resize(output.size());
        const bool api_error = paceval_dGetMultipleComputationsResultsExt(
            mutable_handles.data(), static_cast<unsigned long>(handles.size()),
            input.data(), static_cast<unsigned long>(count), output.data(),
            nullptr, nullptr, errors.data());
        need(!api_error, "paceval multi-graph batch API failure");
        for (size_t i = 0; i < output.size(); ++i)
            need(errors[i] == PACEVAL_ERR_NO_ERROR && std::isfinite(output[i]),
                 "paceval multi-graph result invalid at index " + std::to_string(i));
        for (PACEVAL_HANDLE h : handles)
            need(!paceval_GetIsError(h), "paceval graph failure: " + error(h));
    }

    std::array<double, 3> interval(PACEVAL_HANDLE handle, Values variables) {
        double lower = 0.0, upper = 0.0;
        // This call returns paceval's *reported* TINC endpoints. Independent
        // high-precision inclusion testing is performed by a separate script.
        const double value = paceval_dGetComputationResult(
            handle, variables.data(), &lower, &upper);
        need(!paceval_GetIsError(handle), "paceval TINC evaluation: " + error(handle));
        need(std::isfinite(value) && std::isfinite(lower) &&
             std::isfinite(upper) && lower <= upper,
             "paceval returned invalid TINC endpoints");
        return {{value, lower, upper}};
    }
};
// PACEVAL_HANDLE is a macro expanding to void* (not a typedef). Each
// declarator must therefore be spelled separately, or later names become void.
struct Graphs {
    PACEVAL_HANDLE one = nullptr;
    PACEVAL_HANDLE rhs1 = nullptr;
    PACEVAL_HANDLE rhs2 = nullptr;
    PACEVAL_HANDLE sensor = nullptr;
    PACEVAL_HANDLE loss = nullptr;
    PACEVAL_HANDLE tinc0 = nullptr;
    PACEVAL_HANDLE tinc1 = nullptr;
    PACEVAL_HANDLE tinc2 = nullptr;
};
struct Engine {Paceval api;Graphs g;std::vector<double>inputs,outputs;std::vector<int>errors;
 Engine(){g.one=api.graph(SINGLE);g.rhs1=api.graph(RHS1);g.rhs2=api.graph(RHS2);
 g.sensor=api.graph(SENSOR);g.loss=api.graph(LOSS2);g.tinc0=api.graph(SINGLE,true);
 g.tinc1=api.graph(RHS1,true);g.tinc2=api.graph(RHS2,true);}
 void fill(const std::vector<Scenario>&scenarios,const std::vector<State>&states){need(scenarios.size()==states.size(),"input size mismatch");
 inputs.resize(scenarios.size()*NV);for(size_t i=0;i<scenarios.size();++i){auto v=set_state(scenarios[i].x,states[i]);
 std::copy(v.begin(),v.end(),inputs.begin()+i*NV);}}
 void calc(const std::vector<Scenario>&scenarios,const std::vector<State>&states,std::vector<Derivative>&out){
 fill(scenarios,states);api.evaluate_multi({g.rhs1,g.rhs2},inputs,scenarios.size(),outputs,errors);
 size_t n=states.size();out.resize(n);for(size_t i=0;i<n;++i)out[i]={outputs[i],outputs[n+i]};}
};
static void paceval_batch(void*context,const std::vector<Scenario>&models,const std::vector<State>&states,std::vector<Derivative>&out){
 auto*p=static_cast<Engine*>(context);p->calc(models,states,out);
}
static void validate_single(Engine&e,const std::vector<Scenario>&scenarios,Audit&a){
 // Compare analytic one-state solutions after integrating the exact same math.
 std::vector<double>in(scenarios.size()*NV),out;std::vector<int>err;
 for(size_t i=0;i<scenarios.size();++i)std::copy(scenarios[i].x.begin(),scenarios[i].x.end(),in.begin()+i*NV);
 e.api.evaluate(e.g.one,in,scenarios.size(),out,err);
 for(size_t i=0;i<scenarios.size();++i)a.compare(out[i],one_rhs(scenarios[i].x));
 // One-state RK4 calls the reusable paceval graph at every RK stage.
 auto one_step=[&](const Values&v,double dt,size_t steps){double state=v[0];std::vector<double>input(NV);std::vector<double>out1;std::vector<int>er;
 auto one_derivative=[&](double t){Values x=v;x[0]=t;std::copy(x.begin(),x.end(),input.begin());e.api.evaluate(e.g.one,input,1,out1,er);return out1[0];};
 for(size_t k=0;k<steps;++k){double k1=one_derivative(state);double k2=one_derivative(state+dt*k1*0.5);
 double k3=one_derivative(state+dt*k2*0.5);double k4=one_derivative(state+dt*k3);
 state+=dt*(k1+2*k2+2*k3+k4)/6.;}
 return state;};
 for(size_t i=0;i<std::min(size_t(3),scenarios.size());++i){auto&x=scenarios[i].x;double value=one_step(x,2.,180);
 a.compare(value,exact_one(x,360.),5e-10);}
}
static void validate_auxiliary(Engine&e,const std::vector<Scenario>&scenarios,Audit&a){
 std::vector<State>state;for(auto&s:scenarios)state.push_back({s.x[0],s.x[1]});e.fill(scenarios,state);
 e.api.evaluate_multi({e.g.rhs1,e.g.rhs2,e.g.sensor,e.g.loss},e.inputs,scenarios.size(),e.outputs,e.errors);
 size_t n=scenarios.size();for(size_t i=0;i<n;++i){auto &x=scenarios[i].x;auto d=two_rhs(x);
 a.compare(e.outputs[i],d.a);a.compare(e.outputs[n+i],d.b);
 a.compare(e.outputs[2*n+i],sensor(x));a.compare(e.outputs[3*n+i],nonlinear_loss(x));
 auto computed=Derivative{e.outputs[i],e.outputs[n+i]};a.compare(energy_residual(x,computed),0.,2e-9);}
}
// Export the vendor's pointwise TINC outputs WITHOUT fabricating interval
// guarantees. src/high_precision_reference.py checks the saved binary64 inputs
// against 110-digit arithmetic and intentionally reports two non-enclosures.
static void export_tinc(Engine&e,const std::vector<Scenario>&s,const std::string&file){
 std::ofstream out(file);need(out.good(),"cannot create TINC CSV: "+file);
 out<<"case_id,formula,t1,t2,tamb,power,c1,c2,k12,h1,h2,krad,gain,offset,paceval_result,tinc_lower,tinc_upper\n";
 out<<std::setprecision(17);
 struct Info{const char*name;PACEVAL_HANDLE h;double(*reference)(const Values&);};
 auto r1=[](const Values&v)->double{return two_rhs(v).a;};auto r2=[](const Values&v)->double{return two_rhs(v).b;};
 const Info forms[]={{"single",e.g.tinc0,one_rhs},{"two_rhs1",e.g.tinc1,r1},{"two_rhs2",e.g.tinc2,r2}};
 size_t count=0;for(const auto&form:forms)for(size_t i=0;i<8;++i){Values v=s[i%s.size()].x;
 // Add several boundary-like but physically plausible test temperatures.
 if(i%3==1){v[0]=v[2]+0.0000001*(i+1);v[1]=v[2]-0.0000001*(i+1);}
 auto bounds=e.api.interval(form.h,v);double exactish=form.reference(v);
 need(bounds[1]<=exactish+1e-10&&bounds[2]>=exactish-1e-10,"unexpected interval vs C++ reference");
 out<<count++<<','<<form.name;for(double q:v)out<<','<<q;
 out<<','<<bounds[0]<<','<<bounds[1]<<','<<bounds[2]<<'\n';
 }
 std::cout<<"TINC sample file: "<<file<<" (24 intervals; independent reference script validates enclosure)\n";
}
// Persist final states from independent native and paceval-backed RK4 runs.
// CSVs enable validation with SciPy's adaptive DOP853 integrator.
static void write_trajectories(const std::string &path,const std::vector<Scenario>&s,
 const std::vector<State>&native,const std::vector<State>&paced,size_t steps,double dt){
 std::ofstream out(path);need(out.good(),"cannot create CSV output: "+path);
 out<<"scenario_id,time_s,native_T1_K,native_T2_K,paceval_T1_K,paceval_T2_K,paceval_sensor_K,energy_balance_residual_W\n";
 out<<std::setprecision(17);for(size_t i=0;i<s.size();++i){Values v=set_state(s[i].x,paced[i]);
 out<<s[i].id<<','<<steps*dt<<','<<native[i].t1<<','<<native[i].t2<<','<<paced[i].t1<<','<<paced[i].t2<<','<<sensor(v)<<','<<energy_residual(v,two_rhs(v))<<'\n';}
}
struct Options{std::string inputs,output="trajectories.csv",tinc="tinc_samples.csv";
 size_t scenarios=32,steps=180;double dt=2.;bool self=false;};
static Options parse(int argc,char**argv){Options o;for(int i=1;i<argc;++i){std::string name=argv[i];
 auto val=[&](){need(i+1<argc,"missing value after "+name);return std::string(argv[++i]);};
 if(name=="--input-csv")o.inputs=val();
 else if(name=="--output-csv")o.output=val();else if(name=="--tinc-csv")o.tinc=val();
 else if(name=="--scenarios")o.scenarios=std::stoul(val());else if(name=="--steps")o.steps=std::stoul(val());
 else if(name=="--dt")o.dt=std::stod(val());else if(name=="--self-test")o.self=true;
 
 else if(name=="--help"){std::cout<<"digital_twin [--self-test] [--input-csv scenarios.csv] [--scenarios N] [--steps N] [--dt seconds] [--output-csv file] [--tinc-csv file]\n";std::exit(0);}
 else throw std::runtime_error("unknown argument: "+name);}
 need(o.scenarios>=1&&o.scenarios<=10000&&o.steps>=1&&o.steps<=10000&&std::isfinite(o.dt)&&o.dt>0&&o.dt<=20,"invalid simulation limits");return o;}
}
int main(int argc,char**argv){try{using namespace twin;Options o=parse(argc,argv);self_tests();if(o.self)return 0;
 auto cases=o.inputs.empty()?synthetic(o.scenarios):read_csv(o.inputs,o.scenarios);
 std::cout<<"Digital Twins / mathematical feasibility demonstrator; scenarios="<<cases.size()
 <<" steps="<<o.steps<<" dt="<<o.dt<<" s\n";
 // The SDK adapter and external vendor runtime are linked at build time.
 Engine engine;Audit a;
 validate_single(engine,cases,a);validate_auxiliary(engine,cases,a);
 auto native=simulate(nullptr,native_batch,cases,o.steps,o.dt);
 auto paced=simulate(&engine,paceval_batch,cases,o.steps,o.dt);
 for(size_t i=0;i<cases.size();++i){a.compare(paced[i].t1,native[i].t1,1e-8);a.compare(paced[i].t2,native[i].t2,1e-8);}
 // Demonstrate reuse over parameter sweeps, without rebuilding graphs.
 for(int sweep=0;sweep<5;++sweep){auto varied=cases;
 for(auto&x:varied){x.x[3]*=0.8+0.1*sweep;x.x[8]*=1.+0.025*sweep;}
 auto ref=simulate(nullptr,native_batch,varied,std::min(size_t(30),o.steps),o.dt);
 auto run=simulate(&engine,paceval_batch,varied,std::min(size_t(30),o.steps),o.dt);
 for(size_t i=0;i<varied.size();++i){a.compare(run[i].t1,ref[i].t1,1e-8);a.compare(run[i].t2,ref[i].t2,1e-8);}}
 need(cases.size()>=1,"scenario list must not be empty");export_tinc(engine,cases,o.tinc);
 write_trajectories(o.output,cases,native,paced,o.steps,o.dt);
 std::cout<<"PASS real paceval: 5 reusable expression graphs + 3 TINC graphs, batch/multi-graph RHS,"
 <<" 5 parameter variations, RK4 trajectories, sensor and heat balance\n";
 std::cout<<"Audit: "<<a.count<<" comparisons; failures="<<a.fail<<"; largest absolute difference="<<std::setprecision(12)<<a.largest<<"\n";
 need(a.fail==0,"numerical audit detected failures");std::cout<<"PASS Digital Twins feasibility experiment\n";
 return 0;
 }catch(const std::exception&e){std::cerr<<"ERROR: "<<e.what()<<'\n';return 1;}}
