#!/usr/bin/env python3
"""Archive-wide GitHub-compatible math and link gate, including failing regression cases.

The parser step uses Mistune 3 with its Markdown math plugin. Source-level checks
add restrictions that a permissive parser cannot reliably catch by itself.
"""
from __future__ import annotations
import pathlib
import re
import sys
from urllib.parse import unquote

try:
    import mistune
except ImportError as exc:
    raise SystemExit('The publication check requires mistune>=3.0') from exc

ROOT = pathlib.Path(__file__).resolve().parent.parent
PARSER = mistune.create_markdown(renderer='ast', plugins=['math'])
ALLOWED = {'http', 'https', 'mailto', 'data'}


def without_inline_code(line: str) -> str:
    # Remove GitHub-style single and multiple backtick code spans for gate scanning.
    return re.sub(r'(`+).*?\1', '', line)


def check_source_math(text: str) -> None:
    block_mode = None
    math_dollars_open = False
    math_fence_used = 0
    for number, line in enumerate(text.splitlines(), 1):
        s = line.strip()
        fence = re.match(r'^(`{3,}|~{3,})(.*)$', s)
        if fence:
            marker = fence.group(1)
            info = fence.group(2).strip().lower()
            if block_mode is None:
                block_mode = (marker[0], len(marker), info == 'math')
                math_fence_used += (info == 'math')
            elif marker[0] == block_mode[0] and len(marker) >= block_mode[1] and not info:
                block_mode = None
            continue
        if block_mode is not None:
            if block_mode[2] and (r'\operatorname' in line or re.search(r'\\[\[\]()]', line)):
                raise AssertionError(f'Unapproved math macro/delimiter on line {number}')
            continue
        if s == '$$':
            math_dollars_open = not math_dollars_open
            continue
        code_free = without_inline_code(line)
        if r'\operatorname' in code_free:
            raise AssertionError(f'Banned \\operatorname on line {number}')
        if re.search(r'\\[\[\]()]', code_free):
            raise AssertionError(f'Raw LaTeX math delimiters on line {number}')
        if '$$' in code_free:
            raise AssertionError(f'Double-dollar block math must have its own line: {number}')
        if math_dollars_open and '$' in code_free:
            raise AssertionError(f'Nested math delimiters on line {number}')
        if not math_dollars_open:
            # Inline math is same-line only; excludes escaped $.
            dollars = re.findall(r'(?<!\\)\$(?!\$)', code_free)
            if len(dollars) % 2:
                raise AssertionError(f'Unpaired inline dollar on line {number}')
    if block_mode is not None:
        raise AssertionError('Unclosed Markdown code/math fence')
    if math_dollars_open:
        raise AssertionError('Unmatched display $$ math fence')


def flatten_ast(nodes):
    for node in nodes:
        yield node
        if 'children' in node:
            yield from flatten_ast(node['children'])


def check_markdown(text: str, base: pathlib.Path, validate_links: bool=True) -> tuple[int, int]:
    check_source_math(text)
    tree = PARSER(text)
    if not isinstance(tree, list):
        raise AssertionError('Markdown parser failed')
    math_nodes = 0
    links = 0
    for node in flatten_ast(tree):
        if node['type'] in ('inline_math', 'block_math'):
            math_nodes += 1
            expr = node.get('raw', '')
            if not expr.strip() or r'\operatorname' in expr:
                raise AssertionError('Invalid or empty math expression')
        if node['type'] in ('link','image') and validate_links:
            dest = node.get('attrs', {}).get('url', '')
            if not dest or dest.startswith('#') or re.match(r'^[a-zA-Z][a-zA-Z0-9+.-]*:', dest):
                continue
            target = (base / unquote(dest.split('#')[0].split('?')[0])).resolve()
            if not target.is_relative_to(ROOT.resolve()):
                raise AssertionError(f'Unsafe path outside archive: {dest}')
            if not target.is_file():
                raise AssertionError(f'Broken local Markdown link: {dest}')
            links += 1
    return math_nodes, links


def negative_regressions():
    bad_cases = [
        r'Test \(x+1\)',
        r'Test \[x+1\]',
        r'Test $\operatorname{sig}(x)$',
        'Text $$x+y$$ another word',
        'Text $x+y on one line',
        '$$\nA + B',
        '$$\nA + $B$\n$$',
        '```math\nA+B\n',
        '[broken](figures/not-an-existing-file.png)',
    ]
    for i, case in enumerate(bad_cases):
        try:
            check_markdown(case, ROOT)
        except AssertionError:
            continue
        raise AssertionError(f'Negative regression {i} NOT rejected: {case!r}')


def main():
    files = sorted(ROOT.rglob('*.md'))
    if len(files) < 3:
        raise AssertionError('Not all nested Markdown files found')
    math_total = links_total = 0
    for file in files:
        if 'build' in file.relative_to(ROOT).parts:
            continue
        math_count, link_count = check_markdown(file.read_text(encoding='utf-8'), file.parent)
        math_total += math_count
        links_total += link_count
        print('MARKDOWN PASSED', file.relative_to(ROOT), 'math:', math_count, 'links:', link_count)
    negative_regressions()
    if math_total < 4:
        raise AssertionError(f'Unexpectedly few parsed math expressions: {math_total}')
    print('ARCHIVE MARKDOWN GATE PASSED:',len(files),'files,',math_total,'parsed math nodes,',links_total,'local links, 9 negative tests')

if __name__ == '__main__':
    main()
