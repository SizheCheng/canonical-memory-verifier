# Canonical Memory Verifier

[![Conformance CI](https://github.com/SizheCheng/canonical-memory-verifier/actions/workflows/ci.yml/badge.svg)](https://github.com/SizheCheng/canonical-memory-verifier/actions/workflows/ci.yml)
[![Pinned Codex seam](https://github.com/SizheCheng/canonical-memory-verifier/actions/workflows/upstream-codex-seam.yml/badge.svg)](https://github.com/SizheCheng/canonical-memory-verifier/actions/workflows/upstream-codex-seam.yml)

<img src="assets/logo.svg" alt="Canonical Memory Verifier mark" width="96">

Canonical Memory Verifier is a clean-room, local-first verifier and published
skills-only plugin for one narrow external-memory import boundary:

> Before an agent relies on imported memory, deterministically prove which
> claims are current, which exact declared source bytes they reference, and that
> remembered authority cannot count as live approval.

OpenAI Plugins Directory version `0.1.0` is published at
<https://chatgpt.com/plugins/plugins_6a616d0d67e88191844c7fe0bb2b2ac5>.
Directory publication establishes reviewed distribution; it does not make this
repository an OpenAI product, endorsement, upstream integration, or security
boundary. The repository contains only synthetic data. It does not connect to a
server, scan conversations, discover memory directories, write back to a vault,
or execute an action described by memory.

Publisher: **Sizhe Cheng** ([GitHub identity](https://github.com/SizheCheng)).
The code is licensed under Apache-2.0. See [PUBLISHER.md](PUBLISHER.md),
[LICENSE](LICENSE), and [NOTICE](NOTICE).

## Five-minute review

Requirements: Python 3.10 or newer. The verifier uses only the Python standard
library.

```text
python skills/verify-canonical-memory/scripts/cmverify.py verify fixtures/valid/basic
python skills/verify-canonical-memory/scripts/cmverify.py project fixtures/valid/supersession-chain
python skills/verify-canonical-memory/scripts/cmverify.py trace fixtures/valid/supersession-chain clm_target_new
python skills/verify-canonical-memory/scripts/cmverify.py demo authority-replay
```

Expected behavior:

- a complete bundle with one current head per functional key returns
  `VERIFIED`;
- corrupt graphs, missing evidence, changed source bytes, and ambiguous heads
  return `INVALID`;
- remembered authority with `approval_eligible: true` is rejected whether its
  historical time limit has passed or not;
- output omits input paths and wall-clock timestamps, so the same bundle
  produces the same digests on different machines.

Run the candidate checks:

```text
python tools/generate_synthetic_fixtures.py --check
python -m unittest discover -s tests -p "test_*.py" -v
python tools/scan_public_boundary.py
python tools/build_public_manifest.py --check
```

The same checks run on Python 3.10 and 3.13 across Windows, macOS, and Linux in
`.github/workflows/ci.yml`. The public manifest excludes only Git control data;
generated caches, undeclared files, non-UTF-8 payloads, reparse points, and
unreviewed binary extensions fail the public-boundary checks.

After those checks pass, a deterministic local-review ZIP can be created
outside the plugin root:

```text
python tools/build_candidate_zip.py --output path/to/canonical-memory-verifier-local-review.zip
```

Building a local ZIP does not authorize submission or publication.

## Scope

The normative core is deliberately small:

- exact flat-file source inventory bound to byte length and SHA-256;
- claims with explicit source references;
- same-key, acyclic supersession edges;
- exactly one current head per functional key;
- deterministic projection and declared source-reference trace;
- `approval_eligible: false` on every imported claim.

The verifier does **not** determine whether a source is true, block tool calls,
provide runtime approval, sanitize prompt injection, host user data, or replace
an agent platform's authorization controls. The host remains responsible for
live approval and execution policy.

See [SPEC.md](SPEC.md), [THREAT_MODEL.md](THREAT_MODEL.md),
[PUBLIC_BOUNDARY.md](PUBLIC_BOUNDARY.md), [ADOPTION_PATH.md](ADOPTION_PATH.md),
[SUBMISSION_PACKET.md](SUBMISSION_PACKET.md), and the
[version-pinned Codex import seam experiment](integrations/codex-external-agent-memory-import/README.md).

## Publication and upstream status

OpenAI approved the submission, and Plugins Directory version `0.1.0` was
published by the developer. The exact
submitted source is commit
[`3c88e4623a5f18af6f5998e6189f13b733b6b704`](https://github.com/SizheCheng/canonical-memory-verifier/commit/3c88e4623a5f18af6f5998e6189f13b733b6b704),
released as [`v0.1.0`](https://github.com/SizheCheng/canonical-memory-verifier/releases/tag/v0.1.0).
Its deterministic 116,170-byte ZIP has SHA-256
`c69e85c2487259d9aa6d8cfbfb4e8f43a50c0752fa444ca2bbefa08459c6c999`.
See [PUBLICATION_RECORD.json](PUBLICATION_RECORD.json) for the bounded publication
record.

The public CI runs the conformance route on Windows, macOS, and Linux with
Python 3.10 and 3.13. A separate workflow applies a narrow fail-before-replace
patch to an exact public Codex commit and runs both a preservation test and the
ordinary Markdown compatibility control. It also passes the real verifier's
valid digest, tamper, ambiguous-head, and two authority-eligibility cases through
that seam. See [UPSTREAM_REPRODUCTION_EVIDENCE.md](UPSTREAM_REPRODUCTION_EVIDENCE.md)
for exact commits, hashes, run URLs, failures, and limits.

An independent human clean-checkout reproduction remains a deliberate gate
before upstream maintainer contact. The experiment is not an upstream
contribution or OpenAI endorsement. Directory publication does not authorize a
future submission, maintainer contact, or code contribution.
