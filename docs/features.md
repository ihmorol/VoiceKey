# Features

VoiceKey provides a comprehensive set of features for hands-free text input and system control.

## Core Features

###  Real-time Voice-to-Text

VoiceKey captures your voice through the microphone and converts it to text in real-time. The text is typed directly into the currently focused application.

- **Low Latency**: Sub-200ms end-to-end processing
- **High Accuracy**: Uses faster-whisper for state-of-the-art speech recognition
- **Partial Results**: See live transcription as you speak

###  Wake Word Activation

The default wake phrase is "voice key". When you speak this phrase, VoiceKey enters listening mode and processes your subsequent speech.

- **Configurable**: Change the wake phrase to your preference
- **Fast Detection**: Optimized for minimal latency
- **False Trigger Prevention**: VAD gating and sensitivity controls

###  Command Execution

Speak commands ending with "command" to trigger system actions:

| Command | Action |
|---------|--------|
| `new line command` | Press Enter |
| `tab command` | Press Tab |
| `space command` | Press Space |
| `backspace command` | Press Backspace |
| `delete command` | Press Delete |
| `left command` | Press Left Arrow |
| `right command` | Press Right Arrow |
| `up command` | Press Up Arrow |
| `down command` | Press Down Arrow |
| `control c command` | Copy (Ctrl+C) |
| `control v command` | Paste (Ctrl+V) |
| `control x command` | Cut (Ctrl+X) |
| `control z command` | Undo (Ctrl+Z) |
| `control a command` | Select All (Ctrl+A) |
| `control l command` | Focus Address Bar (Ctrl+L) |
| `scratch that command` | Delete last spoken phrase |

###  Pause/Resume Control

Control VoiceKey with your voice — no wake word required:

- **`pause voice key`** — Pauses all voice recognition
- **`resume voice key`** — Resumes voice recognition
- **`voice key stop`** — Stops current listening session

###  System Tray Integration

VoiceKey runs in the system tray, providing:

- **Visual Status**: Color-coded icon (yellow=standby, green=listening, blue=paused, red=error)
- **Quick Actions**: Start, pause, resume, dashboard, settings, exit
- **Background Operation**: Works without a terminal window

###  Auto-start Integration

Start VoiceKey automatically when you log in:

- **Linux**: `.desktop` file or systemd user service
- **Windows**: Registry Run key
- **Configurable**: Enable/disable from settings

## Listening Modes

### Wake Word Mode (Default)

VoiceKey listens only when you say the wake phrase ("voice key"). This is the safest mode with minimal accidental triggers.

```yaml
listening_mode: wake_word
```

### Toggle Mode

Use a global hotkey to toggle listening on/off. Useful for applications where wake word might trigger falsely.

```yaml
listening_mode: toggle
hotkey: "ctrl+shift+v"
```

### Continuous Mode

VoiceKey listens continuously. **Use with caution** — higher risk of accidental typing.

```yaml
listening_mode: continuous
inactive_auto_pause_seconds: 30
```

## Safety Features

### Inactivity Auto-pause

In toggle and continuous modes, VoiceKey automatically pauses after a period of inactivity (default: 30 seconds).

### Wake Window Timeout

After waking, VoiceKey returns to standby if no speech is detected within the configured timeout (default: 5 seconds).

### Unknown Command Handling

If you speak an unrecognized command phrase, VoiceKey types the literal text — nothing is silently dropped.

## Extensibility

### Custom Commands

Define custom commands in your configuration file:

```yaml
commands:
  - trigger: "email command"
    action: type_text
    text: "example@email.com"
  - trigger: "signature command"
    action: type_text
    text: "Best regards,\nYour Name"
```

### Text Expansion (P1)

Define shortcuts that expand to longer text:

```yaml
text_expansion:
  - shortcut: "/sig"
    expansion: "Best regards,\nYour Name"
  - shortcut: "/addr"
    expansion: "123 Main Street, City, Country"
```

### Per-App Profiles (P1)

Different settings for different applications:

```yaml
profiles:
  - name: terminal
    app_match: "gnome-terminal|konsole"
    wake_word: "terminal"
  - name: code
    app_match: "vscode|jetbrains"
    confidence_threshold: 0.8
```

## Platform Features

### Linux

- **X11 Support**: Full compatibility with X11-based desktop environments
- **Wayland Support**: Best-effort with explicit warnings
- **Input Methods**: pynput primary, evdev fallback

### Windows

- **Windows 10/11**: Full compatibility
- **Admin Mode**: Recommended for maximal compatibility
- **Input Methods**: pynput primary, pywin32 SendInput fallback

## Model Profiles

Choose the right balance between speed and accuracy:

| Profile | Model Size | Use Case |
|---------|------------|----------|
| `tiny` | ~39 MB | Low-end machines |
| `base` | ~74 MB | Default (recommended) |
| `small` | ~244 MB | High accuracy |

---

See also: [Commands Reference](guide/commands.md), [Listening Modes](guide/listening-modes.md)
