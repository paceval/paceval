// Copyright (c) 2026, demonstration host. The adjacent paceval_main.cpp/.h
// preserve the original upstream copyright and AGPL headers.
//
// Six explicitly specified smooth industrial response surfaces, not PDE/CFD/FEM
// solvers or experimentally validated predictive digital twins. The host owns
// all domain/units and mesh sampling; paceval evaluates the reusable graphs.
// Each output CSV includes BOTH direct paceval evaluations and independently
// evaluated native expressions, allowing numerical auditing of every pixel.
#include "paceval_main.h"
#include <algorithm>
#include <array>
#include <cmath>
#include <cstdlib>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <limits>
#include <stdexcept>
#include <string>
#include <vector>
#include <filesystem>

namespace {
constexpr int NX=81, NY=81;
constexpr int BATCH=32;
constexpr double PI=3.1415926535897932384626433832795;
constexpr double TOL=3e-9;
void require(bool ok,const std::string& reason) {if(!ok)throw std::runtime_error(reason);}
struct Model {
 const char *name,*xname,*yname,*zname,*units,*expression;
 double xmin,xmax,ymin,ymax;
};
// x and y are physical coordinates. Parenthesized coefficients and explicit
// unit denominators make expression definitions directly auditable.
const std::array<Model,6> models={{
 {"heat_transfer","position_x","position_y","temperature_K","K",
  "320+75*exp(-((x-0.35)*(x-0.35)+(y+0.25)*(y+0.25))/0.15)+18*sin(3*x)*cos(2*y)",-1,1,-1,1},
 {"motor_resonance","frequency_Hz","rotational_speed_rpm","vibration_mm_s","mm/s",
  "0.4+5/(1+((x-(20+y/300)) /4)*((x-(20+y/300))/4))+1.2*exp(-((x-52)*(x-52))/40)*((y/3000)*(y/3000))",0,100,600,3000},
 {"robot_clearance","end_effector_x_m","end_effector_y_m","clearance_m","m",
  "0.25+0.20*exp(-((x+0.30)*(x+0.30)+(y-0.12)*(y-0.12))/0.28)-0.19*exp(-((x-0.55)*(x-0.55)+(y+0.28)*(y+0.28))/0.06)",-1,1,-1,1},
 {"transformer_hotspot","current_pu","ambient_temperature_C","hotspot_temperature_C","deg C",
  "y+35*(x*x)*(1+0.003*(y-20))+12*exp(-((x-1.10)*(x-1.10))/0.02)",0.4,1.3,-20,50},
 {"reactor_conversion","temperature_K","residence_time_s","conversion_fraction","fraction",
  "1-exp(-0.005*y*exp(3500*(1/500-1/x)))",420,640,10,180},
 {"pressure_loss","volumetric_flow_m3_s","roughness_mm","pressure_drop_kPa","kPa",
  "0.9+35*x*x*(1+0.15*ln(1+y/0.05))+1.3*x*x*x",0.05,1.0,0.01,0.5}
}};
// Native reference is deliberately independent C++ code, NOT generated from
// the paceval expression string. Units and numerical contract are identical.
double native(int m,double x,double y){
 switch(m){
 case 0:return 320+75*std::exp(-((x-.35)*(x-.35)+(y+.25)*(y+.25))/.15)+18*std::sin(3*x)*std::cos(2*y);
 case 1:return .4+5/(1+std::pow((x-(20+y/300))/4,2))+1.2*std::exp(-std::pow(x-52,2)/40)*std::pow(y/3000,2);
 case 2:return .25+.20*std::exp(-((x+.30)*(x+.30)+(y-.12)*(y-.12))/.28)-.19*std::exp(-((x-.55)*(x-.55)+(y+.28)*(y+.28))/.06);
 case 3:return y+35*x*x*(1+.003*(y-20))+12*std::exp(-std::pow(x-1.10,2)/.02);
 case 4:return 1-std::exp(-.005*y*std::exp(3500*(1/500.-1/x)));
 case 5:return .9+35*x*x*(1+.15*std::log(1+y/.05))+1.3*x*x*x;
 default:throw std::runtime_error("Invalid model index");
 }
}
class Engine {
 bool initialized=false; std::vector<PACEVAL_HANDLE> handles;
public:
 Engine(){initialized=paceval_InitializeLibrary(nullptr); require(initialized,"paceval_InitializeLibrary failed");}
 Engine(const Engine&)=delete;Engine& operator=(const Engine&)=delete;
 ~Engine(){for(auto h:handles)if(h)paceval_DeleteComputation(h);if(initialized)paceval_FreeLibrary();}
 PACEVAL_HANDLE make(const Model& m){
  PACEVAL_HANDLE h=paceval_CreateComputation(m.expression,2UL,"x y",false,nullptr);
  require(h!=nullptr,std::string("Null handle for ")+m.name);
  handles.push_back(h); // capture ownership BEFORE any failure
  require(!paceval_GetIsError(h),std::string("Graph creation error: ")+m.name);
  return h;
 }
};
std::string outdir(int argc,char**argv){
 std::string output="examples";
 for(int i=1;i<argc;++i){
  if(std::string(argv[i])=="--out"&&i+1<argc)output=argv[++i];
  else throw std::runtime_error("Usage: industrial_3d [--out EXISTING_DIRECTORY]");
 }
 std::filesystem::create_directories(output);
 require(std::filesystem::is_directory(output),"Output path is not a directory: "+output);
 return output;
}
}
int main(int argc,char**argv){
 try{
  const std::string root=outdir(argc,argv);
  Engine engine;
  std::ofstream manifest(root+"/manifest.csv");require(bool(manifest),"Failed to create manifest");
  manifest<<"model,x_label,y_label,z_label,units,grid_points,scalar_pass,batch_pass,max_abs_error,expression\n";
  manifest<<std::setprecision(17);
  std::size_t total_scalar=0,total_batch=0;
  double all_error=0;
  for(std::size_t mid=0;mid<models.size();++mid){
   const auto& m=models[mid];
   PACEVAL_HANDLE graph=engine.make(m);
   const std::string path=root+"/"+m.name+".csv";
   std::ofstream csv(path);require(bool(csv),"Cannot create "+path);
   csv<<"i,j,x,y,paceval_z,native_z,absolute_error\n";
   csv<<std::setprecision(17);
   std::vector<std::array<double,2>> points;
   points.reserve(NX*NY);
   for(int i=0;i<NX;++i)for(int j=0;j<NY;++j){
    const double x=m.xmin+(m.xmax-m.xmin)*i/(NX-1);
    const double y=m.ymin+(m.ymax-m.ymin)*j/(NY-1);
    points.push_back({x,y});
   }
   double max_error=0;
   for(std::size_t n=0;n<points.size();++n){
    double xy[2]={points[n][0],points[n][1]};
    const double z=paceval_dGetComputationResult(graph,xy,nullptr,nullptr);
    require(!paceval_GetIsError(graph),std::string("Scalar SDK error: ")+m.name);
    const double ref=native(static_cast<int>(mid),xy[0],xy[1]);
    require(std::isfinite(z)&&std::isfinite(ref),"Nonfinite scalar output");
    const double err=std::abs(z-ref);
    require(err<=TOL*(1+std::abs(ref)),std::string("Scalar disagreement in ")+m.name);
    max_error=std::max(max_error,err);
    csv<<n/NY<<','<<n%NY<<','<<xy[0]<<','<<xy[1]<<','<<z<<','<<ref<<','<<err<<'\n';
    ++total_scalar;
   }
   require(bool(csv),"CSV write error");
   // The SDK batch API accepts a row-major packed array of double values.
   // We exercise 32 samples per graph with the SAME reusable computation.
   // false return denotes success; also audit individual error codes.
   std::vector<double> packed(BATCH*2),out(BATCH);
   std::vector<int> errors(BATCH,0);
   for(int j=0;j<BATCH;++j){packed[2*j]=points[j][0];packed[2*j+1]=points[j][1];}
   const bool any_error=paceval_dGetComputationResultExt(graph,packed.data(),BATCH,out.data(),nullptr,nullptr,errors.data());
   require(!any_error,std::string("Batch API failure: ")+m.name);
   for(int j=0;j<BATCH;++j){
    require(errors[j]==PACEVAL_ERR_NO_ERROR,"Batch item error");
    const double ref=native(static_cast<int>(mid),packed[j*2],packed[j*2+1]);
    require(std::isfinite(out[j])&&std::abs(out[j]-ref)<=TOL*(1+std::abs(ref)),"Batch mismatch");
    ++total_batch;
   }
   all_error=std::max(all_error,max_error);
   manifest<<m.name<<','<<m.xname<<','<<m.yname<<','<<m.zname<<','<<m.units<<','<<points.size()<<','<<points.size()<<','<<BATCH<<','<<max_error<<','<<'"'<<m.expression<<'"'<<'\n';
   std::cout<<m.name<<": "<<points.size()<<" scalar values; "<<BATCH<<" batch checks; max abs difference "<<max_error<<"\n";
  }
  require(bool(manifest),"Manifest write failure");
  std::cout<<"PASS: six original paceval graphs; "<<total_scalar<<" scalar outputs; "<<total_batch<<" batch checks; max abs difference "<<all_error<<"\n";
  return EXIT_SUCCESS;
 }catch(const std::exception& e){std::cerr<<"FAIL: "<<e.what()<<'\n';return EXIT_FAILURE;}
}
