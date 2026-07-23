# Adoption path

The target is official adoption, but that phrase has three distinct gates.

## Gate 1: reviewed distribution — complete

OpenAI approved the submission, and Plugins Directory version `0.1.0` was
published by the developer. The exact
submitted source is commit
`3c88e4623a5f18af6f5998e6189f13b733b6b704`; the deterministic 116,170-byte
submitted ZIP has SHA-256
`c69e85c2487259d9aa6d8cfbfb4e8f43a50c0752fa444ca2bbefa08459c6c999` and is
attached to the public GitHub `v0.1.0` release. The bounded live observation is
recorded in `PUBLICATION_RECORD.json`.

Passing review and publication establish official directory distribution. They
do not establish OpenAI endorsement, upstream technical adoption, employment,
or acquisition.

## Gate 2: upstream technical adoption

The version-pinned experiment passes at the actual Codex import boundary. It
carries a stable verifier digest and the tamper, ambiguity, expired-authority,
and unexpired-authority failure classes through the seam while preserving
ordinary Markdown compatibility and the prior imported copy.

Before maintainer contact, one independent human must reproduce the exact clean
checkout route. After that, refresh the claim against then-current public Codex
source and begin with the focused issue in `UPSTREAM_ISSUE_DRAFT.md`, not an
unsolicited pull request. The likely upstream unit remains a test, fixture, or
import-boundary rule—not this entire application. Prepare production code only
when maintainers invite or request it.

## Gate 3: collaboration, employment, or acquisition

These outcomes require evidence beyond directory publication: independent
users, repeatable eval results, maintenance quality, and constructive maintainer
interaction. They are not implied by plugin review or an upstream experiment.

## Current evidence and remaining gates

Established:

1. deterministic fixtures regenerate byte-for-byte;
2. all conformance and CLI tests pass offline;
3. authority replay is rejected independently of historical expiry;
4. ambiguous heads fail closed instead of selecting a claim;
5. privacy, secret, and public-boundary scans pass;
6. the submitted ZIP reproduces byte-for-byte from its source commit; and
7. OpenAI Plugins Directory version `0.1.0` is published.

Still required before upstream contact:

1. an independent human clean-checkout reproduction;
2. a fresh comparison with the then-current upstream import seam and
   contribution guidance; and
3. a focused maintainer issue or discussion after the first two gates pass.

State the observed publication fact precisely. Never convert directory
publication into a claim of OpenAI endorsement, upstream adoption, or interest.
Any later submission, maintainer contact, or code contribution requires its own
current authorization.
