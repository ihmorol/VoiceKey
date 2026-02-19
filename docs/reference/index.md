# API Reference

This section provides detailed API documentation for VoiceKey's modules.

## Module Overview

| Module | Description |
|--------|-------------|
| [Audio Module](audio.md) | Audio capture and VAD |
| [Commands Module](commands.md) | Command parsing and execution |
| [Platform Module](platform.md) | Platform-specific backends |
| [Configuration](config.md) | Configuration schema |

## Quick Reference

### CLI Commands

```bash
voicekey start              # Start VoiceKey
voicekey stop               # Stop VoiceKey
voicekey restart            # Restart VoiceKey
voicekey status             # Show status
voicekey setup              # Run setup wizard
voicekey test-microphone    # Test microphone
voicekey list-devices      # List audio devices
voicekey download-models   # Download ASR models
voicekey config show        # Show configuration
voicekey config set        # Set configuration
voicekey dashboard         # Open dashboard
```

### Python API

```python
from voicekey.audio.capture import AudioCapture
from voicekey.audio.vad import VADProcessor
from voicekey.config.manager import ConfigManager
```

## Module Structure

```
voicekey/
├── app/                 # Application layer
│   ├── main.py         # Entry point
│   ├── state_machine.py
│   └── watchdog.py
├── audio/              # Audio processing
│   ├── capture.py      # Microphone capture
│   ├── vad.py         # Voice activity detection
│   ├── wake.py        # Wake word detection
│   └── asr_faster_whisper.py
├── commands/           # Command handling
│   ├── parser.py      # Command parser
│   ├── registry.py    # Command registry
│   └── builtins.py    # Built-in commands
├── actions/           # Action dispatch
│   ├── router.py
│   ├── keyboard_dispatch.py
│   └── window_dispatch.py
├── platform/          # Platform backends
├── ui/                # User interfaces
├── config/            # Configuration
└── models/            # Model management
```
