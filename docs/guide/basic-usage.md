# Basic Usage

This guide covers the essential commands and workflows for using VoiceKey.

## Starting VoiceKey

### From Command Line

```bash
# Start with interactive dashboard
voicekey start

# Start in background (tray mode)
voicekey start --daemon

# Start minimized to tray
voicekey start --minimized
```

### From System Tray

If you've set up auto-start, VoiceKey will start automatically in the system tray.

## Using VoiceKey

### Step 1: Activate Listening

Say the wake phrase: **"voice key"**

The tray icon will turn green, indicating VoiceKey is listening.

### Step 2: Speak Your Text

Speak naturally. VoiceKey will:

1. Convert your speech to text
2. Type the text into the active application

### Step 3: Use Commands (Optional)

End your command with "command":

```
"new line command" → Presses Enter
"control c command" → Presses Ctrl+C
```

### Step 4: Return to Standby

VoiceKey automatically returns to standby after:
- Wake window timeout (default 5 seconds of silence)
- Inactivity auto-pause (in toggle/continuous mode)

## Controlling VoiceKey

### Voice Commands

These commands work without the wake phrase:

| Command | Action |
|---------|--------|
| `pause voice key` | Pause voice recognition |
| `resume voice key` | Resume voice recognition |
| `voice key stop` | Stop listening session |

### Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| `Ctrl+Shift+V` | Toggle listening (in toggle mode) |

### System Tray Menu

Right-click the tray icon for quick actions:

- **Start** — Begin listening
- **Pause/Resume** — Toggle pause state
- **Dashboard** — Open status dashboard
- **Settings** — Open configuration
- **Exit** — Close VoiceKey

## The Dashboard

The dashboard provides real-time status information:

```bash
voicekey dashboard
```

```
┌────────────────────────────────────────┐
│   VoiceKey Dashboard                │
├────────────────────────────────────────┤
│  Status:     LISTENING                 │
│  Mode:       wake_word                 │
│  Language:   en                        │
│                                        │
│  Last transcript: "Hello world"         │
│  Confidence: 0.92                      │
│                                        │
│  Uptime:     00:05:23                  │
│  CPU:        12%                       │
│  Memory:     185 MB                     │
└────────────────────────────────────────┘
```

## Status Indicators

### Tray Icon Colors

| Color | State | Meaning |
|-------|-------|---------|
|  Yellow | STANDBY | Ready, waiting for activation |
|  Green | LISTENING | Actively listening for speech |
|  Blue | PAUSED | Voice recognition paused |
|  Red | ERROR | Error occurred |

### Dashboard Status

```
Status: STANDBY         # Waiting for wake word
Status: LISTENING       # Ready to receive speech
Status: PROCESSING      # Processing recognized speech
Status: PAUSED          # Paused, awaiting resume
Status: ERROR           # Error, needs attention
```

## Example Workflows

### Workflow 1: Typing a Sentence

1. Say: "voice key"
2. Say: "Hello, how are you today?"
3. VoiceKey types: "Hello, how are you today?"
4. Wait 5 seconds for timeout → returns to STANDBY

### Workflow 2: Using Commands

1. Say: "voice key"
2. Say: "first name command"
3. VoiceKey presses: Left Arrow (home key)
4. Say: "John space last name command"
5. VoiceKey types: "John " then presses: End key

### Workflow 3: Pausing and Resuming

1. Say: "pause voice key"
2. VoiceKey pauses (icon turns blue)
3. Voice commands are ignored
4. Say: "resume voice key"
5. VoiceKey resumes (icon returns to yellow/green)

## Tips for Best Results

### Microphone Tips

- Use a good quality microphone
- Minimize background noise
- Speak clearly at normal pace
- Position microphone close to mouth

### Recognition Tips

- Wait for the wake phrase before speaking
- Speak in complete sentences
- Pause briefly between commands
- Check confidence level in dashboard

### Safety Tips

- Use wake_word mode for maximum safety
- Enable inactivity auto-pause
- Review commands before use
- Keep the wake phrase unique

---

See also: [Commands Reference](commands.md), [Listening Modes](listening-modes.md)
