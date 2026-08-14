## 1. Script scaffold

- [x] 1.1 Create `fdb_restore.py` with CLI entry point (`argparse`, positional `file` argument optional)
- [x] 1.2 Add gbak availability check at startup (exit with clear error if not found)
- [x] 1.3 Add SYSDBA credentials resolution (check `ISC_PASSWORD` / `ISQL_PASSWORD` env vars, fall back to `getpass`)

## 2. Backup file discovery

- [x] 2.1 Implement `find_backup_files()` to glob `TB*.fbk.zip` in the current directory
- [x] 2.2 Implement `select_backup_file(files)` to auto-select when count == 1, prompt numbered list when count > 1, and error-exit when count == 0
- [x] 2.3 Wire argument / auto-discovery into main flow

## 3. Pre-restore backup

- [x] 3.1 Implement `offer_backup(db_path, password)` that prompts user when `TB6DATENBANK.FDB` exists
- [x] 3.2 Implement `run_gbak_backup(db_path, out_path, password)` invoking `gbak -b -v`
- [x] 3.3 Generate timestamped backup filename and call `run_gbak_backup` on user confirmation

## 4. Restore

- [x] 4.1 Implement `extract_fbk(zip_path)` to unzip the `.fbk` to a `tempfile.NamedTemporaryFile`
- [x] 4.2 Fix `run_gbak_restore` to use `gbak -rep -v` instead of `-c`; remove `-fix_fss_metadata`/`-fix_fss_data` flags (Firebird 5-only, not present in Firebird 2.1)
- [x] 4.3 Ensure temp file is deleted in a `finally` block regardless of restore outcome
- [x] 4.4 Surface gbak stderr/stdout on failure and exit non-zero

## 5. Tests

- [x] 5.1 Unit test `find_backup_files()` with a temp directory containing matching and non-matching files
- [x] 5.2 Unit test `select_backup_file()` for the three count cases (0, 1, many)
- [x] 5.3 Unit test `extract_fbk()` with a synthetic ZIP containing a dummy `.fbk` file
- [x] 5.4 Unit test credentials resolution (env var present / absent using monkeypatch)

## 6. Documentation and changelog

- [x] 6.1 Add usage section for `fdb_restore.py` to README.md
- [x] 6.2 Update CHANGELOG.md with new utility entry
