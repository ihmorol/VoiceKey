# Security Policy

VoiceKey is a privacy-first, offline voice-to-keyboard application. We take security seriously and appreciate responsible disclosure of vulnerabilities.

## Supported Versions

We currently support the following versions with security updates:

| Version | Supported          |
| ------- | ------------------ |
| 1.x.x   | :white_check_mark: |

As new versions are released, older versions may be marked as unsupported. Please use the latest stable release.

## Reporting a Vulnerability

### Responsible Disclosure Policy

We follow a responsible disclosure policy. We request that you:

1. **Do not** publicly disclose the vulnerability until we have had an opportunity to address it
2. **Do not** exploit the vulnerability beyond what is necessary to verify the issue
3. **Do not** access or modify data beyond what is necessary to demonstrate the vulnerability

### Contact Channel

Please report security vulnerabilities through **one** of the following methods:

- **Email**: security@voicekey.dev (preferred)
- **GitHub Security Advisories**: Use the [private vulnerability report](https://github.com/voicekey/voice-key/security/advisories/new) feature

Please include the following in your report:

- Description of the vulnerability
- Steps to reproduce the issue
- Potential impact of the vulnerability
- Any suggested remediation (if known)

### What to Expect

We are committed to responding to security reports in a timely manner. Here is our service level agreement (SLA):

| Stage                  | SLA                         |
|------------------------|-----------------------------|
| Acknowledgement        | Within 72 hours            |
| Triage Update          | Within 7 calendar days     |
| Remediation (High/Critical) | Within 30 days        |
| Remediation (Medium/Low)   | Within 90 days        |

### Severity Classification

- **Critical**: Immediate risk of data loss, system compromise, or significant user impact
- **High**: Significant risk requiring urgent attention
- **Medium**: Moderate risk with workarounds available
- **Low**: Minor risk with minimal impact

### Disclosure

Once the vulnerability has been addressed, we will:

1. Publish a security advisory on GitHub
2. Credit the reporter (unless you prefer to remain anonymous)
3. Include remediation details in the release notes

## Security Best Practices

### For Users

- Keep VoiceKey updated to the latest version
- Only download VoiceKey from official sources (GitHub, PyPI)
- Review permissions granted to VoiceKey
- Use the pause feature when not in use

### For Contributors

- Never log raw microphone audio or transcripts
- Follow secure coding practices
- Run security vulnerability scans before adding dependencies
- Report any security concerns immediately

## Security-Related Categories

VoiceKey handles sensitive data (voice input). The following are considered security-relevant:

- Unauthorized audio capture or exfiltration
- Privilege escalation vulnerabilities
- Input validation issues that could lead to code execution
- Credential or API key exposure
- Dependency vulnerabilities

## Thank You

We appreciate your efforts to responsibly disclose security vulnerabilities. Your help keeps VoiceKey and its users safe.

---

*Last Updated: 2026-02-19*
