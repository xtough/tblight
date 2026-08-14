## ADDED Requirements

### Requirement: Backup file discovery
The script SHALL scan the current working directory for files matching `TB*.fbk.zip` and present them to the user for selection when no file argument is given.

#### Scenario: Single backup file found, no argument given
- **WHEN** the script is run without arguments and exactly one `TB*.fbk.zip` file exists in the current directory
- **THEN** the script SHALL use that file without prompting

#### Scenario: Multiple backup files found, no argument given
- **WHEN** the script is run without arguments and multiple `TB*.fbk.zip` files exist
- **THEN** the script SHALL display a numbered list of matching files and prompt the user to enter a number to select one

#### Scenario: No backup files found and no argument given
- **WHEN** the script is run without arguments and no `TB*.fbk.zip` files exist in the current directory
- **THEN** the script SHALL print an error message and exit with a non-zero status code

#### Scenario: File argument provided
- **WHEN** the script is invoked with a file path as a positional argument
- **THEN** the script SHALL use that file directly without scanning or prompting

### Requirement: Pre-restore backup offer
If `TB6DATENBANK.FDB` already exists in the current directory, the script SHALL offer to back it up before overwriting it.

#### Scenario: Existing database, user accepts backup
- **WHEN** `TB6DATENBANK.FDB` exists and the user confirms the backup prompt
- **THEN** the script SHALL run `gbak -b` to create a timestamped backup file (e.g., `20260809_120000_TB6DATENBANK.fbk`) before proceeding with restore

#### Scenario: Existing database, user declines backup
- **WHEN** `TB6DATENBANK.FDB` exists and the user declines the backup prompt
- **THEN** the script SHALL proceed directly to restore without creating a backup

#### Scenario: No existing database
- **WHEN** `TB6DATENBANK.FDB` does not exist
- **THEN** the script SHALL proceed directly to restore without any backup prompt

### Requirement: Database restore
The script SHALL extract the `.fbk` file from the selected ZIP archive and restore it to `TB6DATENBANK.FDB` using Firebird 2.1 `gbak` with the correct flags for TB6 archives.

#### Scenario: Successful restore
- **WHEN** a valid `TB*.fbk.zip` is selected and `gbak` is available
- **THEN** the script SHALL extract the `.fbk` to a temporary file, patch the FSS character set subtype metadata in the temp file, invoke `gbak -rep -v`, restore to `TB6DATENBANK.FDB`, clean up the temp file, and exit with status 0

The FSS patch SHALL replace all occurrences of the byte pattern `\x00\x00\x2b\x04\xff\xff\xff\xff` with `\x00\x00\x2b\x04\x00\x00\x00\x00` in the extracted `.fbk` before passing it to gbak.

#### Scenario: gbak not found on PATH
- **WHEN** `gbak` is not found on the system PATH
- **THEN** the script SHALL print a clear error message indicating Firebird 2.1 must be installed and exit with a non-zero status code before prompting for anything else

#### Scenario: gbak returns a non-zero exit code
- **WHEN** `gbak` exits with an error during restore or backup
- **THEN** the script SHALL surface the gbak error output and exit with a non-zero status code; the temp file SHALL be cleaned up regardless

### Requirement: SYSDBA credentials handling
The script SHALL obtain SYSDBA credentials without storing them in plaintext files.

#### Scenario: Credentials in environment
- **WHEN** the environment variable `ISC_PASSWORD` (or `ISQL_PASSWORD`) is set
- **THEN** the script SHALL use that value as the SYSDBA password without prompting

#### Scenario: Credentials not in environment
- **WHEN** no password environment variable is set
- **THEN** the script SHALL prompt for the SYSDBA password using a secure input method (no echo)
