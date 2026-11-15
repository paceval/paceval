// Optional POSIX dynamic binding to the ORIGINAL paceval Linux shared library.
// This small module contains NO mathematical evaluation, graph implementation,
// or API simulation. Every pacevalLibrary_* call is forwarded to the exact
// exported original FFI symbol. No replacement paceval runtime is distributed.
// The unmodified official paceval_main.cpp performs the public API mapping.
#include "paceval_main.h"
#include <dlfcn.h>
#include <cstdlib>
#include <filesystem>
#include <stdexcept>
#include <string>
#include <limits.h>
#include <unistd.h>
namespace {
namespace fs=std::filesystem;
void* loadOriginal(){
 static void* handle=[]()->void*{
   const char* explicitPath=std::getenv("PACEVAL_RUNTIME");
   fs::path chosen;
   if(explicitPath&&explicitPath[0])chosen=explicitPath;
   else {
     char exe[PATH_MAX]{};ssize_t len=readlink("/proc/self/exe",exe,sizeof(exe)-1);
     if(len<=0)throw std::runtime_error("Cannot locate JOSHUA executable for paceval runtime discovery");
     chosen=fs::path(std::string(exe,size_t(len))).parent_path().parent_path()/"runtime"/"libpaceval_linux_sharedLIB.so";
   }
   void* found=dlopen(chosen.c_str(),RTLD_NOW|RTLD_LOCAL);
   if(!found){const char* why=dlerror();throw std::runtime_error("The ORIGINAL paceval shared library could not be loaded from "+chosen.string()+": "+(why?why:"unknown error")+". Copy authorized SDK runtime to runtime/ or export PACEVAL_RUNTIME.");}
   return found;
 }();
 return handle;
}
void* originalSymbol(const char* name){
 void* h=loadOriginal();dlerror();void* result=dlsym(h,name);const char* why=dlerror();
 if(why||!result)throw std::runtime_error(std::string("Original paceval runtime lacks required FFI symbol ")+name+": "+(why?why:"not exported"));
 return result;
}
} // namespace
#define FORWARD_PACEVAL(symbol,rettype,params,args) \
 extern "C" rettype symbol params {using Callback=rettype (*) params;return reinterpret_cast<Callback>(originalSymbol(#symbol)) args;}

FORWARD_PACEVAL(pacevalLibrary_Initialize,bool,(const char* init),(init))
FORWARD_PACEVAL(pacevalLibrary_Free,bool,(),())
FORWARD_PACEVAL(pacevalLibrary_CreateComputation,PACEVAL_HANDLE,(const char* f,unsigned long n,const char* variables,bool interval,paceval_callbackStatusType* cb),(f,n,variables,interval,cb))
FORWARD_PACEVAL(pacevalLibrary_DeleteComputation,bool,(PACEVAL_HANDLE h),(h))
FORWARD_PACEVAL(pacevalLibrary_dGetComputationResult,double,(PACEVAL_HANDLE h,double values[],double* minResult,double* maxResult),(h,values,minResult,maxResult))
FORWARD_PACEVAL(pacevalLibrary_dGetComputationResultExt,bool,(PACEVAL_HANDLE h,double values[],unsigned long n,double* results,double* mins,double* maxs,int* errors),(h,values,n,results,mins,maxs,errors))
FORWARD_PACEVAL(pacevalLibrary_dGetMultipleComputationsResultsExt,bool,(PACEVAL_HANDLE handles[],unsigned long graphs,double values[],unsigned long rows,double* results,double* mins,double* maxs,int* errors),(handles,graphs,values,rows,results,mins,maxs,errors))
FORWARD_PACEVAL(pacevalLibrary_GetIsError,bool,(PACEVAL_HANDLE h),(h))
FORWARD_PACEVAL(pacevalLibrary_GetErrorInformation,int,(PACEVAL_HANDLE h,char* op,long* position),(h,op,position))
FORWARD_PACEVAL(pacevalLibrary_dConvertFloatToString,int,(char* destination,double value),(destination,value))
FORWARD_PACEVAL(pacevalLibrary_dConvertStringToFloat,double,(const char* source,int* error,long* position,bool interval,double* minResult,double* maxResult),(source,error,position,interval,minResult,maxResult))
