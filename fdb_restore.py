"""
Restore a Tourenbuch 6 Firebird backup archive to TB6DATENBANK.FDB.

Requires Firebird 2.1 gbak on PATH.
"""

import argparse
import getpass
import os
import shutil
import subprocess
import sys
import tempfile
import zipfile
from datetime import datetime
from pathlib import Path


DB_NAME = "TB6DATENBANK.FDB"
BACKUP_PATTERN = "TB*.fbk.zip"


def check_gbak():
    if shutil.which("gbak") is None:
        sys.exit(
            "Error: gbak not found on PATH.\n"
            "Install Firebird 2.1 and add its bin/ directory to PATH."
        )


def resolve_password() -> str:
    for var in ("ISC_PASSWORD", "ISQL_PASSWORD"):
        pw = os.environ.get(var)
        if pw:
            return pw
    return getpass.getpass("SYSDBA password: ")


# ── Backup file discovery ────────────────────────────────────────────────────

def find_backup_files(directory: Path) -> list:
    return sorted(directory.glob(BACKUP_PATTERN))


def select_backup_file(files: list) -> Path:
    if len(files) == 0:
        sys.exit(f"Error: no {BACKUP_PATTERN} files found in the current directory.")
    if len(files) == 1:
        print(f"Using: {files[0].name}")
        return files[0]
    print("Multiple backup files found:")
    for i, f in enumerate(files, 1):
        print(f"  {i}. {f.name}")
    while True:
        raw = input(f"Select [1-{len(files)}]: ").strip()
        if raw.isdigit() and 1 <= int(raw) <= len(files):
            return files[int(raw) - 1]
        print(f"Enter a number between 1 and {len(files)}.")


# ── Pre-restore backup ───────────────────────────────────────────────────────

def run_gbak_backup(db_path: Path, out_path: Path, password: str):
    result = subprocess.run(
        ["gbak", "-b", "-v", str(db_path), str(out_path),
         "-user", "SYSDBA", "-password", password],
        capture_output=True, text=True,
    )
    if result.returncode != 0:
        print(result.stdout)
        print(result.stderr, file=sys.stderr)
        sys.exit(f"Error: gbak backup failed (exit {result.returncode}).")
    print(f"Backup written to: {out_path.name}")


def offer_backup(db_path: Path, password: str):
    if not db_path.exists():
        return
    answer = input(
        f"{db_path.name} already exists. Back it up before overwriting? [Y/n] "
    ).strip().lower()
    if answer in ("", "y", "yes"):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        out_path = db_path.parent / f"{timestamp}_TB6DATENBANK.fbk"
        run_gbak_backup(db_path, out_path, password)


# ── Restore ──────────────────────────────────────────────────────────────────

def extract_fbk(zip_path: Path) -> Path:
    with zipfile.ZipFile(zip_path) as zf:
        fbk_names = [n for n in zf.namelist() if n.endswith(".fbk")]
        if not fbk_names:
            sys.exit(f"Error: no .fbk file found inside {zip_path.name}.")
        tmp = tempfile.NamedTemporaryFile(suffix=".fbk", delete=False)
        try:
            tmp.write(zf.read(fbk_names[0]))
            tmp.flush()
        finally:
            tmp.close()
    return Path(tmp.name)


def run_gbak_restore(fbk_path: Path, db_path: Path, password: str):
    result = subprocess.run(
        ["gbak", "-c", "-v",
         "-fix_fss_metadata", "ISO8859_1",
         "-fix_fss_data", "ISO8859_1",
         str(fbk_path), f"localhost:{db_path}",
         "-user", "SYSDBA", "-password", password],
        capture_output=True, text=True,
    )
    if result.returncode != 0:
        print(result.stdout)
        print(result.stderr, file=sys.stderr)
        sys.exit(f"Error: gbak restore failed (exit {result.returncode}).")
    print(f"Restore complete: {db_path.name}")


# ── Entry point ──────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Restore a Tourenbuch 6 Firebird backup archive to TB6DATENBANK.FDB."
    )
    parser.add_argument(
        "file",
        nargs="?",
        metavar="TB*.fbk.zip",
        help="Backup archive to restore (auto-discovered if omitted).",
    )
    args = parser.parse_args()

    check_gbak()

    cwd = Path.cwd()
    db_path = cwd / DB_NAME

    zip_path = Path(args.file) if args.file else select_backup_file(find_backup_files(cwd))

    password = resolve_password()
    offer_backup(db_path, password)

    fbk_path = extract_fbk(zip_path)
    try:
        run_gbak_restore(fbk_path, db_path, password)
    finally:
        fbk_path.unlink(missing_ok=True)


if __name__ == "__main__":
    main()
