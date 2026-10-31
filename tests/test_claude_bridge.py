import json
import os
import stat
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import claude_bridge as bridge

PACKET = {"snapshot": {"fingerprint": "f" * 64}, "contract_hash": "c" * 64}
REVIEW = {"verdict": "PASS", "reviewed_fingerprint": "f" * 64, "reviewed_contract_hash": "c" * 64,
          "findings": [], "next_action": "merge after CI evidence"}


def envelope(**overrides):
    data = {"type": "result", "is_error": False, "structured_output": REVIEW,
            "modelUsage": {"claude-opus-5-5": {"outputTokens": 10}}}
    data.update(overrides)
    return json.dumps(data)


class ClaudeCommandTests(unittest.TestCase):
    def test_reviewer_defaults_to_opus_5_5_high_read_only(self):
        with patch.dict(os.environ, {}, clear=True):
            args = bridge.claude_command()
        self.assertEqual(args[args.index("--model") + 1], "claude-opus-5-5")
        self.assertEqual(args[args.index("--effort") + 1], "high")
        self.assertEqual(args[args.index("--permission-mode") + 1], "dontAsk")
        self.assertEqual(args[args.index("--tools") + 1], "Read,Grep,Glob,Bash")
        for tool in ("Edit", "Write", "NotebookEdit"):
            self.assertIn(tool, args[args.index("--disallowedTools") + 1:])
        self.assertNotIn("--max-budget-usd", args)
        self.assertEqual(json.loads(args[args.index("--json-schema") + 1]), bridge.REVIEW_SCHEMA)

    def test_model_effort_and_budget_overrides(self):
        env = {"AI_NATIVE_REVIEWER_MODEL": "claude-sonnet-5-5", "AI_NATIVE_REVIEWER_EFFORT": "xhigh",
               "AI_NATIVE_REVIEWER_MAX_BUDGET_USD": "2.5"}
        with patch.dict(os.environ, env, clear=True):
            args = bridge.claude_command()
        self.assertEqual(args[args.index("--model") + 1], "claude-sonnet-5-5")
        self.assertEqual(args[args.index("--effort") + 1], "xhigh")
        self.assertEqual(args[args.index("--max-budget-usd") + 1], "2.5")

    def test_invalid_effort_and_budget_are_rejected(self):
        for env in ({"AI_NATIVE_REVIEWER_EFFORT": "fast"}, {"AI_NATIVE_REVIEWER_MAX_BUDGET_USD": "0"}):
            with self.subTest(env=env), patch.dict(os.environ, env, clear=True), self.assertRaises(ValueError):
                bridge.claude_command()


class ExtractReviewTests(unittest.TestCase):
    def test_structured_output_is_returned(self):
        self.assertEqual(bridge.extract_review(envelope(), PACKET, "claude-opus-5-5"), REVIEW)

    def test_result_text_fallback(self):
        out = envelope(structured_output=None, result=json.dumps(REVIEW))
        self.assertEqual(bridge.extract_review(out, PACKET, "claude-opus-5-5"), REVIEW)

    def test_failures_become_not_verified(self):
        cases = {
            "not json": "garbage",
            "error": envelope(is_error=True, subtype="error_max_turns"),
            "wrong model": envelope(modelUsage={"claude-haiku-5-5": {}}),
            "no review": envelope(structured_output=None, result="looks good to me"),
            "bad shape": envelope(structured_output={"verdict": "PASS"}),
        }
        for name, out in cases.items():
            with self.subTest(case=name):
                review = bridge.extract_review(out, PACKET, "claude-opus-5-5")
                self.assertEqual(review["verdict"], "NOT_VERIFIED")
                self.assertEqual(review["reviewed_fingerprint"], "f" * 64)


class FakeClaudeProcessTests(unittest.TestCase):
    """Runs the bridge against a test-double `claude` executable; no model is called."""

    def run_bridge(self, fake_stdout: str, code: int = 0):
        with tempfile.TemporaryDirectory() as directory:
            folder = Path(directory)
            fake = folder / "claude"
            argv_log = folder / "argv.json"
            fake.write_text("#!/usr/bin/env python3\nimport json, sys\n"
                            f"json.dump(sys.argv[1:], open({str(argv_log)!r}, 'w'))\n"
                            "sys.stdin.read()\n"
                            f"sys.stdout.write({fake_stdout!r})\nsys.exit({code})\n")
            fake.chmod(fake.stat().st_mode | stat.S_IEXEC)
            packet, result = folder / "packet.json", folder / "result.json"
            packet.write_text(json.dumps(PACKET))
            env = {"PATH": str(folder) + os.pathsep + os.environ["PATH"],
                   "AI_NATIVE_REVIEW_PACKET": str(packet), "AI_NATIVE_REVIEW_RESULT": str(result)}
            proc = subprocess.run([sys.executable, str(ROOT / "scripts" / "claude_bridge.py"), "reviewer"],
                                  env=env, capture_output=True, text=True, timeout=30)
            return proc, json.loads(result.read_text()), json.loads(argv_log.read_text())

    def test_pass_review_is_written(self):
        proc, review, argv = self.run_bridge(envelope())
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(review, REVIEW)
        self.assertEqual(argv[argv.index("--model") + 1], "claude-opus-5-5")

    def test_crashed_cli_is_not_verified(self):
        proc, review, _ = self.run_bridge("", code=1)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(review["verdict"], "NOT_VERIFIED")


if __name__ == "__main__":
    unittest.main()
