// Fermi 2FLE paceval batch expression research demonstrator, 13 Nov 2026.
// The 60 metadata rows come from the user-supplied V4 paper, NOT a FITS import.
// All photon counts are deterministic SYNTHETIC toy counts. This code performs NO
// LAT photon likelihood analysis, IRF folding, cross-survey matching or detection.
// Scientific role: verify persistent paceval graph reuse for model families,
// Poisson-style synthetic objective contributions, parameter sweeps and derivatives.
// Host role: parse metadata, seed random counts, coordinate batches, sum bins,
// choose synthetic best-fit curvature, write results, independent reference.
#include "paceval_main.h"
#include <array>
#include <algorithm>
#include <cmath>
#include <filesystem>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <limits>
#include <map>
#include <numeric>
#include <random>
#include <sstream>
#include <stdexcept>
#include <string>
#include <vector>
using namespace std;
namespace fs=std::filesystem;
namespace {
void check(bool b,const string& m){if(!b)throw runtime_error(m);}
using X=array<double,8>; // E_MeV,N_norm,gamma,q,bkg_counts,exposure_scale,bin_weight,observed_counts
constexpr char VARS[]="E N g q b ex w n";
constexpr int FORMULAS=17;
struct Source{string name,assoc,group;double ts,lat;int bands;};
vector<string> csvFields(const string&s){vector<string>v;string z;bool quoted=false;for(size_t k=0;k<s.size();++k){char c=s[k];if(c=='\"'){if(quoted&&k+1<s.size()&&s[k+1]=='\"'){z+='\"';++k;}else quoted=!quoted;}else if(c==','&&!quoted){v.push_back(z);z.clear();}else z+=c;}v.push_back(z);return v;}
vector<Source> readSources(const fs::path&path){ifstream f(path);check(bool(f),"missing source metadata csv: "+path.string());string s;getline(f,s);vector<Source>v;while(getline(f,s)){if(s.empty())continue;auto a=csvFields(s);check(a.size()==7,"invalid source CSV row");v.push_back({a[0],a[4],a[5],stod(a[1]),stod(a[2]),stoi(a[3])});}
 check(v.size()==60,"must have precisely 60 PDF transcription rows");int unconfirmed=0,noband=0,all3=0;map<string,int>names;for(const auto&z:v){check(++names[z.name]==1,"duplicate source name");if(z.group=="has_ASSOC3")++unconfirmed;else{check(z.assoc.empty(),"unexpected assoc flag");++noband;}if(z.bands==3)++all3;check(z.ts>25&&isfinite(z.lat)&&fabs(z.lat)<=90,"metadata validity");}
 check(unconfirmed==38&&noband==22&&all3==10,"catalog transcription totals not reproduced");return v;}
struct Formula{string id,expr,unit;PACEVAL_HANDLE handle=nullptr;};
vector<Formula> formulas(){
 const string x="ln(E/100)";
 const string pl="(N*exp(-g*"+x+"))";
 const string lp="(N*exp(-g*"+x+"-q*"+x+"^2))";
 const string cutoff="(N*exp(-g*"+x+"-(E-100)/500))";
 const string smooth="(N*exp(-g*"+x+")*(1+E/120)^(-0.25))";
 const string lp2="(N*exp(-g*"+x+"-q*"+x+"^2-0.08*"+x+"^3))";
 const string m0="(b+ex*w*"+pl+")",m1="(b+ex*w*"+lp+")",m2="(b+ex*w*"+cutoff+")",m3="(b+ex*w*"+lp2+")";
 const string ll0="(n*ln("+m0+")-"+m0+")",ll1="(n*ln("+m1+")-"+m1+")",ll2="(n*ln("+m3+")-"+m3+")";
 return {
 {"power_law_flux",pl,"arbitrary synthetic spectral units"},
 {"log_parabola_flux_v1",lp,"arbitrary synthetic spectral units"},
 {"cutoff_reference_flux",cutoff,"arbitrary synthetic spectral units"},
 {"smooth_bend_reference_flux",smooth,"arbitrary synthetic spectral units"},
 {"log_parabola_flux_v2",lp2,"arbitrary synthetic spectral units"},
 {"log_flux_ratio_lp_to_pl","(-q*"+x+"^2)","dimensionless"},
 {"sensitivity_log_flux_dq","(-"+x+"^2)","dimensionless"},
 {"expected_counts_power_law",m0,"synthetic toy counts"},
 {"expected_counts_lp_v1",m1,"synthetic toy counts"},
 {"expected_counts_cutoff",m2,"synthetic toy counts"},
 {"expected_counts_lp_v2",m3,"synthetic toy counts"},
 {"poisson_loglikelihood_lp_no_factorial",ll1,"synthetic log likelihood contribution"},
 {"poisson_deviance_lp","(2*("+m1+"-n+n*ln((n+1e-16)/"+m1+")))","synthetic per-bin deviance"},
 {"pearson_residual_lp","((n-"+m1+")/sqrt("+m1+"))","dimensionless"},
 {"poisson_loglikelihood_pl_no_factorial",ll0,"synthetic log likelihood contribution"},
 {"loglikelihood_delta_lp_minus_pl","("+ll1+"-"+ll0+")","synthetic log likelihood contribution"},
 {"poisson_loglikelihood_lp_v2_no_factorial",ll2,"synthetic log likelihood contribution"}
 };}
void validate(const X&x){for(double v:x)check(isfinite(v),"non-finite math input");check(x[0]>=20&&x[0]<=200,"outside 20..200 MeV");check(x[1]>=0&&x[1]<=60&&x[2]>=0.1&&x[2]<=4.5,"spectral parameters outside domain");check(x[3]>=0&&x[3]<=0.8&&x[4]>=0&&x[5]>0&&x[6]>0&&x[7]>=0,"counts/parameters invalid");}
struct Engine{
 vector<PACEVAL_HANDLE>owned;
 Engine(){check(paceval_InitializeLibrary(nullptr),"paceval_InitializeLibrary failed");}
 ~Engine(){for(auto h:owned)if(h)paceval_DeleteComputation(h);paceval_FreeLibrary();}
 PACEVAL_HANDLE reg(const string&e){auto h=paceval_CreateComputation(e.c_str(),8,VARS,false,nullptr);check(h&&!paceval_GetIsError(h),"failed to register paceval graph: "+e.substr(0,140));owned.push_back(h);return h;}
 vector<double> multi(const vector<PACEVAL_HANDLE>&hs,const vector<X>&xs){check(!xs.empty()&&!hs.empty(),"empty batch");vector<double>input;input.reserve(xs.size()*8);for(const auto&x:xs){validate(x);input.insert(input.end(),x.begin(),x.end());}
 vector<double>out(xs.size()*hs.size(),0.0);vector<int>errors(out.size(),-999);auto handles=hs;
 // This API returns TRUE on error, FALSE on success in the tested paceval release.
 bool failed=paceval_dGetMultipleComputationsResultsExt(handles.data(),(unsigned long)handles.size(),input.data(),(unsigned long)xs.size(),out.data(),nullptr,nullptr,errors.data());
 check(!failed,"real paceval Multi-Graph batch returned error");for(size_t j=0;j<out.size();++j)check(errors[j]==0&&isfinite(out[j]),"invalid paceval batch output at "+to_string(j));return out;
 }
 double scalar(PACEVAL_HANDLE h,const X&x){validate(x);auto a=x;double y=paceval_dGetComputationResult(h,a.data(),nullptr,nullptr);check(!paceval_GetIsError(h)&&isfinite(y),"scalar paceval error");return y;}
};
// Independent native C++ oracle for TESTING ONLY; no native spectral mathematics
// are used as outputs of the study.
double reference(int i,const X&z){double E=z[0],N=z[1],g=z[2],q=z[3],b=z[4],ex=z[5],w=z[6],n=z[7],xx=log(E/100);
 double pl=N*exp(-g*xx),lp=N*exp(-g*xx-q*xx*xx),cut=N*exp(-g*xx-(E-100)/500),s=N*exp(-g*xx)*pow(1+E/120,-.25),lp2=N*exp(-g*xx-q*xx*xx-0.08*xx*xx*xx);
 double m0=b+ex*w*pl,m1=b+ex*w*lp,m2=b+ex*w*cut,m3=b+ex*w*lp2;
 double vals[]={pl,lp,cut,s,lp2,-q*xx*xx,-xx*xx,m0,m1,m2,m3,n*log(m1)-m1,2*(m1-n+n*log((n+1e-16)/m1)),(n-m1)/sqrt(m1),n*log(m0)-m0,(n*log(m1)-m1)-(n*log(m0)-m0),n*log(m3)-m3};
 check(i>=0&&i<FORMULAS,"oracle index invalid");return vals[i];}
void same(double a,double b,const string&which,double&maxerror){double d=fabs(a-b);maxerror=max(d,maxerror);check(d<=2e-9*(1+fabs(b)),"reference mismatch: "+which+": "+to_string(a)+" vs "+to_string(b));}
void writeInventory(const fs::path&r,const vector<Formula>&f){ofstream out(r/"results/math_execution_inventory.csv");out<<"function_id,domain_quantity,mathematical_definition,units,execution_owner,paceval_graph_id,formula_version,api_path,reference_test,status,host_reason\n";
 for(size_t i=0;i<f.size();++i){const auto&v=f[i];out<<v.id<<','<<v.id<<",\""<<v.expr<<"\",\""<<v.unit<<"\",paceval,"<<(i+1)<<','<<(v.id.find("_v2")!=string::npos?"v2":"v1")<<",paceval_dGetMultipleComputationsResultsExt,independent_C++_and_mpmath,PASS,\n";}
 out<<"synthetic_poisson_draw,stochastic_count_generation,std_poisson_distribution,count,host,,,cpp_random,seed_replay,PASS,random_state_not_math_expression\n";
 out<<"bin_aggregation,source_loglikelihood,sum_bin_contributions,loglikelihood,host,,,host_reduction,independent_sum,PASS,stateful_sum_across_bins\n";
 out<<"maximization,curvature_argmax,select_best_fixed_grid,dimensionless,host,,,host_selection,finite_grid_check,PASS,selection_not_single_expression\n";
 out<<"metadata_ingestion,PDF_catalog_metadata_source,read_and_verify_60_rows,metadata,host,,,CSV_loader,counts_and_uniqueness,PASS,source_provenance\n";
 out<<"LAT_IRF_forward_folding,instrument_response_integral,not_implemented,counts,not_implemented,,,Fermitools_required,not_performed,NOT_DONE,requires_photon_spacecraft_IRF_diffuse_data\n";}
void testInvalid(){int passes=0;X z{60,9,2,.2,4,50,.15,10};vector<X> bad;auto a=z;a[0]=10;bad.push_back(a);a=z;a[3]=-.1;bad.push_back(a);a=z;a[7]=-3;bad.push_back(a);a=z;a[1]=numeric_limits<double>::quiet_NaN();bad.push_back(a);
 for(const auto&v:bad){try{validate(v);}catch(const exception&){passes++;}}check(passes==4,"invalid input tests failed");}
struct Mock{double N,g,q,b,ex,w;vector<double>E,n,mu;};
vector<Mock> syntheticObservations(Engine&eng,PACEVAL_HANDLE muGraph,int sources,int bins,double&maxerr,int&checked){vector<Mock>v;vector<X>input;input.reserve(sources*bins);for(int k=0;k<sources;++k){Mock m{};m.N=7.5+0.12*(k%13);m.g=1.48+0.035*(k%11);m.q=(k%3==0?0.0:(k%3==1?0.17:0.40));m.b=3.5+0.2*(k%5);m.ex=30;m.w=.12;
 for(int j=0;j<bins;++j){double E=20*pow(10,(j+.5)/double(bins));m.E.push_back(E);input.push_back({E,m.N,m.g,m.q,m.b,m.ex,m.w,0});}v.push_back(move(m));}
 // The mathematical model used to generate the synthetic count expectation is itself computed by paceval.
 vector<double>mu=eng.multi({muGraph},input);std::mt19937_64 rng(20261113002ULL);for(int k=0;k<sources;++k){for(int j=0;j<bins;++j){int idx=k*bins+j;check(mu[idx]>0,"nonpositive synthetic count mean");if(idx%53==0){same(mu[idx],reference(8,input[idx]),"toy mean",maxerr);++checked;}
 std::poisson_distribution<int>dist(mu[idx]);v[k].mu.push_back(mu[idx]);v[k].n.push_back(double(dist(rng)));}}
 return v;}
void run(const fs::path&root,int sources,int bins,int grid){check(sources>=3&&sources<=60&&bins>=8&&bins<=128&&grid>=11&&grid<=121,"invalid workload size");auto catalog=readSources(root/"examples/unidentified_60_from_user_whitepaper.csv");fs::create_directories(root/"results");fs::create_directories(root/"examples");
 Engine eng;auto f=formulas();check(f.size()==FORMULAS,"formula count error");vector<PACEVAL_HANDLE>handles;for(auto&v:f){v.handle=eng.reg(v.expr);handles.push_back(v.handle);}writeInventory(root,f);
 ofstream reg(root/"examples/formula_registry.csv");reg<<"graph_id,function_id,units,expression\n";for(int i=0;i<FORMULAS;++i)reg<<i+1<<','<<f[i].id<<",\""<<f[i].unit<<"\",\""<<f[i].expr<<"\"\n";reg.close();
 double errmax=0;int checked=0;
 auto mock=syntheticObservations(eng,handles[8],sources,bins,errmax,checked);
 // Scalar-to-batch parity and native oracle on a physically meaningful synthetic record.
 X probe{60,8,1.7,.22,3.7,30,.12,14};auto p=eng.multi(handles,{probe});for(int i=0;i<FORMULAS;++i){same(p[i],eng.scalar(handles[i],probe),f[i].id,errmax);same(p[i],reference(i,probe),f[i].id,errmax);checked+=2;}
 ofstream inputCsv(root/"examples/synthetic_photon_counts.csv");inputCsv<<"source_name,energy_center_MeV,synthetic_observed_counts,paceval_expected_counts_truth,synthetic_model_true_q,synthetic_N,synthetic_gamma,synthetic_background_counts,exposure_scale,bin_weight,source_metadata_flag\n"<<setprecision(17);
 for(int i=0;i<sources;++i)for(int j=0;j<bins;++j)inputCsv<<catalog[i].name<<','<<mock[i].E[j]<<','<<mock[i].n[j]<<','<<mock[i].mu[j]<<','<<mock[i].q<<','<<mock[i].N<<','<<mock[i].g<<','<<mock[i].b<<','<<mock[i].ex<<','<<mock[i].w<<','<<catalog[i].group<<'\n';
 inputCsv.close();
 ofstream scan(root/"examples/synthetic_curvature_parameter_scan.csv");scan<<"source_name,truth_q,trial_q,synthetic_loglikelihood_lp,synthetic_loglikelihood_pl,synthetic_deviance,total_spectral_delta_loglike\n"<<setprecision(17);
 ofstream rec(root/"examples/synthetic_injection_recovery.csv");rec<<"source_name,metadata_TS_not_used_in_fit,truth_q,best_grid_q,synthetic_best_loglikelihood,synthetic_reference_q0_loglikelihood,synthetic_doubled_delta_loglikelihood,source_association_flag\n"<<setprecision(17);
 ofstream selected(root/"examples/synthetic_spectral_example.csv");selected<<"energy_MeV,simulated_counts,simulated_expected_lp_truth,lp_flux_truth,powerlaw_flux,cutoff_flux,smooth_flux,lp_flux_v2,log_flux_ratio,sensitivity_dlogflux_dq\n"<<setprecision(17);
 size_t outputCount=0,batchCalls=0;const size_t chunk=256;int recovered=0;
 for(int k=0;k<sources;++k){vector<double>scores(grid,0),base(grid,0),deviances(grid,0),deltas(grid,0);vector<X> all;all.reserve(grid*bins);
  for(int a=0;a<grid;++a){double q=.6*a/double(grid-1);for(int j=0;j<bins;++j){auto&m=mock[k];all.push_back({m.E[j],m.N,m.g,q,m.b,m.ex,m.w,m.n[j]});}}
  for(size_t st=0;st<all.size();st+=chunk){size_t n=min(chunk,all.size()-st);vector<X> x(all.begin()+st,all.begin()+st+n);auto out=eng.multi(handles,x);batchCalls++;outputCount+=out.size();
   for(size_t ii=0;ii<n;++ii){size_t ind=st+ii;int a=int(ind/bins);auto get=[&](int idx){return out[size_t(idx)*n+ii];};scores[a]+=get(11);base[a]+=get(14);deviances[a]+=get(12);deltas[a]+=get(15);
    if(ind%83==0){for(int idx:{0,1,4,6,8,11,12,14,15,16}){same(get(idx),reference(idx,x[ii]),f[idx].id,errmax);++checked;}}
    if(k==0&&a==0){selected<<x[ii][0]<<','<<x[ii][7]<<','<<mock[k].mu[size_t(ind%bins)]<<','<<get(1)<<','<<get(0)<<','<<get(2)<<','<<get(3)<<','<<get(4)<<','<<get(5)<<','<<get(6)<<'\n';}
   }}
  int best=int(max_element(scores.begin(),scores.end())-scores.begin());double bestq=.6*best/double(grid-1);if(fabs(bestq-mock[k].q)<=.05)recovered++;
  for(int a=0;a<grid;++a)scan<<catalog[k].name<<','<<mock[k].q<<','<<.6*a/double(grid-1)<<','<<scores[a]<<','<<base[a]<<','<<deviances[a]<<','<<deltas[a]<<'\n';
  rec<<catalog[k].name<<','<<catalog[k].ts<<','<<mock[k].q<<','<<bestq<<','<<scores[best]<<','<<scores[0]<<','<<2*(scores[best]-scores[0])<<','<<catalog[k].group<<'\n';}
 // Separate two-dimensional analytically controlled study: ALL values computed by paceval.
 vector<X>surf;for(int i=0;i<65;++i)for(int j=0;j<65;++j){double E=20*pow(10,i/64.),q=.6*j/64.;surf.push_back({E,9,1.8,q,4,30,.12,20});}
  ofstream sf(root/"examples/synthetic_spectral_surface.csv");sf<<"energy_MeV,curvature_q,flux_powerlaw,flux_lp_v1,flux_lp_v2,expected_counts_lp,log_likelihood_lp,deviance_lp,log_flux_ratio,sensitivity_logflux_dq\n"<<setprecision(17);
 for(size_t st=0;st<surf.size();st+=256){size_t n=min(size_t(256),surf.size()-st);vector<X>x(surf.begin()+st,surf.begin()+st+n);auto out=eng.multi(handles,x);batchCalls++;outputCount+=out.size();
  for(size_t i=0;i<n;++i){auto get=[&](int id){return out[size_t(id)*n+i];};sf<<x[i][0]<<','<<x[i][3]<<','<<get(0)<<','<<get(1)<<','<<get(4)<<','<<get(8)<<','<<get(11)<<','<<get(12)<<','<<get(5)<<','<<get(6)<<'\n';if((st+i)%169==0){for(int id:{0,1,4,8,11,12,5,6}){same(get(id),reference(id,x[i]),f[id].id,errmax);checked++;}}}}
 testInvalid();ofstream summary(root/"results/execution_summary.txt");summary<<"project=Fermi_2FLE_source_catalog_and_synthetic_spectral_pilot\n"<<"status=PASS\n"<<"catalog_metadata_sources_transcribed_from_user_pdf=60\n"<<"original_2FLE_FITS_and_photon_events_available=NO\n"<<"catalog_total_claim_from_original_paper_not_independently_recounted=450\n"<<"unconfirmed_ASSOC3_metadata=38\n"<<"no_ASSOC3_metadata=22\n"<<"three_usable_bands_metadata=10\n"<<"genuine_paceval_graphs="<<FORMULAS<<"\n"<<"synthetic_source_count="<<sources<<"\n"<<"synthetic_energy_bins_per_source="<<bins<<"\n"<<"synthetic_curvature_grid_per_source="<<grid<<"\n"<<"synthetic_model_candidates="<<sources*grid<<"\n"<<"batch_evaluated_graph_values="<<outputCount+size_t(sources*bins)<<"\n"<<"batch_invocations="<<batchCalls+1<<"\n"<<"native_reference_checked_values="<<checked<<"\n"<<"synthetic_recovery_within_0.05_count="<<recovered<<"\n"<<"invalid_inputs_rejected=4\n"<<"instrument_response_forward_likelihood_performed=NO\n"<<"crossmatches_performed=NO\n"<<"technosignatures_detected=NOT_TESTED\n"<<setprecision(17)<<"internal_maximum_absolute_reference_difference="<<errmax<<"\n";
 cout<<"PASS real paceval; sources_metadata=60 synthetic_sources="<<sources<<" graphs="<<FORMULAS<<" batch_results="<<outputCount+size_t(sources*bins)<<" native_reference_checks="<<checked<<"\n";
}
}
int main(int argc,char**argv){try{fs::path root=".";int n=60,bins=24,grid=61;for(int i=1;i<argc;++i){string z=argv[i];if(z=="--out"&&i+1<argc)root=argv[++i];else if(z=="--sources"&&i+1<argc)n=stoi(argv[++i]);else if(z=="--bins"&&i+1<argc)bins=stoi(argv[++i]);else if(z=="--grid"&&i+1<argc)grid=stoi(argv[++i]);else throw runtime_error("Usage: fermi_2fle_demo --out DIR [--sources 60] [--bins 24] [--grid 61]");}run(root,n,bins,grid);return 0;}catch(const exception&e){cerr<<"FAIL: "<<e.what()<<'\n';return 2;}}
