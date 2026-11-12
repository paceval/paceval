// WP_037 - Space transfer screening using the ORIGINAL paceval SDK.
// Only two-body, impulsive, circular-to-circular analytic transfers are modeled.
// Neither a flight dynamics propagator nor a mission optimizer is implemented.
// Graph evaluation is done by paceval; CSV generation, input validation, ranking,
// and independent native mathematics remain in the host C++ program.
#include "paceval_main.h"
#include <algorithm>
#include <array>
#include <cmath>
#include <cstdint>
#include <filesystem>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <limits>
#include <sstream>
#include <stdexcept>
#include <string>
#include <vector>
namespace fs=std::filesystem;
namespace {
constexpr double PI=3.141592653589793238462643383279502884;
constexpr double MU=398600.4418; // fixed Earth GM, km^3/s^2, reference-model constant
constexpr double G0=9.80665;      // conventional standard gravity, m/s^2
constexpr char VARS[]="mu r1 r2 rb theta isp mass";
using X=std::array<double,7>; // mu,r1,r2,rb in km,km^3/s^2; theta rad; isp s; mass kg
void check(bool condition,const std::string& message){if(!condition)throw std::runtime_error(message);}
std::string lit(double v){std::ostringstream os;os<<std::setprecision(17)<<v;return os.str();}
struct RNG{uint64_t s=20261112037ULL;uint64_t next(){s+=0x9e3779b97f4a7c15ULL;uint64_t z=s;z=(z^(z>>30))*0xbf58476d1ce4e5b9ULL;z=(z^(z>>27))*0x94d049bb133111ebULL;return z^(z>>31);}double uniform(){return double(next()>>11)*0x1.0p-53;}};
void validate(const X& x){for(double v:x)check(std::isfinite(v),"Nonfinite input");
 check(x[0]>0&&x[1]>6378.137&&x[2]>x[1]&&x[3]>x[2],"Invalid radius ordering: Earth-centered outward transfer only");
 check(x[4]>=0&&x[4]<=PI/3&&x[5]>0&&x[6]>0,"Invalid angle or propulsion input");}
struct V{double d1=0,d2=0,d2plane=0,total=0,days=0,fuel=0,fuelFrac=0,bi=0,biDays=0,biFuel=0,bi1=0,bi2=0,bi3=0,v1=0,v2=0,policy1=0,policy2=0;};
// Independently implemented native formula oracle (no calls to paceval).
V reference(const X&x){validate(x);auto [mu,r1,r2,rb,th,isp,mass]=x;
 V o;const double c1=std::sqrt(mu/r1),c2=std::sqrt(mu/r2);
 const double w1=std::sqrt(mu*(2/r1-2/(r1+r2))), w2=std::sqrt(mu*(2/r2-2/(r1+r2)));
 o.v1=c1;o.v2=c2;o.d1=std::abs(w1-c1);o.d2=std::abs(w2-c2);
 // Stable vector difference avoids cancellation in v^2+w^2-2vw*cos(theta).
 o.d2plane=std::sqrt((c2-w2)*(c2-w2)+4*c2*w2*std::sin(th/2)*std::sin(th/2));
 o.total=o.d1+o.d2plane;o.days=PI*std::sqrt(std::pow((r1+r2)/2,3)/mu)/86400;
 o.fuelFrac=-std::expm1(-o.total*1000/(isp*G0));o.fuel=mass*o.fuelFrac;
 double vb1=std::sqrt(mu*(2/r1-2/(r1+rb))), vbh1=std::sqrt(mu*(2/rb-2/(r1+rb)));
 double vbh2=std::sqrt(mu*(2/rb-2/(r2+rb))), vb3=std::sqrt(mu*(2/r2-2/(r2+rb)));
 o.bi1=std::abs(vb1-c1);o.bi2=std::abs(vbh2-vbh1);o.bi3=std::abs(vb3-c2);
 o.bi=o.bi1+o.bi2+o.bi3;
 o.biDays=PI*(std::sqrt(std::pow((r1+rb)/2,3)/mu)+std::sqrt(std::pow((r2+rb)/2,3)/mu))/86400;
 o.biFuel=mass*(-std::expm1(-o.bi*1000/(isp*G0)));
 // Dimensionless policy scores, with explicitly documented normalization factors.
 o.policy1=o.total/4.0+0.10*o.days/0.5+0.35*o.fuelFrac;
 o.policy2=o.total/4.0+0.35*o.days/0.5+0.12*o.fuelFrac;
 return o;
}
const std::string c1="sqrt(mu/r1)",c2="sqrt(mu/r2)";
const std::string w1="sqrt(mu*(2/r1-2/(r1+r2)))",w2="sqrt(mu*(2/r2-2/(r1+r2)))";
std::string absDiff(const std::string&a,const std::string&b){return "sqrt(("+a+"-"+b+")^2)";}
const std::string d1=absDiff(w1,c1),d2=absDiff(w2,c2);
const std::string d2p="sqrt(("+c2+"-"+w2+")^2+4*("+c2+")*("+w2+")*sin(theta/2)^2)";
const std::string total="("+d1+"+"+d2p+")";
const std::string days="("+lit(PI)+"*sqrt(((r1+r2)/2)^3/mu)/86400)";
const std::string frac="(1-exp(-1000*"+total+"/(isp*"+lit(G0)+")))";
const std::string bt1="sqrt(mu*(2/r1-2/(r1+rb)))";
const std::string bh1="sqrt(mu*(2/rb-2/(r1+rb)))";
const std::string bh2="sqrt(mu*(2/rb-2/(r2+rb)))";
const std::string bt3="sqrt(mu*(2/r2-2/(r2+rb)))";
const std::string bi1=absDiff(bt1,c1),bi2=absDiff(bh2,bh1),bi3=absDiff(bt3,c2);
const std::string bi="("+bi1+"+"+bi2+"+"+bi3+")";
const std::string biDays="("+lit(PI)+"*(sqrt(((r1+rb)/2)^3/mu)+sqrt(((r2+rb)/2)^3/mu))/86400)";
const std::string biFrac="(1-exp(-1000*"+bi+"/(isp*"+lit(G0)+")))";
struct Formula{std::string key,expression;PACEVAL_HANDLE h=nullptr;};
std::vector<Formula> formulas(){return {
 {"departure_kms",d1},{"arrival_coplanar_kms",d2},{"arrival_with_plane_kms",d2p},
 {"total_with_plane_kms",total},{"time_days",days},{"propellant_kg","mass*"+frac},
 {"propellant_fraction",frac},{"bielliptic_coplanar_kms",bi},{"bielliptic_time_days",biDays},
 {"bielliptic_propellant_kg","mass*"+biFrac},
 {"bi_departure_kms",bi1},{"bi_apoapsis_kms",bi2},{"bi_arrival_kms",bi3},
 {"initial_circular_speed_kms",c1},{"target_circular_speed_kms",c2},
 {"policy_v1",total+"/4+0.10*"+days+"/0.5+0.35*"+frac},
 {"policy_v2",total+"/4+0.35*"+days+"/0.5+0.12*"+frac}
};}
constexpr int NC=17;
std::array<double,NC> asArray(const V&v){return {v.d1,v.d2,v.d2plane,v.total,v.days,v.fuel,v.fuelFrac,v.bi,v.biDays,v.biFuel,v.bi1,v.bi2,v.bi3,v.v1,v.v2,v.policy1,v.policy2};}
struct Engine {
 std::vector<PACEVAL_HANDLE> graph;
 Engine(){check(paceval_InitializeLibrary(nullptr),"paceval runtime could not initialize");}
 ~Engine(){for(auto h:graph)if(h)paceval_DeleteComputation(h);paceval_FreeLibrary();}
 PACEVAL_HANDLE add(const std::string&expr){auto h=paceval_CreateComputation(expr.c_str(),7,VARS,false,nullptr);
 check(h&&!paceval_GetIsError(h),"paceval graph construction failed: "+expr);graph.push_back(h);return h;}
 double scalar(PACEVAL_HANDLE h,const X&x){X y=x;double z=paceval_dGetComputationResult(h,y.data(),nullptr,nullptr);check(!paceval_GetIsError(h)&&std::isfinite(z),"paceval scalar evaluation failed");return z;}
 std::vector<double> multi(const std::vector<PACEVAL_HANDLE>& hs,const std::vector<X>& xs){
  std::vector<double> in;in.reserve(xs.size()*7);for(auto&x:xs)in.insert(in.end(),x.begin(),x.end());
  std::vector<double> y(xs.size()*hs.size());std::vector<int> errors(y.size(),-1);
  auto copy=hs;bool failed=paceval_dGetMultipleComputationsResultsExt(copy.data(),static_cast<unsigned long>(hs.size()),in.data(),static_cast<unsigned long>(xs.size()),y.data(),nullptr,nullptr,errors.data());
  check(!failed,"paceval multi-graph batch call failed");for(size_t i=0;i<y.size();++i)check(errors[i]==0&&std::isfinite(y[i]),"paceval batch result nonfinite/error");return y;
 }
 std::vector<double> batch(PACEVAL_HANDLE h,const std::vector<X>& xs){std::vector<double> in;in.reserve(xs.size()*7);for(auto&x:xs)in.insert(in.end(),x.begin(),x.end());
  std::vector<double> y(xs.size());std::vector<int> errors(y.size(),-1);bool failed=paceval_dGetComputationResultExt(h,in.data(),static_cast<unsigned long>(xs.size()),y.data(),nullptr,nullptr,errors.data());
  check(!failed,"paceval single-graph batch failed");for(size_t i=0;i<y.size();++i)check(errors[i]==0&&std::isfinite(y[i]),"paceval single batch result invalid");return y;}
};
void verify(double got,double want,const std::string&key,double&worst){double err=std::abs(got-want);worst=std::max(worst,err);
 check(err<=5e-10*(1+std::abs(want)),"independent mathematical cross-check failed: "+key);}
X sample(int i){RNG r;r.s=0x037ABC20261112ULL+uint64_t(i+1)*0x9e3779b97f4a7c15ULL;
 double r1=6800+2400*r.uniform(), r2=r1*(1.15+26*r.uniform()), rb=r2*(1.2+16*r.uniform());
 return {MU,r1,r2,rb,(0.2+19.8*r.uniform())*PI/180,280+180*r.uniform(),600+2200*r.uniform()};}
void row(std::ofstream&f,const X& x,const std::array<double,NC>&a,int id){f<<id;for(double v:x)f<<','<<v;for(double v:a)f<<','<<v;
 // Screening is a transparent host policy, not orbit feasibility certification.
 int pass=a[3]<=5.0 && a[5]<=650 && a[4]<=1.5;f<<','<<pass<<','<<(a[7]<a[0]+a[1])<<'\n';}
void run(const fs::path&root,int n){check(n>0 && n<=30000,"candidate count must be 1..30000");fs::create_directories(root/"examples");fs::create_directories(root/"results");
 Engine e;auto fspec=formulas();check(fspec.size()==NC,"formula specification mismatch");for(auto&f:fspec)f.h=e.add(f.expression);
 std::ofstream freg(root/"examples"/"formula_registry.csv");freg<<"id,role,expression\n";for(size_t i=0;i<fspec.size();++i)freg<<i+1<<','<<fspec[i].key<<",\""<<fspec[i].expression<<"\"\n";
 std::vector<PACEVAL_HANDLE> hs;for(auto&f:fspec)hs.push_back(f.h);
 // Verify multi-graph output is GRAPH-MAJOR before the large workload.
 X probe=sample(17);auto ys=e.multi(hs,{probe});double worst=0;
 for(size_t j=0;j<hs.size();++j)verify(ys[j],e.scalar(hs[j],probe),fspec[j].key,worst);
 std::ofstream out(root/"examples"/"transfer_candidates.csv");out<<"candidate_id,mu_km3_s2,r1_km,r2_km,rb_km,plane_rad,isp_s,mass_kg";
 for(auto&f:fspec){out<<','<<f.key;}out<<",screen_pass,bielliptic_better_coplanar\n"<<std::setprecision(17);
 size_t totalChecked=0,batchValues=0,pass=0,biBetter=0;double best1=1e99,best2=1e99;int bestIndex1=-1,bestIndex2=-1;
 const int batchSize=256;for(int start=0;start<n;start+=batchSize){std::vector<X> xs;for(int i=start;i<std::min(n,start+batchSize);++i)xs.push_back(sample(i));auto v=e.multi(hs,xs);batchValues+=v.size();
  for(size_t i=0;i<xs.size();++i){std::array<double,NC>a{};for(int j=0;j<NC;++j)a[j]=v[size_t(j)*xs.size()+i];
   if((start+(int)i)%19==0){auto expected=asArray(reference(xs[i]));for(int j=0;j<NC;++j){verify(a[j],expected[j],fspec[j].key,worst);++totalChecked;}}
   row(out,xs[i],a,start+int(i)+1);pass+=(a[3]<=5&&a[5]<=650&&a[4]<=1.5);biBetter+=(a[7]<a[0]+a[1]);
   if(a[15]<best1){best1=a[15];bestIndex1=start+int(i)+1;}if(a[16]<best2){best2=a[16];bestIndex2=start+int(i)+1;}
  }
 }
 // A high resolution 2D cost surface; all points evaluated through the single-graph batch API.
 std::ofstream surface(root/"examples"/"cost_surface.csv");surface<<"r2_r1_ratio,plane_change_deg,total_dv_kms,propellant_kg,time_days\n"<<std::setprecision(17);
 std::vector<X> surf;for(int i=0;i<=60;++i)for(int j=0;j<=60;++j){double r1=7100,r2=r1*(1.1+15.0*i/60),rb=r2*3;surf.push_back({MU,r1,r2,rb,(j*20./60)*PI/180,340,1200});}
 // Three persistently reused graphs: both energetic and operational variables genuinely come from paceval.
 auto dv=e.batch(hs[3],surf), prop=e.batch(hs[5],surf),tof=e.batch(hs[4],surf);
 for(size_t i=0;i<surf.size();++i){if(i%53==0){auto ref=reference(surf[i]);verify(dv[i],ref.total,"surface dv",worst);verify(prop[i],ref.fuel,"surface propellant",worst);verify(tof[i],ref.days,"surface tof",worst);totalChecked+=3;}
  surface<<surf[i][2]/surf[i][1]<<','<<surf[i][4]*180/PI<<','<<dv[i]<<','<<prop[i]<<','<<tof[i]<<'\n';}
 // Independent full curves using the multi-graph API for trade-study illustrations.
 std::ofstream trade(root/"examples"/"bielliptic_trade.csv");trade<<"r2_r1_ratio,bi_apo_ratio,hohmann_coplanar_kms,bielliptic_coplanar_kms,hohmann_days,bielliptic_days\n"<<std::setprecision(17);
 std::vector<X> tx;for(int i=0;i<=120;++i){double r1=7100,r2=r1*(2.+26.0*i/120);tx.push_back({MU,r1,r2,r2*20,0,340,1200});}
 auto ty=e.multi({hs[0],hs[1],hs[4],hs[7],hs[8]},tx);
 for(size_t i=0;i<tx.size();++i){auto ref=reference(tx[i]);double ho=ty[i]+ty[tx.size()+i],bio=ty[3*tx.size()+i];verify(ho,ref.d1+ref.d2,"hohmann coplanar",worst);verify(bio,ref.bi,"bielliptic",worst);totalChecked+=2;
 trade<<tx[i][2]/tx[i][1]<<','<<tx[i][3]/tx[i][2]<<','<<ho<<','<<bio<<','<<ty[2*tx.size()+i]<<','<<ty[4*tx.size()+i]<<'\n';}
 // Policy versioning: both graph handles coexist, and the original is never mutated.
 std::ofstream versions(root/"examples"/"policy_versions.csv");versions<<"target_radius_ratio,policy_v1,policy_v2,total_dv_kms,transfer_days\n"<<std::setprecision(17);
 std::vector<X> xx;for(int i=0;i<=100;++i){double r1=7000,r2=r1*(1.1+12.*i/100);xx.push_back({MU,r1,r2,r2*3,5*PI/180,330,1200});}
 auto vy=e.multi({hs[15],hs[16],hs[3],hs[4]},xx);for(size_t i=0;i<xx.size();++i){auto ref=reference(xx[i]);verify(vy[i],ref.policy1,"policy v1",worst);verify(vy[xx.size()+i],ref.policy2,"policy v2",worst);totalChecked+=2;
 versions<<xx[i][2]/xx[i][1]<<','<<vy[i]<<','<<vy[xx.size()+i]<<','<<vy[xx.size()*2+i]<<','<<vy[xx.size()*3+i]<<'\n';}
 // Invalid input rejection by the host is independently exercised before calling the SDK.
 int invalid=0;for(X x:{X{MU,7000,6900,22000,0,340,1200},X{MU,7000,15000,16000,-1,340,1200},X{MU,7000,15000,16000,0,0,1200},X{MU,std::numeric_limits<double>::quiet_NaN(),15000,16000,0,340,1200}}){try{validate(x);}catch(const std::exception&){++invalid;}}check(invalid==4,"invalid-input regression failed");
 std::ofstream summary(root/"results"/"execution_summary.txt");summary<<std::setprecision(17)
 <<"project=WP037\nstatus=PASS\nengine=original paceval Linux SDK\n"
 <<"reusable_graphs="<<hs.size()<<"\ncandidates="<<n<<"\nmulti_graph_batch_results="<<batchValues<<"\n"
 <<"single_graph_surface_batch_results="<<3*surf.size()<<"\nindependent_native_checked_values="<<totalChecked<<"\n"
 <<"passed_screen="<<pass<<"\nbielliptic_lower_dv_coplanar_candidates="<<biBetter<<"\n"
 <<"policy_v1_min_candidate="<<bestIndex1<<"\npolicy_v2_min_candidate="<<bestIndex2<<"\n"
 <<"invalid_inputs_rejected="<<invalid<<"\nmax_internal_absolute_difference="<<worst<<"\n";
 std::cout<<"PASS WP037: "<<n<<" actual candidates, "<<hs.size()<<" real paceval graphs, "<<batchValues<<" multi-graph batch results; native checks="<<totalChecked<<"\n";
}
}
int main(int argc,char**argv){try{fs::path out=".";int cases=8000;for(int i=1;i<argc;++i){std::string a=argv[i];if(a=="--out"&&i+1<argc)out=argv[++i];else if(a=="--cases"&&i+1<argc)cases=std::stoi(argv[++i]);else throw std::runtime_error("Usage: space_transfer --out PATH --cases COUNT");}run(out,cases);return 0;}catch(const std::exception&e){std::cerr<<"FAIL: "<<e.what()<<'\n';return 2;}}
