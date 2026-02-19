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
| FR-S04 | E05-S03, E04-S03 | autostart platform tests |
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
| FR-D04 | E07-S04 | checksum verification tests |
| FR-D05 | E07-S05 | model externalization and download tests |
| FR-D06 | E06-S07 | portable artifact validation |
| FR-D07 | E07-S04 | signing validation checks |
| FR-D08 | E07-S04 | SBOM presence and format checks |
| FR-D09 | E07-S04 | provenance metadata checks |
| FR-CI01 | E08-S01 | CI workflow required checks |
| FR-CI02 | E08-S01 | Linux/Windows matrix enforcement |
| FR-CI03 | E08-S01 | vulnerability scan gates |
| FR-CI04 | E08-S01 | performance guardrail job |
| FR-CI05 | E08-S02 | tag-trigger workflow tests |
| FR-CI06 | E08-S02 | isolated build environment checks |
| FR-CI07 | E08-S02 | release note generation tests |
| FR-CI08 | E08-S03, E10-S04 | post-publish smoke matrix |
| FR-CI09 | E08-S03 | rollback/yank runbook tests |
| FR-CI10 | E08-S02 | OIDC trusted publishing checks |
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
| Performance targets (wake, ASR, parse, p50/p95) | E10-S03 | benchmark reports |
| Resource budgets (CPU/memory/disk) | E10-S03 | profiling reports |
| Reliability bullets (single-instance, reconnect, crash-safe shutdown, bounded retries) | E03-S04, E10-S05 | resilience tests |
| Privacy bullets (offline runtime, no telemetry, no raw audio persistence, no transcript logs by default) | E09-S01 | privacy regression tests |
| Usability targets (first setup <=5 min, first sentence <=2 min) | E06-S03, E10-S02 | onboarding timing tests |
| Linux support target (Ubuntu 22.04/24.04 x64, X11 full, Wayland best-effort) | E04-S03, E10-S04 | compatibility matrix |
| Windows support target (10/11 x64, standard/admin behavior) | E04-S03, E10-S04 | compatibility matrix |
| Error and edge scenarios table (no mic, disconnect, unknown command, hotkey conflict, checksum fail, keyboard block) | E03-S04, E04-S02, E07-S05 | integration/error-path tests |
| Acceptance criteria section 9 | E10-S01..E10-S05 | release gate checks |
| Required implementation artifacts in sections 11 and 15 | E11-S01..E11-S03 | documentation audit gate |

---

## C. Coverage Gate Rule

Release candidate is blocked if any row in section A or B lacks:

1. backlog story mapping,
2. passing verification evidence,
3. updated documentation pointers.
