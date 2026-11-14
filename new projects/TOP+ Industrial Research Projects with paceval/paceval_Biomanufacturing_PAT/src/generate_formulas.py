#!/usr/bin/env python3
import json,pathlib
p=pathlib.Path(__file__).parent
r=json.loads((p/'formula_manifest.json').read_text())
s='// Generated from formula_manifest.json. Original SDK executes all productive model mathematics.\n#pragma once\n#include <array>\nstruct FormulaItem {const char* id;const char* formula;};\nstatic constexpr std::array<FormulaItem,'+str(len(r['graphs']))+'> kGraphs{{\n'
for x in r['graphs']:s+='  FormulaItem{"'+x['id']+'","'+x['formula']+'"},\n'
s+='}};\n'
(p/'generated_formulas.h').write_text(s)
