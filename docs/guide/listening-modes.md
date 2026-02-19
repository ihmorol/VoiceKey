# Listening Modes

VoiceKey supports three listening modes, each designed for different use cases.

## Mode Overview

| Mode | Activation | Best For |
|------|------------|----------|
| `wake_word` | Say wake phrase | Maximum safety |
| `toggle` | Hot Applicationskey | with false triggers |
| `continuous` | Always on | Power users, accessibility |

## Wake Word Mode (Default)

### How It Works

1. VoiceKey waits in STANDBY state
2. You say the wake phrase ("voice key")
3. VoiceKey enters LISTENING state
4. Speak your text
5. After timeout, VoiceKey returns to STANDBY

### Configuration

```yaml
listening:
  mode: wake_word
  wake_phrase: "voice key"
  wake_window_timeout_seconds: 5
```

### Pros

-  Maximum safety — no accidental triggers
-  Saves resources when not in use
-  Clear activation/deactivation

### Cons

-  Requires saying wake phrase each time
-  Slightly higher latency for first word

### Best Practices

- Use the default wake phrase or something unique
- Keep the timeout at 5 seconds
- This is the recommended mode for most users

## Toggle Mode

### How It Works

1. Press the toggle hotkey (default: Ctrl+Shift+V)
2. VoiceKey enters LISTENING state
3. Speak your text
4. Press hotkey again OR inactivity timeout
5. VoiceKey returns to STANDBY

### Configuration

```yaml
listening:
  mode: toggle
  inactive_auto_pause_seconds: 30

hotkeys:
  toggle_listening: "ctrl+shift+v"
```

### Pros

-  No wake phrase needed
-  Good control over activation
-  Inactivity auto-pause for safety

### Cons

-  Requires keyboard interaction
-  May not work in all applications

### Best Practices

- Choose a convenient hotkey
- Keep inactivity timeout short (15-30s)
- Use in applications with frequent false wake triggers

## Continuous Mode

### How It Works

1. VoiceKey starts in LISTENING state
2. Always listening for speech
3. Auto-pauses after inactivity
4. Resume via voice command or hotkey

### Configuration

```yaml
listening:
  mode: continuous
  inactive_auto_pause_seconds: 30
```

!!! warning "Higher Risk"
    Continuous mode has the highest risk of accidental typing. Use with caution and ensure:
    
    - Higher confidence threshold (0.7+)
    - Shorter inactivity timeout (15s)
    - Good microphone noise rejection

### Pros

-  Instant activation — no wake phrase
-  Best for hands-free workflows
-  Seamless dictation

### Cons

-  Highest risk of accidental triggers
-  More CPU usage
-  May type unintended speech

### Best Practices

- Increase confidence threshold to 0.7+
- Reduce inactivity timeout to 15s
- Use in quiet environments
- Consider using VAD sensitivity

## Mode Comparison

| Feature | wake_word | toggle | continuous |
|---------|-----------|--------|------------|
| Activation | Wake phrase | Hotkey | Always |
| Deactivation | Timeout | Hotkey/Timeout | Timeout |
| Safety | High | Medium | Low |
| CPU Usage | Low | Low | Medium |
| Latency | Normal | Normal | Fastest |
| Wake phrase | Required | Not needed | Not needed |
| Hotkey | Optional | Required | Optional |

## Switching Modes

### Via CLI

```bash
# Switch to wake_word mode
voicekey config set listening.mode wake_word

# Switch to toggle mode
voicekey config set listening.mode toggle

# Switch to continuous mode
voicekey config set listening.mode continuous

# Restart to apply
voicekey restart
```

### Via System Tray

1. Right-click tray icon
2. Select "Mode"
3. Choose desired mode

## Safety Features by Mode

### Wake Word Mode

- Wake window timeout (default 5s)
- Only activates on wake phrase
- Clear on/off state

### Toggle Mode

- Wake window timeout (default 5s)
- Inactivity auto-pause (default 30s)
- Manual control via hotkey

### Continuous Mode

- Inactivity auto-pause (default 30s)
- Confidence threshold enforcement
- Pause/resume commands work

## Recommendations

### For Beginners

Use **wake_word mode** — it's the safest and easiest to use.

### For Application Development

Use **toggle mode** — good balance of control and safety.

### For Accessibility

Consider **continuous mode** with careful configuration:
- High confidence threshold (0.8)
- Short inactivity timeout (15s)
- Good microphone setup

---

See also: [Commands Reference](commands.md), [Configuration](configuration.md)
