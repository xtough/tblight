# CLAUDE.md

## Change Process

All new capabilities and significant changes go through OpenSpec before implementation:

```
/opsx:propose   → creates change + proposal
/opsx:apply     → implements tasks from the change
/opsx:archive   → archives the completed change
```

Active changes live in `openspec/changes/`. Archived changes are in `openspec/changes/archive/`.

## Authoritative Documentation

| Topic | Location |
|---|---|
| Tech stack, domain, migration pipeline | `openspec/config.yaml` (context field) |
| Setup and usage | `README.md`, `SETUP.md` |
| Fidelity gate and blocking checks | `MIGRATION_FIDELITY.md` |
| Feature requirements | `openspec/specs/<capability>/spec.md` |
| Design decisions and rationale | `openspec/changes/archive/<change>/design.md` |
