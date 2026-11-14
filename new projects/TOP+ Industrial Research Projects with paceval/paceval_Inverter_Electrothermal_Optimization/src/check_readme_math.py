#!/usr/bin/env python3
"""Small deterministic relative-link and GitHub equation-delimiter checker with negative tests."""
import re,sys
from pathlib import Path
from PIL import Image

def check_text(text,base):
    errors=[]
    if text.count('```')%2:errors.append('unclosed fenced code block')
    if text.count('$$')%2:errors.append('unclosed block math')
    for match in re.finditer(r'!?\[[^\]]*\]\(([^)]+)\)',text):
        link=match.group(1).split('#',1)[0]
        if not link:continue
        if re.match(r'(https?|mailto):',link):continue
        if link.startswith('sandbox:'):errors.append('sandbox URL instead of relative link: '+link);continue
        if not (base/link).is_file():errors.append('broken relative path '+link)
    if not (base/'figures/00_inverter_electrothermal_hero.png').is_file():errors.append('missing hero')
    elif Image.open(base/'figures/00_inverter_electrothermal_hero.png').size!=(2400,1200):errors.append('hero dimension mismatch')
    if 'paceval_Inverter_Electrothermal_Optimization_Whitepaper_EN.pdf' not in text:errors.append('no whitepaper link')
    if '## 1. Industrial use case and current state of the art' not in text:errors.append('missing introduction')
    if 'paceval_dConvertStringToFloat' not in text or 'paceval_dConvertFloatToString' not in text:errors.append('conversion paths missing')
    return errors

def main():
    base=Path(__file__).resolve().parents[1]
    txt=(base/'README.md').read_text()
    assert not check_text(txt,base),check_text(txt,base)
    if '--self-test' in sys.argv:
        assert check_text(txt+'\n![bad](figures/not_here_ever.png)',base), 'broken link missed'
        assert check_text(txt+'\n$$',base),'unclosed math missed'
        assert check_text(txt+'\n```',base),'unclosed fence missed'
    print('PASS README markdown, mathematical delimiters, local links and hero image' + (' with negative regressions' if '--self-test' in sys.argv else ''))
if __name__=='__main__':main()
