## Context

The read-only web application now depends on SQLite data produced by a Firebird-to-SQLite migration script. Current behavior is usable, but trust in migrated data is implicit and undocumented. The baseline must cover user-visible read models and aggregate endpoints so future migration runs can be accepted or rejected consistently.

Constraints:
- Existing APIs and frontend behavior remain the source of user-visible truth.
- The change is specification-first; no implementation changes are required in this proposal phase.
- Validation must remain repeatable for future migration runs.

## Goals / Non-Goals

**Goals:**
- Ensure all Firebird tables are migrated to SQLite, including all table contents.
- Define a deterministic fidelity contract for migrated SQLite data used by current API endpoints.
- Standardize acceptance gates for row parity, null semantics, numeric/date normalization, and key relationship integrity.
- Define evidence outputs for pass/fail decisions before a migrated dataset is considered trustworthy.

**Non-Goals:**
- Redesign the Firebird schema or SQLite schema.
- Add new product features, endpoints, or UI behavior.
- Introduce write support or bidirectional sync.

## Decisions

1. Scope validation to user-visible read models first.
- Rationale: Protects real user workflows with minimal complexity.
- Alternative considered: full-table parity across all tables immediately.
- Why not alternative: high effort with lower short-term user impact.

2. Use multi-layer fidelity gates instead of a single row-count check.
- Rationale: row counts alone miss semantic drift (null handling, date coercion, join fallout).
- Alternative considered: a single global parity score.
- Why not alternative: opaque failures are harder to triage.

3. Define acceptance at endpoint-oriented aggregates plus entity-level checks.
- Rationale: aligns migration quality with API behavior consumed by the frontend.
- Alternative considered: validate only migration script outputs.
- Why not alternative: does not guarantee runtime query semantics in app.py.

4. Keep the baseline independent from implementation tooling details.
- Rationale: allows later choice of SQL scripts, Python checks, or CI jobs without rewriting requirements.
- Alternative considered: lock to one script layout now.
- Why not alternative: premature coupling to tooling.

## Risks / Trade-offs

- [Risk] Sampling misses low-frequency edge cases -> Mitigation: include deterministic boundary scenarios (nulls, extreme grades, earliest/latest dates).
- [Risk] Query semantics differ between Firebird and SQLite even with matched rows -> Mitigation: include endpoint-level aggregate parity checks.
- [Risk] Overly strict gates block practical progress -> Mitigation: classify gates into blocking vs informational and document rationale.
- [Risk] Baseline drifts as APIs evolve -> Mitigation: require updates to fidelity spec whenever affected endpoint requirements change.

## Migration Plan

1. Establish baseline requirements and scenarios in the capability spec.
2. Define canonical validation inputs (source backup + generated SQLite output).
3. Produce a repeatable validation report format with explicit pass/fail outcomes.
4. Use the report as the release gate for migrated datasets.
5. If a gate fails, quarantine dataset, diagnose mismatch class, and rerun migration/validation.

Rollback strategy:
- Continue serving the previously accepted SQLite dataset until all blocking fidelity gates pass.

## Open Questions

- Which subset of tables/endpoints should be treated as blocking on day one vs informational?
- What tolerance, if any, is acceptable for formatting-only differences (for example whitespace or locale date rendering)?
- Should fidelity checks run only on migration execution or also as periodic drift audits?
