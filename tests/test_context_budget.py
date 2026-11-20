"""Behavioral tests for portable spec-section retrieval and optional Read budget hook."""
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SECTION = ROOT / "scripts" / "spec_section.py"
GUARD = ROOT / "scripts" / "read_guard.py"

class ContextBudgetTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name) / "feature.md"
        self.path.write_text(
            "# Feature\nIntro\n## 1. First\nalpha\n### 1.1 Details\nbeta\n"
            "~~~markdown\n## 123. Not a heading\n~~~\n"
            "## 2. Second\n" + ("payload " * 300) + "\n", encoding="utf-8")

    def section(self, *args):
        return subprocess.run([sys.executable, str(SECTION), str(self.path), *args],
                              capture_output=True, text=True)

    def guard(self, event, limit="1"):
        data = event if isinstance(event, str) else json.dumps(event)
        env = dict(os.environ, AI_NATIVE_READ_GUARD_KB=limit)
        return subprocess.run([sys.executable, str(GUARD)], input=data,
                              capture_output=True, text=True, env=env)

    def test_list_sections_skips_fenced_headings(self):
        out = self.section()
        self.assertEqual(out.returncode, 0, out.stderr)
        self.assertIn("1. First", out.stdout)
        self.assertIn("1.1 Details", out.stdout)
        self.assertNotIn("123. Not a heading", out.stdout)

    def test_number_and_title_retrieve_only_needed_section(self):
        first = self.section("1")
        self.assertEqual(first.returncode, 0, first.stderr)
        self.assertIn("## 1. First", first.stdout)
        self.assertIn("### 1.1 Details", first.stdout)
        self.assertNotIn("## 2. Second", first.stdout)
        sub = self.section("§1.1")
        self.assertEqual(sub.returncode, 0, sub.stderr)
        self.assertIn("beta", sub.stdout)
        self.assertNotIn("alpha", sub.stdout)
        self.assertEqual(self.section("2. Second", "--max-bytes", "0").returncode, 0)

    def test_bad_section_and_large_section_fail_without_dump(self):
        self.assertNotEqual(self.section("404").returncode, 0)
        oversized = self.section("2", "--max-bytes", "100")
        self.assertEqual(oversized.returncode, 2)
        self.assertEqual(oversized.stdout, "")
        self.assertIn("Read with offset/limit", oversized.stderr)

    def test_full_large_read_denied(self):
        event = {"tool_name": "Read", "cwd": self.temp.name,
                 "tool_input": {"file_path": "feature.md"}}
        out = self.guard(event)
        self.assertEqual(out.returncode, 0, out.stderr)
        result = json.loads(out.stdout)["hookSpecificOutput"]
        self.assertEqual(result["permissionDecision"], "deny")
        self.assertIn("spec_section.py", result["permissionDecisionReason"])

    def test_scoped_small_binary_disabled_and_malformed_pass(self):
        event = {"tool_name": "Read", "tool_input": {"file_path": str(self.path)}}
        for extra, limit in [({"offset": 1}, "1"), ({"limit": 20}, "1"), ({}, "0")]:
            candidate = dict(event, tool_input={**event["tool_input"], **extra})
            self.assertEqual(self.guard(candidate, limit).stdout, "")
        small = Path(self.temp.name) / "small.md"
        small.write_text("short", encoding="utf-8")
        self.assertEqual(self.guard({"tool_name": "Read", "tool_input": {"file_path": str(small)}}).stdout, "")
        binary = Path(self.temp.name) / "image.png"
        binary.write_bytes(b"x" * 5000)
        self.assertEqual(self.guard({"tool_name": "Read", "tool_input": {"file_path": str(binary)}}).stdout, "")
        self.assertEqual(self.guard("not json").stdout, "")
        self.assertEqual(self.guard({"tool_name": "Grep", "tool_input": {"path": str(self.path)}}).stdout, "")

    def test_read_budget_hook_registered_separately_from_write_scope_guard(self):
        settings = json.loads((ROOT / ".claude" / "settings.json").read_text(encoding="utf-8"))
        hooks = [entry for entry in settings["hooks"]["PreToolUse"] if entry.get("matcher") == "Read"]
        self.assertTrue(any("scripts/read_guard.py" in hook["command"]
                            for entry in hooks for hook in entry["hooks"]))
        self.assertTrue(any("scripts/pre_tool_guard.py" in hook["command"]
                            for entry in settings["hooks"]["PreToolUse"] for hook in entry["hooks"]))

if __name__ == "__main__":
    unittest.main()
