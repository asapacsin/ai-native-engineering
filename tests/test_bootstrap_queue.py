"""Queue-to-supervisor bootstrap; no model sessions or network required."""
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from bootstrap_queue import assemble, verify_destination, main


def contract(task_id):
    return {
        "schema_version": 1, "task_id": task_id, "goal": "Verify " + task_id,
        "acceptance": "A factual independent review confirms completion",
        "budgets": {"max_attempts": 2, "max_total_seconds": 120},
        "gates": [{"id": "unit", "level": "static", "required": True,
                   "command": ["python", "-c", "print('gate')"]}],
    }


class QueueBootstrapTests(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.repo = Path(directory.name)
        subprocess.run(["git", "init", "-q"], cwd=self.repo, check=True)
        (self.repo / ".gitignore").write_text(".ai-native/\n", encoding="utf-8")
        (self.repo / "one.json").write_text(json.dumps(contract("one")), encoding="utf-8")
        (self.repo / "two.json").write_text(json.dumps(contract("two")), encoding="utf-8")
        self.queue = {"schema_version": 1, "contracts": ["one.json", "two.json"]}
        (self.repo / "queue.json").write_text(json.dumps(self.queue), encoding="utf-8")
        subprocess.run(["git", "add", "."], cwd=self.repo, check=True)
        subprocess.run(["git", "-c", "user.name=Test", "-c", "user.email=test@example.invalid",
                        "commit", "-qm", "init"], cwd=self.repo, check=True)

    def test_linear_queue_is_dependency_aware(self):
        result = assemble(self.repo, self.queue)
        self.assertEqual(result["work"][0]["depends_on"], [])
        self.assertEqual(result["work"][1]["depends_on"], ["one"])
        self.assertEqual(result["work"][0]["status"], "NOT_RUN")

    def test_independent_tasks(self):
        result = assemble(self.repo, {**self.queue, "ordered": False})
        self.assertEqual(result["work"][1]["depends_on"], [])

    def test_explicit_dependencies(self):
        task = {"path": "two.json", "depends_on": ["one"]}
        result = assemble(self.repo, {**self.queue, "ordered": False,
                                      "contracts": ["one.json", task]})
        self.assertEqual(result["work"][1]["depends_on"], ["one"])

    def test_duplicate_and_missing_contract_fail(self):
        with self.assertRaisesRegex(ValueError, "duplicate task_id"):
            assemble(self.repo, {**self.queue, "contracts": ["one.json", "one.json"]})
        with self.assertRaises(FileNotFoundError):
            assemble(self.repo, {**self.queue, "contracts": ["missing.json"]})

    def test_escape_and_cycle_are_rejected(self):
        with self.assertRaisesRegex(ValueError, "escapes"):
            assemble(self.repo, {**self.queue, "contracts": ["../outside.json"]})
        bad = {**self.queue, "ordered": False, "contracts": [
            {"path": "one.json", "depends_on": ["two"]},
            {"path": "two.json", "depends_on": ["one"]}]}
        with self.assertRaisesRegex(ValueError, "cycle"):
            assemble(self.repo, bad)

    def test_dry_run_does_not_write_registry(self):
        result = main(["--repo", str(self.repo), "--queue", "queue.json", "--dry-run"])
        self.assertEqual(result, 0)
        self.assertFalse((self.repo / ".ai-native/work.json").exists())

    def test_write_and_no_overwrite(self):
        result = main(["--repo", str(self.repo), "--queue", "queue.json"])
        self.assertEqual(result, 0)
        registry = self.repo / ".ai-native/work.json"
        self.assertEqual(len(json.loads(registry.read_text())["work"]), 2)
        self.assertEqual(main(["--repo", str(self.repo), "--queue", "queue.json"]), 3)
        self.assertEqual(len(json.loads(registry.read_text())["work"]), 2)

    def test_unignored_registry_rejected(self):
        (self.repo / ".gitignore").write_text("build/\n", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "gitignored"):
            verify_destination(self.repo, self.repo / ".ai-native/work.json")


if __name__ == "__main__":
    unittest.main()
