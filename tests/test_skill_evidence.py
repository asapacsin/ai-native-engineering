"""Skill installation and comparative evidence tests; no paid model calls."""
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from install_skills import install
from skill_catalog import load_skill
from skill_eval import compare, digest


class SkillEvidenceTests(unittest.TestCase):
    def setUp(self):
        self.t = tempfile.TemporaryDirectory()
        self.addCleanup(self.t.cleanup)
        self.repo = Path(self.t.name)
        (self.repo / ".git").mkdir()

    def test_install_dry_run_does_not_mutate(self):
        rows = install(self.repo, ["verify"], dry_run=True)
        self.assertEqual(len(rows), 1)
        self.assertIn("would install", rows[0])
        self.assertFalse((self.repo / ".agents").exists())

    def test_install_idempotent_and_refuses_conflict(self):
        install(self.repo, ["verify"])
        target = self.repo / ".agents" / "skills" / "verify" / "SKILL.md"
        self.assertEqual(target.read_text(), load_skill("verify"))
        self.assertIn("unchanged", install(self.repo, ["verify"])[0])
        target.write_text("different")
        with self.assertRaises(ValueError):
            install(self.repo, ["verify"])

    def test_bad_install_name(self):
        with self.assertRaises(ValueError):
            install(self.repo, ["../verify"])
        self.assertFalse((self.repo / ".agents").exists())

    def make_contract(self, skill=None):
        contract = {"schema_version": 1, "task_id": "test-pair",
                    "goal": "Verify a feature", "acceptance": "Required tests",
                    "gates": [{"id": "unit", "level": "unit", "command": ["true"]}]}
        if skill:
            contract["skill"] = skill
        return contract

    def report(self, contract, passed=True):
        snap = {"fingerprint": "a" * 64}
        return {
            "task_id": contract["task_id"], "contract_hash": digest(contract),
            "verdict": "PASS" if passed else "NOT_VERIFIED",
            "snapshot": snap,
            "reviewed_fingerprint": snap["fingerprint"],
            "reviewed_contract_hash": digest(contract),
            "failed_required_gates": [],
            "control_plane_decision": {"action": "TASK_VERIFIED" if passed else "CONFIGURE_REVIEWER"}
        }

    def test_matching_comparison(self):
        baseline, skilled = self.make_contract(), self.make_contract("verify")
        result = compare(baseline, self.report(baseline, False), skilled, self.report(skilled))
        self.assertEqual(result["pair_result"], "IMPROVED")
        self.assertIn("NOT a live-skill lift estimate", result["claim_limit"])

    def test_rejects_changed_acceptance(self):
        baseline, skilled = self.make_contract(), self.make_contract("verify")
        skilled["acceptance"] = "Easy tests"
        with self.assertRaises(ValueError):
            compare(baseline, self.report(baseline), skilled, self.report(skilled))

    def test_rejects_wrong_task_or_hash(self):
        baseline, skilled = self.make_contract(), self.make_contract("verify")
        altered = self.report(skilled)
        altered["contract_hash"] = "wrong"
        with self.assertRaises(ValueError):
            compare(baseline, self.report(baseline), skilled, altered)

    def test_stale_fingerprint_or_missing_gate_is_not_verified(self):
        baseline, skilled = self.make_contract(), self.make_contract("verify")
        altered = self.report(skilled)
        altered["reviewed_fingerprint"] = "stale"
        result = compare(baseline, self.report(baseline), skilled, altered)
        self.assertEqual(result["pair_result"], "REGRESSED")
        altered = self.report(skilled)
        altered["failed_required_gates"] = ["unit"]
        self.assertFalse(compare(baseline, self.report(baseline), skilled, altered)["skilled_controller_verified"])


if __name__ == "__main__":
    unittest.main()
