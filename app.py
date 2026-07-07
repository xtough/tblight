"""
Tourenbuch 6 — Web Frontend Backend
FastAPI + SQLite (read-only)
"""

import sqlite3
from pathlib import Path
from contextlib import contextmanager
from typing import Optional

from fastapi import FastAPI, Query
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

DB = Path(__file__).parent / "TB6.sqlite"

app = FastAPI(title="Tourenbuch 6")
app.mount("/static", StaticFiles(directory=Path(__file__).parent / "static"), name="static")


@contextmanager
def db():
    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA query_only = ON")
    try:
        yield con
    finally:
        con.close()


def rows(con, sql, params=()):
    return [dict(r) for r in con.execute(sql, params).fetchall()]


def one(con, sql, params=()):
    r = con.execute(sql, params).fetchone()
    return dict(r) if r else None


# ── Root ────────────────────────────────────────────────────────────────────

@app.get("/", include_in_schema=False)
def root():
    return FileResponse(Path(__file__).parent / "static" / "index.html")


# ── Lookups ─────────────────────────────────────────────────────────────────

@app.get("/api/regionen")
def get_regionen():
    with db() as con:
        return rows(con, """
            SELECT r.ID, r.REGION, r.NAME2, l.LAND
            FROM REGIONEN r LEFT JOIN LAND l ON l.ID = r.LAND_ID
            ORDER BY r.REGION
        """)


@app.get("/api/gebiete")
def get_gebiete(region_id: Optional[int] = None):
    with db() as con:
        sql = """
            SELECT g.ID, g.GEBIET, g.NAME2, g.REGION_ID, g.NOTIZ,
                   r.REGION, gs.GESTEIN,
                   (SELECT COUNT(*) FROM GIPFEL gp WHERE gp.GEBIET_ID = g.ID) as N_GIPFEL,
                   (SELECT COUNT(*) FROM GIPFEL gp
                    JOIN WEGE w ON w.GIPFEL_ID = gp.ID
                    WHERE gp.GEBIET_ID = g.ID) as N_WEGE
            FROM GEBIETE g
            LEFT JOIN REGIONEN r ON r.ID = g.REGION_ID
            LEFT JOIN GESTEINE gs ON gs.ID = g.GESTEIN
        """
        if region_id:
            return rows(con, sql + " WHERE g.REGION_ID = ? ORDER BY g.GEBIET", (region_id,))
        return rows(con, sql + " ORDER BY g.GEBIET")


@app.get("/api/grade_lookup")
def get_grade_lookup():
    with db() as con:
        return rows(con, "SELECT GRDX, GRD, GRDR FROM GRADE ORDER BY GRDX")


@app.get("/api/personen")
def get_personen():
    with db() as con:
        return rows(con, """
            SELECT ID, NAME, VORNAME, SPITZNAME,
                   (SELECT COUNT(*) FROM SEILSCHAFT s WHERE s.PERSON_ID = PERSONEN.ID) as N_BEGEHUNGEN
            FROM PERSONEN ORDER BY NAME, VORNAME
        """)


# ── Gipfel ───────────────────────────────────────────────────────────────────

@app.get("/api/gipfel")
def get_gipfel(
    gebiet_id: Optional[int] = None,
    search: Optional[str] = None,
    page: int = 1,
    page_size: int = 50,
):
    with db() as con:
        conditions, params = [], []
        if gebiet_id:
            conditions.append("gp.GEBIET_ID = ?")
            params.append(gebiet_id)
        if search:
            conditions.append("(gp.GIPFEL LIKE ? OR gp.NAME2 LIKE ?)")
            params += [f"%{search}%", f"%{search}%"]

        where = ("WHERE " + " AND ".join(conditions)) if conditions else ""
        total = con.execute(
            f"SELECT COUNT(*) FROM GIPFEL gp {where}", params
        ).fetchone()[0]

        sql = f"""
            SELECT gp.ID, gp.GIPFEL, gp.NAME2, gp.H, gp.GPS_B, gp.GPS_L,
                   ge.GEBIET, ge.ID as GEBIET_ID,
                   gt.TYP as GIPFELTYP,
                   (SELECT COUNT(*) FROM WEGE w WHERE w.GIPFEL_ID = gp.ID) as N_WEGE,
                   (SELECT COUNT(*) FROM WEGE w
                    JOIN BEGEHUNGEN b ON b.WEG_ID = w.ID
                    WHERE w.GIPFEL_ID = gp.ID) as N_BEGEHUNGEN
            FROM GIPFEL gp
            LEFT JOIN GEBIETE ge ON ge.ID = gp.GEBIET_ID
            LEFT JOIN GIPFELTYPEN gt ON gt.ID = gp.TYP
            {where}
            ORDER BY ge.GEBIET, gp.GIPFEL
            LIMIT ? OFFSET ?
        """
        params += [page_size, (page - 1) * page_size]
        return {"total": total, "page": page, "page_size": page_size, "items": rows(con, sql, params)}


@app.get("/api/gipfel/{gipfel_id}")
def get_gipfel_detail(gipfel_id: int):
    with db() as con:
        gipfel = one(con, """
            SELECT gp.*, ge.GEBIET, r.REGION, gt.TYP as GIPFELTYP
            FROM GIPFEL gp
            LEFT JOIN GEBIETE ge ON ge.ID = gp.GEBIET_ID
            LEFT JOIN REGIONEN r ON r.ID = ge.REGION_ID
            LEFT JOIN GIPFELTYPEN gt ON gt.ID = gp.TYP
            WHERE gp.ID = ?
        """, (gipfel_id,))
        if not gipfel:
            return {}
        wege = rows(con, """
            SELECT w.ID, w.WEG, w.NAME2, w.GRDX, g.GRDR as GRAD_TEXT, w.GRDXOU, w.GRDXRP,
                   w.QW, w.NOTIZ, w.CRUX, w.TIPP,
                   (SELECT COUNT(*) FROM BEGEHUNGEN b WHERE b.WEG_ID = w.ID) as N_BEGEHUNGEN
            FROM WEGE w
            LEFT JOIN GRADE g ON g.GRDX = w.GRDX
            WHERE w.GIPFEL_ID = ?
            ORDER BY w.GRDX, w.WEG
        """, (gipfel_id,))
        gipfel["wege"] = wege
        return gipfel


# ── Wege ─────────────────────────────────────────────────────────────────────

@app.get("/api/wege")
def get_wege(
    gipfel_id: Optional[int] = None,
    gebiet_id: Optional[int] = None,
    grdx_min: Optional[int] = None,
    grdx_max: Optional[int] = None,
    search: Optional[str] = None,
    page: int = 1,
    page_size: int = 50,
):
    with db() as con:
        conditions, params = [], []
        if gipfel_id:
            conditions.append("w.GIPFEL_ID = ?")
            params.append(gipfel_id)
        if gebiet_id:
            conditions.append("gp.GEBIET_ID = ?")
            params.append(gebiet_id)
        if grdx_min is not None:
            conditions.append("w.GRDX >= ?")
            params.append(grdx_min)
        if grdx_max is not None:
            conditions.append("w.GRDX <= ?")
            params.append(grdx_max)
        if search:
            conditions.append("(w.WEG LIKE ? OR w.NAME2 LIKE ? OR gp.GIPFEL LIKE ?)")
            params += [f"%{search}%", f"%{search}%", f"%{search}%"]

        where = ("WHERE " + " AND ".join(conditions)) if conditions else ""
        count_sql = f"""
            SELECT COUNT(*) FROM WEGE w
            JOIN GIPFEL gp ON gp.ID = w.GIPFEL_ID
            {where}
        """
        total = con.execute(count_sql, params).fetchone()[0]

        sql = f"""
            SELECT w.ID, w.WEG, w.NAME2, w.GRDX, g.GRDR as GRAD_TEXT,
                   w.GRDXOU, gou.GRDR as GRAD_OU_TEXT,
                   w.GRDXRP, grp.GRDR as GRAD_RP_TEXT,
                   w.QW, w.BESCHREIBUNG, w.CRUX, w.TIPP,
                   gp.GIPFEL, gp.ID as GIPFEL_ID,
                   ge.GEBIET, ge.ID as GEBIET_ID,
                   (SELECT COUNT(*) FROM BEGEHUNGEN b WHERE b.WEG_ID = w.ID) as N_BEGEHUNGEN,
                   (SELECT GROUP_CONCAT(c.CHARAKTER, ', ')
                    FROM VC vc JOIN "C" c ON c.ID = vc.C
                    WHERE vc.WEG_ID = w.ID) as CHARAKTER,
                   (SELECT GROUP_CONCAT(s.SIART, ', ')
                    FROM VS vs JOIN S s ON s.ID = vs.S
                    WHERE vs.WEG_ID = w.ID) as SICHERUNG
            FROM WEGE w
            JOIN GIPFEL gp ON gp.ID = w.GIPFEL_ID
            LEFT JOIN GEBIETE ge ON ge.ID = gp.GEBIET_ID
            LEFT JOIN GRADE g ON g.GRDX = w.GRDX
            LEFT JOIN GRADE gou ON gou.GRDX = w.GRDXOU
            LEFT JOIN GRADE grp ON grp.GRDX = w.GRDXRP
            {where}
            ORDER BY ge.GEBIET, gp.GIPFEL, w.GRDX, w.WEG
            LIMIT ? OFFSET ?
        """
        params += [page_size, (page - 1) * page_size]
        return {"total": total, "page": page, "page_size": page_size, "items": rows(con, sql, params)}


@app.get("/api/wege/{weg_id}")
def get_weg_detail(weg_id: int):
    with db() as con:
        weg = one(con, """
            SELECT w.*, g.GRDR as GRAD_TEXT,
                   gp.GIPFEL, gp.GPS_B, gp.GPS_L,
                   ge.GEBIET, ge.ID as GEBIET_ID, r.REGION
            FROM WEGE w
            JOIN GIPFEL gp ON gp.ID = w.GIPFEL_ID
            LEFT JOIN GEBIETE ge ON ge.ID = gp.GEBIET_ID
            LEFT JOIN REGIONEN r ON r.ID = ge.REGION_ID
            LEFT JOIN GRADE g ON g.GRDX = w.GRDX
            WHERE w.ID = ?
        """, (weg_id,))
        if not weg:
            return {}

        weg["charakter"] = rows(con,
            'SELECT c.CHARAKTER FROM VC vc JOIN "C" c ON c.ID = vc.C WHERE vc.WEG_ID = ?',
            (weg_id,))
        weg["sicherung"] = rows(con,
            "SELECT s.SIART FROM VS vs JOIN S s ON s.ID = vs.S WHERE vs.WEG_ID = ?",
            (weg_id,))
        weg["anforderung"] = rows(con,
            "SELECT a.ANFORDERUNG FROM VA va JOIN A a ON a.ID = va.A WHERE va.WEG_ID = ?",
            (weg_id,))
        weg["neigung"] = rows(con,
            "SELECT n.NEIGUNG FROM VN vn JOIN N n ON n.ID = vn.N WHERE vn.WEG_ID = ?",
            (weg_id,))
        weg["begehungen"] = rows(con, """
            SELECT b.ID, b.DATUM, b.NOTIZ,
                   GROUP_CONCAT(p.VORNAME || ' ' || p.NAME, ', ') as PARTNER,
                   bs.STIL as STIL,
                   bg.ART as ART
            FROM BEGEHUNGEN b
            LEFT JOIN SEILSCHAFT s ON s.BEGEHUNG_ID = b.ID
            LEFT JOIN PERSONEN p ON p.ID = s.PERSON_ID
            LEFT JOIN BEGSTIL bs ON bs.ID = s.STIL
            LEFT JOIN BEGART bg ON bg.ID = s.ART
            WHERE b.WEG_ID = ?
            GROUP BY b.ID ORDER BY b.DATUM DESC
        """, (weg_id,))
        return weg


# ── Begehungen ───────────────────────────────────────────────────────────────

@app.get("/api/begehungen")
def get_begehungen(
    person_id: Optional[int] = None,
    year: Optional[int] = None,
    page: int = 1,
    page_size: int = 50,
):
    with db() as con:
        conditions, params = [], []
        if person_id:
            conditions.append("""b.ID IN (
                SELECT BEGEHUNG_ID FROM SEILSCHAFT WHERE PERSON_ID = ?)""")
            params.append(person_id)
        if year:
            conditions.append("strftime('%Y', b.DATUM) = ?")
            params.append(str(year))

        where = ("WHERE " + " AND ".join(conditions)) if conditions else ""
        total = con.execute(
            f"SELECT COUNT(*) FROM BEGEHUNGEN b {where}", params
        ).fetchone()[0]

        sql = f"""
            SELECT b.ID, b.DATUM, b.NOTIZ,
                   w.WEG, w.ID as WEG_ID,
                   w.GRDX, g.GRDR as GRAD_TEXT,
                   gp.GIPFEL, gp.ID as GIPFEL_ID,
                   ge.GEBIET, ge.ID as GEBIET_ID,
                   GROUP_CONCAT(DISTINCT p.VORNAME || ' ' || p.NAME) as PARTNER,
                   GROUP_CONCAT(DISTINCT bs.STIL) as STIL
            FROM BEGEHUNGEN b
            JOIN WEGE w ON w.ID = b.WEG_ID
            JOIN GIPFEL gp ON gp.ID = w.GIPFEL_ID
            LEFT JOIN GEBIETE ge ON ge.ID = gp.GEBIET_ID
            LEFT JOIN GRADE g ON g.GRDX = w.GRDX
            LEFT JOIN SEILSCHAFT s ON s.BEGEHUNG_ID = b.ID
            LEFT JOIN PERSONEN p ON p.ID = s.PERSON_ID
            LEFT JOIN BEGSTIL bs ON bs.ID = s.STIL
            {where}
            GROUP BY b.ID
            ORDER BY b.DATUM DESC
            LIMIT ? OFFSET ?
        """
        params += [page_size, (page - 1) * page_size]
        return {"total": total, "page": page, "page_size": page_size, "items": rows(con, sql, params)}


@app.get("/api/begehungen/{beg_id}")
def get_begehung_detail(beg_id: int):
    with db() as con:
        beg = one(con, """
            SELECT b.*, w.WEG, w.GRDX, g.GRDR as GRAD_TEXT,
                   gp.GIPFEL, ge.GEBIET, r.REGION
            FROM BEGEHUNGEN b
            JOIN WEGE w ON w.ID = b.WEG_ID
            JOIN GIPFEL gp ON gp.ID = w.GIPFEL_ID
            LEFT JOIN GEBIETE ge ON ge.ID = gp.GEBIET_ID
            LEFT JOIN REGIONEN r ON r.ID = ge.REGION_ID
            LEFT JOIN GRADE g ON g.GRDX = w.GRDX
            WHERE b.ID = ?
        """, (beg_id,))
        if not beg:
            return {}
        beg["seilschaft"] = rows(con, """
            SELECT s.ID, s.VERSUCH, s.GRDXBEG, gr.GRDR as GRAD_BEG_TEXT,
                   p.NAME, p.VORNAME, p.SPITZNAME,
                   bg.ART, bs.STIL as STIL, s.NOTIZ
            FROM SEILSCHAFT s
            LEFT JOIN PERSONEN p ON p.ID = s.PERSON_ID
            LEFT JOIN BEGART bg ON bg.ID = s.ART
            LEFT JOIN BEGSTIL bs ON bs.ID = s.STIL
            LEFT JOIN GRADE gr ON gr.GRDX = s.GRDXBEG
            WHERE s.BEGEHUNG_ID = ?
            ORDER BY s.POSNR
        """, (beg_id,))
        return beg


# ── Statistik ────────────────────────────────────────────────────────────────

@app.get("/api/stats")
def get_stats():
    with db() as con:
        # Ascents per year
        per_year = rows(con, """
            SELECT strftime('%Y', DATUM) as JAHR, COUNT(*) as N
            FROM BEGEHUNGEN WHERE DATUM IS NOT NULL
            GROUP BY JAHR ORDER BY JAHR
        """)

        # Grade distribution of ascents
        grade_dist = rows(con, """
            SELECT g.GRDR as GRAD, COUNT(*) as N
            FROM BEGEHUNGEN b
            JOIN WEGE w ON w.ID = b.WEG_ID
            JOIN GRADE g ON g.GRDX = w.GRDX
            WHERE w.GRDX IS NOT NULL AND w.GRDX > 0
            GROUP BY w.GRDX ORDER BY w.GRDX
        """)

        # Top partners (by ascent count)
        top_partners = rows(con, """
            SELECT p.VORNAME || ' ' || p.NAME as NAME, COUNT(*) as N
            FROM SEILSCHAFT s
            JOIN PERSONEN p ON p.ID = s.PERSON_ID
            GROUP BY s.PERSON_ID ORDER BY N DESC LIMIT 10
        """)

        # Areas visited
        areas_visited = rows(con, """
            SELECT ge.GEBIET, COUNT(DISTINCT b.ID) as N_BEGEHUNGEN,
                   COUNT(DISTINCT gp.ID) as N_GIPFEL
            FROM BEGEHUNGEN b
            JOIN WEGE w ON w.ID = b.WEG_ID
            JOIN GIPFEL gp ON gp.ID = w.GIPFEL_ID
            JOIN GEBIETE ge ON ge.ID = gp.GEBIET_ID
            GROUP BY ge.ID ORDER BY N_BEGEHUNGEN DESC LIMIT 15
        """)

        # Summary counts
        summary = one(con, """
            SELECT
                (SELECT COUNT(*) FROM BEGEHUNGEN) as N_BEGEHUNGEN,
                (SELECT COUNT(DISTINCT WEG_ID) FROM BEGEHUNGEN) as N_WEGE,
                (SELECT COUNT(DISTINCT gp.ID)
                 FROM BEGEHUNGEN b JOIN WEGE w ON w.ID=b.WEG_ID
                 JOIN GIPFEL gp ON gp.ID=w.GIPFEL_ID) as N_GIPFEL,
                (SELECT COUNT(DISTINCT ge.ID)
                 FROM BEGEHUNGEN b JOIN WEGE w ON w.ID=b.WEG_ID
                 JOIN GIPFEL gp ON gp.ID=w.GIPFEL_ID
                 JOIN GEBIETE ge ON ge.ID=gp.GEBIET_ID) as N_GEBIETE,
                (SELECT MIN(DATUM) FROM BEGEHUNGEN WHERE DATUM IS NOT NULL) as ERSTE,
                (SELECT MAX(DATUM) FROM BEGEHUNGEN WHERE DATUM IS NOT NULL) as LETZTE
        """)

        return {
            "summary": summary,
            "per_year": per_year,
            "grade_dist": grade_dist,
            "top_partners": top_partners,
            "areas_visited": areas_visited,
        }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)
