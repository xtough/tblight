# Migration Fidelity Gate

## Purpose

The Firebird-to-SQLite migration produces a candidate SQLite database first and only promotes it to the accepted database path after passing two sequential gates:

1. **Fidelity validation** — confirms the candidate faithfully represents the Firebird source. This gate is independent of any previously accepted SQLite file.
2. **Delta gate** — compares the candidate against the currently accepted `TB6.sqlite` (when one exists) and requires explicit user acknowledgment before promotion. Skipped automatically on the first migration when no accepted database is present.

## Blocking Read Workflows

The blocking baseline protects the current read-only workflows exposed by the FastAPI application:

- `/api/regionen`
- `/api/gebiete`
- `/api/gipfel`
- `/api/gipfel/{gipfel_id}`
- `/api/wege`
- `/api/wege/{weg_id}`
- `/api/begehungen`
- `/api/begehungen/{beg_id}`
- `/api/stats`

Informational-only checks currently cover leaderboard-style statistics where tie ordering is less critical:

- `/api/stats top-partners`
- `/api/stats areas-visited`

## Canonical Inputs

Every validation run uses the same source-of-truth inputs:

- Firebird source: built from `TB_FIREBIRD_HOST` + `TBBACKUP` (defaults to `localhost` + repository-local `TB6DATENBANK.FDB`)
- Candidate SQLite output: `TB6.sqlite.candidate`
- Accepted SQLite output: `TB6.sqlite`
- Audit reports: `validation_reports/latest.json` and timestamped JSON snapshots in `validation_reports/`

Related setup contract: see [SETUP.md](SETUP.md).

## Check Classification

Blocking checks:

- Table presence and row-count parity for all discovered Firebird user tables.
- Parent-child integrity for the core entities behind current UI flows.
- Semantic profiles for null handling, dates, numeric grades, and flag-like values.
- Endpoint aggregate parity for the current list/detail/statistics read models.

Informational checks:

- Top-partner ranking output.
- Most-visited-area ranking output.

Rationale:

- Blocking checks protect correctness that directly affects route, summit, ascent, and summary screens.
- Informational checks are still reported, but they do not prevent promotion when only ranking-style differences remain.

## Commands

Restore a Firebird backup before running migration (step 0):

```bash
py fdb_restore.py
```

Run the validator against the accepted database:

```bash
py validate_migration_fidelity.py
```

Run a full migration with gated promotion:

```bash
py migrate_to_sqlite.py
```

Override Firebird input explicitly:

```bash
py migrate_to_sqlite.py --tbbackup ./TB6DATENBANK.FDB
```

**Promotion flow (repeat migration):**

1. Migration writes `TB6.sqlite.candidate`.
2. Fidelity validation runs against Firebird. Fails fast if blocking checks fail — `TB6.sqlite` is unchanged.
3. Delta gate compares candidate against `TB6.sqlite`, prints the report, and prompts: `Promote candidate to TB6.sqlite? [y/N]:`
   Default is abort (`N`). The candidate is retained at `TB6.sqlite.candidate` if the user aborts.
4. On confirmation, the candidate replaces `TB6.sqlite` and the previous accepted file moves to `TB6.sqlite.previous`.

**First migration (no accepted database):** steps 2 and 4 run; step 3 is skipped automatically.

## Failure Handling

If validation fails:

1. The candidate database remains at `TB6.sqlite.candidate`.
2. The accepted database at `TB6.sqlite` remains unchanged.
3. The latest report is written to `validation_reports/latest.json`.
4. Diagnose the failure class from the report before rerunning migration.

Common mismatch classes in the report:

- `row-count-mismatch`
- `orphaned-records`
- `profile-mismatch`
- `aggregate-mismatch`
- `query-error`

Recommended remediation flow:

1. Fix the migration defect or source-data extraction issue.
2. Rerun `py migrate_to_sqlite.py`.
3. Recheck `validation_reports/latest.json`.
4. Promote only after all blocking checks pass.

## Maintenance

Update the validator whenever user-visible read requirements change in `app.py`, especially when:

- a new endpoint is added to the existing read workflows
- aggregate SQL changes for `/api/gebiete`, `/api/gipfel`, `/api/wege`, `/api/begehungen`, or `/api/stats`
- newly user-visible typed or flag-like fields are introduced
- core entity relationships change

Whenever the validator changes, rerun `py validate_migration_fidelity.py` against the current accepted database to confirm the baseline still reflects actual runtime behavior.
