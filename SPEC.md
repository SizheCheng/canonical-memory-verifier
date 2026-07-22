# Canonical Memory Conformance Contract 0.1

Status: experimental candidate.

The contract defines a deterministic, read-only check at an external-memory
import boundary. It is platform-neutral. A Codex skill is the first adapter, not
a semantic dependency of the contract.

## Bundle layout

The verifier accepts one explicitly selected directory:

```text
bundle/
├── bundle.json
└── sources/
    ├── source-a.txt
    └── source-b.json
```

`bundle.json` is strict UTF-8 JSON. The bundle directory and `sources/` must be
real directories, not symbolic links or reparse points. Sources are flat regular
files. Absolute paths, `..`, backslashes, alternate-data-stream syntax, nested
paths, name normalization collisions, and undeclared files are invalid.

Input is bounded to 1 MiB for `bundle.json`, 1,000 records per collection,
1,002 entries per enumerated directory, 256 KiB per source, and 512 KiB of
source bytes in total. Schema string lengths and verifier string lengths both
count Unicode code points. Duplicate JSON keys, non-finite numbers,
floating-point values, excessive nesting, and unknown fields are invalid.

The root object contains exactly:

- `schema_version`: exactly `0.1.0`;
- `bundle_kind`: exactly `imported_memory`;
- `bundle_id`: a stable synthetic or producer-assigned identifier;
- `scope`: the closed-world scope of the claims;
- `sources`: immutable byte records;
- `claims`: statements derived from one or more sources;
- `supersessions`: directed edges from an older claim to a newer claim.

## Source

Each source contains:

- `source_id`;
- `path`, exactly `sources/<flat-file>`;
- `media_type`;
- `bytes`;
- `sha256`, the lowercase SHA-256 of the exact file bytes.

SHA-256 proves only that bytes match the declared bundle record. It does not
prove authorship, authenticity, truth, or factual correctness.

## Claim

Each claim contains:

- `claim_id`;
- `key`, a functional key within the root `scope`;
- `claim_type`, either `fact` or `historical_authority`;
- `value`, a string;
- one or more unique `source_refs`;
- `approval_eligible`, which must be exactly `false`.

Normative invariant:

```text
No claim imported from memory may satisfy a live approval requirement.
```

The verifier does not trust the producer's boolean as a security capability. It
rejects `true` and emits a freshly constructed `false` in every projection and
trace. A remembered instruction that has not expired is still historical
evidence, not a live runtime approval token.

## Supersession

Each edge contains:

- `edge_id`;
- `superseded_claim_id`;
- `superseding_claim_id`;
- `reason`.

Both claims must exist and share the same `key`. Self-edges, cycles, dangling
endpoints, and cross-key edges are invalid. Several old claims may converge on
one new claim.

## Current projection

Claims are grouped by `key`. A head is a claim in the group that is never an
edge's `superseded_claim_id`. Each functional key must have exactly one head.
Zero or multiple heads return `CMV_CURRENT_HEAD_AMBIGUOUS`; the verifier never
selects the most plausible claim.

The only successful bundle status is `VERIFIED`. Any invariant failure returns
`INVALID` and no projection or trace.

## Deterministic conformance digests

Canonical JSON uses UTF-8, lexicographically sorted object keys, no insignificant
whitespace, unescaped Unicode, and the restricted value domain above. Arrays
retain semantic order unless a digest definition explicitly sorts records by
identifier.

For a valid bundle the verifier emits:

- `manifest_sha256`: canonical semantic `bundle.json`;
- `source_set_sha256`: sources sorted by `source_id`, binding paths, byte sizes,
  media types, and raw-byte hashes;
- `graph_sha256`: edges sorted by `edge_id`;
- `projection_sha256`: current heads sorted by `key`;
- `conformance_sha256`: the canonical digest of the four preceding digests and
  the schema version.

No verification time, local path, hostname, or model output enters these
digests. CLI output is emitted as raw UTF-8 bytes independently of the host
console encoding.

## Commands

- `verify BUNDLE_DIR`: validate and emit status, counts, and conformance digests;
- `project BUNDLE_DIR`: additionally emit current heads and values;
- `trace BUNDLE_DIR CLAIM_ID`: additionally emit declared source references,
  predecessor and successor edges, and the functional key's final head;
- `demo authority-replay`: run a fixed synthetic authority-boundary example.

All successful and contract-invalid results are strict JSON on standard output.
`INVALID` exits with status 2. CLI usage errors exit 64; masked internal failures
exit 70.
