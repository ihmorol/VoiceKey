# VoiceKey Incident Response Runbook

> Version: 1.0  
> Date: 2026-02-20  
> Requirement: `requirements/security.md` section 6

---

## Overview

This document provides the incident response procedure for VoiceKey security events and unexpected behavior.

---

## Incident Response Checklist

If unexpected typing or other anomalous behavior is observed:

### Step 1: Pause Voice Input Immediately

```bash
voice key stop
```

Or use the pause hotkey: `Ctrl+Shift+P`

**Verification**: Check that the tray icon shows "paused" state or the dashboard shows state: "paused".

### Step 2: Export Redacted Diagnostics

```bash
voicekey diagnostics --export ./incident-diagnostics.json
```

**Important**: Do NOT use `--full` flag unless specifically required. The default redacted export is safe to share.

The redacted export will:
- Include system information (OS, Python version)
- Include redacted configuration summary
- Include runtime state
- **Exclude** raw audio data
- **Exclude** transcript history
- **Exclude** user directory paths
- **Exclude** any potential secrets

### Step 3: Disable Autostart Until Resolved

Edit configuration to disable autostart:

```bash
voicekey config --set system.autostart_enabled=false
```

Or manually edit the config file and set:
```yaml
system:
  autostart_enabled: false
```

### Step 4: Report the Incident

1. **Security Issues**: Report to security@voicekey.dev (or the security contact defined in SECURITY.md)
2. **General Issues**: Open an issue at https://github.com/voicekey/voicekey/issues

Include in your report:
- The redacted diagnostics file
- Description of the unexpected behavior
- Steps to reproduce (if known)
- Approximate time of incident

---

## Vulnerability Response SLA

Per `requirements/security.md` section 4.1:

| Severity | Response Time |
|----------|---------------|
| Acknowledgment | Within 72 hours |
| Triage Update | Within 7 calendar days |
| High/Critical Remediation | Target 30 days (or publish exception rationale) |

---

## Security Controls Reference

VoiceKey implements the following security controls to prevent and detect incidents:

### Data Handling

| Control | Status |
|---------|--------|
| Raw microphone audio not persisted | ✓ Default |
| Transcript logging disabled by default | ✓ Default |
| Debug mode redacts transcripts | ✓ Default |
| No runtime cloud transmission | ✓ After model download |

### Threat Mitigation

| Threat | Mitigation |
|--------|------------|
| Accidental speech capture | Wake phrase + inactivity auto-pause |
| Injected malicious phrases | Pause mode + visible state indicators |
| Tampered model files | Checksum verification |
| Config poisoning | Schema validation + fallback defaults |

### User Safety Controls

| Control | Command |
|---------|---------|
| Immediate pause | `pause voice key` (spoken) |
| Hard stop | `voice key stop` (spoken) |
| Tray status indicator | Always visible |
| Pause hotkey | `Ctrl+Shift+P` |

---

## Diagnostics Export Safety

### Default (Redacted) Export

Safe to share. Includes:
- System info (OS, Python version, architecture)
- Redacted config summary (feature flags, privacy settings)
- Runtime state
- Redacted file paths

Does NOT include:
- Raw audio
- Transcripts
- User directory paths (show as `[HOME]`, `[USER]`, etc.)
- Secrets or credentials

### Full Export (Use with Caution)

Only use when specifically requested by maintainers:

```bash
voicekey diagnostics --full --export ./full-diagnostics.json
```

**Warning**: Full export may contain sensitive information. Only share with trusted parties.

---

## Recovery After Incident

Once the issue is resolved:

1. Update to the latest VoiceKey version
2. Re-enable autostart if desired:
   ```bash
   voicekey config --set system.autostart_enabled=true
   ```
3. Resume normal operation:
   ```bash
   voicekey start
   ```

---

## Contact

- Security issues: See `SECURITY.md` for disclosure process
- General support: https://github.com/voicekey/voicekey/issues
- Documentation: `docs/` directory

---

*Document Version: 1.0*  
*Last Updated: 2026-02-20*
