// paceval Fusion Diagnostics Research (C++17)
// Copyright (c) 2026 paceval research demonstrator authors.
//
// PURPOSE: Offline proof-of-feasibility for mathematical submodels, not a
// physically calibrated fusion diagnostic and NOT a machine controller.
// All inputs/outputs are dimensionless synthetic normalized signals.
// paceval evaluates explicitly declared formulas; C++ owns CSV input,
// operating-envelope policy, test orchestration, and result export.
//
// The ORIGINAL paceval_main.h and paceval_main.cpp are part of this source
// directory and are compiled against an externally supplied vendor Linux .so.
// No dlopen, hand-written ABI, REST, or MCP is involved.
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
#include <vector>

namespace fusion {
constexpr std::size_t NV = 20;
constexpr std::size_t NG = 7;
using Values = std::array<double, NV>;
static constexpr const char* VARS =
    "i b di si sb target a0 a1 a2 a3 a4 b0 b1 b2 k c ilim blim kp kd";
static const std::array<const char*, NG> NAMES = {{
    "diagnostic", "nonlinear_surrogate", "gradient_current", "gradient_field",
    "propagated_sigma", "ellipse_margin", "advisory_signal"}};
// All expressions use exactly the same 20-variable schema. Derivative and
// propagated-uncertainty graphs represent mathematical checks, not new plasma
// physics.  The envelope is an illustrative normalized ellipse, NOT a safety
// boundary for a tokamak. The advisory signal is NEVER an actuator command.
static const std::array<const char*, NG> FORMULAS = {{
    "a0+a1*i+a2*b+a3*i*b+a4*b^2",
    "b0+b1*tanh(k*i)+b2*exp(-c*b^2)",
    "a1+a3*b",
    "a2+a3*i+2*a4*b",
    "sqrt((a1+a3*b)^2*si^2+(a2+a3*i+2*a4*b)^2*sb^2)",
    "1-(i/ilim)^2-(b/blim)^2",
    "kp*(target-(a0+a1*i+a2*b+a3*i*b+a4*b^2))-kd*di"}};

void require(bool ok, const std::string& message) {
    if (!ok) throw std::runtime_error(message);
}
struct Sample {std::string id; Values x;};
struct Result {std::array<double, NG> q{};};
struct Audit {std::size_t compared = 0, failed = 0; double max_abs = 0.0;
    void check(double observed, double expected, double atol = 2e-11) {
        ++compared;
        const double difference = std::abs(observed-expected);
        max_abs = std::max(max_abs,difference);
        if(!std::isfinite(observed) || difference > atol*(1+std::max(std::abs(expected),std::abs(observed)))) ++failed;
    }
};

// Variable order is contractual: CSV, graph creation, and high-precision
// reference all agree on these indices.
enum Index {I,B,DI,SI,SB,TARGET,A0,A1,A2,A3,A4,B0,B1,B2,K,C,ILIM,BLIM,KP,KD};
static bool valid(const Values&v) {
    for (double x : v) if (!std::isfinite(x)) return false;
    return std::abs(v[I])<=1 && std::abs(v[B])<=1 &&
        v[SI]>=0 && v[SB]>=0 && v[SI]<=0.1 && v[SB]<=0.1 &&
        v[ILIM]>0 && v[BLIM]>0 && v[K]>0 && v[C]>=0 && v[C]<=10 &&
        std::abs(v[K]*v[I])<12;
}
static Values base() {
    return Values{{0.1,0.1,0.02,0.005,0.006,0.2,
        0.1,0.38,-0.19,0.12,0.09,
        0.08,0.42,0.14,1.1,1.8,
        0.95,0.95,0.5,0.06}};
}
static std::vector<Sample> synthetic(std::size_t n) {
    std::vector<Sample> out;out.reserve(n);
    for(std::size_t t=0;t<n;++t){
        auto v=base(); const double z=double(t);
        v[I]=0.87*std::sin(0.081*z)+0.015*std::cos(0.35*z);
        v[B]=0.84*std::cos(0.057*z+0.35);
        v[DI]=0.07*std::cos(0.081*z);
        v[SI]=0.002+0.0005*double(t%13);
        v[SB]=0.003+0.00035*double(t%11);
        v[TARGET]=0.17+0.07*std::sin(0.023*z);
        // Coefficients vary deterministically to exercise graph reuse.
        v[A1]+=0.002*double(t%7);v[A3]-=0.001*double(t%5);
        v[B1]+=0.001*double(t%9);
        require(valid(v), "Internal synthetic case outside documented domain");
        out.push_back({"synthetic_"+std::to_string(t),v});
    }return out;
}
static std::vector<Sample> from_csv(const std::string &filename,std::size_t limit) {
    std::ifstream in(filename); require(in.good(),"Cannot read input CSV: "+filename);
    std::vector<Sample> out;std::string line;std::size_t line_no=0;
    while(std::getline(in,line) && out.size()<limit){
        ++line_no; if(line.empty()||line[0]=='#') continue;
        std::istringstream s(line);std::string f;std::vector<std::string> fields;
        while(std::getline(s,f,',')) fields.push_back(f);
        if(!fields.empty()&&fields[0]=="sample_id")continue;
        require(fields.size()==NV+1,"Expected 21 columns at input line "+std::to_string(line_no));
        Sample r;r.id=fields[0];require(!r.id.empty(),"Empty ID");
        for(std::size_t k=0;k<NV;++k){
            std::size_t consumed=0;
            try {r.x[k]=std::stod(fields[k+1],&consumed);} catch(...) {throw std::runtime_error("Invalid numeric value in input CSV");}
            require(consumed==fields[k+1].find_last_not_of(" \r\t")+1,"Trailing non-numeric CSV token");
        }
        require(valid(r.x),"Input sample is outside the synthetic model domain at line "+std::to_string(line_no));
        out.push_back(r);
    }
    require(!out.empty(),"CSV contains no samples");return out;
}
static Result native(const Values &v){
    const double i=v[I],b=v[B];Result r;
    r.q[0]=v[A0]+v[A1]*i+v[A2]*b+v[A3]*i*b+v[A4]*b*b;
    r.q[1]=v[B0]+v[B1]*std::tanh(v[K]*i)+v[B2]*std::exp(-v[C]*b*b);
    r.q[2]=v[A1]+v[A3]*b;
    r.q[3]=v[A2]+v[A3]*i+2*v[A4]*b;
    r.q[4]=std::sqrt(r.q[2]*r.q[2]*v[SI]*v[SI]+r.q[3]*r.q[3]*v[SB]*v[SB]);
    r.q[5]=1-std::pow(i/v[ILIM],2)-std::pow(b/v[BLIM],2);
    r.q[6]=v[KP]*(v[TARGET]-r.q[0])-v[KD]*v[DI];
    return r;
}
static void self_test(){
    auto s=synthetic(65);
    for(const auto& e:s){auto r=native(e.x); for(double q:r.q)require(std::isfinite(q),"Native reference not finite");
        // Finite difference derivative checks are intentionally independent
        // of the analytical gradient expressions supplied to paceval.
        constexpr double h=1e-6;
        auto a=e.x,b=e.x;a[I]+=h;b[I]-=h;
        require(std::abs((native(a).q[0]-native(b).q[0])/(2*h)-r.q[2])<2e-9,"d/di mismatch");
        a=e.x;b=e.x;a[B]+=h;b[B]-=h;
        require(std::abs((native(a).q[0]-native(b).q[0])/(2*h)-r.q[3])<2e-9,"d/db mismatch");
        require(r.q[4]>=0,"Invalid uncertainty");
    }
    auto v=base();v[I]=0.0;v[B]=0.0;
    require(std::abs(native(v).q[5]-1)<1e-15,"Envelope center is incorrect");
    v[I]=v[ILIM];v[B]=0.0; // This is outside valid input domain, but a valid algebraic identity.
    require(std::abs(native(v).q[5])<1e-15,"Envelope boundary identity is incorrect");
    std::cout<<"PASS native model tests: 65 cases, gradients, uncertainty, ellipse identity\n";
}

// Lifetime wrapper guarantees that all graph handles are released before
// paceval_FreeLibrary is called, including on exception paths.
class Paceval {
    std::vector<PACEVAL_HANDLE> owned_;
    bool initialized_=false;
public:
    Paceval(){require(paceval_InitializeLibrary(nullptr),"paceval_InitializeLibrary failed");initialized_=true;}
    Paceval(const Paceval&)=delete;Paceval& operator=(const Paceval&)=delete;
    ~Paceval(){for(auto it=owned_.rbegin();it!=owned_.rend();++it)paceval_DeleteComputation(*it);
        if(initialized_)paceval_FreeLibrary();}
    std::string error(PACEVAL_HANDLE h){char token[PACEVAL_MAXERR+1]{};long pos=0;
        const int code=paceval_GetErrorInformation(h,token,&pos);
        return std::to_string(code)+" (position "+std::to_string(pos)+", near "+token+")";}
    PACEVAL_HANDLE graph(const char* formula,bool tinc=false){
        PACEVAL_HANDLE h=paceval_CreateComputation(formula,static_cast<unsigned long>(NV),VARS,tinc,nullptr);
        require(h!=nullptr,std::string("Graph creation failed: ")+formula);owned_.push_back(h);
        require(!paceval_GetIsError(h),"paceval graph error "+error(h));return h;
    }
    // paceval multi-output layout is GRAPH-MAJOR [graph][sample]. Input is
    // SAMPLE-MAJOR [sample][variable], as documented by the 4.25 SDK.
    void multi(const std::vector<PACEVAL_HANDLE>& graphs,
               std::vector<double>&input,std::size_t count,
               std::vector<double>&out){
        require(input.size()==NV*count,"Multi-graph input size mismatch");
        std::vector<PACEVAL_HANDLE> mutable_graphs=graphs;
        out.assign(graphs.size()*count,0.0);std::vector<int> err(out.size(),-1);
        const bool bad=paceval_dGetMultipleComputationsResultsExt(mutable_graphs.data(),
            static_cast<unsigned long>(graphs.size()),input.data(),
            static_cast<unsigned long>(count),out.data(),nullptr,nullptr,err.data());
        require(!bad,"paceval multi-graph API reported failure");
        for(std::size_t k=0;k<out.size();++k)
            require(err[k]==PACEVAL_ERR_NO_ERROR&&std::isfinite(out[k]),"Invalid paceval result at index "+std::to_string(k));
        for(auto h:graphs)require(!paceval_GetIsError(h),"Graph runtime error "+error(h));
    }
    std::array<double,3> interval(PACEVAL_HANDLE h,const Values&x){
        auto local=x;double lo=0,hi=0;
        const double z=paceval_dGetComputationResult(h,local.data(),&lo,&hi);
        require(!paceval_GetIsError(h),"TINC graph error "+error(h));
        require(std::isfinite(lo)&&std::isfinite(hi)&&std::isfinite(z)&&lo<=hi,"Invalid TINC endpoints");
        return {{z,lo,hi}};
    }
};
static void write_outputs(const std::string &path,const std::vector<Sample>&cases,
                          const std::vector<Result>&all){
    std::ofstream f(path);require(f.good(),"Cannot write result CSV");
    f<<"sample_id";for(auto name:NAMES)f<<","<<name;
    f<<",host_envelope_flag\n";f<<std::setprecision(17);
    for(std::size_t k=0;k<cases.size();++k){f<<cases[k].id;
        for(double x:all[k].q)f<<","<<x;
        // Host-owned binary classification uses the synthetic envelope only;
        // it is deliberately NOT used to control any external hardware.
        f<<","<<(all[k].q[5]<0?"outside":"inside")<<"\n";
    }
    require(f.good(),"Cannot complete CSV output");
}
static void run(const std::vector<Sample>& cases,const std::string&output,
                const std::string&tinc_path,std::size_t batch){
    Paceval engine;std::vector<PACEVAL_HANDLE> graphs;
    for(auto f:FORMULAS)graphs.push_back(engine.graph(f));
    // Independently instantiated interval-enabled graphs, never presented
    // as rigorously certified enclosures without a reference audit.
    PACEVAL_HANDLE tinc_diag=engine.graph(FORMULAS[0],true);
    PACEVAL_HANDLE tinc_margin=engine.graph(FORMULAS[5],true);
    std::vector<Result> results(cases.size());Audit audit;
    for(std::size_t start=0;start<cases.size();start+=batch){
        std::size_t n=std::min(batch,cases.size()-start);
        std::vector<double> input;input.reserve(n*NV);
        for(std::size_t j=0;j<n;++j)for(double v:cases[start+j].x)input.push_back(v);
        std::vector<double> output_graph_major;engine.multi(graphs,input,n,output_graph_major);
        for(std::size_t j=0;j<n;++j){
            auto ref=native(cases[start+j].x);
            for(std::size_t g=0;g<NG;++g){
                double z=output_graph_major[g*n+j];audit.check(z,ref.q[g]);results[start+j].q[g]=z;
            }
        }
    }
    require(audit.failed==0,"A numerical result differs from the independent C++ reference");
    write_outputs(output,cases,results);
    std::ofstream f(tinc_path);require(f.good(),"Cannot write TINC CSV");
    f<<"sample_id,formula";std::istringstream names(VARS);std::string name;
    while(names>>name)f<<","<<name;
    f<<",paceval_result,tinc_lower,tinc_upper\n"<<std::setprecision(17);
    // 24 total pointwise samples (12 diagnostic, 12 envelope). Samples are
    // deliberately spread through the available synthetic input list.
    for(std::size_t k=0;k<24;++k){
        const auto& sample=cases[(k*cases.size())/24];
        const bool diag=(k%2==0);const auto iv=engine.interval(diag?tinc_diag:tinc_margin,sample.x);
        f<<sample.id<<','<<(diag?"diagnostic":"ellipse_margin");
        for(double v:sample.x)f<<","<<v;
        f<<","<<iv[0]<<","<<iv[1]<<","<<iv[2]<<"\n";
    }
    require(f.good(),"Cannot finish TINC CSV");
    std::cout<<"PASS real paceval execution: "<<cases.size()<<" synthetic/CSV inputs, "
             <<NG<<" ordinary graphs + 2 TINC graphs, "<<audit.compared
             <<" independent numerical comparisons, 0 tolerance failures\n";
    std::cout<<"Maximum observed absolute difference: "<<std::setprecision(8)<<audit.max_abs<<"\n";
    std::cout<<"Wrote "<<output<<" and "<<tinc_path<<"\n";
}
} // namespace fusion

int main(int argc,char**argv){
    try {
        std::string input,output="fusion_results.csv",tinc="fusion_tinc.csv";
        std::size_t samples=256,batch=128;bool self=false;
        for(int i=1;i<argc;++i){std::string flag=argv[i];
            auto arg=[&](){if(i+1>=argc)throw std::runtime_error("Missing argument for "+flag);return std::string(argv[++i]);};
            if(flag=="--self-test")self=true;
            else if(flag=="--input-csv")input=arg();
            else if(flag=="--output-csv")output=arg();
            else if(flag=="--tinc-csv")tinc=arg();
            else if(flag=="--samples")samples=std::stoul(arg());
            else if(flag=="--batch")batch=std::stoul(arg());
            else if(flag=="--help"){
                std::cout<<"Usage: fusion [--self-test] [--input-csv input.csv] [--samples N] [--batch N] [--output-csv path] [--tinc-csv path]\n";
                return 0;
            }else throw std::runtime_error("Unknown command-line argument: "+flag);
        }
        if(self){fusion::self_test();return 0;}
        fusion::require(samples>=24&&samples<=1000000,"--samples must be between 24 and 1000000");
        fusion::require(batch>=1&&batch<=100000,"--batch must be between 1 and 100000");
        auto data=input.empty()?fusion::synthetic(samples):fusion::from_csv(input,samples);
        fusion::require(data.size()>=24,"Need at least 24 valid samples to perform TINC audit");
        fusion::run(data,output,tinc,batch);return 0;
    }catch(const std::exception&e){std::cerr<<"ERROR: "<<e.what()<<"\n";return 1;}
}
