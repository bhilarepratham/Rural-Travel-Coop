import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "backend"))
from fastapi.testclient import TestClient
import arr_data, gobus_data, main

# A leftover made up "Sample Railroad" trip from the old seed data, with a click on it
db = main.get_db()
old_op = main.get_operator_id(db, "Sample Railroad", "Rail", True, "https://example.com")
old_trip = db.insert("INSERT INTO trips (operator_id, origin, destination, depart_time, arrive_time, price, is_sample) "
                     "VALUES (?,?,?,?,?,?,?)", (old_op, "Anchorage", "Seward", "08:00", "12:00", 89, True))
db.execute("INSERT INTO clicks (ref, trip_id, price_at_click) VALUES (?,?,?)", ("old", old_trip, 89))
db.commit(); db.close()
main.setup_database()           # the start up step: loads real data and hides the old sample rail trip

c = TestClient(main.app)
assert c.get("/health").json()["status"] == "ok"
regs = c.get("/regions").json()
assert [r["name"] for r in regs] == ["Alaska", "Ohio"], regs
assert "Anchorage" in regs[0]["cities"] and "Toledo" in regs[1]["cities"] and "Anchorage" not in regs[1]["cities"]
assert "Anchorage" in c.get("/cities", params={"region": "Alaska"}).json()
assert c.get("/cities", params={"region": "Nowhere"}).json() == []
cities = c.get("/cities").json()
assert cities == sorted({x for t in arr_data.ARR_TRIPS for x in t[:2]} | {"Anchorage", "Seward"}
                        | {x for t in gobus_data.GOBUS_TRIPS for x in t[:2]}), cities
assert c.get("/cities", params={"region": "Ohio"}).json() == sorted({x for t in gobus_data.GOBUS_TRIPS for x in t[:2]})

# GoBus (Ohio): estimated fares are flagged and stay inside the published $5 to $25 range
g = c.get("/trips", params={"origin": "Toledo", "destination": "Cincinnati", "on": "2027-01-15"}).json()
assert len(g) == 2 and all(x["fare_estimated"] and x["operator"] == "GoBus (Ohio)" and x["in_season"] is True for x in g), g
assert all(5 <= x["price"] <= 25 for x in g)
r2 = c.get("/trips", params={"origin": "Cincinnati", "destination": "Toledo"}).json()
assert len(r2) == 2
assert len(c.get("/trips", params={"origin": "Dayton", "destination": "Lima"}).json()) == 2      # northbound buses
assert c.get("/trips", params={"origin": "Anchorage", "destination": "Toledo"}).json() == []     # no cross region trips
assert all(not x["fare_estimated"] for x in c.get("/trips", params={"origin": "Anchorage", "destination": "Fairbanks"}).json())

t = c.get("/trips", params={"origin": "anchorage", "destination": "SEWARD", "on": "2027-07-15"}).json()
assert [x["operator"] for x in t] == ["Sample Coach Lines", "Sample Shuttle Co", "Alaska Railroad"], t
rail = t[2]
assert rail["price"] == 133.0 and rail["depart"] == "06:45" and rail["arrive"] == "11:20"
assert rail["sample"] is False and rail["partner"] is False and rail["in_season"] is True
assert rail["source_url"] == arr_data.SCHEDULE_URL and rail["season_start"] == "2027-05-14"
assert t[0]["sample"] is True and t[0]["in_season"] is None
off = c.get("/trips", params={"origin": "Anchorage", "destination": "Seward", "mode": "Rail", "on": "2026-10-21"}).json()
assert len(off) == 1 and off[0]["in_season"] is False       # the old Sample Railroad row is hidden
assert len(c.get("/trips", params={"origin": "Anchorage", "destination": "Fairbanks"}).json()) == 2   # Denali Star + Aurora Winter
assert c.get("/trips", params={"origin": "Fairbanks", "destination": "Seward"}).json() == []

# restart keeps ids stable, adds no duplicates, keeps click history
before = {(x["id"]) for x in c.get("/trips", params={"origin": "Anchorage", "destination": "Seward"}).json()}
a = c.post("/clicks", json={"ref": "coop-1", "trip_id": rail["id"], "riders": 2}).json()
main.setup_database()
after = {(x["id"]) for x in c.get("/trips", params={"origin": "Anchorage", "destination": "Seward"}).json()}
assert before == after
db = main.get_db()
n = db.execute("SELECT COUNT(*) AS n FROM trips t JOIN operators o ON o.id=t.operator_id WHERE o.name='Alaska Railroad'").fetchone()["n"]
assert n == len(arr_data.ARR_TRIPS), n
n2 = db.execute("SELECT COUNT(*) AS n FROM trips t JOIN operators o ON o.id=t.operator_id WHERE o.name='GoBus (Ohio)'").fetchone()["n"]
assert n2 == len(gobus_data.GOBUS_TRIPS), n2
assert db.execute("SELECT COUNT(*) AS n FROM clicks").fetchone()["n"] >= 2
db.close()

# clicks, report, members (as before)
assert a["operator"] == "Alaska Railroad"
assert c.post("/clicks", json={"ref": "x", "trip_id": 99999}).status_code == 404
assert c.post(f"/clicks/{a['id']}/confirm").json()["confirmed"] is True
assert c.post("/clicks/99999/confirm").status_code == 404
r = c.get("/clicks/report", params={"partner_sales": 5320}).json()
ar = [o for o in r["operators"] if o["operator"] == "Alaska Railroad"][0]
assert ar["clicks"] == 1 and ar["bookings"] == 1 and ar["booked_value"] == 266.0 and ar["fee_value"] == 15.96, r
assert r["capture_rate"] == 0.05, r
assert c.post("/members", json={"email": "", "tier": 1}).status_code == 422
assert c.post("/members", json={"email": "a@b.com", "tier": 3}).status_code == 422
assert c.post("/members", json={"email": " A@B.com ", "tier": 1}).json()["status"] == "created"
assert c.post("/members", json={"email": "a@b.com", "tier": 2}).json()["status"] == "updated"
assert c.get("/members/count").json() == {"tier1": 0, "tier2": 1, "total": 1}
# partner weekly reports (Day 4)
good = {"operator": "Alaska Railroad", "week_start": "2027-06-07", "route_label": "Anchorage to Seward",
        "partner_sales_total": 20000, "tagged_tickets": 12, "tagged_value": 1600}
assert c.post("/partner-reports", json=good).json()["status"] == "created"
assert c.post("/partner-reports", json={**good, "tagged_value": 1800}).json()["status"] == "updated"   # same week and route
assert c.post("/partner-reports", json={**good, "route_label": "Anchorage to Talkeetna", "partner_sales_total": 10000,
                                         "tagged_tickets": 3, "tagged_value": 500}).json()["status"] == "created"
assert c.post("/partner-reports", json={**good, "operator": "Nobody"}).status_code == 404
assert c.post("/partner-reports", json={**good, "partner_sales_total": 0}).status_code == 422
assert c.post("/partner-reports", json={**good, "tagged_value": 99999}).status_code == 422
assert c.post("/partner-reports", json={**good, "week_start": "not a date"}).status_code == 422
pr = c.get("/partner-reports").json()
assert len(pr["rows"]) == 2 and pr["rows"][0]["capture_rate"] == 0.09, pr["rows"][0]
sm = pr["summary"]
assert sm["partner_sales_total"] == 30000 and sm["tagged_value"] == 2300 and sm["capture_rate"] == 0.0767, sm
assert sm["decision"].startswith("Preliminary") and "5.5% to 9%" in sm["decision"], sm
assert c.get("/partner-reports", params={"operator": "Sample Coach Lines"}).json()["rows"] == []
# staff key (only enforced when ADMIN_KEY is set)
main.ADMIN_KEY = "secret"
assert c.get("/partner-reports").status_code == 401
assert c.post("/partner-reports", json=good).status_code == 401
assert c.get("/partner-reports", headers={"X-Admin-Key": "wrong"}).status_code == 401
assert c.get("/partner-reports", headers={"X-Admin-Key": "secret"}).status_code == 200
assert c.post("/partner-reports", json=good, headers={"X-Admin-Key": "secret"}).json()["status"] == "updated"
main.ADMIN_KEY = ""
print("ALL TESTS PASSED", "postgres" if main.USE_POSTGRES else "sqlite")
