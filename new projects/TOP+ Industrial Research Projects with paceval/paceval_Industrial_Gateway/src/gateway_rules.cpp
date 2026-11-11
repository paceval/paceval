// paceval Industrial Gateway Mathematical Rules: C++17/Linux research demonstrator.
//
// Scope:
//  * 50 named telemetry channels with timestamps, declared units and quality flags.
//  * 100 individually versioned, pre-approved mathematical rules, each compiled
//    ONCE into an actual paceval computation object and reused over a replay.
//  * Deterministic CSV replay, staged batch evaluation, input-domain screening.
//  * Independent C++ numerical reference; C++ host-owned alarm persistence.
//  * Explicit rule-version update with replacement of exactly one graph.
//  * A separate TINC-enabled numerical diagnostic (24 sampled inputs).
//
// This is NOT an OPC UA / MQTT / Sparkplug implementation, certified safety
// controller, real gateway or demonstrated hard-real-time scheduling system.
// Data are synthetic; alarm rules are mathematical examples, not validated
// predictive-maintenance models. The host owns all protocol and state logic.
//
// Important SDK detail: PACEVAL_HANDLE is a void* macro, hence always use
// separate declarations or std::vector<PACEVAL_HANDLE>, never comma declarations.

#include "paceval_main.h"
#include <algorithm>
#include <array>
#include <cmath>
#include <cstdint>
#include <cstdlib>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <limits>
#include <sstream>
#include <stdexcept>
#include <string>
#include <vector>
#include <utility>

namespace {
constexpr int CHANNELS = 50;
constexpr int RULES = 100;
constexpr int DEFAULT_TICKS = 240;
constexpr double ABS_TOL = 2e-11;

void require(bool ok, const std::string& msg) { if (!ok) throw std::runtime_error(msg); }

std::vector<std::string> split(const std::string& s, char sep) {
    std::vector<std::string> v; std::stringstream ss(s); std::string part;
    while (std::getline(ss, part, sep)) v.push_back(part);
    if (!s.empty() && s.back()==sep) v.push_back("");
    return v;
}
int as_int(const std::string& s) {
    require(!s.empty(), "missing integer");
    std::size_t used=0; int value=0;
    try { value=std::stoi(s,&used); } catch (...) { throw std::runtime_error("invalid integer: "+s); }
    require(used==s.size(),"bad integer trailing content");
    return value;
}
// An external gateway transport must supply an integral millisecond stamp.
// std::stoll by itself accepts trailing garbage (e.g. "12345bad"), so verify
// complete consumption before trusting a timestamp from a CSV replay.
int64_t as_timestamp(const std::string& s) {
    require(!s.empty() && s.size() <= 20, "missing or oversized timestamp");
    std::size_t used=0;
    int64_t value=0;
    try { value=static_cast<int64_t>(std::stoll(s,&used)); }
    catch(...) { throw std::runtime_error("invalid timestamp field"); }
    require(used==s.size() && value>=0,"invalid or negative timestamp field");
    return value;
}
double as_number(const std::string& s) {
    require(!s.empty() && s.size()<100,"missing or excessively long number");
    std::size_t used=0; double value=0;
    try { value=std::stod(s,&used); } catch (...) { throw std::runtime_error("invalid numeric field"); }
    require(used==s.size() && std::isfinite(value),"non-finite numeric field");
    return value;
}

struct Reading {
    int tick=0, channel=0;
    int64_t timestamp=0;
    double temp=0, vib=0, current=0;
    std::string quality;
};
struct Rule {
    int id=0, channel=0, family=0;
    std::string version="1.0";
    double w1=0,w2=0,w3=0,w4=0,limit=0,threshold=0;
};
struct Outcome {
    int tick=0,channel=0,rule=0;
    int64_t timestamp=0;
    std::string version,quality,status;
    bool valid=false, alarm=false;
    double score=0,threshold=0,reference=0;
};

// The three input variables intentionally have declared physical units.
// Normalisation creates dimensionless terms BEFORE they are weighted.
// T [deg C], V [mm/s], I [A] are all fixed by the host input contract.
// Synthetic coefficients are published in examples/rules.csv.
std::vector<Rule> make_rules() {
    std::vector<Rule> rules; rules.reserve(RULES);
    for(int i=0;i<RULES;++i) {
        Rule r; r.id=i; r.channel=i%CHANNELS; r.family=i%4;
        r.w1=0.32+0.007*(i%23);
        r.w2=0.19+0.009*(i%19);
        r.w3=0.41+0.006*(i%29);
        r.w4=0.07+0.003*(i%13);
        r.limit=13.0+0.10*(i%11);
        r.threshold=0.14+0.045*(i%7);
        rules.push_back(r);
    }
    return rules;
}

std::string literal(double x) { std::ostringstream s; s<<std::setprecision(17)<<x; return s.str(); }
std::string expression(const Rule& r) {
    // All one hundred computation objects use the identical input schema
    // but individual, version-controlled coefficients/formulas.
    const std::string t="((T-70)/40)", v="(V/2)",
      i="((I-"+literal(r.limit)+"+abs(I-"+literal(r.limit)+"))/16)";
    const std::string a="("+literal(r.w1)+"*"+t+")";
    const std::string b="("+literal(r.w2)+"*"+v+")";
    const std::string c="("+literal(r.w3)+"*"+i+")";
    switch(r.family) {
        case 0: return a+"+"+b+"+"+c;
        case 1: return "tanh("+a+"+"+b+"+"+c+")";
        case 2: return "("+a+"*"+t+")+(("+literal(r.w2)+"*"+v+")*"+v+")+(("+literal(r.w3)+"*"+i+")*"+i+")";
        default: return a+"+"+b+"+"+c+"+("+literal(r.w4)+"*"+t+"*"+v+")";
    }
}
double native(const Rule& r,const Reading& z) {
    double t=(z.temp-70.)/40., v=z.vib/2.;
    double i=std::max(0.,z.current-r.limit)/8.;
    double sum=r.w1*t+r.w2*v+r.w3*i;
    if(r.family==1) return std::tanh(sum);
    if(r.family==2) return r.w1*t*t+r.w2*v*v+r.w3*i*i;
    if(r.family==3) return sum+r.w4*t*v;
    return sum;
}

bool acceptable(const Reading& x) {
    return x.quality=="GOOD" && std::isfinite(x.temp) && std::isfinite(x.vib)
       && std::isfinite(x.current) && x.temp>=-30 && x.temp<=180
       && x.vib>=0 && x.vib<=50 && x.current>=0 && x.current<=100;
}
std::vector<Reading> create_data(int ticks) {
    require(ticks>0 && ticks<=10000,"invalid tick count");
    std::vector<Reading> result; result.reserve(static_cast<size_t>(ticks)*CHANNELS);
    for(int tick=0; tick<ticks; ++tick) for(int ch=0; ch<CHANNELS; ++ch) {
        Reading x; x.tick=tick; x.channel=ch; x.timestamp=1794398400000LL + 100LL*tick;
        x.temp=65.+6.*std::sin(tick/17.+ch/7.)+2.3*(ch%7);
        x.vib=0.43+0.12*std::cos(tick/9.+ch/6.)+0.015*(ch%9);
        x.current=13.+1.5*std::sin(tick/31.+ch/8.);
        x.quality="GOOD";
        if((tick+7*ch)%71==0) x.quality="STALE";
        if((3*tick+5*ch)%113==0) x.quality="BAD";
        if(tick==157 && ch%13==0) x.quality="MISSING";
        result.push_back(x);
    }
    return result;
}
void write_data(const std::string& path,const std::vector<Reading>& data) {
    std::ofstream o(path); require(bool(o),"cannot write telemetry CSV");
    o<<"tick,channel,timestamp_ms,temp_C,vibration_mm_s,current_A,quality\n"<<std::setprecision(17);
    for(const auto& x:data) {
        o<<x.tick<<','<<x.channel<<','<<x.timestamp<<',';
        if(x.quality!="MISSING") o<<x.temp;
        o<<','<<x.vib<<','<<x.current<<','<<x.quality<<'\n';
    }
}
std::vector<Reading> read_data(const std::string& path) {
    std::ifstream in(path); require(bool(in),"cannot open replay CSV");
    std::string line; require(bool(std::getline(in,line)),"missing CSV header");
    require(line=="tick,channel,timestamp_ms,temp_C,vibration_mm_s,current_A,quality", "unexpected CSV columns");
    std::vector<Reading> items;
    std::array<int64_t,CHANNELS> last_stamp{}; last_stamp.fill(-1);
    std::array<int,CHANNELS> last_tick{}; last_tick.fill(-1);
    while(std::getline(in,line)) {
        if(line.empty()) continue;
        auto f=split(line,',');require(f.size()==7,"malformed CSV row");
        Reading r; r.tick=as_int(f[0]);r.channel=as_int(f[1]);
        require(r.channel>=0 && r.channel<CHANNELS,"bad channel id");
        require(r.tick>=0 && r.tick<10000,"bad tick index");
        r.timestamp=as_timestamp(f[2]);
        require(r.tick==last_tick[r.channel]+1,"missing/duplicated/out-of-order channel sample");
        require(r.timestamp>last_stamp[r.channel],"non-monotone timestamp");
        r.quality=f[6];
        require(r.quality=="GOOD" || r.quality=="BAD" || r.quality=="STALE" || r.quality=="MISSING","unsupported quality");
        if(r.quality=="MISSING") { require(f[3].empty(),"missing quality must have empty temperature"); }
        else r.temp=as_number(f[3]);
        r.vib=as_number(f[4]);r.current=as_number(f[5]);
        if(r.quality=="GOOD")require(acceptable(r),"out-of-range GOOD sensor row");
        last_stamp[r.channel]=r.timestamp;last_tick[r.channel]=r.tick;
        items.push_back(r);
    }
    require(!items.empty() && items.size()%CHANNELS==0,"incomplete sample count");
    const size_t ticks=items.size()/CHANNELS;
    for(int ch=0;ch<CHANNELS;++ch)require(last_tick[ch]==static_cast<int>(ticks)-1,"missing tick for one channel");
    for(size_t i=0;i<items.size();++i)require(items[i].tick==static_cast<int>(i/CHANNELS) && items[i].channel==static_cast<int>(i%CHANNELS),"row ordering mismatch");
    return items;
}
void save_rules(const std::string& path,const std::vector<Rule>& rules) {
    std::ofstream out(path);require(bool(out),"rule manifest open failure");
    out<<"rule_id,version,channel,family,w1,w2,w3,w4,current_limit_A,threshold\n"<<std::setprecision(17);
    for(const Rule& r:rules)out<<r.id<<','<<r.version<<','<<r.channel<<','<<r.family<<','<<r.w1<<','<<r.w2<<','<<r.w3<<','<<r.w4<<','<<r.limit<<','<<r.threshold<<'\n';
}

class Engine {
    bool initialized_=false;
    std::vector<PACEVAL_HANDLE> handles_;
    PACEVAL_HANDLE interval_=nullptr;
    std::vector<Rule> rules_;
public:
    explicit Engine(std::vector<Rule> rules):rules_(std::move(rules)) {
        require(paceval_InitializeLibrary(nullptr),"paceval initialization failed");
        initialized_=true;
        try {
            for(const auto& r:rules_) {
                auto expr=expression(r);
                PACEVAL_HANDLE h=paceval_CreateComputation(expr.c_str(),3,"T V I",false,nullptr);
                if(!h || paceval_GetIsError(h)) {
                    if(h){char msg[256]={0},detail[256]={0};paceval_CreateErrorInformationText(h,msg,detail);
                       std::cerr << "Rule " << r.id << " paceval parser: " << msg << " / " << detail << "\n";paceval_DeleteComputation(h);}
                    std::cerr << "Formula: " << expr << "\n";
                    throw std::runtime_error("paceval graph creation failed for rule "+std::to_string(r.id));
                }
                handles_.push_back(h);
            }
            const auto e=expression(rules_[0]);
            interval_=paceval_CreateComputation(e.c_str(),3,"T V I",true,nullptr);
            require(interval_ && !paceval_GetIsError(interval_),"TINC graph creation failed");
        } catch(...) {release();throw;}
    }
    ~Engine(){release();}
    Engine(const Engine&)=delete; Engine& operator=(const Engine&)=delete;
    void release() {
        if(interval_){paceval_DeleteComputation(interval_);interval_=nullptr;}
        for(auto h:handles_)if(h)paceval_DeleteComputation(h);
        handles_.clear();
        if(initialized_){paceval_FreeLibrary();initialized_=false;}
    }
    const std::vector<Rule>& rules() const{return rules_;}
    void update_rule(int id) {
        require(id>=0 && id<RULES,"unknown update rule");
        Rule candidate=rules_[static_cast<size_t>(id)];
        candidate.w1 +=0.18; candidate.version="1.1";
        auto expr=expression(candidate);
        PACEVAL_HANDLE next=paceval_CreateComputation(expr.c_str(),3,"T V I",false,nullptr);
        if(!next || paceval_GetIsError(next)) {
            // Keep the old validated graph alive on a rejected update.
            // Delete even an error-marked handle if the SDK returned one.
            if(next) paceval_DeleteComputation(next);
            throw std::runtime_error("replacement rule compilation failed");
        }
        // Only swap when new graph is successfully prepared. Old handle stays
        // active until then, making update atomic at this single-thread level.
        PACEVAL_HANDLE next_interval=nullptr;
        if(id==0) { // Keep the interval-enabled graph in sync with rule 0.
            next_interval=paceval_CreateComputation(expr.c_str(),3,"T V I",true,nullptr);
            if(!next_interval || paceval_GetIsError(next_interval)) {
                if(next_interval) paceval_DeleteComputation(next_interval);
                paceval_DeleteComputation(next);
                throw std::runtime_error("replacement TINC graph creation failed");
            }
        }
        PACEVAL_HANDLE prior=handles_[static_cast<size_t>(id)];
        handles_[static_cast<size_t>(id)]=next;
        if(next_interval) {PACEVAL_HANDLE old=interval_;interval_=next_interval;paceval_DeleteComputation(old);}
        rules_[static_cast<size_t>(id)]=candidate;
        paceval_DeleteComputation(prior);
    }
    std::vector<double> batch(int id,const std::vector<const Reading*>& samples,size_t batch_limit) {
        require(id>=0 && id<RULES,"rule out of range");
        require(batch_limit>=1 && batch_limit<=8192,"batch limit outside safe replay envelope");
        std::vector<double> output;output.reserve(samples.size());
        for(size_t offset=0;offset<samples.size();offset+=batch_limit) {
            const auto take=std::min(batch_limit,samples.size()-offset);
            std::vector<double> input;input.reserve(take*3);
            for(size_t j=0;j<take;++j){const auto* p=samples[offset+j];
                require(p && acceptable(*p),"invalid sample reached mathematics engine");
                input.push_back(p->temp);input.push_back(p->vib);input.push_back(p->current);
            }
            std::vector<double> result(take,0);
            std::vector<int> errors(take,-1);
            // NOTE: the Ext API returns true if a computation error occurred.
            // Inputs are sample-major: T,V,I for each sample in order.
            const bool has_errors=paceval_dGetComputationResultExt(handles_[static_cast<size_t>(id)],input.data(),
               static_cast<unsigned long>(take),result.data(),nullptr,nullptr,errors.data());
            require(!has_errors,"paceval batch returned an error");
            for(size_t j=0;j<take;++j) {
                require(errors[j]==PACEVAL_ERR_NO_ERROR && std::isfinite(result[j]),"invalid paceval result");
            }
            output.insert(output.end(),result.begin(),result.end());
        }
        return output;
    }
    std::array<double,3> tinc(const Reading& input) {
        require(acceptable(input),"TINC input invalid");
        double v[]={input.temp,input.vib,input.current},lo=0,hi=0;
        double output=paceval_dGetComputationResult(interval_,v,&lo,&hi);
        require(!paceval_GetIsError(interval_) && std::isfinite(output) &&
                std::isfinite(lo) && std::isfinite(hi) && lo<=hi,"TINC invalid interval output");
        return {output,lo,hi};
    }
};

std::vector<Outcome> evaluate(Engine& engine,const std::vector<Reading>& tele,size_t batch_limit,double& max_delta) {
    const int ticks=static_cast<int>(tele.size()/CHANNELS);
    std::vector<Outcome> outcome(static_cast<size_t>(ticks)*RULES);
    max_delta=0;
    for(const Rule& rule:engine.rules()) {
        std::vector<const Reading*> accepted;
        std::vector<int> accepted_ticks;
        accepted.reserve(ticks);
        for(int tick=0;tick<ticks;++tick) {
            const auto& z=tele[static_cast<size_t>(tick)*CHANNELS+rule.channel];
            Outcome& o=outcome[static_cast<size_t>(tick)*RULES+rule.id];
            o.tick=tick;o.channel=rule.channel;o.rule=rule.id;o.timestamp=z.timestamp;
            o.version=rule.version;o.threshold=rule.threshold;o.quality=z.quality;
            o.status="NO_DATA";
            if(acceptable(z)) {accepted.push_back(&z);accepted_ticks.push_back(tick);}
        }
        auto outputs=engine.batch(rule.id,accepted,batch_limit);
        require(outputs.size()==accepted.size(),"different batch size returned");
        for(size_t i=0;i<outputs.size();++i) {
            const auto& row=*accepted[i];
            Outcome& o=outcome[static_cast<size_t>(accepted_ticks[i])*RULES+rule.id];
            o.score=outputs[i];o.reference=native(rule,row);o.valid=true;
            const double diff=std::abs(o.score-o.reference);
            max_delta=std::max(max_delta,diff);
            require(diff<=ABS_TOL*(1+std::abs(o.reference)),"paceval/native reference mismatch");
        }
        // Host-side stateful alarm rule: three consecutive qualified samples
        // above the threshold to trigger; clear below threshold-hysteresis.
        // Invalid quality leaves alarm status UNKNOWN and resets the state.
        int consecutive=0;bool active=false;
        for(int tick=0;tick<ticks;++tick) {
            Outcome& o=outcome[static_cast<size_t>(tick)*RULES+rule.id];
            if(!o.valid) {consecutive=0;active=false;continue;}
            if(o.score>o.threshold){++consecutive;if(consecutive>=3)active=true;}
            else {consecutive=0;if(o.score<=o.threshold-0.025)active=false;}
            o.alarm=active;o.status=active?"ALERT":"NORMAL";
        }
    }
    return outcome;
}
void save_output(const std::string& path,const std::vector<Outcome>& outcomes) {
    std::ofstream out(path);require(bool(out),"cannot open output CSV");
    out<<"tick,timestamp_ms,channel,rule_id,version,quality,status,score,threshold,alarm,native_reference\n"<<std::setprecision(17);
    for(const auto&o:outcomes) {
        out<<o.tick<<','<<o.timestamp<<','<<o.channel<<','<<o.rule<<','<<o.version<<','<<o.quality<<','<<o.status<<',';
        if(o.valid)out<<o.score;
        out<<','<<o.threshold<<','<<(o.valid && o.alarm?1:0)<<',';
        if(o.valid)out<<o.reference;
        out<<'\n';
    }
}
void save_tinc(const std::string& path,Engine& engine,const std::vector<Reading>& data) {
    std::ofstream out(path);require(bool(out),"cannot open TINC CSV");
    out<<"tick,channel,T,V,I,paceval_value,tinc_low,tinc_high,native_reference\n"<<std::setprecision(17);
    int chosen=0;
    for(const auto&row:data)if(row.channel==0 && acceptable(row) && chosen<24) {
        auto val=engine.tinc(row);
        auto reference=native(engine.rules()[0],row);
        require(std::abs(val[0]-reference)<=ABS_TOL*(1+std::abs(reference)),"TINC point value mismatch");
        out<<row.tick<<','<<row.channel<<','<<row.temp<<','<<row.vib<<','<<row.current<<','<<val[0]<<','<<val[1]<<','<<val[2]<<','<<reference<<'\n';
        ++chosen;
    }
    require(chosen==24,"not enough valid TINC samples");
}
void self_test() {
    auto rules=make_rules();require(rules.size()==RULES,"rule count");
    auto data=create_data(240);require(data.size()==12000,"channel count");
    int stale=0,bad=0,missing=0;
    for(const auto&r:data){if(r.quality=="STALE")++stale;else if(r.quality=="BAD")++bad;else if(r.quality=="MISSING")++missing;}
    require(stale>0 && bad>0 && missing>0,"invalid input cases absent");
    require(expression(rules[0]).find("abs(")!=std::string::npos,"piecewise equivalent missing");
    const auto z=data[51];
    require(std::isfinite(native(rules[1],z)),"native model invalid");
    require(!acceptable(Reading{0,0,0,25,1,1,"STALE"}),"stale accepted");
    require(!acceptable(Reading{0,0,0,25,1,1,"MISSING"}),"missing accepted");
    // Reject malformed timestamps before source data can reach any graph.
    bool rejected=false;
    try { (void)as_timestamp("1794398400000garbage"); }
    catch(const std::exception&) { rejected=true; }
    require(rejected,"malformed timestamp accepted");
    rejected=false;
    try { (void)as_timestamp("-100"); }
    catch(const std::exception&) { rejected=true; }
    require(rejected,"negative timestamp accepted");
    std::cout<<"PASS native tests: 100 rules, 50 channels, data quality and numeric contract\n";
}
void help() {
    std::cout<<"gateway_rules --generate-data telemetry.csv [--ticks N] | --self-test\n"
      <<"gateway_rules --replay telemetry.csv --out results.csv [--batch 256] [--rules rules.csv] [--tinc tinc.csv] [--update-rule 17]\n";
}
}
int main(int argc,char** argv) {
    try {
        std::string generate,replay,out,rule_manifest,tinc;
        int ticks=DEFAULT_TICKS;size_t batch=256;int update_id=-1;bool test=false;
        for(int i=1;i<argc;++i) {
            const std::string a=argv[i];
            auto next=[&](){require(i+1<argc,"missing value for "+a);return std::string(argv[++i]);};
            if(a=="--generate-data")generate=next();
            else if(a=="--ticks")ticks=as_int(next());
            else if(a=="--replay")replay=next();
            else if(a=="--out")out=next();
            else if(a=="--batch")batch=static_cast<size_t>(as_int(next()));
            else if(a=="--rules")rule_manifest=next();
            else if(a=="--tinc")tinc=next();
            else if(a=="--update-rule")update_id=as_int(next());
            else if(a=="--self-test")test=true;
            else if(a=="--help") {help();return 0;}
            else throw std::runtime_error("unknown argument: "+a);
        }
        if(test){self_test();return 0;}
        if(!generate.empty()){write_data(generate,create_data(ticks));std::cout<<"CREATED "<<ticks*CHANNELS<<" telemetry rows\n";return 0;}
        require(!replay.empty() && !out.empty(),"--replay and --out required");
        auto data=read_data(replay);
        Engine engine(make_rules());
        if(update_id>=0) engine.update_rule(update_id);
        if(!rule_manifest.empty())save_rules(rule_manifest,engine.rules());
        double largest=0;
        const auto scores=evaluate(engine,data,batch,largest);
        save_output(out,scores);
        if(!tinc.empty())save_tinc(tinc,engine,data);
        size_t evaluated=0,invalid=0,alarms=0;
        for(const auto& r:scores) {if(r.valid){++evaluated;if(r.alarm)++alarms;}else ++invalid;}
        std::cout<<"PASS real paceval runtime: "<<engine.rules().size()<<" reusable graphs"
                 <<", channels="<<CHANNELS<<", ticks="<<data.size()/CHANNELS
                 <<", evaluated="<<evaluated<<", rejected="<<invalid<<", alerts="<<alarms
                 <<", native_max_abs_error="<<std::setprecision(7)<<largest<<"\n";
        return 0;
    } catch(const std::exception&e) {std::cerr<<"FAIL: "<<e.what()<<"\n";return 1;}
}
