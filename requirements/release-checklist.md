# VoiceKey Release Checklist

> Version: 1.0
> Date: 2026-02-19

---

## Pre-release

- [ ] version bumped
- [ ] changelog updated
- [ ] migration notes prepared (if needed)
- [ ] all required CI checks green
- [ ] benchmark gate passed

## Build and Verify

- [ ] artifacts built for all channels
- [ ] checksums generated
- [ ] signatures attached
- [ ] SBOM generated
- [ ] install smoke tests passed (Linux + Windows)

## Publish

- [ ] GitHub release created with notes
- [ ] PyPI artifacts published
- [ ] Windows artifacts published
- [ ] Linux AppImage published

## Post-release

- [ ] validate fresh install from public channels
- [ ] update compatibility matrix
- [ ] monitor issue tracker for regressions

---

*Document Version: 1.0*  
*Last Updated: 2026-02-19*
