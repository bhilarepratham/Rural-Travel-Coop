"""Backend API for the Rural Travel Co-op prototype (sample data only).

Run locally:  uvicorn main:app --reload      (from the backend folder)
API docs:     http://localhost:8000/docs

Done on Day 1:  /health, /cities, /trips
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


@app.post("/clicks")
def log_click(click: Click) -> dict:
    # TODO (Day 4): save the click to the database (SQLite to start) and return it.
    # TODO (Day 4): add GET /clicks to return a simple report of clicks per operator.
    raise HTTPException(status_code=501, detail="Not built yet: Day 4")


class Member(BaseModel):
    email: str
    tier: int         # 1 = free, 2 = paid


@app.post("/members")
def join(member: Member) -> dict:
    # TODO (Day 5): validate the email, save the member to the database, return the record.
    raise HTTPException(status_code=501, detail="Not built yet: Day 5")
