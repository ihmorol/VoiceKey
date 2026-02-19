# Getting Started

This guide will help you get VoiceKey up and running in minutes.

## Prerequisites

- Python 3.11 or higher
- A working microphone
- Linux (Ubuntu 22.04/24.04) or Windows 10/11

## Installation

=== "Linux (pip)"

    ```bash
    pip install voicekey
    ```

    For Linux-specific dependencies:

    ```bash
    pip install voicekey[linux]
    ```

=== "Windows (pip)"

    ```powershell
    pip install voicekey[windows]
    ```

=== "From Source"

    ```bash
    git clone https://github.com/voicekey/voice-key.git
    cd voice-key
    pip install -e .
    ```

## Initial Setup

### 1. Run the Setup Wizard

```bash
voicekey setup
```

The setup wizard will guide you through:

- [ ] Microphone selection and testing
- [ ] Wake word configuration
- [ ] Global hotkey setup
- [ ] Auto-start preference

### 2. Verify Your Microphone

```bash
voicekey test-microphone
```

This will record a short audio sample and play it back to verify your microphone is working.

### 3. Download Speech Models

```bash
voicekey download-models
```

This downloads the required ASR and VAD models (approximately 100-300 MB depending on profile).

## Basic Usage

### Starting VoiceKey

```bash
# Start with dashboard
voicekey start

# Start in background (tray mode)
voicekey start --daemon
```

### Using VoiceKey

1. **Say the wake phrase**: "voice key"
2. **Speak your text**: The recognized text will be typed automatically
3. **Use commands**: End your command with "command"

### Example Session

```
You: "voice key"
[VoiceKey enters listening mode - tray icon turns green]

You: "Hello world"
[Types: Hello world]

You: "new line command"
[Presses Enter]

You: "pause voice key"
[VoiceKey pauses - tray icon turns blue]
```

## Configuration

### Quick Configuration

```bash
# Set listening mode
voicekey config set listening_mode wake_word

# Set wake phrase
voicekey config set wake_phrase "hey keyboard"

# Set confidence threshold
voicekey config set confidence_threshold 0.7

# View current configuration
voicekey config show
```

### Manual Configuration

Configuration file locations:

- **Linux**: `~/.config/voicekey/config.yaml`
- **Windows**: `%APPDATA%\voicekey\config.yaml`

Example configuration:

```yaml
# ~/.config/voicekey/config.yaml
version: "1.0"

listening:
  mode: wake_word
  wake_phrase: "voice key"
  wake_window_timeout_seconds: 5
  inactive_auto_pause_seconds: 30

asr:
  model_profile: base
  confidence_threshold: 0.5

audio:
  sample_rate: 16000
  chunk_duration: 0.1

hotkeys:
  toggle_listening: "ctrl+shift+v"

autostart:
  enabled: true
  start_minimized: true
```

## Troubleshooting

### Microphone Not Detected

```bash
# List available audio devices
voicekey list-devices

# Test microphone
voicekey test-microphone
```

### Permission Issues

=== "Linux"

    Ensure you have permission to access audio devices:

    ```bash
    # Add user to audio group
    sudo usermod -a -G audio $USER

    # Log out and log back in
    ```

=== "Windows"

    Ensure VoiceKey has microphone permissions in Windows Settings > Privacy > Microphone.

### Model Download Fails

```bash
# Clear model cache and retry
voicekey download-models --force
```

## Next Steps

- Read the [Commands Reference](guide/commands.md) for all available commands
- Configure [Listening Modes](guide/listening-modes.md) to suit your needs
- Explore [Configuration Options](guide/configuration.md) for fine-tuning
- Set up [Auto-start](installation/linux.md#auto-start) for seamless operation

---

Having issues? Check the [Troubleshooting Guide](resources/troubleshooting.md) or [FAQ](resources/faq.md).
