import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "backend"))
from fastapi.testclient import TestClient
import main
c = TestClient(main.app)
assert c.get("/health").json() == {"status": "ok"}
t = c.get("/trips", params={"origin": "anchorage", "destination": "SEWARD"}).json()
assert [x["price"] for x in t] == [45.0, 52.0, 89.0], t
assert t[0]["operator"] == "Sample Coach Lines" and t[0]["partner"] is True and t[1]["partner"] is False
assert len(c.get("/trips", params={"origin": "Anchorage", "destination": "Seward", "mode": "rail"}).json()) == 1
assert c.post("/clicks", json={"ref": "x", "trip_id": 999, "operator": "z"}).status_code == 404
a = c.post("/clicks", json={"ref": "coop-1", "trip_id": t[0]["id"], "operator": "x", "riders": 2}).json()
b = c.post("/clicks", json={"ref": "coop-2", "trip_id": t[2]["id"]}).json()
assert a["operator"] == "Sample Coach Lines"
assert c.post(f"/clicks/{a['id']}/confirm").json()["confirmed"] is True
assert c.post("/clicks/99999/confirm").status_code == 404
r = c.get("/clicks/report", params={"partner_sales": 1800}).json()
co = [o for o in r["operators"] if o["operator"] == "Sample Coach Lines"][0]
assert co["clicks"] == 1 and co["bookings"] == 1 and co["booked_value"] == 90.0 and co["fee_value"] == 5.4, r
assert r["total_clicks"] == 2 and r["capture_rate"] == 0.05, r
assert c.post("/members", json={"email": "", "tier": 1}).status_code == 422
assert c.post("/members", json={"email": "a@b.com", "tier": 3}).status_code == 422
assert c.post("/members", json={"email": " A@B.com ", "tier": 1}).json()["status"] == "created"
assert c.post("/members", json={"email": "a@b.com", "tier": 2}).json()["status"] == "updated"
assert c.get("/members/count").json() == {"tier1": 0, "tier2": 1, "total": 1}
print("ALL TESTS PASSED", "postgres" if main.USE_POSTGRES else "sqlite")
