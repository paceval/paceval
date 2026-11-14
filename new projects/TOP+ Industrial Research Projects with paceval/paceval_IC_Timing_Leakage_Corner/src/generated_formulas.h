// Generated from formula_manifest.json. Original paceval graph execution required.
#pragma once
#include <array>
struct FormulaItem {const char* id;const char* formula;};
static constexpr std::array<FormulaItem,22> kGraphs{{
 FormulaItem{"delay_v1_ps","(t0+aC*C+aS*S+aT*(T-Tref)+aV*(Vref/V)^p)"},
 FormulaItem{"delay_v2_ps","(t0+aC*C*(Vref/V)^q+aS*S+aT*(T-Tref)+aV*(Vref/V)^p+aCT*C*(T-Tref)+aCS*C*S)"},
 FormulaItem{"leak_v1_nA","(I0*exp(bT*(T-Tref)+bV*(V-Vref)))"},
 FormulaItem{"leak_v2_nA","(I0*exp(bT*(T-Tref)+bV*(V-Vref)+bTT*(T-Tref)*(T-Tref)+bVT*(T-Tref)*(V-Vref)))"},
 FormulaItem{"leak_power_v1_nW","(V*(I0*exp(bT*(T-Tref)+bV*(V-Vref))))"},
 FormulaItem{"leak_power_v2_nW","(V*(I0*exp(bT*(T-Tref)+bV*(V-Vref)+bTT*(T-Tref)*(T-Tref)+bVT*(T-Tref)*(V-Vref))))"},
 FormulaItem{"path_delay_v1_ps","(Ncells*(t0+aC*C+aS*S+aT*(T-Tref)+aV*(Vref/V)^p)+Wire)"},
 FormulaItem{"path_delay_v2_ps","(Ncells*(t0+aC*C*(Vref/V)^q+aS*S+aT*(T-Tref)+aV*(Vref/V)^p+aCT*C*(T-Tref)+aCS*C*S)+Wire)"},
 FormulaItem{"slack_v1_ps","(Treq-Tarr-Wire-Ncells*(t0+aC*C+aS*S+aT*(T-Tref)+aV*(Vref/V)^p))"},
 FormulaItem{"slack_v2_ps","(Treq-Tarr-Wire-Ncells*(t0+aC*C*(Vref/V)^q+aS*S+aT*(T-Tref)+aV*(Vref/V)^p+aCT*C*(T-Tref)+aCS*C*S))"},
 FormulaItem{"leak_margin_v1_nW","(Pcap-(V*(I0*exp(bT*(T-Tref)+bV*(V-Vref)))))"},
 FormulaItem{"leak_margin_v2_nW","(Pcap-(V*(I0*exp(bT*(T-Tref)+bV*(V-Vref)+bTT*(T-Tref)*(T-Tref)+bVT*(T-Tref)*(V-Vref)))))"},
 FormulaItem{"composite_score_v1_ps","(((Treq-Tarr-Wire-Ncells*(t0+aC*C+aS*S+aT*(T-Tref)+aV*(Vref/V)^p))) min (Pscale*(Pcap-(V*(I0*exp(bT*(T-Tref)+bV*(V-Vref)))))))"},
 FormulaItem{"composite_score_v2_ps","(((Treq-Tarr-Wire-Ncells*(t0+aC*C*(Vref/V)^q+aS*S+aT*(T-Tref)+aV*(Vref/V)^p+aCT*C*(T-Tref)+aCS*C*S))) min (Pscale*(Pcap-(V*(I0*exp(bT*(T-Tref)+bV*(V-Vref)+bTT*(T-Tref)*(T-Tref)+bVT*(T-Tref)*(V-Vref)))))))"},
 FormulaItem{"corner_guard_v1","((((Treq-Tarr-Wire-Ncells*(t0+aC*C+aS*S+aT*(T-Tref)+aV*(Vref/V)^p)))>=0) AND (((Pcap-(V*(I0*exp(bT*(T-Tref)+bV*(V-Vref))))))>=0) AND (V>=Vmin) AND (V<=Vmax) AND (T>=Tmin) AND (T<=Tmax))"},
 FormulaItem{"corner_guard_v2","((((Treq-Tarr-Wire-Ncells*(t0+aC*C*(Vref/V)^q+aS*S+aT*(T-Tref)+aV*(Vref/V)^p+aCT*C*(T-Tref)+aCS*C*S)))>=0) AND (((Pcap-(V*(I0*exp(bT*(T-Tref)+bV*(V-Vref)+bTT*(T-Tref)*(T-Tref)+bVT*(T-Tref)*(V-Vref))))))>=0) AND (V>=Vmin) AND (V<=Vmax) AND (T>=Tmin) AND (T<=Tmax))"},
 FormulaItem{"delay_sensitivity_voltage_v2","(-aC*C*q*(Vref/V)^q/V-aV*p*(Vref/V)^p/V)"},
 FormulaItem{"delay_sensitivity_temp_v2","(aT+aCT*C)"},
 FormulaItem{"leak_sensitivity_temp_v2","((I0*exp(bT*(T-Tref)+bV*(V-Vref)+bTT*(T-Tref)*(T-Tref)+bVT*(T-Tref)*(V-Vref)))*(bT+2*bTT*(T-Tref)+bVT*(V-Vref)))"},
 FormulaItem{"model_delta_delay_ps","((t0+aC*C*(Vref/V)^q+aS*S+aT*(T-Tref)+aV*(Vref/V)^p+aCT*C*(T-Tref)+aCS*C*S)-(t0+aC*C+aS*S+aT*(T-Tref)+aV*(Vref/V)^p))"},
 FormulaItem{"model_delta_power_nW","((V*(I0*exp(bT*(T-Tref)+bV*(V-Vref)+bTT*(T-Tref)*(T-Tref)+bVT*(T-Tref)*(V-Vref))))-(V*(I0*exp(bT*(T-Tref)+bV*(V-Vref)))))"},
 FormulaItem{"leakage_power_fraction_v2","((V*(I0*exp(bT*(T-Tref)+bV*(V-Vref)+bTT*(T-Tref)*(T-Tref)+bVT*(T-Tref)*(V-Vref))))/Pcap)"},
}};
