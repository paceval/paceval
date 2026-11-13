// Large dense matrix multiplication via genuine paceval. C API (runtime-loaded).
// Reuses one dot-product execution graph per matrix size, batch evaluates output entries.
// Does not create N*N separate computation graphs; independent reference is blocked C++.
#include <algorithm>
#include <chrono>
#include <cmath>
#include <cstdint>
#include <cstdlib>
#include <dlfcn.h>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <limits>
#include <numeric>
#include <stdexcept>
#include <string>
#include <vector>
using Clock=std::chrono::steady_clock;
static double elapsed(Clock::time_point t){return std::chrono::duration<double>(Clock::now()-t).count();}
struct PV{
 using Init=bool(*)(const char*);using Free=bool(*)();using Create=void*(*)(const char*,unsigned long,const char*,bool,void*);
 using Delete=bool(*)(void*);using Error=bool(*)(void*);using Batch=bool(*)(void*,double*,unsigned long,double*,double*,double*,int*);
 void* lib=nullptr;void* handle=nullptr;Init init=nullptr;Free free=nullptr;Create create=nullptr;Delete del=nullptr;Error error=nullptr;Batch batch=nullptr;
 template<class T>T sym(const char* name){std::string s="pacevalLibrary_"+std::string(name);auto p=dlsym(lib,s.c_str());if(!p)throw std::runtime_error("missing symbol "+s);return reinterpret_cast<T>(p);}
 explicit PV(const std::string& path){lib=dlopen(path.c_str(),RTLD_NOW);if(!lib)throw std::runtime_error(dlerror());init=sym<Init>("Initialize");free=sym<Free>("Free");create=sym<Create>("CreateComputation");del=sym<Delete>("DeleteComputation");error=sym<Error>("GetIsError");batch=sym<Batch>("dGetComputationResultExt");if(!init(nullptr))throw std::runtime_error("paceval init failed");}
 ~PV(){if(handle)del(handle);if(free)free();if(lib)dlclose(lib);}
 double setdot(int N){if(handle){del(handle);handle=nullptr;}std::string expr,vars;expr.reserve(N*24);vars.reserve(N*12);for(int k=0;k<N;k++){if(k)expr+='+';expr+="(a"+std::to_string(k)+"*b"+std::to_string(k)+")";if(k)vars+=' ';vars+="a"+std::to_string(k)+" b"+std::to_string(k);}auto t=Clock::now();handle=create(expr.c_str(),2UL*N,vars.c_str(),false,nullptr);double sec=elapsed(t);if(!handle||error(handle))throw std::runtime_error("paceval graph failure N="+std::to_string(N));std::cerr<<"GRAPH N="<<N<<" formula_chars="<<expr.size()<<" variables="<<N*2<<" creation_seconds="<<sec<<"\n";return sec;}
 bool eval(double* input,int count,double* output,double* lo,double* hi,int* err){return batch(handle,input,(unsigned long)count,output,lo,hi,err);}
};
static void fill(std::vector<double>& A,std::vector<double>& B,int N){ // deterministic dense, nontrivial, reproducible
 for(int i=0;i<N;i++)for(int j=0;j<N;j++){int k=i*N+j;A[k]=0.13*std::sin((i+1)*0.173+(j+1)*0.311)+0.08*std::cos((i+1)*(j+2)*0.00017);B[k]=0.15*std::cos((i+1)*0.071-(j+1)*0.229)+0.05*std::sin((i+3)*(j+1)*0.00011);}
}
static void native_blocked(const std::vector<double>& A,const std::vector<double>& B,std::vector<double>& C,int N){
 const int BS=32;std::fill(C.begin(),C.end(),0.);
 for(int ii=0;ii<N;ii+=BS)for(int kk=0;kk<N;kk+=BS)for(int jj=0;jj<N;jj+=BS)
 for(int i=ii;i<std::min(N,ii+BS);i++)for(int k=kk;k<std::min(N,kk+BS);k++){
 const double x=A[i*N+k];for(int j=jj;j<std::min(N,jj+BS);j++)C[i*N+j]+=x*B[k*N+j];}
}
static double ref_long(const std::vector<double>& A,const std::vector<double>& B,int N,int r,int c){long double acc=0;for(int k=0;k<N;k++)acc+=(long double)A[(size_t)r*N+k]*B[(size_t)k*N+c];return (double)acc;}
static std::vector<size_t> selected_positions(int N,int target){
 size_t total=(size_t)N*N;std::vector<size_t> v;if(target>=int(total)){v.resize(total);std::iota(v.begin(),v.end(),size_t(0));return v;}
 v.reserve(target);for(int i=0;i<target;i++){size_t x=((uint64_t)i*2654435761ULL+2246822519ULL)%total;v.push_back(x);}return v;
}
struct Metric{int N;std::string mode;size_t computed;size_t total;int batch;double createS,nativeS,evalS,maxAbs,maxRel,maxHighPrecision;int flags;};
static Metric run(PV& pv,int N,const std::string& mode,int sampleCount,int batchSize,const std::string& results){
 std::vector<double> A((size_t)N*N),B((size_t)N*N),C((size_t)N*N);fill(A,B,N);
 auto start=Clock::now();native_blocked(A,B,C,N);double nativeS=elapsed(start);
 double createS=pv.setdot(N);const int nv=2*N;
 auto cells=selected_positions(N,mode=="full"?N*N:sampleCount);const size_t rows=cells.size();
 std::vector<double> in((size_t)batchSize*nv),out(batchSize),lo(batchSize),hi(batchSize);std::vector<int> err(batchSize);
 std::ofstream sample(results+"/check_"+std::to_string(N)+"_"+mode+".csv");sample<<std::setprecision(17)<<"row,col,paceval,native,abs_error,relative_error\n";
 double worst=0,worstRel=0,worstHp=0;int flags=0;
 // warm up: exactly one point not included in timings
 {size_t id=cells[0],i=id/N,j=id%N;for(int k=0;k<N;k++){in[2*k]=A[i*N+k];in[2*k+1]=B[(size_t)k*N+j];}{bool returned=pv.eval(in.data(),1,out.data(),lo.data(),hi.data(),err.data());std::cerr<<"WARMUP return="<<returned<<" err="<<err[0]<<" value="<<out[0]<<"\n";if(err[0]!=0 || !std::isfinite(out[0]))throw std::runtime_error("warmup failed");}}
 auto bench=Clock::now();
 for(size_t first=0;first<rows;first+=batchSize){int count=std::min<size_t>(batchSize,rows-first);
 for(int m=0;m<count;m++){size_t id=cells[first+m],r=id/N,c=id%N;double* p=in.data()+(size_t)m*nv;for(int k=0;k<N;k++){p[2*k]=A[r*N+k];p[2*k+1]=B[(size_t)k*N+c];}}
 bool ok=pv.eval(in.data(),count,out.data(),lo.data(),hi.data(),err.data());(void)ok;
 for(int m=0;m<count;m++){if(err[m]||!std::isfinite(out[m]))throw std::runtime_error("paceval error at result "+std::to_string(first+m));size_t id=cells[first+m],r=id/N,c=id%N;double aerr=std::abs(out[m]-C[id]);worst=std::max(worst,aerr);worstRel=std::max(worstRel,aerr/std::max(1e-12,std::abs(C[id])));if((first+m)%std::max<size_t>(1,rows/32)==0){double hp=ref_long(A,B,N,(int)r,(int)c);worstHp=std::max(worstHp,std::abs(hp-out[m]));}if(aerr>1e-9)flags++;if((first+m)<64||((first+m)%std::max<size_t>(1,rows/32)==0))sample<<r<<','<<c<<','<<out[m]<<','<<C[id]<<','<<aerr<<','<<aerr/std::max(1e-12,std::abs(C[id]))<<'\n';}
 if(rows>5000 && ((first+count) % std::max<size_t>(1,rows/10)) < (size_t)batchSize)std::cerr<<"PROGRESS N="<<N<<" "<<first+count<<"/"<<rows<<" seconds="<<elapsed(bench)<<"\n";
 }
 double evalS=elapsed(bench);std::cerr<<std::setprecision(12)<<"RESULT N="<<N<<" mode="<<mode<<" computed="<<rows<<"/"<<(size_t)N*N<<" batch="<<batchSize<<" create_s="<<createS<<" native_full_s="<<nativeS<<" paceval_s="<<evalS<<" max_abs="<<worst<<" max_hp="<<worstHp<<" flags="<<flags<<"\n";
 return {N,mode,rows,(size_t)N*N,batchSize,createS,nativeS,evalS,worst,worstRel,worstHp,flags};
}
int main(int argc,char** argv){try{
 if(argc<5){std::cerr<<"Usage: large_matrix_paceval /path/libpaceval.so OUTPUT_DIR N full|sample [samples] [batch=32]\n";return 2;}
 std::string file=argv[1],dir=argv[2];int N=std::stoi(argv[3]);std::string mode=argv[4];int samples=argc>5?std::stoi(argv[5]):1024,batch=argc>6?std::stoi(argv[6]):32;
 if(N<2||N>2048||batch<1||batch>512||(mode!="full"&&mode!="sample"))throw std::runtime_error("invalid arguments");
 PV pv(file);auto m=run(pv,N,mode,samples,batch,dir);std::ofstream out(dir+"/metrics_"+std::to_string(N)+"_"+mode+".csv");out<<"matrix_size,mode,paceval_output_entries,total_output_entries,batch_size,creation_seconds,native_full_seconds,paceval_eval_seconds,max_absolute_error,max_relative_error,max_error_vs_long_double,errors_over_1e-9\n";out<<std::setprecision(15)<<m.N<<","<<m.mode<<","<<m.computed<<","<<m.total<<","<<m.batch<<","<<m.createS<<","<<m.nativeS<<","<<m.evalS<<","<<m.maxAbs<<","<<m.maxRel<<","<<m.maxHighPrecision<<","<<m.flags<<"\n";
 return m.flags?1:0;
 }catch(const std::exception& e){std::cerr<<"ERROR "<<e.what()<<"\n";return 1;}}
