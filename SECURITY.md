# Security model

Experimental document-consistency auditing, not verification of real-world truth/service delivery/agent behavior. No approval certificate, authorization gate or assets exist.

- Whole manifest independently fetched and frozen before any batch; ordered rows cannot be replaced or selectively skipped.
- Provider annotations are hidden from semantic prompts. They are compared only after an independent source-derived label exists.
- Full commit/hash/URL binding, strict schemas, unique IDs/item bindings, safe host/path construction and bounded full UTF-8 responses.
- Every selected evidence body independently fetched by validators; all consequential fields compared exactly.
- Failed evidence forced UNKNOWN; unresolved and pending rows remain in upper bounds and full denominators.
- Exact cursor, run, frozen-root, previous-head and counts binding prevents replay, cross-run substitution and double-counting.
- Immutable batch records; terminal COMPLETE cannot be reset. COMPLETE asserts coverage only.
- Permissionless progress; no unilateral author veto. Model/network failure can still delay progress, without any optimistic quality result.
- Root-bound summary reads and rational integer bounds avoid stale summaries or threshold rounding.
- Bounded run/manifest/source/batch sizes; no arbitrary source host, code evaluation or external contract call.

Residual risk: authors can select which items appear in a manifest, paraphrase duplicates or publish false source content. Full-manifest coverage does not establish population representativeness or publisher authority. Consensus can share semantic errors or succumb to prompt injection. Pinning proves revision integrity, not recency. There is no silent correction of old batch judgments; a new run is explicit and must not be presented as a rewrite of prior history. No Sybil resistance or statistical sampling guarantee exists.

Signing uses a dedicated zero-balance StudioNet account through its native encrypted keystore/OS vault. Never log keys, raw receipts, provider configuration or credentials. Notify the repository maintainer privately before publishing exploitable issues. No professional audit is claimed.
