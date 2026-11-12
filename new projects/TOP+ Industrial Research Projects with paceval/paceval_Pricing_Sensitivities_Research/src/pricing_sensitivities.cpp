// WP-020: Reusable Black-Scholes-Merton mathematical kernels with paceval.
// This is a synthetic numerical research demonstrator, not financial advice.
// The original upstream paceval_main.cpp/.h keep their copyright notices.
// paceval computes the TEN distinct price/Greek formulas through real SDK
// computation handles. The host deliberately computes normal CDF/PDF inputs
// using the platform erfc/exp: the SDK is not claimed to implement an N() CDF.
// This split is explicit in the README and research whitepaper.
#include "paceval_main.h"
#include <array>
#include <algorithm>
#include <cmath>
#include <filesystem>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <stdexcept>
#include <string>
#include <vector>
namespace fs=std::filesystem;
namespace {
constexpr double PI=3.141592653589793238462643383279502884;
constexpr int NX=61, NY=41, BATCH=32;
// Strict fixed input ordering is part of the versioned contract.
constexpr int NV=11;
constexpr const char* vars="S K T r q sig n1 n2 nm1 nm2 pdf";
// theta is calendar-time decay (minus partial derivative in remaining T),
// vega is per unit volatility (= 100 percentage points), rho per unit rate.
const std::array<const char*,10> names={{"call_price","put_price","call_delta","put_delta", "gamma","vega","call_theta","put_theta","call_rho","put_rho"}};
const std::array<const char*,10> expr={{
 "S*exp(-q*T)*n1-K*exp(-r*T)*n2",
 "K*exp(-r*T)*nm2-S*exp(-q*T)*nm1",
 "exp(-q*T)*n1",
 "-exp(-q*T)*nm1",
 "exp(-q*T)*pdf/(S*sig*sqrt(T))",
 "S*exp(-q*T)*pdf*sqrt(T)",
 "-S*exp(-q*T)*pdf*sig/(2*sqrt(T))-r*K*exp(-r*T)*n2+q*S*exp(-q*T)*n1",
 "-S*exp(-q*T)*pdf*sig/(2*sqrt(T))+r*K*exp(-r*T)*nm2-q*S*exp(-q*T)*nm1",
 "K*T*exp(-r*T)*n2",
 "-K*T*exp(-r*T)*nm2"
}};
void ensure(bool ok,const std::string& msg){if(!ok)throw std::runtime_error(msg);}
struct Case {double S,K,T,r,q,sig;};
void valid(const Case& c){
 ensure(std::isfinite(c.S)&&std::isfinite(c.K)&&std::isfinite(c.T)&&std::isfinite(c.r)&&std::isfinite(c.q)&&std::isfinite(c.sig),"nonfinite input");
 ensure(c.S>=20&&c.S<=250&&c.K>=20&&c.K<=250&&c.T>=0.05&&c.T<=5&&c.sig>=0.05&&c.sig<=1&&c.r>=-0.05&&c.r<=0.2&&c.q>=0&&c.q<=0.15,"input outside research contract");
}
double normal(double z){return .5*std::erfc(-z/std::sqrt(2.));}
std::array<double,NV> values(const Case& c){
 valid(c);
 const double srt=std::sqrt(c.T);
 const double d1=(std::log(c.S/c.K)+(c.r-c.q+.5*c.sig*c.sig)*c.T)/(c.sig*srt);
 const double d2=d1-c.sig*srt;
 const double pdf=std::exp(-.5*d1*d1)/std::sqrt(2*PI);
 return {{c.S,c.K,c.T,c.r,c.q,c.sig,normal(d1),normal(d2),normal(-d1),normal(-d2),pdf}};
}
// A deliberately separately written native reference, with independently
// calculated d1/d2, used to audit ALL published scalar and batch outputs.
std::array<double,10> reference(const Case& c){
 const double d=(std::log(c.S)-std::log(c.K)+(c.r-c.q+c.sig*c.sig/2)*c.T)/(c.sig*std::sqrt(c.T));
 const double e=d-c.sig*std::sqrt(c.T), dn=.5*std::erfc(-d/std::sqrt(2.0)), en=.5*std::erfc(-e/std::sqrt(2.0));
 const double nd=.5*std::erfc(d/std::sqrt(2.0)), ne=.5*std::erfc(e/std::sqrt(2.0));
 const double pd=std::exp(-d*d/2)/std::sqrt(2.0*PI), D=std::exp(-c.r*c.T), Q=std::exp(-c.q*c.T);
 const double g=Q*pd/(c.S*c.sig*std::sqrt(c.T));
 const double v=c.S*Q*pd*std::sqrt(c.T);
 const double t0=-c.S*Q*pd*c.sig/(2*std::sqrt(c.T));
 return {{c.S*Q*dn-c.K*D*en, c.K*D*ne-c.S*Q*nd, Q*dn,-Q*nd,g,v,
 t0-c.r*c.K*D*en+c.q*c.S*Q*dn,t0+c.r*c.K*D*ne-c.q*c.S*Q*nd,
 c.K*c.T*D*en,-c.K*c.T*D*ne}};
}
class SDK {
 bool ready=false;
 std::array<PACEVAL_HANDLE,10> handles{};
public:
 SDK(){ready=paceval_InitializeLibrary(nullptr);ensure(ready,"paceval_InitializeLibrary failed");
  for(size_t i=0;i<handles.size();++i){handles[i]=paceval_CreateComputation(expr[i],NV,vars,false,nullptr);
   ensure(handles[i]!=nullptr,"null computation handle: "+std::string(names[i]));
   ensure(!paceval_GetIsError(handles[i]),"paceval graph parse error: "+std::string(names[i]));}
 }
 SDK(const SDK&)=delete;SDK& operator=(const SDK&)=delete;
 ~SDK(){for(auto h:handles)if(h)paceval_DeleteComputation(h);if(ready)paceval_FreeLibrary();}
 double one(int m,std::array<double,NV> &v){
  const double o=paceval_dGetComputationResult(handles[m],v.data(),nullptr,nullptr);
  ensure(!paceval_GetIsError(handles[m])&&std::isfinite(o),"SDK scalar error: "+std::string(names[m]));return o;
 }
 std::vector<double> batch(int m,std::vector<double>& packed,size_t count){
  std::vector<double> output(count);std::vector<int> err(count,0);
  const bool anyError=paceval_dGetComputationResultExt(handles[m],packed.data(),(unsigned long)count,output.data(),nullptr,nullptr,err.data());
  ensure(!anyError,"SDK batch returned error: "+std::string(names[m]));
  for(size_t j=0;j<count;++j) ensure(err[j]==0&&std::isfinite(output[j]),"SDK batch element failed");
  return output;
 }
};
}
int main(int argc,char** argv){
 try{
  fs::path out="examples";
  if(argc==3&&std::string(argv[1])=="--out")out=argv[2];
  else if(argc!=1)throw std::runtime_error("Usage: pricing_sensitivities [--out OUTPUT_DIRECTORY]");
  fs::create_directories(out);
  SDK sdk;
  std::ofstream csv(out/"pricing_grid.csv"), audit(out/"audit_summary.txt");
  ensure(bool(csv)&&bool(audit),"failed to open output files");
  csv<<std::setprecision(17);audit<<std::setprecision(17);
  csv<<"S,sigma,K,T,r,q,call_price,put_price,call_delta,put_delta,gamma,vega,call_theta,put_theta,call_rho,put_rho\n";
  size_t cases=0,scalar=0,batch=0; double maxdiff=0,parity=0;
  std::vector<std::array<double,NV>> packed_rows;
  std::vector<std::array<double,10>> refs;
  // A deterministic 2D spot-volatility research grid, 61 * 41 = 2501 samples.
  for(int j=0;j<NY;++j)for(int i=0;i<NX;++i){
   Case c{60+i*1.4,100,1.25,.035,.012,.08+j*.013};
   auto x=values(c);auto ref=reference(c); std::array<double,10> got{};
   for(int k=0;k<10;++k){got[k]=sdk.one(k,x);++scalar;
    double dif=std::abs(got[k]-ref[k]);maxdiff=std::max(maxdiff,dif);
    ensure(dif<=2e-9*(1+std::abs(ref[k])),"scalar differs from independent reference");}
   parity=std::max(parity,std::abs(got[0]-got[1]-(c.S*std::exp(-c.q*c.T)-c.K*std::exp(-c.r*c.T))));
   csv<<c.S<<','<<c.sig<<','<<c.K<<','<<c.T<<','<<c.r<<','<<c.q;
   for(auto a:got) { csv<<','<<a; }
   csv<<'\n';
   packed_rows.push_back(x);refs.push_back(ref);++cases;
  }
  // The batch audit specifically exercises paceval_dGetComputationResultExt.
  // Chunk length 32 was chosen to make buffers bounded and independently checkable.
  for(int m=0;m<10;++m)for(size_t from=0;from<packed_rows.size();from+=BATCH){
   const size_t n=std::min(size_t(BATCH),packed_rows.size()-from);
   std::vector<double> packed;packed.reserve(n*NV);
   for(size_t z=0;z<n;++z)packed.insert(packed.end(),packed_rows[from+z].begin(),packed_rows[from+z].end());
   auto y=sdk.batch(m,packed,n);
   for(size_t z=0;z<n;++z){double dif=std::abs(y[z]-refs[from+z][m]);maxdiff=std::max(maxdiff,dif);
    ensure(dif<=2e-9*(1+std::abs(refs[from+z][m])),"batch differs from independent reference");++batch;}
  }
  audit<<"sdk_graphs=10\nresearch_cases="<<cases<<"\nscalar_checks="<<scalar<<"\nbatch_checks="<<batch
       <<"\nmax_absolute_native_difference="<<maxdiff<<"\nmax_put_call_parity_residual="<<parity<<"\n"
       <<"status=PASS\nnormal_cdf=host_std_erfc\n";
  std::cout<<"PASS: 10 reused paceval formulas, "<<cases<<" cases, "<<scalar<<" scalar and "<<batch<<" batch checks\n";
  std::cout<<"Maximum native difference="<<maxdiff<<"; put-call parity="<<parity<<"\n";
 }catch(const std::exception&e){std::cerr<<"FAIL: "<<e.what()<<'\n';return 1;}return 0;
}
