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
- Create the local Python environment named `tb` and install dependencies:
	- PowerShell: `./scripts/setup_env.ps1`
	- bash/zsh: `./scripts/setup_env.sh`
- Activate the environment:
	- PowerShell: `.\\tb\\Scripts\\Activate.ps1`
	- bash/zsh: `source tb/bin/activate`
- Optionally set `TBBACKUP` and `TB_ISQL_PATH` if defaults do not match your environment
- Run `python migrate_to_sqlite.py` to create and validate the SQLite database
- Run `python app.py` to start the local backend server
- Open your browser on the localhost URL

## Cross-Platform Setup

For environment variables, compatibility notes, and canonical commands on Windows/macOS/Linux, see [SETUP.md](SETUP.md).

## Important Notice

This project is an independent reconstruction effort for compatibility, preservation, and interoperability purposes.
It is not affiliated with or endorsed by the original Tourenbuch authors or gipfelbuch.de.
