// WP22: regenerative chatter candidate stability-lobe mathematical demonstrator.
// All domain mathematics used for the main outputs is owned by original paceval graphs.
// C++ owns CSV schema, domains, repeatable batch dispatch, state and independent checks.
// The archived evidence is remote MCP 4.26. This local SDK path has NOT been executed.
#include "paceval_main.h"
#include "generated_formulas.h"
#include <algorithm>
#include <array>
#include <cmath>
#include <complex>
#include <fstream>
#include <iostream>
#include <locale>
#include <regex>
#include <sstream>
#include <stdexcept>
#include <string>
#include <vector>

namespace {
void check(bool condition, const std::string& msg) {
    if(!condition) throw std::runtime_error(msg);
}
struct Row { std::string id; std::vector<double> v; };
struct Handles {
    std::vector<PACEVAL_HANDLE> items;
    ~Handles() { for(auto p:items) if(p) paceval_DeleteComputation(p); }
};

bool isNumberLiteral(const std::string& s) {
    // Whitelist to prevent a mathematical formula in a CSV number field.
    // paceval_dConvertStringToFloat can otherwise evaluate mathematical strings.
    static const std::regex pattern(R"(^[+-]?(?:[0-9]+(?:\.[0-9]*)?|\.[0-9]+)(?:[eE][+-]?[0-9]+)?$)");
    return !s.empty() && s.size()<=80 && std::regex_match(s,pattern);
}

double fromPacevalText(const std::string& s, const std::string& where) {
    check(isNumberLiteral(s), "Non-literal CSV number at "+where);
    int errorType=-1; long errorPosition=-1; double lower=0,upper=0;
    const double r=paceval_dConvertStringToFloat(s.c_str(),&errorType,&errorPosition,false,&lower,&upper);
    check(errorType==0 && std::isfinite(r),"SDK numeric conversion failed at "+where+
          " type="+std::to_string(errorType)+" position="+std::to_string(errorPosition));
    return r;
}
std::string toPacevalText(double x) {
    check(std::isfinite(x),"Nonfinite value cannot be written");
    // The original API has no destination buffer-length argument. Large safety
    // capacity is used, but an audit must still check each runtime version.
    std::array<char,4096> buffer{};
    const int accuracy=paceval_dConvertFloatToString(buffer.data(),x);
    check(accuracy>0,"SDK float-to-string conversion failed");
    auto end=std::find(buffer.begin(),buffer.end(),'\0');
    check(end!=buffer.end()&&end!=buffer.begin(),"SDK conversion omitted termination");
    const std::string v(buffer.begin(),end);
    check(isNumberLiteral(v),"SDK result is not canonical decimal literal");
    return v;
}

void validate(const std::vector<double>& v) {
    check(v.size()==variable_count,"Incorrect variable count");
    for(double x:v) check(std::isfinite(x),"Nonfinite input");
    const double w=v[0];
    check(w>0 && w<=1e6,"Angular frequency must be finite positive rad/s");
    check(v[1]>0 && v[2]>0 && v[3]>0 && v[4]>0 && v[5]>0 && v[6]>0,"Modal masses, stiffnesses and dampings must be positive");
    check(v[7]>=0 && v[7]<=10,"Nonnegative second-mode directional weight");
    check(v[8]>0 && v[9]>0,"Positive effective cutting coefficient and candidate depth");
    check(v[10]>=1 && v[10]<=20 && std::floor(v[10])==v[10],"Positive integer tooth count required");
    check(v[11]>=0 && v[11]<=100 && std::floor(v[11])==v[11],"Nonnegative integer lobe index required");
    // Host domain check only: the actual receptances and depth margins
    // are evaluated again as original paceval graphs, not natively substituted.
    const std::complex<double> j1(v[2]-v[1]*w*w,v[3]*w);
    const std::complex<double> j2(v[5]-v[4]*w*w,v[6]*w);
    const std::complex<double> g1=1.0/j1;
    const std::complex<double> g2=g1+v[7]/j2;
    check(g1.real() < -1e-12 && g2.real() < -1e-12,
      "Real FRF must be safely negative for the declared critical-depth phase branch");
    check(g1.imag()<0 && g2.imag()<0,"Only passive negative-imaginary FRF branch supported");
}
std::vector<Row> loadCSV(const std::string& filename) {
    std::ifstream in(filename); in.imbue(std::locale::classic());
    check(bool(in),"Cannot open input: "+filename);
    std::string line; check(bool(std::getline(in,line)),"Missing header");
    if(!line.empty() && line.back()=='\r') line.pop_back();
    std::string expected="case_id"; std::istringstream ss(variable_list);std::string part;
    while(ss>>part) expected+=","+part;
    check(line==expected,"CSV headers do not match declared SDK variables");
    std::vector<Row> rows;unsigned rownum=1;
    while(std::getline(in,line)) {
        ++rownum; if(!line.empty()&&line.back()=='\r')line.pop_back();
        check(!line.empty()&&line.back()!=',',"Missing CSV value at row "+std::to_string(rownum));
        std::stringstream fields(line);std::vector<std::string> cells;
        while(std::getline(fields,part,',')) cells.push_back(part);
        check(cells.size()==variable_count+1,"Wrong CSV field count at row "+std::to_string(rownum));
        Row row; row.id=cells[0];
        check(std::regex_match(row.id,std::regex("[A-Za-z0-9_-]{1,40}")),"Invalid row identifier");
        for(size_t k=1;k<cells.size();++k)
            row.v.push_back(fromPacevalText(cells[k],"row "+std::to_string(rownum)+" col "+std::to_string(k)));
        validate(row.v);rows.push_back(std::move(row));
        check(rows.size()<=500000,"Too many input records");
    }
    check(!rows.empty(),"Empty input dataset");
    return rows;
}


std::array<double,23> nativeReference(const std::vector<double>& a){
    // Validation ONLY: independent complex arithmetic, not a translation
    // of the generated paceval formula strings.
    const double w=a[0],Ks=a[8],depth=a[9],teeth=a[10],lobe=a[11];
    const double pi=std::acos(-1.0);
    const std::complex<double> g1=1.0/std::complex<double>(a[2]-a[1]*w*w,a[3]*w);
    const std::complex<double> g2=g1+a[7]/std::complex<double>(a[5]-a[4]*w*w,a[6]*w);
    const double b1=-1.0/(2*Ks*g1.real()),b2=-1.0/(2*Ks*g2.real());
    const double ph1=pi+2*std::atan(g1.imag()/g1.real()),ph2=pi+2*std::atan(g2.imag()/g2.real());
    const double sp1=60*w/(teeth*(ph1+2*pi*lobe)),sp2=60*w/(teeth*(ph2+2*pi*lobe));
    const double theta=ph2+2*pi*lobe;
    const auto characteristic=1.0+Ks*b2*g2*(1.0-std::exp(std::complex<double>(0,-theta)));
    return {g1.real(),g1.imag(),std::abs(g1),b1,ph1,sp1,b1-depth,double(b1>=depth),
            g2.real(),g2.imag(),std::abs(g2),b2,ph2,sp2,b2-depth,double(b2>=depth),
            b2-b1,-b2/Ks,(b2-depth)/b2,characteristic.real(),characteristic.imag(),
            std::sqrt(a[2]/a[1]),a[3]/(2*std::sqrt(a[2]*a[1]))};
}
void compareIndependently(const std::vector<double>& input,const std::vector<double>& actual){
    const auto ref=nativeReference(input);
    check(actual.size()==ref.size(),"Invalid graph result count");
    for(size_t i=0;i<ref.size();++i){
        // The output of the local SDK should agree with the independent
        // double-precision complex arithmetic for these well-conditioned rows.
        const double tol=5e-14+5e-11*std::abs(ref[i]);
        check(std::isfinite(actual[i]) && std::abs(actual[i]-ref[i])<=tol,
           "Independent local mathematical reference failed at graph "+std::to_string(i));
    }
    check(std::abs(actual[19])<1e-8&&std::abs(actual[20])<1e-8,
          "Regenerative candidate-boundary characteristic residual too large");
}
void conversionTest() {
    for(const char* str:{"0","-0","+3.25","0.000001","1.25e-9","4.2e7",".5","12."}) {
        const double x=fromPacevalText(str,"conversion selftest");
        check(isNumberLiteral(toPacevalText(x)),"Original SDK numeric output format failed");
    }
    for(const char* bad:{"","1+2","NaN","Inf","3,14","1_000"," 1","1/0","0x10"})
        check(!isNumberLiteral(bad),"Non-literal CSV field unexpectedly accepted");
    bool rejected=false;
    try{(void)fromPacevalText("1e99999","overflow test");}catch(const std::exception&){rejected=true;}
    check(rejected,"Huge exponent should fail finite original SDK conversion");
}
void operatorTest() {
    struct OpCase {const char* formula;std::array<double,3> expected;};
    const OpCase cases[]={
        {"(-1) % 10",{{-1,-1,-1}}}, {"(-1) mod 10",{{9,9,9}}},
        {"4 min 5",{{4,4,4}}}, {"4 max 5",{{5,5,5}}},
        {"((x <= (2*y)) AND (z >= 0))",{{1,1,0}}},
        {"((NOT(x = y)) OR (z <> 0))",{{0,1,1}}},
        {"((x = y) XOR (z <> 0))",{{1,0,1}}}
    };
    const double values[3][3]={{1,1,0},{-1,1,0},{2,1,-1}};
    for(const auto& tc:cases){
        PACEVAL_HANDLE handle=paceval_CreateComputation(tc.formula,3,"x y z",false,nullptr);
        check(handle&&!paceval_GetIsError(handle),"Original SDK operator graph creation failed");
        for(size_t i=0;i<3;++i){
            double input[]={values[i][0],values[i][1],values[i][2]};
            const double output=paceval_dGetComputationResult(handle,input,nullptr,nullptr);
            check(!paceval_GetIsError(handle)&&output==tc.expected[i],"Operator semantics mismatch");
        }
        paceval_DeleteComputation(handle);
    }
}
void evaluate(const std::string& inputFile,const std::string& outputFile,const Handles& graphs) {
    auto rows=loadCSV(inputFile);
    const size_t n=rows.size(),ng=graphs.items.size();
    std::vector<double> packed;packed.reserve(n*variable_count);
    for(const auto& row:rows) packed.insert(packed.end(),row.v.begin(),row.v.end());
    // Verify scalar and single-graph batch agree before multi-graph batch.
    const double single=paceval_dGetComputationResult(graphs.items[0],rows[0].v.data(),nullptr,nullptr);
    check(!paceval_GetIsError(graphs.items[0]),"Scalar graph evaluation failed");
    std::vector<double> scalarGraph(n);std::vector<int> scalarErr(n);
    const bool errSingle=paceval_dGetComputationResultExt(graphs.items[0],packed.data(),
                  static_cast<unsigned long>(n),scalarGraph.data(),nullptr,nullptr,scalarErr.data());
    check(!errSingle && std::all_of(scalarErr.begin(),scalarErr.end(),[](int e){return e==0;}) && std::abs(single-scalarGraph[0])<=1e-8*(1+std::abs(single)),
          "Single-graph batch layout mismatch");
    std::vector<double> results(n*ng);std::vector<int> errorCodes(n*ng);
    const bool errMulti=paceval_dGetMultipleComputationsResultsExt(const_cast<PACEVAL_HANDLE*>(graphs.items.data()),
       static_cast<unsigned long>(ng),packed.data(),static_cast<unsigned long>(n),results.data(),
       nullptr,nullptr,errorCodes.data());
    check(!errMulti,"Multi-graph batch failed");
    bool graphMajor=true,rowMajor=true;
    for(size_t j=0;j<std::min<size_t>(3,n);++j){
        graphMajor &= std::abs(results[j]-scalarGraph[j])<=1e-8*(1+std::abs(scalarGraph[j]));
        rowMajor &= std::abs(results[j*ng]-scalarGraph[j])<=1e-8*(1+std::abs(scalarGraph[j]));
    }
    check(graphMajor||rowMajor,"Unknown multi-graph result layout");
    const auto index=[&](size_t row,size_t graph){return graphMajor?graph*n+row:row*ng+graph;};
    std::ofstream out(outputFile);out.imbue(std::locale::classic());check(bool(out),"Cannot open output");
    out<<"case_id";for(const auto& graph:model_graphs)out<<','<<graph.id;out<<'\n';
    for(size_t j=0;j<n;++j){
        std::vector<double> calculated(ng);
        for(size_t k=0;k<ng;++k){
            const size_t at=index(j,k);
            check(errorCodes[at]==0&&std::isfinite(results[at]),"Nonzero error or nonfinite value in main batch");
            calculated[k]=results[at];
        }
        compareIndependently(rows[j].v,calculated);
        out<<rows[j].id;for(double value:calculated) out<<','<<toPacevalText(value);out<<'\n';
    }
    check(bool(out),"Result output failed");
    std::cout<<"Original SDK evaluated "<<n<<" rows via persistent paceval computation graphs.\n";
}
void run(const std::string& root,bool testOnly){
    check(paceval_InitializeLibrary(nullptr),"Original SDK shared library unavailable or incompatible");
    try{
        conversionTest();operatorTest();
        if(!testOnly){
            Handles graphs;
            for(const auto& formula:model_graphs){
                PACEVAL_HANDLE h=paceval_CreateComputation(formula.expression,
                                static_cast<unsigned long>(variable_count),variable_list,false,nullptr);
                check(h&&!paceval_GetIsError(h),std::string("Graph creation failed for ")+formula.id);
                graphs.items.push_back(h);
            }
            evaluate(root+"/examples/synthetic_lobe_inputs.csv",root+"/results/local_sdk_lobe.csv",graphs);
        }
    }catch(...){paceval_FreeLibrary();throw;}
    check(paceval_FreeLibrary(),"Original SDK library teardown failed");
}
}
int main(int argc,char** argv){
    try{
        run(argc>1?argv[1]:".",argc>2&&std::string(argv[2])=="--selftest");
        return 0;
    }catch(const std::exception& ex){
        std::cerr<<"Original SDK run failed: "<<ex.what()<<'\n';return 2;
    }
}
