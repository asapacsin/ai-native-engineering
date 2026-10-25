#!/usr/bin/env python3
"""Trusted portable skill loader; contract selects a name, never an arbitrary path.

This is an opt-in capability for external client adapters (currently Codex).
It does not install a skill in a user's CLI or grant any tool permissions.
"""
from __future__ import annotations

import re
from pathlib import Path

SKILLS_DIR = Path(__file__).resolve().parents[1] / ".agents" / "skills"
SKILL_NAME = re.compile(r"[a-z][a-z0-9-]{0,63}\Z")
MAX_SKILL_BYTES = 12000


def load_skill(name: str) -> str:
    """Resolve and validate one bundled SKILL.md; fail closed on unknown names."""
    if not isinstance(name, str) or not SKILL_NAME.fullmatch(name):
        raise ValueError("skill must be a safe, lower-case skill name")
    directory = SKILLS_DIR / name
    path = directory / "SKILL.md"
    if directory.is_symlink() or path.is_symlink() or not path.is_file():
        raise ValueError("unknown or unsafe portable skill: " + name)
    content = path.read_bytes()
    if len(content) > MAX_SKILL_BYTES:
        raise ValueError("portable skill exceeds context size budget: " + name)
    try:
        text = content.decode("utf-8")
    except UnicodeError as exc:
        raise ValueError("portable skill must be UTF-8") from exc
    lines = text.splitlines()
    if not lines or lines[0] != "---":
        raise ValueError("portable skill must have frontmatter")
    try:
        end = lines.index("---", 1)
    except ValueError as exc:
        raise ValueError("portable skill frontmatter is unterminated") from exc
    metadata = {}
    for line in lines[1:end]:
        if ":" not in line:
            raise ValueError("invalid portable skill frontmatter")
        key, value = line.split(":", 1)
        metadata[key.strip()] = value.strip()
    if metadata.get("name") != name or not metadata.get("description"):
        raise ValueError("portable skill name/description mismatch: " + name)
    if not any(line.strip() for line in lines[end + 1:]):
        raise ValueError("portable skill body is empty: " + name)
    return text


def available_skills() -> list[str]:
    """List only valid, bundled skills; reject broken definitions rather than hiding them."""
    if not SKILLS_DIR.is_dir():
        return []
    names = sorted(p.name for p in SKILLS_DIR.iterdir() if p.is_dir() and not p.is_symlink())
    return [name for name in names if load_skill(name)]
