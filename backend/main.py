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
from typing import Optional

from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel

from data import CITIES, TRIPS

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
    is_sample INTEGER NOT NULL DEFAULT 0);
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
    if db.execute("SELECT COUNT(*) AS n FROM trips").fetchone()["n"] == 0:
        operator_ids = {}
        for t in TRIPS:
            if t["operator"] not in operator_ids:
                row = db.execute("SELECT id FROM operators WHERE name = ?", (t["operator"],)).fetchone()
                if row:
                    operator_ids[t["operator"]] = row["id"]
                else:
                    operator_ids[t["operator"]] = db.insert(
                        "INSERT INTO operators (name, mode, is_partner, booking_url) VALUES (?,?,?,?)",
                        (t["operator"], t["mode"], bool(t["partner"]), t["url"]))
            db.execute(
                "INSERT INTO trips (operator_id, origin, destination, depart_time, arrive_time, "
                "price, booking_url, is_sample) VALUES (?,?,?,?,?,?,?,?)",
                (operator_ids[t["operator"]], t["from"], t["to"], t["depart"], t["arrive"],
                 t["price"], t["url"], True))
    db.commit()
    db.close()


setup_database()


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.get("/cities")
def cities() -> list[str]:
    return CITIES


@app.get("/trips")
def search_trips(
    origin: str = Query(..., description="Departure city"),
    destination: str = Query(..., description="Arrival city"),
    mode: Optional[str] = Query(None, description="Rail or Bus. Leave empty for both."),
) -> list[dict]:
    """Return trips for a route from the database, cheapest first."""
    sql = ("SELECT t.id, t.origin, t.destination, t.depart_time, t.arrive_time, t.price, "
           "COALESCE(t.booking_url, o.booking_url) AS url, o.name AS operator, o.mode, "
           "o.is_partner, t.is_sample FROM trips t JOIN operators o ON o.id = t.operator_id "
           "WHERE lower(t.origin) = lower(?) AND lower(t.destination) = lower(?)")
    params = [origin, destination]
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
             "sample": bool(r["is_sample"])} for r in rows]


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
