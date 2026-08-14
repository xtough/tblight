# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased]

### Added

- `fdb_restore.py`: CLI utility to restore a `TB*.fbk.zip` Firebird backup archive to `TB6DATENBANK.FDB`. Auto-discovers backup files, offers to back up any existing database before overwriting, and applies the correct `gbak` charset flags for TB6 archives.
