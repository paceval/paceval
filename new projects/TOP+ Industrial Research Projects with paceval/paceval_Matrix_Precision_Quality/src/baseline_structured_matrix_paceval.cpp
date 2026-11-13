// Industrial matrix study: exact structured SPD inverse, covariance rotation, log determinant.
// The scientific test uses genuine paceval library execution graphs and batched evaluation.
// C++ standard library + dynamic loading only, no third-party math libraries in this executable.
#include <algorithm>
#include <array>
#include <chrono>
#include <cmath>
#include <cstdint>
#include <dlfcn.h>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <stdexcept>
#include <string>
#include <vector>
using Clock=std::chrono::steady_clock;
using Mat=std::vector<double>;
static double seconds(Clock::time_point t){return std::chrono::duration<double>(Clock::now()-t).count();}
static void ensure(bool ok,const std::string& why){if(!ok)throw std::runtime_error(why);}
class PV{
 using Init=bool(*)(const char*);using Shutdown=bool(*)();using Create=void*(*)(const char*,unsigned long,const char*,bool,void*);using Delete=bool(*)(void*);using Error=bool(*)(void*);
 using Batch=bool(*)(void*,double*,unsigned long,double*,double*,double*,int*);using Multi=bool(*)(void**,unsigned long,double*,unsigned long,double*,double*,double*,int*);
 void* lib=nullptr;Init init=nullptr;Shutdown free=nullptr;Create create=nullptr;Delete del=nullptr;Error error=nullptr;Batch batch=nullptr;Multi multi=nullptr;std::vector<void*> all;
 template<class T>T symbol(const char* name){std::string n="pacevalLibrary_"+std::string(name);auto p=dlsym(lib,n.c_str());ensure(p!=nullptr,"Missing "+n);return reinterpret_cast<T>(p);}
 public:
 explicit PV(std::string path){lib=dlopen(path.c_str(),RTLD_NOW);ensure(lib!=nullptr,"Cannot load paceval library: "+path);init=symbol<Init>("Initialize");free=symbol<Shutdown>("Free");create=symbol<Create>("CreateComputation");del=symbol<Delete>("DeleteComputation");error=symbol<Error>("GetIsError");batch=symbol<Batch>("dGetComputationResultExt");multi=symbol<Multi>("dGetMultipleComputationsResultsExt");ensure(init(nullptr),"Initialize failed");}
 ~PV(){for(void* h:all)del(h);if(free)free();if(lib)dlclose(lib);}
 void* make(const std::string& expr,const std::string& vars,int n){void* h=create(expr.c_str(),n,vars.c_str(),false,nullptr);ensure(h&&!error(h),"paceval expression creation failed: "+expr);all.push_back(h);return h;}
 std::vector<double> values(void* h,const std::vector<double>& inputs,int vars,int limit=256){ensure(!inputs.empty()&&inputs.size()%vars==0,"bad batch input shape");size_t count=inputs.size()/vars;std::vector<double> output(count),low(limit),high(limit);std::vector<int> errs(limit);for(size_t off=0;off<count;off+=limit){int rows=(int)std::min<size_t>(limit,count-off);(void)batch(h,const_cast<double*>(inputs.data()+off*vars),rows,output.data()+off,low.data(),high.data(),errs.data());for(int k=0;k<rows;k++)ensure(errs[k]==0&&std::isfinite(output[off+k]),"paceval batch error");}return output;}
 std::vector<double> multiValues(const std::vector<void*>& handles,const std::vector<double>& inputs,int vars,int limit=64){ensure(inputs.size()%vars==0,"bad multi batch shape");auto h=handles;size_t cnt=inputs.size()/vars,G=h.size();std::vector<double> allOut(cnt*G),out(G*limit),lo(G*limit),hi(G*limit);std::vector<int> errors(G*limit);for(size_t off=0;off<cnt;off+=limit){int rows=(int)std::min<size_t>(limit,cnt-off);(void)multi(h.data(),G,const_cast<double*>(inputs.data()+off*vars),rows,out.data(),lo.data(),hi.data(),errors.data());for(size_t g=0;g<G;g++)for(int r=0;r<rows;r++){size_t idx=g*rows+r;ensure(errors[idx]==0&&std::isfinite(out[idx]),"paceval multigraph batch error");allOut[g*cnt+off+r]=out[idx];}}return allOut;}
};
static constexpr int K=3;
struct Data {int n;Mat D,U,A;};
static Data createData(int n){Data p{n,Mat(n),Mat((size_t)n*K),Mat((size_t)n*n)};
 for(int i=0;i<n;i++){p.D[i]=1.15+.13*std::pow(std::sin((i+1)*.173),2);for(int a=0;a<K;a++)p.U[(size_t)i*K+a]=.03*std::sin((i+1)*(a+2)*.031)+.02*std::cos((i+1)*(a+1)*.017);}
 for(int i=0;i<n;i++)for(int j=0;j<n;j++){double sum=(i==j?p.D[i]:0.);for(int k=0;k<K;k++)sum+=p.U[(size_t)i*K+k]*p.U[(size_t)j*K+k];p.A[(size_t)i*n+j]=sum;}
 return p;
}
static std::array<double,9> nativeInverse3(const std::array<double,9>& M){double aug[3][6]={};for(int i=0;i<3;i++)for(int j=0;j<3;j++){aug[i][j]=M[i*3+j];aug[i][3+j]=(i==j?1.0:0.0);}for(int j=0;j<3;j++){int pivot=j;for(int k=j+1;k<3;k++)if(std::abs(aug[k][j])>std::abs(aug[pivot][j]))pivot=k;ensure(std::abs(aug[pivot][j])>1e-15,"Singular core");for(int k=0;k<6;k++)std::swap(aug[j][k],aug[pivot][k]);double scale=aug[j][j];for(int k=0;k<6;k++)aug[j][k]/=scale;for(int i=0;i<3;i++)if(i!=j){double mult=aug[i][j];for(int k=0;k<6;k++)aug[i][k]-=mult*aug[j][k];}}
 std::array<double,9> inv{};for(int i=0;i<3;i++)for(int j=0;j<3;j++)inv[i*3+j]=aug[i][3+j];return inv;}
static std::array<double,9> coreMat(const Data& d){std::array<double,9>M{};for(int a=0;a<3;a++)for(int b=0;b<3;b++)M[3*a+b]=(a==b?1.:0.);for(int i=0;i<d.n;i++)for(int a=0;a<3;a++)for(int b=0;b<3;b++)M[3*a+b]+=d.U[(size_t)i*3+a]*d.U[(size_t)i*3+b]/d.D[i];return M;}
static double det3(const std::array<double,9>& m){return m[0]*(m[4]*m[8]-m[5]*m[7])-m[1]*(m[3]*m[8]-m[5]*m[6])+m[2]*(m[3]*m[7]-m[4]*m[6]);}
struct Measures{std::string method;int n;long long rows;int graphs;double createSec,evalSec,baselineSec,maxError,residual;};
static Measures covarianceRotation(PV& pv,const Data& d,const std::string& out){const int n=d.n;ensure(n%2==0,"even n required");
 const std::string e="r0*c0*s00+r0*c1*s01+r1*c0*s10+r1*c1*s11";auto begin=Clock::now();void* h=pv.make(e,"r0 r1 c0 c1 s00 s01 s10 s11",8);double createT=seconds(begin);
 Mat angles(n/2),cs(n/2),sn(n/2);for(int t=0;t<n/2;t++){angles[t]=.02+(.5*std::sin((t+1)*.013));cs[t]=std::cos(angles[t]);sn[t]=std::sin(angles[t]);}
 // Independent two-stage reference: B = R A, C = B R^T
 Mat stage((size_t)n*n),reference((size_t)n*n),result((size_t)n*n);auto t=Clock::now();for(int p=0;p<n;p+=2)for(int j=0;j<n;j++){double c=cs[p/2],s=sn[p/2];stage[(size_t)p*n+j]=c*d.A[(size_t)p*n+j]-s*d.A[(size_t)(p+1)*n+j];stage[(size_t)(p+1)*n+j]=s*d.A[(size_t)p*n+j]+c*d.A[(size_t)(p+1)*n+j];}
 for(int i=0;i<n;i++)for(int p=0;p<n;p+=2){double c=cs[p/2],s=sn[p/2];reference[(size_t)i*n+p]=c*stage[(size_t)i*n+p]-s*stage[(size_t)i*n+p+1];reference[(size_t)i*n+p+1]=s*stage[(size_t)i*n+p]+c*stage[(size_t)i*n+p+1];}
 double baseT=seconds(t);
 std::vector<double> inputs;inputs.reserve(256*8);t=Clock::now();int batch=256;for(int index=0;index<n*n;index+=batch){int rows=std::min(batch,n*n-index);inputs.clear();for(int r=0;r<rows;r++){int i=(index+r)/n,j=(index+r)%n;int ip=i&~1,jp=j&~1;double a=(i%2==0?cs[ip/2]:sn[ip/2]),b=(i%2==0?-sn[ip/2]:cs[ip/2]);double c=(j%2==0?cs[jp/2]:sn[jp/2]),dd=(j%2==0?-sn[jp/2]:cs[jp/2]);inputs.insert(inputs.end(),{a,b,c,dd,d.A[(size_t)ip*n+jp],d.A[(size_t)ip*n+jp+1],d.A[(size_t)(ip+1)*n+jp],d.A[(size_t)(ip+1)*n+jp+1]});}
 auto values=pv.values(h,inputs,8,batch);std::copy(values.begin(),values.end(),result.begin()+index);}double paceT=seconds(t);
 double err=0,maxAsym=0,trace0=0,trace1=0;for(int i=0;i<n;i++){trace0+=d.A[(size_t)i*n+i];trace1+=result[(size_t)i*n+i];for(int j=0;j<n;j++){size_t idx=(size_t)i*n+j;err=std::max(err,std::abs(result[idx]-reference[idx]));maxAsym=std::max(maxAsym,std::abs(result[idx]-result[(size_t)j*n+i]));}}double trerr=std::abs(trace0-trace1);ensure(err<1e-11&&maxAsym<1e-11&&trerr<1e-9,"covariance verification failed");
 std::ofstream f(out+"/covariance_"+std::to_string(n)+"_samples.csv");f<<"i,j,paceval,reference,abs_error\n"<<std::setprecision(17);for(int i=0;i<6;i++)for(int j=0;j<6;j++){size_t id=(size_t)i*n+j;f<<i<<','<<j<<','<<result[id]<<','<<reference[id]<<','<<std::abs(result[id]-reference[id])<<'\n';}
 std::cerr<<"COV n="<<n<<" cells="<<(long long)n*n<<" graphs=1 create="<<createT<<" pace="<<paceT<<" native="<<baseT<<" maxErr="<<err<<" sym="<<maxAsym<<" trace="<<trerr<<"\n";
 return {"covariance_rotation_block_2x2",n,(long long)n*n,1,createT,paceT,baseT,err,std::max(maxAsym,trerr)};
}
static Measures structuredInverse(PV& pv,const Data& d,const std::string& out){const int n=d.n;auto start=Clock::now();void* core=pv.make("u*v/d","u v d",3);std::vector<double> input;input.reserve((size_t)n*K*K*3);
 for(int a=0;a<K;a++)for(int b=0;b<K;b++)for(int i=0;i<n;i++)input.insert(input.end(),{d.U[(size_t)i*K+a],d.U[(size_t)i*K+b],d.D[i]});
 auto pair=pv.values(core,input,3,256);std::array<double,9>M{};for(int a=0;a<K;a++)for(int b=0;b<K;b++){double s=(a==b?1.:0.);for(int i=0;i<n;i++)s+=pair[(a*K+b)*n+i];M[a*K+b]=s;}
 double det=det3(M);ensure(det>0,"core determinant not positive");
 const std::string vars="s00 s01 s02 s11 s12 s22",de="(s00*(s11*s22-s12*s12)-s01*(s01*s22-s12*s02)+s02*(s01*s12-s11*s02))";
 const char* numerators[6]={"s11*s22-s12*s12","s02*s12-s01*s22","s01*s12-s02*s11","s00*s22-s02*s02","s01*s02-s00*s12","s00*s11-s01*s01"};
 std::vector<void*> hcore;for(auto num:numerators)hcore.push_back(pv.make("("+std::string(num)+")/"+de,vars,6));
 auto cm=pv.multiValues(hcore,{M[0],M[1],M[2],M[4],M[5],M[8]},6,1);std::array<double,9>V={cm[0],cm[1],cm[2],cm[1],cm[3],cm[4],cm[2],cm[4],cm[5]};
 auto Mref=coreMat(d),Ninv=nativeInverse3(Mref);double coreError=0;for(int i=0;i<9;i++){coreError=std::max(coreError,std::abs(M[i]-Mref[i]));coreError=std::max(coreError,std::abs(V[i]-Ninv[i]));}ensure(coreError<1e-12,"3x3 core inverse mismatch");
 const std::string expr="delta/di-((ui0*m00+ui1*m01+ui2*m02)*uj0+(ui0*m01+ui1*m11+ui2*m12)*uj1+(ui0*m02+ui1*m12+ui2*m22)*uj2)/(di*dj)";
 void* hinv=pv.make(expr,"delta di dj ui0 ui1 ui2 uj0 uj1 uj2 m00 m01 m02 m11 m12 m22",15);
 void* hlog=pv.make("ln(d)","d",1);void* hlogdet=hlog;double createT=seconds(start);
 std::vector<double> lp=pv.values(hlog,d.D,1,256);double logdet=0;for(auto x:lp)logdet+=x;logdet+=pv.values(hlogdet,{det},1,1)[0];double logdetNative=0;for(auto x:d.D)logdetNative+=std::log(x);logdetNative+=std::log(det3(Mref));ensure(std::abs(logdet-logdetNative)<1e-10,"logdet mismatch");
 Mat inverse((size_t)n*n),native((size_t)n*n);std::vector<double> rowInputs;rowInputs.reserve(256*15);
 auto t=Clock::now();for(int i=0;i<n;i++)for(int j=0;j<n;j++){double v=(i==j?1/d.D[i]:0.);double minus=0;for(int a=0;a<3;a++)for(int b=0;b<3;b++)minus+=d.U[(size_t)i*3+a]*Ninv[a*3+b]*d.U[(size_t)j*3+b];v-=minus/(d.D[i]*d.D[j]);native[(size_t)i*n+j]=v;}double baseT=seconds(t);
 t=Clock::now();const int batch=256;for(int index=0;index<n*n;index+=batch){int rows=std::min(batch,n*n-index);rowInputs.clear();for(int r=0;r<rows;r++){int i=(index+r)/n,j=(index+r)%n;rowInputs.insert(rowInputs.end(),{i==j?1.:0.,d.D[i],d.D[j],d.U[(size_t)i*3],d.U[(size_t)i*3+1],d.U[(size_t)i*3+2],d.U[(size_t)j*3],d.U[(size_t)j*3+1],d.U[(size_t)j*3+2],V[0],V[1],V[2],V[4],V[5],V[8]});}auto res=pv.values(hinv,rowInputs,15,batch);std::copy(res.begin(),res.end(),inverse.begin()+index);}double paceT=seconds(t);
 // True full N x N inverse verification via A*X using D+U*U^T factorization.
 // C=A X: compute W=U^T X in O(K*N^2), then C=D X+U W. This evaluates all N^2 residuals.
 double residual=0,err=0,asym=0;std::vector<double> UTX((size_t)3*n,0.);
 for(int a=0;a<3;a++)for(int j=0;j<n;j++){double sum=0.;for(int i=0;i<n;i++)sum+=d.U[(size_t)i*3+a]*inverse[(size_t)i*n+j];UTX[(size_t)a*n+j]=sum;}
 for(int i=0;i<n;i++)for(int j=0;j<n;j++){size_t id=(size_t)i*n+j;double prod=d.D[i]*inverse[id];for(int a=0;a<3;a++)prod+=d.U[(size_t)i*3+a]*UTX[(size_t)a*n+j];residual=std::max(residual,std::abs(prod-(i==j?1.:0.)));err=std::max(err,std::abs(inverse[id]-native[id]));asym=std::max(asym,std::abs(inverse[id]-inverse[(size_t)j*n+i]));}
 ensure(residual<1e-11&&err<1e-11&&asym<1e-11,"structured inverse verification failed");
 std::ofstream f(out+"/inverse_"+std::to_string(n)+"_samples.csv");f<<std::setprecision(17)<<"i,j,paceval,native,abs_error\n";for(int i=0;i<6;i++)for(int j=0;j<6;j++){size_t id=(size_t)i*n+j;f<<i<<','<<j<<','<<inverse[id]<<','<<native[id]<<','<<std::abs(inverse[id]-native[id])<<'\n';}
 std::ofstream dfile(out+"/structured_spd_input_"+std::to_string(n)+".csv");dfile<<std::setprecision(17)<<"i,D,U0,U1,U2\n";for(int i=0;i<n;i++)dfile<<i<<','<<d.D[i]<<','<<d.U[(size_t)i*3]<<','<<d.U[(size_t)i*3+1]<<','<<d.U[(size_t)i*3+2]<<'\n';
 std::ofstream meta(out+"/structured_spd_diagnostics_"+std::to_string(n)+".txt");meta<<std::setprecision(17)<<"shape="<<n<<" x "<<n<<"\nrank=3\nmodel=A=D+U*transpose(U)\nlogdet_paceval="<<logdet<<"\nlogdet_reference="<<logdetNative<<"\ndeterminant_core="<<det<<"\nmax_core_error="<<coreError<<"\nmax_AAinv_minus_I="<<residual<<"\nmax_inverse_error="<<err<<"\nmax_inverse_asymmetry="<<asym<<"\n";
 std::cerr<<"INV n="<<n<<" cells="<<(long long)n*n<<" graphs=9 create="<<createT<<" pace="<<paceT<<" native="<<baseT<<" maxErr="<<err<<" residual="<<residual<<" logdet="<<logdet<<"\n";
 return {"structured_spd_inverse_rank3",n,(long long)n*n,9,createT,paceT,baseT,err,residual};
}
int main(int argc,char**argv){try{ensure(argc==4,"Usage: structured_matrix_paceval /path/libpaceval.so OUT_DIR 512|1024");int n=std::stoi(argv[3]);ensure(n==512||n==1024,"Only 512 or 1024 supported");PV pv(argv[1]);std::string out=argv[2];std::cerr<<"GENERATE n="<<n<<"\n";Data data=createData(n);std::vector<Measures> m; m.push_back(covarianceRotation(pv,data,out));m.push_back(structuredInverse(pv,data,out));std::ofstream file(out+"/structured_metrics_"+std::to_string(n)+".csv");file<<std::setprecision(17)<<"method,n,paceval_output_entries,graphs,graph_create_seconds,paceval_eval_seconds,native_reference_seconds,max_abs_error,max_residual\n";for(auto &x:m)file<<x.method<<','<<x.n<<','<<x.rows<<','<<x.graphs<<','<<x.createSec<<','<<x.evalSec<<','<<x.baselineSec<<','<<x.maxError<<','<<x.residual<<'\n';std::cerr<<"PASS all "<<n<<" tests\n";return 0;}catch(const std::exception&e){std::cerr<<"FAIL "<<e.what()<<"\n";return 1;}}
