# Design

## Context

See proposal.md — Why. The promotion flow in `migrate_to_sqlite.py` currently runs
`run_validation()` (fidelity gate) then `promote_candidate()` with no step between
them. `validate_migration_fidelity.py` compares the candidate against Firebird; it
receives `--accepted-db` only for report metadata, never for actual comparison.

The delta gate is a new phase that runs after fidelity passes and before promotion, but
only when a prior accepted database exists.

## Goals / Non-Goals

**Goals:**
- Insert a delta-comparison phase between fidelity pass and `promote_candidate()`.
- Present a human-readable delta report and a `[Continue/Abort]` prompt at the terminal.
- Detect the four difference classes from the spec: new records, deleted records,
  modified records, and date anomalies in `BEGEHUNGEN.DATUM`.
- Skip the phase entirely when no accepted database file exists (first migration).

**Non-Goals:**
- No changes to `validate_migration_fidelity.py`; fidelity logic is untouched.
- No persistent delta report file (fidelity already writes `validation_reports/`).
- No batch/non-interactive mode for this phase (single-user CLI tool; a future
  `--non-interactive` flag can be added if needed).
- No delta history across multiple runs.

## Decisions

### Where to put the delta logic

**Decision:** Add a `compare_sqlite_delta(candidate_path, accepted_path)` function
directly in `migrate_to_sqlite.py`. It is invoked from the `__main__` block after
`run_validation()` returns 0 and before `promote_candidate()`.

**Why not in `validate_migration_fidelity.py`?** That script's contract is
Firebird→SQLite. Adding SQLite-to-SQLite logic there blurs the scope boundary the
`migration-fidelity-validation` spec update makes explicit. Cross-importing would also
create a circular dependency (`validate` already imports from `migrate`).

**Why not a new file?** The delta gate is a promotion-flow concern owned by
`migrate_to_sqlite.py`. A separate module would be justified if the logic grew complex
or needed independent invocation, neither of which applies now.

### Primary key discovery

**Decision:** Use `PRAGMA table_info(table)` to discover columns flagged `pk > 0`.
Fall back to `ID` if the pragma returns no PK columns (tables without an explicit PK
constraint but with a conventional `ID` column).

**Why not hard-code known PKs?** The database has ~50 user tables; hard-coding would
need maintenance on every schema change. PRAGMA is schema-driven and free.

**Limitation:** For the modified-record check, only tables where a single PK column
can be identified get a row-level diff. Tables with composite PKs or no usable key get
a count-only comparison (new/deleted totals still reported).

### Date anomaly scope

**Decision:** Scope to `BEGEHUNGEN.DATUM` only. The reference point is
`MAX(DATUM)` in the accepted database. A new Begehung with `DATUM <
MAX(accepted.DATUM)` is a retroactive entry — notable but not necessarily an error.

**Why only BEGEHUNGEN?** Retroactive entries are meaningful for ascents (logbook
integrity). Other tables with date columns (TAGESNOTIZ, KOMMENTARE) are ancillary and
their temporal ordering is less critical.

### Handling large tables

**Decision:** For modified-record detection, cap per-table row-level diff at 500 rows
fetched from each side. When a table exceeds the cap, report the count discrepancy only
and note "row diff skipped — table too large for in-memory comparison."

**Why 500?** Keeps memory usage bounded and keeps the terminal output readable. The
whole-table count comparison still catches mass deletions/additions regardless of the
cap.

### User prompt format

**Decision:** Print the delta report to stdout in a structured human-readable format
(section headers, indented counts, anomaly items listed individually up to a sample
limit of 10 per category), then print a single-line prompt:

```
Promote candidate to TB6.sqlite? [y/N]:
```

Default is abort (N). Any response other than `y` or `Y` aborts.

## Risks / Trade-offs

- [Tables with composite PKs have no row-level diff] → Mitigation: report new/deleted
  counts only; composite PKs are rare in this schema (most tables use a single `ID`).
- [Long comparison time on large tables] → Mitigation: row cap at 500 and a progress
  message before the comparison starts.
- [Non-interactive use broken by the prompt] → Mitigation: document that piping input
  through `echo y |` works; a `--non-interactive` flag can be added later if needed.

## Migration Plan

No schema changes. The change is additive: the delta gate is a new function call in the
`__main__` block of `migrate_to_sqlite.py`. Existing `--accepted-db` / `--candidate-db`
flags are unchanged. No rollback is needed — reverting the commit restores the prior
behaviour.
