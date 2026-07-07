## 1. Baseline Scope Definition

- [ ] 1.1 Identify the blocking read workflows and corresponding API endpoints in app.py covered by the fidelity gate.
- [ ] 1.2 Define canonical source and target dataset inputs used for every validation run.
- [ ] 1.3 Classify checks into blocking vs informational with explicit acceptance rationale.

## 2. Fidelity Check Design

- [ ] 2.1 Define entity integrity checks for Gebiete, Gipfel, Wege, and Begehungen including parent-child relationship consistency.
- [ ] 2.2 Define semantic preservation checks for null handling, numeric/grade fields, boolean-like fields, and date/timestamp values.
- [ ] 2.3 Define endpoint aggregate parity checks for list/detail/statistics outputs consumed by the frontend.

## 3. Validation Workflow Implementation

- [ ] 3.1 Implement a repeatable validation runner that executes all defined checks against a migrated SQLite dataset.
- [ ] 3.2 Implement structured mismatch classification and evidence collection per failed check.
- [ ] 3.3 Generate an auditable PASS/FAIL report artifact for each validation execution.

## 4. Operationalization

- [ ] 4.1 Integrate fidelity validation as a required gate before accepting a newly migrated SQLite dataset.
- [ ] 4.2 Document failure handling workflow (quarantine, diagnosis, rerun, re-acceptance).
- [ ] 4.3 Add a maintenance task to update baseline checks whenever relevant API requirements change.
