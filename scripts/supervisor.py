#!/usr/bin/env python3
"""Durable, bounded supervisor for explicitly authorized task contracts.

Single-process orchestration; no LLM is invoked without an external configured
executor/reviewer. This does not discover tasks, configure branch rules, or
automatically merge code.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
import time
from pathlib import Path

from ai_native import load_json, save_json, work_snapshot
from control_plane import canonical_hash, decide_frontier, verify_decision
from frontier import check

CONTROLLER = Path(__file__).resolve().with_name("ai_native.py")


def verified_task(repo: Path, contract: dict, task_id: str) -> bool:
    """Only current, externally reviewed, deterministic TASK_VERIFIED is success."""
    try:
        report = load_json(repo / ".ai-native" / "runs" / task_id / "latest.json")
        decision = report.get("control_plane_decision", {})
        snapshot = work_snapshot(repo)
        digest = canonical_hash(contract)
        return (
            report.get("task_id") == task_id
            and report.get("verdict") == "PASS"
            and isinstance(decision, dict)
            and verify_decision(decision)
            and decision.get("action") == "TASK_VERIFIED"
            and report.get("snapshot", {}).get("fingerprint") == snapshot["fingerprint"]
            and report.get("reviewed_fingerprint") == snapshot["fingerprint"]
            and report.get("contract_hash") == digest
            and report.get("reviewed_contract_hash") == digest
        )
    except (OSError, KeyError, TypeError, ValueError, json.JSONDecodeError):
        return False


def task_evidence_reference(repo: Path, contract: dict, task_id: str) -> dict:
    """Write a hash-bound attestation only after independent cycle validation."""
    if not verified_task(repo, contract, task_id):
        raise ValueError("cannot create evidence without current verified task")
    snapshot = work_snapshot(repo)
    report_path = repo / ".ai-native" / "runs" / task_id / "latest.json"
    proof = {
        "status": "PASS",
        "task_id": task_id,
        "source_fingerprint": snapshot["fingerprint"],
        "contract_hash": canonical_hash(contract),
        "report_sha256": hashlib.sha256(report_path.read_bytes()).hexdigest(),
        "producer": "ai-native/supervisor",
    }
    evidence_path = repo / ".ai-native" / "evidence" / (task_id + ".json")
    save_json(evidence_path, proof)
    return {
        "path": ".ai-native/evidence/" + task_id + ".json",
        "sha256": hashlib.sha256(evidence_path.read_bytes()).hexdigest()
    }


def resolve_contract(registry_path: Path, item: dict) -> tuple[Path, dict]:
    name = item.get("contract_path")
    if not isinstance(name, str) or not name.strip():
        raise ValueError("authorized task must provide contract_path")
    path = Path(name)
    if not path.is_absolute():
        path = registry_path.parent / path
    contract = load_json(path.resolve())
    if contract.get("task_id") != item["id"]:
        raise ValueError("task_id mismatch between registry and contract")
    return path.resolve(), contract


def write_registry(path: Path, data: dict, expected_hash: str) -> None:
    if canonical_hash(load_json(path)) != expected_hash:
        raise RuntimeError("work registry changed concurrently; refusing to overwrite")
    save_json(path, data)


def reconcile_interrupted(repo: Path, registry_path: Path, data: dict) -> dict:
    """Never silently claim success when a previous run was interrupted."""
    running = [item for item in data["work"] if item["status"] == "RUNNING"]
    if not running:
        return data
    before = canonical_hash(data)
    for item in running:
        try:
            _, contract = resolve_contract(registry_path, item)
            passed = verified_task(repo, contract, item["id"])
        except (OSError, ValueError, KeyError, TypeError):
            passed = False
        if passed:
            item["status"] = "PASS"
            item["evidence"] = [task_evidence_reference(repo, contract, item["id"])]
            item.pop("blocked_by", None)
        else:
            item["status"] = "BLOCKED_EXTERNAL"
            item["blocked_by"] = "interrupted execution without current verified evidence; human diagnosis required"
    write_registry(registry_path, data, before)
    return data


def acquire_lock(repo: Path) -> tuple[int, Path]:
    directory = repo / ".ai-native"
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / "supervisor.lock"
    try:
        fd = os.open(str(path), os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    except FileExistsError as exc:
        try:
            pid = int(path.read_text(encoding="utf-8").strip())
            if pid <= 0:
                raise ValueError("invalid lock owner")
            os.kill(pid, 0)
        except ProcessLookupError:
            # Only an absent process owner can be safely reclaimed automatically.
            path.unlink()
            fd = os.open(str(path), os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        except (OSError, ValueError) as error:
            raise RuntimeError("existing supervisor lock cannot be safely reclaimed: "
                               + str(path)) from error
        else:
            raise RuntimeError("supervisor lock owned by a live process: " + str(path)) from exc
    os.write(fd, str(os.getpid()).encode())
    return fd, path


def ensure_registry_is_runtime_state(repo: Path, registry_path: Path) -> None:
    """Mutable state must not change the reviewed source tree during a cycle."""
    try:
        relative = registry_path.resolve().relative_to(repo.resolve())
    except ValueError:
        return  # Trusted state stored outside the project worktree.
    tracked = subprocess.run(["git", "-C", str(repo), "ls-files",
                              "--error-unmatch", "--", str(relative)],
                             capture_output=True)
    if tracked.returncode == 0:
        raise ValueError("mutable work registry is tracked source; use a separate "
                         "untracked gitignored runtime registry")
    ignored = subprocess.run(["git", "-C", str(repo), "check-ignore", "-q",
                              "--", str(relative)], capture_output=True)
    if ignored.returncode != 0:
        raise ValueError("mutable work registry inside repo must be gitignored "
                         "(recommended: .ai-native/work.json)")


def run(repo: Path, registry_path: Path, max_tasks: int, max_seconds: int) -> int:
    ensure_registry_is_runtime_state(repo, registry_path)
    fd, lock_path = acquire_lock(repo)
    began = time.monotonic()
    count = 0
    try:
        data = load_json(registry_path)
        if check(data):
            raise ValueError("invalid work registry: " + "; ".join(check(data)[:5]))
        reconcile_interrupted(repo, registry_path, data)
        while count < max_tasks and time.monotonic() - began < max_seconds:
            data = load_json(registry_path)
            errors = check(data)
            if errors:
                raise ValueError("invalid work registry: " + "; ".join(errors[:5]))
            decision = decide_frontier(data["work"])
            if not verify_decision(decision):
                raise ValueError("frontier decision checksum invalid")
            if decision["action"] != "CONTINUE_FRONTIER":
                print(json.dumps({"action": decision["action"],
                                  "tasks_attempted": count, "reasons": decision["reasons"]}))
                return 0 if decision["action"] == "STOP_COMPLETE" else 3
            item_id = decision["frontier"]["autonomous"][0]["id"]
            item = next(entry for entry in data["work"] if entry["id"] == item_id)
            try:
                contract_path, contract = resolve_contract(registry_path, item)
                from ai_native import validate_contract
                validate_contract(contract)
            except (OSError, ValueError, KeyError, TypeError) as exc:
                before = canonical_hash(data)
                item["status"] = "BLOCKED_EXTERNAL"
                item["blocked_by"] = "missing or invalid authorized contract: " + type(exc).__name__
                write_registry(registry_path, data, before)
                count += 1
                continue

            before = canonical_hash(data)
            item["status"] = "RUNNING"
            item["lease_expired"] = False
            write_registry(registry_path, data, before)
            save_json(repo / ".ai-native/supervisor-checkpoint.json",
                      {"schema_version": 1, "task_id": item_id,
                       "contract_hash": canonical_hash(contract),
                       "base_fingerprint": work_snapshot(repo)["fingerprint"],
                       "state": "RUNNING"})
            remaining = max(1, int(max_seconds - (time.monotonic() - began)))
            try:
                result = subprocess.run(
                    [sys.executable, str(CONTROLLER), "cycle", "--repo", str(repo),
                     "--contract", str(contract_path)],
                    cwd=repo, capture_output=True, text=True, timeout=remaining
                )
                passed = result.returncode == 0 and verified_task(repo, contract, item_id)
                diagnostic = "controller exit " + str(result.returncode)
            except subprocess.TimeoutExpired:
                passed = False
                diagnostic = "supervisor time budget exceeded"

            current = load_json(registry_path)
            if canonical_hash(current) != canonical_hash(data):
                raise RuntimeError("registry changed during execution; refusing to overwrite")
            current_item = next(entry for entry in current["work"] if entry["id"] == item_id)
            if passed:
                current_item["status"] = "PASS"
                current_item["evidence"] = [task_evidence_reference(repo, contract, item_id)]
                current_item.pop("blocked_by", None)
            else:
                current_item["status"] = "BLOCKED_EXTERNAL"
                current_item["blocked_by"] = diagnostic + "; inspect current gate/review artifacts"
            current_item.pop("lease_expired", None)
            write_registry(registry_path, current, canonical_hash(data))
            save_json(repo / ".ai-native/supervisor-checkpoint.json",
                      {"schema_version": 1, "task_id": item_id,
                       "contract_hash": canonical_hash(contract),
                       "state": "VERIFIED" if passed else "BLOCKED",
                       "evidence": ".ai-native/runs/" + item_id + "/latest.json" if passed else None})
            count += 1
        print(json.dumps({"action": "BOUND_REACHED", "tasks_attempted": count}))
        return 3
    finally:
        os.close(fd)
        lock_path.unlink(missing_ok=True)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", required=True)
    parser.add_argument("--registry", required=True)
    parser.add_argument("--max-tasks", type=int, default=10)
    parser.add_argument("--max-seconds", type=int, default=1800)
    args = parser.parse_args(argv)
    if not 1 <= args.max_tasks <= 100 or not 1 <= args.max_seconds <= 86400:
        parser.error("bounded max-tasks 1..100 and max-seconds 1..86400 required")
    try:
        return run(Path(args.repo).resolve(), Path(args.registry).resolve(),
                   args.max_tasks, args.max_seconds)
    except (OSError, ValueError, RuntimeError) as exc:
        print("SUPERVISOR_BLOCKED: " + str(exc), file=sys.stderr)
        return 5


if __name__ == "__main__":
    raise SystemExit(main())
