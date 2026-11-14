#!/usr/bin/env python3
"""Rebuild the C++ declaration header from the versioned formula manifest."""
from pathlib import Path
import json
p=Path(__file__).resolve().parent
r=json.loads((p/'formula_manifest.json').read_text())
s=['// Generated from formula_manifest.json; original SDK executes all production mathematics.','#pragma once','#include <array>','#include <cstddef>','struct GraphFormula {const char* id;const char* expression;};']
for typ in ('edge','network'):
    vars=r['groups'][typ]['variables']
    gs=r['groups'][typ]['graphs']
    s.append('static constexpr const char* '+typ+'_variables='+json.dumps(' '.join(vars))+';')
    s.append('static constexpr size_t '+typ+'_N='+str(len(vars))+';')
    s.append('static constexpr std::array<GraphFormula,'+str(len(gs))+'> '+typ+'_graphs {{')
    for g in gs:s.append('  GraphFormula{'+json.dumps(g['id'])+','+json.dumps(g['formula'])+'},')
    s.append('}};')
(p/'generated_formulas.h').write_text('\n'.join(s)+'\n')
