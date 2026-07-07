## Why

Project setup and operation currently rely on machine-specific assumptions (absolute paths, host-specific tooling behavior, and environment coupling), which increases onboarding time and failure risk across Windows, macOS, and Linux. We need a consistent, platform-independent setup contract now to make development and migration workflows reproducible for all contributors.

## What Changes

- Define a platform-independent setup baseline for local development, migration, and validation workflows.
- Standardize path handling, runtime discovery, and command invocation so workflows do not depend on hardcoded host paths.
- Introduce requirements for deterministic setup verification and failure diagnostics across supported operating systems.
- Introduce an input parameter "TBBACKUP" in migrate_to_sqlite.py for the Firebird migration input, defaulting to TB6DATENBANK.FDB in the current folder.
- Define minimum compatibility expectations for shell usage and tooling entry points.
- Document explicit non-goals: no feature-level API behavior changes, no UI redesign, and no schema redesign.

## Capabilities

### New Capabilities
- `platform-independent-setup`: Defines requirements for cross-platform environment setup, path resolution, tool execution, and reproducible workflow verification.

### Modified Capabilities
- `migration-fidelity-validation`: Extend setup-related requirements to ensure fidelity validation workflows run consistently across supported operating systems.

## Impact

- Affected systems: development environment bootstrap, migration execution flow, and validation tooling.
- Affected code areas: migration and validation scripts, setup/runtime documentation, and command entry points.
- Affected dependencies: Python runtime and external tool discovery behavior (for example Firebird CLI availability and path resolution).
- Affected contributor workflow: local setup, diagnostics, and execution of migration/validation commands on multiple OS platforms.
