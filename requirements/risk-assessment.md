# VoiceKey Risk Assessment and Mitigation Plan

> Version: 2.0 (Aligned)
> Date: 2026-02-19

---

## 1. Top Risks

| ID | Risk | Impact | Likelihood | Priority |
|----|------|--------|------------|----------|
| R-01 | User feels lag during dictation | High | Medium | P0 |
| R-02 | Accidental typing in wrong context | High | Medium | P0 |
| R-03 | Keyboard injection blocked by platform/app | High | Medium | P0 |
| R-04 | Tray/autostart behavior inconsistent by OS | Medium | Medium | P0 |
| R-05 | Wake false triggers in noisy environments | Medium | Medium | P1 |
| R-06 | Wayland feature limitations | Medium | High | P1 |
| R-07 | Config drift and migration errors | Medium | Low | P1 |

---

## 2. Mitigation Strategy

### 2.1 Latency (R-01)

- faster-whisper with tuned model profile (`base/int8` default)
- VAD gating to reduce unnecessary ASR workload
- bounded chunk sizes (80-200ms)
- hot-path queue optimization and model warm-up

Acceptance:

- p50 speech-to-type <= 200ms
- p95 speech-to-type <= 350ms

### 2.2 Accidental Typing (R-02)

- wake_word mode default
- inactivity auto-pause in toggle/continuous modes (default 30s)
- explicit visual state in tray and dashboard
- hard pause mode disables all typing output

### 2.3 Injection Reliability (R-03)

- platform backend abstraction with fallbacks
- startup self-test for key injection
- actionable remediation for permissions/admin mode

### 2.4 Tray and Autostart Reliability (R-04)

- separate platform adapters (Windows Run key, Linux desktop entry/systemd-user)
- startup diagnostics and clear status events
- uninstall cleanup for autostart artifacts

### 2.5 False Wake (R-05)

- configurable wake sensitivity
- VAD pre-filtering
- optional stricter wake confirmation mode for noisy setups

### 2.6 Wayland Constraints (R-06)

- detect Wayland and warn clearly
- document reduced capability matrix
- keep full support promise scoped to Linux X11 + Windows

### 2.7 Config Migration Safety (R-07)

- versioned config schema
- backup-before-migrate
- safe defaults on parse/validation failures

---

## 3. Operational Playbooks

### 3.1 Microphone Disconnect

1. transition to paused
2. retry reconnect (1s, 2s, 4s)
3. if still failing, show recovery prompt

### 3.2 Model Load Failure

1. block start of recognition
2. verify checksum
3. trigger controlled re-download path

### 3.3 Hotkey Conflict

1. detect registration failure
2. suggest next available hotkeys
3. persist updated hotkey on user confirmation

---

## 4. Monitoring Signals

- end-to-end latency p50/p95
- wake false-positive count
- ASR decode failure count
- injection failure count
- reconnect attempts

All metrics remain local unless users explicitly export debug reports.

---

*Document Version: 2.0*  
*Last Updated: 2026-02-19*
