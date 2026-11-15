#pragma once
struct Engine{
 struct Record {std::string formula, variables;std::size_t evaluated_points=0;};
 vector<PACEVAL_HANDLE>owned;std::vector<Record>registered;
 std::map<PACEVAL_HANDLE,std::size_t> handleIndex;
 size_t scalar=0,batches=0,graphPoints=0;bool graphMajor=false;
 Engine(){insist(paceval_InitializeLibrary(nullptr),"paceval library init failed");}
 ~Engine(){for(auto h:owned)paceval_DeleteComputation(h);paceval_FreeLibrary();}
 PACEVAL_HANDLE create(const string& formula,const vector<string>&vars){auto names=join(vars);auto h=paceval_CreateComputation(formula.c_str(),vars.size(),names.c_str(),false,nullptr);insist(h&&!paceval_GetIsError(h),"Graph compile failed: "+formula);owned.push_back(h);handleIndex[h]=registered.size();
 registered.push_back({formula,names,0});return h;}
 double eval(PACEVAL_HANDLE h,const vector<double>&v){auto a=v;double r=paceval_dGetComputationResult(h,a.data(),nullptr,nullptr);scalar++;registered.at(handleIndex.at(h)).evaluated_points++;insist(!paceval_GetIsError(h)&&std::isfinite(r),"Scalar graph failed");graphPoints++;return r;}
 void probe(){auto a=create("x+2*y",{"x","y"}),b=create("3*x-y",{"x","y"});PACEVAL_HANDLE hs[]={a,b};double in[]={1,2,4,7},o[4]{},lo[4]{},hi[4]{};int err[4]{};bool failure=paceval_dGetMultipleComputationsResultsExt(hs,2,in,2,o,lo,hi,err);insist(!failure&&!err[0]&&!err[1]&&!err[2]&&!err[3],"API layout probe failed");
 if(std::abs(o[0]-5)<1e-8&&std::abs(o[1]-18)<1e-8&&std::abs(o[2]-1)<1e-8&&std::abs(o[3]-5)<1e-8)graphMajor=true;
 else if(std::abs(o[0]-5)<1e-8&&std::abs(o[1]-1)<1e-8&&std::abs(o[2]-18)<1e-8&&std::abs(o[3]-5)<1e-8)graphMajor=false;
 else throw std::runtime_error("Unexpected multi-graph output layout");batches++;graphPoints+=4;
 registered.at(handleIndex.at(a)).evaluated_points+=2;
 registered.at(handleIndex.at(b)).evaluated_points+=2;}
 vector<vector<double>> multi(const vector<PACEVAL_HANDLE>&h,const vector<vector<double>>&rows){insist(!h.empty()&&!rows.empty(),"Empty batch");size_t n=rows.size(),m=rows[0].size();vector<double>in;in.reserve(n*m);for(auto&r:rows){insist(r.size()==m,"Width mismatch");for(double v:r)insist(std::isfinite(v),"nonfinite input");in.insert(in.end(),r.begin(),r.end());}
 vector<double>out(n*h.size()),lo(out.size()),hi(out.size());vector<int>e(out.size(),-1);bool fail=paceval_dGetMultipleComputationsResultsExt(const_cast<PACEVAL_HANDLE*>(h.data()),h.size(),in.data(),n,out.data(),lo.data(),hi.data(),e.data());insist(!fail,"MultiGraph failed");for(int x:e)insist(x==0,"MultiGraph error code");vector<vector<double>>z(n,vector<double>(h.size()));for(size_t i=0;i<n;i++)for(size_t j=0;j<h.size();j++){z[i][j]=out[graphMajor?j*n+i:i*h.size()+j];insist(std::isfinite(z[i][j]),"Nonfinite graph result");}batches++;graphPoints+=out.size();
 for(auto handle:h)registered.at(handleIndex.at(handle)).evaluated_points+=n;
 return z;}
 vector<double>single(PACEVAL_HANDLE h,const vector<vector<double>>&rows){size_t n=rows.size(),m=rows[0].size();vector<double>in;in.reserve(n*m);for(auto&r:rows){insist(r.size()==m,"Variable mismatch");in.insert(in.end(),r.begin(),r.end());}vector<double>out(n),lo(n),hi(n);vector<int>err(n,-1);bool fail=paceval_dGetComputationResultExt(h,in.data(),n,out.data(),lo.data(),hi.data(),err.data());insist(!fail,"Single batch error");for(size_t i=0;i<n;i++)insist(err[i]==0&&std::isfinite(out[i]),"Single batch result error");batches++;graphPoints+=n;
 registered.at(handleIndex.at(h)).evaluated_points+=n;
 return out;}
 void exportCatalog(const std::string&directory)const {
  std::ofstream out(std::filesystem::path(directory)/"paceval_all_graphs.csv");
  insist(bool(out),"Cannot write paceval_all_graphs.csv");
  out<<"graph_id,created,evaluated_points,variables,paceval_expression\n";
  auto quote=[](const std::string&value){std::string z="\"";
   for(char c:value){if(c=='\"')z+="\"\"";else z+=c;}
   return z+"\"";};
  for(std::size_t i=0;i<registered.size();i++){
   const auto&r=registered[i];out<<"G"<<std::setfill('0')<<std::setw(4)<<(i+1)
   <<",1,"<<r.evaluated_points<<","<<quote(r.variables)<<","<<quote(r.formula)<<"\n";
  }
  insist(bool(out),"Failed writing paceval full graph catalog");
 }
};
// Input features are literal counts, not native weighted evaluations.
const vector<string> featureNames={"wp","wn","wb","wr","wq","bp","bn","bb","br","bq","wc","bc","wd","bd","wa","ba","wk","bk","bias"};
vector<double> features(const Board&s){vector<double>x(19,0);const string pcs="PNBRQpnbrq";for(int i=0;i<128;i++){if(!inside(i))continue;char p=s.b[i];auto j=pcs.find(p);if(j!=string::npos)x[j]++;
 int c=col(p),f=fileof(i),r=rankof(i);if(c==0)continue;
 if(f>=2&&f<=5&&r>=2&&r<=5){if(c>0)x[10]++;else x[11]++;}
 if(p=='N'||p=='B'){if(r<7)x[12]++;}if(p=='n'||p=='b'){if(r>0)x[13]++;}
 if(p=='P')x[14]+=6-r;else if(p=='p')x[15]+=r-1;
 if(p=='K')x[16]=(f==6||f==2)?1:0;if(p=='k')x[17]=(f==6||f==2)?1:0;
 }x[18]=1;return x;}
const string mat="(100*(wp-bp)+320*(wn-bn)+330*(wb-bb)+500*(wr-br)+900*(wq-bq))";
const string center="(wc-bc)",development="(wd-bd)",advance="(wa-ba)",ksafe="(wk-bk)";
struct Expr{string name,ver,formula;PACEVAL_HANDLE h;size_t points=0;};
struct Evaluator{Engine&e;vector<Expr>expr;std::map<string,size_t>by;
 Evaluator(Engine&a):e(a){auto add=[&](string name,string ver,string f){auto h=e.create(f,featureNames);by[ver+"_"+name]=expr.size();expr.push_back({name,ver,f,h,0});};
   for(string version:{"V1","V2"}){
    bool advanced=version=="V2";string score=advanced?"("+mat+"+13*"+center+"+17*"+development+"+3*"+advance+"+18*"+ksafe+")":mat;
    add("MATERIAL",version,mat);add("CENTER",version,center);add("DEVELOPMENT",version,development);add("PAWN_ADVANCE",version,advance);add("KING_ZONE",version,ksafe);add("SCORE",version,score);
    add("SCORE_MARGIN",version,"(2000-abs("+score+"))");add("SCORE_GUARD",version,"((abs("+score+")<=2000) AND (wp>=0) AND (bp>=0))");
    add("SENSITIVITY_CENTER_WEIGHT",version,center);add("COMPOSITE_PIECE_ACTIVITY",version,"(13*"+center+"+17*"+development+")");
   }
 }
 vector<double> evaluate(const Board&b){auto rows=e.multi(handles(),{features(b)});return rows[0];}
 vector<PACEVAL_HANDLE> handles()const{vector<PACEVAL_HANDLE>h;for(auto&x:expr)h.push_back(x.h);return h;}
};


// JOSHUA V3: deterministic, explicitly scoped handcrafted position features.
// Chess rules and all board/attack extraction remain in C++; the weighted
// evaluation and component functions are reusable REAL paceval computations.
// V1/V2 stay unchanged and retain their original 19-variable SDK graphs.
const vector<string> featureNamesV3={
 "wp","wn","wb","wr","wq","bp","bn","bb","br","bq",
 "wc","bc","wd","bd","wa","ba","wk","bk","bias",
 "wpsq","bpsq","wdoub","bdoub","wisolated","bisolated",
 "wpassed","bpassed","wbpair","bbpair","wshield","bshield","tempo"
};
vector<double> featuresV3(const Board&b){
 vector<double> v=features(b);insist(v.size()==19,"V3 feature source width");
 v.resize(featureNamesV3.size(),0.0);
 int pawns[2][8]{};
 for(int i=0;i<128;i++)if(inside(i)){
   const char p=b.b[i]; if(std::tolower(static_cast<unsigned char>(p))!='p')continue;
   const int side=col(p)==1?0:1;pawns[side][fileof(i)]++;
 }
 for(int side=0;side<2;side++){
   const int dub=side==0?21:22,isolated=side==0?23:24,bishoppair=side==0?27:28;
   for(int f=0;f<8;f++)if(pawns[side][f]){
     v[dub]+=std::max(0,pawns[side][f]-1);
     if((f==0||pawns[side][f-1]==0)&&(f==7||pawns[side][f+1]==0))v[isolated]+=pawns[side][f];
   }
   v[bishoppair]=(v[side==0?2:7]>=2)?1:0;
 }
 for(int i=0;i<128;i++)if(inside(i)){
   const char p=b.b[i];const int color=col(p);if(!color)continue;
   const int side=color==1?0:1, f=fileof(i),r=rankof(i),cf=std::min(f,7-f),cr=std::min(r,7-r);
   const char piece=char(std::tolower(static_cast<unsigned char>(p)));
   double sqScore=0;
   if(piece=='n')sqScore=8*(cf+cr);
   if(piece=='b')sqScore=5*(cf+cr);
   if(piece=='r')sqScore=3*cr;
   if(piece=='q')sqScore=2*(cf+cr);
   if(piece=='p')sqScore=3*cf+2*(color==1?6-r:r-1);
   v[side==0?19:20]+=sqScore;
   if(piece=='p'){
     bool passed=true;
     for(int t=0;t<128;t++)if(inside(t)&&b.b[t]==(color==1?'p':'P')){
       if(std::abs(fileof(t)-f)<=1&& (color==1?rankof(t)<r:rankof(t)>r)) {passed=false;break;}
     }
     if(passed)v[side==0?25:26]++;
   }
   if(piece=='k'){
     const int ahead=color==1?-1:1;
     for(int delta=1;delta<=2;delta++)for(int df=-1;df<=1;df++){
       const int rr=r+ahead*delta,ff=f+df;
       if(rr>=0&&rr<8&&ff>=0&&ff<8&&b.b[rr*16+ff]==(color==1?'P':'p'))v[side==0?29:30]++;
     }
   }
 }
 v[31]=b.turn;return v;
}
const string v3_struct="(-16*(wdoub-bdoub)-12*(wisolated-bisolated)+22*(wpassed-bpassed)+28*(wbpair-bbpair))";
const string v3_activity="(wpsq-bpsq)";
const string v3_shelter="(9*(wshield-bshield))";
const string v3_tempo="(7*tempo)";
const string v3_score="("+mat+"+13*"+center+"+17*"+development+"+3*"+advance+"+18*"+ksafe+"+"+v3_activity+"+"+v3_struct+"+"+v3_shelter+"+"+v3_tempo+")";
int scoreNativeV3(const vector<double>&v){
 insist(v.size()==32,"V3 native width mismatch");
 double score=100*(v[0]-v[5])+320*(v[1]-v[6])+330*(v[2]-v[7])+500*(v[3]-v[8])+900*(v[4]-v[9]);
 score+=13*(v[10]-v[11])+17*(v[12]-v[13])+3*(v[14]-v[15])+18*(v[16]-v[17]);
 score+=v[19]-v[20]-16*(v[21]-v[22])-12*(v[23]-v[24])+22*(v[25]-v[26])+28*(v[27]-v[28])+9*(v[29]-v[30])+7*v[31];
 return int(std::lround(score));
}
struct EvaluatorV3{
 Engine&e;vector<Expr>expr;std::map<string,size_t>by;
 explicit EvaluatorV3(Engine&eng):e(eng){
  auto add=[&](const string&name,const string&formula){auto h=e.create(formula,featureNamesV3);by[name]=expr.size();expr.push_back({name,"V3",formula,h,0});};
  add("SCORE",v3_score);add("MATERIAL",mat);add("POSITIONAL_ACTIVITY",v3_activity);
  add("PAWN_STRUCTURE",v3_struct);add("KING_SHELTER",v3_shelter);add("TEMPO",v3_tempo);
  add("SCORE_MARGIN","(2000-abs("+v3_score+"))");
  add("SCORE_GUARD","((abs("+v3_score+")<=2000) AND (wp>=0) AND (bp>=0))");
  add("SENSITIVITY_ACTIVITY_WEIGHT",v3_activity);
  add("POSITIONAL_COMPOSITE","(13*"+center+"+17*"+development+"+"+v3_activity+")");
 }
 vector<PACEVAL_HANDLE> handles()const{vector<PACEVAL_HANDLE>h;for(const auto&x:expr)h.push_back(x.h);return h;}
};
