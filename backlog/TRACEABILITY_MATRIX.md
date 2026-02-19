# VoiceKey Requirement Traceability Matrix

This matrix provides 100% requirement coverage from specification to backlog and verification.

---

## A. Canonical FR Coverage (FR-*)

| Requirement | Backlog Story Coverage | Verification Method |
|-------------|------------------------|---------------------|
| FR-A01 | E01-S01 | audio capture integration tests |
| FR-A02 | E01-S02 | VAD unit + integration tests |
| FR-A03 | E01-S03 | ASR adapter tests |
| FR-A04 | E01-S03 | transcript event contract tests |
| FR-A05 | E01-S04 | threshold behavior tests |
| FR-A06 | E01-S03 | model profile switch tests |
| FR-W01 | E02-S01 | wake phrase config tests |
| FR-W02 | E02-S01 | wake-no-type safety tests |
| FR-W03 | E02-S01, E03-S02 | wake timeout timer tests |
| FR-W04 | E01-S02, E02-S01 | false-trigger mitigation tests |
| FR-C01 | E02-S02 | parser suffix detection tests |
| FR-C02 | E02-S02 | unknown-command literal fallback tests |
| FR-C03 | E02-S02 | alias/case-insensitive matching tests |
| FR-C04 | E02-S03 | fuzzy on/off guardrail tests |
| FR-C05 | E02-S04, E03-S03 | special phrase control-plane tests |
| FR-M01 | E03-S01 | mode default transition tests |
| FR-M02 | E03-S01, E04-S02 | toggle hotkey tests |
| FR-M03 | E03-S01, E03-S02 | continuous-mode warning/behavior tests |
| FR-M04 | E03-S02 | inactivity auto-pause tests |
| FR-M05 | E03-S02 | timer default/config tests |
| FR-M06 | E03-S03 | paused output suppression tests |
| FR-M07 | E03-S03 | paused resume channel tests |
| FR-S01 | E05-S03 | tray-daemon startup tests |
| FR-S02 | E05-S02, E05-S03 | indicator state mapping tests |
| FR-S03 | E05-S03 | tray action integration tests |
| FR-S04 | E04-S03 | autostart platform tests |
| FR-S05 | E05-S03 | start-minimized tests |
| FR-O01 | E06-S03 | onboarding e2e step validation |
| FR-O02 | E06-S03 | wake test step checks |
| FR-O03 | E06-S03 | hotkey step checks |
| FR-O04 | E06-S03 | autostart preference persistence checks |
| FR-O05 | E06-S03 | tutorial completion checks |
| FR-G01 | E06-S01, E06-S02 | schema + migration tests |
| FR-G02 | E05-S01 | CLI config contract tests |
| FR-G03 | E06-S04 | custom command loader tests |
| FR-G04 | E06-S05 | snippet expansion tests |
| FR-G05 | E06-S06 | per-app profile resolution tests |
| FR-G06 | E06-S07 | portable-mode smoke tests |
| FR-D01 | E07-S01 | PyPI install smoke |
| FR-D02 | E07-S02 | installer/portable smoke |
| FR-D03 | E07-S03 | AppImage + pip smoke |
| FR-D04 | E07-S04 | release integrity helper + generation script tests (`test_release_integrity.py`, `test_generate_integrity_bundle_script.py`) |
| FR-D05 | E07-S05 | model catalog/checksum/downloader tests (`test_model_catalog.py`, `test_model_checksum.py`, `test_model_downloader.py`) |
| FR-D06 | E06-S07 | portable artifact validation |
| FR-D07 | E07-S04 | detached-sign command + signing script smoke (`test_release_signing.py`, `test_sign_release_bundle_script.py`) |
| FR-D08 | E07-S04 | CycloneDX SBOM structure checks (`test_release_integrity.py`) |
| FR-D09 | E07-S04 | provenance metadata content checks (`test_release_integrity.py`) |
| FR-CI01 | E08-S01 | CI workflow required checks (`.github/workflows/ci.yml`) + integration guardrail script coverage (`test_check_perf_guardrails_script.py`) |
| FR-CI02 | E08-S01 | full Linux/Windows Python matrix execution in unit/integration jobs (`.github/workflows/ci.yml`) |
| FR-CI03 | E08-S01 | strict dependency vulnerability scan gate (`pip-audit -r requirements-dev.txt` in `.github/workflows/ci.yml`) |
| FR-CI04 | E08-S01 | performance guardrail job + enforcement toggle (`scripts/ci/check_perf_guardrails.py`, `test_check_perf_guardrails_script.py`) |
| FR-CI05 | E08-S02 | semantic tag trigger + signed-tag verification in release workflow (`.github/workflows/release.yml`) |
| FR-CI06 | E08-S02 | isolated tag build job in release workflow (`.github/workflows/release.yml`) |
| FR-CI07 | E08-S02 | changelog metadata release-note generation (`scripts/release/generate_release_notes.py`, `test_generate_release_notes_script.py`) |
| FR-CI08 | E08-S03, E10-S04 | post-publish smoke matrix |
| FR-CI09 | E08-S03 | rollback/yank runbook tests |
| FR-CI10 | E08-S02 | PyPI trusted publishing via OIDC (`pypa/gh-action-pypi-publish` in `.github/workflows/release.yml`) |
| FR-OSS01 | E00-S01 | repository policy audit |
| FR-OSS02 | E00-S01 | governance file audit |
| FR-OSS03 | E00-S01 | template presence check |
| FR-OSS04 | E00-S02 | semver/changelog policy check |
| FR-OSS05 | E11-S02 | compatibility matrix update check |
| FR-OSS06 | E00-S03 | security policy SLA check |
| FR-OSS07 | E00-S01 | DCO workflow check |

---

## B. Non-ID Requirement Coverage

| Source Requirement (No explicit FR ID) | Backlog Coverage | Verification |
|----------------------------------------|------------------|--------------|
| Built-in command sets in section 4.4 | E02-S05, E04-S04 | command registry and parser tests |
| Productivity commands feature-gated until P1 | E02-S05, E04-S04, E06-S05 | default-config + feature-flag tests |
| Config path defaults and override channels (`--config`, `VOICEKEY_CONFIG`) | E06-S08 | config resolution precedence tests |
| Environment variable runtime controls (`VOICEKEY_MODEL_DIR`, `VOICEKEY_LOG_LEVEL`, `VOICEKEY_DISABLE_TRAY`) | E06-S08 | startup env parsing tests |
| Hot reload semantics (safe-to-reload vs restart-required keys) | E06-S08 | reload contract tests |
| Onboarding accessibility and keyboard-only operation | E06-S09 | onboarding accessibility e2e tests |
| Onboarding skip flow writes safe defaults | E06-S09 | skip-path config safety tests |
| Performance targets (wake, ASR, parse, p50/p95) | E10-S03 | benchmark reports |
| Resource budgets (CPU/memory/disk) | E10-S03 | profiling reports |
| Reliability bullets (single-instance, reconnect, crash-safe shutdown, bounded retries) | E03-S04, E03-S05, E10-S05 | resilience tests |
| Privacy bullets (offline runtime, no telemetry, no raw audio persistence, no transcript logs by default) | E09-S01, E09-S03 | privacy regression tests |
| Usability targets (first setup <=5 min, first sentence <=2 min) | E06-S03, E10-S02 | onboarding timing tests |
| Linux support target (Ubuntu 22.04/24.04 x64, X11 full, Wayland best-effort) | E04-S03, E10-S04 | compatibility matrix |
| Windows support target (10/11 x64, standard/admin behavior) | E04-S03, E10-S04 | compatibility matrix |
| Distribution policy (x64 public scope, artifact naming convention, one-major migration path) | E07-S06 | release policy validator unit/integration checks (`test_release_policy.py`, `test_validate_distribution_policy_script.py`) |
| CI hardening controls (secret scan, license scan, branch protection, CODEOWNERS, pinned actions, least-privilege permissions, CI observability) | E08-S04 | CI governance checks |
| Error and edge scenarios table (no mic, disconnect, unknown command, hotkey conflict, checksum fail, keyboard block) | E03-S04, E04-S02, E07-S05 | integration/error-path tests |
| Test matrix governance (Ubuntu/Windows + Python version matrix coverage) | E10-S06 | matrix coverage reports |
| P2 ecosystem roadmap (plugin SDK, language packs, advanced automation plugins) | E12-S01..E12-S03 | roadmap feature test suites |
| Acceptance criteria section 9 | E10-S01..E10-S06 | release gate checks |
| Required implementation artifacts in sections 11 and 15 | E11-S01..E11-S03 | documentation audit gate |

---

## C. Coverage Gate Rule

Release candidate is blocked if any row in section A or B lacks:

1. backlog story mapping,
2. passing verification evidence,
3. updated documentation pointers.
