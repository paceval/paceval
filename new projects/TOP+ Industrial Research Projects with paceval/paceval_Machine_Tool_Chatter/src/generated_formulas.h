// WP22 reusable mathematical formula registry. Tested on remote paceval MCP 4.26.
// The local original-SDK reproduction path has not been linked or executed.
#pragma once
#include <array>
#include <cstddef>
struct GraphFormula {const char* id;const char* expression;};
static constexpr const char* variable_list="w mone kone cone mtwo ktwo ctwo alpha Ks depth teeth lobe";
static constexpr size_t variable_count=12;
static constexpr std::array<GraphFormula,23> model_graphs {{
 GraphFormula{"frf_real_v1","((kone-mone*w*w)/((kone-mone*w*w)^2+(cone*w)^2))"},
 GraphFormula{"frf_imag_v1","(-(cone*w)/((kone-mone*w*w)^2+(cone*w)^2))"},
 GraphFormula{"amplitude_v1","sqrt(((kone-mone*w*w)/((kone-mone*w*w)^2+(cone*w)^2))^2+(-(cone*w)/((kone-mone*w*w)^2+(cone*w)^2))^2)"},
 GraphFormula{"critical_depth_v1","(-1/(2*Ks*((kone-mone*w*w)/((kone-mone*w*w)^2+(cone*w)^2))))"},
 GraphFormula{"phase_v1","(pi+2*atan((-(cone*w)/((kone-mone*w*w)^2+(cone*w)^2))/((kone-mone*w*w)/((kone-mone*w*w)^2+(cone*w)^2))))"},
 GraphFormula{"boundary_rpm_v1","(60*w/(teeth*((pi+2*atan((-(cone*w)/((kone-mone*w*w)^2+(cone*w)^2))/((kone-mone*w*w)/((kone-mone*w*w)^2+(cone*w)^2))))+2*pi*lobe)))"},
 GraphFormula{"depth_margin_v1","((-1/(2*Ks*((kone-mone*w*w)/((kone-mone*w*w)^2+(cone*w)^2))))-depth)"},
 GraphFormula{"screen_guard_v1","((((kone-mone*w*w)/((kone-mone*w*w)^2+(cone*w)^2))<0) AND ((-1/(2*Ks*((kone-mone*w*w)/((kone-mone*w*w)^2+(cone*w)^2))))>=depth))"},
 GraphFormula{"frf_real_v2","(((kone-mone*w*w)/((kone-mone*w*w)^2+(cone*w)^2))+alpha*(ktwo-mtwo*w*w)/((ktwo-mtwo*w*w)^2+(ctwo*w)^2))"},
 GraphFormula{"frf_imag_v2","((-(cone*w)/((kone-mone*w*w)^2+(cone*w)^2))-alpha*(ctwo*w)/((ktwo-mtwo*w*w)^2+(ctwo*w)^2))"},
 GraphFormula{"amplitude_v2","sqrt((((kone-mone*w*w)/((kone-mone*w*w)^2+(cone*w)^2))+alpha*(ktwo-mtwo*w*w)/((ktwo-mtwo*w*w)^2+(ctwo*w)^2))^2+((-(cone*w)/((kone-mone*w*w)^2+(cone*w)^2))-alpha*(ctwo*w)/((ktwo-mtwo*w*w)^2+(ctwo*w)^2))^2)"},
 GraphFormula{"critical_depth_v2","(-1/(2*Ks*(((kone-mone*w*w)/((kone-mone*w*w)^2+(cone*w)^2))+alpha*(ktwo-mtwo*w*w)/((ktwo-mtwo*w*w)^2+(ctwo*w)^2))))"},
 GraphFormula{"phase_v2","(pi+2*atan(((-(cone*w)/((kone-mone*w*w)^2+(cone*w)^2))-alpha*(ctwo*w)/((ktwo-mtwo*w*w)^2+(ctwo*w)^2))/(((kone-mone*w*w)/((kone-mone*w*w)^2+(cone*w)^2))+alpha*(ktwo-mtwo*w*w)/((ktwo-mtwo*w*w)^2+(ctwo*w)^2))))"},
 GraphFormula{"boundary_rpm_v2","(60*w/(teeth*((pi+2*atan(((-(cone*w)/((kone-mone*w*w)^2+(cone*w)^2))-alpha*(ctwo*w)/((ktwo-mtwo*w*w)^2+(ctwo*w)^2))/(((kone-mone*w*w)/((kone-mone*w*w)^2+(cone*w)^2))+alpha*(ktwo-mtwo*w*w)/((ktwo-mtwo*w*w)^2+(ctwo*w)^2))))+2*pi*lobe)))"},
 GraphFormula{"depth_margin_v2","((-1/(2*Ks*(((kone-mone*w*w)/((kone-mone*w*w)^2+(cone*w)^2))+alpha*(ktwo-mtwo*w*w)/((ktwo-mtwo*w*w)^2+(ctwo*w)^2))))-depth)"},
 GraphFormula{"screen_guard_v2","(((((kone-mone*w*w)/((kone-mone*w*w)^2+(cone*w)^2))+alpha*(ktwo-mtwo*w*w)/((ktwo-mtwo*w*w)^2+(ctwo*w)^2))<0) AND ((-1/(2*Ks*(((kone-mone*w*w)/((kone-mone*w*w)^2+(cone*w)^2))+alpha*(ktwo-mtwo*w*w)/((ktwo-mtwo*w*w)^2+(ctwo*w)^2))))>=depth))"},
 GraphFormula{"critical_depth_delta","((-1/(2*Ks*(((kone-mone*w*w)/((kone-mone*w*w)^2+(cone*w)^2))+alpha*(ktwo-mtwo*w*w)/((ktwo-mtwo*w*w)^2+(ctwo*w)^2))))-(-1/(2*Ks*((kone-mone*w*w)/((kone-mone*w*w)^2+(cone*w)^2)))))"},
 GraphFormula{"critical_depth_sensitivity_Ks_v2","(-(-1/(2*Ks*(((kone-mone*w*w)/((kone-mone*w*w)^2+(cone*w)^2))+alpha*(ktwo-mtwo*w*w)/((ktwo-mtwo*w*w)^2+(ctwo*w)^2))))/Ks)"},
 GraphFormula{"relative_margin_v2","(((-1/(2*Ks*(((kone-mone*w*w)/((kone-mone*w*w)^2+(cone*w)^2))+alpha*(ktwo-mtwo*w*w)/((ktwo-mtwo*w*w)^2+(ctwo*w)^2))))-depth)/(-1/(2*Ks*(((kone-mone*w*w)/((kone-mone*w*w)^2+(cone*w)^2))+alpha*(ktwo-mtwo*w*w)/((ktwo-mtwo*w*w)^2+(ctwo*w)^2)))))"},
 GraphFormula{"regenerative_residual_real_v2","(1+Ks*(-1/(2*Ks*(((kone-mone*w*w)/((kone-mone*w*w)^2+(cone*w)^2))+alpha*(ktwo-mtwo*w*w)/((ktwo-mtwo*w*w)^2+(ctwo*w)^2))))*((((kone-mone*w*w)/((kone-mone*w*w)^2+(cone*w)^2))+alpha*(ktwo-mtwo*w*w)/((ktwo-mtwo*w*w)^2+(ctwo*w)^2))*(1-cos(((pi+2*atan(((-(cone*w)/((kone-mone*w*w)^2+(cone*w)^2))-alpha*(ctwo*w)/((ktwo-mtwo*w*w)^2+(ctwo*w)^2))/(((kone-mone*w*w)/((kone-mone*w*w)^2+(cone*w)^2))+alpha*(ktwo-mtwo*w*w)/((ktwo-mtwo*w*w)^2+(ctwo*w)^2))))+2*pi*lobe)))-((-(cone*w)/((kone-mone*w*w)^2+(cone*w)^2))-alpha*(ctwo*w)/((ktwo-mtwo*w*w)^2+(ctwo*w)^2))*sin(((pi+2*atan(((-(cone*w)/((kone-mone*w*w)^2+(cone*w)^2))-alpha*(ctwo*w)/((ktwo-mtwo*w*w)^2+(ctwo*w)^2))/(((kone-mone*w*w)/((kone-mone*w*w)^2+(cone*w)^2))+alpha*(ktwo-mtwo*w*w)/((ktwo-mtwo*w*w)^2+(ctwo*w)^2))))+2*pi*lobe))))"},
 GraphFormula{"regenerative_residual_imag_v2","(Ks*(-1/(2*Ks*(((kone-mone*w*w)/((kone-mone*w*w)^2+(cone*w)^2))+alpha*(ktwo-mtwo*w*w)/((ktwo-mtwo*w*w)^2+(ctwo*w)^2))))*(((-(cone*w)/((kone-mone*w*w)^2+(cone*w)^2))-alpha*(ctwo*w)/((ktwo-mtwo*w*w)^2+(ctwo*w)^2))*(1-cos(((pi+2*atan(((-(cone*w)/((kone-mone*w*w)^2+(cone*w)^2))-alpha*(ctwo*w)/((ktwo-mtwo*w*w)^2+(ctwo*w)^2))/(((kone-mone*w*w)/((kone-mone*w*w)^2+(cone*w)^2))+alpha*(ktwo-mtwo*w*w)/((ktwo-mtwo*w*w)^2+(ctwo*w)^2))))+2*pi*lobe)))+(((kone-mone*w*w)/((kone-mone*w*w)^2+(cone*w)^2))+alpha*(ktwo-mtwo*w*w)/((ktwo-mtwo*w*w)^2+(ctwo*w)^2))*sin(((pi+2*atan(((-(cone*w)/((kone-mone*w*w)^2+(cone*w)^2))-alpha*(ctwo*w)/((ktwo-mtwo*w*w)^2+(ctwo*w)^2))/(((kone-mone*w*w)/((kone-mone*w*w)^2+(cone*w)^2))+alpha*(ktwo-mtwo*w*w)/((ktwo-mtwo*w*w)^2+(ctwo*w)^2))))+2*pi*lobe))))"},
 GraphFormula{"natural_frequency_rad_s","sqrt(kone/mone)"},
 GraphFormula{"damping_ratio_v1","cone/(2*sqrt(kone*mone))"},
}};
