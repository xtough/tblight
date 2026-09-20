# Spec Delta

## Purpose

Gates promotion of a new SQLite migration candidate by comparing it against the
previously accepted database, classifying differences into report categories, and
requiring explicit user acknowledgment before TB6.sqlite is replaced.

## ADDED Requirements

### Requirement: First migration skips delta gate
When no previously accepted database exists at the promotion target path, the system
SHALL skip the delta comparison phase entirely and proceed directly to promotion after
fidelity validation passes.

#### Scenario: No accepted database present
- **WHEN** `promote_candidate` is called and no file exists at `TB6.sqlite`
- **THEN** promotion proceeds without a delta comparison or user prompt

### Requirement: Repeat migration produces a delta report
When an accepted database exists at `TB6.sqlite` at the time of candidate promotion,
the system SHALL compare `TB6.sqlite.candidate` against `TB6.sqlite` and produce a
delta report before presenting the promotion decision.

#### Scenario: Accepted database present
- **WHEN** `promote_candidate` is called and `TB6.sqlite` exists
- **THEN** a delta report is produced and displayed to the user before promotion is offered

#### Scenario: Delta report covers all user tables
- **WHEN** the delta comparison runs
- **THEN** all tables present in either the candidate or the accepted database SHALL be
  included in the comparison

### Requirement: Delta report classifies findings into four categories
The delta report SHALL classify all differences between candidate and accepted database
into exactly four named categories: new records, deleted records, modified records, and
date anomalies.

#### Scenario: New records reported per table
- **WHEN** a table contains rows in the candidate that are absent from the accepted database
- **THEN** those rows SHALL appear under "New records" in the delta report, grouped by table

#### Scenario: Deleted records reported per table
- **WHEN** a table contains rows in the accepted database that are absent from the candidate
- **THEN** those rows SHALL appear under "Deleted records" in the delta report, grouped by table

#### Scenario: Modified records reported per table
- **WHEN** a row with the same primary key has different column values in candidate versus accepted
- **THEN** that row SHALL appear under "Modified records" in the delta report

#### Scenario: Date anomalies reported for Begehungen
- **WHEN** a new Begehung in the candidate has a DATUM value earlier than the maximum
  DATUM of Begehungen already present in the accepted database
- **THEN** that Begehung SHALL appear under "Date anomalies" in the delta report

### Requirement: Anomalies highlighted separately from plain new records
The delta report SHALL visually distinguish anomalies (deleted records, modified records,
and date anomalies) from plain new-record additions so the user can assess risk at a glance.

#### Scenario: Anomaly summary is separate from new-record summary
- **WHEN** the delta report is displayed
- **THEN** counts and details of deleted records, modified records, and date anomalies
  SHALL be grouped under a distinct "Anomalies" section, separate from the new-records section

### Requirement: Promotion is gated on explicit user acknowledgment
When an accepted database exists, the system SHALL NOT promote the candidate without
first presenting the delta report and receiving an explicit confirmation or abort from
the user.

#### Scenario: User must respond before promotion proceeds
- **WHEN** the delta report has been displayed
- **THEN** the system SHALL pause and prompt the user to either confirm promotion or abort,
  and SHALL NOT proceed until a response is received

#### Scenario: User confirms promotion
- **WHEN** the user explicitly confirms after reviewing the delta report
- **THEN** `TB6.sqlite.candidate` replaces `TB6.sqlite` and the previous accepted file
  moves to `TB6.sqlite.previous`

#### Scenario: User aborts promotion
- **WHEN** the user explicitly aborts after reviewing the delta report
- **THEN** `TB6.sqlite` SHALL remain unchanged and `TB6.sqlite.candidate` SHALL be
  retained at its current path for diagnosis or re-evaluation
