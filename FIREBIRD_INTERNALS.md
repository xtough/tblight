# Firebird Database Internals — Reverse Engineering Notes

Source: gbak restore logs (`gbak_patched.txt` and sibling files) from Tourenbuch VI
backups. These notes inform future feature specs — in particular the
`migration-delta-gate` and `write-capabilities` roadmap changes.

---

## Stored Procedures (39)

### Reporting / selectable (query-like, return result sets)

These were called by the Tourenbuch VI Delphi UI to produce aggregated output. Their
logic is partially reimplemented as plain SQL in `app.py`.

| Procedure | Purpose | app.py coverage |
|---|---|---|
| `PROC_REPORT_STATISTIK` | General statistics report | `/api/stats` (spread across all sub-queries) |
| `REPORT_STAT_JAHR` | Per-year statistics | `/api/stats per_year` |
| `STAT_JAHRE_BEG` / `_1` / `_2` | Ascent counts per year (variants) | `/api/stats per_year` |
| `STAT_JAHRE_1` | Year statistics (variant) | `/api/stats per_year` |
| `COUNT_GRAD_JAHR` | Grade counts per year | `/api/stats grade_dist` — **not cross-tabbed by year; gap** |
| `COUNT_GRDX_JAHR` | Grade-index counts per year | Same gap |
| `BESTIEGENE_GIPFEL` | Summited peaks | `N_GIPFEL` in stats summary |
| `BESTIEGENE_ZIELE` | Summited targets | `N_GEBIETE` in stats summary |
| `GEZ_BEGEHUNGEN` | Counted ascents | `COUNT(*)` in various queries |
| `GET_SEILSCHAFT` | Rope-team lookup for an ascent | JOIN in `/api/begehungen/{id}` → `seilschaft` |
| `GET_BEGEHUNGSDATUM` | Ascent date lookup | Direct column read from `BEGEHUNGEN.DATUM` |
| `LEICHTESTERWEG` | Easiest route per summit | Wege sorted by `GRDX` in gipfel detail — **no scalar "easiest" exposed; gap** |
| `WEGX_ZU_TAG` | Routes per day/tag | Not currently exposed |
| `C_WEG` | Route characterisation lookup | Not currently identified |

### Write / housekeeping (needed for write-capabilities roadmap)

These procedures mutate data or maintain derived state. They have no role in the
current read-only application but must be reimplemented in Python when write endpoints
are added.

| Procedure | Purpose |
|---|---|
| `PCD_MOV_GIPFEL_ID` | Renumber a peak's primary key |
| `PCD_MOV_GIPFELNAME` | Rename a peak |
| `PCD_MOV_WEG` | Move a route to a different peak |
| `PCD_MOV_WEG_GUID` | Move a route by GUID |
| `UPDATE_GRDXBEG` | Update the personal grade for an ascent (`SEILSCHAFT.GRDXBEG`) |
| `RECOUNT_GIPFELBEST` | Recompute `COUNT_GIPFELBEST` for one person/peak pair |
| `RECOUNT_GIPFELBEST_ALL` | Recompute for all peak/person combinations |
| `RECOUNT_GIPFELBEST_ALLPERSONS` | Recompute across all persons |
| `GEN_BEGNR` | Generate the next sequential ascent number (`BEGNR`) |
| `GEN_BEGNR_BEG` | Assign `BEGNR` to a `BEGEHUNGEN` row |
| `GEN_BEGNR_WEG` | Assign `BEGNR` scoped to a route |
| `SAVE_BEGNR` | Persist a `BEGNR` value |
| `REGEN_ALL_BEGNR` | Regenerate all `BEGNR` values in sequence order |
| `NEW_VTAGTYPE` | Create a new virtual tag type |
| `VTAGTYPE_ANLEGEN` | Initialise a tag type with default values |
| `MOV_GLEICHNAMIGEWEGE` | Merge/move same-named routes |

**Key implication for write-capabilities:** Two pieces of derived state maintained by
these procedures must be kept consistent in SQLite when writes happen:

1. **`BEGNR`** — a sequential ascent number assigned per user. `GEN_BEGNR_BEG` drives
   this. The current max can be read from `MAX(BEGNR)` in `BEGEHUNGEN`; new rows
   should increment it.
2. **`COUNT_GIPFELBEST`** — a denormalised count of how many times a person has
   summited a given peak. Maintained by `RECOUNT_GIPFELBEST*`. When a `BEGEHUNGEN`
   or `SEILSCHAFT` row is inserted/deleted, this table must be updated accordingly.

### Admin / destructive (never needed)

| Procedure | Purpose |
|---|---|
| `ALLESLEEREN` | Delete all user data |
| `CLEAN_BEGEHUNGEN` | Purge ascent records |
| `LEEREN` | Clear a table |
| `LEEREN_PERSONELLES` | Clear personal data |
| `RESET_GEN` | Reset a generator to zero |
| `RESET_GEN_BEGNR` | Reset the BEGNR sequence |
| `RESET_GEN_POSNR` | Reset the POSNR sequence |
| `SP_GEN_TBO_IMPORTAUSSCHLUSS_ID` | Generate import-exclusion IDs |
| `TEST` | Development test procedure |

---

## UDFs — External Functions (`F_*`, ~65 functions)

All `F_*` functions are from the **IBSystemFunctions** UDF library (`ibsf_fb21.dll`).
This is a standard Firebird 2.x utility library providing string manipulation, date
arithmetic, BLOB helpers, and expression evaluation.

These functions appear only in stored procedure PSQL code and triggers — never in table
data. Since the migration never executes PSQL, UDFs have zero impact on migration or
the SQLite schema. They are irrelevant to the roadmap.

Functional groups for reference:

- **String**: `F_LEFT`, `F_RIGHT`, `F_MID`, `F_SUBSTR`, `F_LRTRIM`, `F_LTRIM`,
  `F_RTRIM`, `F_PADLEFT`, `F_PADRIGHT`, `F_PROPERCASE`, `F_LINEWRAP`,
  `F_STRINGLENGTH`, `F_FINDWORD`, `F_FINDNTHWORD`, `F_FINDWORDINDEX`,
  `F_STRIPSTRING`, `F_CHARACTER`, `F_CRLF`
- **BLOB**: `F_BLOBASPCHAR`, `F_BLOBSIZE`, `F_BLOBBINCMP`, `F_BLOBLEFT`,
  `F_BLOBRIGHT`, `F_BLOBMID`, `F_BLOBLINE`, `F_BLOBSEGMENTCOUNT`,
  `F_BLOBMAXSEGMENTLENGTH`, `F_BIGLRTRIM`, `F_BIGSTRINGLENGTH`, `F_BIGSUBSTR`,
  `F_STRBLOB`
- **Date/time**: `F_DAYOFMONTH`, `F_DAYOFWEEK`, `F_DAYOFYEAR`, `F_MONTH`,
  `F_QUARTER`, `F_WEEKOFYEAR`, `F_WOY`, `F_YEAR`, `F_YEAROFYEAR`,
  `F_CDOWLONG`, `F_CDOWSHORT`, `F_CMONTHLONG`, `F_CMONTHSHORT`,
  `F_ADDMONTH`, `F_ADDYEAR`, `F_MAXDATE`, `F_MINDATE`, `F_STRIPDATE`,
  `F_STRIPTIME`, `F_AGEINDAYS`, `F_AGEINMONTHS`, `F_AGEINWEEKS`,
  `F_AGEINDAYSTHRESHOLD`, `F_AGEINMONTHSTHRESHOLD`, `F_AGEINWEEKSTHRESHOLD`
- **Numeric**: `F_MODULO`, `F_ROUNDFLOAT`, `F_TRUNCATE`, `F_DOUBLEABS`,
  `F_ISDIVISIBLEBY`, `F_FIXEDPOINT`, `F_DOLLARVAL`
- **Regex / expression**: `F_EVALUATEEXPRESSION`, `F_EVALUATECYCLEEXPRESSION`,
  `F_VALIDATEREGULAREXPRESSION`, `F_VALIDATESTRINGINRE`,
  `F_VALIDATECYCLEEXPRESSION`, `F_VALIDATENAMEFORMAT`
- **Utility**: `F_GENERATESNDXINDEX`, `F_GENERATEFORMATTEDNAME`,
  `F_IBPASSWORD`, `F_IBTEMPPATH`, `F_DEBUG`, `F_SETDEBUGGEROUTPUT`,
  `F_CLOSEDEBUGGEROUTPUT`

---

## Generators (Sequences, ~55)

Firebird generators are equivalent to SQLite `AUTOINCREMENT` sequences. The migration
extracts table data with IDs already assigned; generator current values are not
captured.

**For write-capabilities:** Do not attempt to mirror generator state. Derive the next
safe ID from `SELECT MAX(ID) + 1 FROM <table>` in SQLite, or use SQLite's built-in
`ROWID` / `INTEGER PRIMARY KEY AUTOINCREMENT`.

Key generators and their tables:

| Generator | Table |
|---|---|
| `GEN_BEGEHUNGEN_ID` | `BEGEHUNGEN` |
| `GEN_GIPFEL_ID` | `GIPFEL` |
| `GEN_WEGE_ID` | `WEGE` |
| `GEN_SEILSCHAFT_ID` | `SEILSCHAFT` |
| `GEN_PERSONEN_ID` | `PERSONEN` |
| `GEN_GEBIETE_ID` | `GEBIETE` |
| `GEN_REGIONEN_ID` | `REGIONEN` |
| `GEN_BEGNR` / `GEN_POSNR` | Ascent and position numbering |
| `GEN_BILDER_ID` | `BILDER` (images) |
| `GEN_TAGS_ID` / `GEN_VTAG_ID` | Tag system |
| `GEN_KOORDINATEN_ID` | `KOORDINATEN` |
| `GEN_KOMMENTARE_ID` | `KOMMENTARE` |
| `GEN_KARTEN_ID` | `KARTEN` (maps) |
| `GEN_QUELLEN_ID` | `QUELLEN` (sources) |
| `GEN_SKALEN_ID` | `SKALEN` (grading scales) |
| Various `IMPORT_*`, `SPELL_*`, `TMP_*` | Import and full-text helper tables |

---

## Triggers (~160)

Triggers fire on Firebird INSERT/UPDATE/DELETE. The migration only reads (`SELECT`), so
no trigger ever fires during extraction. All trigger-maintained derived data is already
present in the migrated rows.

Naming convention: `<TABLE>_BI0` = Before Insert priority 0, `_BU0` = Before Update,
`_BD0` = Before Delete, `_AI0` = After Insert, `_AU0` = After Update, `_AD0` = After
Delete. `CHECK_*` triggers implement NOT NULL / CHECK constraints generated by
Firebird.

**Triggers relevant to write-capabilities** — must be replicated in Python:

| Trigger group | What it does |
|---|---|
| `*_BI0` (most tables) | Fires generator to assign next `ID` before insert |
| `BEGEHUNGEN_BI1` / `BEGEHUNGEN_BI2` | Assign `BEGNR` and `GEZ` (sequential numbering) |
| `BEGEHUNGEN_BI3` / `BEGEHUNGEN_BU0` | Maintain `BEGEHUNGEN_IDX_GEZ` ordering |
| `SEILSCHAFT_AI0` / `SEILSCHAFT_AI1` / `SEILSCHAFT_AI2` | Update `COUNT_GIPFELBEST` on new ascent participant |
| `SEILSCHAFT_AD0` / `SEILSCHAFT_AD1` | Update `COUNT_GIPFELBEST` on participant removal |
| `SEILSCHAFT_AU0` / `SEILSCHAFT_AU1` / `SEILSCHAFT_AU2` | Update `COUNT_GIPFELBEST` on participant edit |
| `WEGE_AU*` / `WEGE_BD0` | Propagate grade/route changes to denormalised fields |
| `GIPFEL_AU*` / `GIPFEL_BD0` | Propagate peak changes |
| `GEBIETE_BD0` / `REGIONEN_BD0` | Cascade soft-deletes or nullify FKs |
| `SPELL_*_BI` | Maintain full-text search helper tables (`SPELL_GIPFELNAMEN` etc.) |
| `BEGEHUNGEN_AU0` / `BEGEHUNGEN_AU1` / `BEGEHUNGEN_AU2` | Update derived fields on ascent edit |

**Triggers that can be ignored:**

- `IMPORT_*` — populate import staging tables, not used at runtime
- `TMP_REPORT_*` — populate temp report tables used by stored procedures
- `DB_DATENUPDATELOG_BI` / `DB_INTERNA_BU0` — internal version/audit logging
- `NUTZER_*` — multi-user login management (single-user SQLite app has no `NUTZER`)

---

## Domains

Custom type aliases used throughout the schema. `get_columns()` already resolves these
to base Firebird types via the `RDB$FIELDS` join, so they are transparent to the
migration. Listed for reference:

| Domain | Mapped to |
|---|---|
| `BOOLEAN` | `SMALLINT` (0/1) → SQLite `INTEGER` |
| `GPS` | `DOUBLE PRECISION` → SQLite `REAL` |
| `GUID` | `CHAR(38)` → SQLite `TEXT` |
| `INT` | `INTEGER` → SQLite `INTEGER` |
| `NOTIZ` / `NOTIZ300` | `VARCHAR` / `BLOB SUB_TYPE TEXT` → SQLite `TEXT` |
| `SYMBOL` | `CHAR` → SQLite `TEXT` |
| `TEXT5` … `TEXT300` | `VARCHAR(n)` → SQLite `TEXT` |
| `FELDQ` | `SMALLINT` (quality/flag field) → SQLite `INTEGER` |

---

## Views

None found in this database.

---

## Summary — Roadmap Impact

| Object type | Current migration impact | write-capabilities impact |
|---|---|---|
| Stored procedures (reporting) | None — reimplemented in `app.py` | None |
| Stored procedures (write/housekeeping) | None — not called | Must port: `BEGNR` numbering, `COUNT_GIPFELBEST` maintenance |
| UDFs | None | None |
| Generators | None — IDs already in data | Use `MAX(ID)+1` instead |
| Triggers (`*_BI0` ID assignment) | None | Replace with SQLite autoincrement |
| Triggers (denormalised counts) | None — values already migrated | Must replicate in Python for `SEILSCHAFT` writes |
| Triggers (SPELL full-text) | None | Ignorable unless full-text search is added |
| Domains | Transparent — resolved by `get_columns()` | No change needed |
| Views | N/A | N/A |
