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
inline bool validNumber(const std::string& s) {
 static const std::regex pattern(R"(^[+-]?(?:[0-9]+(?:\.[0-9]{1,4})?|\.[0-9]{1,4})$)");
 return std::regex_match(s,pattern);
}
struct Spec {
 int version=0;
 std::array<double,8> weights{};
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
 if(values.size()!=TERMS.size()+1)throw std::runtime_error("Unrecognized adaptive graph coefficient");
 std::ostringstream expression;expression<<std::fixed<<std::setprecision(4);
 // Bound ONLY the correction, never the material/mate-aware base score.
 expression<<"(base+(((-160) max (0";
 for(std::size_t i=0;i<TERMS.size();i++)if(s.weights[i]!=0)
  expression<<"+("<<s.weights[i]<<"*"<<TERMS[i].second<<")";
 expression<<")) min 160))";
 s.expression=expression.str();
 if(s.expression.size()>4096)throw std::runtime_error("Adaptive graph expression too large");
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
