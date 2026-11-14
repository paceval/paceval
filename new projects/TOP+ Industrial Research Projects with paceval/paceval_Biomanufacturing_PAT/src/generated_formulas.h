// Generated from formula_manifest.json. Original SDK executes all productive model mathematics.
#pragma once
#include <array>
struct FormulaItem {const char* id;const char* formula;};
static constexpr std::array<FormulaItem,24> kGraphs{{
  FormulaItem{"mu_v1","(umax*S/(Ks+S)*DO/(Ko+DO))"},
  FormulaItem{"mu_v2","(umax*S/(Ks+S+S*S/Ki)*DO/(Ko+DO))"},
  FormulaItem{"substrate_consumption_v1","((umax*S/(Ks+S)*DO/(Ko+DO))*X/Yxs)"},
  FormulaItem{"substrate_consumption_v2","((umax*S/(Ks+S+S*S/Ki)*DO/(Ko+DO))*X/Yxs)"},
  FormulaItem{"oxygen_uptake_v1","(qO2*X)"},
  FormulaItem{"oxygen_uptake_v2","((qO2+qG*(umax*S/(Ks+S+S*S/Ki)*DO/(Ko+DO)))*X)"},
  FormulaItem{"oxygen_transfer","(kLa*(DOstar-DO))"},
  FormulaItem{"dDO_v1","((kLa*(DOstar-DO))-(qO2*X)-(F/V)*DO)"},
  FormulaItem{"dDO_v2","((kLa*(DOstar-DO))-((qO2+qG*(umax*S/(Ks+S+S*S/Ki)*DO/(Ko+DO)))*X)-(F/V)*DO)"},
  FormulaItem{"dS_v1","((F/V)*(Sfeed-S)-(umax*S/(Ks+S)*DO/(Ko+DO))*X/Yxs)"},
  FormulaItem{"dS_v2","((F/V)*(Sfeed-S)-(umax*S/(Ks+S+S*S/Ki)*DO/(Ko+DO))*X/Yxs)"},
  FormulaItem{"dX_v1","(((umax*S/(Ks+S)*DO/(Ko+DO))-(F/V))*X)"},
  FormulaItem{"dX_v2","(((umax*S/(Ks+S+S*S/Ki)*DO/(Ko+DO))-(F/V))*X)"},
  FormulaItem{"oxygen_margin_v1","((kLa*(DOstar-DO))-(qO2*X))"},
  FormulaItem{"oxygen_margin_v2","((kLa*(DOstar-DO))-((qO2+qG*(umax*S/(Ks+S+S*S/Ki)*DO/(Ko+DO)))*X))"},
  FormulaItem{"score_v1","((DO-DOmin) min (tau*((kLa*(DOstar-DO))-(qO2*X))))"},
  FormulaItem{"score_v2","((DO-DOmin) min (tau*((kLa*(DOstar-DO))-((qO2+qG*(umax*S/(Ks+S+S*S/Ki)*DO/(Ko+DO)))*X))))"},
  FormulaItem{"guard_v1","(((DO>=DOmin) AND (((kLa*(DOstar-DO))-(qO2*X))>=0)) AND (S>=0))"},
  FormulaItem{"guard_v2","(((DO>=DOmin) AND (((kLa*(DOstar-DO))-((qO2+qG*(umax*S/(Ks+S+S*S/Ki)*DO/(Ko+DO)))*X))>=0)) AND (S>=0))"},
  FormulaItem{"sensitivity_mu_S_v2","(umax*DO/(Ko+DO)*(Ks-S*S/Ki)/((Ks+S+S*S/Ki)*(Ks+S+S*S/Ki)))"},
  FormulaItem{"sensitivity_dDO_kLa","(DOstar-DO)"},
  FormulaItem{"oxygen_capacity_ratio_v2","(((qO2+qG*(umax*S/(Ks+S+S*S/Ki)*DO/(Ko+DO)))*X)/(kLa*(DOstar-DO)))"},
  FormulaItem{"version_growth_delta","((umax*S/(Ks+S+S*S/Ki)*DO/(Ko+DO))-(umax*S/(Ks+S)*DO/(Ko+DO)))"},
  FormulaItem{"minimum_required_kLa_v2","(((qO2+qG*(umax*S/(Ks+S+S*S/Ki)*DO/(Ko+DO)))*X)/(DOstar-DO))"},
}};
