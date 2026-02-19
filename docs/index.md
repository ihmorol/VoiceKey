# Welcome to VoiceKey

**VoiceKey** is a **privacy-first, offline voice-to-keyboard** application for Linux and Windows. It captures microphone audio, recognizes speech in real-time, and emits keyboard input into the currently focused window — all without sending your voice data to the cloud.

## Why VoiceKey?

- **100% Offline** — Your voice never leaves your computer. All speech recognition happens locally.
- **Privacy-First** — No telemetry, no audio logging, no cloud dependencies.
- **Lightning Fast** — Sub-200ms end-to-end latency for seamless typing.
- **Open Source** — MIT licensed with transparent, auditable code.

## Key Features

| Feature | Description |
|---------|-------------|
| 🎙️ **Voice-to-Text** | Dictate text in any application using your voice |
| 🔐 **Wake Word** | Say "voice key" to activate listening mode |
| ⌨️ **Command Execution** | Speak commands ending with "command" for instant actions |
| ⏸️ **Pause/Resume** | Control voice typing with voice commands or hotkeys |
| 🔔 **System Tray** | Runs in background with visual status indicators |
| 🚀 **Auto-start** | Launch at login for seamless integration |

## Quick Example

```
# Simply speak and watch your words appear:
"Hello world" → Hello world

# Use commands for actions:
"new line command" → [Enter pressed]
"control c command" → [Ctrl+C pressed]

# Control VoiceKey itself:
"pause voice key" → Pauses voice recognition
"resume voice key" → Resumes voice recognition
```

## Supported Platforms

| Platform | Status | Version |
|----------|--------|---------|
| 🐧 Ubuntu 22.04 LTS | ✅ Supported | x64 |
| 🐧 Ubuntu 24.04 LTS | ✅ Supported | x64 |
| 🪟 Windows 10 | ✅ Supported | x64 |
| 🪟 Windows 11 | ✅ Supported | x64 |

## Installation

=== "Linux (pip)"

    ```bash
    pip install voicekey
    ```

=== "Linux (AppImage)"

    Download from [Releases](https://github.com/voicekey/voice-key/releases)

=== "Windows"

    ```powershell
    pip install voicekey
    ```

    Or download the installer from [Releases](https://github.com/voicekey/voice-key/releases)

## Getting Started

1. **Install VoiceKey** — Follow the [Installation Guide](installation/index.md)
2. **Run Setup** — Execute `voicekey setup` to configure your microphone
3. **Start Dictating** — Say "voice key" followed by what you want to type!

## Architecture

VoiceKey follows a modular, layer-based architecture:

```
┌─────────────────────────────────────────┐
│         UI Layer (CLI, Tray, Dashboard) │
├─────────────────────────────────────────┤
│    Application Layer (FSM, Commands)    │
├─────────────────────────────────────────┤
│    Speech Layer (Capture → VAD → ASR)    │
├─────────────────────────────────────────┤
│    Platform Layer (Keyboard, Hotkeys)   │
└─────────────────────────────────────────┘
```

## Performance Targets

| Metric | Target | Acceptable |
|--------|--------|------------|
| Wake Detect Latency | ≤100ms | ≤150ms |
| ASR Processing | ≤150ms | ≤220ms |
| End-to-End | ≤200ms p50 | ≤350ms p95 |
| Idle CPU | ≤5% | — |
| Memory | ≤300MB | — |

## Contributing

VoiceKey welcomes contributions! Please see our [Contributing Guide](development/contributing.md) for details.

- 📖 [Documentation](index.md)
- 💬 [GitHub Discussions](https://github.com/voicekey/voice-key/discussions)
- 🐛 [Issue Tracker](https://github.com/voicekey/voice-key/issues)

---

*VoiceKey — Your voice, your keyboard, your privacy.*
