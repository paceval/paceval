// paceval Explainable Anomaly Detection: an offline, reproducible research demonstrator.
// The proprietary Linux runtime is provided externally; official SDK sources are
// compiled in this project without removing their original license notices.
// paceval computes all 100 score formulas and the individual explanation terms.
// C++ owns timestamps, data-quality policy, rule selection, alert state, and metrics.
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
#include <map>
#include <numeric>
#include <sstream>
#include <stdexcept>
#include <string>
#include <vector>
using namespace std;
namespace fs=std::filesystem;
static constexpr int CHANNELS=16, HOURS=256, RULES=100, VARS=11;
static constexpr double EPS=0.125;
static constexpr const char* VARIABLES="x mu sigma dx ds c cs eps w0 w1 w2";
static void check(bool b,const string&msg){if(!b) throw runtime_error(msg);}
static string number(double x){ostringstream s;s<<setprecision(17)<<x;return s.str();}
static string fm(double x){return "("+number(x)+")";}
struct Row {int channel=0,t=0,family=0,truth=0;string quality="GOOD";array<double,VARS> v{};};
struct Rule {int id=0,family=0,version=1;double w0=1,w1=.4,w2=.2,threshold=2.4;string formula;};
static string split_of(int channel){int k=channel%4;return k<=1?"train":k==2?"validation":"test";}
// Three nonnegative, separately inspectable contributions; the algebraic
// sum is the same expression used in each model-specific score graph.
static array<string,3> parts(int family,const string& w0,const string&w1,const string&w2){
 const string z="((x-mu)/(sigma+eps))", d="(dx/(ds+eps))", c="(c/(cs+eps))";
 string a=w0+"*abs"+z, b=w1+"*abs"+d, k=w2+"*abs"+c;
 if(family==1)b=w1+"*"+d+"*"+d;
 if(family==2)a=w0+"*"+z+"*"+z;
 if(family==3)k=w2+"*"+c+"*"+c;
 return {a,b,k};
}
static string formula(const Rule&r){auto p=parts(r.family,fm(r.w0),fm(r.w1),fm(r.w2));return "("+p[0]+"+"+p[1]+"+"+p[2]+")";}
static double native(const Rule&r,const Row&z){
 const auto &v=z.v;double q=(v[0]-v[1])/(v[2]+v[7]), d=v[3]/(v[4]+v[7]), c=v[5]/(v[6]+v[7]);
 double a=r.w0*(r.family==2?q*q:abs(q));
 double b=r.w1*(r.family==1?d*d:abs(d));
 double k=r.w2*(r.family==3?c*c:abs(c));
 return a+b+k;
}
static array<double,3> native_parts(const Rule&r,const Row&z){
 const auto &v=z.v;double q=(v[0]-v[1])/(v[2]+v[7]), d=v[3]/(v[4]+v[7]), c=v[5]/(v[6]+v[7]);
 return {r.w0*(r.family==2?q*q:abs(q)),r.w1*(r.family==1?d*d:abs(d)),r.w2*(r.family==3?c*c:abs(c))};
}
static vector<Rule> make_rules(){vector<Rule> out;out.reserve(RULES);
 for(int i=0;i<RULES;i++){
  Rule r;r.id=i+1;r.family=i/25;r.w0=.70+.025*(i%25);
  r.w1=.14+.020*((i*7)%19);r.w2=.05+.015*((i*11)%15);
  r.threshold=1.7+.095*(i%25);r.formula=formula(r);out.push_back(r);
 }return out;
}
static vector<Row> synthetic(){vector<Row> out;out.reserve(CHANNELS*HOURS);
 for(int ch=0;ch<CHANNELS;ch++){
  double previous=0;
  int family=ch/4;
  for(int t=0;t<HOURS;t++){
   Row r;r.channel=ch;r.t=t;r.family=family;
   r.truth=((t>=70&&t<=76)||(t>=160&&t<=183))?1:0;
   if(ch%3==0 && t==35)r.quality="MISSING";
   if(ch%3==0 && t==120)r.quality="BAD";
   if(ch%4==0 && t==215)r.quality="STALE";
   double sig=.70+.08*family,mu=10.+3.*family+.11*sin(.025*t+.5*ch);
   double x=mu+sig*(.21*sin(.17*t+.67*ch)+.11*cos(.071*t+ch));
   if(t>=70&&t<=76)x+=4.0*sig;
   if(t>=160&&t<=183)x+=sig*(1.90+.100*(t-160));
   double dx=t==0?0.:x-previous;previous=x;
   double ctx=.16*sin(.041*t+.31*ch);
   r.v={x,mu,sig,dx,1.5*sig,ctx,.5,EPS,0.,0.,0.};
   out.push_back(r);
  }
 }return out;
}
static vector<string> tokens(const string&s){vector<string> v; string piece;stringstream ss(s);while(getline(ss,piece,','))v.push_back(piece);return v;}
static double parse_double(const string&s){check(!s.empty(),"Missing numeric input");size_t end=0;double x=stod(s,&end);check(end==s.size()&&isfinite(x),"Non-finite or invalid sensor input");return x;}
static int parse_int(const string&s){size_t end=0;int v=stoi(s,&end);check(end==s.size(),"Invalid integer input");return v;}
static vector<Row> read_input(const fs::path& file){
 ifstream f(file);check((bool)f,"Could not open CSV: "+file.string());string line;
 check(bool(getline(f,line)),"Empty CSV input");
 check(line=="channel,minute,family,split,truth,quality,x,mu,sigma,dx,ds,context,context_scale,eps", "Unexpected CSV header");
 vector<Row> out;array<int,CHANNELS> last;last.fill(-1);
 while(getline(f,line)){
  if(line.empty()) continue;
  auto v=tokens(line);
  check(v.size()==14,"CSV column count mismatch");
  Row r;r.channel=parse_int(v[0]);r.t=parse_int(v[1]);r.family=parse_int(v[2]);r.truth=parse_int(v[4]);r.quality=v[5];
  check(r.channel>=0&&r.channel<CHANNELS&&r.family==r.channel/4,"Invalid channel or family");
  check(v[3]==split_of(r.channel),"Split mismatch");
  check(r.t>=0&&r.t<HOURS&&r.t==last[r.channel]+1,"Missing, duplicate or nonmonotonic timestamp");
  check(r.truth==0||r.truth==1,"Invalid truth flag");
  check(r.quality=="GOOD"||r.quality=="BAD"||r.quality=="MISSING"||r.quality=="STALE", "Invalid quality status");
  for(int k=0;k<8;k++)r.v[k]=parse_double(v[6+k]);
  check(r.v[2]>.05&&r.v[4]>.05&&r.v[6]>.05&&r.v[7]>0.0,"Invalid normalization denominators");
  check(abs(r.v[0])<1000&&abs(r.v[1])<1000&&abs(r.v[3])<1000&&abs(r.v[5])<1000,"Out-of-range signal");
  last[r.channel]=r.t;out.push_back(r);
 }
 check(out.size()==CHANNELS*HOURS,"CSV does not contain 16 complete, ordered 256-sample channels");
 return out;
}
static void write_signal(const fs::path&f,const vector<Row>&rows){ofstream o(f);check(bool(o),"Could not create signals.csv");o<<setprecision(17);
 o<<"channel,minute,family,split,truth,quality,x,mu,sigma,dx,ds,context,context_scale,eps\n";
 for(auto&r:rows){o<<r.channel<<","<<r.t<<","<<r.family<<","<<split_of(r.channel)<<","<<r.truth<<","<<r.quality;
 for(int k=0;k<8;k++) o<<","<<r.v[k];
  o<<"\n";}
}
static void write_rules(const fs::path&f,const vector<Rule>&rules){ofstream o(f);check(bool(o),"Could not create rules.csv");o<<setprecision(17);
 o<<"rule_id,family,version,w0,w1,w2,threshold,formula\n";
 for(auto&r:rules)o<<r.id<<","<<r.family<<","<<r.version<<","<<r.w0<<","<<r.w1<<","<<r.w2<<","<<r.threshold<<","<<r.formula<<"\n";
}
class Engine{
 vector<PACEVAL_HANDLE> owned_;vector<PACEVAL_HANDLE> score_;
 array<PACEVAL_HANDLE,12> components_{};PACEVAL_HANDLE tinc_=nullptr;
 PACEVAL_HANDLE add(const string&expr,bool use_tinc=false){
  auto h=paceval_CreateComputation(expr.c_str(),VARS,VARIABLES,use_tinc,nullptr);
  check(h!=nullptr,"paceval_CreateComputation returned null");
  if(paceval_GetIsError(h)){
   long pos=0;char buffer[PACEVAL_MAXERR+1]{};int code=paceval_GetErrorInformation(h,buffer,&pos);
   string err="paceval could not compile expression error="+to_string(code)+" position="+to_string(pos)+" "+buffer+" expr="+expr;
   paceval_DeleteComputation(h);throw runtime_error(err);
  }
  owned_.push_back(h);return h;
 }
public:
 explicit Engine(const vector<Rule>&rules){
  check(paceval_InitializeLibrary(nullptr),"paceval_InitializeLibrary failed");
  for(auto&r:rules)score_.push_back(add(r.formula));
  for(int f=0;f<4;f++){auto p=parts(f,"w0","w1","w2");for(int j=0;j<3;j++)components_[3*f+j]=add(p[j]);}
  tinc_=add("x*x+1",true);
 }
 Engine(const Engine&)=delete;Engine&operator=(const Engine&)=delete;
 ~Engine(){for(auto h:owned_)paceval_DeleteComputation(h);paceval_FreeLibrary();}
 vector<double> eval_score(const vector<Row>&valid,size_t batch,double&max_diff,const vector<Rule>&rules){
  size_t n=valid.size();vector<double> all(RULES*n,0.0);max_diff=0;
  for(size_t from=0;from<n;from+=batch){
   size_t take=min(batch,n-from);vector<double> vars(take*VARS),value(RULES*take);vector<int>errors(RULES*take,-1);
   for(size_t k=0;k<take;k++)copy(valid[from+k].v.begin(),valid[from+k].v.end(),vars.begin()+VARS*k);
   bool failed=paceval_dGetMultipleComputationsResultsExt(score_.data(),RULES,vars.data(),(unsigned long)take,value.data(),nullptr,nullptr,errors.data());
   check(!failed,"paceval multi-computation batch error");
   for(int j=0;j<RULES;j++)for(size_t k=0;k<take;k++){
    double v=value[j*take+k];check(errors[j*take+k]==PACEVAL_ERR_NO_ERROR&&isfinite(v),"Invalid paceval score");
    double expected=native(rules[j],valid[from+k]);double diff=abs(v-expected);
    check(diff<=5e-12+2e-12*abs(expected),"paceval score/native mismatch");
    max_diff=max(max_diff,diff);all[j*n+from+k]=v;
   }
  }return all;
 }
 vector<array<double,3>> eval_components(const vector<Row>&valid,const vector<int>&selected,const vector<Rule>&rules,size_t batch){
  vector<array<double,3>> out(valid.size());
  for(size_t from=0;from<valid.size();from+=batch){
   size_t take=min(batch,valid.size()-from);vector<double> vars(take*VARS),results(12*take);vector<int>errors(12*take,-1);
   for(size_t k=0;k<take;k++){
    const Row&r=valid[from+k];auto v=r.v;auto &rule=rules[selected[r.family]];
    v[8]=rule.w0;v[9]=rule.w1;v[10]=rule.w2;
    copy(v.begin(),v.end(),vars.begin()+VARS*k);
   }
   bool failed=paceval_dGetMultipleComputationsResultsExt(components_.data(),12,vars.data(),(unsigned long)take,results.data(),nullptr,nullptr,errors.data());
   check(!failed,"paceval explanation graph batch error");
   for(size_t k=0;k<take;k++){
    int fam=valid[from+k].family;
    for(int j=0;j<3;j++){
     int idx=(3*fam+j)*(int)take+(int)k;double z=results[idx];
     check(errors[idx]==PACEVAL_ERR_NO_ERROR&&isfinite(z)&&z>=-1e-12,"Invalid explanation result");
     out[from+k][j]=z;
    }
    auto expected=native_parts(rules[selected[fam]],valid[from+k]);
    for(int j=0;j<3;j++)check(abs(out[from+k][j]-expected[j])<2e-11,"Explanation component mismatch");
   }
  }return out;
 }
 PACEVAL_HANDLE replace_rule(int index,const string&f){check(index>=0&&index<RULES,"rule id out of range");
  auto h=add(f);score_[index]=h;return h; // old graph kept until all auditing is complete
 }
 double single(int rule,const Row&row){auto a=row.v;double lo=0,hi=0;
  double z=paceval_dGetComputationResult(score_[rule],a.data(),&lo,&hi);
  check(!paceval_GetIsError(score_[rule])&&isfinite(z),"Rule evaluation failed");return z;
 }
 array<double,3> tinc(double x){array<double,VARS> a{};a[0]=x;a[2]=1;a[4]=1;a[6]=1;a[7]=EPS;
  double lo=0,hi=0;double v=paceval_dGetComputationResult(tinc_,a.data(),&lo,&hi);
  check(!paceval_GetIsError(tinc_)&&isfinite(v)&&isfinite(lo)&&isfinite(hi)&&lo<=hi,"Invalid TINC diagnostic");
  return {v,lo,hi};
 }
};
struct Conf {int tp=0,fp=0,tn=0,fn=0;double f1()const{return 2.0*tp/(max(1,2*tp+fp+fn));}};
static Conf confusion(const vector<Row>&valid,const vector<double>&scores,int rule,const vector<Rule>&rs,const string&split,int family){
 Conf c;size_t n=valid.size();for(size_t i=0;i<n;i++){
  auto&r=valid[i];if(r.family!=family||split_of(r.channel)!=split)continue;
  bool alarm=scores[rule*n+i]>=rs[rule].threshold;int y=r.truth;
  if(alarm&&y)c.tp++;else if(alarm)c.fp++;else if(y)c.fn++;else c.tn++;
 }return c;
}
static array<int,4> choose(const vector<Row>&valid,const vector<double>&scores,const vector<Rule>&rs){
 array<int,4> selected{};
 for(int fam=0;fam<4;fam++){
  int best=fam*25;Conf cb=confusion(valid,scores,best,rs,"validation",fam);
  for(int i=best+1;i<fam*25+25;i++){
   auto c=confusion(valid,scores,i,rs,"validation",fam);
   if(c.f1()>cb.f1()+1e-12||(abs(c.f1()-cb.f1())<=1e-12 &&c.fp<cb.fp)) {best=i;cb=c;}
  }selected[fam]=best;
 }return selected;
}
static void self_test(){
 auto rules=make_rules();check(rules.size()==RULES,"100 rules missing");
 auto rows=synthetic();check(rows.size()==4096,"Synthetic record count incorrect");
 for(auto &r:rows){double s=native(rules[17],r);auto p=native_parts(rules[17],r);check(abs(s-(p[0]+p[1]+p[2]))<1e-12,"native decomposition failure");}
 Engine eng(rules);double m=0;vector<Row> few(rows.begin(),rows.begin()+15);eng.eval_score(few,3,m,rules);
 cout<<"Self-test passed: official paceval runtime, 100 graphs, explanation reference.\n";
}
int main(int argc,char**argv){
 try{
  fs::path out="examples_generated",input;size_t batch=128;bool st=false;
  for(int i=1;i<argc;i++){
   string v=argv[i];if(v=="--out"&&i+1<argc)out=argv[++i];
   else if(v=="--input"&&i+1<argc)input=argv[++i];
   else if(v=="--batch"&&i+1<argc)batch=(size_t)stoul(argv[++i]);
   else if(v=="--self-test")st=true;else throw runtime_error("Unknown command line argument: "+v);
  }
  check(batch>=1&&batch<=1024,"Batch size must be from 1 to 1024");
  if(st){self_test();return 0;}
  vector<Row> rows=input.empty()?synthetic():read_input(input);
  fs::create_directories(out);write_signal(out/"signals.csv",rows);
  auto rules=make_rules();write_rules(out/"rules.csv",rules);
  vector<Row> valid;valid.reserve(rows.size());for(auto&r:rows)if(r.quality=="GOOD")valid.push_back(r);
  Engine e(rules);double maxdiff=0;
  auto scores=e.eval_score(valid,batch,maxdiff,rules);auto selected=choose(valid,scores,rules);
  auto terms=e.eval_components(valid,vector<int>(selected.begin(),selected.end()),rules,batch);
  ofstream sel(out/"selection.csv"),result(out/"selected_scores.csv"),diagnostics(out/"model_diagnostics.csv");
  check(sel&&result&&diagnostics,"Output open failure");
  sel<<setprecision(17);result<<setprecision(17);diagnostics<<setprecision(17);
  sel<<"family,selected_rule,version,validation_tp,validation_fp,validation_fn,validation_f1,test_tp,test_fp,test_fn,test_f1\n";
  int selected_tp=0,selected_fp=0,selected_fn=0;
  for(int fam=0;fam<4;fam++){
   auto a=confusion(valid,scores,selected[fam],rules,"validation",fam);
   auto b=confusion(valid,scores,selected[fam],rules,"test",fam);
   selected_tp+=b.tp;selected_fp+=b.fp;selected_fn+=b.fn;
   sel<<fam<<","<<rules[selected[fam]].id<<",1,"<<a.tp<<","<<a.fp<<","<<a.fn<<","<<a.f1()<<","<<b.tp<<","<<b.fp<<","<<b.fn<<","<<b.f1()<<"\n";
  }
  result<<"channel,minute,split,family,truth,quality,selected_rule,score,deviation_component,derivative_component,context_component,threshold,raw_alarm,persistent_alarm\n";
  // Persistent alert state: two consecutive positive results turn on, two
  // consecutive readings below 70% of the threshold turn it off. Invalid
  // measurements reset the state and cannot generate a positive alarm.
  array<int,CHANNELS> pos{},neg{},active{};size_t index=0;
  vector<array<int,CHANNELS>> event_times(2);for(auto &a:event_times)a.fill(-1);
  int raw_hits=0;
  for(const auto&r:rows){
   int ri=selected[r.family];const Rule&rule=rules[ri];
   if(r.quality!="GOOD"){
    pos[r.channel]=neg[r.channel]=active[r.channel]=0;
    result<<r.channel<<","<<r.t<<","<<split_of(r.channel)<<","<<r.family<<","<<r.truth<<","<<r.quality<<","<<rule.id<<",,,,,"<<rule.threshold<<",0,0\n";
    continue;
   }
   check(index<valid.size()&&valid[index].channel==r.channel&&valid[index].t==r.t,"Valid-row indexing mismatch");
   double s=scores[ri*valid.size()+index];auto p=terms[index];
   check(abs(s-(p[0]+p[1]+p[2]))<1e-10,"Paceval score does not match paceval components");
   bool raw=s>=rule.threshold;raw_hits+=(int)raw;
   if(raw){pos[r.channel]++;neg[r.channel]=0;if(pos[r.channel]>=2)active[r.channel]=1;}
   else if(s<.70*rule.threshold){pos[r.channel]=0;neg[r.channel]++;if(neg[r.channel]>=2)active[r.channel]=0;}
   else {pos[r.channel]=0;neg[r.channel]=0;}
   if(active[r.channel]&&r.truth&&split_of(r.channel)=="test"){
    int eidx=r.t<100?0:1;if(event_times[eidx][r.channel]<0)event_times[eidx][r.channel]=r.t;
   }
   result<<r.channel<<","<<r.t<<","<<split_of(r.channel)<<","<<r.family<<","<<r.truth<<","<<r.quality<<","<<rule.id<<","<<s<<","<<p[0]<<","<<p[1]<<","<<p[2]<<","<<rule.threshold<<","<<raw<<","<<active[r.channel]<<"\n";
   index++;
  }
  check(index==valid.size(),"Incomplete score replay");
  diagnostics<<"rule_id,family,version,validation_tp,validation_fp,validation_fn,validation_f1,test_tp,test_fp,test_fn,test_f1,selected\n";
  for(int j=0;j<RULES;j++){
   int f=rules[j].family;auto v=confusion(valid,scores,j,rules,"validation",f),t=confusion(valid,scores,j,rules,"test",f);
   diagnostics<<rules[j].id<<","<<f<<",1,"<<v.tp<<","<<v.fp<<","<<v.fn<<","<<v.f1()<<","<<t.tp<<","<<t.fp<<","<<t.fn<<","<<t.f1()<<","<<(int)(selected[f]==j)<<"\n";
  }
  ofstream event(out/"event_detection.csv");check(bool(event),"Could not open event_detection.csv");
  event<<"channel,split,family,event_type,start,end,first_detected,delay_samples,detected\n";
  int test_events=0,detected_events=0;
  for(int ch=0;ch<CHANNELS;ch++)for(int k=0;k<2;k++){
   int start=k==0?70:160,end=k==0?76:183,first=event_times[k][ch];
   if(split_of(ch)=="test"){test_events++;if(first>=0)detected_events++;}
   event<<ch<<","<<split_of(ch)<<","<<ch/4<<","<<(k==0?"spike":"drift")<<","<<start<<","<<end<<","<<first<<","<<(first<0?-1:first-start)<<","<<(first>=0)<<"\n";
  }
  // Audited rule revision: replacing one computation leaves all other graph
  // handles intact. The original formula retains its historical version.
  Rule updated=rules[16];updated.version=2;updated.w0*=1.18;updated.formula=formula(updated);
  e.replace_rule(16,updated.formula);
  ofstream upd(out/"rule_update.csv");upd<<setprecision(17);
  upd<<"rule_id,old_version,new_version,channel,minute,old_score,new_score,other_models_unmodified\n";
  for(int i=0;i<24;i++){
   const Row&r=valid[i];double old=native(rules[16],r),nw=e.single(16,r);
   check(abs(nw-native(updated,r))<5e-12,"Updated rule incorrect");
   upd<<17<<",1,2,"<<r.channel<<","<<r.t<<","<<old<<","<<nw<<",1\n";
  }
  // TINC is audited separately on a smooth dyadic polynomial, NOT inferred
  // as a global enclosure guarantee for the non-smooth anomaly rules.
  ofstream ti(out/"tinc_samples.csv");ti<<setprecision(17);
  ti<<"sample,x,paceval_result,raw_lower,raw_upper,reference_formula\n";
  for(int j=0;j<24;j++){
   double x=(j-12)/8.0;auto z=e.tinc(x);
   ti<<j<<","<<x<<","<<z[0]<<","<<z[1]<<","<<z[2]<<",x*x+1\n";
  }
  // Save exact native-vs-paceval sample locations for high precision audit.
  ofstream audit(out/"audit_samples.csv");audit<<setprecision(17);
  audit<<"channel,minute,rule_id,family,x,mu,sigma,dx,ds,c,cs,eps,w0,w1,w2,paceval_score\n";
  for(int j=0;j<200;j++){
   int ri=(j*43)%100;size_t k=(j*79)%valid.size();auto&r=valid[k];auto&rule=rules[ri];
   audit<<r.channel<<","<<r.t<<","<<rule.id<<","<<rule.family;
   for(int m=0;m<8;m++)audit<<","<<r.v[m];
   audit<<","<<rule.w0<<","<<rule.w1<<","<<rule.w2<<","<<scores[ri*valid.size()+k]<<"\n";
  }
  ofstream summary(out/"validation.json");summary<<setprecision(17);
  summary<<"{\n  \"dataset\": \"synthetic labeled streams only\",\n  \"channels\": "<<CHANNELS<<",\n  \"samples_per_channel\": "<<HOURS<<",\n  \"candidate_rule_graphs\": "<<RULES<<",\n  \"explanation_graphs\": 12,\n  \"tinc_diagnostic_graphs\": 1,\n  \"evaluated_score_count\": "<<RULES*valid.size()<<",\n  \"quality_skipped_rows\": "<<rows.size()-valid.size()<<",\n  \"native_max_absolute_difference\": "<<maxdiff<<",\n  \"validation_selected_test_tp\": "<<selected_tp<<",\n  \"validation_selected_test_fp\": "<<selected_fp<<",\n  \"validation_selected_test_fn\": "<<selected_fn<<",\n  \"test_events\": "<<test_events<<",\n  \"test_events_detected\": "<<detected_events<<",\n  \"raw_score_alerts_across_all_splits\": "<<raw_hits<<"\n}\n";
  cout<<"SUCCESS: score graphs="<<RULES<<" valid rows="<<valid.size()<<" total paceval scores="<<RULES*valid.size()<<"\n";
  cout<<"Native reference max abs error="<<setprecision(12)<<maxdiff<<"; held-out events="<<detected_events<<"/"<<test_events<<"\n";
  return 0;
 }catch(const exception&e){cerr<<"ERROR: "<<e.what()<<"\n";return 2;}
}
