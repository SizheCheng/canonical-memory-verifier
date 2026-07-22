# Version-pinned Codex import seam proof

Status: executable integration experiment; not an upstream contribution and not
an assertion of OpenAI endorsement.

This directory tests one narrow question against a fixed OpenAI Codex source
revision: can an external-memory verifier run after candidate Markdown bytes are
prepared but before a previous imported project is removed?

## Pin and scope

- Repository: `openai/codex`
- Commit: `9fc715c0861c956c894a91890b78dc05b304ba29`
- Crate: `codex-external-agent-migration`
- Files touched by the experiment:
  - `codex-rs/external-agent-migration/src/memory_import.rs`
  - `codex-rs/external-agent-migration/src/memory_import_tests.rs`

The patch factors the existing replacement function around a preflight callback.
The default callback accepts ordinary Markdown, so the current compatibility path
is unchanged. The added test supplies a rejecting callback and proves that the
previous `MEMORY.md` and `scope.json` remain byte-identical after rejection.

The callback is intentionally not exposed as a proposed final public API. This
experiment establishes the mutation boundary first; verifier ownership, error
types, attestation persistence, and service wiring remain upstream design work.

## Reproduce

The `upstream-codex-seam` GitHub Actions workflow performs these steps on a clean
Ubuntu runner:

1. checks out this repository;
2. checks out `openai/codex` at the exact commit above;
3. checks the patch before applying it;
4. verifies Rust formatting;
5. runs the new fail-closed preservation test; and
6. runs the existing ordinary Markdown import test as a compatibility control.

Equivalent commands after both repositories are checked out side by side:

```bash
git -C upstream apply --check ../canonical-memory-verifier/integrations/codex-external-agent-memory-import/codex-import-preflight.patch
git -C upstream apply ../canonical-memory-verifier/integrations/codex-external-agent-memory-import/codex-import-preflight.patch
cd upstream/codex-rs
cargo fmt --all -- --check
cargo test -p codex-external-agent-migration --lib preflight_failure_preserves_previous_imported_project
cargo test -p codex-external-agent-migration --lib copies_only_selected_projects_and_recopies_changed_content
```

## What this proves

- the seam applies to the pinned source revision;
- a rejecting verifier can fail before destructive replacement;
- the previous imported project is preserved on preflight failure; and
- the ordinary Markdown control still executes through the default path.

It does not prove that Codex accepts the Canonical Memory contract, that this is
the final upstream API, or that the public issue draft is ready to post.
