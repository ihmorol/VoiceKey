# VoiceKey Backlog Master

This backlog is implementation-ready and requirement-linked.

Priority legend:

- P0: required for baseline release
- P1: high-value next phase
- P2: expansion

## Execution Status (Live)

- Last updated: 2026-02-20
- E00-S01: complete (governance files and templates committed)
- E00-S02: complete (semver/changelog policy documented in contribution flow)
- E00-S03: complete (security disclosure SLA documented)
- E01-S01: complete (unit verification passed)
- E01-S02: implemented, verification failing (unit test failures require fixes)
- E01-S03: implemented, verification failing (dependency-mocking and test contract fixes required)
- E01-S04: in progress (confidence threshold behavior implemented, boundary integration pending)

---

## Epic E00 - Governance and Delivery Foundation (P0)

- Objective: establish OSS/legal/process foundations so engineering and release work is safe and repeatable.
- Requirement IDs: FR-OSS01, FR-OSS02, FR-OSS03, FR-OSS04, FR-OSS06, FR-OSS07
- Dependencies: none

### Story E00-S01 - Repository governance files

- Requirement IDs: FR-OSS01, FR-OSS02, FR-OSS03, FR-OSS07
- Outputs: `LICENSE`, `CONTRIBUTING.md`, `CODE_OF_CONDUCT.md`, `SECURITY.md`, issue/PR templates, DCO policy text.
- Acceptance criteria:
  - MIT license is present.
  - DCO sign-off workflow is documented and enforceable.
  - CLA is explicitly marked not required.
- Tasks:
  - E00-S01-T01 Create/update governance files with exact policy wording.
  - E00-S01-T02 Add DCO sign-off check guidance in contribution docs.
  - E00-S01-T03 Add issue templates for bug/feature/security.

### Story E00-S02 - Versioning and changelog governance

- Requirement IDs: FR-OSS04
- Acceptance criteria:
  - semantic versioning policy is documented and referenced from release workflow.
  - changelog structure defines breaking change and migration sections.
- Tasks:
  - E00-S02-T01 Define semver rules and examples.
  - E00-S02-T02 Define changelog entry format and release process hooks.

### Story E00-S03 - Security disclosure and SLA policy

- Requirement IDs: FR-OSS06
- Acceptance criteria:
  - SLA: 72h acknowledgement, 7-day triage update, 30-day target for high/critical remediation.
- Tasks:
  - E00-S03-T01 Finalize disclosure channel and SLA text.
  - E00-S03-T02 Link policy from README and release notes template.

---

## Epic E01 - Audio, VAD, and ASR Core Pipeline (P0)

- Objective: implement low-latency local speech pipeline with robust model/runtime controls.
- Requirement IDs: FR-A01, FR-A02, FR-A03, FR-A04, FR-A05, FR-A06, FR-W04
- Dependencies: E00

### Story E01-S01 - Real-time microphone capture

- Requirement IDs: FR-A01
- Inputs: audio device selection config, sample rate/channel config.
- Outputs: callback-based PCM frame producer with bounded queue.
- Edge cases: missing device, busy device, hot swap.
- Acceptance criteria:
  - mono 16kHz capture works on supported platforms.
  - callback thread never blocks on downstream processing.
- Tasks:
  - E01-S01-T01 Implement capture abstraction with health check.
  - E01-S01-T02 Add bounded queue and backpressure strategy.
  - E01-S01-T03 Add reconnect handling with retry backoff.

### Story E01-S02 - VAD gate integration

- Requirement IDs: FR-A02, FR-W04
- Outputs: speech/silence events, VAD confidence stream.
- Acceptance criteria:
  - ASR decode load reduced when no speech.
  - wake false-trigger mitigation honors VAD threshold.
- Tasks:
  - E01-S02-T01 Integrate local VAD in pipeline.
  - E01-S02-T02 Expose tunable thresholds from config.
  - E01-S02-T03 Add noisy-environment calibration helper.

### Story E01-S03 - faster-whisper streaming recognizer

- Requirement IDs: FR-A03, FR-A04, FR-A06
- Outputs: partial/final transcript events with metadata.
- Acceptance criteria:
  - profile switching supports `tiny/base/small`.
  - partial and final results emitted in order.
- Tasks:
  - E01-S03-T01 Implement ASR adapter for faster-whisper.
  - E01-S03-T02 Add model-profile runtime selection.
  - E01-S03-T03 Define transcript event schema.

### Story E01-S04 - Confidence threshold behavior

- Requirement IDs: FR-A05
- Behavior rule: below-threshold final transcript is dropped (never typed), and optional debug metric increments.
- Acceptance criteria:
  - threshold is configurable and enforced before dispatch.
- Tasks:
  - E01-S04-T01 Apply threshold in transcript-to-action boundary.
  - E01-S04-T02 Add metrics/log counters for dropped transcripts.

---

## Epic E02 - Wake Word and Command Parsing (P0)

- Objective: deterministic command/dictation parser with safe fallback behavior.
- Requirement IDs: FR-W01, FR-W02, FR-W03, FR-C01, FR-C02, FR-C03, FR-C04, FR-C05
- Dependencies: E01

### Story E02-S01 - Wake phrase detector and window timer

- Requirement IDs: FR-W01, FR-W02, FR-W03, FR-W04
- Acceptance criteria:
  - default phrase is `voice key` and configurable.
  - wake event opens listening window only; no direct typing.
  - wake window timeout defaults to 5s.
- Tasks:
  - E02-S01-T01 Implement wake phrase detector.
  - E02-S01-T02 Bind wake detector to FSM transition logic.
  - E02-S01-T03 Add wake timeout timer + reset rules.

### Story E02-S02 - Command parser core contract

- Requirement IDs: FR-C01, FR-C02, FR-C03
- Behavior rules:
  - suffix `command` => command candidate.
  - unknown command => type literal text (including suffix).
  - matching is case-insensitive with aliases.
- Acceptance criteria:
  - parser result schema is deterministic and test-covered.
- Tasks:
  - E02-S02-T01 Implement parser normalization pipeline.
  - E02-S02-T02 Implement alias and exact-match lookup.
  - E02-S02-T03 Implement literal fallback output path.

### Story E02-S03 - Fuzzy matching (feature toggle)

- Requirement IDs: FR-C04
- Acceptance criteria:
  - fuzzy matching disabled by default.
  - fuzzy behavior can be toggled and bounded by threshold.
- Tasks:
  - E02-S03-T01 Implement optional fuzzy matcher adapter.
  - E02-S03-T02 Add config flag + tests for on/off behavior.

### Story E02-S04 - Special phrase command channel

- Requirement IDs: FR-C05
- Acceptance criteria:
  - `pause voice key`, `resume voice key`, `voice key stop` recognized as system phrases.
  - phrase handling bypasses `command` suffix rules.
- Tasks:
  - E02-S04-T01 Implement phrase matcher in parser precedence chain.
  - E02-S04-T02 Add paused-state `resume`/`stop` handling tests.

### Story E02-S05 - Built-in command catalog implementation

- Requirement IDs: command groups in Section 4.4 and `requirements/commands.md`
- Acceptance criteria:
  - core editing and modifier commands implemented.
  - window commands and text-expansion-related commands are feature-gated for P1.
- Tasks:
  - E02-S05-T01 Build canonical command registry from `requirements/commands.md`.
  - E02-S05-T02 Add parser tests for every built-in phrase and alias.
  - E02-S05-T03 Enforce command catalog single-source-of-truth policy.

---

## Epic E03 - State Machine, Modes, and Safety (P0)

- Objective: ensure all runtime behavior is explicit, safe, and recoverable.
- Requirement IDs: FR-M01, FR-M02, FR-M03, FR-M04, FR-M05, FR-M06, FR-M07
- Dependencies: E01, E02

### Story E03-S01 - Full FSM implementation

- Requirement IDs: FR-M01, FR-M02, FR-M03
- Acceptance criteria:
  - mode-specific transitions for wake_word/toggle/continuous are implemented.
  - transitions are table-driven and testable.
- Tasks:
  - E03-S01-T01 Implement event-driven transition table.
  - E03-S01-T02 Implement mode entry/exit behavior.
  - E03-S01-T03 Add invalid-transition guard logic.

### Story E03-S02 - Inactivity watchdog and timers

- Requirement IDs: FR-W03, FR-M03, FR-M04, FR-M05
- Acceptance criteria:
  - inactivity auto-pause default 30s in toggle/continuous.
  - wake window timeout default 5s in wake mode.
- Tasks:
  - E03-S02-T01 Implement inactivity watchdog service.
  - E03-S02-T02 Integrate timer resets with VAD/transcript events.
  - E03-S02-T03 Add timeout telemetry counters.

### Story E03-S03 - Paused control plane behavior

- Requirement IDs: FR-C05, FR-M06, FR-M07
- Behavior rules:
  - dictation and non-system command execution disabled while paused.
  - only resume hotkey + optional phrase detector (enabled by default) remain active.
- Acceptance criteria:
  - paused state cannot type text.
  - `resume voice key` and resume hotkey both recover state.
- Tasks:
  - E03-S03-T01 Implement low-power paused phrase channel.
  - E03-S03-T02 Gate action router by paused-state policy.
  - E03-S03-T03 Add pause/resume race-condition tests.

### Story E03-S04 - Runtime resilience and edge handling

- Requirement IDs: Section 8 scenarios + Section 5.3 reliability
- Acceptance criteria:
  - no-mic, hotkey conflict, model checksum fail, keyboard block paths return actionable errors.
- Tasks:
  - E03-S04-T01 Implement structured runtime error taxonomy.
  - E03-S04-T02 Add bounded retry strategies.
  - E03-S04-T03 Add fallback-to-paused policy when safety cannot be guaranteed.

### Story E03-S05 - Single-instance and shutdown safety

- Requirement IDs: Section 5.3 reliability (single-instance, crash-safe shutdown and queue drain)
- Acceptance criteria:
  - startup fails fast with actionable error when another VoiceKey process already owns the runtime lock.
  - shutdown drains or safely discards pending dispatch queue without partial output corruption.
- Tasks:
  - E03-S05-T01 Implement single-instance process lock with cross-platform adapters.
  - E03-S05-T02 Implement shutdown queue-drain policy and timeout guard.
  - E03-S05-T03 Add duplicate-start and shutdown-race tests.

---

## Epic E04 - Platform Backends and OS Compatibility (P0)

- Objective: stable Linux/Windows behavior with deterministic degradation rules.
- Requirement IDs: FR-S04, platform requirements Section 7, error handling Section 8
- Dependencies: E03

### Story E04-S01 - Keyboard backend abstraction and adapters

- Requirement IDs: technology decisions and platform requirements
- Acceptance criteria:
  - Linux and Windows keyboard adapters expose same contract.
  - capability self-check reports degraded states.
- Tasks:
  - E04-S01-T01 Implement base keyboard interface + error codes.
  - E04-S01-T02 Implement Linux adapter (X11 path + fallback hooks).
  - E04-S01-T03 Implement Windows adapter (standard/admin behavior).

### Story E04-S02 - Global hotkey backend

- Requirement IDs: FR-M02, FR-S03
- Acceptance criteria:
  - hotkeys register/unregister dynamically from config.
  - conflicts return alternatives.
- Tasks:
  - E04-S02-T01 Implement hotkey abstraction.
  - E04-S02-T02 Add conflict detection and fallback suggestion logic.

### Story E04-S03 - Wayland/X11 and Windows compatibility matrix behavior

- Requirement IDs: FR-S04, Section 7.1, 7.2
- Acceptance criteria:
  - Wayland explicitly warns and exposes reduced capability message.
  - Windows standard/admin behavior documented by self-check.
  - Linux/Windows autostart adapters are validated at startup with clear remediation on failure.
- Tasks:
  - E04-S03-T01 Implement display-session detection and warnings.
  - E04-S03-T02 Implement startup compatibility self-test report.
  - E04-S03-T03 Implement autostart adapter validation and diagnostics.

### Story E04-S04 - Window command backend (P1 gated)

- Requirement IDs: window command set in Section 4.4
- Acceptance criteria:
  - commands work when feature flag is enabled.
  - disabled by default in P0 baseline.
- Tasks:
  - E04-S04-T01 Implement window backend interfaces.
  - E04-S04-T02 Implement OS-specific window operations.
  - E04-S04-T03 Bind feature flag to parser routing.

---

## Epic E05 - User Interface Surfaces (P0)

- Objective: expose reliable operator UX via CLI, dashboard, and tray.
- Requirement IDs: FR-S01, FR-S02, FR-S03, FR-S05, FR-G02
- Dependencies: E03, E04

### Story E05-S01 - CLI contract and commands

- Requirement IDs: FR-G02 + commands from installation/troubleshooting docs
- Acceptance criteria:
  - CLI supports start/status/devices/commands/config/download/calibrate/diagnostics.
  - command help and error codes are deterministic.
- Tasks:
  - E05-S01-T01 Implement CLI command registry and parser.
  - E05-S01-T02 Define exit-code contract and machine-readable output mode.
  - E05-S01-T03 Add CLI smoke tests.

### Story E05-S02 - Terminal dashboard

- Requirement IDs: FR-S02, usability Section 5.5
- Acceptance criteria:
  - dashboard shows state, latency, and last action.
  - paused/listening indicators are always clear.
- Tasks:
  - E05-S02-T01 Build dashboard renderer and state binding.
  - E05-S02-T02 Add refresh throttling and non-blocking updates.

### Story E05-S03 - Tray runtime and daemon mode

- Requirement IDs: FR-S01, FR-S02, FR-S03, FR-S05
- Acceptance criteria:
  - tray state maps to runtime state.
  - daemon starts without terminal UI; tray active only in graphical session.
- Tasks:
  - E05-S03-T01 Implement tray controller and menu actions.
  - E05-S03-T02 Implement daemon start behavior by session type.
  - E05-S03-T03 Add tray action integration tests.

---

## Epic E06 - Configuration, Onboarding, and Extensibility (P0/P1)

- Objective: predictable setup and extensibility with schema-safe config lifecycle.
- Requirement IDs: FR-O01..FR-O05, FR-G01..FR-G06
- Dependencies: E05

### Story E06-S01 - Config schema and persistence

- Requirement IDs: FR-G01
- Acceptance criteria:
  - all config keys validated with bounds/types.
  - invalid values fallback safely with warnings.
- Tasks:
  - E06-S01-T01 Implement typed schema + serializer.
  - E06-S01-T02 Implement load/save + backup behavior.
  - E06-S01-T03 Implement config error reporting.

### Story E06-S02 - Config migration engine

- Requirement IDs: FR-G01 + migration policy
- Acceptance criteria:
  - versioned migration is idempotent and rollback-safe.
- Tasks:
  - E06-S02-T01 Implement migration registry.
  - E06-S02-T02 Add migration tests for corrupt/legacy configs.

### Story E06-S03 - Onboarding wizard

- Requirement IDs: FR-O01, FR-O02, FR-O03, FR-O04, FR-O05
- Acceptance criteria:
  - wizard completes in <=5 minutes under normal conditions.
  - mic test, wake test, hotkey setup, autostart preference, tutorial all present.
- Tasks:
  - E06-S03-T01 Implement onboarding flow state machine.
  - E06-S03-T02 Persist selected values into config.
  - E06-S03-T03 Add onboarding e2e tests.

### Story E06-S04 - Custom commands

- Requirement IDs: FR-G03
- Acceptance criteria:
  - user-defined command phrases map to key-combo/text actions.
- Tasks:
  - E06-S04-T01 Implement custom command loader/validator.
  - E06-S04-T02 Integrate custom commands into parser precedence.

### Story E06-S05 - Text expansion snippets (P1)

- Requirement IDs: FR-G04
- Acceptance criteria:
  - snippets are disabled by default in P0.
  - enabling snippets applies deterministic expansions.
- Tasks:
  - E06-S05-T01 Implement snippet expansion engine.
  - E06-S05-T02 Add loop-prevention and recursion guards.

### Story E06-S06 - Per-app profiles (P1)

- Requirement IDs: FR-G05
- Acceptance criteria:
  - profile resolution by active app identity works.
  - fallback profile applies when no app-specific profile exists.
- Tasks:
  - E06-S06-T01 Implement app identity resolver.
  - E06-S06-T02 Implement profile override merge strategy.

### Story E06-S07 - Portable mode (P1)

- Requirement IDs: FR-G06, FR-D06
- Acceptance criteria:
  - portable artifact runs with local config/data paths.
  - no global install requirement.
- Tasks:
  - E06-S07-T01 Implement path strategy for portable runtime.
  - E06-S07-T02 Package portable artifact and smoke test.

### Story E06-S08 - Config path overrides and runtime reload contract

- Requirement IDs: FR-G01, FR-G02, `requirements/configuration.md` sections 1 and 6, `architecture.md` section 10.2
- Acceptance criteria:
  - config resolution precedence is deterministic across default path, ENV override, and CLI override.
  - supported environment variables are parsed and validated at startup with actionable errors on invalid values.
  - safe-to-reload keys apply without restart; restart-required keys emit explicit restart-needed signal.
- Tasks:
  - E06-S08-T01 Implement config path resolver with precedence tests.
  - E06-S08-T02 Implement env-var adapters (`VOICEKEY_CONFIG`, `VOICEKEY_MODEL_DIR`, `VOICEKEY_LOG_LEVEL`, `VOICEKEY_DISABLE_TRAY`).
  - E06-S08-T03 Implement hot-reload policy engine and restart-required notifications.

### Story E06-S09 - Onboarding accessibility and skip-default safety

- Requirement IDs: FR-O01, FR-O02, FR-O03, FR-O04, FR-O05, `requirements/onboarding.md` section 5
- Acceptance criteria:
  - onboarding flow is fully keyboard navigable with no mandatory mouse actions.
  - onboarding skip path writes safe defaults and records explicit skipped-step status.
  - onboarding timing evidence includes both completion and skip flows.
- Tasks:
  - E06-S09-T01 Implement keyboard-only interaction map for all wizard screens.
  - E06-S09-T02 Implement skip-flow safe-default writer and audit marker.
  - E06-S09-T03 Add accessibility and skip-path e2e tests.

---

## Epic E07 - Distribution and Packaging (P0/P1)

- Objective: deliver secure, verifiable, cross-platform release artifacts.
- Requirement IDs: FR-D01..FR-D09
- Dependencies: E00, E05, E06

### Story E07-S01 - PyPI packaging

- Requirement IDs: FR-D01
- Acceptance criteria:
  - wheel/sdist publishable and installable from clean env.
- Tasks:
  - E07-S01-T01 Build package metadata and entry points.
  - E07-S01-T02 Add clean-environment install smoke job.

### Story E07-S02 - Windows artifacts

- Requirement IDs: FR-D02
- Acceptance criteria:
  - signed installer and portable zip produced and smoke-tested.
- Tasks:
  - E07-S02-T01 Define installer build script.
  - E07-S02-T02 Define portable packaging script.
  - E07-S02-T03 Integrate code signing step.

### Story E07-S03 - Linux artifacts

- Requirement IDs: FR-D03
- Acceptance criteria:
  - AppImage and pip channel both available and validated.
- Tasks:
  - E07-S03-T01 Build AppImage pipeline.
  - E07-S03-T02 Run launch smoke on Ubuntu targets.

### Story E07-S04 - Artifact integrity bundle

- Requirement IDs: FR-D04, FR-D07, FR-D08, FR-D09
- Acceptance criteria:
  - signed checksums, SBOM, provenance manifest attached per release.
- Tasks:
  - E07-S04-T01 Generate SHA256SUMS for all artifacts.
  - E07-S04-T02 Sign release bundle and tag.
  - E07-S04-T03 Generate CycloneDX SBOM and provenance metadata.

### Story E07-S05 - Model distribution policy

- Requirement IDs: FR-D05
- Acceptance criteria:
  - model not bundled in core installers.
  - checksum-verified download with mirror fallback.
- Tasks:
  - E07-S05-T01 Implement model downloader and checksum verifier.
  - E07-S05-T02 Implement fallback mirror strategy.

### Story E07-S06 - Distribution compatibility and artifact policy enforcement

- Requirement IDs: `requirements/distribution.md` sections 2, 3, and 6
- Acceptance criteria:
  - release artifacts strictly follow naming convention for each channel.
  - public release matrix enforces x64-only channel scope unless requirements are updated.
  - backward-compatibility policy includes migration path support for one previous major version.
- Tasks:
  - E07-S06-T01 Implement artifact naming validator in release pipeline.
  - E07-S06-T02 Implement release-channel architecture gate checks.
  - E07-S06-T03 Add compatibility/migration policy validation in release checklist automation.

---

## Epic E08 - CI/CD and Release Operations (P0/P1)

- Objective: ensure every change and release is validated and reproducible.
- Requirement IDs: FR-CI01..FR-CI10
- Dependencies: E07

### Story E08-S01 - PR pipeline

- Requirement IDs: FR-CI01, FR-CI02, FR-CI03, FR-CI04
- Acceptance criteria:
  - required checks block merge on failure.
  - linux/windows matrix always executed.
- Tasks:
  - E08-S01-T01 Implement CI workflow for lint/tests/scans.
  - E08-S01-T02 Add performance guardrail checks (P1 enforcement toggle).

### Story E08-S02 - Tag-based release pipeline

- Requirement IDs: FR-CI05, FR-CI06, FR-CI07, FR-CI10
- Acceptance criteria:
  - release triggers only on signed semantic tags.
  - PyPI publish path uses OIDC trusted publishing.
- Tasks:
  - E08-S02-T01 Implement release workflow with protected trigger.
  - E08-S02-T02 Add OIDC-based PyPI publish step.
  - E08-S02-T03 Generate release notes from changelog metadata.

### Story E08-S03 - Post-publish validation and rollback

- Requirement IDs: FR-CI08, FR-CI09
- Acceptance criteria:
  - post-publish install smoke matrix runs for all release channels.
  - rollback/yank runbook is executable and tested.
- Tasks:
  - E08-S03-T01 Implement post-publish smoke jobs.
  - E08-S03-T02 Implement rollback decision and runbook automation hooks.

### Story E08-S04 - CI security hardening and governance controls

- Requirement IDs: `requirements/devops-cicd.md` sections 2, 4, 5, and 6
- Acceptance criteria:
  - PR pipeline runs secret scan and license compliance scan as required checks.
  - branch protection and CODEOWNERS review requirements are enforced for release workflow changes.
  - workflows pin external action dependencies and use least-privilege permissions per job.
  - CI observability metrics (duration, flaky rate, failure rate, smoke pass rate) are published per run.
- Tasks:
  - E08-S04-T01 Add secret/license scan jobs with merge-blocking policy.
  - E08-S04-T02 Add branch-protection and CODEOWNERS policy checks.
  - E08-S04-T03 Add workflow hardening checks (pinned actions, permissions) and CI metrics export.

---

## Epic E09 - Security and Privacy Runtime Controls (P0)

- Objective: enforce privacy-by-default and secure release operations.
- Requirement IDs: Section 5.4 + `requirements/security.md` + FR-D07/08
- Dependencies: E07, E08

### Story E09-S01 - Data minimization controls

- Requirement IDs: Section 5.4 privacy, `requirements/security.md` section 2
- Acceptance criteria:
  - raw audio not persisted by default.
  - transcript logging off by default.
  - debug redaction on by default.
- Tasks:
  - E09-S01-T01 Enforce logger redaction pipeline.
  - E09-S01-T02 Add privacy regression tests.

### Story E09-S02 - Secure diagnostics and incident handling

- Requirement IDs: `requirements/security.md` sections 4.1 and 6
- Acceptance criteria:
  - diagnostics export is redacted by default.
  - incident response flow matches security docs.
- Tasks:
  - E09-S02-T01 Implement diagnostics export schema.
  - E09-S02-T02 Add security incident runbook checks.

### Story E09-S03 - Runtime network and telemetry guardrails

- Requirement IDs: Section 5.4 privacy, `architecture.md` section 12, `requirements/configuration.md` privacy defaults
- Acceptance criteria:
  - no outbound network calls occur during normal runtime after model download/install.
  - telemetry remains disabled by default and cannot be enabled implicitly by upgrade/migration.
  - privacy guardrail tests fail build on runtime egress regression.
- Tasks:
  - E09-S03-T01 Implement runtime egress guard for non-download pipeline.
  - E09-S03-T02 Add startup assertions for privacy default flags and migration safety.
  - E09-S03-T03 Add offline-runtime and telemetry-default regression tests.

---

## Epic E10 - Testing, Benchmarks, and Quality Gates (P0)

- Objective: enforce measurable quality and non-functional targets.
- Requirement IDs: Section 5, Section 9, `requirements/testing-strategy.md`
- Dependencies: E01..E09

### Story E10-S01 - Unit test baseline

- Requirement IDs: `requirements/testing-strategy.md` unit and safety layers
- Acceptance criteria:
  - parser, FSM, config migration, backend capability checks covered.
- Tasks:
  - E10-S01-T01 Add unit suites for parser and mode logic.
  - E10-S01-T02 Add schema/migration validation tests.

### Story E10-S02 - Integration suite

- Requirement IDs: `requirements/testing-strategy.md` integration layer
- Acceptance criteria:
  - end-to-end mic->ASR->router->inject path tested.
  - tray/autostart integration tested.
- Tasks:
  - E10-S02-T01 Build deterministic integration harness using fixture audio.
  - E10-S02-T02 Add tray/autostart test fixtures.

### Story E10-S03 - Performance benchmark harness

- Requirement IDs: Section 5.1/5.2 performance and resource budgets
- Acceptance criteria:
  - p50 <= 200ms and p95 <= 350ms measured on reference machines.
  - idle/active resource budgets measured and reported.
- Tasks:
  - E10-S03-T01 Implement benchmark runner and report format.
  - E10-S03-T02 Add CI perf regression comparator.

### Story E10-S04 - Distribution verification tests

- Requirement IDs: FR-CI08, `requirements/testing-strategy.md` section 5
- Acceptance criteria:
  - pip, installer, portable, AppImage install/launch smoke all pass.
  - artifact checksum/signature verification path tested.
- Tasks:
  - E10-S04-T01 Implement release smoke matrix jobs.
  - E10-S04-T02 Implement artifact integrity verification tests.

### Story E10-S05 - Reliability and soak testing

- Requirement IDs: Section 5.3 reliability, `requirements/testing-strategy.md` section 3
- Acceptance criteria:
  - reconnect, rapid toggles, paused-resume phrase path, and long-run stability are validated.
- Tasks:
  - E10-S05-T01 Add reconnect and mode-race test cases.
  - E10-S05-T02 Add long-duration soak tests with memory leak monitoring.

### Story E10-S06 - Compatibility matrix and test-runtime governance

- Requirement IDs: `requirements/testing-strategy.md` CI matrix requirements
- Acceptance criteria:
  - CI evidence includes Ubuntu 22.04/24.04, Windows 10/11, and Python 3.11/3.12 coverage or documented waivers.
  - matrix drift fails the quality gate before release tagging.
- Tasks:
  - E10-S06-T01 Implement matrix coverage assertion checks in CI.
  - E10-S06-T02 Publish matrix coverage report artifact per release candidate.

---

## Epic E11 - Documentation and Developer Enablement (P0/P1)

- Objective: keep implementation and operations understandable and reproducible.
- Requirement IDs: Section 11 and Section 15 artifact requirements
- Dependencies: all epics

### Story E11-S01 - User docs completeness

- Requirement IDs: Section 11 and Section 15 required implementation artifacts
- Acceptance criteria:
  - installation, onboarding, troubleshooting, command docs are current and release-linked.
- Tasks:
  - E11-S01-T01 Validate docs against released artifacts and CLI outputs.
  - E11-S01-T02 Add platform-specific caveats and screenshots/examples.

### Story E11-S02 - Developer docs completeness

- Requirement IDs: FR-OSS05, `requirements/development.md`, `requirements/devops-cicd.md`
- Acceptance criteria:
  - development/testing/devops docs align with actual workflow.
  - compatibility matrix is published and updated per release.
- Tasks:
  - E11-S02-T01 Update development guide with exact toolchain and gates.
  - E11-S02-T02 Maintain compatibility matrix and architecture deltas.

### Story E11-S03 - Backlog and traceability maintenance

- Requirement IDs: backlog execution and traceability maintenance rules
- Acceptance criteria:
  - every requirement maps to implemented stories and test evidence.
- Tasks:
  - E11-S03-T01 Update `TRACEABILITY_MATRIX.md` each release.
  - E11-S03-T02 Block release if any requirement has missing coverage.

---

## Epic E12 - Ecosystem Expansion (P2)

- Objective: deliver extensibility and internationalization features planned for roadmap expansion.
- Requirement IDs: Section 10 P2 roadmap, `requirements/implementation-plan.md` phase 3
- Dependencies: E10, E11

### Story E12-S01 - Plugin SDK contract and safety model

- Requirement IDs: P2 plugin SDK requirement
- Acceptance criteria:
  - plugin API contract includes lifecycle hooks, permission model, and compatibility versioning.
  - plugin execution sandbox rules are documented and test-covered.
- Tasks:
  - E12-S01-T01 Define plugin manifest and runtime interface contracts.
  - E12-S01-T02 Implement plugin capability gating and safety checks.
  - E12-S01-T03 Add SDK reference plugin and validation tests.

### Story E12-S02 - Language pack workflow

- Requirement IDs: P2 multi-language pack requirement
- Acceptance criteria:
  - language pack packaging and activation workflow is deterministic.
  - fallback language behavior is explicit and test-covered.
- Tasks:
  - E12-S02-T01 Define language pack manifest and install flow.
  - E12-S02-T02 Implement language fallback and conflict resolution logic.
  - E12-S02-T03 Add integration tests for language-pack activation lifecycle.

### Story E12-S03 - Advanced automation command plugins

- Requirement IDs: P2 advanced automation command plugin requirement
- Acceptance criteria:
  - automation command plugins run through same parser safety contracts as built-ins.
  - plugin-driven commands remain feature-gated by default.
- Tasks:
  - E12-S03-T01 Define automation plugin action contract and guardrails.
  - E12-S03-T02 Implement registry integration for plugin command packs.
  - E12-S03-T03 Add negative and abuse-case tests for plugin command execution.

---

## Global Done Criteria (Release Candidate)

All of the following must be true:

1. Every P0 story is complete and accepted.
2. `TRACEABILITY_MATRIX.md` shows 100% coverage for P0 requirements.
3. Release checklist passes in full.
4. No unresolved critical/high defects in core safety and typing path.
5. Security/privacy defaults verified in runtime behavior.
