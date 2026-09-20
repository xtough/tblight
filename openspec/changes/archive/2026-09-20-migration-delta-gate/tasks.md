# Tasks

## 1. Primary Key Discovery

- [x] 1.1 Add `get_sqlite_pk_columns(con, table)` to `migrate_to_sqlite.py` using `PRAGMA table_info` to find columns with `pk > 0`; fall back to `['ID']` when none are found (verify: calling it on BEGEHUNGEN returns `['ID']`; calling it on a table with no PK constraint also returns `['ID']`)

## 2. Delta Comparison Core

- [x] 2.1 Add `compare_sqlite_delta(candidate_path, accepted_path)` to `migrate_to_sqlite.py`; function opens both databases, enumerates all user tables from both, and returns a dict with keys `new`, `deleted`, `modified`, `date_anomalies` (verify: calling it with two identical databases returns all-zero counts in every category)
- [x] 2.2 Implement new-record detection inside `compare_sqlite_delta`: for each table, collect PKs present in candidate but absent from accepted and store them under `new[table]` (verify: detects a row added to candidate that is absent from accepted)
- [x] 2.3 Implement deleted-record detection: for each table, collect PKs present in accepted but absent from candidate and store them under `deleted[table]`; skip row-level fetch when table row count exceeds 500 in either DB and record a `skipped_large_table` note (verify: detects a row present in accepted that is absent from candidate)
- [x] 2.4 Implement modified-record detection: for tables within the 500-row cap, compare full rows by PK and collect changed rows under `modified[table]` (verify: detects a single-column change on a row that shares its PK between both databases)

## 3. Date Anomaly Detection

- [x] 3.1 Inside `compare_sqlite_delta`, query `MAX(DATUM)` from the accepted BEGEHUNGEN table; collect new Begehungen from candidate whose DATUM is not NULL and is less than that maximum; store them under `date_anomalies` (verify: a candidate Begehung with a DATUM one day before the accepted MAX(DATUM) appears in `date_anomalies`; a Begehung dated after MAX(DATUM) does not appear)

## 4. Delta Report Output and Prompt

- [x] 4.1 Add `format_delta_report(delta)` to `migrate_to_sqlite.py` that prints a "New records" section (per-table counts) and a separate "Anomalies" section (deleted records, modified records, date anomalies with per-item details, up to 10 samples per category) (verify: output for a delta with all four categories populated contains both section headers and the anomaly details)
- [x] 4.2 Add `prompt_delta_acknowledgment()` to `migrate_to_sqlite.py` that prints `Promote candidate to TB6.sqlite? [y/N]:` and returns `True` for input `y` or `Y`, `False` for anything else including empty input (verify: returns `True` for `y`, `False` for `n`, `False` for Enter with no input)

## 5. Integration into Promotion Flow

- [x] 5.1 In the `__main__` block of `migrate_to_sqlite.py`, after `run_validation()` returns 0 and before `promote_candidate()`: if `accepted_db` exists, call `compare_sqlite_delta`, `format_delta_report`, and `prompt_delta_acknowledgment`; exit with code 1 if the user aborts (verify: running `py migrate_to_sqlite.py` with an existing TB6.sqlite prompts before promotion; cancelling leaves TB6.sqlite unchanged and TB6.sqlite.candidate retained)
- [x] 5.2 Verify first migration path: confirm that when no `accepted_db` file exists, the delta gate is skipped and promotion proceeds without any prompt (verify: fresh run against an empty directory completes without a `[y/N]` prompt)

## 6. Documentation

- [x] 6.1 Update `MIGRATION_FIDELITY.md` to describe the two-phase promotion workflow: (1) fidelity validation — Firebird→SQLite correctness; (2) delta gate — candidate vs. accepted comparison with user acknowledgment; clarify that phase 1 is independent of any previously accepted SQLite file (verify: both phases are described with their inputs, outputs, and the first-migration bypass note)
