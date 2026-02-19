# VoiceKey Delivery Backlog

This folder contains the implementation backlog for VoiceKey.

It is designed to prevent assumption-driven development by providing:

- a strict epic/story/task pattern
- explicit acceptance criteria for each story
- requirement-to-backlog traceability with 100% coverage
- dependency ordering and execution rules for agents/developers

---

## Files

- `COMMON_PATTERN.md`: mandatory template for epics, stories, and tasks
- `BACKLOG_MASTER.md`: full implementation backlog (epics -> stories -> tasks)
- `TRACEABILITY_MATRIX.md`: mapping from every requirement to backlog items/tests
- `EXECUTION_RULES.md`: anti-hallucination implementation protocol
- `WORK_LOG.md`: completed-task evidence and updates log

---

## How to Use

1. Start from `BACKLOG_MASTER.md` in epic order.
2. For each story, implement only what is in scope.
3. Validate against story acceptance criteria and linked tests.
4. Confirm requirement coverage in `TRACEABILITY_MATRIX.md`.
5. Mark completion only when required evidence is produced.

---

## Source of Truth Inputs

This backlog is derived from:

- `software_requirements.md`
- `architecture.md`
- all files under `requirements/`

No behavior outside those docs should be implemented unless requirements are updated first.
