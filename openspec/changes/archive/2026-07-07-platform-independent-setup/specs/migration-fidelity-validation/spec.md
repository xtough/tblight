## MODIFIED Requirements

### Requirement: Baseline Fidelity Gate
The system MUST define a migration fidelity baseline that classifies validation outcomes as PASS or FAIL before a migrated SQLite dataset is accepted for user-facing read workflows.

#### Scenario: Dataset acceptance decision
- **WHEN** a migrated SQLite dataset is produced from the canonical Firebird source
- **THEN** the dataset MUST be accepted only if all blocking fidelity checks pass

#### Scenario: Cross-platform validation entry point
- **WHEN** fidelity validation is executed via the documented canonical command on a supported operating system
- **THEN** the validation workflow MUST resolve required paths and produce an equivalent PASS/FAIL decision for the same dataset state

### Requirement: Validation Evidence Output
The system MUST produce a repeatable validation report that records gate results, mismatch categories, and failing entities so acceptance decisions are auditable.

#### Scenario: Auditable report generation
- **WHEN** fidelity validation completes
- **THEN** a structured report MUST be generated with explicit PASS/FAIL state and mismatch details per check

#### Scenario: Platform-neutral report location
- **WHEN** validation is run on any supported operating system
- **THEN** report output paths and file naming behavior MUST follow repository-relative conventions documented by the setup contract
