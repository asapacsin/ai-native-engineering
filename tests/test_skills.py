"""Static repository-skill contract checks; these are not live skill evals."""
import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKILLS = ("goal", "start", "reproduce", "fix", "verify", "review-packet", "continue", "handoff", "create-skill")


class SkillManifestTests(unittest.TestCase):
    def test_all_procedures_have_two_discovery_manifests(self):
        for skill in SKILLS:
            canonical = ROOT / "skills" / (skill + ".md")
            self.assertTrue(canonical.is_file(), canonical)
            self.assertGreater(len(canonical.read_text(encoding="utf-8")), 250)
            for client in (".claude", ".agents"):
                manifest = ROOT / client / "skills" / skill / "SKILL.md"
                self.assertTrue(manifest.is_file(), manifest)
                contents = manifest.read_text(encoding="utf-8")
                self.assertTrue(contents.startswith("---\n"), manifest)
                self.assertRegex(contents, r"(?m)^name: " + re.escape(skill) + r"$")
                self.assertRegex(contents, r"(?m)^description: .{35,}$")
                self.assertIn("../../../skills/" + skill + ".md", contents)
                self.assertLess(len(contents.split("---", 2)[1]), 1536)

    def test_goal_covers_truthful_terminal_states_and_real_runner(self):
        source = (ROOT / "skills" / "goal.md").read_text(encoding="utf-8")
        for phrase in ("supervisor.py", "frontier.py", "independent", "NOT_VERIFIED",
                       "BLOCKED_EXTERNAL", "HUMAN_REQUIRED", "BOUND_REACHED",
                       "requirements", "Codex Cloud", "gitignored"):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, source)

    def test_evaluation_prompts_are_reviewable(self):
        data = json.loads((ROOT / "skills" / "evals.json").read_text(encoding="utf-8"))
        self.assertEqual(data["schema_version"], 1)
        self.assertGreaterEqual(len(data["evals"]), 5)
        for item in data["evals"]:
            self.assertIn(item["skill"], SKILLS)
            self.assertTrue(item["prompt"].strip())
            self.assertGreaterEqual(len(item["assertions"]), 2)


if __name__ == "__main__":
    unittest.main()
