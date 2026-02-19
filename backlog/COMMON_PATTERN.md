# Common Pattern for Epics, Stories, and Tasks

Use this exact structure for every backlog item.

---

## 1. Epic Pattern

### Epic Header

- `Epic ID`: E##
- `Title`:
- `Objective`:
- `Priority`: P0/P1/P2
- `Source Requirements`: list of requirement IDs
- `Dependencies`: upstream epic/story IDs

### Epic Definition

- `In Scope`:
- `Out of Scope`:
- `Architecture Notes`:
- `Risks`:
- `Completion Gate`:

---

## 2. Story Pattern

### Story Header

- `Story ID`: E##-S##
- `Title`:
- `Parent Epic`:
- `Priority`:
- `Requirement IDs`:
- `Dependency Stories`:

### Story Contract

- `Context`: why this story exists
- `Inputs`: files/interfaces/data/events required
- `Outputs`: exact deliverables
- `Behavior Rules`: explicit rules; no implied behavior
- `Edge Cases`: must-handle edge scenarios
- `Non-goals`: explicit exclusions

### Acceptance Criteria

- AC-1 ...
- AC-2 ...
- AC-3 ...

### Validation Evidence

- required tests
- runtime verification commands
- logs/metrics/proof artifacts

---

## 3. Task Pattern

### Task Header

- `Task ID`: E##-S##-T##
- `Title`:
- `Owner Role`: Builder/Guardian/Operator/etc.
- `Estimate`: XS/S/M/L

### Task Contract

- `Preconditions`:
- `Implementation Steps` (ordered, deterministic)
- `Files to Modify/Create`:
- `Failure Handling`:
- `Done When`:

---

## 4. Requirement Coverage Rule

Each story must map to at least one requirement ID.

Each requirement ID must map to:

1. at least one story,
2. at least one acceptance criterion,
3. at least one test or verification method.

Any requirement without all three is considered not implemented.

---

## 5. Anti-Ambiguity Rule

If behavior is not explicitly defined in requirements:

1. do not implement speculative behavior,
2. create a clarification ticket,
3. block only the ambiguous sub-scope, continue all non-blocked work.
