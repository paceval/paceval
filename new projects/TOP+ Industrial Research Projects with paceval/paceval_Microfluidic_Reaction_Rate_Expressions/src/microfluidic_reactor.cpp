// WP_047 | Microfluidic Reaction–Transport Research Demonstrator
// The *actual application path* uses reusable ORIGINAL paceval SDK execution graphs.
// The C++ host schedules the conservative 1-D finite-volume state updates,
// carries old/new state, writes datasets and performs independent checks.
// Physics: dilute A + B <-> C in a cross-section-averaged 1-D flow channel;
// volume-averaged velocity, effective axial dispersion and isothermal kinetics.
// This synthetic research kernel is NOT a CFD solver or a validated reactor design.
#include "paceval_main.h"
#include <array>
#include <algorithm>
#include <cmath>
#include <filesystem>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <limits>
#include <stdexcept>
#include <string>
#include <vector>
using namespace std; namespace fs=std::filesystem;
static void check(bool x,const string&msg){if(!x)throw runtime_error(msg);}
constexpr int NV=23;
enum Var{A,AL,AR,B,BL,BR,C,CL,CR,U,D,DX,DT,KF,KR,K,LC,RC,AIN,BIN,CIN,L,TARGET};
using Row=array<double,NV>;
static const string VARIABLES="A AL AR B BL BR C CL CR u D dx dt kf kr K lc rc Ain Bin Cin L target";
struct Graph{string name,formula,unit,purpose,version;PACEVAL_HANDLE handle=nullptr;};
static string rate(int v){return v==1?"(kf*A*B-kr*C)":"(kf*A*B/(1+K*A)-kr*C)";}
static string forward(int v){return v==1?"(kf*A*B)":"(kf*A*B/(1+K*A))";}
static string transport(const string&z,const string&le,const string&ri){return "((u*("+le+"-"+z+")+D*(rc*("+ri+"-"+z+")-lc*("+z+"-"+le+"))/dx)/dx)";}
static string update(const string&z,const string&le,const string&ri,int sign,int v){return "("+z+"+dt*("+transport(z,le,ri)+(sign>0?"+":"-")+rate(v)+"))";}
static string num(double x){char c[80];snprintf(c,sizeof(c),"%.10g",x);return string(c);}
static vector<Graph> build_graphs(){vector<Graph> g;auto add=[&](string n,string f,string unit,string purpose,string ver){g.push_back({n,f,unit,purpose,ver,nullptr});};
 for(int v=1;v<=2;v++){string s="v"+to_string(v),r=rate(v),fw=forward(v),tA=transport("A","AL","AR"),tB=transport("B","BL","BR"),tC=transport("C","CL","CR");
  add("reaction_rate_"+s,r,"mmol/(L*s)","reversible_net_rate",s);
  add("forward_rate_"+s,fw,"mmol/(L*s)","forward_kinetics",s);
  add("reverse_rate_"+s,"(kr*C)","mmol/(L*s)","reverse_kinetics",s);
  add("transport_A_"+s,tA,"mmol/(L*s)","advection_dispersion_A",s);
  add("transport_B_"+s,tB,"mmol/(L*s)","advection_dispersion_B",s);
  add("transport_C_"+s,tC,"mmol/(L*s)","advection_dispersion_C",s);
  add("A_next_"+s,update("A","AL","AR",-1,v),"mmol/L","full_finite_volume_reaction_transport_step_A",s);
  add("B_next_"+s,update("B","BL","BR",-1,v),"mmol/L","full_finite_volume_reaction_transport_step_B",s);
  add("C_next_"+s,update("C","CL","CR",+1,v),"mmol/L","full_finite_volume_reaction_transport_step_C",s);
  add("d_rate_dA_"+s,v==1?"(kf*B)":"(kf*B/(1+K*A)^2)","1/s","analytical_concentration_sensitivity_A",s);
  add("d_rate_dB_"+s,v==1?"(kf*A)":"(kf*A/(1+K*A))","1/s","analytical_concentration_sensitivity_B",s);
  add("d_rate_dC_"+s,"(-kr)","1/s","analytical_concentration_sensitivity_C",s);
  add("d_rate_dkf_"+s,v==1?"(A*B)":"(A*B/(1+K*A))","(mmol/L)^2","analytical_kinetic_parameter_sensitivity",s);
  add("d_rate_dK_"+s,v==1?"(0*A)":"(-kf*A^2*B/(1+K*A)^2)","(mmol/L)^2/s","analytical_saturation_parameter_sensitivity",s);
  add("mole_sum_A_C_"+s,"(A+C)","mmol/L","reaction_invariant_species_pair_A_C",s);
  add("mole_sum_B_C_"+s,"(B+C)","mmol/L","reaction_invariant_species_pair_B_C",s);
  add("influx_A_C_"+s,"(u*(Ain+Cin)-2*D*((A-Ain)+(C-Cin))/dx)","mmol*mm/(L*s)","boundary_molar_influx_A_plus_C",s);
  add("influx_B_C_"+s,"(u*(Bin+Cin)-2*D*((B-Bin)+(C-Cin))/dx)","mmol*mm/(L*s)","boundary_molar_influx_B_plus_C",s);
  add("outflux_A_C_"+s,"(u*(A+C))","mmol*mm/(L*s)","boundary_molar_outflux_A_plus_C",s);
  add("outflux_B_C_"+s,"(u*(B+C))","mmol*mm/(L*s)","boundary_molar_outflux_B_plus_C",s);
  add("outlet_reacted_fraction_"+s,"(C/(A+C+0.000000000001))","1","local_stoichiometric_reacted_fraction_regularized_near_zero",s);
  add("outlet_product_ratio_"+s,"(C/Ain)","1","transient_outlet_product_concentration_relative_to_inlet_A",s);
  add("outlet_molar_flux_C_"+s,"(u*C)","mmol*mm/(L*s)","product_molar_flux_density",s);
  add("target_product_margin_"+s,"(C-target)","mmol/L","signed_target_margin_not_chemical_safety",s);
  add("reacted_fraction_margin_"+s,"(C/(A+C+0.000000000001)-0.25)","1","signed_hypothetical_stoichiometric_fraction_margin",s);
  add("local_rate_guard_"+s,"(kf*A*B-kr*C)","mmol/(L*s)","signed_forward_minus_reverse_margin",s);
  add("modified_rate_minus_original_"+s,"("+r+"-(kf*A*B-kr*C))","mmol/(L*s)","retained_model_difference",s);
  for(int j=1;j<=12;j++){double w=.015+.014*j, v1=.5+.035*(j%5),v2=.18+.012*(j%4);
   string expr="("+num(v1)+"*(C-target)^2+"+num(w)+"*((u-0.40)/0.40)^2+"+num(v2)+"*(1-A/Ain-C/Ain)^2)";
   add("score_"+s+"_"+(j<10?"0":"")+to_string(j),expr,"weighted_index","industrial_synthetic_multicriterion_score",s);
  }
 }
 add("peclet_channel","(u*L/D)","1","channel_advection_to_dispersion_ratio","shared");
 add("damkohler_nominal","(kf*Bin*L/u)","1","pseudo_first_order_nominal_residence_reaction_ratio","shared");
 add("flow_residence_time","(L/u)","s","nominal_residence_time","shared");
 add("reaction_rate_v2_minus_v1","("+rate(2)+"-"+rate(1)+")","mmol/(L*s)","cross_version_reaction_rate_difference","v2-v1");
 return g;
}
struct Engine{
 vector<Graph> g;size_t batchCalls=0,scalarCalls=0,totalOutputs=0;double maxRelativeNativeError=0;size_t nativeTests=0;
 Engine(){check(paceval_InitializeLibrary(nullptr),"Original paceval library initialization failed");g=build_graphs();for(auto&v:g){v.handle=paceval_CreateComputation(v.formula.c_str(),NV,VARIABLES.c_str(),false,nullptr);if(!v.handle||paceval_GetIsError(v.handle)){char a[512]={},b[512]={};if(v.handle)paceval_CreateErrorInformationText(v.handle,a,b);throw runtime_error("paceval graph creation "+v.name+": "+a+" "+b+" formula="+v.formula);}}}
 ~Engine(){for(auto&v:g)if(v.handle)paceval_DeleteComputation(v.handle);paceval_FreeLibrary();}
 int id(const string&s)const{for(size_t i=0;i<g.size();i++)if(g[i].name==s)return int(i);throw runtime_error("missing graph "+s);}
 void valid(const Row&r)const{for(double x:r)check(isfinite(x),"nonfinite parameter sent to SDK");check(r[U]>=.15&&r[U]<=.7&&r[D]>.0&&r[DX]>0&&r[DT]>0&&r[KF]>0&&r[KR]>0&&r[K]>=0&&r[AIN]>0&&r[BIN]>0&&r[L]>0,"invalid physical domain or transport input");check(r[LC]>=0&&r[LC]<=2&&r[RC]>=0&&r[RC]<=1,"invalid boundary factors");check(r[A]>=-1e-8&&r[B]>=-1e-8&&r[C]>=-1e-8,"negative reactant concentration");}
 vector<double> batch(const vector<Row>&rows,const vector<int>&ids){check(!rows.empty()&&!ids.empty(),"empty batch");vector<double> inp;inp.reserve(rows.size()*NV);for(const auto&r:rows){valid(r);inp.insert(inp.end(),r.begin(),r.end());}
 vector<PACEVAL_HANDLE> h;for(int i:ids)h.push_back(g.at(i).handle);
 vector<double>out(rows.size()*ids.size(),numeric_limits<double>::quiet_NaN());vector<int>errs(out.size(),-9);
 bool fail=paceval_dGetMultipleComputationsResultsExt(h.data(),h.size(),inp.data(),rows.size(),out.data(),nullptr,nullptr,errs.data());
 check(!fail,"paceval batch returned error flag");for(size_t i=0;i<out.size();i++)check(errs[i]==0&&isfinite(out[i]),"paceval batch output error at index "+to_string(i)+" code="+to_string(errs[i]));
 batchCalls++;totalOutputs+=out.size();return out;}
 double scalar(int i,Row r){valid(r);double v=paceval_dGetComputationResult(g[i].handle,r.data(),nullptr,nullptr);check(!paceval_GetIsError(g[i].handle)&&isfinite(v),"paceval scalar error "+g[i].name);scalarCalls++;return v;}
};
struct Case{int id,version;double u,kf,kr,K;vector<double>a,b,c;double integratedInAC=0,integratedOutAC=0,integratedInBC=0,integratedOutBC=0,maxBalAC=0,maxBalBC=0;};
constexpr double LEN=20.,DIFF=.006,AINLET=1.,BINLET=.9,CINLET=0.,TARGETC=.28,DTSTEP=.1;
static vector<Case> cases(int cells){vector<Case>s;int j=0;for(double u:{.25,.40,.55})for(double k:{.018,.032})for(int v:{1,2}){Case x;x.id=++j;x.u=u;x.kf=k;x.kr=.003;x.K=.65;x.version=v;x.a.assign(cells,0.);x.b.assign(cells,0.);x.c.assign(cells,0.);s.push_back(move(x));}return s;}
static Row inputs(const Case&s,int i,int n){double dx=LEN/n;
 double al=i? s.a[i-1]:AINLET,ar=(i+1<n)?s.a[i+1]:s.a[i],bl=i?s.b[i-1]:BINLET,br=(i+1<n)?s.b[i+1]:s.b[i],cl=i?s.c[i-1]:CINLET,cr=(i+1<n)?s.c[i+1]:s.c[i];
 return {s.a[i],al,ar,s.b[i],bl,br,s.c[i],cl,cr,s.u,DIFF,dx,DTSTEP,s.kf,s.kr,s.K,i==0?2.:1.,i==n-1?0.:1.,AINLET,BINLET,CINLET,LEN,TARGETC};
}
static void nativeAudit(Engine&e,const Row&r,int ver,double aa,double bb,double cc){double kf=r[KF],kr=r[KR],a=r[A],b=r[B],c=r[C],ks=r[K],dt=r[DT],dx=r[DX],d=r[D],u=r[U],lc=r[LC],rc=r[RC];double rr=kf*a*b/(ver==1?1.:(1+ks*a))-kr*c;
 auto T=[&](double l,double mid,double right){return (u*(l-mid)+d*(rc*(right-mid)-lc*(mid-l))/dx)/dx;};
 auto eq=[&](double got,double exp){double d=abs(got-exp)/(1+abs(exp));e.maxRelativeNativeError=max(e.maxRelativeNativeError,d);check(d<1e-10,"Native reference mismatch in state update");e.nativeTests++;};
 eq(aa,a+dt*(T(r[AL],a,r[AR])-rr));eq(bb,b+dt*(T(r[BL],b,r[BR])-rr));eq(cc,c+dt*(T(r[CL],c,r[CR])+rr));
}
static void execution(const fs::path&root,int cells,int steps){check(cells>=16&&cells<=256&&steps>=100&&steps<=1800,"unsupported cells/steps");fs::create_directories(root/"results");fs::create_directories(root/"examples");Engine e;auto sc=cases(cells);const int ncases=sc.size(),n=cells;const double dx=LEN/n;
 {ofstream f(root/"results/formula_registry.csv");f<<"graph_id,formula_version,role,unit,paceval_expression\n";for(auto &g:e.g)f<<g.name<<","<<g.version<<","<<g.purpose<<","<<g.unit<<",\""<<g.formula<<"\"\n";}
 {ofstream f(root/"results/math_execution_inventory.csv");f<<"function_id,domain_quantity,mathematical_definition,units,execution_owner,paceval_graph_id,formula_version,api_path,reference_test,status,host_reason\n";for(auto &g:e.g)f<<g.name<<","<<g.purpose<<",\""<<g.formula<<"\","<<g.unit<<",paceval,"<<g.name<<","<<g.version<<",paceval_dGetMultipleComputationsResultsExt,independent_cpp_and_python,executed_verified,\n";
 f<<"spatial_integral,domain_integrated_mass,dx_times_sum_of_state_cells,mmol_mm_per_L,host,,both,C++_stateful,independent_Python,executed,stateful_spatial_reduction\n";
 f<<"time_integral,boundary_cumulative_flux,dt_times_sum_of_paceval_boundary_flux,mmol_mm_per_L,host,,both,C++_stateful,independent_Python,executed,chronological_integration\n";
 f<<"scenario_selection,rank_and_selection,compare_paceval_score_values,dimensionless,host,,both,C++_host,deterministic_rules,executed,discrete_selection\n";
 f<<"native_check,numerical_oracle,independent_physical_equations,mixed,reference_only,,both,C++_native_and_Python,independent_numerical_audit,executed,independence_required\n";}
 {ofstream f(root/"examples/synthetic_operating_scenarios.csv");f<<"scenario_id,model_version,velocity_mm_per_s,forward_k_L_per_mmol_s,reverse_k_per_s,saturation_K_L_per_mmol,channel_length_mm,axial_effective_D_mm2_per_s,initial_A_mmol_per_L,initial_B_mmol_per_L,initial_C_mmol_per_L,inlet_A_mmol_per_L,inlet_B_mmol_per_L,inlet_C_mmol_per_L\n";for(const auto&s:sc)f<<s.id<<","<<s.version<<","<<s.u<<","<<s.kf<<","<<s.kr<<","<<s.K<<","<<LEN<<","<<DIFF<<",0,0,0,"<<AINLET<<","<<BINLET<<","<<CINLET<<"\n";}
 ofstream snap(root/"results/concentration_profiles.csv");snap<<setprecision(17)<<"scenario_id,model_version,velocity_mm_per_s,time_s,x_mm,A_mmol_per_L,B_mmol_per_L,C_mmol_per_L\n";
 ofstream mass(root/"results/mass_balance.csv");mass<<setprecision(17)<<"scenario_id,model_version,time_s,domain_mass_AplusC,integrated_net_boundary_AplusC,balance_residual_AplusC,domain_mass_BplusC,integrated_net_boundary_BplusC,balance_residual_BplusC\n";
 ofstream probes(root/"results/graph_probe.csv");probes<<setprecision(17)<<"graph_id,graph_version,scenario_id,step_index,cell_index,A,AL,AR,B,BL,BR,C,CL,CR,u,D,dx,dt,kf,kr,K,lc,rc,Ain,Bin,Cin,L,target,paceval_result\n";
 vector<int> updateIds;for(int v=1;v<=2;v++)for(string nam:{"A_next","B_next","C_next"})updateIds.push_back(e.id(nam+"_v"+to_string(v)));
 vector<int> fluxIds;for(string nam:{"influx_A_C","influx_B_C","outflux_A_C","outflux_B_C"})fluxIds.push_back(e.id(nam+"_v1"));
 vector<int> allIds;for(size_t i=0;i<e.g.size();i++)allIds.push_back((int)i);
 // Check single vs multi-graph layout on genuinely independent vectors.
 {vector<Row> test{inputs(sc[0],0,n),inputs(sc[3],n/2,n),inputs(sc[7],n-1,n)};auto out=e.batch(test,updateIds);for(size_t k=0;k<updateIds.size();k++)for(size_t i=0;i<test.size();i++){double s=e.scalar(updateIds[k],test[i]);check(abs(s-out[k*test.size()+i])<1e-13,"SDK scalar vs batch layout mismatch");}}
 size_t sampledProbes=0;int probeTimes=0;
 for(int t=0;t<steps;t++){
  vector<Row> rows;rows.reserve(ncases*n);vector<Row> boundaries;boundaries.reserve(ncases*2);
  for(const auto&s:sc){boundaries.push_back(inputs(s,0,n));boundaries.push_back(inputs(s,n-1,n));for(int i=0;i<n;i++)rows.push_back(inputs(s,i,n));}
  // Both 2026-v1 and 2026-v2 models remain independently registered and callable.
  // Execution uses all six full update graphs, selecting each case's actual version.
  auto upd=e.batch(rows,updateIds);auto flux=e.batch(boundaries,fluxIds);
  for(int ci=0;ci<ncases;ci++){
   auto&s=sc[ci];int v=s.version-1;
   double inAC=flux[0*boundaries.size()+2*ci],inBC=flux[1*boundaries.size()+2*ci];
   double outAC=flux[2*boundaries.size()+2*ci+1],outBC=flux[3*boundaries.size()+2*ci+1];
   s.integratedInAC+=DTSTEP*inAC;s.integratedOutAC+=DTSTEP*outAC;
   s.integratedInBC+=DTSTEP*inBC;s.integratedOutBC+=DTSTEP*outBC;
   for(int i=0;i<n;i++){size_t j=ci*n+i;double a=upd[(v*3)*rows.size()+j],b=upd[(v*3+1)*rows.size()+j],c=upd[(v*3+2)*rows.size()+j];
    if(t%41==0&&i%13==0&&ci%3==0)nativeAudit(e,rows[j],s.version,a,b,c);
    check(a>=-1e-10&&b>=-1e-10&&c>=-1e-10,"Non-physical negative species concentration");s.a[i]=a;s.b[i]=b;s.c[i]=c;
   }
   double integralAC=0,integralBC=0;for(int i=0;i<n;i++){integralAC+=(s.a[i]+s.c[i])*dx;integralBC+=(s.b[i]+s.c[i])*dx;}
   double resAC=integralAC-(s.integratedInAC-s.integratedOutAC),resBC=integralBC-(s.integratedInBC-s.integratedOutBC);
   s.maxBalAC=max(s.maxBalAC,abs(resAC));s.maxBalBC=max(s.maxBalBC,abs(resBC));
   check(abs(resAC)<2e-8&&abs(resBC)<2e-8,"Conservative finite-volume mass closure failed");
   if(t==0||(t+1)%30==0||t==steps-1){mass<<s.id<<","<<s.version<<","<<(t+1)*DTSTEP<<","<<integralAC<<","<<(s.integratedInAC-s.integratedOutAC)<<","<<resAC<<","<<integralBC<<","<<(s.integratedInBC-s.integratedOutBC)<<","<<resBC<<"\n";}
   if(t==0||(t+1)%60==0||t==steps-1){for(int i=0;i<n;i++){snap<<s.id<<","<<s.version<<","<<s.u<<","<<(t+1)*DTSTEP<<","<<(i+.5)*dx<<","<<s.a[i]<<","<<s.b[i]<<","<<s.c[i]<<"\n";}}
  }
  // Full math inventory is ACTUALLY executed on scientifically relevant state samples.
  if(t==0 || (t+1)%max(1,steps/8)==0 || t==steps-1){probeTimes++;
   vector<Row> probeInputs;struct ProbeMeta{int ci,cell;};vector<ProbeMeta> meta;
   for(int ci=0;ci<ncases;ci++)for(int i:{0,n/4,n/2,n-1}){probeInputs.push_back(inputs(sc[ci],i,n));meta.push_back({ci,i});}
   auto all=e.batch(probeInputs,allIds);for(size_t g=0;g<allIds.size();g++)for(size_t j=0;j<probeInputs.size();j++){
    const auto&rr=probeInputs[j];const auto&gr=e.g[allIds[g]];probes<<gr.name<<","<<gr.version<<","<<sc[meta[j].ci].id<<","<<t+1<<","<<meta[j].cell;
    for(double x:rr)probes<<","<<x;probes<<","<<all[g*probeInputs.size()+j]<<"\n";sampledProbes++;
   }
  }
 }
 probes.close();snap.close();mass.close();
 ofstream summ(root/"results/scenario_summary.csv");summ<<setprecision(17)<<"scenario_id,model_version,u_mm_per_s,kf_L_per_mmol_s,kr_per_s,K_L_per_mmol,Pe,Da_nominal,residence_s,end_time_s,A_out_mmol_per_L,B_out_mmol_per_L,C_out_mmol_per_L,outlet_stoichiometric_reacted_fraction,outlet_C_to_A_inlet_ratio,product_outlet_flux,score01,outlet_target_margin,max_mass_balance_AC,max_mass_balance_BC\n";
 ofstream scores(root/"results/score_variants.csv");scores<<setprecision(17)<<"scenario_id,model_version,graph_id,score_value\n";
 for(auto&s:sc){Row row=inputs(s,n-1,n);string vs="_v"+to_string(s.version);double pe=e.scalar(e.id("peclet_channel"),row),da=e.scalar(e.id("damkohler_nominal"),row),res=e.scalar(e.id("flow_residence_time"),row),conv=e.scalar(e.id("outlet_reacted_fraction"+vs),row),yield=e.scalar(e.id("outlet_product_ratio"+vs),row),outflow=e.scalar(e.id("outlet_molar_flux_C"+vs),row),mar=e.scalar(e.id("target_product_margin"+vs),row);
 double score=e.scalar(e.id("score"+vs+"_01"),row);
 summ<<s.id<<","<<s.version<<","<<s.u<<","<<s.kf<<","<<s.kr<<","<<s.K<<","<<pe<<","<<da<<","<<res<<","<<steps*DTSTEP<<","<<s.a.back()<<","<<s.b.back()<<","<<s.c.back()<<","<<conv<<","<<yield<<","<<outflow<<","<<score<<","<<mar<<","<<s.maxBalAC<<","<<s.maxBalBC<<"\n";
 for(int j=1;j<=12;j++){string id="score"+vs+"_"+(j<10?"0":"")+to_string(j);scores<<s.id<<","<<s.version<<","<<id<<","<<e.scalar(e.id(id),row)<<"\n";}}
 summ.close();scores.close();
 ofstream f(root/"results/sdk_execution.txt");f<<setprecision(17)<<"ORIGINAL paceval SDK executed: SUCCESS\n"<<"registered_executed_graphs="<<e.g.size()<<"\n"<<"graph_outputs="<<e.totalOutputs<<"\n"<<"multi_graph_batch_calls="<<e.batchCalls<<"\n"<<"scalar_calls="<<e.scalarCalls<<"\n"<<"native_state_oracle_comparisons="<<e.nativeTests<<"\n"<<"max_native_relative_scaled_error="<<e.maxRelativeNativeError<<"\n"<<"scenarios="<<sc.size()<<"\n"<<"cells="<<n<<"\n"<<"steps="<<steps<<"\n"<<"dt_seconds="<<DTSTEP<<"\n"<<"full_inventory_probe_rows="<<sampledProbes<<"\n"<<"full_inventory_probe_time_steps="<<probeTimes<<"\n"<<"runtime_linked_externally_not_distributed=true\n";
 cout<<"WP047 ORIGINAL PACEVAL PASSED: graphs="<<e.g.size()<<" outputs="<<e.totalOutputs<<" batches="<<e.batchCalls<<" native_checks="<<e.nativeTests<<" scenarios="<<sc.size()<<"\n";
}
int main(int argc,char**argv){try{int cells=64,steps=1440;fs::path out=".";for(int i=1;i<argc;i++){string x=argv[i];auto next=[&](){check(i+1<argc,"option value missing");return string(argv[++i]);};if(x=="--out")out=next();else if(x=="--cells")cells=stoi(next());else if(x=="--steps")steps=stoi(next());else throw runtime_error("Unknown argument: "+x);}execution(out,cells,steps);return 0;}catch(const exception&e){cerr<<"WP047 error: "<<e.what()<<"\n";return 2;}}
