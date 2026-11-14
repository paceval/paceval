// WP06: Genuine paceval execution of synthetic wafer-scale plasma etch mathematics.
// The native host manages finite datasets, graph dependencies, aggregation and CSV I/O.
// All film/mask rates, gradients, etch depths, selectivity, quality and guard math are graphs.
#include "paceval_main.h"
#include <algorithm>
#include <array>
#include <cmath>
#include <cstdint>
#include <filesystem>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <limits>
#include <map>
#include <regex>
#include <set>
#include <sstream>
#include <stdexcept>
#include <string>
#include <vector>
namespace fs=std::filesystem;
static constexpr unsigned NV=17;
static constexpr double PI=3.141592653589793238462643383279502884;
static constexpr char VARS[]="x y temp p bias chem etch filmzero maskzero target depthtol smin maskmin qmax film mask center";
using Row=std::array<double,NV>;
void require(bool b,const std::string& s){if(!b)throw std::runtime_error(s);}
std::string trim(const std::string& s){auto i=s.find_first_not_of(" \t\r\n"),j=s.find_last_not_of(" \t\r\n");return i==std::string::npos?"":s.substr(i,j-i+1);}
std::vector<std::string> split(const std::string& s){std::stringstream ss(s);std::vector<std::string> a;std::string t;while(std::getline(ss,t,','))a.push_back(t);if(!s.empty()&&s.back()==',')a.push_back("");return a;}
class Engine{
 std::vector<PACEVAL_HANDLE> owned;std::set<PACEVAL_HANDLE> used;
public:
 uint64_t batchCalls=0,scalarCalls=0,graphPointResults=0;
 Engine(){require(paceval_InitializeLibrary(nullptr),"Original paceval library failed to initialize");}
 ~Engine(){for(auto h:owned)paceval_DeleteComputation(h);paceval_FreeLibrary();}
 Engine(const Engine&)=delete;Engine& operator=(const Engine&)=delete;
 double parse(const std::string& text)const{
  static const std::regex num(R"(^[+-]?(?:[0-9]+(?:\.[0-9]*)?|\.[0-9]+)(?:[eE][+-]?[0-9]+)?$)");
  auto s=trim(text);require(std::regex_match(s,num),"CSV numeric field is not a finite decimal literal: "+s);
  int err=-1;long pos=-1;double value=paceval_dConvertStringToFloat(s.c_str(),&err,&pos,false,nullptr,nullptr);
  require(err==PACEVAL_ERR_NO_ERROR&&std::isfinite(value),"paceval conversion failed at position "+std::to_string(pos));return value;
 }
 std::string fmt(double x)const{require(std::isfinite(x),"Nonfinite CSV output");char buf[512]={};int n=paceval_dConvertFloatToString(buf,x);require(n>0&&buf[0],"paceval conversion output failed");return buf;}
 PACEVAL_HANDLE add(const std::string& expr){auto h=paceval_CreateComputation(expr.c_str(),NV,VARS,false,nullptr);require(h!=nullptr,"Null paceval graph");
  if(paceval_GetIsError(h)){char a[512]={},b[512]={};paceval_CreateErrorInformationText(h,a,b);paceval_DeleteComputation(h);throw std::runtime_error("paceval formula rejected: "+expr.substr(0,150)+" "+a+" "+b);}owned.push_back(h);return h;}
 std::vector<double> batch(const std::vector<PACEVAL_HANDLE>& handles,const std::vector<Row>& data){require(!handles.empty()&&!data.empty(),"Empty batch");
  std::vector<double> in;in.reserve(data.size()*NV);for(const auto& r:data)for(double a:r){require(std::isfinite(a),"Nonfinite graph input");in.push_back(a);}
  std::vector<double> out(data.size()*handles.size());std::vector<int> errors(out.size(),-900);auto hs=handles;
  bool ok=paceval_dGetMultipleComputationsResultsExt(hs.data(),static_cast<unsigned long>(hs.size()),in.data(),static_cast<unsigned long>(data.size()),out.data(),nullptr,nullptr,errors.data());
  require(!ok,"Multi-graph API reported an error; see per-point error codes");for(size_t i=0;i<out.size();++i)require(errors[i]==PACEVAL_ERR_NO_ERROR&&std::isfinite(out[i]),"Failed paceval graph point index "+std::to_string(i)+" error "+std::to_string(errors[i]));
  for(auto h:handles)used.insert(h);++batchCalls;graphPointResults+=out.size();return out;
 }
 double scalar(PACEVAL_HANDLE h,const Row& r){double d=paceval_dGetComputationResult(h,const_cast<double*>(r.data()),nullptr,nullptr);require(!paceval_GetIsError(h)&&std::isfinite(d),"Scalar graph failed");++scalarCalls;++graphPointResults;used.insert(h);return d;}
 size_t created()const{return owned.size();}size_t executed()const{return used.size();}
};
struct G{std::string name,version,expr,unit;PACEVAL_HANDLE handle=nullptr;};
using FormulaMap=std::map<std::string,std::string>;
// Synthetic formula coefficients are explicitly not fitted to actual chamber or wafer measurements.
const std::string R="(sqr(x)+sqr(y))";
std::string baseFilm(int v){return std::string(v==1?"(33000":"(34000")+"*exp(-12800/(8.314462618*temp))*(p/30)^0.34*(1+0.12*(chem-1))*(1+0.08*(bias-1)))";}
std::string baseMask(int v){return std::string(v==1?"(7000":"(7300")+"*exp(-13800/(8.314462618*temp))*(p/30)^0.20*(1+0.035*(chem-1))*(1+0.10*(bias-1)))";}
std::string ring(const std::string& r){return "exp(-sqr(("+r+"-0.64)/0.18))";}
std::string filmSpace(int v){return v==1?"(1+0.025*"+R+"-0.012*x+0.010*y+0.004*x*y)":"(1+0.015*"+R+"-0.008*x+0.009*y+0.004*x*y+0.025*"+ring(R)+")";}
std::string maskSpace(int v){return v==1?"(1+0.012*"+R+"+0.006*x-0.003*y)":"(1+0.016*"+R+"+0.004*x-0.005*y+0.006*"+ring(R)+")";}
std::string gradientFilm(int v,bool xaxis){std::string basis= v==1?(xaxis?"(0.050*x-0.012+0.004*y)":"(0.050*y+0.010+0.004*x)"):(xaxis?"(0.030*x-0.008+0.004*y+0.025*"+ring(R)+"*(-2*("+R+"-0.64)/sqr(0.18))*2*x)":"(0.030*y+0.009+0.004*x+0.025*"+ring(R)+"*(-2*("+R+"-0.64)/sqr(0.18))*2*y)");return "("+baseFilm(v)+"*"+basis+")";}
FormulaMap primary(int v){auto fr="("+baseFilm(v)+"*"+filmSpace(v)+")",mr="("+baseMask(v)+"*"+maskSpace(v)+")";
 std::string centerShape=v==1?"1":"(1+0.025*exp(-sqr((0-0.64)/0.18)))";
 return {{"film_rate",fr},{"mask_rate",mr},{"center_rate","("+baseFilm(v)+"*"+centerShape+")"},
  {"film_gradient_x",gradientFilm(v,true)},{"film_gradient_y",gradientFilm(v,false)},
  {"film_sensitivity_temperature","("+fr+"*12800/(8.314462618*sqr(temp)))"},
  {"film_sensitivity_pressure","("+fr+"*0.34/p)"},
  {"film_sensitivity_chemistry","("+fr+"*0.12/(1+0.12*(chem-1)))"}};
}
FormulaMap secondary(){const std::string filmDepth="(film*etch)", maskLoss="(mask*etch)",select="(film/(mask max 0.00000001))",delta="((film-center)/center)",maskRem="(maskzero-"+maskLoss+")";
 const std::string depthErr="("+filmDepth+"-target)", sMargin="("+select+"-smin)",mMargin="("+maskRem+"-maskmin)",depthMargin="(depthtol-abs("+depthErr+"))",uniformityMargin="(0.08-abs("+delta+"))";
 const std::string score="(0.48*sqr("+depthErr+"/target)+0.23*sqr("+delta+"/0.08)+0.18*sqr((0 max (smin-"+select+"))/smin)+0.11*sqr("+maskLoss+"/maskzero))";
 const std::string ok="((("+R+" <= 1) AND ("+sMargin+" >= 0)) AND (("+mMargin+" >= 0) AND ("+depthMargin+" >= 0)) AND (("+uniformityMargin+" >= 0) AND ((qmax-"+score+") >= 0)))";
 return {{"etch_depth",filmDepth},{"mask_erosion",maskLoss},{"selectivity",select},{"center_relative_deviation",delta},
 {"film_remaining","(filmzero-"+filmDepth+")"},{"mask_remaining",maskRem},
 {"depth_residual",depthErr},{"depth_margin",depthMargin},{"selectivity_margin",sMargin},{"mask_margin",mMargin},
 {"uniformity_margin",uniformityMargin},{"radial_margin","(1-"+R+")"},
 {"quality_score",score},{"quality_margin","(qmax-"+score+")"},{"quality_guard",ok},
 {"minimum_relative_margin","(("+sMargin+"/smin) min ("+mMargin+"/maskzero))"},
 {"mask_utilization","("+maskLoss+"/maskzero)"},
 {"bounded_film_fraction","(0 max (1 min ("+filmDepth+"/filmzero)))"},
 {"radial_edge_indicator",ring(R)}, {"film_rate_squared","sqr(film)"}};
}
struct Family{int v;std::map<std::string,G> a,b;};
std::map<std::string,G> graphs(Engine& e,const FormulaMap& defs,int ver,const std::string& /*stage*/){std::map<std::string,G> m;for(const auto& [name,expr]:defs){G g;g.name=name;g.version="v"+std::to_string(ver);g.expr=expr;g.unit=(name.find("rate")!=std::string::npos||name.find("gradient")!=std::string::npos||name.find("sensitivity")!=std::string::npos)?"nm_per_min": (name.find("depth")!=std::string::npos||name.find("margin")!=std::string::npos||name.find("remaining")!=std::string::npos||name.find("erosion")!=std::string::npos)?"quantity_specific":"dimensionless";g.handle=e.add(expr);m.emplace(name,g);}return m;}
Family mk_family(Engine& e,int v){Family f;f.v=v;f.a=graphs(e,primary(v),v,"primary");f.b=graphs(e,secondary(),v,"secondary");return f;}
std::vector<std::string> keys(const std::map<std::string,G>& g){std::vector<std::string> names;for(const auto& [n,v]:g)names.push_back(n);return names;}
std::vector<PACEVAL_HANDLE> hs(const std::map<std::string,G>& g){std::vector<PACEVAL_HANDLE> h;for(const auto& [n,v]:g)h.push_back(v.handle);return h;}
struct Recipe{int id;double temp,p,bias,chem,etch,film0,mask0,target,depthtol,smin,maskmin,qmax;};
Recipe recipe(int i){Recipe r{};r.id=i;r.temp=297.0+3.0*((i*7)%13);r.p=12+2*((i*11)%21);r.bias=0.76+0.08*((i*5)%8);r.chem=0.80+0.05*((i*7)%9);r.etch=1.70+0.10*((i*9)%13);r.film0=1050;r.mask0=160;r.target=540+15*((i*3)%9);r.depthtol=48;r.smin=6.5+0.15*(i%7);r.maskmin=79;r.qmax=0.10;return r;}
Row make_row(const Recipe& r,double x,double y){return {x,y,r.temp,r.p,r.bias,r.chem,r.etch,r.film0,r.mask0,r.target,r.depthtol,r.smin,r.maskmin,r.qmax,0,0,0};}
void validate(const Recipe& r){require(r.temp>=280&&r.temp<=355&&r.p>=5&&r.p<=80&&r.bias>=0.5&&r.bias<=1.7&&r.chem>=0.5&&r.chem<=1.5&&r.etch>=0&&r.etch<=5&&r.film0>0&&r.mask0>0&&r.target>0&&r.depthtol>0&&r.smin>0&&r.maskmin>=0&&r.qmax>0,"Recipe is outside declared surrogate domain");}
// A deterministic equal-area polar grid, using host geometry only to generate input coordinates.
std::vector<Row> positions(const Recipe& r,int radial,int angular){std::vector<Row> rows;rows.reserve(radial*angular);for(int a=0;a<radial;a++){double radius=std::sqrt((a+.5)/radial);for(int b=0;b<angular;b++){double th=2*PI*(b+.5)/angular;rows.push_back(make_row(r,radius*std::cos(th),radius*std::sin(th)));}}return rows;}
struct Stat{size_t n=0,pass=0;double min=std::numeric_limits<double>::infinity(),max=-std::numeric_limits<double>::infinity(),sum=0,ss=0,sel=0,depth=0,mask=0,score=0,delta=0,accepted=0;};
static std::map<std::string,std::string> u_map={{"etch_depth","nm"},{"mask_erosion","nm"},{"selectivity","ratio"},{"center_relative_deviation","fraction"},{"film_remaining","nm"},{"mask_remaining","nm"},{"depth_residual","nm"},{"depth_margin","nm"},{"selectivity_margin","ratio"},{"mask_margin","nm"},{"uniformity_margin","fraction"},{"radial_margin","fraction"},{"quality_score","dimensionless"},{"quality_margin","dimensionless"},{"quality_guard","boolean"},{"minimum_relative_margin","fraction"},{"mask_utilization","fraction"},{"bounded_film_fraction","fraction"},{"radial_edge_indicator","fraction"},{"film_rate_squared","nm2_per_min2"},
 {"film_rate","nm_per_min"},{"mask_rate","nm_per_min"},{"center_rate","nm_per_min"},{"film_gradient_x","nm_per_min_per_normalized_x"},{"film_gradient_y","nm_per_min_per_normalized_y"},{"film_sensitivity_temperature","nm_per_min_per_kelvin"},{"film_sensitivity_pressure","nm_per_min_per_mTorr"},{"film_sensitivity_chemistry","nm_per_min_per_index"},
 {"wafer_nonuniformity","percent"},{"wafer_coefficient_variation","percent"},{"wafer_mean_rate","nm_per_min"}};
void inventory(const fs::path& p,const std::vector<Family>& fam,const std::map<std::string,G>& summary){std::ofstream o(p);require(bool(o),"Cannot write formula inventory");o<<"function_id,domain_quantity,mathematical_definition,units,execution_owner,paceval_graph_id,formula_version,api_path,reference_test,status,host_reason\n";
 auto save=[&](const G& g){std::string s=g.expr;std::replace(s.begin(),s.end(),'"',' ');o<<g.version<<'_'<<g.name<<','<<g.name<<",\""<<s<<"\","<<u_map[g.name]<<",paceval,"<<g.version<<'_'<<g.name<<','<<g.version<<",dGetMultipleComputationsResultsExt,verify_reference.py,executed,\n";};for(const auto& f:fam){for(const auto&[n,g]:f.a)save(g);for(const auto&[n,g]:f.b)save(g);}for(const auto&[n,g]:summary)save(g);
 o<<"wafer_aggregate,maximum_minimum_and_moments,host_aggregation,rate_and_fraction,host,,cross_recipe,aggregation,verify_reference.py,executed,Host iterates across independent wafer points\n";
}
// Aggregation is stateful host accumulation; only final normalized formulas remain in paceval.
std::map<std::string,G> make_summary_graphs(Engine& e){std::map<std::string,G> g;const std::map<std::string,std::string> m={{"wafer_nonuniformity","(100*(mask-film)/(2*center))"},{"wafer_coefficient_variation","(100*sqrt((mask/film)-sqr(center/film))/(center/film))"},{"wafer_mean_rate","(film/mask)"}};
 for(const auto&[n,expr]:m){G a;a.name=n;a.version="summary";a.expr=expr;a.unit=u_map[n];a.handle=e.add(expr);g.emplace(n,a);}return g;}
// For summary graphs: film=rate_min, mask=rate_max, center=rate_mean (nonuniformity)
// CV graph: film=n, mask=sum(rate^2), center=sum(rate). Mean graph: film=sum(rate), mask=n.
void test_conversions(Engine& e){const char* good[]={"0","-0.25","+12.75","3e-9","4.82E+6",".75"};for(auto s:good){double d=e.parse(s);require(std::isfinite(d)&&!e.fmt(d).empty(),"Numeric converter failed");}for(auto s:{"1+2","","NaN","Inf","7,5","12x","1e9999"," 4 + 1 "}){bool caught=false;try{(void)e.parse(s);}catch(...){caught=true;}require(caught,"Failed to reject nonliteral CSV numeric field");}require(e.parse(e.fmt(12.125))==12.125,"Converter roundtrip failed");}
void test_operators(Engine& e){Row r{};r.fill(1);struct T{const char* s;double v;};const T t[]={{"(-1) % 10",-1},{"(-1) mod 10",9},{"4 min 5",4},{"4 max 5",5},{"((4<=5) AND (6>=6))",1},{"((4>5) OR (4<>5))",1},{"NOT(1=1)",0},{"((abs(-2) <= (2*1)) AND ((-1) mod 10=9))",1}};for(auto a:t){auto h=e.add(a.s);double z=e.scalar(h,r);require(std::abs(z-a.v)<1e-12,"Operator semantics failed: "+std::string(a.s));}}
void test_layout(Engine& e){auto a=e.add("(x+y)"),b=e.add("(x-y)");Row r{};r.fill(1);r[0]=3;r[1]=2;Row s=r;s[0]=7;s[1]=4;auto z=e.batch({a,b},{r,s});require(z.size()==4&&z[0]==5&&z[1]==11&&z[2]==1&&z[3]==3,"Graph-major multi-batch layout not as expected");require(e.scalar(a,r)==5,"Scalar evaluation mismatch");}
void test_invalid(Engine& e){auto a=recipe(0);a.temp=0;bool rejected=false;try{validate(a);}catch(...){rejected=true;}require(rejected,"Invalid temperature was allowed");rejected=false;try{(void)e.parse("1+2");}catch(...){rejected=true;}require(rejected,"Expression injection into numeric CSV was allowed");}
// This generated numeric CSV is subsequently re-read through original paceval text conversion.
std::vector<Recipe> prepare_read_recipe_csv(Engine& e,const fs::path& dest,int n){
 const std::string schema="recipeId,tempK,pressureMTorr,biasIndex,chemistryIndex,etchMinutes,filmInitialNm,maskInitialNm,targetDepthNm,depthToleranceNm,minSelectivity,minMaskRemainingNm,maxQualityScore";
 const auto file=dest/"synthetic_recipes.csv";
 {std::ofstream out(file);require(bool(out),"Cannot create synthetic recipe CSV");out<<schema<<'\n';
  for(int i=0;i<n;i++){const auto r=recipe(i);validate(r);out<<i;
   for(double x:{r.temp,r.p,r.bias,r.chem,r.etch,r.film0,r.mask0,r.target,r.depthtol,r.smin,r.maskmin,r.qmax})out<<','<<e.fmt(x);
   out<<'\n';}}
 std::ifstream in(file);require(bool(in),"Could not read back generated numerical recipe CSV");std::string text;
 require(bool(std::getline(in,text))&&text==schema,"Incorrect recipe input CSV schema");
 std::vector<Recipe> recipes;int lineno=1;
 while(std::getline(in,text)){
  ++lineno;if(text.empty())continue;auto fields=split(text);require(fields.size()==13,"Wrong number of CSV fields on line "+std::to_string(lineno));
  require(std::regex_match(fields[0],std::regex("[0-9]+")),"Non-integer recipe ID");
  Recipe r{};r.id=std::stoi(fields[0]);require(r.id==int(recipes.size()),"Disordered or duplicate recipe identifier");
  std::array<double*,12> destinations={&r.temp,&r.p,&r.bias,&r.chem,&r.etch,&r.film0,&r.mask0,&r.target,&r.depthtol,&r.smin,&r.maskmin,&r.qmax};
  for(size_t i=0;i<destinations.size();i++)try{*destinations[i]=e.parse(fields[i+1]);}catch(const std::exception& ex){throw std::runtime_error("Invalid recipe CSV line "+std::to_string(lineno)+", column "+std::to_string(i+2)+": "+ex.what());}
  validate(r);recipes.push_back(r);
 }
 require(recipes.size()==size_t(n),"Incorrect number of input recipe rows");return recipes;
}
// The complete v1/v2 execution is multi-stage, with only scalar value transfer performed by C++.
void run(Engine& e,int recipes,int radial,int angular,const fs::path& dest){require(recipes>=1&&recipes<=25&&radial>=2&&radial<=128&&angular>=4&&angular<=128,"Invalid workload size");fs::create_directories(dest);
 auto parsedRecipes=prepare_read_recipe_csv(e,dest,recipes);
 std::vector<Family> fam;fam.push_back(mk_family(e,1));fam.push_back(mk_family(e,2));auto summaryGraphs=make_summary_graphs(e);inventory(dest/"math_execution_inventory.csv",fam,summaryGraphs);
 std::ofstream out(dest/"wafer_points.csv"),summary(dest/"recipe_summary.csv"),trace(dest/"end_to_end_trace.csv"),registry(dest/"graph_registry.csv");require(bool(out)&&bool(summary)&&bool(trace)&&bool(registry),"Cannot open results CSVs");
 out<<"recipe,version,point,x,y,tempK,pressureMTorr,biasIndex,chemistryIndex,etchMinutes,filmRateNmPerMin,maskRateNmPerMin,centerRateNmPerMin,filmDepthNm,maskErosionNm,selectivity,relativeDeviation,filmRemainingNm,maskRemainingNm,depthResidualNm,depthMarginNm,selectivityMargin,maskMarginNm,uniformityMargin,qualityScore,qualityMargin,booleanGate,gradientX,gradientY,sensitivityTemp,sensitivityPressure,sensitivityChemistry\n";
 summary<<"recipe,version,temperatureK,pressureMTorr,etchMinutes,points,meanFilmRateNmPerMin,minFilmRateNmPerMin,maxFilmRateNmPerMin,nonuniformityPct,coefficientVariationPct,meanSelectivity,meanDepthNm,meanMaskRemainingNm,meanQualityScore,passFraction\n";
 trace<<"recipe,version,point,x,y,temperatureK,pressureMTorr,etchMinutes,filmRate,maskRate,centerRate,filmDepth,selectivity,relativeDeviation,maskRemaining,qualityScore,qualityMargin,booleanGate,hostDecision\n";
 registry<<"graph_id,version,stage,expression,api,units\n";
 for(const auto& f:fam)for(const auto& [stage,gm]:std::vector<std::pair<std::string,const std::map<std::string,G>*>>{{"primary",&f.a},{"secondary",&f.b}})for(const auto& [n,g]:*gm)registry<<g.version<<'_'<<n<<','<<g.version<<','<<stage<<",\""<<g.expr<<"\",dGetMultipleComputationsResultsExt,"<<u_map[n]<<'\n';
 for(const auto&[n,g]:summaryGraphs)registry<<"summary_"<<n<<",summary,aggregation,\""<<g.expr<<"\",dGetMultipleComputationsResultsExt,"<<u_map[n]<<'\n';
 uint64_t pointCount=0;
 for(int ri=0;ri<recipes;ri++){
  auto rec=parsedRecipes.at(ri);validate(rec);auto all=positions(rec,radial,angular);
  for(const auto& f:fam){Stat st;auto ka=keys(f.a),kb=keys(f.b);auto ha=hs(f.a),hb=hs(f.b);std::map<std::string,size_t> ai,bi;for(size_t k=0;k<ka.size();k++)ai[ka[k]]=k;for(size_t k=0;k<kb.size();k++)bi[kb[k]]=k;
   for(size_t first=0;first<all.size();first+=256){size_t n=std::min(size_t(256),all.size()-first);std::vector<Row> rows(all.begin()+first,all.begin()+first+n);
    auto z=e.batch(ha,rows);for(size_t j=0;j<n;j++){rows[j][14]=z[ai.at("film_rate")*n+j];rows[j][15]=z[ai.at("mask_rate")*n+j];rows[j][16]=z[ai.at("center_rate")*n+j];}
    auto s=e.batch(hb,rows);for(size_t j=0;j<n;j++){
      auto A=[&](const std::string& key){return z[ai.at(key)*n+j];};auto B=[&](const std::string& key){return s[bi.at(key)*n+j];};
      double rate=A("film_rate");st.n++;st.sum+=rate;st.ss+=B("film_rate_squared");st.min=std::min(st.min,rate);st.max=std::max(st.max,rate);st.sel+=B("selectivity");st.depth+=B("etch_depth");st.mask+=B("mask_remaining");st.score+=B("quality_score");st.pass+=B("quality_guard")>=0.5?1:0;
      int idx=int(first+j);out<<ri<<','<<f.v<<','<<idx<<','<<e.fmt(rows[j][0])<<','<<e.fmt(rows[j][1])<<','<<e.fmt(rec.temp)<<','<<e.fmt(rec.p)<<','<<e.fmt(rec.bias)<<','<<e.fmt(rec.chem)<<','<<e.fmt(rec.etch);
      for(const auto& name:{"film_rate","mask_rate","center_rate"})out<<','<<e.fmt(A(name));
      for(const auto& name:{"etch_depth","mask_erosion","selectivity","center_relative_deviation","film_remaining","mask_remaining","depth_residual","depth_margin","selectivity_margin","mask_margin","uniformity_margin","quality_score","quality_margin","quality_guard"})out<<','<<e.fmt(B(name));
      for(const auto& name:{"film_gradient_x","film_gradient_y","film_sensitivity_temperature","film_sensitivity_pressure","film_sensitivity_chemistry"})out<<','<<e.fmt(A(name));out<<'\n';
      if(idx==0||idx==radial*angular/2){auto gate=B("quality_guard");std::string decision=gate>.5?"ACCEPT":B("quality_margin")>-0.15?"REVIEW":"REJECT";trace<<ri<<','<<f.v<<','<<idx<<','<<e.fmt(rows[j][0])<<','<<e.fmt(rows[j][1])<<','<<e.fmt(rec.temp)<<','<<e.fmt(rec.p)<<','<<e.fmt(rec.etch)<<','<<e.fmt(rate)<<','<<e.fmt(A("mask_rate"))<<','<<e.fmt(A("center_rate"))<<','<<e.fmt(B("etch_depth"))<<','<<e.fmt(B("selectivity"))<<','<<e.fmt(B("center_relative_deviation"))<<','<<e.fmt(B("mask_remaining"))<<','<<e.fmt(B("quality_score"))<<','<<e.fmt(B("quality_margin"))<<','<<e.fmt(gate)<<','<<decision<<'\n';}
      ++pointCount;
    }
   }
   Row agg{};agg.fill(1);agg[14]=st.min;agg[15]=st.max;agg[16]=st.sum/st.n;double nu=e.batch({summaryGraphs.at("wafer_nonuniformity").handle},{agg})[0];agg[14]=st.n;agg[15]=st.ss;agg[16]=st.sum;auto cv=e.batch({summaryGraphs.at("wafer_coefficient_variation").handle},{agg})[0];agg[14]=st.sum;agg[15]=st.n;auto mean=e.batch({summaryGraphs.at("wafer_mean_rate").handle},{agg})[0];
   summary<<ri<<','<<f.v<<','<<e.fmt(rec.temp)<<','<<e.fmt(rec.p)<<','<<e.fmt(rec.etch)<<','<<st.n<<','<<e.fmt(mean)<<','<<e.fmt(st.min)<<','<<e.fmt(st.max)<<','<<e.fmt(nu)<<','<<e.fmt(cv)<<','<<e.fmt(st.sel/st.n)<<','<<e.fmt(st.depth/st.n)<<','<<e.fmt(st.mask/st.n)<<','<<e.fmt(st.score/st.n)<<','<<e.fmt(double(st.pass)/st.n)<<'\n';
  }
 }
 out.close();summary.close();trace.close();registry.close();
 std::ofstream evidence(dest/"execution_evidence.json");require(bool(evidence),"Cannot save evidence");evidence<<"{\n  \"project\": \"WP06 Semiconductor Plasma Etch Uniformity and Selectivity Mapping\",\n  \"runtime\": \"original paceval SDK 4.25 with compatible Linux shared library\",\n  \"synthetic\": true,\n  \"recipe_count\": "<<recipes<<",\n  \"recipe_version_count\": 2,\n  \"wafer_points_per_recipe\": "<<radial*angular<<",\n  \"total_model_point_rows\": "<<pointCount<<",\n  \"unique_graphs_created\": "<<e.created()<<",\n  \"unique_graphs_executed\": "<<e.executed()<<",\n  \"batch_calls\": "<<e.batchCalls<<",\n  \"scalar_calls\": "<<e.scalarCalls<<",\n  \"graph_point_evaluations\": "<<e.graphPointResults<<"\n}\n";
 std::cout<<"WP06 COMPLETE | rows="<<pointCount<<" graphs="<<e.executed()<<" batches="<<e.batchCalls<<" graph_outputs="<<e.graphPointResults<<"\n";
}
int main(int argc,char**argv){try{Engine e;if(argc>1){std::string mode=argv[1];if(mode=="--test-conversion"){test_conversions(e);std::cout<<"CONVERTERS_OK\n";return 0;}
 if(mode=="--test-operators"){test_operators(e);std::cout<<"OPERATORS_OK\n";return 0;}if(mode=="--test-layout"){test_layout(e);std::cout<<"BATCH_LAYOUT_OK\n";return 0;}if(mode=="--test-invalid"){test_invalid(e);std::cout<<"DOMAIN_OK\n";return 0;}if(mode=="--run"){int recipes=25,radial=64,angular=64;fs::path out=fs::current_path()/"results";for(int i=2;i+1<argc;i+=2){std::string arg=argv[i];if(arg=="--recipes")recipes=std::stoi(argv[i+1]);else if(arg=="--radial")radial=std::stoi(argv[i+1]);else if(arg=="--angular")angular=std::stoi(argv[i+1]);else if(arg=="--out")out=argv[i+1];else throw std::runtime_error("Unknown option "+arg);}run(e,recipes,radial,angular,out);return 0;}}
 std::cout<<"Usage: plasma_etch --run [--recipes 25 --radial 64 --angular 64 --out DIR]\n";return 1;
 }catch(const std::exception& x){std::cerr<<"ERROR: "<<x.what()<<'\n';return 2;}}
