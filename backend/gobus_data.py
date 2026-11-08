"""GoBus (Ohio) trips for eight lines, built from the printed and posted timetables. Unofficial.

Sources: the GoBus Red Line brochure (May 2026) and the schedule PDFs on ridegobus.com for the Green,
Purple, Gray, Lime, Pink, Blue and Yellow lines (see gobus_lines.json for each file and its date).
The Orange Line is NOT loaded: the only schedule found is dated 2023 and GoBus says it has changed.

The timetables list departure times only, so the "arrive" time of a trip is the listed time at the
destination stop. Each place is one city: a rider boards or gets off at the FIRST stop listed for that
city on that bus. Stops marked "reservation only" (the rider must phone GoBus first) and "transfer only"
stops are left out, because they cannot be booked online like a normal stop.

FARES ARE ESTIMATES. GoBus publishes no fare for each pair of stops. What it does publish: fares are
mileage based and go up in $5 steps, a trip under 50 miles on one line is $5, and a one way ticket is
never more than $30 on one line ($25 on the Red Line, per its brochure). So each fare here is
$5 x (1 + whole 50 mile steps), using straight line miles between town centers along the route times a
road factor of 1.2, capped at the line maximum. The 50 mile step width and the 1.2 factor are
assumptions. To use real fares, replace estimate_fare() with a lookup table taken from the booking site.
Every row from this file is flagged fare_estimated and shown that way."""
import json
import math
from pathlib import Path

BOOKING_URL = "https://booking.ridegobus.com"
CHECKED = "2026-11-04"
RED_SEASON = ("2026-05-01", "2027-04-30")   # printed on the Red Line brochure; other lines print none
DAYS = "Daily"
ROAD_FACTOR = 1.2
STEP_MILES = 50
STEP_FARE = 5
LINE_MAX_FARE = {"Red": 25}      # brochure: "All fares are between $5 and $25"
DEFAULT_MAX_FARE = 30            # base fares go "up to $30" on one line ($40 with transfers)

# Approximate town centers (lat, lon), used only to estimate road miles.
CITY_XY = {
    "Toledo": (41.6528, -83.5379), "Bowling Green": (41.3748, -83.6513), "Findlay": (41.0442, -83.6499),
    "Lima": (40.7426, -84.1052), "Kenton": (40.6467, -83.6091), "Bellefontaine": (40.3612, -83.7597),
    "Urbana": (40.1084, -83.7524), "Springfield": (39.9242, -83.8088), "Yellow Springs": (39.8070, -83.8872),
    "Dayton": (39.7589, -84.1916), "Middletown": (39.5151, -84.3983), "Oxford": (39.5070, -84.7452),
    "Cincinnati": (39.1031, -84.5120),
    "Akron": (41.0814, -81.5190), "Ashland": (40.8687, -82.3182), "Ashtabula": (41.8651, -80.7898),
    "Athens": (39.3292, -82.1013), "Caldwell": (39.7487, -81.5157), "Cambridge": (40.0312, -81.5885),
    "Canton": (40.7989, -81.3784), "Cleveland": (41.4993, -81.6944), "Columbus": (39.9612, -82.9988),
    "Elyria": (41.3684, -82.1077), "Fremont": (41.3503, -83.1219), "Gambier": (40.3756, -82.3957),
    "Lancaster": (39.7137, -82.5993), "Logan": (39.5403, -82.4071), "Loudonville": (40.6359, -82.2326),
    "Mansfield": (40.7584, -82.5154), "Marietta": (39.4154, -81.4548), "Marion": (40.5887, -83.1285),
    "Marysville": (40.2364, -83.3671), "Mount Eaton": (40.7042, -81.6918), "Mount Vernon": (40.3934, -82.4857),
    "Nelsonville": (39.4595, -82.2321), "New Philadelphia": (40.4898, -81.4457), "Newark": (40.0581, -82.4013),
    "Norwalk": (41.2426, -82.6157), "Painesville": (41.7245, -81.2457), "Parkersburg": (39.2667, -81.5615),
    "Pittsburgh": (40.4915, -80.2329), "Port Clinton": (41.5120, -82.9377), "Sandusky": (41.4489, -82.7080),
    "St Clairsville": (40.0803, -80.9007), "Steubenville": (40.3698, -80.6340), "Upper Sandusky": (40.8273, -83.2810),
    "Utica": (40.2326, -82.4510), "Van Wert": (40.8695, -84.5841), "Wheeling": (40.0640, -80.7209),
    "Wooster": (40.8051, -81.9351), "Zanesville": (39.9403, -82.0132),
}

# ---- Red Line, as printed (departure time of each bus at each stop) ----
SOUTH_STOPS = ["Toledo", "Bowling Green", "Findlay", "Lima", "Kenton", "Bellefontaine", "Urbana",
               "Springfield", "Yellow Springs", "Dayton", "Middletown", "Oxford", "Cincinnati"]
SOUTH = {   # stop: (bus 62, bus 64) as printed
    "Toledo": ("7:21a", "10:21a"), "Bowling Green": ("7:51a", "10:51a"), "Findlay": ("8:22a", "11:22a"),
    "Lima": ("9:05a", "12:05p"), "Kenton": ("9:48a", "12:48p"), "Bellefontaine": ("10:26a", "1:26p"),
    "Urbana": ("10:57a", "1:57p"), "Springfield": ("11:55a", "2:55p"), "Yellow Springs": ("12:16p", "3:16p"),
    "Dayton": ("12:49p", "3:49p"), "Middletown": ("1:27p", "4:27p"), "Oxford": ("2:05p", "5:05p"),
    "Cincinnati": ("3:00p", "6:00p")}
NORTH = {   # stop: (bus 63, bus 65) as printed
    "Toledo": ("4:03p", "7:03p"), "Bowling Green": ("3:33p", "6:33p"), "Findlay": ("3:02p", "6:02p"),
    "Lima": ("2:19p", "5:19p"), "Kenton": ("1:36p", "4:36p"), "Bellefontaine": ("12:58p", "3:58p"),
    "Urbana": ("12:27p", "3:27p"), "Springfield": ("11:57a", "2:57p"), "Yellow Springs": ("11:04a", "2:04p"),
    "Dayton": ("10:31a", "1:31p"), "Middletown": ("9:53a", "12:53p"), "Oxford": ("9:15a", "12:15p"),
    "Cincinnati": ("8:20a", "11:20a")}


def to24(t: str) -> str:
    """'7:21a' or '7:21 AM' to '07:21'."""
    t = t.strip().upper().replace(" ", "")
    pm = t.endswith("P") or t.endswith("PM")
    h, m = t.rstrip("APM").split(":")
    h = int(h) % 12 + (12 if pm else 0)
    return f"{h:02d}:{int(m):02d}"


def minutes(hhmm: str) -> int:
    h, m = hhmm.split(":")
    return int(h) * 60 + int(m)


def miles_between(a: str, b: str) -> float:
    la1, lo1 = map(math.radians, CITY_XY[a])
    la2, lo2 = map(math.radians, CITY_XY[b])
    d = math.sin((la2 - la1) / 2) ** 2 + math.cos(la1) * math.cos(la2) * math.sin((lo2 - lo1) / 2) ** 2
    return 2 * 3958.8 * math.asin(math.sqrt(d))


def estimate_fare(road_miles: float, line: str) -> int:
    """$5 per 50 road miles step (first step $5), at least $5, at most the line maximum."""
    fare = STEP_FARE * (1 + int(road_miles // STEP_MILES))
    return int(min(LINE_MAX_FARE.get(line, DEFAULT_MAX_FARE), max(STEP_FARE, fare)))


def sequences_red() -> list[dict]:
    south = [{"line": "Red", "schedule": f"Bus {n}", "direction": "Toledo to Cincinnati",
              "stops": [(c, to24(SOUTH[c][i])) for c in SOUTH_STOPS]} for i, n in ((0, 62), (1, 64))]
    rev = list(reversed(SOUTH_STOPS))
    north = [{"line": "Red", "schedule": f"Bus {n}", "direction": "Cincinnati to Toledo",
              "stops": [(c, to24(NORTH[c][i])) for c in rev]} for i, n in ((0, 63), (1, 65))]
    return south + north


DATA_ISSUES: list[dict] = []     # things dropped because the printed times disagree; read by the Day 2 workbook
EXCLUDED_STOPS: dict = {}        # (line, stop, reason) -> count of bus runs it was left out of


def sequences_other() -> list[dict]:
    raw = json.loads((Path(__file__).parent / "gobus_lines.json").read_text())
    out = []
    for sch in raw["schedules"]:
        seen, stops = set(), []
        for s in sch["stops"]:
            if s["skip"]:
                key = (sch["line"], s["stop"], s["skip"])
                EXCLUDED_STOPS[key] = EXCLUDED_STOPS.get(key, 0) + 1
                continue
            if s["city"] in seen:       # second stop in the same city: the rider uses the first one
                continue
            seen.add(s["city"])
            stops.append((s["city"], to24(s["time"]), s["stop"]))
        # Printed times must rise along the route. Where one does not, drop the earlier-listed stop and note it.
        i = 1
        while i < len(stops):
            if minutes(stops[i][1]) < minutes(stops[i - 1][1]):
                bad = stops.pop(i - 1)
                DATA_ISSUES.append({"line": sch["line"], "schedule": sch["schedule"], "dropped": bad[2],
                                    "time": bad[1], "reason": f"time is later than the next stop ({stops[i - 1][2]} {stops[i - 1][1]}) on the same bus"})
                i = max(1, i - 1)
            else:
                i += 1
        out.append({"line": sch["line"], "schedule": f"Trip {sch['schedule']}", "direction": sch["direction"],
                    "stops": [(c, t) for c, t, _ in stops]})
    return out


def trips_for(seq: dict) -> list[tuple]:
    """Every stop to stop trip on one bus run: (origin, dest, depart, arrive, price, days, start, end)."""
    line, stops = seq["line"], seq["stops"]
    start, end = RED_SEASON if line == "Red" else (None, None)
    cum = [0.0]
    for (a, _), (b, _) in zip(stops, stops[1:]):
        cum.append(cum[-1] + miles_between(a, b))
    out = []
    for i, (a, dep) in enumerate(stops):
        for j in range(i + 1, len(stops)):
            b, arr = stops[j]
            if a == b or minutes(arr) <= minutes(dep):
                continue
            out.append((a, b, dep, arr, estimate_fare((cum[j] - cum[i]) * ROAD_FACTOR, line), DAYS, start, end))
    return out


LINE_NAMES = ["Red", "Green", "Purple", "Gray", "Lime", "Pink", "Blue", "Yellow"]
_META = json.loads((Path(__file__).parent / "gobus_lines.json").read_text())["meta"]
_SEQS = sequences_red() + sequences_other()

# One operator row per line, so the result card says which line the bus is on.
OPERATORS = {}
for _line in LINE_NAMES:
    _seen, _trips = set(), []
    for _s in (s for s in _SEQS if s["line"] == _line):
        for t in trips_for(_s):
            if t[:3] not in _seen:     # same origin, destination and departure time on two schedules: keep one
                _seen.add(t[:3])
                _trips.append(t)
    OPERATORS[_line] = {
        "name": f"GoBus {_line} Line (Ohio)", "mode": "Bus", "is_partner": False, "booking_url": BOOKING_URL,
        "notes": "Intercity bus network run for ODOT. Unofficial listing, not a partner.",
        "source_url": ("https://www.wittenberg.edu/sites/default/files/media/GoBusRouteBrochure.pdf"
                       if _line == "Red" else _META[_line]["source_url"]),
        "file_date": "2026-05" if _line == "Red" else _META[_line]["file_date"],
        "trips": _trips}

LEGACY_OPERATOR = "GoBus (Ohio)"     # the old single operator name; its trips are hidden on load
GOBUS_TRIPS = [t for o in OPERATORS.values() for t in o["trips"]]
GOBUS_CITIES = sorted({t[0] for t in GOBUS_TRIPS} | {t[1] for t in GOBUS_TRIPS})
