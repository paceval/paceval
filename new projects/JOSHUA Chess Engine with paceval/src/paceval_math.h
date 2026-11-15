#pragma once
struct Engine{
 vector<PACEVAL_HANDLE>owned;size_t scalar=0,batches=0,graphPoints=0;bool graphMajor=false;
 Engine(){insist(paceval_InitializeLibrary(nullptr),"paceval library init failed");}
 ~Engine(){for(auto h:owned)paceval_DeleteComputation(h);paceval_FreeLibrary();}
 PACEVAL_HANDLE create(const string& formula,const vector<string>&vars){auto names=join(vars);auto h=paceval_CreateComputation(formula.c_str(),vars.size(),names.c_str(),false,nullptr);insist(h&&!paceval_GetIsError(h),"Graph compile failed: "+formula);owned.push_back(h);return h;}
 double eval(PACEVAL_HANDLE h,const vector<double>&v){auto a=v;double r=paceval_dGetComputationResult(h,a.data(),nullptr,nullptr);scalar++;insist(!paceval_GetIsError(h)&&std::isfinite(r),"Scalar graph failed");graphPoints++;return r;}
 void probe(){auto a=create("x+2*y",{"x","y"}),b=create("3*x-y",{"x","y"});PACEVAL_HANDLE hs[]={a,b};double in[]={1,2,4,7},o[4]{},lo[4]{},hi[4]{};int err[4]{};bool failure=paceval_dGetMultipleComputationsResultsExt(hs,2,in,2,o,lo,hi,err);insist(!failure&&!err[0]&&!err[1]&&!err[2]&&!err[3],"API layout probe failed");
 if(std::abs(o[0]-5)<1e-8&&std::abs(o[1]-18)<1e-8&&std::abs(o[2]-1)<1e-8&&std::abs(o[3]-5)<1e-8)graphMajor=true;
 else if(std::abs(o[0]-5)<1e-8&&std::abs(o[1]-1)<1e-8&&std::abs(o[2]-18)<1e-8&&std::abs(o[3]-5)<1e-8)graphMajor=false;
 else throw std::runtime_error("Unexpected multi-graph output layout");batches++;graphPoints+=4;}
 vector<vector<double>> multi(const vector<PACEVAL_HANDLE>&h,const vector<vector<double>>&rows){insist(!h.empty()&&!rows.empty(),"Empty batch");size_t n=rows.size(),m=rows[0].size();vector<double>in;in.reserve(n*m);for(auto&r:rows){insist(r.size()==m,"Width mismatch");for(double v:r)insist(std::isfinite(v),"nonfinite input");in.insert(in.end(),r.begin(),r.end());}
 vector<double>out(n*h.size()),lo(out.size()),hi(out.size());vector<int>e(out.size(),-1);bool fail=paceval_dGetMultipleComputationsResultsExt(const_cast<PACEVAL_HANDLE*>(h.data()),h.size(),in.data(),n,out.data(),lo.data(),hi.data(),e.data());insist(!fail,"MultiGraph failed");for(int x:e)insist(x==0,"MultiGraph error code");vector<vector<double>>z(n,vector<double>(h.size()));for(size_t i=0;i<n;i++)for(size_t j=0;j<h.size();j++){z[i][j]=out[graphMajor?j*n+i:i*h.size()+j];insist(std::isfinite(z[i][j]),"Nonfinite graph result");}batches++;graphPoints+=out.size();return z;}
 vector<double>single(PACEVAL_HANDLE h,const vector<vector<double>>&rows){size_t n=rows.size(),m=rows[0].size();vector<double>in;in.reserve(n*m);for(auto&r:rows){insist(r.size()==m,"Variable mismatch");in.insert(in.end(),r.begin(),r.end());}vector<double>out(n),lo(n),hi(n);vector<int>err(n,-1);bool fail=paceval_dGetComputationResultExt(h,in.data(),n,out.data(),lo.data(),hi.data(),err.data());insist(!fail,"Single batch error");for(size_t i=0;i<n;i++)insist(err[i]==0&&std::isfinite(out[i]),"Single batch result error");batches++;graphPoints+=n;return out;}
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
