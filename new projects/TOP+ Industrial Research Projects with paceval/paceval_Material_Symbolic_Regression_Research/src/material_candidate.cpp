// WP-019: Material-property symbolic-regression candidate evaluation.
// Original official paceval_main.h/.cpp from SDK 4.25, linked with the external engine.
// This research program evaluates a PREDECLARED grammar. It does not discover a
// material law, learn descriptors, fit coefficients or validate real material data.
// Units: property E in GPa, composition-like x dimensionless, temperature T in K.
// Each expression is constructed to be dimensionally consistent by construction.
#include "paceval_main.h"
#include <algorithm>
#include <array>
#include <cmath>
#include <cstdint>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <limits>
#include <sstream>
#include <stdexcept>
#include <string>
#include <vector>

namespace {
constexpr size_t N = 60;
constexpr size_t TRAIN_END = 36;
constexpr size_t VAL_END = 48;
constexpr double TOL = 2e-9; // Absolute property error in GPa, not a material accuracy limit.

void check(bool condition, const std::string& message) {
    if (!condition) throw std::runtime_error(message);
}

// Explicit units and family registry: no arbitrary user-provided expression
// is accepted. a,b,c,e have GPa units, d is in kelvin; each family returns GPa.
struct Candidate {
    size_t id = 0;
    int family = 0;
    double a = 0, b = 0, c = 0, d = 0, e = 0;
};
struct Sample {
    size_t id = 0;
    double x = 0;       // Dimensionless descriptor, restricted to [0,1]
    double T = 300;     // Absolute temperature in kelvin
    double y = 0;       // Synthetic reference property in GPa
};

// Deterministic generator shared across compilers (no std::*distribution).
struct Rng {
    std::uint64_t state = 20261112ULL;
    std::uint64_t next() {
        state ^= state >> 12;
        state ^= state << 25;
        state ^= state >> 27;
        return state * 2685821657736338717ULL;
    }
    double unit() { return static_cast<double>(next() >> 11) * 0x1.0p-53; }
};

// The independent native C++ expression evaluator is intentionally separate
// from the paceval parser and graph execution path. This is the numeric oracle
// for per-candidate SDK arithmetic; it is NOT a real-material reference oracle.
double native(const Candidate& c, double x, double T) {
    const double common = c.a + c.b*x;
    switch (c.family) {
        case 0: return common + c.c*std::exp(-c.d/T);
        case 1: return common + c.c/(1.0+T/c.d);
        case 2: return common + c.c*std::exp(-c.d/T)+c.e*x*x;
        case 3: return common + c.c*std::exp(-c.d/T)+c.e*x*(T/300.0);
        default: throw std::runtime_error("Unapproved candidate family");
    }
}

std::string formula(const Candidate& c) {
    std::ostringstream ss;
    ss << std::setprecision(17);
    ss << "(" << c.a << ")+ (" << c.b << ")*x";
    switch(c.family) {
        case 0: ss << "+(" << c.c << ")*exp(-(" << c.d << ")/T)"; break;
        case 1: ss << "+(" << c.c << ")/(1+T/(" << c.d << "))"; break;
        case 2: ss << "+(" << c.c << ")*exp(-(" << c.d << ")/T)+(" << c.e << ")*x*x"; break;
        case 3: ss << "+(" << c.c << ")*exp(-(" << c.d << ")/T)+(" << c.e << ")*x*(T/300)"; break;
        default: throw std::runtime_error("Unapproved candidate family");
    }
    return ss.str();
}

std::vector<Candidate> candidates(size_t count) {
    Rng rng;
    std::vector<Candidate> c;
    c.reserve(count);
    // A seeded reference family intentionally appears in the candidate pool.
    // Hence this is an expression-evaluation feasibility test, not discovery.
    c.push_back(Candidate{0,0,100,25,18,500,0});
    for(size_t i=1; i<count; ++i) {
        const int family = static_cast<int>(i%4);
        c.push_back(Candidate{i,family,82+36*rng.unit(),12+30*rng.unit(),
                              8+28*rng.unit(),250+700*rng.unit(),-6+12*rng.unit()});
    }
    return c;
}

std::vector<Sample> samples() {
    std::vector<Sample> out;
    out.reserve(N);
    const Candidate truth{0,0,100,25,18,500,0};
    for (size_t i=0; i<N; ++i) {
        // Deliberate, reproducible, modest synthetic discrepancy simulating
        // measurement variability; NOT measured material-science data.
        const double x = static_cast<double>((i*37)%61)/60.0;
        const double T = 260.0+static_cast<double>((i*101)%631);
        const double noise = 0.12*std::sin(0.47*static_cast<double>(i));
        out.push_back(Sample{i,x,T,native(truth,x,T)+noise});
    }
    return out;
}

// RAII: library must initialize before any graph and be freed only AFTER all
// computation handles are deleted. Exception paths also release every handle.
class Engine {
public:
    Engine() { check(paceval_InitializeLibrary(nullptr),"paceval_InitializeLibrary failed"); }
    Engine(const Engine&) = delete;
    Engine& operator=(const Engine&) = delete;
    ~Engine() {
        for(PACEVAL_HANDLE h : handles_) if(h) paceval_DeleteComputation(h);
        paceval_FreeLibrary();
    }
    PACEVAL_HANDLE make(const Candidate& candidate) {
        const std::string expression = formula(candidate);
        // Exactly two whitespace-separated variables, in value order x,T.
        PACEVAL_HANDLE h = paceval_CreateComputation(expression.c_str(),2UL,"x T",false,nullptr);
        check(h != nullptr,"Graph creation returned null for candidate " + std::to_string(candidate.id));
        handles_.push_back(h); // Take ownership even if the SDK has set an error.
        check(!paceval_GetIsError(h),"Invalid graph for candidate " + std::to_string(candidate.id));
        return h;
    }
private:
    std::vector<PACEVAL_HANDLE> handles_;
};

struct Row { size_t id; int family; double train, val, test; bool valid; };
void write_samples(const std::string& path,const std::vector<Sample>& v) {
    std::ofstream f(path);
    check(bool(f),"Cannot write samples: "+path);
    f << "sample_id,split,x_dimensionless,T_kelvin,E_synthetic_GPa\n";
    f << std::setprecision(17);
    for(const auto& s:v) f << s.id << ',' << (s.id<TRAIN_END?"train":s.id<VAL_END?"validation":"test")
        << ',' << s.x << ',' << s.T << ',' << s.y << '\n';
    check(bool(f),"Failed writing sample CSV");
}
void write_ranking(const std::string& path,const std::vector<Row>& rows) {
    std::ofstream f(path);
    check(bool(f),"Cannot write rankings: "+path);
    f << "candidate_id,family,train_rmse_GPa,validation_rmse_GPa,dimension_valid\n";
    f << std::setprecision(17);
    for(const auto& r:rows) f << r.id << ',' << r.family << ',' << r.train << ',' << r.val << ',' << (r.valid?1:0) << '\n';
    check(bool(f),"Failed writing ranking CSV");
}
void write_selected(const std::string& path,const Candidate& c,const std::vector<Sample>& sample) {
    std::ofstream f(path);
    check(bool(f),"Cannot write predictions: "+path);
    f << "sample_id,split,candidate_id,family,a_GPa,b_GPa,c_GPa,d_kelvin,e_GPa,x_dimensionless,T_kelvin,synthetic_target_GPa,native_prediction_GPa\n";
    f << std::setprecision(17);
    for(const auto& s:sample) f << s.id << ',' << (s.id<TRAIN_END?"train":s.id<VAL_END?"validation":"test")
        << ',' << c.id << ',' << c.family << ',' << c.a << ',' << c.b << ',' << c.c << ',' << c.d << ',' << c.e
        << ',' << s.x << ',' << s.T << ',' << s.y << ',' << native(c,s.x,s.T) << '\n';
    check(bool(f),"Failed writing prediction CSV");
}

size_t read_count(int argc,char**argv,std::string& prefix) {
    size_t count=1000;
    for(int i=1;i<argc;++i) {
        std::string arg=argv[i];
        if(arg=="--test") count=40;
        else if(arg=="--candidates" && i+1<argc) count=std::stoull(argv[++i]);
        else if(arg=="--out-prefix" && i+1<argc) prefix=argv[++i];
        else throw std::runtime_error("Usage: material_candidates [--test] [--candidates 1000] [--out-prefix FILE_PREFIX]");
    }
    check(count>0 && count<=2000,"Candidate count must be from 1 to 2000");
    return count;
}

} // namespace

int main(int argc,char**argv) {
try {
    std::string prefix = "wp019";
    const size_t count = read_count(argc,argv,prefix);
    const auto work = samples();
    const auto pool = candidates(count);
    write_samples(prefix+"_samples.csv",work);
    std::vector<Row> results;
    results.reserve(count);
    size_t scalar_ok=0, batch_ok=0;
    double max_abs_delta=0;
    double checksum=0;
    {
        Engine sdk;
        for(const Candidate& c:pool) {
            // Domain and dimensional checks are host-owned. The four registered
            // equation families use coefficients with declared compatible units.
            check(c.d>0 && std::isfinite(c.a)&&std::isfinite(c.b)&&std::isfinite(c.c)
                &&std::isfinite(c.d)&&std::isfinite(c.e),"Invalid dimensional coefficient contract");
            PACEVAL_HANDLE h = sdk.make(c);
            std::array<double,3> squared = {0,0,0};
            for(const Sample& s:work) {
                double args[2]={s.x,s.T};
                const double actual=paceval_dGetComputationResult(h,args,nullptr,nullptr);
                check(!paceval_GetIsError(h),"SDK scalar computation error for candidate " + std::to_string(c.id));
                const double expected=native(c,s.x,s.T);
                check(std::isfinite(actual) && std::abs(actual-expected)<=TOL,
                      "SDK/native mismatch candidate="+std::to_string(c.id)+" sample="+std::to_string(s.id));
                max_abs_delta=std::max(max_abs_delta,std::abs(actual-expected));
                const int partition = s.id<TRAIN_END?0:(s.id<VAL_END?1:2);
                squared[partition]+=(actual-s.y)*(actual-s.y);
                checksum+=actual;
                ++scalar_ok;
            }
            // Separately exercise the paceval batch API with the SAME handle.
            // Input is row-major: x0,T0,x1,T1,..., each item has two variables.
            constexpr size_t BATCH=32;
            std::vector<double> packed(BATCH*2),out(BATCH);
            std::vector<int> errors(BATCH,0);
            for(size_t i=0;i<BATCH;++i) { packed[2*i]=work[i].x; packed[2*i+1]=work[i].T; }
            // IMPORTANT SDK 4.25 convention: false means no error (confirmed
            // on actual provided Linux library). Inspect item error codes too.
            const bool any_error=paceval_dGetComputationResultExt(h,packed.data(),
                static_cast<unsigned long>(BATCH),out.data(),nullptr,nullptr,errors.data());
            check(!any_error,"SDK batch failure for candidate " + std::to_string(c.id));
            for(size_t i=0;i<BATCH;++i) {
                check(errors[i]==PACEVAL_ERR_NO_ERROR,"SDK batch item error");
                const double expected=native(c,work[i].x,work[i].T);
                check(std::isfinite(out[i])&&std::abs(out[i]-expected)<=TOL,"Batch mismatch");
                ++batch_ok;
            }
            results.push_back(Row{c.id,c.family,
                std::sqrt(squared[0]/TRAIN_END),
                std::sqrt(squared[1]/(VAL_END-TRAIN_END)),
                std::sqrt(squared[2]/(N-VAL_END)),true});
        }
    }
    // A deliberately simple *validation-only* selection. Train scores are
    // reported, but selection uses the validation partition; the held-out test
    // set is used only for the final reported selected candidate diagnostics.
    // Here all candidate test errors are exported for reproducibility. They
    // must NOT be used to tune or reselect a candidate.
    const auto best=std::min_element(results.begin(),results.end(),
        [](const Row&a,const Row&b){return a.val<b.val || (a.val==b.val&&a.id<b.id);});
    const Candidate& selected=pool[best->id];
    write_ranking(prefix+"_ranking.csv",results);
    write_selected(prefix+"_selected.csv",selected,work);
    std::cout << std::setprecision(17)
        << "WP019 | paceval SDK material-formula feasibility: PASS\n"
        << "candidate_graphs="<<count<<" samples_per_candidate="<<N<<'\n'
        << "scalar_verified="<<scalar_ok<<" batch_verified="<<batch_ok<<'\n'
        << "max_sdk_native_absolute_GPa_difference="<<max_abs_delta<<'\n'
        << "selected_by_validation_candidate="<<best->id<<" family="<<best->family<<'\n'
        << "selected_validation_rmse_GPa="<<best->val<<" selected_test_rmse_GPa="<<best->test<<'\n'
        << "checksum="<<checksum<<'\n'
        << "Synthetic data only; no measured materials or physical law discovery.\n";
    return 0;
} catch (const std::exception& err) {
    std::cerr<<"WP019 FAIL: "<<err.what()<<'\n'; return 1;
}
}
