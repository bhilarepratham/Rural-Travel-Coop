import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "backend"))
from fastapi.testclient import TestClient
import alberta_data
import flight_data, arr_data, gobus_data, main

# A leftover made up "Sample Railroad" trip from the old seed data, with a click on it
db = main.get_db()
old_op = main.get_operator_id(db, "Sample Railroad", "Rail", True, "https://example.com")
old_trip = db.insert("INSERT INTO trips (operator_id, origin, destination, depart_time, arrive_time, price, is_sample) "
                     "VALUES (?,?,?,?,?,?,?)", (old_op, "Anchorage", "Seward", "08:00", "12:00", 89, True))
db.execute("INSERT INTO clicks (ref, trip_id, price_at_click) VALUES (?,?,?)", ("old", old_trip, 89))
leg_op = main.get_operator_id(db, "GoBus (Ohio)", "Bus", False, "https://booking.ridegobus.com")
leg_trip = db.insert("INSERT INTO trips (operator_id, origin, destination, depart_time, arrive_time, price, fare_estimated) "
                     "VALUES (?,?,?,?,?,?,?)", (leg_op, "Toledo", "Cincinnati", "07:21", "15:00", 22, True))
db.commit(); db.close()
main.setup_database()           # the start up step: loads real data and hides the old sample rail trip

c = TestClient(main.app)
assert c.get("/health").json()["status"] == "ok"
regs = c.get("/regions").json()
assert [r["name"] for r in regs] == ["Alaska", "Alberta", "Ohio"], regs
assert "Anchorage" in regs[0]["cities"] and "Toledo" in regs[2]["cities"] and "Anchorage" not in regs[2]["cities"]
assert regs[1]["cities"] == alberta_data.ALBERTA_CITIES and "Edmonton" in regs[1]["cities"]
assert "Anchorage" in c.get("/cities", params={"region": "Alaska"}).json()
assert c.get("/cities", params={"region": "Nowhere"}).json() == []
cities = c.get("/cities").json()
assert cities == sorted({x for t in arr_data.ARR_TRIPS for x in t[:2]} | {"Anchorage", "Seward"}
                        | {x for t in gobus_data.GOBUS_TRIPS for x in t[:2]} | set(alberta_data.ALBERTA_CITIES) | set(flight_data.ALASKA_AIR_CITIES)), cities
assert c.get("/cities", params={"region": "Ohio"}).json() == sorted({x for t in gobus_data.GOBUS_TRIPS for x in t[:2]})

# GoBus (Ohio): nine lines, one operator each. Fares are estimates in $5 steps, flagged on every row.
g = c.get("/trips", params={"origin": "Toledo", "destination": "Cincinnati", "on": "2027-01-15"}).json()
assert len(g) == 2 and all(x["fare_estimated"] and x["operator"] == "GoBus Red Line (Ohio)" and x["in_season"] is True for x in g), g
assert all(5 <= x["price"] <= 25 for x in g)                      # Red Line brochure: $5 to $25
assert leg_trip not in {x["id"] for x in g}                        # the old single "GoBus (Ohio)" row is hidden
r2 = c.get("/trips", params={"origin": "Cincinnati", "destination": "Toledo"}).json()
assert len(r2) == 2
assert len(c.get("/trips", params={"origin": "Dayton", "destination": "Lima"}).json()) == 2      # northbound buses
assert c.get("/trips", params={"origin": "Anchorage", "destination": "Toledo"}).json() == []     # no cross region trips
ca = c.get("/trips", params={"origin": "Columbus", "destination": "Athens"}).json()
assert len(ca) == 3 and {x["operator"] for x in ca} == {"GoBus Green Line (Ohio)"} and all(x["fare_estimated"] for x in ca), ca
assert all(x["price"] == 10 for x in ca) and all(x["in_season"] is None for x in ca)             # no printed season on Green
assert len(c.get("/trips", params={"origin": "Athens", "destination": "Columbus"}).json()) == 3
assert {x["operator"] for x in c.get("/trips", params={"origin": "Columbus", "destination": "Pittsburgh"}).json()} == {"GoBus Yellow Line (Ohio)"}
assert c.get("/trips", params={"origin": "Toledo", "destination": "Columbus"}).json()[0]["operator"] == "GoBus Purple Line (Ohio)"
ohio = c.get("/cities", params={"region": "Ohio"}).json()
assert len(ohio) == len(gobus_data.GOBUS_CITIES) >= 50 and "Athens" in ohio and "Wheeling" in ohio

# ---- Alberta: listings with no times; only Red Arrow rows carry an estimated fare (Canadian dollars) ----
ef_ab = alberta_data.estimate_fare
assert ef_ab(149.9) is None and ef_ab(150) == 34 and ef_ab(315) == 72 and ef_ab(424) == 98 and ef_ab(582) == 134
ab_all = c.get("/trips", params={"origin": "Edmonton", "destination": "Calgary"}).json()
assert {x["operator"] for x in ab_all if x["mode"] == "Air"} == {"Air Canada", "WestJet", "Air North"}
assert [x["operator"] for x in c.get("/trips", params={"origin": "Edmonton", "destination": "Calgary", "mode": "Air"}).json()].count("WestJet") == 1
ab = [x for x in ab_all if x["mode"] == "Bus"]
assert {x["operator"] for x in ab} == {"Red Arrow (Alberta)", "FlixBus (Alberta)", "Cold Shot (Alberta)", "Rider Express (Alberta)"}, ab
assert all(x["depart"] is None and x["arrive"] is None and x["currency"] == "CAD" and x["mode"] == "Bus" for x in ab)
assert ab[0]["operator"] == "Red Arrow (Alberta)" and ab[0]["price"] == 72.0 and ab[0]["fare_estimated"] is True   # priced first
assert all(x["price"] is None and not x["fare_estimated"] for x in ab[1:])                  # no fare shown for the others, listed last
assert ab[0]["days"] == "Daily" and ab[0]["source_url"].startswith("https://www.redarrow.ca/routes/")
fm = c.get("/trips", params={"origin": "Edmonton", "destination": "Fort McMurray"}).json()
assert [x["price"] for x in fm if x["operator"] == "Red Arrow (Alberta)"] == [97.0]
assert c.get("/trips", params={"origin": "Gibbons", "destination": "Radway"}).json()[0]["price"] is None   # under 150 km: no estimate
rd = c.get("/trips", params={"origin": "Red Deer", "destination": "Fort McMurray"}).json()
assert rd[0]["days"] == "Mon, Tue, Wed, Thu, Sun" and rd[0]["price"] == 134.0
assert c.get("/trips", params={"origin": "Fort McMurray", "destination": "Red Deer"}).json()[0]["days"] == "Days not shown on the route page"
assert len(c.get("/trips", params={"origin": "Calgary", "destination": "Lethbridge"}).json()) == 1       # Flix only; WestJet ended these flights Jun 24, 2026
assert c.get("/trips", params={"origin": "Edmonton", "destination": "Toledo"}).json() == []

# ---- Flights (Alaska and Alberta): listings with no times and no fare, mode Air, no estimate flag ----
fl = c.get("/trips", params={"origin": "Anchorage", "destination": "Nome"}).json()
assert [x["operator"] for x in fl] == ["Alaska Airlines"], fl
f0 = fl[0]
assert f0["mode"] == "Air" and f0["depart"] is None and f0["arrive"] is None and f0["price"] is None and not f0["fare_estimated"]
assert f0["currency"] == "USD" and f0["url"] == "https://www.alaskaair.com" and not f0["partner"]
assert {x["operator"] for x in c.get("/trips", params={"origin": "Anchorage", "destination": "Kenai"}).json()} == {"Grant Aviation", "Aleutian Airways"}
assert {x["operator"] for x in c.get("/trips", params={"origin": "Homer", "destination": "Anchorage"}).json()} == {"Aleutian Airways"}
assert [x["mode"] for x in c.get("/trips", params={"origin": "Anchorage", "destination": "Fairbanks", "mode": "Air"}).json()] == ["Air"]
assert {x["mode"] for x in c.get("/trips", params={"origin": "Anchorage", "destination": "Fairbanks"}).json()} == {"Rail", "Air"}
assert c.get("/trips", params={"origin": "Nome", "destination": "Kotzebue"}).json() == []                 # only Anchorage hub routes are listed
cal = c.get("/trips", params={"origin": "Fort McMurray", "destination": "Calgary", "mode": "Air"}).json()
assert {x["operator"] for x in cal} == {"Air Canada", "WestJet"} and all(x["currency"] == "CAD" and x["price"] is None for x in cal)
assert c.get("/trips", params={"origin": "Calgary", "destination": "Medicine Hat", "mode": "Air"}).json() == []   # ended Jun 24, 2026
assert c.get("/trips", params={"origin": "Toledo", "destination": "Columbus", "mode": "Air"}).json() == []        # no flights between Ohio cities
assert all(not any(x["mode"] == "Air" for x in c.get("/trips", params={"origin": a_, "destination": b_}).json()) for a_, b_ in (("Toledo", "Cincinnati"), ("Columbus", "Athens")))
assert sum(len(o["trips"]) for o in flight_data.OPERATORS.values()) == 22 + 2 + 12 + 6 + 10 + 2
assert all(x["currency"] == "USD" for x in g)                                                          # Ohio stays in US dollars
for o_ in alberta_data.OPERATORS.values():
    assert o_["name"].endswith("(Alberta)") and not o_["is_partner"]
    for (a_, b_, days_, price_, src_) in o_["trips"]:
        assert a_ != b_ and src_.startswith("http") and (price_ is None or 30 <= price_ <= 140), (a_, b_, price_)
assert not any(t[3] is not None for k_, o_ in alberta_data.OPERATORS.items() if k_ != "Red Arrow" for t in o_["trips"])
assert {"Jackson", "Batavia", "Seaman", "Arlington Heights"} <= set(ohio) and not ({"Piketon", "Peebles"} & set(ohio))   # Orange Line (Sept 14, 2026 file) is loaded
oc = c.get("/trips", params={"origin": "Cincinnati", "destination": "Athens"}).json()
assert len(oc) == 2 and {x["operator"] for x in oc} == {"GoBus Orange Line (Ohio)"}, oc
gt = c.get("/trips", params={"origin": "Painesville", "destination": "Ashtabula"}).json()
assert gt and {x["operator"] for x in gt} == {"GoBus Gray Line (Ohio)"}, gt
assert not ({"Delphos", "Mount Gilead", "Coolville", "Newcomerstown"} & set(ohio))              # reservation only stops are left out
# the published GoBus mileage table (RFP 2024 p.45, 2025 p.40) and the FAQ "under 50 miles is $5"
ef = gobus_data.estimate_fare
assert [ef(m) for m in (10, 49.9, 50, 74.9, 75, 159.9, 160, 199.9, 200, 400)] == [5, 5, 10, 10, 15, 15, 20, 20, 25, 25]
assert ef(300, adjacent=True) == 5                                                                  # "Next stop over: $5.00"
# every GoBus row: price a multiple of $5 between $5 and $25 (changing lines, which can cost more, is not modeled)
for line, op in gobus_data.OPERATORS.items():
    top = 25
    for (o_, d_, dep, arr, price, *_rest) in op["trips"]:
        assert price % 5 == 0 and 5 <= price <= top and o_ != d_ and arr > dep, (line, o_, d_, dep, arr, price)
assert [i["dropped"] for i in gobus_data.DATA_ISSUES] == ["Marietta Armory Square"]             # the one printed time that did not fit

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
assert len(c.get("/trips", params={"origin": "Anchorage", "destination": "Fairbanks"}).json()) == 3   # Denali Star + Aurora Winter + Alaska Airlines
assert c.get("/trips", params={"origin": "Fairbanks", "destination": "Seward"}).json() == []

# restart keeps ids stable, adds no duplicates, keeps click history
before = {(x["id"]) for x in c.get("/trips", params={"origin": "Anchorage", "destination": "Seward"}).json()}
a = c.post("/clicks", json={"ref": "coop-1", "trip_id": rail["id"], "riders": 2}).json()
main.setup_database()
after = {(x["id"]) for x in c.get("/trips", params={"origin": "Anchorage", "destination": "Seward"}).json()}
assert before == after
ab_before = [x["id"] for x in c.get("/trips", params={"origin": "Edmonton", "destination": "Calgary"}).json()]
db = main.get_db()
nab = db.execute("SELECT COUNT(*) AS n FROM trips t JOIN operators o ON o.id=t.operator_id WHERE o.name LIKE ? AND t.is_active = ?", ("% (Alberta)", True)).fetchone()["n"]
assert nab == len(alberta_data.ALBERTA_TRIPS), nab
nfl = db.execute("SELECT COUNT(*) AS n FROM trips t JOIN operators o ON o.id=t.operator_id WHERE o.mode = ? AND t.is_active = ?", ("Air", True)).fetchone()["n"]
assert nfl == sum(len(o["trips"]) for o in flight_data.OPERATORS.values()), nfl
db.close()
main.setup_database()
assert [x["id"] for x in c.get("/trips", params={"origin": "Edmonton", "destination": "Calgary"}).json()] == ab_before   # Alberta ids stable
db = main.get_db()
assert db.execute("SELECT COUNT(*) AS n FROM trips t JOIN operators o ON o.id=t.operator_id WHERE o.name LIKE ?", ("% (Alberta)",)).fetchone()["n"] == len(alberta_data.ALBERTA_TRIPS)
n = db.execute("SELECT COUNT(*) AS n FROM trips t JOIN operators o ON o.id=t.operator_id WHERE o.name='Alaska Railroad'").fetchone()["n"]
assert n == len(arr_data.ARR_TRIPS), n
n2 = db.execute("SELECT COUNT(*) AS n FROM trips t JOIN operators o ON o.id=t.operator_id WHERE o.name LIKE ? AND t.is_active = ?", ("GoBus %", True)).fetchone()["n"]
assert n2 == len(gobus_data.GOBUS_TRIPS), n2
n3 = db.execute("SELECT COUNT(*) AS n FROM trips t JOIN operators o ON o.id=t.operator_id WHERE o.name LIKE ?", ("GoBus %",)).fetchone()["n"]
assert n3 >= len(gobus_data.GOBUS_TRIPS) + 1, n3          # the old "GoBus (Ohio)" row(s) remain, hidden (count safe to rerun on a used database)
# Remove my email: deletes the row, gives the same answer whether or not the email was there, rejects bad input
c.post("/members", json={"email": "Remove.Me@Example.com", "tier": 1})
before_n = c.get("/members/count").json()["total"]
r = c.post("/members/remove", json={"email": " remove.me@example.COM "})
assert r.status_code == 200 and r.json() == {"status": "done"}
assert c.get("/members/count").json()["total"] == before_n - 1
r2 = c.post("/members/remove", json={"email": "remove.me@example.com"})      # already gone: same answer
assert r2.status_code == 200 and r2.json() == r.json()
assert c.get("/members/count").json()["total"] == before_n - 1
assert c.post("/members/remove", json={"email": "not-an-email"}).status_code == 422
c.post("/members", json={"email": "remove.me@example.com", "tier": 2})        # can join again after removing
assert c.get("/members/count").json()["total"] == before_n
c.post("/members/remove", json={"email": "remove.me@example.com"})
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
# Saturday-only winter train: runs on a Saturday in season, not on a Tuesday
sat = lambda d: [x for x in c.get("/trips", params={"origin": "Anchorage", "destination": "Fairbanks", "mode": "Rail", "on": d}).json() if x["days"].startswith("Saturday")][0]["in_season"]
assert sat("2026-11-21") is True and sat("2026-11-17") is False, "weekday check"
# Ravn Alaska stopped flying in Aug 2025: even a database that still holds its rows must hide them
db = main.get_db()
rid = main.get_operator_id(db, "Ravn Alaska", "Air", False, "https://www.flyravn.com", "old")
db.execute("INSERT INTO trips (operator_id, origin, destination, depart_time, arrive_time, price, days_running, season_start, season_end, booking_url, source_url, last_updated, is_sample, is_active, fare_estimated) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
           (rid, "Anchorage", "Homer", "", "", 0, None, None, None, "https://www.flyravn.com", "x", "2025-01-01", False, True, False))
db.commit(); db.close()
main.setup_database()
assert not [x for x in c.get("/trips", params={"origin": "Anchorage", "destination": "Homer"}).json() if x["operator"] == "Ravn Alaska"], "Ravn hidden"
# Dutch Harbor, Sand Point, Unalakleet (Aleutian) and Air North (Calgary to Edmonton) are listed
assert [x["operator"] for x in c.get("/trips", params={"origin": "Anchorage", "destination": "Unalakleet"}).json()] == ["Aleutian Airways"]
assert "Air North" in [x["operator"] for x in c.get("/trips", params={"origin": "Calgary", "destination": "Edmonton"}).json()]
print("ALL TESTS PASSED", "postgres" if main.USE_POSTGRES else "sqlite")
