// WP30: Industrial furnace heat balance and emission constraint screening.
// All domain equations are original paceval persistent graphs from generated_formulas.h.
// The host performs CSV, domain validation, graph-handle ownership, native cross-checks and I/O.
// This executable has NOT been linked/run in this research release: compatible libpaceval.so absent.
#include "paceval_main.h"
#include "generated_formulas.h"
#include <algorithm>
#include <array>
#include <cmath>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <limits>
#include <locale>
#include <regex>
#include <sstream>
#include <stdexcept>
#include <string>
#include <vector>
#include <utility>

namespace {
void require(bool ok,const std::string& msg){if(!ok)throw std::runtime_error(msg);}
struct Row {std::string id;std::array<double,25> x;};
struct GraphHandles {
  std::vector<PACEVAL_HANDLE> h;
  ~GraphHandles(){for(auto p:h)if(p)paceval_DeleteComputation(p);}
  GraphHandles()=default;
  GraphHandles(const GraphHandles&)=delete;
  GraphHandles& operator=(const GraphHandles&)=delete;
  GraphHandles(GraphHandles&& other) noexcept:h(std::move(other.h)){other.h.clear();}
};
bool literal(const std::string& s){
  static const std::regex e(R"(^[+-]?(?:[0-9]+(?:\.[0-9]*)?|\.[0-9]+)(?:[eE][+-]?[0-9]+)?$)");
  return !s.empty()&&s.size()<85&&std::regex_match(s,e);
}
double fromSdk(const std::string& s,const std::string& label){
  require(literal(s),"Reject non-numeric CSV input: "+label);
  int type=-1;long pos=-1;double lower=0,upper=0;
  double x=paceval_dConvertStringToFloat(s.c_str(),&type,&pos,false,&lower,&upper);
  require(type==0&&std::isfinite(x),"SDK decimal conversion error "+label);
  return x;
}
std::string toSdk(double x){
  require(std::isfinite(x),"Nonfinite conversion argument");
  std::array<char,4096> s{};
  int precision=paceval_dConvertFloatToString(s.data(),x);
  require(precision>0,"Original paceval double-to-string conversion failed");
  auto end=std::find(s.begin(),s.end(),'\0');
  require(end!=s.end()&&end!=s.begin(),"Unterminated SDK numeric buffer");
  std::string out(s.begin(),end);
  require(literal(out),"Noncanonical SDK numeric output");
  return out;
}
void validate(const Row& r){
  for(double v:r.x)require(std::isfinite(v),"Nonfinite input: "+r.id);
  const auto& x=r.x;
  require(x[0]>0&&x[1]>0&&x[2]>0&&x[2]<=1,"Positive fuel and burner domain");
  require(x[3]>0&&x[4]>0&&x[5]>0&&x[6]>=x[5],"Product heat and Kelvin temperatures");
  require(x[7]>=0&&x[7]<=.01,"Nonnegative cp slope domain");
  require(x[8]>=0&&x[9]>0&&x[10]>0&&x[11]>0&&x[10]>=x[11],"Wall/ambient domain");
  require(x[12]>=0&&x[12]<=1&&x[13]>0,"Emissivity/Stefan constant domain");
  require(x[14]>0&&x[15]>0&&x[16]>=x[11],"Exhaust thermodynamic domain");
  require(x[17]>=0&&x[17]<=1,"Recovery fraction out of bounds");
  require(x[18]>=0&&x[19]>=0&&x[20]>=0,"Negative emission input");
  require(x[21]>0&&x[22]>0&&x[23]>0&&x[24]>0,"Positive cap requirements");
}
std::vector<Row> loadCSV(const std::string& path){
  std::ifstream file(path);file.imbue(std::locale::classic());require(bool(file),"Cannot open input CSV");
  std::string line;require(bool(std::getline(file,line)),"Empty input CSV");
  if(!line.empty()&&line.back()=='\r')line.pop_back();
  std::string expected="case_id";std::istringstream names(furnace_variable_list);std::string n;
  while(names>>n)expected+=","+n;
  require(line==expected,"CSV header/schema mismatch");
  std::vector<Row> all;size_t lineNo=1;
  while(std::getline(file,line)){
    ++lineNo;if(!line.empty()&&line.back()=='\r')line.pop_back();
    require(!line.empty()&&line.back()!=',',"Empty/trailing CSV field at line "+std::to_string(lineNo));
    std::stringstream input(line);std::string cell;std::vector<std::string> parts;
    while(std::getline(input,cell,','))parts.push_back(cell);
    require(parts.size()==26,"Expected 26 CSV columns at line "+std::to_string(lineNo));
    Row row;row.id=parts[0];require(std::regex_match(row.id,std::regex("[A-Za-z0-9_-]{1,45}")),"Invalid case ID");
    for(size_t i=0;i<25;++i)row.x[i]=fromSdk(parts[i+1],row.id+" variable "+std::to_string(i));
    validate(row);all.push_back(row);require(all.size()<=500000,"Too many input rows");
  }
  require(!all.empty(),"No rows supplied");return all;
}
void conversionSelfTest(){
  for(const char* s:{"0","+.25","-3.14E+10","0.00000001","5."}){
    const double x=fromSdk(s,"selftest");
    require(literal(toSdk(x)),"Original SDK numeric conversion selftest failed");
  }
  for(const char* s:{"","NaN","Inf","12_34","1,2","1+2"," 2","0xAA"})
    require(!literal(s),"Noncanonical input passed lexical validation");
  bool failed=false;try{fromSdk("1e999999","overflow");}catch(...){failed=true;}
  require(failed,"Overflow was silently accepted");
}
void operatorSelfTest(){
  struct Test{const char* ex;std::array<double,3> result;};
  const Test tests[]={
   {"(-1) % 10",{{-1,-1,-1}}},{"(-1) mod 10",{{9,9,9}}},
   {"4 min 5",{{4,4,4}}},{"4 max 5",{{5,5,5}}},
   {"((x <= (2*y)) AND (z >= 0))",{{1,1,0}}},
   {"((NOT(x = y)) OR (z <> 0))",{{0,1,1}}},
   {"((x = y) XOR (z <> 0))",{{1,0,1}}}};
  const double x[][3]={{1,1,0},{-1,1,0},{2,1,-1}};
  for(const Test& test:tests){
    PACEVAL_HANDLE g=paceval_CreateComputation(test.ex,3,"x y z",false,nullptr);
    require(g&&!paceval_GetIsError(g),"Local operator graph creation failed");
    for(size_t i=0;i<3;++i){
      double v[3]={x[i][0],x[i][1],x[i][2]};
      double out=paceval_dGetComputationResult(g,v,nullptr,nullptr);
      require(!paceval_GetIsError(g)&&out==test.result[i],"Local operator mismatch");
    }paceval_DeleteComputation(g);
  }
}
GraphHandles graphInit(){
  GraphHandles graphs;
  for(size_t i=0;i<furnace_graph_count;++i){
    PACEVAL_HANDLE h=paceval_CreateComputation(furnace_graphs[i].expression,(unsigned long)furnace_variable_count,furnace_variable_list,false,nullptr);
    require(h&&!paceval_GetIsError(h),std::string("Cannot register paceval graph ")+furnace_graphs[i].id);
    graphs.h.push_back(h);
  }
  return graphs;
}
bool closeEnough(double actual,double ref){return std::isfinite(actual)&&std::abs(actual-ref)<=1e-8*(1+std::abs(ref));}
void independentCheck(const Row& row,const double* y){
  const auto& v=row.x;
  const double fuel=v[0]*v[1]*v[2],dt=v[6]-v[5];
  const double load1=v[3]*v[4]*dt,load2=v[3]*v[4]*(dt+v[7]*dt*dt/2);
  const double conv=v[8]*v[9]*(v[10]-v[11]);
  const double rad=v[12]*v[13]*v[9]*(std::pow(v[10],4)-std::pow(v[11],4));
  const double exhaust=v[14]*v[15]*(v[16]-v[11]);
  const double m1=fuel-(load1+conv+rad+exhaust);
  const double m2=fuel-(load2+conv+rad+(1-v[17])*exhaust);
  const double co2=v[0]*v[18], nox=v[19]*v[20]*.000001;
  const double cm=v[21]-co2,nm=v[22]-nox,fm=v[23]-v[0],tm=v[24]-v[6];
  int g1=(m1>=0&&cm>=0&&nm>=0&&fm>=0&&tm>=0)?1:0;
  int g2=(m2>=0&&cm>=0&&nm>=0&&fm>=0&&tm>=0)?1:0;
  const double score=std::min({m2/fuel,cm/v[21],nm/v[22],fm/v[23],tm/v[24]});
  const struct Check {size_t idx;double val;} checks[]={
   {0,fuel},{1,load1},{2,load2},{3,conv},{4,rad},{5,exhaust},{6,v[17]*exhaust},
   {8,load1+conv+rad+exhaust},{9,load2+conv+rad+(1-v[17])*exhaust},{10,m1},{11,m2},
   {15,co2},{16,nox},{21,double(g1)},{22,double(g2)},{23,score}};
  for(const auto& c:checks)
    require(closeEnough(y[c.idx],c.val),row.id+": native independent equation differs: "+furnace_graphs[c.idx].id);
}
std::vector<double> evaluateBatch(const GraphHandles& graph,const std::vector<Row>& rows){
  size_t N=rows.size(),G=graph.h.size();std::vector<double> packed(N*25),raw(N*G),result(N*G);
  std::vector<int> error(N*G,-1);
  for(size_t i=0;i<N;++i)for(size_t j=0;j<25;++j)packed[i*25+j]=rows[i].x[j];
  const bool errorFlag=paceval_dGetMultipleComputationsResultsExt(
     const_cast<PACEVAL_HANDLE*>(graph.h.data()),(unsigned long)G,packed.data(),(unsigned long)N,
     raw.data(),nullptr,nullptr,error.data());
  require(!errorFlag,"Batch SDK returned failure");
  for(auto e:error)require(e==0,"Batch SDK returned nonzero per-point error");
  bool graphMajor=true,rowMajor=true;
  for(size_t i=0;i<std::min(N,size_t(6));++i){
    double probe=paceval_dGetComputationResult(graph.h[0],packed.data()+25*i,nullptr,nullptr);
    require(!paceval_GetIsError(graph.h[0]),"SDK scalar layout test failed");
    graphMajor &= closeEnough(raw[i],probe);rowMajor &= closeEnough(raw[i*G],probe);
  }
  require(graphMajor||rowMajor,"Unknown SDK batch result layout");
  for(size_t i=0;i<N;++i)for(size_t j=0;j<G;++j){
    double x=raw[graphMajor?j*N+i:i*G+j];
    require(std::isfinite(x),"Nonfinite batch output");result[i*G+j]=x;
  }
  for(size_t i=0;i<N;++i)independentCheck(rows[i],result.data()+i*G);
  return result;
}
}
int main(int argc,char** argv){
  try{
    require(argc==3,"Usage: industrial_furnace_paceval <synthetic_operating_points.csv> <output.csv>");
    conversionSelfTest();operatorSelfTest();
    std::vector<Row> rows=loadCSV(argv[1]);GraphHandles gs=graphInit();
    auto result=evaluateBatch(gs,rows);
    std::ofstream out(argv[2]);out.imbue(std::locale::classic());require(bool(out),"Cannot create output CSV");
    out<<"case_id";for(size_t i=0;i<furnace_graph_count;++i)out<<','<<furnace_graphs[i].id;out<<'\n';
    out<<std::setprecision(17);
    for(size_t i=0;i<rows.size();++i){out<<rows[i].id;for(size_t j=0;j<furnace_graph_count;++j)out<<','<<result[i*furnace_graph_count+j];out<<'\n';}
    std::cout<<"Local SDK batch completed: "<<rows.size()<<" inputs * "<<furnace_graph_count<<" graphs.\n";
    return 0;
  }catch(const std::exception& e){std::cerr<<"FAILED: "<<e.what()<<'\n';return 1;}
}
