# Configuration Reference

Complete reference for VoiceKey configuration options.

## Configuration File

### Location

| Platform | Path |
|----------|------|
| Linux | `~/.config/voicekey/config.yaml` |
| Windows | `%APPDATA%\voicekey\config.yaml` |

### Format

YAML with Pydantic validation.

---

## Schema Reference

### Root Options

```yaml
# Config version (do not change)
version: "1.0"
```

---

### Listening Configuration

```yaml
listening:
  # Listening mode
  # Options: wake_word, toggle, continuous
  mode: wake_word

  # Wake phrase for activation
  # Default: "voice key"
  wake_phrase: "voice key"

  # Seconds to wait for speech after wake
  # Default: 5
  # Range: 1-60
  wake_window_timeout_seconds: 5

  # Seconds of inactivity before auto-pause
  # Default: 30
  # Only applies to toggle and continuous modes
  inactive_auto_pause_seconds: 30
```

---

### ASR Configuration

```yaml
asr:
  # Model profile
  # Options: tiny (~39MB), base (~74MB), small (~244MB)
  # Default: base
  model_profile: base

  # Minimum confidence threshold
  # Default: 0.5
  # Range: 0.0-1.0
  confidence_threshold: 0.5

  # Language code
  # Options: auto, en, es, fr, de, etc.
  # Default: auto
  language: auto
```

---

### Audio Configuration

```yaml
audio:
  # Sample rate in Hz
  # Default: 16000
  # Recommended: 16000
  sample_rate: 16000

  # Chunk duration in seconds
  # Default: 0.1
  # Range: 0.05-0.5
  chunk_duration: 0.1

  # Audio device index
  # Options: auto, device index (integer)
  # Default: auto
  device: auto
```

---

### VAD Configuration

```yaml
vad:
  # Enable voice activity detection
  # Default: true
  enabled: true

  # Speech detection threshold
  # Default: 0.5
  # Range: 0.0-1.0
  threshold: 0.5

  # Minimum speech duration in seconds
  # Default: 0.1
  min_speech_duration: 0.1
```

---

### Hotkey Configuration

```yaml
hotkeys:
  # Toggle listening mode
  # Default: ctrl+shift+v
  toggle_listening: "ctrl+shift+v"

  # Alternative pause/resume
  # Default: null (not set)
  pause_resume: null
```

---

### Autostart Configuration

```yaml
autostart:
  # Enable auto-start at login
  # Default: false
  enabled: false

  # Start minimized to tray
  # Default: false
  start_minimized: false
```

---

### Logging Configuration

```yaml
logging:
  # Log level
  # Options: debug, info, warning, error
  # Default: info
  level: info

  # Log file path
  # Default: null (no file logging)
  file: null

  # Enable debug logging temporarily
  # Default: false
  debug: false
```

---

### Feature Gates

```yaml
features:
  # Enable window commands (P1)
  # Default: false
  window_commands: false

  # Enable text expansion (P1)
  # Default: false
  text_expansion: false

  # Enable per-app profiles (P1)
  # Default: false
  profiles: false
```

---

### Custom Commands

```yaml
# Custom commands (advanced)
commands:
  - trigger: "email command"
    action: type_text
    text: "user@example.com"

  - trigger: "address command"
    action: type_text
    text: "123 Main Street\nCity, State 12345"
```

---

### Text Expansion

```yaml
# Text expansion snippets (P1)
text_expansion:
  - shortcut: "/sig"
    expansion: "Best regards,\nYour Name"

  - shortcut: "/addr"
    expansion: "123 Main Street\nCity, State 12345"

  - shortcut: "/todo"
    expansion: "- [ ] "
```

---

### Per-App Profiles

```yaml
# Application-specific profiles (P1)
profiles:
  - name: terminal
    app_match: "gnome-terminal|konsole|xterm"
    wake_word: "terminal"
    confidence_threshold: 0.6

  - name: code
    app_match: "vscode|jetbrains|vim"
    wake_word: "code"
    confidence_threshold: 0.8
```

---

## Environment Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `VOICEKEY_CONFIG_PATH` | Custom config path | `/path/to/config.yaml` |
| `VOICEKEY_LISTENING_MODE` | Override mode | `wake_word` |
| `VOICEKEY_ASR_MODEL_PROFILE` | Override model | `tiny` |
| `VOICEKEY_LOG_LEVEL` | Override log level | `debug` |
| `VOICEKEY_DEBUG` | Enable debug | `1` |
| `VOICEKEY_AUDIO_DEVICE` | Override audio device | `2` |

---

## Default Configuration

```yaml
version: "1.0"

listening:
  mode: wake_word
  wake_phrase: "voice key"
  wake_window_timeout_seconds: 5
  inactive_auto_pause_seconds: 30

asr:
  model_profile: base
  confidence_threshold: 0.5
  language: auto

audio:
  sample_rate: 16000
  chunk_duration: 0.1
  device: auto

vad:
  enabled: true
  threshold: 0.5
  min_speech_duration: 0.1

hotkeys:
  toggle_listening: "ctrl+shift+v"
  pause_resume: null

autostart:
  enabled: false
  start_minimized: false

logging:
  level: info
  file: null
  debug: false

features:
  window_commands: false
  text_expansion: false
  profiles: false
```

---

## Validation

Configuration is validated on load using Pydantic:

```python
from voicekey.config.schema import VoiceKeyConfig

# Load and validate
config = VoiceKeyConfig.from_file("~/.config/voicekey/config.yaml")

# Access values
print(config.listening.mode)  # wake_word
print(config.asr.model_profile)  # base
```

---

See also: [Configuration Guide](../guide/configuration.md), [API Reference](../reference/index.md)
