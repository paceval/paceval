// WP28: actual original paceval graph execution for a two-state control-affine plant.
// C++ is responsible for candidate enumeration, RK4, CSV and decisions, not for
// evaluating the published control, state, Lyapunov, margins and certificate.
// The analytic certificate is sufficient on a specified invariant ellipsoid,
// and is NOT a certified industrial controller or a general-purpose SMT solver.
#include "paceval_main.h"
#include <algorithm>
#include <array>
#include <cmath>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <map>
#include <regex>
#include <sstream>
#include <stdexcept>
#include <string>
#include <vector>
namespace fs=std::filesystem;
namespace {
void need(bool ok,const std::string&why){if(!ok)throw std::runtime_error(why);}
void close(double x,double y,double absTol=1e-8,double relTol=1e-8){need(std::isfinite(x)&&std::isfinite(y)&&std::abs(x-y)<=absTol+relTol*std::max(std::abs(x),std::abs(y)),"Independent C++ formula mismatch");}
const std::vector<std::string> VAR={"x","y","a","b","c","d","k1","k2","k3","p1","p2","R","eps","umax"};
const std::vector<std::string> CMP={"v1","v2","vd1","vd2","cm1","cm2","u1","u2"};
std::string joined(const std::vector<std::string>&x){std::string z;for(auto&v:x){if(z.size())z+=' ';z+=v;}return z;}
std::vector<std::string> split(const std::string&s){std::stringstream f(s);std::string t;std::vector<std::string>a;while(std::getline(f,t,','))a.push_back(t);if(!s.empty()&&s.back()==',')a.push_back("");return a;}
bool validLiteral(const std::string&s){static const std::regex re(R"(^[+-]?(?:[0-9]+(?:\.[0-9]*)?|\.[0-9]+)(?:[eE][+-]?[0-9]+)?$)");return std::regex_match(s,re);}
double numberIn(const std::string&s){need(validLiteral(s),"CSV literal rejected: "+s);int err=-1;long pos=-1;double y=paceval_dConvertStringToFloat(s.c_str(),&err,&pos,false,nullptr,nullptr);need(err==0&&std::isfinite(y),"SDK input conversion failed");return y;}
std::string numberOut(double x){need(std::isfinite(x),"Nonfinite output");char str[512]{};int n=paceval_dConvertFloatToString(str,x);need(n>0&&str[0]&&std::string(str).find(',')==std::string::npos,"SDK output conversion failed");return str;}
using Matrix=std::vector<std::vector<double>>;
struct Engine{
 std::vector<PACEVAL_HANDLE>all;bool graphMajor=false;unsigned long long scalarCalls=0,batchCalls=0,graphPoints=0;
 Engine(){need(paceval_InitializeLibrary(nullptr),"paceval_InitializeLibrary failed");}
 ~Engine(){for(auto h:all)if(h)paceval_DeleteComputation(h);paceval_FreeLibrary();}
 PACEVAL_HANDLE create(const std::string&f,const std::vector<std::string>&vars){auto v=joined(vars);PACEVAL_HANDLE h=paceval_CreateComputation(f.c_str(),vars.size(),v.c_str(),false,nullptr);need(h&&!paceval_GetIsError(h),"Original SDK rejected graph: "+f);all.push_back(h);return h;}
 double scalar(PACEVAL_HANDLE h,const std::vector<double>&row){auto x=row;double y=paceval_dGetComputationResult(h,x.empty()?nullptr:x.data(),nullptr,nullptr);scalarCalls++;need(!paceval_GetIsError(h)&&std::isfinite(y),"paceval scalar error");return y;}
 void probe(){auto a=create("x+2*y",{"x","y"});auto b=create("3*x-y",{"x","y"});PACEVAL_HANDLE h[]={a,b};double x[]={1,2,4,7},out[4]{},lo[4]{},hi[4]{};int err[4]{};bool failed=paceval_dGetMultipleComputationsResultsExt(h,2,x,2,out,lo,hi,err);need(!failed&&std::all_of(err,err+4,[](int z){return z==0;}),"Multi graph probe failed");if(std::abs(out[0]-5)<1e-10&&std::abs(out[1]-18)<1e-10&&std::abs(out[2]-1)<1e-10&&std::abs(out[3]-5)<1e-10)graphMajor=true;else if(std::abs(out[0]-5)<1e-10&&std::abs(out[1]-1)<1e-10&&std::abs(out[2]-18)<1e-10&&std::abs(out[3]-5)<1e-10)graphMajor=false;else throw std::runtime_error("Unknown batch ordering");++batchCalls;graphPoints+=4;}
 Matrix batch(const std::vector<PACEVAL_HANDLE>&h,const Matrix&x,size_t cols){need(h.size()&&x.size(),"Empty batch");std::vector<double>in;in.reserve(cols*x.size());for(auto&r:x){need(r.size()==cols,"Width mismatch");for(double z:r)need(std::isfinite(z),"Invalid batch input");in.insert(in.end(),r.begin(),r.end());}
 std::vector<double>out(h.size()*x.size()),lo(out.size()),hi(out.size());std::vector<int>err(out.size(),-1);bool failed=paceval_dGetMultipleComputationsResultsExt(const_cast<PACEVAL_HANDLE*>(h.data()),h.size(),in.data(),x.size(),out.data(),lo.data(),hi.data(),err.data());need(!failed,"SDK batch failure");for(int e:err)need(e==0,"SDK returned nonzero computation error "+std::to_string(e));Matrix y(x.size(),std::vector<double>(h.size()));for(size_t i=0;i<x.size();i++)for(size_t j=0;j<h.size();j++){auto v=out[graphMajor?j*x.size()+i:i*h.size()+j];need(std::isfinite(v),"Nonfinite SDK batch result");y[i][j]=v;}batchCalls++;graphPoints+=out.size();return y;}
};
struct Graph{std::string version,id,expr,units,description;PACEVAL_HANDLE h;bool used=false;};
struct Model{
 Engine&e;std::vector<Graph>g;std::map<std::string,size_t>ix;
 Model(Engine&eng):e(eng){
  for(int v=1;v<=2;v++){
   std::string ver=v==1?"V1":"V2";
   const std::string U="(-k1*x-k2*y"+(v==2?std::string("-k3*tanh(x)"):std::string(""))+")";
   const std::string F1="(-a*x+"+U+"+c*x*y^2)";
   const std::string F2="(-b*y+d*x^2*y)";
   const std::string V="(p1*x^2+p2*y^2)";
   const std::string VD="(2*p1*x*"+F1+"+2*p2*y*"+F2+")";
   const std::string KH=v==2?"k3":"0";
   const std::string B="(0 max (p1*c+p2*d))";
   const std::string M1="(2*p1*(a+k1)+2*p1*"+KH+"*(1-R^2/3)-p1*abs(k2)-"+B+"*R^2/2-eps)";
   const std::string M2="(2*p2*b-p1*abs(k2)-"+B+"*R^2/2-eps)";
   const std::string ACT="(umax-R*(abs(k1)+abs(k2)+"+KH+"))";
   auto add=[&](const std::string&id,const std::string&expr,const std::string&units,const std::string&purpose){size_t i=g.size();g.push_back({ver,id,expr,units,purpose,e.create(expr,VAR),false});ix[ver+"_"+id]=i;};
   add("CONTROL",U,"actuator","Versioned state feedback, with hyperbolic-tangent term in V2");
   add("FLOW_X",F1,"state/s","Closed-loop first state derivative");
   add("FLOW_Y",F2,"state/s","Closed-loop second state derivative");
   add("LYAPUNOV",V,"state2","Positive quadratic candidate V");
   add("VDOT",VD,"state2/s","Full composite Lie derivative of V");
   add("RESIDUAL","(-eps*(x^2+y^2)-"+VD+")","state2/s","Pointwise Lyapunov negative-definiteness margin");
   add("STATE_MARGIN","(R^2-x^2-y^2)","state2","Signed disk-state constraint");
   add("ACTUATOR_MARGIN","(umax-abs("+U+"))","actuator","Pointwise actuator headroom");
   add("POSITIVE_V","("+V+"-(p1 min p2)*(x^2+y^2))","state2","Quadratic lower-bound residual");
   add("NORM_RESIDUAL","((-eps*(x^2+y^2)-"+VD+")/(1+x^2+y^2))","state2/s","Normalized Lyapunov margin");
   add("M1_CERT",M1,"state2/s","Algebraically sufficient first coefficient over disk");
   add("M2_CERT",M2,"state2/s","Algebraically sufficient second coefficient over disk");
   add("CERT_MARGIN","("+M1+" min "+M2+")","state2/s","Minimum sufficient Lyapunov coefficient");
   add("GLOBAL_ACT_MARGIN",ACT,"actuator","Conservative disk-wide actuator headroom");
   add("CERT_GUARD","(("+M1+">=0) AND ("+M2+">=0) AND ("+ACT+">=0) AND (p1>0) AND (p2>0))","0/1","Sufficient analytic certificate and actuator-screen flag");
   add("SAMPLED_GUARD","(((-eps*(x^2+y^2)-"+VD+")>=(-0.00000001)) AND ("+U+"<=umax) AND ("+U+">=(-umax)) AND ((R^2-x^2-y^2)>=(-0.00000001)))","0/1","Sampled conditions, NOT continuous proof");
   add("SENS_K1_VDOT","(-2*p1*x^2)","state2/s/gain","Analytic sensitivity of Vdot to k1");
   add("SENS_K2_VDOT","(-2*p1*x*y)","state2/s/gain","Analytic sensitivity of Vdot to k2");
   add("SENS_K3_VDOT",v==2?"(-2*p1*x*tanh(x))":"(0*x)","state2/s/gain","Analytic sensitivity of Vdot to nonlinear gain");
   add("SENS_K3_CONTROL",v==2?"(-tanh(x))":"(0*x)","actuator/gain","Analytic control sensitivity to nonlinear gain");
   add("CONTROL_ENERGY","("+U+"^2)","actuator2","Quadratic actuator usage at state");
   add("COMPOSITE_SCORE","((-eps*(x^2+y^2)-"+VD+")-0.01*"+U+"^2)","state2/s","Composite pointwise residual and actuator usage score");
  }
  auto add=[&](const std::string&id,const std::string&expr,const std::string&units,const std::string&purpose){size_t i=g.size();g.push_back({"COMPARE",id,expr,units,purpose,e.create(expr,CMP),false});ix["COMPARE_"+id]=i;};
  add("DELTA_VDOT","(vd2-vd1)","state2/s","Model difference in Lyapunov derivative");
  add("DELTA_CONTROL","(u2-u1)","actuator","Versioned feedback difference");
  add("DELTA_V","(v2-v1)","state2","Lyapunov function difference");
  add("DELTA_CERT","(cm2-cm1)","state2/s","Difference between conservative certificate margins");
  add("BOTH_CERT","((cm1>=0) AND (cm2>=0))","0/1","Joint sufficient coefficient status");
 }
 Matrix batch(const std::string&ver,const Matrix&x){std::vector<PACEVAL_HANDLE>h;for(auto&z:g)if(z.version==ver)h.push_back(z.h);auto a=e.batch(h,x,ver=="COMPARE"?CMP.size():VAR.size());for(auto&z:g)if(z.version==ver)z.used=true;return a;}
 std::map<std::string,double> extract(const std::string&ver,const std::vector<double>&row)const{std::map<std::string,double>m;size_t i=0;for(auto&z:g)if(z.version==ver)m[z.id]=row.at(i++);need(i==row.size(),"Graph count mismatch");return m;}
 double scalar(const std::string&ver,const std::string&id,const std::vector<double>&x){return e.scalar(g[ix.at(ver+"_"+id)].h,x);}
};
struct Case{std::string id;std::vector<double>theta;};
std::vector<Case> read(const fs::path&p){std::ifstream f(p);need(bool(f),"Cannot open input CSV");std::string ln;need(bool(std::getline(f,ln)),"Empty input");need(ln=="candidate_id,k1,k2,k3,a,b,c,d,p1,p2,R,eps,umax","Wrong input schema");std::vector<Case>out;while(std::getline(f,ln)){if(ln.empty())continue;auto a=split(ln);need(a.size()==13,"CSV width wrong");need(std::regex_match(a[0],std::regex("C[0-9]{4}")),"CSV ID invalid");Case c;c.id=a[0];for(size_t i=1;i<a.size();i++)c.theta.push_back(numberIn(a[i]));auto&t=c.theta;need(t[2]>=0&&t[3]>0&&t[4]>0&&t[5]>=0&&t[6]>=0&&t[7]>0&&t[8]>0&&t[9]>0&&t[9]<=1&&t[10]>0&&t[11]>0,"Domain constraints failed");out.push_back(c);}need(!out.empty(),"No candidates");return out;}
std::vector<double> point(const Case&c,double x,double y){auto&t=c.theta;return {x,y,t[3],t[4],t[5],t[6],t[0],t[1],t[2],t[7],t[8],t[9],t[10],t[11]};}
struct Ref{double u,v,vd,f1,f2,cert,act;};
Ref native(const Case&cc,double x,double y,int version){auto&t=cc.theta;double k1=t[0],k2=t[1],k3=(version==2?t[2]:0),a=t[3],b=t[4],c=t[5],d=t[6],p1=t[7],p2=t[8],R=t[9],eps=t[10],umax=t[11];double u=-k1*x-k2*y-k3*std::tanh(x),f1=-a*x+u+c*x*y*y,f2=-b*y+d*x*x*y;double v=p1*x*x+p2*y*y;double vd=2*p1*x*f1+2*p2*y*f2;double B=std::max(0.,p1*c+p2*d),mix=p1*std::abs(k2)+B*R*R/2;double m1=2*p1*(a+k1)+2*p1*k3*(1-R*R/3)-mix-eps,m2=2*p2*b-mix-eps;double act=umax-R*(std::abs(k1)+std::abs(k2)+k3);return {u,v,vd,f1,f2,std::min(m1,m2),act};}
void operatorTests(Engine&e){for(auto z:std::vector<std::pair<std::string,double>>{{"((-1)%10)",-1},{"((-1) mod 10)",9},{"(4 min 5)",4},{"(4 max 5)",5},{"(3<4)",1},{"(3<=3)",1},{"(3>=3)",1},{"(3=3)",1},{"(3<>4)",1},{"NOT(0)",1},{"(1 AND 1)",1},{"(0 OR 1)",1},{"((3<=3) AND (2>=0))",1},{"tanh(0)",0}})close(e.scalar(e.create(z.first,{}),{}),z.second);for(auto s:{"","1+2","NaN","Inf","1,2","1e999","--1"," 1"}){bool rejected=false;try{numberIn(s);}catch(...){rejected=true;}need(rejected,"CSV injection allowed");}close(numberIn("-1.25e-3"),-.00125);need(!numberOut(.125).empty(),"Numeric formatter failed");}
void selftest(){Engine e;e.probe();operatorTests(e);Model m(e);Case c{"C0000",{.4,0,.7,.5,.65,.16,.11,1.2,1.,1.,.05,2.8}};for(int v=1;v<=2;v++){std::string ver=v==1?"V1":"V2";auto p=point(c,.3,.4);auto z=m.extract(ver,m.batch(ver,{p})[0]);auto r=native(c,.3,.4,v);close(z.at("VDOT"),r.vd);close(z.at("CONTROL"),r.u);close(z.at("CERT_MARGIN"),r.cert);close(m.scalar(ver,"FLOW_X",p),r.f1);close(m.scalar(ver,"FLOW_Y",p),r.f2);}std::cout<<"PASS real SDK scalar batch operators conversion and analytic coefficient\n";}
struct Result{double minres=1e100,cert=0,act=0,maxcontrol=0,maxvd=-1e100,meanV=0,sampled=0,analytic=0,finalV=0;int violations=0;};
void run(const fs::path&source,const fs::path&dest){fs::create_directories(dest);Engine e;e.probe();operatorTests(e);Model m(e);auto cases=read(source);size_t n=cases.size(),nativeChecks=0;std::vector<std::array<Result,2>>rs(n);
 std::ofstream screen(dest/"screening.csv"),points(dest/"state_samples.csv"),compare(dest/"model_comparison.csv"),trace(dest/"closed_loop_traces.csv"),audit(dest/"native_audit.csv"),manifest(dest/"formula_manifest.csv"),inventory(dest/"math_execution_inventory.csv"),evidence(dest/"execution_evidence.json");need(bool(screen&&points&&compare&&trace&&audit&&manifest&&inventory&&evidence),"Cannot create result files");
 screen<<"candidate_id,model,sampled_min_residual,analytic_cert_margin,global_actuator_margin,max_sampled_actuator,max_sampled_vdot,sampled_violations,sampled_pass,analytic_certificate,final_rk4_V\n";
 points<<"candidate_id,model,x,y,control,V,Vdot,lyapunov_margin,actuator_margin,pointwise_guard,certificate_margin\n";
 compare<<"candidate_id,delta_Vdot_x03_y04,delta_u_x03_y04,delta_cert_margin,both_certified,sampled_V1,sampled_V2,certified_V1,certified_V2\n";
 trace<<"candidate_id,model,initial_case,time,x,y,V,Vdot,control\n";
 audit<<"candidate_id,model,x,y,checks,passed\n";
 // The disk is sampled only for candidate screening. It never substitutes for the analytic certificate.
 Matrix states;for(int j=-10;j<=10;j++)for(int i=-10;i<=10;i++){double x=i/10.,y=j/10.;if(x*x+y*y<=1.000001)states.push_back({x,y});}
 for(size_t k=0;k<n;k++)for(int v=1;v<=2;v++){
  std::string ver=v==1?"V1":"V2";auto&cc=cases[k];Matrix inputs;for(auto&p:states)inputs.push_back(point(cc,p[0],p[1]));auto rr=m.batch(ver,inputs);auto&res=rs[k][v-1];res.cert=m.extract(ver,rr[0]).at("CERT_MARGIN");res.act=m.extract(ver,rr[0]).at("GLOBAL_ACT_MARGIN");res.analytic=(m.extract(ver,rr[0]).at("CERT_GUARD")>.5)?1:0;
  for(size_t i=0;i<rr.size();i++){auto z=m.extract(ver,rr[i]);double x=states[i][0],y=states[i][1];double val=z.at("RESIDUAL"),vd=z.at("VDOT"),u=z.at("CONTROL");res.minres=std::min(res.minres,val);res.maxvd=std::max(res.maxvd,vd);res.maxcontrol=std::max(res.maxcontrol,std::abs(u));if(val< -1e-8||std::abs(u)>cc.theta[11]+1e-8)res.violations++;
   if(k<14 || (k%31==0&&i%11==0))points<<cc.id<<','<<ver<<','<<numberOut(x)<<','<<numberOut(y)<<','<<numberOut(u)<<','<<numberOut(z.at("LYAPUNOV"))<<','<<numberOut(vd)<<','<<numberOut(val)<<','<<numberOut(z.at("ACTUATOR_MARGIN"))<<','<<numberOut(z.at("SAMPLED_GUARD"))<<','<<numberOut(z.at("CERT_MARGIN"))<<'\n';
   if((k<8&&i%13==0)||(k%19==0&&i%17==0)){auto ref=native(cc,x,y,v);close(ref.u,u);close(ref.v,z.at("LYAPUNOV"));close(ref.vd,vd);close(ref.cert,z.at("CERT_MARGIN"));close(ref.act,z.at("GLOBAL_ACT_MARGIN"));nativeChecks+=5;audit<<cc.id<<','<<ver<<','<<numberOut(x)<<','<<numberOut(y)<<",5,1\n";}
  }
  res.sampled=res.violations==0?1:0;
  // Host RK4 orchestrates time stepping; every RHS evaluation is computed by original paceval.
  if(k<14){for(int ic=0;ic<3;ic++){double x=ic==0?.65:(ic==1?-.4:.2),y=ic==0?.2:(ic==1?.7:-.55),h=.025;
    for(int j=0;j<=120;j++){
      auto p=point(cc,x,y);double vv=m.scalar(ver,"LYAPUNOV",p),vd=m.scalar(ver,"VDOT",p),u=m.scalar(ver,"CONTROL",p);
      trace<<cc.id<<','<<ver<<','<<ic<<','<<numberOut(j*h)<<','<<numberOut(x)<<','<<numberOut(y)<<','<<numberOut(vv)<<','<<numberOut(vd)<<','<<numberOut(u)<<'\n';
      if(j==120){if(ic==0)res.finalV=vv;break;}
      auto rhs=[&](double X,double Y)->std::array<double,2>{auto q=point(cc,X,Y);return {m.scalar(ver,"FLOW_X",q),m.scalar(ver,"FLOW_Y",q)};};
      auto a=rhs(x,y),b=rhs(x+h*a[0]/2,y+h*a[1]/2),c=rhs(x+h*b[0]/2,y+h*b[1]/2),d=rhs(x+h*c[0],y+h*c[1]);x+=h*(a[0]+2*b[0]+2*c[0]+d[0])/6;y+=h*(a[1]+2*b[1]+2*c[1]+d[1])/6;need(std::isfinite(x)&&std::isfinite(y)&&std::abs(x)<10&&std::abs(y)<10,"ODE escaped domain; mark invalid model");
    }
   }}
  screen<<cc.id<<','<<ver<<','<<numberOut(res.minres)<<','<<numberOut(res.cert)<<','<<numberOut(res.act)<<','<<numberOut(res.maxcontrol)<<','<<numberOut(res.maxvd)<<','<<res.violations<<','<<res.sampled<<','<<res.analytic<<','<<numberOut(res.finalV)<<'\n';
 }
 for(size_t k=0;k<n;k++){auto&c=cases[k];auto p=point(c,.3,.4);auto z1=m.extract("V1",m.batch("V1",{p})[0]);auto z2=m.extract("V2",m.batch("V2",{p})[0]);auto& a=rs[k][0];auto& b=rs[k][1];auto comp=m.extract("COMPARE",m.batch("COMPARE",{{z1.at("LYAPUNOV"),z2.at("LYAPUNOV"),z1.at("VDOT"),z2.at("VDOT"),a.cert,b.cert,z1.at("CONTROL"),z2.at("CONTROL")}})[0]);compare<<c.id<<','<<numberOut(comp.at("DELTA_VDOT"))<<','<<numberOut(comp.at("DELTA_CONTROL"))<<','<<numberOut(comp.at("DELTA_CERT"))<<','<<numberOut(comp.at("BOTH_CERT"))<<','<<a.sampled<<','<<b.sampled<<','<<a.analytic<<','<<b.analytic<<'\n';}
 manifest<<"graph_id,formula_version,expression,units,industrial_function\n";inventory<<"function_id,domain_quantity,mathematical_definition,units,execution_owner,paceval_graph_id,formula_version,api_path,reference_test,status,host_reason\n";size_t executed=0;for(auto&g:m.g){executed+=g.used;manifest<<g.version<<'_'<<g.id<<','<<g.version<<",\""<<g.expr<<"\","<<g.units<<",\""<<g.description<<"\"\n";inventory<<g.version<<'_'<<g.id<<",\""<<g.description<<"\",\""<<g.expr<<"\","<<g.units<<",paceval,"<<g.version<<'_'<<g.id<<','<<g.version<<",paceval_dGetMultipleComputationsResultsExt,independent native and mpmath,"<<(g.used?"executed":"registered_only")<<",\n";}need(executed==m.g.size(),"Unused graphs found");inventory<<"CANDIDATE_ENUMERATION,Parameter loop,deterministic candidate enumeration,1,host,,both,C++ loop,CSV schema,executed,stateful algorithm\n";inventory<<"TIME_INTEGRATION,RK4 loop,explicit fourth-order Runge Kutta,seconds,host,,both,C++ RK4,independent Python RK4,executed,stateful integration with paceval-computed RHS\n";inventory<<"DOMAIN_DECISION,Decision based on numeric guards,minimum and model guards,0/1,host,,both,C++ policy,analytic inequality reference,executed,accept-review-reject is host decision\n";
 size_t samp[2]={},cert[2]={},cex[2]={};for(auto&r:rs){for(int v=0;v<2;v++){samp[v]+=r[v].sampled>.5;cert[v]+=r[v].analytic>.5;cex[v]+=r[v].violations>0;}}
 evidence<<"{\n \"sdk\":\"original paceval 4.25, Linux x86-64 shared library\",\n \"unique_graphs_created\":"<<m.g.size()<<",\n \"unique_graphs_executed\":"<<executed<<",\n \"scalar_calls\":"<<e.scalarCalls<<",\n \"batch_calls\":"<<e.batchCalls<<",\n \"graph_point_evaluations\":"<<e.graphPoints<<",\n \"candidate_count\":"<<n<<",\n \"model_candidate_combinations\":"<<n*2<<",\n \"sample_points_per_candidate\":"<<states.size()<<",\n \"sampled_pass_V1\":"<<samp[0]<<",\n \"sampled_pass_V2\":"<<samp[1]<<",\n \"analytic_certificate_V1\":"<<cert[0]<<",\n \"analytic_certificate_V2\":"<<cert[1]<<",\n \"counterexample_candidate_V1\":"<<cex[0]<<",\n \"counterexample_candidate_V2\":"<<cex[1]<<",\n \"native_endvalue_assertions\":"<<nativeChecks<<"\n}\n";
 std::cout<<"PASS "<<executed<<" executed genuine original SDK graphs; "<<n<<" candidate feedback laws; sampled V1/V2="<<samp[0]<<"/"<<samp[1]<<"; sufficient analytic V1/V2="<<cert[0]<<"/"<<cert[1]<<"; native checks="<<nativeChecks<<"\n";
}
}
int main(int argc,char**argv){try{if(argc==2&&std::string(argv[1])=="--selftest"){selftest();return 0;}need(argc==4&&std::string(argv[1])=="--run","Usage: nonlinear_lyapunov --run input/candidates.csv results_folder");run(argv[2],argv[3]);return 0;}catch(const std::exception&e){std::cerr<<"ERROR: "<<e.what()<<'\n';return 1;}}
