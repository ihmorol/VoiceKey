# Development Setup

This guide covers setting up a development environment for VoiceKey.

## Prerequisites

### System Requirements

| Component | Minimum | Recommended |
|-----------|---------|-------------|
| CPU | Dual-core x64 | Quad-core x64 |
| RAM | 8 GB | 16 GB |
| Storage | 2 GB | 5 GB |
| OS | Ubuntu 22.04/24.04 or Windows 10/11 | Same |

### Required Software

- **Git** — Version control
- **Python 3.11+** — Programming language
- **pip** — Package manager
- **virtualenv** — Virtual environment (or venv)

---

## Quick Start

### 1. Clone the Repository

```bash
git clone https://github.com/voicekey/voice-key.git
cd voice-key
```

### 2. Create Virtual Environment

=== "Linux/macOS"

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

# Install in development mode
pip install -e ".[dev]"

# Or with all platform dependencies
pip install -e ".[all-platforms,dev]"
```

### 4. Verify Installation

```bash
voicekey --version
```

### 5. Run Tests

```bash
pytest tests/unit
```

---

## Project Structure

```
voice-key/
├── voicekey/              # Main source code
│   ├── app/              # Application layer
│   ├── audio/            # Audio capture & VAD
│   ├── commands/         # Command parsing
│   ├── actions/          # Action routing
│   ├── platform/         # Platform backends
│   ├── ui/              # User interfaces
│   ├── config/          # Configuration
│   └── models/          # Model management
├── tests/                 # Test suites
│   ├── unit/            # Unit tests
│   ├── integration/     # Integration tests
│   └── perf/            # Performance tests
├── docs/                  # Documentation
├── requirements/          # Requirements docs
├── backlog/              # Project backlog
├── pyproject.toml        # Project config
└── README.md            # Project readme
```

---

## Development Tools

### Code Quality

```bash
# Lint with ruff
ruff check voicekey/

# Check types with mypy
mypy voicekey/

# Format code
ruff format voicekey/
```

### Pre-commit Hooks

Install pre-commit hooks:

```bash
pip install pre-commit
pre-commit install
```

---

## Running VoiceKey

### Development Mode

```bash
# Start with verbose logging
voicekey --verbose start

# Enable debug logging
voicekey --debug start

# Run in foreground
voicekey start
```

### Testing Specific Features

```bash
# Test audio capture only
python -c "from voicekey.audio.capture import AudioCapture; c = AudioCapture(); c.start()"

# Test VAD
python -c "from voicekey.audio.vad import VADProcessor; v = VADProcessor()"
```

---

## IDE Setup

### VS Code

Create `.vscode/settings.json`:

```json
{
    "python.defaultInterpreterPath": ".venv/bin/python",
    "python.linting.enabled": true,
    "python.linting.ruffEnabled": true,
    "python.formatting.provider": "ruff",
    "editor.formatOnSave": true,
    "editor.rulers": [100]
}
```

### PyCharm

1. Open project
2. Set Python interpreter to `.venv/bin/python`
3. Enable Ruff plugin
4. Set line length to 100

---

## Model Management

### Download Models

```bash
voicekey download-models
```

### Force Re-download

```bash
voicekey download-models --force
```

### Model Cache Location

| Platform | Location |
|----------|----------|
| Linux | `~/.cache/voicekey/models/` |
| Windows | `%LOCALAPPDATA%\voicekey\models\` |

---

## Troubleshooting

### Import Errors

```bash
# Reinstall in editable mode
pip install -e .
```

### Missing Dependencies

```bash
# Install all dependencies
pip install -r requirements-dev.txt
```

### Audio Device Issues

```bash
# List available devices
voicekey list-devices
```

---

## Next Steps

- [Testing](testing.md)
- [Contributing](contributing.md)
