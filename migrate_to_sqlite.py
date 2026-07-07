"""
Migrate Tourenbuch 6 Firebird 2.1 database to SQLite.
Uses isql.exe (FB 2.1) to extract data since Python FB drivers require FB 3+.
"""

import argparse
from pathlib import Path
import sqlite3
import subprocess
import re
import sys

ROOT = Path(__file__).parent

ISQL = r'C:/Program Files/Firebird/Firebird_2_1/bin/isql.exe'
FB_DSN = r'localhost:C:/SAPDevelop/tb/TB6DATENBANK.FDB'
FB_USER = 'SYSDBA'
FB_PASS = 'masterkey'
SQLITE_DB = ROOT / 'TB6.sqlite'
SQLITE_CANDIDATE_DB = ROOT / 'TB6.sqlite.candidate'
VALIDATION_SCRIPT = ROOT / 'validate_migration_fidelity.py'
ER_DIAGRAM_PATH = ROOT / 'ER_diagram.md'
FIELD_SEPARATOR = chr(31)
RECORD_SEPARATOR = chr(30)


def parse_args():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--accepted-db', default=str(SQLITE_DB), help='Accepted SQLite database path')
    parser.add_argument('--candidate-db', default=str(SQLITE_CANDIDATE_DB), help='Candidate SQLite database path written before validation')
    return parser.parse_args()


def isql(sql):
    """Run SQL via isql and return stdout as a string."""
    result = subprocess.run(
        [ISQL, FB_DSN, '-user', FB_USER, '-password', FB_PASS, '-q'],
        input=sql.encode('latin-1'),
        capture_output=True,
        timeout=120,
    )
    return result.stdout.decode('latin-1', errors='replace')


def clean_isql_output(raw):
    raw = re.sub(r'^Database:.*?(\r?\n)', '', raw)
    return raw.replace('SQL> ', '')


def get_tables():
    out = isql("SELECT TRIM(RDB$RELATION_NAME) FROM RDB$RELATIONS "
               "WHERE RDB$SYSTEM_FLAG = 0 AND RDB$VIEW_BLR IS NULL "
               "ORDER BY 1;")
    tables = []
    for line in out.splitlines():
        line = line.strip()
        if (
            line
            and line.upper() not in ('', 'TRIM')
            and not line.startswith('=')
            and not line.startswith('Database')
            and not line.startswith('SQL>')
        ):
            tables.append(line)
    return tables


def get_columns(table):
    """Return list of (name, type_str) for a table."""
    sql = f"""
SELECT TRIM(rf.RDB$FIELD_NAME),
       f.RDB$FIELD_TYPE,
       f.RDB$FIELD_SUB_TYPE,
       f.RDB$FIELD_SCALE,
       f.RDB$FIELD_LENGTH
FROM RDB$RELATION_FIELDS rf
JOIN RDB$FIELDS f ON f.RDB$FIELD_NAME = rf.RDB$FIELD_SOURCE
WHERE TRIM(rf.RDB$RELATION_NAME) = '{table}'
ORDER BY rf.RDB$FIELD_POSITION;
"""
    out = isql(sql)
    columns = []
    for line in out.splitlines():
        line = line.strip()
        if not line or line.startswith('=') or line.startswith('Database') or line.startswith('RDB$'):
            continue
        parts = line.split()
        if len(parts) >= 2:
            name = parts[0]
            try:
                ftype = int(parts[1])
                sub   = int(parts[2]) if len(parts) > 2 else 0
                scale = int(parts[3]) if len(parts) > 3 else 0
            except ValueError:
                continue
            columns.append((name, ftype, sub, scale))
    return columns


def fb_to_sqlite_type(ftype, sub, scale):
    if ftype in (7, 8, 16):   # SMALLINT, INTEGER, INT64
        return 'REAL' if scale < 0 else 'INTEGER'
    if ftype in (10, 11, 27): # FLOAT, D_FLOAT, DOUBLE
        return 'REAL'
    if ftype in (12, 13, 35): # DATE, TIME, TIMESTAMP
        return 'TEXT'
    if ftype == 261:          # BLOB
        return 'TEXT' if sub == 1 else 'BLOB'
    if ftype == 23:           # BOOLEAN
        return 'INTEGER'
    return 'TEXT'


def get_foreign_keys():
    """Return list of (table, column, ref_table, ref_column) for ER diagram."""
    sql = """
SELECT TRIM(rc.RDB$RELATION_NAME),
       TRIM(iseg.RDB$FIELD_NAME),
       TRIM(refc.RDB$RELATION_NAME),
       TRIM(fseg.RDB$FIELD_NAME)
FROM RDB$RELATION_CONSTRAINTS rc
JOIN RDB$REF_CONSTRAINTS ref ON ref.RDB$CONSTRAINT_NAME = rc.RDB$CONSTRAINT_NAME
JOIN RDB$RELATION_CONSTRAINTS refc ON refc.RDB$CONSTRAINT_NAME = ref.RDB$CONST_NAME_UQ
JOIN RDB$INDEX_SEGMENTS iseg ON iseg.RDB$INDEX_NAME = rc.RDB$INDEX_NAME
JOIN RDB$INDEX_SEGMENTS fseg ON fseg.RDB$INDEX_NAME = refc.RDB$INDEX_NAME
WHERE rc.RDB$CONSTRAINT_TYPE = 'FOREIGN KEY'
ORDER BY 1, 2;
"""
    out = isql(sql)
    fks = []
    for line in out.splitlines():
        line = line.strip()
        if not line or line.startswith('=') or line.startswith('Database') or line.startswith('RDB$'):
            continue
        parts = line.split()
        if len(parts) == 4:
            fks.append(tuple(parts))
    return fks


def export_table_csv(table):
    """Export all rows of a table as CSV text via isql SET LIST + parsing."""
    # Use SET HEADING OFF + SELECT to get clean output
    sql = f"SET HEADING OFF;\nSELECT * FROM \"{table}\";\n"
    result = subprocess.run(
        [ISQL, FB_DSN, '-user', FB_USER, '-password', FB_PASS, '-q'],
        input=sql.encode('latin-1'),
        capture_output=True,
        timeout=300,
    )
    return result.stdout.decode('latin-1', errors='replace')


def get_row_count(table):
    out = isql(f'SELECT COUNT(*) FROM "{table}";')
    for line in out.splitlines():
        line = line.strip()
        if re.match(r'^\d+$', line):
            return int(line)
    return 0


def build_export_select(columns):
    cast_cols = []
    for name, ftype, sub, scale in columns:
        if ftype == 261:  # BLOB
            cast_expr = f'CAST("{name}" AS VARCHAR(32000))'
        elif ftype in (12, 35):  # DATE, TIMESTAMP
            cast_expr = f'CAST("{name}" AS VARCHAR(30))'
        elif ftype == 13:  # TIME
            cast_expr = f'CAST("{name}" AS VARCHAR(20))'
        else:
            cast_expr = f'CAST("{name}" AS VARCHAR(500))'
        cast_cols.append(f"COALESCE({cast_expr}, '<null>')")
    return ' || ASCII_CHAR(31) || '.join(cast_cols) + ' || ASCII_CHAR(30)'


def export_table_records(table, columns):
    sql = f'SET HEADING OFF;\nSELECT {build_export_select(columns)} FROM "{table}";\n'
    result = subprocess.run(
        [ISQL, FB_DSN, '-user', FB_USER, '-password', FB_PASS, '-q'],
        input=sql.encode('latin-1'),
        capture_output=True,
        timeout=300,
    )
    raw = clean_isql_output(result.stdout.decode('latin-1', errors='replace'))
    for record in raw.split(RECORD_SEPARATOR):
        if not record.strip():
            continue
        yield record.split(FIELD_SEPARATOR)


def migrate(sqlite_db):
    print(f"Getting table list...")
    tables = get_tables()
    print(f"Found {len(tables)} tables\n")

    sqlite_db = Path(sqlite_db)
    sq = sqlite3.connect(sqlite_db)
    sq.execute("PRAGMA journal_mode=WAL")
    sq.execute("PRAGMA foreign_keys=OFF")

    for table in tables:
        row_count = get_row_count(table)
        columns = get_columns(table)
        if not columns:
            print(f"  {table}: no columns, skipping")
            continue

        col_defs  = [f'"{n}" {fb_to_sqlite_type(t, s, sc)}' for n, t, s, sc in columns]
        col_names = [n for n, *_ in columns]

        sq.execute(f'DROP TABLE IF EXISTS "{table}"')
        sq.execute(f'CREATE TABLE "{table}" ({", ".join(col_defs)})')

        if row_count == 0:
            print(f"  {table}: 0 rows")
            sq.commit()
            continue

        rows_inserted = 0
        placeholders = ', '.join('?' * len(col_names))
        quoted_cols = ', '.join(f'"{c}"' for c in col_names)
        insert_sql = f'INSERT INTO "{table}" ({quoted_cols}) VALUES ({placeholders})'

        for parts in export_table_records(table, columns):
            if len(parts) != len(col_names):
                continue
            row = []
            for val, (_, ftype, sub, scale) in zip(parts, columns):
                val = val.strip()
                if val == '<null>':
                    row.append(None)
                elif ftype in (7, 8, 16) and scale == 0:
                    try:
                        row.append(int(val))
                    except ValueError:
                        row.append(val or None)
                elif ftype in (7, 8, 16) and scale < 0:
                    try:
                        row.append(float(val))
                    except ValueError:
                        row.append(val or None)
                elif ftype in (10, 11, 27):
                    try:
                        row.append(float(val))
                    except ValueError:
                        row.append(val or None)
                elif ftype == 23:
                    row.append(1 if val in ('T', '1', 'true', 'TRUE') else 0 if val in ('F', '0', 'false', 'FALSE') else None)
                else:
                    row.append(val if val else None)
            sq.execute(insert_sql, row)
            rows_inserted += 1

        sq.commit()
        print(f"  {table}: {rows_inserted}/{row_count} rows")

    sq.execute("PRAGMA wal_checkpoint(FULL)")
    sq.execute("PRAGMA journal_mode=DELETE")
    sq.close()
    print(f"\nSQLite database written to: {sqlite_db}")
    return tables


def generate_er_diagram(tables, output_path=ER_DIAGRAM_PATH):
    print("\nFetching foreign keys for ER diagram...")
    fks = get_foreign_keys()

    # Only include tables that have FKs or are referenced
    fk_tables = set()
    for t, c, rt, rc in fks:
        fk_tables.add(t)
        fk_tables.add(rt)

    # Exclude import/temp/report tables to keep the diagram readable
    exclude_prefixes = ('IMPORT_', 'TMP_', 'SPELL_', 'DB_', 'MONATSNAMEN')
    core_tables = [t for t in tables
                   if t in fk_tables
                   and not any(t.startswith(p) for p in exclude_prefixes)]

    lines = ['erDiagram']
    for t in sorted(core_tables):
        lines.append('    ' + t + ' {}')

    seen = set()
    for src_t, src_c, dst_t, dst_c in fks:
        if src_t not in set(core_tables) or dst_t not in set(core_tables):
            continue
        key = (src_t, dst_t, src_c)
        if key in seen:
            continue
        seen.add(key)
        lines.append(f'    {dst_t} ||--o{{ {src_t} : "{src_c}"')

    diagram = '\n'.join(lines)

    output_path = Path(output_path)
    with output_path.open('w', encoding='utf-8') as f:
        f.write('```mermaid\n')
        f.write(diagram)
        f.write('\n```\n')

    print(f"ER diagram written to: {output_path}")
    return diagram


def cleanup_sidecars(sqlite_db):
    sqlite_db = Path(sqlite_db)
    for suffix in ('-wal', '-shm'):
        sidecar = Path(str(sqlite_db) + suffix)
        if sidecar.exists():
            sidecar.unlink()


def run_validation(candidate_db, accepted_db):
    result = subprocess.run(
        [
            sys.executable,
            str(VALIDATION_SCRIPT),
            '--target-db',
            str(candidate_db),
            '--accepted-db',
            str(accepted_db),
        ],
        check=False,
    )
    return result.returncode


def promote_candidate(candidate_db, accepted_db):
    candidate_db = Path(candidate_db)
    accepted_db = Path(accepted_db)
    previous_db = Path(str(accepted_db) + '.previous')

    cleanup_sidecars(candidate_db)
    cleanup_sidecars(accepted_db)

    if previous_db.exists():
        previous_db.unlink()

    if accepted_db.exists():
        accepted_db.replace(previous_db)

    candidate_db.replace(accepted_db)
    print(f"Promoted validated SQLite database to: {accepted_db}")


if __name__ == '__main__':
    args = parse_args()
    accepted_db = Path(args.accepted_db)
    candidate_db = Path(args.candidate_db)

    tables = migrate(candidate_db)
    diagram = generate_er_diagram(tables)
    print("\n--- ER Diagram (Mermaid) ---")
    print(diagram)

    validation_code = run_validation(candidate_db, accepted_db)
    if validation_code != 0:
        print(f"\nMigration fidelity validation failed. Candidate database kept at: {candidate_db}")
        print(f"Accepted SQLite database remains unchanged at: {accepted_db}")
        raise SystemExit(validation_code)

    promote_candidate(candidate_db, accepted_db)
