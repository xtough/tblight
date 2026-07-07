## Context

This repository currently mixes platform-dependent assumptions in migration and validation workflows, including host-specific path conventions and command execution expectations. Recent work improved migration fidelity, but setup and operational ergonomics are still implicitly tuned for a Windows environment.

Contributors need setup and execution to be deterministic across Windows, macOS, and Linux so development and validation outcomes are reproducible and support overhead is reduced.

## Goals / Non-Goals

**Goals:**
- Define a platform-independent setup contract for local development and validation workflows.
- Standardize runtime path resolution and command entry points so scripts avoid host-specific hardcoded assumptions.
- Define setup verification and diagnostics that fail clearly when required dependencies are missing.
- Keep migration and fidelity validation execution behavior consistent across supported operating systems.

**Non-Goals:**
- Introduce new product features or API behavior changes.
- Redesign database schemas or migration data models.
- Replace required external tools with alternate backends in this change.

## Decisions

1. Favor repository-relative and environment-driven path discovery over absolute paths.
- Rationale: repository-relative paths are stable across machines and CI environments.
- Alternative considered: maintain hardcoded fallback paths per OS.
- Why not alternative: brittle and difficult to maintain as environments evolve.

2. Define one canonical cross-platform entry point per workflow.
- Rationale: reduces shell-specific command drift and improves documentation clarity.
- Alternative considered: separate commands per OS in daily usage.
- Why not alternative: increases divergence and support burden.

3. Separate dependency checks from workflow execution.
- Rationale: explicit preflight diagnostics improve onboarding and reduce opaque runtime failures.
- Alternative considered: rely on runtime exceptions from migration/validation scripts.
- Why not alternative: exceptions often fail late and are less actionable.

4. Keep setup capability requirements independent of implementation language details.
- Rationale: preserves flexibility to refactor scripts while maintaining setup guarantees.
- Alternative considered: bind setup requirements to current script internals.
- Why not alternative: over-couples specs to transient implementation details.

## Risks / Trade-offs

- [Risk] Cross-platform command differences remain hidden in edge shells -> Mitigation: define compatibility expectations for default shell invocation and documented alternatives.
- [Risk] Dependency auto-discovery can mask misconfiguration -> Mitigation: enforce explicit diagnostics output for resolved paths and missing tools.
- [Risk] Refactoring paths may break existing local scripts -> Mitigation: provide compatibility notes and migration guidance in setup documentation.
- [Risk] Scope creep into broader tooling redesign -> Mitigation: enforce non-goals and keep changes focused on setup contract and verification.

## Migration Plan

1. Define setup capability requirements and scenarios for platform-independent execution.
2. Define delta requirements extending migration-fidelity-validation to include cross-platform setup guarantees.
3. Implement setup preflight checks, path normalization, and canonical command entry points.
4. Update setup and operational documentation with verified commands for supported platforms.
5. Validate workflows on representative Windows and non-Windows environments before adoption.

Rollback strategy:
- Retain current workflow entry points until platform-independent setup checks are validated and accepted.

## Open Questions

- Which minimum shell/runtime matrix is mandatory (PowerShell, bash, zsh, CI shell)?
- Should unsupported environment combinations fail hard or warn with degraded guidance?
- Is Firebird client discovery expected to be automatic or explicitly configured per environment?
