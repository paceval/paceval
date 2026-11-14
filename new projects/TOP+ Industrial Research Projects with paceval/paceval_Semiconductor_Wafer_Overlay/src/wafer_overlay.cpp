// paceval research demonstrator: wafer overlay and distortion correction.
// Original paceval API is in paceval_main.{h,cpp}; do not replace it with a mock.
// Copyright (c) 2026 paceval research example. SDK files retain their upstream notices.
#include "paceval_main.h"
#include <algorithm>
#include <array>
#include <cmath>
#include <cstddef>
#include <cstdlib>
#include <filesystem>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <limits>
#include <map>
#include <numeric>
#include <regex>
#include <sstream>
#include <stdexcept>
#include <string>
#include <vector>

namespace fs = std::filesystem;
constexpr double PI=3.1415926535897932384626433832795;
constexpr double RADIUS_MM=150.0;
constexpr unsigned N_VARS=7;
constexpr char VARS[]="u v temp dxMeasured dyMeasured sigma siteIndex";
constexpr int N_LOTS=10;
constexpr int N_GRID=10000;

std::string trim(const std::string& in){auto a=in.find_first_not_of(" \t\r\n");if(a==std::string::npos)return "";auto b=in.find_last_not_of(" \t\r\n");return in.substr(a,b-a+1);}
std::vector<std::string> split(const std::string& s){std::vector<std::string> v;std::stringstream ss(s);std::string a;while(std::getline(ss,a,','))v.push_back(trim(a));return v;}
void require(bool yes,const std::string& msg){if(!yes)throw std::runtime_error(msg);}
class Engine {
    std::vector<PACEVAL_HANDLE> owned_;
public:
    Engine(){require(paceval_InitializeLibrary(nullptr),"paceval_InitializeLibrary failed");}
    ~Engine(){for(auto h:owned_)paceval_DeleteComputation(h);paceval_FreeLibrary();}
    Engine(const Engine&)=delete;Engine& operator=(const Engine&)=delete;
    // paceval uses a math-expression parser. Industrial CSV must allow a strict
    // numeric token only; a user-provided expression is NOT silently evaluated.
    double parse(const std::string& src)const{
        static const std::regex dec(R"(^[+-]?(?:[0-9]+(?:\.[0-9]*)?|\.[0-9]+)(?:[eE][+-]?[0-9]+)?$)");
        std::string s=trim(src);require(std::regex_match(s,dec),"Non-canonical numeric CSV field: '"+s+"'");
        int err=-1;long pos=-1;double x=paceval_dConvertStringToFloat(s.c_str(),&err,&pos,false,nullptr,nullptr);
        require(err==PACEVAL_ERR_NO_ERROR&&std::isfinite(x),"paceval string-to-double failed: '"+s+"' error "+std::to_string(err));
        return x;
    }
    std::string fmt(double x)const{
        require(std::isfinite(x),"Cannot convert a non-finite numeric value to CSV");
        char buf[512]={};int n=paceval_dConvertFloatToString(buf,x);
        require(n>0 && buf[0],"paceval double-to-string failed");
        return std::string(buf);
    }
    PACEVAL_HANDLE make(const std::string& formula) {
        auto h=paceval_CreateComputation(formula.c_str(),N_VARS,VARS,false,nullptr);
        require(h!=nullptr,"paceval_CreateComputation returned null");
        if(paceval_GetIsError(h)){
            char msg[256]={},details[256]={};paceval_CreateErrorInformationText(h,msg,details);
            paceval_DeleteComputation(h);throw std::runtime_error("paceval graph creation failed: "+formula.substr(0,80)+" / "+msg+" / "+details);
        }
        owned_.push_back(h);return h;
    }
    std::vector<double> batch(const std::vector<PACEVAL_HANDLE>& handles,const std::vector<double>& values,unsigned rows) const {
        require(!handles.empty() && values.size()==static_cast<size_t>(rows)*N_VARS,"Invalid multi-graph batch dimensions");
        std::vector<PACEVAL_HANDLE> hs(handles);
        std::vector<double> val(values),outs(static_cast<size_t>(rows)*hs.size());
        std::vector<int> errors(outs.size(),-999);
        // SDK returns a Boolean error indicator, not a count of successful results.
        // The per-cell error array and finiteness checks are authoritative.
        paceval_dGetMultipleComputationsResultsExt(hs.data(),static_cast<unsigned long>(hs.size()),val.data(),rows,
                 outs.data(),nullptr,nullptr,errors.data());
        for(size_t i=0;i<outs.size();++i) require(errors[i]==PACEVAL_ERR_NO_ERROR && std::isfinite(outs[i]),
           "paceval batch cell "+std::to_string(i)+" failed: "+std::to_string(errors[i]));
        return outs; // graph-major: for every graph, all rows are contiguous
    }
    double scalar(PACEVAL_HANDLE h,std::array<double,N_VARS> a)const{
        double out=paceval_dGetComputationResult(h,a.data(),nullptr,nullptr);
        require(!paceval_GetIsError(h)&&std::isfinite(out),"Scalar paceval calculation failed");
        return out;
    }
};

std::array<double,15> basis(double u,double v,double temp){
    const double t=(temp-25.0)/20.0;
    return {1,u,v,u*u,u*v,v*v,t,t*u,t*v,u*u*u,u*u*v,u*v*v,v*v*v,
            std::sin(PI*u)*std::cos(PI*v),std::sin(PI*v)*std::cos(PI*u)};
}
const std::array<std::string,15> B={
 "1","u","v","sqr(u)","u*v","sqr(v)","((temp-25)/20)","((temp-25)/20)*u","((temp-25)/20)*v",
 "u*u*u","u*u*v","u*v*v","v*v*v","sin(pi*u)*cos(pi*v)","sin(pi*v)*cos(pi*u)"};
const std::array<std::string,15> DU={
 "0","1","0","2*u","v","0","0","((temp-25)/20)","0","3*sqr(u)","2*u*v","sqr(v)","0",
 "pi*cos(pi*u)*cos(pi*v)","(-pi*sin(pi*v)*sin(pi*u))"};
const std::array<std::string,15> DV={
 "0","0","1","0","u","2*v","0","0","((temp-25)/20)","0","sqr(u)","2*u*v","3*sqr(v)",
 "(-pi*sin(pi*u)*sin(pi*v))","pi*cos(pi*v)*cos(pi*u)"};
const std::array<const char*,15> BN={"intercept","u","v","u2","uv","v2","tau","tauu","tauv","u3","u2v","uv2","v3","harmonic_u","harmonic_v"};

// True map is a declared synthetic generator, NOT a physical scanner model.
// It is deliberately not identical to either fitted candidate.
double synthetic_truth(int lot,double u,double v,double t,bool xaxis){
    double tt=(t-25.0)/20.0, drift=lot*.055;
    if(xaxis) return 3.25+drift+1.25*u-.95*v+.72*u*u-.36*u*v+.43*v*v+.43*tt+.18*tt*u-.12*tt*v
        +.62*u*u*u+.24*u*u*v-.27*u*v*v+.17*v*v*v+.46*sin(PI*u)*cos(PI*v)-.31*sin(PI*v)*cos(PI*u)
        +.11*sin(7*u+2*v+lot*.15);
    return -2.4+lot*.048-.78*u+1.1*v-.3*u*u+.52*u*v+.25*v*v-.32*tt+.10*tt*u+.21*tt*v
        -.48*u*u*u+.3*u*u*v+.19*u*v*v-.21*v*v*v-.35*sin(PI*u)*cos(PI*v)+.39*sin(PI*v)*cos(PI*u)
        +.09*cos(3*u-6*v+lot*.12);
}
// Single sample of a synthetic fab metrology file.
struct Sample {int lot=0,id=0;double u=0,v=0,temp=25,dx=0,dy=0,sigma=.4;bool holdout=false;};
// Deterministic sensor noise with rare moderate and strong outliers.
std::array<double,2> synthetic_observation(int lot,int id,double u,double v,double temp){
    double nx=.19*sin(id*1.13+lot*.5)+.12*cos(id*.77+lot*.2);
    double ny=.17*cos(id*1.37+lot*.3)-.11*sin(id*.59+lot*.7);
    if(id%83==0){nx+=1.45;ny-=.65;}
    else if(id%41==0){nx+=.76;ny+=.37;}
    return {synthetic_truth(lot,u,v,temp,true)+nx,synthetic_truth(lot,u,v,temp,false)+ny};
}
// Produce a physically interpretable synthetic wafer, all coordinates inside R=150mm.
void generate_data(const Engine& eng,const fs::path& base){
    fs::create_directories(base);
    std::ofstream tr(base/"synthetic_metrology.csv"),grid(base/"wafer_grid_inputs.csv");
    require(bool(tr)&&bool(grid),"Failed to open input CSV output");
    tr<<"lotId,siteId,xMm,yMm,tempC,dxObservedNm,dyObservedNm,sigmaNm,isHoldout\n";
    grid<<"lotId,siteId,xMm,yMm,tempC,dxObservedNm,dyObservedNm,sigmaNm,isHoldout\n";
    for(int lot=0;lot<N_LOTS;++lot){
        int id=0;
        for(int yi=0;yi<23;++yi)for(int xi=0;xi<23;++xi){
            double u=(xi-11.)/11.,v=(yi-11.)/11.; if(u*u+v*v>1.0)continue;
            double t=19.5+10.0*(.5+.5*sin(yi*.41+xi*.27+lot*.6));
            auto a=synthetic_observation(lot,id,u,v,t);
            bool holdout=((id+2*lot)%5==0);
            tr<<lot<<','<<id<<','<<eng.fmt(u*RADIUS_MM)<<','<<eng.fmt(v*RADIUS_MM)<<','<<eng.fmt(t)<<','
              <<eng.fmt(a[0])<<','<<eng.fmt(a[1])<<','<<eng.fmt(.42)<<','<<int(holdout)<<'\n';++id;
        }
        for(int j=0;j<N_GRID;++j){
            constexpr double GOLDEN=0.6180339887498949;
            double f=std::fmod((j+.5)*GOLDEN,1.0),a=2*PI*f,r=sqrt((j+.5)/N_GRID);
            double u=r*cos(a),v=r*sin(a),temp=21.+8.*sin(.009*j+.17*lot);
            auto o=synthetic_observation(lot,j+100000,u,v,temp);
            grid<<lot<<','<<j<<','<<eng.fmt(u*RADIUS_MM)<<','<<eng.fmt(v*RADIUS_MM)<<','<<eng.fmt(temp)<<','
                <<eng.fmt(o[0])<<','<<eng.fmt(o[1])<<','<<eng.fmt(.42)<<",1\n";
        }
    }
}
std::vector<Sample> read_data(const Engine& eng,const fs::path& file){
    std::ifstream is(file);require(bool(is),"Missing CSV input: "+file.string());
    std::string line;require(bool(std::getline(is,line)),"Empty input CSV");
    require(line=="lotId,siteId,xMm,yMm,tempC,dxObservedNm,dyObservedNm,sigmaNm,isHoldout", "Unexpected CSV schema");
    std::vector<Sample> a;a.reserve(100000);
    while(std::getline(is,line)){
        if(trim(line).empty())continue;
        auto cells=split(line);require(cells.size()==9,"Invalid input CSV field count");
        Sample v;double lot=eng.parse(cells[0]),id=eng.parse(cells[1]),ho=eng.parse(cells[8]);
        require(lot>=0 && lot<N_LOTS && floor(lot)==lot && id>=0 && floor(id)==id,"Invalid lot/site number");
        require((ho==0||ho==1),"Invalid holdout marker");v.lot=int(lot);v.id=int(id);v.holdout=(ho==1);
        double x=eng.parse(cells[2]),y=eng.parse(cells[3]);v.u=x/RADIUS_MM;v.v=y/RADIUS_MM;
        v.temp=eng.parse(cells[4]);v.dx=eng.parse(cells[5]);v.dy=eng.parse(cells[6]);v.sigma=eng.parse(cells[7]);
        require(v.u*v.u+v.v*v.v<=1+1e-12,"CSV contains coordinates outside wafer domain");
        require(v.temp>=10 && v.temp<=50 && v.sigma>.01 && v.sigma<2,"CSV temperature/sigma outside declared range");
        a.push_back(v);
    }
    return a;
}

// Modified Gram-Schmidt QR with re-orthogonalization is strictly host-side fitting.
// paceval evaluates the fitted model, corrections, quality guards and sensitivities.
std::vector<double> fit(const std::vector<Sample>& d,int lot,int version,bool xaxis){
    const int p=version==0?9:15;std::vector<std::vector<double>> rows;std::vector<double> rhs;
    for(const auto& s:d)if(s.lot==lot&&!s.holdout){auto b=basis(s.u,s.v,s.temp);rows.emplace_back(b.begin(),b.begin()+p);rhs.push_back(xaxis?s.dx:s.dy);}
    int m=int(rows.size());require(m>p+20,"Not enough training data");
    // Householder QR, full rank; unlike normal equations it avoids squaring cond(A).
    // The reflector is copied BEFORE the column is modified. Reusing the
    // updated column as a reflector would silently corrupt subsequent columns.
    std::vector<double> x=rhs;std::vector<std::vector<double>> q=rows;
    for(int k=0;k<p;++k){
        double norm=0;for(int i=k;i<m;++i)norm=std::hypot(norm,q[i][k]);
        require(norm>1e-11,"Rank-deficient synthetic design");
        double alpha=(q[k][k]>=0?-norm:norm);
        std::vector<double> reflector(static_cast<size_t>(m-k));
        reflector[0]=q[k][k]-alpha;
        for(int i=k+1;i<m;++i)reflector[i-k]=q[i][k];
        double vnorm=0;for(double val:reflector)vnorm+=val*val;
        require(vnorm>0,"Invalid Householder normal");const double beta=2/vnorm;
        for(int j=k;j<p;++j){
            double dot=0;for(int i=k;i<m;++i)dot+=reflector[i-k]*q[i][j];dot*=beta;
            for(int i=k;i<m;++i)q[i][j]-=dot*reflector[i-k];
        }
        double dot=0;for(int i=k;i<m;++i)dot+=reflector[i-k]*x[i];dot*=beta;
        for(int i=k;i<m;++i)x[i]-=dot*reflector[i-k];
        q[k][k]=alpha;for(int i=k+1;i<m;++i)q[i][k]=0;
    }
    std::vector<double> coef(p);
    for(int j=p-1;j>=0;--j){double acc=x[j];for(int i=j+1;i<p;++i)acc-=q[j][i]*coef[i];coef[j]=acc/q[j][j];}
    for(double v:coef)require(std::isfinite(v),"Non-finite fit coefficient");
    return coef;
}
struct GDef {std::string name,expression,units,description;PACEVAL_HANDLE handle=nullptr;};
struct Model {int lot=0,ver=0;std::vector<double> cx,cy;std::vector<GDef> graphs;};
std::string polynomial(const Engine& eng,const std::vector<double>& c,const std::array<std::string,15>& functions){
    std::string s="(";
    for(size_t j=0;j<c.size();++j){if(j)s+='+';s+='('+eng.fmt(c[j])+")*("+functions[j]+")";}
    return s+")";
}
Model make_model(Engine& eng,int lot,int ver,const std::vector<Sample>& train){
    Model m;m.lot=lot;m.ver=ver;
    m.cx=fit(train,lot,ver,true);m.cy=fit(train,lot,ver,false);
    // Reparse the actual text coefficients. This closes the audit loop for the
    // ~15-significant-digit decimal serialization provided by the SDK.
    for(double& c:m.cx)c=eng.parse(eng.fmt(c));
    for(double& c:m.cy)c=eng.parse(eng.fmt(c));
    // This known synthetic generator must yield a physically plausible
    // nanometre-scale intercept; catches accidental QR/regression corruption.
    require(std::abs(m.cx[0])>1 && std::abs(m.cy[0])>1,
            "Fitted intercept implausible for the declared synthetic truth");
    const auto x=polynomial(eng,m.cx,B), y=polynomial(eng,m.cy,B);
    const auto xu=polynomial(eng,m.cx,DU),xv=polynomial(eng,m.cx,DV),yu=polynomial(eng,m.cy,DU),yv=polynomial(eng,m.cy,DV);
    const std::string dx="(dxMeasured-("+x+"))",dy="(dyMeasured-("+y+"))";
    const std::string rad="sqrt(sqr("+dx+")+sqr("+dy+"))";
    auto add=[&](std::string name,std::string expression,std::string unit,std::string purpose){
        GDef g;g.name=std::move(name);g.expression=std::move(expression);g.units=std::move(unit);g.description=std::move(purpose);
        g.handle=eng.make(g.expression);m.graphs.push_back(std::move(g));
    };
    add("overlayDx",x,"nm","Predicted overlay x direction");
    add("overlayDy",y,"nm","Predicted overlay y direction");
    add("residualX",dx,"nm","Measured minus predicted x");
    add("residualY",dy,"nm","Measured minus predicted y");
    add("residualNorm",rad,"nm","Euclidean overlay residual");
    add("waferMargin","(1-sqr(u)-sqr(v))","1","Circular wafer-domain margin");
    add("residualMargin","(3.5*sigma-("+rad+"))","nm","Guard to an illustrative 3.5 sigma threshold");
    add("riskScore","(sqr(("+rad+")/sigma)+0.06*sqr((temp-25)/20))","1","Composite normalized quadratic loss");
    add("accept","(((1-sqr(u)-sqr(v))>=0) AND (("+rad+")<=(2*sigma)))","0/1","ACCEPT rule only in the valid wafer domain");
    add("review","(((1-sqr(u)-sqr(v))>=0) AND (("+rad+")>(2*sigma)) AND (("+rad+")<=(3.5*sigma)))","0/1","REVIEW decision region");
    add("reject","(((1-sqr(u)-sqr(v))<0) OR (("+rad+")>(3.5*sigma)))","0/1","REJECT decision region");
    add("dDx_dU",xu,"nm/norm","Analytic x correction derivative w.r.t. u");
    add("dDx_dV",xv,"nm/norm","Analytic x correction derivative w.r.t. v");
    add("dDy_dU",yu,"nm/norm","Analytic y correction derivative w.r.t. u");
    add("dDy_dV",yv,"nm/norm","Analytic y correction derivative w.r.t. v");
    const std::string predUnc="sqrt(sqr(sigma)+sqr(0.00015)*(sqr("+xu+")+sqr("+xv+")+sqr("+yu+")+sqr("+yv+")))";
    add("illustrativeUncertainty",predUnc,"nm","First-order propagation with illustrative position input uncertainty");
    add("clampedResidual","(("+rad+") min (3.5*sigma)) max 0","nm","Display-only capped residual via min/max");
    add("fieldSlot","(siteIndex mod 16)","integer","Deterministic routing slot for metrology record");
    return m;
}
std::vector<double> pack(const std::vector<Sample>& rows,size_t off,size_t n){
    std::vector<double> out(n*N_VARS);
    for(size_t k=0;k<n;++k){const auto& s=rows[off+k];double* p=out.data()+k*N_VARS;
        p[0]=s.u;p[1]=s.v;p[2]=s.temp;p[3]=s.dx;p[4]=s.dy;p[5]=s.sigma;p[6]=double(s.id);}
    return out;
}
struct Totals {size_t rows=0,accept=0,review=0,reject=0;double residual2=0,raw2=0,maxResidual=0;};
void write_sample_line(const Engine& e,std::ofstream& out,const Model& m,const Sample& s,const std::vector<double>& d,size_t pos,size_t n){
    out<<s.lot<<','<<(m.ver==0?"quadratic_v1":"cubic_harmonic_v2")<<','<<s.id<<','<<e.fmt(s.u*RADIUS_MM)<<','
       <<e.fmt(s.v*RADIUS_MM)<<','<<e.fmt(s.temp)<<','<<e.fmt(s.dx)<<','<<e.fmt(s.dy);
    for(size_t j=0;j<m.graphs.size();++j)out<<','<<e.fmt(d[j*n+pos]);
    out<<'\n';
}
Totals eval(Engine& e,const Model& m,const std::vector<Sample>& rows,std::ofstream& sampleFile,
            std::ofstream& holdoutFile,const bool isGrid,size_t maxRows,size_t& numOutputs,size_t& batches){
    std::vector<Sample> subset;subset.reserve(std::min(maxRows,rows.size()));
    for(auto& s:rows)if(s.lot==m.lot&&subset.size()<maxRows)subset.push_back(s);
    std::vector<PACEVAL_HANDLE> handles;for(auto& g:m.graphs)handles.push_back(g.handle);
    Totals tot;constexpr size_t BATCH=512;
    for(size_t off=0;off<subset.size();off+=BATCH){size_t n=std::min(BATCH,subset.size()-off);
        std::vector<double> args=pack(subset,off,n);
        auto r=e.batch(handles,args,static_cast<unsigned>(n));numOutputs+=r.size();++batches;
        for(size_t i=0;i<n;++i){const auto& s=subset[off+i];
            double rn=r[4*n+i];
            double a=r[8*n+i],b=r[9*n+i],c=r[10*n+i];
            require(a==0||a==1,"Accept Boolean out of range");
            require(b==0||b==1,"Review Boolean out of range");
            require(c==0||c==1,"Reject Boolean out of range");
            require(a+b+c==1,"Quality partition is not mutually exclusive/exhaustive");
            require(r[5*n+i]>=-5e-13,"Inside-wafer input resulted in invalid wafer margin");
            require(r[17*n+i]>=0&&r[17*n+i]<16&&std::floor(r[17*n+i])==r[17*n+i],"Invalid modulo field slot");
            if(a==1)++tot.accept;else if(b==1)++tot.review;else ++tot.reject;
            ++tot.rows;tot.residual2+=rn*rn;tot.raw2+=s.dx*s.dx+s.dy*s.dy;tot.maxResidual=std::max(tot.maxResidual,rn);
            if(isGrid){if(s.id%40==0)write_sample_line(e,sampleFile,m,s,r,i,n);}
            else if(s.holdout)write_sample_line(e,holdoutFile,m,s,r,i,n);
        }
    }
    return tot;
}
// C++17 does not have sqr; keep host arithmetic explicit and only for aggregate summaries.
double square(double a){return a*a;}

void check_layout(Engine& e){
    auto a=e.make("u+2*v");auto b=e.make("3*u-v");
    std::vector<double> vals{1,2,25,0,0,1,0, 2,3,25,0,0,1,1};
    auto out=e.batch({a,b},vals,2);
    require(out.size()==4,"Unexpected graph-major result shape");
    for(size_t i=0;i<4;++i)require(std::abs(out[i]-(std::array<double,4>{5,8,1,3})[i])<1e-12,"Batch API layout mismatch");
    require(std::abs(e.scalar(a,{2,3,25,0,0,1,0})-8)<1e-12,"Scalar API result differs from batch");
}
void test_operators(Engine& e){
    std::vector<std::pair<std::string,double>> operators={
        {"((-1) mod 10)",9},{"((-1) % 10)",-1},{"((3 min 2) max 0)",2},
        {"((u>=0) AND (u<=1))",1},{"((u<0) OR (u>1))",0},
        {"(u<>0)",1},{"floor(3.8)",3},{"round(3.5)",4},
        {"sqr(3)",9},{"(pi>3)",1},{"fac(5)",120},{"5!",120},{"sig(0)",0.5},
        {"ceil(2.2)",3},{"floor(-2.5)",-3},{"abs(-2)",2},{"sgn(-2)",-1},{"((1 AND 1) XOR 0)",1}};
    for(auto& test:operators){auto h=e.make(test.first);double a=e.scalar(h,{.5,0,25,0,0,1,0});
        require(std::abs(a-test.second)<1e-9,"Failed operator: "+test.first+" got "+e.fmt(a));}
    // Relational operators have parser-specific precedence. Explicitly
    // parenthesize the multiplication side of each Boolean comparison.
    auto edge=e.make("((dxMeasured<=(2*sigma)) AND (sigma>0))");
    require(e.scalar(edge,{0,0,25,.94,0,.42,0})==0,
            "Threshold expression unexpectedly accepts above-limit residual");
    require(e.scalar(edge,{0,0,25,.72,0,.42,0})==1,
            "Threshold expression unexpectedly rejects below-limit residual");
    for(auto s:{"0","-0.0025","1.25e-5","+2.0","10000000"}){
        double n=e.parse(s);double copy=e.parse(e.fmt(n));
        require(std::abs(n-copy)<1e-12+1e-13*std::abs(n),"CSV numeric round-trip mismatch");
    }
    std::cout<<"PASS: "<<operators.size()<<" operator semantics, canonical conversions and scalar evaluation\n";
}
void test_invalid(Engine& e){
    for(auto& bad:{"NaN","Infinity","1,25","2+3","3.2junk","","3 4","1e10000"}){
        bool rejected=false;try{(void)e.parse(bad);}catch(const std::exception&){rejected=true;}
        require(rejected,std::string("Invalid numeric token was accepted: ")+bad);
    }
    require(std::isfinite(e.parse("1.5e-4")),"Valid scientific notation rejected");
    std::cout<<"PASS: unsafe CSV values and expression injection rejected\n";
}

int parse_int_arg(const Engine& e,const char* a,int lo,int hi){double d=e.parse(a);require(d>=lo && d<=hi && std::floor(d)==d,"Invalid integer CLI limit");return int(d);}
int main(int argc,char** argv){
    try{
        Engine e;
        std::string mode=argc<2?"--run":argv[1];
        if(mode=="--test-operators"){test_operators(e);return 0;}
        if(mode=="--test-invalid"){test_invalid(e);return 0;}
        if(mode=="--test-layout"){check_layout(e);return 0;}
        fs::path root=PROJECT_ROOT;
        if(mode=="--generate"){generate_data(e,root/"examples");std::cout<<"Generated deterministic CSV inputs in "<<(root/"examples").string()<<"\n";return 0;}
        require(mode=="--run","Unknown mode; use --run / --generate / --test-operators / --test-invalid / --test-layout");
        int lotLimit=N_LOTS,gridLimit=N_GRID;fs::path target=root/"results";
        for(int a=2;a<argc;++a){std::string k=argv[a];require(a+1<argc,"Option without argument: "+k);
            if(k=="--lot-limit")lotLimit=parse_int_arg(e,argv[++a],1,N_LOTS);
            else if(k=="--grid-limit")gridLimit=parse_int_arg(e,argv[++a],1,N_GRID);
            else if(k=="--out")target=argv[++a];else throw std::runtime_error("Unknown argument: "+k);
        }
        fs::create_directories(target);
        auto tr=read_data(e,root/"examples"/"synthetic_metrology.csv");
        auto gr=read_data(e,root/"examples"/"wafer_grid_inputs.csv");
        std::ofstream coeff(target/"fitted_coefficients.csv"),formulas(target/"graph_registry.csv"),inv(target/"math_execution_inventory.csv"),
                stat(target/"wafer_summary.csv"),grid(target/"wafer_grid_sample.csv"),holdout(target/"holdout_results.csv"),log(target/"sdk_execution.txt");
        require(bool(coeff)&&bool(formulas)&&bool(inv)&&bool(stat)&&bool(grid)&&bool(holdout)&&bool(log),"Unable to create output files");
        coeff<<"lotId,version,axis,basisIndex,basisName,coefficient\n";
        formulas<<"lotId,version,graphId,functionName,expressionLength,expression,variableOrder,status\n";
        inv<<"functionId,domainQuantity,mathematicalDefinition,units,executionOwner,pacevalGraphId,formulaVersion,apiPath,referenceTest,status,hostReason\n";
        stat<<"lotId,version,rows,accept,review,reject,residualRmsNm,maxResidualNm,rawObservedRmsNm\n";
        grid<<"lotId,version,siteId,xMm,yMm,tempC,observedDxNm,observedDyNm";
        holdout<<"lotId,version,siteId,xMm,yMm,tempC,observedDxNm,observedDyNm";
        // See graph list in make_model for the fixed column sequence.
        for(auto name:{"overlayDx","overlayDy","residualX","residualY","residualNorm","waferMargin","residualMargin","riskScore","accept","review","reject","dDx_dU","dDx_dV","dDy_dU","dDy_dV","illustrativeUncertainty","clampedResidual","fieldSlot"}){
            grid<<','<<name;holdout<<','<<name;
        }
        grid<<'\n';holdout<<'\n';
        size_t outputs=0,batches=0;test_operators(e);check_layout(e);
        for(int lot=0;lot<lotLimit;++lot){for(int ver=0;ver<2;++ver){
            Model m=make_model(e,lot,ver,tr);
            const std::string vName=ver==0?"quadratic_v1":"cubic_harmonic_v2";
            for(int axis=0;axis<2;++axis){const auto& c=axis==0?m.cx:m.cy;
                for(size_t i=0;i<c.size();++i)coeff<<lot<<','<<vName<<','<<(axis==0?"dx":"dy")<<','<<i<<','<<BN[i]<<','<<e.fmt(c[i])<<'\n';}
            for(size_t gi=0;gi<m.graphs.size();++gi){const auto& g=m.graphs[gi];std::string id="lot"+std::to_string(lot)+"_v"+std::to_string(ver+1)+"_g"+std::to_string(gi);
                // CSV-escape the formula by using a quoted cell; no user-controlled tokens.
                formulas<<lot<<','<<vName<<','<<id<<','<<g.name<<','<<g.expression.size()<<",\""<<g.expression<<"\","<<VARS<<",executed\n";
                inv<<id<<','<<g.description<<",\""<<g.expression<<"\","<<g.units<<",paceval,"<<id<<','<<vName
                    <<",dGetMultipleComputationsResultsExt,verify_results.py,executed,\n";
            }
            Totals t=eval(e,m,gr,grid,holdout,true,gridLimit,outputs,batches);
            // A separate evaluation of the measured metrology sites supports held-out checks.
            Totals h=eval(e,m,tr,grid,holdout,false,std::numeric_limits<size_t>::max(),outputs,batches);
            stat<<lot<<','<<vName<<','<<t.rows<<','<<t.accept<<','<<t.review<<','<<t.reject<<','
                <<e.fmt(std::sqrt(t.residual2/t.rows))<<','<<e.fmt(t.maxResidual)<<','<<e.fmt(std::sqrt(t.raw2/t.rows))<<'\n';
            log<<"lot="<<lot<<" version="<<vName<<" graphs="<<m.graphs.size()<<" grid="<<t.rows
                <<" holdout_total="<<h.rows<<" grid_accept="<<t.accept<<" grid_review="<<t.review<<" grid_reject="<<t.reject<<"\n";
            std::cout<<"PASS lot "<<lot<<" "<<vName<<" graphs="<<m.graphs.size()<<" grid="<<t.rows
                 <<" held-out-record-source="<<h.rows<<"\n";
        }}
        log<<"SDK=original paceval 4.25, Linux shared library, no performance comparisons\n";
        log<<"graph_objects="<<(lotLimit*2*18)<<" graph_cell_evaluations="<<outputs<<" multi_graph_batches="<<batches<<"\n";
        log<<"model_families=quadratic_v1,cubic_harmonic_v2\n";
        log<<"csv_numeric_parse=paceval_dConvertStringToFloat + strict lexical validation\n";
        log<<"csv_numeric_format=paceval_dConvertFloatToString (~15 significant decimal digits; audited)\n";
        log<<"input_contract=normalized u,v radius 150 mm; temperatures 10..50 C; synthetic overlay nm\n";
        log<<"physics_scope=synthetic, no fab qualification or actuator control\n";
        std::cout<<"PASS graph_objects="<<lotLimit*2*18<<" graph_outputs="<<outputs<<" batches="<<batches<<'\n';
        return 0;
    }catch(const std::exception& e){std::cerr<<"FAIL "<<e.what()<<'\n';return 1;}
}
