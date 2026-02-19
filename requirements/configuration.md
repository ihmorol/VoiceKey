# VoiceKey Configuration Specification

> Version: 2.0 (Aligned)
> Date: 2026-02-19

---

## 1. Config Paths

| Platform | Default Path |
|----------|---------------|
| Linux | `~/.config/voicekey/config.yaml` |
| Windows | `%APPDATA%\voicekey\config.yaml` |

Overrides:

- CLI: `voicekey start --config /path/config.yaml`
- ENV: `VOICEKEY_CONFIG=/path/config.yaml`

---

## 2. Canonical Default Config

```yaml
version: 3

engine:
  asr_backend: "faster-whisper"
  model_profile: "base"          # tiny | base | small
  compute_type: "int8"           # int8 | int16 | float16 (platform dependent)
  language: "en"

audio:
  sample_rate_hz: 16000
  channels: 1
  chunk_ms: 160
  device_id: null

vad:
  enabled: true
  speech_threshold: 0.5
  min_speech_ms: 120

wake_word:
  enabled: true
  phrase: "voice key"
  sensitivity: 0.55
  wake_window_timeout_seconds: 5

modes:
  default: "wake_word"           # wake_word | toggle | continuous
  inactivity_auto_pause_seconds: 30
  allow_continuous_mode: true
  paused_resume_phrase_enabled: true

hotkeys:
  toggle_listening: "ctrl+shift+`"
  pause: "ctrl+shift+p"
  stop: "ctrl+shift+e"

typing:
  char_delay_ms: 8
  undo_buffer_segments: 30
  confidence_threshold: 0.5

ui:
  tray_enabled: true
  start_minimized_to_tray: true
  terminal_dashboard: true
  audio_feedback: true
  show_latency: true

system:
  autostart_enabled: false
  single_instance: true
  daemon_mode_default: true

features:
  text_expansion_enabled: false
  per_app_profiles_enabled: false
  window_commands_enabled: false

privacy:
  telemetry_enabled: false
  transcript_logging: false
  redact_debug_text: true

custom_commands: {}

snippets:
  ty: "thank you"
  brb: "be right back"
```

---

## 3. Config Command Contract

```bash
voicekey config
voicekey config --get wake_word.phrase
voicekey config --set modes.inactivity_auto_pause_seconds=20
voicekey config --set system.autostart_enabled=true
voicekey config --reset
voicekey config --edit
```

---

## 4. Validation Rules

| Key | Constraint |
|-----|------------|
| `audio.sample_rate_hz` | must be one of `8000, 16000, 32000, 44100, 48000` |
| `audio.chunk_ms` | `80..300` |
| `wake_word.sensitivity` | `0.0..1.0` |
| `modes.inactivity_auto_pause_seconds` | `5..300` |
| `modes.paused_resume_phrase_enabled` | boolean |
| `typing.char_delay_ms` | `0..50` |
| `typing.confidence_threshold` | `0.0..1.0` |

Invalid config values must:

1. emit warning,
2. fallback to safe default,
3. preserve user file with migration note.

---

## 5. Migration Policy

- Every config file includes `version`.
- Migrations are forward-only and idempotent.
- On migration failure: backup old config and regenerate defaults.

---

## 6. Environment Variables

| Variable | Meaning |
|----------|---------|
| `VOICEKEY_CONFIG` | config file path override |
| `VOICEKEY_MODEL_DIR` | model storage path override |
| `VOICEKEY_LOG_LEVEL` | runtime log level |
| `VOICEKEY_DISABLE_TRAY` | force tray off |

---

*Document Version: 2.0*  
*Last Updated: 2026-02-19*
