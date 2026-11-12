// WP-018 | Reusable Credit Risk Decision Mathematics
// Synthetic, deterministic C++17 research demonstrator. No lending decisions.
// The original official paceval_main.h/.cpp facade is used, not reimplemented.
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
constexpr std::size_t FEATURES=5;
using FeatureVector=std::array<double, FEATURES>;
struct Scorecard { FeatureVector beta{}; double intercept=0; std::size_t id=0; };
struct Case { FeatureVector values{}; };
struct Score { double probability=0; double linear_predictor=0; FeatureVector contribution{}; std::size_t reason=0; };

void require(bool ok, const std::string& why) { if(!ok) throw std::runtime_error(why); }

// Independent native reference. Stable for both signs of the linear predictor.
double logistic(double z) {
    if(z >= 0) { const double e=std::exp(-z); return 1.0/(1.0+e); }
    const double e=std::exp(z); return e/(1.0+e);
}
Score reference_score(const Scorecard& model, const Case& sample) {
    Score s; s.linear_predictor=model.intercept;
    for(std::size_t j=0;j<FEATURES;++j) {
        s.contribution[j]=model.beta[j]*sample.values[j];
        s.linear_predictor+=s.contribution[j];
    }
    s.probability=logistic(s.linear_predictor);
    // Highest positive contribution to the *synthetic log-odds*, not a legal reason code.
    s.reason=static_cast<std::size_t>(std::max_element(s.contribution.begin(),s.contribution.end())-s.contribution.begin());
    return s;
}

// Fixed integer PRNG; does not depend on the platform's distribution implementation.
struct Generator {
    std::uint64_t state=20261112ULL;
    std::uint64_t next() {
        state ^= state>>12; state ^= state<<25; state ^= state>>27;
        return state*2685821657736338717ULL;
    }
    double uniform() { return static_cast<double>(next()>>11)*0x1.0p-53; }
};
std::vector<Scorecard> make_models(std::size_t count) {
    Generator gen; std::vector<Scorecard> out(count);
    for(std::size_t m=0;m<count;++m) {
        out[m].id=m+1;
        out[m].intercept=-2.6+0.6*gen.uniform();
        for(double& b:out[m].beta) b=0.1+1.8*gen.uniform();
    }
    return out;
}
std::vector<Case> make_cases(std::size_t count) {
    Generator gen; std::vector<Case> out(count);
    for(auto& c:out) for(double& x:c.values) x=gen.uniform();
    if(count>0) out[0].values.fill(0.0);
    if(count>1) out[1].values.fill(1.0);
    return out;
}

// Paceval variable names must be SPACE-separated per the supplied official SDK.
// Formula coefficients are embedded as constants: a different model creates a new graph.
std::string make_formula(const Scorecard& m) {
    std::ostringstream os;
    os << std::setprecision(17) << "1/(1+exp(-(" << m.intercept;
    for(std::size_t j=0;j<FEATURES;++j) os << "+(" << m.beta[j] << ")*x" << j;
    os << ")))";
    return os.str();
}

// Library lifetime: init exactly once before graph construction, free after all
// graph handles have been deleted. Exceptions do not leak graph handles.
class PacevalSession {
public:
    PacevalSession() { require(paceval_InitializeLibrary(nullptr), "paceval_InitializeLibrary failed"); }
    PacevalSession(const PacevalSession&)=delete;
    PacevalSession& operator=(const PacevalSession&)=delete;
    ~PacevalSession() { for(auto h:handles_) if(h) paceval_DeleteComputation(h); paceval_FreeLibrary(); }
    PACEVAL_HANDLE create(const Scorecard& model) {
        // C-string remains valid for the duration of the SDK call.
        const std::string formula=make_formula(model);
        PACEVAL_HANDLE handle=paceval_CreateComputation(formula.c_str(),
                                static_cast<unsigned long>(FEATURES),
                                "x0 x1 x2 x3 x4", false, nullptr);
        require(handle != nullptr, "paceval_CreateComputation returned null for model "+std::to_string(model.id));
        handles_.push_back(handle); // always take ownership before inspecting error state
        require(!paceval_GetIsError(handle), "paceval formula creation error for model "+std::to_string(model.id));
        return handle;
    }
private:
    std::vector<PACEVAL_HANDLE> handles_;
};

void write_header(std::ofstream& stream) {
    stream << "model_version,case_id,intercept,b0,b1,b2,b3,b4,x0,x1,x2,x3,x4,eta,pd,dominant_logodds_feature\n";
}
void export_row(std::ofstream& stream,const Scorecard& model,const Case& input,std::size_t id,const Score& score) {
    stream << model.id << ',' << id << ',' << std::setprecision(17) << model.intercept;
    for(double b:model.beta) stream << ',' << b;
    for(double x:input.values) stream << ',' << x;
    stream << ',' << score.linear_predictor << ',' << score.probability << ',' << score.reason << '\n';
}

} // namespace

int main(int argc,char** argv) {
    try {
        std::size_t model_count=100,case_count=100;
        std::string output="scorecard_samples.csv";
        for(int i=1;i<argc;++i) {
            const std::string a=argv[i];
            if(a=="--test") {model_count=10;case_count=80;}
            else if(a=="--models" && i+1<argc) model_count=std::stoull(argv[++i]);
            else if(a=="--cases" && i+1<argc) case_count=std::stoull(argv[++i]);
            else if(a=="--out" && i+1<argc) output=argv[++i];
            else {std::cerr << "Usage: credit_scorecard [--test] [--models 100] [--cases 100] [--out path.csv]\n";return 2;}
        }
        require(model_count>0 && model_count<=1000 && case_count>=2 && case_count<=1000000,"Invalid workload size");
        const auto models=make_models(model_count);
        const auto samples=make_cases(case_count);
        std::ofstream csv(output);
        require(static_cast<bool>(csv), "Cannot open output CSV: "+output);
        write_header(csv);
        const std::size_t export_count=std::min<std::size_t>(100,case_count);
        std::size_t scalar_checked=0,batch_checked=0;
        double max_abs_difference=0.0;
        double checksum=0.0;
        const double tolerance=1e-10;
        {
            PacevalSession paceval;
            // Each scorecard has its own immutable formula graph and handle.
            // Creating it *once* allows reuse across many independent borrower-like
            // feature vectors without reparsing the expression for every sample.
            for(const auto& model:models) {
                PACEVAL_HANDLE graph=paceval.create(model);
                for(std::size_t i=0;i<samples.size();++i) {
                    const Score ref=reference_score(model,samples[i]);
                    // The C API accepts a mutable contiguous array of exactly five doubles.
                    FeatureVector args=samples[i].values;
                    const double actual=paceval_dGetComputationResult(graph,args.data(),nullptr,nullptr);
                    require(!paceval_GetIsError(graph), "paceval scalar evaluation error");
                    require(std::isfinite(actual), "Nonfinite paceval output");
                    const double delta=std::abs(actual-ref.probability);
                    max_abs_difference=std::max(max_abs_difference,delta);
                    require(delta<=tolerance, "paceval/native scalar mismatch, model="+std::to_string(model.id)+" case="+std::to_string(i));
                    require(ref.reason<FEATURES, "Invalid feature contribution index");
                    checksum += actual;
                    ++scalar_checked;
                    if(i<export_count) export_row(csv,model,samples[i],i,ref);
                }
                // Separate SDK batch-API feasibility check using the SAME graph.
                // The public API requires row-major packing: for each case five
                // consecutive feature values. Only 64 deterministic cases are used
                // in this independent batch test; no performance comparison is made.
                const std::size_t batch_size=std::min<std::size_t>(64,samples.size());
                std::vector<double> packed(batch_size*FEATURES);
                std::vector<double> results(batch_size);
                std::vector<int> errors(batch_size,0);
                for(std::size_t i=0;i<batch_size;++i)
                    for(std::size_t j=0;j<FEATURES;++j)
                        packed[i*FEATURES+j]=samples[i].values[j];
                const bool ok=paceval_dGetComputationResultExt(graph,packed.data(),
                    static_cast<unsigned long>(batch_size),results.data(),nullptr,nullptr,errors.data());
                // In API 4.25 the bool indicates whether an error occurred: false = no error.
                require(!ok, "paceval batch reported a computation error");
                for(std::size_t i=0;i<batch_size;++i) {
                    require(errors[i]==PACEVAL_ERR_NO_ERROR, "paceval batch item error");
                    const double expected=reference_score(model,samples[i]).probability;
                    require(std::isfinite(results[i]) && std::abs(results[i]-expected)<=tolerance,
                            "paceval/native batch mismatch");
                    max_abs_difference=std::max(max_abs_difference,std::abs(results[i]-expected));
                    ++batch_checked;
                }
            }
        } // all graph handles destroyed; then paceval_FreeLibrary() called
        require(static_cast<bool>(csv),"CSV write failed");
        std::cout << std::setprecision(17)
                  << "WP018 | Synthetic research only | paceval SDK execution PASS\n"
                  << "models="<<model_count<<" cases_per_model="<<case_count<<'\n'
                  << "scalar_verified="<<scalar_checked<<" batch_verified="<<batch_checked<<'\n'
                  << "max_absolute_pd_difference="<<max_abs_difference<<'\n'
                  << "paceval_result_checksum="<<checksum<<'\n'
                  << "exported_rows="<<model_count*export_count<<'\n'
                  << "No credit-risk calibration or regulatory compliance is claimed.\n";
        return 0;
    } catch(const std::exception& e) {
        std::cerr << "FAILED: " << e.what() << '\n'; return 1;
    }
}
