// WP18: mathematical nitrification / aeration research demonstrator.
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
    check(v[0]>=0&&v[0]<=500,"NH4 research domain");
    check(v[1]>=0&&v[1]<v[17],"DO below DOsat required");
    check(v[2]>=0&&v[2]<=5000&&v[3]>=0&&v[3]<=2,"Biomass and kinetic bounds");
    check(v[4]>0&&v[4]<=1&&v[5]>0&&v[6]>0&&v[7]>0,"Saturation, yield and residence time");
    check(v[8]>0&&v[8]<20&&v[9]>=0&&v[10]>0&&v[11]>0,"Oxygen and efficiency units");
    check(v[12]>=-5&&v[12]<=45&&v[13]>=-5&&v[13]<=45,"Temperature research bounds");
    check(v[14]>=0.5&&v[14]<=1.5&&v[15]>0&&v[16]>=0,"Temperature base/inhibition/transfer");
    check(v[17]>0&&v[18]>=0&&v[19]>=0&&v[20]>0&&v[21]>=0&&v[22]>=0&&v[23]>=0,"Limits and costs");
    check(v[10]<=100&&v[11]<1e8&&v[7]<=100&&v[15]<=1e8,"Finite research range");
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

struct Independent {double out1,out2,our2,otr,power2;bool guard1,guard2;};
Independent nativeReference(const std::vector<double>& a) {
    // Independent physics reference is explicitly for validation only.
    // This function is NEVER used to generate the primary result CSV.
    const double nh=a[0],do2=a[1];
    const double factor=(a[3]/a[4])*a[2]*(do2/(a[6]+do2));
    const double potential1=factor*nh/(a[5]+nh);
    const double potential2=factor*(nh/(a[5]+nh+nh*nh/a[15]))*std::pow(a[14],a[12]-a[13]);
    const double eff1=std::min(potential1,nh/a[7]);
    const double eff2=std::min(potential2,nh/a[7]);
    const double out1=nh-eff1*a[7],out2=nh-eff2*a[7];
    const double our1=a[8]*eff1+a[9]*a[2], our2=a[8]*eff2+a[9]*a[2];
    const double otr=a[16]*(a[17]-do2);
    const double power1=our1*a[11]/(1000*a[10]);
    const double power2=our2*a[11]/(1000*a[10]);
    const bool g1=out1<=a[18] && otr>=our1 && do2>=a[19] && power1<=a[20];
    const bool g2=out2<=a[18] && otr>=our2 && do2>=a[19] && power2<=a[20];
    return {out1,out2,our2,otr,power2,g1,g2};
}
void compareIndependently(const std::vector<double>& a,const std::vector<double>& z) {
    const auto ref=nativeReference(a);
    auto eq=[](double x,double y){return std::abs(x-y)<=2e-9*(1+std::abs(y));};
    check(eq(z[4],ref.out1)&&eq(z[5],ref.out2),"Reference effluent concentration");
    check(eq(z[7],ref.our2)&&eq(z[8],ref.otr),"Reference oxygen balance components");
    check(eq(z[12],ref.power2),"Reference electric power proxy");
    check(eq(z[15],0),"Nitrogen conservation residual");
    check(z[16]==double(ref.guard1)&&z[17]==double(ref.guard2),"Reference model guards");
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
    check(!errSingle && scalarErr[0]==0 && std::abs(single-scalarGraph[0])<=1e-8*(1+std::abs(single)),
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
            evaluate(root+"/examples/observed_grid_inputs.csv",root+"/results/local_sdk_grid.csv",graphs);
            evaluate(root+"/examples/observed_hourly_inputs.csv",root+"/results/local_sdk_hourly.csv",graphs);
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
