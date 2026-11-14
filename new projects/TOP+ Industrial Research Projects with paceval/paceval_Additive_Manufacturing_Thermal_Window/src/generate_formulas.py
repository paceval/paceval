#!/usr/bin/env python3
"""Regenerate the pure C++ declaration table from JSON without changing any SDK source."""
from pathlib import Path
import json,sys
root=Path(sys.argv[1]) if len(sys.argv)>1 else Path(__file__).resolve().parents[1]
m=json.loads((root/'src/formula_manifest.json').read_text(encoding='utf-8'))
f=m['graph_formulas']
out=['// Generated from the versioned formula manifest. DO NOT alter by hand.','// Core mathematical expressions are evaluated by original paceval graphs.','#pragma once','#include <array>','struct GraphSpec { const char* id; const char* formula; };',f'static constexpr std::array<GraphSpec,{len(f)}> kGraphs{{{{']
for name,expression in f.items():
    assert '"' not in name+expression and '\\' not in expression
    out.append(f'  {{"{name}","{expression}"}},')
out.extend(['}};'])
(root/'src/generated_formulas.h').write_text('\n'.join(out)+'\n',encoding='utf-8')
print('Generated',len(f),'formula registrations')
