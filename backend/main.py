"""Backend API for the Rural Travel Co-op prototype (sample data only).

Run locally:  uvicorn main:app --reload      (from the backend folder)
API docs:     http://localhost:8000/docs

Done on Day 1:  /health, /cities, /trips
Day 5: /members saves sign ups (free Tier 1 or paid Tier 2) and /members/count summarizes them.
Day 4: /clicks logs referral clicks in SQLite and /clicks/report summarizes them.
Day 2: trips now live in a database instead of a Python list.
Week 9 Day 2: set DATABASE_URL to use hosted Postgres (Neon); without it a local SQLite file is used.
"""
import os
import sqlite3
from pathlib import Path
from datetime import date
from typing import Optional

from fastapi import Depends, FastAPI, Header, HTTPException, Query
from pydantic import BaseModel, Field

import arr_data
import gobus_data
from data import TRIPS

app = FastAPI(title="Rural Travel Co-op API (prototype)")

# Week 9 Day 2: if the DATABASE_URL environment variable is set (the Neon connection string),
# the API uses that hosted Postgres database. If it is not set, it uses a local SQLite file,
# so running on your own computer still works with no setup.
DATABASE_URL = os.environ.get("DATABASE_URL", "").strip()
USE_POSTGRES = DATABASE_URL.startswith("postgres")
DB_PATH = Path(__file__).parent / "trips.db"

if USE_POSTGRES:
    import psycopg
    from psycopg.rows import dict_row


class Db:
    """Small wrapper so the rest of the code does not care which database is behind it."""

    def __init__(self) -> None:
        if USE_POSTGRES:
            self.conn = psycopg.connect(DATABASE_URL, row_factory=dict_row, connect_timeout=15)
        else:
            self.conn = sqlite3.connect(DB_PATH)
            self.conn.row_factory = sqlite3.Row   # lets us read columns by name

    def execute(self, sql: str, params: tuple = ()):
        if USE_POSTGRES:
            sql = sql.replace("?", "%s")           # Postgres uses %s, SQLite uses ?
        return self.conn.execute(sql, params)

    def insert(self, sql: str, params: tuple = ()) -> int:
        """Run an INSERT and return the new row id."""
        if USE_POSTGRES:
            return self.execute(sql + " RETURNING id", params).fetchone()["id"]
        return self.execute(sql, params).lastrowid

    def commit(self) -> None:
        self.conn.commit()

    def close(self) -> None:
        self.conn.close()


def get_db() -> Db:
    return Db()


SQLITE_SCHEMA = """
CREATE TABLE IF NOT EXISTS operators (
    id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL UNIQUE, mode TEXT NOT NULL,
    is_partner INTEGER NOT NULL DEFAULT 0, booking_url TEXT, notes TEXT);
CREATE TABLE IF NOT EXISTS trips (
    id INTEGER PRIMARY KEY AUTOINCREMENT, operator_id INTEGER NOT NULL REFERENCES operators(id),
    origin TEXT NOT NULL, destination TEXT NOT NULL, depart_time TEXT NOT NULL,
    arrive_time TEXT NOT NULL, price REAL NOT NULL, days_running TEXT, season_start TEXT,
    season_end TEXT, booking_url TEXT, source_url TEXT, last_updated TEXT DEFAULT CURRENT_DATE,
    is_sample INTEGER NOT NULL DEFAULT 0, is_active INTEGER NOT NULL DEFAULT 1,
    fare_estimated INTEGER NOT NULL DEFAULT 0);
CREATE TABLE IF NOT EXISTS clicks (
    id INTEGER PRIMARY KEY AUTOINCREMENT, ref TEXT NOT NULL,
    trip_id INTEGER NOT NULL REFERENCES trips(id), riders INTEGER NOT NULL DEFAULT 1,
    price_at_click REAL NOT NULL, confirmed INTEGER NOT NULL DEFAULT 0,
    clicked_at TEXT DEFAULT CURRENT_TIMESTAMP, confirmed_at TEXT);
CREATE TABLE IF NOT EXISTS members (
    id INTEGER PRIMARY KEY AUTOINCREMENT, email TEXT NOT NULL UNIQUE,
    tier INTEGER NOT NULL, created_at TEXT DEFAULT CURRENT_TIMESTAMP);
CREATE TABLE IF NOT EXISTS partner_weekly_reports (
    id INTEGER PRIMARY KEY AUTOINCREMENT, operator_id INTEGER NOT NULL REFERENCES operators(id),
    week_start TEXT NOT NULL, route_label TEXT NOT NULL, partner_sales_total REAL NOT NULL,
    tagged_tickets INTEGER NOT NULL DEFAULT 0, tagged_value REAL NOT NULL DEFAULT 0, notes TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP, UNIQUE (operator_id, week_start, route_label));
"""


def setup_database() -> None:
    """Create the tables if needed and fill them with the made up sample trips if empty."""
    db = get_db()
    if USE_POSTGRES:
        # schema.sql is the same file you ran in the Neon SQL Editor. It is safe to run again.
        db.conn.execute((Path(__file__).parent / "schema.sql").read_text())
    else:
        cols = [r["name"] for r in db.execute("PRAGMA table_info(trips)").fetchall()]
        if cols and "operator_id" not in cols:
            # An old trips.db from before Week 9 has a different layout. It only held sample data,
            # so it is safe to remove and rebuild.
            for table in ("clicks", "members", "trips"):
                db.execute(f"DROP TABLE IF EXISTS {table}")
        db.conn.executescript(SQLITE_SCHEMA)
        cols = [r["name"] for r in db.execute("PRAGMA table_info(trips)").fetchall()]
        if "is_active" not in cols:
            db.execute("ALTER TABLE trips ADD COLUMN is_active INTEGER NOT NULL DEFAULT 1")
        if "fare_estimated" not in cols:
            db.execute("ALTER TABLE trips ADD COLUMN fare_estimated INTEGER NOT NULL DEFAULT 0")
    seed_demo_trips(db)
    load_arr_trips(db)
    load_gobus_trips(db)
    db.commit()
    db.close()


def get_operator_id(db: Db, name: str, mode: str, is_partner: bool, url: str, notes: str = "") -> int:
    row = db.execute("SELECT id FROM operators WHERE name = ?", (name,)).fetchone()
    if row:
        return row["id"]
    return db.insert("INSERT INTO operators (name, mode, is_partner, booking_url, notes) "
                     "VALUES (?,?,?,?,?)", (name, mode, is_partner, url, notes))


def seed_demo_trips(db: Db) -> None:
    """Made up bus trips, added only on a brand new database."""
    if db.execute("SELECT COUNT(*) AS n FROM trips").fetchone()["n"] > 0:
        return
    for t in TRIPS:
        op_id = get_operator_id(db, t["operator"], t["mode"], bool(t["partner"]), t["url"])
        db.execute(
            "INSERT INTO trips (operator_id, origin, destination, depart_time, arrive_time, "
            "price, booking_url, is_sample) VALUES (?,?,?,?,?,?,?,?)",
            (op_id, t["from"], t["to"], t["depart"], t["arrive"], t["price"], t["url"], True))


def load_arr_trips(db: Db) -> None:
    """Load the real, unofficial Alaska Railroad list. Safe to run on every start.

    Each row is matched on route, departure time and season start: an existing row is updated
    (so trip ids stay the same and click history is kept), a missing row is added, and any old
    Alaska Railroad row no longer in arr_data.py is hidden. The old made up "Sample Railroad"
    trips are hidden too."""
    op = arr_data.OPERATOR
    op_id = get_operator_id(db, op["name"], op["mode"], op["is_partner"], op["booking_url"], op["notes"])
    db.execute("UPDATE trips SET is_active = ? WHERE operator_id = ?", (False, op_id))
    old = db.execute("SELECT id FROM operators WHERE name = ?", ("Sample Railroad",)).fetchone()
    if old:
        db.execute("UPDATE trips SET is_active = ? WHERE operator_id = ?", (False, old["id"]))
    for (origin, dest, dep, arr, price, days, start, end) in arr_data.ARR_TRIPS:
        days_text = f"{days} ({arr_data.CLASS_NOTE})"
        found = db.execute(
            "SELECT id FROM trips WHERE operator_id = ? AND origin = ? AND destination = ? "
            "AND depart_time = ? AND season_start = ?", (op_id, origin, dest, dep, start)).fetchone()
        if found:
            db.execute(
                "UPDATE trips SET arrive_time = ?, price = ?, days_running = ?, season_end = ?, "
                "booking_url = ?, source_url = ?, last_updated = ?, is_sample = ?, is_active = ? "
                "WHERE id = ?",
                (arr, price, days_text, end, op["booking_url"], arr_data.SCHEDULE_URL,
                 arr_data.CHECKED, False, True, found["id"]))
        else:
            db.execute(
                "INSERT INTO trips (operator_id, origin, destination, depart_time, arrive_time, "
                "price, days_running, season_start, season_end, booking_url, source_url, "
                "last_updated, is_sample, is_active) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                (op_id, origin, dest, dep, arr, price, days_text, start, end,
                 op["booking_url"], arr_data.SCHEDULE_URL, arr_data.CHECKED, False, True))


def load_gobus_trips(db: Db) -> None:
    """Load the unofficial GoBus (Ohio) Red Line list. Same upsert rules as the railroad list.
    Fares here are estimates (see gobus_data.py), so every row is flagged fare_estimated."""
    op = gobus_data.OPERATOR
    op_id = get_operator_id(db, op["name"], op["mode"], op["is_partner"], op["booking_url"], op["notes"])
    db.execute("UPDATE trips SET is_active = ? WHERE operator_id = ?", (False, op_id))
    for (origin, dest, dep, arr, price, days, start, end) in gobus_data.GOBUS_TRIPS:
        found = db.execute(
            "SELECT id FROM trips WHERE operator_id = ? AND origin = ? AND destination = ? "
            "AND depart_time = ? AND season_start = ?", (op_id, origin, dest, dep, start)).fetchone()
        if found:
            db.execute(
                "UPDATE trips SET arrive_time = ?, price = ?, days_running = ?, season_end = ?, "
                "booking_url = ?, source_url = ?, last_updated = ?, is_sample = ?, is_active = ?, "
                "fare_estimated = ? WHERE id = ?",
                (arr, price, days, end, op["booking_url"], gobus_data.SOURCE_URL, gobus_data.CHECKED,
                 False, True, True, found["id"]))
        else:
            db.execute(
                "INSERT INTO trips (operator_id, origin, destination, depart_time, arrive_time, "
                "price, days_running, season_start, season_end, booking_url, source_url, "
                "last_updated, is_sample, is_active, fare_estimated) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                (op_id, origin, dest, dep, arr, price, days, start, end, op["booking_url"],
                 gobus_data.SOURCE_URL, gobus_data.CHECKED, False, True, True))


setup_database()


@app.get("/health")
def health() -> dict:
    # Says which database is in use, so you can tell if DATABASE_URL was picked up.
    # "postgres" means Neon. "sqlite" means the temporary local file, which is wiped on every Render restart.
    return {"status": "ok", "database": "postgres" if USE_POSTGRES else "sqlite"}


# Which region each place belongs to. Add a row here when a new pilot region is added.
REGION_OF = {
    "Anchorage": "Alaska", "Denali": "Alaska", "Fairbanks": "Alaska", "Girdwood": "Alaska", "Healy": "Alaska",
    "Hurricane": "Alaska", "Seward": "Alaska", "Talkeetna": "Alaska", "Wasilla": "Alaska", "Whittier": "Alaska",
    "Toledo": "Ohio", "Bowling Green": "Ohio", "Findlay": "Ohio", "Lima": "Ohio", "Kenton": "Ohio",
    "Bellefontaine": "Ohio", "Urbana": "Ohio", "Springfield": "Ohio", "Yellow Springs": "Ohio",
    "Dayton": "Ohio", "Middletown": "Ohio", "Oxford": "Ohio", "Cincinnati": "Ohio",
}


def active_cities() -> list[str]:
    db = get_db()
    rows = db.execute("SELECT origin AS city FROM trips WHERE is_active = ? UNION "
                      "SELECT destination AS city FROM trips WHERE is_active = ?",
                      (True, True)).fetchall()
    db.close()
    return sorted(r["city"] for r in rows)


@app.get("/regions")
def regions() -> list[dict]:
    """Regions that have at least one active trip, each with its places (alphabetical)."""
    out: dict[str, list[str]] = {}
    for city in active_cities():
        out.setdefault(REGION_OF.get(city, "Other"), []).append(city)
    return [{"name": name, "cities": cs} for name, cs in sorted(out.items())]


@app.get("/cities")
def cities(region: Optional[str] = None) -> list[str]:
    """Every place that appears in an active trip, in alphabetical order. Optional region filter."""
    cs = active_cities()
    if region:
        cs = [c for c in cs if REGION_OF.get(c, "Other") == region]
    return cs


def season_status(start, end, on: Optional[date]) -> Optional[bool]:
    """True if the trip's season includes the date, False if not, None if unknown."""
    if on is None or not start or not end:
        return None
    return str(start) <= on.isoformat() <= str(end)


@app.get("/trips")
def search_trips(
    origin: str = Query(..., description="Departure city"),
    destination: str = Query(..., description="Arrival city"),
    mode: Optional[str] = Query(None, description="Rail or Bus. Leave empty for both."),
    on: Optional[date] = Query(None, description="Travel date (YYYY-MM-DD). Adds an in_season flag."),
) -> list[dict]:
    """Return active trips for a route from the database, cheapest first."""
    sql = ("SELECT t.id, t.origin, t.destination, t.depart_time, t.arrive_time, t.price, "
           "t.days_running, t.season_start, t.season_end, t.source_url, t.last_updated, "
           "COALESCE(t.booking_url, o.booking_url) AS url, o.name AS operator, o.mode, "
           "o.is_partner, t.is_sample, t.fare_estimated FROM trips t JOIN operators o ON o.id = t.operator_id "
           "WHERE t.is_active = ? AND lower(t.origin) = lower(?) AND lower(t.destination) = lower(?)")
    params = [True, origin, destination]
    if mode:
        sql += " AND lower(o.mode) = lower(?)"
        params.append(mode)
    sql += " ORDER BY t.price"
    db = get_db()
    rows = db.execute(sql, tuple(params)).fetchall()
    db.close()
    # Keep the same field names the frontend already uses ("from" and "to")
    return [{"id": r["id"], "from": r["origin"], "to": r["destination"],
             "operator": r["operator"], "mode": r["mode"], "depart": r["depart_time"],
             "arrive": r["arrive_time"], "price": float(r["price"]),
             "partner": bool(r["is_partner"]), "url": r["url"],
             "sample": bool(r["is_sample"]), "fare_estimated": bool(r["fare_estimated"]), "days": r["days_running"],
             "season_start": str(r["season_start"]) if r["season_start"] else None,
             "season_end": str(r["season_end"]) if r["season_end"] else None,
             "in_season": season_status(r["season_start"], r["season_end"], on),
             "source_url": r["source_url"],
             "last_updated": str(r["last_updated"]) if r["last_updated"] else None} for r in rows]


class Click(BaseModel):
    ref: str          # tracking code, for example "coop-1"
    trip_id: int
    operator: str = ""   # kept so older frontends still work; the operator is read from the trip
    riders: int = 1


FEE_RATE = 0.06       # Base case blended fee from the payback model


@app.post("/clicks")
def log_click(click: Click) -> dict:
    """Save one referral click. The price is read from the trips table, not from the browser."""
    db = get_db()
    trip = db.execute("SELECT t.price, o.name FROM trips t JOIN operators o ON o.id = t.operator_id "
                      "WHERE t.id = ?", (click.trip_id,)).fetchone()
    if trip is None:
        db.close()
        raise HTTPException(status_code=404, detail="Unknown trip_id")
    click_id = db.insert(
        "INSERT INTO clicks (ref, trip_id, price_at_click, riders) VALUES (?,?,?,?)",
        (click.ref, click.trip_id, trip["price"], max(click.riders, 1)))
    db.commit()
    db.close()
    return {"id": click_id, "ref": click.ref, "operator": trip["name"]}


@app.post("/clicks/{click_id}/confirm")
def confirm_click(click_id: int) -> dict:
    """Pilot only: the partner reports that this click became a ticket sale."""
    db = get_db()
    cur = db.execute("UPDATE clicks SET confirmed = ?, confirmed_at = CURRENT_TIMESTAMP "
                     "WHERE id = ?", (True, click_id))
    db.commit()
    found = cur.rowcount
    db.close()
    if found == 0:
        raise HTTPException(status_code=404, detail="Unknown click id")
    return {"id": click_id, "confirmed": True}


@app.get("/clicks/report")
def click_report(partner_sales: Optional[float] = Query(
        None, description="Partner's total ticket sales ($) for the same routes and weeks")) -> dict:
    """Clicks and confirmed bookings per operator, plus the capture rate if partner sales are given."""
    db = get_db()
    rows = db.execute("""SELECT o.name AS operator, COUNT(*) AS clicks,
        SUM(CASE WHEN c.confirmed THEN 1 ELSE 0 END) AS bookings,
        SUM(CASE WHEN c.confirmed THEN c.price_at_click * c.riders ELSE 0 END) AS booked_value
        FROM clicks c JOIN trips t ON t.id = c.trip_id JOIN operators o ON o.id = t.operator_id
        GROUP BY o.name ORDER BY COUNT(*) DESC""").fetchall()
    db.close()
    operators = []
    for r in rows:
        bookings = int(r["bookings"] or 0)
        value = float(r["booked_value"] or 0.0)
        operators.append({
            "operator": r["operator"], "clicks": r["clicks"], "bookings": bookings,
            "click_to_booking": round(bookings / r["clicks"], 3),
            "booked_value": round(value, 2), "fee_value": round(value * FEE_RATE, 2)})
    total_value = sum(o["booked_value"] for o in operators)
    report = {"operators": operators,
              "total_clicks": sum(o["clicks"] for o in operators),
              "total_bookings": sum(o["bookings"] for o in operators),
              "total_booked_value": round(total_value, 2),
              "fee_rate": FEE_RATE}
    if partner_sales and partner_sales > 0:
        report["capture_rate"] = round(total_value / partner_sales, 4)
    return report


class Member(BaseModel):
    email: str
    tier: int         # 1 = free, 2 = paid


@app.post("/members")
def join(member: Member) -> dict:
    """Save a sign up. No payment is taken in the prototype; Tier 2 is recorded as interest only."""
    email = member.email.strip().lower()
    if "@" not in email or "." not in email.split("@")[-1] or " " in email:
        raise HTTPException(status_code=422, detail="Please enter a valid email address")
    if member.tier not in (1, 2):
        raise HTTPException(status_code=422, detail="Tier must be 1 (free) or 2 (paid)")
    db = get_db()
    existing = db.execute("SELECT id, tier FROM members WHERE email = ?", (email,)).fetchone()
    if existing:
        # Same email again: update the tier instead of creating a duplicate
        db.execute("UPDATE members SET tier = ? WHERE id = ?", (member.tier, existing["id"]))
        db.commit()
        db.close()
        return {"id": existing["id"], "email": email, "tier": member.tier, "status": "updated"}
    member_id = db.insert("INSERT INTO members (email, tier) VALUES (?, ?)", (email, member.tier))
    db.commit()
    db.close()
    return {"id": member_id, "email": email, "tier": member.tier, "status": "created"}


@app.get("/members/count")
def member_count() -> dict:
    """How many people joined, by tier (no emails are returned)."""
    db = get_db()
    rows = db.execute("SELECT tier, COUNT(*) AS n FROM members GROUP BY tier").fetchall()
    db.close()
    counts = {r["tier"]: r["n"] for r in rows}
    return {"tier1": counts.get(1, 0), "tier2": counts.get(2, 0), "total": sum(counts.values())}


# ---------------------------------------------------------------------------------------------
# Week 9 Day 4: weekly numbers the partner reports during the pilot, and the capture rate.
# Capture rate = value of tickets that carried our tracking code / the partner's total sales on the
# same routes and weeks. Decision bands come from the Week 8 pilot design.
# ---------------------------------------------------------------------------------------------
GO_RATE = 0.09          # 9% or more: go
EXTEND_RATE = 0.055     # 5.5% to 9%: extend and cut costs. Below 5.5%: stop or change the model.
ADMIN_KEY = os.environ.get("ADMIN_KEY", "").strip()   # if set, partner numbers need this key
PILOT_WEEKS = 12
PILOT_MIN_TICKETS = 100


class PartnerReport(BaseModel):
    operator: str
    week_start: date
    route_label: str = Field(min_length=1)
    partner_sales_total: float = Field(gt=0)
    tagged_tickets: int = Field(default=0, ge=0)
    tagged_value: float = Field(default=0, ge=0)
    notes: str = ""


def decision_band(rate: float, weeks: int, tickets: int) -> str:
    if rate >= GO_RATE:
        band = "Go (9% or more)"
    elif rate >= EXTEND_RATE:
        band = "Extend the pilot and cut costs (5.5% to 9%)"
    else:
        band = "Stop or change the model (below 5.5%)"
    if weeks < PILOT_WEEKS or tickets < PILOT_MIN_TICKETS:
        return f"Preliminary, not a decision yet: {band}"
    return band


def require_admin(x_admin_key: str = Header(default="")) -> None:
    """Staff only. If ADMIN_KEY is not set (local testing), anyone may call."""
    if ADMIN_KEY and x_admin_key != ADMIN_KEY:
        raise HTTPException(status_code=401, detail="Staff key missing or wrong")


@app.post("/partner-reports", dependencies=[Depends(require_admin)])
def save_partner_report(rep: PartnerReport) -> dict:
    """Staff entry: one row per operator, week and route label. Sending the same one again updates it."""
    if rep.tagged_value > rep.partner_sales_total:
        raise HTTPException(status_code=422,
                            detail="Tagged value cannot be more than the partner's total sales")
    if rep.tagged_tickets == 0 and rep.tagged_value > 0:
        raise HTTPException(status_code=422, detail="Tagged value needs at least one tagged ticket")
    db = get_db()
    op = db.execute("SELECT id FROM operators WHERE name = ?", (rep.operator,)).fetchone()
    if op is None:
        db.close()
        raise HTTPException(status_code=404, detail="Unknown operator")
    existing = db.execute(
        "SELECT id FROM partner_weekly_reports WHERE operator_id = ? AND week_start = ? AND route_label = ?",
        (op["id"], rep.week_start.isoformat(), rep.route_label.strip())).fetchone()
    values = (rep.partner_sales_total, rep.tagged_tickets, rep.tagged_value, rep.notes)
    if existing:
        db.execute("UPDATE partner_weekly_reports SET partner_sales_total = ?, tagged_tickets = ?, "
                   "tagged_value = ?, notes = ? WHERE id = ?", values + (existing["id"],))
        report_id, status = existing["id"], "updated"
    else:
        report_id = db.insert(
            "INSERT INTO partner_weekly_reports (operator_id, week_start, route_label, partner_sales_total, "
            "tagged_tickets, tagged_value, notes) VALUES (?,?,?,?,?,?,?)",
            (op["id"], rep.week_start.isoformat(), rep.route_label.strip()) + values)
        status = "created"
    db.commit()
    db.close()
    return {"id": report_id, "status": status}


@app.get("/partner-reports", dependencies=[Depends(require_admin)])
def partner_reports(operator: Optional[str] = Query(None)) -> dict:
    """All weekly rows with each week's capture rate, plus the running total and decision band."""
    sql = ("SELECT r.id, o.name AS operator, r.week_start, r.route_label, r.partner_sales_total, "
           "r.tagged_tickets, r.tagged_value, r.notes FROM partner_weekly_reports r "
           "JOIN operators o ON o.id = r.operator_id")
    params: tuple = ()
    if operator:
        sql += " WHERE o.name = ?"
        params = (operator,)
    sql += " ORDER BY r.week_start, o.name, r.route_label"
    db = get_db()
    rows = db.execute(sql, params).fetchall()
    db.close()
    out, sales, value, tickets, weeks = [], 0.0, 0.0, 0, set()
    for r in rows:
        s_total, t_value = float(r["partner_sales_total"]), float(r["tagged_value"])
        sales += s_total
        value += t_value
        tickets += int(r["tagged_tickets"])
        weeks.add(str(r["week_start"]))
        out.append({"id": r["id"], "operator": r["operator"], "week_start": str(r["week_start"]),
                    "route_label": r["route_label"], "partner_sales_total": s_total,
                    "tagged_tickets": int(r["tagged_tickets"]), "tagged_value": t_value,
                    "capture_rate": round(t_value / s_total, 4) if s_total else None,
                    "notes": r["notes"] or ""})
    summary = {"weeks_reported": len(weeks), "partner_sales_total": round(sales, 2),
               "tagged_tickets": tickets, "tagged_value": round(value, 2),
               "capture_rate": round(value / sales, 4) if sales else None,
               "fee_value": round(value * FEE_RATE, 2),
               "decision": decision_band(value / sales, len(weeks), tickets) if sales else "No data yet",
               "note": "Tagged sales are a floor: some buyers click through but book later without the code."}
    return {"rows": out, "summary": summary}
