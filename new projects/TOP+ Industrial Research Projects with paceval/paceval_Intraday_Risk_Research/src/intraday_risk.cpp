// WP029: synthetic intraday two-factor market-risk mathematical kernels.
// paceval evaluates persisted analytical expressions. Host owns data contracts,
// reproducible market replay, risk-limit routing, and independent validation.
// No FRTB expected shortfall, historical VaR, capital measure or live trading.
#include "paceval_main.h"
#include <array>
#include <cmath>
#include <cstdint>
#include <filesystem>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <sstream>
#include <stdexcept>
#include <string>
#include <vector>
#include <algorithm>
namespace fs=std::filesystem;
namespace {
using Input=std::array<double,4>; // signed EUR millions w1,w2; shock; limit EUR millions
constexpr double V1=0.0002, V2=0.00045, COV=0.00012;
constexpr char VARS[]="w1 w2 s l";
void require(bool ok,const std::string& reason){if(!ok)throw std::runtime_error(reason);}
struct Rule {int id=0, family=0,version=1;double a=0,b=0;std::string formula;PACEVAL_HANDLE handle=nullptr;};
double Q(double w1,double w2){return V1*w1*w1+2*COV*w1*w2+V2*w2*w2;}
// Covariance PSD: v1*v2-cov^2 = 7.56e-8 > 0. Covariance is frozen.
void checkInput(const Input& x){for(auto v:x)require(std::isfinite(v),"nonfinite input");
 require(std::abs(x[0])<=25&&std::abs(x[1])<=25&&std::abs(x[2])<=0.5&&x[3]>=0.05&&x[3]<=4,"invalid input domain");}
double oracle(const Rule& r,const Input& x){double w=x[0],u=x[1],s=x[2];double q=Q(w,u);
 switch(r.family){
 case 0:return std::sqrt(q)*(1+r.a*s);
 case 1:return std::sqrt(q+r.a*(w*w+u*u)*0.00002*s*s);
 case 2:return std::sqrt(V1*w*w+V2*u*u+2*(COV+r.a*0.00002*s)*w*u);
 case 3:return std::sqrt(q)+r.a*std::sqrt(w*w+u*u)*std::sqrt(1+s*s)*0.004;
 default:return std::sqrt(q)+r.a*std::abs(w*u)*s*s*0.00015+r.b*std::sqrt(1+s*s)*0.002;
 }}
std::string equation(const Rule& r){std::ostringstream os;os<<std::setprecision(17);std::string q="(0.0002*w1*w1+0.00024*w1*w2+0.00045*w2*w2)";
 switch(r.family){
 case 0:os<<"sqrt("<<q<<")*(1+"<<r.a<<"*s)";break;
 case 1:os<<"sqrt("<<q<<"+"<<r.a<<"*(w1*w1+w2*w2)*0.00002*s*s)";break;
 case 2:os<<"sqrt(0.0002*w1*w1+0.00045*w2*w2+2*(0.00012+"<<r.a<<"*0.00002*s)*w1*w2)";break;
 case 3:os<<"sqrt("<<q<<")+"<<r.a<<"*sqrt(w1*w1+w2*w2)*sqrt(1+s*s)*0.004";break;
 default:os<<"sqrt("<<q<<")+"<<r.a<<"*sqrt((w1*w2)*(w1*w2))*s*s*0.00015+"<<r.b<<"*sqrt(1+s*s)*0.002";break;
 }return os.str();}
std::vector<Rule> rules(){std::vector<Rule> ret;for(int f=0;f<5;++f)for(int j=0;j<10;++j){Rule r;r.id=f*10+j+1;r.family=f;r.a=0.10+0.022*j+0.006*f;r.b=0.2+0.015*j;r.formula=equation(r);ret.push_back(r);}return ret;}
class Paceval {std::vector<PACEVAL_HANDLE> handles;public:
 Paceval(){require(paceval_InitializeLibrary(nullptr),"paceval initialization failed");}
 ~Paceval(){for(auto h:handles)if(h)paceval_DeleteComputation(h);paceval_FreeLibrary();}
 PACEVAL_HANDLE create(const std::string& expression){auto h=paceval_CreateComputation(expression.c_str(),4,VARS,false,nullptr);require(h&&!paceval_GetIsError(h),"paceval CreateComputation failed: "+expression);handles.push_back(h);return h;}
 double value(PACEVAL_HANDLE h,const Input& x){Input in=x;double y=paceval_dGetComputationResult(h,in.data(),nullptr,nullptr);require(!paceval_GetIsError(h)&&std::isfinite(y)&&y>=0,"invalid scalar paceval result");return y;}
 std::vector<double> batch(PACEVAL_HANDLE h,const std::vector<Input>& x){std::vector<double> packed(x.size()*4),out(x.size());std::vector<int> flags(x.size(),-1);for(size_t i=0;i<x.size();++i)for(int j=0;j<4;++j)packed[i*4+j]=x[i][j];
 bool failed=paceval_dGetComputationResultExt(h,packed.data(),(unsigned long)x.size(),out.data(),nullptr,nullptr,flags.data());require(!failed,"paceval batch function failed");for(size_t i=0;i<x.size();++i)require(flags[i]==0&&std::isfinite(out[i])&&out[i]>=0,"bad batch value");return out;}
};
struct Random {uint64_t x=20261112;uint64_t next(){x^=x>>12;x^=x<<25;x^=x>>27;return x*2685821657736338717ULL;}double unit(){return (next()>>11)*0x1.0p-53;}};
Input randomInput(Random& rng){return {-20+40*rng.unit(),-20+40*rng.unit(),-0.4+0.8*rng.unit(),0.1+1.3*rng.unit()};}
void audit(double got,double expected,double& worst){double d=std::abs(got-expected);worst=std::max(d,worst);require(d<1e-10*(1+std::abs(expected)),"mathematical independent verification failed");}
void run(const fs::path& output,int n){fs::create_directories(output);Paceval engine;auto rr=rules();for(auto& r:rr)r.handle=engine.create(r.formula);
 Rule updated=rr[11];updated.version=2;updated.id=51;updated.a+=0.035;updated.formula=equation(updated);updated.handle=engine.create(updated.formula);
 std::ofstream reg(output/"rule_registry.csv");reg<<"rule_id,family,version,a,b,formula\n";for(auto& r:rr)reg<<r.id<<","<<r.family+1<<","<<r.version<<","<<r.a<<","<<r.b<<",\""<<r.formula<<"\"\n";reg<<updated.id<<","<<updated.family+1<<",2,"<<updated.a<<","<<updated.b<<",\""<<updated.formula<<"\"\n";
 std::ofstream replay(output/"risk_replay.csv");replay<<"update,rule_id,w1_eur_m,w2_eur_m,shock,limit_eur_m,risk_eur_m,limit_breach\n";std::array<double,50> sums{},peak{};std::array<int,50> counts{};Random rng;double worst=0;long long alerts=0,sampled=0,scalar=n;for(int i=0;i<n;++i){const Rule& r=rr[i%50];Input x=randomInput(rng);checkInput(x);double y=engine.value(r.handle,x);if(i<100||i%137==0)audit(y,oracle(r,x),worst);int alert=y>x[3];alerts+=alert;sums[i%50]+=y;counts[i%50]++;peak[i%50]=std::max(peak[i%50],y);
 if(i%25==0){replay<<i+1<<","<<r.id<<std::setprecision(17);for(auto z:x)replay<<","<<z;replay<<","<<y<<","<<alert<<"\n";sampled++;}}
 std::ofstream summary(output/"family_summary.csv");summary<<"rule_id,family,mean_risk_eur_m,max_risk_eur_m\n";for(int j=0;j<50;++j)summary<<j+1<<","<<rr[j].family+1<<","<<sums[j]/counts[j]<<","<<peak[j]<<"\n";
 std::ofstream surface(output/"risk_surface.csv");surface<<"w1_eur_m,w2_eur_m,risk_eur_m\n";
 for(int i=0;i<=60;++i)for(int j=0;j<=60;++j){Input x={-20+i*2.0/3,-20+j*2.0/3,0.2,1};double y=engine.value(rr[0].handle,x);audit(y,oracle(rr[0],x),worst);surface<<std::setprecision(17)<<x[0]<<","<<x[1]<<","<<y<<"\n";scalar++;}
 std::ofstream stress(output/"stress_scenarios.csv");stress<<"shock,base_risk_eur_m,stress_variance_eur_m,stress_correlation_eur_m,concentration_risk_eur_m\n";
 for(int j=0;j<=80;++j){Input x={14,-9,-0.4+j*0.01,1.0};double v[4];for(int k=0;k<4;++k){v[k]=engine.value(rr[k*10].handle,x);audit(v[k],oracle(rr[k*10],x),worst);scalar++;}stress<<x[2];for(auto z:v)stress<<","<<z;stress<<"\n";}
 std::ofstream revise(output/"formula_revision.csv");revise<<"shock,version1_risk_eur_m,version2_risk_eur_m\n";
 for(int j=0;j<=60;++j){Input x={12,8,-0.3+j*0.01,0.8};double a=engine.value(rr[11].handle,x),b=engine.value(updated.handle,x);audit(a,oracle(rr[11],x),worst);audit(b,oracle(updated,x),worst);revise<<x[2]<<","<<a<<","<<b<<"\n";scalar+=2;}
 Random rng2;long long batchVerified=0;for(const auto& r:rr){std::vector<Input> xs;for(int j=0;j<32;++j)xs.push_back(randomInput(rng2));auto yy=engine.batch(r.handle,xs);for(size_t j=0;j<yy.size();++j){audit(yy[j],oracle(r,xs[j]),worst);batchVerified++;}}
 int invalid=0;for(Input x:std::vector<Input>{{NAN,1,0,1},{1,2,1,1},{2,3,0,-1}}){try{checkInput(x);}catch(...){invalid++;}}require(invalid==3,"negative input tests failed");
 std::ofstream log(output/"sdk_execution.txt");log<<std::setprecision(17)<<"STATUS PASS\nGRAPH_COUNT 51\nREPLAY_UPDATES "<<n<<"\nSAMPLED_ROWS "<<sampled<<"\nSCALAR_EVALUATIONS "<<scalar<<"\nBATCH_VERIFIED "<<batchVerified<<"\nLIMIT_ALERTS "<<alerts<<"\nSURFACE_POINTS 3721\nINVALID_REJECTED "<<invalid<<"\nINTERNAL_MAX_DIFFERENCE "<<worst<<"\n";
 std::cout<<"PASS "<<n<<" updates, 51 graphs, "<<scalar<<" scalar, "<<batchVerified<<" batch.\n";
}
}
int main(int argc,char** argv){try{fs::path out="examples";int n=20000;for(int i=1;i<argc;++i){std::string arg=argv[i];if(arg=="--out"&&i+1<argc)out=argv[++i];else if(arg=="--updates"&&i+1<argc)n=std::stoi(argv[++i]);else throw std::runtime_error("unknown argument");}require(n>0&&n<=1000000,"invalid updates");run(out,n);return 0;}catch(const std::exception& e){std::cerr<<"FAIL "<<e.what()<<"\n";return 1;}}
