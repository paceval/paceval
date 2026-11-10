// paceval Industrial Control Research: offline constrained finite-control-set MPC.
//
// SCIENTIFIC SCOPE
//  * Synthetic dimensionless plant (NOT a production industrial controller).
//  * paceval evaluates eight explicit mathematical graphs, batched across many
//    candidate actions and reused at every predictive horizon and time step.
//  * A C++ beam-search optimizer, constraints, disturbance model, scenario
//    scheduling, and CSV are HOST logic; paceval is the mathematical evaluator.
//  * The solver is deliberately approximate (beam search). No claim of global
//    MPC optimality, hard real-time scheduling, certified numerical enclosures,
//    plant safety, or physical calibration is implied by this demonstrator.
//
// ORIGINAL PACEVAL SDK
// This translation unit includes paceval_main.h. CMake also compiles the
// accompanying paceval_main.cpp and links the separately supplied Linux .so.
// No hand-written ABI, dlsym wrapper, network request, or replacement library.
#include "paceval_main.h"
#include <algorithm>
#include <array>
#include <cmath>
#include <cstddef>
#include <cstdlib>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <limits>
#include <sstream>
#include <stdexcept>
#include <string>
#include <utility>
#include <vector>

namespace research {
constexpr std::size_t NV = 14;
constexpr std::size_t NG = 8;
using Values = std::array<double,NV>;

enum Index { X, U, UPREV, TARGET, A, B, D, C, Q, RU, SLEW, XLIM, UMAX, DUMAX };
static constexpr const char* VARIABLES =
    "x u uprev target a b d c q ru slew xlim umax dumax";
static constexpr std::array<const char*,NG> NAMES = {{
    "next_state", "tracking_cost", "actuation_cost", "slew_cost",
    "state_margin", "actuation_margin", "slew_margin", "transition_sensitivity"
}};
// Each graph has exactly the same ordered variable declaration. A graph can
// ignore a variable without changing the shared multi-graph input schema.
static constexpr std::array<const char*,NG> EXPRESSIONS = {{
    "a*x+b*u+d+c*x^3",
    "q*(a*x+b*u+d+c*x^3-target)^2",
    "ru*u^2",
    "slew*(u-uprev)^2",
    "xlim^2-(a*x+b*u+d+c*x^3)^2",
    "umax^2-u^2",
    "dumax^2-(u-uprev)^2",
    "a+3*c*x^2"
}};

void check(bool ok,const std::string&why) { if(!ok)throw std::runtime_error(why); }
struct Scenario {
    std::string name;
    double x0, target, a,b,d,c,q,ru,slew,xlim,umax,dumax;
};
struct ModelResult { std::array<double,NG> v{}; };
struct Audit {
    std::size_t compared=0, failed=0;
    double max_abs=0.0;
    void test(double observed,double reference,const std::string&context) {
        ++compared;
        const double delta=std::abs(observed-reference);
        max_abs=std::max(max_abs,delta);
        if(!std::isfinite(observed)||delta>8e-11*(1.0+std::abs(reference))) {
            ++failed;
            if(failed<=4) std::cerr<<"DIFFERENCE "<<context<<" got="<<observed
                <<" ref="<<reference<<"\n";
        }
    }
};

// The discrete plant is a synthetic weakly nonlinear stable process. The
// disturbance d is an additive input (dimensionless) and held constant over
// each finite prediction horizon. The controlled physical plant is simulated
// solely inside the program; there is no actuator interface.
Values parameters(double x,double u,double uprev,const Scenario&s,double disturbance) {
    return Values{{x,u,uprev,s.target,s.a,s.b,disturbance,s.c,s.q,s.ru,
                   s.slew,s.xlim,s.umax,s.dumax}};
}
ModelResult native(const Values&p) {
    const double nx=p[A]*p[X]+p[B]*p[U]+p[D]+p[C]*p[X]*p[X]*p[X];
    const double du=p[U]-p[UPREV];
    ModelResult r;
    r.v={{nx,p[Q]*(nx-p[TARGET])*(nx-p[TARGET]),p[RU]*p[U]*p[U],
          p[SLEW]*du*du,p[XLIM]*p[XLIM]-nx*nx,
          p[UMAX]*p[UMAX]-p[U]*p[U],p[DUMAX]*p[DUMAX]-du*du,
          p[A]+3.0*p[C]*p[X]*p[X]}};
    return r;
}
void validate(const Scenario&s) {
    check(!s.name.empty(),"Empty scenario ID");
    const std::array<double,12> xs={{s.x0,s.target,s.a,s.b,s.d,s.c,s.q,s.ru,
                                     s.slew,s.xlim,s.umax,s.dumax}};
    for(double v:xs)check(std::isfinite(v),"Non-finite parameter in "+s.name);
    check(s.xlim>0.5&&s.xlim<=5.0&&std::abs(s.x0)<s.xlim,
          "Invalid state envelope: "+s.name);
    check(s.umax==1.0 && s.dumax==0.5,
          "This demonstrated finite-action grid requires umax=1 and dumax=0.5");
    check(s.a>0.7&&s.a<1.0&&s.b>0.1&&s.b<0.4&&std::abs(s.c)<0.1,
          "Unverified synthetic dynamic coefficients");
    check(s.q>0&&s.ru>=0&&s.slew>=0&&std::abs(s.target)<s.xlim,
          "Invalid objective or reference");
    check(std::abs(s.d)<0.1,"Synthetic disturbance too large");
}
std::vector<Scenario> scenarios_from_csv(const std::string&path) {
    std::ifstream f(path);check(bool(f),"Cannot open scenario CSV: "+path);
    std::string line;std::size_t line_no=0;std::vector<Scenario> out;
    while(std::getline(f,line)) {
        ++line_no; if(line.empty()||line[0]=='#')continue;
        std::istringstream in(line); std::string field;std::vector<std::string> fields;
        while(std::getline(in,field,','))fields.push_back(field);
        if(fields[0]=="scenario")continue;
        check(fields.size()==13,"Expected 13 CSV fields on line "+std::to_string(line_no));
        Scenario s;s.name=fields[0];std::array<double,12>v{};
        for(std::size_t i=0;i<v.size();++i) {
            std::size_t consumed=0;
            try {v[i]=std::stod(fields[i+1],&consumed);}catch(...) {
                throw std::runtime_error("Invalid number at CSV line "+std::to_string(line_no));
            }
            check(consumed==fields[i+1].size(),"Unexpected numeric suffix on CSV line "+std::to_string(line_no));
        }
        s.x0=v[0];s.target=v[1];s.a=v[2];s.b=v[3];s.d=v[4];s.c=v[5];
        s.q=v[6];s.ru=v[7];s.slew=v[8];s.xlim=v[9];s.umax=v[10];s.dumax=v[11];
        validate(s);out.push_back(s);
    }
    check(!out.empty(),"No scenarios in CSV");
    return out;
}

// Native-only independent self-tests: numerical differentiation checks the
// explicitly derived paceval sensitivity expression; check identities also
// exercise all three quadratic costs and their zero points.
void self_test() {
    const auto all=scenarios_from_csv(std::string(EXAMPLE_SCENARIOS));
    for(const auto&s:all)for(int j=0;j<100;++j) {
        const double x=-0.65+1.3*j/99.0,u=-1+2.0*(j%7)/6.0;
        const Values p=parameters(x,u,0.5,s,s.d);
        const auto r=native(p);
        for(double z:r.v)check(std::isfinite(z),"Non-finite analytic self-test output");
        const double h=1e-6;
        auto a=p,b=p;a[X]+=h;b[X]-=h;
        const double difference=(native(a).v[0]-native(b).v[0])/(2*h);
        check(std::abs(difference-r.v[7])<2e-9,"Analytical transition derivative mismatch");
        check(std::abs(r.v[4]-(s.xlim*s.xlim-r.v[0]*r.v[0]))<1e-12,
              "State-envelope identity failed");
    }
    check(std::abs(native(parameters(0,0,0,all[0],0)).v[2])<1e-14,
          "Zero actuation-cost identity failed");
    std::cout<<"PASS independent native analytical tests: "<<all.size()*100
             <<" samples, derivative and constraint identities\n";
}

// RAII ensures graph destruction always precedes paceval library shutdown.
class Paceval {
    bool initialized_=false;
    std::vector<PACEVAL_HANDLE> allocated_;
public:
    Paceval(){check(paceval_InitializeLibrary(nullptr),"paceval_InitializeLibrary failed");initialized_=true;}
    Paceval(const Paceval&)=delete;
    Paceval&operator=(const Paceval&)=delete;
    ~Paceval(){for(auto it=allocated_.rbegin();it!=allocated_.rend();++it)paceval_DeleteComputation(*it);
        if(initialized_)paceval_FreeLibrary();}
    std::string detail(PACEVAL_HANDLE h) {
        char token[PACEVAL_MAXERR+1]{};long position=0;
        int code=paceval_GetErrorInformation(h,token,&position);
        return std::to_string(code)+" near '"+token+"' at "+std::to_string(position);
    }
    PACEVAL_HANDLE create(const char*formula,bool tinc=false) {
        PACEVAL_HANDLE h=paceval_CreateComputation(formula,(unsigned long)NV,VARIABLES,tinc,nullptr);
        check(h!=nullptr,std::string("Cannot create paceval graph: ")+formula);
        allocated_.push_back(h);
        check(!paceval_GetIsError(h),"Graph analysis failure: "+detail(h));
        return h;
    }
    // Layout contract: sample-major double input [candidate][14 variables],
    // graph-major double output [graph][candidate]. Errors are one per output.
    void multi(const std::vector<PACEVAL_HANDLE>&handles,
               const std::vector<Values>&inputs,std::vector<ModelResult>&outputs,
               Audit&audit) {
        check(!inputs.empty(),"Empty multi-graph input");
        std::vector<double> packed;packed.reserve(inputs.size()*NV);
        for(const Values&p:inputs)for(double x:p)packed.push_back(x);
        std::vector<PACEVAL_HANDLE> hs=handles; // API expects a mutable pointer.
        std::vector<double> raw(handles.size()*inputs.size(),0.0);
        std::vector<int> errors(raw.size(),-1);
        const bool bad=paceval_dGetMultipleComputationsResultsExt(hs.data(),
            (unsigned long)hs.size(),packed.data(),(unsigned long)inputs.size(),
            raw.data(),nullptr,nullptr,errors.data());
        check(!bad,"Multi-graph paceval API returned failure");
        outputs.assign(inputs.size(),ModelResult{});
        for(std::size_t j=0;j<inputs.size();++j) {
            const auto reference=native(inputs[j]);
            for(std::size_t g=0;g<handles.size();++g) {
                const std::size_t idx=g*inputs.size()+j;
                check(errors[idx]==PACEVAL_ERR_NO_ERROR,
                    "Per-output paceval error "+std::to_string(errors[idx]));
                outputs[j].v[g]=raw[idx];
                audit.test(raw[idx],reference.v[g],NAMES[g]);
            }
        }
        for(PACEVAL_HANDLE h:handles)check(!paceval_GetIsError(h),"Runtime graph error "+detail(h));
    }
    std::array<double,3> interval(PACEVAL_HANDLE h,const Values&p) {
        Values copy=p;double low=0,high=0;
        double result=paceval_dGetComputationResult(h,copy.data(),&low,&high);
        check(!paceval_GetIsError(h),"TINC graph error "+detail(h));
        check(std::isfinite(result)&&std::isfinite(low)&&std::isfinite(high)&&low<=high,
              "Invalid TINC endpoints");
        return {{result,low,high}};
    }
};

struct Branch { double x=0,u_prev=0,first_u=0,cost=0,rank=0; };
static constexpr std::array<double,5> ACTIONS={{-1.0,-0.5,0.0,0.5,1.0}};
struct ControlDecision {double u=0, horizon_cost=0;};

// Host-owned approximate search over an explicitly finite input set.
// This is NOT a substitution for acados/CasADi differentiation or a certified
// nonlinear programming solver. Each tree level sends ALL generated branch
// input vectors to paceval's *multi-graph batch API* for evaluation.
ControlDecision optimize(Paceval&engine,const std::vector<PACEVAL_HANDLE>&graphs,
                         const Scenario&s,double x,double previous,double disturbance,
                         std::size_t horizon,std::size_t beam,std::size_t batch,
                         Audit&audit) {
    std::vector<Branch> frontier(1);frontier[0].x=x;frontier[0].u_prev=previous;
    for(std::size_t depth=0;depth<horizon;++depth) {
        std::vector<Values> inputs;
        struct Parent {std::size_t index;double u;};
        std::vector<Parent> parent;
        for(std::size_t i=0;i<frontier.size();++i)for(double u:ACTIONS) {
            if(std::abs(u-frontier[i].u_prev)>s.dumax+1e-12)continue;
            inputs.push_back(parameters(frontier[i].x,u,frontier[i].u_prev,s,disturbance));
            parent.push_back({i,u});
        }
        check(!inputs.empty(),"No admissible predicted input candidates");
        std::vector<Branch> expanded;
        for(std::size_t offset=0;offset<inputs.size();offset+=batch) {
            const std::size_t n=std::min(batch,inputs.size()-offset);
            std::vector<Values> window(inputs.begin()+offset,inputs.begin()+offset+n);
            std::vector<ModelResult> output;engine.multi(graphs,window,output,audit);
            for(std::size_t j=0;j<n;++j) {
                const auto&r=output[j].v;
                // Explicit paceval graph results make the feasibility decision.
                // C++ owns threshold policy, branch selection and scheduling.
                if(r[4]<-1e-11||r[5]<-1e-11||r[6]<-1e-11)continue;
                const auto& par=parent[offset+j];const auto& prev=frontier[par.index];
                Branch z;z.x=r[0];z.u_prev=par.u;
                z.first_u=(depth==0?par.u:prev.first_u);
                z.cost=prev.cost+r[1]+r[2]+r[3];
                // Host heuristic is used only to choose a manageable beam.
                z.rank=z.cost + 0.25*s.q*(z.x-s.target)*(z.x-s.target);
                expanded.push_back(z);
            }
        }
        check(!expanded.empty(),"All candidates violate the synthetic operating envelope");
        std::sort(expanded.begin(),expanded.end(),[](const Branch&a,const Branch&b){
            if(a.rank!=b.rank)return a.rank<b.rank;
            if(a.cost!=b.cost)return a.cost<b.cost;
            return a.first_u<b.first_u;
        });
        if(expanded.size()>beam)expanded.resize(beam);
        frontier.swap(expanded);
    }
    // Final selection minimizes the actual accumulated stage cost, not the
    // pruning heuristic. Beam search does not guarantee a global optimum.
    const auto it=std::min_element(frontier.begin(),frontier.end(),
        [](const Branch&a,const Branch&b){return a.cost<b.cost;});
    return {it->first_u,it->cost};
}

// Small-horizon independent exhaustive oracle: for horizon=3 and beam=512
// there are fewer reachable sequences than the beam limit, so no pruning is
// needed. This verifies that the paceval-driven host search finds the same
// minimum accumulated cost as an independently implemented native solver.
double exhaustive_native(const Scenario&s,double x,double prev,double d,int remaining) {
    if(remaining==0)return 0.0;
    double best=std::numeric_limits<double>::infinity();
    for(double u:ACTIONS) {
        if(std::abs(u-prev)>s.dumax+1e-12)continue;
        const auto r=native(parameters(x,u,prev,s,d)).v;
        if(r[4]<-1e-11||r[5]<-1e-11||r[6]<-1e-11)continue;
        best=std::min(best,r[1]+r[2]+r[3]+exhaustive_native(s,r[0],u,d,remaining-1));
    }
    return best;
}
void oracle_test(const std::vector<Scenario>&scenarios) {
    Paceval engine;std::vector<PACEVAL_HANDLE> h;
    for(const char*formula:EXPRESSIONS)h.push_back(engine.create(formula));
    Audit audit;
    for(const auto&s:scenarios) {
        const double d=s.d+0.011;
        const auto paceval_result=optimize(engine,h,s,s.x0,0.0,d,3,512,128,audit);
        const double reference=exhaustive_native(s,s.x0,0.0,d,3);
        check(std::isfinite(reference),"No feasible native exhaustive path");
        check(std::abs(reference-paceval_result.horizon_cost)<2e-10,
              "Paceval finite-set MPC disagrees with exhaustive native optimum");
    }
    check(audit.failed==0,"paceval numerical mismatch in optimizer oracle test");
    std::cout<<"PASS independent exhaustive 3-step search oracle for "
             <<scenarios.size()<<" scenarios; "<<audit.compared
             <<" mathematical graph comparisons\n";
}

// Disturbance series is deterministic, bounded and deliberately synthetic.
// The same value is supplied to the predictive model for one horizon, while
// the next closed-loop control iteration receives the next measurement.
double disturbance_at(const Scenario&s,std::size_t k) {
    return s.d+0.017*std::sin(0.37*double(k))+0.009*std::cos(0.13*double(k));
}
struct TincRow{std::string scenario;std::size_t step=0;Values input{};};

void run(const std::vector<Scenario>&scenarios,std::size_t steps,std::size_t horizon,
         std::size_t beam,std::size_t batch,const std::string&outpath,
         const std::string&tincpath) {
    Paceval engine;
    std::vector<PACEVAL_HANDLE> graphs;
    for(const char*expression:EXPRESSIONS)graphs.push_back(engine.create(expression));
    PACEVAL_HANDLE state_iv=engine.create("ru*u^2",true);
    PACEVAL_HANDLE margin_iv=engine.create("q*x^2",true);
    Audit audit;
    std::ofstream csv(outpath);check(bool(csv),"Cannot open output CSV");
    csv<<"scenario,step,x_before,target,control,disturbance,x_after,tracking_cost,"
        <<"actuation_cost,slew_cost,state_margin,actuation_margin,slew_margin,"
        <<"sensitivity,predicted_horizon_cost,zero_input_reference_x\n";
    csv<<std::setprecision(17);
    std::vector<TincRow> audit_samples;
    std::size_t violations=0;
    for(const auto&s:scenarios) {
        double x=s.x0,previous=0,reference_x=s.x0;
        for(std::size_t k=0;k<steps;++k) {
            const double disturbance=disturbance_at(s,k);
            const auto pick=optimize(engine,graphs,s,x,previous,disturbance,
                                     horizon,beam,batch,audit);
            const Values p=parameters(x,pick.u,previous,s,disturbance);
            std::vector<ModelResult> output;engine.multi(graphs,{p},output,audit);
            const auto&r=output.front().v;
            if(r[4]<-1e-11||r[5]<-1e-11||r[6]<-1e-11)++violations;
            // The zero-input trajectory is a mathematical reference, not a
            // safety assertion or a speed/performance comparison.
            const double zero_next= s.a*reference_x+disturbance+s.c*reference_x*reference_x*reference_x;
            csv<<s.name<<","<<k<<","<<x<<","<<s.target<<","<<pick.u<<","<<disturbance;
            for(double value:r)csv<<","<<value;
            csv<<","<<pick.horizon_cost<<","<<zero_next<<"\n";
            if((k%3)==0)audit_samples.push_back({s.name,k,p});
            x=r[0];previous=pick.u;reference_x=zero_next;
        }
        std::cout<<"Scenario "<<s.name<<" concluded x="<<x<<" target="<<s.target<<"\n";
    }
    check(bool(csv),"Failed to flush output CSV");
    check(violations==0,"Synthetic hard constraints violated");
    check(audit.failed==0,"paceval differs from independent C++ reference");

    // The TINC exercise evaluates 24 pointwise cases across the actual
    // closed-loop trajectory; a high-precision script independently checks
    // both the numerical output and the claimed interval endpoints.
    check(!audit_samples.empty(),"No TINC samples");
    std::ofstream tinc(tincpath);check(bool(tinc),"Cannot open TINC CSV");
    tinc<<"scenario,step,graph";
    {std::istringstream names(VARIABLES);std::string name;while(names>>name)tinc<<","<<name;}
    tinc<<",paceval_result,tinc_lower,tinc_upper\n"<<std::setprecision(17);
    for(std::size_t i=0;i<24;++i) {
        const auto&row=audit_samples[(i*audit_samples.size())/24];
        const bool dyn=(i%2==0);
        const auto vals=engine.interval(dyn?state_iv:margin_iv,row.input);
        tinc<<row.scenario<<","<<row.step<<","<<(dyn?"actuation_cost":"quadratic_state_energy");
        for(double v:row.input)tinc<<","<<v;
        tinc<<","<<vals[0]<<","<<vals[1]<<","<<vals[2]<<"\n";
    }
    check(bool(tinc),"Failed to write TINC CSV");
    std::cout<<"PASS offline original-paceval MPC: "<<scenarios.size()<<" scenarios x "
             <<steps<<" steps, "<<NG<<" normal and 2 TINC graphs, "
             <<audit.compared<<" independent C++ comparisons, "
             <<audit.failed<<" numerical mismatches, "<<violations<<" constraint violations\n";
}
} // namespace research

int main(int argc,char**argv) {
    try {
        std::string scenarios=EXAMPLE_SCENARIOS;
        std::string output="trajectory.csv",tinc="tinc_samples.csv";
        std::size_t steps=36,horizon=6,beam=24,batch=256;
        bool self=false,oracle=false;
        for(int i=1;i<argc;++i) {
            const std::string arg=argv[i];
            if(arg=="--self-test")self=true;
            else if(arg=="--oracle-test")oracle=true;
            else {
                research::check(i+1<argc,"Missing value after "+arg);
                const std::string v=argv[++i];
                if(arg=="--scenarios-csv")scenarios=v;
                else if(arg=="--steps")steps=std::stoul(v);
                else if(arg=="--horizon")horizon=std::stoul(v);
                else if(arg=="--beam")beam=std::stoul(v);
                else if(arg=="--batch")batch=std::stoul(v);
                else if(arg=="--out-csv")output=v;
                else if(arg=="--tinc-csv")tinc=v;
                else throw std::runtime_error("Unknown argument "+arg);
            }
        }
        research::check(steps>=8&&steps<=500&&horizon>=1&&horizon<=12&&beam>=1&&beam<=4096&&batch>=1&&batch<=100000,
              "Requested parameters outside supported demonstrator limits");
        if(self)research::self_test();
        else if(oracle)research::oracle_test(research::scenarios_from_csv(scenarios));
        else research::run(research::scenarios_from_csv(scenarios),steps,horizon,beam,batch,output,tinc);
        return 0;
    }catch(const std::exception&e){std::cerr<<"FAIL "<<e.what()<<"\n";return 1;}
}
