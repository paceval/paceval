// WP20: generated formula registry; actual expressions accepted by paceval MCP 4.26.
// Local SDK execution remains a separate unexecuted reproduction path until tested.
#pragma once
#include <array>
#include <cstddef>
struct GraphFormula {const char* id; const char* expression;};
static constexpr const char* variable_list="Q T rA LA rB LB K n E Rg Tref etaZero tauStar MachineMax CavityReq ShearMax Tmin Tmax Pheater Theat Pinject Tinject Emax";
static constexpr size_t variable_count=23;
static constexpr std::array<GraphFormula,31> model_graphs {{
 GraphFormula{"gammaA","(4*Q/(pi*rA^3))"},
 GraphFormula{"gammaB","(4*Q/(pi*rB^3))"},
 GraphFormula{"etaApparentA_v1","(K*(4*Q/(pi*rA^3))^(n-1)*exp(E/Rg*(1/T-1/Tref)))"},
 GraphFormula{"etaApparentB_v1","(K*(4*Q/(pi*rB^3))^(n-1)*exp(E/Rg*(1/T-1/Tref)))"},
 GraphFormula{"pressureA_v1","(8*(K*(4*Q/(pi*rA^3))^(n-1)*exp(E/Rg*(1/T-1/Tref)))*LA*Q/(pi*rA^4))"},
 GraphFormula{"pressureB_v1","(8*(K*(4*Q/(pi*rB^3))^(n-1)*exp(E/Rg*(1/T-1/Tref)))*LB*Q/(pi*rB^4))"},
 GraphFormula{"pressureTotal_v1","((8*(K*(4*Q/(pi*rA^3))^(n-1)*exp(E/Rg*(1/T-1/Tref)))*LA*Q/(pi*rA^4))+(8*(K*(4*Q/(pi*rB^3))^(n-1)*exp(E/Rg*(1/T-1/Tref)))*LB*Q/(pi*rB^4)))"},
 GraphFormula{"gammaWallA_v2","((4*Q/(pi*rA^3))*((3*n+1)/(4*n)))"},
 GraphFormula{"gammaWallB_v2","((4*Q/(pi*rB^3))*((3*n+1)/(4*n)))"},
 GraphFormula{"pressureA_v2","(2*K*exp(E/Rg*(1/T-1/Tref))*LA/rA*((4*Q/(pi*rA^3))*((3*n+1)/(4*n)))^n)"},
 GraphFormula{"pressureB_v2","(2*K*exp(E/Rg*(1/T-1/Tref))*LB/rB*((4*Q/(pi*rB^3))*((3*n+1)/(4*n)))^n)"},
 GraphFormula{"pressureTotal_v2","((2*K*exp(E/Rg*(1/T-1/Tref))*LA/rA*((4*Q/(pi*rA^3))*((3*n+1)/(4*n)))^n)+(2*K*exp(E/Rg*(1/T-1/Tref))*LB/rB*((4*Q/(pi*rB^3))*((3*n+1)/(4*n)))^n))"},
 GraphFormula{"pressureMargin_v1","(MachineMax-CavityReq-((8*(K*(4*Q/(pi*rA^3))^(n-1)*exp(E/Rg*(1/T-1/Tref)))*LA*Q/(pi*rA^4))+(8*(K*(4*Q/(pi*rB^3))^(n-1)*exp(E/Rg*(1/T-1/Tref)))*LB*Q/(pi*rB^4))))"},
 GraphFormula{"pressureMargin_v2","(MachineMax-CavityReq-((2*K*exp(E/Rg*(1/T-1/Tref))*LA/rA*((4*Q/(pi*rA^3))*((3*n+1)/(4*n)))^n)+(2*K*exp(E/Rg*(1/T-1/Tref))*LB/rB*((4*Q/(pi*rB^3))*((3*n+1)/(4*n)))^n)))"},
 GraphFormula{"temperatureMargin","((T-Tmin) min (Tmax-T))"},
 GraphFormula{"shearMargin_v1","(ShearMax-((4*Q/(pi*rA^3)) max (4*Q/(pi*rB^3))))"},
 GraphFormula{"shearMargin_v2","(ShearMax-(((4*Q/(pi*rA^3))*((3*n+1)/(4*n))) max ((4*Q/(pi*rB^3))*((3*n+1)/(4*n)))))"},
 GraphFormula{"cycleEnergy","(Pheater*Theat+Pinject*Tinject)"},
 GraphFormula{"energyMargin","(Emax-(Pheater*Theat+Pinject*Tinject))"},
 GraphFormula{"guard_v1","((((((MachineMax-CavityReq-((8*(K*(4*Q/(pi*rA^3))^(n-1)*exp(E/Rg*(1/T-1/Tref)))*LA*Q/(pi*rA^4))+(8*(K*(4*Q/(pi*rB^3))^(n-1)*exp(E/Rg*(1/T-1/Tref)))*LB*Q/(pi*rB^4))))>=0) AND ((ShearMax-((4*Q/(pi*rA^3)) max (4*Q/(pi*rB^3))))>=0)) AND (((T-Tmin) min (Tmax-T))>=0)) AND ((Emax-(Pheater*Theat+Pinject*Tinject))>=0)))"},
 GraphFormula{"guard_v2","((((((MachineMax-CavityReq-((2*K*exp(E/Rg*(1/T-1/Tref))*LA/rA*((4*Q/(pi*rA^3))*((3*n+1)/(4*n)))^n)+(2*K*exp(E/Rg*(1/T-1/Tref))*LB/rB*((4*Q/(pi*rB^3))*((3*n+1)/(4*n)))^n)))>=0) AND ((ShearMax-(((4*Q/(pi*rA^3))*((3*n+1)/(4*n))) max ((4*Q/(pi*rB^3))*((3*n+1)/(4*n)))))>=0)) AND (((T-Tmin) min (Tmax-T))>=0)) AND ((Emax-(Pheater*Theat+Pinject*Tinject))>=0)))"},
 GraphFormula{"score_v1","((((MachineMax-CavityReq-((8*(K*(4*Q/(pi*rA^3))^(n-1)*exp(E/Rg*(1/T-1/Tref)))*LA*Q/(pi*rA^4))+(8*(K*(4*Q/(pi*rB^3))^(n-1)*exp(E/Rg*(1/T-1/Tref)))*LB*Q/(pi*rB^4))))/MachineMax) min ((ShearMax-((4*Q/(pi*rA^3)) max (4*Q/(pi*rB^3))))/ShearMax)) min ((((T-Tmin) min (Tmax-T))/(Tmax-Tmin)) min ((Emax-(Pheater*Theat+Pinject*Tinject))/Emax)))"},
 GraphFormula{"score_v2","((((MachineMax-CavityReq-((2*K*exp(E/Rg*(1/T-1/Tref))*LA/rA*((4*Q/(pi*rA^3))*((3*n+1)/(4*n)))^n)+(2*K*exp(E/Rg*(1/T-1/Tref))*LB/rB*((4*Q/(pi*rB^3))*((3*n+1)/(4*n)))^n)))/MachineMax) min ((ShearMax-(((4*Q/(pi*rA^3))*((3*n+1)/(4*n))) max ((4*Q/(pi*rB^3))*((3*n+1)/(4*n)))))/ShearMax)) min ((((T-Tmin) min (Tmax-T))/(Tmax-Tmin)) min ((Emax-(Pheater*Theat+Pinject*Tinject))/Emax)))"},
 GraphFormula{"pressureDelta_v2_v1","(((2*K*exp(E/Rg*(1/T-1/Tref))*LA/rA*((4*Q/(pi*rA^3))*((3*n+1)/(4*n)))^n)+(2*K*exp(E/Rg*(1/T-1/Tref))*LB/rB*((4*Q/(pi*rB^3))*((3*n+1)/(4*n)))^n))-((8*(K*(4*Q/(pi*rA^3))^(n-1)*exp(E/Rg*(1/T-1/Tref)))*LA*Q/(pi*rA^4))+(8*(K*(4*Q/(pi*rB^3))^(n-1)*exp(E/Rg*(1/T-1/Tref)))*LB*Q/(pi*rB^4))))"},
 GraphFormula{"sensitivityPressureQ_v2","(n*((2*K*exp(E/Rg*(1/T-1/Tref))*LA/rA*((4*Q/(pi*rA^3))*((3*n+1)/(4*n)))^n)+(2*K*exp(E/Rg*(1/T-1/Tref))*LB/rB*((4*Q/(pi*rB^3))*((3*n+1)/(4*n)))^n))/Q)"},
 GraphFormula{"sensitivityPressureT_v2","(-E/(Rg*T*T)*((2*K*exp(E/Rg*(1/T-1/Tref))*LA/rA*((4*Q/(pi*rA^3))*((3*n+1)/(4*n)))^n)+(2*K*exp(E/Rg*(1/T-1/Tref))*LB/rB*((4*Q/(pi*rB^3))*((3*n+1)/(4*n)))^n)))"},
 GraphFormula{"crossEtaA_diagnostic","((etaZero*exp(E/Rg*(1/T-1/Tref)))/(1+((etaZero*exp(E/Rg*(1/T-1/Tref)))*(4*Q/(pi*rA^3))/tauStar)^(1-n)))"},
 GraphFormula{"crossEtaB_diagnostic","((etaZero*exp(E/Rg*(1/T-1/Tref)))/(1+((etaZero*exp(E/Rg*(1/T-1/Tref)))*(4*Q/(pi*rB^3))/tauStar)^(1-n)))"},
 GraphFormula{"pressureCrossProxy_diagnostic","(8*((etaZero*exp(E/Rg*(1/T-1/Tref)))/(1+((etaZero*exp(E/Rg*(1/T-1/Tref)))*(4*Q/(pi*rA^3))/tauStar)^(1-n)))*LA*Q/(pi*rA^4)+8*((etaZero*exp(E/Rg*(1/T-1/Tref)))/(1+((etaZero*exp(E/Rg*(1/T-1/Tref)))*(4*Q/(pi*rB^3))/tauStar)^(1-n)))*LB*Q/(pi*rB^4))"},
 GraphFormula{"crossVsPowerEtaA_ratio","(((etaZero*exp(E/Rg*(1/T-1/Tref)))/(1+((etaZero*exp(E/Rg*(1/T-1/Tref)))*(4*Q/(pi*rA^3))/tauStar)^(1-n)))/(K*(4*Q/(pi*rA^3))^(n-1)*exp(E/Rg*(1/T-1/Tref))))"},
 GraphFormula{"NewtonianLimitingPressure","(8*K*exp(E/Rg*(1/T-1/Tref))*Q/pi*(LA/rA^4+LB/rB^4))"},
}};
