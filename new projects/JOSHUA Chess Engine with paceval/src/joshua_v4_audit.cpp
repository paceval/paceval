// Execute the exact trained V4 network on held-out positions using local paceval.
// This tests all 12 hidden graphs and the fused output graph, independently
// against the separately implemented native C++ feedforward network.
#include "paceval_main.h"
#include "chess_rules.h"
#include "paceval_math.h"
#include "v4_paceval.h"
#include <fstream>
#include <sstream>
#include <iomanip>
using namespace std;
static vector<string> split(const string&s){vector<string>v;istringstream f(s);string z;while(getline(f,z,','))v.push_back(z);return v;}
int main(int argc,char**argv){
 try{
  insist(argc==4,"usage: joshua_v4_audit teacher.csv predictions.csv output.csv");
  ifstream source(argv[1]),pred(argv[2]);ofstream output(argv[3]);
  insist(source&&pred&&output,"Failed to open V4 audit files");
  string h1,h2;getline(source,h1);getline(pred,h2);auto a=split(h1),b=split(h2);
  insist(a.size()==54&&a[6]=="wp"&&a[53]=="bkingDanger","V4 teacher CSV header mismatch");
  insist(b.size()==8&&b[1]=="split","V4 prediction metadata header mismatch");
  vector<vector<double>>records;vector<double>original;vector<string>ids,fenStr;
  string l1,l2;int sourceRows=0;
  while(getline(source,l1)){
   insist(bool(getline(pred,l2)),"Training and prediction row count mismatch");
   auto s=split(l1),p=split(l2);insist(s.size()==54&&p.size()==8,"V4 malformed CSV row");
   sourceRows++;
   insist(s[0]==p[0]&&s[2]==p[2],"V4 prediction FEN and game mismatch");
   if(p[1]!="test")continue;
   if(records.size()>=110)continue;
   vector<double>x;for(int j=6;j<54;j++)x.push_back(stod(s[j]));
   records.push_back(std::move(x));original.push_back(stod(s[4]));
   ids.push_back(s[0]+"_"+s[1]);fenStr.push_back(s[2]);
  }
  insist(records.size()>=100&&sourceRows>=1700,"Insufficient held-out V4 test cases");
  Engine e;e.probe();EvaluatorV3 classical(e);NeuralV4 nn(e);
  vector<vector<double>>v3inputs;for(const auto&x:records)v3inputs.emplace_back(x.begin(),x.begin()+32);
  const auto classic=e.multi(classical.handles(),v3inputs);
  vector<double>base;
  for(size_t i=0;i<records.size();i++){
    double b=classic[i][classical.by.at("SCORE")];near(b,scoreNativeV3(v3inputs[i]),1e-12);
    near(b,original[i],1e-12);base.push_back(b);
  }
  auto result=nn.scoreBatch(records,base);
  output<<"case,fen,paceval_score,native_score,v3_score";
  for(const auto&name:featureNamesV4)output<<','<<name;
  output<<'\n'<<setprecision(17);
  for(size_t i=0;i<result.size();i++){
    const double reference=nn.independent(records[i],base[i]);
    output<<ids[i]<<','<<fenStr[i]<<','<<result[i]<<','<<reference<<','<<base[i];
    for(double v:records[i])output<<','<<v;
    output<<'\n';
  }
  insist(nn.checked==records.size(),"Neural paceval verification count mismatch");
  cout<<"V4_PACEVAL_AUDIT_PASS heldout="<<records.size()<<" trained_graphs="<<V4_HIDDEN+1
      <<" total_graphs="<<e.owned.size()<<" graph_points="<<e.graphPoints<<'\n';
  return 0;
 }catch(const exception&ex){cerr<<"V4_AUDIT_FAILED "<<ex.what()<<'\n';return 1;}
}
