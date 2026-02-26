# VoiceKey

VoiceKey is a privacy-first, offline-first voice-to-keyboard tool for Linux and Windows.

## Prerequisites

- Python `3.11+`
- A working microphone
- Internet access for initial model download (local/offline mode remains default after download)

Linux packages commonly required for microphone support:

```bash
sudo apt-get install -y libportaudio2 portaudio19-dev libasound2-dev ffmpeg
```

## Quick Install (Source)

```bash
git clone https://github.com/your-org/voice-key.git
cd voice-key
./install.sh -y
source .venv/bin/activate
```

Useful installer flags:

- `--skip-system-deps`
- `--skip-model-download`
- `--skip-setup`
- `--autostart`
- `--model-profile tiny|base|small`

## Manual Install

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -U pip setuptools wheel
python -m pip install -e .
```

Windows PowerShell (developer install):

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -U pip setuptools wheel
python -m pip install -e .
```

## Run / Verify

```bash
voicekey --help
voicekey status
voicekey devices
voicekey start --foreground
```

Background mode contract:

```bash
voicekey start --daemon
```

Optional cloud transcription fallback is explicit opt-in in config. Local ASR remains default.

## Documentation

- Project docs: `docs/index.md`
- Requirements: `software_requirements.md`
- Architecture: `architecture.md`
- Security policy: `SECURITY.md`

## Release Cadence

- Target release cadence: monthly patch release window.
