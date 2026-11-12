// WP_034: CNC parameter screening with authentic paceval expression graphs.
// Metric equations for a declared synthetic 4-flute peripheral milling setup.
// This is not validated tool-material response data, an industrial CNC controller,
// or a collision/safety-certified optimizer. The host owns screening decisions.
#include "paceval_main.h"
#include <array>
#include <vector>
#include <string>
#include <iostream>
#include <fstream>
#include <iomanip>
#include <sstream>
#include <filesystem>
#include <cmath>
#include <algorithm>
#include <stdexcept>
#include <limits>
namespace fs=std::filesystem;
using X=std::array<double,8>; // vc[m/min], fz[mm/tooth], ap[mm], ae[mm], D[mm], teeth, kc[N/mm2], spindle_eta
using Y=std::array<double,5>; // Q[cm3/min], Pmotor[kW], Ra[mm], toolLife[min], force[N]
static constexpr double PI=3.141592653589793238462643383279502884;
static void require(bool b,const std::string&s){if(!b)throw std::runtime_error(s);}
static double metricNative(int i,const X& a){
 const double vc=a[0],fz=a[1],ap=a[2],ae=a[3],D=a[4],teeth=a[5],kc=a[6],eta=a[7];
 const double rpm=1000.0*vc/(PI*D),vf=rpm*fz*teeth,Q=ap*ae*vf/1000.0, Pc=Q*kc/60000.0;
 switch(i){case 0:return rpm; case 1:return vf;case 2:return Q;case 3:return Pc/eta;
 case 4:return 40.0*std::pow(180.0/vc,4.0)*std::pow(0.12/fz,0.25); // illustrative Taylor-style wear proxy
 case 5:return fz*fz/(32.0*0.8); // geometric feed-mark proxy for declared 0.8mm radius
 case 6:return Pc*60000.0/vc; // apparent cutting-force proxy: P=F * v
 }
 throw std::runtime_error("undefined metric");
}
static std::string scoreExpression(int k){
 // Five deliberate mathematical model families with ten distinct coefficient sets each.
 // Explicit units are absorbed in normalized arguments Q/20, P/5, Ra/0.001, life/40, F/1000.
 const int family=k/10; const int variant=k%10;
 std::ostringstream os; os<<std::setprecision(12);
 const double a=0.28+0.018*variant, b=0.35+0.012*variant,c=0.20+0.008*variant;
 if(family==0)os<<a<<"*(P/5)^2+"<<b<<"*(Ra/0.001)^2-"<<c<<"*(Q/20)";
 if(family==1)os<<a<<"*(F/1000)^2+"<<b<<"*(40/life)^2-"<<c<<"*ln(1+Q/20)";
 if(family==2)os<<a<<"*(P/5)+"<<b<<"*(Ra/0.001)^2+"<<c<<"*(40/life)-0.45*(Q/20)";
 if(family==3)os<<a<<"*sqrt((P/5)^2+(F/1000)^2)+"<<b<<"*(Ra/0.001)-"<<c<<"*(Q/20)";
 if(family==4)os<<a<<"*(P/5)^2+"<<b<<"*(40/life)^2+"<<c<<"*(Ra/0.001)^2-0.4*ln(1+Q/20)";
 return os.str();
}
static double scoreNative(int k,const Y &y){
 double Q=y[0]/20,P=y[1]/5,Ra=y[2]/0.001,life=40/y[3],F=y[4]/1000;
 double a=.28+.018*(k%10),b=.35+.012*(k%10),c=.20+.008*(k%10);
 switch(k/10){
 case 0:return a*P*P+b*Ra*Ra-c*Q;
 case 1:return a*F*F+b*life*life-c*std::log(1+Q);
 case 2:return a*P+b*Ra*Ra+c*life-.45*Q;
 case 3:return a*std::sqrt(P*P+F*F)+b*Ra-c*Q;
 case 4:return a*P*P+b*life*life+c*Ra*Ra-.4*std::log(1+Q);
 }throw std::runtime_error("undefined score");
}
class Engine{
 std::vector<PACEVAL_HANDLE> handles;
public:
 Engine(){require(paceval_InitializeLibrary(nullptr),"paceval_InitializeLibrary failed");}
 ~Engine(){for(auto h:handles)paceval_DeleteComputation(h);paceval_FreeLibrary();}
 int add(const std::string& f,int n,const char*names){auto h=paceval_CreateComputation(f.c_str(),n,names,false,nullptr);
 require(h&&!paceval_GetIsError(h),"paceval graph failed: "+f);handles.push_back(h);return (int)handles.size()-1;}
 double scalar(int j,const double*x){double mutableInput[8]={};std::copy(x,x+(j<7?8:5),mutableInput);double v=paceval_dGetComputationResult(handles.at(j),mutableInput,nullptr,nullptr);
 require(std::isfinite(v)&&!paceval_GetIsError(handles[j]),"paceval scalar error");return v;}
 std::vector<double> batch(int j,const std::vector<X>&xs){
 std::vector<double> args(xs.size()*8),outs(xs.size());std::vector<int>status(xs.size(),-1);
 for(size_t i=0;i<xs.size();++i)for(int a=0;a<8;++a)args[i*8+a]=xs[i][a];
 const bool error=paceval_dGetComputationResultExt(handles.at(j),args.data(),(unsigned long)xs.size(),outs.data(),nullptr,nullptr,status.data());
 require(!error,"paceval batch error");for(size_t i=0;i<outs.size();++i)require(status[i]==0&&std::isfinite(outs[i]),"paceval batch status error");return outs;
 }
};
int main(int argc,char**argv){try{
 fs::path root="examples"; for(int i=1;i<argc;++i)if(std::string(argv[i])=="--out"&&i+1<argc)root=argv[++i];fs::create_directories(root);
 Engine engine;const char* vars="vc fz ap ae D teeth kc eta";const char*scoreVars="Q P Ra life F";
 const std::vector<std::pair<std::string,std::string>> metricExpressions={
 {"spindle_rpm","1000*vc/(3.14159265358979323846*D)"},
 {"table_feed_mm_min","fz*teeth*1000*vc/(3.14159265358979323846*D)"},
 {"material_removal_cm3_min","ap*ae*fz*teeth*vc/(3.14159265358979323846*D)"},
 {"spindle_power_kW","ap*ae*fz*teeth*vc*kc/(3.14159265358979323846*D*60000*eta)"},
 {"tool_life_proxy_min","40*(180/vc)^4*(0.12/fz)^0.25"},
 {"roughness_proxy_mm","fz^2/(32*0.8)"},
 {"force_proxy_N","ap*ae*fz*teeth*kc/(3.14159265358979323846*D)"}
 };
 std::ofstream registry(root/"formula_registry.csv");registry<<"graph_id,group,version,expression\n";
 for(int m=0;m<7;++m){engine.add(metricExpressions[m].second,8,vars);registry<<m+1<<",metric_v1,1,\""<<metricExpressions[m].second<<"\"\n";}
 for(int j=0;j<50;++j){auto expr=scoreExpression(j);engine.add(expr,5,scoreVars);registry<<j+8<<",score_family_"<<j/10+1<<",1,\""<<expr<<"\"\n";}
 const std::string revised="0.43*(P/5)^2+0.39*(Ra/0.001)^2-0.22*(Q/20)+0.07*(F/1000)^2";
 engine.add(revised,5,scoreVars);registry<<58<<",score_family_1_revision,2,\""<<revised<<"\"\n";registry.close();
 std::ofstream samples(root/"screening_candidates.csv"); samples<<std::setprecision(17)
 <<"candidate_id,rule_id,vc_m_min,fz_mm_tooth,ap_mm,ae_mm,rpm,feed_mm_min,mrr_cm3_min,motor_kW,life_proxy_min,roughness_proxy_mm,force_proxy_N,cost,feasible\n";
 long long scalarCount=0,checkCount=0,batchCount=0;int feasible=0;double maxerror=0;
 auto close=[&](double actual,double expected,const char*s){double err=std::abs(actual-expected);maxerror=std::max(maxerror,err);
 require(err<=2.e-9*(1+std::abs(expected)),std::string("numeric reference mismatch ")+s);++checkCount;};
 std::array<int,50>ruleFeasible{};
 for(int i=0;i<8000;++i){
  // Declarative parameter grid; covers a fixed illustrative 12-mm, 4-flute milling setup.
  double vc=100+5*(i%37), fz=.055+.005*((i/37)%23),ap=.7+.15*((i/851)%8),ae=2+.5*((i/11)%13);
  X x={vc,fz,ap,ae,12,4,1850,0.86};Y y{};
  const double rpm=engine.scalar(0,x.data());++scalarCount;close(rpm,metricNative(0,x),"rpm");
  const double vf=engine.scalar(1,x.data());++scalarCount;close(vf,metricNative(1,x),"feed");
  for(int m=2;m<7;++m){int ix=(m==4?3:(m==5?2:m-2));y[ix]=engine.scalar(m,x.data());++scalarCount;close(y[ix],metricNative(m,x),"metric");}
  int j=i%50;double cost=engine.scalar(7+j,y.data());++scalarCount;close(cost,scoreNative(j,y),"score");
  bool ok=(rpm<=9000&&y[1]<=7.5&&y[3]>=18&&y[2]<=.0012&&y[4]<=1800);
  feasible+=ok;ruleFeasible[j]+=ok;
  samples<<i<<','<<j<<','<<vc<<','<<fz<<','<<ap<<','<<ae<<','<<rpm<<','<<vf<<','<<y[0]<<','<<y[1]<<','<<y[3]<<','<<y[2]<<','<<y[4]<<','<<cost<<','<<(ok?1:0)<<'\n';
 }
 // A deliberately separate grid is evaluated through the true paceval batch API.
 std::vector<X>surface;for(int i=0;i<=60;++i)for(int j=0;j<=60;++j)
 surface.push_back({100+3.5*i,.055+.002*j,1.5,5,12,4,1850,.86});
 std::vector<std::vector<double>> outputs;
 for(int m=2;m<=4;++m){auto o=engine.batch(m,surface);batchCount+=o.size();for(size_t i=0;i<o.size();++i)close(o[i],metricNative(m,surface[i]),"surface");outputs.push_back(std::move(o));}
 std::ofstream sf(root/"cnc_response_surface.csv");sf<<std::setprecision(17)<<"vc_m_min,fz_mm_tooth,mrr_cm3_min,motor_kW,life_proxy_min\n";
 for(size_t i=0;i<surface.size();++i)sf<<surface[i][0]<<','<<surface[i][1]<<','<<outputs[0][i]<<','<<outputs[1][i]<<','<<outputs[2][i]<<'\n';
 // Additional actual scalar formula version comparisons; v1 remains unchanged after creating v2.
 std::ofstream revisions(root/"formula_revision.csv");revisions<<std::setprecision(17)<<"vc_m_min,cost_v1,cost_v2\n";
 for(int i=0;i<=100;++i){X x={110.+i*1.5,.115,1.5,5,12,4,1850,.86};Y y{};
 for(int m=2;m<7;++m){int ix=(m==4?3:(m==5?2:m-2));y[ix]=engine.scalar(m,x.data());++scalarCount;}
 double a=engine.scalar(7,y.data()),b=engine.scalar(57,y.data());scalarCount+=2;
 close(a,scoreNative(0,y),"v1");double ref=.43*std::pow(y[1]/5,2)+.39*std::pow(y[2]/.001,2)-.22*(y[0]/20)+.07*std::pow(y[4]/1000,2);close(b,ref,"v2");
 revisions<<x[0]<<','<<a<<','<<b<<'\n';}
 // 256 independent batch inputs per each of seven dimensional metric graphs.
 for(int m=0;m<7;++m){std::vector<X>sub;for(int i=0;i<256;++i)sub.push_back({105.+.4*i,.07+.0002*i,1.2,3.5,12,4,1850,.86});auto out=engine.batch(m,sub);batchCount+=out.size();for(size_t i=0;i<sub.size();++i)close(out[i],metricNative(m,sub[i]),"batch");}
 std::ofstream audit(root/"sdk_audit.txt");audit<<"WP034 direct paceval SDK scientific demonstration\n"
 <<"metric_graphs=7\nscore_v1_graphs=50\nformula_revision_graphs=1\ngraphs_total=58\n"
 <<"screened_candidates=8000\nfeasible_candidates="<<feasible<<"\nsurface_points=3721\n"
 <<"scalar_evaluations="<<scalarCount<<"\nbatch_evaluations="<<batchCount<<"\nreference_checks="<<checkCount
 <<"\nmax_absolute_reference_difference="<<std::setprecision(17)<<maxerror<<"\nPASS\n";
 require(feasible>0&&feasible<8000,"declared constraint set has degenerate screening");
 std::cout<<"PASS WP034 graphs=58 candidates=8000 feasible="<<feasible<<" scalar="<<scalarCount<<" batch="<<batchCount<<"\n";
 return 0;
 }catch(const std::exception&e){std::cerr<<"FAIL WP034: "<<e.what()<<'\n';return 1;}}
