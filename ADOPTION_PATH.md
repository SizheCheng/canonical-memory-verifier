# Adoption path

The target is official adoption, but that phrase has three distinct gates.

## Gate 1: reviewed distribution

Make a skills-only plugin installable through the official Plugins Directory.
Passing review would establish distribution eligibility, not technical
endorsement. Before this gate the candidate needs a deliberate license, public
repository, verified publisher identity, support material, and a current review
against the submission rules.

The local license, verified individual publisher metadata, support documents,
reviewer cases, deterministic package builder, and cross-platform CI definition
are now present. The remaining work at this gate is public hosting, live URLs,
listing art, clean-checkout reproduction, portal completion, and OpenAI review.

## Gate 2: upstream technical adoption

First obtain one real, versioned reproduction at an actual upstream import seam,
then publish one narrow invariant an upstream maintainer can evaluate. The
likely upstream unit is a test, fixture, or import-boundary rule—not this entire
application. The current synthetic verifier demo is not such an upstream
reproduction. Start with issue analysis only after that evidence exists; prepare
an upstream code change only when maintainers invite or request it.

## Gate 3: collaboration, employment, or acquisition

These outcomes require evidence beyond a local implementation: independent
users, repeatable eval results, maintenance quality, and constructive maintainer
interaction. They are not implied by plugin review or an upstream test.

## Current candidate exit criteria

Before any external action:

1. deterministic fixtures regenerate byte-for-byte;
2. all conformance and CLI tests pass offline;
3. authority replay is rejected independently of historical expiry;
4. ambiguous heads fail closed instead of selecting a claim;
5. privacy and secret scans pass;
6. a reviewer can reproduce the demo in minutes;
7. no claim says OpenAI has expressed interest, adopted, approved, or endorsed
   the project.

Publishing, contacting maintainers, opening an upstream issue, or submitting the
plugin are external-state actions. They must be recorded separately from local
conformance results and must never be described as OpenAI adoption before the
corresponding official action occurs.
