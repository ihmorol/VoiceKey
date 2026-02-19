# VoiceKey Development Guide

> Version: 1.0
> Date: 2026-02-19

---

## 1. Local Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -U pip
pip install -r requirements-dev.txt
```

---

## 2. Project Standards

- keep hot path allocations low
- avoid blocking in audio callback thread
- keep parser deterministic and testable
- never log raw transcript by default

---

## 3. Module Ownership

| Module | Responsibility |
|--------|----------------|
| `audio/*` | capture + vad + wake + ASR integration |
| `commands/*` | parsing and registry |
| `actions/*` | text/key/window dispatch |
| `platform/*` | OS adapters |
| `ui/*` | cli/tray/dashboard/onboarding |
| `config/*` | schema, migration, persistence |

---

## 4. Required Test Commands

```bash
pytest
pytest tests/unit
pytest tests/integration
python scripts/ci/check_perf_guardrails.py --metrics-file tests/perf/metrics_baseline.json
```
Optional performance suite (when present):
```bash
pytest tests/perf
```

---

## 5. Performance Regression Policy

- every ASR or parser change should run perf guardrail checks
- fail build if p50 latency regresses > 15%
- fail build if memory baseline regresses > 20%

---

## 6. Contribution Checklist

1. tests added/updated
2. docs updated
3. compatibility impact noted
4. performance impact measured

---

## 7. Release Engineering Expectations

- follow semantic versioning
- update changelog entry for user-facing changes
- ensure packaging impact is noted in PR description
- ensure no new dependency is added without license compatibility check

---

*Document Version: 1.0*  
*Last Updated: 2026-02-19*
