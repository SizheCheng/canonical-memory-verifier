# Public clean-room boundary

This candidate is built from a fresh schema, fresh code, and deterministic
synthetic fixtures. A future public archive must use an explicit allowlist.

Never include:

- private vault files, runtime snapshots, manifests, packages, or query output;
- real conversation, task, snapshot, source, artifact, or app identifiers;
- share links, local absolute paths, user names, cookies, tokens, or Tunnel logs;
- private hashes, because a hash can fingerprint undisclosed content;
- real repository state, customer data, commercial rankings, authority incidents,
  or distinctive event timelines;
- a copied private verifier whose routes or constants reveal private systems.

Before publication, run the boundary scanner, compare against a private deny-set
outside the candidate tree, inspect the final archive member allowlist, and
revalidate every external release or submission gate from live state. The
selected public license is Apache-2.0.

`PUBLIC_MANIFEST.json` is the candidate allowlist. It binds every other file's
relative path, byte count, SHA-256, and clean-room origin. The manifest excludes
its own bytes to avoid a recursive self-hash. Git control data under `.git/` is
not a distributable plugin member and is excluded; unexpected caches or build
outputs remain a failure rather than an implicit exclusion.
