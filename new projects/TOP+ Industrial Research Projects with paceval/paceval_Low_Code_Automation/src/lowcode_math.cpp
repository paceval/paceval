// paceval - Reusable Mathematical Execution in Low-Code Automation
// Research demonstrator for n8n-style workflows (C++17 / Linux)
//
// Architecture and reproducibility
//   - paceval: four approved/versioned, reusable execution graphs; numerical
//     results for homogeneous batches of model-specific input rows.
//   - C++ host: model registry, units/ordering declarations, domain checks,
//     formula ownership, no dynamic untrusted formula upload, CSV audit,
//     and a persistent process command protocol for a local HTTP adapter.
//   - Python bridge: JSON/HTTP transport only; NOT a claimed n8n implementation.
//   - Results are checked against an independently coded analytic C++ oracle,
//     and again against a high-precision Python Decimal oracle.
//
// SECURITY: STDIO is a local trusted transport, not a public authenticated API.
// The optional HTTP adapter binds to 127.0.0.1 by default. Do not expose it
// without an independently audited authentication, authorization, rate-limit,
// input-size, logging and TLS strategy. The runtime .so is external.
//
// Note: the supplied vendor header defines PACEVAL_HANDLE as void*. Therefore
// declare each handle individually or use std::vector<PACEVAL_HANDLE> to avoid
// accidentally declaring non-pointer variables in comma-separated statements.

#include "paceval_main.h"
#include <algorithm>
#include <cmath>
#include <cstdlib>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <limits>
#include <sstream>
#include <stdexcept>
#include <string>
#include <vector>

namespace {
void check(bool cond, const std::string& why) {
    if (!cond) throw std::runtime_error(why);
}
struct Model {
    const char* name;
    const char* version;
    const char* variables;
    const char* expression;
    unsigned int nvars;
};
// Model contract, variable order and version are immutable for this release.
// The coefficients are synthetic demonstrator parameters, not measured or
// calibrated industrial risk probabilities or legally approved quotations.
const std::vector<Model>& catalog() {
    static const std::vector<Model> items = {
        {"condition_score", "1.0", "uT uV uI b0 bT bV bI",
         "1/(1+exp(-(b0+bT*uT+bV*uV+bI*uI)))", 7},
        {"condition_score", "1.1", "uT uV uI b0 bT bV bI",
         "1/(1+exp(-(b0+bT*uT+bV*uV+bI*uI+0.05*uT*uV)))", 7},
        {"quotation", "1.0", "C m r t F",
         "C*(1+m)*((1+r)^t)+F", 5},
        {"calibration", "1.0", "T a0 a1 a2 b h",
         "T+a0+a1*T+a2*T*T+b*ln(1+h)", 6}
    };
    return items;
}
std::vector<std::string> split(const std::string& s, char delimiter) {
    std::vector<std::string> result;
    std::istringstream stream(s); std::string token;
    while (std::getline(stream, token, delimiter)) result.push_back(token);
    return result;
}
int find_model(const std::string& id, const std::string& version) {
    const auto& items = catalog();
    for (std::size_t i=0; i<items.size(); ++i)
        if (id==items[i].name && version==items[i].version) return static_cast<int>(i);
    return -1;
}
double number(const std::string& token) {
    check(!token.empty() && token.size()<64, "EMPTY_OR_LONG_NUMBER");
    std::size_t pos=0; double x=0;
    try {x=std::stod(token,&pos);} catch(...) {throw std::runtime_error("BAD_NUMBER");}
    check(pos==token.size() && std::isfinite(x), "NONFINITE_OR_BAD_NUMBER");
    return x;
}
void validate(int id, const std::vector<double>&v) {
    const auto& m=catalog()[static_cast<std::size_t>(id)];
    check(v.size()==m.nvars, "WRONG_VARIABLE_COUNT");
    for (double x : v) check(std::isfinite(x), "NONFINITE_INPUT");
    if (id<=1) { // independent physical-unit normalization upstream
        for (int j=0; j<3; ++j) check(v[j]>=-1.0 && v[j]<=1.0, "CONDITION_INPUT_RANGE");
        for (int j=3; j<7; ++j) check(v[j]>=-6.0 && v[j]<=6.0, "COEFFICIENT_RANGE");
        // Coefficient/feature bounds also avoid overflowing exp().
    } else if (id==2) {
        check(v[0]>=0 && v[0]<=1000000, "COST_RANGE");
        check(v[1]>-0.9 && v[1]<=4.0, "MARGIN_RANGE");
        check(v[2]>-0.9 && v[2]<=0.5, "RATE_RANGE");
        check(v[3]>=0 && v[3]<=30, "TERM_RANGE");
        check(v[4]>=-10000 && v[4]<=100000, "ADJUSTMENT_RANGE");
    } else {
        check(v[0]>=-100 && v[0]<=300, "TEMPERATURE_RANGE");
        check(std::abs(v[1])<=30 && std::abs(v[2])<=0.2 &&
              std::abs(v[3])<=0.005 && std::abs(v[4])<=10, "CALIBRATION_COEFFICIENT_RANGE");
        check(v[5]>=0 && v[5]<=100, "HUMIDITY_RANGE");
    }
}
double oracle(int id, const std::vector<double>&v) {
    if(id<=1) {
        double s=v[3]+v[4]*v[0]+v[5]*v[1]+v[6]*v[2];
        if(id==1) s+=0.05*v[0]*v[1];
        return 1.0/(1.0+std::exp(-s));
    }
    if(id==2) return v[0]*(1.0+v[1])*std::pow(1.0+v[2],v[3])+v[4];
    return v[0]+v[1]+v[2]*v[0]+v[3]*v[0]*v[0]+v[4]*std::log1p(v[5]);
}
class PacevalEngine {
    bool live_=false;
    std::vector<PACEVAL_HANDLE> handles_;
    PACEVAL_HANDLE tinc_ = nullptr; // 5th graph, only for pointwise interval audit
public:
    PacevalEngine() {
        check(paceval_InitializeLibrary(nullptr),"PACEVAL_INIT_FAILURE");
        live_=true;
        // Construct each approved graph ONCE, with the actual vendor C++ API.
        try {
            for(const auto&m:catalog()) {
                PACEVAL_HANDLE handle=paceval_CreateComputation(m.expression, m.nvars, m.variables, false, nullptr);
                check(handle!=nullptr,"PACEVAL_GRAPH_NULL");
                handles_.push_back(handle);
                check(!paceval_GetIsError(handle),"PACEVAL_GRAPH_ERROR");
            }
            // Separate interval-enabled graph, not part of normal batch path.
            tinc_=paceval_CreateComputation(catalog()[0].expression, catalog()[0].nvars,
                                             catalog()[0].variables, true, nullptr);
            check(tinc_!=nullptr,"PACEVAL_TINC_GRAPH_NULL");
            check(!paceval_GetIsError(tinc_),"PACEVAL_TINC_GRAPH_ERROR");
        } catch(...) {release(); throw;}
    }
    PacevalEngine(const PacevalEngine&)=delete;
    PacevalEngine& operator=(const PacevalEngine&)=delete;
    ~PacevalEngine(){release();}
    void release() {
        if(tinc_){paceval_DeleteComputation(tinc_);tinc_=nullptr;}
        for(auto it=handles_.rbegin();it!=handles_.rend();++it)paceval_DeleteComputation(*it);
        handles_.clear();
        if(live_)paceval_FreeLibrary();
        live_=false;
    }
    std::vector<double> interval(const std::vector<double>&v) {
        validate(0,v);
        std::vector<double> input=v;
        double lo=0,hi=0;
        double value=paceval_dGetComputationResult(tinc_,input.data(),&lo,&hi);
        check(!paceval_GetIsError(tinc_) && std::isfinite(value) &&
              std::isfinite(lo) && std::isfinite(hi) && lo<=hi,"PACEVAL_TINC_ERROR");
        return {value,lo,hi};
    }
    std::vector<double> evaluate(int id, const std::vector<std::vector<double>>& rows) {
        check(id>=0&&static_cast<std::size_t>(id)<handles_.size(),"UNKNOWN_MODEL");
        check(!rows.empty() && rows.size()<=512,"BATCH_LIMIT");
        const unsigned int n=catalog()[static_cast<std::size_t>(id)].nvars;
        std::vector<double> input; input.reserve(rows.size()*n);
        for(const auto&row:rows) {validate(id,row);input.insert(input.end(),row.begin(),row.end());}
        std::vector<double> result(rows.size());
        std::vector<int> errors(rows.size(),-1);
        // paceval's *Ext layout is sample-major inputs; the returned boolean
        // signals that there WAS an error (true), not success.
        const bool failed=paceval_dGetComputationResultExt(handles_[static_cast<std::size_t>(id)],
              input.data(),static_cast<unsigned long>(rows.size()),result.data(),nullptr,nullptr,errors.data());
        check(!failed,"PACEVAL_BATCH_FAILURE");
        for(std::size_t i=0;i<rows.size();++i) {
            check(errors[i]==PACEVAL_ERR_NO_ERROR && std::isfinite(result[i]),"PACEVAL_RESULT_ERROR");
        }
        check(!paceval_GetIsError(handles_[static_cast<std::size_t>(id)]),"PACEVAL_HANDLE_ERROR");
        return result;
    }
};
std::vector<std::vector<double>> parse_rows(const std::string& s, unsigned int variables,
                                             std::size_t expected_count) {
    check(s.size()<=100000, "REQUEST_TOO_LARGE");
    auto lines=split(s,';');
    check(lines.size()==expected_count,"WRONG_BATCH_COUNT");
    std::vector<std::vector<double>> rows;
    for(const auto&line:lines) {
        auto fields=split(line,',');
        check(fields.size()==variables,"WRONG_VARIABLE_COUNT");
        std::vector<double> row;row.reserve(variables);
        for(const auto&f:fields)row.push_back(number(f));
        rows.push_back(std::move(row));
    }
    return rows;
}
void self_test() {
    check(find_model("condition_score","1.1")==1,"MODEL_LOOKUP");
    check(find_model("quotation","9.0")==-1,"WRONG_VERSION_NOT_REJECTED");
    validate(0,{0,0,0,0,1,1,1});
    check(std::abs(oracle(0,{0,0,0,0,1,1,1})-0.5)<1e-16,"SIGMOID_IDENTITY");
    check(std::abs(oracle(2,{100,0.1,0.05,2,5})-126.275)<1e-10,"QUOTE_IDENTITY");
    bool bad=false;try{validate(2,{-1,0,0,1,0});}catch(...){bad=true;}
    check(bad,"NEGATIVE_COST_ACCEPTED");
    bad=false;try{parse_rows("NaN,0,0,0,1,1,1",7,1);}catch(...){bad=true;}
    check(bad,"NAN_ACCEPTED");
    bad=false;try{parse_rows("0,0,0,0,1,1",7,1);}catch(...){bad=true;}
    check(bad,"MISSING_VARIABLE_ACCEPTED");
    std::cout<<"PASS: native models, version checks, bounds, nonfinite rejection\n";
}
std::vector<std::vector<double>> sample_rows(int id) {
    std::vector<std::vector<double>> rows;
    for(int i=0;i<80;++i) {
        const double u=static_cast<double>(i)/79.0;
        if(id<=1) rows.push_back({2*u-1,std::sin(i*.1),std::cos(i*.13),-0.4+u,
                                  1.2+u,0.5+0.3*u,0.8+0.5*u});
        else if(id==2) rows.push_back({100+10000*u,0.15+0.1*u,0.02+0.03*u,1+15*u,5+30*u});
        else rows.push_back({-20+200*u,-1+2*u,0.01,0.0001,0.5,100*u});
    }
    return rows;
}
void demo(const std::string& path) {
    PacevalEngine engine;
    std::ofstream out(path);check(out.good(),"CANNOT_OPEN_OUTPUT");
    out<<"model,version,index,inputs,paceval_result,native_result,abs_error\n";
    out<<std::setprecision(17);
    std::size_t checked=0;double largest=0;
    for(std::size_t id=0;id<catalog().size();++id) {
        const auto rows=sample_rows(static_cast<int>(id));
        const auto actual=engine.evaluate(static_cast<int>(id),rows);
        for(std::size_t i=0;i<rows.size();++i) {
            const double expected=oracle(static_cast<int>(id),rows[i]);
            const double delta=std::abs(actual[i]-expected);
            check(delta<=2e-11*std::max(1.0,std::abs(expected)),"ORACLE_MISMATCH");
            largest=std::max(largest,delta);++checked;
            out<<catalog()[id].name<<","<<catalog()[id].version<<","<<i<<",\"";
            for(std::size_t k=0;k<rows[i].size();++k){if(k)out<<";";out<<rows[i][k];}
            out<<"\","<<actual[i]<<","<<expected<<","<<delta<<"\n";
        }
    }
    std::cerr<<"PASS real paceval runtime: "<<checked<<" values, max abs error "
             <<std::setprecision(7)<<largest<<", 4 reusable versioned graphs\n";
}
void tinc_demo(const std::string&path) {
    PacevalEngine engine;
    const auto rows=sample_rows(0);
    std::ofstream out(path);check(out.good(),"CANNOT_OPEN_TINC_OUTPUT");
    out<<"index,inputs,result,lower,upper\n"<<std::setprecision(17);
    for(std::size_t i=0;i<24;++i) {
        auto result=engine.interval(rows[i]);
        out<<i<<",\"";
        for(std::size_t j=0;j<rows[i].size();++j){if(j)out<<";";out<<rows[i][j];}
        out<<"\","<<result[0]<<","<<result[1]<<","<<result[2]<<"\n";
    }
    std::cerr<<"PASS real paceval TINC evaluation: 24 pointwise intervals generated\n";
}
void stdio_mode() {
    PacevalEngine engine; // Graphs live across ALL agent/workflow requests.
    std::string line;
    while(std::getline(std::cin,line)) {
        try {
            check(line.size()<=100000,"REQUEST_TOO_LARGE");
            const auto parts=split(line,'|');
            check(parts.size()==5 && parts[0]=="EVAL","INVALID_COMMAND");
            const int id=find_model(parts[1],parts[2]);
            check(id>=0,"UNKNOWN_MODEL_OR_VERSION");
            const double count_d=number(parts[3]);
            check(count_d>=1 && count_d<=512 && std::floor(count_d)==count_d,"BATCH_LIMIT");
            auto rows=parse_rows(parts[4],catalog()[static_cast<std::size_t>(id)].nvars,
                                 static_cast<std::size_t>(count_d));
            auto results=engine.evaluate(id,rows);
            std::cout<<std::setprecision(17)<<"OK|"<<parts[1]<<"|"<<parts[2]<<"|";
            for(std::size_t i=0;i<results.size();++i) {
                if(i)std::cout<<",";
                std::cout<<results[i];
            }
            std::cout<<std::endl;
        } catch(const std::exception& e) {
            // No raw untrusted expressions or internal memory details echoed.
            std::cout<<"ERR|"<<e.what()<<std::endl;
        }
    }
}
} // namespace
int main(int argc,char**argv) {
    try {
        check(argc>=2,"USAGE: --self-test | --demo FILE | --stdio");
        const std::string cmd=argv[1];
        if(cmd=="--self-test" && argc==2)self_test();
        else if(cmd=="--demo" && argc==3)demo(argv[2]);
        else if(cmd=="--tinc" && argc==3)tinc_demo(argv[2]);
        else if(cmd=="--stdio" && argc==2)stdio_mode();
        else throw std::runtime_error("INVALID_ARGUMENTS");
        return 0;
    } catch(const std::exception&e) {
        std::cerr<<"ERROR: "<<e.what()<<"\n";
        return 1;
    }
}
