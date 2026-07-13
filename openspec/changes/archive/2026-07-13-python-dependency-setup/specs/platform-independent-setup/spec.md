## ADDED Requirements

### Requirement: Python Virtual Environment Bootstrap
The setup workflow MUST define a repository-local Python virtual environment bootstrap process that uses a documented environment name of `tb` and works consistently on Windows, macOS, and Linux.

#### Scenario: Create environment in fresh clone
- **WHEN** a contributor follows the documented setup steps in a fresh clone
- **THEN** a local Python virtual environment named `tb` MUST be created successfully using only documented commands

### Requirement: Runtime Dependency Installation Contract
The setup workflow MUST install all Python modules required for web app startup and import resolution before runtime commands are executed.

#### Scenario: Missing dependency prevention
- **WHEN** a contributor completes the documented dependency installation steps
- **THEN** running the documented app startup command MUST NOT fail due to missing Python import modules

### Requirement: Requirements Freeze Reproducibility
The repository MUST provide a `requirements.txt` dependency snapshot generated from the prepared environment using `pip freeze` so setup can be reproduced on clean machines.

#### Scenario: Recreate environment from requirements
- **WHEN** a contributor creates a clean environment and installs dependencies from `requirements.txt`
- **THEN** the app startup dependency set MUST be reproducible without manual package discovery
