// WP25 - Three-contact robotic grasp wrench feasibility.
// Domain mathematics: original paceval graphs. Orchestration, safe CSV parsing,
// contact-to-aggregate graph transport, independent checks: C++ host.
// Archived evidence is REMOTE MCP 4.26, not a local SDK execution.
// Local original SDK source: syntax tested, runtime not executed without shared library.
#include "paceval_main.h"
#include "generated_formulas.h"
#include <algorithm>
#include <array>
#include <cmath>
#include <fstream>
#include <iostream>
#include <limits>
#include <locale>
#include <regex>
#include <sstream>
#include <stdexcept>
#include <string>
#include <vector>

namespace {
void ensure(bool b,const std::string& m){if(!b)throw std::runtime_error(m);}
struct Candidate {std::string id;std::array<std::array<double,9>,3> c{};std::array<double,14> e{};};
struct GraphHandles {
    std::vector<PACEVAL_HANDLE> h;
    GraphHandles()=default;
    GraphHandles(const GraphHandles&)=delete;
    GraphHandles& operator=(const GraphHandles&)=delete;
    GraphHandles(GraphHandles&& other) noexcept : h(std::move(other.h)) {other.h.clear();}
    ~GraphHandles(){for(auto x:h)if(x)paceval_DeleteComputation(x);}
};
constexpr size_t NCONTACT=3, NC=10, NA=18;

bool numericLiteral(const std::string& s){
    static const std::regex re(R"(^[+-]?(?:[0-9]+(?:\.[0-9]*)?|\.[0-9]+)(?:[eE][+-]?[0-9]+)?$)");
    return s.size()>0&&s.size()<=80&&std::regex_match(s,re);
}
double fromSDK(const std::string& s,const std::string& where){
    ensure(numericLiteral(s),"Unsafe/invalid numerical literal: "+where);
    int errorType=-1;long errorPosition=-1;double lo=0,hi=0;
    double v=paceval_dConvertStringToFloat(s.c_str(),&errorType,&errorPosition,false,&lo,&hi);
    ensure(errorType==0&&std::isfinite(v),"SDK conversion error: "+where+" type="+std::to_string(errorType)+" pos="+std::to_string(errorPosition));
    return v;
}
std::string toSDK(double value){
    ensure(std::isfinite(value),"Nonfinite SDK output");
    std::array<char,4096> buffer{};
    int precision=paceval_dConvertFloatToString(buffer.data(),value);
    ensure(precision>0,"Original SDK float-to-string conversion failed");
    auto it=std::find(buffer.begin(),buffer.end(),'\0');
    ensure(it!=buffer.end()&&it!=buffer.begin(),"Non-terminated SDK number");
    std::string s(buffer.begin(),it);ensure(numericLiteral(s),"Noncanonical SDK output");return s;
}
void validate(const Candidate& a){
    for(const auto& c:a.c){
        for(double x:c)ensure(std::isfinite(x),"Nonfinite contact data");
        ensure(c[0]>=0 && c[0]<=c[8] && c[8]>0,"Normal load/capacity domain");
        ensure(c[5]>0&&c[5]<=1&&c[7]>=0&&c[7]<=3,"Radius/friction domain");
        ensure(std::abs(c[3]*c[3]+c[4]*c[4]-1.)<1e-12,"Contact radial normal must be unit length");
        ensure(std::abs(c[6])<=1,"Contact axial position out of domain");
    }
    for(double x:a.e)ensure(std::isfinite(x),"Nonfinite global input");
    ensure(a.e[0]>=0&&a.e[1]>0,"Mass/gravity domain");
    ensure(a.e[8]>0&&a.e[9]>0&&a.e[10]>0,"Force/torque/reference-length tolerance domain");
    ensure(a.e[11]>=0&&a.e[12]>=0&&a.e[13]>=0,"Negative score weights");
}
std::vector<Candidate> readCandidates(const std::string& filename){
    std::ifstream in(filename);in.imbue(std::locale::classic());ensure(bool(in),"Cannot open input CSV");
    std::string header;ensure(bool(std::getline(in,header)),"Empty input CSV");
    if(!header.empty()&&header.back()=='\r')header.pop_back();
    std::string expected="case_id";
    std::string names;
    // Model order in input CSV is contact-major, then 14 global columns.
    for(int i=1;i<=3;++i){std::istringstream cv(contact_variable_list);while(cv>>names)expected+=","+names+std::to_string(i);}
    for(const char* n:{"mass","g","ex","ey","ez","etx","ety","etz","Ftol","Ttol","Lref","wF","wT","wM"})expected+=std::string(",")+n;
    ensure(header==expected,"Input CSV header does not match declared schema");
    std::vector<Candidate> cases;std::string line;size_t lineno=1;
    while(std::getline(in,line)){
        ++lineno;if(!line.empty()&&line.back()=='\r')line.pop_back();
        ensure(!line.empty()&&line.back()!=',',"Empty input/trailing field at line "+std::to_string(lineno));
        std::stringstream parser(line);std::vector<std::string> cells;std::string item;
        while(std::getline(parser,item,','))cells.push_back(item);
        ensure(cells.size()==1+3*9+14,"Wrong number of columns on line "+std::to_string(lineno));
        Candidate r;r.id=cells[0];ensure(std::regex_match(r.id,std::regex("[A-Za-z0-9_-]{1,45}")),"Invalid ID");
        size_t k=1;for(auto& c:r.c)for(auto& x:c){x=fromSDK(cells[k],r.id+" col "+std::to_string(k));++k;}
        for(auto& x:r.e){x=fromSDK(cells[k],r.id+" col "+std::to_string(k));++k;}
        validate(r);cases.push_back(r);ensure(cases.size()<=500000,"Excessive candidate count");
    }
    ensure(!cases.empty(),"No candidates");return cases;
}
std::vector<double> runStage(const GraphHandles& handles,const std::vector<double>& packed,size_t count,size_t width){
    const size_t ng=handles.h.size();ensure(ng>0&&width>0&&packed.size()==count*width,"Invalid multi-graph array dimensions");
    std::vector<double> output(count*ng);std::vector<int> errors(count*ng);
    const bool failed=paceval_dGetMultipleComputationsResultsExt(
        const_cast<PACEVAL_HANDLE*>(handles.h.data()),static_cast<unsigned long>(ng),const_cast<double*>(packed.data()),
        static_cast<unsigned long>(count),output.data(),nullptr,nullptr,errors.data());
    ensure(!failed,"Original SDK multi-graph batch returned an error");
    for(int x:errors)ensure(x==0,"Nonzero original SDK graph error code");
    // Detect output layout with verified scalar values; model supports both documented/observed layouts.
    double first=paceval_dGetComputationResult(handles.h[0],const_cast<double*>(packed.data()),nullptr,nullptr);
    ensure(!paceval_GetIsError(handles.h[0]),"Original SDK scalar layout probe failed");
    const auto close=[](double x,double y){return std::isfinite(x)&&std::isfinite(y)&&std::abs(x-y)<=1e-10*(1+std::abs(y));};
    bool graphMajor=close(output[0],first),rowMajor=graphMajor;
    for(size_t i=1;i<std::min(count,size_t(4));++i){
        double scalar=paceval_dGetComputationResult(handles.h[0],const_cast<double*>(packed.data()+i*width),nullptr,nullptr);
        ensure(!paceval_GetIsError(handles.h[0]),"Original SDK scalar probe failed");
        graphMajor &= close(output[i],scalar);
        rowMajor &= close(output[i*ng],scalar);
    }
    ensure(graphMajor||rowMajor,"Cannot identify multi-graph result layout");
    std::vector<double> rowMajorResult(count*ng);
    for(size_t i=0;i<count;++i)for(size_t g=0;g<ng;++g){
        const size_t source=graphMajor?g*count+i:i*ng+g;
        ensure(std::isfinite(output[source]),"Nonfinite graph output");
        rowMajorResult[i*ng+g]=output[source];
    }
    return rowMajorResult;
}
GraphHandles registerGraphs(const ModelGraph* graph,size_t n,size_t variables,const char* variableList){
    GraphHandles h;for(size_t i=0;i<n;++i){
        PACEVAL_HANDLE p=paceval_CreateComputation(graph[i].expression,static_cast<unsigned long>(variables),variableList,false,nullptr);
        ensure(p&&!paceval_GetIsError(p),std::string("Cannot create genuine paceval graph ")+graph[i].id);
        h.h.push_back(p);
    }return h;
}
void conversionTest(){
    for(const char* x:{"0","-0","+.25","1.0e-9","-3.25E+7","4.",".5"})ensure(numericLiteral(toSDK(fromSDK(x,"selftest"))),"SDK conversion test");
    for(const char* x:{"","1+2","NaN","Inf","1,2","1_000"," 4","1/0","0x10"})ensure(!numericLiteral(x),"Unsafe numeric input accepted");
    bool rejected=false;try{(void)fromSDK("1e99999","overflow");}catch(...){rejected=true;}ensure(rejected,"Overflow input not rejected");
}
void operatorTest(){
    struct Op {const char* f;std::array<double,3> expected;};
    const Op op[]={ {"(-1) % 10",{{-1,-1,-1}}},{"(-1) mod 10",{{9,9,9}}},
       {"4 min 5",{{4,4,4}}},{"4 max 5",{{5,5,5}}},
       {"((x <= (2*y)) AND (z >= 0))",{{1,1,0}}},
       {"((NOT(x = y)) OR (z <> 0))",{{0,1,1}}},
       {"((x = y) XOR (z <> 0))",{{1,0,1}}}};
    const double input[][3]={{1,1,0},{-1,1,0},{2,1,-1}};
    for(const auto& o:op){
        PACEVAL_HANDLE h=paceval_CreateComputation(o.f,3,"x y z",false,nullptr);
        ensure(h&&!paceval_GetIsError(h),"Operator graph registration error");
        for(size_t i=0;i<3;++i){
            double a[3]={input[i][0],input[i][1],input[i][2]};
            const double result=paceval_dGetComputationResult(h,a,nullptr,nullptr);
            ensure(!paceval_GetIsError(h)&&result==o.expected[i],"Original paceval operator result differs from reference");
        }paceval_DeleteComputation(h);
    }
}
void nativeCheck(const Candidate& c,const double* y){
    // Completely independent vector-mechanics reference; never used as published results.
    std::array<double,3> f={0,0,-c.e[0]*c.e[1]},t={0,0,0};
    double minF=1e100,minN=1e100,minCap=1e100,slip=0;
    for(const auto& a:c.c){
        const double fn=a[0],ft=a[1],fz=a[2],nx=a[3],ny=a[4],R=a[5],z=a[6],mu=a[7];
        const double fx=-fn*nx-ft*ny,fy=-fn*ny+ft*nx;
        f[0]+=fx;f[1]+=fy;f[2]+=fz;
        t[0]+=R*ny*fz-z*fy;t[1]+=z*fx-R*nx*fz;t[2]+=R*ft;
        const double fm=mu*fn-std::hypot(ft,fz);minF=std::min(minF,fm);
        minN=std::min(minN,fn);minCap=std::min(minCap,a[8]-fn);
        slip+=std::pow(std::max(0.,-fm),2);
    }
    const auto length=[](std::array<double,3> q){return std::sqrt(q[0]*q[0]+q[1]*q[1]+q[2]*q[2]);};
    const double f1=length(f),t1=length(t);
    for(int i=0;i<3;++i){f[i]+=c.e[2+i];t[i]+=c.e[5+i];}
    const double f2=length(f),t2=length(t),Ftol=c.e[8],Ttol=c.e[9],Lref=c.e[10];
    const double J1=c.e[11]*f1*f1+c.e[12]*std::pow(t1/Lref,2)+c.e[13]*slip;
    const double J2=c.e[11]*f2*f2+c.e[12]*std::pow(t2/Lref,2)+c.e[13]*slip;
    const double margin=std::min({Ftol-f2,(Ttol-t2)/Lref,minF,minN,minCap});
    const double expected[]={f1,t1,f2,t2,minF,minN,minCap,Ftol-f1,Ftol-f2,Ttol-t1,Ttol-t2,slip,J1,J2,
      double(f1<=Ftol&&t1<=Ttol&&minF>=0&&minN>=0&&minCap>=0),
      double(f2<=Ftol&&t2<=Ttol&&minF>=0&&minN>=0&&minCap>=0),margin,J2-J1};
    for(size_t k=0;k<NA;++k){
        double tol=1e-9*(1+std::abs(expected[k]));
        ensure(std::isfinite(y[k])&&std::abs(y[k]-expected[k])<tol,
          c.id+" independent C++ model mismatch: graph index "+std::to_string(k));
    }
}
void run(const std::string& root,bool selftest){
    ensure(paceval_InitializeLibrary(nullptr),"Missing ABI-compatible original paceval runtime");
    try{
        conversionTest();operatorTest();
        if(!selftest){
            const auto cases=readCandidates(root+"/examples/synthetic_contact_candidates.csv");
            auto contact=registerGraphs(contact_graphs,contact_graph_count,contact_variable_count,contact_variable_list);
            auto aggregate=registerGraphs(aggregate_graphs,aggregate_graph_count,aggregate_variable_count,aggregate_variable_list);
            std::vector<double> contactInput;contactInput.reserve(cases.size()*3*NC);
            for(const auto& c:cases)for(const auto& a:c.c)contactInput.insert(contactInput.end(),a.begin(),a.end());
            const auto outputs=runStage(contact,contactInput,cases.size()*3,contact_variable_count);
            std::vector<double> aggregateInput;aggregateInput.reserve(cases.size()*aggregate_variable_count);
            for(size_t i=0;i<cases.size();++i){
                for(size_t finger=0;finger<3;++finger)for(size_t k=0;k<9;++k)
                    aggregateInput.push_back(outputs[(i*3+finger)*NC+k]);
                aggregateInput.insert(aggregateInput.end(),cases[i].e.begin(),cases[i].e.end());
            }
            const auto result=runStage(aggregate,aggregateInput,cases.size(),aggregate_variable_count);
            std::ofstream out(root+"/results/local_sdk_results.csv");
            out.imbue(std::locale::classic());ensure(bool(out),"Cannot write local SDK output");
            out<<"case_id";for(const auto& graph:aggregate_graphs)out<<','<<graph.id;out<<'\n';
            for(size_t i=0;i<cases.size();++i){
                nativeCheck(cases[i],result.data()+i*NA);
                out<<cases[i].id;for(size_t k=0;k<NA;++k)out<<','<<toSDK(result[i*NA+k]);out<<'\n';
            }
            ensure(bool(out),"Local SDK output failed");
            std::cout<<"Real original SDK complete: "<<cases.size()<<" candidates, 3 contacts, 28 persistent graphs.\n";
        }
    }catch(...){paceval_FreeLibrary();throw;}
    ensure(paceval_FreeLibrary(),"paceval SDK teardown failed");
}
} // namespace
int main(int argc,char** argv){
    try{
        const std::string root=argc>1?argv[1]:".";
        run(root,argc>2&&std::string(argv[2])=="--selftest");return 0;
    }catch(const std::exception& e){std::cerr<<"Original paceval SDK error: "<<e.what()<<'\n';return 2;}
}
