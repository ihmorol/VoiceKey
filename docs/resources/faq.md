# Frequently Asked Questions

Find answers to common questions about VoiceKey.

## General

### What is VoiceKey?

VoiceKey is a privacy-first, offline voice-to-keyboard application for Linux and Windows. It captures microphone audio, recognizes speech in real-time, and emits keyboard input into the currently focused window.

### Is VoiceKey free?

Yes! VoiceKey is open source under the MIT license. You can use it for free, modify it, and distribute it.

### How is my data handled?

VoiceKey is **100% offline**. Your voice data never leaves your computer. All speech recognition happens locally on your machine.

### Does VoiceKey send data to the cloud?

No. VoiceKey does not send any audio or text data to external servers. There's no cloud API, no telemetry, and no cloud processing.

---

## Installation

### What are the system requirements?

| Component | Minimum | Recommended |
|-----------|---------|-------------|
| OS | Ubuntu 22.04/24.04 or Windows 10/11 | Same |
| CPU | Dual-core x64 | Quad-core x64 |
| RAM | 4 GB | 8 GB |
| Python | 3.11+ | 3.11+ |

### How do I install VoiceKey?

```bash
pip install voicekey
```

See [Installation Guide](../installation/index.md) for detailed instructions.

### Can I use VoiceKey on macOS?

Not at this time. VoiceKey currently supports only Linux and Windows.

---

## Usage

### How do I start VoiceKey?

```bash
voicekey start
```

Or for background (tray) mode:

```bash
voicekey start --daemon
```

### What is the wake phrase?

The default wake phrase is "voice key". Say this to activate listening mode.

You can change it in the configuration:

```bash
voicekey config set listening.wake_phrase "hey keyboard"
```

### Why isn't VoiceKey typing my text?

Check these things:

1. **Microphone** — Ensure it's working: `voicekey test-microphone`
2. **Wake phrase** — Did you say the wake phrase first?
3. **Confidence threshold** — Try lowering it: `voicekey config set asr.confidence_threshold 0.3`
4. **Focus** — Is the target window focused?

### How do I pause VoiceKey?

Say "pause voice key" (no wake phrase needed) or press the toggle hotkey (Ctrl+Shift+V).

---

## Commands

### How do commands work?

Speak a command ending with "command" to trigger an action:

- "new line command" → Presses Enter
- "control c command" → Presses Ctrl+C

### What if VoiceKey doesn't recognize a command?

If a command isn't recognized, VoiceKey types the literal text. Nothing is silently dropped.

### Can I create custom commands?

Yes! Add custom commands in your configuration:

```yaml
commands:
  - trigger: "email command"
    action: type_text
    text: "user@example.com"
```

---

## Performance

### VoiceKey is slow / has high latency

Try these fixes:

1. **Use smaller model**: `voicekey config set asr.model_profile tiny`
2. **Reduce VAD threshold**: `voicekey config set vad.threshold 0.3`
3. **Close other audio apps**: Reduce system load

### High CPU usage

- Use `tiny` model profile instead of `small`
- Enable VAD to skip silent audio
- Close other applications

### Memory usage is too high

- Use `tiny` model (39MB vs 244MB)
- Reduce queue size in audio settings
- Check for memory leaks with long sessions

---

## Privacy & Security

### Is VoiceKey safe to use?

Yes. VoiceKey:
- ✅ Works completely offline
- ✅ Doesn't send data to the cloud
- ✅ Doesn't log audio or transcripts
- ✅ Verifies model checksums

### Can VoiceKey record my conversations?

No. VoiceKey only processes audio in real-time and doesn't store any audio or transcript data.

---

## Troubleshooting

### "No microphone found"

```bash
# List available devices
voicekey list-devices

# Test microphone
voicekey test-microphone
```

### "Permission denied" for microphone

=== "Linux"

    ```bash
    # Add user to audio group
    sudo usermod -a -G audio $USER
    # Log out and back in
    ```

=== "Windows"

    1. Go to Settings > Privacy > Microphone
    2. Enable microphone access
    3. Find VoiceKey and enable it

### "Keyboard injection failed"

- Run VoiceKey as administrator (Windows)
- Check that no other app has keyboard focus
- Try the fallback keyboard backend

### VoiceKey crashes on startup

Check the logs:

```bash
voicekey --debug start
```

Look for error messages and check the [Troubleshooting Guide](troubleshooting.md).

---

## Development

### How can I contribute?

See our [Contributing Guide](../development/contributing.md). We welcome:

- Bug reports
- Feature requests
- Code contributions
- Documentation improvements

### Can I use VoiceKey in my project?

Yes, VoiceKey is MIT licensed. You can integrate it into other projects.

---

## Contact & Support

### Where can I get help?

- **GitHub Issues** — For bugs and features
- **GitHub Discussions** — For questions
- **Discord** — Join our community

### How do I report a bug?

Use the GitHub Issue tracker with the bug template. Include:
- Your OS and version
- VoiceKey version
- Steps to reproduce
- Error messages

---

Still have questions? Open an issue on GitHub!
