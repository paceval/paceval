// paceval graph runtime for research tools. Only C++17 standard library,
// platform dynamic loader, and the separately licensed paceval shared library.
#pragma once
#include <cstddef>
#include <cmath>
#include <cstdint>
#include <stdexcept>
#include <string>
#include <vector>
#include <utility>
#include <algorithm>
#include "../sdk/paceval_main.h"
#ifdef _WIN32
#define WIN32_LEAN_AND_MEAN
#include <windows.h>
#else
#include <dlfcn.h>
#endif
namespace pv {
inline void require(bool ok,const std::string& msg) { if(!ok) throw std::runtime_error(msg); }
class Runtime {
#ifdef _WIN32
  HMODULE handle_=nullptr;
#else
  void* handle_=nullptr;
#endif
  using Init=bool(*)(const char*);
  using Free=bool(*)();
  using Create=void*(*)(const char*,unsigned long,const char*,bool,void*);
  using Delete=bool(*)(void*);
  using Scalar=double(*)(void*,double*,double*,double*);
  using Batch=bool(*)(void*,double*,unsigned long,double*,double*,double*,int*);
  using Error=bool(*)(void*);
  Init initialize_=nullptr;Free finalize_=nullptr;Create create_=nullptr;
  Delete del_=nullptr;Scalar scalar_=nullptr;Batch batch_=nullptr;Error error_=nullptr;
  std::vector<void*> graphs_;
  std::uint64_t scalar_calls_=0,batch_calls_=0,points_=0;
  void* sym(const char* name) {
    std::string one=std::string("pacevalLibrary_")+name, two=std::string("paceval_")+name;
#ifdef _WIN32
    auto p=GetProcAddress(handle_,one.c_str());if(!p)p=GetProcAddress(handle_,two.c_str());
    require(p!=nullptr,"paceval missing exported symbol: "+one);return reinterpret_cast<void*>(p);
#else
    auto p=dlsym(handle_,one.c_str());if(!p)p=dlsym(handle_,two.c_str());
    require(p!=nullptr,"paceval missing exported symbol: "+one);return p;
#endif
  }
public:
  explicit Runtime(const std::string& path) {
#ifdef _WIN32
    handle_=LoadLibraryA(path.c_str());require(handle_!=nullptr,"paceval DLL not found: "+path);
#else
    handle_=dlopen(path.c_str(),RTLD_NOW|RTLD_LOCAL);
    require(handle_!=nullptr,std::string("paceval shared library not found: ")+path+" ("+(handle_?"":dlerror())+")");
#endif
    initialize_=reinterpret_cast<Init>(sym("Initialize"));
    finalize_=reinterpret_cast<Free>(sym("Free"));
    create_=reinterpret_cast<Create>(sym("CreateComputation"));
    del_=reinterpret_cast<Delete>(sym("DeleteComputation"));
    scalar_=reinterpret_cast<Scalar>(sym("dGetComputationResult"));
    batch_=reinterpret_cast<Batch>(sym("dGetComputationResultExt"));
    error_=reinterpret_cast<Error>(sym("GetIsError"));
    require(initialize_(nullptr),"paceval initialization failed");
  }
  Runtime(const Runtime&)=delete;Runtime& operator=(const Runtime&)=delete;
  ~Runtime() {
    for(auto it=graphs_.rbegin();it!=graphs_.rend();++it)if(*it&&del_)del_(*it);
    if(finalize_)finalize_();
#ifdef _WIN32
    if(handle_)FreeLibrary(handle_);
#else
    if(handle_)dlclose(handle_);
#endif
  }
  std::size_t graph(const std::string& expr,const std::string& variables,unsigned n) {
    auto h=create_(expr.c_str(),n,variables.c_str(),false,nullptr);
    require(h!=nullptr && !error_(h),"paceval graph creation failed: "+expr);
    graphs_.push_back(h);return graphs_.size()-1;
  }
  double eval(std::size_t graph_index,std::vector<double> vars) {
    require(graph_index<graphs_.size(),"paceval invalid graph index");
    double low=0,high=0;
    double val=scalar_(graphs_[graph_index],vars.data(),&low,&high);
    ++scalar_calls_;++points_;
    require(!error_(graphs_[graph_index])&&std::isfinite(val),"paceval scalar failed");
    return val;
  }
  void evaluate(std::size_t graph_index,std::vector<double>& packed, std::size_t nvars,
                std::vector<double>& out,std::size_t chunk=512) {
    require(graph_index<graphs_.size() && nvars>0 && packed.size()%nvars==0,"invalid batch shape");
    const std::size_t n=packed.size()/nvars;out.resize(n);
    std::vector<double> low(chunk),high(chunk);
    std::vector<int> errs(chunk);
    for(std::size_t i=0;i<n;i+=chunk) {
       auto m=static_cast<unsigned long>(std::min(chunk,n-i));
       (void)batch_(graphs_[graph_index],packed.data()+i*nvars,m,out.data()+i,
                    low.data(),high.data(),errs.data());
       ++batch_calls_;points_+=m;
       for(unsigned long j=0;j<m;++j) {
          require(errs[j]==0 && std::isfinite(out[i+j]),
                  "paceval batch error at point "+std::to_string(i+j)+
                  " (code "+std::to_string(errs[j])+")");
       }
    }
  }
  std::uint64_t scalarCalls()const {return scalar_calls_;}
  std::uint64_t batchCalls()const {return batch_calls_;}
  std::uint64_t evaluatedPoints()const {return points_;}
};
} // namespace pv
