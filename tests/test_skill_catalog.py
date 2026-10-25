"""Portable skill dispatch tests; no paid models or target products are invoked."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from ai_native import validate_contract
from codex_bridge import role_prompt
from skill_catalog import available_skills, load_skill


def contract(skill_name="verify"):
    result = {
        "schema_version": 1, "task_id": "skill-smoke", "goal": "Evidence-fresh verification",
        "acceptance": "Focused tests pass",
        "gates": [{"id": "unit", "level": "unit", "command": ["python3", "--version"]}]
    }
    if skill_name is not None:
        result["skill"] = skill_name
    return result


class SkillCatalogTests(unittest.TestCase):
    def test_bundled_skills_are_well_formed(self):
        self.assertEqual(available_skills(), ["token-efficient-task", "verify"])
        for name in available_skills():
            self.assertIn("name: " + name, load_skill(name))

    def test_explicit_skill_is_validated_in_contract(self):
        validate_contract(contract("verify"))
        validate_contract(contract(None))  # Existing contracts remain valid.
        for value in ("../fix", "/etc/passwd", "not-installed", "", 10, None):
            invalid = contract()
            invalid["skill"] = value
            with self.subTest(value=value), self.assertRaises(ValueError):
                validate_contract(invalid)

    def test_executor_receives_requested_skill_in_foreign_project(self):
        prompt = role_prompt("executor", contract("verify"))
        self.assertIn("Selected portable skill: verify", prompt)
        self.assertIn("Fix a reproduced defect", prompt)
        self.assertIn("Task contract:", prompt)
        self.assertIn("Feedback from prior attempt", prompt)

    def test_legacy_contract_does_not_inject_skill(self):
        prompt = role_prompt("executor", contract(None))
        self.assertNotIn("Selected portable skill:", prompt)

    def test_reviewer_never_receives_executor_skill(self):
        prompt = role_prompt("reviewer", contract("verify"))
        self.assertNotIn("Selected portable skill:", prompt)
        self.assertIn("INDEPENDENT READ-ONLY", prompt)


if __name__ == "__main__":
    unittest.main()
