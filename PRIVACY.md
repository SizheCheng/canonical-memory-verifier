# Privacy policy

Effective date: 2026-07-22

Canonical Memory Verifier is a local, read-only skills plugin. The publisher
does not operate a server for this plugin and does not receive, collect, store,
sell, or share the bundle data processed by the bundled verifier.

## Data processed

The verifier reads only the bundle directory explicitly selected by the user.
It checks the bundle manifest, declared source-file sizes and hashes, claims,
and supersession edges. It does not discover chats, scan a home directory,
contact a network service, or write to the selected bundle.

## Output

The verifier emits a bounded JSON conformance result. Projection and trace
commands may include claim values, identifiers, source metadata, and declared
relationships. If the user runs the skill in ChatGPT or Codex, that output is
handled by the host product under the user's agreement with OpenAI; it is not
sent to this plugin's publisher.

## Retention and telemetry

The plugin contains no publisher telemetry, cookies, analytics, advertising,
or persistent storage. The host product, operating system, shell, and source
repository may keep their own logs according to their own policies.

## User responsibility

Users should process only bundles they are authorized to access and should not
publish private source bytes in support reports. This policy will be updated if
a future release adds any hosted service or publisher-side data processing.
