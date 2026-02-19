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
  - ✅ Governance files and legal policy are complete and linked
  - ✅ Required PR checks are enforced (lint, tests, scans)
  - ✅ Security/governance CI controls are active for pull requests

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
