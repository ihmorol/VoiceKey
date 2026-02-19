# Roadmap

This document outlines VoiceKey's development roadmap and future plans.

## Release Philosophy

VoiceKey follows a milestone-driven approach:

- **P0 (Baseline)** — Core features for a world-class product
- **P1 (High Impact)** — Features that significantly enhance usability
- **P2 (Expansion)** — Advanced features for power users

---

## Current Status

### v0.1.x — Foundation

**Status:** In Development

Focus: Core architecture and audio pipeline

-  Audio capture module
-  VAD module
-  State machine
-  Command parser
-  ASR integration
-  Platform backends
-  UI components

---

## P0 — Baseline Features

*Must for world-class baseline*

### Core Speech Pipeline

- [ ] faster-whisper integration
- [ ] Wake word detection
- [ ] Partial transcript support
- [ ] Confidence thresholding

### System Integration

- [ ] System tray background mode
- [ ] Auto-start at login (Linux)
- [ ] Auto-start at login (Windows)
- [ ] First-run onboarding wizard

### Safety

- [ ] Inactivity auto-pause
- [ ] Wake window timeout
- [ ] Unknown command fallback

### Distribution

- [ ] PyPI package
- [ ] Windows installer
- [ ] Linux AppImage

### Documentation

- [ ] Installation guides
- [ ] User guide
- [ ] API reference

---

## P1 — High Impact Features

*High impact for productivity*

### Text Expansion

- [ ] User-defined text snippets
- [ ] Shortcut expansion
- [ ] Variable placeholders

### Window Commands

- [ ] Maximize window
- [ ] Minimize window
- [ ] Close window
- [ ] Switch window

### Per-App Profiles

- [ ] Application detection
- [ ] Per-app settings
- [ ] Different wake words per app

### Portable Mode

- [ ] Local config directory
- [ ] No system installation
- [ ] USB-friendly

---

## P2 — Expansion

*Expansion for power users*

### Multi-Language Support

- [ ] Non-English ASR models
- [ ] Language switching
- [ ] Multi-language dictation

### Plugin SDK

- [ ] Plugin API
- [ ] Custom command plugins
- [ ] Plugin marketplace (future)

### Advanced Automation

- [ ] Script execution
- [ ] Macro recording
- [ ] Conditional commands

### Cloud (Optional)

- [ ] Optional cloud ASR fallback
- [ ] User-configurable
- [ ] Privacy warning

---

## Feature Wishlist

Community-requested features under consideration:

| Feature | Priority | Status |
|---------|----------|--------|
| macOS support | P2 | Considering |
| WebSocket API | P2 | Considering |
| Mobile companion | Out of Scope | No plans |
| Cloud transcription | P2 | Optional |

---

## Version Timeline

### v0.2.0 — Alpha

Target: Q2 2026

- Basic voice-to-text
- Wake word activation
- Core commands

### v0.3.0 — Beta

Target: Q3 2026

- System tray
- Auto-start
- First-run wizard

### v1.0.0 — Stable

Target: Q4 2026

- Full P0 features
- Production-ready
- Documentation complete

### v1.1.0 — Feature Release

Target: Q1 2027

- Text expansion
- Window commands
- Per-app profiles

---

## Contributing to Roadmap

VoiceKey is community-driven. Here's how to influence the roadmap:

1. **Open GitHub Issues** — Suggest features or vote on existing ones
2. **Join Discussions** — Share your use cases
3. **Contribute Code** — Implement features yourself
4. **Provide Feedback** — Help prioritize

---

## Past Releases

### v0.1.0 (Current)

- Initial architecture
- Audio capture module
- VAD module
- Unit tests

---

*Last updated: February 2026*
