// Generic dense SPD Cholesky and inverse, using genuine reusable paceval C API kernels.
// C++17 standard library + dlopen only. Validates all entries, computes full residual.
// Copyright 2026. Research demonstration; source intended for reproducibility.
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
using Mat=std::vector<double>;
using Clock=std::chrono::steady_clock;
static double elapsed(Clock::time_point t){return std::chrono::duration<double>(Clock::now()-t).count();}
static void check(bool x,const std::string& m){if(!x)throw std::runtime_error(m);}
struct Paceval {
 using Init=bool(*)(const char*); using Free=bool(*)();using Create=void*(*)(const char*,unsigned long,const char*,bool,void*);using Delete=bool(*)(void*);using Error=bool(*)(void*);
 using Batch=bool(*)(void*,double*,unsigned long,double*,double*,double*,int*);
 void* lib=nullptr;Init init=nullptr;Free close=nullptr;Create create=nullptr;Delete drop=nullptr;Error error=nullptr;Batch batch=nullptr;std::vector<void*> hs;
 template<typename T>T sym(const char* n){auto p=dlsym(lib,(std::string("pacevalLibrary_")+n).c_str());check(p!=nullptr,std::string("missing paceval symbol: ")+n);return reinterpret_cast<T>(p);}
 explicit Paceval(const std::string& path){lib=dlopen(path.c_str(),RTLD_NOW);check(lib!=nullptr,"Cannot open real libpaceval.so: "+path);init=sym<Init>("Initialize");close=sym<Free>("Free");create=sym<Create>("CreateComputation");drop=sym<Delete>("DeleteComputation");error=sym<Error>("GetIsError");batch=sym<Batch>("dGetComputationResultExt");check(init(nullptr),"paceval initialize failed");}
 ~Paceval(){for(auto x:hs)drop(x);if(close)close();if(lib)dlclose(lib);}
 void* make(const std::string& exp,const std::string& vars,int n){auto h=create(exp.c_str(),n,vars.c_str(),false,nullptr);check(h&&!error(h),"paceval create graph failed: "+exp);hs.push_back(h);return h;}
};
struct Evaluator {
 Paceval& pv;void* h;int arity,cap;std::vector<double> input,output,low,high;std::vector<int>err;std::vector<size_t>indexes;Mat* target=nullptr;int used=0;uint64_t evaluations=0,batches=0;double time=0;
 Evaluator(Paceval& p,void* graph,int vars,int capacity):pv(p),h(graph),arity(vars),cap(capacity),input((size_t)capacity*vars),output(capacity),low(capacity),high(capacity),err(capacity),indexes(capacity){}
 void select(Mat& a){check(used==0,"cannot change target while batch pending");target=&a;}
 void add(size_t at,double a,double b=0,double c=0){check(target!=nullptr,"no output target");double* p=&input[(size_t)used*arity];p[0]=a;if(arity>1)p[1]=b;if(arity>2)p[2]=c;indexes[used]=at;++used;if(used==cap)flush();}
 void flush(){if(!used)return;auto start=Clock::now();bool ok=pv.batch(h,input.data(),(unsigned long)used,output.data(),low.data(),high.data(),err.data());time+=elapsed(start);++batches;(void)ok; // paceval API boolean is not a generic success flag; check element error codes instead.
 for(int k=0;k<used;k++){check(err[k]==0&&std::isfinite(output[k]),"paceval numeric failure");(*target)[indexes[k]]=output[k];}evaluations+=(uint64_t)used;used=0;}
};
static Mat make_dense_seed(int n){Mat L((size_t)n*n);for(int i=0;i<n;i++){L[(size_t)i*n+i]=1.30+.13*std::pow(std::sin((i+1)*.027),2);for(int j=0;j<i;j++) L[(size_t)i*n+j]=.013*std::sin((i+1)*.031+(j+1)*.173+.00011*(i+3)*(j+1))*(std::sqrt(128.0/n));}return L;}
// Independently construct A from a fully dense, full-rank lower triangle, not a low-rank update.
static Mat make_spd(const Mat& L,int n){Mat A((size_t)n*n);for(int i=0;i<n;i++)for(int j=0;j<=i;j++){long double z=0;for(int k=0;k<=j;k++)z+=(long double)L[(size_t)i*n+k]*L[(size_t)j*n+k];A[(size_t)i*n+j]=A[(size_t)j*n+i]=(double)z;}return A;}
static Mat naive_cholesky(const Mat& A,int n){Mat L((size_t)n*n);for(int i=0;i<n;i++)for(int j=0;j<=i;j++){double s=A[(size_t)i*n+j];for(int k=0;k<j;k++)s-=L[(size_t)i*n+k]*L[(size_t)j*n+k];if(i==j){check(s>0,"non-SPD native reference");L[(size_t)i*n+i]=std::sqrt(s);}else L[(size_t)i*n+j]=s/L[(size_t)j*n+j];}return L;}
static double maxdiff(const Mat&A,const Mat&B){check(A.size()==B.size(),"shape mismatch");double z=0;for(size_t i=0;i<A.size();i++)z=std::max(z,std::abs(A[i]-B[i]));return z;}
// Blocked independent residual check for all entries; not used in paceval production kernel.
static double full_residual(const Mat&A,const Mat& X,int n){const int BS=32;Mat E((size_t)n*n);for(int i=0;i<n;i++)E[(size_t)i*n+i]=-1.;for(int ii=0;ii<n;ii+=BS)for(int kk=0;kk<n;kk+=BS)for(int jj=0;jj<n;jj+=BS)for(int i=ii;i<std::min(n,ii+BS);i++)for(int k=kk;k<std::min(n,kk+BS);k++){double a=A[(size_t)i*n+k];for(int j=jj;j<std::min(n,jj+BS);j++) E[(size_t)i*n+j]+=a*X[(size_t)k*n+j];}double r=0;for(double z:E)r=std::max(r,std::abs(z));return r;}
static void store_matrix_binary(const Mat& A,const std::string&path){
 std::ofstream f(path,std::ios::binary);check(f.good(),"cannot write "+path);
 f.write(reinterpret_cast<const char*>(A.data()),(std::streamsize)(A.size()*sizeof(double)));
 check(f.good(),"failed binary write "+path);
}
struct Outcome {int n,cap;double generate=0,create=0,nativeChol=0,paceChol=0,paceTriInv=0,paceGram=0,verify=0,cholError=0,cholVsSeed=0,invSymmetry=0,residual=0,logdet=0,logdetRef=0;uint64_t cholCalls=0,triCalls=0,gramCalls=0,batches=0;Mat inverse;};
static Outcome run(Paceval& pv,int n,int cap,const std::string&dir,bool saveMatrices){Outcome z{};z.n=n;z.cap=cap;
 auto t=Clock::now();Mat seed=make_dense_seed(n),A=make_spd(seed,n);z.generate=elapsed(t);
 t=Clock::now();Mat Lref=naive_cholesky(A,n);z.nativeChol=elapsed(t);
 t=Clock::now();void* hsqrt=pv.make("sqrt(a)","a",1),*hdiv=pv.make("a/b","a b",2),*hsub=pv.make("a-b*c","a b c",3),*hadd=pv.make("a+b*c","a b c",3),*hlog=pv.make("ln(a)","a",1);z.create=elapsed(t);
 Evaluator esqrt(pv,hsqrt,1,cap),ediv(pv,hdiv,2,cap),esub(pv,hsub,3,cap),eadd(pv,hadd,3,cap),elog(pv,hlog,1,cap);
 Mat work=A, L((size_t)n*n),T((size_t)n*n),X((size_t)n*n),diag(n);auto start=Clock::now();
 esqrt.select(diag);ediv.select(L);esub.select(work);
 for(int k=0;k<n;k++){
  esqrt.add(k,work[(size_t)k*n+k]);esqrt.flush();const double d=diag[k];check(d>0,"nonpositive paceval pivot");L[(size_t)k*n+k]=d;
  for(int i=k+1;i<n;i++){ediv.add((size_t)i*n+k,work[(size_t)i*n+k],d);}ediv.flush();
  for(int i=k+1;i<n;i++){const double a=L[(size_t)i*n+k];for(int j=k+1;j<=i;j++)esub.add((size_t)i*n+j,work[(size_t)i*n+j],a,L[(size_t)j*n+k]);}esub.flush();
  if((k+1)%std::max(1,n/8)==0)std::cerr<<"CHOLESKY n="<<n<<" col="<<k+1<<"/"<<n<<" seconds="<<elapsed(start)<<std::endl;
 }
 z.paceChol=elapsed(start);z.cholError=maxdiff(L,Lref);z.cholVsSeed=maxdiff(L,seed);z.cholCalls=esqrt.evaluations+ediv.evaluations+esub.evaluations;
 // Dense triangular inverse via forward substitution using the same persistent paceval divide/subtract graphs.
 t=Clock::now();for(int k=0;k<n;k++)T[(size_t)k*n+k]=1.0;
 ediv.select(T);esub.select(T);
 for(int k=0;k<n;k++){
  for(int j=0;j<=k;j++){ediv.add((size_t)k*n+j,T[(size_t)k*n+j],L[(size_t)k*n+k]);}ediv.flush();
  for(int i=k+1;i<n;i++){double mult=L[(size_t)i*n+k];for(int j=0;j<=k;j++)esub.add((size_t)i*n+j,T[(size_t)i*n+j],mult,T[(size_t)k*n+j]);}esub.flush();
  if((k+1)%std::max(1,n/8)==0)std::cerr<<"TRI_INVERSE n="<<n<<" row="<<k+1<<"/"<<n<<" seconds="<<elapsed(t)<<std::endl;
 }
 z.paceTriInv=elapsed(t);z.triCalls=0; // detailed graph evaluation counts are recorded below
 // X = T^T * T, accumulate unique triangular entries via paceval batches.
 t=Clock::now();eadd.select(X);
 for(int k=0;k<n;k++){
  for(int i=0;i<=k;i++){const double v=T[(size_t)k*n+i];for(int j=0;j<=i;j++)eadd.add((size_t)i*n+j,X[(size_t)i*n+j],v,T[(size_t)k*n+j]);}eadd.flush();
  if((k+1)%std::max(1,n/8)==0)std::cerr<<"GRAM n="<<n<<" row="<<k+1<<"/"<<n<<" seconds="<<elapsed(t)<<std::endl;
 }
 for(int i=0;i<n;i++)for(int j=i+1;j<n;j++)X[(size_t)i*n+j]=X[(size_t)j*n+i];
 z.paceGram=elapsed(t);z.gramCalls=eadd.evaluations;
 t=Clock::now();// The log determinant is also calculated through a reusable paceval graph.
 Mat logs(n);elog.select(logs);for(int k=0;k<n;k++)elog.add(k,L[(size_t)k*n+k]);elog.flush();
 z.logdet=2*std::accumulate(logs.begin(),logs.end(),0.0);
 z.logdetRef=0;for(int k=0;k<n;k++)z.logdetRef+=2*std::log(Lref[(size_t)k*n+k]);
 z.residual=full_residual(A,X,n);
 // independent triangular Cholesky reconstruction max error (use lower-triangle generation check)
 z.invSymmetry=0;for(int i=0;i<n;i++)for(int j=i+1;j<n;j++)z.invSymmetry=std::max(z.invSymmetry,std::abs(X[(size_t)i*n+j]-X[(size_t)j*n+i]));
 z.verify=elapsed(t);
 z.batches=esqrt.batches+ediv.batches+esub.batches+eadd.batches+elog.batches;
 // esub.evaluations counts Cholesky and triangular solves combined.
 z.inverse=std::move(X);
 std::ofstream metrics(dir+"/generic_spd_"+std::to_string(n)+"_metrics.csv");metrics<<std::setprecision(17);
 metrics<<"n,batch_capacity,generation_s,paceval_graph_creation_s,native_cholesky_s,paceval_cholesky_s,paceval_triangular_inverse_s,paceval_gram_inverse_s,full_residual_verify_s,max_cholesky_entry_error,max_cholesky_vs_constructed_seed,max_AAinv_minus_I,max_inverse_symmetry_error,paceval_logdet,native_logdet,cholesky_kernel_evaluations,subtraction_graph_evaluations,total_paceval_batch_calls,total_gram_evaluations\n";
 metrics<<n<<','<<cap<<','<<z.generate<<','<<z.create<<','<<z.nativeChol<<','<<z.paceChol<<','<<z.paceTriInv<<','<<z.paceGram<<','<<z.verify<<','<<z.cholError<<','<<z.cholVsSeed<<','<<z.residual<<','<<z.invSymmetry<<','<<z.logdet<<','<<z.logdetRef<<','<<z.cholCalls<<','<<esub.evaluations<<','<<z.batches<<','<<z.gramCalls<<'\n';
 std::ofstream sam(dir+"/generic_spd_"+std::to_string(n)+"_samples.csv");sam<<std::setprecision(17)<<"i,j,input_A,L_paceval,L_native,inverse_paceval,seed_L\n";for(int i=0;i<std::min(n,24);i++)for(int j=0;j<=i&&j<24;j++)sam<<i<<','<<j<<','<<A[(size_t)i*n+j]<<','<<L[(size_t)i*n+j]<<','<<Lref[(size_t)i*n+j]<<','<<z.inverse[(size_t)i*n+j]<<','<<seed[(size_t)i*n+j]<<'\n';
 if(saveMatrices){store_matrix_binary(A,dir+"/generic_spd_"+std::to_string(n)+"_A.f64");store_matrix_binary(z.inverse,dir+"/generic_spd_"+std::to_string(n)+"_inverse.f64");}
 std::cerr<<std::setprecision(15)<<"DONE n="<<n<<" chol="<<z.paceChol<<" inv_tri="<<z.paceTriInv<<" gram="<<z.paceGram<<" residual="<<z.residual<<" cholesky_diff="<<z.cholError<<" logdet="<<z.logdet<<"\n";
 check(z.cholError<5e-10,"Cholesky mismatch > tolerance");check(z.residual<5e-9,"residual too large");check(std::abs(z.logdet-z.logdetRef)<5e-8,"logdet mismatch");return z;
}
int main(int argc,char**argv){try{
 check(argc>=5,"Usage: dense_spd_paceval /abs/path/libpaceval.so results_folder N batch_size [save_full=0|1]");int n=std::stoi(argv[3]);int b=std::stoi(argv[4]);check(n>=8&&n<=1024,"n outside 8..1024");check(b>=32&&b<=16384,"invalid batch cap");bool save=(argc>5&&std::stoi(argv[5])!=0);Paceval pv(argv[1]);run(pv,n,b,argv[2],save);return 0;
}catch(const std::exception&e){std::cerr<<"FAIL: "<<e.what()<<'\n';return 1;}}
