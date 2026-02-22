#!/usr/bin/env bash
#
# VoiceKey Installation Script
# Supports: Linux (Ubuntu 22.04/24.04), Windows
#

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INSTALL_LOG="$SCRIPT_DIR/voicekey_install.log"
SKIP_SYSTEM_DEPS=0

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$INSTALL_LOG"
}

error() {
    echo "[ERROR] $1" | tee -a "$INSTALL_LOG"
    exit 1
}

detect_os() {
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        if command -v apt-get &> /dev/null; then
            echo "linux-apt"
        else
            echo "linux-other"
        fi
    elif [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "cygwin" ]] || [[ "$OSTYPE" == "win32" ]]; then
        echo "windows"
    else
        error "Unsupported operating system: $OSTYPE"
    fi
}

check_python() {
    log "Checking Python installation..."
    
    if command -v python3 &> /dev/null && python3 -m venv --help &> /dev/null; then
        PYTHON_CMD="python3"
    elif command -v python &> /dev/null && python -m venv --help &> /dev/null; then
        PYTHON_CMD="python"
    else
        error "Python not found. Please install Python 3.11+."
    fi
    
    PYTHON_VERSION=$($PYTHON_CMD -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
    PYTHON_MAJOR=$($PYTHON_CMD -c 'import sys; print(sys.version_info[0])')
    PYTHON_MINOR=$($PYTHON_CMD -c 'import sys; print(sys.version_info[1])')
    
    if [[ "$PYTHON_MAJOR" -lt 3 ]] || ([[ "$PYTHON_MAJOR" -eq 3 ]] && [[ "$PYTHON_MINOR" -lt 11 ]]); then
        error "Python 3.11+ required. Found: $PYTHON_VERSION"
    fi
    
    log "Python version: $PYTHON_VERSION"
}

check_linux_deps() {
    # Check for PortAudio - required for audio capture
    if pkg-config --exists portaudio-2.0 2>/dev/null; then
        log "PortAudio is already installed."
        return 0
    fi
    # Also check for the library directly
    if ldconfig -p 2>/dev/null | grep -q "libportaudio"; then
        log "PortAudio library found."
        return 0
    fi
    log "PortAudio not found - will need to install system dependencies."
    return 1
}

install_linux_deps() {
    log "Installing Linux system dependencies..."
    
    if ! command -v sudo &> /dev/null; then
        error "sudo not found. Please install sudo or run as root."
    fi
    
    if check_linux_deps; then
        log "Skipping apt install - all dependencies present."
        return 0
    fi
    
    sudo apt-get update -qq
    
    PYTHON3_VERSION=$(apt-cache search python3.11 python3.12 | grep -oP 'python3\.\d+' | sort -V | tail -1)
    PYTHON3_PKG="python3"
    
    if [ -n "$PYTHON3_VERSION" ]; then
        PYTHON3_PKG="$PYTHON3_VERSION"
    fi
    
    log "Using Python package: $PYTHON3_PKG"
    
    sudo apt-get install -y \
        "$PYTHON3_PKG" \
        "$PYTHON3_PKG"-venv \
        "$PYTHON3_PKG"-dev \
        python3-pip \
        libportaudio2 \
        libasound2-dev \
        portaudio19-dev \
        ffmpeg \
        curl \
        || error "Failed to install system dependencies"
    
    log "Linux system dependencies installed."
}

configure_linux_audio_group() {
    log "Configuring audio group permissions..."
    
    if groups | grep -q "\baudio\b"; then
        log "User is already in audio group."
        return 0
    fi
    
    log "Adding user to audio group..."
    if sudo usermod -a -G audio "$USER" 2>/dev/null; then
        log "User added to audio group. Please log out and back in for changes to take effect."
    else
        log "Warning: Could not add user to audio group. You may need to do this manually:"
        log "  sudo usermod -a -G audio \$USER"
    fi
}

install_windows_deps() {
    log "Checking Windows prerequisites..."
    
    if ! command -v python &> /dev/null; then
        error "Python not found. Please install Python 3.11+ from https://python.org"
    fi
    
    PYTHON_VERSION=$(python -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
    PYTHON_MAJOR=$(python -c 'import sys; print(sys.version_info[0])')
    PYTHON_MINOR=$(python -c 'import sys; print(sys.version_info[1])')
    
    if [[ "$PYTHON_MAJOR" -lt 3 ]] || ([[ "$PYTHON_MAJOR" -eq 3 ]] && [[ "$PYTHON_MINOR" -lt 11 ]]); then
        error "Python 3.11+ required. Found: $PYTHON_VERSION"
    fi
    
    log "Python version: $PYTHON_VERSION"
    
    if ! python -m pip --version &> /dev/null; then
        log "Installing pip..."
        python -m ensurepip --upgrade
    fi
}

create_venv() {
    log "Creating virtual environment..."
    
    if [[ -d ".venv" ]]; then
        log "Virtual environment already exists. Removing..."
        rm -rf .venv
    fi
    
    $PYTHON_CMD -m venv .venv
    
    if [[ "$OS_TYPE" == "windows" ]]; then
        source .venv/Scripts/activate
    else
        source .venv/bin/activate
    fi
    
    log "Upgrading pip..."
    pip install --upgrade pip
    
    log "Virtual environment ready."
}

install_voicekey() {
    log "Installing VoiceKey..."
    
    if [[ "$OS_TYPE" == "linux-apt" ]]; then
        log "Installing CPU-only PyTorch (faster, smaller download)..."
        pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu
    fi
    
    pip install -e . || error "Failed to install VoiceKey"
    
    log "VoiceKey installed successfully."
}

download_models() {
    log "Downloading speech models..."
    
    MODEL_PROFILE="${1:-base}"
    log "Using model profile: $MODEL_PROFILE"
    
    if voicekey download --all 2>&1 | grep -q "success"; then
        log "Models downloaded successfully."
    else
        log "Note: Model download may require internet access on first run."
        log "Faster-Whisper will download models automatically when first used."
    fi
}

run_setup() {
    log "Running VoiceKey setup..."
    
    voicekey setup --skip --autostart || error "Failed to run setup"
    
    log "Setup completed."
}

verify_installation() {
    log "Verifying installation..."
    
    log "Checking available devices..."
    voicekey devices || log "Warning: Could not list devices"
    
    log "Checking status..."
    voicekey status || log "Warning: Could not get status"
    
    log "Installation verified."
}

setup_autostart_linux() {
    log "Setting up autostart..."
    
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
    
    chmod +x ~/.config/autostart/voicekey.desktop
    
    log "Autostart configured (desktop file)."
}

show_usage() {
    cat << USAGE_EOF

================================================================================
                    VoiceKey Installation Complete!
================================================================================

USAGE:
    source .venv/bin/activate
    
    # Start VoiceKey
    voicekey start              # Start with dashboard
    voicekey start --daemon    # Start in background (tray mode)
    
    # Other commands
    voicekey status             # Show runtime status
    voicekey devices            # List microphone devices
    voicekey commands           # List supported commands
    voicekey config --show     # Show configuration
    
    # Configuration
    voicekey config --set listening_mode=wake_word
    voicekey config --set wake_word.phrase="voice key"
    
MODEL PROFILES:
    tiny   - Smallest, fastest (~\`250 MB)
    base   - Good balance (~\`140 MB)  <default>
    small  - Better accuracy (~\`500 MB)

AUTOSTART:
    Autostart has been configured. VoiceKey will start automatically on login.
    To disable: rm ~/.config/autostart/voicekey.desktop

NEXT STEPS:
    1. Log out and log back in (Linux audio group)
    2. Test your microphone: voicekey devices
    3. Say "voice key" to activate
    4. Speak your command - it will be typed automatically
    
    Say "pause voice key" to pause
    Say "resume voice key" to resume

================================================================================
USAGE_EOF
}

main() {
    log "Starting VoiceKey installation..."
    log "Script directory: $SCRIPT_DIR"
    
    cd "$SCRIPT_DIR"
    
    OS_TYPE=$(detect_os)
    log "Detected OS: $OS_TYPE"
    
    MODEL_PROFILE="${VOICEKEY_MODEL:-base}"
    
    if [[ "$OS_TYPE" == "linux-apt" ]]; then
        check_python
        if ! check_linux_deps; then
            install_linux_deps
        fi
        configure_linux_audio_group
    elif [[ "$OS_TYPE" == "windows" ]]; then
        install_windows_deps
    fi
    
    create_venv
    
    if [[ "$OS_TYPE" == "windows" ]]; then
        source .venv/Scripts/activate
    else
        source .venv/bin/activate
    fi
    
    install_voicekey
    
    download_models "$MODEL_PROFILE"
    
    run_setup
    
    if [[ "$OS_TYPE" == "linux-apt" ]]; then
        setup_autostart_linux
    fi
    
    verify_installation
    
    show_usage
    
    log "Installation complete!"
}

main "$@"
