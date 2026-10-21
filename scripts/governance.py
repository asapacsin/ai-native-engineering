#!/usr/bin/env python3
"""Fail-closed task approval, path scope, and exact-tip merge eligibility.

Requires a normal Git worktree, a task contract, and a saved ai_native cycle
verdict. This is a local process guard, NOT GitHub branch protection or cryptographic
actor authentication. The approver identity is self-asserted; protect the CI job
and governance records with repository permissions/branch rules in production.
"""
from __future__ import annotations
import argparse
import fnmatch
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

from ai_native import load_json, work_snapshot, validate_contract, save_json

LEVELS = ["static", "unit", "integration", "e2e", "device", "visual", "performance"]
PROTECTED = (".git/", ".ai-native/", ".github/workflows/", "AGENTS.md")


def digest(obj: dict) -> str:
    return hashlib.sha256(json.dumps(obj, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def patterns_match(path: str, rule: str) -> bool:
    """Git-style directory prefix or slash-aware * and ** patterns."""
    import re
    rule = rule.replace("\\", "/")
    if rule.endswith("/"):
        return path.startswith(rule)
    expression = ""
    i = 0
    while i < len(rule):
        if rule[i:i + 3] == "**/":
            expression += "(?:.*/)?"
            i += 3
        elif rule[i:i + 2] == "**":
            expression += ".*"
            i += 2
        elif rule[i] == "*":
            expression += "[^/]*"
            i += 1
        elif rule[i] == "?":
            expression += "[^/]"
            i += 1
        else:
            expression += re.escape(rule[i])
            i += 1
    return re.fullmatch(expression, path) is not None


def changed_paths(repo: Path, base: str) -> list[str]:
    subprocess.run(["git", "-C", str(repo), "cat-file", "-e", f"{base}^{{commit}}"],
                   check=True, capture_output=True)
    paths: set[str] = set()
    for args in (["diff", "--no-renames", "--name-only", "-z", base, "HEAD"],
                 ["diff", "--no-renames", "--name-only", "-z", "HEAD"],
                 ["ls-files", "-o", "--exclude-standard", "-z"]):
        output = subprocess.run(["git", "-C", str(repo), *args], check=True, capture_output=True).stdout
        for p in output.split(b"\0"):
            if p:
                paths.add(p.decode("utf-8", errors="surrogateescape").replace("\\", "/"))
    return sorted(paths)


def contract_policy(contract: dict) -> list[str]:
    issues: list[str] = []
    try:
        validate_contract(contract)
    except (ValueError, TypeError) as exc:
        return [str(exc)]
    if not isinstance(contract.get("base_commit"), str) or len(contract["base_commit"]) != 40:
        issues.append("base_commit must be a full 40-character Git commit SHA")
    allowed = contract.get("approved_paths")
    forbidden = contract.get("forbidden_paths", [])
    if not isinstance(allowed, list) or not allowed or not all(isinstance(x, str) and x for x in allowed):
        issues.append("approved_paths must be a nonempty string list")
    if not isinstance(forbidden, list) or not all(isinstance(x, str) and x for x in forbidden):
        issues.append("forbidden_paths must be a string list")
    return issues


def scope_issues(repo: Path, contract: dict) -> list[str]:
    issues = contract_policy(contract)
    if issues:
        return issues
    try:
        paths = changed_paths(repo, contract["base_commit"])
    except subprocess.CalledProcessError:
        return ["base_commit is missing from this Git checkout"]
    for p in paths:
        if any(p == x.rstrip("/") or p.startswith(x) for x in PROTECTED):
            issues.append("protected governance file changed: " + p)
        elif any(patterns_match(p, g) for g in contract.get("forbidden_paths", [])):
            issues.append("forbidden path changed: " + p)
        elif not any(patterns_match(p, g) for g in contract["approved_paths"]):
            issues.append("outside approved scope: " + p)
    return issues


def approval_path(repo: Path, task_id: str) -> Path:
    return repo / ".ai-native" / "approvals" / (task_id + ".json")


def approve(repo: Path, contract: dict, actor: str, role: str) -> dict:
    errs = contract_policy(contract)
    if errs:
        raise ValueError("; ".join(errs))
    if role not in {"planner", "architect", "owner"} or os.getenv("AI_NATIVE_ROLE", "").lower() == "executor":
        raise ValueError("executor cannot approve task contracts")
    if not actor.strip():
        raise ValueError("named approver required")
    # Local approval is a procedural control, not strong authentication.
    item = {"task_id": contract["task_id"], "contract_hash": digest(contract),
            "actor": actor, "role": role, "base_commit": contract["base_commit"]}
    save_json(approval_path(repo, contract["task_id"]), item)
    return item


def required_evidence_issues(repo: Path, requirements: dict, latest: dict) -> list[str]:
    """Requirement-owned minimum scope cannot be weakened by task contract."""
    problems: list[str] = []
    gates_path = repo / ".ai-native" / "runs" / latest.get("task_id", "")
    # Evidence is read from the final cycle attempt, not an earlier successful gate.
    attempt = int(latest.get("attempt", 0))
    datafile = gates_path / f"attempt-{attempt:02}" / "gates.json"
    try:
        records = {g["id"]: g for g in load_json(datafile)["gates"]}
    except (OSError, ValueError, TypeError, KeyError):
        return ["final attempt gate evidence unavailable"]
    for req in requirements.get("requirements", []):
        if not isinstance(req, dict) or not req.get("id"):
            problems.append("requirement entry missing id")
            continue
        level = req.get("min_level")
        if level not in LEVELS:
            problems.append(f"{req['id']}: invalid min_level")
            continue
        for gid in req.get("gate_ids", []):
            evidence = records.get(gid)
            if not evidence or evidence.get("status") != "PASS":
                problems.append(f"{req['id']}: required gate {gid} has no passing evidence")
            elif LEVELS.index(evidence.get("level", "static")) < LEVELS.index(level):
                problems.append(f"{req['id']}: gate {gid} scope below required {level}")
        if not req.get("gate_ids"):
            problems.append(f"{req['id']}: no required gates declared")
        if req.get("terminal_required"):
            terminal = req.get("terminal_state")
            refs = req.get("artifact_refs", [])
            if not terminal or not isinstance(refs, list) or not refs:
                problems.append(f"{req['id']}: missing terminal state or artifact reference")
            # Artifact references are declarations here; external validator must validate real files.
    return problems


def eligibility(repo: Path, contract: dict, requirements: dict | None = None) -> list[str]:
    issues = scope_issues(repo, contract)
    if issues:
        return issues
    try:
        record = load_json(approval_path(repo, contract["task_id"]))
        if record.get("contract_hash") != digest(contract):
            issues.append("contract changed since independent approval")
        if record.get("role") not in {"planner", "architect", "owner"}:
            issues.append("invalid approval role")
    except (OSError, ValueError):
        issues.append("missing independent task approval")
    snapshot = work_snapshot(repo)
    if snapshot["dirty"]:
        issues.append("worktree must be clean before merge eligibility")
    try:
        latest = load_json(repo / ".ai-native" / "runs" / contract["task_id"] / "latest.json")
        if latest.get("verdict") != "PASS":
            issues.append("independent reviewer did not PASS")
        if latest.get("snapshot", {}).get("fingerprint") != snapshot["fingerprint"]:
            issues.append("verification or review is stale relative to current tree")
        if latest.get("contract_hash") != digest(contract):
            issues.append("verification not bound to approved contract")
        if latest.get("failed_required_gates"):
            issues.append("some required gates failed")
        latest["task_id"] = contract["task_id"]
        if requirements is not None:
            issues.extend(required_evidence_issues(repo, requirements, latest))
    except (OSError, ValueError):
        issues.append("no current end-state verification available")
    return issues


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=["approve", "scope", "eligible"])
    parser.add_argument("--repo", default=".")
    parser.add_argument("--contract", required=True)
    parser.add_argument("--requirements")
    parser.add_argument("--actor", default="")
    parser.add_argument("--role", default="executor")
    args = parser.parse_args(argv)
    try:
        repo = Path(args.repo).resolve()
        contract = load_json(Path(args.contract))
        if args.action == "approve":
            print(json.dumps(approve(repo, contract, args.actor, args.role), indent=2))
            return 0
        problems = (scope_issues(repo, contract) if args.action == "scope" else
                    eligibility(repo, contract, load_json(Path(args.requirements)) if args.requirements else None))
        print(json.dumps({"result": "ELIGIBLE" if not problems else "NOT_ELIGIBLE", "problems": problems}, indent=2))
        return 0 if not problems else 2
    except (ValueError, OSError, subprocess.CalledProcessError) as e:
        print("BLOCKED:", str(e), file=sys.stderr)
        return 3


if __name__ == "__main__":
    raise SystemExit(main())
