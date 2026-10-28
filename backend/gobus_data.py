"""GoBus (Ohio) Red Line trips, built from the printed timetable. Unofficial.

Source: GoBus Red Line route brochure, printed May 2026. The timetable lists departure times only, so
the "arrive" time of a trip is the listed time at the destination stop. GoBus fares are mileage based
and the brochure says "All fares are between $5 and $25". It does not give a fare for each pair of
stops, so each fare here is an ESTIMATE: $5 plus $20 in proportion to the time on the bus, out of the
whole Toledo to Cincinnati run. Trips from this file are flagged fare_estimated and shown that way.
To use real fares, replace estimate_fare() with a lookup table taken from the booking site."""

OPERATOR = {"name": "GoBus (Ohio)", "mode": "Bus", "is_partner": False,
            "booking_url": "https://booking.ridegobus.com",
            "notes": "Intercity bus network run for ODOT. Unofficial listing, not a partner."}
SOURCE_URL = "https://www.wittenberg.edu/sites/default/files/media/GoBusRouteBrochure.pdf"
CHECKED = "2026-10-27"
DAYS = "Daily"
SEASON_START = "2026-05-01"
SEASON_END = "2027-04-30"
FARE_MIN, FARE_MAX = 5, 25

# Stops in order from Toledo to Cincinnati, with the departure time of each bus.
# Southbound buses 62 and 64 follow this order. Northbound buses 63 and 65 run it in reverse.
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
FULL_RUN_MINUTES = 489   # Toledo 7:21a to Cincinnati 3:30p on bus 62 (airport stop included)


def to24(t: str) -> str:
    h, m = t[:-1].split(":")
    h = int(h) % 12 + (12 if t[-1] == "p" else 0)
    return f"{h:02d}:{int(m):02d}"


def minutes(hhmm: str) -> int:
    h, m = hhmm.split(":")
    return int(h) * 60 + int(m)


def estimate_fare(depart: str, arrive: str) -> int:
    fare = FARE_MIN + (FARE_MAX - FARE_MIN) * (minutes(arrive) - minutes(depart)) / FULL_RUN_MINUTES
    return int(min(FARE_MAX, max(FARE_MIN, round(fare))))


def build_trips() -> list[tuple]:
    """Every stop to stop trip on each bus: (origin, dest, depart, arrive, price, days, start, end)."""
    out = []
    for idx, table, order in ((0, SOUTH, SOUTH_STOPS), (1, SOUTH, SOUTH_STOPS)):
        for i, a in enumerate(order):
            for b in order[i + 1:]:
                dep, arr = to24(table[a][idx]), to24(table[b][idx])
                out.append((a, b, dep, arr, estimate_fare(dep, arr), DAYS, SEASON_START, SEASON_END))
    rev = list(reversed(SOUTH_STOPS))
    for idx in (0, 1):
        for i, a in enumerate(rev):
            for b in rev[i + 1:]:
                dep, arr = to24(NORTH[a][idx]), to24(NORTH[b][idx])
                out.append((a, b, dep, arr, estimate_fare(dep, arr), DAYS, SEASON_START, SEASON_END))
    return out


GOBUS_TRIPS = build_trips()
