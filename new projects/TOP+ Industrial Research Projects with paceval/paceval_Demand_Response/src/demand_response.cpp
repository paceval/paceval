// paceval: Demand-Response Incentive Mathematics -- RESEARCH DEMONSTRATOR
// Copyright notices in the original paceval_main.h/cpp are retained verbatim.
// The actual proprietary runtime is supplied separately, never redistributed.
//
// Mathematical boundary:
// - paceval creates one independently versioned graph per mathematical rule;
//   its original C++ facade paceval_main.cpp is compiled into this executable.
// - This C++ host generates/validates hourly load data, applies measured-load
//   eligibility and cap rules, checks daily energy balance, and aggregates sums.
// - Rule values are illustrative EUR benefits combining separately labelled
//   shifted-energy price advantage, program bonus and modeled costs/penalties.
//   They are NOT actual regulatory settlement, validated response forecasts,
//   optimization instructions or distribution-grid feasibility certificates.
//
// No ``max'' or ``min'' is delegated to the expression parser. The trusted
// host first validates measured delivery; non-smooth eligibility is explicit.
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
#include <sstream>
#include <stdexcept>
#include <string>
#include <vector>
namespace fs = std::filesystem;
namespace {
constexpr double PI=3.141592653589793238462643383279502884;
constexpr std::size_t NVAR=4;
constexpr char VARS[]="del req pe pr";
using Inputs=std::array<double,NVAR>; // kWh, kWh, EUR/kWh, EUR/kWh
struct Config {std::size_t days=14,rules=100,batch=128; fs::path out="out",input;bool self_test=false;};
void insist(bool ok,const std::string&msg){if(!ok)throw std::runtime_error(msg);}
std::size_t as_size(const std::string&s,const std::string&label,std::size_t max){
 insist(!s.empty()&&s[0]!='-',"negative/empty "+label);std::size_t n=0;auto x=std::stoull(s,&n);
 insist(n==s.size()&&x>=1&&x<=max,"invalid "+label);return std::size_t(x);
}
Config args(int argc,char**argv){Config c;for(int i=1;i<argc;++i){std::string a=argv[i];
 if(a=="--self-test"){c.self_test=true;continue;}insist(i+1<argc,"missing value for "+a);
 const std::string v=argv[++i];if(a=="--days")c.days=as_size(v,a,366);
 else if(a=="--rules")c.rules=as_size(v,a,100);
 else if(a=="--batch")c.batch=as_size(v,a,8192);
 else if(a=="--out")c.out=v;else if(a=="--input")c.input=v;
 else throw std::runtime_error("unknown option: "+a);
 }return c;}
struct Engine{Engine(){insist(paceval_InitializeLibrary(nullptr),"paceval_InitializeLibrary failed");}
 ~Engine(){paceval_FreeLibrary();}Engine(const Engine&)=delete;Engine&operator=(const Engine&)=delete;};
struct Graph{PACEVAL_HANDLE h=nullptr;explicit Graph(PACEVAL_HANDLE ptr=nullptr):h(ptr){}
 ~Graph(){if(h)paceval_DeleteComputation(h);}Graph(const Graph&)=delete;Graph&operator=(const Graph&)=delete;
 Graph(Graph&&o)noexcept:h(o.h){o.h=nullptr;}
 Graph&operator=(Graph&&o)noexcept{if(this!=&o){if(h)paceval_DeleteComputation(h);h=o.h;o.h=nullptr;}return *this;}};
struct Hour{std::size_t id,day,hour;double baseline,actual,pe,pr,requested,cap;bool event,quality;};
struct Rule{std::size_t id;int version,family;double alpha,bonus,penalty,comfort,cubic;std::string formula;};
std::string num(double x){std::ostringstream o;o<<std::setprecision(17)<<x;return "("+o.str()+")";}
Rule make_rule(std::size_t id){Rule r{};r.id=id;r.version=1;r.family=int(id%4);
 r.alpha=0.85+0.01*double(id%29); // dimensionless bill-saving multiplier
 r.bonus=0.025+0.002*double(id%23); // EUR/kWh, hypothetical payment
 r.penalty=0.001+0.00035*double(id%17); // EUR/kWh^2
 r.comfort=0.0007+0.0002*double(id%13); // EUR/kWh^2
 r.cubic=0.00002+0.000007*double(id%11); // EUR/kWh^3
 return r;}
std::string expression(Rule&r){
 // Parenthesize all literal constants to eliminate unary-minus parsing ambiguity.
 std::string s=num(r.alpha)+"*del*(pe-pr)+"+num(r.bonus)+"*del";
 if(r.family>=1)s+="-"+num(r.penalty)+"*(req-del)*(req-del)";
 if(r.family>=2)s+="-"+num(r.comfort)+"*del*del";
 if(r.family>=3)s+="-"+num(r.cubic)+"*del*del*del";
 r.formula=s;return s;
}
double native(const Rule&r,const Inputs&x){const double d=x[0],q=x[1],pe=x[2],pr=x[3];
 double v=r.alpha*d*(pe-pr)+r.bonus*d;
 if(r.family>=1)v-=r.penalty*(q-d)*(q-d);
 if(r.family>=2)v-=r.comfort*d*d;
 if(r.family>=3)v-=r.cubic*d*d*d;
 return v;}
// The study does not promise any customer response. The following is an
// explicitly deterministic, synthetic shift schedule with daily catch-up.
std::vector<Hour> generate(std::size_t days){std::vector<Hour> v;v.reserve(days*24);
 for(std::size_t day=0;day<days;++day){
 std::array<double,24> baseline{},actual{},req{},cap{},pe{},pr{};
 double sum=0;for(std::size_t h=0;h<24;++h){
 baseline[h]=53+10*std::sin(2*PI*(double(h)-8)/24)+2.0*std::cos(2*PI*double(day)/7);
 actual[h]=baseline[h];pe[h]=(h>=17&&h<=19)?0.315+0.006*double(day%5):0.165+0.016*std::sin(2*PI*double(h)/24);
 pr[h]=0.118+0.006*double(day%4);req[h]=0;cap[h]=0;}
 for(std::size_t h=17;h<=19;++h){
 double sh=6.0+0.50*double((day+h)%6);cap[h]=9.0;req[h]=sh;
 if(day==4&&h==18){req[h]=12.0;sh=0.0;} // deliberately false claimed event: no measured reduction
 if(day==7&&h==17){req[h]=12.0;cap[h]=6.0;sh=6.0;} // over-request capped at 6 kWh
 actual[h]-=sh;sum+=sh;}
 // On this controlled one-hour-grid example, all event energy is recovered in
 // three later hours of the SAME day: no erased energy, no free energy.
 for(std::size_t h=20;h<=22;++h)actual[h]+=sum/3;
 for(std::size_t h=0;h<24;++h){bool evt=(h>=17&&h<=19);
 bool quality=!(day==3&&h==18); // one deliberately invalid meter-quality flag
 v.push_back({v.size(),day,h,baseline[h],actual[h],pe[h],pr[h],req[h],cap[h],evt,quality});}}
 return v;}
void validate(const Hour&h){
 insist(h.hour<24&&h.day<=366,"hour or day outside range");
 for(double x:{h.baseline,h.actual,h.pe,h.pr,h.requested,h.cap})insist(std::isfinite(x),"non-finite hourly data");
 insist(h.baseline>0&&h.baseline<=10000&&h.actual>=0&&h.actual<=10000,"load outside range");
 insist(h.pe>=0&&h.pe<=3&&h.pr>=0&&h.pr<=3,"price outside [0,3] EUR/kWh");
 insist(h.requested>=0&&h.requested<=10000&&h.cap>=0&&h.cap<=10000,"requested/cap outside range");
 if(!h.event)insist(h.requested==0&&h.cap==0,"request outside DR event");
}
// Quality-invalid hours are excluded. The minimum is bounded by actual
// meter reduction and physical flexibility; requesting > delivered cannot
// generate an undeserved positive modeled energy benefit.
Inputs eligible(const Hour&h){validate(h);
 if(!h.event||!h.quality)return {0,0,h.pe,h.pr};
 const double measured=std::max(0.0,h.baseline-h.actual);
 const double d=std::min({h.requested,h.cap,measured});
 return {d,h.requested,h.pe,h.pr};}
void check_daily(const std::vector<Hour>&rows){
 insist(rows.size()%24==0,"data must include complete 24-hour days");
 for(std::size_t base=0;base<rows.size();base+=24){
 double energy_base=0,energy_actual=0,red=0,rebound=0;
 for(std::size_t h=0;h<24;++h){const auto&r=rows[base+h];validate(r);
 insist(r.id==base+h&&r.day==base/24&&r.hour==h,"nonsequential synthetic day-hour index");
 energy_base+=r.baseline;energy_actual+=r.actual;
 if(h>=17&&h<=19)red+=r.baseline-r.actual;
 if(h>=20&&h<=22)rebound+=r.actual-r.baseline;}
 insist(std::abs(energy_base-energy_actual)<2e-9,"daily energy must be conserved (synthetic shift model)");
 insist(std::abs(red-rebound)<2e-9,"event reduction and rebound do not reconcile");}}
std::string csv_hdr(){return "index,day,hour,baseline_kwh,actual_kwh,price_event_eur_kwh,price_recovery_eur_kwh,requested_kwh,capacity_kwh,event,quality";}
void write_hours(const fs::path&filename,const std::vector<Hour>&v){std::ofstream out(filename);
 insist(out.good(),"cannot write hourly input CSV");out<<std::setprecision(17)<<csv_hdr()<<'\n';
 for(auto&h:v)out<<h.id<<','<<h.day<<','<<h.hour<<','<<h.baseline<<','<<h.actual<<','<<h.pe<<','<<h.pr<<','<<h.requested<<','<<h.cap<<','<<int(h.event)<<','<<int(h.quality)<<'\n';}
std::vector<Hour> read_hours(const fs::path&filename){std::ifstream in(filename);
 insist(in.good(),"cannot read hourly CSV");std::string ln;insist(bool(std::getline(in,ln))&&ln==csv_hdr(),"invalid hourly CSV header");
 std::vector<Hour> v;while(std::getline(in,ln)){
 insist(!ln.empty()&&std::count(ln.begin(),ln.end(),',')==10,"malformed hourly CSV row");
 std::istringstream s(ln);std::array<std::string,11> cells{};for(auto&c:cells)insist(bool(std::getline(s,c,','))&&!c.empty(),"missing hourly cell");
 auto integer=[](const std::string&x){std::size_t p=0;auto v=std::stoull(x,&p);insist(p==x.size(),"invalid integer");return std::size_t(v);};
 auto number=[](const std::string&x){std::size_t p=0;auto v=std::stod(x,&p);insist(p==x.size()&&std::isfinite(v),"invalid float");return v;};
 Hour h{};h.id=integer(cells[0]);h.day=integer(cells[1]);h.hour=integer(cells[2]);
 h.baseline=number(cells[3]);h.actual=number(cells[4]);h.pe=number(cells[5]);h.pr=number(cells[6]);
 h.requested=number(cells[7]);h.cap=number(cells[8]);int ev=int(integer(cells[9])),qu=int(integer(cells[10]));
 insist(ev<=1&&qu<=1,"event and quality flags must be zero or one");h.event=ev==1;h.quality=qu==1;
 validate(h);v.push_back(h);insist(v.size()<=366*24,"CSV exceeded 366 days");}
 insist(!v.empty(),"empty input CSV");check_daily(v);return v;}
Graph compile(Rule&r){const auto s=expression(r);Graph g(paceval_CreateComputation(s.c_str(),NVAR,VARS,false,nullptr));
 insist(g.h&&!paceval_GetIsError(g.h),"paceval cannot compile rule "+std::to_string(r.id)+" expression="+s);return g;}
std::vector<double> evaluate(PACEVAL_HANDLE h,const std::vector<Inputs>&v,std::size_t batch){
 std::vector<double> ans(v.size()),flat(batch*NVAR),out(batch);std::vector<int> error(batch);
 for(std::size_t offset=0;offset<v.size();offset+=batch){std::size_t n=std::min(batch,v.size()-offset);
 for(std::size_t k=0;k<n;++k)for(std::size_t j=0;j<NVAR;++j)flat[k*NVAR+j]=v[offset+k][j];
 // paceval SDK returns TRUE if the batch reports an error (unusual convention).
 const bool failed=paceval_dGetComputationResultExt(h,flat.data(),(unsigned long)n,out.data(),nullptr,nullptr,error.data());
 insist(!failed,"paceval batch failed");
 for(std::size_t k=0;k<n;++k){insist(error[k]==0&&std::isfinite(out[k]),"non-finite paceval result");ans[offset+k]=out[k];}}
 return ans;}
void native_test(){auto rows=generate(8);check_daily(rows);
 bool false_found=false;for(auto&h:rows){if(h.event&&h.requested>0&&h.actual==h.baseline){false_found=true;insist(eligible(h)[0]==0,"false incentive");}}
 insist(false_found,"missing simulated false request");for(std::size_t i=0;i<100;++i){auto r=make_rule(i);
 for(auto&h:rows)insist(std::isfinite(native(r,eligible(h))),"invalid native rule");}
 bool bad=false;try{auto v=rows;v[0].pe=-0.25;check_daily(v);}catch(const std::exception&){bad=true;}
 insist(bad,"negative price passed validation");bad=false;
 try{auto v=rows;v[0].actual+=1;check_daily(v);}catch(const std::exception&){bad=true;}
 insist(bad,"energy-creation mismatch passed validation");std::cout<<"native validation PASS\n";}
void run(const Config&c){fs::create_directories(c.out);
 const auto rows=c.input.empty()?generate(c.days):read_hours(c.input);check_daily(rows);write_hours(c.out/"hourly_trace.csv",rows);
 Engine runtime;std::vector<Rule> rules;std::vector<Graph> graphs;rules.reserve(c.rules);graphs.reserve(c.rules);
 for(std::size_t i=0;i<c.rules;++i){rules.emplace_back(make_rule(i));graphs.emplace_back(compile(rules.back()));}
 std::vector<Inputs> inputs;inputs.reserve(rows.size());std::size_t quality_excluded=0,false_claims=0,capped=0;
 for(auto&h:rows){inputs.push_back(eligible(h));if(h.event&&!h.quality)++quality_excluded;
 if(h.event&&h.quality&&h.requested>0&&h.baseline<=h.actual)++false_claims;
 if(h.event&&h.quality&&h.requested>h.cap)++capped;}
 std::ofstream m(c.out/"rules.csv"),e(c.out/"evaluations.csv"),s(c.out/"rule_summary.csv"),u(c.out/"model_update.csv");
 insist(m.good()&&e.good()&&s.good()&&u.good(),"CSV output failure");
 for(auto*f:{&m,&e,&s,&u})(*f)<<std::setprecision(17);
 m<<"rule_id,version,family,alpha,bonus_eur_per_kwh,penalty_eur_per_kwh2,comfort_eur_per_kwh2,cubic_eur_per_kwh3,expression\n";
 e<<"rule_id,version,hour_index,day,hour,requested_kwh,delivered_kwh,event_price_eur_kwh,recovery_price_eur_kwh,value_eur,native_value_eur,absolute_difference,quality\n";
 s<<"rule_id,version,rows,event_hours,total_value_eur,positive_value_eur,negative_value_eur,max_native_difference\n";
 u<<"rule_id,hour_index,old_version,new_version,old_value_eur,new_value_eur,unrelated_graph_unchanged\n";
 std::vector<double> before,unchanged;std::size_t checks=0;double global=0,grand=0;
 for(std::size_t id=0;id<c.rules;++id){Rule&r=rules[id];auto out=evaluate(graphs[id].h,inputs,c.batch);
 if(id==17)before=out;
 if(id==18)unchanged=out;
 m<<id<<','<<r.version<<','<<r.family<<','<<r.alpha<<','<<r.bonus<<','<<r.penalty<<','<<r.comfort<<','<<r.cubic<<','<<r.formula<<'\n';
 double total=0,positives=0,negatives=0,maxerr=0;std::size_t events=0;
 for(std::size_t j=0;j<rows.size();++j){const double reference=native(r,inputs[j]);
 const double err=std::abs(out[j]-reference);insist(err<=5e-12*(1+std::abs(reference)),"paceval/native mismatch");
 global=std::max(global,err);maxerr=std::max(maxerr,err);total+=out[j];grand+=out[j];
 positives+=std::max(0.0,out[j]);negatives+=std::min(0.0,out[j]);if(rows[j].event)++events;
 e<<id<<','<<r.version<<','<<rows[j].id<<','<<rows[j].day<<','<<rows[j].hour<<','<<inputs[j][1]<<','<<inputs[j][0]<<','<<inputs[j][2]<<','<<inputs[j][3]<<','<<out[j]<<','<<reference<<','<<err<<','<<int(rows[j].quality)<<'\n';++checks;}
 s<<id<<','<<r.version<<','<<rows.size()<<','<<events<<','<<total<<','<<positives<<','<<negatives<<','<<maxerr<<'\n';}
 // Only rule 17 is updated; all other graph handles remain live and untouched.
 if(c.rules>=19){Rule new_rule=rules[17];new_rule.version=2;new_rule.bonus+=0.015;Graph replacement=compile(new_rule);
 auto after=evaluate(replacement.h,inputs,c.batch);auto untouched=evaluate(graphs[18].h,inputs,c.batch);
 insist(untouched==unchanged,"unrelated graph changed after update");
 for(std::size_t j=0;j<rows.size();++j){const double reference=native(new_rule,inputs[j]);
 insist(std::abs(after[j]-reference)<=5e-12*(1+std::abs(reference)),"updated graph mismatch");
 if(j<128)u<<17<<','<<j<<",1,2,"<<before[j]<<','<<after[j]<<",true\n";}}
 // Controlled TINC experiment uses binary-exact sample inputs; raw endpoints
 // are retained unchanged, and independently checked by Python/multidecimal.
 const char* tinc_expr="del*(pe-pr)";Graph tinc(paceval_CreateComputation(tinc_expr,NVAR,VARS,true,nullptr));
 insist(tinc.h&&!paceval_GetIsError(tinc.h),"TINC graph creation failed");
 std::ofstream t(c.out/"tinc_samples.csv");insist(t.good(),"TINC CSV failed");t<<std::setprecision(17);
 t<<"sample_id,delivered_kwh,requested_kwh,event_price,recovery_price,raw_point,raw_lower,raw_upper\n";
 for(int i=0;i<24;++i){Inputs x={1.0+i/8.0,1.0+i/8.0,0.375,0.125};double low=0,high=0;
 const double point=paceval_dGetComputationResult(tinc.h,x.data(),&low,&high);
 insist(!paceval_GetIsError(tinc.h)&&std::isfinite(low)&&std::isfinite(high)&&low<=high,"TINC failure");
 t<<i<<','<<x[0]<<','<<x[1]<<','<<x[2]<<','<<x[3]<<','<<point<<','<<low<<','<<high<<'\n';}
 std::ofstream report(c.out/"validation_summary.json");insist(report.good(),"cannot write summary");report<<std::setprecision(17);
 report<<"{\n  \"scope\": \"synthetic research; not regulatory settlement or operating control\",\n"
 <<"  \"days\": "<<rows.size()/24<<",\n  \"hours\": "<<rows.size()<<",\n  \"rules\": "<<c.rules
 <<",\n  \"paceval_evaluations\": "<<checks<<",\n  \"max_native_absolute_error_eur\": "<<global
 <<",\n  \"quality_excluded_event_hours\": "<<quality_excluded
 <<",\n  \"false_claim_event_hours\": "<<false_claims
 <<",\n  \"capped_event_hours\": "<<capped<<",\n  \"aggregate_modeled_value_eur\": "<<grand<<"\n}\n";
 std::cout<<"PASS: "<<c.rules<<" reusable paceval graphs, "<<rows.size()<<" hourly traces, "<<checks
 <<" numerically checked outputs, maximum native difference "<<global
 <<" EUR; excluded quality="<<quality_excluded<<", false claims="<<false_claims<<", cap hits="<<capped<<'\n';
}
} // namespace
int main(int argc,char**argv){try{auto c=args(argc,argv);if(c.self_test)native_test();else run(c);return 0;}
 catch(const std::exception&e){std::cerr<<"ERROR: "<<e.what()<<'\n';return 1;}}
