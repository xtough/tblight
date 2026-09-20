# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased]

### Added

- `fdb_restore.py`: CLI utility to restore a `TB*.fbk.zip` Firebird backup archive to `TB6DATENBANK.FDB`. Auto-discovers backup files, offers to back up any existing database before overwriting, and applies the correct `gbak` charset flags for TB6 archives.

### Changed

- Documentation consistency pass across README.md, SETUP.md, and MIGRATION_FIDELITY.md:
  - README now links to MIGRATION_FIDELITY.md, lists all five environment variables with defaults, and describes the candidate→accepted promotion flow and `TB6.sqlite.previous` rollback artefact.
  - SETUP.md canonical command sequence now starts with `fdb_restore.py` (step 0).
  - MIGRATION_FIDELITY.md code fences corrected from `powershell` to `bash`.
  - All command examples use `py` (Windows-canonical) consistently.
