#!/usr/bin/env python3
"""Score and rank research directions from an explicit evidence-backed JSON file."""
from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path
from typing import Any

CRITERIA = ("fit", "novelty", "feasibility", "rigor", "impact", "venue_fit")
GATES = ("closest_work", "data_access", "compute_budget", "evaluation_validity")
DEFAULT_WEIGHTS = {"fit": .25, "novelty": .20, "feasibility": .20,
                   "rigor": .15, "impact": .15, "venue_fit": .05}


class InputError(ValueError):
    pass


def read_json(path: str) -> Any:
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, json.JSONDecodeError) as e:
        raise InputError(f"cannot read JSON {path}: {e}") from e


def _number(value: Any, where: str) -> float | None:
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise InputError(f"{where} must be a finite number or null")
    try:
        result = float(value)
    except (OverflowError, ValueError):
        raise InputError(f"{where} must be a finite number or null") from None
    if not math.isfinite(result):
        raise InputError(f"{where} must be a finite number or null")
    if not 1 <= result <= 5:
        raise InputError(f"{where} must be between 1 and 5")
    return result


def _weights(config: Any) -> dict[str, float]:
    if not isinstance(config, dict):
        raise InputError("config must be a JSON object")
    ranking = config.get("ranking", {})
    if not isinstance(ranking, dict):
        raise InputError("ranking must be an object")
    raw = ranking.get("weights", DEFAULT_WEIGHTS)
    if not isinstance(raw, dict) or set(raw) != set(CRITERIA):
        raise InputError("ranking.weights must contain exactly all six known criteria")
    result = {}
    for c in CRITERIA:
        v = raw[c]
        if isinstance(v, bool) or not isinstance(v, (int, float)):
            raise InputError(f"weight {c} must be a finite positive number")
        try:
            value = float(v)
        except (OverflowError, ValueError):
            raise InputError(f"weight {c} must be a finite positive number") from None
        if not math.isfinite(value) or value <= 0:
            raise InputError(f"weight {c} must be a finite positive number")
        result[c] = value
    # Scale before summing to avoid overflow for large but finite weights.
    largest = max(result.values())
    scaled = {k: v / largest for k, v in result.items()}
    total = math.fsum(scaled.values())
    return {k: v / total for k, v in scaled.items()}


def _sensitivity_fraction(config: dict) -> float:
    ranking = config.get("ranking", {})
    fraction = ranking.get("sensitivity_fraction", .20)
    if isinstance(fraction, bool) or not isinstance(fraction, (int, float)) or not math.isfinite(fraction) or not 0 <= fraction < 1:
        raise InputError("ranking.sensitivity_fraction must be finite and in [0, 1)")
    return float(fraction)


def rank(config: Any, payload: Any) -> dict:
    weights = _weights(config)
    fraction = _sensitivity_fraction(config)
    if not isinstance(payload, dict) or not isinstance(payload.get("directions"), list):
        raise InputError("input must be an object with a directions array")
    directions = payload["directions"]
    seen: set[str] = set()
    evaluated = []
    for i, d in enumerate(directions):
        label = f"directions[{i}]"
        if not isinstance(d, dict) or not isinstance(d.get("id"), str) or not d["id"]:
            raise InputError(f"{label}.id must be a nonempty string")
        ident = d["id"]
        if ident in seen:
            raise InputError(f"duplicate direction id: {ident}")
        seen.add(ident)
        if not isinstance(d.get("title"), str) or not d["title"].strip():
            raise InputError(f"{label}.title must be a nonempty string")
        scores = d.get("scores", {})
        gates = d.get("gates", {})
        if not isinstance(scores, dict) or set(scores) - set(CRITERIA):
            raise InputError(f"{label}.scores contains invalid criteria or is not an object")
        if not isinstance(gates, dict) or set(gates) - set(GATES):
            raise InputError(f"{label}.gates contains invalid gates or is not an object")
        reasons, gate_failures, missing = [], [], []
        normalized = {}
        for c in CRITERIA:
            entry = scores.get(c)
            if entry is None:
                missing.append(f"missing {c} score")
                normalized[c] = None
                continue
            if not isinstance(entry, dict):
                raise InputError(f"{label}.scores.{c} must be an object")
            unknown = set(entry) - {"score", "low", "high", "rationale", "evidence"}
            if unknown:
                raise InputError(f"{label}.scores.{c} has unknown fields: {sorted(unknown)}")
            score = _number(entry.get("score"), f"{label}.{c}.score")
            low = _number(entry.get("low"), f"{label}.{c}.low")
            high = _number(entry.get("high"), f"{label}.{c}.high")
            if low is not None and high is not None and low > high:
                raise InputError(f"{label}.{c} requires low <= high")
            if any(x is None for x in (score, low, high)):
                missing.append(f"incomplete {c} score interval")
            elif not low <= score <= high:
                raise InputError(f"{label}.{c} requires low <= score <= high")
            rationale = entry.get("rationale")
            evidence = entry.get("evidence")
            if not isinstance(rationale, str) or not rationale.strip():
                missing.append(f"missing {c} rationale")
            if not isinstance(evidence, list) or not evidence or any(not isinstance(x, str) or not x.strip() for x in evidence):
                missing.append(f"missing {c} evidence references")
            normalized[c] = {"score": score, "low": low, "high": high,
                              "rationale": rationale if isinstance(rationale, str) else None,
                              "evidence": evidence if isinstance(evidence, list) else None}
        gate_results = {}
        for g in GATES:
            entry = gates.get(g)
            if entry is None:
                missing.append(f"missing {g} gate")
                gate_results[g] = {"status": "unknown", "rationale": None}
                continue
            if not isinstance(entry, dict) or set(entry) - {"status", "rationale"}:
                raise InputError(f"{label}.gates.{g} must contain only status and rationale")
            status = entry.get("status")
            if status not in ("pass", "fail", "unknown"):
                raise InputError(f"{label}.gates.{g}.status must be pass, fail, or unknown")
            rationale = entry.get("rationale")
            if not isinstance(rationale, str) or not rationale.strip():
                missing.append(f"missing {g} rationale")
            if status == "fail":
                gate_failures.append(f"{g} failed" + (f": {rationale.strip()}" if isinstance(rationale, str) and rationale.strip() else ""))
            elif status == "unknown":
                missing.append(f"{g} gate is unknown")
            gate_results[g] = {"status": status, "rationale": rationale if isinstance(rationale, str) else None}
        if gate_failures:
            status = "rejected"
        elif missing:
            status = "deferred"
        else:
            status = "eligible"
        record = {"id": ident, "title": d["title"], "status": status,
                  "reasons": sorted(set(gate_failures if status == "rejected" else missing)),
                  "gates": gate_results,
                  "scores": normalized}
        if status == "eligible":
            record["utility"] = _utility(normalized, weights, "score")
            record["utility_interval"] = {"low": _utility(normalized, weights, "low"),
                                          "high": _utility(normalized, weights, "high")}
        evaluated.append(record)

    eligible = sorted((x for x in evaluated if x["status"] == "eligible"),
                      key=lambda x: (-x["utility"], x["id"]))
    sensitivity = _sensitivity(eligible, weights, fraction)
    overlap = []
    for i, a in enumerate(eligible):
        for b in eligible[i + 1:]:
            ia, ib = a["utility_interval"], b["utility_interval"]
            if ia["low"] <= ib["high"] and ib["low"] <= ia["high"]:
                overlap.append([a["id"], b["id"]])
    return {
        "schema_version": 1,
        "method": {"scale": "1-5", "utility": "25 * (weighted_mean - 1)",
                   "interval_note": "Weighted low/high bounds are score ranges, not statistical confidence intervals.",
                   "evidence_note": "Evidence IDs are references only; this script does not verify factual validity."},
        "weights_normalized": weights,
        "sensitivity_fraction": fraction,
        "eligible_ranked": eligible,
        "deferred": [x for x in evaluated if x["status"] == "deferred"],
        "rejected": [x for x in evaluated if x["status"] == "rejected"],
        "sensitivity": sensitivity,
        "overlapping_eligible_intervals": overlap,
        "numerical_leader_ids": _top_ids(eligible),
    }


def _utility(scores: dict, weights: dict[str, float], bound: str) -> float:
    return 25 * (sum(weights[c] * scores[c][bound] for c in CRITERIA) - 1)


def _top_ids(rows: list[dict]) -> list[str]:
    if not rows:
        return []
    top = max(row["utility"] for row in rows)
    return [row["id"] for row in rows if abs(row["utility"] - top) <= 1e-12]


def _sensitivity(eligible: list[dict], weights: dict[str, float], fraction: float) -> dict:
    if not eligible:
        return {"winner_ids": [], "stable_order": False, "rankings": []}
    base = [x["id"] for x in eligible]
    def winners(rows: list[dict], scenario_weights: dict[str, float]) -> list[str]:
        values = [_utility(x["scores"], scenario_weights, "score") for x in rows]
        best = max(values)
        return [row["id"] for row, value in zip(rows, values) if abs(value - best) <= 1e-9]

    scenarios = []
    if fraction:
        for c in CRITERIA:
            for direction in (-1, 1):
                changed = dict(weights)
                changed[c] *= 1 + direction * fraction
                total = sum(changed.values())
                changed = {k: v / total for k, v in changed.items()}
                rows = sorted(eligible, key=lambda x: (-_utility(x["scores"], changed, "score"), x["id"]))
                scenarios.append({"criterion": c, "weight_change": direction * fraction,
                                  "order": [x["id"] for x in rows],
                                  "winner_ids": winners(rows, changed)})
    base_winners = winners(eligible, weights)
    scenario_winners = sorted({ident for s in scenarios for ident in s["winner_ids"]}) if scenarios else base_winners
    return {"winner_ids": scenario_winners,
            "base_winner_ids": base_winners,
            "stable_order": all(s["order"] == base for s in scenarios) if scenarios else True,
            "rankings": scenarios}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", required=True)
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args(argv)
    try:
        result = rank(read_json(args.config), read_json(args.input))
        Path(args.output).write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        return 0
    except (InputError, OSError) as e:
        print(f"rank_directions: {e}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
