#!/usr/bin/env python3
"""Executable RecordFormula-style dynamic operator tracing on a frozen MLP.
Based conceptually on paceval's Julia/Flux RecordFormula research. This small
Python tracer supports only +, *, and logistic. It is not a general ONNX or Julia exporter.
"""
from pathlib import Path
from dataclasses import dataclass
import csv, math, json
P=Path(__file__).resolve().parents[1]
@dataclass(frozen=True)
class RecordFormula:
    val:float
    formula:str
    def __add__(self,other):
        z=other if isinstance(other,RecordFormula) else RecordFormula(float(other),format(float(other),'.17g'))
        return RecordFormula(self.val+z.val,'('+self.formula+'+'+z.formula+')')
    __radd__=__add__
    def __mul__(self,other):
        z=other if isinstance(other,RecordFormula) else RecordFormula(float(other),format(float(other),'.17g'))
        return RecordFormula(self.val*z.val,'('+self.formula+'*'+z.formula+')')
    __rmul__=__mul__

def sigmoid(z):
    v=1/(1+math.exp(-z.val)) if z.val>=0 else math.exp(z.val)/(1+math.exp(z.val))
    return RecordFormula(v,'(1/(1+exp(-('+z.formula+'))))')

def run():
    ps=list(csv.DictReader((P/'examples/frozen_network_weights.csv').open()))
    dat=next(csv.DictReader((P/'examples/synthetic_bearing_features.csv').open()))
    norm=list(csv.DictReader((P/'examples/normalization.csv').open()))
    registry={}
    for vers in ['v1','v2']:
        x=[RecordFormula((float(dat[f])-float(norm[i]['mean']))/float(norm[i]['std']),'x'+str(i)) for i,f in enumerate(list(dat)[-8:])]
        graph_lines=[]
        bounded_lines=[]
        layer=x
        bounded=x
        for n,input_width in [(8,8),(4,8),(1,4)]:
            l={8:1,4:2,1:3}[n]
            outputs=[]
            bounded_outputs=[]
            for j in range(n):
                entries=[r for r in ps if r['version']==vers and int(r['layer'])==l and int(r['neuron'])==j]
                w={int(r['input']):float(r['weight']) for r in entries}
                z=RecordFormula(w[-1],format(w[-1],'.17g'))
                for i in range(input_width):z=z+layer[i]*w[i]
                outputs.append(sigmoid(z))
                zb=RecordFormula(w[-1],format(w[-1],'.17g'))
                for i in range(input_width):zb=zb+bounded[i]*w[i]
                bounded_outputs.append(RecordFormula(sigmoid(zb).val,('h' if l==1 else 'b' if l==2 else 'y')+str(j)))
                bounded_lines.append({'layer':l,'node':j,'formula_with_intermediate_variables':sigmoid(zb).formula})
                graph_lines.append({'layer':l,'node':j,'fully_expanded_formula':sigmoid(z).formula,'value_at_probe':sigmoid(z).val})
            layer=outputs
            bounded=bounded_outputs
        net=layer[0]
        native_csv=next(r for r in csv.DictReader((P/'results/inference_results.csv').open()) if r['model_version']==vers)
        discrepancy=abs(net.val-float(native_csv['paceval_layered_score']))
        assert discrepancy<2e-12,(vers,discrepancy)
        registry[vers]={'full_expression_character_count':len(net.formula),'probe_score':net.val,'paceval_comparison_error':discrepancy,'fully_expanded_layer_expressions':graph_lines,'intermediate_variable_formulas':bounded_lines}
    (P/'results/recordformula_trace.json').write_text(json.dumps(registry,indent=2)+'\n')
    print('PASS dynamic scalar operator trace:',{v:(x['full_expression_character_count'],x['paceval_comparison_error']) for v,x in registry.items()})
if __name__=='__main__':run()
