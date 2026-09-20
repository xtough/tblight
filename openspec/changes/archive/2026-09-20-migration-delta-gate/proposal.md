# Proposal

## Why

The existing fidelity gate (`validate_migration_fidelity.py`) answers one question only:
did the Firebird→SQLite conversion produce a complete and semantically correct candidate?
It does not answer a second, orthogonal question: what changed between the new candidate
and the last accepted `TB6.sqlite`?  Users who run repeated migrations from fresh
Tourenbuch VI backups have no visibility into new records, deletions, or suspicious
mutations before promotion silently replaces the accepted database.

## What Changes

- Add a new delta-comparison phase to the promotion workflow: before `TB6.sqlite.candidate`
  replaces `TB6.sqlite`, the system compares them and produces a structured delta report.
- Gate promotion on explicit user acknowledgment of the delta report — promotion does not
  proceed automatically when a previous accepted database exists.
- The delta report classifies findings into:
  - **New records** per table (expected in an append-only workflow).
  - **Deleted records** — records present in the old accepted DB that are absent from the
    candidate (unexpected; flags data loss or source-side deletion).
  - **Modified records** — records with the same primary key but changed values
    (uncommon but possible when the user retroactively edits an ascent in Tourenbuch).
  - **Date anomalies** — new Begehungen whose `DATUM` is earlier than `MAX(DATUM)` of
    Begehungen already in the accepted database (retroactive entry; noteworthy but not
    necessarily an error).
- Anomalies (deletions, modifications, date anomalies) are highlighted separately from
  plain new-record additions to let the user make an informed promotion decision.
- When no previous accepted database exists (first-time migration), the delta phase is
  skipped and promotion proceeds after fidelity passes.
- Update `migration-fidelity-validation` spec to make its scope explicit: it covers only
  Firebird→SQLite conversion fidelity, not successive SQLite-to-SQLite comparison.
- Update `MIGRATION_FIDELITY.md` to document both phases and the new user-acknowledgment step.

## Capabilities

### New Capabilities

- `migration-delta-gate`: Compares a new migration candidate against the previously
  accepted SQLite, reports per-table deltas and anomalies, and gates promotion on
  explicit user acknowledgment.

### Modified Capabilities

- `migration-fidelity-validation`: Scope clarification — add requirement that the
  fidelity gate covers Firebird→SQLite conversion correctness only and is independent of
  successive migration comparisons.

## Impact

- `validate_migration_fidelity.py` — delta comparison logic added alongside or after the existing fidelity checks.
- `migrate_to_sqlite.py` — promotion flow updated to call delta gate and await acknowledgment.
- `MIGRATION_FIDELITY.md` — document both phases and their relationship.
- New spec: `openspec/specs/migration-delta-gate/spec.md`.
- Existing spec updated: `openspec/specs/migration-fidelity-validation/spec.md`.
