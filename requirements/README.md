# VoiceKey Requirements Documentation

This folder contains the implementation-ready specification set for VoiceKey.

---

## 1. Core Documents

| File | Purpose |
|------|---------|
| `../software_requirements.md` | Product requirements and acceptance criteria |
| `../architecture.md` | System architecture and runtime design |

---

## 2. Supporting Specifications

| File | Purpose |
|------|---------|
| `analysis.md` | Conflict resolution and gap closure summary |
| `recommendations.md` | Prioritized strategic direction |
| `configuration.md` | Canonical config model and validation rules |
| `commands.md` | Command behavior contract |
| `risk-assessment.md` | Risk register and mitigation playbook |
| `installation.md` | Installation and verification steps |
| `onboarding.md` | First-run wizard requirements |
| `troubleshooting.md` | Known issues and fixes |
| `development.md` | Contributor implementation guide |
| `security.md` | Security and privacy controls |
| `testing-strategy.md` | Test matrix and benchmark gates |
| `implementation-plan.md` | Phased delivery plan |
| `distribution.md` | Packaging channels and artifact policy |
| `devops-cicd.md` | CI/CD requirements and branch protections |
| `open-source-governance.md` | OSS process, licensing, security disclosure |
| `release-checklist.md` | Release readiness and publish checklist |

---

## 3. Recommended Reading Order

1. `../software_requirements.md`
2. `../architecture.md`
3. `configuration.md`
4. `commands.md`
5. `risk-assessment.md`
6. `testing-strategy.md`
7. `implementation-plan.md`
8. `distribution.md`
9. `devops-cicd.md`
10. `open-source-governance.md`
11. `release-checklist.md`

---

## 4. Finalized Product Decisions

- ASR engine: faster-whisper
- pause/resume phrases work without wake phrase
- continuous mode kept with inactivity auto-pause safety
- tray + autostart + onboarding included in core baseline

---

*Last Updated: 2026-02-19*
