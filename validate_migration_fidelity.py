"""Validate Firebird-to-SQLite migration fidelity for Tourenbuch 6."""

from __future__ import annotations

import argparse
import json
import os
import re
import sqlite3
import subprocess
import sys
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from migrate_to_sqlite import (
    DEFAULT_FB_HOST,
    DEFAULT_FB_PASS,
    DEFAULT_FB_USER,
    DEFAULT_TBBACKUP,
    build_firebird_dsn,
    normalize_backup_path,
    resolve_isql_path,
)

ROOT = Path(__file__).parent
DEFAULT_TARGET_DB = ROOT / "TB6.sqlite"
DEFAULT_ACCEPTED_DB = ROOT / "TB6.sqlite"
DEFAULT_REPORT_DIR = ROOT / "validation_reports"
SEPARATOR = "|~|"

RUNTIME = {
    "tbbackup": normalize_backup_path(os.getenv("TBBACKUP", str(DEFAULT_TBBACKUP))),
    "fb_host": os.getenv("TB_FIREBIRD_HOST", DEFAULT_FB_HOST),
    "fb_user": os.getenv("TB_FIREBIRD_USER", DEFAULT_FB_USER),
    "fb_pass": os.getenv("TB_FIREBIRD_PASS", DEFAULT_FB_PASS),
    "isql": resolve_isql_path(os.getenv("TB_ISQL_PATH")),
}
RUNTIME["fb_dsn"] = build_firebird_dsn(RUNTIME["fb_host"], RUNTIME["tbbackup"])

BLOCKING_ENDPOINTS = [
    "/api/regionen",
    "/api/gebiete",
    "/api/gipfel",
    "/api/gipfel/{gipfel_id}",
    "/api/wege",
    "/api/wege/{weg_id}",
    "/api/begehungen",
    "/api/begehungen/{beg_id}",
    "/api/stats",
]

INFORMATIONAL_ENDPOINTS = [
    "/api/stats top-partners",
    "/api/stats areas-visited",
]

RELATIONSHIP_CHECKS = [
    ("GEBIETE", "REGION_ID", "REGIONEN", "ID"),
    ("GEBIETE", "GESTEIN", "GESTEINE", "ID"),
    ("GIPFEL", "GEBIET_ID", "GEBIETE", "ID"),
    ("WEGE", "GIPFEL_ID", "GIPFEL", "ID"),
    ("BEGEHUNGEN", "WEG_ID", "WEGE", "ID"),
    ("SEILSCHAFT", "BEGEHUNG_ID", "BEGEHUNGEN", "ID"),
    ("SEILSCHAFT", "PERSON_ID", "PERSONEN", "ID"),
]

PROFILE_CHECKS = [
    {"table": "GIPFEL", "column": "GPS_B", "kind": "numeric"},
    {"table": "GIPFEL", "column": "GPS_L", "kind": "numeric"},
    {"table": "WEGE", "column": "GRDX", "kind": "numeric"},
    {"table": "WEGE", "column": "GRDXOU", "kind": "numeric"},
    {"table": "WEGE", "column": "GRDXRP", "kind": "numeric"},
    {"table": "WEGE", "column": "QW", "kind": "numeric"},
    {"table": "BEGEHUNGEN", "column": "DATUM", "kind": "date-text"},
    {"table": "GIPFEL", "column": "PRIVAT", "kind": "flag-text"},
    {"table": "WEGE", "column": "PRIVAT", "kind": "flag-text"},
]

AGGREGATE_CHECKS = [
    {
        "id": "regionen-total",
        "severity": "blocking",
        "endpoint": "/api/regionen",
        "description": "Region list row count",
        "sqlite": "SELECT COUNT(*) FROM REGIONEN",
        "firebird": "SELECT COUNT(*) FROM REGIONEN",
        "shape": "scalar",
    },
    {
        "id": "gebiete-overview",
        "severity": "blocking",
        "endpoint": "/api/gebiete",
        "description": "Gebiete totals and nested route counts",
        "sqlite": """
            SELECT COUNT(*),
                   COALESCE(SUM((SELECT COUNT(*) FROM GIPFEL gp WHERE gp.GEBIET_ID = g.ID)), 0),
                   COALESCE(SUM((SELECT COUNT(*) FROM GIPFEL gp JOIN WEGE w ON w.GIPFEL_ID = gp.ID WHERE gp.GEBIET_ID = g.ID)), 0)
            FROM GEBIETE g
        """,
        "firebird": """
            SELECT CAST(COUNT(*) AS VARCHAR(20)) || '|~|' ||
                   CAST(COALESCE(SUM((SELECT COUNT(*) FROM GIPFEL gp WHERE gp.GEBIET_ID = g.ID)), 0) AS VARCHAR(20)) || '|~|' ||
                   CAST(COALESCE(SUM((SELECT COUNT(*) FROM GIPFEL gp JOIN WEGE w ON w.GIPFEL_ID = gp.ID WHERE gp.GEBIET_ID = g.ID)), 0) AS VARCHAR(20))
            FROM GEBIETE g
        """,
        "shape": "scalar-row",
    },
    {
        "id": "gipfel-overview",
        "severity": "blocking",
        "endpoint": "/api/gipfel",
        "description": "Gipfel totals and nested ascent counts",
        "sqlite": """
            SELECT COUNT(*),
                   COALESCE(SUM((SELECT COUNT(*) FROM WEGE w WHERE w.GIPFEL_ID = gp.ID)), 0),
                   COALESCE(SUM((SELECT COUNT(*) FROM WEGE w JOIN BEGEHUNGEN b ON b.WEG_ID = w.ID WHERE w.GIPFEL_ID = gp.ID)), 0)
            FROM GIPFEL gp
        """,
        "firebird": """
            SELECT CAST(COUNT(*) AS VARCHAR(20)) || '|~|' ||
                   CAST(COALESCE(SUM((SELECT COUNT(*) FROM WEGE w WHERE w.GIPFEL_ID = gp.ID)), 0) AS VARCHAR(20)) || '|~|' ||
                   CAST(COALESCE(SUM((SELECT COUNT(*) FROM WEGE w JOIN BEGEHUNGEN b ON b.WEG_ID = w.ID WHERE w.GIPFEL_ID = gp.ID)), 0) AS VARCHAR(20))
            FROM GIPFEL gp
        """,
        "shape": "scalar-row",
    },
    {
        "id": "wege-overview",
        "severity": "blocking",
        "endpoint": "/api/wege",
        "description": "Wege totals and linked ascent counts",
        "sqlite": """
            SELECT COUNT(*),
                   COALESCE(SUM((SELECT COUNT(*) FROM BEGEHUNGEN b WHERE b.WEG_ID = w.ID)), 0),
                   COALESCE((SELECT COUNT(*) FROM VC), 0),
                   COALESCE((SELECT COUNT(*) FROM VS), 0)
            FROM WEGE w
        """,
        "firebird": """
            SELECT CAST(COUNT(*) AS VARCHAR(20)) || '|~|' ||
                   CAST(COALESCE(SUM((SELECT COUNT(*) FROM BEGEHUNGEN b WHERE b.WEG_ID = w.ID)), 0) AS VARCHAR(20)) || '|~|' ||
                   CAST(COALESCE((SELECT COUNT(*) FROM VC), 0) AS VARCHAR(20)) || '|~|' ||
                   CAST(COALESCE((SELECT COUNT(*) FROM VS), 0) AS VARCHAR(20))
            FROM WEGE w
        """,
        "shape": "scalar-row",
    },
    {
        "id": "begehungen-overview",
        "severity": "blocking",
        "endpoint": "/api/begehungen",
        "description": "Begehungen totals and distinct route coverage",
        "sqlite": "SELECT COUNT(*), COUNT(DISTINCT WEG_ID) FROM BEGEHUNGEN",
        "firebird": "SELECT CAST(COUNT(*) AS VARCHAR(20)) || '|~|' || CAST(COUNT(DISTINCT WEG_ID) AS VARCHAR(20)) FROM BEGEHUNGEN",
        "shape": "scalar-row",
    },
    {
        "id": "stats-summary",
        "severity": "blocking",
        "endpoint": "/api/stats",
        "description": "Statistics summary values",
        "sqlite": """
            SELECT
                (SELECT COUNT(*) FROM BEGEHUNGEN),
                (SELECT COUNT(DISTINCT WEG_ID) FROM BEGEHUNGEN),
                (SELECT COUNT(DISTINCT gp.ID) FROM BEGEHUNGEN b JOIN WEGE w ON w.ID = b.WEG_ID JOIN GIPFEL gp ON gp.ID = w.GIPFEL_ID),
                (SELECT COUNT(DISTINCT ge.ID) FROM BEGEHUNGEN b JOIN WEGE w ON w.ID = b.WEG_ID JOIN GIPFEL gp ON gp.ID = w.GIPFEL_ID JOIN GEBIETE ge ON ge.ID = gp.GEBIET_ID),
                (SELECT MIN(DATUM) FROM BEGEHUNGEN WHERE DATUM IS NOT NULL),
                (SELECT MAX(DATUM) FROM BEGEHUNGEN WHERE DATUM IS NOT NULL)
        """,
        "firebird": """
            SELECT
                CAST((SELECT COUNT(*) FROM BEGEHUNGEN) AS VARCHAR(20)) || '|~|' ||
                CAST((SELECT COUNT(DISTINCT WEG_ID) FROM BEGEHUNGEN) AS VARCHAR(20)) || '|~|' ||
                CAST((SELECT COUNT(DISTINCT gp.ID) FROM BEGEHUNGEN b JOIN WEGE w ON w.ID = b.WEG_ID JOIN GIPFEL gp ON gp.ID = w.GIPFEL_ID) AS VARCHAR(20)) || '|~|' ||
                CAST((SELECT COUNT(DISTINCT ge.ID) FROM BEGEHUNGEN b JOIN WEGE w ON w.ID = b.WEG_ID JOIN GIPFEL gp ON gp.ID = w.GIPFEL_ID JOIN GEBIETE ge ON ge.ID = gp.GEBIET_ID) AS VARCHAR(20)) || '|~|' ||
                COALESCE(CAST((SELECT MIN(DATUM) FROM BEGEHUNGEN WHERE DATUM IS NOT NULL) AS VARCHAR(30)), '<null>') || '|~|' ||
                COALESCE(CAST((SELECT MAX(DATUM) FROM BEGEHUNGEN WHERE DATUM IS NOT NULL) AS VARCHAR(30)), '<null>')
            FROM RDB$DATABASE
        """,
        "shape": "scalar-row",
    },
    {
        "id": "stats-per-year",
        "severity": "blocking",
        "endpoint": "/api/stats",
        "description": "Ascents per year distribution",
        "sqlite": "SELECT substr(DATUM, 1, 4), COUNT(*) FROM BEGEHUNGEN WHERE DATUM IS NOT NULL GROUP BY substr(DATUM, 1, 4) ORDER BY substr(DATUM, 1, 4)",
        "firebird": "SELECT CAST(EXTRACT(YEAR FROM DATUM) AS VARCHAR(4)) || '|~|' || CAST(COUNT(*) AS VARCHAR(20)) FROM BEGEHUNGEN WHERE DATUM IS NOT NULL GROUP BY EXTRACT(YEAR FROM DATUM) ORDER BY EXTRACT(YEAR FROM DATUM)",
        "shape": "rows",
    },
    {
        "id": "stats-grade-dist",
        "severity": "blocking",
        "endpoint": "/api/stats",
        "description": "Grade distribution for climbed routes",
        "sqlite": "SELECT CAST(w.GRDX AS TEXT), COUNT(*) FROM BEGEHUNGEN b JOIN WEGE w ON w.ID = b.WEG_ID WHERE w.GRDX IS NOT NULL AND w.GRDX > 0 GROUP BY w.GRDX ORDER BY w.GRDX",
        "firebird": "SELECT CAST(w.GRDX AS VARCHAR(20)) || '|~|' || CAST(COUNT(*) AS VARCHAR(20)) FROM BEGEHUNGEN b JOIN WEGE w ON w.ID = b.WEG_ID WHERE w.GRDX IS NOT NULL AND w.GRDX > 0 GROUP BY w.GRDX ORDER BY w.GRDX",
        "shape": "rows",
    },
    {
        "id": "stats-top-partners",
        "severity": "informational",
        "endpoint": "/api/stats top-partners",
        "description": "Top partners distribution",
        "sqlite": "SELECT p.VORNAME || ' ' || p.NAME, COUNT(*) FROM SEILSCHAFT s JOIN PERSONEN p ON p.ID = s.PERSON_ID GROUP BY s.PERSON_ID, p.VORNAME, p.NAME ORDER BY COUNT(*) DESC, p.VORNAME, p.NAME LIMIT 10",
        "firebird": """
            SELECT CAST(NAME AS VARCHAR(200)) || '|~|' || CAST(N AS VARCHAR(20))
            FROM (
                SELECT p.VORNAME || ' ' || p.NAME AS NAME, COUNT(*) AS N
                FROM SEILSCHAFT s
                JOIN PERSONEN p ON p.ID = s.PERSON_ID
                GROUP BY s.PERSON_ID, p.VORNAME, p.NAME
            ) ranked
            ORDER BY N DESC, NAME ASC
            ROWS 10
        """,
        "shape": "rows",
    },
    {
        "id": "stats-areas-visited",
        "severity": "informational",
        "endpoint": "/api/stats areas-visited",
        "description": "Most visited areas",
        "sqlite": "SELECT ge.GEBIET, COUNT(DISTINCT b.ID), COUNT(DISTINCT gp.ID) FROM BEGEHUNGEN b JOIN WEGE w ON w.ID = b.WEG_ID JOIN GIPFEL gp ON gp.ID = w.GIPFEL_ID JOIN GEBIETE ge ON ge.ID = gp.GEBIET_ID GROUP BY ge.ID, ge.GEBIET ORDER BY COUNT(DISTINCT b.ID) DESC, ge.GEBIET ASC LIMIT 15",
        "firebird": """
            SELECT CAST(GEBIET AS VARCHAR(200)) || '|~|' || CAST(N_BEGEHUNGEN AS VARCHAR(20)) || '|~|' || CAST(N_GIPFEL AS VARCHAR(20))
            FROM (
                SELECT ge.GEBIET AS GEBIET,
                       COUNT(DISTINCT b.ID) AS N_BEGEHUNGEN,
                       COUNT(DISTINCT gp.ID) AS N_GIPFEL
                FROM BEGEHUNGEN b
                JOIN WEGE w ON w.ID = b.WEG_ID
                JOIN GIPFEL gp ON gp.ID = w.GIPFEL_ID
                JOIN GEBIETE ge ON ge.ID = gp.GEBIET_ID
                GROUP BY ge.ID, ge.GEBIET
            ) ranked
            ORDER BY N_BEGEHUNGEN DESC, GEBIET ASC
            ROWS 15
        """,
        "shape": "rows",
    },
]


@dataclass
class CheckResult:
    check_id: str
    category: str
    severity: str
    description: str
    status: str
    rationale: str
    details: dict[str, Any]
    mismatches: list[dict[str, Any]]

    def as_dict(self) -> dict[str, Any]:
        return {
            "id": self.check_id,
            "category": self.category,
            "severity": self.severity,
            "description": self.description,
            "status": self.status,
            "rationale": self.rationale,
            "details": self.details,
            "mismatches": self.mismatches,
        }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--target-db", default=str(DEFAULT_TARGET_DB), help="SQLite database to validate")
    parser.add_argument("--accepted-db", default=str(DEFAULT_ACCEPTED_DB), help="Accepted production SQLite path for metadata")
    parser.add_argument("--report", help="Explicit JSON report path")
    parser.add_argument("--tbbackup", default=os.getenv("TBBACKUP", str(DEFAULT_TBBACKUP)), help="Firebird backup/database file path (TBBACKUP)")
    parser.add_argument("--fb-host", default=os.getenv("TB_FIREBIRD_HOST", DEFAULT_FB_HOST), help="Firebird host used to build DSN")
    parser.add_argument("--fb-user", default=os.getenv("TB_FIREBIRD_USER", DEFAULT_FB_USER), help="Firebird user name")
    parser.add_argument("--fb-pass", default=os.getenv("TB_FIREBIRD_PASS", DEFAULT_FB_PASS), help="Firebird password")
    parser.add_argument("--isql", default=os.getenv("TB_ISQL_PATH"), help="Path to Firebird isql executable")
    return parser.parse_args()


def apply_runtime(args: argparse.Namespace) -> None:
    runtime = {
        "tbbackup": normalize_backup_path(args.tbbackup),
        "fb_host": args.fb_host,
        "fb_user": args.fb_user,
        "fb_pass": args.fb_pass,
        "isql": resolve_isql_path(args.isql),
    }
    runtime["fb_dsn"] = build_firebird_dsn(runtime["fb_host"], runtime["tbbackup"])
    RUNTIME.update(runtime)


def preflight_diagnostics(target_db: Path) -> bool:
    print("Preflight diagnostics:")
    print(f"  ROOT: {ROOT}")
    print(f"  TBBACKUP: {RUNTIME['tbbackup']}")
    print(f"  Firebird host: {RUNTIME['fb_host']}")
    print(f"  Firebird DSN: {RUNTIME['fb_dsn']}")
    print(f"  isql path: {RUNTIME['isql']}")
    print(f"  Target DB: {target_db}")

    errors: list[str] = []
    if not Path(RUNTIME["tbbackup"]).exists():
        errors.append(f"Missing Firebird input file: {RUNTIME['tbbackup']}")
    if not Path(RUNTIME["isql"]).exists():
        errors.append(f"Missing isql executable: {RUNTIME['isql']} (set TB_ISQL_PATH or --isql)")
    if not Path(target_db).exists():
        errors.append(f"Missing target SQLite database: {target_db}")

    if errors:
        print("Preflight failed:")
        for err in errors:
            print(f"  - {err}")
        return False
    return True


def run_isql(sql: str, timeout: int = 120) -> str:
    result = subprocess.run(
        [str(RUNTIME["isql"]), RUNTIME["fb_dsn"], "-user", RUNTIME["fb_user"], "-password", RUNTIME["fb_pass"], "-q"],
        input=sql.encode("latin-1"),
        capture_output=True,
        timeout=timeout,
    )
    if result.returncode != 0:
        stderr = result.stderr.decode("latin-1", errors="replace")
        raise RuntimeError(stderr.strip() or "Firebird query failed")
    return result.stdout.decode("latin-1", errors="replace")


def parse_isql_lines(output: str) -> list[str]:
    lines = []
    for raw_line in output.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("Database:") or line.startswith("SQL>") or line.startswith("="):
            continue
        lines.append(line)
    return lines


def firebird_scalar(sql: str) -> Any:
    lines = parse_isql_lines(run_isql(f"SET HEADING OFF;\n{sql};\n"))
    return convert_token(lines[0]) if lines else None


def firebird_rows(sql: str, expected_columns: int) -> list[list[Any]]:
    lines = parse_isql_lines(run_isql(f"SET HEADING OFF;\n{sql};\n", timeout=300))
    rows: list[list[Any]] = []
    for line in lines:
        parts = line.split(SEPARATOR)
        if len(parts) != expected_columns:
            continue
        rows.append([convert_token(part.strip()) for part in parts])
    return rows


def sqlite_scalar(con: sqlite3.Connection, sql: str) -> Any:
    return con.execute(sql).fetchone()[0]


def sqlite_rows(con: sqlite3.Connection, sql: str) -> list[list[Any]]:
    return [list(row) for row in con.execute(sql).fetchall()]


def convert_token(value: str) -> Any:
    if value in {"", "<null>", "NULL", "null", "None"}:
        return None
    try:
        return int(value)
    except ValueError:
        pass
    try:
        return float(value)
    except ValueError:
        return value


def normalize_rows(rows: list[list[Any]]) -> list[list[Any]]:
    normalized: list[list[Any]] = []
    for row in rows:
        normalized.append([normalize_value(value) for value in row])
    return normalized


def normalize_value(value: Any) -> Any:
    if isinstance(value, float):
        return round(value, 6)
    if isinstance(value, str) and re.fullmatch(r"-?\d+", value):
        return int(value)
    return value


def build_profile_queries(table: str, column: str, kind: str) -> tuple[str, str]:
    if kind in {"numeric", "date-text"}:
        sqlite_sql = f'''SELECT COUNT(*), SUM(CASE WHEN "{column}" IS NULL THEN 1 ELSE 0 END), MIN("{column}"), MAX("{column}") FROM "{table}"'''
        firebird_sql = f'''SELECT COUNT(*) || '{SEPARATOR}' || SUM(CASE WHEN "{column}" IS NULL THEN 1 ELSE 0 END) || '{SEPARATOR}' || COALESCE(CAST(MIN("{column}") AS VARCHAR(100)), '<null>') || '{SEPARATOR}' || COALESCE(CAST(MAX("{column}") AS VARCHAR(100)), '<null>') FROM "{table}"'''
        return sqlite_sql, firebird_sql

    sqlite_sql = f'''SELECT COALESCE("{column}", '<null>'), COUNT(*) FROM "{table}" GROUP BY COALESCE("{column}", '<null>') ORDER BY COALESCE("{column}", '<null>')'''
    firebird_sql = f'''SELECT COALESCE(CAST("{column}" AS VARCHAR(100)), '<null>') || '{SEPARATOR}' || COUNT(*) FROM "{table}" GROUP BY COALESCE(CAST("{column}" AS VARCHAR(100)), '<null>') ORDER BY COALESCE(CAST("{column}" AS VARCHAR(100)), '<null>')'''
    return sqlite_sql, firebird_sql


def get_source_tables() -> list[str]:
    out = run_isql(
        "SELECT TRIM(RDB$RELATION_NAME) FROM RDB$RELATIONS "
        "WHERE RDB$SYSTEM_FLAG = 0 AND RDB$VIEW_BLR IS NULL "
        "ORDER BY 1;"
    )
    tables = []
    for raw_line in out.splitlines():
        line = raw_line.strip()
        if not line or line == "TRIM" or line.startswith("=") or line.startswith("Database") or line.startswith("SQL>"):
            continue
        tables.append(line)
    return sorted(tables)


def compare_table_counts(con: sqlite3.Connection) -> CheckResult:
    source_tables = get_source_tables()
    target_tables = sorted(
        row[0]
        for row in con.execute("SELECT name FROM sqlite_master WHERE type = 'table' AND name NOT LIKE 'sqlite_%' ORDER BY name")
    )
    source_set = set(source_tables)
    target_set = set(target_tables)

    mismatches: list[dict[str, Any]] = []
    for table in sorted(source_set - target_set):
        mismatches.append({"category": "missing-table", "table": table, "source_count": firebird_scalar(f'SELECT COUNT(*) FROM "{table}"'), "target_count": None})

    for table in source_tables:
        if table not in target_set:
            continue
        source_count = firebird_scalar(f'SELECT COUNT(*) FROM "{table}"')
        target_count = sqlite_scalar(con, f'SELECT COUNT(*) FROM "{table}"')
        if source_count != target_count:
            mismatches.append({"category": "row-count-mismatch", "table": table, "source_count": source_count, "target_count": target_count})

    status = "pass" if not mismatches else "fail"
    return CheckResult(
        check_id="table-count-parity",
        category="baseline-scope",
        severity="blocking",
        description="All user tables exist in SQLite and preserve row counts",
        status=status,
        rationale="All migrated user tables must remain present before user-visible checks are trusted.",
        details={
            "blocking_endpoints": BLOCKING_ENDPOINTS,
            "informational_endpoints": INFORMATIONAL_ENDPOINTS,
            "canonical_inputs": {
                "firebird_dsn": RUNTIME["fb_dsn"],
                "sqlite_target": str(con.execute("PRAGMA database_list").fetchone()[2]),
            },
            "classification": {
                "blocking": [
                    "table-count-parity",
                    "relationship-integrity",
                    "semantic-profiles",
                    "endpoint-aggregates",
                ],
                "informational": [
                    "stats-top-partners",
                    "stats-areas-visited",
                ],
            },
            "source_table_count": len(source_tables),
            "target_table_count": len(target_tables),
        },
        mismatches=mismatches,
    )


def compare_relationship_integrity(con: sqlite3.Connection) -> CheckResult:
    mismatches: list[dict[str, Any]] = []
    for child_table, child_column, parent_table, parent_column in RELATIONSHIP_CHECKS:
        orphan_count = sqlite_scalar(
            con,
            f'''
            SELECT COUNT(*)
            FROM "{child_table}" child
            LEFT JOIN "{parent_table}" parent ON parent."{parent_column}" = child."{child_column}"
            WHERE child."{child_column}" IS NOT NULL
              AND parent."{parent_column}" IS NULL
            ''',
        )
        if orphan_count:
            mismatches.append(
                {
                    "category": "orphaned-records",
                    "child_table": child_table,
                    "child_column": child_column,
                    "parent_table": parent_table,
                    "parent_column": parent_column,
                    "orphan_count": orphan_count,
                }
            )

    status = "pass" if not mismatches else "fail"
    return CheckResult(
        check_id="relationship-integrity",
        category="fidelity-design",
        severity="blocking",
        description="Core parent-child relationships remain intact in SQLite",
        status=status,
        rationale="User-visible route and ascent views depend on these joins resolving correctly.",
        details={"relationships_checked": RELATIONSHIP_CHECKS},
        mismatches=mismatches,
    )


def compare_profiles(con: sqlite3.Connection) -> CheckResult:
    mismatches: list[dict[str, Any]] = []
    for check in PROFILE_CHECKS:
        sqlite_sql, firebird_sql = build_profile_queries(check["table"], check["column"], check["kind"])
        sqlite_result = normalize_rows(sqlite_rows(con, sqlite_sql))
        firebird_result = normalize_rows(firebird_rows(firebird_sql, 4 if check["kind"] in {"numeric", "date-text"} else 2))
        if sqlite_result != firebird_result:
            mismatches.append(
                {
                    "category": "profile-mismatch",
                    "table": check["table"],
                    "column": check["column"],
                    "kind": check["kind"],
                    "source": firebird_result,
                    "target": sqlite_result,
                }
            )

    status = "pass" if not mismatches else "fail"
    return CheckResult(
        check_id="semantic-profiles",
        category="fidelity-design",
        severity="blocking",
        description="Nullable, typed, and flag-like fields preserve user-visible semantics",
        status=status,
        rationale="Nulls, grades, dates, and flag values drive rendering and filter behavior in the current UI.",
        details={"profiles_checked": PROFILE_CHECKS},
        mismatches=mismatches,
    )


def aggregate_result(con: sqlite3.Connection, definition: dict[str, Any]) -> tuple[list[list[Any]], list[list[Any]]]:
    if definition["shape"] == "scalar":
        sqlite_result = [[normalize_value(sqlite_scalar(con, definition["sqlite"]))]]
        firebird_result = [[normalize_value(firebird_scalar(definition["firebird"]))]]
        return firebird_result, sqlite_result

    if definition["shape"] == "scalar-row":
        sqlite_result = normalize_rows(sqlite_rows(con, definition["sqlite"]))
        firebird_result = normalize_rows(firebird_rows(definition["firebird"], len(sqlite_result[0]) if sqlite_result else 1))
        return firebird_result, sqlite_result

    sqlite_result = normalize_rows(sqlite_rows(con, definition["sqlite"]))
    expected_columns = len(sqlite_result[0]) if sqlite_result else 2
    firebird_result = normalize_rows(firebird_rows(definition["firebird"], expected_columns))
    return firebird_result, sqlite_result


def compare_aggregates(con: sqlite3.Connection) -> list[CheckResult]:
    results: list[CheckResult] = []
    for definition in AGGREGATE_CHECKS:
        try:
            firebird_result, sqlite_result = aggregate_result(con, definition)
            mismatches: list[dict[str, Any]] = []
            if firebird_result != sqlite_result:
                mismatches.append(
                    {
                        "category": "aggregate-mismatch",
                        "endpoint": definition["endpoint"],
                        "source": firebird_result,
                        "target": sqlite_result,
                    }
                )
            status = "pass" if not mismatches else "fail"
        except Exception as exc:  # pragma: no cover - surfaced in report
            status = "fail"
            mismatches = [{"category": "query-error", "message": str(exc), "endpoint": definition["endpoint"]}]
            firebird_result = []
            sqlite_result = []

        results.append(
            CheckResult(
                check_id=definition["id"],
                category="endpoint-aggregates",
                severity=definition["severity"],
                description=definition["description"],
                status=status,
                rationale=f"Validates the aggregate behavior behind {definition['endpoint']}.",
                details={
                    "endpoint": definition["endpoint"],
                    "sqlite_result": sqlite_result,
                    "source_result": firebird_result,
                },
                mismatches=mismatches,
            )
        )
    return results


def summarize(results: list[CheckResult]) -> dict[str, Any]:
    blocking = [result for result in results if result.severity == "blocking"]
    informational = [result for result in results if result.severity == "informational"]
    blocking_failures = sum(1 for result in blocking if result.status != "pass")
    informational_failures = sum(1 for result in informational if result.status != "pass")
    return {
        "status": "PASS" if blocking_failures == 0 else "FAIL",
        "checks_run": len(results),
        "checks_passed": sum(1 for result in results if result.status == "pass"),
        "blocking_failures": blocking_failures,
        "informational_failures": informational_failures,
    }


def write_report(report_path: Path, report: dict[str, Any]) -> None:
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")
    latest_path = report_path.parent / "latest.json"
    if latest_path != report_path:
        latest_path.write_text(json.dumps(report, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")


def default_report_path() -> Path:
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    return DEFAULT_REPORT_DIR / f"migration-fidelity-{stamp}.json"


def validate(target_db: Path, accepted_db: Path, report_path: Path) -> int:
    with sqlite3.connect(target_db) as con:
        results = [
            compare_table_counts(con),
            compare_relationship_integrity(con),
            compare_profiles(con),
            *compare_aggregates(con),
        ]

    report = {
        "generated_at": datetime.now(UTC).isoformat(),
        "source": {
            "firebird_dsn": RUNTIME["fb_dsn"],
            "isql": str(RUNTIME["isql"]),
        },
        "target": {
            "candidate_db": str(target_db),
            "accepted_db": str(accepted_db),
        },
        "workflow": {
            "blocking_endpoints": BLOCKING_ENDPOINTS,
            "informational_endpoints": INFORMATIONAL_ENDPOINTS,
            "canonical_inputs": {
                "source_database": RUNTIME["fb_dsn"],
                "sqlite_candidate": str(target_db),
                "sqlite_accepted": str(accepted_db),
            },
        },
        "summary": summarize(results),
        "checks": [result.as_dict() for result in results],
    }
    write_report(report_path, report)
    print(json.dumps(report["summary"], ensure_ascii=True))
    return 0 if report["summary"]["status"] == "PASS" else 1


def main() -> int:
    args = parse_args()
    apply_runtime(args)
    target_db = Path(args.target_db)
    accepted_db = Path(args.accepted_db)
    report_path = Path(args.report) if args.report else default_report_path()

    if not preflight_diagnostics(target_db):
        return 2

    return validate(target_db, accepted_db, report_path)


if __name__ == "__main__":
    raise SystemExit(main())
