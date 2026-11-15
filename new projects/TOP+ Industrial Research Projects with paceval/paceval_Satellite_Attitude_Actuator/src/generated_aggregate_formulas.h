// Research graph manifest, actual remote paceval MCP 4.26 successful registration.
#pragma once
#include <cstddef>
static const char* sat_agg_variable_list = R"pv(mtx mty mtz mhx mhy mhz mwx1 mwy1 mwz1 mwx2 mwy2 mwz2 sx1 sy1 sz1 sx2 sy2 sz2)pv";
static constexpr size_t sat_agg_variable_count = 18;
static const ModelGraph sat_agg_graphs[] = {
    {R"pv(joint_guard_v1)pv", R"pv(((sx1>=0) AND ((sy1>=0) AND (sz1>=0))))pv", R"pv(0/1)pv"},
    {R"pv(joint_guard_v2)pv", R"pv(((sx2>=0) AND ((sy2>=0) AND (sz2>=0))))pv", R"pv(0/1)pv"},
    {R"pv(joint_score_v1)pv", R"pv(((sx1 min sy1) min sz1))pv", R"pv(dimensionless)pv"},
    {R"pv(joint_score_v2)pv", R"pv(((sx2 min sy2) min sz2))pv", R"pv(dimensionless)pv"},
    {R"pv(decision_changed)pv", R"pv(((((sx1 min sy1) min sz1)>=0) <> (((sx2 min sy2) min sz2)>=0)))pv", R"pv(0/1)pv"},
    {R"pv(joint_score_delta)pv", R"pv((((sx2 min sy2) min sz2)-((sx1 min sy1) min sz1)))pv", R"pv(dimensionless)pv"},
    {R"pv(smallest_torque_margin)pv", R"pv(((mtx min mty) min mtz))pv", R"pv(N m)pv"},
    {R"pv(smallest_momentum_margin)pv", R"pv(((mhx min mhy) min mhz))pv", R"pv(N m s)pv"},
};
static constexpr size_t sat_agg_graph_count = sizeof(sat_agg_graphs)/sizeof(sat_agg_graphs[0]);
