#!/usr/bin/env bash
#
# VoiceKey Installation Script
# Supports: Linux, macOS, Windows (Git Bash)
#

set -Eeuo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INSTALL_LOG="$SCRIPT_DIR/voicekey_install.log"

ASSUME_YES=0
SKIP_SYSTEM_DEPS=0
SKIP_MODEL_DOWNLOAD=0
SKIP_SETUP=0
ENABLE_AUTOSTART=0
FORCE_RECREATE_VENV=0
MODEL_PROFILE="${VOICEKEY_MODEL:-base}"
VENV_PATH=".venv"
PYTHON_OVERRIDE=""
OS_TYPE=""
PYTHON_CMD=""

log() {
    local message="$1"
    printf '[%s] %s\n' "$(date '+%Y-%m-%d %H:%M:%S')" "$message" | tee -a "$INSTALL_LOG"
}

warn() {
    local message="$1"
    printf '[WARN] %s\n' "$message" | tee -a "$INSTALL_LOG"
}

fatal() {
    local message="$1"
    printf '[ERROR] %s\n' "$message" | tee -a "$INSTALL_LOG"
    exit 1
}

usage() {
    cat <<'USAGE_EOF'
Usage: ./install.sh [options]

Options:
  -y, --yes                Run non-interactively where possible
  --skip-system-deps       Skip OS package installation
  --skip-model-download    Skip model download step
  --skip-setup             Skip `voicekey setup --skip`
  --autostart              Enable autostart during setup
  --model-profile PROFILE  ASR profile to prefetch: tiny|base|small (default: base)
  --venv-path PATH         Virtualenv path (default: .venv)
  --python CMD             Python command/path to use
  --force-recreate-venv    Recreate virtualenv if it already exists
  -h, --help               Show this help
USAGE_EOF
}

confirm() {
    local prompt="$1"
    if [[ "$ASSUME_YES" -eq 1 ]]; then
        return 0
    fi

    local response
    read -r -p "$prompt [y/N]: " response
    [[ "$response" =~ ^[Yy]$ ]]
}

require_command() {
    local cmd="$1"
    command -v "$cmd" >/dev/null 2>&1 || fatal "Required command not found: $cmd"
}

parse_args() {
    while [[ $# -gt 0 ]]; do
        case "$1" in
            -y|--yes)
                ASSUME_YES=1
                ;;
            --skip-system-deps)
                SKIP_SYSTEM_DEPS=1
                ;;
            --skip-model-download)
                SKIP_MODEL_DOWNLOAD=1
                ;;
            --skip-setup)
                SKIP_SETUP=1
                ;;
            --autostart)
                ENABLE_AUTOSTART=1
                ;;
            --model-profile)
                shift
                [[ $# -gt 0 ]] || fatal "--model-profile requires a value"
                MODEL_PROFILE="$1"
                ;;
            --venv-path)
                shift
                [[ $# -gt 0 ]] || fatal "--venv-path requires a value"
                VENV_PATH="$1"
                ;;
            --python)
                shift
                [[ $# -gt 0 ]] || fatal "--python requires a value"
                PYTHON_OVERRIDE="$1"
                ;;
            --force-recreate-venv)
                FORCE_RECREATE_VENV=1
                ;;
            -h|--help)
                usage
                exit 0
                ;;
            *)
                fatal "Unknown option: $1"
                ;;
        esac
        shift
    done
}

detect_os() {
    local uname_s
    uname_s="$(uname -s 2>/dev/null || true)"

    case "$uname_s" in
        Linux*)
            if command -v apt-get >/dev/null 2>&1; then
                OS_TYPE="linux-apt"
            else
                OS_TYPE="linux"
            fi
            ;;
        Darwin*)
            OS_TYPE="macos"
            ;;
        MINGW*|MSYS*|CYGWIN*)
            OS_TYPE="windows"
            ;;
        *)
            fatal "Unsupported operating system: ${uname_s:-unknown}"
            ;;
    esac

    log "Detected OS: $OS_TYPE"
}

resolve_python() {
    log "Checking Python installation..."

    if [[ -n "$PYTHON_OVERRIDE" ]]; then
        PYTHON_CMD="$PYTHON_OVERRIDE"
    else
        local candidates=()
        if [[ "$OS_TYPE" == "windows" ]]; then
            candidates=(python py python3)
        else
            candidates=(python3 python)
        fi

        local candidate
        for candidate in "${candidates[@]}"; do
            if command -v "$candidate" >/dev/null 2>&1 && "$candidate" -m venv --help >/dev/null 2>&1; then
                PYTHON_CMD="$candidate"
                break
            fi
        done
    fi

    [[ -n "$PYTHON_CMD" ]] || fatal "Python 3.11+ with venv support is required."

    local py_version
    py_version="$($PYTHON_CMD -c 'import sys; print(".".join(map(str, sys.version_info[:3])))')"
    local py_major
    py_major="$($PYTHON_CMD -c 'import sys; print(sys.version_info[0])')"
    local py_minor
    py_minor="$($PYTHON_CMD -c 'import sys; print(sys.version_info[1])')"

    if [[ "$py_major" -lt 3 ]] || [[ "$py_major" -eq 3 && "$py_minor" -lt 11 ]]; then
        fatal "Python 3.11+ required. Found: $py_version"
    fi

    log "Using Python: $PYTHON_CMD ($py_version)"
}

install_linux_deps() {
    if [[ "$SKIP_SYSTEM_DEPS" -eq 1 ]]; then
        log "Skipping Linux system dependency installation (--skip-system-deps)."
        return
    fi

    if [[ "$OS_TYPE" != "linux-apt" ]]; then
        warn "Apt-based dependency installation skipped (non-apt Linux)."
        warn "Install manually: libportaudio2 portaudio19-dev libasound2-dev ffmpeg"
        return
    fi

    local deps=(python3-venv python3-pip libportaudio2 portaudio19-dev libasound2-dev ffmpeg)
    local missing=()
    local dep

    for dep in "${deps[@]}"; do
        if ! dpkg -s "$dep" >/dev/null 2>&1; then
            missing+=("$dep")
        fi
    done

    if [[ "${#missing[@]}" -eq 0 ]]; then
        log "All Linux dependencies are already installed."
        return
    fi

    log "Missing Linux packages: ${missing[*]}"

    if ! confirm "Install missing packages using apt-get?"; then
        fatal "Cannot continue without required system dependencies."
    fi

    local sudo_cmd=()
    if [[ "$EUID" -ne 0 ]]; then
        require_command sudo
        sudo_cmd=(sudo)
    fi

    "${sudo_cmd[@]}" apt-get update -qq
    "${sudo_cmd[@]}" apt-get install -y "${missing[@]}"
    log "Linux dependencies installed."
}

install_macos_deps() {
    if [[ "$SKIP_SYSTEM_DEPS" -eq 1 ]]; then
        log "Skipping macOS system dependency installation (--skip-system-deps)."
        return
    fi

    if [[ "$OS_TYPE" != "macos" ]]; then
        return
    fi

    if ! command -v brew >/dev/null 2>&1; then
        warn "Homebrew not found. Install manually: portaudio ffmpeg"
        return
    fi

    local deps=(portaudio ffmpeg)
    local missing=()
    local dep

    for dep in "${deps[@]}"; do
        if ! brew list --formula "$dep" >/dev/null 2>&1; then
            missing+=("$dep")
        fi
    done

    if [[ "${#missing[@]}" -eq 0 ]]; then
        log "All macOS dependencies are already installed."
        return
    fi

    log "Missing Homebrew packages: ${missing[*]}"

    if ! confirm "Install missing packages using Homebrew?"; then
        fatal "Cannot continue without required system dependencies."
    fi

    brew install "${missing[@]}"
    log "macOS dependencies installed."
}

create_or_activate_venv() {
    local venv_abs
    if [[ "$VENV_PATH" = /* ]]; then
        venv_abs="$VENV_PATH"
    else
        venv_abs="$SCRIPT_DIR/$VENV_PATH"
    fi

    if [[ -d "$venv_abs" && "$FORCE_RECREATE_VENV" -eq 1 ]]; then
        log "Removing existing virtualenv: $venv_abs"
        rm -rf "$venv_abs"
    fi

    if [[ ! -d "$venv_abs" ]]; then
        log "Creating virtualenv: $venv_abs"
        "$PYTHON_CMD" -m venv "$venv_abs"
    else
        log "Reusing existing virtualenv: $venv_abs"
    fi

    local activate_path
    if [[ "$OS_TYPE" == "windows" ]]; then
        activate_path="$venv_abs/Scripts/activate"
    else
        activate_path="$venv_abs/bin/activate"
    fi

    [[ -f "$activate_path" ]] || fatal "Virtualenv activation script missing: $activate_path"

    # shellcheck disable=SC1090
    source "$activate_path"

    log "Upgrading pip/setuptools/wheel..."
    if ! python -m pip install --upgrade pip setuptools wheel; then
        warn "Could not upgrade pip/setuptools/wheel (possibly offline). Continuing with existing tooling."
    fi
}

install_voicekey() {
    log "Installing VoiceKey package from source..."
    if ! python -m pip install -e "$SCRIPT_DIR"; then
        warn "Editable install with build isolation failed. Retrying with --no-build-isolation..."
        if ! python -m pip install -e "$SCRIPT_DIR" --no-build-isolation; then
            fatal "VoiceKey package installation failed. Check network/dependency availability and retry."
        fi
    fi
    log "VoiceKey installed."
}

download_models() {
    if [[ "$SKIP_MODEL_DOWNLOAD" -eq 1 ]]; then
        log "Skipping model download (--skip-model-download)."
        return
    fi

    case "$MODEL_PROFILE" in
        tiny|base|small)
            ;;
        *)
            warn "Unknown model profile '$MODEL_PROFILE'. Falling back to 'base'."
            MODEL_PROFILE="base"
            ;;
    esac

    log "Downloading model profile '$MODEL_PROFILE' and VAD artifacts..."
    if ! voicekey download --asr "$MODEL_PROFILE" --vad; then
        warn "Model download failed. VoiceKey can still run and download on first use."
    fi
}

run_setup() {
    if [[ "$SKIP_SETUP" -eq 1 ]]; then
        log "Skipping onboarding setup (--skip-setup)."
        return
    fi

    log "Running setup with safe defaults..."
    if [[ "$ENABLE_AUTOSTART" -eq 1 ]]; then
        voicekey setup --skip --autostart
    else
        voicekey setup --skip --no-autostart
    fi
    log "Setup completed."
}

verify_installation() {
    log "Verifying VoiceKey installation..."

    voicekey --help >/dev/null
    voicekey commands >/dev/null

    if ! voicekey status >/dev/null; then
        warn "Status check reported an issue. See $INSTALL_LOG for details."
    fi

    if ! voicekey devices >/dev/null; then
        warn "Device probe failed. Confirm microphone permissions and audio backend dependencies."
    fi

    log "Verification complete."
}

print_summary() {
    local activate_cmd
    if [[ "$OS_TYPE" == "windows" ]]; then
        activate_cmd="source ${VENV_PATH}/Scripts/activate"
    else
        activate_cmd="source ${VENV_PATH}/bin/activate"
    fi

    cat <<SUMMARY_EOF

================================================================================
VoiceKey installation finished
================================================================================

Next steps:
1. Activate environment:
   $activate_cmd
2. Run VoiceKey in terminal mode:
   voicekey start --foreground
3. Optional background startup contract:
   voicekey start --daemon

Useful checks:
- voicekey status
- voicekey devices
- voicekey commands

Log file:
$INSTALL_LOG

================================================================================
SUMMARY_EOF
}

main() {
    : > "$INSTALL_LOG"
    parse_args "$@"

    log "Starting VoiceKey installation in: $SCRIPT_DIR"
    cd "$SCRIPT_DIR"

    detect_os
    resolve_python

    install_linux_deps
    install_macos_deps

    create_or_activate_venv
    install_voicekey
    run_setup
    download_models
    verify_installation
    print_summary

    log "Installation complete."
}

main "$@"
