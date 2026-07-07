## Why

The application now serves all user-visible data from the migrated SQLite database, but there is no formal baseline that defines when migrated data is trustworthy. We need a clear, testable fidelity contract now so future migration runs and data fixes do not silently regress core behavior.

## What Changes

- Define a migration fidelity baseline for the read-only Tourenbuch workflows currently exposed by the API.
- Specify parity requirements for critical entities and user-visible aggregations (Gebiete, Gipfel, Wege, Begehungen, Statistik).
- Define acceptance gates for row-level integrity, null handling, numeric/date normalization, and key relationship consistency.
- Define a repeatable validation workflow that produces pass/fail outcomes before migrated data is accepted.
- Document explicit non-goals: no UI redesign, no feature expansion, no schema redesign.

## Capabilities

### New Capabilities
- `migration-fidelity-validation`: Defines requirements and acceptance criteria to establish trust in migrated SQLite data for user-visible read models and API responses.

### Modified Capabilities
- None.

## Impact

- Affected systems: Firebird-to-SQLite migration workflow and SQLite acceptance process.
- Affected code areas: migration script logic in migrate_to_sqlite.py and read model behavior in app.py.
- Affected API surface: read-only endpoints under /api used by the current frontend.
- Dependencies: existing Firebird backup source and generated SQLite target used for validation comparisons.
