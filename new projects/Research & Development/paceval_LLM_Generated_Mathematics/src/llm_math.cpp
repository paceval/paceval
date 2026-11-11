// paceval: Evaluating LLM-Generated Mathematical Expressions (offline C++17 pilot)
//
// SECURITY BOUNDARY
// An LLM's proposed formula is UNTRUSTED INPUT. This program implements its
// own bounded grammar, allowed symbols and numerical-domain checks BEFORE
// creating any paceval computation object. It does not run a shell, compiler,
// code-generation hook, network service, Python eval, or arbitrary native code.
// These checks are a research prototype, not a production security sandbox.
// Production deployment also requires process isolation, quotas and reviews.
//
// RESPONSIBILITIES
// paceval: graph creation and reuse; multi-input evaluation; optional TINC.
// C++ host: grammar allowlist; evaluation/domain checks; dataset handling;
//           independent tree interpreter; comparison; report and handle lifetime.
// The 200 synthetic formula strings are representative LLM-like proposals;
// they are NOT sampled from or scored against a live LLM.
//
// SDK: the original paceval_main.h is included and paceval_main.cpp is linked
// into the executable, together with the separately supplied .so.

#include "paceval_main.h"
#include <algorithm>
#include <array>
#include <cctype>
#include <cmath>
#include <cstdlib>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <limits>
#include <map>
#include <memory>
#include <set>
#include <sstream>
#include <stdexcept>
#include <string>
#include <utility>
#include <vector>

namespace pilot {
constexpr unsigned long NVAR=6;
constexpr const char* VAR_NAMES="x y t k w c";
// These limits apply ONLY to untrusted LLM submissions, not to paceval.
constexpr std::size_t MAX_EXPRESSION_LENGTH=180,MAX_NODES=80;
constexpr int MAX_DEPTH=16;
constexpr std::size_t MAX_BATCH=512;
using Vars=std::array<double,6>;
struct Reject:std::runtime_error { std::string code;
  Reject(const std::string& s):std::runtime_error(s),code(s) {} };
void require(bool ok,const std::string&msg){if(!ok)throw std::runtime_error(msg);}
struct Case { std::string id,category,expected,expr; };

// Only simple, unquoted CSV is accepted. Corpus generation quotes nothing;
// malformed or adversarial quoting is rejected at the data boundary.
std::vector<std::string> split(const std::string& s){
  std::vector<std::string> out;std::stringstream ss(s);std::string cell;
  while(std::getline(ss,cell,',')) {if(!cell.empty()&&cell.back()=='\r')cell.pop_back();out.push_back(cell);}
  return out;
}
std::vector<Case> read_cases(const std::string&file){
  std::ifstream in(file);require(in.good(),"Cannot open casebook: "+file);
  std::string line;std::vector<Case> data;std::set<std::string> ids;
  require(bool(std::getline(in,line)),"Missing casebook header");if(!line.empty()&&line.back()=='\r')line.pop_back();require(line=="case_id,category,expected_status,expression","Invalid casebook header");
  while(std::getline(in,line)){
    if(line.empty())continue;
    auto c=split(line);require(c.size()==4,"Invalid expression case CSV row");
    require(!c[0].empty()&&ids.insert(c[0]).second,"Duplicate/empty case ID");
    data.push_back({c[0],c[1],c[2],c[3]});
  }
  require(data.size()==200,"This reference dataset has exactly 200 cases");return data;
}
double finite_number(const std::string&s){
  std::size_t n=0;double v=0;
  try {v=std::stod(s,&n);}catch(...){throw std::runtime_error("Invalid numeric input: "+s);}
  require(n==s.size()&&std::isfinite(v),"Nonfinite or malformed input");return v;
}
std::vector<Vars> read_sweep(const std::string&file){
  std::ifstream in(file);require(in.good(),"Cannot open sample values");
  std::string line;require(bool(std::getline(in,line)),"Missing sweep header");if(!line.empty()&&line.back()=='\r')line.pop_back();require(line=="sample,x,y,t,k,w,c","Invalid sweep header");
  std::vector<Vars> result;int sample=0;
  while(std::getline(in,line)){
    if(line.empty())continue;
    auto cols=split(line);require(cols.size()==7,"Sweep requires 7 columns");
    require(cols[0]==std::to_string(sample),"Sweep samples must be contiguous");
    Vars v{};for(int j=0;j<6;++j)v[j]=finite_number(cols[j+1]);
    // Explicit finite operating envelope. No user-supplied per-case state.
    require(std::abs(v[0])<=1&&std::abs(v[1])<=1&&v[2]>=0&&v[2]<=2&&v[3]>=0&&v[3]<=2&&v[4]>=0&&v[4]<=4&&std::abs(v[5])<=1,"Sample out of domain");
    result.push_back(v);++sample;
  }
  require(result.size()==16,"Expect exactly 16 versioned input samples");return result;
}
// Parser generates a bounded, independent AST; paceval receives the literal
// original expression only after every sample in the fixed evaluation envelope
// has been checked by this interpreter.
enum class Op {Literal,Variable,Add,Sub,Mul,Div,Neg,Sin,Cos,Exp,Ln,Sqrt,Tanh,Square,Cube};
struct Node {
  Op op;double number=0;int variable=-1;
  std::unique_ptr<Node> left,right;
  explicit Node(Op o):op(o){}
};
struct Parser {
  const std::string& s;std::size_t p=0,nodes=0;
  explicit Parser(const std::string& text):s(text){
    if(s.size()>MAX_EXPRESSION_LENGTH)throw Reject("RESOURCE_LIMIT");
    if(s.empty())throw Reject("SYNTAX_ERROR");
    for(unsigned char c:s){
      if(c>=128||(!std::isalnum(c)&&c!='_'&&c!='.'&&c!='+'&&c!='-'&&c!='*'&&c!='/'&&c!='^'&&c!='('&&c!=')'&&c!=' '))
        throw Reject("UNSAFE_CHARACTER");
    }
  }
  void ws(){while(p<s.size()&&s[p]==' ')++p;}
  bool eat(char ch){ws();if(p<s.size()&&s[p]==ch){++p;return true;}return false;}
  std::unique_ptr<Node> make(Op op,std::unique_ptr<Node> a=nullptr,std::unique_ptr<Node>b=nullptr){
    if(++nodes>MAX_NODES)throw Reject("RESOURCE_LIMIT");
    auto n=std::make_unique<Node>(op);n->left=std::move(a);n->right=std::move(b);return n;
  }
  std::unique_ptr<Node> expr(int depth){
    auto a=term(depth+1);
    for(;;){if(eat('+'))a=make(Op::Add,std::move(a),term(depth+1));
      else if(eat('-'))a=make(Op::Sub,std::move(a),term(depth+1));else return a;}
  }
  std::unique_ptr<Node> term(int depth){
    auto a=unary(depth+1);
    for(;;){if(eat('*'))a=make(Op::Mul,std::move(a),unary(depth+1));
      else if(eat('/'))a=make(Op::Div,std::move(a),unary(depth+1));else return a;}
  }
  std::unique_ptr<Node> unary(int depth){
    if(depth>MAX_DEPTH)throw Reject("RESOURCE_LIMIT");
    if(eat('-'))return make(Op::Neg,unary(depth+1));
    if(eat('+'))return unary(depth+1);
    auto a=atom(depth+1);
    if(eat('^')) {ws();if(p>=s.size()||(s[p]!='2'&&s[p]!='3'))throw Reject("SYNTAX_ERROR");
      char n=s[p++];a=make(n=='2'?Op::Square:Op::Cube,std::move(a));}
    return a;
  }
  std::unique_ptr<Node> atom(int depth){
    if(depth>MAX_DEPTH)throw Reject("RESOURCE_LIMIT");
    ws();
    if(eat('(')){auto a=expr(depth+1);if(!eat(')'))throw Reject("SYNTAX_ERROR");return a;}
    if(p>=s.size())throw Reject("SYNTAX_ERROR");
    if(std::isdigit(static_cast<unsigned char>(s[p]))||s[p]=='.'){
      std::size_t begin=p, digits=0;
      while(p<s.size()&&(std::isdigit(static_cast<unsigned char>(s[p]))||s[p]=='.')){if(std::isdigit(static_cast<unsigned char>(s[p])))++digits;++p;}
      if(digits==0)throw Reject("SYNTAX_ERROR");
      auto token=s.substr(begin,p-begin);std::size_t used=0;double number=0;
      try{number=std::stod(token,&used);}catch(...){throw Reject("SYNTAX_ERROR");}
      if(used!=token.size()||!std::isfinite(number))throw Reject("SYNTAX_ERROR");
      auto a=make(Op::Literal);a->number=number;return a;
    }
    if(std::isalpha(static_cast<unsigned char>(s[p]))||s[p]=='_'){
      std::size_t begin=p;
      while(p<s.size()&&(std::isalnum(static_cast<unsigned char>(s[p]))||s[p]=='_'))++p;
      auto token=s.substr(begin,p-begin);ws();
      if(eat('(')){
        const std::map<std::string,Op> fn={{"sin",Op::Sin},{"cos",Op::Cos},{"exp",Op::Exp},{"ln",Op::Ln},{"sqrt",Op::Sqrt},{"tanh",Op::Tanh}};
        auto it=fn.find(token);if(it==fn.end())throw Reject("UNAPPROVED_FUNCTION");
        auto a=expr(depth+1);if(!eat(')'))throw Reject("SYNTAX_ERROR");return make(it->second,std::move(a));
      }
      const std::string vars[]={"x","y","t","k","w","c"};
      for(int j=0;j<6;++j)if(token==vars[j]){auto a=make(Op::Variable);a->variable=j;return a;}
      throw Reject("UNKNOWN_VARIABLE");
    }
    throw Reject("SYNTAX_ERROR");
  }
  std::unique_ptr<Node> parse(){auto root=expr(0);ws();if(p!=s.size())throw Reject("SYNTAX_ERROR");return root;}
};
// Strict finite-domain semantics. The same operating envelope is enforced for
// the reference and for paceval; bad cases never reach vendor execution.
double evaluate(const Node& n,const Vars&v){
  auto left=[&](){return evaluate(*n.left,v);};
  auto binary=[&](auto op){return op(evaluate(*n.left,v),evaluate(*n.right,v));};
  double x=0;
  switch(n.op){
    case Op::Literal:return n.number;case Op::Variable:return v[n.variable];
    case Op::Add:x=binary([](double a,double b){return a+b;});break;
    case Op::Sub:x=binary([](double a,double b){return a-b;});break;
    case Op::Mul:x=binary([](double a,double b){return a*b;});break;
    case Op::Div:{double a=left(),b=evaluate(*n.right,v);if(std::abs(b)<1e-10)throw Reject("DOMAIN_ERROR");x=a/b;break;}
    case Op::Neg:x=-left();break;
    case Op::Sin:x=std::sin(left());break;case Op::Cos:x=std::cos(left());break;
    case Op::Exp:{double a=left();if(a>40||a< -40)throw Reject("DOMAIN_ERROR");x=std::exp(a);break;}
    case Op::Ln:{double a=left();if(a<=1e-10)throw Reject("DOMAIN_ERROR");x=std::log(a);break;}
    case Op::Sqrt:{double a=left();if(a<0)throw Reject("DOMAIN_ERROR");x=std::sqrt(a);break;}
    case Op::Tanh:x=std::tanh(left());break;
    case Op::Square:{double a=left();x=a*a;break;}
    case Op::Cube:{double a=left();x=a*a*a;break;}
  }
  if(!std::isfinite(x)||std::abs(x)>1e12)throw Reject("DOMAIN_ERROR");
  return x;
}
struct Prepared {
  std::string status;std::unique_ptr<Node> ast;
  std::vector<double> reference;
};
Prepared validate(const Case&c,const std::vector<Vars>&sweep){
  Prepared p;
  try{
    Parser parser(c.expr);p.ast=parser.parse();
    for(const auto& v:sweep)p.reference.push_back(evaluate(*p.ast,v));
    p.status="OK";
  }catch(const Reject& e){p.status=e.code;p.ast.reset();p.reference.clear();}
  return p;
}
class Runtime {
  bool initialized=false;std::vector<PACEVAL_HANDLE> handles;
public:
  Runtime(){require(paceval_InitializeLibrary(nullptr),"paceval_InitializeLibrary failed");initialized=true;}
  Runtime(const Runtime&)=delete;Runtime&operator=(const Runtime&)=delete;
  ~Runtime(){for(auto it=handles.rbegin();it!=handles.rend();++it)paceval_DeleteComputation(*it);if(initialized)paceval_FreeLibrary();}
  // The generic API takes an application-selected number of variables.
  // Do not impose the six-variable untrusted-parser limit on reviewed models.
  PACEVAL_HANDLE create_dynamic(const std::string&expr,
      const std::string&var_names,unsigned long variable_count,bool interval=false){
    auto h=paceval_CreateComputation(expr.c_str(),variable_count,var_names.c_str(),interval,nullptr);
    require(h!=nullptr,"paceval_CreateComputation failed for "+expr);
    handles.push_back(h);
    require(!paceval_GetIsError(h),"paceval graph error for reviewed expression");return h;
  }
  PACEVAL_HANDLE create(const std::string&expr,bool interval=false){
    return create_dynamic(expr,VAR_NAMES,NVAR,interval);
  }
  // Row-major variable samples; the original paceval batch API receives the
  // complete variable set for each sample, with a caller-selected stride.
  std::vector<double> batch_dynamic(PACEVAL_HANDLE h,
      const std::vector<std::vector<double>>&samples,
      std::size_t variable_count,std::size_t batch_size){
    require(variable_count>0&&batch_size>0,"Invalid reviewed-model dimensions");
    std::vector<double> results;results.reserve(samples.size());
    for(std::size_t k=0;k<samples.size();k+=batch_size){
      std::size_t n=std::min(batch_size,samples.size()-k);
      std::vector<double> values;values.reserve(n*variable_count);
      for(std::size_t j=0;j<n;++j){
        require(samples[k+j].size()==variable_count,"Incorrect model value count");
        for(double value:samples[k+j]){
          require(std::isfinite(value),"Nonfinite reviewed-model value");
          values.push_back(value);
        }
      }
      std::vector<double> out(n);std::vector<int> errors(n,-1);
      // Return TRUE means one or more batch errors in SDK 4.25.
      bool has_errors=paceval_dGetComputationResultExt(h,values.data(),
           static_cast<unsigned long>(n),out.data(),nullptr,nullptr,errors.data());
      require(!has_errors,"Reviewed-model paceval batch error");
      for(std::size_t j=0;j<n;++j){
        require(errors[j]==PACEVAL_ERR_NO_ERROR&&std::isfinite(out[j]),
                "Invalid reviewed-model batch element");
        results.push_back(out[j]);
      }
    }
    require(!paceval_GetIsError(h),"Reviewed-model graph error");
    return results;
  }
  std::vector<double> batch(PACEVAL_HANDLE h,const std::vector<Vars>&vs,std::size_t batch_size){
    std::vector<double> results;results.reserve(vs.size());
    for(std::size_t k=0;k<vs.size();k+=batch_size){
      std::size_t n=std::min(batch_size,vs.size()-k);std::vector<double> inputs;inputs.reserve(n*NVAR);
      for(std::size_t j=0;j<n;++j)for(double x:vs[k+j])inputs.push_back(x);
      std::vector<double> out(n);std::vector<int> errors(n,-1);
      // In SDK 4.25 this BOOL reports that errors occurred, not success.
      bool error=paceval_dGetComputationResultExt(h,inputs.data(),static_cast<unsigned long>(n),out.data(),nullptr,nullptr,errors.data());
      require(!error,"paceval_dGetComputationResultExt returned error");
      for(std::size_t j=0;j<n;++j)require(errors[j]==PACEVAL_ERR_NO_ERROR&&std::isfinite(out[j]),"Invalid paceval batch element");
      results.insert(results.end(),out.begin(),out.end());
    }
    require(!paceval_GetIsError(h),"Graph error after batch");return results;
  }
  std::array<double,3> interval(PACEVAL_HANDLE h,Vars v){
    double lo=0,hi=0;double value=paceval_dGetComputationResult(h,v.data(),&lo,&hi);
    require(!paceval_GetIsError(h)&&std::isfinite(value)&&std::isfinite(lo)&&std::isfinite(hi)&&lo<=hi,"Invalid TINC result");
    return {value,lo,hi};
  }
};
// REVIEWED MODEL DEMONSTRATION (not exposed to the untrusted agent protocol)
//
// paceval has no intrinsic 180-character or six-variable restriction.
// In contrast, the *untrusted* AST parser above intentionally does.
// This separate path demonstrates a model approved by the application owner:
// the supplied file MUST exactly match the canonical mathematical model
// generated below. A caller cannot opt out of untrusted validation by adding
// a flag to the JSON tool adapter or by choosing arbitrary expression text.
// This is an illustrative exact-equality approval procedure, not a signature,
// code-signing system or general-purpose scientific formula validator.
constexpr std::size_t REVIEWED_VARIABLES = 48; // Chosen test size, NOT a paceval limit.
constexpr std::size_t REVIEWED_SAMPLES = 16;
struct ReviewedModel { std::string id,variables,expression; };
ReviewedModel canonical_reviewed_model(){
  ReviewedModel m;
  m.id="weighted_features_v1";
  for(std::size_t i=0;i<REVIEWED_VARIABLES;++i){
    if(i){m.variables+=' ';m.expression+='+';}
    const std::string v="v"+std::to_string(i);
    m.variables+=v;
    // Deliberately long, mathematically explicit sum of linear and
    // quadratic terms. The original SDK supports the dynamic variable list.
    m.expression+="(("+std::to_string(i%7+1)+"*"+v+"/1000)+("+v+"*"+v+"/10))";
  }
  return m;
}
ReviewedModel read_reviewed_manifest(const std::string&file){
  std::ifstream in(file);require(in.good(),"Cannot read approved model manifest");
  std::string a,b,c,extra;
  require(bool(std::getline(in,a))&&bool(std::getline(in,b))&&
          bool(std::getline(in,c))&&!std::getline(in,extra),
          "Approved model manifest must contain exactly three lines");
  // Accept LF or CRLF line endings from Git checkouts while requiring that
  // the semantic manifest bytes are exactly the reviewed expression.
  for(std::string* line:{&a,&b,&c})
    if(!line->empty()&&line->back()=='\r')line->pop_back();
  const ReviewedModel known=canonical_reviewed_model();
  require(a=="model_id="+known.id&&b=="variables="+known.variables&&
          c=="expression="+known.expression,
          "Reviewed model does not match owner-approved versioned definition");
  return known;
}
std::vector<double> reviewed_sample(std::size_t sample){
  std::vector<double> v(REVIEWED_VARIABLES);
  // Every input is an exactly representable binary rational. This makes
  // independent high-precision reproduction straightforward.
  for(std::size_t i=0;i<v.size();++i)
    v[i]=double(sample+1)/64.0+double(i%7)/256.0;
  return v;
}
double reviewed_native_reference(const std::vector<double>&v){
  double result=0;
  for(std::size_t i=0;i<v.size();++i)
    result+=(double(i%7+1)*v[i]/1000.0)+(v[i]*v[i]/10.0);
  return result;
}
void run_reviewed_model(const std::string&manifest,const std::string&output){
  const ReviewedModel m=read_reviewed_manifest(manifest);
  std::vector<std::vector<double>> samples;
  for(std::size_t j=0;j<REVIEWED_SAMPLES;++j)samples.push_back(reviewed_sample(j));
  Runtime rt;
  auto h=rt.create_dynamic(m.expression,m.variables,REVIEWED_VARIABLES);
  // Evaluate multiple input sets with ONE reusable paceval computation graph.
  const auto actual=rt.batch_dynamic(h,samples,REVIEWED_VARIABLES,7);
  std::ofstream out(output);require(out.good(),"Cannot open reviewed-model CSV output");
  out<<"sample,paceval_result,independent_cpp_reference,absolute_error\n"<<std::setprecision(17);
  double maximum_error=0;
  for(std::size_t j=0;j<samples.size();++j){
    double expected=reviewed_native_reference(samples[j]);
    double error=std::abs(actual[j]-expected);
    require(error<=3e-11*(1+std::abs(expected)),"Reviewed model reference mismatch");
    maximum_error=std::max(maximum_error,error);
    out<<j<<','<<actual[j]<<','<<expected<<','<<error<<'\n';
  }
  require(out.good(),"Unable to write reviewed-model CSV");
  std::cout<<"PASS approved_model="<<m.id
     <<" expression_characters="<<m.expression.size()
     <<" variables="<<REVIEWED_VARIABLES
     <<" input_samples="<<REVIEWED_SAMPLES
     <<" max_absolute_error="<<std::setprecision(10)<<maximum_error<<'\n';
}

// Long-lived standard-input service for *already bounded* expressions.
// This is a local line protocol, not MCP/HTTP. The Python contract adapter
// sends one ASCII expression plus six numbers per line, separated by a TAB.
// Graph handles are cached and automatically released with Runtime (RAII).
// It gives repeated tool calls a real common library lifetime, unlike running
// a new process for every request. Only the host may choose the formula.
void run_stream(){
  Runtime runtime;
  std::map<std::string,PACEVAL_HANDLE> graph_cache;
  std::string line;
  std::size_t n=0;
  while(std::getline(std::cin,line)){
    if(line.empty())continue;
    if(++n>256)throw std::runtime_error("Maximum 256 requests per process");
    try{
      if(line.size()>400)throw Reject("RESOURCE_LIMIT");
      auto tab=line.find('\t');
      if(tab==std::string::npos||line.find('\t',tab+1)!=std::string::npos)
        throw Reject("SYNTAX_ERROR");
      const auto expression=line.substr(0,tab);
      const auto fields=split(line.substr(tab+1));
      if(fields.size()!=6)throw Reject("SYNTAX_ERROR");
      Vars v{};
      for(int j=0;j<6;++j){
        try{v[j]=finite_number(fields[j]);}
        catch(const std::exception&){throw Reject("DOMAIN_ERROR");}
      }
      if(!(std::abs(v[0])<=1&&std::abs(v[1])<=1&&v[2]>=0&&v[2]<=2&&
           v[3]>=0&&v[3]<=2&&v[4]>=0&&v[4]<=4&&std::abs(v[5])<=1))
        throw Reject("DOMAIN_ERROR");
      auto prepared=validate(Case{"stream","agent","",expression},{v});
      if(prepared.status!="OK")throw Reject(prepared.status);
      auto it=graph_cache.find(expression);
      bool reused=(it!=graph_cache.end());
      if(!reused){
        if(graph_cache.size()>=32)throw Reject("RESOURCE_LIMIT");
        auto handle=runtime.create(expression);
        it=graph_cache.emplace(expression,handle).first;
      }
      const double result=runtime.batch(it->second,{v},1)[0];
      const double difference=std::abs(result-prepared.reference[0]);
      require(difference<=3e-11*(1+std::abs(prepared.reference[0])),
              "Independent numerical check failed");
      std::cout<<std::setprecision(17)
         <<"{\"status\":\"OK\",\"result\":"<<result
         <<",\"native_reference\":"<<prepared.reference[0]
         <<",\"absolute_error\":"<<difference
         <<",\"reused_graph\":"<<(reused?"true":"false")<<"}\n";
    }catch(const Reject& e){
      std::cout<<"{\"status\":\""<<e.code<<"\"}\n";
    }catch(const std::exception&){
      std::cout<<"{\"status\":\"BACKEND_ERROR\"}\n";
    }
    std::cout.flush();
  }
}

// Production integrations should enforce an additional caller-specific policy
// and isolate this interpreter/engine process. This interface is an offline
// demonstration, with one accepted expression evaluated at one parameter set.
void run_single(const std::string&expr,const std::string& csv_values){
  if(expr.empty())throw std::runtime_error("--formula must be nonempty");
  auto cols=split(csv_values);require(cols.size()==6,"--values requires six comma-separated doubles");
  Vars values{};
  for(int j=0;j<6;++j)values[j]=finite_number(cols[j]);
  require(std::abs(values[0])<=1&&std::abs(values[1])<=1&&values[2]>=0&&values[2]<=2&&
     values[3]>=0&&values[3]<=2&&values[4]>=0&&values[4]<=4&&std::abs(values[5])<=1,
     "Input outside documented envelope");
  Case c{"tool","interactive","",expr};
  auto validated=validate(c,{values});
  if(validated.status!="OK"){
    std::cout<<"{\"status\":\""<<validated.status<<"\"}\n";
    return;
  }
  Runtime rt;
  auto h=rt.create(expr);
  auto result=rt.batch(h,{values},1);
  double abs_error=std::abs(result[0]-validated.reference[0]);
  require(abs_error<=3e-11*(1+std::abs(validated.reference[0])),"Formula audit failed");
  std::cout<<std::setprecision(17)<<"{\"status\":\"OK\",\"result\":"<<result[0]
     <<",\"native_reference\":"<<validated.reference[0]<<",\"absolute_error\":"<<abs_error<<"}\n";
}
void native_tests(){
  Vars v={0.25,-0.3,0.4,0.6,1.2,0.1};
  auto check=[&](const std::string&s,const std::string&expect){
    Case c{"T","test",expect,s};Prepared p=validate(c,{v});require(p.status==expect,"Parser test failed: "+s+" got "+p.status);
  };
  check("exp(-k*t)*sin(w*t)+c","OK");check("sqrt(2+x*x)","OK");check("1/(t-t)","DOMAIN_ERROR");
  check("eval(x)","UNAPPROVED_FUNCTION");check("z+x","UNKNOWN_VARIABLE");check("x;exit(1)","UNSAFE_CHARACTER");
  check("x^y","SYNTAX_ERROR");check("ln(-1)","DOMAIN_ERROR");
  std::cout<<"PASS: parser, function allowlist, resource envelope and domain rejections\n";
}
void run(const std::string&cases,const std::string&sweep_file,const std::string&output,
         const std::string&tinc_file,std::size_t batch_size){
  require(batch_size>=1&&batch_size<=MAX_BATCH,"Batch size out of [1,512]");
  auto all=read_cases(cases);auto sweep=read_sweep(sweep_file);
  std::vector<Prepared> checked;std::map<std::string,int> counts;
  for(const auto& c:all){auto v=validate(c,sweep);
    require(c.expected==v.status,"Case "+c.id+": status "+v.status+" expected "+c.expected);
    ++counts[v.status];checked.push_back(std::move(v));
  }
  std::ofstream out(output);require(out.good(),"Cannot open results CSV");
  out<<"case_id,expected_status,status,sample,paceval_result,independent_cpp_reference,absolute_error\n"<<std::setprecision(17);
  std::ofstream ti(tinc_file);require(ti.good(),"Cannot open TINC CSV");
  ti<<"case_id,sample,expression,x,y,t,k,w,c,value,lower,upper\n"<<std::setprecision(17);
  Runtime runtime;std::size_t evaluations=0,violations=0,tinc_count=0;double max_error=0;
  for(std::size_t i=0;i<all.size();++i){
    const auto& c=all[i];const auto& valid=checked[i];
    if(valid.status!="OK"){
      out<<c.id<<','<<c.expected<<','<<valid.status<<",,,,\n";continue;
    }
    auto h=runtime.create(c.expr);
    auto results=runtime.batch(h,sweep,batch_size);
    for(std::size_t j=0;j<sweep.size();++j){
      double err=std::abs(results[j]-valid.reference[j]);
      ++evaluations;max_error=std::max(max_error,err);
      if(!std::isfinite(results[j])||err>3e-11*(1+std::abs(valid.reference[j])))++violations;
      out<<c.id<<','<<c.expected<<",OK,"<<j<<','<<results[j]<<','<<valid.reference[j]<<','<<err<<'\n';
    }
    // One TINC-enabled graph for each distinct family: choose the first
    // member of each family and three representative input points.
    if(i<10){
      auto t=runtime.create(c.expr,true);
      for(std::size_t j: {std::size_t(0),std::size_t(7),std::size_t(15)}){
        auto iv=runtime.interval(t,sweep[j]);
        ti<<c.id<<','<<j<<','<<c.expr;
        for(double v:sweep[j])ti<<','<<v;
        ti<<','<<iv[0]<<','<<iv[1]<<','<<iv[2]<<'\n';++tinc_count;
      }
    }
  }
  require(violations==0,"Mathematical reference audit failed");
  require(evaluations==160*sweep.size()&&tinc_count==30,"Unexpected result cardinality");
  std::cout<<"PASS cases="<<all.size()<<" accepted="<<counts["OK"]<<" rejected="<<all.size()-counts["OK"]
   <<" checked_evaluations="<<evaluations<<" violations="<<violations<<" TINC_samples="<<tinc_count
   <<" max_absolute_error="<<std::setprecision(10)<<max_error<<'\n';
  for(const auto& p:counts)std::cout<<"  "<<p.first<<" "<<p.second<<"\n";
}
}
int main(int argc,char**argv){
  try{
    std::string cases="../examples/expressions.csv",sweep="../examples/sweep.csv",out="evaluation.csv",tinc="tinc_samples.csv";
    bool self=false,stream=false;std::size_t batch=16;std::string formula,values,approved_model,approved_output="approved_model_results.csv";
    for(int i=1;i<argc;++i){
      std::string a=argv[i];
      if(a=="--self-test")self=true;
      else if(a=="--stream")stream=true;
      else if(a=="--formula"&&i+1<argc)formula=argv[++i];
      else if(a=="--approved-model"&&i+1<argc)approved_model=argv[++i];
      else if(a=="--approved-output"&&i+1<argc)approved_output=argv[++i];
      else if(a=="--values"&&i+1<argc)values=argv[++i];
      else if(a=="--cases"&&i+1<argc)cases=argv[++i];
      else if(a=="--sweep"&&i+1<argc)sweep=argv[++i];
      else if(a=="--output"&&i+1<argc)out=argv[++i];
      else if(a=="--tinc"&&i+1<argc)tinc=argv[++i];
      else if(a=="--batch"&&i+1<argc)batch=std::stoul(argv[++i]);
      else throw std::runtime_error("Unknown/incomplete argument: "+a);
    }
    if(!approved_model.empty()){
      pilot::require(!stream&&formula.empty(),"Reviewed mode cannot be mixed with untrusted interfaces");
      pilot::run_reviewed_model(approved_model,approved_output);return 0;
    }
    if(stream){pilot::run_stream();return 0;}
    if(!formula.empty()){pilot::run_single(formula,values);return 0;}
    pilot::native_tests();if(!self)pilot::run(cases,sweep,out,tinc,batch);
    return 0;
  }catch(const std::exception& e){std::cerr<<"FAIL: "<<e.what()<<'\n';return 1;}
}
