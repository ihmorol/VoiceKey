# VoiceKey DevOps and CI/CD Specification

> Version: 1.2
> Date: 2026-02-26

---

## 1. CI/CD Principles

1. every change is tested before merge
2. every release is reproducible and verifiable
3. release builds are tag-driven and immutable

---

## 2. PR Pipeline Requirements

Required jobs:

- lint and formatting checks
- unit tests
- integration smoke tests
- hybrid ASR smoke tests (local-only + hybrid fallback paths)
- Linux + Windows matrix execution
- dependency vulnerability scan
- secret scan and license compliance scan

Optional but recommended:

- performance regression smoke on representative fixture audio

---

## 3. Release Pipeline Requirements

Trigger:

- semantic version tag (`vX.Y.Z`)
- release tags must be signed and created from protected branch

Stages:

1. checkout tagged commit
2. build artifacts for all channels
3. sign artifacts
4. generate checksums and SBOM
5. run install smoke tests from built artifacts
6. publish artifacts and release notes

Publishing and provenance rules:

- PyPI publishing must use trusted publishing (OIDC), not long-lived API tokens.
- Release provenance attestation must be emitted and attached to release artifacts.
- Release fails hard if any artifact signing/checksum/SBOM step fails.

---

## 4. Branch Protection Rules

- required status checks enabled
- no direct push to protected branches
- at least one reviewed approval
- signed tags for releases
- required CODEOWNERS review for release pipeline changes

---

## 5. Security Controls in Pipeline

- pinned action/workflow dependencies
- secret scanning on PR and main branch
- dependency audit and CVE triage policy
- release provenance metadata attached
- workflow permissions minimized per job
- signing keys kept outside repository and rotated on schedule

---

## 7. Release Rollback Policy

- if post-publish smoke tests fail, maintainers must halt promotion and issue rollback notice
- PyPI: yank affected version
- GitHub releases: mark as superseded and publish hotfix timeline
- all rollback actions must be documented in release incident log

---

## 6. Observability for CI/CD

- build duration
- flaky test rate
- release failure rate
- install smoke pass rate by platform

---

*Document Version: 1.2*  
*Last Updated: 2026-02-26*
