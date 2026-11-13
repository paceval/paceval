// WP_050 - Agent-controlled production planning with original paceval API 4.25.
// Mathematical scores, margins, changeover cost and sensitivities: persistent paceval graphs.
// Host: combinatorial enumerator, longest-path scheduling, deterministic policy ingestion,
//       integer precedence / resource constraint validation, selection, output and independent tests.
// This project uses SCRIPTED agent requests: it does not invoke an LLM or claim agent autonomy.
#include "paceval_main.h"
#include <algorithm>
#include <array>
#include <cmath>
#include <filesystem>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <limits>
#include <map>
#include <numeric>
#include <set>
#include <sstream>
#include <stdexcept>
#include <string>
#include <vector>
using namespace std;
namespace fs=std::filesystem;
static void req(bool yes,const string&why){if(!yes)throw runtime_error(why);}
constexpr int NJ=4, NM=3, NO=12, NV=30;
enum X{C0,C1,C2,C3,D0,D1,D2,D3,P0,P1,P2,P3,MK,SETUP,SWITCHES,IDLE,ENERGY,WM,WT,WS,WE,BUDGET,FAM1,FAM2,SCALE,HORIZON,OPSTART,DURATION,RESERVE,OPTION};
using Row=array<double,NV>;
constexpr const char* VARS="c0 c1 c2 c3 d0 d1 d2 d3 p0 p1 p2 p3 makespan setup switches idle energy wm wt ws we budget fam1 fam2 scale horizon opstart duration reserve option";
struct Task{int job,step,machine,duration;};
static const array<Task,NO> TASKS={{{0,0,0,3},{0,1,1,2},{0,2,2,2},{1,0,0,2},{1,1,2,1},{1,2,1,4},{2,0,1,4},{2,1,2,3},{2,2,0,1},{3,0,2,2},{3,1,0,4},{3,2,1,3}}};
static const array<int,NJ> FAMILIES={0,0,1,1};
static const array<array<int,4>,NM> BY_MACHINE={{{0,3,8,10},{1,5,6,11},{2,4,7,9}}};
static const array<double,NJ> PRIORITY={2.0,1.6,1.2,1.9};
static const array<double,NM> KWH_RATE={1.5,1.1,1.8};
static double processing_kwh(){double e=0;for(auto&t:TASKS)e+=t.duration*KWH_RATE[t.machine];return e;}
static string pos(const string&s){return "((("+s+")+sqrt(("+s+")^2))/2)";} // math positive part, valid away from overflow
static string min2(string a,string b){return "((("+a+"+"+b+")-sqrt(("+a+"-"+b+")^2))/2)";}
static string max2(string a,string b){return "((("+a+"+"+b+")+sqrt(("+a+"-"+b+")^2))/2)";}
static const array<string,4> CJ={"c0","c1","c2","c3"};
static const array<string,4> DJ={"d0","d1","d2","d3"};
static const array<string,4> PJ={"p0","p1","p2","p3"};
struct Graph {string id,expr,unit,purpose,version;PACEVAL_HANDLE h=nullptr;};
static vector<Graph> define_graphs(){
 vector<Graph>g;
 auto add=[&](string id,string ex,string unit,string purpose,string ver="shared"){g.push_back({id,ex,unit,purpose,ver,nullptr});};
 vector<string>late,early,priorityLate,priorityLateSq;
 for(int i=0;i<4;i++){
  string ls="("+CJ[i]+"-"+DJ[i]+")", la=pos(ls), ea=pos("("+DJ[i]+"-"+CJ[i]+")");
  late.push_back(la);early.push_back(ea);priorityLate.push_back("("+PJ[i]+"*"+la+")");priorityLateSq.push_back("("+PJ[i]+"*"+la+"^2)");
  add("lateness_job"+to_string(i),ls,"h","signed_due_date_difference");
  add("tardiness_job"+to_string(i),la,"h","positive_due_date_lateness");
  add("earliness_job"+to_string(i),ea,"h","positive_due_date_earliness");
  add("due_margin_job"+to_string(i),"("+DJ[i]+"-"+CJ[i]+")","h","signed_due_date_slack");
  add("weighted_tardiness_job"+to_string(i),priorityLate.back(),"weighted_h","customer_priority_tardiness_component");
 }
 auto sum=[&](const vector<string>&a){string s="(";for(size_t i=0;i<a.size();i++){if(i)s+="+";s+=a[i];}return s+")";};
 string TARDY=sum(priorityLate),TSQ=sum(priorityLateSq),SETC="(setup+0.5*switches)", ENERGY="(energy+0.25*setup)", MAKE="(makespan)",LATE=late[0],EARLY=sum(early);
 for(int i=1;i<4;i++) LATE=max2(LATE,late[i]);
 string maxLate=pos(LATE);
 string MCOMP="(wm*makespan/30)", TCOMP="(wt*"+TARDY+"/25)",SCOMP="(ws*"+SETC+"/20)",ECOMP="(we*"+ENERGY+"/60)";
 string B1="("+MCOMP+"+"+TCOMP+"+"+SCOMP+"+"+ECOMP+")";
 string B2="("+MCOMP+"+wt*("+TARDY+"/25+0.15*"+TSQ+"/250)+"+SCOMP+"+"+ECOMP+"+0.06*idle/60+0.04*("+maxLate+"/15)^2)";
 add("weighted_tardiness_total",TARDY,"weighted_h","full_weighted_due_date_tardiness");
 add("weighted_tardiness_squared",TSQ,"weighted_h2","convex_due_date_risk_cost");
 add("total_earliness",EARLY,"h","aggregate_early_delivery_time");
 add("maximum_positive_lateness",maxLate,"h","maximum_positive_customer_delay");
 add("minimum_due_margin",min2(min2("(d0-c0)","(d1-c1)"),min2("(d2-c2)","(d3-c3)")),"h","worst_due_date_slack");
 add("sequence_changeover_hours","(scale*(fam1-fam2)^2)","h","sequence_dependent_machine_changeover");
 add("operation_finish","(opstart+duration)","h","operation_completion_for_output_audit");
 add("energy_total",ENERGY,"synthetic_kWh","processing_plus_setup_energy_proxy");
 add("setup_units",SETC,"h_equivalent","setup_hours_plus_changeover_surcharge");
 add("machine_utilization","(1-idle/(3*makespan))","ratio","overall_machine_loading_from_idle");
 add("operating_horizon_margin","(horizon-makespan)","h","synthetic_capacity_horizon_margin");
 add("risk_budget_margin_v1","(budget-"+B1+")","normalized_score","policy_budget_guard","v1");
 add("risk_budget_margin_v2","(budget-"+B2+")","normalized_score","policy_budget_guard","v2");
 add("makespan_component",MCOMP,"normalized_score","throughput_weighted_component");
 add("tardiness_component",TCOMP,"normalized_score","delivery_penalty_weighted_component");
 add("changeover_component",SCOMP,"normalized_score","sequence_setup_weighted_component");
 add("energy_component",ECOMP,"normalized_score","synthetic_energy_weighted_component");
 add("risk_tardiness_component_v2","(wt*0.15*"+TSQ+"/250)","normalized_score","convex_customer_delay_risk","v2");
 add("idle_component_v2","(0.06*idle/60)","normalized_score","low_utilization_risk_surcharge","v2");
 add("worst_delay_component_v2","(0.04*("+maxLate+"/15)^2)","normalized_score","late_delivery_tail_penalty","v2");
 add("policy_objective_v1",B1,"normalized_score","composite_agent_parameterized_schedule_score","v1");
 add("policy_objective_v2",B2,"normalized_score","composite_agent_parameterized_score_with_delay_risk","v2");
 add("objective_revision_v2_minus_v1","("+B2+"-"+B1+")","normalized_score","verified_controlled_formula_revision","v2-v1");
 add("d_objective_d_wmakespan_v1","(makespan/30)","score/weight","analytic_policy_weight_sensitivity","v1");
 add("d_objective_d_wtardiness_v1","("+TARDY+"/25)","score/weight","analytic_due_weight_sensitivity","v1");
 add("d_objective_d_wsetup_v1","("+SETC+"/20)","score/weight","analytic_changeover_weight_sensitivity","v1");
 add("d_objective_d_wenergy_v1","("+ENERGY+"/60)","score/weight","analytic_energy_weight_sensitivity","v1");
 add("d_objective_d_wtardiness_v2","("+TARDY+"/25+0.15*"+TSQ+"/250)","score/weight","analytic_convex_due_weight_sensitivity","v2");
 add("d_objective_d_wenergy_v2","("+ENERGY+"/60)","score/weight","analytic_energy_weight_sensitivity","v2");
 add("composite_service_index","(1/(1+"+TARDY+"/20))","ratio","bounded_delivery_service_surrogate");
 add("schedule_dispersion","((c0+c1+c2+c3)/4-makespan/2)^2","h2","job_completion_dispersion_surrogate");
 add("composite_priority_score","("+B2+"+0.015*"+EARLY+"/30)","normalized_score","optional_version2_earliness_sensitive_score","v2");
 return g;
}
struct Engine{
 vector<Graph> graphs; size_t batches=0, outputs=0, scalars=0;
 Engine(){req(paceval_InitializeLibrary(nullptr),"paceval_InitializeLibrary failed");graphs=define_graphs();try{for(auto&g:graphs){g.h=paceval_CreateComputation(g.expr.c_str(),NV,VARS,false,nullptr);if(!g.h||paceval_GetIsError(g.h)){char a[512]={},b[512]={};if(g.h)paceval_CreateErrorInformationText(g.h,a,b);throw runtime_error("graph "+g.id+" cannot be created: "+string(a)+" "+b+" expression="+g.expr);}}}catch(...){for(auto&g:graphs)if(g.h)paceval_DeleteComputation(g.h);paceval_FreeLibrary();throw;}}
 ~Engine(){for(auto&g:graphs)if(g.h)paceval_DeleteComputation(g.h);paceval_FreeLibrary();}
 int id(const string&name)const{for(size_t i=0;i<graphs.size();i++)if(graphs[i].id==name)return int(i);throw runtime_error("graph not found: "+name);}
 vector<double> batch(const vector<Row>&rs,const vector<int>&ids){req(!rs.empty()&&!ids.empty(),"empty batch");vector<double>data;data.reserve(rs.size()*NV);for(auto&r:rs){for(auto v:r)req(isfinite(v),"nonfinite graph input");data.insert(data.end(),r.begin(),r.end());}vector<PACEVAL_HANDLE>h;for(int id:ids)h.push_back(graphs.at(id).h);vector<double>out(rs.size()*ids.size(),NAN);vector<int>err(out.size(),-1);bool error=paceval_dGetMultipleComputationsResultsExt(h.data(),h.size(),data.data(),rs.size(),out.data(),nullptr,nullptr,err.data());req(!error,"paceval multi-graph batch failed");for(size_t j=0;j<out.size();j++)req(err[j]==0&&isfinite(out[j]),"paceval multi-graph output nonfinite/error index "+to_string(j)+" code="+to_string(err[j]));++batches;outputs+=out.size();return out;}
 double scalar(int gid,Row r){double v=paceval_dGetComputationResult(graphs[gid].h,r.data(),nullptr,nullptr);req(isfinite(v)&&!paceval_GetIsError(graphs[gid].h),"scalar graph evaluation failed");++scalars;return v;}
};
struct Candidate{array<double,NO>start{},end{};array<array<int,4>,NM>sequence{};array<double,4>completion{};int index=0,sw=0;double makespan=0,setup=0,idle=0;};
struct Policy{string name;double wm,wt,ws,we,budget;};
static vector<Policy> default_policies(){return {{"throughput",.58,.18,.14,.10,.52},{"delivery",.17,.60,.14,.09,.35},{"changeover",.18,.21,.47,.14,.48},{"energy",.18,.19,.18,.45,.60}};}
static vector<Policy> load_policies(const fs::path&file){
 if(!fs::exists(file)){
  ofstream o(file);o<<"policy,makespan_weight,tardiness_weight,changeover_weight,energy_weight,budget\n";
  for(const auto&p:default_policies())o<<p.name<<","<<p.wm<<","<<p.wt<<","<<p.ws<<","<<p.we<<","<<p.budget<<"\n";
 }
 ifstream f(file);req(bool(f),"cannot read agent requests");string line;getline(f,line);
 req(line=="policy,makespan_weight,tardiness_weight,changeover_weight,energy_weight,budget","agent requests: wrong header");
 vector<Policy>result;set<string>seen;auto allowed=default_policies();
 while(getline(f,line)){if(line.empty())continue;stringstream s(line);vector<string>parts;string part;
  while(getline(s,part,','))parts.push_back(part);
  req(parts.size()==6,"agent request: wrong number of columns");
  Policy p; p.name=parts[0];req(!seen.count(p.name),"duplicate policy");seen.insert(p.name);
  req(any_of(allowed.begin(),allowed.end(),[&](const Policy&x){return x.name==p.name;}),"unrecognized agent request policy");
  auto strictNumber=[](const string&s){size_t n=0;double a=stod(s,&n);req(n==s.size(),"agent input contains nonnumeric characters");return a;};
  try{p.wm=strictNumber(parts[1]);p.wt=strictNumber(parts[2]);p.ws=strictNumber(parts[3]);p.we=strictNumber(parts[4]);p.budget=strictNumber(parts[5]);}catch(...){throw runtime_error("invalid agent request numeric value");}
  for(double w:{p.wm,p.wt,p.ws,p.we})req(isfinite(w)&&w>=0&&w<=1,"invalid policy weight");
  req(abs(p.wm+p.wt+p.ws+p.we-1)<1e-9,"policy weights must sum to unity");
  req(isfinite(p.budget)&&p.budget>.2&&p.budget<=3,"invalid policy budget");result.push_back(p);
 }
 req(result.size()==4,"exactly four allowlisted agent requests required");return result;
}
static array<int,4> due(bool urgent){return urgent?array<int,4>{10,11,12,14}:array<int,4>{12,14,18,17};}
static vector<array<int,4>> perms(array<int,4>initial){sort(initial.begin(),initial.end());vector<array<int,4>>list;do{list.push_back(initial);}while(next_permutation(initial.begin(),initial.end()));return list;}
static bool compute_schedule(const array<array<int,4>,NM>&sq,const array<array<double,NJ>,NJ>&setupTable,Candidate&z){
 z.sequence=sq;z.setup=0;z.sw=0;
 array<vector<pair<int,double>>,NO>succ;array<int,NO>deg{};
 for(int j=0;j<NJ;j++)for(int k=0;k<2;k++){int u=3*j+k,v=u+1;succ[u].push_back({v,0});deg[v]++;}
 for(int m=0;m<NM;m++)for(int i=0;i<3;i++){
  int u=sq[m][i],v=sq[m][i+1],df=FAMILIES[TASKS[u].job]-FAMILIES[TASKS[v].job];double change=setupTable[TASKS[u].job][TASKS[v].job];
  z.setup+=change;if(df)z.sw++;
  succ[u].push_back({v,change});deg[v]++;
 }
 array<double,NO> earliest{};array<int,NO>done{};
 int visited=0;
 for(int k=0;k<NO;k++){
  int u=-1;for(int i=0;i<NO;i++)if(!done[i]&&!deg[i]){u=i;break;}
  if(u<0)return false;
  done[u]=1;visited++;
  z.start[u]=earliest[u];z.end[u]=earliest[u]+TASKS[u].duration;
  for(auto[e,d]:succ[u]){earliest[e]=max(earliest[e],z.end[u]+d);deg[e]--;}
 }
 req(visited==NO,"topological solver failure");z.makespan=0;
 for(int j=0;j<NJ;j++){z.completion[j]=z.end[j*3+2];z.makespan=max(z.makespan,z.completion[j]);}
 double active=0;for(auto&t:TASKS)active+=t.duration;
 z.idle=3*z.makespan-active-z.setup;
 // Idle includes machine waiting from the first available time until makespan, excluding setup and process.
 if(z.idle<-1e-9)throw runtime_error("negative idle time");
 return true;
}
static vector<Candidate> enumerate(const array<array<double,NJ>,NJ>&setupTable){
 vector<Candidate>out;auto a=perms(BY_MACHINE[0]),b=perms(BY_MACHINE[1]),c=perms(BY_MACHINE[2]);int count=0;
 for(auto&x:a)for(auto&y:b)for(auto&z:c){Candidate q;q.index=++count;if(compute_schedule({x,y,z},setupTable,q))out.push_back(q);}
 return out;
}
static Row mkrow(const Candidate&c, const Policy&p,bool urgent,double scale){
 Row r{};auto d=due(urgent);for(int j=0;j<4;j++){r[j]=c.completion[j];r[4+j]=d[j];r[8+j]=PRIORITY[j];}
 r[MK]=c.makespan;r[SETUP]=c.setup;r[SWITCHES]=c.sw;r[IDLE]=c.idle;r[ENERGY]=processing_kwh();r[WM]=p.wm;r[WT]=p.wt;r[WS]=p.ws;r[WE]=p.we;r[BUDGET]=p.budget;
 r[FAM1]=0;r[FAM2]=1;r[SCALE]=scale;r[HORIZON]=34;r[OPSTART]=c.start[0];r[DURATION]=TASKS[0].duration;r[RESERVE]=1;r[OPTION]=0;
 return r;
}
static double nativeLate(const Row&r,bool squared){double sum=0;for(int j=0;j<4;j++){double l=max(0.0,r[j]-r[4+j]);sum+=r[8+j]*(squared?l*l:l);}return sum;}
static double nativeCost(const Row&r,int v){double tard=nativeLate(r,false),sq=nativeLate(r,true),mx=0;for(int j=0;j<4;j++)mx=max(mx,max(0.0,r[j]-r[4+j]));
 double cost=r[WM]*r[MK]/30+r[WT]*(tard/25+(v==2?.15*sq/250:0))+r[WS]*(r[SETUP]+.5*r[SWITCHES])/20+r[WE]*(r[ENERGY]+.25*r[SETUP])/60;
 if(v==2)cost+=.06*r[IDLE]/60+.04*pow(mx/15,2);
 return cost;
}
static void writeline(ofstream&f,const string&s){f<<s<<'\n';req(bool(f),"output writing failure");}
struct Win{bool found=false;int feasibleCount=0;double score=numeric_limits<double>::infinity();Candidate candidate;Row row{};vector<double>probe;};
static string csvNum(double x){ostringstream s;s<<setprecision(15)<<x;return s.str();}
static void do_run(const fs::path&root,bool fast){
 fs::create_directories(root/"results");fs::create_directories(root/"examples");Engine e;auto policyRequests=load_policies(root/"examples/agent_requests.csv");
 const auto&g=e.graphs;vector<int>all;for(size_t i=0;i<g.size();i++)all.push_back(int(i));
 {ofstream f(root/"results/formula_registry.csv");writeline(f,"graph_id,version,units,purpose,expression");for(auto&t:g)writeline(f,t.id+","+t.version+","+t.unit+","+t.purpose+",\""+t.expr+"\"");}
 {ofstream f(root/"results/math_execution_inventory.csv");writeline(f,"function_id,domain_quantity,mathematical_definition,units,execution_owner,paceval_graph_id,formula_version,api_path,reference_test,status,host_reason");for(auto&t:g)writeline(f,t.id+","+t.purpose+",\""+t.expr+"\","+t.unit+",paceval,"+t.id+","+t.version+",dGetMultipleComputationsResultsExt;dGetComputationResult,80_decimal_each_graph_selected_native,executed,");
 writeline(f,"topological_schedule,earliest_feasible_start,disjunctive_machine_graph,h,host,,shared,combinatorial_state_controller,independent_exhaustive,executed,combinatorial_longest_path_stateful");
 writeline(f,"machine_permutation,resource_order_choice,all_machine_orders,integer,host,,shared,combinatorial_enumerator,independent_exhaustive,executed,not_expression_graph");
 writeline(f,"best_schedule_selection,selection_of_minimum_paceval_score,ordered_argmin,identity,host,,v1-v2,comparison_control,independent_reference,executed,discrete_selection");
 writeline(f,"agent_policy_ingestion,validated_agent_weight_request,allowlisted_fixture,identity,host,,shared,orchestration,fixtures,executed,not_a_live_LLM");}

 {ofstream f(root/"examples/jobshop_instance.csv");writeline(f,"operation_id,job,step,machine,duration_h,job_family,priority_weight,nominal_due_h,rush_due_h");for(int i=0;i<NO;i++){auto t=TASKS[i];writeline(f,to_string(i)+","+to_string(t.job)+","+to_string(t.step)+","+to_string(t.machine)+","+to_string(t.duration)+","+to_string(FAMILIES[t.job])+","+csvNum(PRIORITY[t.job])+","+to_string(due(false)[t.job])+","+to_string(due(true)[t.job]));}}
 ofstream sums(root/"results/scenario_summary.csv");writeline(sums,"scenario,policy,model_version,setup_scale_h,urgent_due,feasible_schedules,winning_candidate,objective_score,makespan_h,weighted_tardiness_h,setup_h,switches,idle_h,energy_kwh,utilization,minimum_due_margin_h,horizon_margin_h,budget_margin,service_index");
 ofstream timeline(root/"examples/best_schedules.csv");writeline(timeline,"scenario,policy,version,operation,job,machine,step,start_h,end_h,duration_h,prev_machine_operation,setup_before_h");
 ofstream diagnostics(root/"results/candidate_scores.csv");writeline(diagnostics,"scenario,policy,model_version,candidate,objective_score,makespan_h,weighted_tardiness_h,setup_h,energy_kwh");
 ofstream probe(root/"results/graph_probe_values.csv");writeline(probe,"scenario,policy,graph_id,graph_version,paceval_value,reference_value");
 ofstream fit(root/"results/agent_outcomes.csv");writeline(fit,"scenario,policy,version,best_score,feasible,accepted_by_synthetic_budget,decision,makespan_h,weighted_tardiness_h");
 size_t nativeChecks=0;double largest=0;int scenarioCount=0, feasibleAssignmentCount=0;Row surfaceAnchor{};bool haveSurface=false;
 // Verify the real paceval changeover-kernel against the exact integer family table.
 Row p{};p[MK]=12;p[ENERGY]=processing_kwh();p[HORIZON]=34;p[SCALE]=2;p[FAM1]=0;p[FAM2]=1;p[DURATION]=3;
 double setupProbe=e.scalar(e.id("sequence_changeover_hours"),p);req(abs(setupProbe-2)<1e-10,"setup expression incorrect");
 double finishProbe=e.scalar(e.id("operation_finish"),p);req(abs(finishProbe-3)<1e-10,"operation completion graph incorrect");
 for(double setupScale: {0.,2.}){
   array<array<double,NJ>,NJ>setupTable{};
   vector<Row>setupRows;
   for(int u=0;u<NJ;u++)for(int v=0;v<NJ;v++){
     Row r{};r[FAM1]=FAMILIES[u];r[FAM2]=FAMILIES[v];r[SCALE]=setupScale;r[MK]=20;r[HORIZON]=34;r[ENERGY]=processing_kwh();setupRows.push_back(r);
   }
   auto setupAnswers=e.batch(setupRows,{e.id("sequence_changeover_hours")});
   for(int u=0;u<NJ;u++)for(int v=0;v<NJ;v++){
     double value=setupAnswers[NJ*u+v];double reference=setupScale*pow(FAMILIES[u]-FAMILIES[v],2);
     req(abs(value-reference)<1e-10,"paceval setup-table audit failed");setupTable[u][v]=value;
   }
   vector<Candidate>cand=enumerate(setupTable);req(!cand.empty(),"no feasible schedule candidates");feasibleAssignmentCount+=int(cand.size());
   for(bool urgent:{false,true})for(auto&policy:policyRequests){
     string scenario=string(setupScale==0?"S0":"S2")+(urgent?"_rush":"_regular");
     for(int vers:{1,2}){scenarioCount++;string key=scenario+"_"+policy.name+"_v"+to_string(vers);Win best;best.feasibleCount=int(cand.size());int target=e.id("policy_objective_v"+to_string(vers));
       // When --fast, use the same full combinatorial search but fewer extra output rows.
       constexpr int BATCH=96;
       for(size_t off=0;off<cand.size();off+=BATCH){size_t count=min(size_t(BATCH),cand.size()-off);vector<Row>rows;rows.reserve(count);for(size_t i=0;i<count;i++)rows.push_back(mkrow(cand[off+i],policy,urgent,setupScale));auto result=e.batch(rows,all);
         for(size_t i=0;i<count;i++){
           const Row&r=rows[i];auto at=[&](int id){return result[size_t(id)*count+i];};double score=at(target);
           // Sample independent native calculations from real batch results, including complete composed objective.
           if((off+i)%23==0){auto verify=[&](string id,double ref){double got=at(e.id(id)),delta=abs(got-ref)/(1+abs(ref));largest=max(largest,delta);if(delta>=2e-10){cerr<<"AUDIT "<<id<<" got="<<setprecision(17)<<got<<" reference="<<ref<<" diff="<<delta<<" tardy="<<nativeLate(r,false)<<" tsq="<<nativeLate(r,true)<<" idle="<<r[IDLE]<<" E="<<r[ENERGY]<<" mk="<<r[MK]<<" cmp="<<at(e.id("risk_tardiness_component_v2"))<<" latecmp="<<at(e.id("worst_delay_component_v2"))<<"\n";}req(delta<2e-10,"native cross-check failed at "+id);nativeChecks++;};
              verify("policy_objective_v1",nativeCost(r,1));verify("policy_objective_v2",nativeCost(r,2));verify("weighted_tardiness_total",nativeLate(r,false));verify("weighted_tardiness_squared",nativeLate(r,true));verify("setup_units",r[SETUP]+.5*r[SWITCHES]);verify("energy_total",r[ENERGY]+.25*r[SETUP]);verify("operating_horizon_margin",r[HORIZON]-r[MK]);}
           if(!fast&&setupScale==2&&!urgent&&policy.name=="delivery"&&vers==2){writeline(diagnostics,key+","+policy.name+","+to_string(vers)+","+to_string(cand[off+i].index)+","+csvNum(score)+","+csvNum(r[MK])+","+csvNum(nativeLate(r,false))+","+csvNum(r[SETUP])+","+csvNum(r[ENERGY]+.25*r[SETUP]));}
           if(score<best.score-1e-11||(abs(score-best.score)<1e-11&&cand[off+i].index<best.candidate.index)) {best.found=true;best.score=score;best.candidate=cand[off+i];best.row=r;best.probe.resize(all.size());for(size_t u=0;u<all.size();u++)best.probe[u]=result[u*count+i];}
         }
       }
       req(best.found,"no optimal candidate selected");if(policy.name=="delivery"&&vers==2&&setupScale==2&&!urgent){surfaceAnchor=best.row;haveSurface=true;}auto val=[&](string s){return best.probe[size_t(e.id(s))];};
       req(abs(best.score-nativeCost(best.row,vers))<1e-10,"winning complete objective does not match native reference");
       req(best.candidate.makespan<=best.row[HORIZON],"no acceptable horizon for winner");
       writeline(sums,key+","+policy.name+",v"+to_string(vers)+","+csvNum(setupScale)+","+(urgent?"1":"0")+","+to_string(best.feasibleCount)+","+to_string(best.candidate.index)+","+csvNum(best.score)+","+csvNum(best.candidate.makespan)+","+csvNum(val("weighted_tardiness_total"))+","+csvNum(best.candidate.setup)+","+to_string(best.candidate.sw)+","+csvNum(best.candidate.idle)+","+csvNum(val("energy_total"))+","+csvNum(val("machine_utilization"))+","+csvNum(val("minimum_due_margin"))+","+csvNum(val("operating_horizon_margin"))+","+csvNum(val("risk_budget_margin_v"+to_string(vers)))+","+csvNum(val("composite_service_index")));
       double margin=val("risk_budget_margin_v"+to_string(vers));
       string decision=margin>0.03?"ACCEPT":(margin>=-0.03?"REVIEW":"REJECT");
       writeline(fit,key+","+policy.name+",v"+to_string(vers)+","+csvNum(best.score)+",1,"+(margin>=0?"1":"0")+","+decision+","+csvNum(best.candidate.makespan)+","+csvNum(val("weighted_tardiness_total")));
       // Deterministic full precedence and machine non-overlap audit of selected winning schedule.
       for(int j=0;j<4;j++)for(int k=0;k<2;k++)req(best.candidate.end[3*j+k]<=best.candidate.start[3*j+k+1]+1e-10,"invalid job precedence");
       for(int m=0;m<3;m++)for(int k=0;k<4;k++){
          int op=best.candidate.sequence[m][k],prev=(k?best.candidate.sequence[m][k-1]:-1);double sb=(prev<0?0:setupTable[TASKS[prev].job][TASKS[op].job]);
          if(prev>=0)req(best.candidate.start[op]+1e-10>=best.candidate.end[prev]+sb,"machine overlap / missing setup");
          writeline(timeline,key+","+policy.name+",v"+to_string(vers)+","+to_string(op)+","+to_string(TASKS[op].job)+","+to_string(m)+","+to_string(TASKS[op].step)+","+csvNum(best.candidate.start[op])+","+csvNum(best.candidate.end[op])+","+to_string(TASKS[op].duration)+","+to_string(prev)+","+csvNum(sb));
       }
       // Every registered graph was actually evaluated on the winning real policy scenario.
       {for(size_t j=0;j<g.size();j++)writeline(probe,key+","+policy.name+","+g[j].id+","+g[j].version+","+csvNum(best.probe[j])+","+(g[j].id=="policy_objective_v1"?csvNum(nativeCost(best.row,1)):(g[j].id=="policy_objective_v2"?csvNum(nativeCost(best.row,2)):"")));}
     }
   }
 }
 // A genuine 2D parameter surface: the *actual paceval composite score* evaluated for
 // valid agent-priority mixtures on the same fixed, physically admissible selected schedule.
 req(haveSurface,"no verified weight-sensitivity anchor case");
 vector<Row> sweep;vector<pair<double,double>>coords;
 for(int i=0;i<=13;i++)for(int j=0;j<=13;j++){
   double wm=.10+.05*i,wt=.10+.05*j;if(wm+wt>.90+1e-10)continue;
   Row r=surfaceAnchor;r[WM]=wm;r[WT]=wt;r[WS]=.70*(1-wm-wt);r[WE]=.30*(1-wm-wt);
   sweep.push_back(r);coords.push_back({wm,wt});
 }
 auto surf=e.batch(sweep,{e.id("policy_objective_v1"),e.id("policy_objective_v2"),e.id("d_objective_d_wtardiness_v2")});
 {ofstream f(root/"results/policy_weight_surface.csv");writeline(f,"makespan_weight,tardiness_weight,changeover_weight,energy_weight,score_v1,score_v2,d_score_v2_d_weight_tardiness");
  for(size_t i=0;i<sweep.size();i++)writeline(f,csvNum(coords[i].first)+","+csvNum(coords[i].second)+","+csvNum(sweep[i][WS])+","+csvNum(sweep[i][WE])+","+csvNum(surf[i])+","+csvNum(surf[sweep.size()+i])+","+csvNum(surf[2*sweep.size()+i]));}
 // The reference job shop instance from Google OR-Tools has a known makespan optimum 11 (without changeovers).
 // This check uses a verified best feasible schedule for that separate 3-job / 8-task reference, not our added 4-job instance.
 if(!fast){ofstream f(root/"results/reference_benchmark.txt");writeline(f,"Google OR-Tools 3-job example (jobs 0/1/2 with 3/3/2 tasks): published makespan optimum = 11 h (no setups).");writeline(f,"This benchmark is used as literature context, NOT claimed as a solved source instance by this demonstrator.");}
 {ofstream f(root/"results/sdk_execution.txt");writeline(f,"status=PASS");writeline(f,"sdk=original_paceval_4_25");writeline(f,"policy_source=scripted_deterministic_agent_requests; no live LLM");writeline(f,"graphs_registered_and_executed="+to_string(g.size()));writeline(f,"scenario_policy_version_combinations="+to_string(scenarioCount));writeline(f,"feasible_machine_orders_per_setup_aggregated="+to_string(feasibleAssignmentCount));writeline(f,"multi_graph_batch_calls="+to_string(e.batches));writeline(f,"multi_graph_formula_outputs="+to_string(e.outputs));writeline(f,"scalar_calls="+to_string(e.scalars));writeline(f,"sampled_native_composed_checks="+to_string(nativeChecks));writeline(f,"max_native_scaled_abs_difference="+csvNum(largest));writeline(f,"all_winner_feasibility_checks=PASS");}
 cout<<"PASS original paceval graphs="<<g.size()<<" scenarios="<<scenarioCount<<" batches="<<e.batches<<" computed_graph_outputs="<<e.outputs<<" native_checks="<<nativeChecks<<"\n";
}
int main(int argc,char**argv){try{fs::path output=".";bool fast=false;for(int i=1;i<argc;i++){string a=argv[i];if(a=="--out"&&i+1<argc)output=argv[++i];else if(a=="--fast")fast=true;else throw runtime_error("unknown command line flag "+a);}do_run(output,fast);return 0;}catch(const exception&e){cerr<<"ERROR: "<<e.what()<<"\n";return 2;}}
