# Upstream issue draft

Status: **VERSION-PINNED REPRODUCTION GREEN; NOT AUTHORIZED TO POST**. The public
Codex source contains a real external-memory import seam. A clean CI run now
passes fail-before-replace ordering, stable verifier digest, tamper, ambiguity,
both historical-authority cases, and ordinary Markdown compatibility against an
exact upstream commit.

Proposed title:

> Proposal: optional deterministic conformance for external-agent memory imports

## Problem

Codex currently imports explicitly selected, project-scoped Markdown memory into
an external-agent memory extension. Its consolidation instructions already say
that imported content is source material, not authoritative instructions. This
proposal complements that prompt-level safeguard with an optional,
machine-readable producer contract.

This is not a report of a known Codex vulnerability. The proposed contract adds
deterministic source integrity, explicit supersession, unambiguous current
heads, and one portable authority invariant:

```text
No claim imported from memory may satisfy a live approval requirement.
```

## Verified source seam

Pinned public source review:

- repository commit: `9fc715c0861c956c894a91890b78dc05b304ba29`;
- feature: `ExternalAgentMemoryImport`, under development and disabled by
  default;
- import boundary: `codex-rs/external-agent-migration/src/memory_import.rs`;
- current authority safeguard: interpretation rule at lines 25–26.

See `UPSTREAM_GAP_ANALYSIS.md` for commit-specific links and the compatibility
constraints.

## Candidate demonstration

The candidate includes two negative packages:

- a remembered approval whose described historical date has passed;
- a remembered approval whose described historical date has not passed.

Both producer packages claim `approval_eligible: true`. Both are rejected with
the same stable error:

```text
CMV_APPROVAL_ELIGIBILITY_VIOLATION
```

A valid historical record is preserved with `approval_eligible: false`, while
the host remains responsible for obtaining live approval.

```text
python skills/verify-canonical-memory/scripts/cmverify.py demo authority-replay
python skills/verify-canonical-memory/scripts/cmverify.py verify fixtures/invalid/approval-true-expired
python skills/verify-canonical-memory/scripts/cmverify.py verify fixtures/invalid/approval-true-unexpired
python -m unittest discover -s tests -p "test_*.py" -v
```

The implementation is standard-library-only, offline, deterministic, and uses
only synthetic data. This demonstrates the proposed invariant in the candidate;
it is not evidence that Codex currently violates or implements the invariant.

## Current upstream reproduction

`integrations/codex-external-agent-memory-import/` contains an exact-commit patch
and a dedicated CI workflow. The patch invokes a test preflight after all source
bytes are prepared and before old imported resources are removed. A rejecting
preflight must preserve the previous `MEMORY.md` and `scope.json`. The existing
ordinary Markdown importer test is run as the compatibility control.

The exact run and patch identities are recorded in
`UPSTREAM_REPRODUCTION_EVIDENCE.md`. This proves an experimental adapter at the
mutation boundary, not a final production API.

## Required before posting

Before posting, have an independent reviewer reproduce the exact clean-checkout
route and recheck the issue text against the then-current upstream source and
contribution guidance. Posting still requires separate current authorization.

## Question for maintainers

Would an optional deterministic preflight hook at the selected-project import
boundary align with the direction of `ExternalAgentMemoryImport`, while leaving
ordinary Markdown imports and host-controlled live approval unchanged? If so,
would a focused conformance fixture or interface proposal be useful upstream?

If maintainers consider the problem aligned and high-impact, I would be glad to
prepare a narrowly scoped implementation if invited. I am not proposing an
unsolicited pull request or asking Codex to adopt this entire schema.
