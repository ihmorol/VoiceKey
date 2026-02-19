# Installation Guide

VoiceKey supports Linux and Windows platforms. Choose your platform below for detailed installation instructions.

## System Requirements

### Hardware Requirements

| Component | Minimum | Recommended |
|-----------|---------|-------------|
| CPU | Dual-core x64 | Quad-core x64 |
| RAM | 4 GB | 8 GB |
| Storage | 500 MB | 1 GB (plus models) |
| Microphone | Built-in or USB | External with noise cancellation |

### Software Requirements

| Component | Linux | Windows |
|-----------|-------|---------|
| OS | Ubuntu 22.04/24.04 LTS | Windows 10/11 |
| Architecture | x64 | x64 |
| Python | 3.11+ | 3.11+ |
| Desktop | X11/Wayland | - |

## Pre-installation Checklist

- [ ] Python 3.11 or higher installed
- [ ] Microphone connected and working
- [ ] Internet connection (for initial model download)
- [ ] Sufficient permissions for audio device access

## Installation Methods

=== "pip (Recommended)"

    The easiest way to install VoiceKey:

    ```bash
    pip install voicekey
    ```

    For Linux-specific dependencies:

    ```bash
    pip install voicekey[linux]
    ```

    For all dependencies:

    ```bash
    pip install voicekey[all-platforms]
    ```

=== "AppImage (Linux)"

    1. Download the latest AppImage from [Releases](https://github.com/voicekey/voice-key/releases)
    2. Make it executable:

    ```bash
    chmod +x VoiceKey-*.AppImage
    ```

    3. Run it:

    ```bash
    ./VoiceKey-*.AppImage
    ```

=== "From Source"

    ```bash
    # Clone the repository
    git clone https://github.com/voicekey/voice-key.git
    cd voice-key

    # Create virtual environment
    python -m venv .venv
    source .venv/bin/activate  # Linux
    # .venv\Scripts\activate  # Windows

    # Install dependencies
    pip install -U pip
    pip install -r requirements-dev.txt
    pip install -e .
    ```

## Platform-Specific Setup

### Linux

See [Linux Installation](linux.md) for detailed setup instructions including:

- System dependencies (PortAudio, audio group)
- X11/Wayland considerations
- Auto-start configuration

### Windows

See [Windows Installation](windows.md) for detailed setup instructions including:

- Visual C++ Redistributable
- Microphone permissions
- Auto-start configuration

## Post-Installation

### 1. Verify Installation

```bash
voicekey --version
```

### 2. Run Setup Wizard

```bash
voicekey setup
```

### 3. Download Models

```bash
voicekey download-models
```

### 4. Test Installation

```bash
voicekey start
```

## Troubleshooting

### Python Version

Check your Python version:

```bash
python --version
```

If you have Python 3.11+, proceed. Otherwise, install a newer version:

=== "Linux (pyenv)"

    ```bash
    # Install pyenv
    curl https://pyenv.run | bash

    # Install Python 3.11
    pyenv install 3.11.0

    # Set as global
    pyenv global 3.11.0
    ```

=== "Windows"

    Download from [python.org](https://www.python.org/downloads/windows/)

### Missing Dependencies

If you encounter missing dependency errors:

```bash
# Reinstall with all dependencies
pip install --force-reinstall voicekey[all-platforms]
```

## Upgrading

### pip Upgrade

```bash
pip install --upgrade voicekey
```

### AppImage Upgrade

Download the latest version from [Releases](https://github.com/voicekey/voice-key/releases)

## Uninstallation

=== "pip"

    ```bash
    pip uninstall voicekey
    ```

=== "AppImage"

    Simply delete the AppImage file.

=== "Source"

    ```bash
    rm -rf /path/to/voice-key
    ```

## Next Steps

- [Linux Setup](linux.md)
- [Windows Setup](windows.md)
- [Getting Started](../getting-started.md)
- [Configuration](../guide/configuration.md)
