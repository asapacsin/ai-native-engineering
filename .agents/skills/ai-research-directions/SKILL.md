---
name: ai-research-directions
description: "Scout AI research directions from an initial idea using top-conference papers, current implementation practice, and official documentation. Map closest prior work, assess fit, novelty and feasibility, and produce an evidence-backed shortlist and pilot plan. Use for research ideation and literature-to-proposal reviews."
---

# AI Research Directions

Turn an initial idea into a defensible research choice. Preserve the user's problem and constraints; a fashionable adjacent topic is not automatically a better fit. A valid result may be a refined idea, a reproduction or analysis study, or a recommendation to stop.

## Start with a research brief

Copy [assets/research-config.json](assets/research-config.json) into the user's project, set the idea, and resolve the dates at run time. Treat this JSON as a brief for the agent, not an automatically executed pipeline. Only its `ranking` object is consumed by the ranking script. Natural-language requests can override any default; record changes in the run's config.

Capture the problem, proposed mechanism, desired contribution, intended users, constraints, resources and success criterion. If the idea itself is missing, ask for it. If resources are unknown, continue the literature review with explicit assumptions, but leave dependent feasibility gates unknown. Do not assume access to GPUs, proprietary data, paid APIs or human participants.

Use quick, standard or deep mode as scope guidance, not a quota to fill. Default to standard. Save runs inside the user's research project, e.g. `research/<topic>/<date>/`; read existing project state on resumption. Keep research findings out of the installed skill.

## Discover and verify

Read [references/search-and-evidence.md](references/search-and-evidence.md) before searching. It covers venue selection, query construction, status verification, evidence extraction and practice review.

Honor user restrictions on browsing and sources. For an offline or supplied-corpus review, identify the supplied records, mark external verification pending, and do only the available steps. Log packet review separately from actual searches; do not invent queries, counts or precise timestamps.

1. Select relevant venue families and explain their relevance. Prioritize accepted main-track papers at leading venues in the subfield. Include older foundational work and current preprints, workshops, Findings tracks or journals where relevant, with explicit status. “Top conference” is a search priority, not a quality score or a restriction on prior art.
2. Search multiple formulations of the task, mechanism and constraint, including aliases and competing solutions. Combine official proceedings with a broad scholarly index and forward/backward citation searching. Do an explicit recent-work sweep up to the search date.
3. Log the exact query, source, date, filters, retrieved/screened counts and exclusions in [assets/search-log.csv](assets/search-log.csv). Record caps, inaccessible sources and incomplete coverage. Stop on the configured time budget or diminishing relevant returns; explain which. Never describe a bounded scout as an exhaustive systematic review.
4. Verify paper title, authors, year, version and acceptance/track against the canonical record. Deduplicate versions while preserving links and material changes. A result on OpenReview is not itself evidence of acceptance. Treat a preprint as prior art even if it is not peer reviewed.
5. Read full text of the closest competitors and papers supporting the shortlist's decisive claims. Record section/page/table locations and conditions in [assets/paper-records.json](assets/paper-records.json). Label abstract-only or inaccessible evidence; do not invent missing experiments or verified novelty.

Use available web/search connectors first. An optional bounded Semantic Scholar metadata search is available:

```text
python <skill-dir>/scripts/search_papers.py --query "retrieval augmented generation uncertainty" --year 2024- --limit 30 --output <run-dir>/search-s2-01.json
```

This helper retrieves one page, not accepted-paper verification or a complete corpus. `SEMANTIC_SCHOLAR_API_KEY` is optional. If unavailable or rate limited, use official proceedings/web search and log the limitation. Never fabricate a successful search. Before using API integrations, check current provider docs; access rules can change.

## Compare evidence with the idea

Build an idea-to-literature matrix: idea component → supporting paper → contradicting/closest work → transferable mechanism → assumption mismatch → proposed difference → decisive test. Separate authors' claims, observed results, your inference and a proposed hypothesis.

For each serious direction, compare the closest 2–5 works when available along task, method, assumptions, data, evaluation and cost. Search specifically for work that could invalidate its difference. Novelty means a supported, valuable difference; absence from a few search results does not prove novelty. Do not reward a combination of methods without explaining the interaction or knowledge gained.

Review current implementation practice for the actual idea: author repositories and reproducibility reports, relevant maintainer discussions, and official framework/model/dataset/benchmark docs. Record versions, dates, licenses/access and mismatches with the paper. Community discussions are leads or reported experience, not verified scientific results. Popularity and citation counts can guide discovery; neither establishes quality, feasibility or novelty. Read [references/practice-review.md](references/practice-review.md) for sourced design background and its limits; refresh domain-specific evidence every run.

## Propose, challenge and rank

Read [references/ranking-and-pilots.md](references/ranking-and-pilots.md) before assigning ratings. Generate a small, distinct set of directions (standard-mode guide: 3–6). Each needs a falsifiable hypothesis, closest-work delta, strongest objection, expected contribution and smallest useful pilot. Keep a low-cost baseline or analysis option when it addresses the question.

Apply four gates before selecting a direction: `closest_work`, `data_access`, `compute_budget`, `evaluation_validity`. Use pass/fail/unknown with reasons. For theory, interpret access and evaluation as the required mathematical resources and proof/counterexample strategy; explain any not-applicable gate as a reasoned pass. An unknown gate defers selection, a failed gate rejects it for the present constraints. A score cannot override a gate.

Rate fit, novelty, feasibility, rigor, impact and venue fit using evidence and the 1–5 anchors. Record a central estimate and plausible low/high bounds plus a reason and evidence IDs for every criterion. Unknown ratings remain null; do not use a neutral 3 for missing evidence. In particular, venue fit is null until a target's actual scope is established. These are subjective planning judgments, not acceptance probabilities or statistical confidence intervals.

Copy [assets/directions.template.json](assets/directions.template.json), fill evidence-linked ratings, then run:

```text
python <skill-dir>/scripts/rank_directions.py --config <run-dir>/config.json --input <run-dir>/directions.json --output <run-dir>/ranking.json
```

Check the evidence IDs yourself: the helper checks structure and calculates rankings but cannot validate papers or judge claims. It reports eligible/deferred/rejected directions, score ranges and sensitivity to changing each weight. Use [assets/ranking-demo.json](assets/ranking-demo.json) only to learn the format; it is synthetic, not research evidence.

Recommend a lead and an optional complementary fallback among eligible directions, explaining tradeoffs. If rankings reverse under modest weight changes or uncertainty overlaps, report a tentative shortlist and name the next discriminating check. If nothing is eligible, say so and identify the cheapest information needed; do not force a winner. Explicit judgment may override the numerical order only with a recorded evidence-based reason, never a failed/unknown gate.

## Deliver a review the user can act on

Use [assets/research-report.md](assets/research-report.md) as a flexible template. Include:

- The selected direction or deferral, how it serves the original idea, and what would change the decision.
- A cited literature map and current-practice review; closest competing work and the precise claimed difference.
- A ranked comparison with gate status, reasons, score ranges, sensitivity and unresolved objections.
- A pilot with baselines, test conditions, metrics/proof target, ablations or counterexamples, budget, success and stop criteria fixed before the pilot.
- Search dates and limitations, evidence records, reproducible search log and canonical bibliography with verified metadata.

Cite original sources next to material claims, with paper locations for decisive results. Link each recommendation through direction ID → evidence IDs → source location. State estimated vs measured costs, proposed vs completed experiments, and negative evidence explicitly. Refresh the novelty sweep before committing substantial work or submitting. Do not claim publication readiness or guaranteed novelty from this scout.
