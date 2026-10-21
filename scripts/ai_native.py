#!/usr/bin/env python3
"""AI-native, executor-first end-state controller (Python stdlib only).

This tool drives configured *external* executor/reviewer processes. It does NOT
impersonate an LLM, select a provider subscription, or treat tests as review.
"""
from __future__ import annotations
import argparse
import datetime as dt
import hashlib
import json
import os
import re
import shlex
import subprocess
import sys
import time
from pathlib import Path

VERDICTS = {"PASS", "REWORK", "BLOCKED", "NOT_VERIFIED"}
TASK_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]{0,79}$")
EXCLUDE_UNTRACKED = (".ai-native/", ".git/", "__pycache__/", ".pytest_cache/")


def save_json(path: Path, obj: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(obj, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")
    tmp.replace(path)


def load_json(path: Path) -> dict:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("Expected a JSON object")
    return data


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def git(repo: Path, *args: str) -> bytes:
    p = subprocess.run(["git", "-C", str(repo), *args], capture_output=True)
    if p.returncode:
        raise RuntimeError("git " + " ".join(args) + ": " + p.stderr.decode(errors="replace")[:300])
    return p.stdout


def work_snapshot(repo: Path) -> dict:
    """Bind review to HEAD + dirty diff and untracked contents, not merely a commit."""
    head = git(repo, "rev-parse", "HEAD").decode().strip()
    diff = git(repo, "diff", "--binary", "HEAD")
    others = git(repo, "ls-files", "-o", "--exclude-standard", "-z").split(b"\0")
    untracked = {}
    for item in others:
        if not item:
            continue
        rel = item.decode("utf-8", errors="surrogateescape").replace("\\", "/")
        if any(rel.startswith(p) for p in EXCLUDE_UNTRACKED) or "/__pycache__/" in rel:
            continue
        f = repo / rel
        if not f.is_file() or f.is_symlink():
            continue
        digest = hashlib.sha256()
        with f.open("rb") as stream:
            for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                digest.update(chunk)
        untracked[rel] = digest.hexdigest()
    fingerprint = sha(json.dumps({"head": head, "diff": sha(diff), "untracked": untracked}, sort_keys=True).encode())
    return {"commit": head, "diff_sha256": sha(diff), "untracked_hashes": untracked,
            "fingerprint": fingerprint, "dirty": bool(diff or untracked)}


def validate_contract(contract: dict) -> None:
    if contract.get("schema_version") != 1:
        raise ValueError("contract schema_version must be 1")
    if not TASK_RE.fullmatch(str(contract.get("task_id", ""))):
        raise ValueError("task_id must be a safe nonempty slug")
    if not str(contract.get("goal", "")).strip():
        raise ValueError("goal is required")
    gates = contract.get("gates")
    if not isinstance(gates, list) or not gates:
        raise ValueError("nonempty gates array required")
    seen = set()
    for gate in gates:
        if not isinstance(gate, dict) or not TASK_RE.fullmatch(str(gate.get("id", ""))):
            raise ValueError("each gate needs a safe id")
        if gate["id"] in seen:
            raise ValueError("duplicate gate id: " + gate["id"])
        seen.add(gate["id"])
        if gate.get("level") not in {"static", "unit", "integration", "e2e", "device", "visual", "performance"}:
            raise ValueError("gate level must be explicit")
        if not isinstance(gate.get("command"), list) or not gate["command"] or not all(
            isinstance(s, str) and s for s in gate["command"]):
            raise ValueError("gate command requires argv list; shell operators are not interpreted")
        if gate.get("timeout_seconds", 180) <= 0:
            raise ValueError("gate timeout must be positive")
    budgets = contract.get("budgets", {})
    if not isinstance(budgets, dict) or not 1 <= budgets.get("max_attempts", 3) <= 10:
        raise ValueError("max_attempts must be 1..10")
    if budgets.get("max_total_seconds", 900) <= 0:
        raise ValueError("max_total_seconds must be positive")
    if not isinstance(contract.get("acceptance", ""), str) or not contract["acceptance"].strip():
        raise ValueError("acceptance must be explicit")


def call_argv(argv: list[str], repo: Path, env: dict, timeout: float) -> dict:
    began = dt.datetime.now(dt.timezone.utc).isoformat()
    try:
        p = subprocess.run(argv, cwd=repo, capture_output=True, text=True, env=env,
                           timeout=max(1, timeout), errors="replace")
        # Store bounded excerpts only. Never pass secrets/credentials in CLI output.
        return {"command": argv, "started": began, "exit_code": p.returncode,
                "stdout_tail": p.stdout[-5000:], "stderr_tail": p.stderr[-5000:],
                "status": "PASS" if p.returncode == 0 else "FAIL"}
    except subprocess.TimeoutExpired:
        return {"command": argv, "started": began, "status": "FAIL", "error": "timeout"}
    except OSError as e:
        return {"command": argv, "started": began, "status": "BLOCKED",
                "error": e.__class__.__name__ + ": " + str(e)}


def parse_command(value: str | None) -> list[str] | None:
    if not value:
        return None
    parsed = shlex.split(value, posix=(os.name != "nt"))
    return parsed or None


def review_packet(contract: dict, snapshot: dict, gates: list[dict], attempt: int) -> dict:
    return {"schema_version": 1, "task_id": contract["task_id"], "goal": contract["goal"],
            "acceptance": contract["acceptance"], "boundaries": contract.get("boundaries", []),
            "attempt": attempt, "snapshot": snapshot, "gates": gates,
            "review_instructions": (
                "INDEPENDENT, READ-ONLY REVIEW. Inspect actual git diff and changed files, not executor prose. "
                "Validate acceptance, architecture, invariant safety, proof levels, missing E2E, and secret risks. "
                "Write review result JSON with verdict PASS / REWORK / BLOCKED / NOT_VERIFIED, "
                "reviewed_fingerprint equal to snapshot.fingerprint, findings array, next_action string. "
                "PASS only if all required acceptance levels have genuine evidence. Do not modify repo."
            )}


def attempt_cycle(repo: Path, contract: dict, attempt: int, executor: list[str] | None,
                  reviewer: list[str] | None, deadline: float) -> dict:
    task_id = contract["task_id"]
    folder = repo / ".ai-native" / "runs" / task_id / f"attempt-{attempt:02}"
    folder.mkdir(parents=True, exist_ok=True)
    env = os.environ.copy()
    env.update({"AI_NATIVE_TASK_ID": task_id, "AI_NATIVE_ATTEMPT": str(attempt),
                "AI_NATIVE_CONTRACT": str((folder / "contract.json").resolve()),
                "AI_NATIVE_FEEDBACK": str((folder.parent / "latest.json").resolve())})
    save_json(folder / "contract.json", contract)
    execution = None
    if executor:
        execution = call_argv(executor, repo, env, min(300, max(1, deadline - time.monotonic())))
        save_json(folder / "executor.json", execution)
        if execution["status"] != "PASS":
            outcome = "BLOCKED" if execution["status"] == "BLOCKED" else "REWORK"
            return record(folder, {"verdict": outcome, "next_action": "Resolve executor command failure", "executor": execution, "attempt": attempt})
    gates = []
    for gate in contract["gates"]:
        if time.monotonic() >= deadline:
            gates.append({"id": gate["id"], "level": gate["level"], "status": "BLOCKED", "error": "time budget reached"})
            continue
        outcome = call_argv(gate["command"], repo, env, min(gate.get("timeout_seconds", 180), max(1, deadline - time.monotonic())))
        outcome.update({"id": gate["id"], "level": gate["level"], "required": gate.get("required", True)})
        gates.append(outcome)
    save_json(folder / "gates.json", {"gates": gates})
    snapshot = work_snapshot(repo)
    packet = review_packet(contract, snapshot, gates, attempt)
    save_json(folder / "review_packet.json", packet)
    req_failures = [g for g in gates if g.get("required") and g["status"] != "PASS"]
    if not reviewer:
        return record(folder, {"verdict": "NOT_VERIFIED", "next_action": "Configure an independent reviewer command",
                               "reason": "No external reviewer was invoked", "attempt": attempt, "snapshot": snapshot,
                               "failed_required_gates": [g["id"] for g in req_failures]})
    env.update({"AI_NATIVE_REVIEW_PACKET": str((folder / "review_packet.json").resolve()),
                "AI_NATIVE_REVIEW_RESULT": str((folder / "review_result.json").resolve())})
    rv = call_argv(reviewer, repo, env, min(240, max(1, deadline - time.monotonic())))
    save_json(folder / "reviewer_process.json", rv)
    if rv["status"] != "PASS":
        return record(folder, {"verdict": "BLOCKED" if rv["status"] == "BLOCKED" else "NOT_VERIFIED",
                               "next_action": "Restore reviewer command and rerun review", "attempt": attempt,
                               "reviewer_process": rv})
    try:
        response = load_json(folder / "review_result.json")
        if response.get("verdict") not in VERDICTS:
            raise ValueError("invalid reviewer verdict")
        if response.get("reviewed_fingerprint") != snapshot["fingerprint"]:
            raise ValueError("reviewer reviewed wrong snapshot fingerprint")
        if not isinstance(response.get("findings"), list) or not isinstance(response.get("next_action"), str):
            raise ValueError("reviewer must supply findings array and next_action")
        if work_snapshot(repo)["fingerprint"] != snapshot["fingerprint"]:
            raise ValueError("repository changed while reviewer was running")
        outcome = response["verdict"]
        if req_failures and outcome == "PASS":
            outcome = "BLOCKED" if any(g["status"] == "BLOCKED" for g in req_failures) else "REWORK"
            response["findings"].append("Reviewer PASS rejected: required gates lack passing evidence")
        response.update({"verdict": outcome, "attempt": attempt, "snapshot": snapshot,
                         "failed_required_gates": [g["id"] for g in req_failures]})
        return record(folder, response)
    except (OSError, ValueError, json.JSONDecodeError) as e:
        return record(folder, {"verdict": "NOT_VERIFIED", "next_action": "Fix invalid or stale review evidence",
                               "reason": str(e), "attempt": attempt, "snapshot": snapshot})


def record(folder: Path, outcome: dict) -> dict:
    save_json(folder / "verdict.json", outcome)
    save_json(folder.parent / "latest.json", outcome)
    return outcome


def cycle(args: argparse.Namespace) -> int:
    repo = Path(args.repo).resolve()
    contract = load_json(Path(args.contract).resolve())
    validate_contract(contract)
    try:
        work_snapshot(repo)
    except (OSError, RuntimeError) as exc:
        raise ValueError("target must be an initialized git repository: " + str(exc)) from exc
    executor = parse_command(args.executor or os.environ.get("AI_NATIVE_EXECUTOR_CMD"))
    reviewer = parse_command(args.reviewer or os.environ.get("AI_NATIVE_REVIEWER_CMD"))
    max_attempts = contract.get("budgets", {}).get("max_attempts", 3) if executor else 1
    deadline = time.monotonic() + contract.get("budgets", {}).get("max_total_seconds", 900)
    outcome = None
    for attempt in range(1, max_attempts + 1):
        if time.monotonic() >= deadline:
            break
        outcome = attempt_cycle(repo, contract, attempt, executor, reviewer, deadline)
        print(f"Attempt {attempt}/{max_attempts}: {outcome['verdict']} | {outcome.get('next_action','')}")
        if outcome["verdict"] != "REWORK" or not executor:
            break
    if outcome is None:
        print("BLOCKED: budget expired before first attempt")
        return 3
    if outcome["verdict"] == "REWORK" and max_attempts > 1 and attempt == max_attempts:
        print("Retry cap reached; manual diagnosis or Architect escalation required.")
    print("Evidence:", repo / ".ai-native" / "runs" / contract["task_id"] / "latest.json")
    return {"PASS": 0, "REWORK": 2, "BLOCKED": 3, "NOT_VERIFIED": 4}[outcome["verdict"]]


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    subs = p.add_subparsers(dest="cmd", required=True)
    v = subs.add_parser("validate", help="check contract without executing commands")
    v.add_argument("--contract", required=True)
    c = subs.add_parser("cycle", help="execute bounded executor -> gates -> reviewer loop")
    c.add_argument("--contract", required=True)
    c.add_argument("--repo", default=".")
    c.add_argument("--executor", help="optional CLI command to invoke actual executor agent")
    c.add_argument("--reviewer", help="CLI command to invoke an actual independent reviewer")
    args = p.parse_args(argv)
    try:
        if args.cmd == "validate":
            validate_contract(load_json(Path(args.contract)))
            print("Contract is valid; nothing has been executed.")
            return 0
        return cycle(args)
    except (ValueError, OSError, json.JSONDecodeError) as exc:
        print("ERROR:", exc, file=sys.stderr)
        return 5


if __name__ == "__main__":
    raise SystemExit(main())
