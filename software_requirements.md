# Software Requirements Specification - VoiceKey
## Real-time Offline-first Voice-to-Keyboard for Linux and Windows

> Project: VoiceKey  
> Version: 3.2 (Aligned and Expanded)  
> Platforms: Linux and Windows (Primary), macOS (Out of Scope)  
> Last Updated: 2026-02-26

---

## 1. Overview

VoiceKey is a privacy-first, offline-first voice keyboard that captures microphone audio, recognizes speech in real time, and emits keyboard input into the currently focused window.

This specification incorporates all prior analysis findings and decisions:

- ASR engine: faster-whisper (primary)
- Optional internet transcription fallback: explicit opt-in only (disabled by default)
- Pause/resume phrases: `pause voice key`, `resume voice key` (no wake word required)
- Listening modes: `wake_word` (default), `toggle`, `continuous`
- Inactivity safety: auto-pause/auto-standby timers to reduce accidental typing

---

## 2. Product Goals

1. Make dictation feel instant for everyday laptop users.
2. Keep audio/text local and private by default.
3. Be easy for non-technical users to install, start, and trust.
4. Work reliably in Linux and Windows desktop workflows.
5. Remain free and open for community contribution.

---

## 3. Scope

### 3.1 In Scope (Core)

- Offline voice-to-text typing in any focused app.
- Wake-word activation via phrase `voice key`.
- Command execution via `... command` suffix and special system phrases.
- System tray background mode and auto-start integration.
- First-run onboarding wizard.
- Configurable safety timers and hotkeys.
- Optional cloud transcription fallback when explicitly enabled by the user.

### 3.2 Out of Scope (v3 Core)

- macOS support.
- Mobile companion app.

---

## 4. Functional Requirements

### 4.1 Audio and Recognition Pipeline

| ID | Requirement | Priority |
|----|-------------|----------|
| FR-A01 | Capture mono microphone audio at 16kHz with low-latency callback streaming | P0 |
| FR-A02 | Apply VAD before full recognition to reduce false triggers and CPU usage | P0 |
| FR-A03 | Use faster-whisper as primary ASR backend for streaming recognition | P0 |
| FR-A04 | Emit partial and final transcript events | P0 |
| FR-A05 | Apply configurable confidence threshold before typing | P0 |
| FR-A06 | Support runtime model profile selection (`tiny`, `base`, `small`) | P1 |
| FR-A07 | Support optional cloud ASR fallback with explicit user opt-in and provider config; default remains local-only | P1 |

### 4.2 Wake Word and Activation

| ID | Requirement | Priority |
|----|-------------|----------|
| FR-W01 | Wake phrase defaults to `voice key` and is configurable | P0 |
| FR-W02 | Wake detection must not type text directly; it only opens listening window | P0 |
| FR-W03 | Wake-word listening window auto-expires after configurable silence timeout (default 5s) | P0 |
| FR-W04 | False wake mitigation via sensitivity threshold and VAD gating | P0 |

### 4.3 Command Parsing Rules

| ID | Requirement | Priority |
|----|-------------|----------|
| FR-C01 | A phrase ending with `command` is treated as command candidate | P0 |
| FR-C02 | If candidate command is unknown, type full literal text (including `command`) | P0 |
| FR-C03 | Matching is case-insensitive and alias-aware | P0 |
| FR-C04 | Optional fuzzy matching can be enabled (default off for safety) | P1 |
| FR-C05 | `pause voice key` and `resume voice key` are special phrases and work without wake word | P0 |

### 4.4 Built-in Commands

#### Core Editing

- `new line command`, `enter command`
- `tab command`, `space command`
- `backspace command`, `delete command`
- `left command`, `right command`, `up command`, `down command`
- `control c command`, `control v command`, `control x command`, `control z command`, `control a command`, `control l command`
- `scratch that command`

#### Safety/System

- `pause voice key`
- `resume voice key`
- `voice key stop`

#### Added Productivity Commands (from recommendations)

- Window actions: `maximize window command`, `minimize window command`, `close window command`, `switch window command`
- Clipboard aliases: `copy that command`, `paste that command`, `cut that command`

Note: productivity window command group is feature-gated and disabled by default until P1 is delivered.

### 4.5 Listening Modes and Inactivity Safety

| ID | Requirement | Priority |
|----|-------------|----------|
| FR-M01 | `wake_word` mode is default and recommended | P0 |
| FR-M02 | `toggle` mode is supported via global hotkey | P0 |
| FR-M03 | `continuous` mode is supported and clearly marked as higher risk | P1 |
| FR-M04 | In `toggle` and `continuous` modes, inactivity auto-pause is enabled by default | P0 |
| FR-M05 | Default inactivity auto-pause timeout is 30s (configurable) | P0 |
| FR-M06 | In paused state, dictation and command execution are disabled | P0 |
| FR-M07 | Paused state must keep only resume control channels active (`resume voice key` detector and configured hotkey, phrase channel enabled by default) | P0 |

### 4.6 System Integration

| ID | Requirement | Priority |
|----|-------------|----------|
| FR-S01 | Run as tray-enabled background app (no terminal required after startup) | P0 |
| FR-S02 | Tray icon state must reflect standby/listening/paused/error | P0 |
| FR-S03 | Tray menu must provide start, pause/resume, open dashboard, settings, exit | P0 |
| FR-S04 | Auto-start at login supported on Linux and Windows | P0 |
| FR-S05 | Start-minimized-to-tray option supported | P0 |

### 4.7 First-run Experience

| ID | Requirement | Priority |
|----|-------------|----------|
| FR-O01 | Guided first-run wizard for microphone selection and test | P0 |
| FR-O02 | Wake-word test step included | P0 |
| FR-O03 | Hotkey setup step included | P0 |
| FR-O04 | Auto-start preference step included | P0 |
| FR-O05 | Quick command tutorial included | P0 |

### 4.8 Configuration and Extensibility

| ID | Requirement | Priority |
|----|-------------|----------|
| FR-G01 | YAML config with schema validation and migration support | P0 |
| FR-G02 | CLI config set/get/reset/edit commands | P0 |
| FR-G03 | Custom command registration in config | P0 |
| FR-G04 | Text expansion snippets (user-defined) | P1 |
| FR-G05 | Per-application profiles (editor/terminal/browser) | P1 |
| FR-G06 | Portable mode with local config/data directory | P1 |

---

## 5. Non-Functional Requirements

### 5.1 Performance

| Metric | Target | Acceptable |
|--------|--------|------------|
| Wake detect latency | <= 100ms | <= 150ms |
| ASR processing (chunk) | <= 150ms | <= 220ms |
| Command parse/dispatch | <= 10ms | <= 20ms |
| End-to-end speech-to-type | <= 200ms p50 | <= 350ms p95 |

### 5.2 Resource Budget

| Metric | Target |
|--------|--------|
| Idle CPU | <= 5% |
| Active CPU | <= 35% |
| Memory | <= 300MB (model-dependent) |
| Disk (core models + app) | <= 2.5GB |

### 5.3 Reliability

- Single-instance process lock.
- Auto-reconnect on microphone disruption.
- Crash-safe shutdown and queue drain.
- Bounded retries with user-visible remediation guidance.

### 5.4 Privacy and Security

- Offline local transcription by default after model download.
- Optional runtime cloud transmission only when user explicitly enables cloud ASR fallback.
- No telemetry by default.
- No raw audio persistence.
- No transcript logging by default.

### 5.5 Usability

- First-time setup <= 5 minutes.
- Time to first successful typed sentence <= 2 minutes.
- Clear visual listening indicators in tray and dashboard.

---

## 6. Technology Decisions

### 6.1 Required Stack

| Layer | Technology |
|-------|------------|
| ASR | faster-whisper (CTranslate2, default) + optional cloud ASR fallback adapter |
| Audio Capture | sounddevice (PortAudio) |
| VAD | Silero VAD or equivalent local VAD |
| Keyboard Injection | pynput primary, platform fallback adapters |
| Linux low-level fallback | evdev/uinput |
| Windows low-level fallback | pywin32 SendInput path |
| CLI | Click |
| Terminal UX | Rich |
| Tray | pystray |
| Config validation | Pydantic + YAML |

### 6.2 FFmpeg Position

- FFmpeg is optional for file-based diagnostics/transcoding.
- FFmpeg is not required for real-time microphone pipeline.

---

## 7. Platform Requirements

### 7.1 Linux

- Supported release targets: Ubuntu 22.04 LTS x64 and Ubuntu 24.04 LTS x64.
- X11: full support target.
- Wayland: best-effort support with explicit warnings.
- If low-level input requires privileges, provide guided setup.

### 7.2 Windows

- Supported release targets: Windows 10 x64 and Windows 11 x64.
- Standard user mode supported for common applications.
- Admin mode recommended for maximal compatibility.

---

## 8. Error and Edge Handling

| Scenario | Expected Handling |
|----------|-------------------|
| No microphone | actionable error + device listing command |
| Device removed mid-session | auto-retry with backoff then pause |
| Unknown command phrase | type literal text |
| Hotkey conflict | detect and suggest alternatives |
| Model checksum failure | fail safe and force re-download |
| Keyboard block | show clear permissions guidance |

---

## 9. Acceptance Criteria

### 9.1 Core Acceptance

- Wake phrase `voice key` reliably opens listening window.
- `pause voice key` and `resume voice key` work without wake phrase.
- Unknown `... command` phrases type literally, not silently dropped.
- Inactivity in toggle/continuous mode auto-pauses at configured timeout.
- Tray mode and auto-start work on Linux and Windows.

### 9.2 Performance Acceptance

- Meets latency and resource targets in Section 5 on representative laptops.
- No perceptible UI freeze during long dictation sessions.

### 9.3 Reliability Acceptance

- Survives microphone disconnect/reconnect without process crash.
- Handles repeated mode toggles and hotkey changes without deadlock.

### 9.4 Distribution and Governance Acceptance

- Release artifacts are signed and checksummed.
- SBOM and provenance are attached to each public release.
- PyPI release path uses OIDC trusted publishing.
- Repository includes MIT license and DCO-based contribution policy.

---

## 10. Roadmap

### P0 (Must for world-class baseline)

- faster-whisper migration
- tray/background mode
- auto-start integration
- first-run wizard
- inactivity auto-pause safety
- installation and troubleshooting docs

### P1 (High impact)

- text expansion
- per-app profiles
- window management command set
- portable mode

### P2 (Expansion)

- plugin SDK
- broader multi-language packs
- advanced automation command plugins

---

## 11. Implementation Artifacts Required

- `architecture.md` (updated and aligned)
- `requirements/installation.md`
- `requirements/onboarding.md`
- `requirements/troubleshooting.md`
- `requirements/development.md`
- `requirements/security.md`
- `requirements/testing-strategy.md`

---

## 12. Distribution and Packaging Requirements

### 12.1 Supported Distribution Channels

| ID | Requirement | Priority |
|----|-------------|----------|
| FR-D01 | Publish Python package to PyPI (`pip install voicekey`) | P0 |
| FR-D02 | Publish Windows signed installer and portable zip | P0 |
| FR-D03 | Publish Linux AppImage and pip package | P0 |
| FR-D04 | Provide SHA-256 checksums for all release artifacts | P0 |
| FR-D05 | Keep model download external to installer to avoid oversized binaries | P0 |
| FR-D06 | Provide offline-friendly portable mode artifact | P1 |

### 12.2 Release Integrity

| ID | Requirement | Priority |
|----|-------------|----------|
| FR-D07 | Sign release artifacts (code signing on Windows, signed tags/releases) | P0 |
| FR-D08 | Generate SBOM for each release artifact | P0 |
| FR-D09 | Produce reproducible build metadata (commit hash, build date, toolchain) | P1 |

---

## 13. DevOps and CI/CD Requirements

### 13.1 Pull Request Pipeline

| ID | Requirement | Priority |
|----|-------------|----------|
| FR-CI01 | PR checks must run lint, unit tests, and integration smoke tests | P0 |
| FR-CI02 | PR checks must run Linux and Windows matrix jobs | P0 |
| FR-CI03 | PR checks must run dependency vulnerability scan | P0 |
| FR-CI04 | Performance guardrail checks for parser and ASR hot path | P1 |

### 13.2 Release Pipeline

| ID | Requirement | Priority |
|----|-------------|----------|
| FR-CI05 | Release workflow triggered by version tag only | P0 |
| FR-CI06 | Build artifacts in clean, isolated CI environments | P0 |
| FR-CI07 | Publish release notes from changelog and commit metadata | P0 |
| FR-CI08 | Run post-publish install smoke tests on target platforms | P0 |
| FR-CI09 | Automatic rollback guidance if smoke tests fail | P1 |
| FR-CI10 | PyPI publishing must use trusted publishing (OIDC), not long-lived API tokens | P0 |

---

## 14. Open-source Governance Requirements

| ID | Requirement | Priority |
|----|-------------|----------|
| FR-OSS01 | Repository includes LICENSE (MIT) | P0 |
| FR-OSS02 | Repository includes CONTRIBUTING guide and code of conduct | P0 |
| FR-OSS03 | Repository includes issue and PR templates | P0 |
| FR-OSS04 | Semantic versioning policy and changelog process defined | P0 |
| FR-OSS05 | Public compatibility matrix maintained per release | P1 |
| FR-OSS06 | Security disclosure policy and contact method documented | P1 |
| FR-OSS07 | Contribution legal model is DCO sign-off required, CLA not required | P0 |

---

## 15. Additional Implementation Artifacts Required

- `requirements/distribution.md`
- `requirements/devops-cicd.md`
- `requirements/open-source-governance.md`
- `requirements/release-checklist.md`

---

*Document Version: 3.1*  
*Last Updated: 2026-02-19*
