# VoiceKey Release Checklist

> Version: 1.2
> Date: 2026-02-26

---

## Pre-release

- [ ] version bumped
- [ ] changelog updated
- [ ] migration notes prepared (if needed)
- [ ] all required CI checks green
- [ ] benchmark gate passed
- [ ] release tag is signed and verified

## Build and Verify

- [ ] artifacts built for all channels
- [ ] checksums generated
- [ ] signatures attached (including signed checksum file)
- [ ] SBOM generated (CycloneDX JSON)
- [ ] provenance attestation attached
- [ ] install smoke tests passed (Linux + Windows)
- [ ] hybrid ASR smoke tests passed (local-only, hybrid fallback, cloud-primary credential validation)

## Publish

- [ ] GitHub release created with notes
- [ ] PyPI artifacts published
- [ ] Windows artifacts published
- [ ] Linux AppImage published

## Post-release

- [ ] validate fresh install from public channels
- [ ] update compatibility matrix
- [ ] monitor issue tracker for regressions
- [ ] rollback/yank decision logged if regressions are critical

---

*Document Version: 1.2*  
*Last Updated: 2026-02-26*
