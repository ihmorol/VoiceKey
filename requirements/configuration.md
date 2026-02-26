# VoiceKey Configuration Specification

> Version: 2.2 (Hybrid ASR Routing)
> Date: 2026-02-26

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
  asr_backend: "faster-whisper" # faster-whisper | openai-api-compatible
  model_profile: "base"          # tiny | base | small
  compute_type: "int8"           # int8 | int16 | float16 (platform dependent)
  language: "en"
  network_fallback_enabled: false # when true with faster-whisper, run hybrid mode (local primary, cloud fallback)
  cloud_model: "gpt-4o-mini-transcribe"
  cloud_api_base: null            # OpenAI-compatible base URL when fallback/cloud backend is enabled
  cloud_timeout_seconds: 30

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

## 2.1 Hybrid and Cloud Backend Semantics

- `asr_backend=faster-whisper` and `engine.network_fallback_enabled=false` -> local-only mode.
- `asr_backend=faster-whisper` and `engine.network_fallback_enabled=true` -> hybrid mode (local primary, cloud fallback on local failure/timeout).
- `asr_backend=openai-api-compatible` -> cloud-primary mode.
- Cloud fallback/cloud-primary modes require `VOICEKEY_OPENAI_API_KEY` and a reachable API endpoint.

Example hybrid enablement:

```bash
voicekey config --set engine.asr_backend=faster-whisper
voicekey config --set engine.network_fallback_enabled=true
voicekey config --set engine.cloud_api_base=https://api.openai.com/v1
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
| `engine.asr_backend` | `faster-whisper` or `openai-api-compatible` |
| `engine.network_fallback_enabled` | boolean |
| `engine.cloud_api_base` | null or valid `https://` URL |
| `engine.cloud_timeout_seconds` | integer `5..120` |
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

Conditional validation rules:

1. if `engine.asr_backend=openai-api-compatible`, `engine.cloud_api_base` and `VOICEKEY_OPENAI_API_KEY` must be present.
2. if `engine.network_fallback_enabled=true`, cloud endpoint and API key must be available before fallback path is activated.
3. if cloud validation fails, runtime must stay in local-only mode and emit actionable warning.

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
| `VOICEKEY_OPENAI_API_KEY` | API key for hybrid fallback/cloud backend |

---

*Document Version: 2.2*  
*Last Updated: 2026-02-26*
