#!/usr/bin/env python3
"""Import an explicitly authorized contract list into the existing supervisor registry.

No agent/model calls. Never overwrite a registry or silently invent work.
An ordered list is sequential by default; `ordered: false` permits explicitly
independent tasks and per-task `depends_on` entries.
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

from ai_native import validate_contract
from frontier import check


def json_file(path: Path) -> dict:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"expected JSON object: {path}")
    return data


def resolve_in_repo(repo: Path, name: str) -> Path:
    if not isinstance(name, str) or not name.strip():
        raise ValueError("contract path must be a nonempty string")
    raw = Path(name)
    resolved = (raw if raw.is_absolute() else repo / raw).resolve()
    if not resolved.is_relative_to(repo):
        raise ValueError(f"contract path escapes target repository: {name}")
    return resolved


def assemble(repo: Path, queue: dict) -> dict:
    if queue.get("schema_version") != 1:
        raise ValueError("queue schema_version must equal 1")
    entries = queue.get("contracts")
    if not isinstance(entries, list) or not entries:
        raise ValueError("contracts must be a nonempty list")
    ordered = queue.get("ordered", True)
    if not isinstance(ordered, bool):
        raise ValueError("ordered must be true or false")
    result, seen, previous = [], set(), None
    for index, raw_entry in enumerate(entries, start=1):
        if isinstance(raw_entry, str):
            entry = {"path": raw_entry}
        elif isinstance(raw_entry, dict):
            entry = raw_entry
        else:
            raise ValueError(f"contract entry {index} is neither a string nor an object")
        if set(entry) - {"path", "depends_on"}:
            raise ValueError(f"unknown contract entry fields at position {index}")
        path = resolve_in_repo(repo, entry.get("path"))
        contract = json_file(path)
        validate_contract(contract)
        task_id = contract["task_id"]
        if task_id in seen:
            raise ValueError(f"duplicate task_id: {task_id}")
        seen.add(task_id)
        supplied = entry.get("depends_on", [])
        if not isinstance(supplied, list) or not all(isinstance(d, str) and d for d in supplied):
            raise ValueError(f"depends_on for {task_id} must contain task IDs")
        deps = list(supplied)
        if ordered and previous and previous not in deps:
            deps.append(previous)
        result.append({
            "id": task_id, "owner": "AUTONOMOUS", "status": "NOT_RUN",
            "action": contract["goal"], "depends_on": deps,
            "priority": index, "contract_path": str(path),
        })
        previous = task_id
    registry = {"schema_version": 1, "work": result}
    errors = check(registry)
    if errors:
        raise ValueError("invalid dependency registry: " + "; ".join(errors[:5]))
    return registry


def verify_destination(repo: Path, destination: Path) -> None:
    if destination.exists():
        raise FileExistsError(f"registry exists; never overwrite progress: {destination}")
    try:
        relative = destination.relative_to(repo)
    except ValueError:
        return  # Explicit path outside the repo is allowed for trusted runtime state.
    tracked = subprocess.run(
        ["git", "-C", str(repo), "ls-files", "--error-unmatch", "--", str(relative)],
        capture_output=True,
    )
    if tracked.returncode == 0:
        raise ValueError("registry would overwrite a tracked source file")
    ignored = subprocess.run(
        ["git", "-C", str(repo), "check-ignore", "-q", "--", str(relative)],
        capture_output=True,
    )
    if ignored.returncode != 0:
        raise ValueError("registry must be gitignored: add .ai-native/ to the target .gitignore")


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", required=True, help="Target Git repository")
    parser.add_argument("--queue", required=True, help="Approved queue JSON; contract paths relative to --repo")
    parser.add_argument("--registry", help="Mutable output; default <repo>/.ai-native/work.json")
    parser.add_argument("--dry-run", action="store_true", help="Validate and display without writing")
    args = parser.parse_args(argv)
    repo = Path(args.repo).resolve()
    queue_path = Path(args.queue)
    if not queue_path.is_absolute():
        queue_path = repo / queue_path
    registry_path = (Path(args.registry) if args.registry else repo / ".ai-native/work.json").resolve()
    try:
        git = subprocess.run(["git", "-C", str(repo), "rev-parse", "--verify", "HEAD"], capture_output=True)
        if git.returncode != 0:
            raise ValueError("target repository must have an initial Git commit")
        plan = assemble(repo, json_file(queue_path.resolve()))
        print(f"VALID QUEUE: {len(plan['work'])} approved task contracts")
        for item in plan["work"]:
            print(f"  {item['id']} <- {', '.join(item['depends_on']) or 'no dependencies'}")
        if args.dry_run:
            print("DRY RUN: no files written; no model invoked")
            return 0
        verify_destination(repo, registry_path)
        registry_path.parent.mkdir(parents=True, exist_ok=True)
        with registry_path.open("x", encoding="utf-8") as output:
            json.dump(plan, output, ensure_ascii=False, indent=2)
            output.write("\n")
        print(f"REGISTRY CREATED: {registry_path}")
        print("NEXT: scripts/supervisor.py --repo <target> --registry <registry> (after configuring authenticated agent commands)")
        return 0
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print("BOOTSTRAP BLOCKED: " + str(exc), file=sys.stderr)
        return 3


if __name__ == "__main__":
    raise SystemExit(main())
