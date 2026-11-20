#!/usr/bin/env python3
"""List Markdown headings or retrieve one section without reading a whole specification.

Usage: python3 scripts/spec_section.py PATH [SECTION] [--max-bytes N]
SECTION is a number such as 51 or 5.2, or an exact heading title.
"""
from __future__ import annotations
import argparse
import re
from pathlib import Path

HEADING = re.compile(r"^(#{1,6})[ \t]+(.+?)\s*$")
NUMBER = re.compile(r"^(\d+(?:\.\d+)*)(?:\.|\s+|$)")
FENCE = re.compile(r"^(\x60{3,}|~{3,})")

def sections(lines):
    found = []
    fence_char, fence_length = "", 0
    for i, line in enumerate(lines):
        stripped = line.lstrip(" ")
        fence = FENCE.match(stripped) if len(line) - len(stripped) <= 3 else None
        if fence:
            token = fence.group(1)
            if not fence_char:
                fence_char, fence_length = token[0], len(token)
            elif token[0] == fence_char and len(token) >= fence_length:
                fence_char, fence_length = "", 0
            continue
        if fence_char:
            continue
        match = HEADING.match(line)
        if match:
            title = match.group(2).rstrip(" #").strip()
            number = NUMBER.match(title)
            found.append((i, len(match.group(1)), title, number.group(1) if number else None))
    result = []
    for n, (start, level, title, number) in enumerate(found):
        end = next((index for index, depth, _, _ in found[n + 1:] if depth <= level), len(lines))
        result.append((start, end, level, title, number))
    return result

def run(path, requested, max_bytes):
    if not path.is_file():
        raise ValueError(f"no such spec file: {path}")
    lines = path.read_text(encoding="utf-8").splitlines()
    headings = sections(lines)
    if requested is None:
        for start, end, depth, title, _ in headings:
            size = len(("\n".join(lines[start:end]) + "\n").encode("utf-8"))
            print(f"{start + 1:>5}-{end:<5} {size // 1024:>4} KB  {'  ' * (depth - 1)}{title[:100]}")
        return 0
    key = requested.lstrip("§").strip()
    matches = [(start, end) for start, end, _, title, number in headings
               if number == key or title.casefold() == key.casefold()]
    if len(matches) != 1:
        raise ValueError(f"expected one section {requested!r} in {path}, found {len(matches)}; list sections first")
    start, end = matches[0]
    content = "\n".join(lines[start:end]) + "\n"
    size = len(content.encode("utf-8"))
    if max_bytes > 0 and size > max_bytes:
        raise ValueError(f"section {requested} is {size} bytes above {max_bytes}; "
                         f"Read with offset/limit for lines {start + 1}-{end} or increase --max-bytes")
    print(f"[{path} lines {start + 1}-{end}]")
    print(content, end="")
    return 0

def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("file", type=Path)
    parser.add_argument("section", nargs="?")
    parser.add_argument("--max-bytes", type=int, default=40960)
    args = parser.parse_args(argv)
    try:
        return run(args.file, args.section, args.max_bytes)
    except (OSError, UnicodeError, ValueError) as error:
        parser.exit(2, f"spec_section: {error}\n")

if __name__ == "__main__":
    raise SystemExit(main())
