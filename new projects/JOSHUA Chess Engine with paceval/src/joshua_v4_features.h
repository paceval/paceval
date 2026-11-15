#pragma once
// JOSHUA V4: board-derived, material-aware and tactical input features.
// Exactly 48 numeric inputs; the first 32 preserve V3 without modification.
const vector<string> featureNamesV4 = [] {
    vector<string> v=featureNamesV3;
    const vector<string> add={"wmob","bmob","wcaps","bcaps", "wcheck","bcheck",
      "whanging","bhanging","wattacked","battacked", "wqueenThreat","bqueenThreat",
      "wrookThreat","brookThreat","wkingDanger","bkingDanger"};
    v.insert(v.end(), add.begin(), add.end());
    insist(v.size()==48,"V4 feature width"); return v;
}();
inline vector<double> featuresV4(const Board&b){
    vector<double> v=featuresV3(b);v.resize(48,0.0);
    // Pseudo-legal mobility is explicitly a proxy, not legal move count;
    // en-passant is omitted when constructing opposite-side counterfactuals.
    for(int side : {1,-1}){
      Board p=b;p.turn=side;p.ep=-1;
      auto options=pseudo(p);
      const int offset=side==1?0:1;
      v[32+offset]=options.size();
      int captures=0;
      for(const auto&m:options)if(p.b[m.t]!='.')captures++;
      v[34+offset]=captures;
      v[36+offset]=check(b,side)?1.0:0.0;
      int hanging=0,attackedPieces=0,queenThreat=0,rookThreat=0;
      for(int i=0;i<128;i++)if(inside(i)&&col(b.b[i])==side){
        char lower=char(std::tolower(static_cast<unsigned char>(b.b[i])));
        if(lower=='k')continue;
        if(attacked(b,i,-side)){
          attackedPieces++;
          if(!attacked(b,i,side))hanging++;
          if(lower=='q')queenThreat++;
          if(lower=='r')rookThreat++;
        }
      }
      v[38+offset]=hanging;v[40+offset]=attackedPieces;
      v[42+offset]=queenThreat;v[44+offset]=rookThreat;
      const int king=kingAt(b,side);
      for(int d: ::king){int t=king+d;if(inside(t)&&attacked(b,t,-side))v[46+offset]++;}
    }
    return v;
}
