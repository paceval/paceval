// WP_040 Factory-Line Digital Twin Formula Modules - reproducible original paceval SDK study.
// Copyright (c) 2026 research demonstration authors.
// Included paceval_main.h/.cpp retain their original SDK copyright and provenance.
// This is a synthetic four-station manufacturing line. It is NOT a live plant digital twin.
// ALL per-operation process models and analytical KPIs in the registry run in paceval.
// C++ alone owns event ordering, finite buffers, downtime scheduling, stable sorting,
// source generation and trace output. Independent native functions exist ONLY for audits.
#include "paceval_main.h"
#include <algorithm>
#include <array>
#include <cmath>
#include <cstdint>
#include <deque>
#include <filesystem>
#include <functional>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <limits>
#include <numeric>
#include <queue>
#include <sstream>
#include <stdexcept>
#include <string>
#include <tuple>
#include <vector>
using namespace std;
namespace fs=std::filesystem;
static void check(bool b,const string&msg){if(!b)throw runtime_error(msg);}
static constexpr int ST=4,NV=17,NMODELS=20;
static const char* VARIABLE_LIST="b wear temp load phase q busy count good horizon downtime energy price ideal blocked arrived cycle";
static constexpr array<double,ST> BASE{4.15,5.15,4.55,4.80};
using Input=array<double,NV>;
struct Formula{string id,expression,unit,meaning;PACEVAL_HANDLE handle=nullptr;};
static string fmt(double x){ostringstream o;o<<setprecision(14)<<x;return o.str();}
static string modelExpression(int k){
 // A deliberately transparent synthetically parameterized, always-positive local cycle model.
 const double bias=(k-9.5)*0.010;
 const double osc=(k%4+1)*0.003;
 const double coupled=((k%5)-2)*0.006;
 return "b*(1+("+fmt(bias)+")+0.011*wear+0.0009*(temp-22)^2+0.014*load+"+
  fmt(osc)+"*sin(phase+"+fmt(k*0.09)+")+("+fmt(coupled)+")*wear*load)";
}
static vector<Formula> makeRegistry(){
 vector<Formula> f;
 for(int k=0;k<NMODELS;++k){ostringstream id;id<<"cycle_module_v"<<setw(2)<<setfill('0')<<(k+1);
  f.push_back({id.str(),modelExpression(k),"min/operation","Interchangeable positive synthetic process-time expression"});}
 auto add=[&](string id,string exp,string unit,string why){f.push_back({id,exp,unit,why});};
 add("reject_probability","0.006+0.01*wear+0.00007*(temp-22)^2","fraction","Synthetic rejection probability per station operation");
 add("energy_per_operation","0.018*b*(1+0.2*load)","kWh/operation","Synthetic station electricity per completed operation");
 add("nominal_rate","60/b","operations/hour","Ideal nominal station rate");
 add("cycle_rate","60/cycle","operations/hour","Reciprocal cycle-time performance rate");
 add("quality_margin","0.05-(0.006+0.01*wear+0.00007*(temp-22)^2)","fraction","Margin below illustrative 5 percent quality threshold");
 add("cycle_delta","cycle-b","min","Difference of modeled cycle time from nominal time");
 add("running_fraction","busy/horizon","fraction","Active machining time divided by scenario horizon");
 add("calendar_uptime","(horizon-downtime)/horizon","fraction","Calendar availability excluding imposed machine downtime");
 add("performance_ratio","ideal*count/busy","fraction","Ideal processing minutes divided by actually busy minutes");
 add("station_first_pass_yield","good/count","fraction","One-station first-pass pass fraction");
 add("oee_like","(busy/horizon)*(ideal*count/busy)*(good/count)","fraction","Declared illustrative OEE-style combination (not certified ISO 22400 KPI)");
 add("line_good_throughput","60*good/horizon","units/hour","Good line output per simulated elapsed hour");
 add("line_gross_throughput","60*count/horizon","units/hour","Completed final station jobs per elapsed hour");
 add("line_yield","good/arrived","fraction","Final passed units relative to initial arrivals");
 add("energy_per_good","energy/good","kWh/unit","Synthetic energy per passed line unit");
 add("electricity_cost","energy*price","EUR proxy","Synthetic electricity cost for the run");
 add("blocked_fraction","blocked/(4*horizon)","fraction","Aggregate blocked-station minutes divided by all four station-minutes");
 add("takt_margin","60*good/horizon-10.5","units/hour","Difference from declared illustrative target throughput");
 return f;
}
static constexpr size_t G=38;
static uint64_t splitmix64(uint64_t x){x+=0x9e3779b97f4a7c15ULL;x=(x^(x>>30))*0xbf58476d1ce4e5b9ULL;x=(x^(x>>27))*0x94d049bb133111ebULL;return x^(x>>31);}
static double uniform01(uint64_t i,uint64_t s){return (splitmix64(20261113ULL+i*0x9e3779b9ULL+s*0x85ebca6bULL)>>11)*(1.0/9007199254740992.0);}
static Input makeInput(int j,int s){
 const double wear=fmod(j*0.019+s*0.17,1.0),temp=22.+3.5*sin(j*0.037+s*0.41);
 const double load=0.58+0.22*sin(j*0.061+s*0.21),phase=j*0.045;
 return {BASE[s],wear,temp,load,phase,0.,1.,1.,1.,1.,0.,1.,0.23,3.6,0.,1.,BASE[s]};
}
static double nativeCycle(int k,const Input&x){
 return x[0]*(1+(k-9.5)*0.010+0.011*x[1]+0.0009*pow(x[2]-22,2)+0.014*x[3]+(k%4+1)*0.003*sin(x[4]+k*0.09)+((k%5)-2)*0.006*x[1]*x[3]);
}
class Engine{
 vector<PACEVAL_HANDLE>handles;
 public:
 vector<Formula>formulas;
 size_t calls=0,outputs=0,audits=0;
 double max_scaled_error=0;
 Engine(){check(paceval_InitializeLibrary(nullptr),"original paceval initialization failed");formulas=makeRegistry();check(formulas.size()==G,"graph registry length changed");for(auto&f:formulas){
 f.handle=paceval_CreateComputation(f.expression.c_str(),NV,VARIABLE_LIST,false,nullptr);
 if(f.handle&&paceval_GetIsError(f.handle)){char msg[256]={0},det[256]={0};paceval_CreateErrorInformationText(f.handle,msg,det);cerr<<"PACEVAL DIAGNOSTIC "<<f.id<<" "<<msg<<" "<<det<<"\n";}
 check(f.handle!=nullptr&&!paceval_GetIsError(f.handle),"paceval graph create failure "+f.id+" "+f.expression);
 handles.push_back(f.handle);}}
 ~Engine(){for(auto h:handles)if(h)paceval_DeleteComputation(h);paceval_FreeLibrary();}
 vector<double>batch(const vector<Input>&in){
 check(!in.empty(),"empty paceval inputs");vector<double>flat;flat.reserve(in.size()*NV);
 for(auto&x:in){for(double z:x)check(isfinite(z),"nonfinite paceval input");check(x[0]>0 && x[1]>=0&&x[1]<=1&&x[2]>=10&&x[2]<=40&&x[3]>=0&&x[3]<=2,"operation parameter out of declared range");
 check(x[6]>0&&x[7]>0&&x[8]>0&&x[9]>0&&x[13]>0&&x[15]>0&&x[16]>0,"KPI positivity guard failed");flat.insert(flat.end(),x.begin(),x.end());}
 vector<double>r(G*in.size());vector<int>errs(r.size(),-17);
 // IMPORTANT: for this tested SDK, FALSE indicates success for the batch return.
 const bool failure=paceval_dGetMultipleComputationsResultsExt(handles.data(),(unsigned long)G,flat.data(),(unsigned long)in.size(),r.data(),nullptr,nullptr,errs.data());
 check(!failure,"paceval Multi-Graph batch API failed");
 for(size_t i=0;i<r.size();++i)check(errs[i]==0&&isfinite(r[i]),"paceval nonfinite/graph error");
 ++calls;outputs+=r.size();
 // Separate independently coded C++ oracle: tests pure formula outputs only.
 for(size_t k=0;k<in.size();k+=max<size_t>(1,in.size()/12)){
  for(int v=0;v<20;++v){double a=r[(size_t)v*in.size()+k],b=nativeCycle(v,in[k]);double err=abs(a-b)/(1+abs(b));
  max_scaled_error=max(max_scaled_error,err);check(err<3e-11,"independent process-duration oracle failed");++audits;}
  double prob=.006+.01*in[k][1]+.00007*pow(in[k][2]-22,2);
  double energy=.018*in[k][0]*(1+.2*in[k][3]);
  for(auto [idx,b]:vector<pair<size_t,double>>{{20,prob},{21,energy}}){double a=r[idx*in.size()+k];double err=abs(a-b)/(1+abs(b));max_scaled_error=max(max_scaled_error,err);check(err<3e-11,"independent quality/energy oracle failed");++audits;}
 }
 return r;
 }
};
struct Operation{Input input{};array<double,NMODELS>cycle{};double reject=0,energy=0;};
struct Window{double a,b;};
static const array<vector<Window>,ST> FAILURES{{
 {{350,390},{1370,1400}},{{220,255},{1080,1140}},{{650,685},{1600,1640}},{{540,590},{1880,1925}}
}};
static double earliestAvailable(int s,double t){for(auto&w:FAILURES[s])if(t>=w.a-1e-10 && t<w.b-1e-10)t=w.b;return t;}
static double processFinish(int s,double t,double duration){
 check(duration>0,"nonpositive operation");t=earliestAvailable(s,t);
 for(auto&w:FAILURES[s]){
  if(t>=w.b)continue;
  if(t<w.a){double gap=w.a-t;if(duration<=gap+1e-10)return t+duration;duration-=gap;t=w.b;}
  else if(t<w.b)t=w.b;
 }
 return t+duration;
}
static double plannedDowntime(int s,double horizon){double z=0;for(auto&w:FAILURES[s])z+=max(0.,min(horizon,w.b)-min(horizon,w.a));return z;}
struct Event{double t;uint64_t seq;int kind,job,station;};
struct EventAfter{bool operator()(const Event&a,const Event&b)const{return tie(a.t,a.seq)>tie(b.t,b.seq);}};
struct Station{deque<int>q;bool busy=false;int blockedJob=-1;double blockedSince=0,blockedTime=0,busyTime=0,energy=0;int processed=0,rejected=0,maxBuffer=0;};
struct Scenario{int variant=0,arrived=0,good=0,scrap=0;double horizon=0,energy=0,blocked=0,meanSojourn=0;array<Station,ST>stations;vector<array<double,ST>>start,finish;vector<int>exit;};
static Scenario simulate(const vector<Operation>&op,int jobs,int variant){
 Scenario sc;sc.variant=variant;sc.start.resize(jobs);sc.finish.resize(jobs);sc.exit.assign(jobs,0);
 for(auto&x:sc.start)x.fill(-1);
 for(auto&x:sc.finish)x.fill(-1);
 priority_queue<Event,vector<Event>,EventAfter>pq;uint64_t seq=0;
 auto event=[&](double t,int kind,int job,int st){pq.push({t,seq++,kind,job,st});};
 for(int j=0;j<jobs;++j)event(j*4.80+0.14*(j%7),0,j,0); // deterministic exogenous arrivals, identical for all variants.
 auto&stations=sc.stations;
 // Recursive machine release and finite buffer unblocking model.
 function<void(int,double)>start;
 function<void(int,double)>release;
 start=[&](int s,double t){Station&st=stations[s];if(st.busy||st.blockedJob>=0||st.q.empty())return;
  double available=earliestAvailable(s,t);if(available>t+1e-10){event(available,2,-1,s);return;}
  int job=st.q.front();st.q.pop_front();
  st.busy=true; // Set busy before the unblock callback may re-enter start(s).
  // Removing a waiting job may unblock the preceding station's completed job.
  if(s>0)release(s-1,t);double duration=op[size_t(job)*ST+s].cycle[variant];check(duration>0.1&&duration<20,"invalid computed station process time");
  st.busyTime+=duration;double finish=processFinish(s,t,duration);sc.start[job][s]=t;sc.finish[job][s]=finish;
  event(finish,1,job,s);
 };
 release=[&](int s,double t){if(s<0||s>=ST-1)return;auto&st=stations[s];if(st.blockedJob<0)return;
  auto&to=stations[s+1];static constexpr array<int,ST> CAP{{99999,3,4,3}};
  if(int(to.q.size())>=CAP[s+1])return;
  int j=st.blockedJob;st.blockedJob=-1;st.blockedTime+=t-st.blockedSince;
  to.q.push_back(j);to.maxBuffer=max(to.maxBuffer,int(to.q.size()));start(s+1,t);start(s,t);
 };
 int events=0;
 while(!pq.empty()){
  Event e=pq.top();pq.pop();check(++events<500000,"event calendar runaway");double t=e.t;
  if(e.kind==0){stations[0].q.push_back(e.job);stations[0].maxBuffer=max(stations[0].maxBuffer,int(stations[0].q.size()));++sc.arrived;start(0,t);}
  else if(e.kind==2)start(e.station,t);
  else {
   int s=e.station,j=e.job;Station&st=stations[s];check(st.busy,"completion for idle station");st.busy=false;++st.processed;
   const Operation&x=op[size_t(j)*ST+s];st.energy+=x.energy;
   if(uniform01(j,s)<x.reject){++st.rejected;++sc.scrap;sc.exit[j]=2;start(s,t);}
   else if(s==ST-1){++sc.good;sc.exit[j]=1;sc.meanSojourn+=t-(j*4.80+0.14*(j%7));start(s,t);}
   else {
    static constexpr array<int,ST> CAP{{99999,3,4,3}};
    auto&to=stations[s+1];
    if(int(to.q.size())<CAP[s+1]){to.q.push_back(j);to.maxBuffer=max(to.maxBuffer,int(to.q.size()));start(s+1,t);start(s,t);}
    else{st.blockedJob=j;st.blockedSince=t;}
   }
  }
  if(e.kind!=2)sc.horizon=max(sc.horizon,t);
 }
 check(sc.arrived==jobs&&sc.good+sc.scrap==jobs,"production conservation: every arrived job must exit");
 for(auto&st:stations){check(!st.busy&&st.blockedJob==-1&&st.q.empty(),"station not drained at end");sc.energy+=st.energy;sc.blocked+=st.blockedTime;}
 sc.meanSojourn/=max(1,sc.good);
 check(sc.horizon>0&&sc.horizon<10000,"invalid event horizon");return sc;
}
static void dumpTrace(const Scenario&sc,int jobs,const fs::path&root){
 ofstream f(root/"examples/selected_event_timeline.csv");f<<"variant,job,station,arrival_min,operation_start_min,operation_finish_min,exit_code\n"<<setprecision(16);
 for(int j=0;j<jobs;++j)for(int s=0;s<ST;++s)if(sc.start[j][s]>=0)f<<sc.variant+1<<','<<j<<','<<s+1<<','<<j*4.80+0.14*(j%7)<<','<<sc.start[j][s]<<','<<sc.finish[j][s]<<','<<sc.exit[j]<<'\n';
}
static void run(const fs::path&root,int jobs,int variants,int surface){
 check(jobs>=10&&jobs<=2000&&variants>=1&&variants<=20&&surface>=5&&surface<=101,"invalid CLI bounds");
 fs::create_directories(root/"examples");fs::create_directories(root/"results");
 Engine sdk;
 {ofstream f(root/"examples/formula_registry.csv");f<<"id,expression,units,interpretation\n";
  for(auto&x:sdk.formulas)f<<x.id<<",\""<<x.expression<<"\","<<x.unit<<",\""<<x.meaning<<"\"\n";}
 {ofstream f(root/"results/math_execution_inventory.csv");f<<"function,execution_owner,API,scope\n";
  for(auto&x:sdk.formulas)f<<x.id<<",paceval,paceval_dGetMultipleComputationsResultsExt,declared_synthetic_mathematical_model\n";
  f<<"discrete_event_calendar,C++ host,priority_queue,source_and_processing_events\n";
  f<<"finite_buffer_blocking,C++ host,discrete_state_transitions,manufacturing_line_logic\n";
  f<<"scheduled_downtime,C++ host,window_aware_clock,deterministic_nonprocessing_intervals\n";
  f<<"random_rejection_draw,C++ host,splitmix64_fixed_seed,compare_to_paceval_reject_probability\n";
  f<<"independent_oracle,C++/Python,reference_math_only,validation_not_paceval_execution\n";
  f<<"live_industrial_twin,NOT_IMPLEMENTED,requires_real_plant_connection,not_claimed\n";}
 vector<Operation>ops(size_t(jobs)*ST);
 ofstream trace(root/"examples/synthetic_line_event_inputs.csv");trace<<"job,station,arrival_min,b,wear,temp,load,phase,deterministic_rejection_draw,source\n"<<setprecision(16);
 for(int j=0;j<jobs;++j)for(int s=0;s<ST;++s){auto&op=ops[size_t(j)*ST+s];op.input=makeInput(j,s);
  trace<<j<<','<<s+1<<','<<j*4.80+0.14*(j%7)<<','<<op.input[0]<<','<<op.input[1]<<','<<op.input[2]<<','<<op.input[3]<<','<<op.input[4]<<','<<uniform01(j,s)<<",synthetic_fixed_trace\n";}
 trace.close();
 ofstream fop(root/"examples/paceval_operation_results.csv");fop<<"job,station,base_min,wear,temp_C,load,phase,reject_probability,energy_kWh";
 for(int v=0;v<NMODELS;++v)fop<<",cycle_v"<<setw(2)<<setfill('0')<<(v+1);
 fop<<"\n"<<setprecision(16);
 constexpr int CHUNK=96;
 for(size_t offset=0;offset<ops.size();offset+=CHUNK){size_t n=min(size_t(CHUNK),ops.size()-offset);vector<Input>in;
  for(size_t k=0;k<n;++k)in.push_back(ops[offset+k].input);
  auto result=sdk.batch(in);
  for(size_t k=0;k<n;++k){Operation&x=ops[offset+k];x.reject=result[20*n+k];x.energy=result[21*n+k];
   check(x.reject>=0&&x.reject<0.1&&x.energy>0,"model validation failed");
   fop<<((offset+k)/ST)<<','<<((offset+k)%ST+1)<<','<<x.input[0]<<','<<x.input[1]<<','<<x.input[2]<<','<<x.input[3]<<','<<x.input[4]<<','<<x.reject<<','<<x.energy;
   for(int v=0;v<20;++v){x.cycle[v]=result[v*n+k];check(x.cycle[v]>0,"nonpositive operation");fop<<','<<x.cycle[v];}
   fop<<'\n';
  }
 }
 fop.close();
 ofstream sum(root/"examples/scenario_summary.csv");sum<<"module,arrivals,completed_good,scrapped,simulated_minutes,paceval_good_throughput_units_hr,paceval_gross_throughput_units_hr,paceval_line_yield,paceval_line_energy_per_good_kWh,paceval_electricity_EUR_proxy,paceval_blocked_fraction,mean_good_flowtime_min,station2_busy_min,station2_processed,station2_passed,station2_max_buffer,paceval_station2_running_fraction,paceval_station2_calendar_uptime,paceval_station2_performance,paceval_station2_quality,paceval_station2_oee_like,paceval_target_margin_units_hr\n"<<setprecision(16);
 vector<Scenario>scenarios;scenarios.reserve(variants);
 // Once the input trace and paceval results are frozen, all variants use the same event ordering semantics.
 for(int v=0;v<variants;++v){auto sc=simulate(ops,jobs,v);scenarios.push_back(sc);
  auto&b=sc.stations[1];double planned=plannedDowntime(1,sc.horizon);
  // Every mathematical KPI, including OEE-style combination, is calculated by the real engine.
  Input z={BASE[1],.5,22.,.7,0.,double(b.q.size()),max(1e-12,b.busyTime),double(sc.stations[3].processed),double(sc.good),sc.horizon,planned,sc.energy,.23,3.6,sc.blocked,double(sc.arrived),BASE[1]};
  auto out=sdk.batch({z});
  Input zs=z; zs[7]=double(b.processed); zs[8]=double(b.processed-b.rejected);
  auto outStation=sdk.batch({zs});
  sum<<v+1<<','<<sc.arrived<<','<<sc.good<<','<<sc.scrap<<','<<sc.horizon<<','<<out[31]<<','<<out[32]<<','<<out[33]<<','<<out[34]<<','<<out[35]<<','<<out[36]<<','<<sc.meanSojourn<<','<<b.busyTime<<','<<b.processed<<','<<b.processed-b.rejected<<','<<b.maxBuffer<<','<<outStation[26]<<','<<outStation[27]<<','<<outStation[28]<<','<<outStation[29]<<','<<outStation[30]<<','<<out[37]<<'\n';
  // independent domain-level invariants on source output
  check(abs(out[33]-double(sc.good)/jobs)<2e-12,"real paceval yield KPI check failed");
  check(abs(out[31]-60.*sc.good/sc.horizon)<2e-11,"real paceval throughput KPI check failed");
  check(abs(out[35]-sc.energy*.23)<2e-10,"real paceval cost KPI check failed");
 }
 sum.close();dumpTrace(scenarios[0],jobs,root);
 {ofstream f(root/"examples/station_performance.csv");f<<"module,station,processed,rejected,active_process_min,blocked_min,planned_down_min,max_waiting_queue\n";
  for(auto&sc:scenarios)for(int s=0;s<ST;++s){auto&st=sc.stations[s];f<<sc.variant+1<<','<<s+1<<','<<st.processed<<','<<st.rejected<<','<<st.busyTime<<','<<st.blockedTime<<','<<plannedDowntime(s,sc.horizon)<<','<<st.maxBuffer<<'\n';}}
 // A real mathematical response surface: identical paceval graph but varied supplied wear/temperature inputs.
 {ofstream f(root/"examples/paceval_cycle_response_surface.csv");f<<"wear,temp_C,module_01_min,module_10_min,module_20_min,reject_probability,energy_kWh\n"<<setprecision(16);
  vector<Input>buffer;
  auto flush=[&](){if(buffer.empty())return;auto out=sdk.batch(buffer);size_t n=buffer.size();for(size_t k=0;k<n;++k){
   auto g=[&](int i){return out[size_t(i)*n+k];};f<<buffer[k][1]<<','<<buffer[k][2]<<','<<g(0)<<','<<g(9)<<','<<g(19)<<','<<g(20)<<','<<g(21)<<'\n';}buffer.clear();};
  for(int i=0;i<surface;++i)for(int j=0;j<surface;++j){Input x=makeInput(24,1);x[1]=double(i)/(surface-1);x[2]=17.+16.*j/(surface-1);buffer.push_back(x);if(buffer.size()==CHUNK)flush();}flush();}
 {ofstream f(root/"results/execution_summary.csv");f<<"key,value\n";
  f<<"original_paceval_graphs,"<<G<<"\n"<<"scenario_modules_executed,"<<variants<<"\n"<<"synthetic_arrivals_per_scenario,"<<jobs<<"\n"<<"workstations,"<<ST<<"\n";
  f<<"real_multi_graph_batch_calls,"<<sdk.calls<<"\n"<<"real_multi_graph_outputs,"<<sdk.outputs<<"\n";
  f<<"independent_C++_formula_checks,"<<sdk.audits<<"\n"<<"max_native_scaled_error,"<<setprecision(17)<<sdk.max_scaled_error<<"\n";
  f<<"observed_good_units_module01,"<<scenarios[0].good<<"\n"<<"observed_scrapped_units_module01,"<<scenarios[0].scrap<<"\n";
  f<<"first_scenario_max_queue_station1,"<<scenarios[0].stations[0].maxBuffer<<"\n";
  f<<"experimental_status,synthetic_discrete_event_execution_not_live_plant\n";}
 cout<<"WP040 original paceval SDK OK: graphs="<<G<<" variants="<<variants<<" jobs="<<jobs<<" batch outputs="<<sdk.outputs<<" audit="<<sdk.audits<<"\n";
}
int main(int argc,char**argv){try{fs::path out=".";int jobs=440,variants=20,surface=61;
 for(int i=1;i<argc;++i){string arg=argv[i];check(i+1<argc,"missing CLI parameter value");string val=argv[++i];
 if(arg=="--out")out=val;else if(arg=="--jobs")jobs=stoi(val);else if(arg=="--variants")variants=stoi(val);else if(arg=="--surface")surface=stoi(val);else throw runtime_error("unknown CLI option: "+arg);}
 run(out,jobs,variants,surface);return 0;
 }catch(const exception&e){cerr<<"ERROR "<<e.what()<<'\n';return 2;}}
