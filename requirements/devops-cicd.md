# VoiceKey DevOps and CI/CD Specification

> Version: 1.0
> Date: 2026-02-19

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
- Linux + Windows matrix execution
- dependency vulnerability scan

Optional but recommended:

- performance regression smoke on representative fixture audio

---

## 3. Release Pipeline Requirements

Trigger:

- semantic version tag (`vX.Y.Z`)

Stages:

1. checkout tagged commit
2. build artifacts for all channels
3. sign artifacts
4. generate checksums and SBOM
5. run install smoke tests from built artifacts
6. publish artifacts and release notes

---

## 4. Branch Protection Rules

- required status checks enabled
- no direct push to protected branches
- at least one reviewed approval
- signed tags for releases

---

## 5. Security Controls in Pipeline

- pinned action/workflow dependencies
- secret scanning on PR and main branch
- dependency audit and CVE triage policy
- release provenance metadata attached

---

## 6. Observability for CI/CD

- build duration
- flaky test rate
- release failure rate
- install smoke pass rate by platform

---

*Document Version: 1.0*  
*Last Updated: 2026-02-19*
