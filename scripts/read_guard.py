#!/usr/bin/env python3
"""Optional Claude Code PreToolUse Read budget; NOT an access-control/security guard."""
from __future__ import annotations
import json
import os
import sys
from pathlib import Path

NON_TEXT = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".pdf", ".ipynb",
            ".mp3", ".mp4", ".wav", ".zip", ".gz", ".db", ".sqlite", ".ipa", ".jar"}

def deny_reason(event, limit_kb):
    if limit_kb <= 0 or not isinstance(event, dict) or event.get("tool_name") != "Read":
        return None
    params = event.get("tool_input")
    if not isinstance(params, dict):
        return None
    raw = params.get("file_path")
    if not isinstance(raw, str) or not raw or params.get("offset") is not None or params.get("limit") is not None:
        return None
    path = Path(raw)
    if not path.is_absolute():
        path = Path(event.get("cwd") or os.getcwd()) / path
    if path.suffix.lower() in NON_TEXT:
        return None
    try:
        size = path.stat().st_size
    except OSError:
        return None
    if size <= limit_kb * 1024:
        return None
    return (f"{path.name} is {size // 1024} KB, above the {limit_kb} KB context read budget. "
            "Grep for the relevant symbol/heading, then Read with offset/limit. "
            "For Markdown specs run python3 scripts/spec_section.py <path> "
            "to list headings, then add a section number/name.")

def main():
    try:
        event = json.load(sys.stdin)
        limit = int(os.environ.get("AI_NATIVE_READ_GUARD_KB", "40"))
        reason = deny_reason(event, limit)
    except Exception:
        return 0
    if reason:
        print(json.dumps({"hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": reason,
        }}))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
