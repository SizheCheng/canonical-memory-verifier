# Plugin submission packet

Status: **LOCAL CANDIDATE — NOT SUBMITTED**

This packet maps the current skills-only candidate to the OpenAI plugin
submission form. It is a preparation record, not a policy attestation or an
authorization to submit.

## Info

- Submission type: Skills only
- Plugin name: Canonical Memory Verifier
- Developer identity: Sizhe Cheng (verified individual)
- Category: Developer Tools
- Short description: Verify imported memory before an agent relies on it.
- Long description: A local, read-only verifier for source integrity, explicit
  supersession, deterministic current projection, declared source-reference
  tracing, and remembered-authority boundaries.
- License: Apache-2.0
- Website: https://github.com/SizheCheng/canonical-memory-verifier
- Support: https://github.com/SizheCheng/canonical-memory-verifier/issues
- Privacy: https://github.com/SizheCheng/canonical-memory-verifier/blob/main/PRIVACY.md
- Terms: https://github.com/SizheCheng/canonical-memory-verifier/blob/main/TERMS.md

These live HTTPS URLs are hosted in the public repository under the matching
publisher identity. A final production-ready logo is still required.

## Skills bundle

Upload one ZIP no larger than 100 MB with this repository as the single plugin
root. The final ZIP must include `.codex-plugin/plugin.json` and
`skills/verify-canonical-memory/SKILL.md` and must not include an MCP or app
reference. Build it with:

```text
python tools/build_candidate_zip.py --output path/to/canonical-memory-verifier.zip
```

The build result intentionally reports `submission_authorized: false`; that
field records package provenance and does not attempt to control the portal.

## Starter prompts

1. Verify this external memory bundle before use.
2. Trace this current claim to its sources.
3. Check this bundle for remembered-authority replay.

## Tests

Use exactly the five positive and three negative cases in
`REVIEWER_TESTS.md`. Every case uses bundled synthetic data and requires no
account, network, credential, private context, MFA, email, or SMS.

## Availability

Country and region availability has not been selected. It should be chosen only
after the support process and public legal pages are live for those locations.

## Initial release notes

Initial skills-only submission. Canonical Memory Verifier checks explicitly
selected external-memory bundles offline for exact source-byte integrity,
machine-readable supersession, deterministic current projection, ambiguous
heads, and the invariant that remembered authority cannot satisfy live
approval. It uses only Python's standard library, contains only synthetic
fixtures, does not operate a server, and does not write to the selected bundle.

## Final portal gate

Before `Submit for Review`, confirm from the live candidate and portal that:

- the upload is the final inspected ZIP and remains under 100 MB;
- plugin and skill validators pass on the exact uploaded tree;
- the five positive and three negative reviewer cases reproduce cleanly;
- the publisher identity and all public URLs match Sizhe Cheng;
- listing art is final and owned by the publisher;
- all policy attestations are accurate for this exact version.
