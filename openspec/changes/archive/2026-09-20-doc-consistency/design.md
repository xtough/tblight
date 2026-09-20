# Design

## Context

See proposal.md — Why. Three documentation files describe overlapping material without a
shared canonical ordering or cross-references, and several small errors (wrong command,
missing env vars, absent workflow step) have accumulated since the tools were last touched.

## Goals / Non-Goals

**Goals:**
- All three files describe the end-to-end workflow in the same order.
- README.md is the entry point: it links to SETUP.md and MIGRATION_FIDELITY.md and gives a
  concise description of each stage.
- SETUP.md is the setup contract: canonical command sequence starts with fdb_restore.py.
- MIGRATION_FIDELITY.md covers the fidelity gate: code fences use a portable language tag.

**Non-Goals:**
- No behavior changes; no scripts are modified.
- No new documentation sections beyond what the proposal lists.

## Decisions

**Single canonical workflow order: restore → migrate → (optional validate) → run app.**
All three files use this order. README states it at the top; SETUP.md sequences commands in
this order; MIGRATION_FIDELITY.md introduces the fidelity gate as step 3.

**`py` throughout** — Windows-canonical per project convention (memory: `py` not `python`).
Applied wherever a command example appears.

**Code fence tag `bash` in MIGRATION_FIDELITY.md** — the commands run on Windows and
non-Windows alike; `powershell` was a misnomer. `bash` is the least-wrong generic tag and
renders syntax highlighting without implying a shell requirement.

## Risks / Trade-offs

None significant. All changes are additive or corrective text edits with no behavioral side
effects.
