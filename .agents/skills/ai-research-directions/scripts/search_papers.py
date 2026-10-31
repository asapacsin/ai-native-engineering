#!/usr/bin/env python3
"""Fetch one bounded relevance-search page from the Semantic Scholar Graph API."""
from __future__ import annotations

import argparse
import datetime as dt
import email.utils
import json
import math
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any, Callable

ENDPOINT = "https://api.semanticscholar.org/graph/v1/paper/search"
FIELDS = "title,authors,year,venue,publicationVenue,externalIds,url,openAccessPdf,abstract"


class SearchError(RuntimeError):
    pass


def _retry_delay(value: str | None, attempt: int) -> float | None:
    delay = min(2 ** attempt, 10)
    if value:
        try:
            delay = float(value)
        except ValueError:
            try:
                when = email.utils.parsedate_to_datetime(value)
                if when.tzinfo is None:
                    when = when.replace(tzinfo=dt.timezone.utc)
                delay = (when - dt.datetime.now(dt.timezone.utc)).total_seconds()
            except (TypeError, ValueError, OverflowError):
                pass
        if not math.isfinite(delay) or delay > 10:
            return None
    return max(0.0, min(delay, 10.0))


def _wait_before_retry(sleeper: Callable[[float], None], value: str | None, attempt: int) -> None:
    delay = _retry_delay(value, attempt)
    if delay is None:
        raise SearchError("provider requested a retry later than the bounded wait; rerun the search later")
    sleeper(delay)


def fetch(query: str, limit: int = 30, year: str | None = None, api_key: str | None = None,
          opener: Callable = urllib.request.urlopen,
          sleeper: Callable[[float], None] = time.sleep,
          now: Callable[[], dt.datetime] = lambda: dt.datetime.now(dt.timezone.utc)) -> dict[str, Any]:
    if not query.strip():
        raise SearchError("query must not be empty")
    if isinstance(limit, bool) or not isinstance(limit, int) or not 1 <= limit <= 100:
        raise SearchError("limit must be an integer from 1 to 100")
    params = {"query": query, "limit": str(limit), "fields": FIELDS}
    if year is not None:
        params["year"] = year
    url = ENDPOINT + "?" + urllib.parse.urlencode(params)
    headers = {"User-Agent": "ai-research-directions/1.0"}
    if api_key:
        headers["x-api-key"] = api_key
    request = urllib.request.Request(url, headers=headers, method="GET")
    last_error = "request failed"
    for attempt in range(3):
        try:
            with opener(request, timeout=20) as response:
                status = getattr(response, "status", 200)
                body = response.read()
                if status >= 500 or status == 429:
                    if attempt < 2:
                        _wait_before_retry(sleeper, response.headers.get("Retry-After"), attempt)
                        continue
                    raise SearchError(f"Semantic Scholar returned HTTP {status} after 3 attempts")
                if status < 200 or status >= 300:
                    raise SearchError(f"Semantic Scholar returned HTTP {status}")
            try:
                payload = json.loads(body.decode("utf-8"))
            except (UnicodeDecodeError, json.JSONDecodeError) as e:
                raise SearchError("Semantic Scholar returned invalid JSON") from e
            if not isinstance(payload, dict) or not isinstance(payload.get("data"), list):
                raise SearchError("Semantic Scholar response did not contain a data array")
            next_value = payload.get("next")
            return {
                "schema_version": 1,
                "provider": "Semantic Scholar Academic Graph API",
                "source_url": ENDPOINT,
                "retrieved_at_utc": now().astimezone(dt.timezone.utc).isoformat().replace("+00:00", "Z"),
                "request_parameters": params,
                "raw_metadata_unverified": True,
                "truncated": next_value is not None,
                "next": next_value,
                "total": payload.get("total"),
                "papers": payload["data"],
            }
        except urllib.error.HTTPError as e:
            retry_after = e.headers.get("Retry-After") if e.headers else None
            e.close()
            if e.code in (429,) or 500 <= e.code <= 599:
                last_error = f"Semantic Scholar returned HTTP {e.code}"
                if attempt < 2:
                    _wait_before_retry(sleeper, retry_after, attempt)
                    continue
                raise SearchError(f"{last_error} after 3 attempts") from None
            raise SearchError(f"Semantic Scholar returned HTTP {e.code}") from None
        except SearchError:
            raise
        except (urllib.error.URLError, TimeoutError, OSError) as e:
            # Do not include exception text; it can contain request URLs or headers.
            last_error = "network error or timeout"
            if attempt < 2:
                sleeper(min(2 ** attempt, 10))
                continue
            raise SearchError(f"{last_error} after 3 attempts") from None
    raise SearchError(last_error)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--query", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--limit", type=int, default=30)
    parser.add_argument("--year")
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args(argv)
    target = Path(args.output)
    if target.exists() and not args.overwrite:
        print("search_papers: output exists; use --overwrite to replace it", file=sys.stderr)
        return 2
    try:
        result = fetch(args.query, args.limit, args.year, os.environ.get("SEMANTIC_SCHOLAR_API_KEY"))
        target.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        return 0
    except (SearchError, OSError) as e:
        print(f"search_papers: {e}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
