#!/usr/bin/env python3
"""Independent Python chess-tree valuation and move-transition audit.

Uses independent board parsing/transition routines, not the C++/paceval formula
strings. Checks ALL stored parent-child links and minimax reductions. A separate
Decimal(90) path checks sampled leaf scores and FEN feature extraction.
"""
from pathlib import Path
import csv, json, math, random, sys
from decimal import Decimal, getcontext
getcontext().prec = 90
DEFAULT_START='rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1'

def parse(fen):
    pieces,turn,rights,ep,half,full=fen.split()
    rows=pieces.split('/')
    if len(rows)!=8:raise AssertionError('bad ranks')
    board={}
    for rr,row in enumerate(rows):
        f=0
        for c in row:
            if c.isdigit():f+=int(c)
            else:board[f'{chr(97+f)}{8-rr}']=c;f+=1
        assert f==8
    return board,turn,rights,ep,int(half),int(full)

def encode(s):
    b,turn,rights,ep,half,full=s
    out=[]
    for r in range(8,0,-1):
        row='';empty=0
        for f in 'abcdefgh':
            p=b.get(f+str(r))
            if p is None:empty+=1
            else:
                if empty:row+=str(empty);empty=0
                row+=p
        if empty:row+=str(empty)
        out.append(row)
    return '/'.join(out)+f' {turn} {rights} {ep} {half} {full}'

def move(s,uc):
    b,turn,rights,ep,half,full=s
    b=b.copy();fr,to=uc[:2],uc[2:4]
    p=b.pop(fr);taken=b.pop(to,None)
    if p.lower()=='p' and to==ep and fr[0]!=to[0] and taken is None:
        taken=b.pop(to[0]+fr[1]);assert taken.lower()=='p'
    if p.lower()=='k' and abs(ord(to[0])-ord(fr[0]))==2:
        if to[0]=='g':rook_fr='h'+fr[1];rook_to='f'+fr[1]
        else:rook_fr='a'+fr[1];rook_to='d'+fr[1]
        b[rook_to]=b.pop(rook_fr)
    if len(uc)>4:
        assert p.lower()=='p' and uc[4] in 'qrbn'
        p=uc[4].upper() if turn=='w' else uc[4]
    b[to]=p
    if p=='K':rights=rights.replace('K','').replace('Q','')
    elif p=='k':rights=rights.replace('k','').replace('q','')
    rights=rights.replace({'a1':'Q','h1':'K','a8':'q','h8':'k'}.get(fr),'') if fr in ['a1','h1','a8','h8'] else rights
    rights=rights.replace({'a1':'Q','h1':'K','a8':'q','h8':'k'}.get(to),'') if to in ['a1','h1','a8','h8'] else rights
    rights=''.join(v for v in 'KQkq' if v in rights) or '-'
    newep='-'
    if p.lower()=='p' and abs(int(to[1])-int(fr[1]))==2:newep=fr[0]+str((int(fr[1])+int(to[1]))//2)
    half=0 if p.lower()=='p' or taken is not None else half+1
    return b, 'b' if turn=='w' else 'w', rights, newep, half, full+(turn=='b')

def native_features(fen):
    b,turn,rights,ep,half,full=parse(fen)
    v={p:0 for p in 'PNBRQpnbrq'}
    wc=bc=wd=bd=wa=ba=wk=bk=0
    for sq,p in b.items():
        if p in v:v[p]+=1
        r=int(sq[1]);file=ord(sq[0])-97
        if 2<=file<=5 and 3<=r<=6:
            if p.isupper():wc+=1
            else:bc+=1
        if p in 'NB' and r>1:wd+=1
        if p in 'nb' and r<8:bd+=1
        if p=='P':wa+=r-2
        if p=='p':ba+=7-r
        if p=='K':wk=int(sq[0] in 'cg')
        if p=='k':bk=int(sq[0] in 'cg')
    mat=sum(w*(v[white]-v[black]) for w,white,black in [(100,'P','p'),(320,'N','n'),(330,'B','b'),(500,'R','r'),(900,'Q','q')])
    extra=13*(wc-bc)+17*(wd-bd)+3*(wa-ba)+18*(wk-bk)
    return Decimal(mat),Decimal(mat+extra)

def verify(root):
    root=Path(root)
    with (root/'decision_nodes.csv').open(newline='') as f:
        rows=list(csv.DictReader(f))
    ev=json.loads((root/'execution_evidence.json').read_text())
    assert rows and len(rows)==ev['node_count']
    dep=ev['depth'];leaves=0;values=[(float(r['value_v1']),float(r['value_v2'])) for r in rows]
    children=[[] for x in rows]
    for i,r in enumerate(rows):
        assert int(r['id'])==i
        p=int(r['parent'])
        if i==0:assert p==-1 and r['uci']=='ROOT'
        else:
            assert p<i and int(r['ply'])==int(rows[p]['ply'])+1
            children[p].append(i)
        if not int(r['child_count']):leaves+=1
        else:assert int(r['ply'])<dep
        assert float(r['value_v1'])==float(r['value_v1'])
    assert leaves==ev['leaf_count']
    assert all(len(children[i])==int(r['child_count']) for i,r in enumerate(rows))
    # Check all explicit transitions, including castling/EP/clocks after source FEN.
    transitions=0
    for i in range(1,len(rows)):
        r=rows[i];par=rows[int(r['parent'])]
        assert encode(move(parse(par['fen']),r['uci']))==r['fen'],f"FEN child mismatch id={i}"
        transitions+=1
    # Completely independent Python minimax reduction with no paceval calls.
    reductions=0
    for i in range(len(rows)-1,-1,-1):
        if not children[i]:continue
        r=rows[i]
        cv=[values[j] for j in children[i]]
        expected=tuple((max(v[k] for v in cv) if r['side']=='w' else min(v[k] for v in cv)) for k in [0,1])
        for got,want in zip(values[i],expected):assert abs(got-want)<=1e-8*(1+abs(want)),f'Minimax mismatch at {i}'
        reductions+=2
    # Deterministic sample of high-precision independent chess evaluation.
    rng=random.Random(20261115)
    sample={i for i,r in enumerate(rows) if not children[i] and i%197==0}
    sample.update(i for i,r in enumerate(rows) if not children[i] for _ in [] )
    leaf_indices=[i for i in range(len(rows)) if not children[i]]
    sample.update(rng.sample(leaf_indices,min(1000,len(leaf_indices))))
    decimal_checks=0
    for i in sorted(sample):
        r=rows[i]
        if r['terminal']=='1':continue
        a,b=native_features(r['fen'])
        assert abs(Decimal(str(values[i][0]))-a)<Decimal('1e-6')
        assert abs(Decimal(str(values[i][1]))-b)<Decimal('1e-6')
        decimal_checks+=2
    assert ev['unrolled_depth2_graph_executed'] is True
    assert (root/'generated_single_graph_depth2.txt').exists()
    if dep==4 and rows[0]['fen']==DEFAULT_START:assert leaves==197281 and len(rows)==206604
    summary={'status':'PASS','nodes':len(rows),'leaf_count':leaves,'independent_fen_transitions':transitions,'python_minimax_checks':reductions,'decimal_90_digit_checks':decimal_checks,'unrolled_depth2_graph_executed':True,'scope':'synthetic bounded search; no historical repetition reconstruction'}
    (root/'independent_verification.json').write_text(json.dumps(summary,indent=2)+'\n')
    print('INDEPENDENT_CHESS_AUDIT_PASS',summary)
if __name__=='__main__':verify(sys.argv[1])
