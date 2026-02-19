# Contributing

Thank you for your interest in contributing to VoiceKey! This guide will help you get started.

## Code of Conduct

By participating in this project, you agree to abide by our [Code of Conduct](https://github.com/voicekey/voice-key/blob/main/CODE_OF_CONDUCT.md).

---

## Getting Started

### 1. Fork the Repository

```bash
# Fork on GitHub, then clone your fork
git clone https://github.com/YOUR_USERNAME/voice-key.git
cd voice-key
```

### 2. Set Up Development Environment

```bash
# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # Linux/macOS
# .venv\Scripts\activate  # Windows

# Install dependencies
pip install -e ".[dev,all-platforms]"
```

### 3. Create a Branch

```bash
# Create feature branch
git checkout -b feature/my-awesome-feature

# Or bugfix branch
git checkout -b fix/issue-description
```

---

## Contribution Types

### 🐛 Bug Reports

Use GitHub Issues with the `bug` template:

```markdown
## Description
A clear description of the bug

## Steps to Reproduce
1. Go to '...'
2. Click on '...'
3. See error

## Expected Behavior
What should happen

## Actual Behavior
What actually happens

## Environment
- OS: Ubuntu 22.04
- VoiceKey version: 0.1.0
- Python version: 3.11
```

### 💡 Feature Requests

Use GitHub Issues with the `feature` template:

```markdown
## Feature Description
Clear description of the feature

## Use Case
Why this feature is needed

## Proposed Solution
How you think it should work

## Alternatives
Other solutions you've considered
```

### 🔧 Pull Requests

1. **Before starting work**, check existing issues and PRs
2. **Create an issue** to discuss large changes
3. **Keep PRs small and focused** — one feature or fix per PR
4. **Write tests** for new functionality
5. **Update documentation** as needed

---

## Development Workflow

### 1. Make Changes

```bash
# Make your changes to the code
# Follow coding standards (see below)
```

### 2. Run Tests

```bash
# Run tests
pytest tests/unit

# Run linting
ruff check voicekey/

# Run type checking
mypy voicekey/
```

### 3. Commit Changes

Follow the commit message format:

```
<type>(<scope>): <description>

[optional body]

[optional footer]
```

Types:
- `feat` — New feature
- `fix` — Bug fix
- `docs` — Documentation
- `style` — Formatting
- `refactor` — Code refactoring
- `test` — Tests
- `chore` — Maintenance

Examples:

```
feat(audio): add audio capture callback support

fix(parser): handle unknown commands by typing literally

docs(readme): update installation instructions
```

### 4. Push and Create PR

```bash
git push origin feature/my-awesome-feature
```

Then open a Pull Request on GitHub.

---

## Coding Standards

### Python Style

- Follow PEP 8
- Use **Black** formatting (line length: 100)
- Use type hints
- Use absolute imports

### Import Order

```python
# Standard library
import os
import sys

# Third-party
import pytest
import sounddevice

# Local
from voicekey.audio.capture import AudioCapture
```

### Naming

- **Functions/Variables**: `snake_case`
- **Classes**: `PascalCase`
- **Constants**: `UPPER_SNAKE_CASE`

### Documentation

- Use docstrings for public APIs
- Keep docstrings concise but descriptive
- Include type hints in signatures

```python
def process_audio(audio: np.ndarray, sample_rate: int) -> AudioFrame:
    """Process raw audio into an AudioFrame.
    
    Args:
        audio: Raw PCM audio samples
        sample_rate: Sample rate in Hz
        
    Returns:
        Processed AudioFrame
    """
```

---

## Commit Sign-off (DCO)

VoiceKey requires Developer Certificate of Origin (DCO) sign-off.

### Sign-off on Commit

```bash
git commit -s -m "feat: add new feature"
```

The `-s` flag adds a `Signed-off-by` line:

```
Signed-off-by: Your Name <your@email.com>
```

### Corporate Contributors

If you're contributing on behalf of a company:

```
Signed-off-by: Company Name <company@email.com>
```

---

## Pull Request Checklist

Before submitting:

- [ ] Tests pass (`pytest tests/unit`)
- [ ] Linting passes (`ruff check`)
- [ ] Type checking passes (`mypy`)
- [ ] New code has docstrings
- [ ] Documentation updated if needed
- [ ] Commits are signed off (DCO)
- [ ] PR description explains the changes

---

## Recognition

Contributors will be recognized in:

- CONTRIBUTORS.md file
- Release notes
- GitHub Contributors page

---

## Getting Help

- **GitHub Discussions** — For questions
- **Discord** — Join our community
- **Issue Tracker** — For bugs and features

---

## Thank You!

Your contributions make VoiceKey better for everyone. We appreciate your time and effort!
