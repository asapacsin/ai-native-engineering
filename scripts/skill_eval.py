#!/usr/bin/env python3
"""Compare one matched no-skill/skill controller run; never fabricate a lift."""
import argparse
import hashlib
import json
import sys
from pathlib import Path


def read_json(path: Path) -> dict:
    obj = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(obj, dict):
        raise ValueError("expected JSON object: " + str(path))
    return obj


def digest(value: dict) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def verified(report: dict, contract: dict) -> bool:
    if report.get("task_id") != contract.get("task_id"):
        raise ValueError("report/contract task mismatch")
    if report.get("contract_hash") != digest(contract):
        raise ValueError("report/contract digest mismatch")
    if report.get("verdict") != "PASS":
        return False
    snap = report.get("snapshot", {})
    return (
        isinstance(snap, dict) and bool(snap.get("fingerprint"))
        and report.get("reviewed_fingerprint") == snap.get("fingerprint")
        and report.get("reviewed_contract_hash") == digest(contract)
        and not report.get("failed_required_gates")
        and report.get("control_plane_decision", {}).get("action") == "TASK_VERIFIED"
    )


def compare(base_contract: dict, base_report: dict, skill_contract: dict, skill_report: dict) -> dict:
    skill_name = skill_contract.get("skill")
    if not skill_name or "skill" in base_contract:
        raise ValueError("requires a skill-free baseline and one selected skill")
    if {k: v for k, v in skill_contract.items() if k != "skill"} != base_contract:
        raise ValueError("matched contracts must differ only by skill")
    baseline = verified(base_report, base_contract)
    skilled = verified(skill_report, skill_contract)
    return {
        "skill": skill_name,
        "baseline_controller_verified": baseline,
        "skilled_controller_verified": skilled,
        "pair_result": "IMPROVED" if skilled and not baseline else
                       "REGRESSED" if baseline and not skilled else "TIED",
        "claim_limit": "One controller-evidence pair, NOT a live-skill lift estimate. Independently audit actual task behavior, provider usage, and acceptance scope."
    }


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    for name in ("baseline_contract", "baseline_report", "skilled_contract", "skilled_report"):
        p.add_argument("--" + name.replace("_", "-"), required=True, type=Path)
    args = p.parse_args(argv)
    try:
        result = compare(*[read_json(getattr(args, name)) for name in
                           ("baseline_contract", "baseline_report", "skilled_contract", "skilled_report")])
    except (ValueError, OSError, json.JSONDecodeError) as exc:
        print("skill comparison rejected: " + str(exc), file=sys.stderr)
        return 2
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
