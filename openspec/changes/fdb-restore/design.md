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

### FSS character set subtype patch

TB6 backup archives contain FSS character set subtype fields set to `0xffffffff` (invalid). Firebird 2.1's gbak rejects these with "Implementation of text subtype N not located." The fix is a targeted binary patch of the extracted `.fbk` before restore: replace every occurrence of the 8-byte sequence `\x00\x00\x2b\x04\xff\xff\xff\xff` with `\x00\x00\x2b\x04\x00\x00\x00\x00`, zeroing the 4-byte subtype value. This was verified empirically — the two patched locations are the only binary differences between the original backup and the version that restored successfully.

**Alternative considered**: Firebird 5's gbak with `-fix_fss_metadata`/`-fix_fss_data` — rejected because this project requires Firebird 2.1 tools exclusively.

### gbak invocation via subprocess
Use `subprocess.run` with a constructed argument list. The restore command is:
```
gbak -rep -v <source.fbk> <host:DB_PATH> -user SYSDBA -password <pw>
```
`-rep` (replace) is used instead of `-c` (create) so the command succeeds whether or not `TB6DATENBANK.FDB` already exists. The pre-restore backup offer already gives the user the opportunity to save the existing database before it is overwritten.

Note: `-fix_fss_metadata` and `-fix_fss_data` are Firebird 5-only flags and must not be used — this project requires Firebird 2.1 tools exclusively.

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
