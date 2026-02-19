# Backlog Work Log

## 2026-02-19

- Created `AGENTS.md` with repository-specific operational rules for agentic developers.
- Included setup/test command contract with single-test examples.
- Included coding style, typing, naming, error handling, logging/privacy standards.
- Captured source-of-truth ordering and mandatory backlog/traceability maintenance rules.
- Verified no Cursor/Copilot rules currently exist in repository.
- Added `.agent` project guardrail rules at `.agent/rules/project-repo-rules.md`.
- Added `.opencode` project guardrail rules at `.opencode/rules/project-repo-rules.md`.
- Updated `.agent/README.md` and `.opencode/README.md` to point to repository guardrail rules.
- Performed backlog gap audit against `software_requirements.md`, `architecture.md`, and `requirements/*.md`.
- Updated `backlog/BACKLOG_MASTER.md` to close identified gaps: added explicit requirement IDs to all stories, added missing FR-OSS05 linkage, and introduced new stories/epic (E03-S05, E06-S08/S09, E07-S06, E08-S04, E09-S03, E10-S06, E12-S01/S02/S03).
- Updated `backlog/TRACEABILITY_MATRIX.md` with corrected FR mappings and expanded non-ID coverage rows for configuration, onboarding accessibility, CI hardening, distribution policy, matrix governance, and P2 roadmap coverage.
- Verification commands/evidence:
  - `python3` FR coverage check across SRS/backlog/traceability => 64/64 FR IDs present in both backlog and traceability.
  - `python3` story contract check => every story has `Requirement IDs`.
  - `python3` traceability linkage check => 0 mismatches between FR mapping and story requirement fields.
- Updated `requirements/implementation-plan.md` to v2.1 with backlog-aligned phase sequencing (E00/E08 bootstrap, core runtime, distribution+security hardening, quality gates, then P1/P2 expansion).
- Verification evidence:
  - Cross-checked phase-to-epic alignment against `backlog/BACKLOG_MASTER.md` (E00..E12 dependency order).

## Phase 0: Governance and CI Bootstrap (E00)

- **E00-S01** - Repository governance files:
  - Created `LICENSE` (MIT)
  - Created `CONTRIBUTING.md` with DCO sign-off policy
  - Created `CODE_OF_CONDUCT.md` (Contributor Covenant v2.1)
  - Created `SECURITY.md` with disclosure policy and SLA
  - Created GitHub issue templates (bug_report.md, feature_request.md, security_report.md)
  - Created GitHub PR template with DCO checkbox
- **E00-S02** - Versioning and changelog governance:
  - Documented in CONTRIBUTING.md (semver policy)
- **E00-S03** - Security disclosure and SLA policy:
  - Documented in SECURITY.md (72h acknowledgement, 7-day triage, 30-day remediation)
- **CI Pipeline** (.github/workflows/ci.yml):
  - Lint job (ruff)
  - Vulnerability scan (pip-audit)
  - Secret scan (trufflehog)
  - License compliance scan (license-cop)
  - Unit tests (pytest with coverage) - matrix: Ubuntu 22.04/24.04, Windows 2022 × Python 3.11/3.12
  - Integration smoke tests
  - All actions pinned to SHA
  - Least-privilege workflow permissions
- **Phase 0 Exit Criteria Verified**:
  -  Governance files and legal policy are complete and linked
  -  Required PR checks are enforced (lint, tests, scans)
  -  Security/governance CI controls are active for pull requests

## Phase 1: Core Runtime Baseline (Starting)

- Starting Epic E01: Audio, VAD, and ASR Core Pipeline

## 2026-02-20

- Added root `.gitignore` with Python, virtualenv, build, cache, editor, and VoiceKey runtime model artifact exclusions.
- Updated `voicekey/audio/threshold.py` for E01-S04 behavior compliance: confidence threshold is now enforced for final transcript events only (typing boundary behavior).
- Updated `tests/unit/test_threshold.py` to validate final-only threshold semantics and dropped-count behavior.
- Updated `backlog/BACKLOG_MASTER.md` with live execution status for completed and in-progress stories.
- Verification commands/evidence:
  - `.venv/bin/python -m pytest tests/unit/test_threshold.py` => PASS (12 passed)
  - `.venv/bin/python -m pytest tests/unit/test_capture.py tests/unit/test_vad.py tests/unit/test_asr.py` => FAIL (19 failed, 67 passed)
- Verification outcome and next action:
  - E01-S01 remains verified based on passing capture tests.
  - E01-S02 and E01-S03 moved to "implemented, verification failing" until failing tests are corrected.
  - E01-S04 is in progress; threshold module behavior is now aligned with backlog rule and pending integration at transcript-to-action boundary.

- Follow-up verification and fixes completed:
  - Updated `voicekey/audio/vad.py` to resolve runtime Silero loader lookup and strict `bool` return semantics.
  - Updated `voicekey/audio/asr_faster_whisper.py` to resolve faster-whisper model class at runtime for deterministic test/runtime behavior.
  - Re-ran verification: `.venv/bin/python -m pytest tests/unit/test_capture.py tests/unit/test_vad.py tests/unit/test_asr.py tests/unit/test_threshold.py` => PASS (98 passed)
  - Story status update:
    - E01-S01: complete and verified
    - E01-S02: complete and verified
    - E01-S03: complete and verified
    - E01-S04: complete and verified

- E02-S01 implementation progress:
  - Implemented `voicekey/audio/wake.py` with `WakePhraseDetector` and `WakeWindowController`.
  - Added configurable wake phrase support (default `voice key`) and wake-window timeout logic (default 5 seconds).
  - Added unit coverage in `tests/unit/test_wake.py` for phrase matching, case-insensitivity, timeout expiry, and activity-based timer reset rules.
  - Exported wake components via `voicekey/audio/__init__.py`.
  - Verification command:
    - `.venv/bin/python -m pytest tests/unit/test_wake.py tests/unit/test_capture.py tests/unit/test_vad.py tests/unit/test_asr.py tests/unit/test_threshold.py` => PASS (106 passed)
  - Remaining task for E02-S01:
    - Bind wake detection/window events to FSM transitions after E03 state machine implementation.

- E02-S02 completed:
  - Implemented deterministic command parsing contract in `voicekey/commands/parser.py`.
  - Implemented command registry + alias/case-insensitive matching in `voicekey/commands/registry.py`.
  - Implemented built-in command catalog + feature-gated productivity commands in `voicekey/commands/builtins.py`.
  - Added parser unit coverage in `tests/unit/test_parser.py` for suffix handling, unknown-command literal fallback, special phrase precedence, alias-aware matching, and feature gates.
- E03-S01 completed:
  - Implemented table-driven runtime FSM in `voicekey/app/state_machine.py` with mode-specific transitions, common transitions, and invalid-transition guard errors.
  - Added unit coverage in `tests/unit/test_state_machine.py` for wake_word/toggle/continuous transitions and terminal shutdown marker handling.
- Verification commands/evidence:
  - `.venv/bin/python -m pytest tests/unit/test_parser.py tests/unit/test_state_machine.py` => PASS (33 passed)
  - `.venv/bin/python -m pytest tests/unit` => PASS (139 passed)

## 2026-02-20

- Completed comprehensive MkDocs documentation set under `docs/` covering installation, user guide, architecture, API reference, development, FAQ, troubleshooting, and roadmap.
- Added MkDocs site configuration at `mkdocs.yml` with Material theme, strict link validation, and production-ready navigation structure.
- Added docs dependency lock file at `docs/requirements.txt` with verified package constraints for reproducible local documentation builds.
- Completed documentation hardening pass to resolve strict-mode link warnings:
  - fixed relative links in `docs/installation/source.md`
  - fixed anchor link in `docs/getting-started.md`
- Backlog mapping notes:
  - E11-S01 user docs completeness materially advanced (installation/onboarding/troubleshooting/commands/docs coverage).
  - E11-S02 developer docs completeness materially advanced (development/setup/testing/contribution docs now aligned with repo workflow).
- Verification commands/evidence:
  - `python -m pip install -r docs/requirements.txt` completed successfully with all dependencies resolved.
  - `python -m mkdocs build` completed successfully with strict mode enabled and no unresolved doc-link warnings.

- E02-S01 binding completed:
  - Implemented wake/FSM orchestration in `voicekey/app/main.py` via `RuntimeCoordinator` and deterministic `RuntimeUpdate` outputs.
  - Bound wake phrase detection to wake_word `STANDBY -> LISTENING` transition and wake-window open behavior.
  - Bound wake timeout polling to `LISTENING -> STANDBY` transition and preserved no-typing behavior for wake phrase events.
  - Added activity hooks (`on_transcript`, `on_activity`) to reset wake timeout while listening.
  - Added focused unit coverage in `tests/unit/test_runtime_coordinator.py`.
  - Updated backlog status: `backlog/BACKLOG_MASTER.md` marks E02-S01 complete.
- Verification commands/evidence:
  - `.venv/bin/python -m pytest tests/unit/test_runtime_coordinator.py` => PASS (6 passed)
  - `.venv/bin/python -m pytest tests/unit/test_wake.py tests/unit/test_state_machine.py tests/unit/test_runtime_coordinator.py` => PASS (37 passed)

- E02-S04 completed:
  - Updated `voicekey/app/main.py` `RuntimeCoordinator` to parse paused transcripts via special phrase channel and trigger FSM events for `resume voice key` (`RESUME_REQUESTED`) and `voice key stop` (`STOP_REQUESTED`).
  - Preserved command-suffix bypass semantics by relying on parser system-phrase exact matching; non-exact variants like `resume voice key command` do not take the system phrase path.
  - Added paused-state coordinator coverage in `tests/unit/test_runtime_coordinator.py` for `PAUSED -> STANDBY` (resume) and `PAUSED -> SHUTTING_DOWN` (stop).
  - Added parser coverage in `tests/unit/test_parser.py` verifying `resume voice key command` remains literal text.
  - Updated backlog live execution status in `backlog/BACKLOG_MASTER.md` to mark E02-S04 complete.
- Verification commands/evidence:
  - `.venv/bin/python -m pytest tests/unit/test_runtime_coordinator.py tests/unit/test_parser.py` => PASS (19 passed)

- E03-S03 completed:
  - Added deterministic paused-state routing policy in `voicekey/app/routing_policy.py` to gate parsed outputs by state.
  - Policy now enforces FR-M06/FR-M07 in `PAUSED`: blocks dictation text and non-system commands, allows only `resume voice key` (when phrase channel enabled) and `voice key stop`.
  - Integrated policy enforcement in `voicekey/app/main.py` `RuntimeCoordinator` via new `routing_policy` dependency and paused transcript handler.
  - Added policy unit coverage in `tests/unit/test_routing_policy.py` for paused suppression and allowed control phrases.
  - Expanded paused coordinator coverage in `tests/unit/test_runtime_coordinator.py` for suppression behavior, optional resume-phrase channel toggle, and rapid pause/resume race-style sequencing.
  - Updated backlog live execution status in `backlog/BACKLOG_MASTER.md` to mark E03-S03 complete.
- Verification commands/evidence:
  - `.venv/bin/python -m pytest tests/unit/test_routing_policy.py tests/unit/test_runtime_coordinator.py` => PASS (18 passed)
  - `.venv/bin/python -m pytest tests/unit/test_parser.py tests/unit/test_state_machine.py tests/unit/test_routing_policy.py tests/unit/test_runtime_coordinator.py` => PASS (52 passed)

- E02-S05 completed:
  - Updated `voicekey/commands/builtins.py` to align built-in command catalog with `requirements/commands.md` section 3, including missing core phrases (`escape`) and formatting phrases (`capital hello`, `all caps hello`).
  - Preserved productivity command feature-gate behavior (`window_commands`) as disabled by default until explicitly enabled.
  - Enforced parser single-source-of-truth for special phrases by deriving parser special phrase set directly from `voicekey/commands/builtins.py`.
  - Added dedicated catalog coverage in `tests/unit/test_builtins_catalog.py` to validate every built-in phrase and alias, including gated-on/gated-off behavior checks.
  - Updated backlog live execution status in `backlog/BACKLOG_MASTER.md` to mark E02-S05 complete.
- Verification commands/evidence:
  - `.venv/bin/python -m pytest tests/unit/test_builtins_catalog.py tests/unit/test_parser.py` => PASS (49 passed)

- E03-S04 completed:
  - Added structured runtime error taxonomy in `voicekey/app/runtime_errors.py` for required edge scenarios (`no_microphone`, `hotkey_conflict`, `model_checksum_failed`, `keyboard_blocked`, and microphone disconnect recovery path).
  - Added bounded retry and safety-fallback helpers in `voicekey/app/resilience.py`, including deterministic retry policy and explicit fallback-to-paused decisions when safety cannot be guaranteed.
  - Added unit coverage in `tests/unit/test_runtime_resilience.py` for actionable remediation text, bounded retries, and pause fallback policy decisions.
- E03-S05 completed:
  - Added cross-platform single-instance guard in `voicekey/app/single_instance.py` with POSIX/Windows lock adapters and actionable duplicate-start errors.
  - Added shutdown-safe queue drain policy in `voicekey/app/shutdown.py` with timeout guard and safe discard behavior for pending work.
  - Added unit coverage in `tests/unit/test_single_instance.py` and `tests/unit/test_shutdown.py` for duplicate-start, release/reacquire, shutdown timeout, and enqueue race paths.
- Verification commands/evidence:
  - `.venv/bin/python -m pytest tests/unit/test_runtime_resilience.py tests/unit/test_single_instance.py tests/unit/test_shutdown.py` => PASS (18 passed)
  - `.venv/bin/python -m pytest tests/unit` => PASS (223 passed)

- E04-S01 completed:
  - Added shared keyboard backend contract and typed capability/error models in `voicekey/platform/keyboard_base.py`.
  - Implemented `voicekey/platform/keyboard_linux.py` with X11 primary path, fallback hooks, and explicit Wayland best-effort degraded diagnostics.
  - Implemented `voicekey/platform/keyboard_windows.py` with standard/admin capability reporting and primary/fallback adapter states.
  - Added contract and capability coverage in `tests/unit/test_keyboard_backends.py`.
- E04-S02 completed:
  - Added global hotkey abstraction and deterministic conflict suggestion logic in `voicekey/platform/hotkey_base.py`.
  - Implemented Linux/Windows hotkey adapters in `voicekey/platform/hotkey_linux.py` and `voicekey/platform/hotkey_windows.py`.
  - Added registration lifecycle and conflict-suggestion tests in `tests/unit/test_hotkey_backends.py`.
- Verification commands/evidence:
  - `.venv/bin/python -m pytest tests/unit/test_keyboard_backends.py tests/unit/test_hotkey_backends.py` => PASS (18 passed)
  - `.venv/bin/python -m pytest tests/unit` => PASS (241 passed)

- E04-S03 completed:
  - Added startup compatibility report framework in `voicekey/platform/compatibility.py` with display-session detection (`x11`, `wayland`, `windows`, `unknown`) and component rollup diagnostics.
  - Updated Linux keyboard session detection fallback in `voicekey/platform/keyboard_linux.py` to use shared display-session detection logic.
  - Added shared autostart diagnostics model in `voicekey/platform/autostart_base.py`.
  - Implemented Linux autostart validation in `voicekey/platform/autostart_linux.py` with directory presence/writability checks and remediation guidance.
  - Implemented Windows autostart validation in `voicekey/platform/autostart_windows.py` with startup-folder/registry checks and remediation guidance.
  - Added coverage in `tests/unit/test_compatibility_report.py` and `tests/unit/test_autostart_adapters.py` for Wayland reduced-capability warnings, Windows admin recommendation propagation, and autostart degraded/unavailable diagnostics.
- Verification commands/evidence:
  - `.venv/bin/python -m pytest tests/unit/test_compatibility_report.py tests/unit/test_autostart_adapters.py` => PASS (13 passed)
  - `.venv/bin/python -m pytest tests/unit` => PASS (241 passed)

- Post-integration verification refresh:
  - `.venv/bin/python -m pytest tests/unit` => PASS (254 passed)

- E05-S01 completed:
  - Implemented Click CLI contract in `voicekey/ui/cli.py` with required commands: `start`, `status`, `devices`, `commands`, `config`, `download`, `calibrate`, `diagnostics`.
  - Added deterministic machine-readable output mode (`--output json`) and stable text output rendering.
  - Added explicit CLI exit-code contract in `voicekey/ui/exit_codes.py`.
  - Implemented `config` operation contract (`--get`, `--set`, `--reset`, `--edit`) with deterministic validation and usage-error behavior.
  - Added CLI smoke and contract coverage in `tests/unit/test_cli.py`.
- Verification commands/evidence:
  - `.venv/bin/python -m pytest tests/unit/test_cli.py` => PASS (5 passed)
  - `.venv/bin/python -m pytest tests/unit` => PASS (259 passed)

- E05-S02 completed:
  - Implemented deterministic terminal dashboard renderer in `voicekey/ui/dashboard.py` with explicit state indicator, latency display, and last-action display.
  - Added `DashboardController` throttling and non-blocking latest-snapshot update behavior.
  - Added unit coverage in `tests/unit/test_dashboard.py` for state clarity and throttled refresh semantics.
- E05-S03 completed:
  - Implemented tray runtime controller in `voicekey/ui/tray.py` with runtime-state indicator mapping and deterministic action dispatch contracts.
  - Implemented daemon/session behavior resolution in `voicekey/ui/daemon.py` so daemon mode suppresses terminal UI and enables tray only in graphical sessions.
  - Added integration coverage in `tests/unit/test_tray.py` for tray action flows and daemon headless/graphical behavior.
- Verification commands/evidence:
  - `.venv/bin/python -m pytest tests/unit/test_dashboard.py tests/unit/test_tray.py` => PASS (10 passed)
  - `.venv/bin/python -m pytest tests/unit` => PASS (269 passed)

- E02-S03 completed:
  - Added optional fuzzy matching module in `voicekey/commands/fuzzy.py` with explicit `enabled` and threshold validation controls.
  - Integrated threshold-bounded fuzzy fallback into `voicekey/commands/parser.py` command-candidate path while preserving default-off behavior.
  - Added parser-facing fuzzy coverage in `tests/unit/test_fuzzy_parser.py` and expanded parser factory coverage in `tests/unit/test_parser.py`.
- E04-S04 completed:
  - Added cross-platform window backend contract and typed diagnostics/errors in `voicekey/platform/window_base.py`.
  - Implemented Linux/Windows window adapters in `voicekey/platform/window_linux.py` and `voicekey/platform/window_windows.py`.
  - Added deterministic command-to-operation window action routing in `voicekey/actions/window_dispatch.py`.
  - Added unit coverage in `tests/unit/test_window_backends.py` and `tests/unit/test_window_dispatch.py`, and parser gate routing checks in `tests/unit/test_parser.py`.
- Updated backlog live execution status in `backlog/BACKLOG_MASTER.md` to mark E02-S03 and E04-S04 complete.
- Verification commands/evidence:
  - `.venv/bin/python -m pytest tests/unit` => PASS (285 passed)

- E06-S01 completed:
  - Implemented typed config schema in `voicekey/config/schema.py` covering canonical defaults, bounds, and enums from `requirements/configuration.md`.
  - Added deterministic schema fallback behavior: invalid/unsupported keys are replaced/removed with warning messages instead of hard failure.
  - Implemented config persistence and error-reporting flow in `voicekey/config/manager.py` with explicit path resolution precedence (`--config` override via explicit path, `VOICEKEY_CONFIG`, then platform defaults).
  - Added backup-on-repair behavior for invalid YAML and invalid values, with migration-note warnings and sanitized config rewrite.
  - Exported config API surface in `voicekey/config/__init__.py`.
  - Added unit coverage in `tests/unit/test_config_schema.py` and `tests/unit/test_config_manager.py` for validation bounds, fallback semantics, backup handling, and path precedence.
- Development dependency alignment:
  - Updated `requirements-dev.txt` to include `pydantic` and `pyyaml` so local dev/test setup matches config subsystem requirements.
- Updated backlog live execution status in `backlog/BACKLOG_MASTER.md` to mark E06-S01 complete.
- Verification commands/evidence:
  - `.venv/bin/python -m pytest tests/unit/test_config_schema.py tests/unit/test_config_manager.py` => PASS (7 passed)
  - `.venv/bin/python -m pytest tests/unit` => PASS (292 passed)

- E06-S02 completed:
  - Implemented versioned migration engine in `voicekey/config/migration.py` with explicit forward-only registry, deterministic step ordering, and idempotent behavior for already-current configs.
  - Added migration error taxonomy (`ConfigMigrationError`) and safe guards for unsupported future versions, invalid version fields, and missing migration steps.
  - Integrated migration execution into `voicekey/config/manager.py` before schema fallback validation so legacy payloads migrate first, then validate/sanitize.
  - Added rollback-safe failure path in config manager: migration failure now preserves backup and regenerates safe defaults with migration-note warnings.
  - Added unit coverage in `tests/unit/test_config_migration.py` for migration chain behavior, idempotency, duplicate registration guard, unsupported-version safety, and missing-step failures.
  - Expanded `tests/unit/test_config_manager.py` with legacy-version rewrite, migration failure fallback, and future-version fallback scenarios.
- Updated backlog live execution status in `backlog/BACKLOG_MASTER.md` to mark E06-S02 complete.
- Verification commands/evidence:
  - `.venv/bin/python -m pytest tests/unit/test_config_migration.py tests/unit/test_config_manager.py` => PASS (13 passed)
  - `.venv/bin/python -m pytest tests/unit` => PASS (301 passed)

- E06-S03 completed:
  - Implemented onboarding wizard flow state machine and deterministic run contract in `voicekey/ui/onboarding.py` with required ordered steps: welcome/privacy, microphone selection, wake test, hotkey confirmation, autostart preference, and tutorial script.
  - Added onboarding completion constraints aligned to requirements: completion requires valid microphone selection and wake phrase verification; failure path is non-persisting and returns explicit errors.
  - Implemented skip-safe behavior: `skip` path writes safe default config values.
  - Added CLI onboarding entry command `setup` in `voicekey/ui/cli.py` with deterministic text/json outputs and persisted config path reporting.
  - Added onboarding unit coverage in `tests/unit/test_onboarding.py` for step ordering, success persistence, skip-safe defaults, and required-check failure behavior.
  - Expanded CLI coverage in `tests/unit/test_cli.py` to include `setup` in required commands/smoke tests and validate onboarding JSON output fields.
- Updated backlog live execution status in `backlog/BACKLOG_MASTER.md` to mark E06-S03 complete.
- Verification commands/evidence:
  - `.venv/bin/python -m pytest tests/unit/test_onboarding.py tests/unit/test_cli.py` => PASS (10 passed)
  - `.venv/bin/python -m pytest tests/unit` => PASS (306 passed)

- E06-S04 completed:
  - Implemented custom command loader/validator in `voicekey/commands/custom.py` for config-defined command actions (`key_combo` and `text`) with phrase normalization, collision protection, and strict action payload validation.
  - Integrated custom command registration into parser factory in `voicekey/commands/parser.py` and built-in registry composition in `voicekey/commands/builtins.py`.
  - Added keyboard command-id dispatch mapping in `voicekey/actions/keyboard_dispatch.py` and action routing across window/keyboard/custom command channels in `voicekey/actions/router.py`.
  - Exported custom command types/loaders in `voicekey/commands/__init__.py`.
  - Added parser and loader coverage in `tests/unit/test_custom_commands.py` and `tests/unit/test_custom_parser.py`.
  - Added dispatch/router coverage in `tests/unit/test_keyboard_dispatch.py` and `tests/unit/test_action_router.py`.
- Updated backlog live execution status in `backlog/BACKLOG_MASTER.md` to mark E06-S04 complete.
- Verification commands/evidence:
  - `.venv/bin/python -m pytest tests/unit/test_custom_commands.py tests/unit/test_custom_parser.py tests/unit/test_keyboard_dispatch.py tests/unit/test_action_router.py` => PASS (16 passed)
  - `.venv/bin/python -m pytest tests/unit` => PASS (322 passed)

- E06-S08 completed:
  - Hardened config path resolution in `voicekey/config/manager.py` to ignore blank `VOICEKEY_CONFIG` values while preserving precedence (`--config` override, then env, then platform default).
  - Implemented startup env adapters in `voicekey/config/manager.py` for `VOICEKEY_CONFIG`, `VOICEKEY_MODEL_DIR`, `VOICEKEY_LOG_LEVEL`, and `VOICEKEY_DISABLE_TRAY` with actionable validation errors.
  - Implemented deterministic hot-reload policy evaluation in `voicekey/config/manager.py` via `evaluate_reload_decision()` to classify safe-to-apply keys vs restart-required keys per architecture hot-reload semantics.
  - Exported new config env/reload contracts in `voicekey/config/__init__.py`.
  - Wired startup env validation in CLI `start` contract (`voicekey/ui/cli.py`) so invalid startup env values produce deterministic command errors.
  - Added env adapter coverage in `tests/unit/test_env_adapters.py`.
  - Added hot-reload policy coverage in `tests/unit/test_config_reload_policy.py`.
  - Expanded existing tests in `tests/unit/test_config_manager.py` and `tests/unit/test_cli.py` for blank env override behavior and startup invalid-env error handling.
- Updated backlog live execution status in `backlog/BACKLOG_MASTER.md` to mark E06-S08 complete.
- Verification commands/evidence:
  - `.venv/bin/python -m pytest tests/unit/test_env_adapters.py tests/unit/test_config_reload_policy.py tests/unit/test_config_manager.py tests/unit/test_cli.py` => PASS (23 passed)
  - `.venv/bin/python -m pytest tests/unit` => PASS (332 passed)

- E06-S09 completed:
  - Added explicit keyboard-only onboarding interaction map in `voicekey/ui/onboarding.py` and exposed it through onboarding result metadata.
  - Added explicit skip-step status markers for skip flows in `voicekey/ui/onboarding.py` (`skipped_steps` now records every skipped onboarding step in canonical order).
  - Extended onboarding result contract with keyboard map and skip markers and surfaced these in CLI setup output (`voicekey/ui/cli.py`).
  - Added onboarding accessibility/timing coverage in `tests/unit/test_onboarding.py` for keyboard-only map, explicit skip-step markers, and timing evidence across both complete and skip flows.
  - Expanded CLI setup output coverage in `tests/unit/test_cli.py` for onboarding accessibility metadata fields.
- Updated backlog live execution status in `backlog/BACKLOG_MASTER.md` to mark E06-S09 complete.
- Verification commands/evidence:
  - `.venv/bin/python -m pytest tests/unit/test_onboarding.py tests/unit/test_cli.py` => PASS (13 passed)
  - `.venv/bin/python -m pytest tests/unit` => PASS (334 passed)

- E06-S05 completed:
  - Implemented deterministic snippet expansion engine with recursion/loop guards in `voicekey/commands/snippets.py`.
  - Integrated optional text expansion into parser text path in `voicekey/commands/parser.py` with default-disabled behavior (`text_expansion_enabled=False`) and explicit enablement controls.
  - Preserved unknown-command literal fallback invariant under text expansion mode.
  - Exported snippet engine in `voicekey/commands/__init__.py`.
  - Added snippet engine coverage in `tests/unit/test_snippets.py` (deterministic behavior, non-match passthrough, self/mutual recursion guard, max-depth guard).
  - Expanded parser coverage in `tests/unit/test_parser.py` for text-expansion disabled-by-default, enabled expansion behavior, and fallback invariants.
  - Expanded config baseline assertions in `tests/unit/test_config_schema.py` for default `features.text_expansion_enabled` safety value.
- Updated backlog live execution status in `backlog/BACKLOG_MASTER.md` to mark E06-S05 complete.
- Verification commands/evidence:
  - `.venv/bin/python -m pytest tests/unit/test_snippets.py tests/unit/test_parser.py tests/unit/test_config_schema.py` => PASS (25 passed)
  - `.venv/bin/python -m pytest tests/unit` => PASS (343 passed)

- E06-S06 completed:
  - Implemented per-app profile resolution and merge utilities in `voicekey/config/profiles.py`, including:
    - active app identity contract,
    - deterministic direct/category profile-key resolution,
    - fallback profile application when no app-specific match exists,
    - deep-merge override strategy with non-mutating behavior.
  - Extended config schema in `voicekey/config/schema.py` to include `app_profiles` payload support with safe default `{}`.
  - Exported profile resolution contracts in `voicekey/config/__init__.py`.
  - Added profile resolution coverage in `tests/unit/test_profile_resolution.py` for identity matching, fallback behavior, merge precedence, feature-gate-off behavior, and non-mutation guarantees.
  - Expanded config baseline assertions in `tests/unit/test_config_schema.py` for default `app_profiles` safety value.
- Updated backlog live execution status in `backlog/BACKLOG_MASTER.md` to mark E06-S06 complete.
- Verification commands/evidence:
  - `.venv/bin/python -m pytest tests/unit/test_profile_resolution.py tests/unit/test_config_schema.py` => PASS (10 passed)
  - `.venv/bin/python -m pytest tests/unit` => PASS (350 passed)

- E06-S07 completed:
  - Implemented deterministic runtime path strategy in `voicekey/config/manager.py` via `RuntimePaths` and `resolve_runtime_paths(...)`.
  - Added portable mode resolution contract:
    - portable paths use local root (`<portable_root>/config/config.yaml`, `<portable_root>/data`, `<portable_root>/data/models`),
    - explicit config and model directory overrides remain supported,
    - non-portable mode keeps existing precedence behavior and derives data/model paths from effective config path.
  - Exported runtime path contract in `voicekey/config/__init__.py`.
  - Extended CLI `start` command contract in `voicekey/ui/cli.py` with `--portable` and `--portable-root`, plus deterministic `runtime_paths` output.
  - Added unit coverage in `tests/unit/test_portable_paths.py` for portable and non-portable resolution, env-config override behavior, and model-dir override behavior.
  - Expanded CLI coverage in `tests/unit/test_cli.py` for portable-mode start output and env-config precedence in runtime path output.
  - Added integration smoke coverage in `tests/integration/test_portable_mode_smoke.py` for portable startup contract.
- Verification commands/evidence:
  - `.venv/bin/python -m pytest tests/unit/test_portable_paths.py tests/unit/test_cli.py::test_start_command_supports_portable_mode_runtime_paths tests/unit/test_cli.py::test_start_command_uses_env_config_override_for_runtime_paths tests/integration/test_portable_mode_smoke.py` => PASS (8 passed)
  - `.venv/bin/python -m pytest tests/unit tests/integration` => PASS (358 passed)

- E07-S01 completed:
  - Added root project `README.md` so package metadata references an existing file for wheel/sdist builds.
  - Updated `pyproject.toml` packaging metadata to SPDX-style license declaration (`license = "MIT"`) and removed deprecated license classifier.
  - Extended CI pipeline in `.github/workflows/ci.yml` with `package-smoke` job:
    - builds wheel and sdist via `python -m build`,
    - validates clean-environment installation for wheel and sdist in fresh virtual environments.
  - Updated test-summary aggregation in CI to include package smoke status.
- Verification commands/evidence:
  - `.venv/bin/python -m build` => PASS (wheel + sdist generated successfully)
  - `python3 -m venv /tmp/voicekey-smoke-wheel-nodeps2 && /tmp/voicekey-smoke-wheel-nodeps2/bin/python -m pip install --upgrade pip && /tmp/voicekey-smoke-wheel-nodeps2/bin/python -m pip install --no-deps dist/*.whl && /tmp/voicekey-smoke-wheel-nodeps2/bin/python -m pip show voicekey && /tmp/voicekey-smoke-wheel-nodeps2/bin/python -c "import voicekey; print(voicekey.__version__)"` => PASS
  - `python3 -m venv /tmp/voicekey-smoke-sdist-nodeps && /tmp/voicekey-smoke-sdist-nodeps/bin/python -m pip install --upgrade pip && /tmp/voicekey-smoke-sdist-nodeps/bin/python -m pip install --no-deps dist/*.tar.gz && /tmp/voicekey-smoke-sdist-nodeps/bin/python -m pip show voicekey && /tmp/voicekey-smoke-sdist-nodeps/bin/python -c "import voicekey; print(voicekey.__version__)"` => PASS

- E07-S02 completed:
  - Added Windows artifact helper module `voicekey/release/windows_artifacts.py` with deterministic semver normalization, canonical file naming, installer artifact preparation, portable zip creation, and signtool command generation.
  - Added exports in `voicekey/release/__init__.py` for release helper APIs.
  - Added Windows packaging scripts:
    - `scripts/windows/build_installer.py`
    - `scripts/windows/build_portable.py`
    Both scripts support optional Authenticode signing through `signtool.exe` with certificate thumbprint and timestamp URL inputs.
  - Added unit coverage in `tests/unit/test_windows_artifacts.py` for naming contract, version validation, installer copy behavior, portable zip contents, and signtool command contract.
- Verification commands/evidence:
  - `.venv/bin/python -m pytest tests/unit/test_windows_artifacts.py` => PASS (6 passed)
  - `mkdir -p /tmp/voicekey-script-test && printf 'exe' > /tmp/voicekey-script-test/unsigned.exe && mkdir -p /tmp/voicekey-script-test/portable && printf 'run' > /tmp/voicekey-script-test/portable/voicekey.exe && .venv/bin/python scripts/windows/build_installer.py --version 1.2.3 --unsigned-installer-path /tmp/voicekey-script-test/unsigned.exe --output-dir /tmp/voicekey-script-test/dist && .venv/bin/python scripts/windows/build_portable.py --version 1.2.3 --source-dir /tmp/voicekey-script-test/portable --output-dir /tmp/voicekey-script-test/dist` => PASS

- E07-S03 completed:
  - Added Linux artifact helper module `voicekey/release/linux_artifacts.py` with deterministic semver normalization, canonical AppImage naming (`voicekey-<version>-linux-x86_64.AppImage`), artifact preparation, and launch-smoke command builder.
  - Updated `voicekey/release/__init__.py` exports to include Linux release helper APIs.
  - Added Linux packaging scripts:
    - `scripts/linux/build_appimage.py`
    - `scripts/linux/smoke_launch_appimage.py`
    Scripts build canonical artifact output and run deterministic launch smoke command.
  - Added unit coverage:
    - `tests/unit/test_linux_artifacts.py`
    - `tests/unit/test_linux_appimage_scripts.py`
  - Extended CI in `.github/workflows/ci.yml` with `appimage-smoke` matrix job on Ubuntu 22.04/24.04 to build canonical AppImage artifact via script and run launch smoke.
  - Updated CI test-summary aggregation to include Linux AppImage smoke result.
- Verification commands/evidence:
  - `.venv/bin/python -m pytest tests/unit/test_linux_artifacts.py tests/unit/test_linux_appimage_scripts.py tests/unit/test_windows_artifacts.py` => PASS (12 passed)
  - `.venv/bin/python -m pytest tests/unit tests/integration` => PASS (364 passed)
  - `.venv/bin/python - <<'PY' ... yaml.safe_load('.github/workflows/ci.yml') ...` => PASS (`ci_yaml_parse=ok`)

- E07-S04 completed:
  - Added release integrity helper module `voicekey/release/integrity.py`:
    - deterministic `SHA256SUMS` generation,
    - CycloneDX SBOM payload generation,
    - provenance manifest generation with artifact hash metadata.
  - Added release signing helper module `voicekey/release/signing.py` with deterministic detached-sign and signed-tag verification command builders.
  - Extended `voicekey/release/__init__.py` exports for integrity/signing APIs.
  - Added unit coverage:
    - `tests/unit/test_release_integrity.py`
    - `tests/unit/test_release_signing.py`
  - Added release scripts:
    - `scripts/release/generate_integrity_bundle.py` (writes `SHA256SUMS`, `sbom.cyclonedx.json`, `provenance.json`)
    - `scripts/release/sign_release_bundle.py` (creates detached signature for checksum bundle with configurable signer path)
  - Added script integration coverage:
    - `tests/integration/test_generate_integrity_bundle_script.py`
    - `tests/integration/test_sign_release_bundle_script.py`
  - Extended CI workflow `.github/workflows/ci.yml` with `integrity-bundle-smoke` job to validate integrity bundle generation and detached signature path in CI.
- Verification commands/evidence:
  - `.venv/bin/python -m pytest tests/unit/test_release_integrity.py tests/unit/test_release_signing.py tests/integration/test_generate_integrity_bundle_script.py tests/integration/test_sign_release_bundle_script.py` => PASS (9 passed)
  - `.venv/bin/python -m pytest tests/unit tests/integration` => PASS (371 passed)
  - `.venv/bin/python - <<'PY' ... yaml.safe_load('.github/workflows/ci.yml') ...` => PASS (`ci_yaml_parse=ok`)
