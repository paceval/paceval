// paceval High-Volume Insurance Tariff Evaluation -- synthetic research demonstration.
//
// The official SDK C++ facade paceval_main.cpp is compiled as part of the target.
// The externally provided paceval Linux .so is linked through CMake; neither a
// custom dlopen adapter nor a redistributed proprietary runtime is used.
//
// IMPORTANT SCIENTIFIC BOUNDARY: the explicit tariff expressions below are
// illustrative mathematics, NOT actuarially fitted, legally cleared, or sold
// insurance products. No real person or real policy appears in the dataset.
//
// paceval: create 100 independent, reusable computation objects, batch-evaluate
// the tariff mathematics, recreate exactly one graph for a controlled update.
// Host: synthetic policy generation, data validation, reference arithmetic,
// CSV import/export, diagnostics, counterfactual non-rating tag comparison.
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
#include <numeric>
#include <random>
#include <sstream>
#include <stdexcept>
#include <string>
#include <utility>
#include <vector>
namespace fs = std::filesystem;
namespace {
constexpr std::size_t D = 5;
constexpr char VARS[] = "age claims km cover excess";
// age = INSURED ASSET AGE (years), never a person's age; km in 1000 km/year;
// excess in 1000 EUR. cover is a synthetic 1,2,3 coverage-code, not a protected trait.
using Inputs=std::array<double,D>;
struct Config {std::size_t pairs=512,models=100,batch=128;std::uint64_t seed=20261112;
 fs::path out="out",input="";bool selftest=false;};
void check(bool b,const std::string&why){if(!b)throw std::runtime_error(why);}
std::size_t parse_int(const std::string&s,const char* name,std::size_t max){
 check(!s.empty()&&s[0]!='-',std::string("invalid ")+name);
 std::size_t end=0;unsigned long long v=std::stoull(s,&end);
 check(end==s.size()&&v>0&&v<=max,std::string("invalid ")+name);return std::size_t(v);}
Config args(int argc,char**argv){Config c;for(int i=1;i<argc;++i){
 std::string name=argv[i];if(name=="--self-test"){c.selftest=true;continue;}
 check(i+1<argc,"missing value after "+name);std::string value=argv[++i];
 if(name=="--pairs")c.pairs=parse_int(value,"pairs",20000);
 else if(name=="--models")c.models=parse_int(value,"models",100);
 else if(name=="--batch")c.batch=parse_int(value,"batch",8192);
 else if(name=="--seed")c.seed=parse_int(value,"seed",1000000000);
 else if(name=="--out")c.out=value;
 else if(name=="--input")c.input=value;
 else throw std::runtime_error("unknown option "+name);
 }check(!c.out.empty(),"empty output path");return c;}
struct Engine{Engine(){check(paceval_InitializeLibrary(nullptr),"paceval initialization failed");}
 ~Engine(){paceval_FreeLibrary();}Engine(const Engine&)=delete;Engine&operator=(const Engine&)=delete;};
// RAII ensures release of every graph before the enclosing Engine object dies.
struct Graph{PACEVAL_HANDLE h=nullptr;explicit Graph(PACEVAL_HANDLE p=nullptr):h(p){}
 ~Graph(){if(h)paceval_DeleteComputation(h);}Graph(const Graph&)=delete;Graph&operator=(const Graph&)=delete;
 Graph(Graph&&o)noexcept:h(o.h){o.h=nullptr;}
 Graph&operator=(Graph&&o)noexcept{if(this!=&o){if(h)paceval_DeleteComputation(h);h=o.h;o.h=nullptr;}return *this;}};
struct Policy{std::size_t id,pair;int tag;Inputs x;};
struct Model{std::size_t id;int family,version;double base,a,c,m,g,h,f;std::string expr;};
std::string real(double x){std::ostringstream s;s<<std::setprecision(17)<<x;return "("+s.str()+")";}
Model model_for(std::size_t id){
 Model m{};m.id=id;m.family=int(id%4);m.version=1;
 m.base=280.0+double(id%17)*7.0;
 m.a=0.012+double(id%9)*0.0008;
 m.c=0.09+double(id%13)*0.004;
 m.m=0.018+double(id%7)*0.0012;
 m.g=0.035+double(id%11)*0.001;
 m.h=0.07+double(id%10)*0.004;
 m.f=0.002+double(id%6)*0.0005;
 return m;
}
std::string expression(const Model&m){
 // Literal negative numbers (when relevant) are always parenthesized because
 // paceval may parse unary minus differently from the native reference.
 const auto b=real(m.base),a=real(m.a),c=real(m.c),d=real(m.m),g=real(m.g),h=real(m.h),f=real(m.f);
 if(m.family==0) return b+"*(1+"+a+"*age)*(1+"+c+"*claims)";
 if(m.family==1) return b+"*(1+"+a+"*age)*(1+"+c+"*claims)*(1+"+d+"*(km-12)/12)*(1+"+g+"*(cover-1))";
 if(m.family==2) return b+"*(1+"+a+"*age)*(1+"+c+"*claims)*(1+"+g+"*(cover-1))*exp("+d+"*(km-12)/12)/(1+"+h+"*excess)";
 return b+"*(1+"+a+"*age+"+c+"*claims+"+d+"*km/12+"+g+"*(cover-1)+"+f+"*age*claims)/(1+"+h+"*excess)";
}
double native(const Model&m,const Inputs&x){
 const double age=x[0],claim=x[1],km=x[2],cover=x[3],exc=x[4];
 if(m.family==0)return m.base*(1+m.a*age)*(1+m.c*claim);
 if(m.family==1)return m.base*(1+m.a*age)*(1+m.c*claim)*(1+m.m*(km-12)/12)*(1+m.g*(cover-1));
 if(m.family==2)return m.base*(1+m.a*age)*(1+m.c*claim)*(1+m.g*(cover-1))*std::exp(m.m*(km-12)/12)/(1+m.h*exc);
 return m.base*(1+m.a*age+m.c*claim+m.m*km/12+m.g*(cover-1)+m.f*age*claim)/(1+m.h*exc);
}
void validate(const Inputs&x){for(double v:x)check(std::isfinite(v),"nonfinite policy input");
 check(x[0]>=0&&x[0]<=25,"asset age outside [0,25] years");
 check(x[1]>=0&&x[1]<=4&&std::floor(x[1])==x[1],"claims outside integer 0..4");
 check(x[2]>=1&&x[2]<=50,"mileage outside [1,50] thousand km/year");
 check(x[3]>=1&&x[3]<=3&&std::floor(x[3])==x[3],"coverage code outside 1..3");
 check(x[4]>=0&&x[4]<=2,"deductible outside [0,2] thousand EUR");}
Graph graph_for(Model&m,bool tinc=false){m.expr=expression(m);
 Graph g(paceval_CreateComputation(m.expr.c_str(),D,VARS,tinc,nullptr));
 check(g.h && !paceval_GetIsError(g.h),"paceval could not compile tariff model "+std::to_string(m.id)+" / "+m.expr);return g;}
std::vector<Policy> generate(std::size_t pairs,std::uint64_t seed){
 // Each synthetic rating vector is copied to a second record with a different
 // "nonrating_tag". Neither tag nor pair ID is provided as a paceval variable.
 std::mt19937_64 rng(seed);std::vector<Policy> v;v.reserve(2*pairs);
 for(std::size_t i=0;i<pairs;++i){Inputs x={double(rng()%26),double(rng()%5),
 1.0+double(rng()%491)/10.0,double(1+rng()%3),double(rng()%21)/10.0};
 validate(x);v.push_back({v.size(),i,0,x});v.push_back({v.size(),i,1,x});}
 return v;}
void write_policies(const fs::path&file,const std::vector<Policy>&v){
 std::ofstream f(file);check(f.good(),"could not write policy CSV");f<<std::setprecision(17);
 f<<"policy_id,pair_id,nonrating_tag,asset_age_years,claims,mileage_1000km,coverage_code,deductible_1000eur\n";
 for(auto&p:v)f<<p.id<<','<<p.pair<<','<<p.tag<<','<<p.x[0]<<','<<p.x[1]<<','<<p.x[2]<<','<<p.x[3]<<','<<p.x[4]<<'\n';}
std::vector<Policy> read_policies(const fs::path&file){
 std::ifstream f(file);check(f.good(),"could not open policy input CSV");std::string line;
 check(bool(std::getline(f,line))&&line=="policy_id,pair_id,nonrating_tag,asset_age_years,claims,mileage_1000km,coverage_code,deductible_1000eur","invalid CSV header");
 std::vector<Policy> out;while(std::getline(f,line)){
 check(!line.empty()&&std::count(line.begin(),line.end(),',')==7,"malformed policy CSV row");
 std::stringstream s(line);std::array<std::string,8> z;for(auto&cell:z)check(bool(std::getline(s,cell,','))&&!cell.empty(),"empty CSV field");
 auto tosize=[](const std::string&t){std::size_t n=0;auto v=std::stoull(t,&n);check(n==t.size(),"invalid integer field");return std::size_t(v);};
 Policy p{};p.id=tosize(z[0]);p.pair=tosize(z[1]);p.tag=int(tosize(z[2]));
 check(p.id==out.size()&&p.tag<=1,"IDs or tag invalid");
 for(std::size_t k=0;k<D;++k){std::size_t n=0;p.x[k]=std::stod(z[k+3],&n);check(n==z[k+3].size(),"invalid numeric field");}
 validate(p.x);out.push_back(p);check(out.size()<=40000,"too many policy rows");}
 check(!out.empty()&&out.size()%2==0,"expected paired synthetic records");
 for(std::size_t i=0;i<out.size();i+=2){check(out[i].pair==out[i+1].pair&&out[i].tag==0&&out[i+1].tag==1&&out[i].x==out[i+1].x,"counterfactual pair mismatch");}
 return out;}
std::vector<double> evaluate(PACEVAL_HANDLE h,const std::vector<Policy>&v,std::size_t batch){
 std::vector<double> result(v.size()),in(batch*D),out(batch);std::vector<int> error(batch,0);
 for(std::size_t offset=0;offset<v.size();offset+=batch){auto count=std::min(batch,v.size()-offset);
 for(std::size_t j=0;j<count;++j){validate(v[offset+j].x);for(std::size_t k=0;k<D;++k)in[j*D+k]=v[offset+j].x[k];}
 // SDK convention: TRUE denotes that an error occurred!
 bool failed=paceval_dGetComputationResultExt(h,in.data(),(unsigned long)count,out.data(),nullptr,nullptr,error.data());
 check(!failed,"paceval batch reported failure");
 for(std::size_t j=0;j<count;++j){check(error[j]==0&&std::isfinite(out[j])&&out[j]>0,"invalid premium result");result[offset+j]=out[j];}}
 return result;}
void self_test(){
 auto policies=generate(20,17);check(policies.size()==40,"generation count");
 for(std::size_t i=0;i<policies.size();i+=2)check(policies[i].x==policies[i+1].x,"counterfactual values");
 for(std::size_t i=0;i<100;++i){auto m=model_for(i);m.expr=expression(m);
 for(auto&p:policies)check(std::isfinite(native(m,p.x))&&native(m,p.x)>0,"invalid reference tariff");}
 bool caught=false;try{validate({5,0,70,1,0});}catch(const std::exception&){caught=true;}check(caught,"mileage validation missing");
 caught=false;try{validate({5,1.5,12,1,0});}catch(const std::exception&){caught=true;}check(caught,"claims validation missing");
 std::cout<<"native policy and model self-tests PASS\n";}
void run(const Config&c){
 fs::create_directories(c.out);const auto v=c.input.empty()?generate(c.pairs,c.seed):read_policies(c.input);
 check(v.size()>=2,"no policies");write_policies(c.out/"policies.csv",v);
 Engine runtime;std::vector<Model> models;std::vector<Graph> graphs;
 models.reserve(c.models);graphs.reserve(c.models);
 for(std::size_t i=0;i<c.models;++i){models.push_back(model_for(i));graphs.push_back(graph_for(models.back()));}
 std::ofstream mod(c.out/"models.csv"),eva(c.out/"premiums.csv"),stats(c.out/"model_summary.csv"),update(c.out/"model_update.csv");
 check(mod.good()&&eva.good()&&stats.good()&&update.good(),"output file open failed");
 for(auto*f:{&mod,&eva,&stats,&update})(*f)<<std::setprecision(17);
 mod<<"model_id,version,family,formula,base,a,c,m,g,h,f\n";
 eva<<"model_id,version,policy_id,pair_id,nonrating_tag,premium_eur,native_premium_eur,abs_difference\n";
 stats<<"model_id,version,policies,mean_premium_eur,min_premium_eur,max_premium_eur,max_native_abs_difference,max_tag_pair_difference\n";
 update<<"model_id,policy_id,old_version,new_version,old_premium,new_premium,unrelated_model_unchanged\n";
 std::size_t count=0;double global_err=0,global_pair=0;
 std::vector<double> old_version,unchanged;
 for(std::size_t i=0;i<c.models;++i){auto&m=models[i];auto results=evaluate(graphs[i].h,v,c.batch);
 if(i==17)old_version=results;
 if(i==18)unchanged=results;
 mod<<i<<','<<m.version<<','<<m.family<<','<<m.expr<<','<<m.base<<','<<m.a<<','<<m.c<<','<<m.m<<','<<m.g<<','<<m.h<<','<<m.f<<'\n';
 double total=0,lo=std::numeric_limits<double>::infinity(),hi=0,maxerr=0,maxpair=0;
 for(std::size_t j=0;j<v.size();++j){double expected=native(m,v[j].x),err=std::abs(results[j]-expected);
 check(err<=2e-10*(1+std::abs(expected)),"native mismatch model="+std::to_string(i));
 global_err=std::max(global_err,err);maxerr=std::max(maxerr,err);total+=results[j];lo=std::min(lo,results[j]);hi=std::max(hi,results[j]);
 eva<<i<<','<<m.version<<','<<j<<','<<v[j].pair<<','<<v[j].tag<<','<<results[j]<<','<<expected<<','<<err<<'\n';++count;}
 for(std::size_t j=0;j<v.size();j+=2){double diff=std::abs(results[j]-results[j+1]);maxpair=std::max(maxpair,diff);global_pair=std::max(global_pair,diff);
 check(diff==0.0,"nonrating tag influenced a tariff result");}
 stats<<i<<','<<m.version<<','<<v.size()<<','<<total/double(v.size())<<','<<lo<<','<<hi<<','<<maxerr<<','<<maxpair<<'\n';}
 // The replacement is an independently versioned mathematical object; the old
 // formula is retained in the CSV and all other preexisting handles survive.
 if(c.models>=19){Model revised=models[17];revised.version=2;revised.base*=1.04;
 Graph fresh=graph_for(revised);auto now=evaluate(fresh.h,v,c.batch);
 auto again=evaluate(graphs[18].h,v,c.batch);
 check(again==unchanged,"an unrelated model was invalidated by tariff update");
 for(std::size_t j=0;j<v.size();++j){double ref=native(revised,v[j].x);
 check(std::abs(now[j]-ref)<=2e-10*(1+std::abs(ref)),"updated model mismatch");
 if(j<64)update<<17<<','<<j<<",1,2,"<<old_version[j]<<','<<now[j]<<",true\n";}}
 // Smooth TINC experiment. No globally certified enclosure is inferred from
 // empirical high-precision inclusion; raw endpoints are preserved unmodified.
 Model dummy=model_for(0);dummy.expr="age*age+claims*claims";
 Graph tinc(paceval_CreateComputation(dummy.expr.c_str(),D,VARS,true,nullptr));
 check(tinc.h&&!paceval_GetIsError(tinc.h),"failed to build diagnostic TINC graph");
 std::ofstream tf(c.out/"tinc_samples.csv");check(tf.good(),"TINC CSV open failed");tf<<std::setprecision(17);
 tf<<"policy_id,asset_age_years,claims,point_value,raw_min,raw_max\n";
 for(std::size_t sample=0;sample<std::min(std::size_t(24),v.size()/2);++sample){
 // Use one member from each counterfactual pair: 24 distinct rating records.
 std::size_t j=2*sample;double lo=0,hi=0;Inputs scratch=v[j].x;double value=paceval_dGetComputationResult(tinc.h,scratch.data(),&lo,&hi);
 check(!paceval_GetIsError(tinc.h)&&std::isfinite(value)&&std::isfinite(lo)&&std::isfinite(hi)&&lo<=hi,"TINC error");
 tf<<j<<','<<v[j].x[0]<<','<<v[j].x[1]<<','<<value<<','<<lo<<','<<hi<<'\n';}
 std::ofstream report(c.out/"run_summary.json");check(report.good(),"summary open failed");report<<std::setprecision(17);
 report<<"{\n  \"scope\": \"synthetic numerical feasibility, not approved actuarial ratemaking\",\n"
 <<"  \"policies\": "<<v.size()<<",\n  \"counterfactual_pairs\": "<<v.size()/2
 <<",\n  \"models\": "<<c.models<<",\n  \"evaluations\": "<<count
 <<",\n  \"max_native_absolute_difference\": "<<global_err
 <<",\n  \"max_nonrating_tag_pair_difference\": "<<global_pair
 <<",\n  \"seed\": "<<c.seed<<"\n}\n";
 std::cout<<"PASS: "<<c.models<<" paceval graphs, "<<v.size()<<" policies, "<<count
 <<" independently compared premiums, paired-tag max difference "<<global_pair<<"; max native difference "<<global_err<<"\n";
}
}
int main(int argc,char**argv){try{auto c=args(argc,argv);if(c.selftest)self_test();else run(c);return 0;}
 catch(const std::exception& e){std::cerr<<"ERROR: "<<e.what()<<'\n';return 1;}}
