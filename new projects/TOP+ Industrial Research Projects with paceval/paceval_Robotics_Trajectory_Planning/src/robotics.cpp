// paceval Robotic Trajectories Research - offline C++17 demonstrator.
// Scope: synthetic planar two-link arm, finite-grid waypoint scoring and
// simplified *centerline-segment versus circle* geometry. This is not a
// motion-planning library, a full 3D collision checker, or a robot controller.
//
// paceval owns the *mathematical* execution: kinematics, a 2x2 Jacobian,
// determinant, a tracking/smoothness objective, its analytic gradient,
// and clearances at host-computed clamped projection parameters. The C++ host
// owns candidate generation, geometric nearest-point projection, safety
// acceptance, transition interpolation, CSV I/O and the greedy search.
//
// The original SDK translation unit paceval_main.cpp is compiled alongside
// this file. Link against an externally supplied original Linux paceval .so.
// No handwritten dlopen/dlsym signatures or bundled runtime are used.
#include "paceval_main.h"
#include <algorithm>
#include <array>
#include <cmath>
#include <cstddef>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <limits>
#include <sstream>
#include <stdexcept>
#include <string>
#include <vector>

namespace demo {
constexpr std::size_t NV=14, NG=15;
using V=std::array<double,NV>;
using R=std::array<double,NG>;
enum Col {Q1,Q2,L1,L2,TX,TY,P1,P2,W,OX,OY,RADIUS,T1,T2};
const char* const VARS="q1 q2 l1 l2 tx ty p1 p2 w ox oy radius t1 t2";
// A single variable schema is used for every graph and candidate row.
// The clamped t1 and t2 parameters lie in [0,1], computed by host geometry.
// Thus each segment clearance is the *exact squared distance for these planar
// centerline segments and static circles*, not full robot-volume checking.
static const std::array<const char*,NG> FORMULAS={{
    "l1*cos(q1)",
    "l1*sin(q1)",
    "l1*cos(q1)+l2*cos(q1+q2)",
    "l1*sin(q1)+l2*sin(q1+q2)",
    "-l1*sin(q1)-l2*sin(q1+q2)",
    "-l2*sin(q1+q2)",
    "l1*cos(q1)+l2*cos(q1+q2)",
    "l2*cos(q1+q2)",
    "l1*l2*sin(q2)",
    "(l1*cos(q1)+l2*cos(q1+q2)-tx)^2+(l1*sin(q1)+l2*sin(q1+q2)-ty)^2+w*((q1-p1)^2+(q2-p2)^2)",
    "(l1*cos(q1)+l2*cos(q1+q2)-ox)^2+(l1*sin(q1)+l2*sin(q1+q2)-oy)^2-radius^2",
    "(t1*l1*cos(q1)-ox)^2+(t1*l1*sin(q1)-oy)^2-radius^2",
    "(l1*cos(q1)+t2*l2*cos(q1+q2)-ox)^2+(l1*sin(q1)+t2*l2*sin(q1+q2)-oy)^2-radius^2",
    "2*(l1*cos(q1)+l2*cos(q1+q2)-tx)*(-l1*sin(q1)-l2*sin(q1+q2))+2*(l1*sin(q1)+l2*sin(q1+q2)-ty)*(l1*cos(q1)+l2*cos(q1+q2))+2*w*(q1-p1)",
    "2*(l1*cos(q1)+l2*cos(q1+q2)-tx)*(-l2*sin(q1+q2))+2*(l1*sin(q1)+l2*sin(q1+q2)-ty)*l2*cos(q1+q2)+2*w*(q2-p2)"
}};

[[noreturn]] void fail(const std::string& msg){throw std::runtime_error(msg);}
void require(bool ok,const std::string& msg){if(!ok)fail(msg);}
double clamp01(double v){return std::max(0.0,std::min(1.0,v));}
struct Point {double x=0,y=0;};
struct Obstacle {double x,y,r;};
constexpr std::array<Obstacle,2> OBS{{{0.48,1.14,0.13},{1.19,-0.14,0.15}}};
constexpr double PAD=0.035;  // user-visible synthetic safety padding (metres)
constexpr double L1M=1.0,L2M=0.78;
constexpr double SMOOTH=0.17;
constexpr double MAX_STEP=0.24; // per-joint angle change per planner step
struct Joints {double q1=0.35,q2=1.0;};
Point elbow(Joints q){return {L1M*std::cos(q.q1),L1M*std::sin(q.q1)};}
Point endpoint(Joints q){const Point e=elbow(q);return {e.x+L2M*std::cos(q.q1+q.q2),e.y+L2M*std::sin(q.q1+q.q2)};}
// Standard closest-point projection onto a finite segment, including both
// endpoints. The host computes the clamp because this is a geometric policy,
// not a claim that paceval implements a general geometry engine.
double projection(Point a,Point b,Obstacle o){
    const double dx=b.x-a.x,dy=b.y-a.y, d=dx*dx+dy*dy;
    require(d>0,"Degenerate robot segment");
    return clamp01(((o.x-a.x)*dx+(o.y-a.y)*dy)/d);
}
double squared_clearance(Point a,Point b,Obstacle o){
    const double t=projection(a,b,o), dx=a.x+t*(b.x-a.x)-o.x,
      dy=a.y+t*(b.y-a.y)-o.y;
    return dx*dx+dy*dy-(o.r+PAD)*(o.r+PAD);
}
// Each row describes one candidate and one obstacle. Its two clamped
// projection parameters are precomputed by the host. The circle radius is
// expanded by PAD to provide a documented synthetic clearance margin.
V values(Joints q,Point target,Joints previous,Obstacle obstacle){
    const Point e=elbow(q),end=endpoint(q);
    const double t1=projection({0,0},e,obstacle),t2=projection(e,end,obstacle);
    return {{q.q1,q.q2,L1M,L2M,target.x,target.y,previous.q1,previous.q2,
        SMOOTH,obstacle.x,obstacle.y,obstacle.r+PAD,t1,t2}};
}
// Independent native C++ implementation: no calls to paceval, and geometric
// clearances use nearest-point vectors instead of merely reusing graph results.
R native(const V&v){
    const double q1=v[Q1],q2=v[Q2],a=v[L1],b=v[L2],
      c1=std::cos(q1),s1=std::sin(q1),c12=std::cos(q1+q2),s12=std::sin(q1+q2);
    const double ex=a*c1,ey=a*s1,x=ex+b*c12,y=ey+b*s12;
    R r{};
    r[0]=ex;r[1]=ey;r[2]=x;r[3]=y;
    r[4]=-a*s1-b*s12;r[5]=-b*s12;
    r[6]=x;r[7]=b*c12;r[8]=a*b*std::sin(q2);
    const double dx=x-v[TX],dy=y-v[TY];
    r[9]=dx*dx+dy*dy+v[W]*((q1-v[P1])*(q1-v[P1])+(q2-v[P2])*(q2-v[P2]));
    const double radius2=v[RADIUS]*v[RADIUS];
    r[10]=(x-v[OX])*(x-v[OX])+(y-v[OY])*(y-v[OY])-radius2;
    const Point p1={v[T1]*ex,v[T1]*ey};
    const Point p2={ex+v[T2]*b*c12,ey+v[T2]*b*s12};
    r[11]=(p1.x-v[OX])*(p1.x-v[OX])+(p1.y-v[OY])*(p1.y-v[OY])-radius2;
    r[12]=(p2.x-v[OX])*(p2.x-v[OX])+(p2.y-v[OY])*(p2.y-v[OY])-radius2;
    r[13]=2*dx*r[4]+2*dy*r[6]+2*v[W]*(q1-v[P1]);
    r[14]=2*dx*r[5]+2*dy*r[7]+2*v[W]*(q2-v[P2]);
    return r;
}
struct Audit{std::size_t checks=0,failures=0;double max_abs=0;
    void check(double got,double ref){
        ++checks;const double err=std::abs(got-ref);
        max_abs=std::max(max_abs,err);
        if(!std::isfinite(got)||err>3e-11*(1+std::max(std::abs(got),std::abs(ref))))++failures;
    }
};
// SDK owns the handle implementation. RAII ensures all live handles are
// destroyed *before* paceval_FreeLibrary, including on exception paths.
class Paceval{
    bool initialized_=false;std::vector<PACEVAL_HANDLE> owned_;
public:
    Paceval(){require(paceval_InitializeLibrary(nullptr),"paceval_InitializeLibrary failed");initialized_=true;}
    Paceval(const Paceval&)=delete;Paceval& operator=(const Paceval&)=delete;
    ~Paceval(){for(auto it=owned_.rbegin();it!=owned_.rend();++it)paceval_DeleteComputation(*it);
        if(initialized_)paceval_FreeLibrary();}
    std::string error(PACEVAL_HANDLE h){char txt[PACEVAL_MAXERR+1]{};long position=0;
        int type=paceval_GetErrorInformation(h,txt,&position);
        return std::to_string(type)+" at position "+std::to_string(position)+" near "+txt;}
    PACEVAL_HANDLE make(const char* f,bool tinc=false){
        PACEVAL_HANDLE h=paceval_CreateComputation(f,(unsigned long)NV,VARS,tinc,nullptr);
        require(h!=nullptr,std::string("Cannot create paceval graph: ")+f);
        owned_.push_back(h);
        require(!paceval_GetIsError(h),"Formula analysis failed: "+error(h));return h;
    }
    // API contract: input sample-major [sample][variable]; output graph-major
    // [graph][sample]. All 15 graphs share precisely the same 14 variables.
    void many(const std::vector<PACEVAL_HANDLE>& handles,std::vector<double>&input,
              std::size_t rows,std::vector<double>&out){
        require(rows>0 && input.size()==NV*rows,"Invalid paceval batch dimensions");
        std::vector<PACEVAL_HANDLE> mutable_handles=handles;
        out.assign(handles.size()*rows,0);std::vector<int>errors(out.size(),-1);
        const bool error_flag=paceval_dGetMultipleComputationsResultsExt(mutable_handles.data(),
          (unsigned long)handles.size(),input.data(),(unsigned long)rows,
          out.data(),nullptr,nullptr,errors.data());
        require(!error_flag,"paceval multi-graph API returned failure");
        for(std::size_t i=0;i<errors.size();++i)
            require(errors[i]==PACEVAL_ERR_NO_ERROR&&std::isfinite(out[i]),
               "Invalid paceval batch output row="+std::to_string(i));
        for(auto h:handles)require(!paceval_GetIsError(h),"Graph computation error: "+error(h));
    }
    std::array<double,3> interval(PACEVAL_HANDLE h,const V&v){
        V mutable_values=v;double low=0,high=0;
        double z=paceval_dGetComputationResult(h,mutable_values.data(),&low,&high);
        require(!paceval_GetIsError(h),"TINC error: "+error(h));
        require(std::isfinite(z)&&std::isfinite(low)&&std::isfinite(high)&&low<=high,
            "Invalid pointwise TINC interval");
        return {{z,low,high}};
    }
};

// For each candidate configuration we submit one row *per obstacle*.
// Both the endpoint-only and complete-centerline clearance proxies are
// therefore evaluated by paceval on both circles, even though the geometry
// here is purposefully limited to a planar 2-link arm and circular disks.
struct Candidate{Joints q;R first{};double min_margin=0;bool feasible=false;};
class Engine{
    Paceval p;std::vector<PACEVAL_HANDLE> g;
    PACEVAL_HANDLE tinc_x=nullptr;
    PACEVAL_HANDLE tinc_y=nullptr; // PACEVAL_HANDLE expands to void*: declare separately.
    Audit audited;
public:
    Engine(){for(auto f:FORMULAS)g.push_back(p.make(f));
        tinc_x=p.make(FORMULAS[2],true);tinc_y=p.make(FORMULAS[3],true);}
    Audit stats()const{return audited;}
    std::array<double,3> interval(const V&v,bool x){return p.interval(x?tinc_x:tinc_y,v);}
    void evaluate(std::vector<Candidate>&c,Point target,Joints previous,
                 std::size_t batch){
        require(batch>=OBS.size(),"Batch must accommodate at least one row per obstacle");
        for(std::size_t pos=0;pos<c.size();){
            // Two obstacle rows per candidate; each batch is bounded by the
            // actual input row count, not by number of candidate objects.
            std::size_t n=std::min(batch/OBS.size(),c.size()-pos);n=std::max(std::size_t(1),n);
            const std::size_t rows=n*OBS.size();
            std::vector<V> records;records.reserve(rows);
            std::vector<double> input;input.reserve(rows*NV);
            for(std::size_t j=0;j<n;++j)for(const auto&ob:OBS){
                V v=values(c[pos+j].q,target,previous,ob);
                records.push_back(v);
                for(double value:v)input.push_back(value);
            }
            std::vector<double> output;p.many(g,input,rows,output);
            for(std::size_t j=0;j<n;++j){
                double margin=std::numeric_limits<double>::infinity();
                for(std::size_t ob=0;ob<OBS.size();++ob){
                    std::size_t row=j*OBS.size()+ob;
                    R reference=native(records[row]);
                    for(std::size_t k=0;k<NG;++k)
                        audited.check(output[k*rows+row],reference[k]);
                    for(std::size_t k=10;k<=12;++k)
                        margin=std::min(margin,output[k*rows+row]);
                    if(ob==0)for(std::size_t k=0;k<NG;++k)
                        c[pos+j].first[k]=output[k*rows+row];
                }
                c[pos+j].min_margin=margin;
                c[pos+j].feasible=(margin>=-1e-12);
            }
            pos+=n;
        }
        require(audited.failures==0,"paceval / independent C++ mismatch beyond tolerance");
    }
};

// These finite-segment interpolation checks are host-owned. They ensure the
// transition between successive candidate joints respects the same simplified
// circle geometry, not merely that discrete endpoint configurations are safe.
bool safe(Joints q){
    const Point a=elbow(q),b=endpoint(q);
    for(const auto&ob:OBS){
        if(squared_clearance({0,0},a,ob)<-1e-12||
           squared_clearance(a,b,ob)<-1e-12)return false;
    }return true;
}
bool safe_transition(Joints from,Joints to){
    const double d1=to.q1-from.q1,d2=to.q2-from.q2;
    if(std::abs(d1)>MAX_STEP+1e-12 ||std::abs(d2)>MAX_STEP+1e-12)return false;
    // Sampled interpolation is *not* continuous path certification.
    for(int s=0;s<=12;++s){double t=s/12.0;
        if(!safe({from.q1+t*d1,from.q2+t*d2}))return false;
    }return true;
}
void self_test(){
    const Joints q={0.71,1.12};const Point tgt={1.3,0.8};
    const Joints last={0.65,1.1};const V v=values(q,tgt,last,OBS[0]);
    const R r=native(v);
    require(std::abs(r[8]-L1M*L2M*std::sin(q.q2))<1e-15,"Jacobian determinant identity");
    const double h=1e-6;
    for(int k=0;k<2;++k){
        Joints p=q,m=q; if(k==0){p.q1+=h;m.q1-=h;}else{p.q2+=h;m.q2-=h;}
        const R plus=native(values(p,tgt,last,OBS[0]));
        const R minus=native(values(m,tgt,last,OBS[0]));
        require(std::abs((plus[2]-minus[2])/(2*h)-r[4+k])<2e-9,"Jacobian x finite difference");
        require(std::abs((plus[3]-minus[3])/(2*h)-r[6+k])<2e-9,"Jacobian y finite difference");
        require(std::abs((plus[9]-minus[9])/(2*h)-r[13+k])<2e-8,"Cost gradient finite difference");
    }
    require(std::abs(projection({0,0},{1,0},{-1,0,0.1}))<1e-15,"Segment near start");
    require(std::abs(projection({0,0},{1,0},{3,0,0.1})-1)<1e-15,"Segment near end");
    require(std::abs(projection({0,0},{1,0},{.5,.2,.1})-.5)<1e-15,"Segment interior");
    require(safe({0.35,1.0}),"Initial configuration must be collision-free");
    std::cout<<"PASS native: kinematics, finite-difference Jacobian and gradients, segment projections\n";
}
struct Waypoint{std::string id;Point target;};
std::vector<Waypoint> waypoints(const std::string& path){
    std::ifstream f(path);require(f.good(),"Cannot open waypoint CSV: "+path);
    std::vector<Waypoint> out;std::string line;std::size_t line_no=0;
    while(std::getline(f,line)){
        ++line_no;if(line.empty()||line[0]=='#'||line.rfind("step_id,",0)==0)continue;
        std::istringstream s(line);std::string id,a,b,more;
        require(bool(std::getline(s,id,','))&&bool(std::getline(s,a,','))&&bool(std::getline(s,b,','))&&!std::getline(s,more,','),
            "Expected step_id,target_x,target_y on input line "+std::to_string(line_no));
        require(!id.empty(),"Empty waypoint id");
        auto parse=[](const std::string&str){std::size_t n=0;double v=std::stod(str,&n);
            require(n==str.size()&&std::isfinite(v),"Invalid waypoint float");return v;};
        Point t={parse(a),parse(b)};
        require(std::hypot(t.x,t.y)<=L1M+L2M+1e-12,"Waypoint is outside workspace");
        out.push_back({id,t});
    }
    require(!out.empty(),"Empty waypoint input");return out;
}
std::vector<Candidate> grid(std::size_t resolution){
    require(resolution>=5&&resolution<=121,"Grid resolution must be in [5,121]");
    std::vector<Candidate> c;c.reserve(resolution*resolution);
    for(std::size_t i=0;i<resolution;++i)for(std::size_t j=0;j<resolution;++j){
        double q1=-0.1+1.8*double(i)/double(resolution-1);
        double q2=-0.2+2.4*double(j)/double(resolution-1);
        c.push_back({{q1,q2}});
    }
    return c;
}
struct Step{std::string id;Point target,endpoint;Joints q;double cost,margin,det;};
static void csv_header(std::ostream&f){f<<"step_id,target_x,target_y,q1,q2,endpoint_x,endpoint_y,cost,min_circle_margin_sq,jacobian_determinant\n";}
void save(const std::string&path,const std::vector<Step>&steps){
    std::ofstream f(path);require(f.good(),"Cannot create trajectory CSV: "+path);
    csv_header(f);f<<std::setprecision(17);
    for(const auto&s:steps){f<<s.id<<","<<s.target.x<<","<<s.target.y<<","<<s.q.q1<<","<<s.q.q2<<","<<s.endpoint.x<<","<<s.endpoint.y<<","<<s.cost<<","<<s.margin<<","<<s.det<<"\n";}
    require(f.good(),"Trajectory CSV write failed");
}
void write_tinc(const std::string&path,Engine&engine,const std::vector<Step>&steps){
    std::ofstream f(path);require(f.good(),"Cannot create TINC CSV");f<<"sample_id,expression";
    std::istringstream ss(VARS);std::string name;while(ss>>name)f<<","<<name;
    f<<",paceval_result,tinc_lower,tinc_upper\n"<<std::setprecision(17);
    for(std::size_t k=0;k<24;++k){
        const Step&s=steps[k*steps.size()/24];
        const Joints previous=(k*steps.size()/24? steps[k*steps.size()/24-1].q:Joints{0.35,1.0});
        const V v=values(s.q,s.target,previous,OBS[0]);
        const bool use_x=(k%2==0);
        const auto interval=engine.interval(v,use_x);
        f<<"point_"<<k<<","<<(use_x?"endpoint_x":"endpoint_y");
        for(double val:v)f<<","<<val;
        for(double val:interval)f<<","<<val;
        f<<"\n";
    }
    require(f.good(),"TINC CSV write failed");
}
void plan(const std::string&input,const std::string&output,const std::string&tinc,
          std::size_t grid_size,std::size_t batch,std::size_t limit){
    auto targets=waypoints(input);
    if(limit)targets.resize(std::min(limit,targets.size()));
    std::vector<Step>steps;steps.reserve(targets.size());
    require(safe({0.35,1.0}),"Initial configuration is unsafe");
    Joints previous={0.35,1.0};Engine engine;
    for(const auto&wp:targets){
        auto candidates=grid(grid_size);
        engine.evaluate(candidates,wp.target,previous,batch);
        const Candidate* best=nullptr;
        for(const auto&candidate:candidates){
            if(!candidate.feasible||!safe_transition(previous,candidate.q))continue;
            if(!best||candidate.first[9]<best->first[9])best=&candidate;
        }
        require(best!=nullptr,"No feasible joint candidate at waypoint "+wp.id);
        const Point end={best->first[2],best->first[3]};
        steps.push_back({wp.id,wp.target,end,best->q,best->first[9],
                         best->min_margin,best->first[8]});
        previous=best->q;
    }
    save(output,steps);write_tinc(tinc,engine,steps);
    const auto audit=engine.stats();
    require(audit.failures==0,"Independent reference audit failed");
    std::cout<<"PASS original paceval runtime: "<<steps.size()<<" waypoint selections, "
        <<audit.checks<<" checked scalar graph results, "<<audit.failures<<" mismatches\n";
    std::cout<<"Wrote "<<output<<" and "<<tinc<<"\n";
}
} // namespace demo

int main(int argc,char**argv){
    try{
        std::string input="examples/waypoints.csv",out="trajectory.csv",tinc="tinc_samples.csv";
        std::size_t grid=31,batch=256,steps=0;bool test=false;
        for(int i=1;i<argc;++i){std::string a=argv[i];
            auto next=[&](){if(i+1>=argc)demo::fail("Missing value for "+a);return std::string(argv[++i]);};
            auto num=[&](const std::string&s){std::size_t used=0;
                unsigned long v=std::stoul(s,&used);demo::require(used==s.size(),"Invalid integer");return std::size_t(v);};
            if(a=="--self-test")test=true;
            else if(a=="--waypoints")input=next();
            else if(a=="--out-csv")out=next();
            else if(a=="--tinc-csv")tinc=next();
            else if(a=="--grid")grid=num(next());
            else if(a=="--batch")batch=num(next());
            else if(a=="--steps")steps=num(next());
            else if(a=="--help"){
                std::cout<<"Usage: robotics [--self-test] [--waypoints CSV] [--grid N] [--batch N] "
                  "[--steps N] [--out-csv PATH] [--tinc-csv PATH]\n";
                return 0;
            } else demo::fail("Unknown argument: "+a);
        }
        demo::self_test();
        if(!test)demo::plan(input,out,tinc,grid,batch,steps);
        return 0;
    }catch(const std::exception&e){std::cerr<<"FAIL: "<<e.what()<<"\n";return 1;}
}
