# VoiceKey Distribution Specification

> Version: 1.0
> Date: 2026-02-19

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

---

## 3. Artifact Naming Convention

Examples:

- `voicekey-<version>-py3-none-any.whl`
- `voicekey-<version>-windows-x64-installer.exe`
- `voicekey-<version>-windows-x64-portable.zip`
- `voicekey-<version>-linux-x86_64.AppImage`

---

## 4. Artifact Integrity

Each release must include:

1. checksums file (`SHA256SUMS`)
2. signature metadata
3. SBOM document
4. release notes with breaking changes and migration notes

---

## 5. Model Distribution Policy

- Models are not bundled in core app installers.
- First run downloads required model profile.
- `voicekey download` supports prefetch/offline preparation.
- Every model archive must pass checksum before activation.

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

---

*Document Version: 1.0*  
*Last Updated: 2026-02-19*
