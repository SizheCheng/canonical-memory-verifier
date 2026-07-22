# Threat model

## Protected boundary

The verifier protects a consumer that has been explicitly given one external
memory bundle and wants to reject malformed, corrupted, ambiguous, or
authority-confused input before retrieval.

It is designed to detect:

- source files that no longer match their declared size or hash;
- unsafe paths, hidden files, undeclared files, and nonregular source entries;
- missing, duplicate, or unclosed declared source references;
- dangling, cross-key, cyclic, or self-supersession;
- multiple current heads without silently choosing one;
- remembered claims presented as eligible for live approval;
- parser ambiguity from duplicate keys, non-finite numbers, or unbounded input.

## Explicit non-goals

The verifier does not:

- prove that a source or claim is factually true;
- decide whether an agent should trust a producer;
- prevent prompt injection inside source bytes;
- provide encryption, access control, identity, authentication, or tenancy;
- scan a user's chats or filesystem for memory;
- enforce a host's tool-call approval or sandbox;
- certify an implementation as OpenAI-approved.

The authority invariant is an import-data invariant. The host runtime must still
refuse execution without fresh authority from its own control plane.

## Adversaries and failures

The candidate assumes the selected bundle may be corrupt, partially generated,
malicious, stale, or produced by a buggy agent. It also assumes a consumer may
accidentally treat old natural-language permission as current approval.

It does not assume the local Python runtime, operating system, or verifier source
code is trusted against an already-compromised host.

## Fail-closed behavior

No projection or trace is returned when verification fails. Ambiguous heads are
a contract failure, not an invitation for the model to choose one.
