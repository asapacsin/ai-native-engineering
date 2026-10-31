import datetime as dt
import json
import sys
import tempfile
import unittest
import urllib.error
from pathlib import Path
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import rank_directions as ranker
import search_papers as searcher


def complete_direction(ident="A", value=4):
    return {
        "id": ident, "title": "Example",
        "scores": {c: {"score": value, "low": value - 1, "high": value,
                        "rationale": "because", "evidence": ["P1"]}
                   for c in ranker.CRITERIA},
        "gates": {g: {"status": "pass", "rationale": "checked"} for g in ranker.GATES},
    }


class RankingTests(unittest.TestCase):
    def run_rank(self, *directions, config=None):
        return ranker.rank(config or {}, {"directions": list(directions)})

    def test_gate_statuses_missing_inputs_and_interval_bounds(self):
        deferred = complete_direction("D"); deferred["scores"].pop("fit")
        deferred["gates"]["data_access"] = {"status": "unknown", "rationale": "pending"}
        rejected = complete_direction("R"); rejected["gates"]["compute_budget"] = {"status": "fail", "rationale": "over budget"}
        result = self.run_rank(complete_direction("E"), deferred, rejected)
        self.assertEqual([x["id"] for x in result["eligible_ranked"]], ["E"])
        self.assertEqual(result["deferred"][0]["id"], "D")
        self.assertEqual(result["rejected"][0]["id"], "R")
        self.assertAlmostEqual(result["eligible_ranked"][0]["utility"], 75)
        self.assertEqual(result["eligible_ranked"][0]["utility_interval"], {"low": 50.0, "high": 75.0})

    def test_no_eligible_means_no_recommendation(self):
        d = complete_direction(); d["gates"]["closest_work"]["status"] = "unknown"
        result = self.run_rank(d)
        self.assertEqual(result["numerical_leader_ids"], [])
        self.assertEqual(result["sensitivity"]["winner_ids"], [])

    def test_invalid_numbers_duplicate_ids_unknown_fields_and_bad_weights(self):
        for value in (float("nan"), float("inf"), True, 0, 5.1):
            d = complete_direction(); d["scores"]["fit"]["score"] = value
            with self.subTest(value=value), self.assertRaises(ranker.InputError):
                self.run_rank(d)
        with self.assertRaisesRegex(ranker.InputError, "duplicate"):
            self.run_rank(complete_direction(), complete_direction())
        d = complete_direction(); d["scores"]["bogus"] = {}
        with self.assertRaises(ranker.InputError):
            self.run_rank(d)
        with self.assertRaisesRegex(ranker.InputError, "weight"):
            self.run_rank(complete_direction(), config={"ranking": {"weights": {"fit": 0}}})
        with self.assertRaisesRegex(ranker.InputError, "exactly all six"):
            self.run_rank(complete_direction(), config={"ranking": {"weights": {"fit": 1}}})
        large_weights = {c: 1e308 for c in ranker.CRITERIA}
        normalized = self.run_rank(complete_direction(), config={"ranking": {"weights": large_weights}})
        self.assertAlmostEqual(sum(normalized["weights_normalized"].values()), 1)
        inverted = complete_direction()
        inverted["scores"]["fit"].update(score=None, low=4, high=3)
        with self.assertRaisesRegex(ranker.InputError, "low <= high"):
            self.run_rank(inverted)

    def test_sensitivity_has_deterministic_tie_breaking_and_overlap(self):
        result = self.run_rank(complete_direction("Z"), complete_direction("A"))
        self.assertEqual([x["id"] for x in result["eligible_ranked"]], ["A", "Z"])
        self.assertEqual(result["overlapping_eligible_intervals"], [["A", "Z"]])
        self.assertTrue(result["sensitivity"]["stable_order"])
        self.assertEqual(result["sensitivity"]["winner_ids"], ["A", "Z"])
        self.assertEqual(len(result["sensitivity"]["rankings"]), 12)
        self.assertEqual(result["numerical_leader_ids"], ["A", "Z"])


class FakeResponse:
    status = 200
    headers = {}
    def __init__(self, data): self.data = data
    def __enter__(self): return self
    def __exit__(self, *args): pass
    def read(self): return json.dumps(self.data).encode()


class RawResponse(FakeResponse):
    def __init__(self, raw, status=200, headers=None):
        self.raw = raw
        self.status = status
        self.headers = headers or {}
    def read(self): return self.raw


class SearchTests(unittest.TestCase):
    def test_success_serializes_metadata_and_truncation_without_secret(self):
        calls = []
        def opener(req, timeout):
            calls.append((req, timeout))
            return FakeResponse({"total": 50, "next": 30, "data": [{"paperId": "p", "title": "x"}]})
        stamp = dt.datetime(2026, 1, 1, tzinfo=dt.timezone.utc)
        result = searcher.fetch("research idea", 30, "2020-2025", "secret", opener, lambda _: None, lambda: stamp)
        self.assertTrue(result["truncated"])
        self.assertEqual(result["next"], 30)
        self.assertTrue(result["raw_metadata_unverified"])
        self.assertNotIn("secret", json.dumps(result))
        self.assertEqual(calls[0][0].get_header("X-api-key"), "secret")
        self.assertEqual(calls[0][1], 20)

    def test_retry_after_respected_and_succeeds(self):
        attempts, delays = [], []
        def opener(req, timeout):
            attempts.append(1)
            if len(attempts) == 1:
                raise urllib.error.HTTPError(req.full_url, 429, "rate", {"Retry-After": "5"}, None)
            return FakeResponse({"total": 0, "data": []})
        result = searcher.fetch("query", opener=opener, sleeper=delays.append)
        self.assertEqual(len(attempts), 2)
        self.assertEqual(delays, [5])
        self.assertFalse(result["truncated"])

    def test_long_retry_after_stops_for_later_retry_without_early_retry(self):
        attempts, delays = [], []
        def opener(req, timeout):
            attempts.append(1)
            raise urllib.error.HTTPError(req.full_url, 429, "rate", {"Retry-After": "11"}, None)
        with self.assertRaisesRegex(searcher.SearchError, "rerun the search later"):
            searcher.fetch("query", opener=opener, sleeper=delays.append)
        self.assertEqual(len(attempts), 1)
        self.assertEqual(delays, [])

    def test_server_failure_stops_after_three_attempts_and_sanitizes_error(self):
        attempts, delays = [], []
        def opener(req, timeout):
            attempts.append(1)
            raise urllib.error.HTTPError(req.full_url + "?api=secret", 503, "secret", {}, None)
        with self.assertRaisesRegex(searcher.SearchError, "503 after 3") as caught:
            searcher.fetch("query", opener=opener, sleeper=delays.append)
        self.assertEqual(len(attempts), 3)
        self.assertNotIn("secret", str(caught.exception))
        self.assertLessEqual(max(delays), 10)

    def test_network_error_is_bounded_and_nonempty_input_required(self):
        with self.assertRaises(searcher.SearchError):
            searcher.fetch("  ")
        with self.assertRaisesRegex(searcher.SearchError, "after 3 attempts"):
            searcher.fetch("q", opener=lambda *a, **k: (_ for _ in ()).throw(TimeoutError()), sleeper=lambda _: None)

    def test_invalid_json_and_wrong_response_shape_fail(self):
        with self.assertRaisesRegex(searcher.SearchError, "invalid JSON"):
            searcher.fetch("q", opener=lambda *a, **k: RawResponse(b"{"))
        with self.assertRaisesRegex(searcher.SearchError, "data array"):
            searcher.fetch("q", opener=lambda *a, **k: FakeResponse({"items": []}))

    def test_main_does_not_overwrite_existing_output_or_call_network(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "papers.json"
            output.write_text("preserve", encoding="utf-8")
            with patch.object(searcher, "fetch") as fetch:
                result = searcher.main(["--query", "q", "--output", str(output)])
            self.assertEqual(result, 2)
            self.assertEqual(output.read_text(encoding="utf-8"), "preserve")
            fetch.assert_not_called()


if __name__ == "__main__":
    unittest.main()
