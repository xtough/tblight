# Tourenbuch VI (2012) Reverse Engineering

This repository contains an unofficial reverse engineering and data-migration focused reimplementation of the 2012-era Tourenbuch VI application.

Reference source page:
- http://www.gipfelbuch.de/tourenbuch/

## Project Scope

- Firebird 2.1 to SQLite migration tooling
- Read-only API and web UI for exploration and analysis
- Migration fidelity validation and promotion gate

## Restoring a Firebird Backup

`fdb_restore.py` restores a `TB*.fbk.zip` backup archive to `TB6DATENBANK.FDB`.
Requires Firebird 2.1 `gbak` on PATH.

```bash
# auto-discover backup in current directory
py fdb_restore.py

# or specify a file explicitly
py fdb_restore.py "TB Sicherung 20260613_1207.fbk.zip"
```

The script will:

1. Prompt to back up any existing `TB6DATENBANK.FDB` before overwriting
2. Extract the `.fbk` from the ZIP to a temp file
3. Invoke `gbak` with the correct charset flags for TB6 archives
4. Clean up the temp file on success or failure

SYSDBA password is read from `ISC_PASSWORD` or `ISQL_PASSWORD` env vars, or prompted securely if neither is set.

## Usage

- Clone the tblight git repository to your machine
- Restore `TB6DATENBANK.FDB` from your Tourenbuch VI backup using `fdb_restore.py` (see above)
- Create the local Python environment named `tb` and install dependencies:
	- PowerShell: `./scripts/setup_env.ps1`
	- bash/zsh: `./scripts/setup_env.sh`
- Activate the environment:
	- PowerShell: `.\\tb\\Scripts\\Activate.ps1`
	- bash/zsh: `source tb/bin/activate`
- Optionally set environment variables if defaults do not match your environment:
  - `TBBACKUP` — path to Firebird input file (default: `TB6DATENBANK.FDB` in repo root)
  - `TB_FIREBIRD_HOST` — Firebird host (default: `localhost`)
  - `TB_FIREBIRD_USER` — Firebird user (default: `SYSDBA`)
  - `TB_FIREBIRD_PASS` — Firebird password (default: `masterkey`)
  - `TB_ISQL_PATH` — explicit path to `isql` executable (default: resolved from PATH)
- Run `py migrate_to_sqlite.py` to migrate Firebird → SQLite and promote to `TB6.sqlite`
- Run `py app.py` to start the local backend server
- Open your browser on the localhost URL

### Migration Promotion

`migrate_to_sqlite.py` produces a candidate at `TB6.sqlite.candidate` and runs the
fidelity gate before promotion. On success:

- `TB6.sqlite.candidate` → `TB6.sqlite` (new accepted database)
- Previous `TB6.sqlite` → `TB6.sqlite.previous` (rollback artefact)

If validation fails, `TB6.sqlite` is left untouched and the candidate remains at
`TB6.sqlite.candidate` for diagnosis.

`validate_migration_fidelity.py` can also be run standalone to re-validate an
already-accepted `TB6.sqlite` without running a new migration.

## Cross-Platform Setup

For environment variables, compatibility notes, and canonical commands on Windows/macOS/Linux, see [SETUP.md](SETUP.md).
For the fidelity gate, check classification, and validation report format, see [MIGRATION_FIDELITY.md](MIGRATION_FIDELITY.md).

## Important Notice

This project is an independent reconstruction effort for compatibility, preservation, and interoperability purposes.
It is not affiliated with or endorsed by the original Tourenbuch authors or gipfelbuch.de.
