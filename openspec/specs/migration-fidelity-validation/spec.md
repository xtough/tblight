# migration-fidelity-validation

## Purpose
Define the baseline fidelity gate for Firebird-to-SQLite migration validation so migrated datasets are accepted only when user-visible data integrity and semantics are preserved.

## Requirements

### Requirement: Baseline Fidelity Gate
The system MUST define a migration fidelity baseline that classifies validation outcomes as PASS or FAIL before a migrated SQLite dataset is accepted for user-facing read workflows.

#### Scenario: Dataset acceptance decision
- **WHEN** a migrated SQLite dataset is produced from the canonical Firebird source
- **THEN** the dataset MUST be accepted only if all blocking fidelity checks pass

#### Scenario: Cross-platform validation entry point
- **WHEN** fidelity validation is executed via the documented canonical command on a supported operating system
- **THEN** the validation workflow MUST resolve required paths and produce an equivalent PASS/FAIL decision for the same dataset state

### Requirement: Entity Integrity Parity
The system MUST verify parity for critical entities used by read workflows, including presence of primary records and consistency of key relationships across Gebiete, Gipfel, Wege, and Begehungen.

#### Scenario: Relationship consistency check
- **WHEN** integrity validation is executed for a migrated dataset
- **THEN** each evaluated child record MUST reference an existing parent record for required relationships

### Requirement: Semantic Value Preservation
The system MUST preserve user-visible value semantics for nullable fields, graded values, boolean-like values, and date/timestamp representations used by API responses.

#### Scenario: Null and typed value preservation
- **WHEN** mapped fields are compared between source truth and migrated output
- **THEN** null/empty distinctions and normalized type semantics MUST match the baseline mapping rules

### Requirement: Endpoint Aggregate Fidelity
The system MUST validate user-visible aggregate behavior for current read endpoints, including totals and grouped outputs used by filters, tables, and statistics views.

#### Scenario: Aggregate parity for read endpoints
- **WHEN** aggregate validation is run for baseline endpoints
- **THEN** reported counts and grouped results MUST match the expected baseline outcomes for the same source snapshot

### Requirement: Validation Evidence Output
The system MUST produce a repeatable validation report that records gate results, mismatch categories, and failing entities so acceptance decisions are auditable.

#### Scenario: Auditable report generation
- **WHEN** fidelity validation completes
- **THEN** a structured report MUST be generated with explicit PASS/FAIL state and mismatch details per check

#### Scenario: Platform-neutral report location
- **WHEN** validation is run on any supported operating system
- **THEN** report output paths and file naming behavior MUST follow repository-relative conventions documented by the setup contract

### Requirement: Non-goal Protection
The baseline validation capability MUST NOT require UI behavior changes, API feature expansion, or schema redesign as a prerequisite for adoption.

#### Scenario: Scope guard
- **WHEN** baseline validation requirements are applied
- **THEN** existing user-facing features MUST remain unchanged unless explicitly covered by a separate capability change
