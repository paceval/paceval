// Real 2FLE FITS (450 measured source records) + original paceval SDK demonstration.
// Every mathematical spectral, integrated flux, uncertainty diagnostic and
// illustrative curvature function is evaluated by a real paceval computation handle.
// Inputs are the REAL NASA FITS power-law fit parameters, not simulated photons.
// No Fermitools ROI likelihood, measured spectral curvature, line search or
// technosignature inference is performed. Never conflate catalog fit products
// with independent science measurements or a detector-response analysis.
#include "paceval_main.h"
#include <fitsio.h>
#include <algorithm>
#include <array>
#include <cmath>
#include <filesystem>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <limits>
#include <map>
#include <set>
#include <sstream>
#include <stdexcept>
#include <string>
#include <vector>
using namespace std; namespace fs=std::filesystem;
namespace {
void require(bool v,const string&msg){if(!v)throw runtime_error(msg);}
string trim(string s){while(!s.empty()&&isspace(static_cast<unsigned char>(s.back())))s.pop_back();while(!s.empty()&&isspace(static_cast<unsigned char>(s.front())))s.erase(s.begin());return s;}
void fitsCheck(int s,const string&at){if(s){char err[80]="";fits_get_errstatus(s,err);throw runtime_error("CFITSIO "+at+": "+err);}}
string field(fitsfile*f,int col,long row){char value[FLEN_VALUE*2]="";char*arr[1]={value};int s=0,any=0;fits_read_col_str(f,col,row,1,1,nullptr,arr,&any,&s);fitsCheck(s,"read string col="+to_string(col));return trim(value);}
double numeric(fitsfile*f,int col,long row,int elem=1){double v=0;int s=0,any=0;fits_read_col(f,TDOUBLE,col,row,elem,1,nullptr,&v,&any,&s);fitsCheck(s,"numeric col="+to_string(col));return v;}
struct Source {string name,type,assoc1,assoc2,assoc3,cls;double ra,dec,glon,glat,a,b,pa,pivot,N,dN,g,dg,flux,dFlux,eflux,dEflux,ts,npred;int fluxflag;array<double,3> tsband,fluxband;};
vector<Source> load(const fs::path&name){int st=0,type=0;fitsfile*f=nullptr;fits_open_file(&f,name.string().c_str(),READONLY,&st);fitsCheck(st,"open FITS");fits_movabs_hdu(f,2,&type,&st);fitsCheck(st,"move to 2FLE HDU");require(type==BINARY_TBL,"HDU 2 must be binary table");long rows=0;int cols=0;fits_get_num_rows(f,&rows,&st);fits_get_num_cols(f,&cols,&st);fitsCheck(st,"table dimensions");require(rows==450&&cols==38,"expected original v8 450x38 FITS catalog");vector<Source> v;v.reserve(rows);set<string> names;
 for(long k=1;k<=rows;++k){Source z{};z.name=field(f,1,k);z.type=field(f,2,k);z.ra=numeric(f,3,k);z.dec=numeric(f,4,k);z.glon=numeric(f,5,k);z.glat=numeric(f,6,k);z.a=numeric(f,7,k);z.b=numeric(f,8,k);z.pa=numeric(f,9,k);z.pivot=numeric(f,11,k);z.N=numeric(f,12,k);z.dN=numeric(f,13,k);z.flux=numeric(f,14,k);z.dFlux=numeric(f,15,k);z.fluxflag=int(numeric(f,16,k));z.eflux=numeric(f,17,k);z.dEflux=numeric(f,18,k);z.g=numeric(f,19,k);z.dg=numeric(f,20,k);z.npred=numeric(f,21,k);z.ts=numeric(f,22,k);for(int b=0;b<3;++b){z.fluxband[b]=numeric(f,23,k,b+1);z.tsband[b]=numeric(f,25,k,b+1);}z.cls=field(f,29,k);z.assoc1=field(f,30,k);z.assoc2=field(f,31,k);z.assoc3=field(f,32,k);
 require(names.insert(z.name).second,"duplicate FITS source name");require(z.type=="PowerLaw","a non-PowerLaw FITS spectral type requires a separate model path");require(isfinite(z.N)&&z.N>0&&isfinite(z.pivot)&&z.pivot>0&&isfinite(z.g)&&isfinite(z.ts)&&z.ts>25,"invalid FITS spectral input");require(fabs(z.g-1)>1e-5&&fabs(z.g-2)>1e-5,"analytical integral singular; use logarithmic limit");v.push_back(z);}
 fits_close_file(f,&st);fitsCheck(st,"close FITS");return v;}
// Independent earlier report used for source-name SELECTION only, never for FITS values.
set<string> loadLegacy(const fs::path&p){ifstream f(p);require(bool(f),"missing legacy user-report source-name list");string line;getline(f,line);set<string>v;while(getline(f,line)){if(line.empty())continue;string name=line.substr(0,line.find(','));v.insert(name);}require(v.size()==60,"expected 60 source names in legacy list");return v;}
using Input=array<double,10>;
void validateInput(const Input& x){
 for(double z:x)require(isfinite(z),"nonfinite paceval input");
 require(x[0]>=20.0&&x[0]<=200.0,"energy outside 20-200 MeV");
 require(x[1]>0&&x[2]>0,"nonpositive differential normalization or pivot energy");
 require(x[4]>=0&&x[5]>=0&&x[6]>=0&&x[6]<=0.60000001,"negative uncertainty or illustrative curvature out of declared domain");
 require(x[7]>=0&&x[8]>=0&&x[9]>25,"invalid published ellipse / catalog TS");
}
void testInvalidInputs(){Input x={80,1e-9,100,2,1e-10,0.1,0.2,0.3,0.2,35};
 int errors=0;for(int test=0;test<5;++test){Input bad=x;
  if(test==0)bad[0]=10;else if(test==1)bad[1]=-1;else if(test==2)bad[6]=-0.1;
  else if(test==3)bad[7]=std::numeric_limits<double>::quiet_NaN();else bad[9]=0;
  try{validateInput(bad);}catch(const std::exception&){++errors;}}
 require(errors==5,"invalid-domain input tests failed");
}

// E: MeV, N: ph/cm2/MeV/s, P: MeV, g: fitted photon index, dN and dg:
// one-parameter standard errors from FITS, q: illustrative curvature only;
// a,b: 95%-ellipse semiaxes in degrees; S: published TS (NOT significance).
constexpr char VARNAMES[]="E N P g dN dg q a b S";
struct Formula {string id,expr,unit,meaning; PACEVAL_HANDLE h=nullptr;};
vector<Formula> registry(){string L="ln(E/P)",F="(N*exp(-g*"+L+"))";
 string I="(N*P/(1-g)*((200/P)^(1-g)-(20/P)^(1-g)))";
 string J="(1.602176634e-6*N*P*P/(2-g)*((200/P)^(2-g)-(20/P)^(2-g)))";
 string Fr="sqrt((dN/N)^2+(dg*"+L+")^2)";
 return {
 {"differential_powerlaw",F,"ph cm^-2 s^-1 MeV^-1","Published FITS power-law formula evaluated at E"},
 {"spectral_energy_distribution","(E^2*"+F+")","MeV ph cm^-2 s^-1","E squared times fitted differential flux"},
 {"pivot_normalized_ratio","exp(-g*"+L+")","dimensionless","F(E)/N"},
 {"log_differential_flux","ln(N)-g*"+L,"log differential flux in FITS units","Logarithm of differential flux"},
 {"index_sensitivity_log_flux","(-"+L+")","dimensionless","Derivative of log flux with respect to g"},
 {"catalog_powerlaw_photon_integral",I,"ph cm^-2 s^-1","Analytical PL 20..200 MeV integral"},
 {"catalog_powerlaw_energy_integral",J,"erg cm^-2 s^-1","Analytical energy flux 20..200 MeV integral"},
 {"independent_errors_fractional",Fr,"dimensionless","Diagnostic quadrature ignores N-g covariance"},
 {"independent_errors_flux",F+"*"+Fr,"ph cm^-2 s^-1 MeV^-1","Diagnostic only, not calibrated uncertainty"},
 {"plus_one_index_error", "N*exp(-(g+dg)*"+L+")","ph cm^-2 s^-1 MeV^-1","Index-only sensitivity curve"},
 {"minus_one_index_error", "N*exp(-(g-dg)*"+L+")","ph cm^-2 s^-1 MeV^-1","Index-only sensitivity curve"},
 {"illustrative_curved_spectrum", "N*exp(-g*"+L+"-q*"+L+"^2)","ph cm^-2 s^-1 MeV^-1","Hypothetical q; never fitted to real photons"},
 {"illustrative_log_flux_ratio","(-q*"+L+"^2)","dimensionless","Log of toy-curved over catalog PL"},
 {"illustrative_curvature_sensitivity","(-"+L+"^2)","dimensionless","Derivative wrt hypothetical curvature parameter"},
 {"localization_95_ellipse_area","3.14159265358979323846*a*b","deg^2","Small-angle planar area of 95-percent location ellipse"},
 {"signal_to_pivot_ratio", "E/P","dimensionless","Energy / fitted pivot"}
 };}
struct Engine {vector<PACEVAL_HANDLE>owned;Engine(){require(paceval_InitializeLibrary(nullptr),"paceval initialization failed");}~Engine(){for(auto h:owned)if(h)paceval_DeleteComputation(h);paceval_FreeLibrary();}PACEVAL_HANDLE create(const string&e){auto h=paceval_CreateComputation(e.c_str(),10,VARNAMES,false,nullptr);require(h&&!paceval_GetIsError(h),"paceval graph creation failed for "+e);owned.push_back(h);return h;}
vector<double> batch(const vector<PACEVAL_HANDLE>&hs,const vector<Input>&xs){require(!hs.empty()&&!xs.empty(),"empty batch");vector<double>inputs;inputs.reserve(xs.size()*10);for(auto&x:xs){validateInput(x);inputs.insert(inputs.end(),x.begin(),x.end());}auto hh=hs;vector<double>out(xs.size()*hs.size());vector<int>errors(out.size(),-999);
 // Verified SDK return convention: TRUE means failure, FALSE means success.
 bool failed=paceval_dGetMultipleComputationsResultsExt(hh.data(),(unsigned long)hh.size(),inputs.data(),(unsigned long)xs.size(),out.data(),nullptr,nullptr,errors.data());require(!failed,"paceval Multi-Graph batch failed");for(size_t i=0;i<out.size();++i)require(errors[i]==0&&isfinite(out[i]),"paceval batch invalid value at "+to_string(i));return out;}
};
Input xmake(const Source&s,double e,double q=0){return {e,s.N,s.pivot,s.g,fabs(s.dN),fabs(s.dg),q,s.a,s.b,s.ts};}
void oracle(const vector<double>&out,const vector<Input>&inputs,int ngraph,double&maxErr,size_t&testCount){for(size_t j=0;j<inputs.size();j+=max(size_t(1),inputs.size()/5)){const auto&x=inputs[j];double E=x[0],N=x[1],P=x[2],g=x[3],dN=x[4],dg=x[5],q=x[6],a=x[7],b=x[8],L=log(E/P),flux=N*exp(-g*L),r=sqrt(pow(dN/N,2)+pow(dg*L,2));double expected[]={flux,E*E*flux,exp(-g*L),log(N)-g*L,-L,N*P/(1-g)*(pow(200/P,1-g)-pow(20/P,1-g)),1.602176634e-6*N*P*P/(2-g)*(pow(200/P,2-g)-pow(20/P,2-g)),r,flux*r,N*exp(-(g+dg)*L),N*exp(-(g-dg)*L),N*exp(-g*L-q*L*L),-q*L*L,-L*L,3.14159265358979323846*a*b,E/P};
 for(int k=0;k<ngraph;++k){double val=out[size_t(k)*inputs.size()+j],absErr=fabs(val-expected[k]);maxErr=max(maxErr,absErr/(1+fabs(expected[k])));require(absErr<=1e-9*(1+fabs(expected[k])),"oracle mismatch graph="+to_string(k));++testCount;}}}
void writeCSVSource(ostream&o,const Source&s){o<<s.name<<','<<s.ra<<','<<s.dec<<','<<s.glon<<','<<s.glat<<','<<s.ts<<','<<s.pivot<<','<<s.N<<','<<s.dN<<','<<s.g<<','<<s.dg<<','<<s.flux<<','<<s.dFlux<<','<<s.eflux<<','<<s.dEflux<<','<<s.a<<','<<s.b<<','<<s.pa<<','<<s.npred<<','<<s.tsband[0]<<','<<s.tsband[1]<<','<<s.tsband[2]<<','<<s.fluxband[0]<<','<<s.fluxband[1]<<','<<s.fluxband[2]<<','<<s.fluxflag<<','<<s.type<<','<<s.cls<<','<<s.assoc1<<','<<s.assoc2<<','<<s.assoc3;}
string head="source_name,RA_deg,DEC_deg,GLON_deg,GLAT_deg,TS,pivot_MeV,flux_density_ph_cm2_MeV_s,unc_flux_density,photon_index,unc_photon_index,fit_flux_ph_cm2_s,unc_fit_flux,fit_energy_flux_erg_cm2_s,unc_fit_energy_flux,95_ellipse_major_deg,95_ellipse_minor_deg,95_ellipse_PA_deg,Npred,TS_band_1,TS_band_2,TS_band_3,flux_density_band_1,flux_density_band_2,flux_density_band_3,flux_flag,spectrum_type,class,ASSOC1,ASSOC2,ASSOC3";
void run(const fs::path&fits,const fs::path&legacy,const fs::path&outDir,int limit){fs::create_directories(outDir/"examples");fs::create_directories(outDir/"results");testInvalidInputs();auto all=load(fits);auto target=loadLegacy(legacy);map<string,int>index;for(int i=0;i<(int)all.size();++i)index[all[i].name]=i;vector<Source>v;for(const string&name:target){auto it=index.find(name);require(it!=index.end(),"legacy source not found in original FITS: "+name);v.push_back(all[it->second]);}require(v.size()==60,"exact 60 original FITS sources required");sort(v.begin(),v.end(),[](const auto&a,const auto&b){return a.ts>b.ts;});int ass3=0,bands3=0,allHighLat=0;for(const auto&s:v){ass3+=!s.assoc3.empty();int usable=0;for(double ts:s.tsband)usable+=ts>=4;bands3+=usable==3;allHighLat+=fabs(s.glat)>10;}
 require(ass3==38,"ASSOC3 count is not 38 in FITS for 60 selected names");require(bands3==10,"TS_Band >=4 in all 3 differs from PDF count");
 {ofstream f(outDir/"examples/real_450_original_fits.csv");f<<head<<'\n'<<setprecision(16);for(auto&s:all){writeCSVSource(f,s);f<<'\n';}}
 {ofstream f(outDir/"examples/real_60_original_fits.csv");f<<head<<'\n'<<setprecision(16);for(auto&s:v){writeCSVSource(f,s);f<<'\n';}}
 Engine sdk;auto registryData=registry();vector<PACEVAL_HANDLE>hs;for(auto&f:registryData){f.h=sdk.create(f.expr);hs.push_back(f.h);}const int ng=int(hs.size());
 {ofstream f(outDir/"examples/paceval_formula_registry.csv");f<<"id,function,units,expression,interpretation\n";for(int k=0;k<ng;k++)f<<k+1<<','<<registryData[k].id<<",\""<<registryData[k].unit<<"\",\""<<registryData[k].expr<<"\",\""<<registryData[k].meaning<<"\"\n";}
 {ofstream f(outDir/"results/math_execution_inventory.csv");f<<"function,owner,execution,validation,meaning\n";for(auto&t:registryData)f<<t.id<<",paceval,paceval_dGetMultipleComputationsResultsExt,independent_C++_and_mpmath,\""<<t.meaning<<"\"\n";f<<"read_original_FITS,CFITSIO,read columns and maintain source provenance,verified 450 rows,not mathematical execution\n"<<"select_exact_new_60,C++ host,match source names to previous V4 report,crosschecked 60 and ASSOC3,classification not inferred\n"<<"photon_IRF_folding,NOT_PERFORMED,requires event spacecraft exposure and IRFs,not tested,not inferable from this FITS\n";}
 size_t batchCount=0,graphOutputs=0,referenceChecks=0;double maxRelative=0;const int chunk=128;
 auto eval=[&](const vector<Input>&inputs,auto accept){for(size_t st=0;st<inputs.size();st+=chunk){size_t n=min(size_t(chunk),inputs.size()-st);vector<Input>xx(inputs.begin()+st,inputs.begin()+st+n);auto out=sdk.batch(hs,xx);++batchCount;graphOutputs+=out.size();oracle(out,xx,ng,maxRelative,referenceChecks);for(size_t j=0;j<n;++j){auto get=[&](int idx){return out[size_t(idx)*n+j];};accept(st+j,get);}}};
 vector<Input>one;one.reserve(450);for(auto&s:all)one.push_back(xmake(s,s.pivot));
 {ofstream f(outDir/"examples/real_450_paceval_consistency.csv");f<<"source_name,published_photon_flux,published_energy_flux_erg,pv_integrated_photon_flux,pv_integrated_energy_flux_erg,relative_photon_residual,relative_energy_residual,ellipse95_area_deg2,original_fit_index,TS,fit_flux_flag\n"<<setprecision(16);
 eval(one,[&](size_t i,auto get){auto&s=all[i];double I=get(5),J=get(6);f<<s.name<<','<<s.flux<<','<<s.eflux<<','<<I<<','<<J<<','<<(I/s.flux-1)<<','<<(J/s.eflux-1)<<','<<get(14)<<','<<s.g<<','<<s.ts<<','<<s.fluxflag<<'\n';});}
 int n=limit>0?min(limit,60):60;vector<Input>samples;constexpr int ns=81;samples.reserve(n*ns);for(int k=0;k<n;++k)for(int i=0;i<ns;++i){double E=20*pow(10.,i/80.);samples.push_back(xmake(v[k],E,0.2));}
 {ofstream f(outDir/"examples/real_60_paceval_spectral_samples.csv");f<<"source_name,E_MeV,published_normalization,pivot_MeV,published_index,published_index_uncertainty,paceval_powerlaw_flux,paceval_SED_E2_flux,paceval_index_dlogflux,paceval_fractional_error_diagnostic,paceval_flux_error_diagnostic,paceval_index_plus_error_flux,paceval_index_minus_error_flux,paceval_toy_curvature_q02_flux,paceval_toy_curvature_log_ratio\n"<<setprecision(16);
 eval(samples,[&](size_t i,auto get){const auto&s=v[i/ns];f<<s.name<<','<<samples[i][0]<<','<<s.N<<','<<s.pivot<<','<<s.g<<','<<s.dg<<','<<get(0)<<','<<get(1)<<','<<get(4)<<','<<get(7)<<','<<get(8)<<','<<get(9)<<','<<get(10)<<','<<get(11)<<','<<get(12)<<'\n';});}
 vector<Input>surface;surface.reserve(65*65);for(int i=0;i<65;++i){double E=20*pow(10.,i/64.);for(int j=0;j<65;++j){double q=0.6*j/64.;surface.push_back(xmake(v[0],E,q));}}
 {ofstream f(outDir/"examples/paceval_curvature_sensitivity_surface_HYPOTHETICAL.csv");f<<"source_name,E_MeV,toy_curvature_q,paceval_catalog_powerlaw_flux,paceval_illustrative_curved_flux,paceval_log_ratio,paceval_curvature_derivative\n"<<setprecision(16);
 eval(surface,[&](size_t i,auto get){f<<v[0].name<<','<<surface[i][0]<<','<<surface[i][6]<<','<<get(0)<<','<<get(11)<<','<<get(12)<<','<<get(13)<<'\n';});}
 {ofstream f(outDir/"results/original_fits_catalog_summary.txt");f<<setprecision(15)<<"ORIGINAL_FITS=true\nHDU2_ROWS=450\nHDU2_COLUMNS=38\nMATCHED_PREVIOUS_60_NAMES=60\nSOURCE_ASSOC3_NONEMPTY_IN_60="<<ass3<<"\nSOURCE_ASSOC3_EMPTY_IN_60="<<60-ass3<<"\nSOURCES_TS_BAND_ALL_3_GE4="<<bands3<<"\nSOURCES_ABS_LATITUDE_GT10="<<allHighLat<<"\nPACEVAL_GRAPHS="<<ng<<"\nPACEVAL_BATCH_INVOCATIONS="<<batchCount<<"\nPACEVAL_GRAPH_OUTPUTS="<<graphOutputs<<"\nINDEPENDENT_CXX_VALUES_CHECKED="<<referenceChecks<<"\nINVALID_INPUTS_REJECTED=5\nMAX_SCALED_REFERENCE_DIFFERENCE="<<maxRelative<<"\nPHOTON_DATA_USED=false\nFERMITOOLS_IRF_OR_LIKELIHOOD_USED=false\nSOURCE_CLASSIFICATION_OR_TECHNOSIGNATURE=false\n";}
 cout<<"PASS actual 2FLE FITS 450 rows; selected 60; ASSOC3="<<ass3<<"; threeTSbands="<<bands3<<"; pacevalGraphs="<<ng<<" batchOutputs="<<graphOutputs<<" independentChecks="<<referenceChecks<<'\n';}
}
int main(int argc,char**argv){try{fs::path fits="data/2FLE_psc_v8.fits",legacy="data/legacy_60_report_metadata.csv",out=".";int limit=0;for(int i=1;i<argc;++i){string k=argv[i];if(k=="--fits"&&i+1<argc)fits=argv[++i];else if(k=="--legacy"&&i+1<argc)legacy=argv[++i];else if(k=="--out"&&i+1<argc)out=argv[++i];else if(k=="--limit"&&i+1<argc)limit=stoi(argv[++i]);else throw runtime_error("Usage: --fits PATH --legacy PATH --out DIR [--limit N] ");}run(fits,legacy,out,limit);return 0;}catch(const exception&e){cerr<<"FAIL "<<e.what()<<'\n';return 1;}}
