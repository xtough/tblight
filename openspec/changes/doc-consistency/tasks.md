# Tasks

## 1. README.md

- [x] 1.1 Add cross-link to MIGRATION_FIDELITY.md alongside the SETUP.md link (verify: link appears in Cross-Platform Setup or a dedicated section)
- [x] 1.2 Fix `python` → `py` in the Usage section command examples (lines with `migrate_to_sqlite.py` and `app.py`)
- [x] 1.3 Expand env-var list to all five variables: TBBACKUP, TB_FIREBIRD_HOST, TB_FIREBIRD_USER, TB_FIREBIRD_PASS, TB_ISQL_PATH (verify: all five are listed with defaults)
- [x] 1.4 Describe the candidate→accepted promotion flow and the TB6.sqlite.previous rollback artefact (verify: readers can understand what happens when migration succeeds or fails)
- [x] 1.5 Add a note that validate_migration_fidelity.py can be run standalone against an already-accepted TB6.sqlite (verify: note appears near the promotion flow description)
- [x] 1.6 Ensure end-to-end workflow order is stated as: restore → migrate → (optional standalone validate) → run app (verify: the Usage steps follow this order)

## 2. SETUP.md

- [x] 2.1 Add fdb_restore.py as step 0 in the Canonical Commands section, before the migration step (verify: step 0 appears first in the sequence)
- [x] 2.2 Fix `python` → `py` in all Canonical Commands and Shell Examples (verify: no bare `python` invocations remain in command examples)

## 3. MIGRATION_FIDELITY.md

- [x] 3.1 Change code fence language tags from `powershell` to `bash` for all three command blocks (verify: no `powershell` fence tags remain)
- [x] 3.2 Fix `python` → `py` in the command examples inside those fences (verify: all three command examples use `py`)
- [x] 3.3 Add fdb_restore.py as the step preceding migration in the workflow overview or Commands section (verify: the end-to-end order restore → migrate → validate is visible)
