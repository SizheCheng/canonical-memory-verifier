# Upstream import-boundary analysis

Status: **PINNED SOURCE REVIEW — NO UPSTREAM CONTACT**

This analysis was performed against the public `openai/codex` repository at:

```text
9fc715c0861c956c894a91890b78dc05b304ba29
```

The review establishes an integration seam. It does not establish a Codex
vulnerability, OpenAI interest, or an invitation to contribute code.

## What Codex already does

The public source contains `Feature::ExternalAgentMemoryImport`, marked
`UnderDevelopment` and disabled by default:

- <https://github.com/openai/codex/blob/9fc715c0861c956c894a91890b78dc05b304ba29/codex-rs/features/src/lib.rs#L943-L947>

The external-agent migration flow discovers project-scoped Markdown memory,
requires explicit selected projects, copies selected bytes into a dedicated
memory extension, records project scope, and enqueues consolidation:

- <https://github.com/openai/codex/blob/9fc715c0861c956c894a91890b78dc05b304ba29/codex-rs/external-agent-migration/src/memory.rs#L19-L155>
- <https://github.com/openai/codex/blob/9fc715c0861c956c894a91890b78dc05b304ba29/codex-rs/external-agent-migration/src/memory_import.rs#L53-L89>

Codex also already tells its consolidation agent to preserve scope and
provenance and to treat imported content as source material rather than
authoritative instructions:

- <https://github.com/openai/codex/blob/9fc715c0861c956c894a91890b78dc05b304ba29/codex-rs/external-agent-migration/src/memory_import.rs#L14-L32>

These safeguards must be acknowledged. Canonical Memory Verifier is not a
replacement for them.

## Narrow gap the candidate can address

The current importer intentionally accepts ordinary Markdown resources. It
compares source and imported bytes to decide whether a project needs to be
recopied, but the imported format does not provide an optional machine-readable
contract for:

- a byte-bound source manifest supplied by the external-memory producer;
- explicit claim-to-source references;
- an explicit supersession graph and deterministic current heads;
- a producer-independent rule that every imported claim is ineligible to
  satisfy live approval;
- a stable conformance digest that can be recorded with the import result.

Those are additional semantics, not proof that the existing importer is broken.
Prompt-level interpretation rules and a deterministic producer contract solve
different problems and can coexist.

## Smallest plausible integration

Do not replace the Markdown importer or Codex consolidation pipeline. Add an
optional preflight adapter at the selected-project import boundary:

1. If no recognized conformance bundle is present, preserve existing behavior.
2. If a bundle is present, verify it before replacing any existing imported
   project resources.
3. On any integrity, reference, graph, ambiguity, or authority-eligibility
   failure, reject that selected project and preserve the prior imported copy.
4. On success, return the conformance digest with the import result and expose
   only deterministic current heads to the adapter.
5. Keep live approval and execution policy entirely in the Codex host.

The first upstream unit should be a focused fixture or optional hook, not this
whole Python plugin and not the private Canonical Memories vault.

## Executable seam proof

The repository now contains a version-pinned patch and dedicated CI workflow at
`integrations/codex-external-agent-memory-import/`. The patch prepares all
candidate source bytes, calls a test preflight, and only then reaches the
existing destructive replacement. Its focused negative test rejects the
candidate and verifies that the previous `MEMORY.md` and `scope.json` remain
byte-identical. The existing ordinary Markdown importer test is retained as a
compatibility control.

This closes only the mutation-order question. It deliberately does not expose a
final upstream API or port the Python verifier into Codex.

## Full contract reproduction still required

Before posting an issue or discussion, build a version-pinned upstream test that
demonstrates all of the following without modifying current default behavior:

- ordinary Markdown import remains compatible when no bundle is present;
- a valid bundle imports successfully and returns a stable digest;
- a changed source byte fails before target replacement;
- ambiguous current heads fail closed;
- both expired and unexpired remembered-authority records with
  `approval_eligible: true` fail identically;
- the prior imported project remains intact after a failed preflight.

The narrow workflow covers ordinary compatibility and preservation after a
generic preflight rejection. The bundle-aware digest, tamper, ambiguity, and
authority cases remain to be wired through a real adapter before this can be
called a completed contract reproduction or posted as an upstream proposal.
