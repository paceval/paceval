#pragma once
// Reloadable V4 evaluation augmentation. The persistent graph computes the
// complete base + correction score using the authentic paceval C API.
// Only a fixed mathematical basis and bounded numeric coefficients are accepted.
// Untrusted text cannot inject free-form paceval expressions.
#include <fstream>
#include <array>
#include <regex>
#include <iomanip>
#include <sstream>
#include <filesystem>
#include <map>
#include <limits>
namespace joshua_adapt {
static const std::array<std::pair<const char*,const char*>,8> TERMS = {{
 {"mobility","(wmob-bmob)"}, {"captures","(wcaps-bcaps)"},
 {"hanging","(bhanging-whanging)"}, {"attacked","(battacked-wattacked)"},
 {"passed","(wpassed-bpassed)"}, {"kingdanger","(bkingDanger-wkingDanger)"},
 {"queenthreat","(bqueenThreat-wqueenThreat)"}, {"rookthreat","(brookThreat-wrookThreat)"}
}};
// V11: whitelisted nonlinear tactical templates. A promoted model may append
// terms without recompiling the engine. No user-controlled expression syntax
// is passed to the paceval parser.
static const std::array<std::pair<const char*,const char*>,10> EXTRA_TERMS = {{
 {"king_alarm","((bkingDanger*bkingDanger)-(wkingDanger*wkingDanger))"},
 {"king_tactics","((bkingDanger*(1+bqueenThreat+brookThreat))-(wkingDanger*(1+wqueenThreat+wrookThreat)))"},
 {"hanging_pressure","((bhanging*bhanging)-(whanging*whanging))"},
 {"queen_exposure","((bqueenThreat*battacked)-(wqueenThreat*wattacked))"},
 {"rook_exposure","((brookThreat*battacked)-(wrookThreat*wattacked))"},
 {"check_pressure","(bcheck-wcheck)"},
 {"pawn_race","((wpassed*wpassed)-(bpassed*bpassed))"},
 {"active_captures","((wmob*wcaps)-(bmob*bcaps))"},
 {"king_check_combo","((bcheck*(1+bkingDanger+bqueenThreat))-(wcheck*(1+wkingDanger+wqueenThreat)))"},
 {"hanging_capture_combo","((bhanging*wcaps)-(whanging*bcaps))"}
}};
inline bool validNumber(const std::string& s) {
 static const std::regex pattern(R"(^[+-]?(?:[0-9]+(?:\.[0-9]{1,4})?|\.[0-9]{1,4})$)");
 return std::regex_match(s,pattern);
}
struct Spec {
 int version=0;
 std::array<double,8> weights{};
 std::map<std::string,double> extra;
 std::string expression;
};
inline Spec load(const std::string&file) {
 Spec s;
 if(file.empty())return s;
 std::ifstream in(file);if(!in)throw std::runtime_error("Adaptive graph file not found: "+file);
 std::map<std::string,std::string> values;std::string line;
 while(std::getline(in,line)){
  if(line.empty()||line[0]=='#')continue;
  auto tab=line.find('\t');
  if(tab==std::string::npos || line.find('\t',tab+1)!=std::string::npos)
    throw std::runtime_error("Invalid adaptive graph TSV layout");
  auto name=line.substr(0,tab),number=line.substr(tab+1);
  if(values.count(name))throw std::runtime_error("Duplicate adaptive coefficient: "+name);
  values[name]=number;
 }
 if(!values.count("version") || !std::regex_match(values["version"],std::regex("[0-9]{1,7}")))
  throw std::runtime_error("Invalid adaptive graph version");
 s.version=std::stoi(values["version"]);
 for(std::size_t i=0;i<TERMS.size();i++){
  auto it=values.find(TERMS[i].first);
  if(it==values.end()||!validNumber(it->second))throw std::runtime_error("Missing or invalid adaptive weight: "+std::string(TERMS[i].first));
  double w=std::stod(it->second);
  if(!std::isfinite(w)||std::abs(w)>32)throw std::runtime_error("Adaptive weight out of range");
  s.weights[i]=w;
 }
 // An absent template is an inactive term. Nonzero templates add real graph
 // nodes. Reject unknown keys and bound both coefficients and graph size.
 for(const auto& item:values){
  if(item.first=="version")continue;
  bool base=false;for(const auto&t:TERMS)if(item.first==t.first)base=true;
  if(base)continue;
  if(item.first.rfind("feature.",0)!=0)throw std::runtime_error("Unknown graph key: "+item.first);
  const std::string name=item.first.substr(8);
  bool known=false;for(const auto&t:EXTRA_TERMS)if(name==t.first)known=true;
  if(!known||!validNumber(item.second))throw std::runtime_error("Invalid nonlinear term: "+name);
  double w=std::stod(item.second);
  if(!std::isfinite(w)||std::abs(w)>8)throw std::runtime_error("Nonlinear coefficient out of range");
  if(w!=0)s.extra[name]=w;
 }
 if(s.extra.size()>6)throw std::runtime_error("Too many nonlinear graph terms");
 std::ostringstream expression;expression<<std::fixed<<std::setprecision(4);
 // Bound ONLY the correction, never the material/mate-aware base score.
 expression<<"(base+(((-160) max (0";
 for(std::size_t i=0;i<TERMS.size();i++)if(s.weights[i]!=0)
  expression<<"+("<<s.weights[i]<<"*"<<TERMS[i].second<<")";
 for(const auto&t:EXTRA_TERMS){auto it=s.extra.find(t.first);
  if(it!=s.extra.end())expression<<"+("<<it->second<<"*"<<t.second<<")";
 }
 expression<<")) min 160))";
 s.expression=expression.str();
 if(s.expression.size()>8192)throw std::runtime_error("Adaptive graph expression too large");
 return s;
}
struct Graph {
 Engine& e;
 Spec spec;
 PACEVAL_HANDLE h{};
 std::size_t evaluations=0;
 explicit Graph(Engine&engine,const std::string&file):e(engine),spec(load(file)){
   if(!file.empty()) {
    std::vector<std::string> vars=featureNamesV4;
    vars.push_back("base");
    h=e.create(spec.expression,vars);
   }
 }
 void exportFiles(const std::string& directory)const {
  namespace fs=std::filesystem;
  fs::create_directories(directory);
  {std::ofstream f(fs::path(directory)/"paceval_graph.txt");
   if(!f)throw std::runtime_error("Cannot export paceval_graph.txt");
   f<<"# Actual whitelisted adaptive paceval graph registered in this Joshua run\n";
   f<<"version="<<spec.version<<"\n";
   f<<"feature_count=48\n";
   f<<"input_variables=";for(const auto&v:featureNamesV4)f<<v<<",";f<<"base\n";
   f<<"expression="<<spec.expression<<"\n";
   f<<"note=Score is white-oriented centipawns; correction bounded to [-160,+160].\n";
  }
  {std::ofstream f(fs::path(directory)/"paceval_graph_terms.csv");
   if(!f)throw std::runtime_error("Cannot export paceval_graph_terms.csv");
   f<<"version,category,term,coefficient,paceval_expression\n";
   f<<spec.version<<",base,base,1,base\n";
   for(std::size_t i=0;i<TERMS.size();++i)f<<spec.version<<",linear,"<<TERMS[i].first<<","<<spec.weights[i]<<",\""<<TERMS[i].second<<"\"\n";
   for(const auto&t:EXTRA_TERMS){auto it=spec.extra.find(t.first);if(it!=spec.extra.end())
    f<<spec.version<<",nonlinear,"<<t.first<<","<<it->second<<",\""<<t.second<<"\"\n";
   }
  }
 }
 bool active()const{return h!=nullptr;}
 double one(const std::vector<double>&features,double base){
  if(!active())return base;
  if(features.size()!=48||!std::isfinite(base))throw std::runtime_error("Invalid adaptive graph inputs");
  std::vector<double> in=features;in.push_back(base);
  ++evaluations;return e.eval(h,in);
 }
 std::vector<double> batch(const std::vector<std::vector<double>>&features,const std::vector<double>&base){
  if(!active())return base;
  if(features.size()!=base.size())throw std::runtime_error("Adaptive batch mismatch");
  std::vector<std::vector<double>> rows;
  for(std::size_t i=0;i<features.size();i++){
   if(features[i].size()!=48||!std::isfinite(base[i]))throw std::runtime_error("Invalid adaptive batch row");
   rows.push_back(features[i]);rows.back().push_back(base[i]);
  }
  evaluations+=rows.size();return e.single(h,rows);
 }
};
} // namespace joshua_adapt
