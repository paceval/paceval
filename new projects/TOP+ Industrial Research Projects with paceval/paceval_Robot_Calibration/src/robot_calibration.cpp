// paceval Robot Calibration Residuals: reproducible synthetic 6R demonstration.
// All model coordinate / residual evaluations are performed by the original
// paceval computation objects. The independent oracle uses matrix products,
// not the symbolic expression strings supplied to paceval.
// Copyright notice for the vendor SDK remains in paceval_main.h/.cpp.
#include "paceval_main.h"
#include "generated_formulas.h"
#include <array>
#include <algorithm>
#include <cmath>
#include <cstdint>
#include <cstdlib>
#include <filesystem>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <limits>
#include <random>
#include <sstream>
#include <stdexcept>
#include <string>
#include <vector>

using V3=std::array<double,3>; using A6=std::array<double,6>;
using Params=std::array<double,9>;
constexpr double PI=3.14159265358979323846;
constexpr std::array<double,6> LINK={{0.45,0.53,0.42,0.16,0.27,0.14}};
constexpr Params TRUE_P={{0.008,-0.012,0.007,0.010,-0.006,0.011,0.006,-0.009,0.004}};
constexpr int NP=9;
static void require(bool ok,const std::string& msg){if(!ok) throw std::runtime_error(msg);}
struct Observation {std::string split; int id=0; A6 q{}; V3 measured{};};
using Observations=std::vector<Observation>;

// Independent forward kinematics: fixed base frame, intrinsic local rotations
// Z-Y-Y-X-Y-Z, then local link translation. q_i and encoder zero offsets in rad;
// all lengths and TCP measured coordinates in metres. This native matrix path
// is structurally different from the paceval expanded closed expressions.
static V3 native_fk(const A6&q,const Params&p){
 double r[3][3]={{1,0,0},{0,1,0},{0,0,1}};
 V3 x={{0,0,0}}; double lens[6];
 std::copy(LINK.begin(),LINK.end(),lens);
 lens[1]+=p[6];lens[2]+=p[7];lens[5]+=p[8];
 const char axes[]="ZYYXYZ";
 for(int k=0;k<6;k++){
  double a=q[k]+p[k],c=std::cos(a),s=std::sin(a);
  double h[3][3]={{1,0,0},{0,1,0},{0,0,1}};
  if(axes[k]=='Z') {h[0][0]=c;h[0][1]=-s;h[1][0]=s;h[1][1]=c;}
  if(axes[k]=='Y') {h[0][0]=c;h[0][2]=s;h[2][0]=-s;h[2][2]=c;}
  if(axes[k]=='X') {h[1][1]=c;h[1][2]=-s;h[2][1]=s;h[2][2]=c;}
  double z[3][3]={{0,0,0},{0,0,0},{0,0,0}};
  for(int i=0;i<3;i++)for(int j=0;j<3;j++)for(int m=0;m<3;m++)z[i][j]+=r[i][m]*h[m][j];
  for(int i=0;i<3;i++)for(int j=0;j<3;j++)r[i][j]=z[i][j];
  int along=(k==0||k==3)?2:0;
  for(int i=0;i<3;i++)x[i]+=r[i][along]*lens[k];
 }
 return x;
}

static std::array<double,21> pack(const Observation& o,const Params&p){
 std::array<double,21> v{};
 for(int i=0;i<6;i++){v[i]=o.q[i];v[6+i]=p[i];v[12+i]=LINK[i];}
 v[13]+=p[6]; v[14]+=p[7]; v[17]+=p[8];
 for(int k=0;k<3;k++)v[18+k]=o.measured[k];
 return v;
}

class PacevalEngine {
 std::vector<PACEVAL_HANDLE> owned_;
 std::array<PACEVAL_HANDLE,3> residual_{};
 std::array<PACEVAL_HANDLE,3> position_{};
 PACEVAL_HANDLE tinc_=nullptr;
 PACEVAL_HANDLE make(const char* expression,bool tinc=false){
  auto h=paceval_CreateComputation(expression,robot_formula::nvars,robot_formula::variables,tinc,nullptr);
  require(h!=nullptr,std::string("paceval_CreateComputation returned null for ")+expression);
  if(paceval_GetIsError(h)){
   long pos=0;char desc[PACEVAL_MAXERR+1]{};
   int code=paceval_GetErrorInformation(h,desc,&pos);
   std::string msg="paceval formula analysis error="+std::to_string(code)+" pos="+std::to_string(pos)+" "+desc;
   paceval_DeleteComputation(h);throw std::runtime_error(msg);
  }
  owned_.push_back(h);return h;
 }
public:
 PacevalEngine(){
  require(paceval_InitializeLibrary(nullptr),"paceval_InitializeLibrary failed");
  for(int k=0;k<3;k++)position_[k]=make(robot_formula::position[k]);
  for(int k=0;k<3;k++)residual_[k]=make(robot_formula::residual[k]);
  // A smooth kinematic subexpression allows a separate TINC check. This is
  // a pointwise observation, not a global guarantee about robotic accuracy.
  tinc_=make("l2*cos(q2+o2)",true);
 }
 PacevalEngine(const PacevalEngine&)=delete;
 PacevalEngine& operator=(const PacevalEngine&)=delete;
 ~PacevalEngine(){for(auto h:owned_)paceval_DeleteComputation(h);paceval_FreeLibrary();}
 // Input rows [pose][21 parameters]; multi-graph outputs [graph][pose].
 void evaluate(const Observations&obs,const Params&p,std::vector<V3>&out,
               bool residual=true,std::size_t batch=128){
  require(batch>=1&&batch<=4096,"Batch must be between 1 and 4096");
  out.resize(obs.size());
  auto handles=(residual?residual_:position_);
  for(std::size_t from=0;from<obs.size();from+=batch){
   auto n=std::min(batch,obs.size()-from);
   std::vector<double> vars(21*n), results(3*n,0.0);
   std::vector<int> errors(3*n,-1);
   for(std::size_t i=0;i<n;i++){
    auto packed=pack(obs[from+i],p);
    std::copy(packed.begin(),packed.end(),vars.begin()+21*i);
   }
   bool failed=paceval_dGetMultipleComputationsResultsExt(handles.data(),3,
      vars.data(),static_cast<unsigned long>(n),results.data(),nullptr,nullptr,errors.data());
   require(!failed,"paceval multi-graph batch returned an error");
   for(std::size_t i=0;i<n;i++)for(int k=0;k<3;k++){
    auto v=results[k*n+i];
    require(errors[k*n+i]==PACEVAL_ERR_NO_ERROR&&std::isfinite(v),
            "paceval invalid residual component");
    out[from+i][k]=v;
   }
  }
 }
 V3 tinc(const Observation&o,const Params&p){
  auto a=pack(o,p);double lo=0,hi=0;
  double z=paceval_dGetComputationResult(tinc_,a.data(),&lo,&hi);
  require(!paceval_GetIsError(tinc_)&&std::isfinite(z)&&std::isfinite(lo)&&std::isfinite(hi)&&lo<=hi,
    "TINC calculation or interval invalid");
  return {z,lo,hi};
 }
};

static Observations make_dataset(const std::string&split,int n,bool degenerate=false){
 std::mt19937_64 rng(20261112016ULL+(split=="holdout"?10:split=="degenerate"?20:0));
 std::uniform_real_distribution<double> unif(-1.35,1.35);
 Observations out;
 for(int i=0;i<n;i++){
  Observation o;o.split=split;o.id=i;
  for(int j=0;j<6;j++)o.q[j]=degenerate?((j%2)?-.27:.36):unif(rng);
  auto f=native_fk(o.q,TRUE_P);
  for(int k=0;k<3;k++)o.measured[k]=f[k]+(degenerate?0.0:0.000025*std::sin((i+1)*7.3+k*4.7));
  out.push_back(o);
 }
 return out;
}
// Strict CSV input for real or externally generated measurements. The input
// must identify training/holdout rows explicitly; we do not allow the caller
// to move holdout measurements into the calibration step accidentally.
static Observations load_dataset(const std::filesystem::path&path,const std::string&expected){
 std::ifstream f(path);require(bool(f),"Cannot open measurement CSV: "+path.string());
 std::string line;require(bool(std::getline(f,line)),"Empty CSV input");
 require(line=="split,id,q1,q2,q3,q4,q5,q6,mx_m,my_m,mz_m", "Unexpected measurement CSV header");
 Observations data;int previous=-1;
 while(std::getline(f,line)){
  if(line.empty())continue;
  std::stringstream row(line);std::string cell;std::vector<std::string> v;
  while(std::getline(row,cell,','))v.push_back(cell);
  require(v.size()==11,"Invalid number of CSV columns");
  require(v[0]==expected,"Training/holdout split mismatch");
  Observation o;o.split=v[0];
  auto integer=[](const std::string&t){std::size_t pos=0;int z=std::stoi(t,&pos);require(pos==t.size(),"Malformed identifier");return z;};
  auto decimal=[](const std::string&t){std::size_t pos=0;double z=std::stod(t,&pos);require(pos==t.size()&&std::isfinite(z),"Nonfinite or malformed CSV value");return z;};
  o.id=integer(v[1]);require(o.id>previous,"IDs must increase strictly");previous=o.id;
  for(int i=0;i<6;i++){o.q[i]=decimal(v[i+2]);require(std::abs(o.q[i])<=PI,"Joint angle outside validated range [-pi,pi]");}
  for(int i=0;i<3;i++){o.measured[i]=decimal(v[8+i]);require(std::abs(o.measured[i])<5.0,"Measured coordinate outside demonstration range");}
  data.push_back(o);require(data.size()<=5000,"Too many measurements for the research demo");
 }
 require(data.size()>=12,"At least 12 observations required per split");return data;
}
static double rmse(const std::vector<V3>&r){double v=0;for(auto a:r)for(double x:a)v+=x*x;return std::sqrt(v/(3.0*r.size()));}
static double norm2(const std::vector<V3>&r){double v=0;for(auto a:r)for(double x:a)v+=x*x;return v;}
static bool solve_linear(double a[NP][NP],double rhs[NP],double out[NP]){
 // Partial pivoting; LM adds a positive diagonal. Singular datasets are
 // rejected by the separate observability check, not masked with an inverse.
 for(int k=0;k<NP;k++){
  int piv=k;for(int i=k+1;i<NP;i++)if(std::abs(a[i][k])>std::abs(a[piv][k]))piv=i;
  if(std::abs(a[piv][k])<1e-20)return false;
  for(int j=0;j<NP;j++)std::swap(a[k][j],a[piv][j]);
  std::swap(rhs[k],rhs[piv]);
  for(int i=k+1;i<NP;i++){
   double f=a[i][k]/a[k][k];
   for(int j=k;j<NP;j++)a[i][j]-=f*a[k][j];
   rhs[i]-=f*rhs[k];
  }
 }
 for(int i=NP-1;i>=0;i--){double s=rhs[i];for(int j=i+1;j<NP;j++)s-=a[i][j]*out[j];out[i]=s/a[i][i];}
 return true;
}
static std::array<double,NP> eigenvalues_symmetric(double x[NP][NP]){
 // Symmetric Jacobi diagonalization for an *observability diagnostic*, not
 // part of the paceval mathematical evaluation or the LM equation solver.
 for(int it=0;it<NP*NP*32;it++){
  int p=0,q=1;double m=0;
  for(int i=0;i<NP;i++)for(int j=i+1;j<NP;j++)
   if(std::abs(x[i][j])>m){p=i;q=j;m=std::abs(x[i][j]);}
  if(m<1e-12)break;
  double angle=.5*std::atan2(2*x[p][q],x[q][q]-x[p][p]);
  // Convention: rotation [[c,s],[-s,c]] with this angle.
  double c=std::cos(angle),s=std::sin(angle);
  double app=x[p][p],aqq=x[q][q],apq=x[p][q];
  x[p][p]=c*c*app-2*c*s*apq+s*s*aqq;
  x[q][q]=s*s*app+2*c*s*apq+c*c*aqq;
  x[p][q]=x[q][p]=0;
  for(int k=0;k<NP;k++)if(k!=p&&k!=q){double u=x[k][p],v=x[k][q];
    x[k][p]=x[p][k]=c*u-s*v; x[k][q]=x[q][k]=s*u+c*v;}
 }
 std::array<double,NP> sv{};for(int i=0;i<NP;i++)sv[i]=std::sqrt(std::max(0.0,x[i][i]));
 std::sort(sv.begin(),sv.end(),std::greater<double>());return sv;
}
static void jacobian(PacevalEngine&engine,const Observations&obs,const Params&p,
         std::vector<V3> derivative[NP],std::size_t batch){
 for(int j=0;j<NP;j++){
  Params plus=p,minus=p;double h=(j<6?1e-5:2e-5);
  plus[j]+=h;minus[j]-=h;
  std::vector<V3> a,b;
  engine.evaluate(obs,plus,a,true,batch);engine.evaluate(obs,minus,b,true,batch);
  derivative[j].resize(obs.size());
  for(std::size_t i=0;i<obs.size();i++)for(int k=0;k<3;k++)
   derivative[j][i][k]=(a[i][k]-b[i][k])/(2*h);
 }
}
static std::array<double,NP> singular_values(std::vector<V3> J[NP]){
 double a[NP][NP]{};
 for(int j=0;j<NP;j++)for(int k=0;k<NP;k++)
  for(std::size_t i=0;i<J[0].size();i++)for(int d=0;d<3;d++)a[j][k]+=J[j][i][d]*J[k][i][d];
 return eigenvalues_symmetric(a);
}
static std::vector<double> calibrate(PacevalEngine&engine,const Observations&train,
           Params&estimated,std::size_t batch){
 std::vector<V3> residual; engine.evaluate(train,estimated,residual,true,batch);
 std::vector<double> progress={rmse(residual)};
 double lambda=0.0003;
 for(int iter=0;iter<24;iter++){
  std::vector<V3> j[NP];jacobian(engine,train,estimated,j,batch);
  double normal[NP][NP]{},g[NP]{};
  for(int k=0;k<NP;k++)for(std::size_t n=0;n<train.size();n++)for(int d=0;d<3;d++)g[k]+=j[k][n][d]*residual[n][d];
  for(int a=0;a<NP;a++)for(int b=0;b<NP;b++)for(std::size_t n=0;n<train.size();n++)
   for(int d=0;d<3;d++)normal[a][b]+=j[a][n][d]*j[b][n][d];
  bool accepted=false;double original=norm2(residual);
  for(int trial=0;trial<12;trial++){
   double a[NP][NP],rhs[NP],dx[NP]{};
   for(int k=0;k<NP;k++){rhs[k]=-g[k];for(int l=0;l<NP;l++)a[k][l]=normal[k][l];
    a[k][k]+=lambda*std::max(1.,normal[k][k]);}
   require(solve_linear(a,rhs,dx),"LM normal equation singular");
   Params proposed=estimated;
   for(int k=0;k<NP;k++)proposed[k]=std::clamp(proposed[k]+dx[k],k<6?-.085:-.06,k<6?.085:.06);
   std::vector<V3> next;engine.evaluate(train,proposed,next,true,batch);
   if(norm2(next)<original-1e-23){estimated=proposed;residual.swap(next);lambda=std::max(1e-10,lambda*.35);accepted=true;break;}
   lambda=std::min(1e10,lambda*6.0);
  }
  if(!accepted)break;
  progress.push_back(rmse(residual));
  if(progress.size()>2&&std::abs(progress[progress.size()-2]-progress.back())<1e-11)break;
 }
 return progress;
}
static void dump_dataset(const std::filesystem::path&path,const Observations&data){
 std::ofstream f(path);require(bool(f),"cannot write "+path.string());f<<std::setprecision(17);
 f<<"split,id,q1,q2,q3,q4,q5,q6,mx_m,my_m,mz_m\n";
 for(const auto&o:data){f<<o.split<<','<<o.id;for(double a:o.q)f<<','<<a;for(double a:o.measured)f<<','<<a;f<<'\n';}
}
static void dump_predictions(const std::filesystem::path&path,const Observations&obs,
   const std::vector<V3>&base,const std::vector<V3>&fit){
 std::ofstream f(path);require(bool(f),"write predictions failed");f<<std::setprecision(17);
 f<<"split,id,measured_x,measured_y,measured_z,nominal_rx,nominal_ry,nominal_rz,fitted_rx,fitted_ry,fitted_rz,nominal_error_mm,fitted_error_mm\n";
 for(std::size_t i=0;i<obs.size();i++){
  f<<obs[i].split<<','<<obs[i].id;for(double a:obs[i].measured)f<<','<<a;
  for(double a:base[i])f<<','<<a;
  for(double a:fit[i])f<<','<<a;
  auto mag=[](V3 v){return 1000*std::sqrt(v[0]*v[0]+v[1]*v[1]+v[2]*v[2]);};
  f<<','<<mag(base[i])<<','<<mag(fit[i])<<'\n';
 }
}
static void dump_tinc(const std::filesystem::path&path,PacevalEngine&eng,const Observations&obs,
                      const Params&p){
 std::ofstream f(path);require(bool(f),"write TINC failed");f<<std::setprecision(17);
 f<<"id,q2_rad,o2_rad,l2_m,point_m,lower_m,upper_m\n";
 for(int i=0;i<24;i++){
  auto x=eng.tinc(obs[i],p);double l2=LINK[1]+p[6];
  f<<i<<','<<obs[i].q[1]<<','<<p[1]<<','<<l2<<','<<x[0]<<','<<x[1]<<','<<x[2]<<'\n';
 }
}
static void self_test(PacevalEngine&eng){
 Params p{};auto obs=make_dataset("test",20);
 std::vector<V3> a,b;eng.evaluate(obs,p,a,true,17);eng.evaluate(obs,p,b,false,17);
 double maxerr=0;
 for(std::size_t i=0;i<obs.size();i++){
  auto native=native_fk(obs[i].q,p);
  for(int k=0;k<3;k++){
   maxerr=std::max({maxerr,std::abs(b[i][k]-native[k]),
                           std::abs(a[i][k]-(obs[i].measured[k]-native[k]))});
  }
 }
 require(maxerr<2e-11,"independent kinematics disagrees");
 auto test1=obs;test1[0].q[0]=std::numeric_limits<double>::quiet_NaN();
 auto validate=[](const Observations&d){for(auto&o:d){for(auto a:o.q)if(!std::isfinite(a)||std::abs(a)>PI) return false;for(double m:o.measured)if(!std::isfinite(m))return false;}return true;};
 require(!validate(test1)&&validate(obs),"input validity test failed");
 std::cout<<"self-test PASS, independent FK maximum absolute discrepancy: "<<maxerr<<" m\n";
}
int main(int argc,char**argv){
 try{
  std::filesystem::path out="examples";std::size_t batch=128;
  bool onlytest=false;
  std::string train_csv,holdout_csv;
  for(int i=1;i<argc;i++){
   std::string a=argv[i];
   if(a=="--out"&&i+1<argc)out=argv[++i];
   else if(a=="--batch"&&i+1<argc)batch=std::stoul(argv[++i]);
   else if(a=="--self-test")onlytest=true;
   else if(a=="--train-csv"&&i+1<argc)train_csv=argv[++i];
   else if(a=="--holdout-csv"&&i+1<argc)holdout_csv=argv[++i];
   else throw std::runtime_error("Usage: robot_calibration [--out DIR] [--batch 1..4096] [--self-test]");
  }
  PacevalEngine eng;
  if(onlytest){self_test(eng);return 0;}
  require(train_csv.empty()==holdout_csv.empty(),"Provide both --train-csv and --holdout-csv");
  const bool external=!train_csv.empty();
  auto training=external?load_dataset(train_csv,"training"):make_dataset("training",120);
  auto holdout=external?load_dataset(holdout_csv,"holdout"):make_dataset("holdout",48);
  auto degenerate=make_dataset("degenerate",24,true);
  Params estimate{},nominal{};
  std::vector<V3> sens[NP];jacobian(eng,training,nominal,sens,batch);
  auto sv=singular_values(sens);
  jacobian(eng,degenerate,nominal,sens,batch);auto degsv=singular_values(sens);
  require(sv.back()>0.05,"training calibration insufficiently observable");
  require(degsv.back()<1e-3,"degenerate pose set unexpectedly observable");
  auto history=calibrate(eng,training,estimate,batch);
  std::vector<V3> nominal_tr,fit_tr,nominal_val,fit_val;
  eng.evaluate(training,nominal,nominal_tr,true,batch);
  eng.evaluate(training,estimate,fit_tr,true,batch);
  eng.evaluate(holdout,nominal,nominal_val,true,batch);
  eng.evaluate(holdout,estimate,fit_val,true,batch);
  double pre=rmse(nominal_val), post=rmse(fit_val);
  if(!external)require(post<pre*.20,"Synthetic holdout calibration did not improve enough");
  std::filesystem::create_directories(out);
  dump_dataset(out/"training_observations.csv",training);
  dump_dataset(out/"holdout_observations.csv",holdout);
  dump_dataset(out/"degenerate_observations.csv",degenerate);
  dump_predictions(out/"train_predictions.csv",training,nominal_tr,fit_tr);
  dump_predictions(out/"holdout_predictions.csv",holdout,nominal_val,fit_val);
  dump_tinc(out/"tinc_samples.csv",eng,training,estimate);
  {
   std::ofstream f(out/"calibration_trace.csv");f<<"iteration,training_rmse_m\n"<<std::setprecision(17);
   for(std::size_t i=0;i<history.size();i++)f<<i<<','<<history[i]<<'\n';
  }
  {
   std::ofstream f(out/"parameters.csv");f<<"parameter,unit,nominal,true,fitted\n"<<std::setprecision(17);
   for(int i=0;i<NP;i++){
   f<<(i<6?"joint_offset_":"link_delta_")<<(i<6?i+1:(i==6?2:i==7?3:6))
      <<','<<(i<6?"rad":"m")<<",0,";
   if(!external)f<<TRUE_P[i];
   f<<','<<estimate[i]<<'\n';
   }
  }
  {
   std::ofstream f(out/"observability.csv");f<<"index,training_singular_value,degenerate_singular_value\n"<<std::setprecision(17);
   for(int i=0;i<NP;i++)f<<i+1<<','<<sv[i]<<','<<degsv[i]<<'\n';
  }
  {
   std::ofstream f(out/"summary.json");f<<std::setprecision(17);
   f<<"{\n  \"train_poses\":"<<training.size()<<",\n  \"holdout_poses\":"<<holdout.size()<<",\n  \"degenerate_poses\":24,\n";
   f<<"  \"external_measurements\":"<<(external?"true":"false")<<",\n";
   f<<"  \"paceval_regular_graphs\":6,\n  \"paceval_tinc_graphs\":1,\n";
   f<<"  \"holdout_rmse_before_m\":"<<pre<<",\n  \"holdout_rmse_after_m\":"<<post<<",\n";
   f<<"  \"train_singular_min\":"<<sv.back()<<",\n  \"degenerate_singular_min\":"<<degsv.back()<<",\n";
   f<<"  \"lm_accepted_steps\":"<<history.size()-1<<",\n";
   f<<"  \"model_definition\":\"6R local-axis ZYYXYZ; position-only calibration; fixed base and tool frames\"\n}\n";
  }
  std::cout<<std::setprecision(10)<<"paceval 6R calibration PASSED: training 120, holdout 48; "
     <<"holdout RMSE "<<pre*1000<<" -> "<<post*1000<<" mm; full rank minimum "<<sv.back()
     <<"; degenerate minimum "<<degsv.back()<<"; iterations "<<history.size()-1<<'\n';
  return 0;
 }catch(const std::exception&e){std::cerr<<"ERROR: "<<e.what()<<'\n';return 1;}
}
