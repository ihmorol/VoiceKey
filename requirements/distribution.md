# VoiceKey Distribution Specification

> Version: 1.2
> Date: 2026-02-26

---

## 1. Distribution Goals

- predictable installs for non-technical users
- verifiable artifacts for security-conscious users
- multi-channel delivery without feature drift

---

## 2. Release Channels

| Channel | Artifacts | Install Path |
|---------|-----------|--------------|
| PyPI | wheel + sdist | `pip install voicekey` |
| Windows | signed installer + portable zip | installer wizard or unzip/run |
| Linux | AppImage + pip | executable AppImage or pip |

Supported architecture for public releases: x64 only.

---

## 3. Artifact Naming Convention

Examples:

- `voicekey-<version>-cp311-cp311-win_amd64.whl` (if platform wheel required)
- `voicekey-<version>-py3-none-any.whl` (only if truly pure-python)
- `voicekey-<version>-windows-x64-installer.exe`
- `voicekey-<version>-windows-x64-portable.zip`
- `voicekey-<version>-linux-x86_64.AppImage`

---

## 4. Artifact Integrity

Each release must include:

1. checksums file (`SHA256SUMS`)
2. detached signature for release artifact set (including `SHA256SUMS`)
3. SBOM document (CycloneDX JSON)
4. release notes with breaking changes and migration notes
5. artifact manifest with commit hash and build environment metadata

---

## 5. Model Distribution Policy

- Models are not bundled in core app installers.
- First run either downloads required local model profile or validates configured cloud endpoint (for cloud-primary mode).
- `voicekey download` supports prefetch/offline preparation for local and hybrid modes.
- Every model archive must pass checksum before activation.
- At least one fallback model mirror must be supported.
- Cloud backend onboarding must validate API key and endpoint reachability before runtime start.

---

## 6. Backward Compatibility

- semantic versioning for CLI and config behavior
- explicit migration notes for config schema updates
- one previous major version migration path supported

---

## 7. Operational Risks and Controls

| Risk | Control |
|------|---------|
| oversized installers | external model strategy |
| corrupted releases | checksums + signature verification |
| channel drift | single release pipeline and manifest |
| missing runtime deps | post-build install smoke matrix |
| model host outage | mirrored model source + retry strategy |
| cloud api outage/rate-limit | hybrid fallback to local path + bounded retry and user warning |

---

*Document Version: 1.2*  
*Last Updated: 2026-02-26*
