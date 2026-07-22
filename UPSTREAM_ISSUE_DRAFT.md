# Upstream issue draft

Status: **NOT READY TO POST**. The current artifacts demonstrate this
candidate's behavior only. They do not reproduce Codex behavior or establish an
actual Codex external-memory import seam. A real versioned upstream reproduction
and baseline comparison are required before this draft can be considered for
posting.

Proposed title:

> Proposal: fail-closed authority semantics for imported agent memory

## Problem

An external memory producer may preserve text such as “the user approved this
deployment.” At an import boundary, that statement is useful historical
evidence, but it must not become a credential that satisfies a new runtime
approval.

This is not a report of a known Codex vulnerability. The proposal is a portable
conformance invariant for third-party memory packages:

```text
No claim imported from memory may satisfy a live approval requirement.
```

## Minimal synthetic reproduction

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

## Candidate-only demonstration

```text
python skills/verify-canonical-memory/scripts/cmverify.py demo authority-replay
python skills/verify-canonical-memory/scripts/cmverify.py verify fixtures/invalid/approval-true-expired
python skills/verify-canonical-memory/scripts/cmverify.py verify fixtures/invalid/approval-true-unexpired
python -m unittest discover -s tests -p "test_*.py" -v
```

The implementation is standard-library-only, offline, deterministic, and uses
only synthetic data. This demonstrates the proposed invariant in the candidate;
it is not evidence that Codex currently violates or implements the invariant.

## Question for maintainers

After a real Codex import-boundary reproduction exists: does a fail-closed,
non-transitive authority invariant match the intended boundary for imported
agent memory? If so, would a focused conformance fixture or test be useful
upstream?

If maintainers consider the problem aligned and high-impact, I would be glad to
prepare a narrowly scoped implementation if invited. I am not proposing an
unsolicited pull request or asking Codex to adopt this entire schema.
