"""Alberta bus listings: which carrier sells which pair of towns, from public pages. Unofficial.

WHAT IS HERE AND WHAT IS NOT. No Alberta carrier publishes a timetable we could read (times appear only inside each
carrier's booking engine), so these rows have NO departure or arrival times. Each row says: this carrier sells a
ticket between these two towns, on these days if the carrier's page says so. The rider is sent to the carrier's own
site for times and the exact fare. Rows are stored with empty time text and price 0; the API shows both as null.

FARES. Only Red Arrow rows get a fare, and it is an estimate. Red Arrow's route pages show an "average price" for
some routes: Edmonton to Fort McMurray $92.24, Fort McMurray to Red Deer $136.76, and (search snippet) Edmonton to
Calgary $74.57. A rate of $0.23 per road kilometre, with road km = straight line km x 1.12, gives $72, $97 and $134
(within 5.2%). The rate is a fit to those three points, so it is used only from 150 road km up (about half the
shortest published route); shorter pairs show no fare. Canadian dollars. Cold Shot, Rider Express and Flix rows have
no usable published fares and show none.

Sources (checked 2026-11-11): Red Arrow route pages on redarrow.ca; 511 Alberta bus service list (revised Mar 18,
2025); FlixBus news release of Apr 29, 2026; Busbud, Wanderu and CheckMyBus listings for Cold Shot and Rider Express.
Town coordinates below are approximate and typed by hand; they only feed the fare estimate."""
import math

CHECKED = "2026-11-11"
ROAD_FACTOR = 1.12               # assumption, same as the Ohio rule
RATE_PER_KM = 0.23               # CAD per road km, fitted to three Red Arrow route averages
MIN_FARE_KM = 150                # the rule is not used below this many road km

# Approximate town centers (lat, lon). Needed only for Red Arrow towns, the only rows that get a fare.
CITY_XY = {
    "Edmonton": (53.5461, -113.4938), "Calgary": (51.0447, -114.0719), "Red Deer": (52.2681, -113.8112),
    "Fort McMurray": (56.7264, -111.3803), "Gibbons": (53.83, -113.33), "Radway": (54.07, -112.95),
    "Boyle": (54.58, -112.81), "Grassland": (54.98, -112.47), "Wandering River": (55.17, -112.50),
}

# Red Arrow's own "Book Now" button points here (read on redarrow.ca on 2026-11-24). The older
# redarrow.ca/order/reservation address now redirects to the home page and drops our tracking code.
RA_BOOK = "https://pwt.betterez.com/cart/60d0b80b88369e0fb992a014/reservation/60d0b80b88369e0fb992a015"
RA_ROUTES = "https://www.redarrow.ca/routes/"
SRC_A = RA_ROUTES + "calgary-to-edmonton"
SRC_B = RA_ROUTES + "edmonton-to-fort-mcmurray/"
SRC_C_SOUTH = RA_ROUTES + "red-deer-to-fort-mcmurray-2"        # Red Deer to Fort McMurray: Mon to Thu and Sun
SRC_C_NORTH = "https://redarrow.ca/routes/fort-mcmurray-to-red-deer"
SRC_FLIX = "https://www.flixbus.com/flixbus-expands-western-canada-network-with-new-prairie-routes-may-7"
SRC_COLD = "https://www.busbud.com/en/busmaatschappij/coldshot"
SRC_RIDER = "https://www.busbud.com/en-ca/bus-company/rider-express"
SRC_RIDER_CMB = "https://www.checkmybus.com/calgary-ab/lloydminster-ab"


def km_between(a: str, b: str) -> float:
    la1, lo1 = map(math.radians, CITY_XY[a])
    la2, lo2 = map(math.radians, CITY_XY[b])
    d = math.sin((la2 - la1) / 2) ** 2 + math.cos(la1) * math.cos(la2) * math.sin((lo2 - lo1) / 2) ** 2
    return 2 * 6371.0 * math.asin(math.sqrt(d))


def estimate_fare(road_km: float):
    """Red Arrow estimate in whole Canadian dollars, or None when the pair is shorter than the tested range."""
    if road_km < MIN_FARE_KM:
        return None
    return round(RATE_PER_KM * road_km)


def red_arrow_fare(a: str, b: str):
    return estimate_fare(km_between(a, b) * ROAD_FACTOR)


# ---- Red Arrow: three lines, read from the route pages ----
LINE_A = ["Edmonton", "Red Deer", "Calgary"]                                   # every day, both ways
LINE_B = ["Edmonton", "Gibbons", "Radway", "Boyle", "Grassland", "Wandering River", "Fort McMurray"]   # every day
LINE_C_NORTH = ["Gibbons", "Radway", "Boyle", "Grassland", "Wandering River", "Fort McMurray"]  # beyond Edmonton


def _pairs(stops):
    for i, a in enumerate(stops):
        for b in stops[i + 1:]:
            yield a, b
            yield b, a


def red_arrow_trips() -> list[tuple]:
    """(origin, destination, days, price, source_url). One row per directed pair; first line listed wins."""
    out, seen = [], set()

    def add(a, b, days, src):
        if (a, b) in seen:
            return
        seen.add((a, b))
        out.append((a, b, days, red_arrow_fare(a, b), src))

    for a, b in _pairs(LINE_A):
        add(a, b, "Daily", SRC_A)
    for a, b in _pairs(LINE_B):
        add(a, b, "Daily", SRC_B)
    for b in LINE_C_NORTH:      # Red Deer to Fort McMurray through Edmonton: Mon, Tue, Wed, Thu, Sun on that page
        add("Red Deer", b, "Mon, Tue, Wed, Thu, Sun", SRC_C_SOUTH)
        add(b, "Red Deer", "Days not shown on the route page", SRC_C_NORTH)
    return out


def _both(pairs, src):
    return [t for a, b in pairs for t in ((a, b, None, None, src), (b, a, None, None, src))]


# ---- Flix: pairs named in the Apr 29, 2026 release and 2024 to 2025 launch news ----
FLIX_PAIRS = [("Edmonton", "Calgary"), ("Edmonton", "Red Deer"), ("Red Deer", "Calgary"), ("Calgary", "Lethbridge"),
              ("Calgary", "Medicine Hat"), ("Lethbridge", "Medicine Hat")]
# ---- Cold Shot: pairs listed as Cold Shot routes on Busbud ----
COLD_PAIRS = [("Edmonton", "Calgary"), ("Edmonton", "Red Deer"), ("Calgary", "Red Deer"),
              ("Edmonton", "Fort McMurray"), ("Calgary", "Fort McMurray"), ("Edmonton", "Cold Lake"),
              ("Edmonton", "Bonnyville"), ("Edmonton", "Grande Prairie"), ("Edmonton", "Peace River"),
              ("Edmonton", "Whitecourt"), ("Edmonton", "Slave Lake"), ("Edmonton", "Valleyview"),
              ("Calgary", "Grande Prairie")]
# ---- Rider Express: pairs named on Busbud, Wanderu and CheckMyBus ----
RIDER_PAIRS = [("Edmonton", "Calgary"), ("Edmonton", "Fort McMurray"), ("Calgary", "Fort McMurray"),
               ("Edmonton", "Lloydminster")]
RIDER_PAIRS_CMB = [("Calgary", "Lloydminster"), ("Red Deer", "Lloydminster")]

OPERATORS = {
    "Red Arrow": {
        "name": "Red Arrow (Alberta)", "mode": "Bus", "is_partner": False, "booking_url": RA_BOOK,
        "notes": "Intercity coach company. Listing only: no times. Not a partner.", "trips": red_arrow_trips()},
    "Flix": {
        "name": "FlixBus (Alberta)", "mode": "Bus", "is_partner": False, "booking_url": "https://www.flixbus.ca",
        "notes": "Sells tickets for coaches run by local companies. Listing only: no times. Not a partner.",
        "trips": _both(FLIX_PAIRS, SRC_FLIX)},
    "Cold Shot": {
        "name": "Cold Shot (Alberta)", "mode": "Bus", "is_partner": False, "booking_url": "https://www.coldshot.ca",
        "notes": "Intercity shuttle service. Listing only: no times. Not a partner.",
        "trips": _both(COLD_PAIRS, SRC_COLD)},
    "Rider Express": {
        "name": "Rider Express (Alberta)", "mode": "Bus", "is_partner": False, "booking_url": "https://www.riderexpress.ca",
        "notes": "Intercity coach company. Listing only: no times. Not a partner.",
        "trips": _both(RIDER_PAIRS, SRC_RIDER) + _both(RIDER_PAIRS_CMB, SRC_RIDER_CMB)},
}

ALBERTA_TRIPS = [t for o in OPERATORS.values() for t in o["trips"]]
ALBERTA_CITIES = sorted({t[0] for t in ALBERTA_TRIPS} | {t[1] for t in ALBERTA_TRIPS})
AIR_LINKS = [("Air Canada", "https://www.aircanada.com"), ("WestJet", "https://www.westjet.com")]
