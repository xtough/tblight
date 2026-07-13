## 1. Environment Bootstrap Baseline

- [x] 1.1 Identify all Python runtime imports required by app startup paths (including `app.py`) and confirm missing dependencies in a clean environment.
- [x] 1.2 Add or update setup commands/scripts to create a local Python virtual environment named `tb` on supported platforms.
- [x] 1.3 Document environment activation and dependency installation commands for Windows, macOS, and Linux.

## 2. Dependency Installation and Manifest

- [x] 2.1 Install all required runtime modules into the `tb` environment and verify import resolution for app startup.
- [x] 2.2 Generate or update `requirements.txt` using `pip freeze` from the validated environment.
- [x] 2.3 Review the frozen dependency set for obvious non-runtime noise and regenerate if needed to keep setup deterministic.

## 3. Validation and Setup Fidelity

- [x] 3.1 Recreate a fresh environment from documented steps and `requirements.txt` to confirm reproducible startup.
- [x] 3.2 Execute the documented app startup command in the recreated environment and verify no missing-module failures.
- [x] 3.3 Update setup documentation and README references so contributors can bootstrap the app out of the box.
