#!/usr/bin/env python3
"""Reproducibly derive the three symbolic FK coordinates from a six-axis chain.

This optional development tool requires SymPy. Compiling/running the committed
C++ project does not require SymPy: generated_formulas.h is checked in.
It is deliberately independent of the native matrix-transform reference.
"""
from pathlib import Path
import sympy as s
q=s.symbols('q1:7'); o=s.symbols('o1:7'); l=s.symbols('l1:7')
R=s.eye(3); pos=s.zeros(3,1)
for i,axis in enumerate('ZYYXYZ'):
    t=q[i]+o[i]; c=s.cos(t); si=s.sin(t)
    if axis=='Z': S=s.Matrix([[c,-si,0],[si,c,0],[0,0,1]])
    if axis=='Y': S=s.Matrix([[c,0,si],[0,1,0],[-si,0,c]])
    if axis=='X': S=s.Matrix([[1,0,0],[0,c,-si],[0,si,c]])
    R=R*S
    vector=s.Matrix([0,0,l[i]]) if i in (0,3) else s.Matrix([l[i],0,0])
    pos += R*vector

coords=[]
for i in range(3):
    expr=s.ccode(s.expand(pos[i])).replace('pow(', 'pow(')
    coords.append(expr)
# Every expression is emitted as standard paceval syntax. No C++ source
# concatenation is needed to modify formulas in the application itself.
lines=['// AUTO-GENERATED: regenerate with python3 generate_formulas.py (SymPy).',
       '// Independent C++ forward kinematics is a separate matrix implementation.',
       '#pragma once', '#include <array>', 'namespace robot_formula {',
       'static constexpr const char* variables = "'+' '.join(str(x) for x in (q+o+l+s.symbols('mx my mz')))+'";',
       'static constexpr unsigned int nvars = 21;',
       'static const std::array<const char*,3> position = {']
for c in coords: lines.append('    R"EXPR('+c+')EXPR",')
lines+=['};','static const std::array<const char*,3> residual = {']
for k,c in enumerate(coords):
    lines.append('    R"EXPR((' + ('mx','my','mz')[k]+' - ('+c+')))EXPR",')
lines+=['};','} // namespace robot_formula','']
path=Path(__file__).with_name('generated_formulas.h')
path.write_text('\n'.join(lines),encoding='utf-8')
print('Generated',path,'coordinate lengths:',list(map(len,coords)))
