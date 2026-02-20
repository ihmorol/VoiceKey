# VoiceKey Compatibility Matrix

> Version: 1.0
> Date: 2026-02-20
> Last Updated: 2026-02-20

---

## Overview

This document describes the officially supported platforms, Python versions, and known limitations for VoiceKey. Compatibility is verified per release through automated CI testing.

---

## 1. Supported Operating Systems

| Platform | Version | Architecture | Status | Notes |
|----------|---------|--------------|--------|-------|
| **Ubuntu** | 22.04 LTS | x64 | ✅ Fully Supported | Primary Linux target |
| **Ubuntu** | 24.04 LTS | x64 | ✅ Fully Supported | Primary Linux target |
| **Windows** | 10 | x64 | ✅ Fully Supported | Primary Windows target |
| **Windows** | 11 | x64 | ✅ Fully Supported | Primary Windows target |

### Out of Scope

- macOS (not currently supported)
- 32-bit architectures (x86, ARM32)
- ARM64 architectures (planned for future release)
- Linux distributions other than Ubuntu LTS

---

## 2. Supported Python Versions

| Python Version | Status | Notes |
|----------------|--------|-------|
| **3.11** | ✅ Supported | Primary target |
| **3.12** | ✅ Supported | Secondary target |
| 3.10 | ❌ Not Supported | Minimum required: 3.11 |
| 3.13 | ⚠️ Best Effort | Not yet in CI matrix |

---

## 3. Linux Platform Notes

### 3.1 Display Servers

| Display Server | Status | Notes |
|----------------|--------|-------|
| **X11** | ✅ Full Support | Primary display server target |
| **Wayland** | ⚠️ Best Effort | Reduced functionality, explicit user warning |

#### Wayland Limitations

On Wayland sessions:
- Global hotkey registration may require additional permissions
- Keyboard injection may require XWayland fallback
- User receives explicit warning at startup about best-effort support

### 3.2 Audio Requirements

- **PortAudio** is required for microphone capture
- Install with: `sudo apt install libportaudio2 portaudio19-dev`

### 3.3 Input/Permissions

| Feature | Requirement |
|---------|-------------|
| Keyboard injection | User must be in `input` group for uinput |
| Global hotkeys | X11: full support; Wayland: limited |
| Autostart | Desktop entry in `~/.config/autostart/` |

### 3.4 Ubuntu-Specific Setup

```bash
# Install system dependencies
sudo apt update
sudo apt install -y libportaudio2 portaudio19-dev python3.11-venv

# Add user to input group (for keyboard injection)
sudo usermod -a -G input $USER
# Note: Requires logout/login to take effect
```

---

## 4. Windows Platform Notes

### 4.1 User Permissions

| Mode | Status | Notes |
|------|--------|-------|
| **Standard User** | ✅ Supported | Works for most applications |
| **Administrator** | ✅ Recommended | Required for UAC-elevated apps |

### 4.2 Windows-Specific Requirements

- No special system dependencies required
- Keyboard injection works via `SendInput` API
- Global hotkeys work without additional setup
- Autostart via Registry `Run` key

### 4.3 Known Windows Limitations

| Limitation | Impact | Workaround |
|------------|--------|------------|
| UAC-elevated apps | Cannot inject into admin apps from standard user | Run VoiceKey as admin |
| Windows Sandbox | Limited keyboard injection | Use standard desktop session |
| Remote Desktop | May require focus on RDP window | Ensure target window has focus |

---

## 5. Distribution Channels

| Channel | Platform | Architecture | Status |
|---------|----------|--------------|--------|
| PyPI | Linux, Windows | x64 | ✅ Supported |
| Windows Installer | Windows | x64 | ✅ Supported |
| Windows Portable ZIP | Windows | x64 | ✅ Supported |
| Linux AppImage | Linux | x86_64 | ✅ Supported |

---

## 6. Hardware Requirements

### 6.1 Minimum Requirements

| Component | Minimum | Recommended |
|-----------|---------|-------------|
| CPU | 2 cores | 4+ cores |
| RAM | 4 GB | 8+ GB |
| Disk | 3 GB | 5 GB (for models) |
| Microphone | Any 16kHz-capable | USB headset |

### 6.2 Model Size Impact

| Model Profile | Disk Space | RAM Usage | Latency |
|---------------|------------|-----------|---------|
| tiny | ~150 MB | ~200 MB | Fastest |
| base | ~300 MB | ~250 MB | Fast |
| small | ~500 MB | ~350 MB | Good |

---

## 7. Known Limitations

### 7.1 Cross-Platform

| Limitation | Description |
|------------|-------------|
| First-run model download | Requires internet connection for initial setup |
| Wake word sensitivity | May need calibration in noisy environments |
| Memory usage | Increases with larger ASR models |

### 7.2 Linux-Specific

| Limitation | Description |
|------------|-------------|
| Wayland global hotkeys | May not work; use XWayland or switch to X11 |
| uinput permissions | Requires `input` group membership |
| PulseAudio/PipeWire | Both supported; may require configuration |

### 7.3 Windows-Specific

| Limitation | Description |
|------------|-------------|
| UAC applications | Cannot inject into elevated apps from standard user context |
| Anti-virus software | May flag keyboard injection; add exception |
| Windows Defender | May require whitelist for installer |

---

## 8. CI Testing Matrix

The following matrix is tested in CI for every pull request:

| OS | Python | Test Suite |
|----|--------|------------|
| Ubuntu 22.04 | 3.11 | Unit + Integration |
| Ubuntu 22.04 | 3.12 | Unit + Integration |
| Ubuntu 24.04 | 3.11 | Unit + Integration |
| Ubuntu 24.04 | 3.12 | Unit + Integration |
| Windows Server 2022 | 3.11 | Unit + Integration |
| Windows Server 2022 | 3.12 | Unit + Integration |

---

## 9. Release Verification

Each release includes:

1. ✅ Automated install smoke tests for all channels
2. ✅ Checksum verification for all artifacts
3. ✅ SBOM (Software Bill of Materials) generation
4. ✅ Integrity bundle with signatures

---

## 10. Future Roadmap

| Feature | Status | Target |
|---------|--------|--------|
| ARM64 support | Planned | P2 |
| macOS support | Under evaluation | P2+ |
| Additional Linux distros | Under evaluation | P2 |
| Python 3.13 | Planned | After stable release |

---

## 11. Compatibility Policy

### Backward Compatibility

- Semantic versioning for CLI and config behavior
- Explicit migration notes for config schema updates
- One previous major version migration path supported

### Breaking Changes

Breaking changes require:
1. Major version bump
2. Migration documentation
3. Deprecation warnings in prior minor release

---

*Document Version: 1.0*
*Last Updated: 2026-02-20*
*Requirement: FR-OSS05*
