# Configuration

VoiceKey can be configured via CLI commands or by editing the configuration file directly.

## Configuration File Location

| Platform | Location |
|----------|----------|
| Linux | `~/.config/voicekey/config.yaml` |
| Windows | `%APPDATA%\voicekey\config.yaml` |

## Using the CLI

### View Configuration

```bash
# Show all settings
voicekey config show

# Get specific value
voicekey config get listening.mode
voicekey config get asr.model_profile
```

### Set Configuration

```bash
# Set a value
voicekey config set listening.mode wake_word
voicekey config set asr.model_profile base
voicekey config set listening.wake_phrase "hey keyboard"

# Set nested values
voicekey config set hotkeys.toggle_listening "ctrl+shift+v"
```

### Reset Configuration

```bash
# Reset to defaults
voicekey config reset

# Reset specific section
voicekey config reset listening
```

## Configuration Schema

### Listening Settings

```yaml
listening:
  # Listening mode: wake_word, toggle, continuous
  mode: wake_word

  # Wake phrase (used in wake_word mode)
  wake_phrase: "voice key"

  # Seconds to wait for speech after wake
  wake_window_timeout_seconds: 5

  # Seconds of inactivity before auto-pause (toggle/continuous mode)
  inactive_auto_pause_seconds: 30
```

### ASR Settings

```yaml
asr:
  # Model profile: tiny, base, small
  model_profile: base

  # Minimum confidence (0.0-1.0)
  confidence_threshold: 0.5

  # Language code (auto-detected by default)
  language: auto
```

### Audio Settings

```yaml
audio:
  # Sample rate in Hz
  sample_rate: 16000

  # Chunk duration in seconds
  chunk_duration: 0.1

  # Audio device index (auto-detect by default)
  device: auto
```

### VAD Settings

```yaml
vad:
  # Enable/disable VAD
  enabled: true

  # Speech detection threshold (0.0-1.0)
  threshold: 0.5

  # Minimum speech duration in seconds
  min_speech_duration: 0.1
```

### Hotkey Settings

```yaml
hotkeys:
  # Toggle listening (toggle mode)
  toggle_listening: "ctrl+shift+v"

  # Alternative toggle
  pause_resume: "ctrl+alt+v"
```

### Autostart Settings

```yaml
autostart:
  # Enable auto-start at login
  enabled: true

  # Start minimized to tray
  start_minimized: true
```

### Logging Settings

```yaml
logging:
  # Log level: debug, info, warning, error
  level: info

  # Log file path
  file: null  # null = no file logging

  # Enable debug logging temporarily
  debug: false
```

### Feature Gates

```yaml
features:
  # Enable window commands (P1)
  window_commands: false

  # Enable text expansion (P1)
  text_expansion: false

  # Enable per-app profiles (P1)
  profiles: false
```

## Example Configuration

### Basic Configuration

```yaml
version: "1.0"

listening:
  mode: wake_word
  wake_phrase: "voice key"
  wake_window_timeout_seconds: 5

asr:
  model_profile: base
  confidence_threshold: 0.5

autostart:
  enabled: true
  start_minimized: true
```

### Toggle Mode Configuration

```yaml
version: "1.0"

listening:
  mode: toggle
  inactive_auto_pause_seconds: 30

hotkeys:
  toggle_listening: "ctrl+shift+v"

asr:
  model_profile: tiny  # Faster for toggle mode
```

### Continuous Mode Configuration

```yaml
version: "1.0"

listening:
  mode: continuous
  inactive_auto_pause_seconds: 15  # Shorter for safety

asr:
  model_profile: tiny
  confidence_threshold: 0.7  # Higher threshold
```

## Environment Variables

Override configuration with environment variables:

```bash
# Set environment variable
export VOICEKEY_LISTENING_MODE=wake_word
export VOICEKEY_ASR_MODEL_PROFILE=base

# Run VoiceKey
voicekey start
```

| Variable | Description |
|----------|-------------|
| `VOICEKEY_CONFIG_PATH` | Custom config file path |
| `VOICEKEY_LISTENING_MODE` | Override listening mode |
| `VOICEKEY_ASR_MODEL_PROFILE` | Override ASR model |
| `VOICEKEY_LOG_LEVEL` | Override log level |
| `VOICEKEY_DEBUG` | Enable debug mode |

## Configuration Migration

When VoiceKey updates, it may update your configuration:

1. Backup is created automatically (`config.yaml.bak`)
2. Unknown keys are warned but preserved
3. Invalid values fail to defaults with warning

## Troubleshooting

### Config Not Loading

```bash
# Check config path
voicekey config show

# Validate YAML syntax
python -c "import yaml; yaml.safe_load(open('~/.config/voicekey/config.yaml'))"
```

### Changes Not Taking Effect

Some settings require restart:

```bash
# Restart VoiceKey
voicekey restart
```

---

See also: [Commands Reference](commands.md), [Listening Modes](listening-modes.md)
