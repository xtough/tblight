## Context

The repository currently lacks a deterministic Python dependency bootstrap path for running the web app in a fresh environment. The immediate failure mode is missing imports at startup (for example FastAPI-related modules), which forces contributors to guess package installs manually. Existing setup guidance already targets cross-platform behavior, so this change extends that contract with explicit Python environment and dependency manifest expectations.

## Goals / Non-Goals

**Goals:**
- Define a single, repeatable Python environment bootstrap path for local development.
- Standardize dependency installation by creating a local virtual environment named `tb` and installing all runtime imports required by app startup.
- Produce and maintain `requirements.txt` as the canonical dependency snapshot (`pip freeze`) for deterministic setup.
- Keep setup steps portable across Windows, macOS, and Linux.

**Non-Goals:**
- Introducing containerized workflows or replacing virtual environments with other environment managers.
- Refactoring application architecture beyond what is needed to ensure startup dependencies are installable.
- Defining production deployment packaging.

## Decisions

1. Use Python virtual environments as the baseline setup mechanism.
Rationale: Built into Python, cross-platform, and already familiar to contributors. This minimizes tooling assumptions and aligns with repository-local setup.
Alternatives considered: Poetry/pipenv/conda as mandatory tooling. Rejected to avoid introducing additional installation prerequisites for this change.

2. Standardize the environment name as `tb` for dependency collection and documentation examples.
Rationale: A consistent name reduces support friction and keeps commands/documentation unambiguous.
Alternatives considered: Arbitrary user-defined names. Rejected because inconsistency reduces reproducibility in support and onboarding.

3. Use `requirements.txt` generated from the prepared environment via `pip freeze` as the project dependency manifest.
Rationale: Provides a concrete, reproducible dependency set for clean-machine setup.
Alternatives considered: Manually curated requirements file without freeze. Rejected due to drift risk and missed transitive/runtime dependencies.

4. Validate setup by ensuring app startup imports resolve after installation.
Rationale: Import resolution is the direct user-visible failure today and is the minimum correctness gate for this change.
Alternatives considered: Static dependency declaration only. Rejected because declarations alone do not guarantee runnable startup state.

5. The project should keep the latest Python version implicit until compatibility issues appear.

6. Keep optional development-only tools should be separated into a `requirements-dev.txt`.

## Risks / Trade-offs

- [Frozen dependencies may capture unnecessary transitive packages] -> Mitigation: Regenerate after clean install and review for obvious tool-only packages before committing.
- [Different Python versions can produce slightly different dependency resolution] -> Mitigation: Document supported Python version expectations in setup docs.
- [Local environment naming convention may conflict with contributor preferences] -> Mitigation: Keep `tb` as the documented default while allowing optional local aliasing outside committed artifacts.

## Migration Plan

1. Create or update setup documentation with explicit venv creation, activation, install, and freeze commands for all supported platforms.
2. Create the `tb` environment, install required runtime modules, and verify app startup succeeds.
3. Generate/update `requirements.txt` from the validated environment.
4. Re-run setup in a clean environment using only documented steps to confirm reproducibility.
