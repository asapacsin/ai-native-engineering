# Rating directions and deciding what to test

This is a local planning rubric designed for this skill. The weights, numerical scale, gates and sensitivity sweep are not official conference scoring rules. They help expose judgments and tradeoffs; they do not predict acceptance.

## Evidence before arithmetic

Give each direction a falsifiable question, explicit relationship to the original idea and closest-work comparison. Assign evidence IDs (P for papers, E for documentation, project constraints or estimates) to the claim behind every criterion. Evidence can be an explicit user constraint or a reasoned estimate; identify it honestly and widen bounds when uncertain. An ID's existence does not make the inference valid.

Use the same interpretation of each criterion for every direction in a run. Set or revise weights before seeing a preferred direction's aggregate score; record any later change and its reason.

| Criterion | Default weight | 1 | 3 | 5 |
|---|---:|---|---|---|
| fit | 25% | Misses the user's central problem or violates a preserved objective | Addresses the problem with material compromises | Directly serves the problem, mechanism and success criterion |
| novelty | 20% | Closest work already answers the question under comparable conditions | A specific incremental difference is supported but its value is uncertain | Strongly differentiated question/insight with closest-work checks and a convincing reason it matters |
| feasibility | 20% | Required resources or capabilities are far beyond what is available | Plausible pilot with substantial engineering or resource uncertainty | Decisive pilot fits confirmed access, skills, budget and time |
| rigor | 15% | Proposed test cannot separate the claim from alternatives | Testable with remaining confounds or measurement concerns | Strong controls, valid evaluation or proof strategy, and explicit falsifiers |
| impact | 15% | Little useful knowledge or practical value even if successful | Useful to a defined audience or resolves a narrow uncertainty | Meaningful advance in understanding or usefulness with a credible adoption or scientific path |
| venue_fit | 5% | Contribution conflicts with venue/track scope | In scope with evidence still needed for the contribution type | Clear fit to the current official scope and evaluation expectations |

Use 2 and 4 for intermediate judgments. A 5 for novelty means strongest supported difference among the scoped options, not proof of global novelty. A null rating means unknown, not poor; 3 must not stand in for unavailable evidence. Leave venue fit null if there is no established target scope; being broadly about AI is insufficient. A surprising negative result, evaluation insight, dataset contribution, efficiency gain or theory result can score highly without a new architecture or a leaderboard gain. Apply expectations to the contribution type; [NeurIPS 2026 review guidance](https://nips.cc/Conferences/2026/ReviewerGuidelines) and [ICLR 2026 review guidance](https://iclr.cc/Conferences/2026/ReviewerGuide) are examples to recheck for the target venue/year.

## Four gates

| Gate | Pass when | Fail or defer when |
|---|---|---|
| closest_work | Decisive competitor text is reviewed and a meaningful difference survives direct comparison | Fail if already answered with no useful remaining contribution; unknown if decisive text/status or novelty checks are unavailable |
| data_access | Required data/models/permissions are available under the project's conditions, or not required with explanation | Fail if unavailable under the constraints; unknown if permission/license or access is unresolved |
| compute_budget | Pilot's cost and elapsed time fit confirmed resources with a stated estimation basis | Fail if over budget; unknown if resources or scaling costs are unestablished |
| evaluation_validity | A feasible protocol can test the central claim with appropriate controls | Fail if claim cannot be isolated under constraints; unknown if splits, measurements or proof route remain unresolved |

Reasoned non-applicability is allowed: for a pure theorem, data access may pass because no external data is needed. Confirm the mathematical assumptions and counterexample/proof plan instead of demanding an empirical benchmark. A pass means sufficient grounds to attempt a pilot, not successful experimental evidence. Do not run the pilot unless the user's task authorizes experimentation; the normal scout delivers its plan.

## Calculations and interpretation

All six weights must be present if specifying `ranking.weights`; the script normalizes positive finite weights to sum to 1. If that object is omitted, defaults apply. For ratings s in [1, 5], utility is `25 * (sum(weight * s) - 1)`, mapped to [0, 100]. Low/high rating bounds propagate with the same formula. They are plausible judgment ranges, not probabilities, statistical error bars or confidence intervals.

Only complete, evidence-linked directions with all gates passed are ranked. Others are deferred; a failed gate rejects the direction under the present constraints. Preserve them in the review with reasons. The script identifies numerical leaders, not a research decision. It does not resolve evidence IDs against source files or verify scientific validity; the agent must do that review.

Sensitivity changes each criterion's weight by plus/minus the configured fraction (default 20%) and renormalizes all weights. It reports tied winners and order changes. This is a local preference check, not a search over all possible preferences or correlated rating uncertainty. Inspect score-range overlap separately. If the leader changes, or the leader's range overlaps another candidate, make the decision tentative and choose the cheapest discriminating evidence or pilot. Do not hide tie-breaking by ID as scientific superiority.

## Pilot design

An empirical pilot should establish a simple baseline and closest practical competitor, use matched data/compute/tuning budgets, define a primary metric and meaningful effect threshold, and include a mechanism-removal ablation or alternative explanation. Protect evaluation data from training and tuning. Use repeated runs or paired uncertainty estimates proportionate to the claim and budget; report the limits when only one run is feasible.

For theory, replace datasets and metrics with explicit assumptions, exact statement, known special cases, proof lemmas and counterexample searches. For datasets/evaluation, test construct validity, leakage, label quality and whether conclusions change across reasonable protocols. For systems, measure hardware, workload, latency/throughput, memory and quality tradeoffs under comparable conditions.

Estimate total pilot cost from a small representative unit when available: unit cost × planned runs, including baselines, tuning and overhead. Label extrapolation and unknown prices. Avoid estimating an entire training run from an unrelated model. Fix success/stop criteria and a timebox before measurement. The pilot should answer an uncertainty that can change the decision, not merely produce an attractive demo.
