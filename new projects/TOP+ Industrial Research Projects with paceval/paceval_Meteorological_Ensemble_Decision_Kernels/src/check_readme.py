#!/usr/bin/env python3
"""Deterministic README math/image/link checker with a negative regression test."""
import re,sys,pathlib
from PIL import Image
root=pathlib.Path(__file__).resolve().parent.parent

def check(text):
    if text.count('$$')%2:raise AssertionError('Unmatched block mathematics delimiter')
    without_blocks=text.replace('$$','')
    if without_blocks.count('$')%2:raise AssertionError('Unmatched inline mathematics delimiter')
    links=re.findall(r'!?(?:\[[^\]]*\])\(([^)]+)\)',text)
    n=0
    for dest in links:
        if dest.startswith(('http://','https://','#','mailto:')):continue
        p=(root/dest).resolve()
        if not p.is_relative_to(root.resolve()):raise AssertionError('Unsafe escaped link '+dest)
        if not p.exists():raise AssertionError('Missing README resource '+dest)
        n+=1
    assert n>=9,('Too few local resource links',n)
    assert '## 1. Industrial use case and current state of the art' in text
    assert 'forecast skill' in text.lower()
    assert 'paceval_dConvertStringToFloat' in text
    assert 'paceval_dConvertFloatToString' in text
    with Image.open(root/'figures/00_weather_risk_hero.png') as im:assert im.size==(2400,1200)
    assert (root/'paceval_Meteorological_Ensemble_Decision_Kernels_Whitepaper_EN.pdf').exists()
    return n
if __name__=='__main__':
    text=(root/'README.md').read_text(encoding='utf-8')
    n=check(text)
    if len(sys.argv)>1 and sys.argv[1]=='--self-test':
        try:check(text+'\n[broken regression](figures/this_DOES_NOT_EXIST.png)\n')
        except AssertionError:pass
        else:raise AssertionError('Negative link test was not detected')
        print('README NEGATIVE REGRESSION PASSED')
    else:print('README PASSED: checked',n,'relative links, Markdown delimiters, hero and content')
