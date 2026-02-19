# VoiceKey Implementation and Release Plan

> Version: 2.0
> Date: 2026-02-19

---

## Phase 0: DevOps and Distribution Foundation (P0)

1. Define packaging strategy (PyPI, Windows installer+portable, Linux AppImage+pip).
2. Set up CI pipeline for PR validation (lint/test/scan matrix).
3. Set up release pipeline for tag-based artifact builds.
4. Add release signing, checksums, and SBOM generation.
5. Add install smoke tests per target artifact.
6. Add OSS governance files (license, contributing, code of conduct, security policy).
7. Implement legal/process baseline: MIT license, DCO sign-off policy, no CLA, vulnerability SLA in `SECURITY.md`.

Exit criteria:

- CI required checks enforced on PRs.
- Release workflow produces signed, verifiable artifacts.
- install smoke matrix passes in Linux and Windows.

---

## Phase 1: Core Product Baseline (P0)

1. Build config/schema foundation with migration support.
2. Implement audio + VAD + wake detection.
3. Integrate faster-whisper ASR.
4. Implement parser and keyboard routing.
5. Add inactivity watchdog.
6. Add tray, daemon mode, and autostart.
7. Build first-run wizard.

Exit criteria:

- core acceptance criteria pass.
- performance gate p50/p95 pass on reference devices.

---

## Phase 2: Productivity Expansion (P1)

1. Add window command backend.
2. Add text expansion snippets.
3. Add per-app profile resolution.
4. Add portable mode packaging flow.

Exit criteria:

- P1 feature tests pass.
- docs updated for all new UX paths.

---

## Phase 3: Ecosystem (P2)

1. Define plugin SDK contract.
2. Add language pack workflows.
3. Add advanced automation command packs.

---

## Verification Gates

- architecture review gate
- security/privacy review gate
- benchmark gate
- cross-platform compatibility gate
- release readiness checklist gate

---

*Document Version: 2.0*  
*Last Updated: 2026-02-19*
