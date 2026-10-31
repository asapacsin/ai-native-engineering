#!/usr/bin/env python3
"""External Claude Code CLI reviewer bridge. Runs a real Claude session only when explicitly invoked.

Requires an installed, authenticated `claude` CLI supporting `-p`, `--model`,
`--effort`, `--json-schema` and `--output-format json`. Defaults: Claude Opus 5.5
(`claude-opus-5-5`) at `high` effort, read-only tools. No test in this repository
invokes a paid model. Reviewer role only; configure the Executor separately.
"""
import argparse
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

from codex_bridge import REVIEW_SCHEMA, role_prompt, role_timeout_seconds

DEFAULT_MODEL = "claude-opus-5-5"
DEFAULT_EFFORT = "high"
EFFORTS = {"low", "medium", "high", "xhigh", "max"}
READ_ONLY_TOOLS = ["Read", "Grep", "Glob", "Bash"]
ALLOWED_TOOLS = ["Read", "Grep", "Glob", "Bash(git status*)", "Bash(git diff*)", "Bash(git log*)",
                 "Bash(git show*)", "Bash(git ls-files*)", "Bash(git rev-parse*)"]
DENIED_TOOLS = ["Edit", "Write", "NotebookEdit", "Bash(git commit*)", "Bash(git push*)",
                "Bash(git merge*)", "Bash(git checkout*)", "Bash(git reset*)"]


def reviewer_settings() -> tuple[str, str]:
    model = os.environ.get("AI_NATIVE_REVIEWER_MODEL", DEFAULT_MODEL)
    effort = os.environ.get("AI_NATIVE_REVIEWER_EFFORT", DEFAULT_EFFORT)
    if effort not in EFFORTS:
        raise ValueError("AI_NATIVE_REVIEWER_EFFORT must be one of " + ", ".join(sorted(EFFORTS)))
    return model, effort


def claude_command() -> list[str]:
    model, effort = reviewer_settings()
    command = ["claude", "-p", "--model", model, "--effort", effort,
               "--output-format", "json", "--json-schema", json.dumps(REVIEW_SCHEMA),
               "--permission-mode", "dontAsk", "--no-session-persistence",
               "--tools", ",".join(READ_ONLY_TOOLS),
               "--allowedTools", *ALLOWED_TOOLS, "--disallowedTools", *DENIED_TOOLS]
    budget = os.environ.get("AI_NATIVE_REVIEWER_MAX_BUDGET_USD")
    if budget:
        if float(budget) <= 0:
            raise ValueError("AI_NATIVE_REVIEWER_MAX_BUDGET_USD must be positive")
        command += ["--max-budget-usd", budget]
    return command


def not_verified(packet: dict, reason: str) -> dict:
    return {"verdict": "NOT_VERIFIED",
            "reviewed_fingerprint": packet.get("snapshot", {}).get("fingerprint", ""),
            "reviewed_contract_hash": packet.get("contract_hash", ""),
            "findings": [reason], "next_action": "Inspect the Claude reviewer run and re-run the review"}


def extract_review(stdout: str, packet: dict, model: str) -> dict:
    """Turn `claude -p --output-format json` output into a review result; fail closed."""
    try:
        envelope = json.loads(stdout)
    except json.JSONDecodeError:
        return not_verified(packet, "Claude reviewer did not return JSON output")
    if not isinstance(envelope, dict) or envelope.get("is_error"):
        return not_verified(packet, "Claude reviewer reported an error: " + str(envelope.get("subtype", "unknown")))
    used = envelope.get("modelUsage")
    if isinstance(used, dict) and used and not any(name.startswith(model) for name in used):
        return not_verified(packet, "Claude reviewer ran on " + ", ".join(sorted(used))
                            + " instead of the configured " + model)
    review = envelope.get("structured_output")
    if review is None:
        try:
            review = json.loads(envelope.get("result", ""))
        except (TypeError, json.JSONDecodeError):
            return not_verified(packet, "Claude reviewer returned no structured review")
    if not isinstance(review, dict) or set(review) != set(REVIEW_SCHEMA["required"]):
        return not_verified(packet, "Claude reviewer output does not match the review schema")
    return review


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("role", choices=["reviewer"])
    parser.parse_args(argv)
    if not shutil.which("claude"):
        print("Claude Code CLI not found on PATH; install/authenticate it before running paid model tasks.",
              file=sys.stderr)
        return 10
    packet_path, result_path = os.environ.get("AI_NATIVE_REVIEW_PACKET"), os.environ.get("AI_NATIVE_REVIEW_RESULT")
    if not packet_path or not result_path:
        print("Missing review packet/result env paths", file=sys.stderr)
        return 12
    packet = json.loads(Path(packet_path).read_text(encoding="utf-8"))
    model, _ = reviewer_settings()
    result = subprocess.run(claude_command(), input=role_prompt("reviewer", packet), text=True,
                            capture_output=True, timeout=role_timeout_seconds("reviewer"))
    if result.returncode != 0 and not result.stdout.strip():
        review = not_verified(packet, "Claude reviewer exited with status " + str(result.returncode))
    else:
        review = extract_review(result.stdout, packet, model)
    Path(result_path).write_text(json.dumps(review, indent=2), encoding="utf-8")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, ValueError, json.JSONDecodeError, subprocess.TimeoutExpired) as error:
        print("Claude reviewer failed: " + str(error), file=sys.stderr)
        raise SystemExit(13)
