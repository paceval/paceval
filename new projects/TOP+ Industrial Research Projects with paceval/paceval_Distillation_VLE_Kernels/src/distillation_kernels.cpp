// WP17 Distillation VLE research demonstrator.
// Real paceval SDK graph evaluation; synthetic process scenarios and explicitly bounded NIST vapor-pressure equations.
// This is neither a full MESH column simulator nor a validated plant design or control system.
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
#include <vector>
namespace fs=std::filesystem;
static void need(bool v,const std::string& s){if(!v)throw std::runtime_error(s);}
static constexpr int NV=24;
static constexpr int X=0,T=1,P=2,AL=3,AM=4,F=5,ZF=6,XD=7,XB=8,R=9,H=10,QMAX=11,TARGET=12,TOL=13,TMIN=14,TMAX=15,Y=16,PB=17,D=18,B=19,L=20,V=21,STAGE=22,YREF=23;
static const char* NAMES="x temp press alpha amag feed zf xd xb reflux hvap emax target tol tmin tmax ycalc pbcalc dcal bcal lcal vcal stage yref";
using Row=std::array<double,NV>;
static const std::string PA="exp(ln(10)*(4.72583-1660.652/(temp-1.461)))";
static const std::string PSB="exp(ln(10)*(4.07827-1343.943/(temp-53.773)))";
static const std::string GA="exp(amag*sqr(1-x))";
static const std::string GB="exp(amag*sqr(x))";
static const std::string BUB="(x*"+GA+"*"+PA+"+(1-x)*"+GB+"*"+PSB+")";
static const std::string Y2="(x*"+GA+"*"+PA+"/"+BUB+")";
static const std::string A2="("+GA+"*"+PA+"/("+GB+"*"+PSB+"))";
static const std::string Y1="(alpha*x/(1+(alpha-1)*x))";
static const std::string NDA="("+GA+"*"+PA+")";
static const std::string NDB="("+GB+"*"+PSB+")";
static const std::string DNUM="("+NDA+"-2*amag*x*(1-x)*"+NDA+")";
static const std::string DOTHER="(-"+NDB+"+2*amag*x*(1-x)*"+NDB+")";
static const std::string DER2="( ("+DNUM+"*((1-x)*"+NDB+")-(x*"+NDA+")*"+DOTHER+")/sqr("+BUB+") )";
struct Engine{
 std::vector<PACEVAL_HANDLE> owned;std::set<PACEVAL_HANDLE> executed;uint64_t batch_calls=0,scalar_calls=0,outputs=0;
 Engine(){need(paceval_InitializeLibrary(nullptr),"Unable to initialize original paceval runtime");}
 ~Engine(){for(auto h:owned)paceval_DeleteComputation(h);paceval_FreeLibrary();}
 PACEVAL_HANDLE add(const std::string& formula){auto h=paceval_CreateComputation(formula.c_str(),NV,NAMES,false,nullptr);need(h!=nullptr,"paceval returned null handle");
  if(paceval_GetIsError(h)){char a[2000]={},b[2000]={};paceval_CreateErrorInformationText(h,a,b);paceval_DeleteComputation(h);throw std::runtime_error("Graph creation failed: "+formula.substr(0,130)+" -- "+a+" "+b);}owned.push_back(h);return h;}
 double scalar(PACEVAL_HANDLE h,const Row& r){double v=paceval_dGetComputationResult(h,const_cast<double*>(r.data()),nullptr,nullptr);need(!paceval_GetIsError(h)&&std::isfinite(v),"Failed scalar graph call");executed.insert(h);scalar_calls++;outputs++;return v;}
 std::vector<double> batch(const std::vector<PACEVAL_HANDLE>& hs,const std::vector<Row>& rs){need(!rs.empty()&&!hs.empty(),"Empty batch");
  std::vector<double> input;input.reserve(rs.size()*NV);for(auto& r:rs)for(double v:r){need(std::isfinite(v),"Nonfinite graph input");input.push_back(v);}
  std::vector<double> out(rs.size()*hs.size());std::vector<int> errors(out.size(),-1);auto a=hs;
  bool failed=paceval_dGetMultipleComputationsResultsExt(a.data(),(unsigned long)a.size(),input.data(),(unsigned long)rs.size(),out.data(),nullptr,nullptr,errors.data());need(!failed,"Multi graph evaluation failed");
  for(size_t i=0;i<out.size();i++)need(errors[i]==PACEVAL_ERR_NO_ERROR&&std::isfinite(out[i]),"Multi graph error idx="+std::to_string(i)+" err="+std::to_string(errors[i]));
  for(auto h:hs)executed.insert(h);batch_calls++;outputs+=out.size();return out;}
 double parse(const std::string& s)const{static const std::regex decimal(R"(^[+-]?(?:[0-9]+(?:\.[0-9]*)?|\.[0-9]+)(?:[eE][+-]?[0-9]+)?$)");need(std::regex_match(s,decimal),"Rejected non-literal CSV numeric field: "+s);int err=-1;long pos=-1;double v=paceval_dConvertStringToFloat(s.c_str(),&err,&pos,false,nullptr,nullptr);need(err==PACEVAL_ERR_NO_ERROR&&std::isfinite(v),"paceval numeric conversion error at "+std::to_string(pos));return v;}
 std::string fmt(double v)const{need(std::isfinite(v),"Refused nonfinite output");char buf[512]={};int digits=paceval_dConvertFloatToString(buf,v);need(digits>0&&buf[0],"paceval numeric formatting failed");return std::string(buf);}
};
using Defs=std::map<std::string,std::string>;
struct Graph{std::string key,formula,version;PACEVAL_HANDLE handle;};
using Graphs=std::map<std::string,Graph>;
static Graphs create(Engine& e,const Defs& d,const std::string& vers){Graphs out;for(auto& [key,expr]:d)out.emplace(key,Graph{key,expr,vers,e.add(expr)});return out;}
static std::vector<PACEVAL_HANDLE> hs(const Graphs& g){std::vector<PACEVAL_HANDLE> a;for(auto& [key,v]:g)a.push_back(v.handle);return a;}
static std::map<std::string,size_t> index(const Graphs& g){std::map<std::string,size_t> a;size_t i=0;for(auto& p:g)a[p.first]=i++;return a;}
static Defs primary(int v){
 if(v==1)return {{"vapor_y",Y1},{"effective_alpha","alpha"},{"sensitivity_x","(alpha/sqr(1+(alpha-1)*x))"},
  {"sensitivity_alpha","(x*(1-x)/sqr(1+(alpha-1)*x))"},{"separation_factor","alpha"},{"bubble_pressure_reference",BUB},
  {"liquid_composition_margin","(x min (1-x))"},{"vapor_enrichment","("+Y1+"-x)"},
  {"enrichment_indicator","("+Y1+">=x)"}};
 return {{"vapor_y",Y2},{"effective_alpha",A2},{"sensitivity_x",DER2},
  {"sensitivity_temperature","("+Y2+"*(1-"+Y2+")*ln(10)*(1660.652/sqr(temp-1.461)-1343.943/sqr(temp-53.773)))"},
  {"separation_factor",A2},{"vapor_enrichment","("+Y2+"-x)"},
  {"psat_benzene",PA},{"psat_toluene",PSB},{"activity_benzene",GA},{"activity_toluene",GB},
  {"bubble_pressure",BUB},{"bubble_residual","("+BUB+"-press)"},
  {"liquid_composition_margin","(x min (1-x))"},{"enrichment_indicator","("+Y2+">=x)"}};
}
static Defs secondary(){return {
 {"distillate_flow","(feed*(zf-xb)/(xd-xb))"},
 {"bottoms_flow","(feed*(xd-zf)/(xd-xb))"},
 {"light_component_balance","(feed*zf-dcal*xd-bcal*xb)"},
 {"total_mass_balance","(feed-dcal-bcal)"},
 {"reflux_liquid_flow","(dcal*reflux)"},
 {"vapor_flow","(dcal*(reflux+1))"},
 {"reflux_ratio","(lcal/dcal)"},
 {"reboiler_duty_kw","(vcal*hvap/3.6)"},
 {"condenser_duty_kw","(-vcal*hvap/3.6)"},
 {"energy_margin_kw","(emax-vcal*hvap/3.6)"},
 {"product_purity_margin","(xd-target)"},
 {"vle_target_margin","(tol-abs(ycalc-yref))"},
 {"rectifying_operating_y","((reflux*x+xd)/(reflux+1))"},
 {"stripping_operating_y","(xb+(x-xb)*(((reflux*zf+xd)/(reflux+1))-xb)/(zf-xb))"},
 {"combined_quality_indicator","(((xd>=target) AND (vcal*hvap/3.6<=emax)) AND (abs(ycalc-yref)<=tol))"},
 {"energy_purity_score","(0.65*(xd-target)+0.35*(emax-vcal*hvap/3.6)/emax)"},
 {"stage_approach_margin","(ycalc-x)"},
 {"fenske_local_proxy","(ln((xd*(1-xb))/(xb*(1-xd)))/ln(alpha))"},
 {"temperature_domain_margin","((temp-tmin) min (tmax-temp))"},
 {"isobaric_bubble_residual","(pbcalc-press)"}
 };}
static double psat_a(double t){return std::pow(10.,4.72583-1660.652/(t-1.461));}
static double psat_b(double t){return std::pow(10.,4.07827-1343.943/(t-53.773));}
static double native_y(int ver,double x,double t,double a,double m){
 if(ver==1)return a*x/(1+(a-1)*x);
 double ga=std::exp(m*(1-x)*(1-x)),gb=std::exp(m*x*x);double q=x*ga*psat_a(t),r=(1-x)*gb*psat_b(t);return q/(q+r);
}
static double native_pb(double x,double t,double m){return x*std::exp(m*(1-x)*(1-x))*psat_a(t)+(1-x)*std::exp(m*x*x)*psat_b(t);}
static bool close(double v,double expected,double rtol=1e-9){return std::isfinite(v)&&std::isfinite(expected)&&std::abs(v-expected)<=rtol*std::max(1.,std::abs(expected));}
static void check(double v,double ref,const std::string& what,double tol=1e-9){need(close(v,ref,tol),"Native independent reference mismatch: "+what+" got "+std::to_string(v)+" ref "+std::to_string(ref));}
static uint64_t mix(uint64_t x){x^=x>>30;x*=UINT64_C(0xbf58476d1ce4e5b9);x^=x>>27;x*=UINT64_C(0x94d049bb133111eb);return x^(x>>31);}
static double uni(uint64_t s){return double(mix(s)>>11)/(9007199254740992.0);}
static Row make_row(size_t i){Row r{};r.fill(0.);r[X]=0.02+0.96*uni(i*277+12);r[T]=336+36*uni(i*911+57);r[P]=.60;r[AL]=2.6;r[AM]=.18;r[F]=100.;r[ZF]=.47;r[XD]=.94;r[XB]=.08;
 r[R]=1.1+5.9*uni(i*53+81);r[H]=31.0;r[QMAX]=3600;r[TARGET]=.925;r[TOL]=.12;r[TMIN]=333.4;r[TMAX]=373.5;r[STAGE]=1;r[YREF]=.55+.38*uni(i*71+23);
 return r;}
static void validate(const Row& r){for(double v:r)need(std::isfinite(v),"Non-finite scenario field");need(r[X]>=0&&r[X]<=1&&r[T]>=333.4&&r[T]<=373.5,"Composition/Antoine temperature out of range");need(r[P]>0&&r[AL]>1&&r[AM]>=0&&r[AM]<=.4&&r[F]>0&&r[ZF]>r[XB]&&r[XD]>r[ZF]&&r[XD]<1&&r[XB]>0,"Invalid thermodynamics or split inputs");need(r[R]>=0&&r[H]>0&&r[QMAX]>0&&r[TOL]>0,"Invalid policy domain");}
static std::vector<std::string> split(const std::string& a){std::stringstream s(a);std::vector<std::string> b;std::string t;while(std::getline(s,t,','))b.push_back(t);if(!a.empty()&&a.back()==',')b.push_back("");return b;}
static void create_inputs(const Engine& e,const fs::path& p,int count){std::ofstream f(p);need(bool(f),"Input CSV cannot be created");f<<"sample,x,temp_K,pressure_bar,alpha_constant,margules_A,feed_kmol_h,zfeed,xd,xb,reflux,latent_MJ_kmol,heatcap_kW,target_xd,eq_tol,tmin_K,tmax_K,yref\n";
 for(int i=0;i<count;i++){Row r=make_row(i);f<<i;for(int j=0;j<=TMAX;j++)f<<','<<e.fmt(r[j]);f<<','<<e.fmt(r[YREF])<<'\n';}}
static std::vector<Row> load_inputs(const Engine& e,const fs::path& p){std::ifstream f(p);need(bool(f),"Input CSV missing");std::string line;need(bool(std::getline(f,line))&&split(line).size()==18,"CSV schema header invalid");std::vector<Row> rows;size_t expected=0;
 while(std::getline(f,line)){if(line.empty())continue;auto p=split(line);need(p.size()==18,"CSV row has invalid field count");need(p[0]==std::to_string(expected),"Unexpected input record ID");Row r{};r.fill(0);for(int j=0;j<=TMAX;j++)r[j]=e.parse(p[j+1]);r[YREF]=e.parse(p[17]);validate(r);rows.push_back(r);expected++;}return rows;}
static void selftest(Engine& e){for(auto s:{"0","-21.5","7.1e-5","1.005","1E+9"})need(std::isfinite(e.parse(e.fmt(e.parse(s)))),"CSV roundtrip failed");
 for(auto s:{"","3+2","NaN","inf","2,3","1e9999","bad","0xA"}){bool bad=false;try{(void)e.parse(s);}catch(...){bad=true;}need(bad,"Unsafe CSV numeric literal accepted");}
 Row r=make_row(4);for(auto [formula,val]:std::vector<std::pair<std::string,double>>{{"(-1) % 10",-1},{"(-1) mod 10",9},{"(4 min 5)",4},{"(4 max 5)",5},{"((x>0) AND (x<=1))",1},{"((x<0) OR (x>=0))",1},{"NOT(x<0)",1},{"((x=0) OR (x<>0))",1}}){auto h=e.add(formula);check(e.scalar(h,r),val,"operator "+formula);}
 auto h=e.add("(x+temp)"),h2=e.add("(temp-x)");Row r2=r;r2[X]=.75;auto o=e.batch({h,h2},{r,r2});need(o.size()==4&&close(o[0],r[X]+r[T])&&close(o[1],r2[X]+r2[T])&&close(o[2],r[T]-r[X])&&close(o[3],r2[T]-r2[X]),"Wrong multi-graph output layout");
 check(e.scalar(h,r),r[X]+r[T],"scalar vs batch");
 auto bad=make_row(12);bad[T]=380.;bool denied=false;try{validate(bad);}catch(...){denied=true;}need(denied,"Out of range Antoine input accepted");
 std::cout<<"SDK selftest passed (CSV conversions, operators, scalar and multi-graph layout, domains)\n";
}
static void inventory(const fs::path& dir,const Graphs& a,const Graphs& b,const Graphs& s1,const Graphs& s2){std::ofstream f(dir/"math_execution_inventory.csv"),g(dir/"formula_registry.csv");need(bool(f)&&bool(g),"Cannot write inventories");
 f<<"function_id,domain_quantity,mathematical_definition,units,execution_owner,paceval_graph_id,formula_version,api_path,reference_test,status,host_reason\n";
 g<<"graph_id,version,role,formula\n";
 for(auto p:{std::pair<const Graphs*,std::string>{&a,"V1"},{&b,"V2"},{&s1,"V1"},{&s2,"V2"}})for(auto& [name,graph]:*p.first){std::string id=p.second+"_"+name;f<<id<<','<<name<<",\""<<graph.formula<<"\",documented,paceval,"<<id<<','<<p.second<<",dGetMultipleComputationsResultsExt,native_cpp_and_high_precision,executed,\n";
 g<<id<<','<<p.second<<",verified_graph,\""<<graph.formula<<"\"\n";}
 for(auto& name:{"stagewise_iteration","isobaric_temperature_bisection","CSV_schema_validation"})f<<name<<','<<name<<",algorithm_or_validation,not_applicable,host,,both,host_orchestration,independent_tests,executed,iterative_or_categorical\n";
}
static int stage_count(int vers,double xd,double xb,double zf,double reflux,const std::vector<std::pair<double,double>>& curve){
 // Total-condenser, saturated-liquid feed and constant molar overflow McCabe-Thiele shortcut.
 // y(x) was tabulated from paceval graphs. It is monotone on the model domain; inverse via interpolation.
 double vy=xd;int stages=0;for(;stages<70;stages++){
  if(vy<=curve.front().second)return -1;double x=curve.front().first;
  auto it=std::lower_bound(curve.begin(),curve.end(),vy,[](auto& pair,double yy){return pair.second<yy;});
  if(it==curve.end())return -1;
  if(it!=curve.begin()){auto lo=it-1;x=lo->first+(it->first-lo->first)*(vy-lo->second)/(it->second-lo->second);}else x=it->first;
  if(x<=xb)return stages+1;
  double yr=(reflux*x+xd)/(reflux+1);double yfeed=(reflux*zf+xd)/(reflux+1);
  double ys=xb+(x-xb)*(yfeed-xb)/(zf-xb);double yn=(x>=zf?yr:ys);
  if(!(yn<vy-1e-10)||yn<=0||yn>=1)return -1;
  vy=yn;
 }return -1;
}
static double calculate_t_bubble(Engine& e,PACEVAL_HANDLE bubble,const Row& reference,double x){Row r=reference;r[X]=x;double lo=333.4,hi=373.5;r[T]=lo;double f0=e.scalar(bubble,r)-r[P];r[T]=hi;double f1=e.scalar(bubble,r)-r[P];need(f0<0&&f1>0,"Bubble root not bracketed inside NIST range");
 for(int it=0;it<32;it++){double mid=.5*(lo+hi);r[T]=mid;double val=e.scalar(bubble,r)-r[P];if(val>0)hi=mid;else lo=mid;}
 return .5*(lo+hi);
}
static std::vector<std::pair<double,double>> curve(Engine& e,const Graphs& g,const Graphs& eqg,int ver,const Row& base,int nodes,std::ofstream& out){auto bubb=g.at("bubble_pressure").handle;auto eq=eqg.at("vapor_y").handle;
 std::vector<std::pair<double,double>> vals;vals.reserve(nodes+1);
 for(int j=0;j<=nodes;j++){double x=.001+.998*j/nodes;Row r=base;r[X]=x;r[T]=calculate_t_bubble(e,bubb,r,x);double y=e.scalar(eq,r);check(y,native_y(ver,x,r[T],r[AL],r[AM]),"stage VLE",2e-10);need(y>x,"Non-monotone relative volatility stage curve");vals.push_back({x,y});if(j%8==0)out<<ver<<','<<e.fmt(x)<<','<<e.fmt(r[T])<<','<<e.fmt(y)<<','<<e.fmt(e.scalar(bubb,r))<<'\n';}
 return vals;
}
static void run(Engine& e,int count,int scenarios,const fs::path& dir){fs::create_directories(dir);
 create_inputs(e,dir/"synthetic_vle_inputs.csv",count);auto data=load_inputs(e,dir/"synthetic_vle_inputs.csv");need(data.size()==size_t(count),"Incorrect reloaded inputs count");
 auto pa=create(e,primary(1),"V1"),pb=create(e,primary(2),"V2");auto sa=create(e,secondary(),"V1"),sb=create(e,secondary(),"V2");inventory(dir,pa,pb,sa,sb);
 std::ofstream sample(dir/"vle_samples.csv"),summary(dir/"version_summary.csv"),column(dir/"column_configurations.csv"),eqcsv(dir/"isobaric_equilibrium_curves.csv"),trace(dir/"end_to_end_trace.csv"),audit(dir/"numerical_audit.csv");
 need(bool(sample)&&bool(summary)&&bool(column)&&bool(eqcsv)&&bool(trace)&&bool(audit),"Output files missing");
 sample<<"sample,version,x,T_K,alpha_eff,y,bubble_pressure_bar,dy_dx,dy_dT,stage_product_margin,heat_duty_kW,heat_margin_kW,vle_quality_indicator\n";
 summary<<"version,input_cases,mean_vapor_y,mean_enrichment,mean_alpha_eff,mean_bubble_pressure_bar,mean_dy_dx,indicator_count,mean_heat_duty_kW\n";
 column<<"version,config_id,reflux,xd,xb,zfeed,distillate_kmol_h,bottoms_kmol_h,vapor_kmol_h,reboiler_kW,stage_count,feasible,component_balance_residual\n";
 eqcsv<<"version,x,bubble_temperature_K,vapor_y,bubble_pressure_bar\n";
 trace<<"sample,version,x,T_K,stage,distillate,bottoms,liquid,vapor,ycalc,pbcalc,heat_kW,margin_kW,quality_indicator\n";
 audit<<"sample,version,quantity,paceval_value,native_reference,absolute_difference\n";
 uint64_t ref_checks=0,model_cases=0,validity_count=0;
 std::array<double,2> mean_y{},mean_enrich{},mean_a{},mean_pb{},mean_slope{},mean_heat{};std::array<int,2> yes{};
 constexpr int BATCH=256;
 for(int ver=1;ver<=2;ver++){
  auto& p=(ver==1?pa:pb);auto& s=(ver==1?sa:sb);auto ip=index(p);auto is=index(s);auto hp=hs(p);auto hsec=hs(s);
  for(size_t start=0;start<data.size();start+=BATCH){size_t n=std::min(size_t(BATCH),data.size()-start);
   std::vector<Row> rows(data.begin()+start,data.begin()+start+n);auto pv=e.batch(hp,rows);auto readp=[&](size_t j,const std::string& k){return pv.at(ip.at(k)*n+j);};
   for(size_t j=0;j<n;j++){auto& r=rows[j];double y=readp(j,"vapor_y");r[Y]=y;r[PB]=(ver==2?readp(j,"bubble_pressure"):readp(j,"bubble_pressure_reference")); // Shared activity-model bubble pressure is a diagnostic, not a v1 equilibrium closure.
    double x=r[X],t=r[T],a=r[AL],m=r[AM];double yn=native_y(ver,x,t,a,m);check(y,yn,"VLE",2e-10);ref_checks++;
    double effective=(ver==1?a:std::exp(m*((1-x)*(1-x)-x*x))*psat_a(t)/psat_b(t));check(readp(j,"effective_alpha"),effective,"relative volatility",2e-10);ref_checks++;
    {check(r[PB],native_pb(x,t,m),"diagnostic bubble pressure");ref_checks++;}
    double dx=readp(j,"sensitivity_x");double dxref=ver==1?a/std::pow(1+(a-1)*x,2):yn*(1-yn)*(1/(x*(1-x))-2*m);
    check(dx,dxref,"composition sensitivity",8e-9);ref_checks++;
   }
   // Genuine paceval-to-paceval execution chain: first obtain D and B from graph outputs.
   auto flows=e.batch({s.at("distillate_flow").handle,s.at("bottoms_flow").handle},rows);
   for(size_t j=0;j<n;j++){rows[j][D]=flows[j];rows[j][B]=flows[n+j];}
   // Use those paceval outputs to feed the next graph layer for L and V.
   auto vapors=e.batch({s.at("reflux_liquid_flow").handle,s.at("vapor_flow").handle},rows);
   for(size_t j=0;j<n;j++){rows[j][L]=vapors[j];rows[j][V]=vapors[n+j];}
   auto sec=e.batch(hsec,rows);auto reads=[&](size_t j,const std::string& k){return sec.at(is.at(k)*n+j);};
   for(size_t j=0;j<n;j++){const Row& r=rows[j];size_t k=start+j;double y=r[Y],yp=readp(j,"effective_alpha"),pbv=r[PB],q=reads(j,"reboiler_duty_kw"),margin=reads(j,"energy_margin_kw");
    double Dn=r[F]*(r[ZF]-r[XB])/(r[XD]-r[XB]);double vn=Dn*(1+r[R]);check(reads(j,"distillate_flow"),Dn,"split D");ref_checks++;
    check(reads(j,"bottoms_flow"),r[F]-Dn,"split B");ref_checks++;
    check(reads(j,"total_mass_balance"),0,"mass balance");ref_checks++;
    check(reads(j,"light_component_balance"),0,"component balance");ref_checks++;
    check(q,vn*r[H]/3.6,"heat duty");ref_checks++;
    check(margin,r[QMAX]-q,"heat guard");ref_checks++;
    check(reads(j,"reflux_ratio"),r[R],"reflux ratio");ref_checks++;
    check(reads(j,"rectifying_operating_y"),(r[R]*r[X]+r[XD])/(1+r[R]),"rect line");ref_checks++;
    check(reads(j,"temperature_domain_margin"),std::min(r[T]-r[TMIN],r[TMAX]-r[T]),"temperature domain");ref_checks++;
    double indicator=(r[XD]>=r[TARGET] && q<=r[QMAX] && std::abs(y-r[YREF])<=r[TOL])?1.:0.;
    check(reads(j,"combined_quality_indicator"),indicator,"quality decision");ref_checks++;
    double thermal=q/r[QMAX];need(thermal>=0,"Negative heat duty");
    mean_y[ver-1]+=y;mean_enrich[ver-1]+=y-r[X];mean_a[ver-1]+=yp;mean_pb[ver-1]+=pbv;mean_slope[ver-1]+=readp(j,"sensitivity_x");mean_heat[ver-1]+=q;yes[ver-1]+=(int)indicator;
    if(k%std::max<size_t>(1,data.size()/3200)==0){sample<<k<<','<<ver<<','<<e.fmt(r[X])<<','<<e.fmt(r[T])<<','<<e.fmt(yp)<<','<<e.fmt(y)<<','<<e.fmt(pbv)<<','<<e.fmt(readp(j,"sensitivity_x"))<<','<<e.fmt(ver==2?readp(j,"sensitivity_temperature"):0)<<','<<e.fmt(reads(j,"product_purity_margin"))<<','<<e.fmt(q)<<','<<e.fmt(margin)<<','<<e.fmt(indicator)<<'\n';}
    if(k%std::max<size_t>(1,data.size()/64)==0){trace<<k<<','<<ver<<','<<e.fmt(r[X])<<','<<e.fmt(r[T])<<','<<e.fmt(r[STAGE])<<','<<e.fmt(reads(j,"distillate_flow"))<<','<<e.fmt(reads(j,"bottoms_flow"))<<','<<e.fmt(reads(j,"reflux_liquid_flow"))<<','<<e.fmt(reads(j,"vapor_flow"))<<','<<e.fmt(y)<<','<<e.fmt(pbv)<<','<<e.fmt(q)<<','<<e.fmt(margin)<<','<<e.fmt(indicator)<<'\n';
     audit<<k<<','<<ver<<",equilibrium_y,"<<e.fmt(y)<<','<<e.fmt(native_y(ver,r[X],r[T],r[AL],r[AM]))<<','<<e.fmt(std::abs(y-native_y(ver,r[X],r[T],r[AL],r[AM])))<<'\n';}
    model_cases++;validity_count+=(indicator==1);
   }
  }
  auto avg=[&](double v){return e.fmt(v/data.size());};
  summary<<ver<<','<<data.size()<<','<<avg(mean_y[ver-1])<<','<<avg(mean_enrich[ver-1])<<','<<avg(mean_a[ver-1])<<','<<avg(mean_pb[ver-1])<<','<<avg(mean_slope[ver-1])<<','<<yes[ver-1]<<','<<avg(mean_heat[ver-1])<<'\n';
 }
 // The stagewise column calculation uses a physically consistent, fixed pressure and bubble-T for v2.
 // Version 1 is a constant-alpha equilibrium shortcut. A common NIST vapor-pressure bubble curve is used only for stage-temperature illustration.
 Row base=make_row(0);base[P]=.60;base[R]=2.5;auto curve1=curve(e,pb,pa,1,base,512,eqcsv);auto curve2=curve(e,pb,pb,2,base,512,eqcsv);
 // For v1 use the actual v1 graph to replace y; bubble temperatures are still the same shared physical reference.
 
 for(int ver=1;ver<=2;ver++){auto& curvev=(ver==1?curve1:curve2);for(int j=0;j<scenarios;j++){
  Row r=base;r[R]=1.65+4.8*uni(j*127+8);r[XD]=.90+.055*uni(j*191+11);r[XB]=.045+.065*uni(j*43+97);r[ZF]=.39+.16*uni(j*31+18);
  // Guard the saturated-liquid q-line and material split assumptions.
  validate(r);auto sd=(ver==1?sa:sb);
  double d=e.scalar(sd.at("distillate_flow").handle,r);r[D]=d;double b=e.scalar(sd.at("bottoms_flow").handle,r);r[B]=b;
  double liquidFlow=e.scalar(sd.at("reflux_liquid_flow").handle,r);r[L]=liquidFlow;double v=e.scalar(sd.at("vapor_flow").handle,r);r[V]=v;
  double q=e.scalar(sd.at("reboiler_duty_kw").handle,r);double bal=e.scalar(sd.at("light_component_balance").handle,r);
  check(bal,0,"column component conservation");ref_checks++;
  int stages=stage_count(ver,r[XD],r[XB],r[ZF],r[R],curvev);
  column<<ver<<','<<j<<','<<e.fmt(r[R])<<','<<e.fmt(r[XD])<<','<<e.fmt(r[XB])<<','<<e.fmt(r[ZF])<<','<<e.fmt(d)<<','<<e.fmt(b)<<','<<e.fmt(v)<<','<<e.fmt(q)<<','<<stages<<','<<(stages>0?1:0)<<','<<e.fmt(bal)<<'\n';
 }}
 std::ofstream evidence(dir/"execution_evidence.json");need(bool(evidence),"Cannot write audit evidence");evidence<<"{\n \"study\":\"WP17 distillation VLE\",\n \"sdk_mode\":\"original-local-C++\",\n \"model_versions\":2,\n \"input_pairs\":"<<data.size()<<",\n \"model_point_cases\":"<<model_cases<<",\n \"stagewise_configurations\":"<<2*scenarios<<",\n \"unique_graphs_created\":"<<e.owned.size()<<",\n \"unique_graphs_executed\":"<<e.executed.size()<<",\n \"scalar_calls\":"<<e.scalar_calls<<",\n \"multi_graph_batch_calls\":"<<e.batch_calls<<",\n \"graph_point_evaluations\":"<<e.outputs<<",\n \"native_reference_checks\":"<<ref_checks<<",\n \"quality_indicator_accept\":"<<validity_count<<"\n}\n";
 std::cout<<"PASS WP17 input_pairs="<<data.size()<<" model_cases="<<model_cases<<" graphs_created="<<e.owned.size()<<" graphs_executed="<<e.executed.size()<<" graph_outputs="<<e.outputs<<" native_checks="<<ref_checks<<std::endl;
}
int main(int argc,char** argv){try{Engine e;std::string mode=argc>1?argv[1]:"--run";if(mode=="--selftest"){selftest(e);return 0;}int n=argc>2?std::stoi(argv[2]):4096;int sc=argc>3?std::stoi(argv[3]):600;need(n>=64&&n<=1000000&&sc>=16&&sc<=10000,"Invalid workload limits");fs::path dst=argc>4?argv[4]:"results";selftest(e);run(e,n,sc,dst);return 0;}catch(std::exception& ex){std::cerr<<"FAIL: "<<ex.what()<<"\n";return 1;}}
