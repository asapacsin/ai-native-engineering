# Source review and design rationale

Reviewed 2026-10-18. This is a selective review of official guidance and public community infrastructure, not a survey estimating how often all researchers use each practice. The ranking formula, defaults and planning budgets are this skill's design choices. Recheck live documentation and domain-specific practice when the skill runs.

## What the reviewed sources support

| Source | Observed guidance or capability | Design consequence and limit |
|---|---|---|
| [NeurIPS 2026 reviewer guidelines](https://nips.cc/Conferences/2026/ReviewerGuidelines) | Discusses quality, clarity, significance and originality, with contribution-specific expectations. Originality can include insight into existing methods; theory need not have empirical validation. | Review valuable knowledge, not only new methods or benchmark wins. Do not reuse one venue's rules as every venue's rubric. |
| [ICLR 2026 reviewer guide](https://iclr.cc/Conferences/2026/ReviewerGuide) | Asks reviewers to understand the whole paper, its relation to literature, support for claims and value of the knowledge contributed. | Read decisive full texts and challenge claims. A direction scout is not a conference accept/reject decision. |
| [PRISMA-S overview](https://www.prisma-statement.org/prisma-search) and [PRISMA-S explanatory paper](https://doi.org/10.1186/s13643-020-01542-z) | Provides a 16-item reporting extension for literature searches. | Borrow transparent query/date/source/filter and deduplication reporting. This skill does not claim PRISMA compliance or exhaustive systematic-review coverage. |
| [OpenReview note retrieval](https://docs.openreview.net/how-to-guides/data-retrieval-and-modification/how-to-get-all-notes-for-submissions-reviews-rebuttals-etc) | Distinguishes submission retrieval from acceptance/status filtering using venue metadata. | Verify main/workshop/other-track status; do not treat every discovered submission as an accepted paper. |
| [ACL Anthology development and API](https://aclanthology.org/info/development/) | Publishes authoritative metadata and recommends its Python API for programmatic publication access. | Use canonical records and supported interfaces rather than invented scraping/API assumptions. |
| [PMLR](https://proceedings.mlr.press/) | Hosts event-specific volumes from workshops and conferences. | Check the volume and event before assigning venue prestige or track. |
| [Semantic Scholar official tutorial](https://webflow.development.semanticscholar.org/product/api/tutorial) and [API documentation](https://api.semanticscholar.org/api-docs/) | Supports metadata searches, citations and related-paper recommendations. Explains bulk vs relevance search, pagination and optional API keys. | Combine keyword discovery with citation expansion; keep the small helper bounded and preserve continuation information. Index metadata is not canonical acceptance verification. |
| [Hugging Face Paper Pages documentation](https://huggingface.co/docs/hub/paper-pages) | Links papers with models, datasets and Spaces, and hosts discussion. | Follow paper-to-artifact links to inspect practical readiness; discussion/upvotes are not validation of claims. |
| [ML Reproducibility Challenge 2026](https://reproml.org/) | Maintains an active community venue for reproducibility work. | Look for independent reproductions and discrepancies rather than assuming released code reproduces results. Presence of the initiative does not establish field-wide adoption rates. |
| [Pineau et al., Improving Reproducibility in ML Research](https://arxiv.org/abs/2003.12206v4) | Reports a program combining code submission, a community reproducibility challenge and a checklist. | Historical foundation for checking claims against artifacts; this 2020 report is not evidence of present-day package compatibility. Only the abstract/metadata was inspected for this design review. |
| [ML Contests: State of ML Competitions 2025](https://mlcontests.com/state-of-machine-learning-competitions-2025/) | Aggregates winner/organizer correspondence and public information, including methods and hardware. | Investigate contemporary practical baselines and resource costs. Competition winners are a selected population and competition performance is not proof of scientific novelty or transfer to the user's task. |
| [OpenAI: Build skills](https://learn.chatgpt.com/docs/build-skills) | Describes a skill folder with SKILL.md, optional references/scripts/assets and progressive loading; documents local discovery locations. | Keep the entrypoint focused, place detailed protocols in references and support project-local installation. Agent and browsing capabilities remain environment-dependent. |

## Practical synthesis

The reviewed ecosystem offers complementary evidence: proceedings establish publication identity, indexes and citation graphs broaden discovery, artifact hubs expose implementation resources, and reproduction efforts examine reliability. A defensible research choice combines these rather than substituting popularity for evidence. This is our synthesis of the above sources, not a quoted consensus rule.

The skill therefore follows: configurable brief → transparent discovery → identity/full-text verification → closest-work and implementation comparison → falsifiable directions → feasibility gates → explicit ratings and uncertainty → a selective pilot plan. It retains contradictions and unknowns so a plausible research story cannot erase missing evidence.

## Known limits

Search engines and indexes can omit fresh or non-English work; citations lag and bias toward established areas. Venue prestige, repository stars and community attention are imperfect discovery signals. Accessible papers can still contain unsupported claims. An untested implementation remains untested. A weighted judgment cannot certify novelty or replace expert assessment. The workflow exposes these limits in each run and refreshes current prior art before a costly commitment.

No topic-specific papers or reproducibility results are claimed in this reusable bundle. The included ranking example is synthetic; each real use must populate its own evidence and research findings.
