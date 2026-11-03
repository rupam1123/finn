> Historical checkpoint. Current status: [final pack status](../../final-pack-status.md). Current setup: [final pack setup](../../final-pack-setup.md).

# Say–Do build checkpoint — 31 October 2026

This is an updated build, not a completed general Say–Do implementation.

The Pull pipeline now invokes a deterministic Say–Do analyzer rather than only displaying retrieved excerpts. It extracts narrowly specified first-person percentage guidance/actual sentences, preserves primary citations, matches adjacent reporting periods, handles conflicting values, and prevents annual guidance from being judged against quarterly actuals. Accounting-basis and speaker uncertainty block numerical verdicts. Unsupported wording remains insufficient_comparable_evidence, not an assertion that no guidance exists.

Real saved-source run: INFY Q1 FY2027 reports one annual-guidance/quarter-actual horizon mismatch and one missing comparable actual. Other rows in the four-company acceptance set still lack supported comparison pairs. No four-quarter numerical credibility score is established. The extractors do not yet cover the broader language and metrics needed to satisfy the requested complete workflow.

229 backend tests passed. The model test remains waived. See verification/say-do-tests.txt, say-do-real-results.json and say-do-build.txt. The existing 80.4% coverage report predates these changes and must not be presented as current coverage.

Next work: broader primary guidance/actual extraction, explicit speaker-role and accounting-basis binding, date-aware revision selection, and independent labelled semantic evaluation. Do not promote candidates merely because their quotes appear in a source. Preserve baseline source records and all historical analyses.
