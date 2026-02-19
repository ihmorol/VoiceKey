# VoiceKey Troubleshooting Guide

> Version: 1.0
> Date: 2026-02-19

---

## 1. No Typing Occurs

Possible causes:

- VoiceKey is paused
- target app blocks synthetic input
- missing permissions

Checks:

```bash
voicekey status
voicekey config --get modes.default
```

Fixes:

- say `resume voice key`
- run terminal/app with required privileges
- switch to supported app to validate baseline

---

## 2. Wake Word Triggers Too Often

Fixes:

```bash
voicekey config --set wake_word.sensitivity=0.7
voicekey config --set vad.speech_threshold=0.6
```

---

## 3. Wake Word Not Triggering

Fixes:

```bash
voicekey config --set wake_word.sensitivity=0.4
voicekey calibrate
```

Also verify microphone device selection.

---

## 4. High Latency

Fixes:

```bash
voicekey config --set engine.model_profile=tiny
voicekey config --set audio.chunk_ms=120
voicekey config --set typing.char_delay_ms=0
```

Close CPU-heavy background apps.

---

## 5. Tray Icon Missing

Checks:

- desktop environment supports system tray
- `ui.tray_enabled` is true

```bash
voicekey config --set ui.tray_enabled=true
```

---

## 6. Hotkey Conflict

Set alternative hotkey:

```bash
voicekey config --set hotkeys.toggle_listening="ctrl+shift+f12"
```

---

## 7. Model Download/Load Failure

Actions:

```bash
voicekey download --force
voicekey status
```

Ensure enough disk space and no proxy/firewall corruption during download.

---

## 8. Linux Wayland Limitations

Symptoms:

- keyboard injection works only in some apps

Mitigation:

- use X11 session for full compatibility
- keep Wayland support as best-effort mode

---

## 9. Export Debug Bundle

```bash
voicekey diagnostics --export ./voicekey-debug.zip
```

Debug export should redact transcript by default.

---

*Document Version: 1.0*  
*Last Updated: 2026-02-19*
