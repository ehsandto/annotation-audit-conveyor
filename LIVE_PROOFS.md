# StudioNet proof matrix

## Deployment and exact source

- Contract: [0xeACeD0F3067c02c545913c4658F61910544485B8](https://explorer-studio.genlayer.com/address/0xeACeD0F3067c02c545913c4658F61910544485B8).
- Network: gasless StudioNet, chain ID 61999. Dedicated test signer `0x7a413BB4AB62E31d62d4cD9efC8C8a8Dae37FB42`; no existing key was exported or funds transferred.
- Contract/manifest commit: [`da2e2739acaa3428c80314dc4e55950df4879db7`](https://github.com/ehsandto/annotation-audit-conveyor/commit/da2e2739acaa3428c80314dc4e55950df4879db7).
- Evidence document commit: [`dbd87dad64020dc3421fd6b92952e6f761828881`](https://github.com/ehsandto/annotation-audit-conveyor/commit/dbd87dad64020dc3421fd6b92952e6f761828881).
- Deployed source SHA-256 after CRLF normalization and one trailing newline: `a6a782d8d5dca3f851777a186568bc558b2d08fdc1d5b9ad2cd9a600b099b20e`.
- `gen_getContractCode` matched the local tested source. Subsequent commits add tests, documentation and proof tooling only; deployed contract source and pinned data remain unchanged.
- [PROOFS.json](PROOFS.json) contains sanitized metadata, not raw receipts or validator credentials.

## Finalized transaction matrix

All seven transactions finalized with MAJORITY_AGREE. Four executed SUCCESS: deployment, manifest freeze, and two audit batches. Three deliberately executed ERROR. Expected rejections are never counted as successful audits.

| Step | Execution | Observed effect | Transaction |
| --- | --- | --- | --- |
| Deploy | SUCCESS | Contract created | [d6b5fbcd](https://explorer-studio.genlayer.com/tx/0xd6b5fbcd71c4406295dae9791a5339be34d494dc61929a364652d8c512769a94) |
| Freeze manifest | SUCCESS | Whole four-item dataset fetched, hash-checked and frozen at cursor zero | [d7cb911d](https://explorer-studio.genlayer.com/tx/0xd7cb911dee6a38ba90c409ba43c9aa1c3fd92be4beeec436b795cecb773f7c43) |
| Attempt to skip first batch | **ERROR, expected** | `Audit cursor mismatch`; no rows skipped | [e2b92ea4](https://explorer-studio.genlayer.com/tx/0xe2b92ea4e8bdebb6c773db8a5c6cb4733b18e35df383d1e87996ebfd5f5d0768) |
| Audit rows 0–1 | SUCCESS | Independent REFUTE/SUPPORT → MISMATCH/MATCH; cursor advances to two | [fe5eff49](https://explorer-studio.genlayer.com/tx/0xfe5eff492ff334caea05923386a9faf7b18c419ae7c470a1d508a16a804922ed) |
| Replay first batch | **ERROR, expected** | `Audit cursor mismatch`; no double counting | [83ae961f](https://explorer-studio.genlayer.com/tx/0x83ae961fc0de7270309af4fb6cec655dfb8e32dff00b94dbb655aadd1f1cc00b) |
| Audit rows 2–3 | SUCCESS | SUPPORT/UNKNOWN → MATCH/UNRESOLVED; bad commitment stays unresolved; coverage COMPLETE | [353b97e8](https://explorer-studio.genlayer.com/tx/0x353b97e8d3964cd6d39e9d1a546c4b9916b6214eb3a21cfb1dfeb61a5cb44b19) |
| Replay completed run | **ERROR, expected** | `Audit run complete`; no reset or new batch | [aa299df6](https://explorer-studio.genlayer.com/tx/0xaa299df66af4ef01ff6ae246b7dbeeff4809ee686a7fb507d7083eb2df1cf073) |

## Verified roots and coverage

Run ID: `437dc33f44873fd3e1b8ebc8348220c521b0a8aaf54d3a410077a3a0395b9663`.

| Snapshot | Head / batch root | Audited | Pending | MATCH / MISMATCH / UNRESOLVED | Error lower–upper |
| --- | --- | --- | --- | --- | --- |
| Frozen dataset | `f33ec7e20e45c16047313e84713acc5e2aa9a5c6d0520279dc81896d6598d05a` | 0 | 4 | 0 / 0 / 0 | 0/4–4/4 |
| First batch | `4ada2de36f0b43923d9cd50654ae60a849c3c3b9fdb439761f822972b07ac7d2` | 2 | 2 | 1 / 1 / 0 | 1/4–3/4 |
| Final batch/head | `2e72dd7262e17253016fa81a8366a7fd8633acadc527197e8cf615e5e7b85eff` | 4 | 0 | 2 / 1 / 1 | 1/4–2/4 |

The first-batch OPEN summary and final COMPLETE summary were both read live. The checker independently recomputed the frozen dataset root, exact acquired body hashes, consecutive batch indexes, prior-root chain, deterministic verdicts, count conservation and rational bounds. Read-only checks are not additional transaction proofs.

### Per-row evidence-backed observations

| Item | Provider annotation (not shown to model) | Independent observation | Source status | Deterministic outcome |
| --- | --- | --- | --- | --- |
| A1: unauthenticated callers may submit nonempty payloads | SUPPORT | REFUTE | OK | MISMATCH |
| A2: empty payloads rejected even from authenticated callers | SUPPORT | SUPPORT | OK | MATCH |
| A3: successful submissions return HTTP 202 | SUPPORT | SUPPORT | OK | MATCH |
| A4: successful submissions return HTTP 200 | REFUTE | UNKNOWN | HASH_MISMATCH | UNRESOLVED |

A4's intended evidence commitment is deliberately wrong. Even though the document would otherwise refute its statement, the contract cannot count that annotation as correct without an intact commitment. Its unresolved status remains in the upper bound.

Final root-bound summary:

```json
{"status":"COMPLETE","total":4,"audited":4,"pending":0,"counts":{"MATCH":2,"MISMATCH":1,"UNRESOLVED":1},"error_lower":{"numerator":1,"denominator":4},"error_upper":{"numerator":2,"denominator":4},"document_consistency_only":true}
```

COMPLETE asserts coverage only, not a passing grade. These ranges assume the known consensus judgments are correct; they do not incorporate shared model errors or assert universal truth.

## Source commitments and honest scope

- [Published manifest](https://raw.githubusercontent.com/ehsandto/annotation-audit-conveyor/da2e2739acaa3428c80314dc4e55950df4879db7/examples/dataset.json): `e212a568ebc922987be156a9293c4fae319f9db3c7e325824805babdb83c2005`.
- [Published fictional API reference](https://raw.githubusercontent.com/ehsandto/annotation-audit-conveyor/dbd87dad64020dc3421fd6b92952e6f761828881/examples/ingestion-reference.txt): `998b6f1cd4ae769b4f18a5296d2867c83d964deb662b121bf3fdffa8d590f891`.

These are authored test artifacts from one publisher, not independent authorities. The reference describes a fictional API. This proves real contract-side acquisition and semantic annotation consistency, **not actual service delivery, uptime, agent alignment, source authority, statistical representativeness or current applicability**. Coverage is exhaustive only for the four frozen items, not a provider's unseen corpus. No random-sampling or confidence-interval claim is made.

## Local versus live coverage

| Property | Local test | Live evidence |
| --- | --- | --- |
| Complete frozen manifest and mandatory batch order | Passed | Freeze + two successful batches |
| Permissionless progress by a different authenticated participant | Passed | One signer used live; no multi-signer proof claimed |
| Negative annotation produces mismatch | Passed | A1 independently REFUTE |
| Failed evidence never counts as correct | Passed, including forged post-consensus promotion | A4 UNKNOWN / UNRESOLVED |
| Pending rows retained in upper bound | Exhaustive bound checks | First-batch OPEN summary 1/4–3/4 |
| Skip and stale cursor replay rejected | Passed | Expected ERROR receipts above |
| Terminal run cannot restart | Passed | Expected ERROR receipt above |
| Cross-run substitution, fake body/index/observation rejected | Passed | Not injected live |
| Validator independently recomputes observations and bindings | Actual callback test passed | Network MAJORITY_AGREE; forced disagreement not claimed |
| Maximum 16-row dataset, all evidence unavailable | Passed | Not forced live |
| Malformed model output and invalid manifests/sources | Passed | Not all forced live |
| Exhaustive conservation and logical error bounds | 4,844 states passed | Concrete partial/final bounds checked |

Verification: GenVM lint/SDK validation passed; 38 direct/unit tests passed; five SDK calldata roundtrips passed. Direct mode executes the leader, not distributed validator consensus. The callback test invokes actual validator code separately. No professional security audit or guaranteed steward acceptance is claimed.

## Reproduce read-only verification

```powershell
node --dns-result-order=ipv4first scripts/check.mjs source 0xeACeD0F3067c02c545913c4658F61910544485B8
node --dns-result-order=ipv4first scripts/check.mjs state 0xeACeD0F3067c02c545913c4658F61910544485B8 437dc33f44873fd3e1b8ebc8348220c521b0a8aaf54d3a410077a3a0395b9663
```

Use `check.mjs success HASH` for the four success receipts. Use `error HASH "Audit cursor mismatch"` or `error HASH "Audit run complete"` for the three labeled rejection proofs. Never dump raw receipts, which may include private validator configuration. `complete-proofs.mjs` preserves known hashes and halts on uncertain execution; an unknown broadcast without a hash requires sender-history inspection before any retry. Run only one runner at a time.
