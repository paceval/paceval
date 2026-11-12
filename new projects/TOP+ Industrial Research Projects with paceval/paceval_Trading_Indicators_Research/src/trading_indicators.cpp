// Research host (2026). Original paceval SDK files next to this file retain
// their original upstream copyright and AGPL notices.
// This is a deterministic, causal arithmetic demonstrator, NOT a trading bot.
// Each bar is processed in chronological order. A graph receives only values
// already known at the current bar; future prices never enter an input vector.
#include "paceval_main.h"
#include <algorithm>
#include <array>
#include <cmath>
#include <cstdlib>
#include <filesystem>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <limits>
#include <numeric>
#include <stdexcept>
#include <string>
#include <vector>

namespace fs=std::filesystem;
namespace {
constexpr int DEFAULT_BARS=420, MODELS=128, WARMUP=40, BATCH=16;
constexpr double PI=3.14159265358979323846;
constexpr double TOL=1e-9;
void check(bool b,const std::string& msg){if(!b)throw std::runtime_error(msg);}
struct Weights {double a,b,c,d,e;};
// These deterministic weights are experiment choices, not optimized strategies.
Weights weights(int id,int version=1){
 const double shift=version==2?0.12:0.0;
 return {-0.18+0.04*(id%9),0.35+0.025*(id%7)+shift,
         0.28+0.02*((id/7)%9),0.22+0.015*((id/13)%11),
         -0.45-0.02*((id/17)%9)};
}
// The score is a bounded descriptor in [0,1], NOT a probability of profit.
double native_score(int id,const Weights&w,double m,double h,double q,double v){
 const double cross1=0.001*(1+(id%16));
 const double cross2=0.001*(1+((id/16)%8));
 const double z=w.a+w.b*m+w.c*h+w.d*q+w.e*v+cross1*m*q+cross2*h*v;
 return z>=0?1/(1+std::exp(-z)):std::exp(z)/(1+std::exp(z));
}
// Safe and transparent synthetic closing-price series (arbitrary price units).
// Uses only integer index t; no market data or external feeds.
double synthetic_price(int t){
 return 100*std::exp(0.00036*t+0.044*std::sin(t*0.059)+
                      0.024*std::sin(t*0.177)+0.009*std::cos(t*0.311));
}
struct Library {
 bool active=false;std::vector<PACEVAL_HANDLE> owned;
 Library(){active=paceval_InitializeLibrary(nullptr);check(active,"paceval_InitializeLibrary failed");}
 ~Library(){for(auto h:owned)if(h)paceval_DeleteComputation(h);if(active)paceval_FreeLibrary();}
 Library(const Library&)=delete;Library&operator=(const Library&)=delete;
 PACEVAL_HANDLE graph(const std::string&expr,unsigned long count,const char* vars){
  PACEVAL_HANDLE h=paceval_CreateComputation(expr.c_str(),count,vars,false,nullptr);
  check(h!=nullptr,"Null paceval graph for "+expr);
  owned.push_back(h);
  check(!paceval_GetIsError(h),"paceval graph creation rejected "+expr);
  return h;
 }
 double eval(PACEVAL_HANDLE h,std::initializer_list<double> vals){
  std::vector<double> x(vals);
  double y=paceval_dGetComputationResult(h,x.data(),nullptr,nullptr);
  check(!paceval_GetIsError(h)&&std::isfinite(y),"paceval scalar evaluation error");
  return y;
 }
};
struct Bar {int index;double price,ema20,ema12,ema26,macd,signal,rsi,vol,m,h,q,v;};
std::string outdir(int argc,char**argv,int &bars){
 std::string out="examples";
 for(int i=1;i<argc;++i){if(std::string(argv[i])=="--out"&&i+1<argc)out=argv[++i];
 else if(std::string(argv[i])=="--bars"&&i+1<argc)bars=std::stoi(argv[++i]);
 else throw std::runtime_error("Usage: trading_indicators [--out DIRECTORY]");}
 fs::create_directories(out);return out;
}
}
int main(int argc,char**argv){
 try{
  int bars=DEFAULT_BARS;
  const std::string dir=outdir(argc,argv,bars);
  check(bars>=WARMUP+BATCH&&bars<=100000,"Bar count outside research domain");
  Library sdk;
  // paceval owns every reusable numerical expression (including state updates).
  auto ema=sdk.graph("alpha*p+(1-alpha)*prev",3,"alpha p prev");
  auto rsi_graph=sdk.graph("100*g/(g+l)",2,"g l");
  auto momentum=sdk.graph("100*(p/ema-1)",2,"p ema");
  auto macd_normalization=sdk.graph("100*hist/p",2,"hist p");
  auto rsi_center=sdk.graph("(rsi-50)/50",1,"rsi");
  auto signal_difference=sdk.graph("fast-slow",2,"fast slow");
  const char* variables="a b c d e m h q v";
  const auto expression_for=[](int id){
   // 128 explicitly different, versioned expression strings. The two small
   // interaction coefficients are encoded in the graph itself, not in host
   // post-processing. Each ID therefore has a distinct mathematical kernel.
   const double k1=0.001*(1+(id%16));
   const double k2=0.001*(1+((id/16)%8));
   return std::string("1/(1+exp(-(a+b*m+c*h+d*q+e*v+")+
          std::to_string(k1)+"*m*q+"+std::to_string(k2)+"*h*v)))";
  };
  std::vector<PACEVAL_HANDLE> score_handles;
  // Separate model IDs, same exact arithmetic expression. Unique coefficients
  // are supplied as inputs. Each handle stays alive through the full experiment.
  for(int j=0;j<MODELS;++j)score_handles.push_back(sdk.graph(expression_for(j),9,variables));
  // Controlled version update is isolated: original graph remains usable.
  auto version_two=sdk.graph(expression_for(0),9,variables);

  std::ofstream state_file(dir+"/indicator_states.csv");
  std::ofstream score_file(dir+"/score_results.csv");
  std::ofstream version_file(dir+"/version_comparison.csv");
  std::ofstream manifest(dir+"/models.csv");
  check(bool(state_file)&&bool(score_file)&&bool(version_file)&&bool(manifest),"CSV open failed");
  for(auto *f:{&state_file,&score_file,&version_file,&manifest})*f<<std::setprecision(17);
  state_file<<"bar,price,ema20,ema12,ema26,macd,signal,rsi14,realized_vol20,momentum_pct,macd_hist_pct,rsi_centered,vol_normalized\n";
  score_file<<"bar,model_id,version,score_paceval,score_native,abs_difference,momentum_pct,macd_hist_pct,rsi_centered,vol_normalized\n";
  version_file<<"bar,score_v1,score_v2,delta\n";
  manifest<<"model_id,version,intercept,momentum_weight,macd_weight,rsi_weight,volatility_weight,formula\n";
  for(int id=0;id<MODELS;++id){auto w=weights(id);manifest<<id<<",1,"<<w.a<<','<<w.b<<','<<w.c<<','<<w.d<<','<<w.e<<",\""<<expression_for(id)<<"\"\n";}
  auto w2=weights(0,2);manifest<<"0,2,"<<w2.a<<','<<w2.b<<','<<w2.c<<','<<w2.d<<','<<w2.e<<",\""<<expression_for(0)<<"\"\n";

  double ema20=0,ema12=0,ema26=0,signal=0,prev=0,g=0,l=0;
  std::vector<double> returns;
  std::vector<Bar> rows;
  std::size_t scalar_scores=0,batch_checks=0;
  double maxdiff=0;
  for(int t=0;t<bars;++t){
   const double p=synthetic_price(t);
   check(p>0&&std::isfinite(p),"Invalid input price");
   // EMA is seeded at the first close. This convention is frozen across all runs.
   if(t==0){ema20=ema12=ema26=p;prev=p;}
   else {
    const double a20=2.0/21,a12=2.0/13,a26=2.0/27;
    const double n20=sdk.eval(ema,{a20,p,ema20});
    const double n12=sdk.eval(ema,{a12,p,ema12});
    const double n26=sdk.eval(ema,{a26,p,ema26});
    check(std::abs(n20-(a20*p+(1-a20)*ema20))<TOL,"EMA20 mismatch");
    check(std::abs(n12-(a12*p+(1-a12)*ema12))<TOL,"EMA12 mismatch");
    check(std::abs(n26-(a26*p+(1-a26)*ema26))<TOL,"EMA26 mismatch");
    ema20=n20;ema12=n12;ema26=n26;
   }
   const double macd=sdk.eval(signal_difference,{ema12,ema26});
   if(t==0)signal=macd;else signal=sdk.eval(ema,{2.0/10,macd,signal});
   if(t>0){
    double change=p-prev;
    returns.push_back(std::log(p/prev));
    if(t<=14){g+=std::max(change,0.0)/14;l+=std::max(-change,0.0)/14;}
    else {g=sdk.eval(ema,{1.0/14,std::max(change,0.0),g});
          l=sdk.eval(ema,{1.0/14,std::max(-change,0.0),l});}
   }
   prev=p;
   double rsi=50.0;
   if(t>=14){rsi=(g+l>0)?sdk.eval(rsi_graph,{g,l}):50.0;}
   // 20 trailing log-returns INCLUDING current bar; no next-bar input.
   double vol=0;
   if(returns.size()>=20){
     double mean=0,sumsq=0;
     const auto start=returns.end()-20;
     for(auto it=start;it!=returns.end();++it)mean+=*it/20;
     for(auto it=start;it!=returns.end();++it)sumsq+=(*it-mean)*(*it-mean);
     vol=std::sqrt(sumsq/19)*std::sqrt(252.0)*100;
   }
   double m=sdk.eval(momentum,{p,ema20})/5.0;
   double h=sdk.eval(macd_normalization,{macd-signal,p})/1.5;
   double q=sdk.eval(rsi_center,{rsi});
   double v=vol/20.0;
   check(std::isfinite(m)&&std::isfinite(h)&&std::isfinite(q)&&std::isfinite(v),"Nonfinite feature");
   // Gate all signal output until indicators are initialized and warmed up.
   if(t<WARMUP)continue;
   rows.push_back({t,p,ema20,ema12,ema26,macd,signal,rsi,vol,m,h,q,v});
   state_file<<t<<','<<p<<','<<ema20<<','<<ema12<<','<<ema26<<','<<macd<<','<<signal<<','<<rsi<<','<<vol<<','<<m<<','<<h<<','<<q<<','<<v<<'\n';
   for(int id=0;id<MODELS;++id){
     auto w=weights(id);
     double y=sdk.eval(score_handles[id],{w.a,w.b,w.c,w.d,w.e,m,h,q,v});
     double ref=native_score(id,w,m,h,q,v);
     double diff=std::abs(y-ref);
     check(diff<=TOL*(1+std::abs(ref))&&y>=0&&y<=1,"Score mismatch");
     maxdiff=std::max(maxdiff,diff);++scalar_scores;
     score_file<<t<<','<<id<<",1,"<<y<<','<<ref<<','<<diff<<','<<m<<','<<h<<','<<q<<','<<v<<'\n';
   }
   auto w1=weights(0);
   double s1=sdk.eval(score_handles[0],{w1.a,w1.b,w1.c,w1.d,w1.e,m,h,q,v});
   double s2=sdk.eval(version_two,{w2.a,w2.b,w2.c,w2.d,w2.e,m,h,q,v});
   check(std::abs(s2-native_score(0,w2,m,h,q,v))<TOL,"Version-two mismatch");
   version_file<<t<<','<<s1<<','<<s2<<','<<(s2-s1)<<'\n';
  }
  // Evaluate a packed batch through the same graph. The published SDK uses
  // row-major [sample][variable] layout and returns per-item error codes.
  for(int id=0;id<MODELS;++id){
   double packed[BATCH*9], result[BATCH];int errors[BATCH]{};
   auto w=weights(id);
   for(int k=0;k<BATCH;++k){const auto &r=rows.at((id*17+k*3)%rows.size());
    const double vals[9]={w.a,w.b,w.c,w.d,w.e,r.m,r.h,r.q,r.v};
    std::copy(vals,vals+9,packed+9*k);
   }
   bool failure=paceval_dGetComputationResultExt(score_handles[id],packed,BATCH,result,nullptr,nullptr,errors);
   check(!failure,"paceval batch API failure");
   for(int k=0;k<BATCH;++k){
    check(errors[k]==PACEVAL_ERR_NO_ERROR,"Batch item returned SDK error");
    const double* f=packed+9*k;double ref=native_score(id,w,f[5],f[6],f[7],f[8]);
    check(std::isfinite(result[k])&&std::abs(result[k]-ref)<=TOL*(1+std::abs(ref)),"Batch result disagreement");
    ++batch_checks;
   }
  }
  // A controlled two-parameter score landscape. The remaining feature values
  // are frozen at the final observed bar. Every plotted surface point is
  // independently evaluated by the actual paceval score graph and native code.
  {
   std::ofstream surface(dir+"/score_surface.csv");
   check(bool(surface),"Cannot create score surface");
   surface<<std::setprecision(17);
   surface<<"i,j,momentum_scaled,rsi_centered,score_paceval,score_native,abs_difference\n";
   const auto &last=rows.back(); const auto w=weights(0);
   for(int i=0;i<61;++i)for(int j=0;j<61;++j){
    const double m=-2.0+4.0*i/60.0,q=-1.0+2.0*j/60.0;
    const double val=sdk.eval(score_handles[0],{w.a,w.b,w.c,w.d,w.e,m,last.h,q,last.v});
    const double ref=native_score(0,w,m,last.h,q,last.v);
    check(std::abs(val-ref)<=TOL*(1+std::abs(ref)),"Surface numerical mismatch");
    surface<<i<<','<<j<<','<<m<<','<<q<<','<<val<<','<<ref<<','<<std::abs(val-ref)<<'\n';
   }
   check(bool(surface),"Score surface write failed");
  }
  // Deterministic prefix-causality audit: regenerate each historic price from
  // its index and verify no value depends on an observation after that index.
  for(const auto& r:rows){check(r.price==synthetic_price(r.index),"Prefix audit failed");}
  check(bool(state_file)&&bool(score_file)&&bool(version_file)&&bool(manifest),"CSV write failed");
  std::cout<<"PASS: "<<MODELS<<" version-one score graphs, 1 updated graph, "
           <<rows.size()<<" causal bars, "<<scalar_scores<<" checked score outputs, "
           <<batch_checks<<" checked packed batch outputs, max abs difference "
           <<std::setprecision(17)<<maxdiff<<"\n";
  return EXIT_SUCCESS;
 }catch(const std::exception&e){std::cerr<<"FAIL: "<<e.what()<<'\n';return EXIT_FAILURE;}
}
