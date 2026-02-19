# Installation from Source

This guide covers installing VoiceKey from source code.

## Prerequisites

### System Dependencies

=== "Linux (Ubuntu)"

    ```bash
    sudo apt update
    sudo apt install -y \
        python3.11 \
        python3.11-venv \
        python3-pip \
        git \
        libportaudio2 \
        libasound2-dev \
        portaudio19-dev
    ```

=== "Windows"

    - [Python 3.11+](https://www.python.org/downloads/windows/)
    - [Git for Windows](https://git-scm.com/download/win)
    - [Visual C++ Redistributable](https://aka.ms/vs/17/release/vc_redist.x64.exe)

### Python Version

```bash
python --version  # Should be 3.11 or higher
```

## Installation Steps

### 1. Clone the Repository

```bash
git clone https://github.com/voicekey/voice-key.git
cd voice-key
```

### 2. Create Virtual Environment

=== "Linux"

    ```bash
    python -m venv .venv
    source .venv/bin/activate
    ```

=== "Windows"

    ```cmd
    python -m venv .venv
    .venv\Scripts\activate
    ```

### 3. Install Dependencies

```bash
# Upgrade pip
python -m pip install -U pip

# Install project dependencies
pip install -e .

# Or with dev dependencies
pip install -e ".[dev]"
pip install -r requirements-dev.txt
```

### 4. Verify Installation

```bash
voicekey --version
```

### 5. Download Models

```bash
voicekey download-models
```

## Development Setup

### Running Tests

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/unit/test_capture.py

# Run with coverage
pytest --cov=voicekey
```

### Code Quality

```bash
# Lint
ruff check voicekey/

# Type check
mypy voicekey/

# Format
ruff format voicekey/
```

### Running in Development Mode

```bash
# Start with development settings
voicekey --verbose start

# Enable debug logging
voicekey --debug start
```

## Project Structure

```
voice-key/
├── voicekey/              # Main source code
│   ├── app/               # Application layer
│   ├── audio/             # Audio capture & VAD
│   ├── commands/         # Command parsing
│   ├── actions/          # Action routing
│   ├── platform/          # Platform backends
│   ├── ui/               # User interfaces
│   ├── config/           # Configuration
│   └── models/           # Model management
├── tests/                 # Test suites
├── docs/                  # Documentation
├── requirements/          # Requirements docs
├── backlog/               # Project backlog
├── pyproject.toml        # Project config
└── README.md             # Project readme
```

## Building Documentation

```bash
# Install mkdocs and dependencies
pip install -r docs/requirements.txt

# Build docs
mkdocs build

# Serve locally
mkdocs serve
```

## Building Distribution Packages

```bash
# Build wheel
python -m build

# Build sdist
python -m build --sdist
```

## Uninstalling

```bash
# Deactivate virtual environment
deactivate

# Remove virtual environment
rm -rf .venv  # Linux
rmdir /s /q .venv  # Windows

# Remove cloned repository
cd ..
rm -rf voice-key
```

## Troubleshooting

### Import Errors

```bash
# Reinstall in development mode
pip install -e .
```

### Missing Dependencies

```bash
# Install all dependencies
pip install -r requirements-dev.txt
```

### Model Download Issues

```bash
# Force redownload
voicekey download-models --force

# Clear cache
rm -rf ~/.cache/voicekey
```

## Next Steps

- [Development Setup](development/setup.md)
- [Testing](development/testing.md)
- [Contributing](development/contributing.md)
