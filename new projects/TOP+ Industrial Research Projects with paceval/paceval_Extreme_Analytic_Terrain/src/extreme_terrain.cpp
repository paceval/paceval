// Reproducible analytic 2.5D terrain generation via the original paceval SDK.
// Three distinct scenes. Each explicitly saved formula is >=250,000 characters.
// The host generates model coefficients, checks numeric output and exports samples;
// paceval evaluates original mathematical expression graphs, not a mock engine.
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
namespace fs = std::filesystem;
struct Term { double amplitude, cx, cy, sx, sy; };
static void require(bool p,const std::string& s){if(!p)throw std::runtime_error(s);}
struct RNG {uint64_t state; uint64_t next(){state+=0x9e3779b97f4a7c15ULL;uint64_t z=state;z=(z^(z>>30))*0xbf58476d1ce4e5b9ULL;z=(z^(z>>27))*0x94d049bb133111ebULL;return z^(z>>31);}double uniform(){return double(next()>>11)*(1.0/9007199254740992.0);}};
static std::string dec(double a){std::ostringstream o;o<<std::setprecision(17)<<a;return o.str();}
static std::string background(int scene){
 if(scene==0) return "(0.72*exp(-((x+0.46)^2/0.082+(y-0.19)^2/0.14))+0.57*exp(-((x-0.48)^2/0.12+(y-0.53)^2/0.085))-0.85*exp(-((x-0.27)^2/0.085+(y+0.31)^2/0.11))+0.10*sin(7*x)*cos(5*y)-0.055*(x+y))";
 if(scene==1) return "(0.95*exp(-((x+0.07)^2/0.17+(y-0.06)^2/0.19))-0.62*exp(-((x+0.07)^2/0.028+(y-0.06)^2/0.03))+0.16*sin(12*x+4*y)*exp(-((x+0.04)^2+(y-0.09)^2)/0.75)-0.13*exp(-((x-0.62)^2/0.08+(y+0.44)^2/0.1)))";
 return "(0.35*sin(2.8*x+1.4*y)+0.22*cos(3.8*y-0.6*x)-0.65*exp(-((x+0.2*y+0.13)^2/0.028))+0.18*exp(-((x-0.62)^2/0.048+(y+0.45)^2/0.095))+0.11*sin(11*x+3*y)*cos(5*y))";
}
static double evalbg(int s,double x,double y){
 if(s==0)return .72*std::exp(-(std::pow(x+.46,2)/.082+std::pow(y-.19,2)/.14))+.57*std::exp(-(std::pow(x-.48,2)/.12+std::pow(y-.53,2)/.085))-.85*std::exp(-(std::pow(x-.27,2)/.085+std::pow(y+.31,2)/.11))+.10*std::sin(7*x)*std::cos(5*y)-.055*(x+y);
 if(s==1)return .95*std::exp(-(std::pow(x+.07,2)/.17+std::pow(y-.06,2)/.19))-.62*std::exp(-(std::pow(x+.07,2)/.028+std::pow(y-.06,2)/.03))+.16*std::sin(12*x+4*y)*std::exp(-(std::pow(x+.04,2)+std::pow(y-.09,2))/.75)-.13*std::exp(-(std::pow(x-.62,2)/.08+std::pow(y+.44,2)/.1));
 return .35*std::sin(2.8*x+1.4*y)+.22*std::cos(3.8*y-.6*x)-.65*std::exp(-(std::pow(x+.2*y+.13,2)/.028))+.18*std::exp(-(std::pow(x-.62,2)/.048+std::pow(y+.45,2)/.095))+.11*std::sin(11*x+3*y)*std::cos(5*y);
}
static std::vector<Term> terms(int scene,int n){ RNG r{0xACE20261112ULL+uint64_t(scene)*10991ULL};std::vector<Term> v;v.reserve(n);
 for(int i=0;i<n;++i){double a=(r.uniform()*2-1)*.065/std::sqrt(double(n)/2048.),cx=-1.15+2.3*r.uniform(),cy=-1.15+2.3*r.uniform(),sx=.006+.09*r.uniform(),sy=.006+.09*r.uniform();v.push_back({a,cx,cy,sx,sy});}return v;}
static std::string one(const Term& t){return "("+dec(t.amplitude)+"*exp(-((x-("+dec(t.cx)+"))^2/("+dec(t.sx)+")+(y-("+dec(t.cy)+"))^2/("+dec(t.sy)+"))))";}
static double native(const std::vector<Term>& t,int scene,double x,double y){double v=evalbg(scene,x,y);for(const auto& a:t)v+=a.amplitude*std::exp(-(std::pow(x-a.cx,2)/a.sx+std::pow(y-a.cy,2)/a.sy));return v;}
class Engine {std::vector<PACEVAL_HANDLE> handles;public:
 Engine(){require(paceval_InitializeLibrary(nullptr),"paceval_InitializeLibrary failed");}
 ~Engine(){for(auto h:handles)paceval_DeleteComputation(h);paceval_FreeLibrary();}
 PACEVAL_HANDLE create(const std::string& f){auto h=paceval_CreateComputation(f.c_str(),2,"x y",false,nullptr);require(h!=nullptr && !paceval_GetIsError(h),"paceval_CreateComputation failed for expression length "+std::to_string(f.size()));handles.push_back(h);return h;}
 double scalar(PACEVAL_HANDLE h,double x,double y){double a[]={x,y};auto r=paceval_dGetComputationResult(h,a,nullptr,nullptr);require(!paceval_GetIsError(h)&&std::isfinite(r),"paceval scalar failed");return r;}
 std::vector<double> batch(const std::vector<PACEVAL_HANDLE>& hs,const std::vector<double>& coords,int count){std::vector<double> output(size_t(hs.size())*count);std::vector<int> codes(output.size(),-1);auto input=coords;auto handlesCopy=hs;
 // API results are graph-major, then coordinate-major; each result code is checked.
 bool err=paceval_dGetMultipleComputationsResultsExt(handlesCopy.data(),(unsigned long)hs.size(),input.data(),(unsigned long)count,output.data(),nullptr,nullptr,codes.data());require(!err,"multi-graph batch API returned error");for(size_t j=0;j<output.size();++j)require(codes[j]==0&&std::isfinite(output[j]),"invalid batch result");return output;}
};
int main(int argc,char**argv){try{
 fs::path dir=".";bool quick=false;int resolution=40;for(int a=1;a<argc;++a){std::string v=argv[a];if(v=="--out"&&a+1<argc)dir=argv[++a];else if(v=="--quick")quick=true;else if(v=="--grid"&&a+1<argc)resolution=std::stoi(argv[++a]);else throw std::runtime_error("Usage: extreme_terrain --out DIRECTORY [--grid 40] [--quick]");}
 require(resolution>=8 && resolution<=256,"grid out of bounds");fs::create_directories(dir/"examples");fs::create_directories(dir/"expressions");fs::create_directories(dir/"results");
 Engine engine;auto csv=std::ofstream(dir/"results"/"execution_summary.csv");csv<<"scene,terms,formula_characters,graph_count,grid_points,water_level,native_check_count,native_max_abs_difference,monolithic_samples,monolithic_max_abs_difference\n";
 std::array<std::string,3> names={"alpine_lake","volcanic_caldera","canyon_ridges"};double globalWorst=0;int totalGraphs=0;
 for(int s=0;s<(quick?1:3);++s){int n=(s==0?2048:s==1?3072:4096);auto model=terms(s,n);std::string full=background(s);std::vector<std::string> chunks;const int CHUNK=256;for(int j=0;j<n;j+=CHUNK){std::string part="0";for(int k=j;k<std::min(n,j+CHUNK);++k)part+="+"+one(model[k]);chunks.push_back(part);full+="+("+part+")";}
 require(full.size()>=250000,"formula shorter than required 250000 characters");std::ofstream formula(dir/"expressions"/(names[s]+"_full_formula.txt"),std::ios::binary);formula<<full<<'\n';formula.close();
 // Both the complete monolithic expression and decomposed component graphs are real paceval handles.
 auto monolithic=engine.create(full);std::vector<PACEVAL_HANDLE> hs;hs.push_back(engine.create(background(s)));for(auto& c:chunks)hs.push_back(engine.create(c));totalGraphs+=(int)hs.size()+1;
 double monoWorst=0;for(int k=0;k<5;++k){double x=-.8+k*.36,y=-.65+k*.22;double calc=engine.scalar(monolithic,x,y);double ref=native(model,s,x,y);monoWorst=std::max(monoWorst,std::abs(ref-calc));require(std::abs(ref-calc)<2e-9,"monolithic formula correctness failed");}
 int grid=quick?std::min(resolution,12):resolution;std::ofstream out(dir/"examples"/(names[s]+"_height_grid.csv"));out<<std::setprecision(17)<<"i,j,x,y,height,water_level\n";int checked=0;double worst=0;const int batchSize=128;std::vector<double> all(size_t(grid)*grid);
 for(int start=0;start<grid*grid;start+=batchSize){int count=std::min(batchSize,grid*grid-start);std::vector<double> coord(size_t(count)*2);for(int k=0;k<count;++k){int ind=start+k;coord[size_t(k)*2]=-1.+2.*(ind%grid)/(grid-1);coord[size_t(k)*2+1]=-1.+2.*(ind/grid)/(grid-1);}auto results=engine.batch(hs,coord,count);
 for(int k=0;k<count;++k){double v=0;for(size_t h=0;h<hs.size();++h)v+=results[h*count+k];int ind=start+k;int ix=ind%grid,iy=ind/grid;double x=coord[2*k],y=coord[2*k+1];require(std::isfinite(v),"nonfinite height");all[ind]=v;out<<ix<<','<<iy<<','<<x<<','<<y<<','<<v<<','<<(s==2?-0.32:s==1?0.08:-0.12)<<'\n';if((ind%17)==0){double ref=native(model,s,x,y);worst=std::max(worst,std::abs(v-ref));require(std::abs(v-ref)<3e-8,"native validation failed");++checked;}}}
 globalWorst=std::max(globalWorst,worst);csv<<names[s]<<','<<n<<','<<full.size()<<','<<hs.size()+1<<','<<grid*grid<<','<<(s==2?-.32:s==1?.08:-.12)<<','<<checked<<','<<std::setprecision(17)<<worst<<','<<5<<','<<monoWorst<<'\n';std::cout<<"PASS "<<names[s]<<": "<<full.size()<<" expression chars, "<<grid*grid<<" paceval samples, "<<hs.size()+1<<" graphs\n";}
 std::cout<<"PASS original paceval SDK, total graphs="<<totalGraphs<<" max difference="<<globalWorst<<"\n";return 0;
 }catch(const std::exception& e){std::cerr<<"FAIL "<<e.what()<<'\n';return 1;}}
