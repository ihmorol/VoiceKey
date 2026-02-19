# VoiceKey Implementation and Release Plan

> Version: 2.1 (Backlog-aligned)
> Date: 2026-02-19

---

## Phase 0: Governance and CI Bootstrap (P0, early foundation)

Backlog alignment: E00 + early E08-S01 + baseline E11-S02

1. Complete OSS/legal foundation:
   - LICENSE, CONTRIBUTING, CODE_OF_CONDUCT, SECURITY, issue/PR templates, DCO policy.
2. Establish minimum PR validation pipeline:
   - lint, unit tests, integration smoke, Linux/Windows matrix, vulnerability scan.
3. Add CI hardening baseline:
   - secret scan, license compliance scan, pinned actions, least-privilege workflow permissions.
4. Establish release-governance docs baseline:
   - semver policy, changelog policy, compatibility matrix ownership.

Exit criteria:

- governance files and legal policy are complete and linked.
- required PR checks are enforced and merge-blocking.
- security/governance CI controls are active for pull requests.

---

## Phase 1: Core Runtime Baseline (P0)

Backlog alignment: E01, E02, E03, E04, E05, E06 (P0 stories only)

1. Implement audio capture + VAD + faster-whisper transcript flow.
2. Implement wake detection and parser contracts, including unknown-command literal fallback.
3. Implement runtime state machine, inactivity watchdog, paused control plane, and shutdown safety.
4. Implement platform adapters for keyboard/hotkey/session compatibility behavior.
5. Implement user surfaces: CLI, dashboard, tray/daemon behavior.
6. Implement config/onboarding P0 scope:
   - schema + migration, custom commands, config override/reload contract, onboarding accessibility/skip-safe defaults.

Exit criteria:

- core acceptance behavior from software requirements is test-covered.
- pause/resume and unknown-command safety rules are verified.
- core runtime works on Linux/Windows baseline paths.

---

## Phase 2: Distribution, CI/CD, and Runtime Security Hardening (P0)

Backlog alignment: E07, E08, E09

1. Implement packaging outputs:
   - PyPI, Windows installer + portable, Linux AppImage.
2. Add integrity bundle:
   - SHA256SUMS, signatures, SBOM, provenance metadata.
3. Implement tag-triggered release workflow and post-publish smoke matrix.
4. Enforce CI governance controls:
   - branch protection/CODEOWNERS checks, security scans, CI observability metrics.
5. Enforce runtime privacy/security defaults and egress guardrails.

Exit criteria:

- release pipeline can produce signed/verifiable artifacts from tags.
- post-publish smoke and rollback/yank procedures are executable.
- privacy/security defaults are validated by tests.

---

## Phase 3: Quality Gates and Release Candidate (P0)

Backlog alignment: E10, E11

1. Complete unit/integration/perf/reliability/distribution verification suites.
2. Enforce compatibility matrix governance (Ubuntu/Windows + Python versions).
3. Finalize user/dev docs and release-linked traceability maintenance.
4. Run release checklist and coverage gates.

Exit criteria:

- global done criteria in backlog are met for all P0 stories.
- traceability matrix coverage and verification evidence are complete.
- release checklist passes fully.

---

## Phase 4: Productivity Expansion (P1)

Backlog alignment: E04-S04, E06-S05, E06-S06, E06-S07 (+ related test/docs updates)

1. Enable window command backend (feature-gated by default until gate pass).
2. Add text expansion snippets.
3. Add per-application profiles.
4. Finalize portable-mode UX and packaging validation.

Exit criteria:

- P1 feature tests pass.
- documentation is updated for all new user paths.
- feature flags/default safety behavior remains compliant.

---

## Phase 5: Ecosystem Expansion (P2)

Backlog alignment: E12

1. Define and implement plugin SDK contract and safety model.
2. Add language-pack workflow and fallback behavior.
3. Add advanced automation command plugin support.

Exit criteria:

- P2 roadmap stories pass contract and safety tests.
- ecosystem extension points are documented and versioned.

---

## Verification Gates (Release Governance)

1. requirement-to-story-to-test traceability gate (`backlog/TRACEABILITY_MATRIX.md`).
2. security/privacy defaults gate.
3. benchmark/performance gate.
4. cross-platform compatibility gate.
5. distribution integrity gate (signing/checksum/SBOM/provenance).
6. release readiness checklist gate (`requirements/release-checklist.md`).

---

*Document Version: 2.1*  
*Last Updated: 2026-02-19*
