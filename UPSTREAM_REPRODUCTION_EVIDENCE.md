# Version-pinned upstream reproduction evidence

Status: **GREEN EXPERIMENT — NO UPSTREAM CONTACT**

This record binds the first complete Canonical Memory Verifier experiment at
the public Codex external-agent memory import boundary. It is not an OpenAI
review, endorsement, invitation, or production integration.

## Exact identities

- Candidate repository commit:
  `b24cb165b8455a00f55ad8afbf8865f6d427ef87`
- Pinned `openai/codex` commit:
  `9fc715c0861c956c894a91890b78dc05b304ba29`
- Patch SHA-256:
  `d2ad4cce7c7355b8e6d3425e6bfb465cbdfdf0ed8386589a65282bb4d5fb6adb`
- Rust toolchain: upstream-pinned `1.95.0`

## Green runs

### Codex import seam

- Workflow run:
  <https://github.com/SizheCheng/canonical-memory-verifier/actions/runs/29935987607>
- Conclusion: `success`
- Completed: `2026-07-22T16:06:45Z`

The clean Ubuntu runner:

1. checked out the candidate repository;
2. checked out the exact Codex commit;
3. proved the exact upstream revision;
4. applied the patch with `git apply --check` first;
5. passed `cargo fmt --all -- --check`;
6. passed the generic fail-before-replace preservation test;
7. passed the real `cmverify` adapter tests; and
8. passed the existing ordinary Markdown import control.

The adapter tests established:

- `valid/basic` returned the same `conformance_sha256` across two verifier
  invocations and that digest was returned through the Rust preflight seam;
- `invalid/source-tampered` returned `CMV_SOURCE_HASH_MISMATCH` before target
  replacement;
- `invalid/ambiguous-heads` returned `CMV_CURRENT_HEAD_AMBIGUOUS` before target
  replacement;
- both `invalid/approval-true-expired` and
  `invalid/approval-true-unexpired` returned the same
  `CMV_APPROVAL_ELIGIBILITY_VIOLATION`; and
- after every rejection, the prior imported `MEMORY.md` and `scope.json`
  remained byte-identical.

### Cross-platform conformance

- Workflow run:
  <https://github.com/SizheCheng/canonical-memory-verifier/actions/runs/29935984893>
- Conclusion: `success`

All six jobs passed:

- Ubuntu / Python 3.10 and 3.13;
- macOS / Python 3.10 and 3.13; and
- Windows / Python 3.10 and 3.13.

Each job regenerated the synthetic fixtures, ran the complete Python tests,
scanned the public boundary, verified the byte-bound public manifest, and built
the deterministic review ZIP.

## Preserved failed attempts

The path to the green run is intentionally not hidden:

- run `29923486792` failed at rustfmt before Rust tests executed; the initial
  patch formatting was corrected;
- run `29923772757` then passed the narrower generic seam and ordinary Markdown
  control before the real verifier adapter was added;
- run `29935738737` failed at rustfmt before the expanded adapter tests
  executed; the two exact formatting differences were corrected.

Neither failed run is evidence about verifier semantics. The successful run
above is the first run in which formatting, the generic seam test, the real
adapter cases, and the ordinary compatibility control all completed.

## Remaining boundary

The experiment supplies the bundle path to the callback through test wiring. A
production design still has to decide how Codex discovers an optional bundle,
owns the verifier implementation, persists or reports the conformance digest,
and exposes a stable error type. The default Markdown path remains unchanged.

No repository file authorizes opening an upstream issue, sending a message,
submitting a plugin, or preparing an unsolicited pull request.
