# Spec Delta

## ADDED Requirements

### Requirement: Fidelity validation scope is limited to Firebird-to-SQLite conversion
The migration fidelity validation capability SHALL exclusively assess whether the SQLite
candidate faithfully represents the source Firebird database. It SHALL NOT compare
successive SQLite databases or account for differences between the candidate and any
previously accepted SQLite file at `TB6.sqlite`.

#### Scenario: Firebird is the sole comparison source
- **WHEN** fidelity validation is executed
- **THEN** all comparisons SHALL be performed against the live Firebird database, not
  against any previously accepted SQLite file

#### Scenario: Fidelity outcome is independent of accepted database state
- **WHEN** fidelity validation is executed against a candidate
- **THEN** the PASS/FAIL outcome SHALL depend only on the Firebird-to-SQLite mapping,
  regardless of whether an accepted database exists or what it contains
