## Why

Restoring Tourenbuch 6 Firebird databases from backup archives (`.fbk.zip`) is a recurring manual process that requires exact gbak flags and character set handling. A utility script eliminates error-prone repetition and guides users through file selection and safe overwrite handling.

## What Changes

- Add `fdb_restore` utility script that locates and restores `TB*.fbk.zip` backup archives to `TB6DATENBANK.FDB`
- Script auto-detects backup files in the current directory and prompts for selection when multiple exist
- Before overwriting an existing `TB6DATENBANK.FDB`, script offers to create a gbak backup of the current database

## Capabilities

### New Capabilities
- `fdb-restore`: CLI utility to restore a Firebird 2.1 `.fbk.zip` backup archive to `TB6DATENBANK.FDB`, with auto-discovery of backup files, interactive selection, and optional pre-restore backup of any existing database

### Modified Capabilities

## Impact

- New file: `fdb_restore.sh` (or `fdb_restore.py`) in the project root
- Requires Firebird 2.1 `gbak` on PATH
- Requires `unzip` (or Python `zipfile`) to extract the `.fbk` from the archive
- No changes to existing code or database schema
