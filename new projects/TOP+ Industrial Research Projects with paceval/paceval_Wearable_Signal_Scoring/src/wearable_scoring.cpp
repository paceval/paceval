// WP_036: Reproducible, non-clinical wearable IMU/PPG scoring with the ORIGINAL paceval C/C++ API.
// The host synthesizes and preprocesses 8-second raw traces; paceval evaluates mathematical
// score expressions via persistent handles, single-value queries and documented batch calls.
// The results are demonstration scores; they do NOT diagnose disease or validate a medical device.
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
#include <numeric>
#include <sstream>
#include <stdexcept>
#include <string>
#include <vector>
namespace fs=std::filesystem;
namespace {
constexpr double PI=3.14159265358979323846264338327950288;
constexpr int SAMPLES=200, FS=25; // 8 s at 25 Hz; synthetic, not a particular device's sampling rate
using Features=std::array<double,6>; // a,c,h,m,p,q, all explicitly normalized dimensionless values
constexpr char VARIABLES[]="a c h m p q";
void require(bool b,const std::string& why){if(!b)throw std::runtime_error(why);}
std::string lit(double v){std::ostringstream o;o<<std::setprecision(17)<<v;return o.str();}
struct Rng {uint64_t state=20261112036ULL;uint64_t next(){state+=0x9e3779b97f4a7c15ULL;uint64_t z=state;z=(z^(z>>30))*0xbf58476d1ce4e5b9ULL;z=(z^(z>>27))*0x94d049bb133111ebULL;return z^(z>>31);}double uniform(){return double(next()>>11)*0x1.0p-53;}double signedNoise(){return 2*uniform()-1;}};
struct Rule {int id=0,family=0,version=1;double alpha=0,beta=0;std::string text;PACEVAL_HANDLE handle=nullptr;};
struct Signal {double t=0,ax=0,ay=0,az=0,ppg=0;};
struct Window {Features input{};double accRmsG=0,cadencePerMin=0,pulseProxyBpm=0,artifactProxy=0,modulation=0,periodicity=0;std::vector<Signal> raw;};
// Synthetic wrist motion and photoplethysmography: intentionally simplified, no physiology model.
Window makeWindow(int index){
 Rng rng; rng.state=0xBDAD123456ULL+uint64_t(index+1)*0x9e3779b97f4a7c15ULL;
 double motion=0.08+0.8*(0.5+0.5*std::sin(index*.017));
 double stepsHz=0.9+1.1*(0.5+0.5*std::sin(index*.0067));
 double pulseHz=0.95+0.95*(0.5+0.5*std::cos(index*.011));
 double optic=0.075+0.035*std::cos(index*.004);
 Window out;out.raw.reserve(SAMPLES);
 for(int j=0;j<SAMPLES;++j){double t=j/double(FS), noise=rng.signedNoise();
  Signal s;s.t=t;s.ax=motion*(.58*std::sin(2*PI*stepsHz*t)+.10*rng.signedNoise());
  s.ay=motion*(.33*std::cos(2*PI*stepsHz*t+.7)+.09*rng.signedNoise());
  s.az=1+motion*(.28*std::sin(2*PI*stepsHz*t+1.2)+.06*rng.signedNoise());
  s.ppg=1.25+optic*(std::sin(2*PI*pulseHz*t)+.18*std::sin(4*PI*pulseHz*t+.2))
          +motion*.045*std::sin(2*PI*stepsHz*t+.4)+.009*noise;
  out.raw.push_back(s);
 }
 double aSum=0, pSum=0;int crossings=0;for(int j=0;j<SAMPLES;++j){const auto&s=out.raw[j];aSum+=s.ax*s.ax+s.ay*s.ay+(s.az-1)*(s.az-1);pSum+=s.ppg;
  if(j>0&&out.raw[j-1].ax<0&&s.ax>=0)++crossings;}
 out.accRmsG=std::sqrt(aSum/SAMPLES);out.cadencePerMin=60.*crossings/(SAMPLES/double(FS));
 double mean=pSum/SAMPLES, var=0;std::vector<double> centered(SAMPLES);
 for(int j=0;j<SAMPLES;++j){centered[j]=out.raw[j].ppg-mean;var+=centered[j]*centered[j];}var/=SAMPLES;
 double best=-1;int bestLag=25;
 for(int lag=12;lag<=38;++lag){double num=0,xx=0,yy=0;for(int j=lag;j<SAMPLES;++j){double x=centered[j],y=centered[j-lag];num+=x*y;xx+=x*x;yy+=y*y;}
  double corr=num/std::sqrt(std::max(1e-24,xx*yy));if(corr>best){best=corr;bestLag=lag;}}
 out.periodicity=std::clamp(best,0.,1.);out.pulseProxyBpm=60.*FS/bestLag;
 out.modulation=std::sqrt(var)/mean;out.artifactProxy=out.accRmsG*(1.-out.periodicity);
 // Strict normalization: these six feature values are never physiological diagnoses.
 out.input={out.accRmsG/0.65, out.cadencePerMin/145., out.pulseProxyBpm/140.,
            out.artifactProxy/0.65, out.modulation/0.12, out.periodicity};
 for(double v:out.input)require(std::isfinite(v)&&v>=0&&v<=3.,"synthetic feature out of contract");
 return out;
}
double sigmoid(double z){return 1/(1+std::exp(-z));}
// Independent C++ reference implementation; not derived by evaluating a paceval expression.
double native(const Rule& r,Features v){auto [a,c,h,m,p,q]=v;double z=0;
 switch(r.family){
 case 0:z=r.alpha*a+r.beta*c+0.14*h-0.37;break;
 case 1:z=r.alpha*q-r.beta*m+0.27*p-0.30;break;
 case 2:z=r.alpha*a*c+r.beta*p*q-0.28*m-0.37;break;
 case 3:z=r.alpha*std::sin(a)+r.beta*std::cos(h)+0.32*q-0.42*m-0.43;break;
 default:z=r.alpha*std::log(1+a*a)+r.beta*std::exp(-m*m)+0.19*p*q-0.66;break;
 }return sigmoid(z);
}
std::string expression(const Rule&r){const std::string A=lit(r.alpha),B=lit(r.beta);std::string z;
 switch(r.family){
 case 0:z="("+A+"*a+"+B+"*c+0.14*h-0.37)";break;
 case 1:z="("+A+"*q-"+B+"*m+0.27*p-0.30)";break;
 case 2:z="("+A+"*a*c+"+B+"*p*q-0.28*m-0.37)";break;
 case 3:z="("+A+"*sin(a)+"+B+"*cos(h)+0.32*q-0.42*m-0.43)";break;
 default:z="("+A+"*ln(1+a^2)+"+B+"*exp(-m^2)+0.19*p*q-0.66)";break;
 }return "1/(1+exp(-"+z+"))";
}
class Paceval {
 std::vector<PACEVAL_HANDLE> objects;
public:
 Paceval(){require(paceval_InitializeLibrary(nullptr),"paceval runtime initialization failed");}
 ~Paceval(){for(auto h:objects)if(h)paceval_DeleteComputation(h);paceval_FreeLibrary();}
 PACEVAL_HANDLE add(const std::string&s){auto h=paceval_CreateComputation(s.c_str(),6,VARIABLES,false,nullptr);require(h&&!paceval_GetIsError(h),"paceval_CreateComputation failed: "+s);objects.push_back(h);return h;}
 double scalar(PACEVAL_HANDLE h,const Features&v){Features copy=v;double result=paceval_dGetComputationResult(h,copy.data(),nullptr,nullptr);require(!paceval_GetIsError(h)&&std::isfinite(result),"invalid scalar paceval output");return result;}
 std::vector<double> batch(PACEVAL_HANDLE h,const std::vector<Features>&vs){std::vector<double> packed;packed.reserve(vs.size()*6);for(const auto&v:vs)for(double x:v)packed.push_back(x);
  std::vector<double> out(vs.size());std::vector<int> errors(vs.size(),-1);bool failed=paceval_dGetComputationResultExt(h,packed.data(),static_cast<unsigned long>(vs.size()),out.data(),nullptr,nullptr,errors.data());
  require(!failed,"paceval batch call failed");for(size_t i=0;i<vs.size();++i)require(errors[i]==0&&std::isfinite(out[i]),"paceval batch result failure");return out;
 }
};
std::vector<Rule> getRules(){std::vector<Rule> result;for(int family=0;family<5;++family)for(int j=0;j<10;++j){Rule r;r.id=family*10+j+1;r.family=family;r.alpha=.36+.049*j+.031*family;r.beta=.22+.035*j;r.text=expression(r);result.push_back(r);}return result;}
void checkEqual(double y,double ref,double &worst){double diff=std::abs(y-ref);worst=std::max(worst,diff);require(diff<3e-11*(1+std::abs(ref)),"independent native C++ formula mismatch");}
void writeTrace(const fs::path &path,const Window&w){std::ofstream f(path);f<<"time_s,acc_x_g,acc_y_g,acc_z_g,ppg_normalized\n"<<std::setprecision(17);for(const auto&s:w.raw)f<<s.t<<','<<s.ax<<','<<s.ay<<','<<s.az<<','<<s.ppg<<'\n';}
void execute(const fs::path&out,int windowCount){fs::create_directories(out);Paceval engine;auto rules=getRules();
 for(auto&r:rules)r.handle=engine.add(r.text);
 Rule revision=rules[0];revision.id=51;revision.version=2;revision.alpha+=.15;revision.text=expression(revision);revision.handle=engine.add(revision.text);
 std::ofstream formulas(out/"formula_registry.csv");formulas<<"id,family,version,alpha,beta,expression\n"<<std::setprecision(17);for(const auto&r:rules)formulas<<r.id<<','<<r.family+1<<','<<r.version<<','<<r.alpha<<','<<r.beta<<",\""<<r.text<<"\"\n";
 formulas<<revision.id<<','<<revision.family+1<<",2,"<<revision.alpha<<','<<revision.beta<<",\""<<revision.text<<"\"\n";
 std::ofstream records(out/"wearable_feature_windows.csv");records<<"window_id,formula_id,acc_rms_g,cadence_proxy_per_min,pulse_proxy_bpm,motion_artifact_proxy,ppg_modulation,ppg_periodicity,a,c,h,m,p,q,score,screen_flag\n"<<std::setprecision(17);
 long long screen=0;double worst=0;for(int i=0;i<windowCount;++i){Window w=makeWindow(i);if(i<4)writeTrace(out/("synthetic_trace_"+std::to_string(i+1)+".csv"),w);
  const Rule&r=rules[i%50];double score=engine.scalar(r.handle,w.input);checkEqual(score,native(r,w.input),worst);int flag=score>=.65;screen+=flag;
  records<<i+1<<','<<r.id<<','<<w.accRmsG<<','<<w.cadencePerMin<<','<<w.pulseProxyBpm<<','<<w.artifactProxy<<','<<w.modulation<<','<<w.periodicity;
  for(double v:w.input){records<<','<<v;}records<<','<<score<<','<<flag<<'\n';}
 // For each persistent graph, batch-evaluate a separate deterministic subset of signal-derived windows.
 long long batchOutputs=0;for(int k=0;k<50;++k){std::vector<Features> v;for(int j=0;j<32;++j)v.push_back(makeWindow(20000+k*32+j).input);
  auto ys=engine.batch(rules[k].handle,v);for(int j=0;j<32;++j){checkEqual(ys[j],native(rules[k],v[j]),worst);++batchOutputs;}}
 std::ofstream surface(out/"signal_quality_surface.csv");surface<<"normalized_motion,periodicity,score\n"<<std::setprecision(17);
 for(int i=0;i<=60;++i)for(int j=0;j<=60;++j){Features v={0.15+1.5*i/60.,.72,.8,.05+1.2*i/60.,.55,.10+.9*j/60.};double y=engine.scalar(rules[10].handle,v);checkEqual(y,native(rules[10],v),worst);surface<<v[0]<<','<<v[5]<<','<<y<<'\n';}
 std::ofstream vfile(out/"formula_version_trace.csv");vfile<<"normalized_acc,score_v1,score_v2\n"<<std::setprecision(17);
 for(int j=0;j<=100;++j){Features v={j*1.8/100.,.6,.75,.15,.50,.75};double u=engine.scalar(rules[0].handle,v),v2=engine.scalar(revision.handle,v);checkEqual(u,native(rules[0],v),worst);checkEqual(v2,native(revision,v),worst);vfile<<v[0]<<','<<u<<','<<v2<<'\n';}
 int rejected=0;for(double invalid: {std::numeric_limits<double>::quiet_NaN(),-1.0,4.5}){Features x={.5,.5,.6,.1,.5,.5};x[0]=invalid;bool valid=true;for(double t:x)if(!std::isfinite(t)||t<0||t>3)valid=false;if(!valid)++rejected;}
 require(rejected==3,"input-validation tests failed");
 std::ofstream report(out/"execution_summary.txt");report<<std::setprecision(17)<<"project=WP036\nstatus=PASS\norigin=original_paceval_linux_sdk\nwindow_samples="<<SAMPLES<<"\nsample_rate_hz="<<FS<<"\nraw_samples="<<static_cast<long long>(windowCount)*SAMPLES<<"\nreusable_graphs=51\nformula_versions=2\nwindows="<<windowCount<<"\nscalar_evaluations="<<windowCount+3721+202<<"\nbatch_results="<<batchOutputs<<"\nnonclinical_screen_flags="<<screen<<"\ninvalid_inputs_rejected="<<rejected<<"\nmax_abs_native_audit="<<worst<<"\n";
 std::cout<<"PASS 51 graphs, "<<windowCount<<" IMU/PPG windows, "<<windowCount+3923<<" scalar scores, "<<batchOutputs<<" batch results, "<<screen<<" synthetic screen flags\n";
}
}
int main(int argc,char**argv){try{int windows=10000;fs::path out="examples";for(int i=1;i<argc;++i){std::string x=argv[i];if(x=="--windows"&&i+1<argc)windows=std::stoi(argv[++i]);else if(x=="--out"&&i+1<argc)out=argv[++i];else throw std::runtime_error("unrecognized parameter: "+x);}require(windows>=100&&windows<=100000,"window count must be within 100..100000");execute(out,windows);return 0;}catch(const std::exception&e){std::cerr<<"FAIL: "<<e.what()<<'\n';return 1;}}
