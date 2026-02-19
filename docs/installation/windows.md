# Windows Installation

This guide covers VoiceKey installation on Windows 10/11.

## System Requirements

### Hardware Requirements

| Component | Minimum | Recommended |
|-----------|---------|-------------|
| CPU | Dual-core x64 | Quad-core x64 |
| RAM | 4 GB | 8 GB |
| Storage | 500 MB | 1 GB (plus models) |
| Microphone | Built-in or USB | External with noise cancellation |

### Software Requirements

- Windows 10 version 1903 or later / Windows 11
- Python 3.11 or higher

## Installation

### Method 1: pip (Recommended)

```powershell
pip install voicekey[windows]
```

### Method 2: From Source

```powershell
# Clone repository
git clone https://github.com/voicekey/voice-key.git
cd voice-key

# Create virtual environment
python -m venv .venv
.venv\Scripts\Activate

# Install dependencies
python -m pip install -U pip
pip install -e .[windows]
```

## Prerequisites

### Visual C++ Redistributable

VoiceKey may require the Visual C++ Redistributable. Install it from:

- [Microsoft Visual C++ 2015-2022 Redistributable](https://aka.ms/vs/17/release/vc_redist.x64.exe)

### Microphone Permissions

1. Open **Settings** > **Privacy & Security** > **Microphone**
2. Enable **Microphone access**
3. Find VoiceKey and enable microphone access

!!! warning "Microphone Access Required"
    VoiceKey cannot function without microphone access. Please ensure it's enabled.

## Auto-start Configuration

### Method 1: Startup Folder

```powershell
# Create a shortcut in the startup folder
$shell = New-Object -ComObject WScript.Shell
$shortcut = $shell.CreateShortcut("$env:APPDATA\Microsoft\Windows\Start Menu\Programs\Startup\VoiceKey.lnk")
$shortcut.TargetPath = "voicekey"
$shortcut.Arguments = "start --daemon"
$shortcut.Save()
```

### Method 2: Registry

```powershell
# Add to registry (run as Administrator)
$regPath = "HKCU:\Software\Microsoft\Windows\CurrentVersion\Run"
Set-ItemProperty -Path $regPath -Name "VoiceKey" -Value "voicekey start --daemon"
```

### Method 3: Task Scheduler

```powershell
# Create scheduled task
$action = New-ScheduledTaskAction -Execute "voicekey" -Argument "start --daemon"
$trigger = New-ScheduledTaskTrigger -AtLogOn
Register-ScheduledTask -Action $action -Trigger $trigger -TaskName "VoiceKey" -Description "VoiceKey - Offline Voice-to-Keyboard"
```

## Running VoiceKey

### From Command Prompt

```cmd
voicekey start
```

### From PowerShell

```powershell
voicekey start --daemon
```

### From GUI

1. Double-click the VoiceKey shortcut
2. VoiceKey will appear in the system tray

## Admin Mode

Some features may require administrator privileges:

- Injecting keystrokes into elevated applications
- Accessing certain system APIs

To run in admin mode:

1. Right-click the VoiceKey shortcut
2. Select **Run as administrator**

!!! tip "Recommended Setup"
    For best compatibility, run VoiceKey as administrator, especially if you need to type into applications that run elevated.

## Windows Security

### Antivirus Considerations

Windows Defender or other antivirus software may flag VoiceKey as suspicious because it:

- Captures audio input
- Injects keyboard events

To exclude VoiceKey from scanning:

1. Open **Windows Security** > **Virus & threat protection**
2. Go to **Virus & threat protection settings**
3. Add exclusions:
   - `%APPDATA%\voicekey`
   - `C:\path\to\voicekey` (install location)

### Firewall

VoiceKey does not require network access for normal operation. All speech recognition happens locally.

## Testing

### Verify Installation

```cmd
voicekey --version
```

### Test Microphone

```cmd
voicekey test-microphone
```

### List Devices

```cmd
voicekey list-devices
```

### Start VoiceKey

```cmd
voicekey start
```

## Common Issues

### "Microphone access denied"

1. Open **Settings** > **Privacy & Security** > **Microphone**
2. Enable **Microphone access**
3. Find VoiceKey and enable it

### "Python not found"

Add Python to PATH:

1. Open **System Properties** > **Advanced** > **Environment Variables**
2. Edit **Path** and add Python directory (e.g., `C:\Python311`)

### "Permission denied" for keyboard injection

Run VoiceKey as administrator, or:
1. Open **User Account Control (UAC)**
2. Lower the slider to "Never notify"

### "Application failed to initialize"

Install Visual C++ Redistributable:

```powershell
# Download and install
Invoke-WebRequest -Uri "https://aka.ms/vs/17/release/vc_redist.x64.exe" -OutFile vc_redist.x64.exe
.\vc_redist.x64.exe
```

### High CPU Usage

- Reduce ASR model profile to "tiny"
- Close other applications using the microphone
- Increase VAD sensitivity

## Uninstallation

```cmd
pip uninstall voicekey

# Remove startup entry
Remove-Item "$env:APPDATA\Microsoft\Windows\Start Menu\Programs\Startup\VoiceKey.lnk"

# Remove registry entry
Remove-ItemProperty -Path "HKCU:\Software\Microsoft\Windows\CurrentVersion\Run" -Name "VoiceKey"
```

## Next Steps

- [Getting Started](../getting-started.md)
- [Configuration](../guide/configuration.md)
- [Commands Reference](../guide/commands.md)
