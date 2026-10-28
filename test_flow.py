"""Full flow test against a RUNNING backend (local or hosted): the same steps a visitor and staff member take.

  1. Start the backend (for example: cd backend && uvicorn main:app --port 8000)
  2. In another window, from the repo folder:
       BACKEND_URL=http://localhost:8000 ADMIN_KEY=yourkey python test_flow.py
  3. After a restart of the backend, check that the data is still there:
       BACKEND_URL=http://localhost:8000 ADMIN_KEY=yourkey python test_flow.py --after-restart

It writes a few test rows (a click, a member, a partner week). Use a test database, not the pilot one.
"""
import os
import sys

import requests

BASE = os.environ.get("BACKEND_URL", "http://localhost:8000").rstrip("/")
KEY = os.environ.get("ADMIN_KEY", "")
STAFF = {"X-Admin-Key": KEY} if KEY else {}
EMAIL = "flowtest@example.com"
WEEK = "2027-06-07"


def get(path, **kw):
    r = requests.get(BASE + path, timeout=60, **kw)
    r.raise_for_status()
    return r.json()


def post(path, **kw):
    r = requests.post(BASE + path, timeout=60, **kw)
    r.raise_for_status()
    return r.json()


def check(ok, label):
    print(("PASS  " if ok else "FAIL  ") + label)
    if not ok:
        sys.exit(1)


if "--after-restart" in sys.argv:
    members = get("/members/count")
    check(members["total"] >= 1, f"member still saved after restart ({members})")
    report = get("/clicks/report")
    check(report["total_clicks"] >= 1 and report["total_bookings"] >= 1, f"click and booking still saved ({report['total_clicks']} clicks)")
    rows = get("/partner-reports", headers=STAFF)["rows"]
    check(any(r["week_start"] == WEEK for r in rows), "partner week still saved")
    print("\nAll persistence checks passed.")
    sys.exit(0)

check(get("/health")["status"] == "ok", "backend is up")
cities = get("/cities")
check({"Anchorage", "Seward", "Fairbanks"} <= set(cities), f"{len(cities)} places listed")
trips = get("/trips", params={"origin": "Anchorage", "destination": "Seward", "on": "2027-07-15"})
rail = [t for t in trips if t["operator"] == "Alaska Railroad"]
check(len(trips) == 3 and len(rail) == 1, "search returns the railroad and two demo buses")
check(rail[0]["in_season"] is True and rail[0]["sample"] is False and rail[0]["partner"] is False,
      "railroad is real, unofficial, not a partner, in season")
winter = get("/trips", params={"origin": "Anchorage", "destination": "Fairbanks", "on": "2026-10-24"})
check(any(t["in_season"] for t in winter) and any(not t["in_season"] for t in winter), "season flag separates winter and summer trains")
click = post("/clicks", json={"ref": f"coop-{rail[0]['id']}", "trip_id": rail[0]["id"], "riders": 2})
check(click["operator"] == "Alaska Railroad", "referral click saved")
check(post(f"/clicks/{click['id']}/confirm")["confirmed"], "booking confirmed")
rep = get("/clicks/report", params={"partner_sales": 5320})
check(rep["total_bookings"] >= 1 and "capture_rate" in rep, "click report shows bookings and capture rate")
check(post("/members", json={"email": EMAIL, "tier": 1})["status"] in ("created", "updated"), "member saved")
check(post("/members", json={"email": EMAIL, "tier": 2})["status"] == "updated", "same email updates the tier")
week = {"operator": "Alaska Railroad", "week_start": WEEK, "route_label": "Anchorage to Seward",
        "partner_sales_total": 20000, "tagged_tickets": 12, "tagged_value": 1800}
if KEY:
    r = requests.get(BASE + "/partner-reports", timeout=60)
    check(r.status_code == 401, "partner numbers are refused without the staff key")
check(post("/partner-reports", json=week, headers=STAFF)["status"] in ("created", "updated"), "partner week saved")
summary = get("/partner-reports", headers=STAFF)["summary"]
check(summary["capture_rate"] is not None and summary["decision"].startswith("Preliminary"), f"capture rate {summary['capture_rate']:.1%} shown as preliminary")
print("\nAll flow checks passed. Restart the backend, then run this file with --after-restart.")
