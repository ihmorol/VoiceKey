# Execution Rules (No Hallucination Implementation)

These rules are mandatory for agents and developers implementing VoiceKey.

---

## 1. Scope Control

- Implement only stories/tasks listed in `BACKLOG_MASTER.md`.
- If a needed behavior is missing from backlog/requirements, open a clarification item first.
- Do not silently introduce new commands, modes, or default values.

---

## 2. Contract-First Development

- Define interfaces and schemas before implementation.
- Add tests before or alongside implementation for each acceptance criterion.
- Never merge a story without requirement ID linkage.

---

## 3. Safe Defaults

- Respect current defaults in requirements/configuration docs.
- P1 feature flags (`window_commands`, `text_expansion`) remain disabled by default until their epic completion gate is passed.

---

## 4. Deterministic Verification

For each story, provide:

1. unit/integration/perf test evidence (as applicable),
2. reproducible command(s) used for verification,
3. explicit pass/fail outcome.

---

## 5. Change Management

- Any modification that affects requirement behavior must update:
  - backlog story acceptance criteria,
  - traceability matrix,
  - related requirement docs.

---

## 6. Release Safety

- Public release work must satisfy `requirements/release-checklist.md`.
- CI/CD and signing/provenance steps are not optional for release tags.

---

## 7. Clarification Protocol

Ask for clarification only when the ambiguity changes implementation behavior materially.

When asking, include:

- conflicting references,
- recommended default,
- impact if choosing each option.
