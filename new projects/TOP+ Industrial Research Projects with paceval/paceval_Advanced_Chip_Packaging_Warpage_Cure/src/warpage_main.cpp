// WP07: advanced packaging. Original paceval SDK 4.25, genuine persistent graphs.
// The model is an illustrative small-strain, perfectly bonded, three-layer,
// equi-biaxial linear-elastic laminate screening model, NOT a 3D FEM model.
// C++ transports results between graphs, orchestrates time integration, and I/O.
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
void need(bool ok,const std::string& msg){if(!ok)throw std::runtime_error(msg);}
void near(double x,double y,double rel=4e-9,double abs=2e-12){need(std::isfinite(x)&&std::isfinite(y)&&std::abs(x-y)<=abs+rel*std::max(std::abs(x),std::abs(y)),"Numerical mismatch");}
std::string joined(const std::vector<std::string>& names){std::string s;for(auto& n:names){if(!s.empty())s+=" ";s+=n;}return s;}
bool literal(const std::string& s){static const std::regex pat(R"(^[+-]?(?:[0-9]+(?:\.[0-9]*)?|\.[0-9]+)(?:[eE][+-]?[0-9]+)?$)");return std::regex_match(s,pat);}
double parse(const std::string& s){need(literal(s),"Not a finite decimal literal: "+s);int error=-1;long pos=-1;double r=paceval_dConvertStringToFloat(s.c_str(),&error,&pos,false,nullptr,nullptr);need(error==0&&std::isfinite(r),"Invalid SDK numeric conversion: "+s+" code="+std::to_string(error));return r;}
std::string fmt(double v){need(std::isfinite(v),"Cannot output nonfinite value");char b[512]{};int n=paceval_dConvertFloatToString(b,v);need(n>0&&b[0]&&std::string(b).find(',')==std::string::npos,"SDK output conversion failure");return b;}
std::vector<std::string> split(const std::string& row){std::vector<std::string> out;std::stringstream s(row);std::string part;while(std::getline(s,part,','))out.push_back(part);if(!row.empty()&&row.back()==',')out.push_back("");return out;}
using VV=std::vector<std::vector<double>>;
struct Graph{std::string id,version,units,expression,description,stage;PACEVAL_HANDLE handle{};bool used=false;};
struct Engine{
 std::vector<PACEVAL_HANDLE> handles;bool graphMajor=false;uint64_t scalarCalls=0,batchCalls=0,batchGraphPoints=0; 
 Engine(){need(paceval_InitializeLibrary(nullptr),"paceval_InitializeLibrary failed");}
 ~Engine(){for(auto h:handles)if(h)paceval_DeleteComputation(h);paceval_FreeLibrary();}
 PACEVAL_HANDLE add(const std::string& expression,const std::vector<std::string>& vars){auto n=joined(vars);auto h=paceval_CreateComputation(expression.c_str(),vars.size(),n.c_str(),false,nullptr);need(h&&!paceval_GetIsError(h),"Graph creation failed for "+expression);handles.push_back(h);return h;}
 double scalar(PACEVAL_HANDLE h,const std::vector<double>& input){auto v=input;for(double x:v)need(std::isfinite(x),"Invalid graph input");double r=paceval_dGetComputationResult(h,v.data(),nullptr,nullptr);scalarCalls++;need(!paceval_GetIsError(h)&&std::isfinite(r),"Scalar evaluation error");return r;}
 void calibrate(){auto h1=add("x+2*y",{"x","y"}),h2=add("3*x-y",{"x","y"});PACEVAL_HANDLE h[]={h1,h2};double in[]={1,2,4,7},out[4]{},lo[4]{},hi[4]{};int err[4]{};bool failed=paceval_dGetMultipleComputationsResultsExt(h,2,in,2,out,lo,hi,err);need(!failed&&std::all_of(err,err+4,[](int z){return z==0;}),"Batch SDK probe failed");if(std::abs(out[0]-5)<1e-9&&std::abs(out[1]-18)<1e-9&&std::abs(out[2]-1)<1e-9&&std::abs(out[3]-5)<1e-9)graphMajor=true;else if(std::abs(out[0]-5)<1e-9&&std::abs(out[1]-1)<1e-9&&std::abs(out[2]-18)<1e-9&&std::abs(out[3]-5)<1e-9)graphMajor=false;else throw std::runtime_error("Unknown multi-graph layout");batchCalls++;batchGraphPoints+=4;}
 VV multi(const std::vector<PACEVAL_HANDLE>& handles,const VV& rows,size_t nvars){need(!handles.empty()&&!rows.empty(),"Empty batch");std::vector<double> in;in.reserve(rows.size()*nvars);for(const auto& row:rows){need(row.size()==nvars,"Batch width mismatch");for(auto x:row)need(std::isfinite(x),"Nonfinite batch input");in.insert(in.end(),row.begin(),row.end());}
 std::vector<double> out(rows.size()*handles.size()),lo(out.size()),hi(out.size());std::vector<int> err(out.size(),-1);
 // Confirmed SDK convention: a false return means no API error; inspect per-item status.
 bool failed=paceval_dGetMultipleComputationsResultsExt(const_cast<PACEVAL_HANDLE*>(handles.data()),handles.size(),in.data(),rows.size(),out.data(),lo.data(),hi.data(),err.data());need(!failed,"Batch SDK error flag");for(int e:err)need(e==0,"Batch result error code "+std::to_string(e));
 VV result(rows.size(),std::vector<double>(handles.size()));for(size_t j=0;j<rows.size();j++)for(size_t k=0;k<handles.size();k++){size_t idx=graphMajor?k*rows.size()+j:j*handles.size()+k;need(std::isfinite(out[idx]),"Nonfinite batch output");result[j][k]=out[idx];}batchCalls++;batchGraphPoints+=out.size();return result;}
};
const std::vector<std::string> VAR1={"T","Tr","a","gel","beta","H1","H2","H3","E1","E2","E3","N1","N2","N3","C1","C2","C3","W","k1","k2","Ea1","Ea2","Tkin","gE","Wlim","Slim","Rg"};
const std::vector<std::string> VAR2={"P","Q","S","e1","e2","e3","H1","H2","H3"};
const std::vector<std::string> VAR3={"A","B","D","N","M","P","Q","S","e1","e2","e3","H1","H2","H3","W","C1","C2","C3","a","gel","beta"};
const std::vector<std::string> VAR4={"w","s11","s12","s21","s22","s31","s32","Wlim","Slim","a"};
const std::vector<std::string> VAR5={"k1","k2","w1","w2"};
struct Models{
 Engine& e;std::vector<Graph> graphs;std::map<std::string,size_t> ids;
 Models(Engine& ee):e(ee){
 auto add=[&](const std::string& stage,const std::string& id,const std::string& version,const std::string& units,const std::string& expr,const std::string& desc){const auto& names=stage=="S1"?VAR1:stage=="S2"?VAR2:stage=="S3"?VAR3:stage=="S4"?VAR4:VAR5;need(!ids.count(id),"Repeated id");Graph g{id,version,units,expr,desc,stage,e.add(expr,names),false};ids[id]=graphs.size();graphs.push_back(g);};
 const std::string kin1="(k1*exp((-Ea1/Rg)*((1/T)-(1/Tkin))))",kin2="(k2*exp((-Ea2/Rg)*((1/T)-(1/Tkin))))";
 add("S1","KIN1","common","1/s",kin1,"First cure kinetic contribution");
 add("S1","KIN2","common","1/s",kin2,"Autocatalytic kinetic contribution");
 add("S1","CURE_RATE","common","1/s","("+kin1+"+"+kin2+"*a)*(1-a)","Post-gel illustrative cure ODE RHS");
 add("S1","CURE_SENS_A","common","1/s","("+kin2+"*(1-2*a))-"+kin1,"Derivative of degree of cure rate");
 add("S1","EBAR1","common","Pa","E1/(1-N1)","Substrate biaxial modulus");
 add("S1","EBAR2","common","Pa","E2/(1-N2)","Die/bond layer biaxial modulus");
 add("S1","V1_EBAR3","V1","Pa","E3/(1-N3)","Constant encapsulant modulus");
 add("S1","V2_EBAR3","V2","Pa","(E3*(1+gE*(a-gel)))/(1-N3)","Cure-dependent encapsulant modulus proxy");
 add("S1","EIGEN1","common","1","C1*(T-Tr)","Substrate free thermal strain");
 add("S1","EIGEN2","common","1","C2*(T-Tr)","Die/bond layer free thermal strain");
 add("S1","V1_EIGEN3","V1","1","C3*(T-Tr)","Thermal-only encapsulant free strain");
 add("S1","V2_EIGEN3","V2","1","(C3*(T-Tr))-(beta*((a-gel) max 0)/(1-gel))","Post-gel effective cure shrinkage plus thermal strain");
 add("S1","SHRINKAGE","V2","1","(-beta)*((a-gel) max 0)/(1-gel)","Post-gel chemical free shrinkage");
 add("S1","MODULUS_FACTOR","V2","1","1+gE*(a-gel)","Effective cure stiffness multiplier");
 const std::string z2="(H1+H2)",z3="(H1+H2+H3)";
 add("S2","EXTENSION_A","common","N/m","P*H1+Q*H2+S*H3","Laminate extensional stiffness");
 add("S2","COUPLING_B","common","N","(P*H1^2+Q*("+z2+"^2-H1^2)+S*("+z3+"^2-"+z2+"^2))/2","Extension-bending coupling");
 add("S2","BENDING_D","common","N m","(P*H1^3+Q*("+z2+"^3-H1^3)+S*("+z3+"^3-"+z2+"^3))/3","Laminate bending stiffness");
 add("S2","EIGEN_FORCE_N","common","N/m","P*H1*e1+Q*H2*e2+S*H3*e3","Thermal and cure eigenstrain force");
 add("S2","EIGEN_MOMENT_M","common","N","(P*H1^2*e1+Q*("+z2+"^2-H1^2)*e2+S*("+z3+"^2-"+z2+"^2)*e3)/2","Eigenstrain-induced bending moment");
 const std::string den="((A*D)-(B*B))",eps="((D*N-B*M)/"+den+")",curv="((A*M-B*N)/"+den+")";
 add("S3","LAMINATE_DET","common","N2","(A*D)-(B*B)","Positive laminate constitutive determinant");
 add("S3","MEMBRANE_STRAIN","common","1",eps,"Free laminate mid-plane strain");
 add("S3","SIGNED_CURVATURE","common","1/m",curv,"Free laminate curvature from force/moment balance");
 add("S3","EDGE_WARPAGE","common","m","0.125*W*W*"+curv,"Signed center-to-edge 1D deflection proxy");
 auto ss=[&](const std::string& id,const std::string& biax,const std::string& z,const std::string& eigen){add("S3",id,"common","Pa",biax+"*("+eps+"+"+curv+"*"+z+"-"+eigen+")","Interface endpoint biaxial stress proxy");};
 ss("STRESS1_LOWER","P","0","e1");ss("STRESS1_UPPER","P","H1","e1");ss("STRESS2_LOWER","Q","H1","e2");ss("STRESS2_UPPER","Q",z2,"e2");ss("STRESS3_LOWER","S",z2,"e3");ss("STRESS3_UPPER","S",z3,"e3");
 const std::string dndt="(P*H1*C1+Q*H2*C2+S*H3*C3)",dmdt="(P*H1^2*C1+Q*("+z2+"^2-H1^2)*C2+S*("+z3+"^2-"+z2+"^2)*C3)/2";
 add("S3","D_CURV_D_T","common","1/(m K)","(A*"+dmdt+"-B*"+dndt+")/"+den,"Temperature derivative at fixed degree of cure");
 const std::string de="(-(a-gel)/(1-gel))",dnb="(S*H3*"+de+")",dmb="(S*("+z3+"^2-"+z2+"^2)*"+de+"/2)";
 add("S3","V2_D_CURV_D_BETA","V2","1/m","(A*"+dmb+"-B*"+dnb+")/"+den,"Analytical derivative with respect to cure shrinkage coefficient (V2 only)");
 const std::string mx="((((((abs(s11) max abs(s12)) max abs(s21)) max abs(s22)) max abs(s31)) max abs(s32)))";
 add("S4","MAX_STRESS","common","Pa",mx,"Peak sampled layer-interface stress magnitude");
 add("S4","WARP_MARGIN","common","m","Wlim-abs(w)","Illustrative signed warpage margin");
 add("S4","STRESS_MARGIN","common","Pa","Slim-"+mx,"Illustrative signed stress margin");
 add("S4","SCREEN_GUARD","common","0/1","((abs(w)<=Wlim) AND ("+mx+"<=Slim))","Composite limit predicate, not a physical qualification");
 add("S4","SCREEN_SCORE","common","1","(abs(w)/Wlim)+("+mx+"/Slim)+0.1*(1-a)","Uncalibrated normalized screening priority");
 add("S5","DELTA_CURVATURE","V1-V2","1/m","k2-k1","Incremental curvature attributable to model change");
 add("S5","DELTA_WARPAGE","V1-V2","m","w2-w1","Incremental deflection attributable to model change");
 add("S5","RELATIVE_WARPAGE","V1-V2","1","abs(w2)/((abs(w1)) max 1e-9)","Relative absolute warp magnitude for nonzero baseline");
 }
 std::vector<std::string> names(const std::string& stage)const{std::vector<std::string> result;for(auto& g:graphs)if(g.stage==stage)result.push_back(g.id);return result;}
 VV batch(const std::string& stage,const VV& data){auto nn=names(stage);std::vector<PACEVAL_HANDLE> hs;for(auto& name:nn)hs.push_back(graphs.at(ids.at(name)).handle);size_t nv=stage=="S1"?VAR1.size():stage=="S2"?VAR2.size():stage=="S3"?VAR3.size():stage=="S4"?VAR4.size():VAR5.size();auto result=e.multi(hs,data,nv);for(auto& name:nn)graphs.at(ids.at(name)).used=true;return result;}
 double eval(const std::string& name,const std::vector<double>& input){auto& g=graphs.at(ids.at(name));double v=e.scalar(g.handle,input);g.used=true;return v;}
};
// User-data fields are *strict decimal literals*, not expressions accepted by the SDK.
struct Case{std::string id;double H3,W,C3,beta,T;};
std::vector<Case> readCases(const fs::path& path){std::ifstream f(path);need(bool(f),"Missing scenarios.csv");std::string line;need(bool(std::getline(f,line))&&line=="case_id,H3_m,W_m,C3_invK,beta,T_K","Wrong CSV header");std::vector<Case> rows;int index=1;while(std::getline(f,line)){++index;need(!line.empty()&&line.back()!='\r',"Blank line or CRLF not in schema");auto fields=split(line);need(fields.size()==6,"Input field count invalid at line "+std::to_string(index));need(std::regex_match(fields[0],std::regex("[A-Za-z][A-Za-z0-9]{0,18}")),"Invalid case id");Case c{fields[0],0,0,0,0,0};double* dest[]={&c.H3,&c.W,&c.C3,&c.beta,&c.T};for(int j=1;j<6;j++)try{*dest[j-1]=parse(fields[j]);}catch(const std::exception& e){throw std::runtime_error("CSV line "+std::to_string(index)+" column "+std::to_string(j+1)+" "+e.what());}need(c.H3>=1e-4&&c.H3<=1.5e-3&&c.W>=0.005&&c.W<=0.05&&c.C3>=0&&c.C3<=1e-4&&c.beta>=0&&c.beta<=0.01&&c.T>=270&&c.T<=460,"Case domain failure");rows.push_back(c);}need(rows.size()>0&&rows.size()<=10000,"Invalid scenario count");return rows;}
struct Constants{double Tr=423.15,a=.85,gel=.4,H1=500e-6,H2=70e-6,E1=130e9,E2=2.5e9,E3=8e9,N1=.28,N2=.35,N3=.32,C1=2.6e-6,C2=45e-6,k1=.0004,k2=.002,Ea1=55000,Ea2=65000,Tkin=423.15,gE=.8,Wlim=100e-6,Slim=150e6,Rg=8.31446261815324;};
std::vector<double> first(const Case&c,const Constants&s){return {c.T,s.Tr,s.a,s.gel,c.beta,s.H1,s.H2,c.H3,s.E1,s.E2,s.E3,s.N1,s.N2,s.N3,s.C1,s.C2,c.C3,c.W,s.k1,s.k2,s.Ea1,s.Ea2,s.Tkin,s.gE,s.Wlim,s.Slim,s.Rg};}
struct Output{double curv=0,warp=0,maxstress=0,marginw=0,margins=0,guard=0,score=0,dbeta=0,dtemp=0,e3=0,Ebar3=0,st1=0,st2=0,st3=0;};
struct Intermediate{VV v1,v2,v3,v4;};
Intermediate calculate(Models& m,const VV& in,int ver){need(!in.empty(),"No initial rows");Intermediate result;result.v1=m.batch("S1",in);VV ii;ii.reserve(in.size());for(size_t n=0;n<in.size();n++){auto& a=result.v1[n];auto& x=in[n];ii.push_back({a[4],a[5],a[ver==1?6:7],a[8],a[9],a[ver==1?10:11],x[5],x[6],x[7]});}
 result.v2=m.batch("S2",ii);ii.clear();for(size_t n=0;n<in.size();n++){const auto& a=result.v2[n];const auto& j=result.v1[n];const auto& x=in[n];ii.push_back({a[0],a[1],a[2],a[3],a[4],j[4],j[5],j[ver==1?6:7],j[8],j[9],j[ver==1?10:11],x[5],x[6],x[7],x[17],x[14],x[15],x[16],x[2],x[3],x[4]});}
 result.v3=m.batch("S3",ii);ii.clear();for(size_t n=0;n<in.size();n++){const auto& b=result.v3[n];const auto& x=in[n];need(b[0]>0,"Nonpositive laminate A*D-B^2");ii.push_back({b[3],b[4],b[5],b[6],b[7],b[8],b[9],x[24],x[25],x[2]});}
 result.v4=m.batch("S4",ii);return result;}
Output pack(const Intermediate& in,size_t n,int ver){const auto& b=in.v3[n];const auto& s=in.v4[n];const auto& a=in.v1[n];return {b[2],b[3],s[0],s[1],s[2],s[3],s[4],ver==2?b[11]:0,b[10],a[ver==1?10:11],a[ver==1?6:7],b[5],b[7],b[9]};}
// A wholly separate native C++ analytical implementation for selected end-value controls.
std::array<double,3> nativeMechanics(const Case& c,const Constants& s,int ver){double p=s.E1/(1-s.N1),q=s.E2/(1-s.N2),r=s.E3*(ver==1?1.0:1+s.gE*(s.a-s.gel))/(1-s.N3);double z1=s.H1,z2=z1+s.H2,z3=z2+c.H3;double e1=s.C1*(c.T-s.Tr),e2=s.C2*(c.T-s.Tr),e3=c.C3*(c.T-s.Tr)-(ver==1?0:c.beta*(s.a-s.gel)/(1-s.gel));double A=p*z1+q*s.H2+r*c.H3,B=(p*z1*z1+q*(z2*z2-z1*z1)+r*(z3*z3-z2*z2))/2,D=(p*z1*z1*z1+q*(z2*z2*z2-z1*z1*z1)+r*(z3*z3*z3-z2*z2*z2))/3;double N=p*z1*e1+q*s.H2*e2+r*c.H3*e3,M=(p*z1*z1*e1+q*(z2*z2-z1*z1)*e2+r*(z3*z3-z2*z2)*e3)/2;double k=(A*M-B*N)/(A*D-B*B),w=k*c.W*c.W/8;double eps=(D*N-B*M)/(A*D-B*B);double stress[]={p*(eps-e1),p*(eps+k*z1-e1),q*(eps+k*z1-e2),q*(eps+k*z2-e2),r*(eps+k*z2-e3),r*(eps+k*z3-e3)};double peak=0;for(double x:stress)peak=std::max(peak,std::abs(x));return {k,w,peak};}
void selftest(){Engine e;e.calibrate();Models m(e);for(const char* s:{"0","-0.25","3.1E-5","+0.002",".125","2."})near(parse(fmt(parse(s))),parse(s),2e-12,2e-16);for(const char* t:{""," 2","NaN","Inf","1e99999","2+3","1,20","0x1","1;2","-"}){bool denied=false;try{(void)parse(t);}catch(...){denied=true;}need(denied,"Unsafe numeric field accepted");}
 auto opr=[&](const std::string& x,double truth){auto g=e.add(x,{"x","y","z"});near(e.scalar(g,{1,2,3}),truth,1e-10,1e-10);};
 opr("((x < y) AND (z >= 0))",1);opr("((x >= y) OR (z = 3))",1);opr("NOT(x=y)",1);opr("((x <> y) AND (x <= y))",1);opr("((abs(x) <= (2*y)) AND (z >= 0))",1);opr("(x min y)",1);opr("(x max y)",2);opr("(-1) % 10",-1);opr("(-1) mod 10",9);opr("((x=y) XOR (x<y))",1);
 Constants s;Case c{"TEST",550e-6,.020,20e-6,.0018,298.15};auto in=VV{first(c,s)};auto a=calculate(m,in,1),b=calculate(m,in,2);for(int v:{1,2}){auto n=nativeMechanics(c,s,v);auto o=pack(v==1?a:b,0,v);near(o.curv,n[0],3e-8,5e-10);near(o.warp,n[1],3e-8,5e-13);near(o.maxstress,n[2],3e-8,1e-4);near(o.guard, double(o.marginw>=0&&o.margins>=0),0,1e-12);} // Algebraic reference.
 // Zero mismatch / zero thermal excursion / no shrinkage -> all strains zero.
 Case zero=c;zero.T=s.Tr;zero.C3=s.C1;zero.beta=0;Constants z=s;z.C2=z.C1;auto zz=calculate(m,VV{first(zero,z)},2);near(pack(zz,0,2).curv,0,0,1e-11);near(pack(zz,0,2).maxstress,0,0,1e-4);
 std::cout<<"SELFTEST PASS: original SDK, multi-graph, input conversion, composite operators, three-layer force/moment equilibrium, zero-mismatch limit\n";}
void run(Models& m,const fs::path& input,const fs::path& folder){fs::create_directories(folder);auto cases=readCases(input);Constants s;Engine& e=m.e;
 std::ofstream outcome(folder/"screening.csv"),compare(folder/"model_comparison.csv"),profile(folder/"thermal_profile.csv"),cure(folder/"cure_profile.csv"),shape(folder/"deflection_surface.csv"),audit(folder/"native_audit.csv");need(outcome&&compare&&profile&&cure&&shape&&audit,"Result CSV cannot be created");
 outcome<<"case_id,model,T_K,H3_m,W_m,C3_invK,beta,alpha,signed_curvature_inv_m,signed_center_edge_warpage_m,peak_endpoint_stress_Pa,warpage_margin_m,stress_margin_Pa,screen_guard,screen_score,dcurvature_dT_inv_mK,dcurvature_dbeta_inv_m,eigen3_strain,encapsulant_Ebar_Pa\n";
 compare<<"case_id,T_K,V1_curvature_inv_m,V2_curvature_inv_m,delta_curvature_inv_m,V1_warp_m,V2_warp_m,delta_warp_m,abs_warp_ratio\n";
 profile<<"model,T_K,curvature_inv_m,center_edge_warp_m,peak_endpoint_stress_Pa,warpage_margin_m,stress_margin_Pa,score,dcurvature_dT_inv_mK,screen_guard\n";
 cure<<"time_s,T_K,degree_of_cure,cure_rate_inv_s,curvature_inv_m,center_edge_warp_m,peak_endpoint_stress_Pa\n";
 shape<<"model,x_m,y_m,deflection_m\n";
 audit<<"case_id,model,paceval_curvature_inv_m,reference_curvature_inv_m,paceval_warp_m,reference_warp_m,paceval_stress_Pa,reference_stress_Pa\n";
 size_t casesN=cases.size(),checks=0,guards1=0,guards2=0;std::vector<Output> O1,O2;O1.reserve(casesN);O2.reserve(casesN);
 VV incoming;for(const auto& c:cases)incoming.push_back(first(c,s));
 auto a=calculate(m,incoming,1);auto b=calculate(m,incoming,2);
 VV comparisons;for(size_t i=0;i<casesN;i++){auto p=pack(a,i,1),q=pack(b,i,2);O1.push_back(p);O2.push_back(q);comparisons.push_back({p.curv,q.curv,p.warp,q.warp});for(int version:{1,2}){const auto& o=version==1?p:q;const auto& c=cases[i];outcome<<c.id<<","<<version<<","<<fmt(c.T)<<","<<fmt(c.H3)<<","<<fmt(c.W)<<","<<fmt(c.C3)<<","<<fmt(c.beta)<<","<<fmt(s.a)<<","<<fmt(o.curv)<<","<<fmt(o.warp)<<","<<fmt(o.maxstress)<<","<<fmt(o.marginw)<<","<<fmt(o.margins)<<","<<fmt(o.guard)<<","<<fmt(o.score)<<","<<fmt(o.dtemp)<<","<<fmt(o.dbeta)<<","<<fmt(o.e3)<<","<<fmt(o.Ebar3)<<"\n";
 if(version==1&&o.guard>.5)guards1++;if(version==2&&o.guard>.5)guards2++;
 if(i%11==0){auto n=nativeMechanics(c,s,version);near(o.curv,n[0],1e-7,1e-8);near(o.warp,n[1],1e-7,1e-12);near(o.maxstress,n[2],1e-7,1e-3);audit<<c.id<<","<<version<<","<<fmt(o.curv)<<","<<fmt(n[0])<<","<<fmt(o.warp)<<","<<fmt(n[1])<<","<<fmt(o.maxstress)<<","<<fmt(n[2])<<"\n";checks+=3;}}}
 auto diff=m.batch("S5",comparisons);for(size_t i=0;i<cases.size();i++)compare<<cases[i].id<<","<<fmt(cases[i].T)<<","<<fmt(O1[i].curv)<<","<<fmt(O2[i].curv)<<","<<fmt(diff[i][0])<<","<<fmt(O1[i].warp)<<","<<fmt(O2[i].warp)<<","<<fmt(diff[i][1])<<","<<fmt(diff[i][2])<<"\n";
 Case base{"REFERENCE",550e-6,20e-3,20e-6,.0018,298.15};VV grid;for(int j=0;j<=190;j++){Case cc=base;cc.T=278.15+j;grid.push_back(first(cc,s));}for(int version:{1,2}){auto z=calculate(m,grid,version);for(size_t j=0;j<grid.size();j++){auto o=pack(z,j,version);profile<<version<<","<<fmt(grid[j][0])<<","<<fmt(o.curv)<<","<<fmt(o.warp)<<","<<fmt(o.maxstress)<<","<<fmt(o.marginw)<<","<<fmt(o.margins)<<","<<fmt(o.score)<<","<<fmt(o.dtemp)<<","<<fmt(o.guard)<<"\n";}}
 // A stateful thermal program: post-gel dwell, cooling, and late room-temperature hold.
 // C++ manages RK4 time marching; the complete non-linear kinetic RHS is a paceval graph.
 auto rhs=[&](double degree,double T){auto c=base;c.T=T;auto row=first(c,s);row[2]=degree;return m.eval("CURE_RATE",row);};
 auto calcT=[&](int i){if(i<=65)return s.Tr;if(i<=155)return s.Tr-(s.Tr-298.15)*(i-65)/90.;return 298.15;};
 double degree=s.gel+0.03;for(int i=0;i<=180;i++){
  double T=calcT(i);Case c=base;c.T=T;auto x=first(c,s);x[2]=degree;auto z=calculate(m,VV{x},2);auto o=pack(z,0,2);cure<<fmt(i*60.)<<","<<fmt(T)<<","<<fmt(degree)<<","<<fmt(rhs(degree,T))<<","<<fmt(o.curv)<<","<<fmt(o.warp)<<","<<fmt(o.maxstress)<<"\n";
  if(i==180)break;double dt=60,tn=calcT(i+1);double k1=rhs(degree,T),k2=rhs(degree+dt*k1/2,(T+tn)/2),k3=rhs(degree+dt*k2/2,(T+tn)/2),k4=rhs(degree+dt*k3,tn);degree+=dt*(k1+2*k2+2*k3+k4)/6;need(degree>=s.gel&&degree<=1.00001,"Cure state left valid range");degree=std::min(1.,degree);
 }
 // Package-deflection surfaces from a separately registered genuine paceval graph.
 auto hx=e.add("0.5*k*(x*x+y*y)",{"k","x","y"});for(int version:{1,2}){auto z=calculate(m,VV{first(base,s)},version);double k=pack(z,0,version).curv;VV xy;for(int i=0;i<=40;i++)for(int j=0;j<=40;j++)xy.push_back({k,base.W*(i-20)/40.,base.W*(j-20)/40.});auto vals=e.multi({hx},xy,3);for(size_t n=0;n<xy.size();n++)shape<<version<<","<<fmt(xy[n][1])<<","<<fmt(xy[n][2])<<","<<fmt(vals[n][0])<<"\n";}
 std::ofstream inv(folder/"math_execution_inventory.csv"),manifest(folder/"formula_manifest.csv"),ev(folder/"execution_evidence.json");inv<<"function_id,domain_quantity,mathematical_definition,units,execution_owner,paceval_graph_id,formula_version,api_path,reference_test,status,host_reason\n";manifest<<"graph_id,version,stage,variable_list,expression,units\n";
 size_t used=0;for(auto& g:m.graphs){if(g.used)used++;const auto& vars=g.stage=="S1"?VAR1:g.stage=="S2"?VAR2:g.stage=="S3"?VAR3:g.stage=="S4"?VAR4:VAR5;
 inv<<g.id<<",\""<<g.description<<"\",\""<<g.expression<<"\","<<g.units<<",paceval,"<<g.id<<","<<g.version<<",paceval_dGetMultipleComputationsResultsExt / paceval_dGetComputationResult,independent native C++ plus Python mpmath,"<<(g.used?"executed":"registered_only")<<",\n";
 manifest<<g.id<<","<<g.version<<","<<g.stage<<",\""<<joined(vars)<<"\",\""<<g.expression<<"\","<<g.units<<"\n";}
 inv<<"RK4_CURE,Post-gel state integration,RK4 method,s,host,,V2,C++ time step,high precision integration,executed,History-dependent stateful integration\n";
 inv<<"CURVE_GRID,Scenarios and profile generation,Parameter enumeration,1,host,,both,C++ control flow,independent input checks,executed,Data orchestration\n";
 inv<<"SURFACE_GRID,Deflection mesh construction,Mesh coordinate enumeration,m,host,,both,C++ control flow,domain tests,executed,Mesh is not a single scalar graph\n";
 inv<<"SHAPE_DEFLECTION,Two-dimensional idealized deflection,0.5*k*(x*x+y*y),m,paceval,SHAPE_DEFLECTION,both,paceval_dGetMultipleComputationsResultsExt,native geometric check,executed,\n";
 ev<<"{\n \"sdk_version\": \"4.25\", \"provenance\": \"deterministic synthetic, uncalibrated mechanical screening\",\n \"unique_domain_graphs_created\": "<<m.graphs.size()+1<<", \"unique_domain_graphs_executed\": "<<used+1<<",\n \"scalar_calls\": "<<e.scalarCalls<<", \"batch_calls\": "<<e.batchCalls<<", \"batch_graph_point_evaluations\": "<<e.batchGraphPoints<<", \"scenario_count\": "<<cases.size()<<", \"model_scenario_count\": "<<2*cases.size()<<",\n \"V1_screen_guard_passes\": "<<guards1<<", \"V2_screen_guard_passes\": "<<guards2<<", \"native_reference_endvalue_checks\": "<<checks<<",\n \"recorded_results\": [\"screening.csv\",\"model_comparison.csv\",\"thermal_profile.csv\",\"cure_profile.csv\",\"deflection_surface.csv\",\"native_audit.csv\"],\n \"scope\": \"functionality and numerical reproducibility only, no speed/energy/safety qualification\"\n}\n";
 std::cout<<"RESEARCH PASS: executed "<<used+1<<"/"<<m.graphs.size()+1<<" domain graphs, scenarios "<<cases.size()<<", two versions, independent endvalue checks "<<checks<<"\n";
}
}
int main(int argc,char**argv){try{if(argc==2&&std::string(argv[1])=="--selftest"){selftest();return 0;}need(argc==4&&std::string(argv[1])=="--run","Usage: chip_warpage --run input/scenarios.csv results/");Engine e;e.calibrate();Models m(e);run(m,argv[2],argv[3]);return 0;}catch(const std::exception&ex){std::cerr<<"ERROR: "<<ex.what()<<"\n";return 1;}}
