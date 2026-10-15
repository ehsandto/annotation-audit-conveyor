# Builder → Intelligent Contracts

## Title

AnnotationAuditConveyor — Complete-Coverage Evidence Audits

## Notes / Description

AnnotationAuditConveyor audits entire bounded annotation datasets. It independently fetches a commit-pinned manifest, freezes its ordered items and source commitments, and forces permissionless progress through two-row batches. Callers cannot skip or select favorable examples.

Leader and validators independently fetch each evidence body, verify HTTP status and SHA-256, and derive SUPPORT, REFUTE or UNKNOWN without seeing the provider annotation. Exact report equality is required. Deterministic comparison records MATCH, MISMATCH or UNRESOLVED; failed evidence cannot count as correct.

Run, cursor and prior-root bindings prevent replay, cross-run substitution and double-counting. Batch history is immutable. Rational error bounds include unresolved and pending rows in the full denominator. COMPLETE means coverage, not approval or universal truth.

StudioNet proofs cover full coverage and skip/replay rejection. The demo yields 2 matches, 1 mismatch and 1 unresolved. 38 tests pass.

## Evidence

- Repository: https://github.com/ehsandto/annotation-audit-conveyor
- Contract: https://github.com/ehsandto/annotation-audit-conveyor/blob/main/contracts/AnnotationAuditConveyor.py
- README: https://github.com/ehsandto/annotation-audit-conveyor/blob/main/README.md
- Proof matrix: https://github.com/ehsandto/annotation-audit-conveyor/blob/main/LIVE_PROOFS.md
- Sanitized ledger: https://github.com/ehsandto/annotation-audit-conveyor/blob/main/PROOFS.json
- Deployment: https://explorer-studio.genlayer.com/address/0xeACeD0F3067c02c545913c4658F61910544485B8
- Manifest freeze: https://explorer-studio.genlayer.com/tx/0xd7cb911dee6a38ba90c409ba43c9aa1c3fd92be4beeec436b795cecb773f7c43
- First audit batch: https://explorer-studio.genlayer.com/tx/0xfe5eff492ff334caea05923386a9faf7b18c419ae7c470a1d508a16a804922ed
- Final audit batch: https://explorer-studio.genlayer.com/tx/0x353b97e8d3964cd6d39e9d1a546c4b9916b6214eb3a21cfb1dfeb61a5cb44b19
- Skip rejection (expected execution ERROR): https://explorer-studio.genlayer.com/tx/0xe2b92ea4e8bdebb6c773db8a5c6cb4733b18e35df383d1e87996ebfd5f5d0768
- Batch replay (expected execution ERROR): https://explorer-studio.genlayer.com/tx/0x83ae961fc0de7270309af4fb6cec655dfb8e32dff00b94dbb655aadd1f1cc00b
- Completed-run replay (expected execution ERROR): https://explorer-studio.genlayer.com/tx/0xaa299df66af4ef01ff6ae246b7dbeeff4809ee686a7fb507d7083eb2df1cf073

Use the actual contribution date. Preserve expected-error labels for negative transaction evidence. Do not represent document consistency as verified live service delivery, publisher authority, population representativeness or universal truth. No award/acceptance guarantee is made.
