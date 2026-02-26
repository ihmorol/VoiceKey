# VoiceKey Security and Privacy Specification

> Version: 1.2
> Date: 2026-02-26

---

## 1. Security Principles

1. privacy by default
2. least data retention
3. explicit user control
4. secure local configuration

---

## 2. Data Handling Rules

- raw microphone audio must not be persisted by default
- recognized text must not be logged by default
- debug mode must redact transcript unless user explicitly disables redaction
- no runtime cloud transmission by default after model download
- cloud transcription may run only when explicitly enabled by user configuration

---

## 3. Threat Scenarios

| Threat | Mitigation |
|--------|------------|
| accidental speech capture | wake phrase + inactivity auto-pause |
| injected malicious phrases nearby | pause mode + visible state indicators |
| tampered model files | checksum verification |
| config poisoning | schema validation + fallback defaults |

---

## 4. Security Controls

- signed release artifacts (required for public releases)
- checksum file for model and package releases
- local process lock to prevent duplicate service conflicts
- bounded retry loops to prevent runaway states

---

## 4.1 Vulnerability Response SLA

- acknowledge reports within 72 hours
- provide triage update within 7 calendar days
- target remediation within 30 days for high/critical issues, or publish exception rationale

---

## 5. User-visible Safety Controls

- `pause voice key` immediate stop
- tray status indicator always visible
- `voice key stop` hard stop command

---

## 6. Incident Response Guidance

If unexpected typing is observed:

1. pause voice input immediately
2. export redacted diagnostics
3. disable autostart until resolved

---

*Document Version: 1.2*  
*Last Updated: 2026-02-26*
