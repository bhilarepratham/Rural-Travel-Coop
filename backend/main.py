"""Backend API for the Rural Travel Co-op prototype (sample data only).

Run locally:  uvicorn main:app --reload      (from the backend folder)
API docs:     http://localhost:8000/docs

Done on Day 1:  /health, /cities, /trips
To build later: /clicks (Day 4), /members (Day 5)
"""
from typing import Optional

from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel

from data import CITIES, TRIPS

app = FastAPI(title="Rural Travel Co-op API (prototype)")


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
    """Return sample trips for a route, optionally filtered by mode."""
    results = [t for t in TRIPS if t["from"] == origin and t["to"] == destination]
    if mode:
        results = [t for t in results if t["mode"].lower() == mode.lower()]
    return results


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
