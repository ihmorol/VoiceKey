# VoiceKey Installation Guide

> Version: 1.1
> Date: 2026-02-26

---

## 1. Prerequisites

- Python 3.11+
- microphone input device
- internet connection for first model download and/or cloud ASR endpoint access

Optional:

- FFmpeg for audio-file diagnostics (not required for live mic)

---

## 2. Linux Install

```bash
python -m venv .venv
source .venv/bin/activate
pip install -U pip
pip install voicekey
```

Optional permissions for low-level input fallback:

```bash
sudo usermod -aG input "$USER"
```

Log out/in after group changes.

### 2.1 Linux AppImage (Recommended for non-Python users)

1. Download `voicekey-<version>-linux-x86_64.AppImage`.
2. Make executable: `chmod +x voicekey-<version>-linux-x86_64.AppImage`.
3. Run: `./voicekey-<version>-linux-x86_64.AppImage`.

---

## 3. Windows Install

### 3.1 Signed Installer (Recommended)

1. Download `voicekey-<version>-windows-x64-installer.exe`.
2. Verify signature/checksum.
3. Run installer and select autostart preference.

### 3.2 Python Install (Developer path)

1. Install Python 3.11+.
2. Open PowerShell.
3. Run:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -U pip
pip install voicekey
```

### 3.3 Portable Zip

1. Download `voicekey-<version>-windows-x64-portable.zip`.
2. Extract to any writable folder.
3. Run executable from extracted folder.

---

## 4. First Startup

```bash
voicekey start
```

Expected:

1. model download prompt (local/hybrid mode) or cloud endpoint validation (cloud-primary mode)
2. onboarding wizard
3. tray icon appears

---

## 5. Enable Hybrid ASR (Optional)

```bash
voicekey config --set engine.asr_backend=faster-whisper
voicekey config --set engine.network_fallback_enabled=true
voicekey config --set engine.cloud_api_base=https://api.openai.com/v1
```

Set API key in environment before launch:

```bash
export VOICEKEY_OPENAI_API_KEY="<your-key>"
```

---

## 6. Autostart Setup

Use onboarding or:

```bash
voicekey config --set system.autostart_enabled=true
```

---

## 7. Verify Installation

```bash
voicekey devices
voicekey status
voicekey commands
```

---

## 8. Verify Artifact Integrity

1. Download release checksum file (`SHA256SUMS`).
2. Verify local artifact hash matches published hash.
3. For Windows installer, confirm valid code-signature metadata.

---

*Document Version: 1.1*  
*Last Updated: 2026-02-26*
