import os
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import codex_bridge as bridge


class CodexBridgeTests(unittest.TestCase):
    def test_executor_defaults_to_luna_medium_write(self):
        with patch.dict(os.environ, {}, clear=True):
            args = bridge.codex_command("executor", Path("/tmp/o"))
        self.assertEqual(args[args.index("--model") + 1], "gpt-6-luna")
        self.assertIn("model_reasoning_effort=medium", args)
        self.assertEqual(args[args.index("--sandbox") + 1], "workspace-write")

    def test_reviewer_defaults_to_astra_high_read_only(self):
        with patch.dict(os.environ, {}, clear=True):
            args = bridge.codex_command("reviewer", Path("/tmp/o"), Path("/tmp/s"))
        self.assertEqual(args[args.index("--model") + 1], "gpt-6-astra")
        self.assertIn("model_reasoning_effort=high", args)
        self.assertEqual(args[args.index("--sandbox") + 1], "read-only")
        self.assertIn("--output-schema", args)

    def test_role_timeout_defaults_match_controller_caps(self):
        with patch.dict(os.environ, {}, clear=True):
            self.assertEqual(bridge.role_timeout_seconds("executor"), 290)
            self.assertEqual(bridge.role_timeout_seconds("reviewer"), 230)

    def test_role_timeout_honors_controller_budget(self):
        with patch.dict(os.environ, {"AI_NATIVE_STEP_TIMEOUT_SECONDS": "37"}, clear=True):
            self.assertEqual(bridge.role_timeout_seconds("executor"), 37)
            self.assertEqual(bridge.role_timeout_seconds("reviewer"), 37)

    def test_invalid_role_timeout_fails_closed(self):
        for value in ("0", "-1", "nan", "12.5", "86401"):
            with self.subTest(value=value), patch.dict(
                os.environ, {"AI_NATIVE_STEP_TIMEOUT_SECONDS": value}, clear=True
            ):
                with self.assertRaises(ValueError):
                    bridge.role_timeout_seconds("executor")

    def test_reviewer_schema_requires_fingerprint_and_verdict(self):
        self.assertEqual(set(bridge.REVIEW_SCHEMA["required"]),
                         {"verdict", "reviewed_fingerprint", "reviewed_contract_hash", "findings", "next_action"})

    def test_review_prompt_avoids_self_review(self):
        content = bridge.role_prompt("reviewer", {"snapshot": {"fingerprint": "f00"}})
        self.assertIn("INDEPENDENT READ-ONLY", content)
        self.assertIn("git diff HEAD", content)


if __name__ == "__main__":
    unittest.main()
