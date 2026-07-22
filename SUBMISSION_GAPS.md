# Submission and adoption gaps

The local candidate is not yet ready for public submission.

## Established locally

- one plugin root with `.codex-plugin/plugin.json`;
- one narrow, explicit-input skill;
- standard-library-only read-only verifier;
- exactly five positive and three negative reviewer cases;
- deterministic synthetic fixtures;
- local validators and behavior, Unicode, graph, path, inventory, and privacy
  tests;
- one OpenClaw `main` model-assisted code review, followed by local remediation.
- Apache-2.0 license and individual publisher metadata for Sizhe Cheng;
- clean public source repository under the matching GitHub identity;
- live website, support, privacy, and terms URLs under that repository;
- passing public Windows, macOS, and Linux CI for Python 3.10 and 3.13;
- local privacy, terms, support, security, and publisher documents;
- strict validation of the public packaging manifest, including malicious
  manifest records and deterministic ZIP reproduction tests.

This is not an independent security audit, external validation, or OpenAI
review.

## Current documented portal requirements

The current official submission documentation permits a skills-only ZIP and
requires a verified individual or business identity, one plugin root, a ZIP no
larger than 100 MB, and exactly five positive plus three negative tests. Listing
and support information must be completed in the submission flow.

- https://learn.chatgpt.com/docs/submit-plugins

The intended publisher is the verified individual identity **Sizhe Cheng**.
Publisher metadata and the final OpenAI submission must use that exact identity.

## Self-imposed strategic readiness gates

These are project readiness choices, not claims about mandatory portal fields:

- have a human reviewer reproduce the commands from a clean checkout;
- finalize listing logo and confirm the prepared starter prompts;
- inspect a final allowlisted ZIP and rerun current official checks;
- complete the portal draft and policy attestations from live evidence.

## Upstream Codex evidence gap

A live import seam has now been verified in public `openai/codex` source at
commit `9fc715c0861c956c894a91890b78dc05b304ba29`. The feature is under development
and disabled by default. The current demo still proves only how this verifier
behaves; it has not yet been integrated with or tested against that Rust import
boundary. `UPSTREAM_ISSUE_DRAFT.md` is therefore still not ready to post.

Before upstream contact:

- build a minimal reproduction at the pinned import boundary and retain the
  ordinary Markdown path as the compatibility baseline;
- distinguish observed behavior from proposed invariant;
- publish a reproducible artifact only with separate authorization;
- begin with an issue or discussion, not an unsolicited pull request;
- prepare code only if maintainers invite or request it.

The current Codex contribution guide says external code contributions are by
invitation and asks contributors to start with an issue, analysis, and
reproduction:

- https://github.com/openai/codex/blob/main/docs/contributing.md
