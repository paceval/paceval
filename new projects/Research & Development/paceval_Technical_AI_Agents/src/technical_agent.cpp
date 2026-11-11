// SPDX-License-Identifier: AGPL-3.0-or-later
// paceval Technical AI Agents: deterministic, allowlisted engineering mathematics.
//
// This is an OFFLINE tool-execution demonstrator, not an LLM and not an autonomous
// agent. The model/expression ID, declared units and finite numeric values are
// explicit tool arguments. The host checks the contract BEFORE calling paceval.
// No arbitrary formula text is executed. No network, commands, files or actuator
// operations are exposed through the mathematical tool interface.
//
// The original vendor SDK files paceval_main.h / paceval_main.cpp are compiled
// directly alongside this file and linked against the external original .so.
// Graphs are persistent and shared across requests for the same approved model.
// TINC intervals are independently audited for selected finite test cases only.

#include "paceval_main.h"
#include <algorithm>
#include <array>
#include <cmath>
#include <cctype>
#include <cstddef>
#include <cstdlib>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <limits>
#include <map>
#include <sstream>
#include <stdexcept>
#include <string>
#include <vector>

namespace agent {
constexpr std::size_t NV=6;
constexpr std::size_t MAX_BATCH=65536;
constexpr const char* VARIABLE_NAMES="x0 x1 x2 x3 x4 x5";
using Values=std::array<double,NV>;
using Dimension=std::array<int,5>; // SI base dimension exponents: kg,m,s,A,K
struct Unit {std::string name; double scale; Dimension dim;};
using D=Dimension;
const std::vector<Unit>& units(){
    // All units are positive multiplicative scales. Offset temperature units
    // such as Celsius are deliberately rejected; K is absolute temperature.
    static const std::vector<Unit> table={
      {"1",1,D{0,0,0,0,0}},{"kg",1,D{1,0,0,0,0}},{"g",1e-3,D{1,0,0,0,0}},
      {"m",1,D{0,1,0,0,0}},{"cm",1e-2,D{0,1,0,0,0}},{"mm",1e-3,D{0,1,0,0,0}},
      {"m2",1,D{0,2,0,0,0}},{"cm2",1e-4,D{0,2,0,0,0}},{"mm2",1e-6,D{0,2,0,0,0}},
      {"m4",1,D{0,4,0,0,0}},{"cm4",1e-8,D{0,4,0,0,0}},
      {"s",1,D{0,0,1,0,0}},{"m/s",1,D{0,1,-1,0,0}},{"km/h",1.0/3.6,D{0,1,-1,0,0}},
      {"N",1,D{1,1,-2,0,0}},{"kN",1e3,D{1,1,-2,0,0}},
      {"Pa",1,D{1,-1,-2,0,0}},{"kPa",1e3,D{1,-1,-2,0,0}},
      {"MPa",1e6,D{1,-1,-2,0,0}},{"GPa",1e9,D{1,-1,-2,0,0}},
      {"A",1,D{0,0,0,1,0}},{"mA",1e-3,D{0,0,0,1,0}},
      {"V",1,D{1,2,-3,-1,0}},{"mV",1e-3,D{1,2,-3,-1,0}},
      {"ohm",1,D{1,2,-3,-2,0}},{"W",1,D{1,2,-3,0,0}},
      {"kW",1e3,D{1,2,-3,0,0}},{"J",1,D{1,2,-2,0,0}},
      {"kJ",1e3,D{1,2,-2,0,0}},{"K",1,D{0,0,0,0,1}},
      {"W/K",1,D{1,2,-3,0,-1}},{"kg/m3",1,D{1,-3,0,0,0}},
      {"N*s/m2",1,D{1,-1,-1,0,0}},{"N/m",1,D{1,0,-2,0,0}}
    };
    return table;
}
const Unit* find_unit(const std::string& n){for(const auto&u:units())if(u.name==n)return &u;return nullptr;}
void require(bool ok,const std::string&msg){if(!ok)throw std::runtime_error(msg);}
struct Model {
    std::string id,expression,output_unit;
    std::array<std::string,NV> inputs;
    std::size_t used;
};
const std::vector<Model>& models(){
    static const std::vector<Model> all={
      {"axial_stress","x0/x1","Pa",{{"N","m2"}},2},
      {"electrical_power","x0*x1","W",{{"V","A"}},2},
      {"kinetic_energy","0.5*x0*x1^2","J",{{"kg","m/s"}},2},
      {"heat_flow","x0*(x1-x2)","W",{{"W/K","K","K"}},3},
      {"voltage_drop","x0*x1","V",{{"ohm","A"}},2},
      {"cantilever_deflection","x0*x1^3/(3*x2*x3)","m",{{"N","m","Pa","m4"}},4},
      {"aerodynamic_drag","0.5*x0*x1*x2*x3^2","N",{{"kg/m3","1","m2","m/s"}},4},
      // This is only the paper's intentionally illustrative synthetic score.
      // k has units N*s/m2, so both terms have the same unit N/m.
      {"proposal_proxy","(x0*x1)/(x2+x3)+x4*sqrt(x5*x5)","N/m",{{"N","m","m2","m2","N*s/m2","m/s"}},6}
    };
    return all;
}
const Model* find_model(const std::string& id){for(const auto& m:models())if(m.id==id)return &m;return nullptr;}
std::string trim(std::string s){
    const auto p=s.find_first_not_of(" \t\r\n");if(p==std::string::npos)return "";
    const auto q=s.find_last_not_of(" \t\r\n");return s.substr(p,q-p+1);
}
std::vector<std::string> csv_fields(const std::string& line){
    // Restricted CSV: deliberately no quoting, escaping, multiline records.
    // All test fields are machine-generated and may not contain commas.
    std::vector<std::string> out;std::string token;std::istringstream in(line);
    while(std::getline(in,token,','))out.push_back(trim(token));
    if(!line.empty()&&line.back()==',')out.emplace_back();
    return out;
}
double parse_finite(const std::string& s){
    require(!s.empty(),"missing numeric argument");
    std::size_t pos=0;double n=0;
    try{n=std::stod(s,&pos);}catch(...){throw std::invalid_argument("numeric conversion failed");}
    require(pos==s.size()&&std::isfinite(n),"nonfinite or malformed number");
    return n;
}
bool safe_identifier(const std::string&s){
    if(s.empty()||s.size()>64)return false;
    for(char c:s)if(!std::isalnum(static_cast<unsigned char>(c))&&c!='_'&&c!='-')return false;
    return true;
}
bool expression_lexically_well_formed(const std::string&s){
    if(s.empty()||s.size()>160||s.find("**")!=std::string::npos||s.find("//")!=std::string::npos)return false;
    int balance=0;
    for(char c:s){
        if(c=='(')++balance;
        if(c==')'&&--balance<0)return false;
        if(!std::isalnum(static_cast<unsigned char>(c))&&c!='_'&&c!='.'&&c!='+'&&c!='-'&&c!='*'&&c!='/'&&c!='^'&&c!='('&&c!=')')return false;
    }
    return balance==0;
}
std::string without_spaces(std::string s){
    s.erase(std::remove_if(s.begin(),s.end(),[](unsigned char c){return std::isspace(c)!=0;}),s.end());return s;
}
// Reference formulas are intentionally independent C++ implementations.
// The paceval expression parser is NEVER used by this function.
double native_result(const Model&m,const Values&v){
    if(m.id=="axial_stress")return v[0]/v[1];
    if(m.id=="electrical_power")return v[0]*v[1];
    if(m.id=="kinetic_energy")return 0.5*v[0]*v[1]*v[1];
    if(m.id=="heat_flow")return v[0]*(v[1]-v[2]);
    if(m.id=="voltage_drop")return v[0]*v[1];
    if(m.id=="cantilever_deflection")return v[0]*v[1]*v[1]*v[1]/(3*v[2]*v[3]);
    if(m.id=="aerodynamic_drag")return 0.5*v[0]*v[1]*v[2]*v[3]*v[3];
    if(m.id=="proposal_proxy")return (v[0]*v[1])/(v[2]+v[3])+v[4]*std::abs(v[5]);
    throw std::runtime_error("unknown native model");
}
// An approved formula is checked for simple mathematical domain constraints.
// These are *model-specific* assumptions, not assertions of a universal
// engineering operating envelope or safety certification.
bool domain_valid(const Model&m,const Values&v){
    for(std::size_t i=0;i<m.used;++i)if(!std::isfinite(v[i]))return false;
    if(m.id=="axial_stress")return v[1]>0;
    if(m.id=="electrical_power")return true;
    if(m.id=="kinetic_energy")return v[0]>=0;
    if(m.id=="heat_flow")return v[0]>=0&&v[1]>0&&v[2]>0;
    if(m.id=="voltage_drop")return v[0]>=0;
    if(m.id=="cantilever_deflection")return v[1]>0&&v[2]>0&&v[3]>0;
    if(m.id=="aerodynamic_drag")return v[0]>0&&v[1]>=0&&v[2]>=0;
    if(m.id=="proposal_proxy")return v[2]>0&&v[3]>=0;
    return false;
}
struct Request {
    std::string id,model_id,expression,output_unit,expected_status;
    std::array<std::string,NV> number_text,units;
};
struct Outcome {
    std::string status;
    const Model* model=nullptr;
    Values si{};
    double output_scale=1,reference=0,result=0,abs_error=0;
};
std::vector<Request> read_requests(const std::string&path){
    std::ifstream f(path);require(f.good(),"Cannot open request file: "+path);
    std::string line;std::vector<Request> rows;std::size_t rowno=0;
    while(std::getline(f,line)){
        ++rowno;if(line.empty()||line[0]=='#'||line.rfind("request_id,",0)==0)continue;
        auto c=csv_fields(line);require(c.size()==17,"CSV column mismatch at row "+std::to_string(rowno));
        Request r;r.id=c[0];r.model_id=c[1];r.expression=c[2];r.output_unit=c[3];
        for(std::size_t i=0;i<NV;++i){r.number_text[i]=c[4+2*i];r.units[i]=c[5+2*i];}
        r.expected_status=c[16];require(safe_identifier(r.id),"Unsafe request ID at row "+std::to_string(rowno));
        rows.push_back(r);
    }
    require(!rows.empty(),"Empty request file");return rows;
}
Outcome prepare(const Request&r){
    Outcome out;
    const Model* m=find_model(r.model_id);
    if(!m){out.status="UNKNOWN_MODEL";return out;}
    if(!expression_lexically_well_formed(r.expression)){out.status="MALFORMED_EXPR";return out;}
    // Allowlist is intentional: no untrusted arbitrary expression evaluation.
    if(without_spaces(r.expression)!=m->expression){out.status="UNAPPROVED_EXPR";return out;}
    for(std::size_t i=0;i<m->used;++i){
        const Unit* src=find_unit(r.units[i]);
        const Unit* expected=find_unit(m->inputs[i]);
        if(!src||!expected||src->dim!=expected->dim){out.status="UNIT_MISMATCH";return out;}
    }
    const Unit* target=find_unit(r.output_unit);const Unit* canonical=find_unit(m->output_unit);
    if(!target||!canonical||target->dim!=canonical->dim){out.status="OUTPUT_UNIT_MISMATCH";return out;}
    try{
        for(std::size_t i=0;i<m->used;++i){
            const Unit* u=find_unit(r.units[i]);out.si[i]=parse_finite(r.number_text[i])*u->scale;
            if(!std::isfinite(out.si[i]))throw std::invalid_argument("conversion overflow");
        }
    }catch(...){out.status="INVALID_NUMBER";return out;}
    for(std::size_t i=m->used;i<NV;++i)
       if(!r.number_text[i].empty()||!r.units[i].empty()){out.status="INVALID_NUMBER";return out;}
    if(!domain_valid(*m,out.si)){out.status="DOMAIN_ERROR";return out;}
    out.model=m;out.output_scale=target->scale;
    out.reference=native_result(*m,out.si)/out.output_scale;
    if(!std::isfinite(out.reference)){out.status="DOMAIN_ERROR";out.model=nullptr;return out;}
    out.status="OK";return out;
}
class PacevalRuntime {
    bool alive=false;
    std::vector<PACEVAL_HANDLE> handles;
public:
    PacevalRuntime(){require(paceval_InitializeLibrary(nullptr),"paceval_InitializeLibrary returned false");alive=true;}
    PacevalRuntime(const PacevalRuntime&)=delete;PacevalRuntime&operator=(const PacevalRuntime&)=delete;
    ~PacevalRuntime(){for(auto it=handles.rbegin();it!=handles.rend();++it)paceval_DeleteComputation(*it);if(alive)paceval_FreeLibrary();}
    PACEVAL_HANDLE make(const Model&m,bool interval=false){
       PACEVAL_HANDLE h=paceval_CreateComputation(m.expression.c_str(),static_cast<unsigned long>(NV),VARIABLE_NAMES,interval,nullptr);
       require(h!=nullptr,"Graph allocation failed: "+m.id);
       handles.push_back(h);
       require(!paceval_GetIsError(h),"Graph syntax error in "+m.id);
       return h;
    }
    void batch(PACEVAL_HANDLE h,const std::vector<Values>& vals,std::vector<double>&out){
       std::vector<double> x; x.reserve(vals.size()*NV);
       for(const auto& a:vals)for(double v:a)x.push_back(v);
       out.assign(vals.size(),0);std::vector<int> errors(vals.size(),-1);
       // Per SDK: TRUE means errors were observed, not success.
       bool failed=paceval_dGetComputationResultExt(h,x.data(),static_cast<unsigned long>(vals.size()),out.data(),nullptr,nullptr,errors.data());
       require(!failed,"paceval_dGetComputationResultExt reported an error");
       for(std::size_t i=0;i<out.size();++i)
          require(errors[i]==PACEVAL_ERR_NO_ERROR&&std::isfinite(out[i]),"Failed batch element "+std::to_string(i));
       require(!paceval_GetIsError(h),"Graph error after batch evaluation");
    }
    std::array<double,3> interval(PACEVAL_HANDLE h,const Values& input){
       Values x=input;double lo=0,hi=0;
       double v=paceval_dGetComputationResult(h,x.data(),&lo,&hi);
       require(!paceval_GetIsError(h),"TINC graph evaluation error");
       require(std::isfinite(v)&&std::isfinite(lo)&&std::isfinite(hi)&&lo<=hi,"Invalid TINC result");
       return {v,lo,hi};
    }
};
void native_self_tests(){
    require(models().size()==8,"Model registry count changed");
    require(find_unit("MPa")&&find_unit("kPa"),"Missing unit conversions");
    for(const auto&m:models()){
        require(m.used>=2&&m.used<=6,"Model arity invalid");
        for(std::size_t i=0;i<m.used;++i)require(find_unit(m.inputs[i])!=nullptr,"Registry input unit invalid");
        require(find_unit(m.output_unit)!=nullptr,"Registry output unit invalid");
        require(expression_lexically_well_formed(m.expression),"Registry formula invalid");
    }
    Request r; r.model_id="axial_stress";r.expression="x0/x1";r.output_unit="MPa";
    r.number_text[0]="10";r.units[0]="kN";r.number_text[1]="2";r.units[1]="cm2";
    auto a=prepare(r);require(a.status=="OK"&&std::abs(a.reference-50)<1e-12,"10 kN / 2 cm2 should be 50 MPa");
    r.units[1]="K";require(prepare(r).status=="UNIT_MISMATCH","Dimension error not rejected");
    r.units[1]="cm2";r.expression="x0+x1";
    require(prepare(r).status=="UNAPPROVED_EXPR","Unapproved expression not rejected");
    r.expression="x0/x1";r.number_text[1]="0";
    require(prepare(r).status=="DOMAIN_ERROR","Singular denominator not rejected");
    std::cout<<"PASS: registry, unit conversion, unapproved formula and domain rejection\n";
}
void run(const std::string&request_path,const std::string&output_path,const std::string&tinc_path,std::size_t batch_size,bool skip_tinc){
    require(batch_size>0&&batch_size<=MAX_BATCH,"Batch size out of range");
    const auto reqs=read_requests(request_path);
    std::vector<Outcome> outcomes;outcomes.reserve(reqs.size());
    std::size_t rejected=0,accepted=0,errors=0,repeats=0;
    for(const auto&r:reqs){
        auto a=prepare(r);if(a.status=="OK")++accepted;else ++rejected;
        if(!r.expected_status.empty())
            require(a.status==r.expected_status,"Unexpected validation result for "+r.id+": "+a.status+" expected "+r.expected_status);
        if(r.id.find("REPEAT")==0)++repeats;
        outcomes.push_back(a);
    }
    PacevalRuntime rt;
    std::vector<PACEVAL_HANDLE> graphs,tinc_graphs;
    for(const auto&m:models()){graphs.push_back(rt.make(m));if(!skip_tinc)tinc_graphs.push_back(rt.make(m,true));}
    // Group requests by model so one graph is reused for all its input values.
    // A batch may contain unrelated request IDs, but its variable ordering
    // exactly follows x0..x5 in the declared graph.
    std::size_t checked=0;double maxerror=0;
    for(std::size_t m=0;m<models().size();++m){
        std::vector<std::size_t> indices;
        for(std::size_t i=0;i<outcomes.size();++i)
            if(outcomes[i].model==&models()[m])indices.push_back(i);
        for(std::size_t start=0;start<indices.size();start+=batch_size){
            std::size_t n=std::min(batch_size,indices.size()-start);
            std::vector<Values> vars;vars.reserve(n);
            for(std::size_t j=0;j<n;++j)vars.push_back(outcomes[indices[start+j]].si);
            std::vector<double> values;rt.batch(graphs[m],vars,values);
            for(std::size_t j=0;j<n;++j){
                auto& a=outcomes[indices[start+j]];
                a.result=values[j]/a.output_scale;
                a.abs_error=std::abs(a.result-a.reference);
                maxerror=std::max(maxerror,a.abs_error);
                ++checked;
                if(!std::isfinite(a.result)||a.abs_error>6e-12*(1+std::abs(a.reference)))++errors;
            }
        }
    }
    std::ofstream out(output_path);require(out.good(),"Cannot open result CSV");
    out<<"request_id,model_id,status,result,unit,native_reference,absolute_error\n"<<std::setprecision(17);
    for(std::size_t i=0;i<reqs.size();++i){
        const auto&r=reqs[i];const auto&a=outcomes[i];
        out<<r.id<<','<<r.model_id<<','<<a.status<<',';
        if(a.status=="OK")out<<a.result<<','<<r.output_unit<<','<<a.reference<<','<<a.abs_error;
        else out<<",,,";
        out<<'\n';
    }
    // 3 TINC samples per model, 24 in total. The independent Python script
    // checks inclusion at >=100-digit working precision. No global guarantee.
    std::ofstream ti(tinc_path);require(ti.good(),"Cannot open TINC CSV");
    ti<<"request_id,model_id,x0,x1,x2,x3,x4,x5,result_si,lower_si,upper_si\n"<<std::setprecision(17);
    std::size_t samples=0;
    if(!skip_tinc)for(std::size_t m=0;m<models().size();++m){
        std::size_t seen=0;
        for(std::size_t j=0;j<outcomes.size()&&seen<3;++j){
            const auto& a=outcomes[j];
            if(a.model!=&models()[m])continue;
            auto res=rt.interval(tinc_graphs[m],a.si);
            ti<<reqs[j].id<<','<<models()[m].id;
            for(double v:a.si)ti<<','<<v;
            ti<<','<<res[0]<<','<<res[1]<<','<<res[2]<<'\n';
            ++seen;++samples;
        }
        require(seen==3,"Not enough TINC samples for "+models()[m].id);
    }
    require(checked==accepted&&errors==0,"Numerical reference audit failed");
    std::cout<<"PASS: requests="<<reqs.size()<<" accepted="<<accepted<<" rejected="<<rejected
             <<" repeats="<<repeats<<" numerical_checks="<<checked<<" failures="<<errors
             <<" TINC_samples="<<samples<<" graphs="<<graphs.size()+tinc_graphs.size()
             <<" max_absolute_difference="<<std::setprecision(9)<<maxerror<<"\n";
}
} // namespace agent
int main(int argc,char**argv){
  try{
    std::string cases="../examples/requests.csv",output="agent_results.csv",tinc="tinc_samples.csv";
    std::size_t batch=64;bool self=false,skip_tinc=false;
    for(int i=1;i<argc;++i){
       std::string arg=argv[i];
       if(arg=="--self-test")self=true;
       else if(arg=="--skip-tinc")skip_tinc=true;
       else if(arg=="--cases"&&i+1<argc)cases=argv[++i];
       else if(arg=="--output"&&i+1<argc)output=argv[++i];
       else if(arg=="--tinc"&&i+1<argc)tinc=argv[++i];
       else if(arg=="--batch"&&i+1<argc){batch=std::stoul(argv[++i]);}
       else throw std::runtime_error("Unknown or incomplete CLI argument: "+arg);
    }
    agent::native_self_tests();
    if(!self)agent::run(cases,output,tinc,batch,skip_tinc);
    return 0;
  }catch(const std::exception&e){std::cerr<<"FAIL: "<<e.what()<<'\n';return 2;}
}
