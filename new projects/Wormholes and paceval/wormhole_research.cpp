/*
===============================================================================
 wormhole_100_stage1_api_documented.cpp
===============================================================================

Autonomous mathematical-structure search for Morris-Thorne wormhole candidates.
  Double-precision Visual C++ version: scalar and batched paceval evaluation.
  Negative constants are emitted as binary subtractions to avoid unary-minus ambiguity.

This is deliberately a RESEARCH DEMONSTRATOR, not a claim that a physical
wormhole exists. The program evolves the actual mathematical structure of
b(r) and Phi(r), not merely coefficients of one fixed formula family.

Core loop:
  random expression trees
	  -> construct b(r), Phi(r) with an exact throat condition and
       asymptotic flatness within the bounded grammar
	  -> symbolic differentiation
	  -> paceval Create
	  -> classical-GR screening on a radial grid
	  -> selection / mutation / crossover
	  -> repeat
	  -> high-resolution recheck
	  -> TINC batched pointwise recheck of the selected finalist
	  -> CSV + detailed logs

The program uses the public paceval API surface:
  paceval_InitializeLibrary(...) / paceval_FreeLibrary(...)
  paceval_CreateComputation(...) / paceval_DeleteComputation(...)
  paceval_dGetComputationResult(...) for scalar checks and diagnostics
  paceval_dGetComputationResultExt(...) for high-throughput radial batches
  paceval_GetIsError(...) / paceval_GetErrorInformation(...) for diagnostics

That makes the implementation intentionally easy to audit.

IMPORTANT SCIENTIFIC LIMITS
---------------------------
* Static Morris-Thorne wormholes in classical GR necessarily violate the
  radial null energy condition at the throat when the flare-out condition
  b'(r0)<1 is satisfied.
* The search space is finite and grammar-defined. "Autonomous discovery"
  means that the program composes structures not explicitly enumerated by
  the programmer; it does NOT mean the search covers all mathematical
  functions.
* Grid sampling is not a proof of a continuum inequality.
* TINC is used as a numerical interval check at sampled points. It is not a
  substitute for an analytic proof.
* Quantum Energy Inequalities are NOT implemented as an invented scalar
  threshold. A defensible QEI test requires a specified field, quantum state,
  observer/worldline and sampling function.
* Any interesting candidate must be independently reconstructed with a
  tensor/CAS package and compared with the scientific literature.


STAGE 1 SCIENTIFIC VALIDATION (2026-10-30)
----------------------------------------
* Three independently evaluable constant-U / constant-V geometries.
* All twelve fields (b, b', b'', Phi, Phi', Phi'', rho8, pr8, pt8,
  NEC8, Ricci, Kretschmann) tested against direct analytic derivatives.
* Closed-form independent baseline, GR trace and curvature-component tests.
* TINC scalar versus vectorized batch regression on six radii.
* Hard failure before search if any validation test fails.
* Note: sampled tests do not prove validity on entire radial intervals.


STAGE 3: RESEARCH DIAGNOSTICS AND BENCHMARKS
-------------------------------------------
* Adaptive verification skips floating-point-saturated subintervals instead
  of terminating all remaining refinement; it logs the exact stop reason.
* Proper-distance and static-frame tidal-curvature diagnostics are estimated
  using paceval batch evaluation; these are NOT certified interval integrals.
* For the present bounded finite expression grammar the throat condition and
  the asymptotic vanishing of Phi and b/r follow from the construction.
  This is a mathematical structural argument, not a paceval-TINC domain proof.
* Optional reproducibility experiment: --benchmark-seeds 30
  --benchmark-trials 100. CSV compares independent genetic-programming runs
  against a restricted random parameter-search baseline with equal evaluation
  budgets; this is NOT a comparison against optimized methods in the literature.
* No general continuum verification is claimed because the current API
  checks TINC intervals only at individual input values.

BUILD
-----
Add this file to an already working paceval Visual Studio C++ example project.
That avoids guessing your local include/library/DLL configuration.

Default run (no command-line arguments):
	100 newly evaluated candidates, verbose debug logging, TINC enabled.

Optional quick run:
	paceval_autonomous_wormhole_discovery.exe --smoke

Then:
	paceval_autonomous_wormhole_discovery.exe --population 200 --generations 40

A larger run:
	paceval_autonomous_wormhole_discovery.exe --population 1000 --generations 200

Diagnostic options:
	--investigations N
	--verbose 0|1|2|3
	--seed N
	--checkpoint N
	--no-tinc

===============================================================================
*/

#include <algorithm>
#include <array>
#include <chrono>
#include <thread>
#include <cmath>
#include <cstdint>
#include <cstdlib>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <limits>
#include <memory>
#include <random>
#include <sstream>
#include <stdexcept>
#include <string>
#include <unordered_set>
#include <utility>
#include <vector>

#include "../../system-independent/source_public/inc/paceval_main.h" //We include the paceval header

namespace awd {

	// ============================================================================
	// Logging
	// ============================================================================

	static int g_verbose = 2;
	static bool g_diagnose_paceval = false;
	static std::ofstream g_log;
	// Monotonic elapsed time since entry into main(), unaffected by clock changes.
	static std::chrono::steady_clock::time_point g_programStart = std::chrono::steady_clock::now();

	static std::string elapsedTag() {
		const double elapsed = std::chrono::duration<double>(
			std::chrono::steady_clock::now() - g_programStart).count();
		std::ostringstream out;
		out << "[+" << std::fixed << std::setprecision(3) << elapsed << "s] ";
		return out.str();
	}

	static std::string nowTag() {
		using namespace std::chrono;
		const auto ms = duration_cast<milliseconds>(
			system_clock::now().time_since_epoch()).count();
		return std::to_string(ms);
	}

	static void logLine(int level, const std::string& s) {
		const std::string line = elapsedTag() + s;
		if (level <= g_verbose) {
			std::cout << line << "\n";
			std::cout.flush();
		}
		if (g_log) {
			g_log << line << "\n";
			g_log.flush();
		}
	}

	static void warn(const std::string& s) { logLine(0, "[WARN]  " + s); }
	static void info(const std::string& s) { logLine(1, "[INFO]  " + s); }
	static void debug(const std::string& s) { logLine(2, "[DEBUG] " + s); }
	static void trace(const std::string& s) { logLine(3, "[TRACE] " + s); }

	// ============================================================================
	// Configuration
	// ============================================================================

	struct Options {
		std::uint64_t seed = 20261029ULL;
		unsigned population = 20;
		unsigned generations = 100; // Upper limit; stop after exactly 100 new evaluations
		unsigned elite = 4;
		unsigned coarsePoints = 72;
		unsigned finePoints = 1200;
		unsigned tincPoints = 1024;
		unsigned tincBatchSize = 128; // Configurable throughput/progress tradeoff; not a proven optimum
		unsigned paretoFinalLimit = 24; // Fast preview: 0 evaluates the complete archive at fine resolution
		unsigned benchmarkSeeds = 0; // Optional independent seed comparisons (30 recommended)
		unsigned benchmarkTrials = 100; // Equal function-evaluation budget per benchmark arm
		unsigned adaptivePoints = 256; // Additional pointwise TINC samples, adaptively selected; zero disables
		unsigned adaptiveWaveSize = 16; // Independent high-priority intervals evaluated together per adaptation round
		unsigned maxTreeDepth = 5;
		unsigned checkpointEvery = 1;
		unsigned verbose = 2;
		bool tinc = true;
		bool smoke = false;
		unsigned investigations = 100; // Default budget of newly evaluated candidates
	};

	static Options parseArgs(int argc, char** argv) {
		Options o;
		for (int i = 1; i < argc; ++i) {
			std::string a = argv[i];
			auto need = [&](const char* name)->const char* {
				if (i + 1 >= argc) throw std::runtime_error(
					std::string("Missing value after ") + name);
				return argv[++i];
			};
			if (a == "--seed") o.seed = std::strtoull(need("--seed"), nullptr, 10);
			else if (a == "--investigations") o.investigations =
				static_cast<unsigned>(std::strtoul(need("--investigations"), nullptr, 10));
			else if (a == "--population") o.population =
				static_cast<unsigned>(std::strtoul(need("--population"), nullptr, 10));
			else if (a == "--generations") o.generations =
				static_cast<unsigned>(std::strtoul(need("--generations"), nullptr, 10));
			else if (a == "--elite") o.elite =
				static_cast<unsigned>(std::strtoul(need("--elite"), nullptr, 10));
			else if (a == "--coarse-points") o.coarsePoints =
				static_cast<unsigned>(std::strtoul(need("--coarse-points"), nullptr, 10));
			else if (a == "--fine-points") o.finePoints =
				static_cast<unsigned>(std::strtoul(need("--fine-points"), nullptr, 10));
			else if (a == "--tinc-batch-size") o.tincBatchSize =
			static_cast<unsigned>(std::strtoul(need("--tinc-batch-size"), nullptr, 10));
			else if (a == "--pareto-final-limit") o.paretoFinalLimit =
                static_cast<unsigned>(std::strtoul(need("--pareto-final-limit"),nullptr,10));
			else if (a == "--benchmark-seeds") o.benchmarkSeeds =
                static_cast<unsigned>(std::strtoul(need("--benchmark-seeds"),nullptr,10));
            else if (a == "--benchmark-trials") o.benchmarkTrials =
                static_cast<unsigned>(std::strtoul(need("--benchmark-trials"),nullptr,10));
            else if (a == "--adaptive-points") o.adaptivePoints =
				static_cast<unsigned>(std::strtoul(need("--adaptive-points"), nullptr, 10));
			else if (a == "--adaptive-wave-size") o.adaptiveWaveSize =
				static_cast<unsigned>(std::strtoul(need("--adaptive-wave-size"), nullptr, 10));
			else if (a == "--tinc-points") o.tincPoints =
				static_cast<unsigned>(std::strtoul(need("--tinc-points"), nullptr, 10));
			else if (a == "--max-depth") o.maxTreeDepth =
				static_cast<unsigned>(std::strtoul(need("--max-depth"), nullptr, 10));
			else if (a == "--checkpoint") o.checkpointEvery =
				static_cast<unsigned>(std::strtoul(need("--checkpoint"), nullptr, 10));
			else if (a == "--verbose") o.verbose =
				static_cast<unsigned>(std::strtoul(need("--verbose"), nullptr, 10));
			else if (a == "--no-tinc") o.tinc = false;
			else if (a == "--smoke") o.smoke = true;
			else throw std::runtime_error("Unknown argument: " + a);
		}
		if (o.smoke) {
			o.population = 20;
			o.investigations = 20;
			o.generations = 3;
			o.elite = 4;
			o.coarsePoints = 32;
			o.finePoints = 200;
			o.tincPoints = 128;
			o.maxTreeDepth = 3;
			o.checkpointEvery = 1;
			o.verbose = std::max(o.verbose, 2u);
		}
		if (o.paretoFinalLimit > 100000) throw std::runtime_error("pareto-final-limit must be <= 100000");
		if (o.benchmarkSeeds>1000 || o.benchmarkTrials<20 || o.benchmarkTrials>100000)
            throw std::runtime_error("benchmark-seeds <=1000 and benchmark-trials 20..100000 required");
        if (o.adaptiveWaveSize < 1 || o.adaptiveWaveSize > 65536)
			throw std::runtime_error("adaptive-wave-size must be between 1 and 65536");
		if (o.adaptivePoints > 65536)
			throw std::runtime_error("adaptive-points must not exceed 65536");
		if (o.tincBatchSize < 1 || o.tincBatchSize > 65536)
			throw std::runtime_error("tinc-batch-size must be between 1 and 65536");
		if (o.investigations < 1) throw std::runtime_error("investigations must be >= 1");
		if (o.population < 4) throw std::runtime_error("population must be >= 4");
		if (o.elite < 2 || o.elite >= o.population)
			throw std::runtime_error("elite must be >=2 and < population");
		if (o.coarsePoints < 16 || o.finePoints < 32)
			throw std::runtime_error("radial grids are too small");
		return o;
	}

	// ============================================================================
	// Symbolic expression tree
	// ============================================================================

	enum class Op {
		CONST,
		Q,          // q=(r-1)/r; on r>=1 it lies in [0,1), approaching 1 as r->infinity
		ADD,
		SUB,
		MUL,
		DIV_SAFE,   // a / (1 + b^2), no pole
		EXP_NEG_SQ, // exp(-(a*a)), bounded
		SIN,
		COS,
		TANH_LIKE   // a / sqrt(1+a*a), bounded and paceval-friendly
	};

	struct Node {
		Op op = Op::CONST;
		double c = 0.0;
		std::unique_ptr<Node> a;
		std::unique_ptr<Node> b;

		Node() = default;
		explicit Node(double v) : op(Op::CONST), c(v) {}
		explicit Node(Op x) : op(x) {}

		std::unique_ptr<Node> clone() const {
			auto n = std::make_unique<Node>();
			n->op = op; n->c = c;
			if (a) n->a = a->clone();
			if (b) n->b = b->clone();
			return n;
		}
	};

	static unsigned arity(Op op) {
		switch (op) {
		case Op::CONST:
		case Op::Q: return 0;
		case Op::EXP_NEG_SQ:
		case Op::SIN:
		case Op::COS:
		case Op::TANH_LIKE: return 1;
		default: return 2;
		}
	}

	static std::string fmt(double x) {
		std::ostringstream s;
		s << std::setprecision(17) << x;
		return s.str();
	}

	// Avoid unary minus in paceval input: represent negative constants with binary subtraction.
	static std::string formulaConstant(double x) {
		if (x < 0.0) return "(0-" + fmt(-x) + ")";
		return "(" + fmt(x) + ")";
	}

	static std::string expr(const Node& n) {
		switch (n.op) {
		case Op::CONST: return formulaConstant(n.c);
		case Op::Q: return "((r-1)/r)";
		case Op::ADD: return "((" + expr(*n.a) + ")+(" + expr(*n.b) + "))";
		case Op::SUB: return "((" + expr(*n.a) + ")-(" + expr(*n.b) + "))";
		case Op::MUL: return "((" + expr(*n.a) + ")*(" + expr(*n.b) + "))";
		case Op::DIV_SAFE: {
			std::string B = expr(*n.b);
			return "((" + expr(*n.a) + ")/(1+(" + B + ")*(" + B + ")))";
		}
		case Op::EXP_NEG_SQ: {
			std::string A = expr(*n.a);
			return "exp((0-((" + A + ")*(" + A + "))))";
		}
		case Op::SIN: return "sin(" + expr(*n.a) + ")";
		case Op::COS: return "cos(" + expr(*n.a) + ")";
		case Op::TANH_LIKE: {
			std::string A = expr(*n.a);
			return "((" + A + ")/sqrt(1+(" + A + ")*(" + A + ")))";
		}
		}
		return "0";
	}

	static unsigned nodeCount(const Node& n) {
		return 1u + (n.a ? nodeCount(*n.a) : 0u) + (n.b ? nodeCount(*n.b) : 0u);
	}

	static unsigned depth(const Node& n) {
		return 1u + std::max(n.a ? depth(*n.a) : 0u, n.b ? depth(*n.b) : 0u);
	}

	// Numerical tree evaluator used to independently sanity-check paceval.
	static double evalTree(const Node& n, double q) {
		const double A = n.a ? evalTree(*n.a, q) : 0.0;
		const double B = n.b ? evalTree(*n.b, q) : 0.0;
		switch (n.op) {
		case Op::CONST: return n.c;
		case Op::Q: return q;
		case Op::ADD: return A + B;
		case Op::SUB: return A - B;
		case Op::MUL: return A * B;
		case Op::DIV_SAFE: return A / (1.0 + B * B);
		case Op::EXP_NEG_SQ: return std::exp(-(A*A));
		case Op::SIN: return std::sin(A);
		case Op::COS: return std::cos(A);
		case Op::TANH_LIKE: return A / std::sqrt(1.0 + A * A);
		}
		return 0.0;
	}

	// ============================================================================
	// Symbolic differentiation as strings
	// ============================================================================
	//
	// We differentiate final paceval expressions with respect to r using a small
	// symbolic string algebra. The tree itself uses q=(r-1)/r, whose derivatives
	// are exact:
	//     q'  = 1/r^2
	//     q'' = -2/r^3
	//
	// For robustness and auditability, we generate value, first derivative and
	// second derivative simultaneously for each grammar node.
	// ============================================================================

	struct D2 {
		std::string v, d1, d2;
	};

	// -------------------------------------------------------------------------
	// SAFE SYMBOLIC IDENTITIES (crucial for TINC)
	// -------------------------------------------------------------------------
	// The old differentiator emitted expressions like
	//    (0/r) - ((1 + q*0)/(r*r))
	// for the exact derivative of b=1/r. The ordinary double API evaluated
	// the expression, but the TINC engine reported division error 142 at
	// perfectly regular radii. This is an avoidable intermediate expression,
	// not a pole in the analytic solution.
	//
	// Simplify *during construction* rather than using textual substitutions
	// on finished expressions. We recognize only exact symbolic 0 and 1,
	// never "almost zero" floating-point numbers. This preserves meaningful
	// near-zero terms and avoids changing physically significant results.
	//
	// The identities 0*x=0 and 0/x=0 assume a well-defined finite operand
	// and nonzero denominator on the physical domain r>=1. The grammar's
	// DIV_SAFE denominator 1+y^2 is strictly positive, and the geometric
	// denominators are powers of r. Should arbitrary potentially singular
	// functions be added, re-evaluate these simplification preconditions.
	static bool symbolicZero(const std::string& s) {
		return s=="0" || s=="(0)" || s=="(0.0)" || s=="0.0";
	}
	static bool symbolicOne(const std::string& s) {
		return s=="1" || s=="(1)" || s=="(1.0)" || s=="1.0";
	}
	static std::string A(const std::string& x, const std::string& y)
	{
		if (symbolicZero(x)) return y;
		if (symbolicZero(y)) return x;
		return "((" + x + ")+(" + y + "))";
	}
	static std::string S(const std::string& x, const std::string& y)
	{
		if (symbolicZero(y)) return x;
		if (x == y) return "0";
		if (symbolicZero(x)) return "((0)-(" + y + "))";
		return "((" + x + ")-(" + y + "))";
	}
	static std::string M(const std::string& x, const std::string& y)
	{
		if (symbolicZero(x) || symbolicZero(y)) return "0";
		if (symbolicOne(x)) return y;
		if (symbolicOne(y)) return x;
		return "((" + x + ")*(" + y + "))";
	}
	static std::string D(const std::string& x, const std::string& y)
	{
		if (symbolicZero(x)) return "0";
		if (symbolicOne(y)) return x;
		return "((" + x + ")/(" + y + "))";
	}
	static std::string SQ(const std::string& x) { return M(x, x); }

	static D2 diff2(const Node& n) {
		if (n.op == Op::CONST) return { formulaConstant(n.c),"0","0" };
		if (n.op == Op::Q) return { "((r-1)/r)","(1/(r*r))","((0-2)/(r*r*r))" };

		D2 x = diff2(*n.a);
		D2 y;
		if (n.b) y = diff2(*n.b);

		if (n.op == Op::ADD)
			return { A(x.v,y.v), A(x.d1,y.d1), A(x.d2,y.d2) };
		if (n.op == Op::SUB)
			return { S(x.v,y.v), S(x.d1,y.d1), S(x.d2,y.d2) };
		if (n.op == Op::MUL) {
			return {
				M(x.v,y.v),
				A(M(x.d1,y.v),M(x.v,y.d1)),
				A(A(M(x.d2,y.v),M("2",M(x.d1,y.d1))),M(x.v,y.d2))
			};
		}
		if (n.op == Op::SIN) {
			return {
				"sin(" + x.v + ")",
				M("cos(" + x.v + ")",x.d1),
				A(M(M("(0-1)","sin(" + x.v + ")"),SQ(x.d1)),
				  M("cos(" + x.v + ")",x.d2))
			};
		}
		if (n.op == Op::COS) {
			return {
				"cos(" + x.v + ")",
				M(M("(0-1)","sin(" + x.v + ")"),x.d1),
				S(M(M("(0-1)","cos(" + x.v + ")"),SQ(x.d1)),
				  M("sin(" + x.v + ")",x.d2))
			};
		}
		if (n.op == Op::EXP_NEG_SQ) {
			// f=exp(-x^2)
			// f'=-2 x x' f
			// f''=f*[4 x^2 x'^2 -2 x'^2 -2 x x'']
			std::string f = "exp((0-(" + SQ(x.v) + ")))";
			return {
				f,
				M(M(M("(0-2)",x.v),x.d1),f),
				M(f, A(A(M("4",M(SQ(x.v),SQ(x.d1))),
							 M("(0-2)",SQ(x.d1))),
						M("(0-2)",M(x.v,x.d2))))
			};
		}
		if (n.op == Op::TANH_LIKE) {
			// f=x/sqrt(1+x^2)
			// f' = x'/(1+x^2)^(3/2)
			// f''=x''/(1+x^2)^(3/2)-3*x*x'^2/(1+x^2)^(5/2)
			std::string den = A("1", SQ(x.v));
			std::string root = "sqrt(" + den + ")";
			std::string den32 = M(den, root);
			std::string den52 = M(M(den, den), root);
			return {
				D(x.v,root),
				D(x.d1,den32),
				S(D(x.d2,den32),D(M("3",M(x.v,SQ(x.d1))),den52))
			};
		}
		if (n.op == Op::DIV_SAFE) {
			// f=x/(1+y^2). Instead of maintaining a fragile quotient second
			// derivative by hand, rewrite as x * h with h=(1+y^2)^-1.
			// h'=-g'/g^2; h''=2g'^2/g^3-g''/g^2
			std::string g = A("1", SQ(y.v));
			std::string gp = M("2", M(y.v, y.d1));
			std::string gpp = M("2", A(SQ(y.d1), M(y.v, y.d2)));
			std::string h = D("1", g);
			std::string hp = M("(0-1)", D(gp, SQ(g)));
			std::string hpp = S(D(M("2", SQ(gp)), M(SQ(g), g)), D(gpp, SQ(g)));
			return {
				M(x.v,h),
				A(M(x.d1,h),M(x.v,hp)),
				A(A(M(x.d2,h),M("2",M(x.d1,hp))),M(x.v,hpp))
			};
		}

		throw std::runtime_error("diff2: unsupported operator");
	}

	// ============================================================================
	// Random grammar, mutation, crossover
	// ============================================================================

	static std::unique_ptr<Node> randomTree(std::mt19937_64& rng,
		unsigned depthLeft)
	{
		std::uniform_real_distribution<double> u(0.0, 1.0);
		std::normal_distribution<double> c(0.0, 1.0);

		if (depthLeft == 0 || u(rng) < 0.28) {
			if (u(rng) < 0.35) return std::make_unique<Node>(Op::Q);
			return std::make_unique<Node>(std::max(-3.0, std::min(3.0, c(rng))));
		}

		static const std::array<Op, 8> ops = {
			Op::ADD,Op::SUB,Op::MUL,Op::DIV_SAFE,
			Op::EXP_NEG_SQ,Op::SIN,Op::COS,Op::TANH_LIKE
		};
		std::uniform_int_distribution<unsigned> pick(0,
			static_cast<unsigned>(ops.size() - 1));

		Op op = ops[pick(rng)];
		auto n = std::make_unique<Node>(op);
		n->a = randomTree(rng, depthLeft - 1);
		if (arity(op) == 2) n->b = randomTree(rng, depthLeft - 1);
		return n;
	}

	static void collectNodes(Node& n, std::vector<Node*>& out) {
		out.push_back(&n);
		if (n.a) collectNodes(*n.a, out);
		if (n.b) collectNodes(*n.b, out);
	}

	static void mutateConstants(Node& n, std::mt19937_64& rng, double sigma) {
		std::normal_distribution<double> d(0.0, sigma);
		if (n.op == Op::CONST) n.c = std::max(-5.0, std::min(5.0, n.c + d(rng)));
		if (n.a) mutateConstants(*n.a, rng, sigma);
		if (n.b) mutateConstants(*n.b, rng, sigma);
	}

	// Replace a randomly chosen subtree. Root replacement is handled explicitly.
	static void mutateStructure(std::unique_ptr<Node>& root,
		std::mt19937_64& rng,
		unsigned maxDepth)
	{
		std::uniform_real_distribution<double> u(0.0, 1.0);
		if (u(rng) < 0.20) {
			root = randomTree(rng, std::max(1u, maxDepth / 2));
			return;
		}

		std::vector<Node*> nodes;
		collectNodes(*root, nodes);
		std::uniform_int_distribution<std::size_t> pick(0, nodes.size() - 1);
		Node* target = nodes[pick(rng)];

		if (target->op == Op::CONST && u(rng) < 0.60) {
			std::normal_distribution<double> d(0.0, 0.35);
			target->c = std::max(-5.0, std::min(5.0, target->c + d(rng)));
			return;
		}

		auto replacement = randomTree(rng, std::max(1u, maxDepth / 2));
		*target = std::move(*replacement);
	}

	// Crossover copies a random subtree from donor into child.
	static void crossoverInto(std::unique_ptr<Node>& child,
		const Node& donor,
		std::mt19937_64& rng)
	{
		std::vector<Node*> targets;
		collectNodes(*child, targets);

		// Gather donor pointers read-only using a local recursive lambda.
		std::vector<const Node*> sources;
		auto gather = [&](auto&& self, const Node& n)->void {
			sources.push_back(&n);
			if (n.a) self(self, *n.a);
			if (n.b) self(self, *n.b);
		};
		gather(gather, donor);

		std::uniform_int_distribution<std::size_t> pt(0, targets.size() - 1);
		std::uniform_int_distribution<std::size_t> ps(0, sources.size() - 1);
		Node* t = targets[pt(rng)];
		auto repl = sources[ps(rng)]->clone();
		*t = std::move(*repl);
	}

	// ============================================================================
	// Genome -> constrained metric functions
	// ============================================================================

	struct Genome {
		std::unique_ptr<Node> shapeCore;
		std::unique_ptr<Node> redshiftCore;

		Genome clone() const {
			Genome g;
			g.shapeCore = shapeCore->clone();
			g.redshiftCore = redshiftCore->clone();
			return g;
		}
	};

	struct MetricExpressions {
		std::string b, bp, bpp, phi, phip, phipp;
		std::string rho8, pr8, pt8, nec8, ricci, kretsch;
	};

	static MetricExpressions buildMetric(const Genome& g, bool alternateTincForm = false) {
		D2 U = diff2(*g.shapeCore);
		D2 V = diff2(*g.redshiftCore);

		// Constructive constraints:
		//
		// q=(r-1)/r, s=1/r.
		//
		// b = s * [1 + q*U(q)]
		// -> b(1)=1 exactly. For THIS grammar, U is continuous and bounded
		//    on q in [0,1]: constants and q are bounded; sums/products of
		//    bounded functions remain bounded; sin, cos, exp(-x*x) are bounded;
		//    DIV_SAFE has denominator 1+y*y >= 1; x/sqrt(1+x*x) is bounded.
		//    Therefore b/r = (1+q*U)/r^2 -> 0 analytically as r -> infinity.
		//    This does NOT prove all exterior inequalities or traversability.
		//
		// Phi = s * V(q)
		// -> Phi -> 0 analytically as r -> infinity because V is bounded
		//    under the same finite-expression, protected-operator assumptions.
		//
		// We calculate derivatives using product rules from the already generated
		// derivatives of U and V.
		const D2 q = { "((r-1)/r)","(1/(r*r))","((0-2)/(r*r*r))" };
		const D2 s = { "(1/r)","((0-1)/(r*r))","(2/(r*r*r))" };

		auto mulD = [](const D2& x, const D2& y)->D2 {
			return {
				M(x.v,y.v),
				A(M(x.d1,y.v),M(x.v,y.d1)),
				A(A(M(x.d2,y.v),M("2",M(x.d1,y.d1))),M(x.v,y.d2))
			};
		};
		auto addD = [](const D2& x, const D2& y)->D2 {
			return { A(x.v,y.v),A(x.d1,y.d1),A(x.d2,y.d2) };
		};

		// ----------------------------------------------------------------------
		// TINC STABILITY: work with B(r) = 1 + q(r)*U(r), so b(r)=B(r)/r.
		//
		// Let P(r) = dB/dr = q'*U + q*U'.  Here U' is dU/dr, NOT dU/dq:
		// diff2() has already applied the chain rule for q(r)=(r-1)/r.
		// Exact identities:
		//   b' = P/r - B/r^2
		//   b'' = B''/r - 2*P/r^2 + 2*B/r^3
		//   Delta := r*b' - b = P - 2*B/r
		//
		// Computing Delta directly avoids the larger expression r*b'-b,
		// which can magnify dependency/rounding in interval arithmetic.
		// ----------------------------------------------------------------------
		const D2 one = { "1","0","0" };
		// The default expression builds 1+q*U directly. A rare paceval TINC
		// arithmetic error (observed code 144 at an addition) can leave every
		// downstream field unverified. The alternate form uses the EXACT identity
		//   1+q*U = [r+(r-1)*U]/r.
		// It changes the operation graph, not the mathematical metric. Both
		// forms are compiled and evaluated by paceval; no external math engine.
		// This is a diagnostic recovery route, NOT a guarantee that TINC will pass.
		const D2 rD = {"r","1","0"};
		const D2 rm1D = {"(r-1)","1","0"};
		const D2 Bmetric = alternateTincForm
			? mulD(addD(rD,mulD(rm1D,U)),s)
			: addD(one, mulD(q,U));
		const std::string& Bv = Bmetric.v;
		const std::string& P = Bmetric.d1;
		const std::string delta = S(P,D(M("2",Bv),"r"));
		const D2 b = {
			D(Bv,"r"),
			S(D(P,"r"),D(Bv,"(r*r)")),
			A(S(D(Bmetric.d2,"r"),D(M("2",P),"(r*r)")),
			  D(M("2",Bv),"(r*r*r)"))
		};
		const D2 phi = mulD(s,V);

		// In the wormhole exterior r>=1 we can factor exactly:
		//   1 - b/r = (r^2 - 1 - q*U)/r^2
		//           = q*[r*(r+1)-U]/r^2.
		// This removes the subtraction of two nearly equal numbers at r~1.
		// We do NOT divide by q, because q=0 at the throat.
		const std::string oneMinusBR = D(
			M(q.v,S(M("r",A("r","1")),U.v)),"(r*r)");

		// Classical GR diagnostic quantities. Preserve original formulas for
		// rho and the pressures, but use the factored exterior where possible.
		const std::string rho8 = D(b.d1,"(r*r)");
		const std::string pr8 = A(M("(0-1)",D(b.v,"(r*r*r)")),
			M("2",M(oneMinusBR,D(phi.d1,"r"))));
		const std::string pt8 = S(S(M(oneMinusBR,A(A(phi.d2,SQ(phi.d1)),D(phi.d1,"r"))),
			D(M(delta,phi.d1),"(2*r*r)")), D(delta,"(2*r*r*r)"));

		// Stable radial NEC: use one common r^3 denominator. Do not first
		// evaluate rho and p_r separately, then subtract nearly equal values.
		//   8*pi*(rho+p_r) = Delta/r^3 + 2*(1-b/r)*Phi'/r
		//                     = [Delta + 2*r^2*(1-b/r)*Phi']/r^3.
		const std::string necNumerator = A(delta,
			M("2",M(M("(r*r)",oneMinusBR),phi.d1)));
		const std::string nec8 = D(necNumerator,"(r*r*r)");

		// Orthonormal Riemann components reused by Ricci and Kretschmann.
		// Reusing components reduces duplicated chains of cancellation-prone
		// arithmetic. These are algebraic transformations, not error suppression.
		const std::string RA = S(M(oneMinusBR,A(phi.d2,SQ(phi.d1))),
			D(M(phi.d1,delta),"(2*r*r)"));
		const std::string RB = M(oneMinusBR,D(phi.d1,"r"));
		const std::string RC = D(delta,"(2*r*r*r)");
		const std::string RD = D(Bv,"(r*r*r*r)");
		const std::string ricci = A(A(M("(0-2)",RA),M("(0-4)",RB)),
			A(M("4",RC),M("2",RD)));
		const std::string K = M("4",A(A(SQ(RA),M("2",SQ(RB))),
			A(M("2",SQ(RC)),SQ(RD))));
		// IMPORTANT: An error 145 may still occur inside paceval's TINC engine.
		// Such a point remains UNVERIFIED. No fallback may fabricate bounds.

		return { b.v,b.d1,b.d2,phi.v,phi.d1,phi.d2,
				rho8,pr8,pt8,nec8,ricci,K };
	}

	// ============================================================================
	// paceval computation bundle
	// ============================================================================

	enum FI { B = 0, BP, BPP, PHI, PHIP, PHIPP, RHO8, PR8, PT8, NEC8, RICCI, KRET, NFUN };

	static const char* functionName(unsigned i) {
		static const char* names[] = { "b", "b_prime", "b_second", "Phi", "Phi_prime", "Phi_second",
			"8pi_rho", "8pi_pr", "8pi_pt", "8pi_NEC", "Ricci_R", "Kretschmann_K" };
		return i < NFUN ? names[i] : "INVALID_INDEX";
	}

	struct PaceBundle {
		// Only the expressions required in the current screening and TINC paths.
		static constexpr unsigned required[6] = { B, BP, PHI, NEC8, RICCI, KRET };
		std::array<PACEVAL_HANDLE, NFUN> h{};
		std::array<std::string, NFUN> f{};
		bool tinc = false;
		bool ok = false;

		PaceBundle(const MetricExpressions& m, bool useTinc) :tinc(useTinc) {
			f = { m.b,m.bp,m.bpp,m.phi,m.phip,m.phipp,m.rho8,m.pr8,m.pt8,
			   m.nec8,m.ricci,m.kretsch };
			h.fill(NULL);

			for (unsigned fi = 0; fi < 6; ++fi) {
				unsigned i = required[fi];
				if (g_diagnose_paceval) {
					info(std::string("[CREATE BEGIN] index=") + std::to_string(i) +
						" name=" + functionName(i) + " length=" + std::to_string(f[i].size()) +
						" tinc=" + (tinc ? "1" : "0"));
					if (!tinc) debug(std::string("[CREATE EXPR] ") + functionName(i) + " = " + f[i]);
				}
				const auto handleStart = std::chrono::steady_clock::now();
				// paceval_CreateComputation parses and compiles each formula ONCE into
				// an opaque reusable execution handle. One variable ("r") suffices.
				// Set TINC only in the verification phase: interval bookkeeping
				// during all evolutionary evaluations would increase cost.
				// The last NULL uses the SDK default optional configuration.
				h[i] = paceval_CreateComputation(f[i].c_str(), 1, "r", tinc, NULL);
				if (g_diagnose_paceval) {
					const double dt = std::chrono::duration<double>(
						std::chrono::steady_clock::now() - handleStart).count();
					info(std::string("[CREATE TIME] ") + functionName(i) + " seconds=" + fmt(dt));
				}
				if (g_diagnose_paceval) info(std::string("[CREATE END] ") + functionName(i) + (h[i] ? " SUCCESS" : " FAILED"));
				// A non-null handle may still carry an API error state.
				if (h[i] != NULL && paceval_GetIsError(h[i])) {
					char operatorName[256] = {};
					long errorPosition = -1;
					// Retrieve exact SDK error code, operator, and expression offset.
					const int code = paceval_GetErrorInformation(h[i], operatorName, &errorPosition);
					warn(std::string("[PACEVAL CREATE ERROR] ") + functionName(i) +
						" code=" + std::to_string(code) + " operator=" + operatorName +
						" position=" + std::to_string(errorPosition));
					cleanup();
					return;
				}
				if (h[i] == NULL) {
					warn(std::string("[CREATE FAILED] index=") + std::to_string(i) +
						" name=" + functionName(i) + " expression_length=" + std::to_string(f[i].size()));
					warn("Expression: " + f[i]);
					cleanup();
					return;
				}
			}
			ok = true;
		}

		~PaceBundle() { cleanup(); }
		PaceBundle(const PaceBundle&) = delete;
		PaceBundle& operator=(const PaceBundle&) = delete;

		void cleanup() {
			for (auto& x : h) {
				if (x != NULL) {
					// Free compiled graph and associated SDK resources; no handle leaks.
					paceval_DeleteComputation(x);
					x = NULL;
				}
			}
			ok = false;
		}

		bool eval(unsigned fi, double r, double& value,
			double* lo = nullptr, double* hi = nullptr) const
		{
			if (!ok || fi >= NFUN || h[fi] == NULL) {
				warn("[EVAL INVALID] index=" + std::to_string(fi) + " bundle_ok=" + std::to_string(ok));
				return false;
			}
			double vars[1] = { r };
			// Scalar double API: exact requested radius; optional lo/hi are
			// meaningful when TINC was enabled at handle creation.
			// Use instead of batch only for throat checks / diagnostics.
			value = paceval_dGetComputationResult(h[fi], vars, lo, hi);
			if (paceval_GetIsError(h[fi])) {
				char operatorName[256] = {};
				long errorPosition = -1;
				const int code = paceval_GetErrorInformation(h[fi], operatorName, &errorPosition);
				warn(std::string("[PACEVAL EVAL ERROR] ") + functionName(fi) +
					" r=" + fmt(r) + " code=" + std::to_string(code) +
					" operator=" + operatorName + " position=" + std::to_string(errorPosition));
				return false;
			}
			const bool finite = std::isfinite(value);
			if (!finite) {
				warn(std::string("[EVAL NONFINITE] ") + functionName(fi) +
					" r=" + fmt(static_cast<double>(r)) + " value=" + fmt(static_cast<double>(value)));
			}
			if (g_diagnose_paceval) {
				debug(std::string("[EVAL] ") + functionName(fi) +
					" r=" + fmt(static_cast<double>(r)) +
					" value=" + fmt(static_cast<double>(value)));
			}
			return finite;
		}
		// One API call per mathematical expression, covering the full radial grid.
		// This reduces per-point API overhead and makes independent input sets
		// available to the SDK batch executor. Actual thread count and speedup
		// depend on SDK configuration, formula complexity, and hardware.
		bool evalGrid(unsigned fi, const std::vector<double>& radii,
			std::vector<double>& values) const {
			if (!ok || fi >= NFUN || h[fi] == NULL || radii.empty()) return false;
			values.resize(radii.size());
			std::vector<int> errors(radii.size(), 0);
			// API requires non-const double* inputs; do not modify caller data.
			std::vector<double> inputs(radii);
			// Batch double API: one formula evaluated at N radii. The
			// results and per-point codes are caller-owned contiguous buffers.
			// NULL interval arrays avoid unnecessary TINC output in screening.
			// Fewer host calls allow the SDK to schedule work efficiently; the
			// optimal throughput depends on the actual paceval build.
			const bool hasError = paceval_dGetComputationResultExt(
				h[fi], inputs.data(), static_cast<unsigned long>(inputs.size()),
				values.data(), NULL, NULL, errors.data());
			bool good = !hasError;
			for (std::size_t k = 0; k < radii.size(); ++k) {
				if (errors[k] != 0 || !std::isfinite(values[k])) {
					warn(std::string("[BATCH ERROR] ") + functionName(fi) +
						" index=" + std::to_string(k) + " r=" + fmt(radii[k]) +
						" error=" + std::to_string(errors[k]));
					good = false;
					break;
				}
			}
			if (!good) {
				// Diagnostics: reproduce the failing point via the scalar API.
				for (std::size_t k = 0; k < radii.size(); ++k) {
					if (errors[k] != 0 || !std::isfinite(values[k])) {
						double v = 0;
						eval(fi, radii[k], v);
						break;
					}
				}
				if (hasError) warn(std::string("[BATCH RETURN ERROR] ") + functionName(fi));
			}
			return good;
		}

	};

	// ============================================================================
	// Fitness
	// ============================================================================

	enum class Reject {
		NONE, CREATE, NONFINITE, THROAT, EXTERIOR, CURVATURE, REDSHIFT, COMPLEXITY
	};

	static const char* rejectName(Reject r) {
		switch (r) {
		case Reject::NONE:return "accepted";
		case Reject::CREATE:return "create";
		case Reject::NONFINITE:return "nonfinite";
		case Reject::THROAT:return "throat";
		case Reject::EXTERIOR:return "exterior";
		case Reject::CURVATURE:return "curvature";
		case Reject::REDSHIFT:return "redshift";
		case Reject::COMPLEXITY:return "complexity";
		}
		return "?";
	}

	struct Fitness {
		bool valid = false;
		Reject reject = Reject::NONE;
		double score = std::numeric_limits<double>::infinity();
		double negNec = 0.0;
        // Second Pareto objective: worst of static radial and angular tidal curvature.
        // Computed by physicalDiagnostics() on the search grid; not a traveller-frame acceleration.
        double tidalObjective = std::numeric_limits<double>::infinity();
		double signedViq = 0.0;
		double minNec8 = 0.0;
		double bp0 = 0.0;
		double maxAbsR = 0.0;
		double maxK = 0.0;
		double maxAbsPhi = 0.0;
		double minExterior = 0.0;
		unsigned nodes = 0;
		unsigned depth = 0;
	};

	struct Individual {
		Genome g;
		Fitness fit;
		bool evaluated = false;
		std::string signature;

		Individual clone() const {
			Individual x;
			x.g = g.clone();
			x.fit = fit;
			x.evaluated = evaluated;
			x.signature = signature;
			return x;
		}
	};

	static std::vector<double> grid(unsigned n, double rmax) {
		std::vector<double> r(n);
		const double eps = 1e-7;
		for (unsigned i = 0; i < n; ++i) {
			double u = static_cast<double>(i) / (n - 1);
			// cubic concentration near throat
			r[i] = 1.0 + eps + (rmax - 1.0 - eps)*u*u*u;
		}
		return r;
	}

	static Fitness evaluateGenome(const Genome& g,
		const std::vector<double>& radii,
		bool diagnostic = false)
	{
		struct DiagnosticScope {
			bool previous;
			explicit DiagnosticScope(bool enabled) : previous(g_diagnose_paceval) {
				g_diagnose_paceval = enabled;
			}
			~DiagnosticScope() { g_diagnose_paceval = previous; }
		} diagScope(diagnostic);
		Fitness z;
		if (diagnostic) info("[DIAG BEGIN] evaluateGenome: radial_points=" + std::to_string(radii.size()));
		z.nodes = nodeCount(*g.shapeCore) + nodeCount(*g.redshiftCore);
		z.depth = std::max(depth(*g.shapeCore), depth(*g.redshiftCore));

		if (z.nodes > 180 || z.depth > 14) {
			z.reject = Reject::COMPLEXITY;
			return z;
		}

		MetricExpressions m;
		try { m = buildMetric(g); }
		catch (const std::exception& e) {
			if (diagnostic) warn(std::string("buildMetric exception: ") + e.what());
			z.reject = Reject::CREATE; return z;
		}

		if (diagnostic) {
			debug("shape core U(q) = " + expr(*g.shapeCore));
			debug("redshift V(q)   = " + expr(*g.redshiftCore));
			trace("b(r)   = " + m.b);
			trace("Phi(r) = " + m.phi);
		}

		PaceBundle p(m, false);
		if (!p.ok) { warn("[REJECT CREATE] One or more computation handles could not be created"); z.reject = Reject::CREATE; return z; }

		// Evaluate throat derivative just outside throat and also compare against
		// an independent finite-difference estimate of b from paceval.
		double bpv = 0;
		if (!p.eval(BP, 1.0, bpv)) {
			warn("[REJECT NONFINITE] b_prime at throat r=1 failed");
			z.reject = Reject::NONFINITE; return z;
		}
		z.bp0 = static_cast<double>(bpv);
		if (diagnostic) info("[THROAT] b_prime(1)=" + fmt(z.bp0) + " expected baseline=-1");

		if (!(z.bp0 < 1.0 - 1e-6) || z.bp0 < -100.0) {
			warn("[REJECT THROAT] b_prime(1)=" + fmt(z.bp0) + " required -100 <= b_prime < 0.999999");
			z.reject = Reject::THROAT; return z;
		}

		z.minNec8 = std::numeric_limits<double>::infinity();
		z.minExterior = std::numeric_limits<double>::infinity();

		double prevNeg = 0, prevSigned = 0;
		bool first = true;

		// Bulk evaluation: only five expressions are required on the grid.
		// This avoids 5*N individual API calls and uses paceval's internal parallelization.
		const unsigned fields[] = { B, PHI, NEC8, RICCI, KRET };
		std::array<std::vector<double>, 5> batch;
		const auto batchStart = std::chrono::steady_clock::now();
		for (unsigned j = 0; j < 5; ++j) {
			if (!p.evalGrid(fields[j], radii, batch[j])) {
				warn(std::string("[REJECT BATCH] field=") + functionName(fields[j]));
				z.reject = Reject::NONFINITE;
				return z;
			}
		}
		if (diagnostic) {
			const double elapsed = std::chrono::duration<double>(
				std::chrono::steady_clock::now() - batchStart).count();
			info("[BATCH] points=" + std::to_string(radii.size()) +
				" functions=5 seconds=" + fmt(elapsed));
		}
		for (std::size_t i = 0; i < radii.size(); ++i) {
			const double vb = batch[0][i], vphi = batch[1][i];
			const double vnec = batch[2][i], vR = batch[3][i], vK = batch[4][i];

			double b = static_cast<double>(vb);
			double ph = static_cast<double>(vphi);
			double ne = static_cast<double>(vnec);
			double rc = static_cast<double>(vR);
			double kk = static_cast<double>(vK);
			double r = radii[i];

			double ext = 1.0 - b / r;
			z.minExterior = std::min(z.minExterior, ext);
			z.minNec8 = std::min(z.minNec8, ne);
			z.maxAbsR = std::max(z.maxAbsR, std::abs(rc));
			z.maxK = std::max(z.maxK, kk);
			z.maxAbsPhi = std::max(z.maxAbsPhi, std::abs(ph));

			if (!(ext > 1e-10)) {
				warn("[REJECT EXTERIOR] index=" + std::to_string(i) + " r=" + fmt(r) +
					" b=" + fmt(b) + " 1-b/r=" + fmt(ext));
				z.reject = Reject::EXTERIOR; return z;
			}
			if (!(kk >= -1e-10) || std::abs(rc) > 1e3 || kk > 1e6) {
				warn("[REJECT CURVATURE] index=" + std::to_string(i) + " r=" + fmt(r) +
					" Ricci=" + fmt(rc) + " K=" + fmt(kk));
				z.reject = Reject::CURVATURE; return z;
			}
			if (std::abs(ph) > 30.0) {
				warn("[REJECT REDSHIFT] index=" + std::to_string(i) + " r=" + fmt(r) + " Phi=" + fmt(ph));
				z.reject = Reject::REDSHIFT; return z;
			}

			double signedDensity = 0.5*r*r*ne;
			double negDensity = 0.5*r*r*std::max(0.0, -ne);

			if (!first) {
				double dr = radii[i] - radii[i - 1];
				z.signedViq += 0.5*(prevSigned + signedDensity)*dr;
				z.negNec += 0.5*(prevNeg + negDensity)*dr;
			}
			prevSigned = signedDensity;
			prevNeg = negDensity;
			first = false;
		}

		// Parsimony matters: prefer a simpler equation when physical quality is
		// comparable. This is essential for interpretable discovery.
		const double complexityPenalty = 2e-5*static_cast<double>(z.nodes);
		const double flarePenalty = 2e-5 / std::max(1e-8, 1.0 - z.bp0);
		const double phiPenalty = 1e-5*z.maxAbsPhi*z.maxAbsPhi;
		const double curvaturePenalty = 1e-8*z.maxAbsR*z.maxAbsR + 1e-11*z.maxK;

		z.score = z.negNec + complexityPenalty + flarePenalty +
			phiPenalty + curvaturePenalty;
		z.valid = std::isfinite(z.score);
		z.reject = z.valid ? Reject::NONE : Reject::NONFINITE;
		if (diagnostic) info("[DIAG END] valid=" + std::to_string(z.valid) +
			" score=" + fmt(z.score) + " minNEC8=" + fmt(z.minNec8) +
			" maxK=" + fmt(z.maxK) + " minExterior=" + fmt(z.minExterior));
		return z;
	}

	// ============================================================================
	// Independent derivative sanity check
	// ============================================================================

	static bool derivativeSanity(const Genome& g) {
		MetricExpressions m = buildMetric(g);
		PaceBundle p(m, false);
		if (!p.ok) return false;

		const std::array<double, 3> rs = { 1.2,2.0,5.0 };
		double worst = 0.0;

		for (double r : rs) {
			const double h = 1e-5;
			double bm = 0, b0 = 0, bp = 0, analytic = 0;
			if (!p.eval(B, r - h, bm) || !p.eval(B, r, b0) || !p.eval(B, r + h, bp) ||
				!p.eval(BP, r, analytic)) return false;
			double fd = (bp - bm) / (2 * h);
			double scale = std::max(1.0, std::abs(static_cast<double>(analytic)));
			worst = std::max(worst,
				std::abs(static_cast<double>(fd - analytic)) / scale);
		}
		info("Derivative sanity worst relative error = " + fmt(worst));
		return worst < 1e-5;
	}

	// ============================================================================
	// Population mechanics
	// ============================================================================

	static Individual randomIndividual(std::mt19937_64& rng, unsigned maxDepth) {
		Individual x;
		x.g.shapeCore = randomTree(rng, maxDepth);
		x.g.redshiftCore = randomTree(rng, maxDepth);
		return x;
	}

	static std::string signature(const Genome& g) {
		return expr(*g.shapeCore) + "||" + expr(*g.redshiftCore);
	}

	static Individual breed(const Individual& p1, const Individual& p2,
		std::mt19937_64& rng, unsigned maxDepth)
	{
		Individual c = p1.clone();
		std::uniform_real_distribution<double> u(0.0, 1.0);

		if (u(rng) < 0.65) crossoverInto(c.g.shapeCore, *p2.g.shapeCore, rng);
		if (u(rng) < 0.65) crossoverInto(c.g.redshiftCore, *p2.g.redshiftCore, rng);

		if (u(rng) < 0.70) mutateStructure(c.g.shapeCore, rng, maxDepth);
		if (u(rng) < 0.70) mutateStructure(c.g.redshiftCore, rng, maxDepth);

		mutateConstants(*c.g.shapeCore, rng, 0.12);
		mutateConstants(*c.g.redshiftCore, rng, 0.12);

		c.fit = Fitness{};
		c.evaluated = false;
		c.signature.clear();
		return c;
	}

	struct RejectStats {
		std::array<std::uint64_t, 8> n{};
		void add(Reject r) { n[static_cast<unsigned>(r)]++; }
		std::string str() const {
			std::ostringstream s;
			s << "accepted=" << n[0]
				<< " create=" << n[1]
				<< " nonfinite=" << n[2]
				<< " throat=" << n[3]
				<< " exterior=" << n[4]
				<< " curvature=" << n[5]
				<< " redshift=" << n[6]
				<< " complexity=" << n[7];
			return s.str();
		}
	};

	static void sortPopulation(std::vector<Individual>& pop) {
		std::sort(pop.begin(), pop.end(),
			[](const Individual& a, const Individual& b) {
			if (a.fit.valid != b.fit.valid) return a.fit.valid > b.fit.valid;
			return a.fit.score < b.fit.score;
		});
	}

	static void writeCheckpoint(const std::vector<Individual>& pop, unsigned gen) {
		std::ofstream f("wormhole_checkpoint_gen_" + std::to_string(gen) + ".csv");
		if (!f) return;
		f << "rank,valid,score,neg_nec,signed_viq,bp0,max_abs_R,max_K,"
			<< "max_abs_phi,min_exterior,nodes,depth,shape_core,redshift_core\n";
		for (std::size_t i = 0; i < pop.size() && i < 50; ++i) {
			const auto& x = pop[i];
			auto quote = [](std::string s) {
				std::string q = "\"";
				for (char c : s) { if (c == '\"') q += "\"\""; else q += c; }
				q += "\""; return q;
			};
			f << i + 1 << "," << x.fit.valid << "," << std::setprecision(17) << x.fit.score << ","
				<< x.fit.negNec << "," << x.fit.signedViq << "," << x.fit.bp0 << ","
				<< x.fit.maxAbsR << "," << x.fit.maxK << "," << x.fit.maxAbsPhi << ","
				<< x.fit.minExterior << "," << x.fit.nodes << "," << x.fit.depth << ","
				<< quote(expr(*x.g.shapeCore)) << ","
				<< quote(expr(*x.g.redshiftCore)) << "\n";
		}
	}

	static void printBest(const Individual& x, unsigned gen) {
		std::ostringstream s;
		s << std::setprecision(10) << std::scientific;
		s << "GEN " << gen << " BEST score=" << x.fit.score
			<< " negNEC=" << x.fit.negNec
			<< " bp0=" << x.fit.bp0
			<< " max|R|=" << x.fit.maxAbsR
			<< " maxK=" << x.fit.maxK
			<< " nodes=" << x.fit.nodes;
		info(s.str());
		debug("BEST U(q)=" + expr(*x.g.shapeCore));
		debug("BEST V(q)=" + expr(*x.g.redshiftCore));
	}

	// ============================================================================
	// TINC finalist report
	// ============================================================================

	// WHY BATCHES: scalar TINC evaluation at 1024 radii took much longer than
	// evaluation of ordinary doubles. GetComputationResultExt performs the same
	// pointwise checks with fewer API calls and allows paceval to parallelize.
	// It does NOT change the scientific meaning of a TINC interval.
	// These intervals apply to individual input values, NOT all r between them.
	//
	// IMPORTANT: a batch can fail for individual points (e.g. subtraction code
	// 145). Therefore each result AND both interval endpoints are checked.
	// A scalar retry is allowed only as a separately validated computation;
	// never turn a failed result into a passing one by ignoring an error code.
	// This function returns true only if ALL requested sampled points meet the
	// checked exterior/curvature conditions and have a valid NEC classification.
	// Even true is a grid-based result, not a continuous-domain proof.
	// A compact result object is filled by tincReport and printed at the very end.
	// This avoids repeating or guessing statistics in the user-facing conclusion.
	// Counts describe POINTWISE interval checks, never certified radial ranges.
	struct TincSummary {
		unsigned requested = 0;
		std::size_t exteriorPassed = 0, curvaturePassed = 0;
		std::size_t necNegative = 0, necNonnegative = 0, necInconclusive = 0;
		std::size_t necEvaluated = 0, unresolved = 0;
		double widestNecInterval = 0.0;
		double evaluationSeconds = 0.0;
		bool passed = false;
	};

	// Optional output pointer preserves all existing callers and the fast 128-point
	// batch computation. It is populated only after the complete interval report.
	static bool tincReport(const Individual& x, unsigned npoints, unsigned configuredBatchSize, TincSummary* summary = nullptr) {
		using clock = std::chrono::steady_clock;
		const auto totalStart = clock::now();
		auto elapsed = [](clock::time_point t)->double {
			return std::chrono::duration<double>(clock::now()-t).count();
		};
		info("[TINC] Batch interval verification starting; points=" + std::to_string(npoints));
		info("[TINC] Stable symbolic forms: factorized exterior, direct Delta, common-denominator NEC.");
		const auto metricStart = clock::now();
		MetricExpressions m = buildMetric(x.g);
		info("[TINC] Metric expressions built in " + fmt(elapsed(metricStart)) + " s");
		const bool previousDiag = g_diagnose_paceval;
		struct RestoreDiag { bool old; ~RestoreDiag() { g_diagnose_paceval = old; } } restore{previousDiag};
		g_diagnose_paceval = true;
		const auto createStart = clock::now();
		PaceBundle p(m, true);
		info("[TINC] Handles created in " + fmt(elapsed(createStart)) + " s");
		if (!p.ok) { warn("[TINC] Handle creation failed"); return false; }
		g_diagnose_paceval = false;
		// Compile the equivalent graph ONLY when an actual TINC failure occurs.
		// In the successful common case this has zero creation/evaluation cost.
		std::unique_ptr<PaceBundle> alternative;
		std::size_t alternateAttempts=0, alternateRecovered=0, alternateRejected=0;
		const std::vector<double> radii = grid(npoints, 100.0);
		const std::array<unsigned, 4> fields = {{ B, NEC8, RICCI, KRET }};
		// Moderate chunk size: regular progress messages, bounded temporary
		// buffers, and enough work per API call to amortize overhead. Benchmark
		// 64/128/256/1024 on the target machine before selecting a final optimum.
		const std::size_t batchSize = std::max<std::size_t>(1, configuredBatchSize);
		std::size_t extOK=0, necNeg=0, necPos=0, necInc=0, curvOK=0;
		std::array<std::size_t,4> rawErrors{{0,0,0,0}}, recovered{{0,0,0,0}}, failures{{0,0,0,0}};
		std::size_t eligibleExterior=0, eligibleNec=0, eligibleCurvature=0;
		double widestNec=0.0;
		const auto evalStart = clock::now();
		info("[TINC BATCH] chunk_size=" + std::to_string(batchSize) +
			" functions=4 (b,NEC,Ricci,Kretschmann)");
		for (std::size_t start=0; start<radii.size(); start+=batchSize) {
			const std::size_t count=std::min(batchSize,radii.size()-start);
			info("[TINC BATCH BEGIN] points "+std::to_string(start+1)+"-"+
				std::to_string(start+count)+"/"+std::to_string(radii.size()));
			std::vector<double> inputs(radii.begin()+start,radii.begin()+start+count);
			struct BatchData {
				std::vector<double> result,lo,hi;
				std::vector<int> error;
				std::vector<unsigned char> good;
			};
			std::array<BatchData,4> data;
			for (unsigned j=0;j<4;++j) {
				auto& d=data[j];
				d.result.assign(count,std::numeric_limits<double>::quiet_NaN());
				d.lo.assign(count,std::numeric_limits<double>::quiet_NaN());
				d.hi.assign(count,std::numeric_limits<double>::quiet_NaN());
				d.error.assign(count,0); d.good.assign(count,0);
				unsigned fi=fields[j];
				const auto fieldStart=clock::now();
				// TINC batch: request BOTH lower and upper numerical bounds
				// at every sampled r. Codes are inspected per point even if
				// aggregate API status is set. Batch size is tunable, not proven
				// optimal; fewer calls can trade off latency and progress detail.
				const bool batchHasError=paceval_dGetComputationResultExt(
					p.h[fi],inputs.data(),static_cast<unsigned long>(count),
					d.result.data(),d.lo.data(),d.hi.data(),d.error.data());
				info(std::string("[TINC BATCH FIELD] ")+functionName(fi)+
					" seconds="+fmt(elapsed(fieldStart))+
					" api_error="+(batchHasError?"1":"0"));
				for (std::size_t i=0;i<count;++i) {
					// Require an error-free computation AND an enclosing finite interval.
					// A finite point estimate alone is insufficient for TINC validation.
					bool valid=(d.error[i]==0 && std::isfinite(d.result[i]) &&
						std::isfinite(d.lo[i]) && std::isfinite(d.hi[i]) &&
						d.lo[i]<=d.result[i] && d.result[i]<=d.hi[i]);
					if (d.error[i]!=0) ++rawErrors[j];
					if (!valid) {
						warn(std::string("[TINC RAW ERROR] ")+functionName(fi)+
							" index="+std::to_string(start+i)+" r="+fmt(inputs[i])+
							" code="+std::to_string(d.error[i]));
						// Some batch failures may be transient or specific to parallel
						// evaluation. Repeat this radius using the scalar API, and only
						// recover if there is NO paceval error AND both bounds enclose
						// the finite point estimate. Do not overwrite a failed point
						// with a normal floating-point result without interval bounds.
						double value=0,lo=0,hi=0;
						if (p.eval(fi,inputs[i],value,&lo,&hi) &&
							std::isfinite(lo) && std::isfinite(hi) &&
							lo<=value && value<=hi) {
							d.result[i]=value;d.lo[i]=lo;d.hi[i]=hi;
							valid=true;++recovered[j];
							info(std::string("[TINC SCALAR RECOVERED] ")+functionName(fi)+
								" index="+std::to_string(start+i));
						}
						if (!valid) {
							// Retry with a different, mathematically equivalent operation
							// graph. This often changes which additions TINC encounters.
							// Crucial: require finite enclosing TINC bounds; normal
							// floating-point results alone NEVER recover a failed point.
							++alternateAttempts;
							if (!alternative) {
								info("[TINC ALTERNATE] Creating independent, algebraically equivalent TINC handles");
								alternative = std::make_unique<PaceBundle>(buildMetric(x.g, true), true);
							}
							double av=0,al=0,ah=0;
							if (alternative->ok && alternative->eval(fi,inputs[i],av,&al,&ah) &&
								std::isfinite(av) && std::isfinite(al) && std::isfinite(ah) &&
								al<=av && av<=ah) {
								// Compare independent numerical point values when one is
								// available. The comparison is a diagnostic guard against
								// accidental algebraic differences, not a proof of identity.
								const double base=d.result[i];
								const double tolerance=1e-10*std::max({1.0,std::abs(base),std::abs(av)});
								if (!std::isfinite(base) || std::abs(base-av)<=tolerance) {
									d.result[i]=av; d.lo[i]=al; d.hi[i]=ah;
									valid=true; ++alternateRecovered;
									info(std::string("[TINC ALTERNATE RECOVERED] ")+functionName(fi)+
										" index="+std::to_string(start+i)+" r="+fmt(inputs[i]));
								}
							}
							if (!valid) {
								++alternateRejected;
								warn(std::string("[TINC ALTERNATE UNRESOLVED] ")+functionName(fi)+
									" r="+fmt(inputs[i])+"; sampled point remains unverified");
							}
						}
					}
					d.good[i]=valid?1:0;
					if (!valid) ++failures[j];
				}
			}
			// Count each physical condition independently. Earlier statistics
			// could mislabel a curvature failure after a NEC error as success,
			// because the code skipped later checks for that radial point.
			for(std::size_t i=0;i<count;++i) {
				const double r=inputs[i];
				if(data[0].good[i]) {
					++eligibleExterior;
					if(1.0-data[0].hi[i]/r>0.0) ++extOK;
				}
				if(data[1].good[i]) {
					++eligibleNec;
					widestNec=std::max(widestNec,data[1].hi[i]-data[1].lo[i]);
					if(data[1].hi[i]<0) ++necNeg;
					else if(data[1].lo[i]>=0) ++necPos;
					else ++necInc;
				}
				if(data[2].good[i] && data[3].good[i]) {
					++eligibleCurvature;
					if(std::max(std::abs(data[2].lo[i]),std::abs(data[2].hi[i]))<=1e3 &&
						data[3].lo[i]>=-1e-10 && data[3].hi[i]<=1e6) ++curvOK;
				}
			}
			info("[TINC BATCH PROGRESS] "+std::to_string(start+count)+"/"+
				std::to_string(radii.size())+" ("+
				fmt(100.0*static_cast<double>(start+count)/radii.size())+
				"%) elapsed="+fmt(elapsed(evalStart))+" s");
		}
		const double evaluationSeconds = elapsed(evalStart);
		info("[TINC] Batch evaluations finished in "+fmt(evaluationSeconds)+" s");
		info("[TINC ALTERNATE SUMMARY] attempted="+std::to_string(alternateAttempts)+
			" recovered="+std::to_string(alternateRecovered)+
			" unresolved="+std::to_string(alternateRejected));
		info("TINC sampled points          : "+std::to_string(npoints));
		info("TINC exterior verified       : "+std::to_string(extOK)+" / "+std::to_string(eligibleExterior));
		info("TINC curvature verified      : "+std::to_string(curvOK)+" / "+std::to_string(eligibleCurvature));
		info("TINC NEC definitely negative : "+std::to_string(necNeg));
		info("TINC NEC inconclusive        : "+std::to_string(necInc));
		info("TINC NEC nonnegative         : "+std::to_string(necPos));
		info("TINC NEC classified          : "+std::to_string(eligibleNec)+" / "+std::to_string(npoints));
		info("TINC widest NEC interval     : "+fmt(widestNec));
		for(unsigned j=0;j<4;++j) {
			info(std::string("[TINC FIELD SUMMARY] ")+functionName(fields[j])+
				" raw_errors="+std::to_string(rawErrors[j])+
				" scalar_recovered="+std::to_string(recovered[j])+
				" unresolved="+std::to_string(failures[j]));
		}
		// Only complete coverage of all requested samples counts as a passed
		// pointwise TINC check. No extrapolation to untested radii is implied.
		const bool fullyVerified=(eligibleExterior==npoints && extOK==npoints &&
			eligibleNec==npoints && eligibleCurvature==npoints && curvOK==npoints);
		if (summary) {
			summary->requested = npoints;
			summary->exteriorPassed = extOK;
			summary->curvaturePassed = curvOK;
			summary->necNegative = necNeg;
			summary->necNonnegative = necPos;
			summary->necInconclusive = necInc;
			summary->necEvaluated = eligibleNec;
			for (const auto count : failures) summary->unresolved += count;
			summary->widestNecInterval = widestNec;
			summary->evaluationSeconds = evaluationSeconds;
			summary->passed = fullyVerified;
		}
		if(!fullyVerified) warn("[TINC] INCOMPLETE: some points failed numerical or geometric verification.");
		else info("[TINC] All sampled points passed the implemented interval geometry checks.");

		info("[TINC] Total time (excluding handle destruction)=" + fmt(elapsed(totalStart)) + " s");
		warn("TINC report covers discrete radial samples only, not continuous radial intervals.");
		return fullyVerified;
	}


	// ============================================================================
	// STAGE 2: ADAPTIVE POINTWISE TINC SAMPLING (NO EXTERNAL LIBRARY)
	// ============================================================================
	// Scientific scope: paceval TINC returns numerical error bounds at a
	// SPECIFIED input value r. It does NOT provide, through the APIs used here,
	// a mathematical enclosure of f([r_left,r_right]). Consequently even a
	// successful adaptive run is NOT a continuous-domain interval certificate.
	// This stage nevertheless improves the chance of detecting narrow adverse
	// regions that a fixed radial mesh might miss. Never label it "proof".
	//
	// We retain paceval handles for the whole stage, use the batched Ext API
	// to amortize overhead and let the SDK schedule independent input sets,
	// and read both TINC endpoints for all four geometric observables.
	// A failed or inconclusive point is never silently converted into success.
	struct AdaptiveTincSummary {
		std::size_t tested = 0, failures = 0, exteriorPassed = 0;
		std::size_t curvaturePassed = 0, necNegative = 0, necNonnegative = 0;
		std::size_t necInconclusive = 0, refined = 0, unbisectable = 0;
		std::size_t waves = 0, batchCalls = 0, scalarEquivalentCalls = 0;
		std::string stopReason = "not started";
		double seconds = 0.0;
		bool passed = false;
	};
	struct AdaptivePoint {
		double r = 0;
		std::array<double,4> value{},lo{},hi{};
		bool valid = false, exterior = false, curvature = false;
		int necSign = 0; // -1 negative, +1 nonnegative, 0 inconclusive
	};
	static AdaptiveTincSummary adaptiveTincReport(const Individual& champion,
		unsigned additionalBudget, unsigned batchSize, unsigned waveSize) {
		using clock=std::chrono::steady_clock;
		const auto begin=clock::now();
		AdaptiveTincSummary out;
		if(additionalBudget==0) { info("[ADAPTIVE TINC] Disabled (--adaptive-points 0)"); return out; }
		info("[ADAPTIVE TINC] Starting paceval-only adaptive POINTWISE validation; budget="+
			std::to_string(additionalBudget)+" initial_points=17 wave_size="+
			std::to_string(waveSize)+" TINC_chunk="+std::to_string(batchSize));
		MetricExpressions metric=buildMetric(champion.g);
		PaceBundle bundle(metric,true);
		if(!bundle.ok) { warn("[ADAPTIVE TINC] Failed to create TINC handles"); ++out.failures; return out; }
		const std::array<unsigned,4> fields={{ B,NEC8,RICCI,KRET }};
		std::vector<AdaptivePoint> points;
		const double eps=1e-7, maximum=100.0;
		// Parameter t gives more attention near the throat than uniform r.
		const auto radius=[&](double t){return 1.0+eps+(maximum-1.0-eps)*t*t*t;};
		const auto evaluate=[&](const std::vector<double>& rs)->std::vector<AdaptivePoint> {
			std::vector<AdaptivePoint> result(rs.size());
			for(std::size_t k=0;k<rs.size();++k) result[k].r=rs[k];
			for(std::size_t start=0;start<rs.size();start+=batchSize) {
				const std::size_t n=std::min<std::size_t>(batchSize,rs.size()-start);
				std::vector<double> inputs(rs.begin()+start,rs.begin()+start+n);
				std::array<std::vector<double>,4> vals, lows, highs;
				std::array<std::vector<int>,4> errors;
				for(unsigned j=0;j<4;++j) {
					vals[j].resize(n);lows[j].resize(n);highs[j].resize(n);errors[j].assign(n,0);
					// Ext batches MANY INPUT VALUES for ONE precompiled formula. TINC
					// lower/upper outputs are mandatory, unlike the coarse screening.
					++out.batchCalls;
					const bool anyError=paceval_dGetComputationResultExt(bundle.h[fields[j]],
						inputs.data(),static_cast<unsigned long>(n),vals[j].data(),
						lows[j].data(),highs[j].data(),errors[j].data());
					// Keep the aggregate error flag too: anyError may be set even when
					// an SDK version leaves individual error slots at zero.
					if(anyError) {
						bool identified=false;
						for(int code:errors[j]) if(code!=0) identified=true;
						if(!identified) {
							warn("[ADAPTIVE TINC ERROR] Aggregate API error with no point code, field="+
								std::string(functionName(fields[j])));
							for(auto& code:errors[j]) code=-1; // fail closed
						}
					}
				}
				for(std::size_t k=0;k<n;++k) {
					auto& pt=result[start+k];pt.valid=true;
					for(unsigned j=0;j<4;++j) {
						pt.value[j]=vals[j][k];pt.lo[j]=lows[j][k];pt.hi[j]=highs[j][k];
						if(errors[j][k] || !std::isfinite(vals[j][k]) ||
							!std::isfinite(lows[j][k]) || !std::isfinite(highs[j][k]) ||
							lows[j][k]>vals[j][k] || vals[j][k]>highs[j][k]) {
							pt.valid=false;
							warn("[ADAPTIVE TINC ERROR] r="+fmt(pt.r)+" field="+
								functionName(fields[j])+" code="+std::to_string(errors[j][k]));
						}
					}
					if(pt.valid) {
						pt.exterior=(1.0-pt.hi[0]/pt.r>0.0);
						pt.curvature=(std::max(std::abs(pt.lo[2]),std::abs(pt.hi[2]))<=1e3 &&
								pt.lo[3]>=-1e-10 && pt.hi[3]<=1e6);
						pt.necSign=pt.hi[1]<0 ? -1 : (pt.lo[1]>=0 ? 1 : 0);
					}
				}
			}
			return result;
		};
		// Start with a small deterministic mesh; refinement decisions depend on
		// observed values, not on an assumed smoothness bound.
		std::vector<double> initial;
		for(unsigned k=0;k<=16;++k) initial.push_back(radius(k/16.0));
		points=evaluate(initial);
		// Adaptive priority: focus on NEC sign changes / ambiguous bounds,
		// rapid relative changes and larger unexamined physical gaps. This is
		// a HEURISTIC for selecting sampling locations, not a certified bound.
		//
		// PERFORMANCE: the previous algorithm evaluated one midpoint at a time.
		// Four paceval_dGetComputationResultExt calls per midpoint were then
		// effectively four 1-element batches. For 256 midpoints that meant
		// 1024 API calls plus repeated vector allocation and scheduling overhead.
		// We now select up to adaptiveWaveSize DISJOINT existing intervals at once,
		// evaluate all their midpoints with the SAME paceval TINC batch API, and
		// re-rank the intervals after the batch returns. Each midpoint is selected
		// from the current valid observations; no extrapolated values are accepted.
		// Note: grouping changes the exact sampling order versus fully sequential
		// greedy refinement. --adaptive-wave-size 1 reproduces the original
		// sequential midpoint-selection approach for A/B benchmarking.
		while(out.refined<additionalBudget) {
			struct Priority { double score; std::size_t index; double midpoint; };
			std::vector<Priority> ranked;
			for(std::size_t k=0;k+1<points.size();++k) {
				const auto& a=points[k]; const auto& b=points[k+1];
				if(!(b.r>a.r)) continue;
				const double candidate=a.r+0.5*(b.r-a.r);
				if(!(candidate>a.r && candidate<b.r)) continue;
				double score=std::log(b.r)-std::log(a.r);
				if(!a.valid || !b.valid) score+=100.0;
				else {
					if(a.necSign!=b.necSign || a.necSign==0 || b.necSign==0) score+=10.0;
					const double scale=1e-8+std::max(std::abs(a.value[1]),std::abs(b.value[1]));
					score+=std::min(5.0,std::abs(a.value[1]-b.value[1])/scale);
					if(!a.exterior || !b.exterior || !a.curvature || !b.curvature) score+=20.0;
				}
				ranked.push_back({score,k,candidate});
			}
			if(ranked.empty()) {
				out.stopReason="no representable midpoint in any remaining interval";
				break;
			}
			std::sort(ranked.begin(),ranked.end(),[](const Priority& a,const Priority& b){
				if(a.score!=b.score) return a.score>b.score;
				return a.index<b.index; // deterministic equal-priority tie-break
			});
			const std::size_t take=std::min<std::size_t>(
				std::min<std::size_t>(waveSize,additionalBudget-out.refined),ranked.size());
			std::vector<Priority> selected(ranked.begin(),ranked.begin()+take);
			// The selection order is by scientific priority. Sorting is needed
			// only for stable insertion into the ordered-radius point vector.
			std::sort(selected.begin(),selected.end(),[](const Priority& a,const Priority& b){
				return a.index<b.index;
			});
			std::vector<double> newRadii;newRadii.reserve(take);
			for(const auto& x:selected) newRadii.push_back(x.midpoint);
			std::vector<AdaptivePoint> examined=evaluate(newRadii);
			// Insert from right to left, preserving the original interval indexes.
			for(std::size_t k=take;k>0;--k)
				points.insert(points.begin()+static_cast<std::ptrdiff_t>(selected[k-1].index+1),
					std::move(examined[k-1]));
			out.refined+=take;
			++out.waves;
			if(out.refined%32==0 || out.refined==additionalBudget)
				info("[ADAPTIVE TINC PROGRESS] new="+std::to_string(out.refined)+"/"+
					std::to_string(additionalBudget)+" tested="+std::to_string(points.size())+
					" waves="+std::to_string(out.waves)+
					" API_calls="+std::to_string(out.batchCalls));
		}
		if(out.refined==additionalBudget)
			out.stopReason="requested additional-point budget exhausted";
		if(out.stopReason=="not started")
			out.stopReason="refinement terminated without reaching budget";
		for(std::size_t k=0;k+1<points.size();++k) {
			const double mid=points[k].r+0.5*(points[k+1].r-points[k].r);
			if(!(mid>points[k].r && mid<points[k+1].r)) ++out.unbisectable;
		}
		out.tested=points.size();
		for(const auto& pt:points) {
			if(!pt.valid) {++out.failures;continue;}
			if(pt.exterior) ++out.exteriorPassed;
			if(pt.curvature) ++out.curvaturePassed;
			if(pt.necSign<0) ++out.necNegative;
			else if(pt.necSign>0) ++out.necNonnegative;
			else ++out.necInconclusive;
		}
		out.passed=(out.tested>0 && out.failures==0 &&
			out.exteriorPassed==out.tested && out.curvaturePassed==out.tested);
		out.seconds=std::chrono::duration<double>(clock::now()-begin).count();
		info("[ADAPTIVE TINC SUMMARY] points="+std::to_string(out.tested)+
			" refined="+std::to_string(out.refined)+
			" errors="+std::to_string(out.failures)+
			" exterior="+std::to_string(out.exteriorPassed)+
			" curvature="+std::to_string(out.curvaturePassed)+
			" NEC_negative="+std::to_string(out.necNegative)+
			" NEC_nonnegative="+std::to_string(out.necNonnegative)+
			" NEC_inconclusive="+std::to_string(out.necInconclusive)+
			" seconds="+fmt(out.seconds)+
			" waves="+std::to_string(out.waves)+
			" TINC_batch_API_calls="+std::to_string(out.batchCalls));
		info("[ADAPTIVE TINC STOP] reason="+out.stopReason+
			" unbisectable_intervals="+std::to_string(out.unbisectable));
		warn("[ADAPTIVE TINC] POINTWISE only. No theorem for untested r; continuous validity NOT certified.");
		return out;
	}


    // ============================================================================
    // PHYSICAL DIAGNOSTICS, NOT ADDITIONAL HARD ACCEPTANCE CONSTRAINTS
    // ============================================================================
    // Proper radial length on a static t=const hypersurface:
    //     L(r) = integral[1,r] 1/sqrt(1-b(s)/s) ds.
    // The integrand diverges integrably at the throat. Therefore we substitute
    // r=1+t^2, dr=2t dt; the new integrand approaches 2/sqrt(1-b'(1))
    // as t->0. This quadrature is a diagnostic estimate, not an interval proof.
    //
    // Static orthonormal tidal curvature is described by the components
    //     R_trtr = (1-b/r)(Phi''+Phi'^2)-Phi'(r b'-b)/(2r^2)
    //     R_ttheta_ttheta = (1-b/r)Phi'/r.
    // They are geometric, not a traveller-frame tidal acceleration: the latter
    // additionally depends on a trajectory, Lorentz transformation and physical scale r0.
    //
    // The legacy negative NEC integral is a MODEL-SPECIFIC objective and not
    // automatically the total exotic-matter volume-integral quantifier.
    struct PhysicalDiagnostics {
        bool complete = false;
        double properLength = 0.0;
        double maxRadialTidal = 0.0;
        double maxAngularTidal = 0.0;
        double maxAbsPhiPrime = 0.0;
        double minExterior = std::numeric_limits<double>::infinity();
        double negativeNecRadial = 0.0;
        unsigned points = 0;
    };

    static PhysicalDiagnostics physicalDiagnostics(const Genome& g, unsigned n=1200) {
        PhysicalDiagnostics d;
        // Geometry expressions still come from the same symbolic generator;
        // paceval compiles once, and all radial evaluations reuse handles.
        const MetricExpressions m=buildMetric(g);
        const std::array<std::string,5> expressions={{m.b,m.bp,m.phip,m.phipp,m.nec8}};
        std::array<PACEVAL_HANDLE,5> hs{};
        hs.fill(NULL);
        auto release=[&]() {for(auto& h:hs) if(h) {paceval_DeleteComputation(h);h=NULL;}};
        for(std::size_t j=0;j<hs.size();++j) {
            // Double mode is deliberate: physical diagnostics are exploratory
            // quadratures and maxima, NOT incorrectly labelled TINC enclosures.
            hs[j]=paceval_CreateComputation(expressions[j].c_str(),1,"r",false,NULL);
            if(!hs[j] || paceval_GetIsError(hs[j])) {release();return d;}
        }
        n=std::max(32u,n);
        std::vector<double> radii(n);
        const double tMax=std::sqrt(99.0);
        // t^2 grid exactly starts at r=1. The integral's t=0 value is
        // supplied by its analytic limit, avoiding division by zero.
        for(unsigned i=0;i<n;++i) {
            const double t=tMax*static_cast<double>(i)/static_cast<double>(n-1);
            radii[i]=1.0+t*t;
        }
        std::array<std::vector<double>,5> vv;
        for(std::size_t j=0;j<5;++j) {
            vv[j].resize(n);
            std::vector<int> errors(n,0);
            std::vector<double> input=radii;
            // Throughput: a single Ext call evaluates a fixed expression
            // over the entire radial grid, with no repeated formula parsing.
            const bool bad=paceval_dGetComputationResultExt(hs[j],input.data(),
                static_cast<unsigned long>(n),vv[j].data(),NULL,NULL,errors.data());
            if(bad) {release();return d;}
            for(unsigned i=0;i<n;++i)
                if(errors[i] || !std::isfinite(vv[j][i])) {release();return d;}
        }
        release();
        const double bp0=vv[1][0];
        if(!(1.0-bp0>0.0)) return d;
        const double limit=2.0/std::sqrt(1.0-bp0);
        double prev=limit;
        double prevNEC=0.0;
        for(unsigned i=0;i<n;++i) {
            const double r=radii[i];
            const double t=tMax*static_cast<double>(i)/static_cast<double>(n-1);
            const double b=vv[0][i],bp=vv[1][i],phip=vv[2][i],phipp=vv[3][i];
            const double ext=1.0-b/r;
            const double delta=r*bp-b;
            const double RA=ext*(phipp+phip*phip)-phip*delta/(2*r*r);
            const double RB=ext*phip/r;
            d.maxRadialTidal=std::max(d.maxRadialTidal,std::abs(RA));
            d.maxAngularTidal=std::max(d.maxAngularTidal,std::abs(RB));
            d.maxAbsPhiPrime=std::max(d.maxAbsPhiPrime,std::abs(phip));
            if(i>0) d.minExterior=std::min(d.minExterior,ext);
            const double f=(i==0)?limit:((ext>0.0)?(2.0*t/std::sqrt(ext)):
                 std::numeric_limits<double>::quiet_NaN());
            if(!std::isfinite(f)) return d;
            const double ne=0.5*r*r*std::max(0.0,-vv[4][i]);
            if(i>0) {
                d.properLength+=(prev+f)*0.5*(tMax/static_cast<double>(n-1));
                d.negativeNecRadial+=(prevNEC+ne)*0.5*(r-radii[i-1]);
            }
            prev=f;prevNEC=ne;
        }
        d.points=n;d.complete=true;
        return d;
    }


    // ============================================================================
    // TWO-OBJECTIVE PARETO SEARCH (minimize NEC violation AND static tidal curvature)
    // ============================================================================
    // No weighted sum is used for Pareto dominance: a dominates b iff neither
    // objective is worse and at least one is strictly better. A point with less
    // NEC violation but more tidal curvature is NOT dominated merely because
    // another point has a smaller legacy scalar fitness score.
    //
    // Each candidate receives double-precision diagnostics on the SAME radial
    // sample count during the search. The archive is then reevaluated at the
    // final fine-grid resolution. These sampled maxima and integrals are not
    // mathematically certified global extrema, integrals or traveller forces.
    // TINC remains the independent pointwise verification of the legacy winner.
    struct ParetoArchive {
        std::vector<Individual> candidates;
        unsigned evaluated=0;
        unsigned rejectedDiagnostics=0;
        void observe(const Individual& x) {
            if(!x.fit.valid || !std::isfinite(x.fit.tidalObjective)) {
                ++rejectedDiagnostics; return;
            }
            ++evaluated;
            candidates.push_back(x.clone());
        }
    };

    static bool dominates(const Fitness& a,const Fitness& b) {
        return a.valid && b.valid &&
          a.negNec<=b.negNec && a.tidalObjective<=b.tidalObjective &&
          (a.negNec<b.negNec || a.tidalObjective<b.tidalObjective);
    }

    // NSGA-II style fast nondominated sorting. The second objective is sampled
    // static tidal curvature; sorting NEVER uses the legacy scalar score.
    static std::vector<std::vector<unsigned>> paretoFronts(const std::vector<Individual>& pop) {
        const unsigned n=static_cast<unsigned>(pop.size());
        std::vector<std::vector<unsigned>> dominated(n),fronts;
        std::vector<unsigned> count(n,0),first;
        for(unsigned i=0;i<n;++i) {
            if(!pop[i].fit.valid || !std::isfinite(pop[i].fit.tidalObjective)) continue;
            for(unsigned j=0;j<n;++j) {
                if(i==j || !pop[j].fit.valid || !std::isfinite(pop[j].fit.tidalObjective)) continue;
                if(dominates(pop[i].fit,pop[j].fit)) dominated[i].push_back(j);
                else if(dominates(pop[j].fit,pop[i].fit)) ++count[i];
            }
            if(!count[i]) first.push_back(i);
        }
        if(first.empty()) return fronts;
        fronts.push_back(first);
        for(std::size_t k=0;k<fronts.size();++k) {
            std::vector<unsigned> next;
            for(unsigned i:fronts[k]) for(unsigned j:dominated[i])
                if(count[j] && --count[j]==0) next.push_back(j);
            if(!next.empty()) fronts.push_back(next);
        }
        return fronts;
    }

    // Crowding distance promotes diversity, including BOTH boundary solutions.
    static std::vector<double> paretoCrowding(const std::vector<Individual>& pop,
                                             const std::vector<unsigned>& front) {
        std::vector<double> d(pop.size(),0.0);
        if(front.size()<=2) {
            for(unsigned i:front) d[i]=std::numeric_limits<double>::infinity();
            return d;
        }
        for(unsigned objective=0;objective<2;++objective) {
            std::vector<unsigned> order=front;
            auto val=[&](unsigned i)->double {return objective==0 ? pop[i].fit.negNec:pop[i].fit.tidalObjective;};
            std::sort(order.begin(),order.end(),[&](unsigned a,unsigned b){
                if(val(a)!=val(b)) return val(a)<val(b);
                return a<b;
            });
            d[order.front()]=d[order.back()]=std::numeric_limits<double>::infinity();
            const double range=val(order.back())-val(order.front());
            if(!(range>0.0)) continue;
            for(std::size_t j=1;j+1<order.size();++j)
                if(std::isfinite(d[order[j]]))
                    d[order[j]]+=(val(order[j+1])-val(order[j-1]))/range;
        }
        return d;
    }

    static void paretoSortPopulation(std::vector<Individual>& pop) {
        const auto fronts=paretoFronts(pop);
        std::vector<Individual> ordered;
        ordered.reserve(pop.size());
        for(const auto& f:fronts) {
            auto crowd=paretoCrowding(pop,f);
            auto indices=f;
            std::stable_sort(indices.begin(),indices.end(),[&](unsigned a,unsigned b){
                if(crowd[a]!=crowd[b]) return crowd[a]>crowd[b];
                if(pop[a].fit.negNec!=pop[b].fit.negNec)
                    return pop[a].fit.negNec<pop[b].fit.negNec;
                return a<b;
            });
            for(unsigned idx:indices) ordered.push_back(pop[idx].clone());
        }
        for(const auto& x:pop) if(!x.fit.valid || !std::isfinite(x.fit.tidalObjective))
            ordered.push_back(x.clone());
        pop=std::move(ordered);
    }

    static void paretoFinalReport(const ParetoArchive& archive,
                                  unsigned finePoints,
                                  const Individual& scalarWinner,
                                  unsigned finalLimit) {
        info("============================================================");
        info("PARETO MULTIOBJECTIVE RESULT FOR THE USER");
        info("============================================================");
        info("[PARETO] Objective 1: minimize sampled negative radial NEC integral");
        info("[PARETO] Objective 2: minimize maximum sampled static tidal Riemann component");
        info("[PARETO] No arbitrary weighted sum determines nondominance.");
        info("[PARETO] Fine-grid cap="+std::to_string(finalLimit)+
             " (0=full scientific archive comparison; nonzero=fast preview)");
        info("[PARETO] Search evaluation count="+std::to_string(archive.evaluated)+
             " missing_tidal_diagnostics="+std::to_string(archive.rejectedDiagnostics));
        std::vector<Individual> fine;
        auto radii=grid(finePoints,100.0);
        // Optional PREVIEW acceleration: the expensive final stage would otherwise
        // compile and evaluate several independent paceval expressions for EVERY
        // archived candidate on the fine radial grid. Each expression ALREADY uses
        // the paceval Ext batch API for all its radii. Threading the calls without a
        // verified thread-safety contract for paceval handles is deliberately avoided.
        //
        // A nonzero limit selects candidates from ALL coarse nondominated fronts
        // in their Pareto rank order. Within a front, crowding distance preserves
        // objective-space diversity, while both extrema are selected first.
        // This is an APPROXIMATE fine-grid Pareto preview: a coarse-dominated
        // candidate may become nondominated after fine-grid reevaluation.
        // Use --pareto-final-limit 0 for the complete, unbiased archive comparison.
        std::vector<unsigned> selected;
        const auto& coarse=archive.candidates;
        if (finalLimit==0 || finalLimit>=coarse.size()) {
            for(unsigned i=0;i<coarse.size();++i) selected.push_back(i);
        } else {
            const auto coarseFronts=paretoFronts(coarse);
            for(const auto& front:coarseFronts) {
                if(selected.size()>=finalLimit) break;
                auto crowd=paretoCrowding(coarse,front);
                std::vector<unsigned> order=front;
                std::stable_sort(order.begin(),order.end(),[&](unsigned a,unsigned b){
                    if(crowd[a]!=crowd[b]) return crowd[a]>crowd[b];
                    return coarse[a].fit.negNec<coarse[b].fit.negNec;
                });
                for(unsigned i:order) {
                    if(selected.size()>=finalLimit) break;
                    selected.push_back(i);
                }
            }
        }
        info("[PARETO FINE] archived="+std::to_string(coarse.size())+
             " selected="+std::to_string(selected.size())+
             " grid="+std::to_string(finePoints)+
             " mode="+std::string(selected.size()==coarse.size()?"FULL":"PREVIEW_COARSE_PREFILTER"));
        const auto reportStart=std::chrono::steady_clock::now();
        unsigned processed=0;
        unsigned accepted=0;
        unsigned invalidGeometry=0;
        unsigned invalidPhysics=0;
        // Report attempts, not just accepted candidates: a rejected candidate must
        // never suppress the progress message or make completion look stalled.
        for(unsigned idx:selected) {
            const auto& x=coarse[idx];
            Individual y=x.clone();
            y.fit=evaluateGenome(y.g,radii);
            if(!y.fit.valid) {
                ++invalidGeometry;
            } else {
                const auto phys=physicalDiagnostics(y.g,finePoints);
                if(!phys.complete) {
                    ++invalidPhysics;
                } else {
                    y.fit.tidalObjective=std::max(phys.maxRadialTidal,phys.maxAngularTidal);
                    fine.push_back(std::move(y));
                    ++accepted;
                }
            }
            ++processed;
            if(processed==1 || processed%4==0 || processed==selected.size()) {
                const double seconds=std::chrono::duration<double>(
                    std::chrono::steady_clock::now()-reportStart).count();
                const double per=seconds/static_cast<double>(processed);
                const double remaining=per*static_cast<double>(selected.size()-processed);
                info("[PARETO FINE PROGRESS] processed="+std::to_string(processed)+
                     "/"+std::to_string(selected.size())+
                     " accepted="+std::to_string(accepted)+
                     " invalid_geometry="+std::to_string(invalidGeometry)+
                     " invalid_physics="+std::to_string(invalidPhysics)+
                     " elapsed_s="+fmt(seconds)+" estimated_remaining_s="+fmt(remaining));
            }
        }
        info("[PARETO FINE] elapsed_s="+fmt(std::chrono::duration<double>(
             std::chrono::steady_clock::now()-reportStart).count()));
        const auto fronts=paretoFronts(fine);
        std::ofstream csv("wormhole_pareto_front.csv");
        if(csv) csv<<"rank,negative_nec,static_tidal_max,legacy_score,bp_throat,max_k,"
                    "nodes,depth,shape_U,redshift_V\n";
        if(fronts.empty() || fronts.front().empty()) {
            warn("[PARETO] No valid fine-grid Pareto candidates; no front asserted.");
            return;
        }
        auto ids=fronts.front();
        std::sort(ids.begin(),ids.end(),[&](unsigned a,unsigned b){
            return fine[a].fit.negNec<fine[b].fit.negNec;
        });
        auto quote=[](const std::string& s){
            std::string out="\"";
            for(char c:s) {if(c=='\"') out+="\"\"";else out+=c;}
            return out+"\"";
        };
        for(std::size_t j=0;j<ids.size();++j) {
            const auto& x=fine[ids[j]];
            if(csv) csv<<j+1<<","<<std::setprecision(17)<<x.fit.negNec<<","<<x.fit.tidalObjective
               <<","<<x.fit.score<<","<<x.fit.bp0<<","<<x.fit.maxK<<","<<x.fit.nodes
               <<","<<x.fit.depth<<","<<quote(expr(*x.g.shapeCore))<<","<<quote(expr(*x.g.redshiftCore))<<"\n";
            info("[PARETO FRONT] rank="+std::to_string(j+1)+
                 " NEC="+fmt(x.fit.negNec)+" tidal="+fmt(x.fit.tidalObjective)+
                 " legacy_score="+fmt(x.fit.score)+" nodes="+std::to_string(x.fit.nodes));
        }
        const auto& lowNEC=fine[ids.front()];
        const auto lowTidalId=*std::min_element(ids.begin(),ids.end(),[&](unsigned a,unsigned b){
            return fine[a].fit.tidalObjective<fine[b].fit.tidalObjective;
        });
        const auto& lowTidal=fine[lowTidalId];
        info("[PARETO SUMMARY] fine_grid_survivors="+std::to_string(fine.size())+
             " nondominated="+std::to_string(ids.size()));
        info("[PARETO SUMMARY] Minimum NEC option: NEC="+fmt(lowNEC.fit.negNec)+
             " tidal="+fmt(lowNEC.fit.tidalObjective));
        info("[PARETO SUMMARY] Minimum tidal option: NEC="+fmt(lowTidal.fit.negNec)+
             " tidal="+fmt(lowTidal.fit.tidalObjective));
        info("[PARETO SUMMARY] Legacy winner NEC="+fmt(scalarWinner.fit.negNec)+
             " (legacy scoring remains separately reported)");
        info("[PARETO SUMMARY] CSV: wormhole_pareto_front.csv");
        if(selected.size()!=coarse.size())
            warn("[PARETO CAUTION] PREVIEW front: only a coarse-selected subset was fine-checked; "
                 "the complete fine-grid Pareto front can differ. Run --pareto-final-limit 0 for full comparison.");
        info("[PARETO CAUTION] Pareto front is ONLY relative to sampled candidates.");
        info("[PARETO CAUTION] Search maxima and integrals use doubles, not TINC-certified quadrature.");
        info("[PARETO CAUTION] TINC verification of legacy winner does NOT validate all Pareto points.");
        info("[PARETO CAUTION] No continuum proof, traveller safety, stability or matter model is established.");
    }

    // ============================================================================
    // SCIENTIFIC REFERENCE COMPARISON (same normalization and radial domain)
    // ============================================================================
    // The labels distinguish a published metric from original comparison
    // families. Morris-Thorne is a GENERAL framework, not one unique shape
    // function; Visser-Kar-Dadhich (2003) is a result concerning exotic-matter
    // quantification, not the constant-U examples used here.
    //
    // Ellis/Bronnikov (r0=1): b=1/r, Phi=0, represented by U=V=0.
    // Redshift deformation: same b and Phi=-0.75/r (illustrative model).
    // Near-marginal flare-out: U=1.9 or 1.99, V=0; these are purpose-built
    // parameter examples, NOT asserted to be published solutions.
    // Since b'(1)=U(0)-1, U approaching 2 from below approaches the strict
    // flare-out boundary. Small NEC integral alone does not imply better
    // overall physical quality or realizability.
    //
    // All rows use identical fine-grid points and the identical diagnostic
    // quadrature. Results are double-precision estimates, not certified
    // integrals or proofs of inequalities on a continuous interval.
    // No TINC reference certification is claimed by this table.
    struct ReferenceComparisonRow {
        std::string label;
        Fitness fit;
        PhysicalDiagnostics physics;
    };

    static Genome constantReferenceGenome(double u, double v) {
        Genome g;
        g.shapeCore=std::make_unique<Node>(u);
        g.redshiftCore=std::make_unique<Node>(v);
        return g;
    }

    static void referenceComparison(const Individual& champion,
                                    unsigned finePoints) {
        info("[REFERENCE COMPARISON] Start, r0=1, r in [1+1e-7,100]");
        info("[REFERENCE COMPARISON] Morris-Thorne denotes a metric framework, not a unique reference solution.");
        info("[REFERENCE COMPARISON] Near-flare-out examples are constructed comparisons, NOT literature attributions.");
        const std::vector<double> radii=grid(finePoints,100.0);
        std::vector<ReferenceComparisonRow> rows;
        auto add=[&](const std::string& label,const Genome& g) {
            ReferenceComparisonRow row;
            row.label=label;
            row.fit=evaluateGenome(g,radii);
            row.physics=physicalDiagnostics(g,finePoints);
            rows.push_back(std::move(row));
        };
        add("Ellis-Bronnikov_r0=1",constantReferenceGenome(0.0,0.0));
        add("Ellis_redshift_deformation",constantReferenceGenome(0.0,-0.75));
        add("Constructed_near_flareout_U1.9",constantReferenceGenome(1.9,0.0));
        add("Constructed_near_flareout_U1.99",constantReferenceGenome(1.99,0.0));
        add("paceval_discovered",champion.g);

        std::ofstream csv("wormhole_reference_comparison.csv");
        if(!csv) {warn("[REFERENCE COMPARISON] Cannot open output CSV");return;}
        csv << "model,valid,physics_complete,score,negative_NEC_fitness,"
               "negative_NEC_quadrature,signed_VIQ,bprime_throat,"
               "max_abs_Ricci,max_K,proper_length,max_radial_tidal,"
               "max_angular_tidal,max_abs_Phi_prime,nodes,depth\n";
        csv << std::setprecision(17);
        const auto& selected=rows.back();
        for(const auto& row:rows) {
            const bool good=row.fit.valid && row.physics.complete;
            csv << row.label << ',' << (row.fit.valid?1:0) << ','
                << (row.physics.complete?1:0) << ',';
            auto field=[&](double v) {
                if(std::isfinite(v)) csv<<v;
                csv<<',';
            };
            field(row.fit.score);
            field(row.fit.negNec);
            field(row.physics.complete?row.physics.negativeNecRadial:
                  std::numeric_limits<double>::quiet_NaN());
            field(row.fit.signedViq);
            field(row.fit.bp0);
            field(row.fit.maxAbsR);
            field(row.fit.maxK);
            field(row.physics.complete?row.physics.properLength:
                  std::numeric_limits<double>::quiet_NaN());
            field(row.physics.complete?row.physics.maxRadialTidal:
                  std::numeric_limits<double>::quiet_NaN());
            field(row.physics.complete?row.physics.maxAngularTidal:
                  std::numeric_limits<double>::quiet_NaN());
            field(row.physics.complete?row.physics.maxAbsPhiPrime:
                  std::numeric_limits<double>::quiet_NaN());
            csv << row.fit.nodes << ',' << row.fit.depth << '\n';
            info("[REFERENCE COMPARISON] " + row.label +
                 " valid="+std::to_string(good)+
                 " negNEC="+fmt(row.fit.negNec)+
                 " bp0="+fmt(row.fit.bp0)+
                 " maxK="+fmt(row.fit.maxK)+
                 " properLength="+(row.physics.complete?fmt(row.physics.properLength):"UNAVAILABLE")+
                 " radialTidal="+(row.physics.complete?fmt(row.physics.maxRadialTidal):"UNAVAILABLE")+
                 " angularTidal="+(row.physics.complete?fmt(row.physics.maxAngularTidal):"UNAVAILABLE"));
        }
        if(selected.fit.valid && selected.physics.complete) {
            const auto& ellis=rows.front();
            if(ellis.fit.valid && ellis.physics.complete) {
                info("[REFERENCE COMPARISON] paceval minus Ellis: delta_negNEC="+
                     fmt(selected.fit.negNec-ellis.fit.negNec)+
                     " delta_maxRadialTidal="+
                     fmt(selected.physics.maxRadialTidal-ellis.physics.maxRadialTidal)+
                     " delta_maxAngularTidal="+
                     fmt(selected.physics.maxAngularTidal-ellis.physics.maxAngularTidal));
            }
        }
        info("[REFERENCE COMPARISON] Saved wormhole_reference_comparison.csv");
        info("[REFERENCE COMPARISON] No universal ranking: NEC, tidal curvature and proper length trade off.");
        info("[REFERENCE COMPARISON] Literature's volume integral need not equal this program's radial NEC objective.");
    }

    // Reproducible comparative benchmark, deliberately opt-in because running
    // 30 independent evolutionary searches is substantially more expensive
    // than the normal 100-candidate demonstration.
    //
    // Arm A: a small copy of the EXISTING genetic-programming strategy with
    // elitism, tournament parent selection, crossover and mutation.
    // Arm B: independent random parameter search in the restricted family
    // constant U(q)=u0, V(q)=v0. Both use the exact SAME number of candidate
    // evaluations on the SAME coarse radial grid. This controls evaluator
    // work but does NOT constitute a fair comparison against an optimized
    // competing algorithm (which should get parameter tuning as well).
    //
    // Both arms are reproducible via mt19937_64 and printed seed. We report
    // each seed, not just a single cherry-picked result. The optional CSV
    // is designed for independent statistical analysis (median, IQR, paired
    // bootstrap confidence intervals, success rate and wall-clock time).
    static void runBenchmark(unsigned seeds, unsigned trials,
                             std::uint64_t baseSeed, const std::vector<double>& radii) {
        if(!seeds) return;
        info("[BENCHMARK] Independent genetic-programming searches vs constant-parameter random search");
        std::ofstream csv("wormhole_benchmark.csv");
        csv<<"seed,genetic_best,constant_parameter_best,evals_per_arm,genetic_seconds,constant_seconds\n";
        for(unsigned k=0;k<seeds;++k) {
            const std::uint64_t seed=baseSeed+static_cast<std::uint64_t>(k);
            std::mt19937_64 rng(seed), parameterRng(seed ^ 0x9e3779b97f4a7c15ULL);
            std::normal_distribution<double> coeff(0.0,1.5);
            const unsigned popSize=std::min(20u,std::max(1u,trials));
            std::vector<Individual> pop;
            pop.reserve(popSize);
            double genetic=std::numeric_limits<double>::infinity();
            const auto beginGen=std::chrono::steady_clock::now();
            unsigned count=0;
            while(count<trials) {
                // Retained elites have already been evaluated. Only new children
                // count against the budget, as in the main genetic search.
                while(pop.size()<popSize && count<trials) {
                    Individual x=randomIndividual(rng,5);
                    x.fit=evaluateGenome(x.g,radii);
                    x.evaluated=true;
                    genetic=std::min(genetic,x.fit.valid?x.fit.score:
                        std::numeric_limits<double>::infinity());
                    pop.push_back(std::move(x));
                    ++count;
                }
                if(count>=trials) break;
                sortPopulation(pop);
                std::vector<Individual> valid;
                for(const auto& x:pop) if(x.fit.valid) valid.push_back(x.clone());
                std::vector<Individual> next;
                next.reserve(popSize);
                if(valid.empty()) {
                    pop.clear();
                    continue;
                }
                const unsigned elites=std::min(4u,static_cast<unsigned>(valid.size()));
                for(unsigned i=0;i<elites;++i) next.push_back(valid[i].clone());
                auto tournament=[&]()->const Individual& {
                    std::uniform_int_distribution<std::size_t> pick(0,valid.size()-1);
                    std::size_t best=pick(rng);
                    for(unsigned j=0;j<3;++j) {
                        const std::size_t candidate=pick(rng);
                        if(valid[candidate].fit.score<valid[best].fit.score) best=candidate;
                    }
                    return valid[best];
                };
                while(next.size()<popSize && count<trials) {
                    const auto& p1=tournament();
                    const auto& p2=tournament();
                    Individual child=breed(p1,p2,rng,5);
                    child.fit=evaluateGenome(child.g,radii);
                    child.evaluated=true;
                    genetic=std::min(genetic,child.fit.valid?child.fit.score:
                        std::numeric_limits<double>::infinity());
                    next.push_back(std::move(child));
                    ++count;
                }
                // If budget is exhausted, no further generation is needed.
                pop=std::move(next);
            }
            const double genSeconds=std::chrono::duration<double>(
                std::chrono::steady_clock::now()-beginGen).count();
            const auto beginPar=std::chrono::steady_clock::now();
            double param=std::numeric_limits<double>::infinity();
            for(unsigned i=0;i<trials;++i) {
                Genome g;
                g.shapeCore=std::make_unique<Node>(coeff(parameterRng));
                g.redshiftCore=std::make_unique<Node>(coeff(parameterRng));
                const Fitness fit=evaluateGenome(g,radii);
                if(fit.valid) param=std::min(param,fit.score);
            }
            const double paramSeconds=std::chrono::duration<double>(
                std::chrono::steady_clock::now()-beginPar).count();
            csv<<seed<<","<<fmt(genetic)<<","<<fmt(param)<<","<<trials
               <<","<<fmt(genSeconds)<<","<<fmt(paramSeconds)<<"\n";
            info("[BENCHMARK] seed="+std::to_string(seed)+
                 " genetic="+fmt(genetic)+" constant="+fmt(param)+
                 " genetic_s="+fmt(genSeconds)+" constant_s="+fmt(paramSeconds));
        }
        info("[BENCHMARK] CSV written: wormhole_benchmark.csv");
        info("[BENCHMARK] Fairness caveat: baseline is RANDOM parameter search, not tuned optimization.");
    }

	// ============================================================================
	// paceval library lifetime (RAII)
	// ============================================================================

	class PacevalLibraryGuard {
	public:
		PacevalLibraryGuard() {
			// Initialize the native SDK ONCE per process before any handle.
			// NULL selects the API default initialization options.
			if (!paceval_InitializeLibrary(NULL)) {
				throw std::runtime_error("paceval_InitializeLibrary(NULL) failed. Check the paceval DLL and configuration.");
			}
		}

		~PacevalLibraryGuard() noexcept {
			// All PaceBundle objects must be destroyed before the library is freed.
			// Release library-global resources AFTER every computation handle
			// has been deleted (RAII scope guarantees this in normal control flow).
			if (!paceval_FreeLibrary()) {
				std::cerr << "[WARN] paceval_FreeLibrary() failed.\n";
			}
		}

		PacevalLibraryGuard(const PacevalLibraryGuard&) = delete;
		PacevalLibraryGuard& operator=(const PacevalLibraryGuard&) = delete;
	};


	// ============================================================================
	// SCIENTIFIC VALIDATION STAGE 1 - reference identities and TINC regression
	// ============================================================================
	// IMPORTANT: The fitness evaluator deliberately creates only six handles.
	// Validation needs ALL twelve physical fields, so it creates a temporary
	// complete set of handles. These are discarded before the evolutionary search.
	// None of the validation code changes candidate ranking or batch settings.
	//
	// Independent reference family (r0=1):
	//   U(q)=u (constant), V(q)=v (constant), q=(r-1)/r.
	//   b(r)=(1+u)/r-u/r^2, Phi(r)=v/r.
	// The derivatives below are implemented directly in C++, not produced by
	// diff2(), buildMetric(), or paceval. Thus failures can expose mistakes in
	// the symbolic chain rule and in the tensor identities.
	//
	// These are exact analytical reference functions in classical GR, not
	// guarantees of physical realizability or a continuum proof.
	static std::array<double, NFUN> independentReference(double r, double u, double v) {
		const double inv = 1.0/r;
		const double i2 = inv*inv, i3 = i2*inv, i4 = i3*inv;
		const double i5 = i4*inv;
		const double b   = (1.0+u)*inv-u*i2;
		const double bp  = -(1.0+u)*i2+2.0*u*i3;
		const double bpp = 2.0*(1.0+u)*i3-6.0*u*i4;
		const double phi = v*inv;
		const double phip = -v*i2;
		const double phipp = 2.0*v*i3;
		const double e = 1.0-b*inv;
		const double delta = r*bp-b;
		const double rho = bp*i2;
		const double pr = -b*i3+2.0*e*phip*inv;
		const double pt = e*(phipp+phip*phip+phip*inv)
			 - delta*phip*i2/2.0 - delta*i3/2.0;
		const double nec = rho+pr;
		// Independent check from the trace of the Einstein equations.
		const double ricci = rho-pr-2.0*pt;
		const double ra = e*(phipp+phip*phip)-phip*delta*i2/2.0;
		const double rb = e*phip*inv;
		const double rc = delta*i3/2.0;
		const double rd = b*i3;
		const double kretsch = 4.0*(ra*ra+2.0*rb*rb+2.0*rc*rc+rd*rd);
		(void)i5;
		return {b,bp,bpp,phi,phip,phipp,rho,pr,pt,nec,ricci,kretsch};
	}

	static bool nearReference(double actual, double expected, double atol=2e-10,
		double rtol=2e-9) {
		return std::isfinite(actual) && std::isfinite(expected) &&
			std::abs(actual-expected)<=atol+rtol*std::abs(expected);
	}

	// Simple independent analytical identities for the first reference.
	// This prevents two accidentally matching implementations from hiding an
	// incorrect baseline: rho=pr=-1/r^4, pt=+1/r^4, R=-2/r^4,
	// K=12/r^8, and NEC=-2/r^4.
	static bool checkClosedBaseline(double r) {
		const auto z=independentReference(r,0.0,0.0);
		const double r2=r*r, r4=r2*r2, r8=r4*r4;
		const std::array<std::pair<unsigned,double>, 7> expected = {{
			{B,1.0/r}, {BP,-1.0/r2}, {RHO8,-1.0/r4},
			{PR8,-1.0/r4}, {PT8,1.0/r4}, {NEC8,-2.0/r4},
			{RICCI,-2.0/r4}}};
		for (const auto& e:expected) {
			if (!nearReference(z[e.first], e.second, 1e-13, 1e-13)) return false;
		}
		return nearReference(z[KRET],12.0/r8,1e-13,1e-13);
	}

	// The return value of the Ext API is treated as an error indicator, as in
	// the existing screening code. Per-point errors take precedence. A scalar
	// fallback is used only to diagnose a failure; it never converts a bad
	// batch TINC interval into a successful verification silently.
	static bool runScientificValidation() {
		using clock=std::chrono::steady_clock;
		const auto started=clock::now();
		info("[VALIDATION] Stage 1 START: 12 analytic fields, tensor identities, TINC scalar/batch regression");
		struct ReferenceCase { const char* name; double u; double v; };
		const std::array<ReferenceCase,3> cases = {{
			{"Ellis-type baseline U=0,V=0",0.0,0.0},
			{"Nonzero redshift U=0,V=-0.75",0.0,-0.75},
			{"Nontrivial shape U=0.5,V=0.25",0.5,0.25}
		}};
		// Include the throat exactly for algebraic tests, but keep it out of
		// the TINC regression where degenerate intervals could be SDK-specific.
		const std::vector<double> rs = {1.0,1.0001,1.03,1.2,1.5,2.0,5.0,10.0,25.0};
		const std::vector<double> tincRs = {1.03,1.2,1.5,2.0,5.0,10.0};
		unsigned checks=0, batchChecks=0, intervalChecks=0;
		for (const auto& c:cases) {
			info(std::string("[VALIDATION CASE] ")+c.name);
			Genome genome;
			genome.shapeCore=std::make_unique<Node>(c.u);
			genome.redshiftCore=std::make_unique<Node>(c.v);
			const MetricExpressions m=buildMetric(genome);
			// This is especially valuable for regression of the old TINC 142:
			// for U=V=0 the b_prime expression should now be a short, direct
			// representation of -1/r^2, with no 0/r subexpressions.
			info(std::string("[VALIDATION EXPRESSION] ")+c.name+
				" b_prime="+m.bp+" length="+std::to_string(m.bp.size()));
			const std::array<std::string,NFUN> expressions = {{
				m.b,m.bp,m.bpp,m.phi,m.phip,m.phipp,m.rho8,m.pr8,m.pt8,
				m.nec8,m.ricci,m.kretsch
			}};
			// Full RAII handle ownership, including in exception / early-return paths.
			struct HandleSet {
				std::array<PACEVAL_HANDLE,NFUN> h{};
				~HandleSet(){for(auto& x:h) if(x) // Free compiled graph and associated SDK resources; no handle leaks.
					paceval_DeleteComputation(x);}
			};
			HandleSet plain, interval;
			for (unsigned f=0;f<NFUN;++f) {
				// Baseline validation: compile a NON-TINC handle to check
				// ordinary double values against independent analytic formulas.
				plain.h[f]=paceval_CreateComputation(expressions[f].c_str(),1,"r",false,NULL);
				if (!plain.h[f] || paceval_GetIsError(plain.h[f])) {
					warn(std::string("[VALIDATION FAIL] create double field=")+functionName(f));return false;
				}
			}
			for (double r:rs) {
					const auto ref=independentReference(r,c.u,c.v);
					if (c.u==0.0 && c.v==0.0 && !checkClosedBaseline(r)) {
						warn("[VALIDATION FAIL] independent closed-form baseline at r="+fmt(r));return false;
					}
					for (unsigned f=0;f<NFUN;++f) {
						double arg[1]={r};
						const double got=paceval_dGetComputationResult(plain.h[f],arg,NULL,NULL);
						if (paceval_GetIsError(plain.h[f]) || !nearReference(got,ref[f])) {
							warn(std::string("[VALIDATION FAIL] double ")+c.name+" field="+functionName(f)+
								" r="+fmt(r)+" got="+fmt(got)+" expected="+fmt(ref[f]));return false;
						}
						++checks;
					}
			}
			// A separate TINC-enabled handle is created for every physical field.
			// Test all 12, including rho/pr/pt and both second derivatives.
			for (unsigned f=0;f<NFUN;++f) {
				// Regression: compile the same expression with TINC enabled.
				// This is distinct from double-only evaluation and must return
				// valid bounds for all selected reference points.
				interval.h[f]=paceval_CreateComputation(expressions[f].c_str(),1,"r",true,NULL);
				if (!interval.h[f] || paceval_GetIsError(interval.h[f])) {
					warn(std::string("[VALIDATION FAIL] create TINC field=")+functionName(f));return false;
				}
				std::vector<double> inputs(tincRs), out(inputs.size()), low(inputs.size()), high(inputs.size());
				std::vector<int> errors(inputs.size(),0);
				// Verify vectorized TINC agrees with the scalar TINC API at
				// identical radii (regression for numerical correctness).
				const bool batchError=paceval_dGetComputationResultExt(interval.h[f],inputs.data(),
					static_cast<unsigned long>(inputs.size()),out.data(),low.data(),high.data(),errors.data());
				// IMPORTANT: 'batchError' summarizes the entire batch. It does NOT identify
				// which radius failed. Earlier code aborted here and suppressed all useful
				// diagnostic information, making error 145 look like a global failure.
				// Always inspect every per-point error and record the field/radius/code.
				if (batchError) {
					warn(std::string("[VALIDATION BATCH ERROR] case=")+c.name+
						" field="+functionName(f)+" hasError=1; inspecting all points");
				}
				unsigned badPoints=0;
				for(std::size_t k=0;k<inputs.size();++k) {
					const double r=inputs[k], expected=independentReference(r,c.u,c.v)[f];
					const bool intervalBad=(errors[k]!=0 || !std::isfinite(out[k]) ||
						!std::isfinite(low[k]) || !std::isfinite(high[k]) || low[k]>high[k] ||
						!nearReference(out[k],expected) ||
						low[k]>expected+2e-10 || high[k]<expected-2e-10);
					// Never interpret a failed TINC interval as verified. A scalar retry
					// diagnoses whether the issue is specific to batch execution; its
					// result is reported separately, not substituted silently.
					double arg[1]={r}, slo=0.0,shi=0.0;
					// Scalar TINC provides an independent CALL PATH, though both
					// paths still use the same underlying paceval evaluator.
					const double scalar=paceval_dGetComputationResult(interval.h[f],arg,&slo,&shi);
					const bool scalarError=paceval_GetIsError(interval.h[f]);
					int scalarCode=0;
					char operatorName[256]={};
					long errorPosition=-1;
					if(scalarError) scalarCode=paceval_GetErrorInformation(interval.h[f],operatorName,&errorPosition);
					const bool scalarBad=scalarError || !std::isfinite(scalar) ||
						!std::isfinite(slo) || !std::isfinite(shi) || slo>shi ||
						!nearReference(scalar,expected) ||
						slo>expected+2e-10 || shi<expected-2e-10;
					if(intervalBad || scalarBad) {
						++badPoints;
						warn(std::string("[VALIDATION POINT DIAGNOSTIC] case=")+c.name+
							" field="+functionName(f)+" index="+std::to_string(k)+" r="+fmt(r)+
							" expected="+fmt(expected)+" batch_code="+std::to_string(errors[k])+
							" batch_value="+fmt(out[k])+" batch_interval=["+fmt(low[k])+","+fmt(high[k])+ "]"+
							" scalar_code="+std::to_string(scalarCode)+" scalar_value="+fmt(scalar)+
							" scalar_interval=["+fmt(slo)+","+fmt(shi)+"]"+
							" operator="+operatorName+" position="+std::to_string(errorPosition));
					}
					if (intervalBad || scalarBad) {
						// Strict scientific mode: if either path fails, the *regression*
						// fails. Passing scalar alone would not prove that batch is correct.
						// Continue through every radius so the log captures the full pattern.
						continue;
					}
					if(!nearReference(scalar,out[k])) {
						++badPoints;
						warn(std::string("[VALIDATION SCALAR/BATCH DIFFERENCE] field=")+functionName(f)+
							" r="+fmt(r)+" scalar="+fmt(scalar)+" batch="+fmt(out[k]));
						continue;
					}
					++batchChecks;
					++intervalChecks;
				}
				if (badPoints || batchError) {
					// The batch summary may report an error even when point diagnostics
					// do not; preserve that distinction and fail conservatively.
					warn(std::string("[VALIDATION FAIL] ")+c.name+" field="+functionName(f)+
						" bad_points="+std::to_string(badPoints)+
						" batch_has_error="+std::to_string(batchError)+
						" formula_length="+std::to_string(expressions[f].size()));
					debug(std::string("[VALIDATION FAILED EXPRESSION] ")+functionName(f)+" = "+expressions[f]);
					return false;
				}

			}
			info(std::string("[VALIDATION PASS] ")+c.name+" all 12 fields, scalar and batch TINC");
		}
		const double elapsed=std::chrono::duration<double>(clock::now()-started).count();
		info("[VALIDATION PASS] Stage 1: double="+std::to_string(checks)+
			" TINC_batch="+std::to_string(batchChecks)+" TINC_scalar="+
			std::to_string(intervalChecks)+" seconds="+fmt(elapsed));
		info("[VALIDATION NOTE] Sampled TINC intervals do not establish continuum validity.");
		return true;
	}

	// ============================================================================
	// Main
	// ============================================================================

} // namespace awd

int main(int argc, char** argv) {
	using namespace awd;
	g_programStart = std::chrono::steady_clock::now();

	try {
		Options o = parseArgs(argc, argv);
		g_verbose = static_cast<int>(o.verbose);
		g_log.open("wormhole_discovery_debug.log", std::ios::out);

		// Initialize once before any paceval computation; automatically free
		// after all local computations have been destroyed, even on early return.
		info("[INIT] Calling paceval_InitializeLibrary...");
		PacevalLibraryGuard pacevalLibrary;
		info("[INIT] paceval initialized successfully");

		info("============================================================");
		info(" paceval AUTONOMOUS WORMHOLE GEOMETRY DISCOVERY");
		info("============================================================");
		info("Run tag       : " + nowTag());
		info("Seed          : " + std::to_string(o.seed));
		info("Population    : " + std::to_string(o.population));
		info("Investigations: " + std::to_string(o.investigations));
		info("Default start : no arguments needed");
		info("Generations   : " + std::to_string(o.generations));
		info("Elite         : " + std::to_string(o.elite));
		info("Max tree depth: " + std::to_string(o.maxTreeDepth));
		info("Coarse points : " + std::to_string(o.coarsePoints));
		info("Fine points   : " + std::to_string(o.finePoints));
		info("TINC          : " + std::string(o.tinc ? "enabled" : "disabled"));
		info("Adaptive TINC additional points: " + std::to_string(o.adaptivePoints));
		info("Adaptive TINC wave size: " + std::to_string(o.adaptiveWaveSize));
		info("TINC batch size: " + std::to_string(o.tincBatchSize) + " (user configurable; benchmark before optimizing)");
		info("Hardware threads (hint): " + std::to_string(std::thread::hardware_concurrency()));
		info("Batch evaluation: paceval_dGetComputationResultExt; 6 handles/candidate");
		info("Debug log     : wormhole_discovery_debug.log");

		std::mt19937_64 rng(o.seed);
		auto coarse = grid(o.coarsePoints, 40.0);

		// ---------------------------------------------------------------
		// Pre-flight test 1: known simple genome.
		// U=0, V=0 -> b=1/r, Phi=0.
		// Analytically: b'(1)=-1; NEC8=-2/r^4; R=-2/r^4; K=12/r^8.
		// ---------------------------------------------------------------
		Genome baseline;
		baseline.shapeCore = std::make_unique<Node>(0.0);
		baseline.redshiftCore = std::make_unique<Node>(0.0);

		// Check potentially problematic sign expressions independently before the full baseline.
		info("[SIGN TEST] Checking equivalent formulas at r=1...");
		const std::array<std::pair<const char*, double>, 5> signTests = { {
			{ "(0-1)", -1.0 },
			{ "((0-1)/(r*r))", -1.0 },
			{ "(0-(1/(r*r)))", -1.0 },
			{ "(1/r)", 1.0 },
			{ "((0-2)/(r*r*r))", -2.0 }
		} };
		for (const auto& test : signTests) {
			// Minimal operator regression; a fresh handle isolates parser
			// or arithmetic API errors before searching candidate geometries.
			PACEVAL_HANDLE htest = paceval_CreateComputation(test.first, 1, "r", false, NULL);
			if (htest == NULL) {
				warn(std::string("[SIGN TEST FAILED CREATE] ") + test.first);
				return EXIT_FAILURE;
			}
			double v[1] = { 1.0 };
			// Single-value double check; no TINC bounds needed here.
			double actual = paceval_dGetComputationResult(htest, v, NULL, NULL);
			const bool testError = paceval_GetIsError(htest);
			if (testError) {
				char operatorName[256] = {};
				long errorPosition = -1;
				const int code = paceval_GetErrorInformation(htest, operatorName, &errorPosition);
				warn(std::string("[SIGN TEST PACEVAL ERROR] code=") + std::to_string(code) +
					" operator=" + operatorName + " position=" + std::to_string(errorPosition));
			}
			// The test handle is no longer needed; release immediately.
			paceval_DeleteComputation(htest);
			info(std::string("[SIGN TEST] ") + test.first + " result=" +
				fmt(static_cast<double>(actual)) + " expected=" + fmt(static_cast<double>(test.second)));
			if (testError || !std::isfinite(actual) || std::abs(actual - test.second) > 1e-10) {
				warn("[SIGN TEST FAILED] Stopping before wormhole search: paceval expression semantics differ.");
				return EXIT_FAILURE;
			}
		}

		info("Pre-flight: evaluating analytic baseline b=1/r, Phi=0...");
		Fitness bf = evaluateGenome(baseline, coarse, true);
		if (!bf.valid) {
			warn(std::string("BASELINE FAILED. reject=") + rejectName(bf.reject));
			warn("[BASELINE EXPECTED] b(1)=1, b_prime(1)=-1, NEC8(1)=-2, Ricci(1)=-2, K(1)=12");
			warn("[BASELINE ACTUAL] bp0=" + fmt(bf.bp0) + " minNEC8=" + fmt(bf.minNec8) +
				" maxK=" + fmt(bf.maxK) + " minExterior=" + fmt(bf.minExterior));
			warn("Stop: do not trust a search when the analytic baseline fails.");
			return EXIT_FAILURE;
		}
		info("Baseline passed. b'(1)=" + fmt(bf.bp0) +
			" minNEC8=" + fmt(bf.minNec8) +
			" maxK=" + fmt(bf.maxK));

		// ---------------------------------------------------------------
		// Pre-flight test 2: symbolic derivative vs finite difference.
		// ---------------------------------------------------------------
		Genome derivativeTest;
		derivativeTest.shapeCore = randomTree(rng, 3);
		derivativeTest.redshiftCore = randomTree(rng, 3);
		info("Pre-flight: symbolic derivative sanity check...");
		if (!derivativeSanity(derivativeTest)) {
			warn("DERIVATIVE SANITY CHECK FAILED.");
			warn("Stop: inspect generated expressions before continuing.");
			return EXIT_FAILURE;
		}
		info("Derivative sanity passed.");

		// The search is prohibited until all 12 symbolic fields, their independent
		// analytic references, and TINC scalar/batch consistency have passed.
		if (!runScientificValidation()) {
			warn("[VALIDATION FATAL] Search stopped: investigate reference or TINC mismatch.");
			return EXIT_FAILURE;
		}

        // Optional paired, repeatable performance/quality comparison. It uses
        // independent RNGs, so the main deterministic evolution is unchanged.
        if(o.benchmarkSeeds)
            runBenchmark(o.benchmarkSeeds,o.benchmarkTrials,o.seed,coarse);

		// ---------------------------------------------------------------
		// Initial population
		// ---------------------------------------------------------------
		std::vector<Individual> pop;
		pop.reserve(o.population);
		std::unordered_set<std::string> seen;

		for (unsigned i = 0; i < o.population; ++i) {
			Individual x = randomIndividual(rng, o.maxTreeDepth);
			x.signature = signature(x.g);
			if (seen.insert(x.signature).second) pop.push_back(std::move(x));
			else --i;
		}

		ParetoArchive paretoArchive;
		double allTimeBest = std::numeric_limits<double>::infinity();
		Individual champion;
		bool haveChampion = false;
		unsigned investigationsDone = 0;

		const auto t0 = std::chrono::steady_clock::now();

		for (unsigned gen = 0; gen < o.generations; ++gen) {
			RejectStats rs;
			auto gt0 = std::chrono::steady_clock::now();

			// Count only NEW evaluations; retained elites are not investigations.
			for (unsigned i = 0; i < pop.size(); ++i) {
				if (!pop[i].evaluated) {
					if (investigationsDone >= o.investigations) break;
					debug("Investigation " + std::to_string(investigationsDone + 1) +
						"/" + std::to_string(o.investigations) + " START (generation " +
						std::to_string(gen) + ", candidate " + std::to_string(i) + ")");
					pop[i].fit = evaluateGenome(pop[i].g, coarse,
						g_verbose >= 3 && i < 2);
                    // A second objective is evaluated independently, using the same
                    // paceval-based physical diagnostics for every candidate.
                    // Coarse resolution reduces cost; final front uses fine resolution.
                    if(pop[i].fit.valid) {
                        const auto diag=physicalDiagnostics(pop[i].g,o.coarsePoints);
                        if(diag.complete) pop[i].fit.tidalObjective=
                            std::max(diag.maxRadialTidal,diag.maxAngularTidal);
                    }
                    paretoArchive.observe(pop[i]);
					pop[i].evaluated = true;
					++investigationsDone;
					debug("Investigation " + std::to_string(investigationsDone) +
						"/" + std::to_string(o.investigations) +
						" END: " + rejectName(pop[i].fit.reject) +
						" score=" + fmt(pop[i].fit.score) +
						" nodes=" + std::to_string(pop[i].fit.nodes));
				}
				rs.add(pop[i].fit.reject);
			}

			paretoSortPopulation(pop);

			unsigned validCount = 0;
			for (const auto& x : pop) if (x.fit.valid) validCount++;

			auto gt1 = std::chrono::steady_clock::now();
			double gsec = std::chrono::duration<double>(gt1 - gt0).count();

			info("------------------------------------------------------------");
			info("Generation " + std::to_string(gen) +
				" evaluated in " + fmt(gsec) + " s");
			info("Reject statistics: " + rs.str());
			info("Valid population: " + std::to_string(validCount) +
				" / " + std::to_string(pop.size()));

			if (validCount == 0) {
				if (investigationsDone >= o.investigations) break;
				warn("No valid individuals. Injecting fresh random population.");
				pop.clear(); seen.clear();
				for (unsigned i = 0; i < o.population; ++i)
					pop.push_back(randomIndividual(rng, o.maxTreeDepth));
				continue;
			}

            // The first population item is now ranked by Pareto front and crowding,
            // NOT by the historical scalar fitness score.
            const auto generationScalarBest=std::min_element(pop.begin(),pop.end(),
                [](const Individual& a,const Individual& b) {
                    if(a.fit.valid!=b.fit.valid) return a.fit.valid>b.fit.valid;
                    return a.fit.score<b.fit.score;
                });
            if(generationScalarBest!=pop.end() && generationScalarBest->fit.valid)
                printBest(*generationScalarBest, gen);
            const auto generationFronts=paretoFronts(pop);
            info("[PARETO GENERATION] nondominated="+
                std::to_string(generationFronts.empty()?0:generationFronts.front().size())+
                " (NEC and sampled static tidal curvature)");

            const auto scalarIt=std::min_element(pop.begin(),pop.end(),
                [](const Individual& a,const Individual& b) {
                    if(a.fit.valid!=b.fit.valid) return a.fit.valid>b.fit.valid;
                    return a.fit.score<b.fit.score;
                });
			if (scalarIt!=pop.end() && scalarIt->fit.valid && scalarIt->fit.score < allTimeBest) {
				allTimeBest = scalarIt->fit.score;
				champion = scalarIt->clone();
				haveChampion = true;
				info("*** NEW ALL-TIME CHAMPION ***");
				info("U(q) = " + expr(*champion.g.shapeCore));
				info("V(q) = " + expr(*champion.g.redshiftCore));
				MetricExpressions cm = buildMetric(champion.g);
				debug("b(r)   = " + cm.b);
				debug("Phi(r) = " + cm.phi);
			}

			if (o.checkpointEvery > 0 &&
				((gen + 1) % o.checkpointEvery == 0 || gen + 1 == o.generations)) {
				writeCheckpoint(pop, gen + 1);
				info("Checkpoint written for generation " + std::to_string(gen + 1));
			}

			// Last generation needs no offspring.
			if (gen + 1 == o.generations || investigationsDone >= o.investigations) break;

			// -----------------------------------------------------------
			// Breed next generation.
			// Keep elites, then tournament-select parents.
			// -----------------------------------------------------------
			std::vector<Individual> next;
			next.reserve(o.population);

			unsigned keep = std::min(o.elite, validCount);
			for (unsigned i = 0; i < keep; ++i) next.push_back(pop[i].clone());

			auto tournament = [&]()->const Individual& {
				std::uniform_int_distribution<unsigned> d(0, validCount - 1);
				unsigned best = d(rng);
				for (int k = 0; k < 3; ++k) {
					unsigned j = d(rng);
					if (j < best) best = j; // NSGA-II front/crowding order, not scalar fitness
				}
				return pop[best];
			};

			seen.clear();
			for (auto& x : next) {
				x.signature = signature(x.g);
				seen.insert(x.signature);
			}

			unsigned duplicateAttempts = 0;
			while (next.size() < o.population) {
				const Individual& p1 = tournament();
				const Individual& p2 = tournament();
				Individual child = breed(p1, p2, rng, o.maxTreeDepth);
				child.signature = signature(child.g);

				if (seen.insert(child.signature).second) {
					next.push_back(std::move(child));
				}
				else {
					duplicateAttempts++;
					if (duplicateAttempts > 10000) {
						warn("Too many duplicate offspring; injecting random individual.");
						next.push_back(randomIndividual(rng, o.maxTreeDepth));
						duplicateAttempts = 0;
					}
				}
			}

			pop = std::move(next);
		}

		if (!haveChampion) {
			warn("Search ended without a valid champion.");
			return EXIT_FAILURE;
		}

		const auto t1 = std::chrono::steady_clock::now();
		info("============================================================");
		info("SEARCH COMPLETE");
		info("Investigations performed: " + std::to_string(investigationsDone) +
			" / " + std::to_string(o.investigations));
		info("Total seconds: " +
			fmt(std::chrono::duration<double>(t1 - t0).count()));

		// ---------------------------------------------------------------
		// Fine-grid re-evaluation
		// ---------------------------------------------------------------
		info("Fine-grid re-evaluation of champion...");
		auto fine = grid(o.finePoints, 100.0);
		Fitness ff = evaluateGenome(champion.g, fine, true);

		if (!ff.valid) {
			warn(std::string("CHAMPION FAILED FINE GRID. reject=") +
				rejectName(ff.reject));
			warn("This is scientifically useful: coarse-grid false positive rejected.");
			return EXIT_FAILURE;
		}

		champion.fit = ff;
		MetricExpressions finalM = buildMetric(champion.g);

		info("============================================================");
		info("FINAL FINE-GRID CANDIDATE");
		info("============================================================");
		info("score             = " + fmt(ff.score));
		info("negative NEC      = " + fmt(ff.negNec));
		info("signed VIQ        = " + fmt(ff.signedViq));
		info("min NEC8          = " + fmt(ff.minNec8));
		info("b'(r0)            = " + fmt(ff.bp0));
		info("max |R|           = " + fmt(ff.maxAbsR));
		info("max K             = " + fmt(ff.maxK));
		info("max |Phi|         = " + fmt(ff.maxAbsPhi));
		info("min (1-b/r)       = " + fmt(ff.minExterior));
		info("tree nodes        = " + std::to_string(ff.nodes));
		info("tree depth        = " + std::to_string(ff.depth));
		info("------------------------------------------------------------");
		info("DISCOVERED SHAPE CORE U(q):");
		info(expr(*champion.g.shapeCore));
		info("DISCOVERED REDSHIFT CORE V(q):");
		info(expr(*champion.g.redshiftCore));
		info("------------------------------------------------------------");
		info("FULL b(r):");
		info(finalM.b);
		info("FULL Phi(r):");
		info(finalM.phi);

		// Write final expressions separately for easy CAS import/review.
		{
			std::ofstream f("wormhole_final_candidate.txt");
			f << "Autonomous wormhole discovery candidate\n\n";
			f << "q=(r-1)/r\n\n";
			f << "U(q) = " << expr(*champion.g.shapeCore) << "\n\n";
			f << "V(q) = " << expr(*champion.g.redshiftCore) << "\n\n";
			f << "b(r) = " << finalM.b << "\n\n";
			f << "Phi(r) = " << finalM.phi << "\n\n";
			f << "b'(r) = " << finalM.bp << "\n\n";
			f << "b''(r) = " << finalM.bpp << "\n\n";
			f << "8*pi*rho = " << finalM.rho8 << "\n\n";
			f << "8*pi*pr = " << finalM.pr8 << "\n\n";
			f << "8*pi*pt = " << finalM.pt8 << "\n\n";
			f << "8*pi*(rho+pr) = " << finalM.nec8 << "\n\n";
			f << "Ricci R = " << finalM.ricci << "\n\n";
			f << "Kretschmann K = " << finalM.kretsch << "\n";
		}
		info("Final expressions written to wormhole_final_candidate.txt");

		// Preserve the TINC outcome for a scientifically qualified final summary.
		// Do not report a verified candidate if any point remained unresolved.
		TincSummary tincSummary;
		const bool tincPassed = o.tinc ? tincReport(champion, o.tincPoints, o.tincBatchSize, &tincSummary) : false;
		// Extra adaptive TINC samples are a heuristic improvement in coverage,
		// NOT an enclosure of every real r between adjacent samples.
		const AdaptiveTincSummary adaptive = o.tinc ? adaptiveTincReport(champion, o.adaptivePoints, o.tincBatchSize, o.adaptiveWaveSize) : AdaptiveTincSummary{};
        const PhysicalDiagnostics physical=physicalDiagnostics(champion.g,o.finePoints);
        if(!physical.complete) warn("[PHYSICS] Diagnostic quadrature failed; no physical metrics asserted.");
        // Reference comparison is deliberately post-search: zero effect on selection.
        referenceComparison(champion, o.finePoints);
        // Full fine-grid Pareto archive report is independent of legacy winner.
        paretoFinalReport(paretoArchive,o.finePoints,champion,o.paretoFinalLimit);

		info("============================================================");
		info("SCIENTIFIC INTERPRETATION");
		info("============================================================");
		info("The program has evolved mathematical structures, not merely");
		info("parameters of one preselected wormhole function.");
		info("A low score is NOT evidence that a physical wormhole exists.");
		info("Before any novelty claim, independently verify the tensor");
		info("equations, continuum behavior, proper-distance/traversal");
		info("properties, stability, QEI constraints, and literature novelty.");
		info("Full diagnostic trace: wormhole_discovery_debug.log");
		info("============================================================");
		info("CONCLUSION FOR THE USER");
		info("============================================================");
		// Scientific result summary. Read fitness values exclusively from the
		// FINAL fine-grid evaluation: a coarse-grid score is not comparable.
		// The radius r0=1 is a dimensionless normalization, not a physical size.
		info("[CANDIDATE SUMMARY] Investigations       : " + std::to_string(o.investigations));
		info("[CANDIDATE SUMMARY] Fine-grid points    : " + std::to_string(o.finePoints));
		info("[CANDIDATE SUMMARY] Fine-grid radius    : 1+1e-7 to 100 (r0=1 units)");
		info("[CANDIDATE SUMMARY] Fitness score       : " + fmt(ff.score));
		info("[CANDIDATE SUMMARY] Negative NEC integral: " + fmt(ff.negNec));
		info("[CANDIDATE SUMMARY] Signed VIQ          : " + fmt(ff.signedViq));
		info("[CANDIDATE SUMMARY] Min 8pi(rho+pr)    : " + fmt(ff.minNec8));
		info("[CANDIDATE SUMMARY] Throat b'(r0)       : " + fmt(ff.bp0));
		info("[CANDIDATE SUMMARY] Max abs(Ricci)     : " + fmt(ff.maxAbsR));
		info("[CANDIDATE SUMMARY] Max Kretschmann    : " + fmt(ff.maxK));
		info("[CANDIDATE SUMMARY] Max abs(Phi)       : " + fmt(ff.maxAbsPhi));
		info("[CANDIDATE SUMMARY] Min (1-b/r)        : " + fmt(ff.minExterior));
		info("[CANDIDATE SUMMARY] Expression nodes   : " + std::to_string(ff.nodes));
		info("[CANDIDATE SUMMARY] Expression depth   : " + std::to_string(ff.depth));
		info("[VALIDATION SUMMARY] Stage 1          : PASSED (3 analytic references, 12 fields)");
		if (o.tinc) {
			info("[TINC SUMMARY] Pointwise status       : " + std::string(tincPassed ? "PASSED" : "INCOMPLETE"));
			info("[TINC SUMMARY] Radius samples         : " + std::to_string(tincSummary.requested));
			info("[TINC SUMMARY] Exterior passed        : " + std::to_string(tincSummary.exteriorPassed));
			info("[TINC SUMMARY] Curvature passed       : " + std::to_string(tincSummary.curvaturePassed));
			info("[TINC SUMMARY] NEC negative           : " + std::to_string(tincSummary.necNegative));
			info("[TINC SUMMARY] NEC nonnegative        : " + std::to_string(tincSummary.necNonnegative));
			info("[TINC SUMMARY] NEC inconclusive       : " + std::to_string(tincSummary.necInconclusive));
			info("[TINC SUMMARY] NEC evaluated          : " + std::to_string(tincSummary.necEvaluated));
			info("[TINC SUMMARY] Unresolved evaluations : " + std::to_string(tincSummary.unresolved));
			info("[TINC SUMMARY] Widest NEC interval    : " + fmt(tincSummary.widestNecInterval));
			info("[TINC SUMMARY] Batch calculation [s] : " + fmt(tincSummary.evaluationSeconds));
		} else {
			info("[TINC SUMMARY] Pointwise status       : DISABLED");
		}
        if(physical.complete) {
            info("[PHYSICS] Proper radial length r=1..100 (r0 units): "+fmt(physical.properLength));
            info("[PHYSICS] Max static radial Riemann tidal term : "+fmt(physical.maxRadialTidal));
            info("[PHYSICS] Max static angular Riemann tidal term: "+fmt(physical.maxAngularTidal));
            info("[PHYSICS] Max abs(Phi prime)               : "+fmt(physical.maxAbsPhiPrime));
            info("[PHYSICS] Negative NEC radial quadrature   : "+fmt(physical.negativeNecRadial));
            info("[PHYSICS] Quadrature status               : ESTIMATE, not TINC-certified");
            info("[PHYSICS] Asymptotics                     : guaranteed for finite grammar trees");
            info("[PHYSICS] Note: traveller tidal forces need speed and physical throat radius");
        }
		info("[ADAPTIVE SUMMARY] Additional tested points : " + std::to_string(adaptive.tested));
		info("[ADAPTIVE SUMMARY] TINC numerical failures : " + std::to_string(adaptive.failures));
		info("[ADAPTIVE SUMMARY] Exterior/curvature pass: " + std::to_string(adaptive.exteriorPassed) + "/" + std::to_string(adaptive.curvaturePassed));
        info("[ADAPTIVE SUMMARY] New points inserted      : " + std::to_string(adaptive.refined));
        info("[ADAPTIVE SUMMARY] Stop reason              : " + adaptive.stopReason);
		info("[ADAPTIVE SUMMARY] Continuous proof       : NOT ESTABLISHED");
        info("[PARETO SUMMARY] Independent NEC/tidal front: wormhole_pareto_front.csv");
		info("[CANDIDATE SUMMARY] Full formulas: wormhole_final_candidate.txt");
		info("------------------------------------------------------------");
		if (!o.tinc) {
			info("The search found a candidate satisfying the tested classical GR");
			info("conditions on the numerical grid; TINC was disabled, so numerical");
			info("interval verification is still outstanding.");
		} else if (tincPassed && (o.adaptivePoints == 0 || adaptive.passed)) {
			info("The search found a Morris-Thorne geometry candidate that passed");
			info("the implemented classical GR checks and pointwise TINC interval");
			info("checks at all sampled radii. This does not establish continuum");
			info("validity, dynamical stability, quantum realizability or a real wormhole.");
		} else {
			warn("The search found a promising classical GR geometry candidate,");
			warn("but at least one sampled TINC condition remains unverified or failed.");
			warn("No interval-verified candidate can be claimed from this run.");
		}
		info("In all cases, a low negative-NEC score measures the chosen model");
		info("objective only; it is NOT evidence that a physical wormhole exists.");

		return EXIT_SUCCESS;
	}
	catch (const std::exception& e) {
		logLine(0, std::string("[FATAL] ") + e.what());
		return EXIT_FAILURE;
	}
}
