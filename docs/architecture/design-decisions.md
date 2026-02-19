# Design Decisions

This document explains the key architectural decisions made in VoiceKey and the reasoning behind them.

## ASR Engine Selection

### Decision: Use faster-whisper as Primary ASR

**Alternatives Considered:**
- Whisper (OpenAI)
- Whisper.cpp
- Coqui STT
- Vosk

**Chosen:** faster-whisper (CTranslate2 backend)

**Rationale:**
-  2-4x faster than original Whisper
-  Int8 and float16 quantization support
-  Same accuracy as original Whisper
-  Active maintenance
-  Easy model selection (tiny/base/small)

**Trade-offs:**
- Larger model sizes compared to tiny models like Vosk
- Higher CPU usage than specialized small models

## Voice Activity Detection

### Decision: Silero VAD with Energy-based Fallback

**Chosen:** Silero VAD

**Rationale:**
-  State-of-the-art accuracy
-  Lightweight models
-  Local processing (privacy)
-  Good for streaming
-  Fallback ensures functionality when Silero unavailable

**Trade-offs:**
- Requires model download (~50MB)
- Fallback is less accurate

## Keyboard Injection

### Decision: pynput Primary with Platform Fallbacks

**Chosen:** pynput → evdev (Linux) / pywin32 (Windows)

**Rationale:**
-  Cross-platform abstraction
-  Works in most scenarios
-  Fallbacks handle edge cases

**Trade-offs:**
- Requires permissions on some systems
- Some applications may block input

## Wake Word Detection

### Decision: Phrase Spottable Detection with VAD Gating

**Chosen:** Streaming ASR with phrase detection + VAD pre-filtering

**Rationale:**
-  Reuses ASR model (no extra model)
-  VAD reduces false triggers
-  Configurable sensitivity

**Trade-offs:**
- Higher latency than specialized wake word models
- More CPU usage while monitoring

## Listening Modes

### Decision: Three Modes (wake_word, toggle, continuous)

**Chosen:** wake_word (default), toggle, continuous

**Rationale:**
- **wake_word** — Default for safety, minimizes accidental triggers
- **toggle** — For applications with frequent false wake triggers
- **continuous** — Power users who want always-on, with auto-pause safety

**Trade-offs:**
- Multiple modes increase complexity
- Each mode has different safety characteristics

## State Machine Design

### Decision: Hierarchical FSM with Safety Timers

**Chosen:** Single FSM with timers

**Rationale:**
-  Clear state transitions
-  Predictable behavior
-  Easy to debug
-  Safety timers prevent hung states

**Trade-offs:**
- Complex for advanced users to customize
- Some edge cases require careful handling

## Command Parsing

### Decision: Suffix-based Command Detection

**Chosen:** Commands end with "command" suffix

**Rationale:**
-  Simple and intuitive
-  Natural language integration
-  Unknown commands type literally
-  No silent failures

**Trade-offs:**
- Requires saying "command" for every action
- Some phrases may be awkward

## Configuration Format

### Decision: YAML with Pydantic Validation

**Chosen:** YAML config + Pydantic schema

**Rationale:**
-  Human-readable
-  Supports comments
-  Pydantic provides validation and migration
-  Easy to extend

**Trade-offs:**
- YAML parsing can be slow for very large configs
- Schema changes require migration

## Model Distribution

### Decision: External Download, Separate from Installer

**Chosen:** Runtime download with checksum verification

**Rationale:**
-  Smaller installer
-  User can choose model size
-  Easy model updates
-  Checksum ensures integrity

**Trade-offs:**
- First-run requires internet
- Multiple downloads for multiple sizes

## Privacy Design

### Decision: Offline-Only with No Telemetry

**Chosen:** Fully offline after model download

**Rationale:**
-  Maximum privacy
-  No network dependencies
-  Works without internet
-  User trust

**Trade-offs:**
- No automatic updates without user action
- Can't collect usage data for improvements

## Error Recovery

### Decision: Auto-Pause on Uncertainty

**Chosen:** Transition to PAUSED state on errors

**Rationale:**
-  Prevents accidental typing
-  User can manually resume
-  Clear feedback

**Trade-offs:**
- Requires user intervention to resume
- May interrupt workflow

## Platform Support

### Decision: Linux (X11 primary) and Windows

**Chosen:** Ubuntu 22.04/24.04 + Windows 10/11

**Rationale:**
-  Largest desktop user base
-  Best library support
-  Clear testing matrix

**Trade-offs:**
- macOS not supported
- Wayland has limited support

## Future Considerations

### Potential Changes

1. **Plugin SDK** — For extensibility (P2)
2. **Multi-language** — Non-English ASR models (P2)
3. **WebSocket API** — For integration with other tools (P2)
4. **macOS Support** — If demand increases
5. **Cloud Optional** — For users who want it (P2)

---

See also: [Architecture Overview](overview.md), [State Machine](state-machine.md)
