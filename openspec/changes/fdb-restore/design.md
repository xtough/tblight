## Context

The Tourenbuch 6 database (TB6DATENBANK.FDB) is distributed as gbak backup archives compressed in ZIP files matching the pattern `TB*.fbk.zip`. Restoring requires specific gbak flags (`-fix_fss_metadata ISO8859_1`) due to the FSS/Latin-1 encoding mix in Firebird 2.1. This is currently done manually, which is fragile and error-prone.

The project already uses Python (see existing setup), making a Python script the natural fit for cross-platform operation.

## Goals / Non-Goals

**Goals:**
- Locate `TB*.fbk.zip` files in the current directory automatically
- Accept an optional file path argument to skip interactive selection
- When multiple files are found, present a numbered list for the user to choose
- If `TB6DATENBANK.FDB` already exists, offer to back it up via gbak before overwriting
- Restore the selected `.fbk` (extracted from ZIP) to `TB6DATENBANK.FDB` using Firebird 2.1 gbak with the correct flags

**Non-Goals:**
- Managing Firebird server installation or configuration
- Supporting Firebird versions other than 2.1
- Restoring to a different target filename
- Automating SYSDBA credentials (user provides them or they are read from environment)

## Decisions

### Python over Shell Script
The project uses Python and has a platform-independent setup. Python's `zipfile` module handles ZIP extraction without requiring an external `unzip` binary, and Python's `subprocess` and `input()` work identically on Windows and Linux.

**Alternative considered**: Bash script — rejected because it is not cross-platform (Windows requires WSL or Cygwin).

### gbak invocation via subprocess
Use `subprocess.run` with a constructed argument list. The exact restore command is:
```
gbak -c -v -fix_fss_metadata ISO8859_1 <source.fbk> <host:DB_PATH> -user SYSDBA -password <pw>
```
The `-fix_fss_metadata ISO8859_1` flag is required for TB6 archives (FSS metadata stored as ISO8859_1).

**SYSDBA credentials**: Prompt interactively using `getpass` if not provided via `ISQL_PASSWORD` / `ISC_PASSWORD` environment variables, which is the Firebird convention.

### Extract to a temp file, clean up after
The `.fbk` is extracted from the ZIP into a `tempfile.NamedTemporaryFile` and deleted after restore completes (success or failure). This avoids leaving large uncompressed files on disk.

### Backup before overwrite uses gbak -b
If `TB6DATENBANK.FDB` exists and the user consents, run:
```
gbak -b -v TB6DATENBANK.FDB <timestamp>_TB6DATENBANK.fbk -user SYSDBA -password <pw>
```
The backup filename includes a timestamp to avoid collisions.

## Risks / Trade-offs

- **gbak not on PATH** → Script checks for `gbak` on PATH at startup and exits with a clear error pointing to the Firebird 2.1 installation.
- **Large ZIP extraction fills disk** → Extraction is to a temp directory; no mitigation beyond the error message from the OS.
- **SYSDBA password in process args** → Known Firebird limitation; password is passed as a subprocess argument (visible in `ps`). Acceptable for a developer utility on a local machine.
- **Firebird server may not be running** → gbak will fail with a descriptive message; the script surfaces the error and exits non-zero.
