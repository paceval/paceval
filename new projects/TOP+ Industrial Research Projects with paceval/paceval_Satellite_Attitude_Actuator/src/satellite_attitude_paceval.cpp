// WP32: Satellite Attitude Actuator Torque and Momentum Envelopes.
// Mathematical ownership: actual persistent paceval graphs for physics, constraints, scores,
// sensitivities, quaternion normalization and cross-axis candidate decisions.
// C++ ownership: CSV schema, numeric input validation, graph-handle lifetime, batching,
// three-axis aggregation, sequential test-profile orchestration, and independent checks.
// IMPORTANT: This local C++ target has passed syntax checking ONLY in the provided release.
// It has not been linked/executed because a compatible libpaceval.so is unavailable.
#include "paceval_main.h"
#include <algorithm>
#include <array>
#include <cmath>
#include <cstddef>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <limits>
#include <locale>
#include <regex>
#include <sstream>
#include <stdexcept>
#include <string>
#include <utility>
#include <vector>

struct ModelGraph { const char* id; const char* expression; const char* units; };
#include "generated_axis_formulas.h"
#include "generated_aggregate_formulas.h"
#include "generated_quaternion_formulas.h"

namespace {
void check(bool value,const std::string& message){if(!value)throw std::runtime_error(message);}
struct AxisRow{std::string id;std::string axis;std::array<double,20> v{};};
struct QuatRow{std::string id;std::array<double,8> v{};};
struct Group {
 std::vector<PACEVAL_HANDLE> handles;
 Group()=default;
 Group(const Group&)=delete;Group& operator=(const Group&)=delete;
 Group(Group&& rhs) noexcept:handles(std::move(rhs.handles)){rhs.handles.clear();}
 ~Group(){for(auto x:handles)if(x)paceval_DeleteComputation(x);}
};

bool isDecimalLiteral(const std::string& s){
 static const std::regex re(R"(^[+-]?(?:[0-9]+(?:\.[0-9]*)?|\.[0-9]+)(?:[eE][+-]?[0-9]+)?$)");
 return !s.empty() && s.size()<85 && std::regex_match(s,re);
}
double fromOriginalSdk(const std::string& s){
 check(isDecimalLiteral(s),"CSV numeric cell must be a literal, not an expression: "+s);
 int err=-1;long pos=-1;double lo=0,hi=0;
 double value=paceval_dConvertStringToFloat(s.c_str(),&err,&pos,false,&lo,&hi);
 check(err==0 && std::isfinite(value),"Original paceval input conversion failed");
 return value;
}
std::string toOriginalSdk(double value){
 check(std::isfinite(value),"Output must be finite");
 std::array<char,4096> buffer{};
 int p=paceval_dConvertFloatToString(buffer.data(),value);
 check(p>0,"Original paceval output conversion failed");
 auto end=std::find(buffer.begin(),buffer.end(),'\0');
 check(end!=buffer.end() && end!=buffer.begin(),"Original SDK conversion string invalid");
 std::string text(buffer.begin(),end);
 check(isDecimalLiteral(text),"Output must be a canonical decimal literal");
 return text;
}
void converterSelfTest(){
 for(const char* s:{"0","+.25","-3.14E+10","0.00000001","5."})
  check(isDecimalLiteral(toOriginalSdk(fromOriginalSdk(s))),"SDK conversion self-test failed");
 for(const char* s:{"","NaN","Inf","0xFF","1+2"," 2","2,1","1_000"})
  check(!isDecimalLiteral(s),"Lexical gate accepted forbidden CSV expression");
 bool overflowRejected=false;
 try{(void)fromOriginalSdk("1e99999");}catch(...){overflowRejected=true;}
 check(overflowRejected,"Overflow input was not rejected");
}
std::vector<std::string> split(const std::string& line){
 std::stringstream input(line);std::vector<std::string> result;std::string part;
 while(std::getline(input,part,','))result.push_back(part);
 check(!line.empty() && line.back()!=',',"Trailing CSV comma");
 return result;
}
std::string header(const std::string& first,const char* variables){
 std::string h=first;std::stringstream ss(variables);std::string word;
 while(ss>>word)h+=","+word;
 return h;
}
void validateAxis(const AxisRow& row){
 const auto& x=row.v;
 for(double v:x)check(std::isfinite(v),"Nonfinite satellite input");
 check(x[0]>0 && x[1]>0 && x[2]>0,"Inertia eigenaxes must be positive");
 check(x[11]>0 && x[12]>0 && x[13]>0 && x[14]>0,"Positive time and envelope limits required");
 check(x[15]>0,"Reaction-wheel axial inertia must be positive");
 check(x[16]>=0 && x[17]>=0 && x[18]>=0,"Nonnegative dimensionless cost weights required");
 check(row.axis=="x"||row.axis=="y"||row.axis=="z","Only orthogonal x/y/z wheel frames accepted");
}
std::vector<AxisRow> readAxis(const std::string& fileName){
 std::ifstream in(fileName);in.imbue(std::locale::classic());check(bool(in),"Cannot open axis input CSV");
 std::string line;check(bool(std::getline(in,line)),"Empty axis CSV");
 if(!line.empty()&&line.back()=='\r')line.pop_back();
 check(line==header("case_id,axis",sat_axis_variable_list),"Axis CSV schema mismatch");
 std::vector<AxisRow> rows;
 while(std::getline(in,line)){
  if(!line.empty()&&line.back()=='\r')line.pop_back();
  if(line.empty())continue;
  auto c=split(line);check(c.size()==22,"22 axis CSV columns required");
  AxisRow r;r.id=c[0];r.axis=c[1];
  check(std::regex_match(r.id,std::regex(R"(^[A-Za-z0-9_-]{1,40}$)")),"Invalid case id");
  for(size_t i=0;i<20;i++)r.v[i]=fromOriginalSdk(c[i+2]);
  validateAxis(r);rows.push_back(r);check(rows.size()<=600000,"Axis row cap exceeded");
 }
 check(!rows.empty() && rows.size()%3==0,"Complete xyz triplets required");
 for(size_t i=0;i<rows.size();i+=3){
  check(rows[i].axis=="x"&&rows[i+1].axis=="y"&&rows[i+2].axis=="z","Must provide consecutive x/y/z");
  check(rows[i].id==rows[i+1].id&&rows[i].id==rows[i+2].id,"Axes within triplet have different IDs");
 }
 return rows;
}
std::vector<QuatRow> readQuat(const std::string& fileName){
 std::ifstream in(fileName);in.imbue(std::locale::classic());check(bool(in),"Cannot open quaternion CSV");
 std::string line;check(bool(std::getline(in,line)),"Empty quaternion CSV");
 if(!line.empty()&&line.back()=='\r')line.pop_back();
 check(line==header("case_id",sat_quat_variable_list),"Quaternion CSV schema mismatch");
 std::vector<QuatRow> rows;
 while(std::getline(in,line)){
  if(!line.empty()&&line.back()=='\r')line.pop_back();
  if(line.empty())continue;
  auto c=split(line);check(c.size()==9,"9 quaternion CSV columns required");
  QuatRow r;r.id=c[0];
  for(size_t j=0;j<8;j++)r.v[j]=fromOriginalSdk(c[j+1]);
  check(r.v[7]>0,"Quaternion update dt must be positive");
  double n=std::sqrt(r.v[0]*r.v[0]+r.v[1]*r.v[1]+r.v[2]*r.v[2]+r.v[3]*r.v[3]);
  check(n>1e-12&&std::isfinite(n),"Quaternion must have nonzero finite norm");
  rows.push_back(r);check(rows.size()<=600000,"Quaternion row cap exceeded");
 }
 check(!rows.empty(),"No quaternion samples supplied");return rows;
}
Group init(const ModelGraph* list,size_t n,unsigned long dim,const char* variables){
 Group g;
 for(size_t i=0;i<n;i++){
  PACEVAL_HANDLE h=paceval_CreateComputation(list[i].expression,dim,variables,false,nullptr);
  check(h&&!paceval_GetIsError(h),std::string("Original paceval graph failed: ")+list[i].id);
  g.handles.push_back(h);
 }
 return g;
}
void operatorSelfTest(){
 struct T{const char* expr;std::array<double,3> expected;};
 const T tests[]={
  {"(-1) % 10",{{-1,-1,-1}}},{"(-1) mod 10",{{9,9,9}}},
  {"4 min 5",{{4,4,4}}},{"4 max 5",{{5,5,5}}},
  {"((x <= (2*y)) AND (z >= 0))",{{1,1,0}}},
  {"((NOT(x = y)) OR (z <> 0))",{{0,1,1}}},
  {"((x = y) XOR (z <> 0))",{{1,0,1}}}
 };
 const double vv[3][3]={{1,1,0},{-1,1,0},{2,1,-1}};
 for(const T& test:tests){
  PACEVAL_HANDLE g=paceval_CreateComputation(test.expr,3,"x y z",false,nullptr);
  check(g&&!paceval_GetIsError(g),"Operator self-test: graph registration failed");
  for(size_t i=0;i<3;i++){
   double x[3]={vv[i][0],vv[i][1],vv[i][2]};
   double y=paceval_dGetComputationResult(g,x,nullptr,nullptr);
   check(!paceval_GetIsError(g)&&y==test.expected[i],"Operator self-test: wrong output");
  }
  paceval_DeleteComputation(g);
 }
}

bool near(double a,double b){return std::isfinite(a)&&std::isfinite(b)&&std::abs(a-b)<=8e-11*(1+std::abs(b));}
std::vector<double> evaluate(const Group& group,const std::vector<double>& flattened,size_t dim,size_t rows){
 const size_t G=group.handles.size();check(dim&&rows&&flattened.size()==dim*rows,"Incorrect batch dimensions");
 check(G>0,"Empty graph list");
 std::vector<double> packed=flattened,raw(G*rows),out(G*rows);
 std::vector<int> err(G*rows,-1);
 bool failed=paceval_dGetMultipleComputationsResultsExt(const_cast<PACEVAL_HANDLE*>(group.handles.data()),
   (unsigned long)G,packed.data(),(unsigned long)rows,raw.data(),nullptr,nullptr,err.data());
 check(!failed,"Original SDK batch execution returned an error");
 for(int e:err)check(e==0,"Original SDK per-graph/row error occurred");
 bool graphMajor=true,rowMajor=true;
 for(size_t j=0;j<std::min(rows,size_t(5));j++){
  double v=paceval_dGetComputationResult(group.handles[0],packed.data()+j*dim,nullptr,nullptr);
  check(!paceval_GetIsError(group.handles[0]),"Scalar layout probe failed");
  graphMajor&=near(v,raw[j]);rowMajor&=near(v,raw[j*G]);
 }
 check(graphMajor||rowMajor,"Unknown batch output layout");
 // Ambiguous at all probe points is acceptable only if layouts are numerically identical.
 if(graphMajor&&rowMajor){
  for(size_t j=0;j<rows;j++)for(size_t k=0;k<G;k++)
   check(near(raw[k*rows+j],raw[j*G+k]),"Ambiguous non-equivalent SDK result layouts");
 }
 for(size_t j=0;j<rows;j++)for(size_t k=0;k<G;k++){
  double y=raw[graphMajor?k*rows+j:j*G+k];check(std::isfinite(y),"Nonfinite SDK output");out[j*G+k]=y;
 }
 return out;
}
void independentAxisCheck(const AxisRow& in,const double* out){
 const auto& p=in.v;
 double inert=(p[2]-p[1])*p[4]*p[5];double gyro=p[4]*p[8]-p[5]*p[7];
 double a1=(p[9]+p[10]-inert)/p[0],a2=(p[9]+p[10]-inert-gyro)/p[0];
 double hnext=p[6]-p[9]*p[11],mT=p[12]-std::abs(p[9]),mH=p[13]-std::abs(hnext);
 double r1=p[3]+p[11]*a1,r2=p[3]+p[11]*a2;
 double mR1=p[14]-std::abs(r1),mR2=p[14]-std::abs(r2);
 double s1=std::min({mT/p[12],mH/p[13],mR1/p[14]});
 double s2=std::min({mT/p[12],mH/p[13],mR2/p[14]});
 struct Check{size_t i;double val;};
 const Check tests[]={{0,inert},{1,gyro},{2,a1},{3,a2},{4,r1},{5,r2},{6,hnext},{7,mT},{8,mH},{9,mR1},{10,mR2},
                    {11,double(s1>=0)},{12,double(s2>=0)},{13,s1},{14,s2},{19,a2-a1},{20,0.}};
 for(const auto& item:tests)check(near(out[item.i],item.val),in.id+" native independent mismatch: "+sat_axis_graphs[item.i].id);
}
void independentAggregateCheck(const double* out,const double* v){
 double s1=std::min({v[12],v[13],v[14]});double s2=std::min({v[15],v[16],v[17]});
 const double expected[]={double(s1>=0),double(s2>=0),s1,s2,double((s1>=0)!=(s2>=0)),s2-s1,
 std::min({v[0],v[1],v[2]}),std::min({v[3],v[4],v[5]})};
 for(size_t i=0;i<sat_agg_graph_count;i++)check(near(out[i],expected[i]),"Independent aggregate reference mismatch");
}
void independentQuatCheck(const QuatRow& row,const double* out){
 const auto& x=row.v;const double& a=x[0];const double& b=x[1];const double& c=x[2];const double& d=x[3];
 double wx=x[4],wy=x[5],wz=x[6],dt=x[7];
 double qq[]={a-.5*dt*(b*wx+c*wy+d*wz),b+.5*dt*(a*wx+c*wz-d*wy),
              c+.5*dt*(a*wy+d*wx-b*wz),d+.5*dt*(a*wz+b*wy-c*wx)};
 double n=std::sqrt(qq[0]*qq[0]+qq[1]*qq[1]+qq[2]*qq[2]+qq[3]*qq[3]);
 check(near(out[0],n),"Quaternion candidate norm mismatch");
 for(size_t i=0;i<4;i++)check(near(out[i+1],qq[i]/n),"Quaternion normalized update mismatch");
 check(near(std::sqrt(out[1]*out[1]+out[2]*out[2]+out[3]*out[3]+out[4]*out[4]),1),"Quaternion not normalized");
}
void writeRows(const std::string& name,const std::vector<std::string>& ids,const ModelGraph* graph,size_t G,const std::vector<double>& result){
 std::ofstream o(name);o.imbue(std::locale::classic());check(bool(o),"Cannot create output CSV");
 o<<"case_id";for(size_t k=0;k<G;k++)o<<','<<graph[k].id;o<<'\n';
 for(size_t j=0;j<ids.size();j++){
  o<<ids[j];for(size_t k=0;k<G;k++)o<<','<<toOriginalSdk(result[j*G+k]);o<<'\n';
 }
}
void localDesaturationProfile(const Group& axis,const std::string& outName){
 std::ofstream out(outName);check(bool(out),"Cannot create local desaturation file");
 out<<"step,time_s,wheel_momentum_in_Nms,wheel_momentum_next_Nms,momentum_margin_Nms,body_acceleration_rad_s2\n";
 double h=.039;
 for(int i=1;i<=12;i++){
  double v[20]={.085,.105,.075,0,0,0,h,-.018,.026,.00015,-.00015,10,.0009,.041,.026,.00013,1,.25,.5,0};
  double dh=paceval_dGetComputationResult(axis.handles[6],v,nullptr,nullptr);
  double acc=paceval_dGetComputationResult(axis.handles[3],v,nullptr,nullptr);
  double margin=paceval_dGetComputationResult(axis.handles[8],v,nullptr,nullptr);
  check(!paceval_GetIsError(axis.handles[6])&&!paceval_GetIsError(axis.handles[3])&&!paceval_GetIsError(axis.handles[8]),"Profile SDK graph error");
  check(near(acc,0)&&near(dh,h-.0015),"Profile independent reference failed");
  out<<i<<','<<i*10<<','<<toOriginalSdk(h)<<','<<toOriginalSdk(dh)<<','<<toOriginalSdk(margin)<<','<<toOriginalSdk(acc)<<'\n';
  h=dh;
 }
}
}

int main(int argc,char** argv){
 try{
  check(argc==5,"Usage: satellite_attitude_paceval axis_inputs.csv quaternion_inputs.csv axis_output.csv aggregate_output_prefix");
  converterSelfTest();operatorSelfTest();
  std::vector<AxisRow> rows=readAxis(argv[1]);
  std::vector<QuatRow> quats=readQuat(argv[2]);
  Group axis=init(sat_axis_graphs,sat_axis_graph_count,(unsigned long)sat_axis_variable_count,sat_axis_variable_list);
  Group agg=init(sat_agg_graphs,sat_agg_graph_count,(unsigned long)sat_agg_variable_count,sat_agg_variable_list);
  Group quat=init(sat_quat_graphs,sat_quat_graph_count,(unsigned long)sat_quat_variable_count,sat_quat_variable_list);
  std::vector<double> input;input.reserve(rows.size()*sat_axis_variable_count);
  for(const auto& r:rows)input.insert(input.end(),r.v.begin(),r.v.end());
  auto axisResult=evaluate(axis,input,sat_axis_variable_count,rows.size());
  for(size_t j=0;j<rows.size();j++)independentAxisCheck(rows[j],axisResult.data()+j*sat_axis_graph_count);
  std::vector<std::string> axisId;for(const auto& r:rows)axisId.push_back(r.id+"_"+r.axis);
  writeRows(argv[3],axisId,sat_axis_graphs,sat_axis_graph_count,axisResult);

  std::vector<double> aggInputs;std::vector<std::string> aggIDs;
  for(size_t j=0;j<rows.size();j+=3){
   aggIDs.push_back(rows[j].id);
   // Group axis outputs into comparable SI physical margins and dimensionless scores.
   for(size_t field:{size_t(7),size_t(8),size_t(9),size_t(10),size_t(13),size_t(14)})
    for(size_t a=0;a<3;a++)aggInputs.push_back(axisResult[(j+a)*sat_axis_graph_count+field]);
  }
  auto aggregate=evaluate(agg,aggInputs,sat_agg_variable_count,aggIDs.size());
  for(size_t j=0;j<aggIDs.size();j++)independentAggregateCheck(aggregate.data()+j*sat_agg_graph_count,aggInputs.data()+j*sat_agg_variable_count);
  writeRows(std::string(argv[4])+"_joint.csv",aggIDs,sat_agg_graphs,sat_agg_graph_count,aggregate);
  std::vector<double> qs;std::vector<std::string> qi;for(const auto& v:quats){qi.push_back(v.id);qs.insert(qs.end(),v.v.begin(),v.v.end());}
  auto qResult=evaluate(quat,qs,sat_quat_variable_count,quats.size());
  for(size_t i=0;i<quats.size();i++)independentQuatCheck(quats[i],qResult.data()+i*sat_quat_graph_count);
  writeRows(std::string(argv[4])+"_quaternion.csv",qi,sat_quat_graphs,sat_quat_graph_count,qResult);
  localDesaturationProfile(axis,std::string(argv[4])+"_desaturation.csv");
  std::cout<<"Local SDK operations completed; outputs recorded to CSV.\n";
  return 0;
 }catch(const std::exception& e){std::cerr<<"FAILED: "<<e.what()<<'\n';return 1;}
}
