# Linux Installation

This guide covers VoiceKey installation on Linux (Ubuntu 22.04/24.04).

## System Dependencies

### Required Packages

Install the required system dependencies:

```bash
# Update package list
sudo apt update

# Install system dependencies
sudo apt install -y \
    python3.11 \
    python3.11-venv \
    python3-pip \
    libportaudio2 \
    libasound2-dev \
    portaudio19-dev
```

### Audio Group

Add your user to the audio group to access audio devices:

```bash
sudo usermod -a -G audio $USER
```

!!! warning "Log out required"
    You must log out and log back in for the group change to take effect.

## Installation

### Method 1: pip (Recommended)

```bash
pip install voicekey[linux]
```

### Method 2: From Source

```bash
# Clone repository
git clone https://github.com/voicekey/voice-key.git
cd voice-key

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -U pip
pip install -e .[linux]
```

## Desktop Environment Support

### X11 (Recommended)

VoiceKey works best with X11. Most Ubuntu installations use X11 by default.

To verify your session type:

```bash
echo $XDG_SESSION_TYPE
```

### Wayland (Best Effort)

Wayland support is best-effort with explicit warnings. Some features may not work:

- Global hotkeys may not function
- Window control commands may be limited

To check if you're using Wayland:

```bash
echo $XDG_SESSION_TYPE  # Should output "wayland"
```

!!! warning "Wayland Limitations"
    On Wayland, consider using toggle mode instead of wake word mode for more reliable operation.

## Auto-start Configuration

### Method 1: .desktop File (Recommended)

Create a desktop entry file:

```bash
mkdir -p ~/.config/autostart

cat > ~/.config/autostart/voicekey.desktop << 'EOF'
[Desktop Entry]
Type=Application
Name=VoiceKey
Comment=Privacy-first offline voice-to-keyboard
Exec=voicekey start --daemon
Icon=voicekey
Terminal=false
Categories=Utility;
EOF
```

### Method 2: systemd User Service

Create a systemd service:

```bash
mkdir -p ~/.config/systemd/user

cat > ~/.config/systemd/user/voicekey.service << 'EOF'
[Unit]
Description=VoiceKey - Offline Voice-to-Keyboard
After=default.target

[Service]
Type=simple
ExecStart=voicekey start --daemon
Restart=on-failure

[Install]
WantedBy=default.target
EOF
```

Enable the service:

```bash
systemctl --user enable voicekey.service
systemctl --user start voicekey.service
```

## Permissions

### Input Device Access

For keyboard injection, you may need additional permissions:

```bash
# For pynput (primary method)
# Usually no additional setup needed

# For evdev fallback (low-level input)
sudo apt install -y evdev
sudo chmod +r /dev/input/event*
```

### Troubleshooting Permissions

If you get permission errors:

```bash
# Check audio group
groups $USER

# List audio devices
ls -la /dev/audio*
```

## X11 Specific Configuration

### Keyboard Injection

VoiceKey uses pynput for keyboard injection. On X11, this should work out of the box.

If keyboard injection fails:

```bash
# Install python-xlib if needed
pip install python-xlib
```

### Global Hotkeys

Global hotkeys work on X11 using the `python-xlib` or `keyboard` backend.

## Testing

### Verify Installation

```bash
voicekey --version
```

### Test Microphone

```bash
voicekey test-microphone
```

### List Devices

```bash
voicekey list-devices
```

### Start VoiceKey

```bash
voicekey start
```

## Common Issues

### "No module named 'portaudio'"

```bash
sudo apt install -y portaudio19-dev
pip install --force-reinstall sounddevice
```

### "Permission denied" for audio device

```bash
# Verify audio group membership
groups $USER

# If not in audio group, re-add
sudo usermod -a -G audio $USER

# Log out and log back in
```

### "Cannot connect to X11"

```bash
# Check DISPLAY variable
echo $DISPLAY

# If empty, ensure X11 is running
```

### "Failed to acquire keyboard"

This usually happens when another application has keyboard focus. Ensure VoiceKey is running and try again.

## Uninstallation

```bash
pip uninstall voicekey

# Remove autostart
rm ~/.config/autostart/voicekey.desktop

# Remove systemd service
rm ~/.config/systemd/user/voicekey.service
```

## Next Steps

- [Getting Started](../getting-started.md)
- [Configuration](../guide/configuration.md)
- [Commands Reference](../guide/commands.md)
