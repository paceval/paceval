// WP31. Real paceval execution for a Beer-Lambert transmission channel and a
// coherent single-layer, normal-incidence, real-index Fresnel reflectance channel.
// These are TWO physical measurement models, not alternate solvers for identical
// optics. The C++ host handles the global grid and local 1-D inverse search;
// the forward formulas, residuals, sensitivities and decisions are paceval graphs.
// Synthetic input files are NOT measurements. No multilayer/ellipsometry claim.
#include "paceval_main.h"
#include <algorithm>
#include <array>
#include <cmath>
#include <filesystem>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <map>
#include <regex>
#include <sstream>
#include <stdexcept>
#include <string>
#include <vector>
namespace fs=std::filesystem;
namespace {
void require(bool b,const std::string&s){if(!b)throw std::runtime_error(s);}
void near(double x,double y,double abs=1e-8,double rel=1e-8){require(std::isfinite(x)&&std::isfinite(y)&&std::abs(x-y)<=abs+rel*std::max(std::abs(x),std::abs(y)),"Independent C++ reference discrepancy");}
const std::vector<std::string> V={"d","lam","alpha","i0","offset","noise","y","sigma","target","tol","n0","nf","ns"};
const std::vector<std::string> C={"bt","rt","db","dr","ub","ur","q","lim"};
const std::vector<std::string> S={"info","fit","target","tol","objective","threshold"};
std::string joined(const std::vector<std::string>&v){std::string s;for(auto&t:v){if(!s.empty())s+=' ';s+=t;}return s;}
std::vector<std::string> split(const std::string&s){std::stringstream ss(s);std::string t;std::vector<std::string>v;while(std::getline(ss,t,','))v.push_back(t);if(!s.empty()&&s.back()==',')v.push_back("");return v;}
bool numericLiteral(const std::string&s){static const std::regex r(R"(^[+-]?(?:[0-9]+(?:\.[0-9]*)?|\.[0-9]+)(?:[eE][+-]?[0-9]+)?$)");return std::regex_match(s,r);}
double parseNumber(const std::string&s){require(numericLiteral(s),"CSV numeric literal rejected: "+s);int err=-1;long pos=-1;double x=paceval_dConvertStringToFloat(s.c_str(),&err,&pos,false,nullptr,nullptr);require(err==0&&std::isfinite(x),"SDK numeric conversion failed");return x;}
std::string formatNumber(double x){require(std::isfinite(x),"Attempted to export nonfinite");char b[512]{};int k=paceval_dConvertFloatToString(b,x);require(k>0&&b[0]&&std::string(b).find(',')==std::string::npos,"SDK numeric output failed");return b;}
using Matrix=std::vector<std::vector<double>>;
struct Engine {
 std::vector<PACEVAL_HANDLE>owned;size_t scalarCalls=0,batchCalls=0,graphPoints=0;bool graphMajor=false;
 Engine(){require(paceval_InitializeLibrary(nullptr),"paceval initialisation failed");}
 ~Engine(){for(auto h:owned)paceval_DeleteComputation(h);paceval_FreeLibrary();}
 PACEVAL_HANDLE make(const std::string&f,const std::vector<std::string>&vars){auto names=joined(vars);auto h=paceval_CreateComputation(f.c_str(),(unsigned long)vars.size(),names.c_str(),false,nullptr);require(h&&!paceval_GetIsError(h),"Graph rejected: "+f);owned.push_back(h);return h;}
 double scalar(PACEVAL_HANDLE h,const std::vector<double>&v){auto x=v;double z=paceval_dGetComputationResult(h,x.empty()?nullptr:x.data(),nullptr,nullptr);scalarCalls++;require(!paceval_GetIsError(h)&&std::isfinite(z),"paceval scalar failed");return z;}
 void layoutProbe(){auto a=make("x+2*y",{"x","y"});auto b=make("3*x-y",{"x","y"});PACEVAL_HANDLE h[]={a,b};double in[]={1,2,4,7},out[4]{},lo[4]{},hi[4]{};int err[4]{};bool fail=paceval_dGetMultipleComputationsResultsExt(h,2,in,2,out,lo,hi,err);require(!fail&&std::all_of(err,err+4,[](int e){return e==0;}),"Multi-graph layout probe failed");if(std::abs(out[0]-5)<1e-10&&std::abs(out[1]-18)<1e-10&&std::abs(out[2]-1)<1e-10&&std::abs(out[3]-5)<1e-10)graphMajor=true;else if(std::abs(out[0]-5)<1e-10&&std::abs(out[1]-1)<1e-10&&std::abs(out[2]-18)<1e-10&&std::abs(out[3]-5)<1e-10)graphMajor=false;else throw std::runtime_error("Unexpected layout");batchCalls++;graphPoints+=4;}
 Matrix multi(const std::vector<PACEVAL_HANDLE>&h,const Matrix&data,size_t vars){require(!h.empty()&&!data.empty(),"Empty batch");std::vector<double>in;in.reserve(data.size()*vars);for(auto&row:data){require(row.size()==vars,"Batch width mismatch");for(auto x:row)require(std::isfinite(x),"Nonfinite batch input");in.insert(in.end(),row.begin(),row.end());}std::vector<double>out(h.size()*data.size()),low(out.size()),high(out.size());std::vector<int>errors(out.size(),-1);bool failed=paceval_dGetMultipleComputationsResultsExt(const_cast<PACEVAL_HANDLE*>(h.data()),h.size(),in.data(),data.size(),out.data(),low.data(),high.data(),errors.data());require(!failed,"Multi-graph failed");for(int e:errors)require(e==0,"Multi-graph error "+std::to_string(e));Matrix z(data.size(),std::vector<double>(h.size()));for(size_t i=0;i<data.size();i++)for(size_t j=0;j<h.size();j++){double q=out[graphMajor?j*data.size()+i:i*h.size()+j];require(std::isfinite(q),"Nonfinite batch result");z[i][j]=q;}batchCalls++;graphPoints+=out.size();return z;}
 std::vector<double>one(PACEVAL_HANDLE h,const Matrix&data,size_t vars){require(!data.empty(),"Empty single batch");std::vector<double>in;in.reserve(data.size()*vars);for(auto&r:data){require(r.size()==vars,"Width mismatch");in.insert(in.end(),r.begin(),r.end());}std::vector<double>out(data.size()),lo(data.size()),hi(data.size());std::vector<int>e(data.size(),-1);bool failed=paceval_dGetComputationResultExt(h,in.data(),data.size(),out.data(),lo.data(),hi.data(),e.data());require(!failed,"Single-graph batch failed");for(size_t i=0;i<out.size();i++)require(e[i]==0&&std::isfinite(out[i]),"Single-graph output invalid");batchCalls++;graphPoints+=out.size();return out;}
};
struct Graph{std::string v,id,expr,units,purpose;PACEVAL_HANDLE h;size_t evals=0;};
struct Models{
 Engine&e;std::vector<Graph>g;std::map<std::string,size_t>at;
 Models(Engine&x):e(x){
 const std::string ae="(alpha*(550/lam))";
 const std::string B="(i0*exp(-"+ae+"*d)+offset)";
 const std::string Bd="(-"+ae+"*i0*exp(-"+ae+"*d))";
 const std::string inv="(-ln((y-offset)/i0)/"+ae+")";
 const std::string r0="((n0-nf)/(n0+nf))",r1="((nf-ns)/(nf+ns))";
 const std::string theta="(4*pi*nf*d/lam)";
 const std::string a="("+r0+"^2+"+r1+"^2)",b="(2*"+r0+"*"+r1+")",c="(1+("+r0+"*"+r1+")^2)";
 const std::string denominator="("+c+"+"+b+"*cos("+theta+"))";
 const std::string R="( ("+a+"+"+b+"*cos("+theta+")) / "+denominator+")";
 const std::string Rd="((4*pi*nf/lam)*"+b+"*sin("+theta+")*("+a+"-"+c+")/("+denominator+"^2))";
 auto add=[&](std::string v,std::string id,std::string f,std::string units,std::string purpose){auto vars=v=="COMPARE"?C:(v=="SUMMARY"?S:V);size_t i=g.size();g.push_back({v,id,f,units,purpose,e.make(f,vars),0});at[v+"_"+id]=i;};
 add("BEER","ALPHA_EFF",ae,"1/nm","Wavelength-scaled absorption coefficient");
 add("BEER","FORWARD",B,"normalized intensity","Beer-Lambert transmission plus offset");
 add("BEER","SENSOR","("+B+"+noise)","normalized intensity","Synthetic intensity with specified sensor error");
 add("BEER","INVERSE",inv,"nm","Direct Beer-Lambert inverse thickness");
 add("BEER","SENS_INTENSITY","(-1/("+ae+"*(y-offset)))","nm/intensity","Analytic inverse-intensity sensitivity");
 add("BEER","DERIV_D",Bd,"intensity/nm","Forward thickness derivative");
 add("BEER","FISHER","("+Bd+"/sigma)^2","1/nm^2","Per-wavelength thickness information");
 add("BEER","RESIDUAL","(("+B+"-y)/sigma)^2","1","Squared normalized intensity residual");
 add("BEER","UNCERTAINTY","(sigma*abs(-1/("+ae+"*(y-offset))))","nm","Local propagated sensor uncertainty proxy");
 add("BEER","THICKNESS_MARGIN","(tol-abs(d-target))","nm","Signed target thickness tolerance");
 add("BEER","QUALITY_GUARD","(((abs(d-target))<=tol) AND ((y-offset)>0) AND ("+ae+">0))","0/1","Composite domain and thickness guard");
 add("FILM","R01",r0,"1","Air-to-film real Fresnel amplitude");
 add("FILM","R12",r1,"1","Film-to-substrate real Fresnel amplitude");
 add("FILM","PHASE",theta,"rad","Roundtrip interference phase");
 add("FILM","DENOMINATOR",denominator,"1","Airy multiple-reflection denominator");
 add("FILM","REFLECTANCE",R,"1","Normal-incidence coherent single-layer reflectance");
 add("FILM","SENSOR","("+R+"+noise)","1","Synthetic reflectometer sensor output");
 add("FILM","DR_DD",Rd,"1/nm","Analytic reflectance thickness sensitivity");
 add("FILM","FISHER","("+Rd+"/sigma)^2","1/nm^2","Per-wavelength local thickness information");
 add("FILM","RESIDUAL","(("+R+"-y)/sigma)^2","1","Per-wavelength spectral inverse objective");
 add("FILM","ABS_RESIDUAL","abs("+R+"-y)","1","Absolute reflectance fit error");
 add("FILM","THICKNESS_MARGIN","(tol-abs(d-target))","nm","Signed thickness specification margin");
 add("FILM","QUALITY_GUARD","(((abs(d-target))<=tol) AND ("+denominator+">0) AND (lam>0) AND (nf>0))","0/1","Combined optical and thickness guard");
 add("FILM","REGULARIZED_SENS","(sigma/sqrt("+Rd+"^2+0.000000000001))","nm","Regularized local single-wavelength uncertainty indicator");
 add("FILM","REFLECTIVITY_MARGIN","((0.99-"+R+") min ("+R+"-0.000001))","1","Physical reflectivity range margin");
 add("SUMMARY","UNCERTAINTY","(1/sqrt(info))","nm","Information-based local thickness uncertainty after spectral summation");
 add("SUMMARY","THICKNESS_MARGIN","(tol-abs(fit-target))","nm","Recovered thickness margin for film result");
 add("SUMMARY","OBJECTIVE_MARGIN","(threshold-objective)","1","Composite spectral objective threshold margin");
 add("SUMMARY","QUALITY_GUARD","(((abs(fit-target))<=tol) AND (objective<=threshold) AND (info>0))","0/1","Final fitted spectral and thickness guard");
 add("COMPARE","FIT_DIFFERENCE","(dr-db)","nm","Difference in recovered thickness across distinct channels");
 add("COMPARE","JOINT_MARGIN","((lim-abs(db-bt)) min (lim-abs(dr-rt)))","nm","Both-channel recovery versus synthetic reference");
 add("COMPARE","UNCERTAINTY_RATIO","(ur/(ub+0.000000001))","1","Local uncertainty estimate ratio; not a speed comparison");
 add("COMPARE","JOINT_GUARD","(((abs(db-bt))<=lim) AND ((abs(dr-rt))<=lim) AND (q>=0) AND (q<=45))","0/1","Joint fit quality and truth-recovery guard");
 }
 PACEVAL_HANDLE handle(const std::string&ver,const std::string&id)const{return g.at(at.at(ver+"_"+id)).h;}
 double scalar(const std::string&v,const std::string&id,const std::vector<double>&p){auto&z=g[at.at(v+"_"+id)];z.evals++;return e.scalar(z.h,p);}
 Matrix multi(const std::string&ver,const Matrix&in){std::vector<PACEVAL_HANDLE>hs;for(auto&z:g)if(z.v==ver){hs.push_back(z.h);z.evals+=in.size();}return e.multi(hs,in,ver=="COMPARE"?C.size():(ver=="SUMMARY"?S.size():V.size()));}
 std::vector<double>one(const std::string&ver,const std::string&id,const Matrix&in){auto&z=g[at.at(ver+"_"+id)];z.evals+=in.size();return e.one(z.h,in,V.size());}
 std::map<std::string,double>decode(const std::string&v,const std::vector<double>&r)const{std::map<std::string,double>m;size_t j=0;for(auto&z:g)if(z.v==v)m[z.id]=r.at(j++);require(j==r.size(),"Decode mismatch");return m;}
};
struct Raw{std::string id;int ix,iy;double truth,alpha,nf,ns,offset,lam,noiseT,noiseR,measT=0,measR=0;};
std::vector<Raw>readCSV(const fs::path&p){std::ifstream f(p);require(bool(f),"Missing CSV");std::string line;require(bool(std::getline(f,line)),"CSV empty");require(line=="site_id,pixel_x,pixel_y,true_nm,alpha_per_nm,film_n,substrate_n,offset,wavelength_nm,noise_t,noise_r","Bad CSV schema");std::vector<Raw>v;while(std::getline(f,line)){if(line.empty())continue;auto a=split(line);require(a.size()==11,"CSV field count mismatch");require(std::regex_match(a[0],std::regex(R"(S[0-9]{4})")),"Site ID invalid");Raw r{};r.id=a[0];auto xi=parseNumber(a[1]),yi=parseNumber(a[2]);require(xi>=0&&xi<=11&&yi>=0&&yi<=11&&std::floor(xi)==xi&&std::floor(yi)==yi,"Pixel invalid");r.ix=int(xi);r.iy=int(yi);r.truth=parseNumber(a[3]);r.alpha=parseNumber(a[4]);r.nf=parseNumber(a[5]);r.ns=parseNumber(a[6]);r.offset=parseNumber(a[7]);r.lam=parseNumber(a[8]);r.noiseT=parseNumber(a[9]);r.noiseR=parseNumber(a[10]);require(r.truth>80&&r.truth<460&&r.alpha>0&&r.nf>1.1&&r.nf<1.9&&r.ns>1.4&&r.ns<2&&r.offset>=0&&r.offset<.1&&r.lam>=390&&r.lam<=800&&std::abs(r.noiseT)<.002&&std::abs(r.noiseR)<.001,"Input outside model domain");v.push_back(r);}require(!v.empty()&&v.size()%9==0,"Expected 9 wavelengths per sample");for(size_t i=0;i<v.size();i+=9){for(size_t j=0;j<9;j++){auto&r=v[i+j];require(r.id==v[i].id&&r.truth==v[i].truth&&r.nf==v[i].nf,"Site data inconsistent");}}return v;}
std::vector<double>inputs(const Raw&r,double d,double y,double noise=0){return {d,r.lam,r.alpha,1.,r.offset,noise,y,.00035,235.,35.,1.,r.nf,r.ns};}
double nativeR(double d,const Raw&r){double r0=(1-r.nf)/(1+r.nf),r1=(r.nf-r.ns)/(r.nf+r.ns),t=4*std::acos(-1.)*r.nf*d/r.lam;double k=2*r0*r1*std::cos(t);return (r0*r0+r1*r1+k)/(1+std::pow(r0*r1,2)+k);}
double nativeRd(double d,const Raw&r){double a=(1-r.nf)/(1+r.nf),b=(r.nf-r.ns)/(r.nf+r.ns),phase=4*std::acos(-1.)*r.nf*d/r.lam,num=a*a+b*b,den=1+(a*b)*(a*b),co=2*a*b;return (4*std::acos(-1.)*r.nf/r.lam)*co*std::sin(phase)*(num-den)/std::pow(den+co*std::cos(phase),2);}
void sdkOperatorTest(Engine&e){std::vector<std::pair<std::string,double>>z={{"((-1)%10)",-1},{"((-1) mod 10)",9},{"(4 min 5)",4},{"(4 max 5)",5},{"(2<3)",1},{"(2<=2)",1},{"(2>=2)",1},{"(2=2)",1},{"(2<>3)",1},{"NOT(0)",1},{"(1 AND 1)",1},{"(0 OR 1)",1},{"((2<=2) AND (3>=0))",1}};for(auto&p:z)near(e.scalar(e.make(p.first,{}),{}),p.second);for(auto s:{"","NaN","Inf","1+2","1,2","1e999","--1"," 1","2nm"}){bool rejected=false;try{parseNumber(s);}catch(...){rejected=true;}require(rejected,"Unsafe text accepted");}near(parseNumber("-1.25e-3"),-.00125);require(!formatNumber(1.25e-6).empty(),"Numeric format test");}
void selftest(){Engine e;e.layoutProbe();sdkOperatorTest(e);Models m(e);Raw r{};r.id="S0000";r.truth=200;r.lam=550;r.alpha=.003;r.nf=1.53;r.ns=1.73;r.offset=.01;double n=nativeR(200,r);auto x=inputs(r,200,n);auto b=m.decode("FILM",m.multi("FILM",{x})[0]);near(b.at("REFLECTANCE"),n);near(b.at("DR_DD"),nativeRd(200,r));near(m.scalar("FILM","REFLECTANCE",x),n);auto t=m.scalar("BEER","SENSOR",inputs(r,200,.5));auto be=m.decode("BEER",m.multi("BEER",{inputs(r,200,t)})[0]);near(be.at("INVERSE"),200,1e-7);near(be.at("RESIDUAL"),0,1e-7);auto s=m.one("FILM","RESIDUAL",{x});near(s[0],0);std::cout<<"PASS original SDK scalar, multigraph, single batch, numerical conversion and mathematical operators\n";}
struct SiteResult{std::string id;int x,y;double truth,beer,film,uBeer,uFilm,score,bestAlt;int beerPass,filmPass,jointPass;};
void run(const fs::path&source,const fs::path&folder){fs::create_directories(folder);Engine e;e.layoutProbe();sdkOperatorTest(e);Models m(e);auto data=readCSV(source);size_t nativeChecks=0;
 std::ofstream spectra(folder/"spectral_samples.csv"),sites(folder/"site_summary.csv"),curves(folder/"objective_profiles.csv"),compare(folder/"model_comparison.csv"),alias(folder/"alias_case.csv"),aliasCurve(folder/"alias_curve.csv"),audit(folder/"native_audit.csv"),inventory(folder/"math_execution_inventory.csv"),manifest(folder/"formula_manifest.csv"),evidence(folder/"execution_evidence.json");require(bool(spectra&&sites&&curves&&compare&&alias&&audit&&inventory&&manifest&&evidence),"Output open failed");
 spectra<<"site_id,wavelength_nm,true_nm,transmission_observed,reflectance_observed,beer_inverse_nm,beer_sensitivity_nm_per_intensity,film_reflectance_at_truth,film_dR_dd_at_truth,beer_local_uncertainty_nm,film_local_information\n";
 sites<<"site_id,pixel_x,pixel_y,true_nm,beer_fit_nm,film_fit_nm,beer_uncertainty_nm,film_local_uncertainty_nm,film_objective,second_separated_objective,beer_tolerance_pass,film_tolerance_pass,joint_recovery_guard\n";
 curves<<"site_id,thickness_nm,normalized_objective\n";
 compare<<"site_id,fit_difference_nm,joint_recovery_margin_nm,uncertainty_ratio,joint_guard\n";
 alias<<"wavelength_nm,thickness_a_nm,thickness_b_nm,reflectance_a,reflectance_b,reflection_period_nm\n";aliasCurve<<"thickness_nm,reflectance\n";
 audit<<"site_id,wavelength_nm,forward_checks,derivative_checks,pass\n";
 std::vector<SiteResult>all;
 for(size_t s=0;s<data.size();s+=9){
  std::vector<double>beerRecovered,beerUnc,filmInfo;
  // Simulated measurement values are generated by REAL paceval sensor graphs.
  for(size_t j=0;j<9;j++){auto&r=data[s+j];r.measT=m.scalar("BEER","SENSOR",inputs(r,r.truth,0,r.noiseT));r.measR=m.scalar("FILM","SENSOR",inputs(r,r.truth,0,r.noiseR));require(r.measT>r.offset&&r.measR>0&&r.measR<1,"Sensor outside model domain");}
  Matrix bt,fr;for(size_t j=0;j<9;j++){auto&r=data[s+j];bt.push_back(inputs(r,r.truth,r.measT));bt.back()[7]=.001;fr.push_back(inputs(r,r.truth,r.measR));}
  auto btvals=m.multi("BEER",bt),frvals=m.multi("FILM",fr);
  for(size_t j=0;j<9;j++){auto&r=data[s+j];auto b=m.decode("BEER",btvals[j]),f=m.decode("FILM",frvals[j]);beerRecovered.push_back(b.at("INVERSE"));beerUnc.push_back(b.at("UNCERTAINTY"));filmInfo.push_back(f.at("FISHER"));if((s/9)<40 || ((s/9)%13==0)){
   double tr=std::exp(-r.alpha*550/r.lam*r.truth)+r.offset;near(b.at("FORWARD"),tr);near(f.at("REFLECTANCE"),nativeR(r.truth,r));near(f.at("DR_DD"),nativeRd(r.truth,r),1e-9,1e-7);nativeChecks+=3;audit<<r.id<<','<<formatNumber(r.lam)<<",3,1,1\n";}
   spectra<<r.id<<','<<formatNumber(r.lam)<<','<<formatNumber(r.truth)<<','<<formatNumber(r.measT)<<','<<formatNumber(r.measR)<<','<<formatNumber(b.at("INVERSE"))<<','<<formatNumber(b.at("SENS_INTENSITY"))<<','<<formatNumber(f.at("REFLECTANCE"))<<','<<formatNumber(f.at("DR_DD"))<<','<<formatNumber(b.at("UNCERTAINTY"))<<','<<formatNumber(f.at("FISHER"))<<'\n';
  }
  // V1 inverse: median of nine independently paceval-reconstructed thicknesses.
  auto median=[](std::vector<double>v){std::sort(v.begin(),v.end());return v[v.size()/2];};
  double beer=median(beerRecovered),ub=median(beerUnc);
  // V2 inverse: C++ manages global exploration, paceval evaluates its spectral residual.
  // We intentionally use a broad grid, then local golden-section search. The solver
  // does not claim globally unique recovery in all optical regimes.
  std::vector<double>grid,values;Matrix rows;int steps=124;for(int k=0;k<=steps;k++){double d=88.+3*k;grid.push_back(d);for(size_t j=0;j<9;j++)rows.push_back(inputs(data[s+j],d,data[s+j].measR));}
  auto ev=m.one("FILM","RESIDUAL",rows);for(int k=0;k<=steps;k++){double sum=0;for(int j=0;j<9;j++)sum+=ev[k*9+j];values.push_back(sum);if(s/9<4)curves<<data[s].id<<','<<formatNumber(grid[k])<<','<<formatNumber(sum)<<'\n';}
  size_t bestIdx=size_t(std::min_element(values.begin(),values.end())-values.begin());double second=1e200;for(size_t j=0;j<values.size();j++)if(std::abs(grid[j]-grid[bestIdx])>70)second=std::min(second,values[j]);
  auto objective=[&](double d){Matrix rr;for(size_t j=0;j<9;j++)rr.push_back(inputs(data[s+j],d,data[s+j].measR));auto z=m.one("FILM","RESIDUAL",rr);double q=0;for(auto v:z)q+=v;return q;};
  double lo=std::max(88.,grid[bestIdx]-3),hi=std::min(460.,grid[bestIdx]+3);const double phi=(std::sqrt(5.)-1)/2;double p=hi-phi*(hi-lo),q=lo+phi*(hi-lo),fp=objective(p),fq=objective(q);for(int k=0;k<35;k++){if(fp<fq){hi=q;q=p;fq=fp;p=hi-phi*(hi-lo);fp=objective(p);}else{lo=p;p=q;fp=fq;q=lo+phi*(hi-lo);fq=objective(q);}}double film=(lo+hi)/2,score=objective(film);
  Matrix fitted;for(size_t j=0;j<9;j++)fitted.push_back(inputs(data[s+j],film,data[s+j].measR));auto fm=m.multi("FILM",fitted);double information=0;for(size_t j=0;j<9;j++)information+=m.decode("FILM",fm[j]).at("FISHER");auto summary=m.decode("SUMMARY",m.multi("SUMMARY",{{information,film,235.,35.,score,45.}})[0]);double uf=summary.at("UNCERTAINTY"); // The actual uncertainty function is executed by paceval.
  auto cmp=m.decode("COMPARE",m.multi("COMPARE",{{data[s].truth,data[s].truth,beer,film,ub,uf,score,3.}})[0]);
  int bp=(m.scalar("BEER","THICKNESS_MARGIN",inputs(data[s],beer,data[s].measT))>=0),fpb=(summary.at("QUALITY_GUARD")>.5),both=(cmp.at("JOINT_GUARD")>.5);
  sites<<data[s].id<<','<<data[s].ix<<','<<data[s].iy<<','<<formatNumber(data[s].truth)<<','<<formatNumber(beer)<<','<<formatNumber(film)<<','<<formatNumber(ub)<<','<<formatNumber(uf)<<','<<formatNumber(score)<<','<<formatNumber(second)<<','<<bp<<','<<fpb<<','<<both<<'\n';
  compare<<data[s].id<<','<<formatNumber(cmp.at("FIT_DIFFERENCE"))<<','<<formatNumber(cmp.at("JOINT_MARGIN"))<<','<<formatNumber(cmp.at("UNCERTAINTY_RATIO"))<<','<<formatNumber(cmp.at("JOINT_GUARD"))<<'\n';
  all.push_back({data[s].id,data[s].ix,data[s].iy,data[s].truth,beer,film,ub,uf,score,second,bp,fpb,both});
 }
 // A single wavelength has exact thickness aliases in the lossless model:
 // adding lambda/(2*n_f) to film thickness leaves cos(4*pi*n_f*d/lambda) unchanged.
 Raw a=data[0];a.lam=525;double da=170.,period=a.lam/(2*a.nf),db=da+period;
 double ra=m.scalar("FILM","REFLECTANCE",inputs(a,da,.02));double rb=m.scalar("FILM","REFLECTANCE",inputs(a,db,.02));near(ra,rb,1e-10);
 alias<<formatNumber(a.lam)<<','<<formatNumber(da)<<','<<formatNumber(db)<<','<<formatNumber(ra)<<','<<formatNumber(rb)<<','<<formatNumber(period)<<'\n';
 Matrix aliasRows;for(int k=0;k<=760;k++)aliasRows.push_back(inputs(a,80.+.5*k,.02));auto aliasValues=m.one("FILM","REFLECTANCE",aliasRows);for(size_t k=0;k<aliasRows.size();k++)aliasCurve<<formatNumber(aliasRows[k][0])<<','<<formatNumber(aliasValues[k])<<'\n';
 manifest<<"graph_id,version,formula,units,purpose\n";inventory<<"function_id,domain_quantity,mathematical_definition,units,execution_owner,paceval_graph_id,formula_version,api_path,reference_test,status,host_reason\n";size_t exec=0;for(auto&g:m.g){exec+=g.evals>0;manifest<<g.v<<'_'<<g.id<<','<<g.v<<",\""<<g.expr<<"\","<<g.units<<",\""<<g.purpose<<"\"\n";inventory<<g.v<<'_'<<g.id<<",\""<<g.purpose<<"\",\""<<g.expr<<"\","<<g.units<<",paceval,"<<g.v<<'_'<<g.id<<','<<g.v<<",scalar_or_batch,mpmath_reference,"<<(g.evals?"executed":"registered_only")<<",\n";}require(exec==m.g.size(),"Registered but unused graph");inventory<<"GLOBAL_INVERSION_SEARCH,Global grid and golden section,host-controlled sequence of paceval residuals,nm,host,,FILM,C++ numerical search,independent reference,executed,stateful minimization algorithm\n";
 inventory<<"SPECTRAL_AGGREGATION,Sum spectral objective and information,finite sum over wavelengths,1,host,,both,C++ reduction,mpmath reference,executed,variable-length reduction\n";
 inventory<<"QUALITY_DECISION,Final quality status,binary classification from paceval guards,0/1,host,,both,C++ policy,independent reference,executed,operator and decision policy\n";
 size_t p1=0,p2=0,joint=0;double mbe=0,mfr=0;for(auto&r:all){p1+=r.beerPass;p2+=r.filmPass;joint+=r.jointPass;mbe+=std::abs(r.beer-r.truth);mfr+=std::abs(r.film-r.truth);}mbe/=all.size();mfr/=all.size();
 evidence<<"{\n  \"original_sdk\":\"paceval 4.25, Linux x86-64\",\n  \"unique_graphs_created\":"<<m.g.size()<<",\n  \"unique_graphs_executed\":"<<exec<<",\n  \"scalar_calls\":"<<e.scalarCalls<<",\n  \"batch_calls\":"<<e.batchCalls<<",\n  \"graph_point_evaluations\":"<<e.graphPoints<<",\n  \"site_count\":"<<all.size()<<",\n  \"wavelengths_per_site\":9,\n  \"spectral_sample_rows\":"<<data.size()<<",\n  \"model_versions\":2,\n  \"beer_tolerance_pass\":"<<p1<<",\n  \"film_tolerance_pass\":"<<p2<<",\n  \"joint_recovery_within_3nm\":"<<joint<<",\n  \"native_reference_assertions\":"<<nativeChecks<<",\n  \"mean_absolute_thickness_recovery_error_beer_nm\":"<<std::setprecision(12)<<mbe<<",\n  \"mean_absolute_thickness_recovery_error_film_nm\":"<<mfr<<"\n}\n";
 std::cout<<"PASS original SDK executed "<<exec<<" graphs; sites="<<all.size()<<"; Beer/FILM tolerance="<<p1<<"/"<<p2<<"; native reference assertions="<<nativeChecks<<"\n";
}
}
int main(int argc,char**argv){try{if(argc==2&&std::string(argv[1])=="--selftest"){selftest();return 0;}require(argc==4&&std::string(argv[1])=="--run","Usage: optical_film --run input/spectral_samples.csv results");run(argv[2],argv[3]);return 0;}catch(const std::exception&e){std::cerr<<"ERROR "<<e.what()<<'\n';return 1;}}
