# Tourenbuch VI (2012) Reverse Engineering

This repository contains an unofficial reverse engineering and data-migration focused reimplementation of the 2012-era Tourenbuch VI application.

Reference source page:
- http://www.gipfelbuch.de/tourenbuch/

## Project Scope

- Firebird 2.1 to SQLite migration tooling
- Read-only API and web UI for exploration and analysis
- Migration fidelity validation and promotion gate

## Usage

- Clone the tblight git repository to your machine
- Unzip the TB6DATENBANK.FDB file from your latest Tourenbuch VI backup into the root folder of tblight
- Run `python migrate_to_sqlite.py` to create the TB6.sqlite database
- Run `python app.py` to start the local backend server
- Open your browser on the localhost URL

## Important Notice

This project is an independent reconstruction effort for compatibility, preservation, and interoperability purposes.
It is not affiliated with or endorsed by the original Tourenbuch authors or gipfelbuch.de.
