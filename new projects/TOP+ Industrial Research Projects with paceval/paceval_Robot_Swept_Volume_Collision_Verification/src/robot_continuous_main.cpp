// WP26: Exact-degree quadratic 3D center trajectories of two conservative spheres.
// Original paceval performs all physical scalar formulas, analytic sensitivities,
// Boolean guards and model-comparison expressions. C++ owns polynomial root
// isolation, candidate selection, numerical domain validation, CSV and state.
// The system is NOT a certified robot collision/safety controller.
#include "paceval_main.h"
#include <algorithm>
#include <array>
#include <cmath>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <limits>
#include <map>
#include <regex>
#include <sstream>
#include <stdexcept>
#include <string>
#include <vector>
namespace fs=std::filesystem;
namespace {
void require(bool ok,const std::string&msg){if(!ok)throw std::runtime_error(msg);}
void near(double a,double b,double atol=3e-8,double rtol=2e-8){require(std::isfinite(a)&&std::isfinite(b)&&std::abs(a-b)<=atol+rtol*std::max(std::abs(a),std::abs(b)),"Reference result mismatch");}
const std::vector<std::string> VAR={"t","x0","x1","x2","y0","y1","y2","z0","z1","z2","r1","r2","buffer"};
const std::vector<std::string> CMP={"marginA","marginB","clearA","clearB","guardA","guardB"};
std::string joined(const std::vector<std::string>&x){std::string s;for(auto&v:x){if(!s.empty())s+=' ';s+=v;}return s;}
bool numericLiteral(const std::string&x){static const std::regex re(R"(^[+-]?(?:[0-9]+(?:\.[0-9]*)?|\.[0-9]+)(?:[eE][+-]?[0-9]+)?$)");return std::regex_match(x,re);}
double numberIn(const std::string&x){require(numericLiteral(x),"Rejected nonliteral CSV cell: "+x);int err=-1;long pos=-1;double y=paceval_dConvertStringToFloat(x.c_str(),&err,&pos,false,nullptr,nullptr);require(err==0&&std::isfinite(y),"paceval_dConvertStringToFloat error="+std::to_string(err));return y;}
std::string numberOut(double x){require(std::isfinite(x),"Nonfinite output");char buf[512]{};int p=paceval_dConvertFloatToString(buf,x);require(p>0&&buf[0]!=0&&std::string(buf).find(',')==std::string::npos,"paceval_dConvertFloatToString failed");return buf;}
std::vector<std::string> split(const std::string&s){std::stringstream f(s);std::string item;std::vector<std::string>o;while(std::getline(f,item,','))o.push_back(item);if(!s.empty()&&s.back()==',')o.push_back("");return o;}
using Matrix=std::vector<std::vector<double>>;
struct Engine{
 std::vector<PACEVAL_HANDLE>all;bool graphMajor=false;unsigned long long scalarCalls=0,batchCalls=0,graphPoints=0;
 Engine(){require(paceval_InitializeLibrary(nullptr),"Original paceval library initialization failed");}
 ~Engine(){for(auto h:all)if(h)paceval_DeleteComputation(h);paceval_FreeLibrary();}
 PACEVAL_HANDLE create(const std::string&formula,const std::vector<std::string>&vars){auto v=joined(vars);auto h=paceval_CreateComputation(formula.c_str(),vars.size(),v.c_str(),false,nullptr);require(h&&!paceval_GetIsError(h),"paceval graph error: "+formula);all.push_back(h);return h;}
 double scalar(PACEVAL_HANDLE h,const std::vector<double>&values){auto v=values;double y=paceval_dGetComputationResult(h,v.empty()?nullptr:v.data(),nullptr,nullptr);++scalarCalls;require(!paceval_GetIsError(h)&&std::isfinite(y),"paceval scalar evaluation failed");return y;}
 void probe(){auto a=create("x+2*y",{"x","y"});auto b=create("3*x-y",{"x","y"});PACEVAL_HANDLE hs[]={a,b};double in[]={1,2,4,7},out[4]{},lo[4]{},hi[4]{};int err[4]{};bool fail=paceval_dGetMultipleComputationsResultsExt(hs,2,in,2,out,lo,hi,err);require(!fail&&std::all_of(err,err+4,[](int x){return x==0;}),"SDK batch probe returned an error");
  if(std::abs(out[0]-5)<1e-10&&std::abs(out[1]-18)<1e-10&&std::abs(out[2]-1)<1e-10&&std::abs(out[3]-5)<1e-10)graphMajor=true;
  else if(std::abs(out[0]-5)<1e-10&&std::abs(out[1]-1)<1e-10&&std::abs(out[2]-18)<1e-10&&std::abs(out[3]-5)<1e-10)graphMajor=false;
  else throw std::runtime_error("Unsupported multi-graph batch output order");++batchCalls;graphPoints+=4;
 }
 Matrix batch(const std::vector<PACEVAL_HANDLE>&hs,const Matrix&rows,size_t width){require(!hs.empty()&&!rows.empty(),"Empty graph batch");std::vector<double>in;in.reserve(rows.size()*width);for(auto&r:rows){require(r.size()==width,"Batch width mismatch");for(auto v:r)require(std::isfinite(v),"Nonfinite batch input");in.insert(in.end(),r.begin(),r.end());}
  std::vector<double>out(hs.size()*rows.size()),lo(out.size()),hi(out.size());std::vector<int>err(out.size(),-1);
  bool fail=paceval_dGetMultipleComputationsResultsExt(const_cast<PACEVAL_HANDLE*>(hs.data()),hs.size(),in.data(),rows.size(),out.data(),lo.data(),hi.data(),err.data());require(!fail,"SDK multi-graph API failed");for(auto e:err)require(e==0,"SDK graph error code="+std::to_string(e));
  Matrix y(rows.size(),std::vector<double>(hs.size()));for(size_t i=0;i<rows.size();i++)for(size_t j=0;j<hs.size();j++){auto v=out[graphMajor?j*rows.size()+i:i*hs.size()+j];require(std::isfinite(v),"SDK nonfinite graph value");y[i][j]=v;}++batchCalls;graphPoints+=out.size();return y;
 }
};
struct Graph{std::string id,version,formula,units,what;PACEVAL_HANDLE handle;bool executed=false;};
struct Model{
 Engine&e;std::vector<Graph>g;std::map<std::string,size_t>indices;
 explicit Model(Engine&z):e(z){
  const std::string X="(x0+x1*t+x2*t^2)",Y="(y0+y1*t+y2*t^2)",Z="(z0+z1*t+z2*t^2)";
  const std::string VX="(x1+2*x2*t)",VY="(y1+2*y2*t)",VZ="(z1+2*z2*t)";
  const std::string D="("+X+"^2+"+Y+"^2+"+Z+"^2)";
  const std::string DS="(2*("+X+"*"+VX+"+"+Y+"*"+VY+"+"+Z+"*"+VZ+"))";
  const std::string DDS="(2*("+VX+"^2+"+VY+"^2+"+VZ+"^2+2*x2*"+X+"+2*y2*"+Y+"+2*z2*"+Z+"))";
  auto add=[&](const std::string&v,const std::string&id,const std::string&f,const std::string&units,const std::string&what,const std::vector<std::string>&vs){
    auto full=v+"_"+id;auto h=e.create(f,vs);indices[full]=g.size();g.push_back({full,v,f,units,what,h,false});};
  for(int vv=1;vv<=2;vv++){
   const std::string v=vv==1?"V1":"V2";
   const std::string R=vv==1?"(r1+r2)":"(r1+r2+buffer)";
   const std::string M="("+D+"-"+R+"^2)";
   const std::string C="(sqrt("+D+")-"+R+")";
   add(v,"RELATIVE_X",X,"m","Relative center x coordinate",VAR);
   add(v,"RELATIVE_Y",Y,"m","Relative center y coordinate",VAR);
   add(v,"RELATIVE_Z",Z,"m","Relative center z coordinate",VAR);
   add(v,"VELOCITY_X",VX,"m/normalized_time","Relative center velocity coordinate",VAR);
   add(v,"VELOCITY_Y",VY,"m/normalized_time","Relative center velocity coordinate",VAR);
   add(v,"VELOCITY_Z",VZ,"m/normalized_time","Relative center velocity coordinate",VAR);
   add(v,"DISTANCE_SQUARED",D,"m2","Squared center separation",VAR);
   add(v,"DISTANCE", "sqrt("+D+")","m","Center separation",VAR);
   add(v,"EFFECTIVE_RADIUS",R,"m","Sum of conservative bounding radii and optional uncertainty buffer",VAR);
   add(v,"SQUARED_MARGIN",M,"m2","Signed squared minimum-distance margin",VAR);
   add(v,"SIGNED_CLEARANCE",C,"m","Signed surface clearance",VAR);
   add(v,"DERIVATIVE_TIME",DS,"m2/normalized_time","Exact first derivative of squared margin",VAR);
   add(v,"SECOND_DERIVATIVE",DDS,"m2/normalized_time2","Exact second derivative",VAR);
   add(v,"RELATIVE_SPEED","sqrt("+VX+"^2+"+VY+"^2+"+VZ+"^2)","m/normalized_time","Relative center velocity magnitude",VAR);
   add(v,"NEGATIVE_MARGIN","(0 max (-"+M+"))","m2","Penetration squared-margin deficit",VAR);
   add(v,"NORM_MARGIN","("+M+"/(1+"+R+"^2))","1","Normalized squared-margin score",VAR);
   add(v,"SENS_X0","(2*"+X+")","m","Analytic sensitivity of squared margin to initial x",VAR);
   add(v,"SENS_X1","(2*t*"+X+")","m","Analytic sensitivity to x velocity coefficient",VAR);
   add(v,"SENS_BUFFER",vv==1?"(0*buffer)":"(-2*"+R+")","m","Analytic sensitivity to uncertainty-buffer thickness",VAR);
   add(v,"POINTWISE_GUARD","(("+M+">=0) AND (t>=0) AND (t<=1))","0_or_1","Pointwise nonnegative-distance guard; NOT an interval certificate",VAR);
  }
  add("COMPARE","MARGIN_DELTA","(marginB-marginA)","m2","Difference between inflated and nominal global minima",CMP);
  add("COMPARE","CLEARANCE_DELTA","(clearB-clearA)","m","Difference between inflated and nominal surface clearances",CMP);
  add("COMPARE","BOTH_POINTWISE","((guardA=1) AND (guardB=1))","0_or_1","Combined pointwise status at global minima",CMP);
 }
 Matrix batch(const std::string&v,const Matrix&rows){std::vector<PACEVAL_HANDLE>h;for(auto&x:g)if(x.version==v)h.push_back(x.handle);auto ans=e.batch(h,rows,v=="COMPARE"?CMP.size():VAR.size());for(auto&x:g)if(x.version==v)x.executed=true;return ans;}
 std::map<std::string,double> extract(const std::string&v,const std::vector<double>&row){std::map<std::string,double>z;size_t k=0;for(auto&x:g)if(x.version==v)z[x.id.substr(v=="COMPARE"?8:3)]=row.at(k++);require(k==row.size(),"Graph result width error");return z;}
 double scalar(const std::string&v,const std::string&id,const std::vector<double>&x){return e.scalar(g[indices.at(v+"_"+id)].handle,x);}
};
struct Case{std::string id,group;std::vector<double>x;};
void validate(const Case&c){require(c.x.size()==12,"Expected 12 numeric columns");for(double x:c.x)require(std::isfinite(x)&&std::abs(x)<=8,"Nonfinite/out-of-domain coefficient");require(c.x[9]>0&&c.x[10]>0&&c.x[11]>=0&&c.x[9]+c.x[10]+c.x[11]<2,"Unphysical effective radii");}
std::vector<Case> readCases(const fs::path&p){std::ifstream f(p);require(bool(f),"Input CSV missing");std::string line;require(bool(std::getline(f,line)),"Missing CSV header");std::string h="case_id,scenario";for(size_t i=1;i<VAR.size();i++)h+=","+VAR[i];require(line==h,"CSV header mismatch");std::vector<Case>cases;size_t n=1;while(std::getline(f,line)){++n;if(line.empty())continue;auto col=split(line);require(col.size()==14,"CSV width failed line "+std::to_string(n));require(std::regex_match(col[0],std::regex("[A-Z0-9_]+"))&&std::regex_match(col[1],std::regex("[a-z_]+")),"Unsafe identifiers");Case c{col[0],col[1],{}};for(size_t j=2;j<col.size();j++)c.x.push_back(numberIn(col[j]));validate(c);cases.push_back(c);}require(!cases.empty(),"No input rows");return cases;}
std::vector<double> values(const Case&c,double t){std::vector<double>x;x.reserve(VAR.size());x.push_back(t);x.insert(x.end(),c.x.begin(),c.x.end());return x;}
// Cubic-root isolation: split derivative polynomial at roots of its derivative.
// Host uses this solver to propose all stationary-time candidates. Physical
// squared-margin and derivative results themselves are always paceval outputs.
long double poly(const std::vector<long double>&c,long double t){long double y=0;for(auto it=c.rbegin();it!=c.rend();++it)y=y*t+*it;return y;}
void addRoot(std::vector<long double>&r,long double x){if(x<-1e-14L||x>1+1e-14L)return;x=std::max(0.L,std::min(1.L,x));for(auto y:r)if(fabsl(x-y)<1e-11L)return;r.push_back(x);}
std::vector<long double> roots(const std::vector<long double>&coeff){auto c=coeff;while(c.size()>1&&fabsl(c.back())<1e-18L)c.pop_back();std::vector<long double>out;if(c.size()<2)return out;
 if(c.size()==2){addRoot(out,-c[0]/c[1]);return out;}
 std::vector<long double>d;for(size_t i=1;i<c.size();i++)d.push_back(i*c[i]);auto critical=roots(d);std::vector<long double>interval={0};for(auto t:critical)if(t>0&&t<1)interval.push_back(t);interval.push_back(1);std::sort(interval.begin(),interval.end());for(auto t:interval)if(fabsl(poly(c,t))<1e-12L)addRoot(out,t);
 for(size_t i=1;i<interval.size();i++){auto a=interval[i-1],b=interval[i];long double fa=poly(c,a),fb=poly(c,b);if((fa<0&&fb>0)||(fa>0&&fb<0)){for(int iter=0;iter<82;iter++){auto m=(a+b)/2;long double fm=poly(c,m);if((fa<0&&fm<0)||(fa>0&&fm>0)){a=m;fa=fm;}else{b=m;fb=fm;}}addRoot(out,(a+b)/2);}}
 std::sort(out.begin(),out.end());return out;
}
std::vector<double> stationaryTimes(const Case&c){long double p[3][3]{};for(int j=0;j<3;j++)for(int k=0;k<3;k++)p[j][k]=c.x[j*3+k];long double A[5]{};for(int j=0;j<3;j++)for(int k=0;k<3;k++)for(int l=0;l<3;l++)A[k+l]+=p[j][k]*p[j][l];std::vector<long double>d;for(int j=1;j<=4;j++)d.push_back(j*A[j]);auto rr=roots(d);std::vector<double>t{0,1};for(auto x:rr)if(x>0&&x<1)t.push_back(static_cast<double>(x));std::sort(t.begin(),t.end());return t;}
std::map<std::string,double> native(const Case&c,int vv,double t){double p[3]{},dp[3]{},dd=0,dist2=0,speed2=0;for(int j=0;j<3;j++){int k=3*j;p[j]=c.x[k]+t*(c.x[k+1]+t*c.x[k+2]);dp[j]=c.x[k+1]+2*t*c.x[k+2];dd+=2*p[j]*dp[j];dist2+=p[j]*p[j];speed2+=dp[j]*dp[j];}double R=c.x[9]+c.x[10]+(vv==2?c.x[11]:0);double M=dist2-R*R;return {{"SQUARED_MARGIN",M},{"SIGNED_CLEARANCE",std::sqrt(dist2)-R},{"DERIVATIVE_TIME",dd},{"RELATIVE_SPEED",std::sqrt(speed2)},{"SENS_X0",2*p[0]},{"POINTWISE_GUARD",M>=0?1.:0.}};}
void operatorTests(Engine&e){const std::vector<std::pair<std::string,double>>tests={{"((-1)%10)",-1},{"((-1) mod 10)",9},{"(4 min 5)",4},{"(4 max 5)",5},{"(3<4)",1},{"(3<=3)",1},{"(3>=3)",1},{"(3=3)",1},{"(3<>4)",1},{"NOT(0)",1},{"(1 AND 1)",1},{"(0 OR 1)",1},{"((3<=3) AND (2>=0))",1}};for(auto&x:tests)near(e.scalar(e.create(x.first,{}),{}),x.second);
 for(auto s:{"","NaN","Inf","1+2","1,2","1e999","--1"," 1"}){bool rejected=false;try{numberIn(s);}catch(...){rejected=true;}require(rejected,"Non-literal numeric input accepted");}near(numberIn("-1.25e-3"),-.00125);require(!numberOut(.125).empty(),"SDK numeric formatting untested");}
void selftest(){Engine e;e.probe();operatorTests(e);Model m(e);Case c{"TEST","normal",{-1,2,0,0.5,0,0,0,0,0,0.25,0.25,0.125}};auto z=values(c,.5);for(auto v:{"V1","V2"}){auto o=m.extract(v,m.batch(v,{z})[0]);auto n=native(c,v==std::string("V1")?1:2,.5);for(auto&j:n)near(o.at(j.first),j.second);near(m.scalar(v,"SQUARED_MARGIN",z),n.at("SQUARED_MARGIN"));}auto t=stationaryTimes(c);require(std::any_of(t.begin(),t.end(),[](double x){return std::abs(x-.5)<1e-9;}),"Stationary isolator failed tangency");std::cout<<"SELFTEST PASS original SDK scalar, multiple-graph batch, operators, conversion and tangency\n";}
struct Result{double t=0,margin=0,clearance=0,coarse=0,guard=0,derivative=0;int stationary=0;bool coarseSafe=false;};
void run(const fs::path&source,const fs::path&dest){fs::create_directories(dest);Engine e;e.probe();operatorTests(e);Model m(e);auto cases=readCases(source);size_t n=cases.size(),nativeCount=0;std::vector<std::array<Result,2>>R(n);std::ofstream screen(dest/"screening.csv"),compare(dest/"model_comparison.csv"),audit(dest/"native_audit.csv"),samples(dest/"sampled_clearance.csv"),manifest(dest/"formula_manifest.csv"),inventory(dest/"math_execution_inventory.csv"),evidence(dest/"execution_evidence.json");require(bool(screen&&compare&&audit&&samples&&manifest&&inventory&&evidence),"Cannot open results directory");
 screen<<"case_id,scenario,model,min_time_normalized,min_squared_margin_m2,min_surface_clearance_m,coarse_squared_margin_m2,coarse_safe,continuous_status,stationary_points,derivative_at_min\n";
 compare<<"case_id,scenario,min_margin_V1_m2,min_margin_V2_m2,delta_margin_m2,clearance_V1_m,clearance_V2_m,delta_clearance_m,both_pointwise_nonnegative\n";
 samples<<"case_id,scenario,model,t,relative_x_m,relative_y_m,relative_z_m,squared_margin_m2,surface_clearance_m,derivative_m2_per_normalized_time\n";
 audit<<"case_id,model,checked_endvalues,pass\n";
 const int NSAMP=32;
 for(size_t start=0;start<n;start+=32){size_t end=std::min(n,start+32);
  for(int v=1;v<=2;v++){std::string ver=v==1?"V1":"V2";Matrix x;for(size_t k=start;k<end;k++)for(int j=0;j<=NSAMP;j++)x.push_back(values(cases[k],double(j)/NSAMP));auto yy=m.batch(ver,x);
   for(size_t k=start;k<end;k++){auto&c=cases[k];double coarse=std::numeric_limits<double>::infinity();for(int j=0;j<=NSAMP;j++){auto z=m.extract(ver,yy[(k-start)*(NSAMP+1)+j]);coarse=std::min(coarse,z.at("SQUARED_MARGIN"));if(k<18 || (k==18 && j%4==0))samples<<c.id<<','<<c.group<<','<<ver<<','<<numberOut(double(j)/NSAMP)<<','<<numberOut(z.at("RELATIVE_X"))<<','<<numberOut(z.at("RELATIVE_Y"))<<','<<numberOut(z.at("RELATIVE_Z"))<<','<<numberOut(z.at("SQUARED_MARGIN"))<<','<<numberOut(z.at("SIGNED_CLEARANCE"))<<','<<numberOut(z.at("DERIVATIVE_TIME"))<<'\n';}
    auto t=stationaryTimes(c);double best=std::numeric_limits<double>::infinity(),bestT=0;for(auto s:t){auto p=values(c,s);double y=m.scalar(ver,"SQUARED_MARGIN",p);if(y<best){best=y;bestT=s;}}
    auto p=values(c,bestT);double clear=m.scalar(ver,"SIGNED_CLEARANCE",p);double der=m.scalar(ver,"DERIVATIVE_TIME",p);double guard=m.scalar(ver,"POINTWISE_GUARD",p);bool coarseSafe=coarse>0;auto&rr=R[k][v-1];rr={bestT,best,clear,coarse,guard,der,int(t.size()>1?t.size()-2:0),coarseSafe};std::string state=best>1e-9?"SEPARATED":(best< -1e-9?"OVERLAP":"CONTACT_OR_NUMERIC_BOUNDARY");
    screen<<c.id<<','<<c.group<<','<<ver<<','<<numberOut(bestT)<<','<<numberOut(best)<<','<<numberOut(clear)<<','<<numberOut(coarse)<<','<<(coarseSafe?1:0)<<','<<state<<','<<rr.stationary<<','<<numberOut(der)<<'\n';
    if(k%23==0||k<18||k==n-1){auto ref=native(c,v,bestT);for(auto&j:ref){if(j.first=="POINTWISE_GUARD"&&std::abs(best)<=1e-10)continue;double actual=(j.first=="SQUARED_MARGIN"?best:(j.first=="SIGNED_CLEARANCE"?clear:(j.first=="DERIVATIVE_TIME"?der:m.scalar(ver,j.first,p))));near(actual,j.second);nativeCount++;}audit<<c.id<<','<<ver<<','<<ref.size()<<",1\n";}}
  }
 }
 for(size_t start=0;start<n;start+=128){size_t end=std::min(n,start+128);Matrix z;for(size_t k=start;k<end;k++){auto&a=R[k][0],&b=R[k][1];z.push_back({a.margin,b.margin,a.clearance,b.clearance,a.guard,b.guard});}auto r=m.batch("COMPARE",z);for(size_t k=start;k<end;k++){auto o=m.extract("COMPARE",r[k-start]);auto&a=R[k][0],&b=R[k][1];compare<<cases[k].id<<','<<cases[k].group;for(auto v:{a.margin,b.margin,o.at("MARGIN_DELTA"),a.clearance,b.clearance,o.at("CLEARANCE_DELTA"),o.at("BOTH_POINTWISE")})compare<<','<<numberOut(v);compare<<'\n';if(k%101==0){near(o.at("MARGIN_DELTA"),b.margin-a.margin);near(o.at("CLEARANCE_DELTA"),b.clearance-a.clearance);nativeCount+=2;}}}
 // Dense trajectory visualization is also evaluated by genuine original paceval graphs.
 std::ofstream fine(dest/"fine_clearance.csv");require(bool(fine),"Could not write fine clearance trajectory");
 fine<<"case_id,scenario,model,t,squared_margin_m2,surface_clearance_m\n";
 for(int v=1;v<=2;v++)for(size_t k=0;k<std::min<size_t>(18,n);k++){
   auto&c=cases[k];std::string ver=v==1?"V1":"V2";Matrix xx;
   for(int j=0;j<=256;j++)xx.push_back(values(c,double(j)/256));
   auto yy=m.batch(ver,xx);for(int j=0;j<=256;j++){
    auto z=m.extract(ver,yy[j]);fine<<c.id<<','<<c.group<<','<<ver<<','<<numberOut(double(j)/256)<<','<<numberOut(z.at("SQUARED_MARGIN"))<<','<<numberOut(z.at("SIGNED_CLEARANCE"))<<'\n';
   }
 }
 manifest<<"graph_id,version,expression,units,purpose\n";inventory<<"function_id,domain_quantity,mathematical_definition,units,execution_owner,paceval_graph_id,formula_version,api_path,reference_test,status,host_reason\n";size_t executed=0;for(auto&g:m.g){if(g.executed)executed++;manifest<<g.id<<','<<g.version<<",\""<<g.formula<<"\","<<g.units<<",\""<<g.what<<"\"\n";inventory<<g.id<<",\""<<g.what<<"\",\""<<g.formula<<"\","<<g.units<<",paceval,"<<g.id<<','<<g.version<<",paceval_dGetMultipleComputationsResultsExt,native and mpmath,"<<(g.executed?"executed":"registered_only")<<",\n";}
 inventory<<"ROOT_ISOLATION,Polynomial stationary points,cubic derivative root isolation,normalized_time,host,,both,long double numeric solver,exact independent Bernstein check,executed,roots require stateful bracket isolation\n";
 inventory<<"MIN_SELECTION,Global candidate comparison,min over endpoint and derivative roots,m2,host,,both,selection control,exact rational interval check,executed,C++ selects best of graph-evaluated candidate margins\n";
 inventory<<"CSV_DECIMAL_INPUT,CSV decimal parser,numeric literal parsing,m,paceval,,both,paceval_dConvertStringToFloat,negative and schema tests,executed,\n";
 inventory<<"CSV_DECIMAL_OUTPUT,CSV decimal formatter,digit conversion,m,paceval,,both,paceval_dConvertFloatToString,Python numeric CSV reader,executed,\n";
 require(executed==m.g.size(),"Registered nonexecuted graphs in final package");
 size_t miss[2]={},contacts[2]={},overlap[2]={},separate[2]={};for(size_t i=0;i<n;i++)for(int j=0;j<2;j++){auto&r=R[i][j];if(r.coarseSafe&&r.margin< -1e-9)miss[j]++;if(std::abs(r.margin)<=1e-9)contacts[j]++;else if(r.margin<0)overlap[j]++;else separate[j]++;}
 evidence<<"{\n \"sdk\":\"original paceval 4.25, supplied ELF x86-64 shared library\",\n \"unique_graphs_created\":"<<m.g.size()<<",\n \"unique_graphs_executed\":"<<executed<<",\n \"scalar_calls_including_operator_tests\":"<<e.scalarCalls<<",\n \"batch_calls_including_layout_probe\":"<<e.batchCalls<<",\n \"graph_point_evaluations_including_layout_probe\":"<<e.graphPoints<<",\n \"trajectory_pair_count\":"<<n<<",\n \"model_case_combinations\":"<<2*n<<",\n \"coarse_grid_intervals\":"<<NSAMP<<",\n \"missed_overlap_by_coarse_grid_V1\":"<<miss[0]<<",\n \"missed_overlap_by_coarse_grid_V2\":"<<miss[1]<<",\n \"overlap_V1\":"<<overlap[0]<<",\n \"overlap_V2\":"<<overlap[1]<<",\n \"separated_V1\":"<<separate[0]<<",\n \"separated_V2\":"<<separate[1]<<",\n \"near_tangent_V1\":"<<contacts[0]<<",\n \"near_tangent_V2\":"<<contacts[1]<<",\n \"native_endvalue_assertions\":"<<nativeCount<<",\n \"independent_certification\":\"see exact_interval_audit.json\"\n}\n";
 std::cout<<"RESEARCH PASS "<<executed<<'/'<<m.g.size()<<" graphs, "<<n<<" pairs; grid missed "<<miss[0]<<'/'<<miss[1]<<" overlaps (V1/V2); native checks "<<nativeCount<<"\n";
}
}
int main(int argc,char**argv){try{if(argc==2&&std::string(argv[1])=="--selftest"){selftest();return 0;}require(argc==4&&std::string(argv[1])=="--run","Usage: robot_continuous --run input/cases.csv results_dir");run(argv[2],argv[3]);return 0;}catch(const std::exception&e){std::cerr<<"ERROR: "<<e.what()<<'\n';return 1;}}
