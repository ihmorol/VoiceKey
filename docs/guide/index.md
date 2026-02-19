# User Guide

Welcome to the VoiceKey user guide. This section covers everything you need to know to use VoiceKey effectively.

## Contents

- [Basic Usage](basic-usage.md) — Getting started with VoiceKey
- [Commands Reference](commands.md) — All available voice commands
- [Configuration](configuration.md) — Customizing VoiceKey settings
- [Listening Modes](listening-modes.md) — Understanding different modes

## Quick Reference

### Starting VoiceKey

```bash
# With dashboard
voicekey start

# In background (tray mode)
voicekey start --daemon

# With specific mode
voicekey start --mode toggle
```

### Common Commands

| Command | Action |
|---------|--------|
| "voice key" | Activate listening (wake word) |
| "pause voice key" | Pause voice recognition |
| "resume voice key" | Resume voice recognition |
| "voice key stop" | Stop listening session |

### System Tray

| Icon Color | Status |
|------------|--------|
|  Yellow | STANDBY - Ready |
|  Green | LISTENING - Active |
|  Blue | PAUSED - Paused |
|  Red | ERROR - Issue |

## Getting Help

- [Troubleshooting](../resources/troubleshooting.md)
- [FAQ](../resources/faq.md)
- [GitHub Issues](https://github.com/voicekey/voice-key/issues)
