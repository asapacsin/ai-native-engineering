# Search and evidence protocol

Use this when gathering a corpus or updating prior work. The venue examples are starting points, not a universal ranking. Verify current official proceedings and track names rather than guessing this year's URLs or API invitation names.

## Choose the sources for the question

| Area | Venue examples to consider | Canonical verification route |
|---|---|---|
| General ML, learning theory, representation learning | NeurIPS, ICML, ICLR; COLT for theory; AISTATS and UAI for relevant statistics/uncertainty | [NeurIPS proceedings](https://proceedings.neurips.cc/), [PMLR](https://proceedings.mlr.press/), official conference pages and OpenReview |
| NLP and language models | ACL, EMNLP, NAACL; distinguish main, Findings and workshops | [ACL Anthology](https://aclanthology.org/), event/volume/track metadata |
| Vision and multimodal learning | CVPR, ICCV, ECCV | [CVF Open Access](https://openaccess.thecvf.com/) and the event's official proceedings |
| Broad AI, reasoning and planning | AAAI, IJCAI and relevant specialist venues | Official accepted lists/proceedings and publisher records |
| Retrieval, recommendation, data and web | SIGIR, KDD, The Web Conference, WSDM, RecSys; database venues when needed | Official event proceedings/accepted lists and publisher records |
| Robotics and embodied AI | RSS, CoRL, ICRA, IROS | Official proceedings/accepted lists; PMLR for applicable CoRL volumes |
| AI systems or human interaction | MLSys, relevant systems venues, CHI or FAccT when the contribution fits | Official proceedings and artifact/track records |

Use cross-field venues for mechanism transfer, but explain why their assumptions apply. Include journals, technical reports and preprints that could defeat a novelty claim. Do not exclude a direct competitor because its venue is less prestigious.

## Query lattice

Decompose the brief into task T, mechanism M, bottleneck B, setting S and evaluation E. Create synonyms and older terminology for each. Search separately before combining all five; overconstrained queries miss competitors. Adapt Boolean syntax to each engine.

Suggested query families:

- Task survey: `(T OR synonym) survey benchmark`; inspect surveys as maps, then verify original papers.
- Mechanism: `(M OR predecessor term) (T OR adjacent task)`.
- Bottleneck: `T (B OR failure OR limitation)` and alternatives solving B without M.
- Novelty challenge: the exact proposed mechanism, likely renamed equivalents, and the closest paper titles plus forward citations.
- Recent work: T/M with the resolved recent date window; include new preprints and accepted papers not yet indexed.
- Transfer: M in a neighboring setting, with explicit differences in assumptions or data.

For each family, search an official proceedings source and a broad index where available. A web query such as `site:aclanthology.org "task phrase"` is a discovery aid; a failed engine query does not establish that no paper exists. Citation searching must record the seed and direction (references, citing papers or related-paper recommendation). Perform at least one backward and one forward pass on the closest works when the services permit it; log exceptions.

Follow citation chains until the configured budget or diminishing-return rule. Report actual counts; do not manufacture counts for interfaces that do not expose them. `unknown` is acceptable in CSV counts. Keep exclusions with reasons such as wrong task, duplicate version, unsupported claim, irrelevant setting or insufficient accessible evidence. Abstract-only candidates can stay in the map with restricted conclusions.

## Identity, status and version

Deduplicate first by DOI, then arXiv/OpenReview/Anthology ID and linked versions, then normalized title plus author/year checks. Do not merge title matches blindly: related papers and extended versions may contain different contributions. Use one stable P ID per research work with version-specific findings and links.

OpenReview has multiple APIs; inspect the venue's API version and group metadata. Its official guide distinguishes accepted papers via `content.venueid` from submissions, rejected and withdrawn notes. A submission invitation retrieves multiple statuses. Check the actual venue/group, decision and track rather than relying on venue text in an aggregator. See [OpenReview note retrieval](https://docs.openreview.net/how-to-guides/data-retrieval-and-modification/how-to-get-all-notes-for-submissions-reviews-rebuttals-etc) and [API-version guidance](https://docs.openreview.net/how-to-guides/data-retrieval-and-modification/how-to-check-the-api-version-of-a-venue).

PMLR publishes both workshop and conference volumes, so verify each volume's event. The ACL Anthology exposes authoritative publication metadata and a maintained Python API; prefer that over invented REST endpoints. See [PMLR](https://proceedings.mlr.press/) and [Anthology development/API](https://aclanthology.org/info/development/).

Record official status as main accepted / other accepted track / workshop / journal / preprint / submitted / withdrawn / rejected / unverified, with the source and access date. An arXiv journal-reference string is a clue to verify, not independent acceptance confirmation.

## Extract decision-relevant evidence

For the closest competitors and every decisive source, read the paper's method, evaluation, limitations and relevant appendix. Save:

- What was tested or proved, on which task/data/split/assumptions, against which baselines.
- Which observation supports the claim, with section/page/table/theorem and conditions.
- Whether cost, hyperparameter search, seeds/uncertainty, failure cases and artifacts are reported.
- The exact component transferable to the user's idea, what breaks in transfer, and how the proposed pilot will check it.

Do not compare metric values across incompatible splits, models, budgets, benchmark versions or contamination exposure. Mark results as reported, independently reproduced, or measured in this run. Read an official full text or author version when possible; avoid silently treating an abstract, model summary or review as full-paper evidence.

## Review implementation practice

For the shortlisted mechanism, inspect the author repository and at least one additional practice source when available: an independent reproduction, maintainer discussion with logs, benchmark implementation, or documented deployed use. Read official docs for the chosen framework/model/data dependencies. Inspect release/commit dates, hardware, supported versions, model/data cards and licensing/access conditions. A repository link alone does not establish reproducibility, nor does an issue establish a confirmed defect.

If sources disagree, show the versions and evidence on both sides. Do not force consensus. In the absence of independent evidence, say implementation readiness remains unverified and design a smoke test.

## Optional metadata helper and fallback

`search_papers.py` is a small Semantic Scholar relevance-search client for a bounded shortlist. It saves query parameters, raw metadata, time, result count and continuation information, with no acceptance verification. It intentionally does not harvest a full proceedings archive. For large collections use the provider's current bulk-search documentation rather than repeatedly calling the small helper. The [official tutorial](https://webflow.development.semanticscholar.org/product/api/tutorial) documents relevance vs bulk search and optional API keys.

A key can be supplied as `SEMANTIC_SCHOLAR_API_KEY`; do not put credentials in the config or evidence bundle. If authentication, rate limits or a provider outage blocks the helper, use available search connectors and proceedings websites. Preserve the failure in the search log and state what was not searched. A blocked endpoint is not a zero-result literature search.
