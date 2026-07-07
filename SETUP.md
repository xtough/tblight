# Platform-Independent Setup

This project supports development and migration workflows on:

- Windows (PowerShell 5.1+ or PowerShell 7+)
- macOS (bash/zsh)
- Linux (bash/zsh)

## Minimum Requirements

- Python 3.11+
- Firebird 2.1 `isql` client
- Firebird database backup/input file (`TB6DATENBANK.FDB` by default)

## Canonical Environment Variables

- `TBBACKUP`: path to Firebird input database/backup file
- `TB_FIREBIRD_HOST`: Firebird host (`localhost` default)
- `TB_FIREBIRD_USER`: Firebird user (`SYSDBA` default)
- `TB_FIREBIRD_PASS`: Firebird password (`masterkey` default)
- `TB_ISQL_PATH`: explicit path to `isql` executable

All variables are optional; defaults are used when omitted.

## Canonical Commands

These commands are the same on all supported platforms.

### 1. Run migration (candidate -> validate -> promote)

```bash
python migrate_to_sqlite.py
```

### 2. Run fidelity validation only

```bash
python validate_migration_fidelity.py
```

### 3. Override Firebird input file explicitly

```bash
python migrate_to_sqlite.py --tbbackup ./TB6DATENBANK.FDB
```

## Shell Examples

### PowerShell

```powershell
$env:TBBACKUP = "C:/data/TB6DATENBANK.FDB"
$env:TB_ISQL_PATH = "C:/Program Files/Firebird/Firebird_2_1/bin/isql.exe"
python migrate_to_sqlite.py
```

### bash/zsh

```bash
export TBBACKUP="/data/TB6DATENBANK.FDB"
export TB_ISQL_PATH="/opt/firebird/bin/isql"
python migrate_to_sqlite.py
```

## Preflight Diagnostics

Both migration and validation commands print preflight diagnostics before execution, including:

- resolved root path
- resolved Firebird input (`TBBACKUP`)
- resolved Firebird DSN
- resolved `isql` executable path
- target database path (validation)

If a required dependency is missing, execution exits early with actionable messages.

## Compatibility Notes and Known Limitations

- Firebird server/client compatibility must match the source database format.
- Local Firebird access assumes `host:path` DSN syntax.
- Spaces in file paths are supported; quote env var values in shells.
- If `isql` is not on `PATH`, set `TB_ISQL_PATH` explicitly.
- This workflow does not provide an alternate non-Firebird extraction backend.

## Fallback Guidance

If setup fails:

1. Run `python validate_migration_fidelity.py --help` and verify expected parameters.
2. Set `TB_ISQL_PATH` explicitly to a known working `isql` binary.
3. Set `TBBACKUP` explicitly to a known readable Firebird database file.
4. Re-run migration/validation and inspect preflight diagnostics.

## Manual Cross-Platform Verification Steps

Use this checklist to verify equivalent behavior across Windows and at least one non-Windows environment:

1. Set `TBBACKUP` and `TB_ISQL_PATH` explicitly.
2. Run `python migrate_to_sqlite.py` and confirm promotion succeeds.
3. Run `python validate_migration_fidelity.py` and confirm PASS/FAIL matches for the same data snapshot.
4. Compare generated `validation_reports/latest.json` summary fields (`status`, `checks_run`, `blocking_failures`).

## Maintenance Guidance

When scripts or dependencies change:

1. Keep canonical commands in this file up to date.
2. Keep preflight diagnostics aligned with required dependencies.
3. Re-run manual cross-platform verification checklist.
4. Update `MIGRATION_FIDELITY.md` when validation behavior or report contracts change.
