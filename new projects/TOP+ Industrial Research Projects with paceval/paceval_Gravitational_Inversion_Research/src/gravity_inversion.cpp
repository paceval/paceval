// WP_033: reproducible degree-2 gravity potential forward/inverse research demonstration.
// Units: r,R [km], mu [km^3/s^2], potential [km^2/s^2], radial field [km/s^2].
// The radial gravitational acceleration here is inward *magnitude*, NOT full vector gravity.
// No centrifugal terms, topography, tides, or observational data are modeled.
#include "paceval_main.h"
#include <algorithm>
#include <array>
#include <cmath>
#include <filesystem>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <limits>
#include <stdexcept>
#include <string>
#include <vector>
namespace fs=std::filesystem;
constexpr double R=6378.137, MU0=398600.4418, J0=0.00108262668;
constexpr const char* VARS="r c mu j"; // c=cos(colatitude)
using X=std::array<double,4>;
void check(bool b,const std::string& msg){if(!b)throw std::runtime_error(msg);}
double p2(double c){return 0.5*(3*c*c-1);}
double pot(X a){return a[2]/a[0]*(1-a[3]*(R/a[0])*(R/a[0])*p2(a[1]));}
double radial(X a){return a[2]/(a[0]*a[0])*(1-3*a[3]*(R/a[0])*(R/a[0])*p2(a[1]));}
double dmu(X a){return (1-3*a[3]*(R/a[0])*(R/a[0])*p2(a[1]))/(a[0]*a[0]);}
double dj(X a){return -3*a[2]*R*R*p2(a[1])/(a[0]*a[0]*a[0]*a[0]);}
double gradient_theta(X a){return 9*a[2]*a[3]*R*R*a[1]*std::sqrt(std::max(0.,1-a[1]*a[1]))/std::pow(a[0],4);}
class Engine{
 std::vector<PACEVAL_HANDLE> hs;
public:
 Engine(){check(paceval_InitializeLibrary(nullptr),"SDK initialization failed");}
 ~Engine(){for(auto h:hs)paceval_DeleteComputation(h);paceval_FreeLibrary();}
 int create(const std::string& s){auto h=paceval_CreateComputation(s.c_str(),4,VARS,false,nullptr);check(h&&!paceval_GetIsError(h),"SDK formula creation failed: "+s);hs.push_back(h);return (int)hs.size()-1;}
 double eval(int n,X x){double y=paceval_dGetComputationResult(hs.at(n),x.data(),nullptr,nullptr);check(!paceval_GetIsError(hs[n])&&std::isfinite(y),"invalid paceval value");return y;}
 std::vector<double> batch(int n,const std::vector<X>& xs){std::vector<double> x(4*xs.size()),y(xs.size());std::vector<int> status(xs.size(),-1);for(size_t i=0;i<xs.size();++i)for(int j=0;j<4;++j)x[4*i+j]=xs[i][j];bool error=paceval_dGetComputationResultExt(hs[n],x.data(),(unsigned long)xs.size(),y.data(),nullptr,nullptr,status.data());check(!error,"paceval batch failed");for(size_t i=0;i<xs.size();++i)check(status[i]==0&&std::isfinite(y[i]),"paceval batch status invalid");return y;}
};
void near(double x,double ref,double& worst){double e=std::abs(x-ref);worst=std::max(worst,e);check(e<=3e-11*(1+std::abs(ref)),"independent C++ numerical audit failed");}
struct Obs{double r,c,y,clean;};
struct Fit{double mu,j,rms;};
// Solve a well-scaled two-coefficient weighted LS problem for the linearized model
// g(r,c)=m*A(r,c)+b*B(r,c), where m=mu/MU0, b=mu*j/(MU0*J0).
// The host inversion uses normal equations only after dimensionless feature scaling.
Fit fit(const std::vector<Obs>& obs){
 long double aa=0,bb=0,ab=0,ay=0,by=0;
 for(auto& o:obs){double a=MU0/(o.r*o.r),b=-3*MU0*J0*R*R*p2(o.c)/std::pow(o.r,4); // normalized to 0.01 units
  long double A=a/.01L,B=b/.01L,Y=o.y/.01L;
  aa+=A*A;bb+=B*B;ab+=A*B;ay+=A*Y;by+=B*Y;}
 long double det=aa*bb-ab*ab;check(det>1e-20L,"rank-deficient observations");
 double m=(double)((ay*bb-by*ab)/det),b=(double)((aa*by-ab*ay)/det);
 check(m>0,"nonpositive fitted mu");double mu=m*MU0,j=b*J0/m;
 double ss=0;for(auto&o:obs){double e=radial({o.r,o.c,mu,j})-o.y;ss+=e*e;}
 return {mu,j,std::sqrt(ss/obs.size())};}
int main(int argc,char**argv){try{
 fs::path out="examples";for(int i=1;i<argc;++i)if(std::string(argv[i])=="--out"&&i+1<argc)out=argv[++i];fs::create_directories(out);
 Engine e;
 std::vector<std::pair<std::string,std::string>> formulas={
 {"potential", "mu/r*(1-j*(6378.137/r)^2*((3*c^2-1)/2))"},
 {"radial_gravity", "mu/r^2*(1-3*j*(6378.137/r)^2*((3*c^2-1)/2))"},
 {"d_g_d_mu", "(1-3*j*(6378.137/r)^2*((3*c^2-1)/2))/r^2"},
 {"d_g_d_j", "-3*mu*6378.137^2*((3*c^2-1)/2)/r^4"},
 {"d_g_d_theta", "9*mu*j*6378.137^2*c*sqrt(1-c^2)/r^4"},
 {"monopole", "mu/r^2"},
 {"squared_residual", "(mu/r^2*(1-3*j*(6378.137/r)^2*((3*c^2-1)/2))-0.008)^2"},
 {"revision_quadrupole_scaled", "mu/r^2*(1-3*j*1.1*(6378.137/r)^2*((3*c^2-1)/2))"}
 };
 std::vector<int> h;std::ofstream reg(out/"formula_registry.csv");reg<<"id,name,version,expression\n";
 for(size_t k=0;k<formulas.size();++k){h.push_back(e.create(formulas[k].second));reg<<k+1<<','<<formulas[k].first<<','<<(k==7?2:1)<<",\""<<formulas[k].second<<"\"\n";}
 const double trueMu=MU0*1.0007,trueJ=J0*1.035;
 std::ofstream survey(out/"synthetic_observations.csv");survey<<std::setprecision(17)<<"id,r_km,cos_colatitude,radial_clean_km_s2,radial_observed_km_s2\n";
 std::vector<Obs> all;double worst=0;int scalar=0;
 for(int ir=0;ir<32;++ir)for(int ic=0;ic<30;++ic){double r=R+250.+ir*24.,c=-.96+ic*1.92/29.;X x={r,c,trueMu,trueJ};double pure=e.eval(1,x);near(pure,radial(x),worst);scalar++;
 // Deterministic bounded perturbation, not a model of an actual sensor.
 double noise=1e-8*(std::sin((ir+1)*1.73+(ic+1)*2.21)+0.2*std::cos(ir*0.4-ic));double y=pure+noise;
 all.push_back({r,c,y,pure});survey<<all.size()<<','<<r<<','<<c<<','<<pure<<','<<y<<'\n';}
 Fit f=fit(all),cleanFit;{auto tmp=all;for(auto&x:tmp)x.y=x.clean;cleanFit=fit(tmp);}
 // Holdout uses a different radial/angle grid, not the training points.
 double hold=0;int holdn=0;for(int ir=0;ir<13;++ir)for(int ic=0;ic<17;++ic){double r=R+266+ir*51.,c=-.93+ic*1.86/16.;double delta=radial({r,c,f.mu,f.j})-radial({r,c,trueMu,trueJ});hold+=delta*delta;++holdn;}hold=std::sqrt(hold/holdn);
 std::ofstream diag(out/"inversion_summary.csv");diag<<std::setprecision(17)<<"fit,mu_km3_s2,j2,rms_km_s2\ntrue,"<<trueMu<<','<<trueJ<<",0\nnoisy,"<<f.mu<<','<<f.j<<','<<f.rms<<"\nnoiseless,"<<cleanFit.mu<<','<<cleanFit.j<<','<<cleanFit.rms<<"\n";
 std::ofstream grid(out/"gravity_surface.csv");grid<<std::setprecision(17)<<"r_km,cos_colatitude,potential_km2_s2,radial_km_s2,monopole_km_s2,scaled_version_km_s2,d_g_d_mu,d_g_d_j,d_g_d_theta\n";
 std::vector<X> surf;
 for(int ir=0;ir<61;++ir)for(int ic=0;ic<61;++ic)surf.push_back({R+230+ir*13.,-0.98+ic*1.96/60.,trueMu,trueJ});
 std::array<std::vector<double>,8> columns;
 for(int j=0;j<8;++j)columns[j]=e.batch(j,surf);
 for(size_t i=0;i<surf.size();++i){const X& x=surf[i];std::array<double,8> v{};
  for(int j=0;j<8;++j)v[j]=columns[j][i];
  near(v[0],pot(x),worst);near(v[1],radial(x),worst);near(v[2],dmu(x),worst);near(v[3],dj(x),worst);near(v[4],gradient_theta(x),worst);near(v[5],x[2]/(x[0]*x[0]),worst);near(v[7],radial({x[0],x[1],x[2],x[3]*1.1}),worst);
  grid<<x[0]<<','<<x[1]<<','<<v[0]<<','<<v[1]<<','<<v[5]<<','<<v[7]<<','<<v[2]<<','<<v[3]<<','<<v[4]<<'\n';}
 std::vector<X> xs;for(int i=0;i<256;++i)xs.push_back({R+300+i*3.,-0.96+i*1.92/255.,trueMu,trueJ});int batch=0;
 for(int j=0;j<8;++j){auto ys=e.batch(j,xs);for(int i=0;i<256;++i){double val=e.eval(j,xs[i]);near(ys[i],val,worst);++batch;++scalar;}}
 // Probe the analytic partials with centered differences; finite differencing done by C++ host.
 int gradientChecks=0;for(int i=0;i<16;++i){X x={R+350+i*21.,-0.85+i*.1,trueMu,trueJ};double dmStep=0.1,djStep=1e-7;
 X p=x,m=x;p[2]+=dmStep;m[2]-=dmStep;near(e.eval(2,x),(radial(p)-radial(m))/(2*dmStep),worst);p=x;m=x;p[3]+=djStep;m[3]-=djStep;near(e.eval(3,x),(radial(p)-radial(m))/(2*djStep),worst);++gradientChecks;}
 check(std::abs(cleanFit.mu-trueMu)<1e-5 && std::abs(cleanFit.j-trueJ)<1e-10,"noiseless parameter recovery failed");
 std::ofstream audit(out/"execution_summary.txt");audit<<std::setprecision(17)<<"paceval graphs: 8\nsynthetic observations: "<<all.size()<<"\nsurface samples: 3721\nscalar SDK calls: "<<scalar<<"\nbatch results compared: "<<batch<<"\nanalytic derivative checks: "<<gradientChecks*2<<"\nholdout RMS km/s2: "<<hold<<"\nnoisy recovered mu: "<<f.mu<<"\nnoisy recovered J2: "<<f.j<<"\nnoiseless recovered mu: "<<cleanFit.mu<<"\nnoiseless recovered J2: "<<cleanFit.j<<"\nmax native scalar audit absolute difference: "<<worst<<"\nstatus: PASS\n";
 std::cout<<"PASS: "<<all.size()<<" observations, 8 paceval graphs, "<<scalar<<" scalar, "<<batch<<" batch results; recovered mu="<<f.mu<<" J2="<<f.j<<"\n";
 return 0;
 }catch(const std::exception& ex){std::cerr<<"FAIL: "<<ex.what()<<'\n';return 1;}}
