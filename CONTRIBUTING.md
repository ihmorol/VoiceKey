# Contributing to VoiceKey

Thank you for your interest in contributing to VoiceKey! This document outlines the contribution process and guidelines for the project.

## Code of Conduct

Please read and follow our [Code of Conduct](CODE_OF_CONDUCT.md). We are committed to providing a welcoming and inclusive experience for everyone.

## Getting Started

### Development Environment Setup

```bash
# Clone the repository
git clone https://github.com/voicekey/voice-key.git
cd voice-key

# Create virtual environment
python -m venv .venv

# Activate virtual environment
# Linux/macOS:
source .venv/bin/activate
# Windows:
.venv\Scripts\Activate.ps1

# Install dependencies
pip install -U pip
pip install -r requirements-dev.txt
```

### Prerequisites

- Python 3.10+
- PortAudio (for audio capture on Linux)
- A working microphone

## Contribution Workflow

1. **Open an Issue**: Before starting work, please open an issue for bugs, features, or proposals.
2. **Create a Branch**: Create a feature branch from `main`.
3. **Make Changes**: Implement your changes following our coding standards.
4. **Add Tests**: Ensure all new functionality includes appropriate tests.
5. **Submit PR**: Push your changes and submit a pull request linked to the issue.
6. **CI Checks**: All CI checks must pass before review.
7. **Maintainer Review**: A maintainer will review and merge your PR.

## DCO Sign-Off Requirement

**All contributions must include a DCO (Developer Certificate of Origin) sign-off.**

By contributing to VoiceKey, you agree to the following:

> Developer's Certificate of Origin 1.1
> 
> By making a contribution to this project, I certify that:
> 
> (a) The contribution was created in whole or in part by me and I have the right to submit it under the open source license indicated in the file; or
> 
> (b) The contribution is based upon previous work that, to the best of my knowledge, is covered under an appropriate open source license and I have the right under that license to submit that work with modifications, whether created in whole or in part by me, under the same open source license (unless I am permitted to submit under a different license), as indicated in the file; or
> 
> (c) The contribution was provided directly to me by some other person who certified (a), (b) or (c) and I have not modified it.
> 
> (d) I understand and agree that this project and the contribution are public and that a record of the contribution (including all personal information I submit with it, including my sign-off) is maintained indefinitely and may be redistributed consistent with this project or the open source license(s) involved.

### How to Sign Your Work

Add a line to every commit message:

```
Signed-off-by: Your Name <your.email@example.com>
```

You can use `git commit -s` to automatically add the sign-off line:

```bash
git commit -s -m "Your commit message"
```

## Testing Requirements

All contributions must pass tests before being merged.

### Running Tests

```bash
# Run all tests
pytest

# Run unit tests only
pytest tests/unit

# Run integration tests
pytest tests/integration

# Run performance tests
pytest tests/perf

# Run a specific test file
pytest tests/unit/test_parser.py

# Run a specific test function
pytest tests/unit/test_parser.py::test_unknown_command_literal_fallback
```

### Test Standards

- All new code must include unit tests
- Integration tests are required for system-level functionality
- Performance tests are required for ASR/parser hot path changes
- Tests must be deterministic and not depend on external services
- Do not log raw microphone audio or transcripts in tests

## Coding Standards

### Python Style

- Follow PEP 8
- Use type hints for all public functions and methods
- Prefer explicit return types
- Use dataclasses/Pydantic for structured payloads

### Naming Conventions

- `snake_case`: variables, functions, modules
- `PascalCase`: classes
- `UPPER_SNAKE_CASE`: constants

### Performance Guidelines

- Keep hot path allocations low
- Avoid blocking in audio callback thread
- Keep parser deterministic and testable
- Run perf tests before submitting ASR or parser changes

## Documentation

- Update inline documentation for new features
- Update user-facing documentation if behavior changes
- Include docstrings for all public functions

## Dependency Policy

- New runtime dependencies require license compatibility review
- All dependencies must be open source and compatible with MIT license
- Run dependency vulnerability scans before adding new dependencies

## Pull Request Guidelines

- Keep PRs small and focused
- Include a clear description of changes
- Link to related issues
- Update CHANGELOG.md for user-facing changes
- Ensure all CI checks pass
- Add appropriate labels

## Issue Guidelines

- Use the provided issue templates
- Include reproduction steps for bugs
- Include clear feature descriptions for enhancements
- Check existing issues before creating duplicates

## License

By contributing to VoiceKey, you agree that your contributions will be licensed under the [MIT License](LICENSE).

---

*Last Updated: 2026-02-19*
