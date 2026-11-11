// paceval Predictive Maintenance Mathematics: reproducible C++17/Linux research demonstrator.
//
// The host performs vibration feature extraction, asset-isolated data partitioning,
// validity checks, threshold classification, metric calculation, and model selection.
// The genuine paceval runtime executes 50 independently versioned, reusable mathematical
// scoring graphs via the official paceval_main.h / paceval_main.cpp API bridge.
//
// This is NOT a trained predictive-failure model or an operational maintenance system.
// The bundled vibration signals and fault labels are synthetic; the score is a
// formula-defined condition index rather than a calibrated failure probability.

#include "paceval_main.h"
#include <algorithm>
#include <array>
#include <cmath>
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
#include <tuple>
#include <utility>
#include <vector>

namespace {
constexpr int MODEL_COUNT=50;
constexpr double THRESHOLD=0.55; // fixed ahead of model selection
void check(bool valid, const std::string& why) {if(!valid) throw std::runtime_error(why);}
std::vector<std::string> split(const std::string& s) {
    std::vector<std::string> out; std::stringstream ss(s);std::string token;
    while(std::getline(ss,token,',')) out.push_back(token);
    if(!s.empty() && s.back()==',')out.emplace_back();
    return out;
}
int parse_int(const std::string& x) {
    std::size_t used=0; int v=0;
    try{v=std::stoi(x,&used);}catch(...){throw std::runtime_error("invalid integer");}
    check(used==x.size(),"trailing text in integer");return v;
}
double parse_double(const std::string& x) {
    std::size_t used=0;double v=0;
    try{v=std::stod(x,&used);}catch(...){throw std::runtime_error("invalid floating point input");}
    check(used==x.size() && std::isfinite(v),"nonfinite or invalid input");return v;
}
struct Window {
    int asset=0,window=0,label=0; std::string split;
    double temperature=0, rms=0, kurtosis=0;
    std::vector<double> vibration;
};
void features(Window& w) {
    const double n=static_cast<double>(w.vibration.size());
    check(n>=128 && n<=8192,"invalid vibration window length");
    double mean=0,sum2=0;
    for(double x:w.vibration){check(std::isfinite(x) && std::abs(x)<=100,"invalid acceleration");mean+=x;sum2+=x*x;}
    mean/=n;w.rms=std::sqrt(sum2/n);
    double m2=0,m4=0;
    for(double x:w.vibration){const double y=x-mean;const double y2=y*y;m2+=y2;m4+=y2*y2;}
    m2/=n;m4/=n;
    check(m2>1e-14,"zero variance vibration window");
    w.kurtosis=m4/(m2*m2); // Pearson central kurtosis (normal: approximately 3)
    check(std::isfinite(w.kurtosis) && w.kurtosis>=1 && w.kurtosis<100000,"invalid kurtosis");
    check(w.temperature>=-40 && w.temperature<=200,"temperature outside permitted range");
}
std::vector<Window> load_raw(const std::string& path) {
    std::ifstream in(path);check(bool(in),"cannot read raw recordings");
    std::string line;check(bool(std::getline(in,line)),"empty raw file");
    check(line=="asset_id,window_id,split,label,temp_C,sample_index,accel_g", "unexpected raw header");
    std::vector<Window> windows;std::map<int,std::string> asset_splits;std::map<int,int> asset_labels;
    while(std::getline(in,line)){
        if(line.empty())continue;
        auto f=split(line);check(f.size()==7,"raw CSV row requires exactly seven fields");
        int asset=parse_int(f[0]),win=parse_int(f[1]),label=parse_int(f[3]),idx=parse_int(f[5]);
        double temp=parse_double(f[4]),acc=parse_double(f[6]);
        check(asset>=0 && asset<100000 && win>=0 && win<100000,"invalid asset/window id");
        check(label==0 || label==1,"label must be 0 or 1");
        check(f[2]=="train" || f[2]=="validation" || f[2]=="test","unknown split");
        const auto it=asset_splits.find(asset);
        if(it==asset_splits.end())asset_splits.emplace(asset,f[2]);
        else check(it->second==f[2],"asset leaked across splits");
        const auto label_it=asset_labels.find(asset);
        if(label_it==asset_labels.end())asset_labels.emplace(asset,label);
        else check(label_it->second==label,"inconsistent asset label across windows");
        if(windows.empty() || windows.back().asset!=asset || windows.back().window!=win){
            if(!windows.empty())features(windows.back());
            check(idx==0,"each window must start at sample index zero");
            Window w;w.asset=asset;w.window=win;w.label=label;w.split=f[2];w.temperature=temp;
            windows.push_back(std::move(w));
        }
        auto& current=windows.back();
        check(current.label==label && current.split==f[2] && current.temperature==temp,"inconsistent window metadata");
        check(idx==static_cast<int>(current.vibration.size()),"missing/reordered sample index");
        current.vibration.push_back(acc);
    }
    check(!windows.empty(),"no raw windows");features(windows.back());
    // Metrics need positive and negative assets in every partition; without
    // these, e.g. recall would be mathematically undefined / misleading.
    std::array<std::array<int,2>,3> groups={};
    for(const auto& asset:asset_splits) {
        const int part=asset.second=="train"?0:(asset.second=="validation"?1:2);
        ++groups[part][asset_labels.at(asset.first)];
    }
    for(const auto& g:groups)check(g[0]>0&&g[1]>0,"each partition must contain both labelled asset classes");
    // Disallow interleaved reappearance of an earlier (asset,window) pair.
    std::map<std::pair<int,int>,bool> seen;
    for(const auto& w:windows)check(seen.emplace(std::make_pair(w.asset,w.window),true).second,"duplicate vibration window");
    return windows;
}
struct Model {int id=0,family=0;double a=0,b=0,c=0,d=0;};
Model model(int id){
    check(id>=0 && id<MODEL_COUNT,"invalid model id");
    Model m; m.id=id;m.family=id%4;
    m.a=0.35+0.045*(id%11);m.b=0.18+0.05*(id%7);
    m.c=0.12+0.04*(id%9);m.d=-1.4+0.065*(id%13);
    return m;
}
std::string num(double value){std::ostringstream s;s<<std::setprecision(17)<<value;return s.str();}
std::string formula(const Model& m){
    std::string z="("+num(m.a)+"*R+"+num(m.b)+"*K+"+num(m.c)+"*T+("+num(m.d)+"))";
    if(m.family==1)z="("+z+"+0.035*R*K)";
    if(m.family==2)z="("+z+"+0.03*R*R)";
    if(m.family==3)z="("+z+"+0.045*tanh(K))";
    return "1/(1+exp(-"+z+"))";
}
std::array<double,3> normalized(const Window& w){
    return {w.rms/0.3,(w.kurtosis-3.)/3.,(w.temperature-60.)/20.};
}
double reference(const Model& m,const Window& w){
    const auto n=normalized(w);const double R=n[0],K=n[1],T=n[2];
    double z=m.a*R+m.b*K+m.c*T+m.d;
    if(m.family==1)z+=0.035*R*K;
    if(m.family==2)z+=0.03*R*R;
    if(m.family==3)z+=0.045*std::tanh(K);
    return 1./(1.+std::exp(-z));
}
struct Engine {
    std::vector<PACEVAL_HANDLE> graph;PACEVAL_HANDLE interval=nullptr;bool initialized=false;
    Engine(){
        check(paceval_InitializeLibrary(nullptr),"paceval initialization failed");
        initialized=true;
        try{
            for(int i=0;i<MODEL_COUNT;++i){
                std::string expr=formula(model(i));
                PACEVAL_HANDLE h=paceval_CreateComputation(expr.c_str(),3,"R K T",false,nullptr);
                if(!h || paceval_GetIsError(h)){if(h){char message[256]={0},detail[256]={0};paceval_CreateErrorInformationText(h,message,detail);std::cerr<<"paceval parser: "<<message<<" / "<<detail<<"\n";paceval_DeleteComputation(h);}throw std::runtime_error("paceval graph creation failed for model "+std::to_string(i)+" formula="+expr);}
                graph.push_back(h);
            }
            const std::string f=formula(model(0));
            interval=paceval_CreateComputation(f.c_str(),3,"R K T",true,nullptr);
            if(!interval || paceval_GetIsError(interval))throw std::runtime_error("TINC graph creation failed");
        }catch(...){release();throw;}
    }
    Engine(const Engine&)=delete;Engine& operator=(const Engine&)=delete;
    ~Engine(){release();}
    void release() noexcept {
        if(interval){paceval_DeleteComputation(interval);interval=nullptr;}
        for(auto* h:graph)paceval_DeleteComputation(h);
        graph.clear();
        if(initialized){paceval_FreeLibrary();initialized=false;}
    }
    std::vector<double> evaluate(int id,const std::vector<Window>& w,size_t batch){
        check(id>=0 && id<MODEL_COUNT,"invalid model id");check(batch>=1 && batch<=8192,"bad batch size");
        std::vector<double> results;results.reserve(w.size());
        for(size_t start=0;start<w.size();start+=batch){
            const size_t n=std::min(batch,w.size()-start);
            std::vector<double> variables;variables.reserve(3*n);
            for(size_t j=0;j<n;++j){const auto p=normalized(w[start+j]);
                variables.insert(variables.end(),p.begin(),p.end());}
            std::vector<double> out(n);std::vector<int> codes(n,-1);
            const bool error=paceval_dGetComputationResultExt(graph[static_cast<size_t>(id)],variables.data(),
                static_cast<unsigned long>(n),out.data(),nullptr,nullptr,codes.data());
            check(!error,"paceval returned batch error");
            for(size_t j=0;j<n;++j)check(codes[j]==PACEVAL_ERR_NO_ERROR && std::isfinite(out[j]),"paceval returned nonfinite or error code");
            results.insert(results.end(),out.begin(),out.end());
        }
        return results;
    }
    std::array<double,3> tinc(const Window& w){
        const auto x=normalized(w);double values[]={x[0],x[1],x[2]},lo=0,hi=0;
        const double y=paceval_dGetComputationResult(interval,values,&lo,&hi);
        check(!paceval_GetIsError(interval) && std::isfinite(y) && std::isfinite(lo) && std::isfinite(hi) && lo<=hi,"invalid TINC output");
        return {y,lo,hi};
    }
};
struct Metrics {int TP=0,TN=0,FP=0,FN=0;
    void add(bool truth,bool positive){if(truth){if(positive)++TP;else ++FN;}else{if(positive)++FP;else ++TN;}}
    double precision() const {return (TP+FP)?double(TP)/(TP+FP):0;}
    double recall() const {return (TP+FN)?double(TP)/(TP+FN):0;}
    double specificity() const {return (TN+FP)?double(TN)/(TN+FP):0;}
    double f1() const {const double p=precision(),r=recall();return p+r>0?2*p*r/(p+r):0;}
    double balanced_accuracy() const{return 0.5*(recall()+specificity());}
};
struct Candidate {Model m;Metrics train,val,test;};
void save_features(const std::vector<Window>& data,const std::string& path){
    std::ofstream o(path);check(bool(o),"cannot write features");
    o<<"asset_id,window_id,split,label,temp_C,rms_g,kurtosis\n"<<std::setprecision(17);
    for(const auto& w:data)o<<w.asset<<','<<w.window<<','<<w.split<<','<<w.label<<','<<w.temperature<<','<<w.rms<<','<<w.kurtosis<<'\n';
}
void run(const std::string& raw,const std::string& scores,const std::string& feats,
         const std::string& rank,const std::string& tinc,size_t batch){
    auto data=load_raw(raw);Engine engine;
    std::ofstream output(scores);check(bool(output),"cannot write scores");
    output<<"model_id,version,asset_id,window_id,split,label,rms_g,kurtosis,temp_C,score,native_reference,decision\n"<<std::setprecision(17);
    double maxdiff=0;std::vector<Candidate> all;
    for(int id=0;id<MODEL_COUNT;++id){
        auto result=engine.evaluate(id,data,batch);
        Candidate candidate;candidate.m=model(id);
        for(size_t j=0;j<data.size();++j){
            const auto& w=data[j];const double ref=reference(candidate.m,w),y=result[j];
            maxdiff=std::max(maxdiff,std::abs(ref-y));
            check(std::abs(ref-y)<=3e-11,"native/paceval numerical mismatch");
            const bool flag=y>=THRESHOLD;
            auto* m=w.split=="train"?&candidate.train:(w.split=="validation"?&candidate.val:&candidate.test);
            m->add(w.label!=0,flag);
            output<<id<<",v1."<<id<<','<<w.asset<<','<<w.window<<','<<w.split<<','<<w.label<<','
                <<w.rms<<','<<w.kurtosis<<','<<w.temperature<<','<<y<<','<<ref<<','<<(flag?1:0)<<'\n';
        }
        all.push_back(candidate);
    }
    save_features(data,feats);
    // Top 10 selected on TRAIN ONLY. The final model is chosen on a disjoint
    // VALIDATION split, and TEST is not consulted until that model is frozen.
    std::vector<int> ids;for(int i=0;i<MODEL_COUNT;++i)ids.push_back(i);
    std::stable_sort(ids.begin(),ids.end(),[&](int a,int b){const auto& x=all[a].train;const auto& y=all[b].train;
       return x.f1()!=y.f1()?x.f1()>y.f1():a<b;});
    ids.resize(10);
    std::stable_sort(ids.begin(),ids.end(),[&](int a,int b){const auto& x=all[a].val;const auto& y=all[b].val;
       return x.f1()!=y.f1()?x.f1()>y.f1():a<b;});
    const int best=ids.front();
    std::ofstream ranked(rank);check(bool(ranked),"cannot write model metrics");
    ranked<<"model_id,version,formula,train_f1,validation_f1,test_f1,train_balanced_accuracy,validation_balanced_accuracy,test_balanced_accuracy,test_TP,test_TN,test_FP,test_FN,selected\n"<<std::setprecision(17);
    for(const auto& c:all)ranked<<c.m.id<<",v1."<<c.m.id<<','<<'"'<<formula(c.m)<<'"'<<','
         <<c.train.f1()<<','<<c.val.f1()<<','<<c.test.f1()<<','<<c.train.balanced_accuracy()<<','
         <<c.val.balanced_accuracy()<<','<<c.test.balanced_accuracy()<<','<<c.test.TP<<','<<c.test.TN<<','
         <<c.test.FP<<','<<c.test.FN<<','<<(c.m.id==best?1:0)<<'\n';
    std::ofstream intervals(tinc);check(bool(intervals),"cannot write TINC samples");
    intervals<<"asset_id,window_id,R,K,T,computed,lower,upper,reference\n"<<std::setprecision(17);
    for(size_t i=0;i<std::min<size_t>(24,data.size());++i){
        const auto p=normalized(data[i]);const auto z=engine.tinc(data[i]);
        intervals<<data[i].asset<<','<<data[i].window<<','<<p[0]<<','<<p[1]<<','<<p[2]<<','
           <<z[0]<<','<<z[1]<<','<<z[2]<<','<<reference(model(0),data[i])<<'\n';
    }
    std::cout<<"WINDOWS="<<data.size()<<" MODELS="<<MODEL_COUNT<<" EVALUATIONS="<<data.size()*MODEL_COUNT
             <<" MAX_ABS_DIFF="<<std::setprecision(10)<<maxdiff<<" SELECTED_MODEL="<<best
             <<" TEST_F1="<<all[best].test.f1()<<" TEST_BALANCED_ACCURACY="<<all[best].test.balanced_accuracy()<<'\n';
}
void self_test(){
    Window w;w.temperature=65;w.vibration.resize(256);
    for(size_t i=0;i<w.vibration.size();++i)w.vibration[i]=0.2*std::sin(i*0.12)+0.07*std::cos(i*0.5);
    features(w);check(w.rms>0.1 && w.rms<0.3,"rms test failed");
    check(w.kurtosis>1 && w.kurtosis<4,"kurtosis test failed");
    for(int id=0;id<MODEL_COUNT;++id)check(reference(model(id),w)>0 && reference(model(id),w)<1,"sigmoid failed");
    std::cout<<"Self-test PASS: 50 versioned mathematical models and feature extraction\n";
}
} // namespace
int main(int argc,char** argv){
    try{
        std::string raw,out="evaluation.csv",features="features.csv",metrics="model_metrics.csv",tinc="tinc_samples.csv";
        size_t batch=37;bool test=false;
        for(int i=1;i<argc;++i){const std::string a=argv[i];
            auto next=[&](){check(i+1<argc,"missing option value");return std::string(argv[++i]);};
            if(a=="--raw")raw=next();else if(a=="--out")out=next();
            else if(a=="--features")features=next();else if(a=="--metrics")metrics=next();
            else if(a=="--tinc")tinc=next();else if(a=="--batch")batch=static_cast<size_t>(parse_int(next()));
            else if(a=="--self-test")test=true;else throw std::runtime_error("unknown argument: "+a);
        }
        if(test){self_test();return 0;}check(!raw.empty(),"use --raw <recordings.csv>");
        run(raw,out,features,metrics,tinc,batch);return 0;
    }catch(const std::exception& e){std::cerr<<"ERROR: "<<e.what()<<'\n';return 2;}
}
