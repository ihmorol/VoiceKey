# Troubleshooting

This guide helps you diagnose and fix common issues with VoiceKey.

## Diagnostic Commands

### Check VoiceKey Status

```bash
voicekey status
```

### View Logs

```bash
# With debug output
voicekey --debug start
```

### List Audio Devices

```bash
voicekey list-devices
```

### Test Microphone

```bash
voicekey test-microphone
```

---

## Common Issues

### Microphone Issues

#### No Microphone Found

**Symptoms:**
- "No audio device found" error
- Microphone not listed in devices

**Solutions:**

1. Check microphone is connected
2. List all devices:
   ```bash
   voicekey list-devices
   ```
3. Set specific device:
   ```bash
   voicekey config set audio.device 1
   ```

#### Microphone Permission Denied

**Symptoms:**
- "Permission denied" error
- Cannot access microphone

**Solutions:**

=== "Linux"

```bash
# Add user to audio group
sudo usermod -a -G audio $USER

# Log out and log back in
```

=== "Windows"

1. Open **Settings** > **Privacy** > **Microphone**
2. Enable **Microphone access**
3. Enable VoiceKey specifically

#### Microphone Already in Use

**Symptoms:**
- "Audio device is busy" error

**Solutions:**
1. Close other apps using microphone (Zoom, Discord, etc.)
2. Restart VoiceKey

---

### Audio Issues

#### Audio Dropouts / Choppy Audio

**Symptoms:**
- Incomplete transcription
- Words missing from dictation

**Solutions:**

1. **Reduce system load**: Close other applications
2. **Use better microphone**: USB microphone recommended
3. **Reduce chunk duration**:
   ```bash
   voicekey config set audio.chunk_duration 0.05
   ```
4. **Increase queue size**:
   ```bash
   voicekey config set audio.queue_size 64
   ```

#### High Latency

**Symptoms:**
- Delay between speaking and text appearing

**Solutions:**

1. **Use smaller model**:
   ```bash
   voicekey config set asr.model_profile tiny
   ```
2. **Lower confidence threshold**:
   ```bash
   voicekey config set asr.confidence_threshold 0.3
   ```
3. **Reduce VAD threshold**:
   ```bash
   voicekey config set vad.threshold 0.3
   ```

---

### Keyboard Injection Issues

#### Keys Not Being Typed

**Symptoms:**
- VoiceKey recognizes speech but doesn't type

**Solutions:**

=== "Linux"

1. Check permissions:
   ```bash
   groups $USER
   ```
2. Try evdev backend:
   ```python
   # In config.yaml
   platform:
     keyboard_backend: evdev
   ```

=== "Windows"

1. Run as administrator
2. Check UAC settings
3. Try pywin32 backend:
   ```python
   platform:
     keyboard_backend: pywin32
   ```

#### Some Keys Don't Work

**Symptoms:**
- Modifier keys (Ctrl, Alt) not working

**Solutions:**

1. Run as administrator
2. Check target application compatibility
3. Try different keyboard backend

---

### Wake Word Issues

#### False Triggers

**Symptoms:**
- VoiceKey activates without wake phrase

**Solutions:**

1. **Increase VAD threshold**:
   ```bash
   voicekey config set vad.threshold 0.7
   ```
2. **Use toggle mode instead**:
   ```bash
   voicekey config set listening.mode toggle
   ```

#### No Response to Wake Word

**Symptoms:**
- Wake phrase not detected

**Solutions:**

1. **Lower VAD threshold**:
   ```bash
   voicekey config set vad.threshold 0.3
   ```
2. **Lower confidence threshold**:
   ```bash
   voicekey config set asr.confidence_threshold 0.3
   ```
3. **Use a clearer microphone**
4. **Speak louder and more clearly**

---

### Installation Issues

#### Python Not Found

**Symptoms:**
- "python not found" error

**Solutions:**

=== "Linux"

```bash
# Install Python
sudo apt install python3.11 python3-pip
```

=== "Windows"

Download from [python.org](https://www.python.org/downloads/windows/)

#### Module Import Errors

**Symptoms:**
- "ModuleNotFoundError" errors

**Solutions:**

```bash
# Reinstall dependencies
pip install -e .
```

#### Permission Errors

**Symptoms:**
- "Permission denied" during install

**Solutions:**

```bash
# Use --user flag
pip install --user voicekey

# Or use virtual environment
python -m venv .venv
source .venv/bin/activate
pip install voicekey
```

---

### Model Issues

#### Model Download Fails

**Symptoms:**
- "Failed to download model" error

**Solutions:**

1. **Check internet connection**
2. **Clear cache and retry**:
   ```bash
   voicekey download-models --force
   ```
3. **Check disk space** (need ~500MB)

#### Model Checksum Error

**Symptoms:**
- "Model checksum failed" error

**Solutions:**

```bash
# Force re-download
voicekey download-models --force
```

---

### Performance Issues

#### High CPU Usage

**Symptoms:**
- VoiceKey uses too much CPU

**Solutions:**

1. **Use smaller model**:
   ```bash
   voicekey config set asr.model_profile tiny
   ```
2. **Enable VAD**:
   ```bash
   voicekey config set vad.enabled true
   ```
3. **Reduce sample rate** (advanced):
   ```bash
   voicekey config set audio.sample_rate 8000
   ```

#### High Memory Usage

**Symptoms:**
- VoiceKey uses too much RAM

**Solutions:**

1. Use `tiny` model
2. Restart VoiceKey periodically
3. Check for memory leaks in logs

---

### Crash Issues

#### VoiceKey Crashes on Startup

**Debug steps:**

1. Run with debug logging:
   ```bash
   voicekey --debug start
   ```
2. Check error message
3. Try fresh config:
   ```bash
   mv ~/.config/voicekey/config.yaml ~/.config/voicekey/config.yaml.bak
   voicekey setup
   ```

#### Crash During Use

1. Check logs for error messages
2. Note steps to reproduce
3. Report issue on GitHub

---

## Getting Help

If these solutions don't work:

1. **Check GitHub Issues** — Search for similar problems
2. **Enable debug logging** — `voicekey --debug start`
3. **Collect information**:
   - OS and version
   - VoiceKey version (`voicekey --version`)
   - Error messages
   - Steps to reproduce
4. **Open an issue** — Include all collected information

---

## Reset to Defaults

If all else fails, reset VoiceKey:

```bash
# Backup config
cp ~/.config/voicekey/config.yaml ~/voicekey-config-backup.yaml

# Reset config
voicekey config reset

# Re-run setup
voicekey setup
```
