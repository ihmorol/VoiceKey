# VoiceKey Testing Strategy

> Version: 1.0
> Date: 2026-02-19

---

## 1. Test Layers

### Unit

- command parser behavior
- state transitions
- config migration and validation

### Integration

- mic -> VAD -> ASR -> parser -> keyboard route
- tray state synchronization
- autostart adapters

### Platform

- Linux X11 matrix
- Linux Wayland best-effort matrix
- Windows standard/admin matrix

Minimum CI matrix requirement:

- Ubuntu 22.04 LTS x64 and Ubuntu 24.04 LTS x64 (X11 session tests where possible)
- Windows 10 x64 and Windows 11 x64
- Python 3.11 and 3.12

### Performance

- latency percentiles
- CPU and memory under sustained dictation

---

## 2. Acceptance Benchmarks

- p50 speech-to-type <= 200ms
- p95 speech-to-type <= 350ms
- idle CPU <= 5%
- active CPU <= 35%

---

## 3. Reliability Scenarios

- microphone disconnect/reconnect
- rapid mode switching
- repeated hotkey registration changes
- model reload failure and recovery

---

## 4. Safety Scenarios

- unknown command fallback to literal text
- inactivity auto-pause trigger
- pause phrase immediate output suppression
- paused-state `resume voice key` phrase path (when enabled) and hotkey path

---

## 5. Distribution Verification Scenarios

- pip install smoke from published PyPI package
- Windows installer install/start/tray smoke
- Windows portable zip launch smoke
- Linux AppImage launch/tray smoke
- checksum/signature validation flow

---

*Document Version: 1.0*  
*Last Updated: 2026-02-19*
