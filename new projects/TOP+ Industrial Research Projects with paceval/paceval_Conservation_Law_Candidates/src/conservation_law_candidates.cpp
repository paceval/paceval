// WP_041 - Computational Testing of Conservation-Law Candidates.
// A transparent, reproducible, synthetic science demonstrator, not a discovery claim.
// All candidate invariants, Lie derivatives, normalized Lie scores, and squared derivatives
// are REGISTERED AS REAL PERSISTENT PACEVAL GRAPHS and evaluated via the original batch API.
// The C++ host owns analytic benchmark trajectory generation, deterministic measurement
// noise, data grouping and threshold decisions, file I/O, and independent native audits.
// All original paceval SDK copyright information in paceval_main.{h,cpp} is retained.
#include "paceval_main.h"
#include "generated_registry.h"
#include <array>
#include <algorithm>
#include <cmath>
#include <cstdint>
#include <filesystem>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <limits>
#include <numeric>
#include <sstream>
#include <stdexcept>
#include <string>
#include <vector>
using namespace std;
namespace fs=std::filesystem;
using Input=array<double,7>; // x v y w mu zeta t
static constexpr int NV=7;
static const char* VARIABLES="x v y w mu zeta t";
static constexpr int NS=192;
static constexpr double NOISES[4]={0.,0.005,0.02,0.05};
static constexpr double PI=3.1415926535897932384626433832795;
static void must(bool b,const string&s){if(!b)throw runtime_error(s);}
struct ScalarCheck{size_t checked=0;double worst=0;};
struct Candidate {FormulaDef def;array<PACEVAL_HANDLE,4> graph{};};
// The actual source-specific drift statistic below is computed from the recorded
// paceval invariant values; no independent replacement formula is used for production.
class Engine {
 vector<Candidate> candidates;
 public:
 size_t batch_invocations=0, batch_outputs=0, scalar_calls=0;
 ScalarCheck audit;
 Engine(){
   must(paceval_InitializeLibrary(nullptr),"original paceval runtime failed to initialize");
   for(const auto&f:makeFormulaDefs()){
     Candidate c;c.def=f;
     array<string,4> expr={f.expression,f.lie,f.normalized_lie,f.lie_sq};
     for(int k=0;k<4;++k){
       c.graph[k]=paceval_CreateComputation(expr[k].c_str(),NV,VARIABLES,false,nullptr);
       if(c.graph[k]&&paceval_GetIsError(c.graph[k])){
         char error[512]={0},details[512]={0};paceval_CreateErrorInformationText(c.graph[k],error,details);
         cerr<<"paceval formula create error: "<<f.id<<" kind="<<k<<" "<<error<<" "<<details<<"\n";
       }
       must(c.graph[k]!=nullptr&&!paceval_GetIsError(c.graph[k]),string("graph creation failed: ")+f.id);
     }
     candidates.push_back(c);
   }
   must(candidates.size()==36,"unexpected formula registry size");
 }
 ~Engine(){for(auto&c:candidates)for(auto h:c.graph)if(h)paceval_DeleteComputation(h);paceval_FreeLibrary();}
 const vector<Candidate>& defs()const{return candidates;}
 vector<size_t> indexes(const string&model) const{vector<size_t> idx;for(size_t i=0;i<candidates.size();++i)if(model==candidates[i].def.model)idx.push_back(i);return idx;}
 struct Batch{vector<double> results;size_t npoints=0,ngraphs=0;double at(size_t f,size_t kind,size_t i)const{return results[(4*f+kind)*npoints+i];}};
 Batch run(const string&model,const vector<Input>& in){
   must(!in.empty()&&in.size()<=512,"batch must have 1..512 samples");
   auto idx=indexes(model);must(idx.size()==12,"unexpected model candidate count");
   vector<PACEVAL_HANDLE> handles;handles.reserve(idx.size()*4);
   for(auto i:idx)for(auto h:candidates[i].graph)handles.push_back(h);
   vector<double> flat;flat.reserve(in.size()*NV);
   for(const auto&z:in){for(double v:z)must(isfinite(v),"non-finite input");
     if(model=="kepler")must(z[0]*z[0]+z[2]*z[2]>.1&&z[4]>.0,"invalid Kepler radius or mu");
     if(model=="damped")must(z[5]>.0&&z[5]<.4,"invalid damping");
     flat.insert(flat.end(),z.begin(),z.end());}
   vector<double> out(handles.size()*in.size(),numeric_limits<double>::quiet_NaN());
   vector<int> errors(out.size(),-9);
   // For the tested original library, the bool return value indicates failure,
   // not success. The full per-result error array is checked unconditionally.
   bool failed=paceval_dGetMultipleComputationsResultsExt(handles.data(),(unsigned long)handles.size(),flat.data(),(unsigned long)in.size(),out.data(),nullptr,nullptr,errors.data());
   must(!failed,string("paceval multi-graph batch failure: ")+model);
   for(size_t i=0;i<out.size();++i)must(errors[i]==0&&isfinite(out[i]),"per-result paceval numeric error");
   ++batch_invocations;batch_outputs+=out.size();
   // Independent scientific identities: analytic Lie derivatives should vanish
   // at ALL finite phase-space points for known invariants (also noisy inputs).
   for(size_t c=0;c<idx.size();++c){
     if(!candidates[idx[c]].def.known)continue;
     for(size_t j=0;j<in.size();j+=max<size_t>(1,in.size()/9)){
       double val=out[(4*c+1)*in.size()+j];
       must(abs(val)<2e-8,string("known invariant's Lie derivative nonzero: ")+candidates[idx[c]].def.id);
       ++audit.checked;audit.worst=max(audit.worst,abs(val));
     }
   }
   return {move(out),in.size(),handles.size()};
 }
 void scalarSpotCheck(const string&model,const Input&input){
   auto idx=indexes(model);for(size_t k=0;k<idx.size();++k){
     const auto&c=candidates[idx[k]];
     double raw[NV];copy(input.begin(),input.end(),raw);
     double z=paceval_dGetComputationResult(c.graph[0],raw,nullptr,nullptr);
     must(isfinite(z),"scalar paceval spot check failed");++scalar_calls;
   }
 }
};
static uint64_t hash64(uint64_t z){z+=0x9e3779b97f4a7c15ULL;z=(z^(z>>30))*0xbf58476d1ce4e5b9ULL;z=(z^(z>>27))*0x94d049bb133111ebULL;return z^(z>>31);}
static double gaussian(uint64_t id){
 double a=((hash64(id)>>11)+.5)*(1./9007199254740992.0);
 double b=((hash64(id^0x3c79ac492ba7b653ULL)>>11)+.5)*(1./9007199254740992.0);
 return sqrt(-2*log(a))*cos(2*PI*b);
}
static Input trajectory(const string&m,int tr,int j,double noise){
 const double t=14.*j/(NS-1.0);
 Input z{0,0,0,0,1,0.075,t};
 if(m=="oscillator"){
   const double a=0.75+0.22*tr,b=0.55+0.13*tr;
   const double p=0.15+tr*.17,q=0.42+tr*.09;
   z[0]=a*cos(t+p);z[1]=-a*sin(t+p);z[2]=b*cos(2*t+q);z[3]=-2*b*sin(2*t+q);
 }else if(m=="kepler"){
   const double a=1.32+0.14*tr,e=0.16+0.035*tr;
   const double meanMotion=sqrt(z[4]/(a*a*a));
   const double M=meanMotion*t+0.21+tr*.3;
   double u=M;
   for(int k=0;k<12;++k)u-=(u-e*sin(u)-M)/(1-e*cos(u));
   double denom=1-e*cos(u),s=sqrt(1-e*e);
   z[0]=a*(cos(u)-e);z[2]=a*s*sin(u);
   z[1]=-a*meanMotion*sin(u)/denom;z[3]=a*meanMotion*s*cos(u)/denom;
 }else if(m=="damped"){
   const double A=0.8+0.13*tr,V0=0.27+0.09*tr;
   double omega=sqrt(1-z[5]*z[5]);
   double B=(V0+z[5]*A)/omega;
   double phase=A*cos(omega*t)+B*sin(omega*t);
   double derivative=omega*(-A*sin(omega*t)+B*cos(omega*t));
   z[0]=exp(-z[5]*t)*phase;z[1]=exp(-z[5]*t)*(derivative-z[5]*phase);
 }
 if(noise>0){
   for(int k=0;k<4;++k){
     if(m=="damped"&&k>=2)continue;
     // Noisy measured state, while the exact dynamical model remains fixed.
     // This tests observational robustness of trajectory-drift statistics.
     z[k]+=noise*gaussian(20261113ULL+uint64_t(tr)*900000+uint64_t(j)*19+uint64_t(k)*103+uint64_t(m.size())*1531);
   }
 }
 return z;
}
struct Aggregate {vector<double> val,lie,score,lie2;};
struct Metric{string model,id,split;int true_label=0;double noise=0,lie_norm=0,drift=0;bool selected=false;};
static double rootMeanSquare(const vector<double>&a){double s=0;for(double z:a)s+=z*z;return sqrt(s/max<size_t>(1,a.size()));}
static Metric summarize(const string&model,const FormulaDef&def,int split,double noise,
                        const vector<Aggregate>&a){
 // Each trajectory is normalized by its OWN mean invariant value, not across
 // distinct initial conditions whose true conserved constants differ.
 double score=0,drift=0;
 for(const auto&v:a){
   double mean=accumulate(v.val.begin(),v.val.end(),0.0)/v.val.size();
   vector<double> diff;diff.reserve(v.val.size());for(double x:v.val)diff.push_back(x-mean);
   drift+=rootMeanSquare(diff)/max(1.,abs(mean));
   score+=rootMeanSquare(v.score);
 }
 drift/=a.size();score/=a.size();
 // Locked before evaluation: the normalized Lie threshold is independent of
 // observational noise; the state-drift tolerance increases with declared noise.
 double driftMargin=.002+12*noise;
 bool found=score<1e-7 && drift<driftMargin;
 return {model,def.id,split==0?"training":"heldout",def.known?1:0,noise,score,drift,found};
}
int main(int argc,char**argv){
 try{
  fs::path out=".";bool smoke=false;
  for(int i=1;i<argc;++i){string a=argv[i];if(a=="--out"&&i+1<argc)out=argv[++i];else if(a=="--smoke")smoke=true;else throw runtime_error("unknown CLI argument: "+a);}
  fs::create_directories(out/"results");fs::create_directories(out/"examples");
  Engine engine;
  auto idx=engine.defs();
  ofstream metrics(out/"results"/"candidate_metrics.csv");metrics<<"model,candidate_id,split,known_invariant,noise_sigma,normalized_lie_rms,trajectory_drift_rms,selected\n"<<setprecision(17);
  ofstream profiles(out/"examples"/"trajectory_profiles.csv");profiles<<"model,noise_sigma,trajectory_id,t,x,v,y,w,candidate_id,value_from_paceval,lie_from_paceval\n"<<setprecision(17);
  ofstream reference(out/"examples"/"high_precision_reference_samples.csv");reference<<"model,candidate_id,t,x,v,y,w,mu,zeta,expression_value,lie_value,normalized_lie,lie_squared\n"<<setprecision(17);
  ofstream curves(out/"results"/"precision_recall.csv");curves<<"model,noise_sigma,split,true_positive,false_positive,false_negative,true_negative,precision,recall\n"<<setprecision(17);
  size_t totalInputs=0,allCandidates=0,successful=0;
  const vector<string>models={"oscillator","kepler","damped"};
  for(const auto&m:models){
   auto ids=engine.indexes(m);engine.scalarSpotCheck(m,trajectory(m,0,42,0));
   for(double noise:NOISES){
    // Candidate arrays per training/heldout trajectory; expressions grouped into
    // chunks to maximize genuine multi-graph batch evaluation and handle reuse.
    vector<vector<Aggregate>>store(2,vector<Aggregate>(ids.size()*2));
    for(int tr=0;tr<4;++tr){
     const int split=tr<2?0:1;
     vector<Aggregate> accum(ids.size());
     for(int first=0;first<NS;first+=96){
       int n=min(96,NS-first);vector<Input>batch;batch.reserve(n);
       for(int j=0;j<n;++j)batch.push_back(trajectory(m,tr,first+j,noise));
       auto result=engine.run(m,batch);totalInputs+=n;
       for(size_t k=0;k<ids.size();++k){
         for(int j=0;j<n;++j){
           auto v=result.at(k,0,j),l=result.at(k,1,j),sc=result.at(k,2,j),lsq=result.at(k,3,j);
           must(abs(l*l-lsq)<1e-7*(1+abs(lsq)),"paceval squared Lie relation invalid");
           auto&agg=accum[k];agg.val.push_back(v);agg.lie.push_back(l);agg.score.push_back(sc);agg.lie2.push_back(lsq);
           // Fixed deterministic reference sample: 16 points per candidate
           // from an independently held-out, noiseless trajectory. Values come
           // from four separate paceval-registered mathematical graphs.
           if(tr==2 && noise==0. && (first+j)%12==0){
             const auto&z=batch[j];
             reference<<m<<','<<engine.defs()[ids[k]].def.id<<','<<z[6]<<','<<z[0]<<','<<z[1]<<','<<z[2]<<','<<z[3]<<','<<z[4]<<','<<z[5]<<','<<v<<','<<l<<','<<sc<<','<<lsq<<'\n';
           }
           // Save a faithful, compact sampled subset for science diagrams.
           if((tr==0 || tr==2)&&(noise==0. || noise==0.02)&&k<4){
             const auto&z=batch[j];profiles<<m<<','<<noise<<','<<tr<<','<<z[6]<<','<<z[0]<<','<<z[1]<<','<<z[2]<<','<<z[3]<<','<<engine.defs()[ids[k]].def.id<<','<<v<<','<<l<<'\n';
           }
         }
       }
     }
     for(size_t k=0;k<ids.size();++k)store[split][2*k+(tr%2)]=move(accum[k]);
    }
    for(int split=0;split<2;++split){int tp=0,fp=0,fn=0,tn=0;
     for(size_t k=0;k<ids.size();++k){
       auto&def=engine.defs()[ids[k]].def;
       vector<Aggregate> a={store[split][2*k],store[split][2*k+1]};
       Metric z=summarize(m,def,split,noise,a);
       metrics<<m<<','<<z.id<<','<<z.split<<','<<z.true_label<<','<<noise<<','<<z.lie_norm<<','<<z.drift<<','<<int(z.selected)<<'\n';
       int truth=z.true_label;int predicted=int(z.selected);
       if(truth && predicted)++tp;else if(!truth&&predicted)++fp;else if(truth&&!predicted)++fn;else ++tn;
       ++allCandidates;if(z.selected)++successful;
     }
     double precision=tp+fp?double(tp)/(tp+fp):0.;double recall=tp+fn?double(tp)/(tp+fn):0.;
     curves<<m<<','<<noise<<','<<(split?"heldout":"training")<<','<<tp<<','<<fp<<','<<fn<<','<<tn<<','<<precision<<','<<recall<<'\n';
    }
   }
   cout<<"[OK] "<<m<<" evaluated with 12 reusable formula candidates across 4 trajectories and 4 noise conditions\n";
   if(smoke)break;
  }
  // 3D Lie-residual surface, evaluated via paceval as a large batch (not plotted from a native reimplementation).
  if(!smoke){
   ofstream surface(out/"examples"/"oscillator_lie_surface.csv");surface<<"x,v,energy_lie_abs,cross_xv_lie_abs,position_x_lie_abs\n"<<setprecision(17);
   for(int row=0;row<65;++row){
    vector<Input> grid;grid.reserve(65);
    for(int col=0;col<65;++col){Input x{};x[0]=-2.+4.*row/64.;x[1]=-2.+4.*col/64.;x[2]=0.3;x[3]=0.25;x[4]=1.;x[5]=.075;x[6]=1.;grid.push_back(x);}
    auto r=engine.run("oscillator",grid);totalInputs+=65;
    for(int col=0;col<65;++col)surface<<grid[col][0]<<','<<grid[col][1]<<','<<abs(r.at(0,1,col))<<','<<abs(r.at(8,1,col))<<','<<abs(r.at(4,1,col))<<'\n';
   }
  }
  ofstream inventory(out/"results"/"math_execution_inventory.csv");inventory<<"model,candidate_id,formula_kind,expression,owner,api,registered_graph,known_invariant\n";
  for(const auto&c:engine.defs()){
   const char*kind[]={"candidate_value","analytic_lie_derivative","normalized_lie","lie_derivative_squared"};
   const char*expr[]={c.def.expression,c.def.lie,c.def.normalized_lie,c.def.lie_sq};
   for(int k=0;k<4;++k)inventory<<c.def.model<<','<<c.def.id<<','<<kind[k]<<",\""<<expr[k]<<"\",paceval,paceval_dGetMultipleComputationsResultsExt,1,"<<int(c.def.known)<<"\n";
  }
  inventory<<"all,deterministic_samples,orchestration,,C++ host,analytic benchmark generator,0,0\n";
  inventory<<"all,aggregated_rms_and_roc,orchestration,,C++ host,aggregation and threshold decisions,0,0\n";
  ofstream summary(out/"results"/"execution_summary.csv");summary<<"metric,value\n";
  summary<<"candidate_invariants,36\npaceval_graphs,144\nobservational_noise_levels,4\ntrajectories_per_model,4\npoints_per_trajectory,"<<NS<<"\n";
  summary<<"paceval_sample_vectors,"<<totalInputs<<"\n";
  summary<<"batch_api_invocations,"<<engine.batch_invocations<<"\n";
  summary<<"multi_graph_batch_outputs,"<<engine.batch_outputs<<"\n";
  summary<<"scalar_sdk_calls,"<<engine.scalar_calls<<"\n";
  summary<<"analytic_lie_checks,"<<engine.audit.checked<<"\n";
  summary<<"analytic_lie_max_abs,"<<setprecision(17)<<engine.audit.worst<<"\n";
  summary<<"classification_rows,"<<allCandidates<<"\nselected_rows,"<<successful<<"\n";
  must(totalInputs>5000 || smoke,"too few genuinely evaluated points");
  cout<<"[SUCCESS] original paceval graphs=144, batch outputs="<<engine.batch_outputs<<" scalar="<<engine.scalar_calls<<" candidates="<<allCandidates<<"\n";
  return 0;
 }catch(const exception&e){cerr<<"FATAL: "<<e.what()<<"\n";return 1;}
}
