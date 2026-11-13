// Industrial matrix quality-monitoring demonstrator using the ORIGINAL paceval SDK interface.
// This source is provided for native Linux reproduction with a separately acquired ABI-compatible
// libpaceval_linux_sharedLIB.so. Current release numbers for the new workload were obtained via
// the separate REAL paceval MCP 4.26 service because that local binary was not available here.
// Copyright for paceval_main.* remains with upstream paceval authors.
#include "paceval_main.h"
#include <algorithm>
#include <array>
#include <cmath>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <limits>
#include <stdexcept>
#include <string>
#include <vector>

namespace {
constexpr unsigned NVAR = 11;
constexpr unsigned N = 512;
struct Model { const char* id; const char* formula; };
const std::array<Model,9> MODELS{{
  {"q_v1", "a*x*x+2*b*x*y+2*c*x*z+d*y*y+2*e*y*z+f*z*z"},
  {"q_v2", "a*x*x+2*b*x*y+2*c*x*z+d*y*y+2*e*y*z+f*z*z+h*(x*x+y*y+z*z)"},
  {"margin_v1", "t-(a*x*x+2*b*x*y+2*c*x*z+d*y*y+2*e*y*z+f*z*z)"},
  {"margin_v2", "t-(a*x*x+2*b*x*y+2*c*x*z+d*y*y+2*e*y*z+f*z*z+h*(x*x+y*y+z*z))"},
  {"dx_v1", "2*a*x+2*b*y+2*c*z"},
  {"dx_v2", "2*a*x+2*b*y+2*c*z+2*h*x"},
  {"dz_v2", "2*c*x+2*e*y+2*f*z+2*h*z"},
  {"radius_v1", "sqrt(a*x*x+2*b*x*y+2*c*x*z+d*y*y+2*e*y*z+f*z*z)"},
  {"delta_v2_v1", "h*(x*x+y*y+z*z)"}
}};
const char* VARS = "x y z a b c d e f t h";
struct Handles {
  std::vector<PACEVAL_HANDLE> active;
  ~Handles() { for (auto p: active) if(p) paceval_DeleteComputation(p); }
};
void require(bool ok, const char* msg) {if (!ok) throw std::runtime_error(msg);}
std::vector<double> load_inverse(const std::string& root) {
  const std::string path=root+"/results/recorded_baseline/generic_spd_512_inverse.f64";
  std::ifstream in(path,std::ios::binary|std::ios::ate);
  require(in.good(),"Missing recorded full 512x512 paceval inverse");
  auto bytes=in.tellg();
  require(bytes==static_cast<std::streamoff>(sizeof(double)*N*N),"Unexpected inverse byte count");
  in.seekg(0);
  std::vector<double> data(N*N);
  in.read(reinterpret_cast<char*>(data.data()),static_cast<std::streamsize>(bytes));
  require(bool(in),"Failed to read inverse");
  for (double a:data) require(std::isfinite(a),"Nonfinite matrix element");
  return data; // Original file is IEEE754 binary64 little-endian row major.
}
// The 512D residual vector is exactly (x,y,z,0,...,0). Hence its FULL quadratic form
// depends only on the leading 3x3 submatrix of the full 512D precision matrix.
std::array<double,NVAR> input(double x,double y,double z,const std::vector<double>& precision) {
  require(std::isfinite(x)&&std::isfinite(y)&&std::isfinite(z),"Nonfinite residual");
  auto at=[&](unsigned i,unsigned j){return precision[i*N+j];};
  std::array<double,NVAR> v{{x,y,z,at(0,0),at(0,1),at(0,2),at(1,1),at(1,2),at(2,2),7.815,0.08}};
  for (double a:v) require(std::isfinite(a),"Nonfinite graph input");
  require(v[9]>0.0 && v[10]>=0.0,"Invalid threshold or penalty");
  return v;
}
double independent_q(const std::array<double,NVAR>& v) {
  const double x=v[0],y=v[1],z=v[2];
  // Native reference only. NEVER substitute it for actual paceval outputs.
  return v[3]*x*x+2*v[4]*x*y+2*v[5]*x*z+v[6]*y*y+2*v[7]*y*z+v[8]*z*z;
}
void verify_expected(const std::array<double,NVAR>& v,const std::array<double,9>& out) {
  const double q=independent_q(v);
  const double v2=q+v[10]*(v[0]*v[0]+v[1]*v[1]+v[2]*v[2]);
  const std::array<double,9> expected{{q,v2,v[9]-q,v[9]-v2,
    2*v[3]*v[0]+2*v[4]*v[1]+2*v[5]*v[2],
    2*v[3]*v[0]+2*v[4]*v[1]+2*v[5]*v[2]+2*v[10]*v[0],
    2*v[5]*v[0]+2*v[7]*v[1]+2*v[8]*v[2]+2*v[10]*v[2],std::sqrt(q),v2-q}};
  for (unsigned i=0;i<out.size();++i){
    require(std::isfinite(out[i]),"Nonfinite paceval output");
    if (std::abs(out[i]-expected[i])>2e-10*(1.0+std::abs(expected[i]))) {
      throw std::runtime_error("Independent numerical validation failed for model "+std::string(MODELS[i].id));
    }
  }
}
}
int main(int argc,char** argv){
  try {
    const std::string root=(argc>1?argv[1]:".");
    const auto precision=load_inverse(root);
    std::vector<std::array<double,NVAR>> scenarios;
    for (int y=-4;y<=4;++y) for (int x=-4;x<=4;++x)
      scenarios.push_back(input(double(x),double(y),0.75,precision));
    require(paceval_InitializeLibrary(nullptr),"paceval_InitializeLibrary failed");
    try {
      Handles graphs;
      for (const auto& spec: MODELS) {
        PACEVAL_HANDLE h=paceval_CreateComputation(spec.formula,NVAR,VARS,true,nullptr);
        require(h!=nullptr && !paceval_GetIsError(h),"paceval graph creation failed");
        graphs.active.push_back(h);
      }
      // Reuse 8 persistent graph handles across 81 independent scenario inputs.
      std::vector<double> flat;
      flat.reserve(scenarios.size()*NVAR);
      for (const auto& v:scenarios) flat.insert(flat.end(),v.begin(),v.end());
      std::array<std::vector<double>,9> outputs;
      std::array<std::vector<double>,9> lower;
      std::array<std::vector<double>,9> upper;
      for (unsigned g=0;g<9;++g){
        outputs[g].resize(scenarios.size()); lower[g].resize(scenarios.size()); upper[g].resize(scenarios.size());
        std::vector<int> errors(scenarios.size(),0);
        bool has_error=paceval_dGetComputationResultExt(graphs.active[g],flat.data(),
          static_cast<unsigned long>(scenarios.size()),outputs[g].data(),lower[g].data(),upper[g].data(),errors.data());
        require(!has_error,"paceval batch evaluation returned an error");
        for (unsigned i=0;i<scenarios.size();++i){
          require(errors[i]==0 && std::isfinite(outputs[g][i]),"paceval per-point calculation error");
          require(std::isfinite(lower[g][i]) && std::isfinite(upper[g][i]) &&
                  lower[g][i]<=outputs[g][i] && outputs[g][i]<=upper[g][i],"Invalid TINC bounds");
        }
      }
      for (unsigned i=0;i<scenarios.size();++i){
        std::array<double,9> all{};
        for (unsigned g=0;g<9;++g) all[g]=outputs[g][i];
        verify_expected(scenarios[i],all);
      }
      // Verify the actual output arrangement on a 2 graph x 3 point multi-graph batch.
      // This avoids silently assuming a particular flattening convention.
      PACEVAL_HANDLE pair[]{graphs.active[0],graphs.active[1]};
      double check_values[NVAR*3]{};
      for (unsigned i=0;i<3;++i) for (unsigned j=0;j<NVAR;++j) check_values[i*NVAR+j]=scenarios[i][j];
      double checks[6]{},lo[6]{},hi[6]{}; int errs[6]{};
      bool bad=paceval_dGetMultipleComputationsResultsExt(pair,2,check_values,3,checks,lo,hi,errs);
      require(!bad,"Multi-graph API returned an error");
      for (int err: errs) require(err==0,"Multi-graph per-result error");
      bool graph_major=true,point_major=true;
      for (unsigned g=0;g<2;++g) for (unsigned i=0;i<3;++i) {
        double target=outputs[g][i];
        graph_major &= std::abs(checks[g*3+i]-target)<1e-10;
        point_major &= std::abs(checks[i*2+g]-target)<1e-10;
      }
      require(graph_major || point_major,"Multi-graph layout did not match scalar batch paths");
      const std::string path=root+"/results/local_sdk_regenerated_grid.csv";
      std::ofstream out(path);
      require(out.good(),"Cannot create local results file");
      out<<"x,y,z,q_v1,q_v2,margin_v1,margin_v2,dx_v1,dx_v2,dz_v2,radius_v1,q_tinc_lower,q_tinc_upper\n";
      out<<std::setprecision(17);
      for (unsigned i=0;i<scenarios.size();++i){
        out<<scenarios[i][0]<<','<<scenarios[i][1]<<','<<scenarios[i][2];
        for (unsigned g=0;g<9;++g) out<<','<<outputs[g][i];
        out<<','<<lower[0][i]<<','<<upper[0][i]<<'\n';
      }
      require(out.good(),"Failed to write results");
      std::cout<<"Completed original local paceval SDK execution for "<<scenarios.size()
               <<" synthetic scenarios with "<<graphs.active.size()<<" graphs.\n"
               <<"Multi-graph layout: "<<(graph_major?"graph-major":"point-major")<<"\n";
    }catch(...){ paceval_FreeLibrary(); throw; }
    require(paceval_FreeLibrary(),"paceval_FreeLibrary failed");
    return 0;
  } catch(const std::exception& e) {
    std::cerr<<"matrix_precision_paceval: "<<e.what()<<"\n";
    return 2;
  }
}
