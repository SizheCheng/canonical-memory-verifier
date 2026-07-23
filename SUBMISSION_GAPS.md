# Publication and adoption gaps

OpenAI Plugins Directory version `0.1.0` is published. This file now separates
completed reviewed distribution from the remaining technical-adoption gates.

## Established and published

- one plugin root with `.codex-plugin/plugin.json`;
- one narrow, explicit-input skill;
- a standard-library-only read-only verifier;
- exactly five positive and three negative reviewer cases;
- deterministic synthetic fixtures;
- local behavior, Unicode, graph, path, inventory, privacy, and package tests;
- Apache-2.0 licensing and verified individual publisher **Sizhe Cheng**;
- public website, support, privacy, and terms URLs under the matching identity;
- passing Windows, macOS, and Linux CI for Python 3.10 and 3.13;
- production listing assets and starter prompts;
- a portal scan result of `Passed` for `verify-canonical-memory`;
- OpenAI approval followed by developer publication of Plugins Directory
  version `0.1.0`; and
- public GitHub release `v0.1.0` with the exact submitted ZIP.

The submitted source commit is
`3c88e4623a5f18af6f5998e6189f13b733b6b704`. The 116,170-byte submitted ZIP has
SHA-256
`c69e85c2487259d9aa6d8cfbfb4e8f43a50c0752fa444ca2bbefa08459c6c999`.
`PUBLICATION_RECORD.json` binds these facts and the directory URL.

`PUBLIC_MANIFEST.json` retains `candidate_licensed_not_published` as the local
package-builder posture. It prevents a repository file from pretending to grant
submission authority; it is not the live portal status.

Directory publication is reviewed distribution, not an independent security
audit, OpenAI endorsement, upstream Codex adoption, or evidence of acquisition
interest.

## Remaining distribution verification

The portal generated the public directory URL. A clean installation and starter
prompt run should be repeated after directory propagation and retained as user-
visible distribution evidence. A temporary public-page loading error is not a
reason to republish or change the submitted bundle.

## Upstream Codex gate

A live import seam was verified in public `openai/codex` source at commit
`9fc715c0861c956c894a91890b78dc05b304ba29`. The feature was under development
and disabled by default at that pinned revision. The exact green-run evidence is
in `UPSTREAM_REPRODUCTION_EVIDENCE.md`.

Before upstream contact:

- obtain an independent human clean-checkout reproduction of the bundle-aware
  experiment while retaining ordinary Markdown as the compatibility baseline;
- refresh observed upstream behavior against then-current public source;
- distinguish observed behavior from the proposed invariant;
- begin with an issue or discussion, not an unsolicited pull request; and
- prepare production code only if maintainers invite or request it.

The current contribution guide is:

- https://github.com/openai/codex/blob/main/docs/contributing.md
