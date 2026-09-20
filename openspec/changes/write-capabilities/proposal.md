# Proposal

## Why

Tourenbuch VI has been effectively abandonware since 2012.  The long-term goal is to
sunset the Firebird dependency entirely and let users maintain their climbing logbook
exclusively through the SQLite-backed application.  That requires write endpoints in
`app.py` for creating and editing Gipfel, Wege, and Begehungen — and a migration-time
conflict detection mechanism so that users who have already written local records are
warned before a new migration run from a Tourenbuch backup overwrites `TB6.sqlite`.

The migration-delta-gate change (see `openspec/changes/migration-delta-gate`) is a
prerequisite: its comparison logic is reused here to detect local writes in the current
accepted database that are absent from the incoming Firebird candidate.

## What Changes

- **BREAKING**: Remove the read-only architectural constraint from `openspec/config.yaml`
  and update the project description to reflect the extended scope.
- Add write endpoints to `app.py` for the core logbook entities:
  - `POST /api/begehungen` — log a new ascent
  - `PUT /api/begehungen/{beg_id}` — edit an existing ascent
  - `DELETE /api/begehungen/{beg_id}` — remove an ascent
  - `POST /api/gipfel` — add a new summit
  - `PUT /api/gipfel/{gipfel_id}` — edit a summit
  - `POST /api/wege` — add a new route
  - `PUT /api/wege/{weg_id}` — edit a route
- Migration becomes **one-shot after first local write**: once `TB6.sqlite` contains any
  locally-written record, subsequent migration runs from a Tourenbuch backup must warn
  the user that promotion would overwrite local data.
- At promotion time, the delta gate detects locally-written records (records in the
  current `TB6.sqlite` absent from the incoming candidate) and presents them to the user
  with two explicit choices:
  - **Stop** — abort promotion, keep the current `TB6.sqlite` with local writes intact.
  - **Overwrite** — proceed with promotion, accepting that local writes will be lost.
- No silent promotion is permitted when local writes exist; the user must choose explicitly.

## Capabilities

### New Capabilities

- `write-api`: Write endpoints in `app.py` for creating and editing Gipfel, Wege, and
  Begehungen, backed by the SQLite runtime database.
- `migration-write-conflict-detection`: Detection and user-facing resolution of conflicts
  between incoming Firebird migrations and locally-written SQLite records.

### Modified Capabilities

- `migration-delta-gate`: Extend the delta report to identify locally-written records
  (records in accepted DB absent from candidate) as a distinct conflict class, separate
  from ordinary deletions, and present the stop/overwrite choice.

## Impact

- `app.py` — write endpoints and input validation added.
- `migrate_to_sqlite.py` — pre-promotion conflict detection using delta gate.
- `openspec/config.yaml` — read-only architectural constraint removed; project
  description updated to reflect write capability and sunset roadmap.
- `MIGRATION_FIDELITY.md` — document the conflict detection and stop/overwrite behaviour.
- New specs: `openspec/specs/write-api/spec.md`,
  `openspec/specs/migration-write-conflict-detection/spec.md`.
- Existing spec updated: `openspec/specs/migration-delta-gate/spec.md`.
- **Dependency**: `migration-delta-gate` change must be implemented first.
