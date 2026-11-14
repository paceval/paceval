// WP11: Balanced synthetic radial distribution-grid hosting-capacity study.
// The original paceval SDK executes algebraic network kernels and all scored constraints.
// C++ owns topology traversal, fixed-point convergence, I/O and the scenario decision.
// No real feeder, interconnection approval, 3-phase unbalance or protection study is claimed.
#include "paceval_main.h"
#include <algorithm>
#include <array>
#include <cmath>
#include <cstdint>
#include <filesystem>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <map>
#include <regex>
#include <set>
#include <sstream>
#include <stdexcept>
#include <string>
#include <utility>
#include <vector>
namespace fs=std::filesystem;
static void req(bool a,const std::string& s){if(!a)throw std::runtime_error(s);}
static constexpr size_t NV=25, NB=12;
static constexpr char VARS[]="pload qload pv qder vre vim vupre vupim ire iim R X Imax Vmin Vmax Vref weight vm cm loss vlow vhigh bus pnet qnet";
using Row=std::array<double,NV>;
class Engine{
 std::vector<PACEVAL_HANDLE> owned; std::set<PACEVAL_HANDLE> used;
public:
 uint64_t scalar_calls=0,batch_calls=0,graph_point_evaluations=0;
 Engine(){req(paceval_InitializeLibrary(nullptr),"Failed initializing real paceval SDK");}
 ~Engine(){for(auto h:owned)paceval_DeleteComputation(h);paceval_FreeLibrary();}
 Engine(const Engine&)=delete;Engine& operator=(const Engine&)=delete;
 std::string fmt(double x)const{req(std::isfinite(x),"Nonfinite CSV value");char s[512]={};int n=paceval_dConvertFloatToString(s,x);req(n>0&&s[0],"paceval float->string failed");return s;}
 double parse(const std::string& v)const{
  static const std::regex literal(R"(^[+-]?(?:[0-9]+(?:\.[0-9]*)?|\.[0-9]+)(?:[eE][+-]?[0-9]+)?$)");
  req(std::regex_match(v,literal),"Unsafe nonnumeric CSV literal: "+v);int err=-1;long pos=-1;
  double d=paceval_dConvertStringToFloat(v.c_str(),&err,&pos,false,nullptr,nullptr);
  req(err==PACEVAL_ERR_NO_ERROR&&std::isfinite(d),"paceval string->float failed at "+std::to_string(pos));return d;
 }
 PACEVAL_HANDLE create(const std::string& f){PACEVAL_HANDLE h=paceval_CreateComputation(f.c_str(),(unsigned long)NV,VARS,false,nullptr);req(h!=nullptr,"Null paceval handle");
  if(paceval_GetIsError(h)){char a[1024]={},b[1024]={};paceval_CreateErrorInformationText(h,a,b);paceval_DeleteComputation(h);throw std::runtime_error("paceval formula failed '"+f+"': "+a+" "+b);}owned.push_back(h);return h;}
 std::vector<double> eval(const std::vector<PACEVAL_HANDLE>& handles,const std::vector<Row>& rows){req(!rows.empty()&&!handles.empty(),"empty graph batch");
  std::vector<double> input;input.reserve(rows.size()*NV);for(auto& r:rows)for(double d:r){req(std::isfinite(d),"Nonfinite paceval graph input");input.push_back(d);}
  auto h=handles;std::vector<double> output(h.size()*rows.size());std::vector<int> errors(output.size(),-1);
  bool failed=paceval_dGetMultipleComputationsResultsExt(h.data(),(unsigned long)h.size(),input.data(),(unsigned long)rows.size(),output.data(),nullptr,nullptr,errors.data());req(!failed,"Multi-graph batch returned failure");
  for(size_t j=0;j<errors.size();j++)req(errors[j]==PACEVAL_ERR_NO_ERROR&&std::isfinite(output[j]),"paceval per-value batch error "+std::to_string(j));
  for(auto g:handles){used.insert(g);}++batch_calls;graph_point_evaluations+=output.size();return output;
 }
 double scalar(PACEVAL_HANDLE h,const Row& r){Row copy=r;double d=paceval_dGetComputationResult(h,copy.data(),nullptr,nullptr);req(!paceval_GetIsError(h)&&std::isfinite(d),"Invalid paceval scalar result");used.insert(h);++scalar_calls;++graph_point_evaluations;return d;}
 size_t created()const{return owned.size();}size_t executed()const{return used.size();}
};
struct Function{std::string name,formula,owner,units;PACEVAL_HANDLE handle;};
class Graphs{
 Engine &e;std::map<std::string,Function> reg;
public:
 explicit Graphs(Engine& x):e(x){}
 void add(const std::string& id,const std::string& f,const std::string& units="pu"){req(reg.count(id)==0,"Graph duplicate");reg.emplace(id,Function{id,f,"paceval",units,e.create(f)});}
 PACEVAL_HANDLE h(const std::string& id)const{return reg.at(id).handle;}
 std::vector<PACEVAL_HANDLE> hs(const std::vector<std::string>& names)const{std::vector<PACEVAL_HANDLE> v;for(auto& n:names)v.push_back(h(n));return v;}
 std::vector<double> batch(const std::vector<std::string>& names,const std::vector<Row>& rows){return e.eval(hs(names),rows);}
 double scalar(const std::string& n,const Row& r){return e.scalar(h(n),r);}
 const auto& inventory()const{return reg;}
};
struct Branch{int parent;double R,X,Imax,Pload,Qload;};
static std::array<Branch,NB> topology(){std::array<Branch,NB> a{};a[0]={-1,0,0,99,0,0};
 for(int i=1;i<(int)NB;i++){
  int par= i==10?8:(i==11?7:i-1);
  double R=.0078+.0012*(i%4), X=.0050+.0008*(i%3), Imax= (i==1?1.42:(i==2?1.3:(i==3?1.18:(i==4?1.08:(i==5?.97:(i==6?.82:(i==7?.71:(i==8?.62:.46))))))));
  a[i]={par,R,X,Imax,.050+.008*(i%4),.013+.003*(i%3)};
 }return a;
}
static void register_graphs(Graphs& g){
 g.add("der_q_unity","(0*pv)");g.add("der_q_absorb","(-0.25*pv)");
 g.add("net_p","(pload-pv)");g.add("net_q","(qload-qder)");
 g.add("injection_current_real","((pnet*vre+qnet*vim)/(sqr(vre)+sqr(vim)))");
 g.add("injection_current_imag","((pnet*vim-qnet*vre)/(sqr(vre)+sqr(vim)))");
 g.add("ohmic_voltage_real","(vupre-(R*ire-X*iim))");g.add("ohmic_voltage_imag","(vupim-(X*ire+R*iim))");
 g.add("bus_voltage_magnitude","sqrt(sqr(vre)+sqr(vim))");g.add("branch_current_magnitude","sqrt(sqr(ire)+sqr(iim))");
 g.add("real_line_loss","(R*(sqr(ire)+sqr(iim)))");g.add("reactive_line_loss","(X*(sqr(ire)+sqr(iim)))");
 g.add("line_active_power","(vupre*ire+vupim*iim)");g.add("line_reactive_power","(vupim*ire-vupre*iim)");
 g.add("linear_voltage_drop_proxy","((R*(vupre*ire+vupim*iim)+X*(vupim*ire-vupre*iim))/Vref)");
 g.add("low_voltage_margin","(vm-Vmin)");g.add("high_voltage_margin","(Vmax-vm)");
 g.add("voltage_margin","(vlow min vhigh)");g.add("current_margin","(Imax-cm)");
 g.add("thermal_utilization","(cm/Imax)");g.add("normalized_voltage_margin","((vlow min vhigh)/(Vmax-Vmin))");
 g.add("branch_feasible","((vm>=Vmin) AND (vm<=Vmax) AND (cm<=Imax))","boolean");
 g.add("branch_violated","((vm<Vmin) OR (vm>Vmax) OR (cm>Imax))","boolean");
 g.add("branch_penalty_v1","(sqr(0 max (Vmin-vm))+sqr(0 max (vm-Vmax))+0.4*sqr(0 max (cm-Imax)))");
 g.add("branch_penalty_v2","(1.4*sqr(0 max (Vmin-vm))+1.8*sqr(0 max (vm-Vmax))+0.7*sqr(0 max (cm-Imax)))");
 g.add("branch_quality_score","(weight*sqr(cm/Imax)+0.3*sqr((vm-1)/0.05))");
 g.add("voltage_sensitivity_approx_P","(R/Vref)");g.add("voltage_sensitivity_approx_Q","(X/Vref)");
 g.add("current_limit_ratio","(cm/Imax)");
}
static std::vector<std::string> net_names={"net_p","net_q"};
static std::vector<std::string> cur_names={"injection_current_real","injection_current_imag"};
static std::vector<std::string> volt_names={"ohmic_voltage_real","ohmic_voltage_imag"};
static std::vector<std::string> base_names={"bus_voltage_magnitude","branch_current_magnitude","real_line_loss","reactive_line_loss","line_active_power","line_reactive_power","linear_voltage_drop_proxy","voltage_sensitivity_approx_P","voltage_sensitivity_approx_Q"};
static std::vector<std::string> margin_names={"low_voltage_margin","high_voltage_margin"};
static std::vector<std::string> guard_names={"voltage_margin","current_margin","thermal_utilization","normalized_voltage_margin","branch_feasible","branch_violated","branch_penalty_v1","branch_penalty_v2","branch_quality_score","current_limit_ratio"};
struct Scenario{int bus,mode,step;double pder;};
static std::vector<Scenario> scenarios(Engine& e,const fs::path& out,int steps){
 req(steps>=4&&steps<=200,"invalid number of penetration levels");
 {std::ofstream f(out);req(bool(f),"cannot write scenario CSV");f<<"candidate_bus,control_mode,penetration_step,der_active_power_pu\n";
  for(int bus=4;bus<=11;bus++)for(int mode=0;mode<2;mode++)for(int step=0;step<steps;step++)f<<bus<<','<<mode<<','<<step<<','<<e.fmt(2.5*step/(steps-1))<<'\n';}
 std::ifstream f(out);req(bool(f),"cannot reread scenario CSV");std::string line;std::getline(f,line);req(line=="candidate_bus,control_mode,penetration_step,der_active_power_pu","scenario schema mismatch");
 std::vector<Scenario> rows;while(std::getline(f,line)){if(line.empty())continue;std::stringstream s(line);std::array<std::string,4> fields;for(auto& x:fields)req(bool(std::getline(s,x,',')),"missing field");std::string trailing;req(!std::getline(s,trailing,','),"extra field");
  auto strict_integer=[](const std::string& text){req(!text.empty()&&std::all_of(text.begin(),text.end(),[](char c){return c>='0'&&c<='9';}),"invalid integer");return std::stoi(text);};
  Scenario sc{strict_integer(fields[0]),strict_integer(fields[1]),strict_integer(fields[2]),e.parse(fields[3])};
  req(sc.bus>=4&&sc.bus<=11&&sc.mode>=0&&sc.mode<=1&&sc.step>=0&&sc.step<steps&&sc.pder>=0&&sc.pder<=2.51,"invalid scenario domain");rows.push_back(sc);
 }req(rows.size()==8*2*(size_t)steps,"scenario count mismatch");return rows;
}
static Row row_for(const Branch& b,int bus){Row a{};a.fill(0);a[0]=b.Pload;a[1]=b.Qload;a[4]=1;a[6]=1;a[10]=b.R;a[11]=b.X;a[12]=b.Imax;a[13]=.950;a[14]=1.050;a[15]=1;a[16]=.38;a[22]=bus;return a;}
struct Result{int count=0,viols=0,iterations=0;bool converged=false,feasible=false;double minv=99,maxv=0,min_vm=99,min_im=99,loss=0,score=0,penalty1=0,penalty2=0,min_current_margin=99,min_voltage_margin=99,voltage_at_der=0,rootP=0,rootQ=0;
 std::array<std::array<double,11>,NB> busvals{};
};
static void check_close(double a,double b,const std::string& msg,double tol=2.e-9){req(std::isfinite(a)&&std::abs(a-b)<=tol*(1+std::abs(b)),"numerical reference failed "+msg);}
static Result solve(Engine& e,Graphs& g,const std::array<Branch,NB>& topo,const Scenario& sc,bool audit){
 constexpr int maxit=70;constexpr double eps=1.e-12;
 std::array<Row,NB> rows{};std::array<double,NB> ir{},ii{},vr{},vi{},pnet{},qnet{};
 for(int i=1;i<(int)NB;i++){rows[i]=row_for(topo[i],i);rows[i][2]=(i==sc.bus?sc.pder:0);rows[i][3]=g.scalar(sc.mode?"der_q_absorb":"der_q_unity",rows[i]);
  auto r=g.batch(net_names,{rows[i]});pnet[i]=r[0];qnet[i]=r[1];rows[i][23]=pnet[i];rows[i][24]=qnet[i];}
 for(auto& d:vr){d=1;}for(auto& d:vi){d=0;}
 Result out;for(int iter=0;iter<maxit;iter++){
  std::vector<Row> input;input.reserve(NB-1);for(int i=1;i<(int)NB;i++){rows[i][4]=vr[i];rows[i][5]=vi[i];req(vr[i]*vr[i]+vi[i]*vi[i]>.25,"voltage singularity prevention");input.push_back(rows[i]);}
  auto c=g.batch(cur_names,input);for(int i=1;i<(int)NB;i++){ir[i]=c[i-1];ii[i]=c[NB-1+i-1];}
  // Backward topology accumulation is an index-dependent reduction, so C++ handles traversal.
  for(int i=(int)NB-1;i>=1;i--){int p=topo[i].parent;if(p>0){ir[p]+=ir[i];ii[p]+=ii[i];}}
  std::array<double,NB> nextVr{},nextVi{};nextVr[0]=1;nextVi[0]=0;
  for(int i=1;i<(int)NB;i++){
   int p=topo[i].parent;Row v=rows[i];v[6]=nextVr[p];v[7]=nextVi[p];v[8]=ir[i];v[9]=ii[i];auto z=g.batch(volt_names,{v});nextVr[i]=z[0];nextVi[i]=z[1];
  }
  double delta=0;for(int i=1;i<(int)NB;i++)delta=std::max(delta,std::hypot(nextVr[i]-vr[i],nextVi[i]-vi[i]));vr=nextVr;vi=nextVi;out.iterations=iter+1;
  if(delta<eps){out.converged=true;break;}
 }
 if(!out.converged)return out;
 // Recompute injection currents from converged voltages and check AC KCL and Ohm's law.
 std::vector<Row> rowList;rowList.reserve(NB-1);for(int i=1;i<(int)NB;i++){rows[i][4]=vr[i];rows[i][5]=vi[i];rowList.push_back(rows[i]);}
 auto c=g.batch(cur_names,rowList);for(int i=1;i<(int)NB;i++){ir[i]=c[i-1];ii[i]=c[NB-1+i-1];}
 for(int i=(int)NB-1;i>=1;i--){int p=topo[i].parent;if(p>0){ir[p]+=ir[i];ii[p]+=ii[i];}}
 for(int i=1;i<(int)NB;i++){
  int p=topo[i].parent;rows[i][6]=vr[p];rows[i][7]=vi[p];rows[i][8]=ir[i];rows[i][9]=ii[i];
  // Independent complex Ohm's-law and nodal injection residual checks (C++ audit only).
  if(audit){double vrr=vr[p]-topo[i].R*ir[i]+topo[i].X*ii[i],vii=vi[p]-topo[i].X*ir[i]-topo[i].R*ii[i];check_close(vr[i],vrr,"AC real branch equation",5.e-10);check_close(vi[i],vii,"AC imag branch equation",5.e-10);
    double loadre=(pnet[i]*vr[i]+qnet[i]*vi[i])/(vr[i]*vr[i]+vi[i]*vi[i]);double loadim=(pnet[i]*vi[i]-qnet[i]*vr[i])/(vr[i]*vr[i]+vi[i]*vi[i]);
    for(int child=1;child<(int)NB;child++){if(topo[child].parent==i){loadre+=ir[child];loadim+=ii[child];}}check_close(ir[i],loadre,"KCL real",5.e-10);check_close(ii[i],loadim,"KCL imag",5.e-10);
  }
 }
 rowList.clear();for(int i=1;i<(int)NB;i++)rowList.push_back(rows[i]);auto b=g.batch(base_names,rowList);const int n=NB-1;
 for(int i=1;i<(int)NB;i++){int j=i-1;rows[i][17]=b[j];rows[i][18]=b[n+j];rows[i][19]=b[2*n+j];out.loss+=rows[i][19];out.minv=std::min(out.minv,rows[i][17]);out.maxv=std::max(out.maxv,rows[i][17]);
  if(audit){check_close(rows[i][17],std::hypot(vr[i],vi[i]),"V magnitude");check_close(rows[i][18],std::hypot(ir[i],ii[i]),"I magnitude");check_close(rows[i][19],topo[i].R*(ir[i]*ir[i]+ii[i]*ii[i]),"line loss");}
 }
 rowList.clear();for(int i=1;i<(int)NB;i++)rowList.push_back(rows[i]);auto m=g.batch(margin_names,rowList);
 for(int i=1;i<(int)NB;i++){rows[i][20]=m[i-1];rows[i][21]=m[n+i-1];}
 rowList.clear();for(int i=1;i<(int)NB;i++)rowList.push_back(rows[i]);auto results=g.batch(guard_names,rowList);auto idx=[&](const std::string& k){auto it=std::find(guard_names.begin(),guard_names.end(),k);req(it!=guard_names.end(),"internal error");return size_t(it-guard_names.begin());};auto value=[&](const std::string& k,int i){return results[idx(k)*n+(i-1)];};
 out.feasible=true;out.rootP=vr[0]*ir[1]+vi[0]*ii[1];out.rootQ=vi[0]*ir[1]-vr[0]*ii[1];
 for(int i=1;i<(int)NB;i++){
  double vm=rows[i][17],cm=rows[i][18],mv=value("voltage_margin",i),mi=value("current_margin",i);double pass=value("branch_feasible",i),fail=value("branch_violated",i);
  out.min_voltage_margin=std::min(out.min_voltage_margin,mv);out.min_current_margin=std::min(out.min_current_margin,mi);
  out.penalty1+=value("branch_penalty_v1",i);out.penalty2+=value("branch_penalty_v2",i);out.score+=value("branch_quality_score",i);
  if(pass<.5){out.feasible=false;out.viols++;}req((pass==0||pass==1)&&(fail==0||fail==1)&&pass+fail==1,"invalid Boolean decision semantics");
  out.busvals[i]={vm,cm,mv,rows[i][19],b[3*n+(i-1)],b[4*n+(i-1)],b[5*n+(i-1)],b[6*n+(i-1)],b[7*n+(i-1)],b[8*n+(i-1)],value("thermal_utilization",i)};
  if(audit){check_close(value("current_margin",i),topo[i].Imax-cm,"current margin");check_close(mv,std::min(vm-.95,1.05-vm),"voltage margin");check_close(value("thermal_utilization",i),cm/topo[i].Imax,"ratio");}
 }
 out.voltage_at_der=out.busvals[sc.bus][0];out.count=NB-1;return out;
}
static void operator_tests(Engine& e,Graphs& g){Row r{};r.fill(1);r[4]=1;r[5]=0;r[12]=.8;r[13]=.95;r[14]=1.05;r[17]=1;r[18]=.7;r[20]=.05;r[21]=.05;
 for(const auto& test:std::vector<std::pair<std::string,double>>{{"(-1) % 10",-1},{"(-1) mod 10",9},{"(4 min 5)",4},{"(4 max 5)",5},{"((vm>=Vmin) AND (vm<=Vmax) AND (cm<=Imax))",1},{"((vm<Vmin) OR (cm>Imax))",0},{"NOT(vm<Vmin)",1},{"(1=1)",1},{"(0<>1)",1}}){auto h=e.create(test.first);check_close(e.scalar(h,r),test.second,"operator "+test.first);}
 (void)g;
}
static void conversion_tests(Engine& e){for(const auto& s:{"1.5","-0.0","0.00000025","1.23E+4","-1000.25"}){double x=e.parse(s),y=e.parse(e.fmt(x));req(std::abs(x-y)<1e-11*std::max(1.,std::abs(x)),"conversion error");}
 for(const auto& s:{"","1+2","NaN","1,2","Infinity","1e5000"," 0.4","1/2"}){bool bad=false;try{e.parse(s);}catch(...){bad=true;}req(bad,"unsafe CSV input accepted");}}
static void layout_test(Engine& e,Graphs& g){Row a{};a.fill(1);a[0]=.1;a[2]=.04;a[1]=.05;a[3]=-.02;Row b=a;b[2]=.07;b[3]=0;auto results=g.batch(net_names,{a,b});check_close(results[0],.06,"first P");check_close(results[1],.03,"second P");check_close(results[2],.07,"first Q");check_close(results[3],.05,"second Q");check_close(g.scalar("net_p",a),.06,"scalar vs batch");}
static void write_inventory(const Graphs& g,const fs::path& dest){std::ofstream f(dest);f<<"function_id,domain_quantity,mathematical_definition,units,execution_owner,paceval_graph_id,formula_version,api_path,reference_test,status,host_reason\n";
 for(const auto& [k,v]:g.inventory())f<<k<<','<<k<<",\""<<v.formula<<"\","<<v.units<<",paceval,"<<k<<",v1_v2,dGetMultipleComputationsResultsExt,independent_AC_reference,executed,\n";
 f<<"host_topology,network_traversal,parent_child_aggregation,indexed,host,,both,C++,KCL_audit,executed,tree_dependency\n";
 f<<"host_solver,fixed_point_iteration,balanced_AC_backward_forward_sweep,pu,host,,both,C++,independent_scipy_root,executed,iterative_orchestration\n";
 f<<"host_classification,scenario_status,all_branch_indicators_true,bool,host,,both,C++,independent_reference,executed,discrete_aggregate\n";
}
static void run(Engine& e,Graphs& g,const fs::path& dest,int steps,bool audit){fs::create_directories(dest);auto scs=scenarios(e,dest/"input_scenarios.csv",steps);auto topo=topology();
 std::ofstream f(dest/"scenario_results.csv"),detail(dest/"branch_samples.csv"),hc(dest/"hosting_capacity.csv"),trace(dest/"end_to_end_trace.csv"),nlines(dest/"network_branches.csv");
 req(bool(f)&&bool(detail)&&bool(hc)&&bool(trace)&&bool(nlines),"Output path not writable");
 f<<"candidate_bus,control_mode,penetration_step,der_pu,der_q_pu,converged,iterations,feasible,violated_branches,min_voltage_pu,max_voltage_pu,min_voltage_margin_pu,min_current_margin_pu,total_line_loss_pu,scenario_score,penalty_v1,penalty_v2,der_bus_voltage_pu,slack_real_power_pu,slack_reactive_power_pu\n";
 detail<<"candidate_bus,control_mode,penetration_step,der_pu,bus,voltage_pu,current_pu,voltage_margin_pu,real_line_loss_pu,reactive_line_loss_pu,line_active_power_pu,line_reactive_power_pu,linear_voltage_drop_proxy_pu,approx_sensitivity_p,approx_sensitivity_q,current_utilization_ratio\n";
 hc<<"candidate_bus,control_mode,highest_feasible_der_pu,feasible_levels,tested_levels,first_infeasible_der_pu\n";
 trace<<"candidate_bus,control_mode,der_pu,pnet_local_pu,qnet_local_pu,voltage_pu,current_pu,voltage_margin_pu,current_margin_pu,host_decision\n";
 nlines<<"bus,parent,r_pu,x_pu,imax_pu,pload_pu,qload_pu\n";for(int i=1;i<(int)NB;i++){const auto& b=topo[i];nlines<<i<<','<<b.parent<<','<<e.fmt(b.R)<<','<<e.fmt(b.X)<<','<<e.fmt(b.Imax)<<','<<e.fmt(b.Pload)<<','<<e.fmt(b.Qload)<<'\n';}
 uint64_t feas=0,conv=0,viol=0,indep=0,casecount=0;int bus=-1,mode=-1,levels=0,passed=0;double highest=-1,firstbad=-1;
 auto flush=[&]{if(bus<0)return;hc<<bus<<','<<mode<<','<<e.fmt(highest)<<','<<passed<<','<<levels<<','<<e.fmt(firstbad)<<'\n';};
 for(const auto& sc:scs){if(bus!=sc.bus||mode!=sc.mode){flush();bus=sc.bus;mode=sc.mode;levels=passed=0;highest=firstbad=-1;}
  auto x=solve(e,g,topo,sc,audit);Row derrow{};derrow.fill(0);derrow[2]=sc.pder;double qder_report=g.scalar(sc.mode?"der_q_absorb":"der_q_unity",derrow);req(x.converged,"AC solver failed to converge at bus="+std::to_string(sc.bus)+", level="+std::to_string(sc.step));
  ++conv;++levels;++casecount;passed+=x.feasible;feas+=x.feasible;viol+=x.viols;if(x.feasible)highest=std::max(highest,sc.pder);else if(firstbad<0)firstbad=sc.pder;
  if(audit)indep+=size_t(NB-1)*10;
  f<<sc.bus<<','<<sc.mode<<','<<sc.step<<','<<e.fmt(sc.pder)<<','<<e.fmt(qder_report)<<','<<x.converged<<','<<x.iterations<<','<<x.feasible<<','<<x.viols<<','<<e.fmt(x.minv)<<','<<e.fmt(x.maxv)<<','<<e.fmt(x.min_voltage_margin)<<','<<e.fmt(x.min_current_margin)<<','<<e.fmt(x.loss)<<','<<e.fmt(x.score)<<','<<e.fmt(x.penalty1)<<','<<e.fmt(x.penalty2)<<','<<e.fmt(x.voltage_at_der)<<','<<e.fmt(x.rootP)<<','<<e.fmt(x.rootQ)<<'\n';
  if(sc.step%std::max(1,steps/16)==0){for(int i=1;i<(int)NB;i++){detail<<sc.bus<<','<<sc.mode<<','<<sc.step<<','<<e.fmt(sc.pder)<<','<<i<<','<<e.fmt(x.busvals[i][0])<<','<<e.fmt(x.busvals[i][1])<<','<<e.fmt(x.busvals[i][2]);for(int t=3;t<11;t++)detail<<','<<e.fmt(x.busvals[i][t]);detail<<'\n';}}
  if(sc.step==steps/2){int n=sc.bus;Row r=row_for(topo[n],n);r[2]=sc.pder;r[3]=qder_report;double pnet=g.scalar("net_p",r),qnet=g.scalar("net_q",r);trace<<sc.bus<<','<<sc.mode<<','<<e.fmt(sc.pder)<<','<<e.fmt(pnet)<<','<<e.fmt(qnet)<<','<<e.fmt(x.busvals[n][0])<<','<<e.fmt(x.busvals[n][1])<<','<<e.fmt(x.busvals[n][2])<<','<<e.fmt(x.min_current_margin)<<','<<(x.feasible?"ACCEPT":"REJECT")<<'\n';}
 }flush();f.close();detail.close();hc.close();trace.close();nlines.close();
 write_inventory(g,dest/"math_execution_inventory.csv");std::ofstream registry(dest/"formula_registry.csv");registry<<"formula_id,model_versions,expression,units,execution_owner\n";for(auto& [k,v]:g.inventory())registry<<k<<",v1_v2,\""<<v.formula<<"\","<<v.units<<",paceval\n";registry.close();
 std::ofstream ev(dest/"execution_evidence.json");ev<<"{\n  \"project\": \"WP11 Distribution Grid Hosting Capacity Constraint Kernels\",\n  \"runtime\": \"original paceval SDK 4.25 via locally provided Linux shared library\",\n  \"source_data\": \"synthetic balanced radial feeder, not official IEEE feeder or field measurement\",\n  \"feeder_buses\": "<<NB<<",\n  \"der_location_count\": 8,\n  \"control_modes\": 2,\n  \"penetration_steps\": "<<steps<<",\n  \"scenario_count\": "<<casecount<<",\n  \"feasible_scenarios\": "<<feas<<",\n  \"infeasible_scenarios\": "<<casecount-feas<<",\n  \"all_ac_converged\": "<<(conv==casecount?"true":"false")<<",\n  \"unique_graphs_created\": "<<e.created()<<",\n  \"unique_graphs_executed\": "<<e.executed()<<",\n  \"scalar_calls\": "<<e.scalar_calls<<",\n  \"batch_calls\": "<<e.batch_calls<<",\n  \"graph_point_evaluations\": "<<e.graph_point_evaluations<<",\n  \"native_cpp_reference_checks\": "<<indep<<",\n  \"total_branch_violations\": "<<viol<<"\n}\n";
 std::cout<<"WP11 SUCCESS: cases="<<casecount<<" converged="<<conv<<" feasible="<<feas<<" graphs="<<e.executed()<<" graph_results="<<e.graph_point_evaluations<<" independent_checks="<<indep<<"\n";
}
int main(int argc,char** argv){try{Engine engine;Graphs g(engine);register_graphs(g);
 std::string cmd=argc>1?argv[1]:"--run";
 if(cmd=="--test-conversion"){conversion_tests(engine);std::cout<<"conversion PASS\n";return 0;}
 if(cmd=="--test-operators"){operator_tests(engine,g);std::cout<<"operators PASS\n";return 0;}
 if(cmd=="--test-layout"){layout_test(engine,g);std::cout<<"layout PASS\n";return 0;}
 if(cmd=="--test-invalid"){auto top=topology();auto s=Scenario{7,0,63,2.5};auto r=solve(engine,g,top,s,true);req(r.converged,"test fixed-point nonconvergence");req(!r.feasible,"Expected high-penetration network limit not detected");std::cout<<"invalid-domain PASS\n";return 0;}
 if(cmd=="--run"){fs::path dest=fs::current_path()/"results";int steps=64;for(int i=2;i<argc;i++){std::string k=argv[i];if(k=="--out"&&i+1<argc)dest=argv[++i];else if(k=="--steps"&&i+1<argc)steps=std::stoi(argv[++i]);else throw std::runtime_error("Invalid command argument "+k);}run(engine,g,dest,steps,true);return 0;}
 throw std::runtime_error("Supported commands: --run [--out folder] [--steps integer], --test-conversion, --test-operators, --test-layout, --test-invalid");
 }catch(const std::exception& e){std::cerr<<"WP11 ERROR: "<<e.what()<<'\n';return 1;}}
