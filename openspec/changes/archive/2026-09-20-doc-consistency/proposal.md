# Proposal

## Why

The three primary documentation files (README.md, SETUP.md, MIGRATION_FIDELITY.md) are
inconsistent with each other and with the actual workflow: README does not link to
MIGRATION_FIDELITY.md, the restore step via `fdb_restore.py` is absent from SETUP.md's
canonical command sequence, `python` is used throughout instead of `py` on Windows, the
env-var inventory is incomplete, and the candidate→accepted promotion flow is not
described anywhere for the user reading README.

## What Changes

- Add cross-link from README.md to MIGRATION_FIDELITY.md alongside the existing SETUP.md link.
- Correct invocation command from `python` to `py` in README.md usage steps and SETUP.md canonical commands (Windows-canonical per project convention).
- Expand README.md env-var list to include all five canonical variables (`TBBACKUP`, `TB_FIREBIRD_HOST`, `TB_FIREBIRD_USER`, `TB_FIREBIRD_PASS`, `TB_ISQL_PATH`).
- Add `fdb_restore.py` as step 0 to SETUP.md canonical command sequence, before migration.
- Describe the candidate→accepted promotion flow (and `TB6.sqlite.previous` rollback artefact) in README.md.
- Add a note in README.md that `validate_migration_fidelity.py` can also be run standalone against an already-accepted `TB6.sqlite`.
- Fix MIGRATION_FIDELITY.md code fences from `powershell` to `bash` (commands are cross-platform).
- Ensure the end-to-end workflow is stated consistently across all three files in the same order: restore → migrate → (optional standalone validate) → run app.

## Capabilities

### New Capabilities
_(none — pure documentation change)_

### Modified Capabilities
_(none — no spec-level behavior changes)_

## Impact

- `README.md`
- `SETUP.md`
- `MIGRATION_FIDELITY.md`
