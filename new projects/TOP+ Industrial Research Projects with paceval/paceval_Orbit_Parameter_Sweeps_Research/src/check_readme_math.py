#!/usr/bin/env python3
"""Validate GitHub-compatible mathematical Markdown and local README targets.

Run from the repository root: python3 src/check_readme_math.py

This verifies delimiters, basic expression structure and relative links, not a
browser screenshot of GitHub's rendering or the physical validity of equations.
GitHub syntax: https://docs.github.com/en/get-started/writing-on-github/working-with-advanced-formatting/writing-mathematical-expressions
"""
from pathlib import Path
import re
import sys
from urllib.parse import unquote

ROOT = Path(__file__).resolve().parent.parent
README = ROOT / "README.md"


def validate() -> list[str]:
    errors: list[str] = []
    src = README.read_text(encoding="utf-8")
    # Disallow delimiters GitHub does not document for Markdown math.
    for marker in (r"\(", r"\)", r"\[", r"\]"):
        if marker in src:
            errors.append(f"Unsupported math delimiter: {marker}")

    # Remove fenced blocks before checking inline math. A math block must have
    # unbalanced Markdown backticks nowhere, nonempty content and balanced braces.
    lines = src.splitlines()
    outside = []
    inside = False
    math_lines: list[str] = []
    nmath = 0
    for line in lines:
        stripped = line.strip()
        if not inside and stripped == "```math":
            inside = True
            math_lines = []
            nmath += 1
        elif inside and stripped == "```":
            expr = "\n".join(math_lines)
            if not expr.strip() or expr.count("{") != expr.count("}"):
                errors.append(f"Invalid math block #{nmath}")
            inside = False
        elif inside:
            math_lines.append(line)
        else:
            outside.append(line)
    if inside:
        errors.append("Unclosed math block")
    body = "\n".join(outside)
    # GitHub's $`...`$ form is robust in the presence of Markdown punctuation.
    inline = re.findall(r"\$`([^`\n]+)`\$", body)
    if body.count("$`") != len(inline) or body.count("`$") != len(inline):
        errors.append("Unbalanced inline math delimiters")
    for i, expr in enumerate(inline, 1):
        if expr.count("{") != expr.count("}"):
            errors.append(f"Unbalanced braces in inline math #{i}")

    # All Markdown links and image references with relative destinations must
    # exist in the package; external web links are intentionally exempt.
    links = re.findall(r"!?\[[^\]]*\]\(([^)]+)\)", src)
    checked = 0
    for target in links:
        if target.startswith(("https://", "http://", "mailto:", "#")):
            continue
        local = unquote(target.split("#", 1)[0])
        if not local:
            continue
        checked += 1
        if not (ROOT / local).exists():
            errors.append(f"Missing local target: {target}")
    print(f"Math blocks: {nmath}; inline expressions: {len(inline)}; local links: {checked}")
    return errors


if __name__ == "__main__":
    problems = validate()
    if problems:
        for problem in problems:
            print("ERROR:", problem, file=sys.stderr)
        raise SystemExit(1)
    print("PASS: GitHub math delimiter and local-link checks")
