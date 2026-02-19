# AGENTS.md
Repository instructions for agentic coding contributors.

## 1) Repository State
- This repository is currently requirements-first.
- Core implementation source files are planned; docs are authoritative now.
- Do not invent behavior beyond documented requirements.

## 2) Source of Truth (Strict Order)
1. `software_requirements.md`
2. `architecture.md`
3. `requirements/*.md`
4. `backlog/BACKLOG_MASTER.md`
5. `backlog/TRACEABILITY_MATRIX.md`
6. `backlog/EXECUTION_RULES.md`

If docs conflict, follow (1) and (2), then raise a clarification item.

## 3) Cursor/Copilot Rules
- `.cursor/rules/` not found.
- `.cursorrules` not found.
- `.github/copilot-instructions.md` not found.
If these appear later, merge their constraints into this file.

## 4) Environment Setup
Linux/macOS shell:
```bash
python -m venv .venv
source .venv/bin/activate
pip install -U pip
pip install -r requirements-dev.txt
```
Windows PowerShell:
```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -U pip
pip install -r requirements-dev.txt
```

## 5) Build / Lint / Test Commands
Note: full build/lint toolchain is still being finalized; CI enforces checks.

### Tests
Run all tests:
```bash
pytest
```
Run suites:
```bash
pytest tests/unit
pytest tests/integration
pytest tests/perf
```
Run a single test file:
```bash
pytest tests/unit/test_parser.py
```
Run a single test function:
```bash
pytest tests/unit/test_parser.py::test_unknown_command_literal_fallback
```
Run by keyword:
```bash
pytest -k "resume and paused" tests/unit
```
Stop fast on first failure:
```bash
pytest -x
```

### Lint/Format/Type
- Required by CI, but local tool names/config files are not finalized here yet.
- If introducing Ruff/Black/Mypy (or alternatives), update this file with exact commands.

### Release Build
- Release artifacts are created by tag-triggered CI pipeline.
- Follow `requirements/devops-cicd.md`, `requirements/distribution.md`, and `requirements/release-checklist.md`.

## 6) Python Style Guidelines

### Imports
- Absolute imports for project modules.
- Order: stdlib -> third-party -> local.
- No wildcard imports.

### Formatting
- Follow PEP 8.
- Prefer small, composable functions.
- Keep hot-path logic allocation-light.

### Typing
- Type hints required for public functions/methods.
- Prefer explicit return types.
- Use structured models (dataclass/Pydantic) for payloads.
- Avoid `Any` unless justified.

### Naming
- `snake_case`: variables, functions, modules.
- `PascalCase`: classes.
- `UPPER_SNAKE_CASE`: constants.
- Keep state/event names aligned with `architecture.md`.

### Error Handling
- Never swallow exceptions silently.
- Raise/convert to typed domain errors at subsystem boundaries.
- Provide actionable user-facing messages.
- Preserve safety invariants (fallback to paused when uncertain/unsafe).

### Logging and Privacy
- Never log raw microphone audio.
- Never log raw transcript by default.
- Respect redaction rules from `requirements/security.md`.

## 7) Domain Rules (Must Preserve)
- Unknown `... command` input must type literally.
- `pause voice key` / `resume voice key` behavior must match requirements.
- In paused state, dictation is disabled; only approved resume control channels remain.
- P1 features (`window_commands`, `text_expansion`) remain disabled by default until P1 completion.

## 8) Verification and Quality Rules
- Each story/task change must include tests and acceptance evidence.
- Map implemented behavior to requirement IDs in PR/task notes.
- Run perf tests when changing ASR/parser/hot path behavior.
- Release-related changes must pass full release checklist.

## 9) Backlog Update Rule (Mandatory)
After each completed meaningful task:
1. Update backlog status/details (`backlog/BACKLOG_MASTER.md` or tracking section).
2. Update `backlog/TRACEABILITY_MATRIX.md` if coverage changed.
3. Record verification commands/evidence in backlog work log.

## 10) Commit Rule for This Project
Project policy: commit after every meaningful change.
- Keep commits small, scoped, and atomic.
- Tie commit messages to story/task IDs where possible.
- Do not batch unrelated changes.

## 11) Clarification Protocol
Ask questions only when ambiguity materially changes behavior.
When asking, include:
- conflicting references,
- recommended default,
- impact of each option.

## 12) Release/Platform Baseline
- License: MIT.
- Contribution policy: DCO required, CLA not required.
- Supported release targets: Windows 10/11 x64, Ubuntu 22.04/24.04 x64.
- Wayland support is best-effort with explicit user warnings.
