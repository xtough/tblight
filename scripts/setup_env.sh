#!/usr/bin/env bash
set -euo pipefail

ENV_NAME="${1:-tb}"

if ! command -v python3 >/dev/null 2>&1; then
  echo "python3 was not found. Install Python 3.11+ first." >&2
  exit 1
fi

if [ ! -d "$ENV_NAME" ]; then
  python3 -m venv "$ENV_NAME"
fi

"$ENV_NAME/bin/python" -m pip install --upgrade pip

if [ -f requirements.txt ]; then
  "$ENV_NAME/bin/python" -m pip install -r requirements.txt
else
  "$ENV_NAME/bin/python" -m pip install fastapi uvicorn
  "$ENV_NAME/bin/python" -m pip freeze > requirements.txt
fi

echo "Environment '$ENV_NAME' is ready."
echo "Activate with: source $ENV_NAME/bin/activate"
