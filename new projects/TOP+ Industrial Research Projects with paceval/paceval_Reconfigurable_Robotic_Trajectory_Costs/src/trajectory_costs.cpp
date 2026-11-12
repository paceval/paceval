// WP031: Reconfigurable full-trajectory costs, original paceval C++ SDK.
// Host generates whole trajectories, checks finite-sample disk/segment constraints,
// finite-difference derivatives, and selects a complete feasible candidate.
// paceval evaluates kinematics, singularity indicator and five versioned analytical
// whole-trajectory scoring kernels using persistent computation handles.
#include "paceval_main.h"
#include <array>
#include <cmath>
#include <cstdio>
#include <algorithm>
#include <filesystem>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <limits>
#include <stdexcept>
#include <string>
#include <vector>
namespace fs=std::filesystem;
namespace {
constexpr double PI=3.14159265358979323846, DT=0.08,L1=1.0,L2=0.78;
constexpr int N=51,CANDIDATES=16;
using Vec=std::array<double,14>;
const char* VARS="q1 q2 l1 l2 tx ty v1 v2 a1 a2 j1 j2 clear det";
void check(bool b,const std::string& s){if(!b)throw std::runtime_error(s);}
struct Engine {
 std::vector<PACEVAL_HANDLE> owned;
 Engine(){check(paceval_InitializeLibrary(nullptr),"paceval SDK initialization failed");}
 ~Engine(){for(auto h:owned)paceval_DeleteComputation(h);paceval_FreeLibrary();}
 PACEVAL_HANDLE create(const std::string& exp){auto h=paceval_CreateComputation(exp.c_str(),14,VARS,false,nullptr);check(h!=nullptr&&!paceval_GetIsError(h),"Graph creation error: "+exp);owned.push_back(h);return h;}
 double eval(PACEVAL_HANDLE h,const Vec& v){Vec copy=v;double x=paceval_dGetComputationResult(h,copy.data(),nullptr,nullptr);check(!paceval_GetIsError(h)&&std::isfinite(x),"Invalid paceval scalar result");return x;}
 void batch(PACEVAL_HANDLE h,const std::vector<Vec>& vs,const std::vector<double>& refs){std::vector<double> packed(vs.size()*14),out(vs.size());std::vector<int> stat(vs.size(),-1);for(size_t i=0;i<vs.size();i++)for(int j=0;j<14;j++)packed[i*14+j]=vs[i][j];bool failed=paceval_dGetComputationResultExt(h,packed.data(),(unsigned long)vs.size(),out.data(),nullptr,nullptr,stat.data());check(!failed,"Batch API failed");for(size_t i=0;i<vs.size();i++){check(stat[i]==0&&std::isfinite(out[i]),"Bad batch entry");check(std::abs(out[i]-refs[i]) <= 2e-9*(1+std::abs(refs[i])),"Batch oracle mismatch");}}
};
struct Q {double a,b;};
Q point(int c,int i){double t=double(i)/(N-1),s=std::sin(PI*t);
 // The same fixed initial and final joint states for every complete candidate.
 double oa=0.20*std::sin(0.73*(c+1))*s+0.09*std::sin((c%3+1)*PI*t)*s;
 double ob=0.23*std::cos(0.49*(c+2))*s+0.075*std::sin((c%4+1)*PI*t)*s;
 return {.20+.85*t+oa,1.05-.48*t+ob};}
Q target(int i){double t=double(i)/(N-1);return {.20+.85*t+.07*std::sin(PI*t),1.05-.48*t-.05*std::sin(PI*t)};}
std::array<double,2> fk(Q q){return {L1*std::cos(q.a)+L2*std::cos(q.a+q.b),L1*std::sin(q.a)+L2*std::sin(q.a+q.b)};}
// Squared minimum distance between the centerline link and a padded circular obstacle.
double segmentMargin(double ax,double ay,double bx,double by,double ox,double oy,double r){double dx=bx-ax,dy=by-ay,len=dx*dx+dy*dy;double t=std::clamp(((ox-ax)*dx+(oy-ay)*dy)/len,0.0,1.0);double x=ax+t*dx-ox,y=ay+t*dy-oy;return x*x+y*y-r*r;}
double minMargin(Q q){auto p=fk(q);double ex=L1*std::cos(q.a),ey=L1*std::sin(q.a);double m=1e10;
 // Padded obstacles chosen for a constrained but nonempty synthetic test scene.
 for(auto ob:std::array<std::array<double,3>,2>{{{0.35,1.15,0.13},{1.60,0.35,0.14}}}){
 m=std::min(m,segmentMargin(0,0,ex,ey,ob[0],ob[1],ob[2]));m=std::min(m,segmentMargin(ex,ey,p[0],p[1],ob[0],ob[1],ob[2]));}
 return m;}
struct Weights{std::string name;double wp,wv,wa,wj,wo,ws;int version;};
const std::vector<Weights> POLICIES={{"precision",6.0,.045,.0005,.000012,.0001,.00008,1},{"gentle",0.4,.22,.16,.035,.00004,.00005,1},{"clearance",0.9,.055,.001,.00003,.20,.0001,1},{"balanced",1.7,.11,.035,.004,.009,.00008,1},{"gentle",0.4,.20,.16,.055,.00004,.00005,2}};
std::string fmt(double v){char b[60];std::snprintf(b,sizeof(b),"%.17g",v);return b;}
std::string formula(const Weights& w){
 std::string x="(l1*cos(q1)+l2*cos(q1+q2))",y="(l1*sin(q1)+l2*sin(q1+q2))";
 return fmt(w.wp)+"*( ("+x+"-tx)^2+("+y+"-ty)^2 )+"+fmt(w.wv)+"*(v1^2+v2^2)+"+fmt(w.wa)+"*(a1^2+a2^2)+"+fmt(w.wj)+"*(j1^2+j2^2)+"+fmt(w.wo)+"/(0.05+clear^2)+"+fmt(w.ws)+"/(0.1+det^2)";
}
double native(const Weights& w,const Vec& v){auto p=fk({v[0],v[1]});double dx=p[0]-v[4],dy=p[1]-v[5];return w.wp*(dx*dx+dy*dy)+w.wv*(v[6]*v[6]+v[7]*v[7])+w.wa*(v[8]*v[8]+v[9]*v[9])+w.wj*(v[10]*v[10]+v[11]*v[11])+w.wo/(.05+v[12]*v[12])+w.ws/(.1+v[13]*v[13]);}
struct Metrics{double score=0,tracking=0,vel=0,acc=0,jerk=0,minclear=1e6,minabsdet=1e6;bool feasible=true;};
void run(const fs::path& out){fs::create_directories(out);Engine en;
 auto hx=en.create("l1*cos(q1)+l2*cos(q1+q2)");auto hy=en.create("l1*sin(q1)+l2*sin(q1+q2)");auto hd=en.create("l1*l2*sin(q2)");
 std::vector<PACEVAL_HANDLE> handles;for(auto& p:POLICIES)handles.push_back(en.create(formula(p)));
 std::ofstream reg(out/"formula_registry.csv");reg<<"policy,version,w_position,w_velocity,w_acceleration,w_jerk,w_obstacle,w_singularity,expression\n";
 for(auto& p:POLICIES)reg<<p.name<<','<<p.version<<','<<p.wp<<','<<p.wv<<','<<p.wa<<','<<p.wj<<','<<p.wo<<','<<p.ws<<",\""<<formula(p)<<"\"\n";
 std::ofstream detail(out/"trajectory_candidates.csv");detail<<"policy,version,candidate,feasible,total_cost,mean_tracking_m2,velocity_cost,acceleration_cost,jerk_cost,min_clearance_m2,min_abs_det\n";
 std::ofstream winners(out/"selected_trajectories.csv");winners<<"policy,version,candidate,total_cost,mean_tracking_m2,min_clearance_m2,min_abs_det\n";
 std::ofstream paths(out/"selected_path_points.csv");paths<<"policy,version,sample,time_s,q1_rad,q2_rad,x_m,y_m,margin_m2,step_cost\n";paths<<std::setprecision(17);
 std::ofstream audits(out/"numeric_audit.csv");audits<<"comparison_count,batch_count,max_absolute_error,passed\n";
 std::vector<std::vector<Vec>> candidate_rows(CANDIDATES);
 std::vector<bool> feasible(CANDIDATES,true);
 int comparisons=0,batchcount=0;double worst=0;
 for(int k=0;k<CANDIDATES;k++){
  std::vector<Q> qs;for(int i=0;i<N;i++)qs.push_back(point(k,i));
  for(int i=0;i<N;i++){
   Q q=qs[i];Q qp=qs[std::max(0,i-1)],qn=qs[std::min(N-1,i+1)];
   auto vel=[&](int j)->Q {int a=std::max(0,j-1),b=std::min(N-1,j+1);double h=(b-a)*DT;return {(qs[b].a-qs[a].a)/h,(qs[b].b-qs[a].b)/h};};
   Q v=vel(i),prevv=vel(std::max(0,i-1)),nextv=vel(std::min(N-1,i+1));
   double timebase=((i==0||i==N-1)?DT:2*DT);
   Q a={(nextv.a-prevv.a)/timebase,(nextv.b-prevv.b)/timebase};
   auto accel=[&](int j)->Q {Q va=vel(std::max(0,j-1)),vb=vel(std::min(N-1,j+1));double h=(std::min(N-1,j+1)-std::max(0,j-1))*DT;return {(vb.a-va.a)/h,(vb.b-va.b)/h};};
   Q apre=accel(std::max(0,i-1)),anext=accel(std::min(N-1,i+1));Q jerk={(anext.a-apre.a)/timebase,(anext.b-apre.b)/timebase};
   Q tg=target(i);auto pt=fk(tg);double margin=minMargin(q);double det=L1*L2*std::sin(q.b);
   Vec row{q.a,q.b,L1,L2,pt[0],pt[1],v.a,v.b,a.a,a.b,jerk.a,jerk.b,margin,det};
   check(std::isfinite(margin),"nonfinite collision proxy");
   feasible[k]=feasible[k]&&margin>=0 && std::abs(v.a)<=2.7 && std::abs(v.b)<=2.7 && std::abs(a.a)<=40 && std::abs(a.b)<=40 && std::abs(det)>=0.28;
   double px=en.eval(hx,row),py=en.eval(hy,row),pd=en.eval(hd,row);auto oracle=fk(q);
   for(auto pr:std::array<std::array<double,2>,3>{{{px,oracle[0]},{py,oracle[1]},{pd,det}}}){double err=std::abs(pr[0]-pr[1]);worst=std::max(worst,err);check(err<=2e-10,"kinematics oracle mismatch");comparisons++;}
   candidate_rows[k].push_back(row);
  }
 }
 // All candidates must share endpoints, enabling meaningful whole-path comparisons.
 for(int k=0;k<CANDIDATES;k++)check(std::abs(candidate_rows[k].front()[0]-.2)<1e-12&&std::abs(candidate_rows[k].back()[0]-1.05)<1e-12,"candidate endpoint mismatch");
 for(size_t mode=0;mode<POLICIES.size();mode++){
  double best=1e300;int chosen=-1;std::vector<Metrics> stats(CANDIDATES);
  for(int k=0;k<CANDIDATES;k++){
   Metrics m;m.feasible=feasible[k];
   for(auto& row:candidate_rows[k]){
    double val=en.eval(handles[mode],row),ref=native(POLICIES[mode],row);double diff=std::abs(val-ref);worst=std::max(worst,diff);check(diff<=2e-9*(1+std::abs(ref)),"independent full-score oracle mismatch");comparisons++;
    m.score+=val*DT;auto p=fk({row[0],row[1]});m.tracking+=(std::pow(p[0]-row[4],2)+std::pow(p[1]-row[5],2))/N;
    m.vel+=(row[6]*row[6]+row[7]*row[7])*DT;m.acc+=(row[8]*row[8]+row[9]*row[9])*DT;m.jerk+=(row[10]*row[10]+row[11]*row[11])*DT;
    m.minclear=std::min(m.minclear,row[12]);m.minabsdet=std::min(m.minabsdet,std::abs(row[13]));
   }
   stats[k]=m;detail<<POLICIES[mode].name<<','<<POLICIES[mode].version<<','<<k<<','<<(m.feasible?1:0)<<','<<std::setprecision(17)<<m.score<<','<<m.tracking<<','<<m.vel<<','<<m.acc<<','<<m.jerk<<','<<m.minclear<<','<<m.minabsdet<<'\n';
   if(m.feasible&&m.score<best){best=m.score;chosen=k;}
  }
  check(chosen>=0,"no feasible complete trajectory; check synthetic scenario");auto m=stats[chosen];
  winners<<POLICIES[mode].name<<','<<POLICIES[mode].version<<','<<chosen<<','<<std::setprecision(17)<<best<<','<<m.tracking<<','<<m.minclear<<','<<m.minabsdet<<'\n';
  for(int i=0;i<N;i++){auto row=candidate_rows[chosen][i];double value=en.eval(handles[mode],row);std::array<double,2> p{en.eval(hx,row),en.eval(hy,row)};paths<<POLICIES[mode].name<<','<<POLICIES[mode].version<<','<<i<<','<<i*DT<<','<<row[0]<<','<<row[1]<<','<<p[0]<<','<<p[1]<<','<<row[12]<<','<<value<<'\n';comparisons++;}
 }
 // Check scalar versus actual multi-point paceval SDK batch for every published policy.
 for(size_t mode=0;mode<POLICIES.size();mode++){
  std::vector<Vec> data;std::vector<double> refs;
  for(int k=0;k<CANDIDATES;k+=2)for(int j=0;j<8;j++){auto v=candidate_rows[k][j*6];data.push_back(v);refs.push_back(native(POLICIES[mode],v));}
  en.batch(handles[mode],data,refs);batchcount+=data.size();
 }
 audits<<comparisons<<','<<batchcount<<','<<std::setprecision(17)<<worst<<",true\n";
 std::cout<<"WP031 PASS graphs="<<en.owned.size()<<" full_candidates="<<CANDIDATES<<" policies="<<POLICIES.size()<<" scalar_oracle_checks="<<comparisons<<" batch="<<batchcount<<" max_error="<<worst<<"\n";
}
}
int main(int argc,char** argv){try{fs::path out="examples";for(int i=1;i<argc;i++){std::string a=argv[i];if(a=="--out"&&i+1<argc)out=argv[++i];else throw std::runtime_error("Use --out <directory>");}run(out);return 0;}catch(const std::exception& e){std::cerr<<"FAIL: "<<e.what()<<'\n';return 1;}}
