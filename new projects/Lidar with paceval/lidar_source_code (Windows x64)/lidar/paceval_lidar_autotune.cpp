// SPDX-License-Identifier: Proprietary
// ============================================================================
// COMPONENT : paceval LiDAR Geometry Processing Demonstrator
// PURPOSE   : Deterministic offline evaluation of cell-wise LiDAR covariance
//             and geometric descriptors using reusable paceval computations.
// TARGET    : C++17; Windows x64 (Visual Studio) and Linux x64 (GCC).
// ALGORITHM : paceval analytic symmetric 3x3 eigenvalues with selective paceval-Jacobi fallback.
// SPEED PATH: paceval batches analytic eigenspectrum expressions;
// near-degenerate covariances use verified paceval-Jacobi fallback.
//             Numerical invariants are normalized and conditioned in C++;
//             paceval evaluates one analytical angle expression per eligible matrix.
// INPUT     : CSV columns frame,x,y,z (Cartesian coordinates; units must agree).
// OUTPUT    : Cell-wise feature CSV and timestamped execution log.
// DATA      : Features are per angular bin, not a true spatial-neighborhood PCA.
//             Point density, range and object boundaries may bias descriptors.
// LIMITS    : No real-time deadline, sensor safety case, ISO 26262 compliance,
//             object detection, tracking, or production fault containment.
//             Input values are assumed to be finite, but sensor calibration,
//             point provenance and measurement uncertainty are not modeled.
// NUMERICS  : Covariance is population-normalized (N), not sample (N-1).
//             Matrix-relative convergence and dimensionless residual tests.
// CONTROL   : C++ manages cell grouping, analytic guards and fallback pivots;
//             paceval evaluates reusable analytic expressions and Jacobi parameters.
// PRECOND   : Input coordinates and derived covariances must be finite;
//             each processed bin must meet the configured minimum point count.
// FAILURE   : File, paceval or numerical failures raise errors or mark per-cell
//             invalid-quality status; no automotive fail-operational promise.
// VERIFY    : Analytic known-spectrum and scale/degeneracy regression tests.
// PROFILE   : CSV I/O, binning, covariance, eigenspectrum, features and
//             fallback sweeps are timed separately; no WCET claim is made.
// TINC      : Optional isolated Jacobi-formula diagnostics, not a certification
//             of analytic eigenvalue graphs; trace-based C++ updates are not
//             interval-propagated.
//             The intervals do NOT certify the analytic/hybrid eigensolver.
//             These checks are not formal verification or safety certification.
// ============================================================================
#ifndef NOMINMAX
#define NOMINMAX
#endif
#include <algorithm>
#include <array>
#include <chrono>
#include <cmath>
#include <cstdint>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <limits>
#include <map>
#include <stdexcept>
#include <string>
#include <vector>
#include <sstream>
#include <cstdlib>
#include <numeric>
#include <memory>
#if defined(_WIN32)
#include <windows.h>
#else
#include <filesystem>
#endif
// Defensive: other Windows/SDK headers can still define these macros.
#ifdef min
#undef min
#endif
#ifdef max
#undef max
#endif
#include "../../system-independent/source_public/inc/paceval_main.h"

// ============================================================================
// BUILD-TIME DEFAULT: OPTIONAL TINC VALIDATION
// Set to true to perform additional interval diagnostics after each LiDAR CSV
// is processed. Set to false to keep TINC diagnostics disabled by default.
// The production Jacobi solver and batch autotuning ALWAYS run without TINC.
// These intervals cover selected paceval formula evaluations only; they do
// not establish certified eigenvalue bounds or automotive functional safety.
// Optional environment override: PACEVAL_LIDAR_VALIDATE_TINC=0 or =1.
// The environment override takes precedence over this source-code default.
// ============================================================================
static constexpr bool PACEVAL_LIDAR_VALIDATE_TINC = false; // true = ON, false = OFF
// Suppress repetitive per-candidate diagnostics during startup timing.
static bool g_startupBenchmarkActive = false;

// DIAGNOSTICS: monotonic elapsed-time stamps, identical on-screen/file messages.
// NOTE: logging is best-effort observability; it is not a safety event recorder.
// Human-readable scientific values in diagnostics. A fixed-decimal conversion
// would print 1e-120 as 0.000000 and produce hundreds of digits for 1e+120.
static std::string diagnosticScientific(double value, int precision = 3) {
    std::ostringstream os;
    os << std::scientific << std::setprecision(precision) << value;
    return os.str();
}

static bool ensureOutputDirectory() {
#if defined(_WIN32)
    return CreateDirectoryA("output", nullptr) || GetLastError()==ERROR_ALREADY_EXISTS;
#else
    std::filesystem::create_directories("output"); return true;
#endif
}

namespace console_elapsed {
    using Clock = std::chrono::steady_clock;

    // Stream each already time-stamped line to both console and a persistent
    // UTF-8-compatible text log. Flush the file at every newline, so partial
    // runs and failures remain available even if the process is interrupted.
    class LinePrefixBuffer : public std::streambuf {
        std::streambuf* destination_;
        std::streambuf* log_;
        Clock::time_point start_;
        bool atLineStart_ = true;

        void emit(const char* data, std::streamsize count) {
            destination_->sputn(data, count);
            if (log_) log_->sputn(data, count);
        }
        void writeOne(char c) {
            if (atLineStart_) {
                const double elapsed = std::chrono::duration<double>(Clock::now() - start_).count();
                std::ostringstream prefix;
                prefix << "[+" << std::fixed << std::setprecision(3) << elapsed << "s] ";
                const std::string stamp = prefix.str();
                emit(stamp.data(), static_cast<std::streamsize>(stamp.size()));
                atLineStart_ = false;
            }
            emit(&c, 1);
            if (c == '\n') {
                atLineStart_ = true;
                if (log_) log_->pubsync();
            }
        }
    public:
        LinePrefixBuffer(std::streambuf* destination, std::streambuf* log,
                         Clock::time_point start)
            : destination_(destination), log_(log), start_(start) {}
    protected:
        int_type overflow(int_type ch) override {
            if (traits_type::eq_int_type(ch, traits_type::eof()))
                return traits_type::not_eof(ch);
            writeOne(traits_type::to_char_type(ch));
            return ch;
        }
        std::streamsize xsputn(const char* data, std::streamsize size) override {
            for (std::streamsize i = 0; i < size; ++i) writeOne(data[i]);
            return size;
        }
        int sync() override {
            if (log_) log_->pubsync();
            return destination_->pubsync();
        }
    };

    class ScopedConsoleTimestamps {
        // Member order matters: the file must outlive both stream buffers.
        std::ofstream log_;
        LinePrefixBuffer out_;
        LinePrefixBuffer err_;
        std::streambuf* savedOut_;
        std::streambuf* savedErr_;
    public:
        explicit ScopedConsoleTimestamps(Clock::time_point start)
            : log_(((ensureOutputDirectory(), true),
                    "output/paceval_lidar_run.log"), std::ios::out | std::ios::trunc),
              out_(std::cout.rdbuf(), log_.rdbuf(), start),
              err_(std::cerr.rdbuf(), log_.rdbuf(), start),
              savedOut_(std::cout.rdbuf()), savedErr_(std::cerr.rdbuf()) {
            if (!log_) throw std::runtime_error(
                "Cannot open output\\paceval_lidar_run.log for writing");
            std::cout.rdbuf(&out_);
            std::cerr.rdbuf(&err_);
        }
        ~ScopedConsoleTimestamps() {
            std::cout.flush();
            std::cerr.flush();
            std::cout.rdbuf(savedOut_);
            std::cerr.rdbuf(savedErr_);
            log_.flush();
        }
        ScopedConsoleTimestamps(const ScopedConsoleTimestamps&) = delete;
        ScopedConsoleTimestamps& operator=(const ScopedConsoleTimestamps&) = delete;
    };
}

namespace lidar {
	using Clock = std::chrono::steady_clock;
	static constexpr double PI = 3.1415926535897932384626433832795;
	struct Point { double x, y, z; };
	// Online centered second moments (Welford): avoids E[x*x]-E[x]^2 cancellation.
	struct Moments {
		unsigned n = 0;
		double mx = 0, my = 0, mz = 0;
		double xx = 0, xy = 0, xz = 0, yy = 0, yz = 0, zz = 0;
		void add(Point p) {
			++n;
			const double dx = p.x - mx, dy = p.y - my, dz = p.z - mz;
			const double inv = 1.0 / static_cast<double>(n);
			mx += dx * inv; my += dy * inv; mz += dz * inv;
			const double ex = p.x - mx, ey = p.y - my, ez = p.z - mz;
			xx += dx * ex; xy += dx * ey; xz += dx * ez;
			yy += dy * ey; yz += dy * ez; zz += dz * ez;
		}
	};
	struct Mat { double a, b, c, d, e, f; };
    // NUMERICAL CONTRACT: this norm is homogeneous: norm(alpha*A)=|alpha|*norm(A).
    // Do not clamp it to 1.0: very small valid covariances must retain accuracy.
    static double matrixScale(const Mat& m) {
        return (std::max)({std::abs(m.a),std::abs(m.b),std::abs(m.c),
                           std::abs(m.d),std::abs(m.e),std::abs(m.f)});
    }
    static Mat scaledMatrix(const Mat& m, double scale) {
        return {m.a/scale,m.b/scale,m.c/scale,m.d/scale,m.e/scale,m.f/scale};
    }
    // Relative off-diagonal termination threshold. The normalized matrix has
    // max absolute element <=1, avoiding under/overflow in the Jacobi rotations.
    static constexpr double JACOBI_REL_TOL = 1e-13;
    static constexpr double RESIDUAL_REL_TOL = 1e-8;

	using Eig = std::array<double, 3>;
	struct Cell { int frame, az, el; Mat cov; unsigned count; };
	struct MomentCell { int frame, az, el; Moments moments; };
	struct MathBatchTiming { double covarianceMs=0, featureMs=0; size_t covarianceCalls=0, featureCalls=0; };
	struct Config {
		unsigned azBins = 2048, elBins = 64;
		double minElevation = -0.5, maxElevation = 0.5; // radians
		unsigned minPointsPerCell = 3;
	};
	static Config g_config;
	struct Ingestion { std::map<int, std::vector<Point>> frames; size_t rows = 0; double milliseconds = 0; };
	// Read environment variables without MSVC C4996 warnings. The allocated
	// _dupenv_s buffer is copied into std::string and released immediately.
	static std::string readEnvironment(const char* name) {
#if defined(_MSC_VER)
		char* buffer = nullptr;
		size_t length = 0;
		const errno_t err = _dupenv_s(&buffer, &length, name);
		if (err != 0) {
			std::free(buffer);
			throw std::runtime_error(std::string("Cannot read environment variable: ") + name);
		}
		const std::string value = buffer ? std::string(buffer) : std::string();
		std::free(buffer);
		return value;
#else
		const char* value = std::getenv(name);
		return value ? std::string(value) : std::string();
#endif
	}
	static unsigned readEnvUnsigned(const char* name, unsigned fallback, unsigned lo, unsigned hi) {
		const std::string value = readEnvironment(name);
		if (value.empty()) return fallback;
		const char* v = value.c_str();
		char* end = nullptr;
		const unsigned long parsed = std::strtoul(v, &end, 10);
		if (end == v || *end != '\0' || parsed < lo || parsed > hi)
			throw std::runtime_error(std::string("Invalid ") + name + " (allowed " + std::to_string(lo) + ".." + std::to_string(hi) + ")");
		return static_cast<unsigned>(parsed);
	}
	static double readEnvDouble(const char* name, double fallback) {
		const std::string value = readEnvironment(name);
		if (value.empty()) return fallback;
		const char* v = value.c_str();
		char* end = nullptr;
		const double x = std::strtod(v, &end);
		if (end == v || *end != '\0' || !std::isfinite(x))
			throw std::runtime_error(std::string("Invalid ") + name);
		return x;
	}
	static double ms(Clock::time_point a, Clock::time_point b) { return std::chrono::duration<double, std::milli>(b - a).count(); }
	static void apiCheck(int error, size_t k, const char*name) { if (error)throw std::runtime_error(std::string("paceval ") + name + " error=" + std::to_string(error) + " index=" + std::to_string(k)); }
	// Allocated once per solver; all buffers and handles persist across iterations.
	// Output layout of the paceval multi-computation API is function-major.
	class Handles {
		std::vector<PACEVAL_HANDLE> v;
		std::vector<int> errors;
		std::vector<PACEVAL_HANDLE> callHandles;
	public:
		Handles(const std::vector<std::string>& expr, const char* vars, unsigned n) {
			try {
				for (const auto& f : expr) {
					PACEVAL_HANDLE h = paceval_CreateComputation(f.c_str(), n, vars, false, nullptr);
					if (!h || paceval_GetIsError(h)) {
						if (h)paceval_DeleteComputation(h);
						throw std::runtime_error("paceval_CreateComputation failed for: " + f);
					}
					v.push_back(h);
				}
			}
			catch (...) { for (auto h : v)paceval_DeleteComputation(h); throw; }
			callHandles = v;
		}
		~Handles() { for (auto h : v)paceval_DeleteComputation(h); }
		Handles(const Handles&) = delete; Handles&operator=(const Handles&) = delete;
		// No buffer allocation in the timed API call after initial capacities are reached.
		void batch(double* in, unsigned /* nInputs */, size_t N, std::vector<double>& out) {
			if (N == 0) { out.clear(); return; }
			if (!in)throw std::runtime_error("Null paceval batch input");
			if (N > static_cast<size_t>((std::numeric_limits<unsigned long>::max)()))
				throw std::runtime_error("paceval batch size exceeds unsigned long API limit");
			const size_t count = N * v.size();
			out.resize(count); errors.resize(count);
			std::fill(errors.begin(), errors.end(), 0);
			const bool apiReportsError = paceval_dGetMultipleComputationsResultsExt(
				callHandles.data(), static_cast<unsigned long>(v.size()), in,
				static_cast<unsigned long>(N), out.data(), nullptr, nullptr, errors.data());
			for (size_t j = 0; j < count; ++j) {
				apiCheck(errors[j], j, "batch");
				if (!std::isfinite(out[j]))throw std::runtime_error("Nonfinite paceval result at " + std::to_string(j));
			}
			if (apiReportsError)throw std::runtime_error("paceval batch API reports an error without a nonzero result code");
		}
	};

	// Persistent mathematical execution graphs. Initialized once after library startup;
	// shared across incoming LiDAR frames, destroyed before paceval_FreeLibrary.
	static std::unique_ptr<Handles> g_covCalc, g_featureCalc, g_angleCalc, g_jacobiCalc;
	static void initializePersistentComputations() {
		const auto begin=Clock::now();
		const std::string tau="((d-a)/(2*b))";
		const std::string t="(sgn/((sgn*"+tau+")+sqrt(1+("+tau+")*("+tau+"))))";
		g_jacobiCalc.reset(new Handles({t}, "a d b u v sgn",6));
		g_angleCalc.reset(new Handles({"(acos(r)/3)"}, "q p r",3));
		g_covCalc.reset(new Handles({"(xx/n)","(xy/n)","(xz/n)","(yy/n)","(yz/n)","(zz/n)"},
			"xx xy xz yy yz zz n",7));
		const std::string poly="((((x-tr)*x+s2)*x-det))";
		const std::string res="(sqrt(("+poly+")*("+poly+"))/(scale*scale*scale))";
		auto replaceX=[](std::string str,const std::string& x){
			std::string::size_type at=0;
			while((at=str.find("x",at))!=std::string::npos){str.replace(at,1,x);at+=x.size();}
			return str;
		};
		g_featureCalc.reset(new Handles({"((l1-l2)/l1)","((l2-l3)/l1)","(l3/l1)","(l3/(l1+l2+l3))",
			replaceX(res,"l1"),replaceX(res,"l2"),replaceX(res,"l3")},"l1 l2 l3 tr s2 det scale",7));
		std::cout<<"[PERSISTENT INIT] computations=15 initialized_before_frames_ms="
			<<ms(begin,Clock::now())<<"\n";
	}
	static void releasePersistentComputations() {
		g_featureCalc.reset();g_covCalc.reset();g_angleCalc.reset();g_jacobiCalc.reset();
	}

	struct SolverTiming {
		double apiMs = 0, packingMs = 0, controlMs = 0;
		size_t calls = 0;
	};
	static size_t g_batchLimit = 0; // 0 = full active set; startup calibration chooses a measured chunk unless overridden.
    // Full-active mode maximizes inter-matrix concurrency for each independent Jacobi sweep.
    // Restrict each API call to the validated 1,048,576-item safety ceiling.
    static bool g_fullActiveBatch = true;
	static bool g_batchWasCalibrated = false;
	static bool g_pacevalCovariance = false; // Batch Welford moment normalization via paceval.
	static bool g_pacevalFeatures = false;   // Batch four descriptors + three residuals.
	static bool g_validateTinc = false; // Optional diagnostics, never in production path or tuner.
	static unsigned g_tincSamples = 12;
	static double g_tincWidthLimit = 1e-9; // Width relative to max(1,abs(value)) of normalized formula result.
	static double g_tincDegenerateLimit = 1e-8; // Relative eigenvalue/gap threshold.
	static size_t batchSize(size_t remaining) {
        if (g_fullActiveBatch) return (std::min)(remaining, static_cast<size_t>(1048576));
        return g_batchLimit ? (std::min)(g_batchLimit, remaining) : remaining;
    }

    // Fast adaptive startup calibration: one real paceval Jacobi batch for each
    // candidate, ascending by 32,768 items. Unlike the older method, this does
    // NOT reprocess a fixed million-item workload for every candidate.
    // Throughput (items/second), rather than raw duration, is compared because
    // candidate batch sizes differ. This is a heuristic, not a proof of optimum.
    // A soft global time budget avoids needlessly lengthy startup; a running
    // paceval API call itself cannot be interrupted. The default ceiling of
    // 1,048,576 is a *safety limit*, not a measured SDK optimum.
    static void calibrateBatchSize() {
        const size_t STEP=32768;
        const size_t HARD_MAX=1048576;
        const size_t maxChunk=readEnvUnsigned("PACEVAL_LIDAR_AUTOTUNE_MAX_BATCH",1048576,32768,1048576);
        const double budgetMs=readEnvDouble("PACEVAL_LIDAR_AUTOTUNE_BUDGET_MS",6500.0);
        const double slowdownPct=readEnvDouble("PACEVAL_LIDAR_AUTOTUNE_SLOWDOWN_PCT",5.0);
        // Calibrate the exact same single paceval Jacobi parameter graph used in production.
        // The predicted duration guard protects against unexpectedly slow tests.
        const double maxTrialMs=readEnvDouble("PACEVAL_LIDAR_AUTOTUNE_MAX_TRIAL_MS",2000.0);
        if (!(budgetMs>=0.0 && budgetMs<=3600000.0) ||
            !(slowdownPct>=0.0 && slowdownPct<=50.0) ||
            !(maxTrialMs>=0.0 && maxTrialMs<=3600000.0))
            throw std::runtime_error("Invalid autotune time or slowdown setting");
        const std::string tau="((d-a)/(2*b))";
        const std::string t="(sgn/((sgn*"+tau+")+sqrt(1+("+tau+")*("+tau+"))))";
        const std::string co="(1/sqrt(1+("+t+")*("+t+")))";
        const std::string si="(("+t+")*("+co+"))";
        Handles calc({t},"a d b u v sgn",6);
        // Reserve only a single candidate's buffers at a time.
        std::vector<double> inputs,results;
        auto fillInputs = [&](size_t N) {
            inputs.resize(N*6);
            for (size_t i=0;i<N;++i) {
                const double z=static_cast<double>(i%997)/997.0;
                inputs[6*i+0]=2.0+z;
                inputs[6*i+1]=3.0+z*0.5;
                inputs[6*i+2]=0.05+0.01*z;
                inputs[6*i+3]=0.1+z*0.02;
                inputs[6*i+4]=0.04+z*0.01;
                inputs[6*i+5]=(i%2)?-1.0:1.0;
            }
        };
        // One small global warmup, excluded from timing.
        fillInputs(1024);
        calc.batch(inputs.data(),6,1024,results);
        const auto tuneStart=Clock::now();
        std::cout<<"[BATCH AUTO FAST] step=32768 max_chunk="<<maxChunk
                 <<" hard_max="<<HARD_MAX<<" budget_ms="<<budgetMs
                 <<" trial_guard_ms="<<maxTrialMs
                 <<" slowdown_pct="<<slowdownPct
                 <<" mode=production-single-formula throughput-comparison (single warmup)\n";
        size_t bestSize=0;
        double bestRate=0.0;
        double bestMs=0.0;
        double previousMs=0.0;
        size_t previousN=0;
        for (size_t chunk=STEP; chunk<=maxChunk; chunk+=STEP) {
            const double used=ms(tuneStart,Clock::now());
            if (bestSize && budgetMs>0.0 && used>=budgetMs) {
                std::cout<<"[BATCH AUTO FAST] STOP: global time budget reached\n";
                break;
            }
            // Predict duration from the last measured throughput. A large
            // single SDK call can otherwise exceed the soft time budget.
            if (bestSize && previousMs>0.0 && previousN>0) {
                const double projected=previousMs*static_cast<double>(chunk)/previousN;
                if ((maxTrialMs>0.0 && projected>maxTrialMs) ||
                    (budgetMs>0.0 && used+projected>budgetMs)) {
                    std::cout<<"[BATCH AUTO FAST] STOP: predicted next call "
                             <<std::fixed<<std::setprecision(1)<<projected
                             <<" ms exceeds remaining calibration budget / per-call guard\n";
                    break;
                }
            }
            fillInputs(chunk);
            // Reuse output/error allocations on the next candidate; untimed
            // input construction is excluded from the SDK throughput timing.
            const auto started=Clock::now();
            calc.batch(inputs.data(),6,chunk,results);
            const double elapsed=ms(started,Clock::now());
            previousMs=elapsed; previousN=chunk;
            // Verify 32 deterministic points distributed across the batch
            // against independent host arithmetic. Handles.batch itself also
            // rejects all per-item errors and non-finite outputs.
            bool valid=true;
            for (size_t k=0;k<32;++k) {
                const size_t i=k*(chunk-1)/31;
                const double a=inputs[6*i],d=inputs[6*i+1],b=inputs[6*i+2];
                const double u=inputs[6*i+3],v=inputs[6*i+4],sgn=inputs[6*i+5];
                const double tauValue=(d-a)/(2.0*b);
                const double tv=sgn/(sgn*tauValue+std::sqrt(1+tauValue*tauValue));
                const double cv=1/std::sqrt(1+tv*tv),sv=tv*cv;
                const double expected[3]={a-tv*b,cv*u-sv*v,sv*u+cv*v};
                for (size_t f=0;f<3;++f)
                    if (!std::isfinite(results[f*chunk+i]) ||
                        std::abs(results[f*chunk+i]-expected[f])>
                        1e-10*(std::max)(1.0,std::abs(expected[f]))) valid=false;
            }
            const double rate=1000.0*static_cast<double>(chunk)/(std::max)(elapsed,1e-9);
            std::cout<<"[BATCH AUTO FAST] chunk="<<chunk<<" calls=1 ms="
                     <<std::fixed<<std::setprecision(3)<<elapsed
                     <<" rotations_per_s="<<std::setprecision(1)<<rate
                     <<" verified="<<(valid?"yes":"NO")<<"\n";
            if (!valid) {
                std::cout<<"[BATCH AUTO FAST] STOP: numeric verification failed\n";
                break;
            }
            if (rate>bestRate) {
                bestRate=rate; bestMs=elapsed; bestSize=chunk;
                std::cout<<"[BATCH AUTO FAST] new best="<<bestSize
                         <<" throughput="<<bestRate<<" rotations/s\n";
            } else if (bestRate>0.0 && rate<bestRate*(1.0-slowdownPct/100.0)) {
                std::cout<<"[BATCH AUTO FAST] STOP: throughput "
                         <<std::fixed<<std::setprecision(1)
                         <<100.0*(1.0-rate/bestRate)
                         <<"% below best; retaining batch="<<bestSize<<"\n";
                break;
            }
        }
        if (bestSize) {
            g_batchLimit=bestSize;
            g_batchWasCalibrated=true;
            std::cout<<"[BATCH AUTO FAST] SELECTED limit="<<bestSize
                     <<" measured_ms="<<bestMs
                     <<" rotations_per_s="<<bestRate
                     <<" total_calibration_ms="<<ms(tuneStart,Clock::now())<<"\n";
            if (bestSize==maxChunk)
                std::cout<<"[BATCH AUTO FAST] Reached configured safety ceiling without confirmed slowdown.\n";
        } else {
            g_batchLimit=0;
            std::cout<<"[BATCH AUTO FAST] WARNING: No verified chunk; using full active batch.\n";
        }
        // One chunk limit is shared by Jacobi, covariance and features. Their
        // optimal chunk sizes may differ: this calibration times Jacobi only.
    }

	static std::vector<std::string> filesInData() {
        std::vector<std::string> out;
#if defined(_WIN32)
        WIN32_FIND_DATAA data={};HANDLE h=FindFirstFileA("data\\*.csv",&data);
        if(h!=INVALID_HANDLE_VALUE){do{if(!(data.dwFileAttributes & FILE_ATTRIBUTE_DIRECTORY))
            out.push_back(std::string("data\\")+data.cFileName);
        }while(FindNextFileA(h,&data));FindClose(h);}
#else
        if (std::filesystem::exists("data"))
            for (const auto& p : std::filesystem::directory_iterator("data"))
                if (p.is_regular_file() && p.path().extension()==".csv") out.push_back(p.path().string());
#endif
        std::sort(out.begin(),out.end());return out;
    }

	static std::map<int, std::vector<Point>> readCsv(const std::string&path) {
		std::ifstream in(path); if (!in)throw std::runtime_error("Cannot open " + path);
		std::map<int, std::vector<Point>> frames; std::string line; size_t lineno = 0;
		while (std::getline(in, line)) {
			++lineno; if (line.empty() || line[0] == '#')continue;
			std::replace(line.begin(), line.end(), ';', ','); std::stringstream ss(line); std::string fields[4];
			for (int k = 0; k < 4; ++k) { if (!std::getline(ss, fields[k], ','))throw std::runtime_error("Bad CSV columns line " + std::to_string(lineno)); }
			if (fields[0] == "frame" || fields[0] == "Frame")continue;
			try {
				int frame = std::stoi(fields[0]); Point p = { std::stod(fields[1]),std::stod(fields[2]),std::stod(fields[3]) };
				if (frame < 0 || !std::isfinite(p.x) || !std::isfinite(p.y) || !std::isfinite(p.z))throw std::runtime_error("nonfinite");
				frames[frame].push_back(p);
			}
			catch (...) { throw std::runtime_error("Invalid CSV value on line " + std::to_string(lineno)); }
		}
		if (frames.empty())throw std::runtime_error("CSV has no points: " + path);
		return frames;
	}
	// Dense per-frame angular grid. Only occupied bins with enough points become cells.
	static std::vector<MomentCell> collectCells(const std::map<int, std::vector<Point>>& frames,
		size_t& points, size_t& inField, size_t& validPoints, size_t& occupied) {
		std::vector<MomentCell> result;
		points = inField = validPoints = occupied = 0;
		const unsigned NA = g_config.azBins, NE = g_config.elBins;
		const double emin = g_config.minElevation, emax = g_config.maxElevation;
		for (const auto& frame : frames) {
			std::vector<Moments> bins(static_cast<size_t>(NA) * NE);
			for (const Point& p : frame.second) {
				++points;
				const double xy = std::hypot(p.x, p.y);
				const double r = std::hypot(xy, p.z);
				if (!(r > 0.0) || !std::isfinite(r)) continue;
			double az = std::atan2(p.y, p.x); if (az < 0.0) az += 2.0 * PI;
				const double el = std::atan2(p.z, xy);
				if (el < emin || el > emax) continue;
				++inField;
				const unsigned ia = (std::min)(NA - 1, static_cast<unsigned>(az * NA / (2.0 * PI)));
				const unsigned ie = (std::min)(NE - 1, static_cast<unsigned>((el - emin) * NE / (emax - emin)));
				bins[static_cast<size_t>(ia) * NE + ie].add(p);
			}
			for (unsigned ia = 0; ia < NA; ++ia) for (unsigned ie = 0; ie < NE; ++ie) {
				const Moments& m = bins[static_cast<size_t>(ia) * NE + ie];
				if (m.n) ++occupied;
				if (m.n < g_config.minPointsPerCell) continue;
				result.push_back({frame.first,static_cast<int>(ia),static_cast<int>(ie),m});
				validPoints += m.n;
			}
		}
		return result;
	}

	// PREPROCESSING: Welford online centered moments are accumulated per bin.
	// Parallel implementations may merge partial Welford accumulators; the current
	// stream-oriented implementation updates each bin sequentially. paceval
	// evaluates the six population-covariance normalizations in batches.
	// The optional native normalization is not an alternative eigensolver.
	static std::vector<Cell> normalizeCovariance(const std::vector<MomentCell>& source,
		MathBatchTiming& timing) {
		std::vector<Cell> cells;
		cells.reserve(source.size());
		if (source.empty()) return cells;
		if (!g_pacevalCovariance) {
			for (const auto& s : source) {
				const double inv = 1.0/static_cast<double>(s.moments.n);
				const Moments& m = s.moments;
				cells.push_back({s.frame,s.az,s.el,{m.xx*inv,m.xy*inv,m.xz*inv,
					m.yy*inv,m.yz*inv,m.zz*inv},m.n});
			}
			return cells;
		}
		Handles& calc=*g_covCalc;
		std::vector<double> input, output;
		const size_t reserve = g_batchLimit ? (std::min)(g_batchLimit,source.size()) : source.size();
		input.reserve(7*reserve); output.reserve(6*reserve);
		for (size_t offset=0;offset<source.size();) {
			const size_t chunk = batchSize(source.size()-offset);
			input.clear();
			for (size_t j=0;j<chunk;++j) {
				const Moments& m=source[offset+j].moments;
				input.insert(input.end(),{m.xx,m.xy,m.xz,m.yy,m.yz,m.zz,static_cast<double>(m.n)});
			}
			const auto start=Clock::now();
			calc.batch(input.data(),7,chunk,output);
			timing.covarianceMs+=ms(start,Clock::now()); ++timing.covarianceCalls;
			for (size_t j=0;j<chunk;++j) {
				const auto& cell=source[offset+j];
				cells.push_back({cell.frame,cell.az,cell.el,
					{output[j],output[chunk+j],output[2*chunk+j],output[3*chunk+j],
					output[4*chunk+j],output[5*chunk+j]},cell.moments.n});
			}
			offset+=chunk;
		}
		return cells;
	}

	// Timing and workload counters for ONE Jacobi sweep. A sweep selects at
    // most one pivot rotation per covariance matrix. No additional paceval
    // calls are made for instrumentation, and no solver decisions are changed.
    struct JacobiSweepStats {
        unsigned sweep = 0;
        size_t matrices = 0, active = 0, apiCalls = 0;
        size_t minChunk = 0, maxChunk = 0;
        double packingMs = 0, apiMs = 0, updatesMs = 0, elapsedMs = 0;
    };
    struct SolverResult { std::vector<JacobiSweepStats> sweeps; std::vector<Eig> eigen; std::vector<unsigned char> converged;
		double milliseconds = 0, handleMs = 0; unsigned iterations = 0;
		size_t evaluations = 0, unconverged = 0, fallbackMatrices = 0; SolverTiming timing; };
	// paceval evaluates one reusable Jacobi rotation parameter graph in batches. C++ selects
	// pivots, computes signs, schedules calls, performs rotations, and sorts eigenvalues.
	// This is NOT a claim that the entire LiDAR pipeline is computed by paceval.
	static SolverResult jacobiReference(const std::vector<Cell>&cells) {
		// t = sign(tau)/(abs(tau)+hypot(1,tau)), tau=(d-a)/(2*b).
		// The equivalent sign-input formula avoids catastrophic cancellation.
		// sgn is chosen in host control, while trigonometric-free rotations are
		// calculated by the reusable paceval graphs.
		const std::string tau = "((d-a)/(2*b))";
		const std::string t = "(sgn/((sgn*" + tau + ")+sqrt(1+(" + tau + ")*(" + tau + "))))";
		const auto handleStart = Clock::now();
		Handles& calc=*g_jacobiCalc;
		const double handleMs = ms(handleStart, Clock::now());
        // Normalize each matrix before iterating. Jacobi is homogeneous under
        // positive scaling. This protects tau, tau*tau and intermediate squares
        // for inputs spanning many orders of magnitude; rescale eigenvalues later.
        std::vector<Mat> mats; mats.reserve(cells.size());
        std::vector<double> scales; scales.reserve(cells.size());
        for (const auto& c : cells) {
            const double scale = matrixScale(c.cov);
            if (!std::isfinite(scale)) throw std::runtime_error("Nonfinite covariance matrix");
            scales.push_back(scale);
            mats.push_back(scale > 0.0 ? scaledMatrix(c.cov,scale) : Mat{0,0,0,0,0,0});
        }
		SolverResult result; result.eigen.resize(cells.size()); result.converged.resize(cells.size(), 1); result.handleMs = handleMs;
		struct Work { size_t i; int p, q, k; };
		std::vector<Work> active; active.reserve(cells.size());
		std::vector<double> in, out; in.reserve(6 * cells.size()); out.reserve(cells.size());
		const auto begin = Clock::now(); const unsigned MAX = 24;
		for (unsigned it = 0; it < MAX; ++it) {
            const auto sweepStart = Clock::now();
            JacobiSweepStats sweep;
            sweep.sweep = it + 1;
            sweep.matrices = mats.size();
			const auto packingStart = Clock::now(); active.clear(); in.clear();
			for (size_t i = 0; i < mats.size(); ++i) {
				const Mat&m = mats[i];
				const double ab = std::abs(m.b), ac = std::abs(m.c), de = std::abs(m.e);
				int p = 0, q = 1, k = 2; double mx = ab;
				if (ac > mx) { p = 0; q = 2; k = 1; mx = ac; }if (de > mx) { p = 1; q = 2; k = 0; mx = de; }
                const double scale = matrixScale(m);
                if (scale == 0.0 || mx <= JACOBI_REL_TOL * scale) continue;
				double A[3][3] = { {m.a,m.b,m.c},{m.b,m.d,m.e},{m.c,m.e,m.f} };
				const double aa = A[p][p], dd = A[q][q], bb = A[p][q], uu = A[k][p], vv = A[k][q];
				const double tauValue = (dd - aa) / (2.0*bb);
				if (!std::isfinite(tauValue))throw std::runtime_error("Nonfinite Jacobi rotation parameter");
				const double sgn = (tauValue >= 0.0) ? 1.0 : -1.0;
				active.push_back({ i,p,q,k });
				in.push_back(aa); in.push_back(dd); in.push_back(bb);
                in.push_back(uu); in.push_back(vv); in.push_back(sgn);
			}
            sweep.packingMs = ms(packingStart, Clock::now());
            result.timing.packingMs += sweep.packingMs;
            sweep.active = active.size();
            if (active.empty()) {
                // The final sweep is a convergence check, not a paceval call.
                sweep.elapsedMs = ms(sweepStart, Clock::now());
                result.sweeps.push_back(sweep);
                result.iterations = it;
                break;
            }
			result.iterations = it + 1; const size_t N = active.size(); result.evaluations += N;
			// Batch size controls the independent per-matrix paceval work;
            // changing it does not alter the Jacobi pivot or update order.
			for (size_t offset = 0; offset < N;) {
				const size_t chunk = batchSize(N - offset);
				// The packed input is contiguous: pass an offset directly, without copying.
				auto apiStart = Clock::now();
				calc.batch(in.data() + 6 * offset, 6, chunk, out);
                const double callMs = ms(apiStart, Clock::now());
                result.timing.apiMs += callMs;
                ++result.timing.calls;
                sweep.apiMs += callMs;
                ++sweep.apiCalls;
                if (sweep.minChunk == 0 || chunk < sweep.minChunk) sweep.minChunk = chunk;
                if (chunk > sweep.maxChunk) sweep.maxChunk = chunk;
				const auto controlStart = Clock::now();
				for (size_t j = 0; j < chunk; ++j) {
					const Work&w = active[offset + j]; Mat&m = mats[w.i];
					double A[3][3] = { {m.a,m.b,m.c},{m.b,m.d,m.e},{m.c,m.e,m.f} };
					// MATHEMATICAL INVARIANT: a' + d' = a + d in exact arithmetic.
					// C++ obtains d' = (a+d)-a' instead of evaluating a fourth
					// paceval expression. Floating-point addition/subtraction can
					// round; analytic regressions, convergence and residual checks
					// monitor the resulting numerical accuracy.
					const double trace = A[w.p][w.p] + A[w.q][w.q];
                    // One paceval graph evaluates the Jacobi t parameter for all active matrices.
                    // The rotation and symmetric updates then use inexpensive scalar arithmetic.
                    const double tj = out[j];
                    const double cj = 1.0/std::sqrt(1.0+tj*tj);
                    const double sj = tj*cj;
                    const double newA = A[w.p][w.p] - tj*A[w.p][w.q];
                    const double newU = cj*A[w.k][w.p] - sj*A[w.k][w.q];
                    const double newV = sj*A[w.k][w.p] + cj*A[w.k][w.q];
                    A[w.p][w.p] = newA; A[w.q][w.q] = trace - newA;
                    A[w.k][w.p] = A[w.p][w.k] = newU;
                    A[w.k][w.q] = A[w.q][w.k] = newV;
					A[w.p][w.q] = A[w.q][w.p] = 0;
					m = { A[0][0],A[0][1],A[0][2],A[1][1],A[1][2],A[2][2] };
				}
                const double updateMs = ms(controlStart, Clock::now());
                result.timing.controlMs += updateMs;
                sweep.updatesMs += updateMs;
                offset += chunk;
            }
            sweep.elapsedMs = ms(sweepStart, Clock::now());
            result.sweeps.push_back(sweep);
        }
		const auto ctrl = Clock::now();
		for (size_t i = 0; i < mats.size(); ++i) {
			const Mat&m = mats[i];
            const double scale = matrixScale(m);
            if (scale > 0.0 && (std::max)({std::abs(m.b),std::abs(m.c),std::abs(m.e)}) > JACOBI_REL_TOL*scale) {
				++result.unconverged; result.converged[i] = 0;
			}
            // Covariance eigenvalues are nonnegative in exact arithmetic.
            // Clip only tiny negative roundoff; a material negative eigenvalue
            // is flagged as a solver-quality failure, not silently accepted.
            const double negativeTol = 1e-11;
            if (m.a < -negativeTol || m.d < -negativeTol || m.f < -negativeTol) {
                if (result.converged[i]) ++result.unconverged;
                result.converged[i] = 0;
            }
            Eig e = {{(std::max)(0.0,m.a)*scales[i],
                      (std::max)(0.0,m.d)*scales[i],
                      (std::max)(0.0,m.f)*scales[i]}};
			std::sort(e.begin(), e.end(), std::greater<double>()); result.eigen[i] = e;
		}
		result.timing.controlMs += ms(ctrl, Clock::now());
		result.milliseconds = ms(begin, Clock::now()); return result;
	}

    // paceval closed-form 3x3 symmetric eigenvalues with selective Jacobi fallback.
    // Host calculates bounded, scale-normalized invariants; paceval evaluates
    // the shared transcendental eigenspectrum expressions over independent cells.
    static SolverResult jacobiPaceval(const std::vector<Cell>&cells) {
        const auto handleStart=Clock::now();
        // acos(r) is defined for |r| <= 1; clamp host side due to roundoff.
        // Two output graphs: third eigenvalue is recovered from the trace.
        // This can lose relative accuracy for very small eigenvalues: those
        // cells are reprocessed by the original paceval Jacobi reference path.
        Handles& calc=*g_angleCalc;
        SolverResult result;
        result.handleMs=ms(handleStart,Clock::now());
        result.eigen.resize(cells.size());result.converged.assign(cells.size(),1);
        std::vector<double> in, out, scales;
        std::vector<size_t> indices;
        in.reserve(cells.size()*3); indices.reserve(cells.size());scales.resize(cells.size());
        const auto begin=Clock::now();
        for(size_t i=0;i<cells.size();++i){
            const double sc=matrixScale(cells[i].cov);scales[i]=sc;
            if(!std::isfinite(sc))throw std::runtime_error("Nonfinite matrix");
            if(sc==0){result.eigen[i]={{0,0,0}};continue;}
            const Mat m=scaledMatrix(cells[i].cov,sc);
            const double q=(m.a+m.d+m.f)/3.0;
            const double aa=m.a-q, dd=m.d-q, ff=m.f-q;
            const double p2=(aa*aa+dd*dd+ff*ff+2*(m.b*m.b+m.c*m.c+m.e*m.e))/6.0;
            if(p2 <= 1e-32){result.eigen[i]={{q*sc,q*sc,q*sc}};continue;}
            const double p=std::sqrt(p2);
            const double ia=aa/p,id=dd/p,iff=ff/p,ib=m.b/p,ic=m.c/p,ie=m.e/p;
            double r=(ia*id*iff+2*ib*ic*ie-ia*ie*ie-id*ic*ic-iff*ib*ib)/2.0;
            r=(std::max)(-1.0,(std::min)(1.0,r));
            indices.push_back(i);in.push_back(q);in.push_back(p);in.push_back(r);
        }
        result.evaluations=indices.size();
        const size_t N=indices.size();
        for(size_t offset=0;offset<N;){
            size_t chunk=batchSize(N-offset);
            const auto st=Clock::now();calc.batch(in.data()+3*offset,3,chunk,out);
            result.timing.apiMs+=ms(st,Clock::now());++result.timing.calls;
            for(size_t j=0;j<chunk;++j){
                const size_t k=indices[offset+j];
                const double tr=3.0*in[3*(offset+j)+0];
                const double q=in[3*(offset+j)],p=in[3*(offset+j)+1],theta=out[j]; const double l0=q+2*p*std::cos(theta); const double l2=q+2*p*std::cos(theta+2.0943951023931954923);const double l1=tr-l0-l2;
                Eig e = {{(std::max)(0.0,l0)*scales[k],(std::max)(0.0,l1)*scales[k],(std::max)(0.0,l2)*scales[k]}};
                std::sort(e.begin(),e.end(),std::greater<double>());
                result.eigen[k]=e;
            }
            offset+=chunk;
        }
        // Numerical fallback: analytic trigonometric roots lose relative accuracy
        // when the smallest root is tiny versus the dominant root.
        std::vector<Cell> fallback;std::vector<size_t> fallbackIndices;
        for(size_t i=0;i<cells.size();++i){
            const Eig& e=result.eigen[i];
            // A conservative 1e-5 condition threshold protects small roots.
            // It is a fallback trigger, not the application accuracy tolerance.
            if(scales[i]>0.0 && e[2] < 1e-5*(std::max)(e[0],1e-300)){
                fallback.push_back(cells[i]);fallbackIndices.push_back(i);
            }
        }
        result.fallbackMatrices=fallback.size();
        if(!fallback.empty()){
            auto corrected=jacobiReference(fallback);
            for(size_t i=0;i<fallback.size();++i){
                result.eigen[fallbackIndices[i]]=corrected.eigen[i];
                result.converged[fallbackIndices[i]]=corrected.converged[i];
            }
            result.unconverged+=corrected.unconverged;
            result.evaluations+=corrected.evaluations;
            result.timing.apiMs+=corrected.timing.apiMs;
            result.timing.calls+=corrected.timing.calls;
            result.sweeps=corrected.sweeps;
            if (!g_startupBenchmarkActive)
                std::cout << "[EIGENSPECTRUM] matrices="<<cells.size()<<" Jacobi_fallback="<<fallback.size()<<"\n";
        }
        result.milliseconds=ms(begin,Clock::now());
        return result;
    }
	static std::string basename(const std::string&s) { size_t p = s.find_last_of("\\/"); std::string t = s.substr(p == std::string::npos ? 0 : p + 1); size_t dot = t.find_last_of('.'); return dot == std::string::npos ? t : t.substr(0, dot); }
    // VALIDATION: dimensionless characteristic-polynomial residual computed
    // from a uniformly normalized copy of the ORIGINAL covariance matrix.
    // This is not another eigenvalue solver. Scaling eliminates x^3 overflows
    // for finite, extremely large or extremely small covariance matrices.
    static double polynomialResidual(const Mat& m, double eigenvalue) {
        const double magnitude = matrixScale(m);
        if (!(magnitude > 0.0)) return eigenvalue == 0.0 ? 0.0 : 1.0;
        const Mat a=scaledMatrix(m,magnitude);
        const double x=eigenvalue/magnitude;
        if (!std::isfinite(x)) return std::numeric_limits<double>::infinity();
        const double tr=a.a+a.d+a.f;
        const double s2=a.a*a.d+a.a*a.f+a.d*a.f-a.b*a.b-a.c*a.c-a.e*a.e;
        const double det=a.a*a.d*a.f+2.0*a.b*a.c*a.e-a.a*a.e*a.e-a.d*a.c*a.c-a.f*a.b*a.b;
        const double value=(((x-tr)*x+s2)*x-det);
        const double norm=(std::max)({std::abs(a.a)+std::abs(a.b)+std::abs(a.c),
            std::abs(a.b)+std::abs(a.d)+std::abs(a.e),
            std::abs(a.c)+std::abs(a.e)+std::abs(a.f)});
        return std::abs(value)/(norm*norm*norm);
    }
	// Known-spectrum validation for the paceval analytic/Jacobi hybrid eigensolver.
	// These are regression tests, not certified interval computations.
	static bool analyticRegression() {
		const Mat examples[] = { {4,0,0,2,0,1}, {2,1,0,2,0,0},
		                           {1,1,1,1,1,1}, {1,0,0,1,0,1} };
		const Eig expected[] = { {{4,2,1}}, {{3,1,0}}, {{3,0,0}}, {{1,1,1}} };
		const char* names[] = { "diagonal_distinct", "two_by_two_block_zero_root",
		                        "rank_one_repeated_zero", "identity_triple_root" };
        // Independent reference values are specified analytically; no native
        // numerical eigensolver is present in the production path or tests.
        std::vector<Cell> set;
        std::vector<Eig> references;
        std::vector<std::string> labels;
        const double factors[] = {1.0,1e-120,1e120};
        for (int i=0;i<4;++i) for (double factor : factors) {
            const Mat& a=examples[i];
            set.push_back({0,i,0,{a.a*factor,a.b*factor,a.c*factor,
                         a.d*factor,a.e*factor,a.f*factor},10});
            references.push_back({{expected[i][0]*factor,expected[i][1]*factor,expected[i][2]*factor}});
            labels.push_back(std::string(names[i])+" scale="+diagnosticScientific(factor));
        }
        // Nearly degenerate analytical cases: a tiny positive eigenvalue
        // must not be discarded as zero merely because the main root is 1.
        set.push_back({0,5,0,{1,0,0,1e-12,0,0},10});
        references.push_back({{1,1e-12,0}});
        labels.push_back("near_degenerate_diagonal scale="+diagnosticScientific(1.0));
        const double nearSmall=1e-12;
        const double nearDiag=0.5*(1.0+nearSmall);
        const double nearOff=0.5*(1.0-nearSmall);
        set.push_back({0,6,0,{nearDiag,nearOff,0,nearDiag,0,0},10});
        references.push_back({{1,nearSmall,0}});
        labels.push_back("near_degenerate_rotated scale="+diagnosticScientific(1.0));
        set.push_back({0,4,0,{0,0,0,0,0,0},10});
        references.push_back({{0,0,0}}); labels.push_back("zero_covariance scale="+diagnosticScientific(0.0));
        const SolverResult result=jacobiPaceval(set);
        bool passed=result.unconverged==0;
        size_t passingCases = 0;
        std::cout << "\n[VALIDATION] ==================================================\n"
                  << "[VALIDATION] ANALYTIC EIGENVALUE REGRESSIONS (15 cases)\n"
                  << "[VALIDATION] 4 known spectra x 3 scales + 2 near-degenerate + zero covariance\n"
                  << "[VALIDATION] Eigenvalue algorithm: paceval analytic with Jacobi fallback\n"
                  << "[VALIDATION] Error and residual units: dimensionless\n"
                  << "[VALIDATION] ==================================================\n";
        for (size_t i=0;i<set.size();++i) {
			bool casePassed = true;
			double maxError = 0.0, maxResidual = 0.0;
			for (int k = 0; k < 3; ++k) {
				const double eigen = result.eigen[i][k];
				const double expectedEigen=references[i][k];
                const double err=std::abs(eigen-expectedEigen);
                const double relativeErr=err/(std::max)(matrixScale(set[i].cov),std::numeric_limits<double>::min());
                maxError=(std::max)(maxError,relativeErr);
                maxResidual=(std::max)(maxResidual,polynomialResidual(set[i].cov,eigen));
                if (!std::isfinite(eigen) || relativeErr>1e-6) casePassed=false;
                // For near-degenerate cases also protect the small positive
                // eigenvalue; a global matrix-relative tolerance alone would
                // accept incorrectly rounding 1e-12 down to zero.
                if (labels[i].find("near_degenerate_") == 0 && expectedEigen > 0.0 &&
                    err > 0.01*expectedEigen + 1e-16*matrixScale(set[i].cov))
                    casePassed=false;
			}
			if (maxResidual > 1e-8) casePassed = false;
			passed = passed && casePassed;
            if (casePassed) ++passingCases;
            std::cout << "[REGRESSION] case=" << (i+1) << "/" << set.size()
                      << " name=" << labels[i]
                      << " relative_eigen_error=" << diagnosticScientific(maxError, 6)
                      << " normalized_poly_residual=" << diagnosticScientific(maxResidual, 6)
                      << " status=" << (casePassed ? "PASS" : "FAIL") << "\n";
		}
		std::cout << "[VALIDATION SUMMARY] passed=" << passingCases
                  << " total=" << set.size()
                  << " unconverged=" << result.unconverged
                  << " overall=" << (passed ? "PASS" : "FAIL") << "\n\n";
        std::cout << "[REGRESSION] Hybrid known-spectrum checks=" << (passed ? "PASS" : "FAIL") << "\n";
		return passed;
	}
	struct Features { double linearity=0, planarity=0, scattering=0, curvature=0; bool valid=false; };
	static Features features(const Eig& eigen, bool solverConverged) {
		Features f;
		if (!solverConverged || !std::isfinite(eigen[0]) || !std::isfinite(eigen[1]) || !std::isfinite(eigen[2])) return f;
		const double scale = eigen[0];
		const double total = eigen[0]+eigen[1]+eigen[2];
		// A near-degenerate covariance does not define reliable shape descriptors.
        if (!(scale > 0.0) || !(total > 0.0) || !std::isfinite(total)) return f;
        // No absolute world-unit threshold is used for low-variance cells.
		f.linearity = (std::max)(0.0, (eigen[0]-eigen[1])/scale);
		f.planarity = (std::max)(0.0, (eigen[1]-eigen[2])/scale);
		f.scattering = (std::max)(0.0, eigen[2]/scale);
		f.curvature = (std::max)(0.0, eigen[2]/total);
        f.valid = std::isfinite(f.linearity) && std::isfinite(f.planarity) &&
                  std::isfinite(f.scattering) && std::isfinite(f.curvature);
        return f;
	}
	struct BatchDiagnostics { std::vector<Features> feature; std::vector<std::array<double,3>> residual; };
	// Seven functions, one multi-computation call per chunk:
	// four eigenvalue shape descriptors and three matrix-scaled polynomial residuals.
	// The characteristic polynomial coefficients are constructed from the original
	// symmetric matrix in C++; only their numerical evaluation is sent to paceval.
	// Pre-validation excludes degenerate inputs and prevents division by zero.
	static BatchDiagnostics featureResidualBatch(const std::vector<Cell>& cells,
		const SolverResult& eigen, MathBatchTiming& timing) {
		BatchDiagnostics result;
		result.feature.resize(cells.size()); result.residual.resize(cells.size());
		if (!g_pacevalFeatures) {
			for (size_t i=0;i<cells.size();++i) {
				for (int k=0;k<3;++k) result.residual[i][k]=polynomialResidual(cells[i].cov,eigen.eigen[i][k]);
				bool good=eigen.converged[i]!=0;
				for (int k=0;k<3;++k) if (!std::isfinite(result.residual[i][k]) || result.residual[i][k]>1e-8)good=false;
				result.feature[i]=features(eigen.eigen[i],good);
			}
			return result;
		}
		const std::string polynomial = "((((x-tr)*x+s2)*x-det))";
		// The polynomial inputs have already been normalized to a unit-scale
        // matrix, so squared polynomial terms remain in a bounded range.
        const std::string residual = "(sqrt(("+polynomial+")*("+polynomial+"))/(scale*scale*scale))";
		auto replaceX=[](std::string str,const std::string& x)->std::string {
			std::string::size_type at=0;
			while ((at=str.find("x",at))!=std::string::npos) {str.replace(at,1,x);at+=x.size();}
			return str;
		};
		Handles& calc=*g_featureCalc;
		struct Index {size_t value;};
		std::vector<size_t> work; work.reserve(cells.size());
		std::vector<double> input,output;
		const size_t cap=g_batchLimit?(std::min)(g_batchLimit,cells.size()):cells.size();
		input.reserve(7*cap);output.reserve(7*cap);
		// Degenerate matrices still receive host-computed residuals, but invalid
		// feature expressions are not sent to paceval.
		for (size_t i=0;i<cells.size();++i) {
			const Eig& e=eigen.eigen[i];
			if (!eigen.converged[i] || !(e[0]>0.0) || !(e[0]+e[1]+e[2]>0.0) ||
				!std::isfinite(e[0]) || !std::isfinite(e[1]) || !std::isfinite(e[2])) {
				for (int k=0;k<3;++k) result.residual[i][k]=polynomialResidual(cells[i].cov,e[k]);
			} else work.push_back(i);
		}
		for (size_t offset=0;offset<work.size();) {
			const size_t chunk=batchSize(work.size()-offset); input.clear();
			for (size_t j=0;j<chunk;++j) {
				const size_t i=work[offset+j];const Mat& m=cells[i].cov;const Eig& e=eigen.eigen[i];
                const double magnitude=matrixScale(m);
                const Mat a=scaledMatrix(m,magnitude);
                const double tr=a.a+a.d+a.f;
                const double s2=a.a*a.d+a.a*a.f+a.d*a.f-a.b*a.b-a.c*a.c-a.e*a.e;
                const double det=a.a*a.d*a.f+2*a.b*a.c*a.e-a.a*a.e*a.e-a.d*a.c*a.c-a.f*a.b*a.b;
                const double norm=(std::max)({std::abs(a.a)+std::abs(a.b)+std::abs(a.c),
                    std::abs(a.b)+std::abs(a.d)+std::abs(a.e),std::abs(a.c)+std::abs(a.e)+std::abs(a.f)});
                input.insert(input.end(),{e[0]/magnitude,e[1]/magnitude,e[2]/magnitude,tr,s2,det,norm});
			}
			const auto start=Clock::now();calc.batch(input.data(),7,chunk,output);
			timing.featureMs+=ms(start,Clock::now());++timing.featureCalls;
			for (size_t j=0;j<chunk;++j) {
				const size_t i=work[offset+j];
				for (int k=0;k<3;++k)result.residual[i][k]=output[(4+k)*chunk+j];
				bool good=true;for (int k=0;k<3;++k)if (result.residual[i][k]>1e-8)good=false;
				if (good) {
					Features f;f.linearity=output[j];f.planarity=output[chunk+j];
					f.scattering=output[2*chunk+j];f.curvature=output[3*chunk+j];
	                f.valid=std::isfinite(f.linearity)&&std::isfinite(f.planarity)&&
                        std::isfinite(f.scattering)&&std::isfinite(f.curvature);
                result.feature[i]=f;
				}
			}
			offset+=chunk;
		}
		return result;
	}

    // -------------------------------------------------------------------------
    // OPTIONAL TINC DIAGNOSTICS (post-processing, not part of Jacobi convergence)
    // -------------------------------------------------------------------------
    // The optional legacy TINC diagnostic checks three mathematically equivalent
    // Jacobi output expressions, NOT the production single-graph implementation.
    // Production evaluates only t in paceval; all updates are computed in C++.
    // TINC validation of the complete solver is NOT provided.
    // Inputs are original covariances normalized by their maximum element.
    // Host pivot selection, trace update, and iterations are NOT interval-
    // propagated: passing results certify neither final eigenvalues nor a
    // complete, interval-bounded eigenvalue decomposition.
    // TINC errors are recorded per sample; they never silently become PASS.
    struct TincCandidate {
        size_t index = 0;
        double severity = 0.0;
        double relativeMin = 0.0;
        double relativeGap = 0.0;
        bool qualityIssue = false;
    };
    static void validateTincSelected(const std::vector<Cell>& cells,
        const SolverResult& j, const BatchDiagnostics& diagnostics) {
        if (!g_validateTinc) return;
        const auto begin = Clock::now();
        std::cout << "[TINC] === OPTIONAL POST-PROCESSING FORMULA VALIDATION ===\n"
                  << "[TINC] Production Jacobi and startup batch tuning used TINC=OFF.\n"
                  << "[TINC] Interval results apply to three isolated Jacobi rotation expressions,"
                     " NOT to the complete eigensolver.\n"
                  << "[TINC] Selection: near-zero eigenvalue, repeated/close eigenvalues,"
                     " high residual or nonconvergence.\n"
                  << "[TINC] Units: covariance and eigenvalues are matrix-normalized;"
                     " interval widths are dimensionless.\n";
        std::vector<TincCandidate> candidates;
        candidates.reserve(cells.size());
        for (size_t i=0; i<cells.size(); ++i) {
            const Eig& e=j.eigen[i];
            const double norm=(std::max)({std::abs(e[0]),std::abs(e[1]),std::abs(e[2])});
            double relativeMin=0.0, relativeGap=0.0;
            if (norm>0.0 && std::isfinite(norm)) {
                relativeMin=std::abs(e[2]/norm);
                relativeGap=(std::min)(std::abs((e[0]-e[1])/norm),
                                       std::abs((e[1]-e[2])/norm));
            }
            const double residual=(std::max)({diagnostics.residual[i][0],
                diagnostics.residual[i][1],diagnostics.residual[i][2]});
            const bool issue=j.converged[i]==0 || !diagnostics.feature[i].valid ||
                !std::isfinite(residual) || residual>1e-8;
            const double critical=(std::min)(relativeMin,relativeGap);
            // Larger scores are more relevant; deterministic index tie-break.
            const double severity=issue?1e10:(critical<=g_tincDegenerateLimit ?
                1e5/(1.0+critical/g_tincDegenerateLimit):1.0/(1.0+critical));
            candidates.push_back({i,severity,relativeMin,relativeGap,issue});
        }
        std::sort(candidates.begin(),candidates.end(),[](const TincCandidate& a,const TincCandidate& b) {
            if (a.severity!=b.severity) return a.severity>b.severity;
            return a.index<b.index;
        });
        const size_t samples=(std::min)(static_cast<size_t>(g_tincSamples),candidates.size());
        std::cout << "[TINC] selected=" << samples << " eligible=" << cells.size()
                  << " width_warning_threshold=" << diagnosticScientific(g_tincWidthLimit)
                  << " close_eigen_threshold=" << diagnosticScientific(g_tincDegenerateLimit) << "\n";
        if (samples==0) return;
        const std::string tau="((d-a)/(2*b))";
        const std::string t="(sgn/((sgn*"+tau+")+sqrt(1+("+tau+")*("+tau+"))))";
        const std::string co="(1/sqrt(1+("+t+")*("+t+")))";
        const std::string si="(("+t+")*("+co+"))";
        // Legacy equivalent output expressions; NOT the production single t graph.
        const std::array<std::string,3> expressions={{
            "(a-("+t+")*b)",
            "(("+co+")*u-("+si+")*v)",
            "(("+si+")*u+("+co+")*v)"}};
        const char* names[3]={"diagonal_p","offdiagonal_kp","offdiagonal_kq"};
        std::array<PACEVAL_HANDLE,3> handles={{nullptr,nullptr,nullptr}};
        size_t passed=0,warnings=0,failed=0,skipped=0;
        try {
            for (size_t k=0;k<3;++k) {
                handles[k]=paceval_CreateComputation(expressions[k].c_str(),6,"a d b u v sgn",true,nullptr);
                if (!handles[k] || paceval_GetIsError(handles[k]))
                    throw std::runtime_error("TINC handle creation failed: "+std::string(names[k]));
            }
            for (size_t n=0;n<samples;++n) {
                const TincCandidate& c=candidates[n];
                const Cell& cell=cells[c.index];
                const double magnitude=matrixScale(cell.cov);
                const Mat m=(magnitude>0.0) ? scaledMatrix(cell.cov,magnitude) : Mat{0,0,0,0,0,0};
                const double ab=std::abs(m.b),ac=std::abs(m.c),de=std::abs(m.e);
                int p=0,q=1,k=2;double mx=ab;
                if (ac>mx){p=0;q=2;k=1;mx=ac;}
                if (de>mx){p=1;q=2;k=0;mx=de;}
                std::cout << "[TINC] sample=" << (n+1) << "/" << samples
                    << " frame=" << cell.frame << " az=" << cell.az << " el=" << cell.el
                    << " points=" << cell.count
                    << " lambda_min_relative=" << diagnosticScientific(c.relativeMin,6)
                    << " eigen_gap_relative=" << diagnosticScientific(c.relativeGap,6)
                    << " quality_issue=" << (c.qualityIssue?"yes":"no") << "\n";
                // A diagonal matrix has no valid Jacobi pivot: this is a
                // mathematically expected skip, not an interval failure.
                if (!(mx>JACOBI_REL_TOL*matrixScale(m))) {
                    ++skipped;
                    std::cout << "[TINC] sample=" << n+1
                              << " status=SKIP reason=no_active_Jacobi_pivot\n";
                    continue;
                }
                double A[3][3]={{m.a,m.b,m.c},{m.b,m.d,m.e},{m.c,m.e,m.f}};
                const double aa=A[p][p],dd=A[q][q],bb=A[p][q],uu=A[k][p],vv=A[k][q];
                const double tauValue=(dd-aa)/(2.0*bb);
                if (!std::isfinite(tauValue)) {
                    ++failed;
                    std::cout << "[TINC] sample=" << n+1 << " status=ERROR reason=nonfinite_tau\n";
                    continue;
                }
                double args[6]={aa,dd,bb,uu,vv,tauValue>=0.0?1.0:-1.0};
                double values[3]={},lo[3]={},hi[3]={};int errors[3]={};
                const bool apiError=paceval_dGetMultipleComputationsResultsExt(
                    handles.data(),3,args,1,values,lo,hi,errors);
                bool bad=apiError, wide=false;
                for (size_t z=0;z<3;++z) {
                    const bool finite=std::isfinite(values[z])&&std::isfinite(lo[z])&&std::isfinite(hi[z]);
                    const bool valid=errors[z]==0&&finite&&lo[z]<=hi[z]&&
                        values[z]>=lo[z]&&values[z]<=hi[z];
                    const double width=(valid?(hi[z]-lo[z]):std::numeric_limits<double>::quiet_NaN());
                    const double relativeWidth=width/((std::max)(1.0,std::abs(values[z])));
                    if (!valid || !std::isfinite(relativeWidth)) bad=true;
                    if (valid && relativeWidth>g_tincWidthLimit)wide=true;
                    std::cout << "[TINC]   expr=" << names[z]
                        << " result=" << diagnosticScientific(values[z],12)
                        << " lower=" << diagnosticScientific(lo[z],12)
                        << " upper=" << diagnosticScientific(hi[z],12)
                        << " rel_width=" << diagnosticScientific(relativeWidth,6)
                        << " api_error=" << errors[z]
                        << " status=" << (!valid?"INVALID":relativeWidth>g_tincWidthLimit?"WIDE":"OK") << "\n";
                }
                if (bad){++failed;std::cout<<"[TINC] sample="<<n+1<<" status=ERROR\n";}
                else if(wide){++warnings;std::cout<<"[TINC] sample="<<n+1<<" status=WARN\n";}
                else{++passed;std::cout<<"[TINC] sample="<<n+1<<" status=PASS\n";}
            }
        } catch(const std::exception& e) {
            ++failed;
            std::cout << "[TINC] ERROR " << e.what() << "\n";
        }
        for (auto h:handles) if (h) paceval_DeleteComputation(h);
        std::cout << "[TINC SUMMARY] checked=" << (passed+warnings+failed)
                  << " passed=" << passed << " wide=" << warnings
                  << " errors=" << failed << " skipped=" << skipped
                  << " elapsed_ms=" << ms(begin,Clock::now())
                  << " status=" << (failed ? "CHECK":warnings ? "WARN":"PASS") << "\n";
        std::cout << "[TINC] Interpretation: interval bounds cover the three isolated"
                  << " paceval formulas only. The trace-derived diagonal, C++ updates,"
                  << " pivot decisions and eigenvalues are not interval-certified.\n";
    }


    // -----------------------------------------------------------------------
    // STARTUP PHASE AUTOTUNER
    // Four measured choices, all with paceval analytical eigenvalue execution:
    //   E     : Eigenvalues in paceval; covariance and features in C++.
    //   EC    : Eigenvalues and covariance normalization in paceval.
    //   EF    : Eigenvalues and geometry/quality features in paceval.
    //   ECF   : All three stages in paceval.
    // The same input moments and math handles are reused for each candidate.
    // Handle creation, warmup, and configuration selection are excluded
    // from operational frame time. Startup samples include data packing.
    // Numerical comparison precedes any configuration acceptance. The selected
    // configuration is fixed until the next explicit startup calibration.
    struct PhaseChoice { const char* name; bool covariancePaceval; bool featuresPaceval; };
    struct PhaseBenchmarkResult { double medianMs=0; bool valid=false; };
    static bool benchmarkClose(double x,double y,double relativeTolerance=1e-10) {
        if (!std::isfinite(x)||!std::isfinite(y)) return false;
        return std::abs(x-y)<=relativeTolerance*(std::max)(1.0,(std::max)(std::abs(x),std::abs(y)));
    }
    static double medianElapsed(std::vector<double> times){
        std::sort(times.begin(),times.end());
        const size_t m=times.size()/2;
        return (times.size()%2)?times[m]:0.5*(times[m-1]+times[m]);
    }
    static void benchmarkAndSelectPhases(const std::string& path) {
        const unsigned repeats=readEnvUnsigned("PACEVAL_LIDAR_PHASE_TUNE_REPEATS",5,3,15);
        const auto loaded=readCsv(path);
        size_t points=0,inField=0,validPoints=0,occupied=0;
        const auto moments=collectCells(loaded,points,inField,validPoints,occupied);
        if (moments.empty())throw std::runtime_error("No covariance cells for startup autotuning");
        // Reference is computed before timing with C++ covariance/features and
        // the same paceval eigenvalue solver; this tests phase equivalence,
        // not independence of the eigensolver.
        g_pacevalCovariance=false;g_pacevalFeatures=false;
        MathBatchTiming referenceTiming;
        const auto referenceCells=normalizeCovariance(moments,referenceTiming);
        const auto referenceEigen=jacobiPaceval(referenceCells);
        const auto referenceFeatures=featureResidualBatch(referenceCells,referenceEigen,referenceTiming);
        const PhaseChoice candidates[]={
            {"evaluateEigenvaluesPaceval",false,false},
            {"evaluateEigenvaluesAndCovariancePaceval",true,false},
            {"evaluateEigenvaluesAndFeaturesPaceval",false,true},
            {"evaluateAllMathPhasesPaceval",true,true}
        };
        struct BenchmarkLogScope {
            BenchmarkLogScope() { g_startupBenchmarkActive=true; }
            ~BenchmarkLogScope() { g_startupBenchmarkActive=false; }
        } benchmarkLogScope;
        PhaseBenchmarkResult results[4];
        std::cout<<"[PHASE AUTOTUNE] start; points="<<points
            <<" matrices="<<moments.size()<<" repeats="<<repeats
            <<"; paceval handles persistent; CSV I/O excluded\n";
        // Interleave candidates (rather than running one candidate's samples
        // consecutively) to reduce CPU-frequency and scheduler-order bias.
        std::vector<double> durations[4];
        bool valid[4]={true,true,true,true};
        for(unsigned pass=0;pass<repeats+1;++pass) {
            for(unsigned step=0;step<4;++step) {
                const unsigned index=(step+pass)%4;
                const PhaseChoice& choice=candidates[index];
                g_pacevalCovariance=choice.covariancePaceval;
                g_pacevalFeatures=choice.featuresPaceval;
                MathBatchTiming timings;
                const auto start=Clock::now();
                const auto cells=normalizeCovariance(moments,timings);
                const auto eigen=jacobiPaceval(cells);
                const auto diagnostics=featureResidualBatch(cells,eigen,timings);
                const double duration=ms(start,Clock::now());
                // All numeric comparisons are outside the measured interval.
                bool ok=cells.size()==referenceCells.size() &&
                    eigen.eigen.size()==referenceEigen.eigen.size() &&
                    diagnostics.feature.size()==referenceFeatures.feature.size();
                if(ok) for(size_t j=0;j<cells.size();++j){
                    const Mat& a=cells[j].cov;const Mat& b=referenceCells[j].cov;
                    const double aa[]={a.a,a.b,a.c,a.d,a.e,a.f};
                    const double bb[]={b.a,b.b,b.c,b.d,b.e,b.f};
                    for(int k=0;k<6;++k)if(!benchmarkClose(aa[k],bb[k]))ok=false;
                    for(int k=0;k<3;++k){
                        if(!benchmarkClose(eigen.eigen[j][k],referenceEigen.eigen[j][k]))ok=false;
                        if(!benchmarkClose(diagnostics.residual[j][k],referenceFeatures.residual[j][k],1e-7))ok=false;
                    }
                    const Features& f=diagnostics.feature[j];const Features& r=referenceFeatures.feature[j];
                    if(f.valid!=r.valid || eigen.converged[j]!=referenceEigen.converged[j])ok=false;
                    if(f.valid && (!benchmarkClose(f.linearity,r.linearity) ||
                        !benchmarkClose(f.planarity,r.planarity) ||
                        !benchmarkClose(f.scattering,r.scattering) ||
                        !benchmarkClose(f.curvature,r.curvature)))ok=false;
                }
                valid[index]=valid[index]&&ok;
                if(pass>0)durations[index].push_back(duration);
                if(!ok)std::cout<<"[PHASE AUTOTUNE] REJECT "<<choice.name
                    <<" due to numerical mismatch\n";
            }
        }
        size_t best=0;
        double bestMs=std::numeric_limits<double>::infinity();
        for(size_t i=0;i<4;++i){
            results[i].medianMs=medianElapsed(durations[i]);
            results[i].valid=valid[i];
            std::cout<<"[PHASE AUTOTUNE] "<<candidates[i].name
                <<" median_ms="<<results[i].medianMs
                <<" status="<<(valid[i]?"PASS":"REJECT")<<"\n";
            if(valid[i] && results[i].medianMs<bestMs){bestMs=results[i].medianMs;best=i;}
        }
        if(!std::isfinite(bestMs))throw std::runtime_error("No numerically valid math phase candidate");
        g_pacevalCovariance=candidates[best].covariancePaceval;
        g_pacevalFeatures=candidates[best].featuresPaceval;
        std::cout<<"[PHASE AUTOTUNE] SELECTED="<<candidates[best].name
            <<" median_ms="<<bestMs
            <<" covariance="<<(g_pacevalCovariance?"paceval":"C++")
            <<" features="<<(g_pacevalFeatures?"paceval":"C++")
            <<"; eigenvalues=paceval\n";
    }

    // One record per processed input file. These figures are measured wall-clock
    // stage durations, not CPU utilization, deterministic deadlines, or sensor latency.
    struct FrameReport {
        std::string source;
        size_t frames=0, points=0, cells=0, badCells=0, invalidFeatures=0;
        size_t fallbackCount=0;
        double binningMs=0, covarianceMs=0, eigenMs=0;
        double featuresMs=0, computeMs=0;
        bool covariancePaceval=false, featuresPaceval=false;
    };
    static std::vector<FrameReport> g_frameReports;

    // Final operator-facing report. Run after all input files and repeat passes.
    // Startup calibration, one-time handle creation, and optional TINC diagnostics
    // are intentionally not included in the per-frame compute-only figures.
    static void printEngineeringSummary() {
        if (g_frameReports.empty()) return;
        FrameReport total;
        bool allGood=true;
        std::cout << "\n==============================================================\n"
                  << " LiDAR GEOMETRY PROCESSING - EXECUTION SUMMARY\n"
                  << "==============================================================\n"
                  << "Pipeline: map Cartesian LiDAR points into azimuth/\n"
                  << "elevation cells; accumulate centered moments (Welford); form\n"
                  << "symmetric 3x3 covariance matrices; compute eigenvalues using\n"
                  << "persistent paceval analytical expressions with selective paceval\n"
                  << "Jacobi fallback; calculate geometry descriptors and verify\n"
                  << "numerical residuals for each processed point cloud.\n"
                  << "Execution policy: covariance=" << (g_pacevalCovariance ? "paceval" : "C++")
                  << ", eigenvalues=paceval, descriptors=" << (g_pacevalFeatures ? "paceval" : "C++") << "\n"
                  << "Timing scope: recurring in-memory processing only.\n";
        for (const FrameReport& r : g_frameReports) {
            total.frames += r.frames; total.points += r.points; total.cells += r.cells;
            total.badCells += r.badCells; total.invalidFeatures += r.invalidFeatures;
            total.fallbackCount += r.fallbackCount;
            total.binningMs += r.binningMs;
            total.covarianceMs += r.covarianceMs; total.eigenMs += r.eigenMs;
            total.featuresMs += r.featuresMs; total.computeMs += r.computeMs;
            if (r.badCells || r.invalidFeatures) allGood=false;
        }
        const double n=static_cast<double>(g_frameReports.size());
        std::cout << "\nProcessing passes=" << g_frameReports.size()
                  << ", sensor frames in processed files=" << total.frames
                  << ", input points=" << total.points
                  << ", evaluated cells=" << total.cells << "\n"
                  << "\nMeasured recurring processing stage           Mean/pass (ms)\n"
                  << "--------------------------------------------------------------\n";
        auto printRow=[&](const char* name,double duration) {
            std::cout << std::left << std::setw(42) << name << std::right
                      << std::setw(15) << std::fixed << std::setprecision(3) << (duration/n) << "\n";
        };
        printRow("Angular binning and Welford moments",total.binningMs);
        printRow("Covariance normalization",total.covarianceMs);
        printRow("paceval eigenspectrum incl. fallback",total.eigenMs);
        printRow("Geometry descriptors and residual checks",total.featuresMs);
        std::cout << "--------------------------------------------------------------\n";
        printRow("RECURRING FRAME PROCESSING",total.computeMs);
        std::cout << "\nQuality: " << (allGood?"PASS":"CHECK")
                  << "; bad-quality cells=" << total.badCells
                  << "; invalid feature cells=" << total.invalidFeatures
                  << "; Jacobi fallback matrices=" << total.fallbackCount << "\n"
                  << "Mean recurring time is per processed INPUT PASS, not necessarily\n"
                  << "per physical LiDAR frame when a CSV contains multiple frames.\n"
                  << "10 Hz (100 ms) / 20 Hz (50 ms) are reference frame budgets,\n"
                  << "not verified real-time deadlines. CSV I/O, startup initialization,\n"
                  << "autotuning, optional TINC diagnostics, sensor transfer and\n"
                  << "downstream perception are excluded from these measurements.\n"
                  << "This software is an offline mathematical demonstrator; it is\n"
                  << "not an automotive safety-certified perception component.\n"
                  << "==============================================================\n";
    }

	// EXECUTION CONTRACT: one file is processed to completion before the next.
	// Timing excludes startup tuning and optional post-processing TINC checks;
	// exported CSV retains per-cell quality indicators. A PASS status covers
	// tested numerical criteria, not sensor detection performance or safety.
	// Batch size is optional; both timing totals and phase breakdown are reported.
	static void process(const std::string& path) {
		const auto loadStart = Clock::now();
		const auto frames = readCsv(path);
		(void)loadStart; // Input is excluded from recurring-frame timing.
		size_t points = 0, inField = 0, validPoints = 0, occupied = 0;
		const auto prepStart = Clock::now();
		const auto moments = collectCells(frames, points, inField, validPoints, occupied);
		const double binningMs = ms(prepStart, Clock::now());
		MathBatchTiming mathTiming;
		const auto covarianceStart=Clock::now();
		const auto cells=normalizeCovariance(moments,mathTiming);
		const double covarianceMs=ms(covarianceStart,Clock::now());
		if (cells.empty()) throw std::runtime_error("No angular cells with enough points: " + path);
		std::cout << "\n=====================================================\n"
		          << "PACEVAL AUTOMOTIVE LiDAR: HYBRID EIGENSPECTRUM CORE\n"
		          << "=====================================================\n"
		          << "Input: " << path << "; frames=" << frames.size() << "; points=" << points << "\n"
		          << "Grid=" << g_config.azBins << "x" << g_config.elBins
		          << " elevation=[" << g_config.minElevation << "," << g_config.maxElevation << "] rad"
		          << " minPoints=" << g_config.minPointsPerCell << "\n"
		          << "Points in elevation FOV=" << inField << " occupied bins=" << occupied
		          << " eligible covariance cells=" << cells.size() << " points in eligible cells=" << validPoints << "\n"
		          << "Online centered moments: Welford; covariance normalization: " << (g_pacevalCovariance ? "paceval batch" : "C++") << ".\n"
		          << "Shape features + polynomial residuals: " << (g_pacevalFeatures ? "paceval batch" : "C++") << ".\n"
		          << "Solver: paceval analytic with paceval Jacobi fallback; production TINC disabled. Optional post-validation: "
                  << (g_validateTinc ? "ON" : "OFF") << ".\n" << std::flush;
		const SolverResult j = jacobiPaceval(cells);
		const auto featuresStart = Clock::now();
		const BatchDiagnostics diagnostics=featureResidualBatch(cells,j,mathTiming);
		const auto& feat=diagnostics.feature;
		const auto& residuals=diagnostics.residual;
		double maxResidual=0.0;size_t badResidual=0,badQuality=0,invalidFeatures=0;
		for (size_t i=0;i<cells.size();++i) {
			bool good=j.converged[i]!=0;
			for (int k=0;k<3;++k) {
				const double r=residuals[i][k];
				if (!std::isfinite(r) || r>1e-8) {good=false;++badResidual;}
				if (std::isfinite(r))maxResidual=(std::max)(maxResidual,r);
			}
			if (!feat[i].valid)++invalidFeatures;
			if (!good)++badQuality;
		}
		const double featuresMs = ms(featuresStart, Clock::now());
		const auto writeStart = Clock::now();
		ensureOutputDirectory();
		const std::string filename = "output/" + basename(path) + "_jacobi_features.csv";
		std::ofstream out(filename); if (!out) throw std::runtime_error("Cannot write " + filename);
		out << "frame,azimuth_bin,elevation_bin,points,lambda1,lambda2,lambda3,linearity,planarity,scattering,curvature,"
		       "jacobi_converged,features_valid,scaled_residual_l1,scaled_residual_l2,scaled_residual_l3\n";
		for (size_t i = 0; i < cells.size(); ++i) {
			const Cell& c = cells[i]; const Eig& e = j.eigen[i]; const Features& f = feat[i];
			const auto& r = residuals[i];
			out << std::setprecision(17) << c.frame << ',' << c.az << ',' << c.el << ',' << c.count
			    << ',' << e[0] << ',' << e[1] << ',' << e[2];
			if (f.valid) out << ',' << f.linearity << ',' << f.planarity << ',' << f.scattering << ',' << f.curvature;
			else out << ",,,,"; // Empty feature fields: do not present invalid results as zeros.
			out << ',' << static_cast<unsigned>(j.converged[i]) << ',' << (f.valid ? 1 : 0)
			    << ',' << r[0] << ',' << r[1] << ',' << r[2] << '\n';
		}
		out.flush(); if (!out) throw std::runtime_error("CSV write failed: " + filename);
		out.close();
		(void)writeStart; // Output is excluded from recurring-frame timing.
		
        // Recurring in-memory frame latency excludes CSV file I/O and logging. It includes
        // in-memory binning/Welford, covariance normalization, paceval Jacobi,
        // descriptor/residual evaluation, and required numerical checks.
        // It is NOT a measured real-time deadline or a streaming sensor pipeline.
        const double computeOnlyMs = binningMs + covarianceMs + j.milliseconds + featuresMs;
        const double mathOnlyMs = covarianceMs + j.milliseconds + featuresMs;
        std::cout << std::fixed << std::setprecision(3)
                  << "[FRAME LATENCY] frames=" << frames.size()
                  << " points=" << points
                  << " eligible_cells=" << cells.size()
                  << " compute_only_ms=" << computeOnlyMs
                  << " math_only_ms=" << mathOnlyMs
                  << " budget_10hz_ms=100 budget_20hz_ms=50"
                  << " status=" << ((j.unconverged==0 && badResidual==0 && invalidFeatures==0 && badQuality==0) ? "PASS" : "CHECK") << "\n";
        // Detailed per-sweep diagnostics run AFTER the measured computation.
        // Emitting log lines inside the solver would perturb wall-clock timing.
        std::cout << "[JACOBI PROFILE] --- PER-SWEEP PACEVAL WORKLOAD ---\n";
        size_t sumActive = 0, sumCalls = 0;
        double sumApiMs = 0.0, sumPackingMs = 0.0, sumUpdatesMs = 0.0;
        for (const JacobiSweepStats& sw : j.sweeps) {
            sumActive += sw.active;
            sumCalls += sw.apiCalls;
            sumApiMs += sw.apiMs;
            sumPackingMs += sw.packingMs;
            sumUpdatesMs += sw.updatesMs;
            const double activePercent = sw.matrices ? 100.0 * double(sw.active) / double(sw.matrices) : 0.0;
            const double throughput = sw.apiMs > 0.0 ? 1000.0 * double(sw.active) / sw.apiMs : 0.0;
            const size_t configuredLimit = g_batchLimit ? g_batchLimit : sw.active;
            const double fillPercent = (sw.apiCalls && configuredLimit)
                ? 100.0 * double(sw.active) / (double(sw.apiCalls) * double(configuredLimit)) : 0.0;
            std::cout << std::fixed << std::setprecision(3)
                << "[JACOBI PROFILE] sweep=" << sw.sweep
                << " matrices=" << sw.matrices << " active=" << sw.active
                << " active_pct=" << activePercent
                << " rotations=" << sw.active
                << " api_calls=" << sw.apiCalls
                << " chunk_min=" << sw.minChunk << " chunk_max=" << sw.maxChunk
                << " nominal_batch_fill_pct=" << fillPercent
                << " packing_ms=" << sw.packingMs
                << " paceval_api_ms=" << sw.apiMs
                << " cpp_update_ms=" << sw.updatesMs
                << " sweep_total_ms=" << sw.elapsedMs
                << " rotations_per_api_s=" << throughput
                << (sw.active ? " status=ACTIVE" : " status=CONVERGED") << "\n";
        }
        std::cout << std::fixed << std::setprecision(3)
            << "[JACOBI PROFILE SUMMARY] sweeps=" << j.sweeps.size()
            << " rotations=" << sumActive
            << " api_calls=" << sumCalls
            << " packing_ms=" << sumPackingMs
            << " paceval_api_ms=" << sumApiMs
            << " cpp_update_ms=" << sumUpdatesMs
            << " rotations_per_api_s=" << (sumApiMs > 0.0 ? 1000.0 * double(sumActive) / sumApiMs : 0.0)
            << " production_batch_limit=" << g_batchLimit << "\n";
        std::cout << std::fixed << std::setprecision(3)
                  << "[TIMING] --- RECURRING FRAME PROCESSING (milliseconds) ---\n"
		          << "[TIMING] Binning + Welford centered moments ms=" << binningMs << "\n"
		          << "[TIMING] Covariance normalization total ms=" << covarianceMs
		          << " paceval_API_ms=" << mathTiming.covarianceMs << " API_calls=" << mathTiming.covarianceCalls << "\n"
		          << "[TIMING] --- PACEVAL JACOBI SOLVER (milliseconds) ---\n"
		          << "[TIMING] Hybrid eigenspectrum calculation ms=" << j.milliseconds << "\n"
		          << "[TIMING]   API ms=" << j.timing.apiMs << " packing ms=" << j.timing.packingMs
		          << " C++ updates ms=" << j.timing.controlMs << " calls=" << j.timing.calls << "\n"
		          << "[TIMING] --- RECURRING FEATURES AND QUALITY CHECKS (milliseconds) ---\n"
                  << "[TIMING] Features + residual validation ms=" << featuresMs
                  << " paceval_API_ms=" << mathTiming.featureMs << " API_calls=" << mathTiming.featureCalls << "\n"
                  << "[TIMING] RECURRING FRAME ms=" << computeOnlyMs << " points/s="
                  << (computeOnlyMs > 0.0 ? 1000.0 * points / computeOnlyMs : 0.0)
                  << " covariance cells/s=" << (computeOnlyMs > 0.0 ? 1000.0 * cells.size() / computeOnlyMs : 0.0) << "\n"
                  << "[BATCH] selected limit=" << g_batchLimit
		          << "; source=" << (g_batchWasCalibrated ? "startup calibration" : "manual/default") << "; SDK controls core/thread use.\n"
		          << "[RESULT] passes=" << j.iterations << " rotations=" << j.evaluations
		          << " unconverged=" << j.unconverged << " residual failures=" << badResidual
		          << " invalid features=" << invalidFeatures << " bad-quality cells=" << badQuality << "\n"
		          << "[QUALITY] " << ((j.unconverged==0 && badResidual==0 && invalidFeatures==0 && badQuality==0) ? "PASS" : "CHECK")
                  << " (zero unconverged/failed cells required for PASS)"
                  << " max_normalized_residual=" << diagnosticScientific(maxResidual, 6) << "\n"
                  << "[RESULT] " << filename << "\n"
		          << "[SCOPE] File-based numerical demonstrator, not realtime or automotive-certified.\n";
        // Capture processing durations before optional post-processing diagnostics.
        FrameReport report;
        report.source=path; report.frames=frames.size(); report.points=points;
        report.cells=cells.size(); report.badCells=badQuality;
        report.invalidFeatures=invalidFeatures;
        report.fallbackCount=j.fallbackMatrices;
        report.binningMs=binningMs;
        report.covarianceMs=covarianceMs; report.eigenMs=j.milliseconds;
        report.featuresMs=featuresMs; report.computeMs=computeOnlyMs;
        report.covariancePaceval=g_pacevalCovariance;
        report.featuresPaceval=g_pacevalFeatures;
        g_frameReports.push_back(report);
        // Post-processing diagnostics run AFTER all production timing snapshots.
        validateTincSelected(cells,j,diagnostics);
	}

}
int main() {
    const auto programStart = console_elapsed::Clock::now();
    console_elapsed::ScopedConsoleTimestamps timestampConsole(programStart);
    std::cout << "[RUN] paceval Automotive LiDAR Mathematical Processing Demonstrator\n";
    std::cout << "[RUN] Time prefix [+seconds] = monotonic elapsed time since main()\n";
    std::cout << "[RUN] Eigensolver = persistent paceval analytic angle + selective paceval Jacobi fallback\n";
    std::cout << "[LOG] Console output and errors saved to output\\paceval_lidar_run.log (overwritten each run).\n";
	int status = 0;
	// PACEVAL_LIDAR_BATCH_LIMIT=512|4096|16384 overrides tuning.
	// Unset/0: fast startup calibration by default; disable with PACEVAL_LIDAR_BATCH_AUTOTUNE=0.
#if defined(_MSC_VER)
	char* envValue = nullptr;
	size_t envLength = 0;
	if (_dupenv_s(&envValue, &envLength, "PACEVAL_LIDAR_BATCH_LIMIT") == 0 && envValue != nullptr) {
		char* end = nullptr;
		const unsigned long n = std::strtoul(envValue, &end, 10);
		if (end != envValue && *end == '\0')
			lidar::g_batchLimit = static_cast<size_t>(n);
	}
	std::free(envValue);
#else
	if (const char* envValue = std::getenv("PACEVAL_LIDAR_BATCH_LIMIT")) {
		char* end = nullptr;
		const unsigned long n = std::strtoul(envValue, &end, 10);
		if (end != envValue && *end == '\0')
			lidar::g_batchLimit = static_cast<size_t>(n);
	}
#endif
	try {
		lidar::g_validateTinc = lidar::readEnvUnsigned(
            "PACEVAL_LIDAR_VALIDATE_TINC", PACEVAL_LIDAR_VALIDATE_TINC ? 1u : 0u, 0u, 1u) != 0;
        std::cout << "[RUN] TINC post-processing diagnostics = "
                  << (lidar::g_validateTinc ? "ON" : "OFF")
                  << " (source default=" << (PACEVAL_LIDAR_VALIDATE_TINC ? "ON" : "OFF")
                  << "; environment override PACEVAL_LIDAR_VALIDATE_TINC=0|1)\n";
        lidar::g_tincSamples=lidar::readEnvUnsigned("PACEVAL_LIDAR_TINC_SAMPLES",12,1,128);
        lidar::g_tincWidthLimit=lidar::readEnvDouble("PACEVAL_LIDAR_TINC_MAX_REL_WIDTH",1e-9);
        lidar::g_tincDegenerateLimit=lidar::readEnvDouble("PACEVAL_LIDAR_TINC_DEGENERATE_REL",1e-8);
        if (!(lidar::g_tincWidthLimit>0.0) || !(lidar::g_tincDegenerateLimit>0.0))
            throw std::runtime_error("TINC width and degeneracy thresholds must be positive");
        lidar::g_fullActiveBatch=lidar::readEnvUnsigned("PACEVAL_LIDAR_FULL_ACTIVE_BATCH",1,0,1)!=0;
        std::cout << "[BATCH] Full-active batching=" << (lidar::g_fullActiveBatch ? "ON" : "OFF")
                  << " (safety cap 1048576; set PACEVAL_LIDAR_FULL_ACTIVE_BATCH=0 for tuned/manual chunks)\n";
        lidar::g_pacevalCovariance=lidar::readEnvUnsigned("PACEVAL_LIDAR_BATCH_COVARIANCE",0,0,1)!=0;
		lidar::g_pacevalFeatures=lidar::readEnvUnsigned("PACEVAL_LIDAR_BATCH_FEATURES",0,0,1)!=0;
		lidar::g_config.azBins = lidar::readEnvUnsigned("PACEVAL_LIDAR_AZ_BINS", 2048, 1, 16384);
		lidar::g_config.elBins = lidar::readEnvUnsigned("PACEVAL_LIDAR_EL_BINS", 64, 1, 2048);
		lidar::g_config.minPointsPerCell = lidar::readEnvUnsigned("PACEVAL_LIDAR_MIN_POINTS", 3, 3, 1000000);
		lidar::g_config.minElevation = lidar::readEnvDouble("PACEVAL_LIDAR_MIN_ELEV_RAD", -0.5);
		lidar::g_config.maxElevation = lidar::readEnvDouble("PACEVAL_LIDAR_MAX_ELEV_RAD", 0.5);
		if (!(lidar::g_config.minElevation < lidar::g_config.maxElevation) ||
			lidar::g_config.minElevation < -1.5707963267948966 ||
			lidar::g_config.maxElevation > 1.5707963267948966 ||
			static_cast<size_t>(lidar::g_config.azBins) * lidar::g_config.elBins > 2000000)
			throw std::runtime_error("Invalid grid/elevation settings");
		auto files = lidar::filesInData(); if (files.empty())throw std::runtime_error("No data/*.csv files found. Set Visual Studio Debugging > Working Directory to $(ProjectDir)");
		if (!paceval_InitializeLibrary(nullptr))throw std::runtime_error("paceval_InitializeLibrary failed");
		try {
            lidar::initializePersistentComputations();
            if (!lidar::analyticRegression()) throw std::runtime_error("Hybrid eigenspectrum regression failed");
            if (!lidar::g_fullActiveBatch && lidar::g_batchLimit == 0 && lidar::readEnvUnsigned("PACEVAL_LIDAR_BATCH_AUTOTUNE",1,0,1) != 0)
                lidar::calibrateBatchSize();
            else std::cout << "[BATCH] Startup calibration skipped (manual limit or disabled).\n";
            if (lidar::readEnvUnsigned("PACEVAL_LIDAR_PHASE_AUTOTUNE",1,0,1)!=0)
                lidar::benchmarkAndSelectPhases(files.front());
            else std::cout<<"[PHASE AUTOTUNE] disabled; manual covariance/features flags retained\n";
            const unsigned repeats=lidar::readEnvUnsigned("PACEVAL_LIDAR_REPEAT_FRAMES",3,1,50);
            for(unsigned rep=0;rep<repeats;++rep) {
                std::cout<<"[STREAM] frame_iteration="<<(rep+1)<<"/"<<repeats<<" reusable_handles=YES\n";
                for (const auto&f : files) lidar::process(f);
            }
            lidar::printEngineeringSummary();
        }
		catch (...) { lidar::releasePersistentComputations(); paceval_FreeLibrary(); throw; }
		lidar::releasePersistentComputations();
		paceval_FreeLibrary();
		std::cout << "\nAll CSV files processed. Review output/*_jacobi_features.csv.\n";
	}
	catch (const std::exception&e) { std::cerr << "ERROR: " << e.what() << "\n"; status = 1; }
	if (lidar::readEnvironment("PACEVAL_LIDAR_NONINTERACTIVE") == "1") return status;
	std::cout << "See results above (1 of 2). Press ENTER to continue..." << std::flush; std::cin.get();
	std::cout << "\nSee results above (2 of 2). Press ENTER to exit..." << std::flush; std::cin.get(); return status;
}
