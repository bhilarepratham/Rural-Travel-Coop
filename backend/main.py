"""Backend API for the Rural Travel Co-op prototype (sample data only).

Run locally:  uvicorn main:app --reload      (from the backend folder)
API docs:     http://localhost:8000/docs

Done on Day 1:  /health, /cities, /trips
Day 5: /members saves sign ups (free Tier 1 or paid Tier 2) and /members/count summarizes them.
Day 4: /clicks logs referral clicks in SQLite and /clicks/report summarizes them.
Day 2: trips now live in a SQLite database (trips.db) instead of a Python list.
To build later: /clicks (Day 4), /members (Day 5)
"""
import sqlite3
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel

from data import CITIES, TRIPS

app = FastAPI(title="Rural Travel Co-op API (prototype)")

DB_PATH = Path(__file__).parent / "trips.db"


def get_db() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row   # lets us read columns by name
    return conn


def setup_database() -> None:
    """Create the trips table and fill it from data.py if it is empty."""
    conn = get_db()
    conn.execute("""CREATE TABLE IF NOT EXISTS trips (
        id INTEGER PRIMARY KEY, origin TEXT, destination TEXT, operator TEXT,
        mode TEXT, depart TEXT, arrive TEXT, price REAL, partner INTEGER, url TEXT)""")
    if conn.execute("SELECT COUNT(*) FROM trips").fetchone()[0] == 0:
        for t in TRIPS:
            conn.execute("INSERT INTO trips VALUES (?,?,?,?,?,?,?,?,?,?)",
                (t["id"], t["from"], t["to"], t["operator"], t["mode"], t["depart"],
                 t["arrive"], t["price"], int(t["partner"]), t["url"]))
        conn.commit()
    conn.execute("""CREATE TABLE IF NOT EXISTS clicks (
        id INTEGER PRIMARY KEY AUTOINCREMENT, ref TEXT, trip_id INTEGER, operator TEXT,
        price REAL, riders INTEGER DEFAULT 1, confirmed INTEGER DEFAULT 0,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP)""")
    conn.execute("""CREATE TABLE IF NOT EXISTS members (
        id INTEGER PRIMARY KEY AUTOINCREMENT, email TEXT UNIQUE, tier INTEGER,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP)""")
    conn.commit()
    conn.close()


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
    """Return sample trips for a route from the database, cheapest first."""
    sql = ("SELECT * FROM trips WHERE lower(origin) = lower(?) "
           "AND lower(destination) = lower(?)")
    params = [origin, destination]
    if mode:
        sql += " AND lower(mode) = lower(?)"
        params.append(mode)
    sql += " ORDER BY price"
    conn = get_db()
    rows = conn.execute(sql, params).fetchall()
    conn.close()
    # Keep the same field names the frontend already uses ("from" and "to")
    return [{"id": r["id"], "from": r["origin"], "to": r["destination"],
             "operator": r["operator"], "mode": r["mode"], "depart": r["depart"],
             "arrive": r["arrive"], "price": r["price"], "partner": bool(r["partner"]),
             "url": r["url"]} for r in rows]


class Click(BaseModel):
    ref: str          # tracking code, for example "coop-1"
    trip_id: int
    operator: str
    riders: int = 1


FEE_RATE = 0.06       # Base case blended fee from the payback model


@app.post("/clicks")
def log_click(click: Click) -> dict:
    """Save one referral click. The price is read from the trips table, not from the browser."""
    conn = get_db()
    trip = conn.execute("SELECT price FROM trips WHERE id = ?", (click.trip_id,)).fetchone()
    if trip is None:
        conn.close()
        raise HTTPException(status_code=404, detail="Unknown trip_id")
    cur = conn.execute(
        "INSERT INTO clicks (ref, trip_id, operator, price, riders) VALUES (?,?,?,?,?)",
        (click.ref, click.trip_id, click.operator, trip["price"], max(click.riders, 1)))
    conn.commit()
    click_id = cur.lastrowid
    conn.close()
    return {"id": click_id, "ref": click.ref, "operator": click.operator}


@app.post("/clicks/{click_id}/confirm")
def confirm_click(click_id: int) -> dict:
    """Pilot only: the partner reports that this click became a ticket sale."""
    conn = get_db()
    cur = conn.execute("UPDATE clicks SET confirmed = 1 WHERE id = ?", (click_id,))
    conn.commit()
    conn.close()
    if cur.rowcount == 0:
        raise HTTPException(status_code=404, detail="Unknown click id")
    return {"id": click_id, "confirmed": True}


@app.get("/clicks/report")
def click_report(partner_sales: Optional[float] = Query(
        None, description="Partner's total ticket sales ($) for the same routes and weeks")) -> dict:
    """Clicks and confirmed bookings per operator, plus the capture rate if partner sales are given."""
    conn = get_db()
    rows = conn.execute("""SELECT operator, COUNT(*) AS clicks, SUM(confirmed) AS bookings,
        SUM(CASE WHEN confirmed = 1 THEN price * riders ELSE 0 END) AS booked_value
        FROM clicks GROUP BY operator ORDER BY clicks DESC""").fetchall()
    conn.close()
    operators = []
    for r in rows:
        bookings = r["bookings"] or 0
        value = r["booked_value"] or 0.0
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
    conn = get_db()
    existing = conn.execute("SELECT id, tier FROM members WHERE email = ?", (email,)).fetchone()
    if existing:
        # Same email again: update the tier instead of creating a duplicate
        conn.execute("UPDATE members SET tier = ? WHERE id = ?", (member.tier, existing["id"]))
        conn.commit()
        conn.close()
        return {"id": existing["id"], "email": email, "tier": member.tier, "status": "updated"}
    cur = conn.execute("INSERT INTO members (email, tier) VALUES (?, ?)", (email, member.tier))
    conn.commit()
    member_id = cur.lastrowid
    conn.close()
    return {"id": member_id, "email": email, "tier": member.tier, "status": "created"}


@app.get("/members/count")
def member_count() -> dict:
    """How many people joined, by tier (no emails are returned)."""
    conn = get_db()
    rows = conn.execute("SELECT tier, COUNT(*) AS n FROM members GROUP BY tier").fetchall()
    conn.close()
    counts = {r["tier"]: r["n"] for r in rows}
    return {"tier1": counts.get(1, 0), "tier2": counts.get(2, 0), "total": sum(counts.values())}
