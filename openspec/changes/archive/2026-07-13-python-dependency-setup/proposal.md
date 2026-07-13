## Why

The application cannot be started in a clean environment because required Python modules are not declared and installed consistently. This blocks onboarding and reproducible execution across machines.

## What Changes

- Define a project-local Python virtual environment workflow using a standard environment name (`tb`) for dependency collection.
- Ensure all modules required by `app.py` and related startup paths are installed in the environment.
- Add and maintain a `requirements.txt` lock snapshot generated via `pip freeze` so the app can be set up and run out of the box.
- Update setup guidance to include deterministic environment creation and dependency installation steps.

## Capabilities

### New Capabilities
- None.

### Modified Capabilities
- `platform-independent-setup`: Add explicit requirements for creating a Python virtual environment, installing runtime dependencies, and maintaining `requirements.txt` for reproducible startup.

## Impact

- Affected code: Python setup and dependency declaration files (`requirements.txt`) and setup documentation.
- Affected systems: Local developer environment bootstrap on Windows/Linux/macOS.
- Dependencies: Runtime Python packages currently imported by the app and startup scripts.
