// WP20: injection molding rheology and pressure-window research demonstrator.
// All domain mathematics used for the main outputs is owned by original paceval graphs.
// C++ owns CSV schema, domains, repeatable batch dispatch, state and independent checks.
// The archived evidence is remote MCP 4.26. This local SDK path has NOT been executed.
#include "paceval_main.h"
#include "generated_formulas.h"
#include <algorithm>
#include <array>
#include <cmath>
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
    check(v[0]>0 && v[0]<0.0001,"Positive flow required (isothermal model)");
    check(v[1]>=400 && v[1]<=650,"Absolute melt temperature range");
    check(v[2]>0 && v[2]<=0.02 && v[4]>0 && v[4]<=0.02,"Positive circular radii");
    check(v[3]>0 && v[3]<=10 && v[5]>0 && v[5]<=10,"Positive runner lengths");
    check(v[6]>0 && v[6]<=1e6 && v[7]>0 && v[7]<=1,"Power-law material domain");
    check(v[8]>=0 && v[8]<=1e6 && v[9]>0 && v[10]>0,"Arrhenius parameters");
    check(v[11]>0 && v[12]>0,"Cross proxy parameters");
    check(v[13]>v[14] && v[14]>=0 && v[15]>0,"Machine/cavity/shear limits");
    check(v[16]>0 && v[16]<v[17],"Temperature limits must be ordered");
    check(v[18]>=0 && v[19]>=0 && v[20]>=0 && v[21]>=0 && v[22]>0,"Energy inputs and budget");
    check(v[0]/(v[4]*v[4]*v[4])<1e6,"Shear proxy research stability bound");
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

struct Independent { double pressureV1,pressureV2,marginV1,marginV2,scoreV1,scoreV2,delta,dQ,dT,newton; bool guardV1,guardV2; };
Independent nativeReference(const std::vector<double>& a) {
    // Independent C++ reference is used ONLY for checking paceval results.
    // It is never substituted for the primary CSV mathematical outputs.
    const double flow=a[0],T=a[1],n=a[7];
    const double f=std::exp(a[8]/a[9]*(1/T-1/a[10]));
    const double corr=(3*n+1)/(4*n);
    const double gA=4*flow/(3.1415926535897932384626433832795*std::pow(a[2],3));
    const double gB=4*flow/(3.1415926535897932384626433832795*std::pow(a[4],3));
    auto pressure=[&](double L,double r,double g,bool corrected) {
       return 2*a[6]*f*L/r*std::pow(g*(corrected?corr:1),n);
    };
    const double p1=pressure(a[3],a[2],gA,false)+pressure(a[5],a[4],gB,false);
    const double p2=pressure(a[3],a[2],gA,true)+pressure(a[5],a[4],gB,true);
    const double m1=a[13]-a[14]-p1,m2=a[13]-a[14]-p2;
    const double tmargin=std::min(T-a[16],a[17]-T);
    const double shear1=a[15]-std::max(gA,gB);
    const double shear2=a[15]-std::max(gA,gB)*corr;
    const double energy=a[18]*a[19]+a[20]*a[21],emargin=a[22]-energy;
    auto score=[&](double p,double sh) {
        return std::min(std::min(p/a[13],sh/a[15]),std::min(tmargin/(a[17]-a[16]),emargin/a[22]));
    };
    const double newton=8*a[6]*f*flow/3.1415926535897932384626433832795*(a[3]/std::pow(a[2],4)+a[5]/std::pow(a[4],4));
    return {p1,p2,m1,m2,score(m1,shear1),score(m2,shear2),p2-p1,
            n*p2/flow,-a[8]/(a[9]*T*T)*p2,newton,
            m1>=0&&shear1>=0&&tmargin>=0&&emargin>=0,
            m2>=0&&shear2>=0&&tmargin>=0&&emargin>=0};
}
void compareIndependently(const std::vector<double>& a,const std::vector<double>& z) {
    const Independent ref=nativeReference(a);
    auto eq=[](double x,double y){return std::abs(x-y)<=1e-10*(1+std::abs(y));};
    check(eq(z[6],ref.pressureV1) && eq(z[11],ref.pressureV2),"Reference pressure equations");
    check(eq(z[12],ref.marginV1) && eq(z[13],ref.marginV2),"Reference pressure margins");
    check(z[19]==double(ref.guardV1) && z[20]==double(ref.guardV2),"Reference versioned logical guards");
    check(eq(z[21],ref.scoreV1) && eq(z[22],ref.scoreV2),"Reference model scores");
    check(eq(z[23],ref.delta) && eq(z[24],ref.dQ) && eq(z[25],ref.dT),"Reference sensitivities");
    check(eq(z[30],ref.newton),"Reference Newtonian limit helper");
    if(a[7]==1) check(eq(z[6],z[11]) && eq(z[11],z[30]),"Newtonian n=1 identity");
}
void conversionTest() {
    for(const char* s:{"0","-0","+3.25","0.000001","1.25e-9","4.2e7",".5","12."}) {
        const double x=fromPacevalText(s,"conversion selftest");
        check(isNumberLiteral(toPacevalText(x)),"Float text output roundtrip format");
    }
    for(const char* s:{"","1+2","NaN","Inf","3,14","1_000"," 1","1/0","1e99999","0x10"})
        check(!isNumberLiteral(s) || std::string(s)=="1e99999","Illegal numeric schema text");
    // Huge exponents are syntactically decimal literals but must fail the finite SDK check.
}
void operatorTest() {
    struct Entry {const char* expr;double want;};
    const Entry cases[]={{"(-1) % 10",-1},{"(-1) mod 10",9},
       {"4 min 5",4},{"4 max 5",5},
       {"((x <= (2*y)) AND (z >= 0))",1},
       {"((NOT(x = y)) OR (z <> 0))",0},
       {"((x = y) XOR (z <> 0))",1}};
    for(const auto& t:cases){
        PACEVAL_HANDLE p=paceval_CreateComputation(t.expr,3,"x y z",false,nullptr);
        check(p && !paceval_GetIsError(p),"Operator graph not created");
        double val[]={1,1,0};const double result=paceval_dGetComputationResult(p,val,nullptr,nullptr);
        check(!paceval_GetIsError(p)&&result==t.want,"Operator semantics invalid");
        paceval_DeleteComputation(p);
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
    std::cout<<"SDK evaluated "<<n<<" rows via persistent paceval computation graphs.\n";
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
            evaluate(root+"/examples/synthetic_grid_inputs.csv",root+"/results/local_sdk_grid.csv",graphs);
            evaluate(root+"/examples/synthetic_edge_inputs.csv",root+"/results/local_sdk_edge.csv",graphs);
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
