// Exhaustive 20-decision-level binary tree, 1,048,576 reachable terminal paths.
// Original paceval API (SDK 4.25) and external runtime. Synthetic, non-safety model.
// Demonstrates a STRUCTURED tree whose leaf rules admit compact factorization.
// Does NOT claim arbitrary one-million-leaf tables can be compressed similarly.
#include "paceval_main.h"
#include <algorithm>
#include <array>
#include <cmath>
#include <cstdint>
#include <filesystem>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <limits>
#include <sstream>
#include <stdexcept>
#include <string>
#include <vector>

namespace fs=std::filesystem;
static constexpr unsigned D=20, LEAVES=1u<<D, BATCH=4096;
static void check(bool x,const char *msg){ if(!x)throw std::runtime_error(msg); }
static unsigned bitcount(unsigned x){unsigned n=0;while(x){n+=x&1u;x>>=1;}return n;}
static std::string make_sum(bool weighted){
 std::string out="(";
 for(unsigned j=0;j<D;j++){
  if(j)out+="+";
  out+="(x"+std::to_string(j)+">=0.5)";
  if(weighted)out+="*"+std::to_string(1u<<(D-1-j));
 }
 return out+")";
}
struct Graph{
 PACEVAL_HANDLE h=nullptr;
 explicit Graph(const std::string& expr,const std::string& vars){
  h=paceval_CreateComputation(expr.c_str(),D,vars.c_str(),false,nullptr);
  if(!h||paceval_GetIsError(h)){
   char err[256]={},detail[256]={};
   if(h)paceval_CreateErrorInformationText(h,err,detail);
   throw std::runtime_error(std::string("paceval graph construction failed: ")+err+" "+detail);
  }
 }
 Graph(const Graph&)=delete;
 Graph& operator=(const Graph&)=delete;
 ~Graph(){if(h)paceval_DeleteComputation(h);}
};
int main(int argc,char**argv){
 try{
  check(argc==2,"Usage: depth20_exhaustive <project-root>");
  fs::path root=fs::absolute(argv[1]);fs::create_directories(root/"results");
  check(paceval_InitializeLibrary(nullptr),"paceval initialization failed");
  const std::string index=make_sum(true),ones=make_sum(false);
  const std::string s1="(0.07+0.0000003*"+index+"+0.002*"+ones+"+0.03*sin("+index+"/250000))";
  const std::string s2="(0.09+0.00000025*"+index+"+0.0014*"+ones+"+0.04*sin("+index+"/200000)+0.005*((x0>=0.5) AND (x19>=0.5)))";
  std::string vars;for(unsigned j=0;j<D;j++){if(j)vars+=' ';vars+="x"+std::to_string(j);}
  Graph g0(index,vars),g1(ones,vars),g2(s1,vars),g3(s2,vars);
  PACEVAL_HANDLE h[4]={g0.h,g1.h,g2.h,g3.h};
  std::vector<double> input(BATCH*D),output(BATCH*4);
  std::vector<int> errors(BATCH*4);
  uint64_t n=0,counts[4]={0,0,0,0};
  std::array<unsigned,21> pophist{};
  double min1=1e200,max1=-1e200,min2=1e200,max2=-1e200;
  fs::path csv=root/"results"/"depth20_representative_cases.csv";
  std::ofstream casefile(csv);check(bool(casefile),"cannot write representative results");
  casefile<<"leaf_id,ones,score_v1,score_v2,reference_score_v1,reference_score_v2\n";
  casefile<<std::setprecision(17);
  std::ofstream sampled(root/"results"/"depth20_score_samples.csv");
  check(bool(sampled),"cannot write score samples");
  sampled<<"leaf_id,true_predicates,score_v1,score_v2\n"<<std::setprecision(17);
  const unsigned selected[]={0,1,2,3,15,127,1023,65535,262143,524287,524288,524289,786432,1048574,1048575};
  for(unsigned offset=0;offset<LEAVES;offset+=BATCH){
   const unsigned batch=std::min(BATCH,LEAVES-offset);
   for(unsigned k=0;k<batch;k++){
    const unsigned id=offset+k;
    // Twenty actual sensor predicates. Every one of the 2^20 paths is visited once.
    for(unsigned j=0;j<D;j++)input[k*D+j]=((id>>(D-1-j))&1u)?1.0:0.0;
   }
   // Real API call with four persistent paceval graphs; output is graph-major.
   bool failed=paceval_dGetMultipleComputationsResultsExt(h,4,input.data(),batch,output.data(),nullptr,nullptr,errors.data());
   check(!failed,"paceval batch API returned an error");
   for(unsigned k=0;k<batch;k++){
    const unsigned id=offset+k,onesref=bitcount(id);
    double indexgot=output[k],onesgot=output[batch+k];
    double v1=output[2*batch+k],v2=output[3*batch+k];
    for(unsigned j=0;j<4;j++){check(errors[j*batch+k]==0,"paceval per-result error");check(std::isfinite(output[j*batch+k]),"nonfinite paceval result");counts[j]++;}
    check(indexgot==static_cast<double>(id),"wrong leaf index: exhaustive failure");
    check(onesgot==static_cast<double>(onesref),"wrong popcount: exhaustive failure");
    // Independently specified C++ reference. Only used for verification.
    const double r1=0.07+0.0000003*id+0.002*onesref+0.03*std::sin(id/250000.0);
    const double r2=0.09+0.00000025*id+0.0014*onesref+0.04*std::sin(id/200000.0)+0.005*((id&(1u<<19))&&(id&1u)?1.0:0.0);
    check(std::abs(v1-r1)<=1e-12,"v1 score mismatch");
    check(std::abs(v2-r2)<=1e-12,"v2 score mismatch");
    min1=std::min(min1,v1);max1=std::max(max1,v1);min2=std::min(min2,v2);max2=std::max(max2,v2);pophist[onesref]++;n++;
    if(id%512u==0)sampled<<id<<','<<onesref<<','<<v1<<','<<v2<<'\n';
    if(std::find(std::begin(selected),std::end(selected),id)!=std::end(selected))casefile<<id<<','<<onesref<<','<<v1<<','<<v2<<','<<r1<<','<<r2<<'\n';
   }
  }
  // Threshold stress. IEEE-adjacent values are recorded rather than silently
  // treated as exact comparator semantics; host may need an explicit guard band.
  std::ofstream boundary(root/"results"/"depth20_threshold_boundaries.csv");
  check(bool(boundary),"cannot write threshold-boundary results");
  boundary<<"test_id,changed_bit,sensor_value,strict_expected_leaf_id,paceval_leaf_id,strict_match,in_guard_zone\n";
  unsigned boundaryCount=0,boundaryMismatch=0,guardMismatch=0;
  const double testValues[]={0.5-0.000001,0.5-0.0000000001,
   std::nextafter(0.5,0.0),0.5,std::nextafter(0.5,1.0),0.5+0.0000000001,0.5+0.000001};
  for(unsigned bit=0;bit<D;bit++)for(unsigned q=0;q<7;q++){
   std::array<double,D> xs{};double val=testValues[q];xs[bit]=val;
   const unsigned expected=val<0.5?0u:(1u<<(D-1-bit));
   double got=paceval_dGetComputationResult(g0.h,xs.data(),nullptr,nullptr);
   check(!paceval_GetIsError(g0.h) && std::isfinite(got),"threshold evaluation failed");
   bool match=got==static_cast<double>(expected),inGuard=std::abs(val-0.5)<1e-9;
   if(!match){boundaryMismatch++;if(inGuard)guardMismatch++;}
   // Outside the guard band, the documented rule must agree exactly.
   if(!match && !inGuard)check(false,"threshold mismatch outside guard band");
   boundary<<boundaryCount++<<','<<bit<<','<<std::setprecision(17)<<val<<','<<expected<<','<<got<<','<<(match?"true":"false")<<','<<(inGuard?"true":"false")<<'\n';
  }
  check(n==LEAVES,"incomplete set of terminal paths");
  // Combinatorial coverage cross-check: binomial distribution C(20,k).
  uint64_t choose=1;
  for(unsigned k=0;k<=D;k++){
   check(pophist[k]==choose,"unexpected leaf-path histogram");
   if(k<D)choose=choose*(D-k)/(k+1);
  }
  // Persist the observed path-cardinality distribution, not just a theoretical claim.
  std::ofstream cardinality(root/"results"/"depth20_path_cardinality.csv");
  check(bool(cardinality),"cannot write path-cardinality CSV");
  cardinality<<"true_conditions,verified_paths\n";
  for(unsigned k=0;k<=D;k++)cardinality<<k<<','<<pophist[k]<<'\n';
  std::ofstream registry(root/"results"/"depth20_graph_registry.csv");
  check(bool(registry),"cannot write formula manifest");
  registry<<"graph_id,variables,mathematical_function,formula,actual_execution\n";
  auto csvquote=[](const std::string &x){std::string z="\"";for(char c:x){if(c=='\"')z+="\"\"";else z+=c;}return z+"\"";};
  registry<<"depth20_leaf_id,"<<csvquote(vars)<<",exhaustive_path_index,"<<csvquote(index)<<",yes\n";
  registry<<"depth20_true_count,"<<csvquote(vars)<<",number_of_true_predicates,"<<csvquote(ones)<<",yes\n";
  registry<<"depth20_score_v1,"<<csvquote(vars)<<",model_v1_structured_leaf_score,"<<csvquote(s1)<<",yes\n";
  registry<<"depth20_score_v2,"<<csvquote(vars)<<",model_v2_structured_leaf_score,"<<csvquote(s2)<<",yes\n";
  fs::path log=root/"results"/"depth20_exhaustive_audit.txt";
  std::ofstream audit(log);check(bool(audit),"cannot write audit");
  audit<<"study=Complete 20-level structured binary decision tree\n";
  audit<<"execution=original paceval SDK 4.25 and external Linux runtime\n";
  audit<<"scope=all paths tested; leaf scores defined by factored expression, not arbitrary per-leaf table\n";
  audit<<"levels=20\nleaves_declared=1048576\nleaves_visited="<<n<<"\n";
  audit<<"different_graphs_executed=4\n";
  audit<<"graph_output_counts=1048576,1048576,1048576,1048576\n";
  audit<<"total_paceval_graph_outputs="<<counts[0]+counts[1]+counts[2]+counts[3]<<"\n";
  audit<<"multi_graph_batch_calls="<<(LEAVES+BATCH-1)/BATCH<<"\n";
  audit<<"index_exact_checks="<<n<<"\nscore_reference_checks="<<2*n<<"\npath_bitcount_checks="<<n<<"\n";
  audit<<"additional_threshold_stress_cases="<<boundaryCount<<"\n";
  audit<<"strict_comparator_mismatches_near_threshold="<<boundaryMismatch<<"\n";
  audit<<"all_mismatches_inside_1e-9_guard_band="<<(boundaryMismatch==guardMismatch?"true":"false")<<"\n";
  audit<<"all_binomial_coverage_checks=passed\n";
  audit<<std::setprecision(17);
  audit<<"score_v1_range="<<min1<<","<<max1<<"\nscore_v2_range="<<min2<<","<<max2<<"\n";
  audit<<"factored_index_formula_characters="<<index.size()<<"\n";
  audit<<"factored_score_v1_formula_characters="<<s1.size()<<"\n";
  audit<<"factored_score_v2_formula_characters="<<s2.size()<<"\n";
  audit<<"all_combinations_executed=true\nfull_million_term_expansion_executed=false\n";
  audit<<"tinc_used=false\nno_performance_benchmark=true\n";
  std::cout<<"Real paceval 20-level exhaustive test PASSED: "<<n<<" paths, "<<counts[0]+counts[1]+counts[2]+counts[3]<<" graph outputs, "<<(LEAVES+BATCH-1)/BATCH<<" multi-graph batches.\n";
  paceval_FreeLibrary();return 0;
 }catch(const std::exception&e){std::cerr<<"ERROR: "<<e.what()<<'\n';return 2;}
}
