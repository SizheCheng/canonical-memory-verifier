# Canonical Memory Verifier

[![Conformance CI](https://github.com/SizheCheng/canonical-memory-verifier/actions/workflows/ci.yml/badge.svg)](https://github.com/SizheCheng/canonical-memory-verifier/actions/workflows/ci.yml)

Canonical Memory Verifier is a clean-room, local-first candidate for one narrow
external-memory import boundary:

> Before an agent relies on imported memory, deterministically prove which
> claims are current, which exact declared source bytes they reference, and that
> remembered authority cannot count as live approval.

This repository is a conformance candidate, not an OpenAI product, endorsement,
security boundary, or published plugin. It contains only synthetic data. It does
not connect to a server, scan conversations, discover memory directories, write
back to a vault, or execute an action described by memory.

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
and [SUBMISSION_PACKET.md](SUBMISSION_PACKET.md).

## Public-review status

The source is public at
<https://github.com/SizheCheng/canonical-memory-verifier>. The code, license,
publisher metadata, reviewer cases, privacy policy, terms, support policy, and
deterministic package builder are present. The public CI runs the complete
conformance route on Windows, macOS, and Linux with Python 3.10 and 3.13. Final
listing art, an independent human clean-checkout reproduction, and submission
through the OpenAI portal remain external gates. No file in this repository
authorizes submitting it.
