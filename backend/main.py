"""Scheduled airline routes for Alaska and Alberta, from public news pages and airline route lists. Unofficial.

WHAT IS HERE AND WHAT IS NOT. Each row says: this airline flies between these two places. There are NO times and NO
fares: airlines show both only inside their booking engines, so the rider is sent to the airline's own site. Rows are
stored with empty time text and price 0; the API shows both as null (same rule as the Alberta bus listings).
Routes change often (seasons, carriers leaving), so every row is a snapshot and the app says so.

ALASKA (US dollars)
  Alaska Airlines: in-state nonstops from Anchorage to Fairbanks, Kodiak, Cordova, King Salmon, Adak, Dillingham,
    Bethel, Nome, Kotzebue and Utqiagvik (Anchorage Daily News, Oct 11, 2025); Anchorage to Juneau (Alaska Air Cargo
    summer 2026 network page).
  Grant Aviation: Anchorage to Kenai (Alaska Business, Mar 2025; FlightConnections, Apr 2026). Kenai Aviation, which
    also flew this route, shut down (AvWeb), so it is not listed.
  Aleutian Airways: Anchorage to Kenai (two daily round trips from June 6, 2025; KDLL, Feb 28, 2025), Homer, King
    Salmon, Dutch Harbor and Sand Point (Alaska Airlines partner page for Aleutian), and Unalakleet (three weekly round
    trips from Dec 2, 2025; Peninsula Clarion).
  Ravn Alaska is NOT listed: it ended Homer service on March 3, 2025 and stopped all operations on August 5, 2025
    (City of Homer airport page; Anchorage Daily News). Schedule sites that still show it are out of date.

ALBERTA (Canadian dollars)
  Air Canada and WestJet between Calgary and Edmonton, Fort McMurray and Grande Prairie, and WestJet between Edmonton
  and Fort McMurray and Grande Prairie (Air Canada route page; WestJet summer 2026 schedule changes on AeroRoutes;
  FlightConnections). Air North between Calgary and Edmonton (flyairnorth.com is its own site).
  NOT listed: WestJet's Calgary to Lethbridge and Calgary to Medicine Hat flights, which ended June 24, 2026.
  Not listed: small northern carriers.

OHIO: no rows. The sources I found show Ohio airports (Columbus, Cleveland, Cincinnati, Dayton, Akron-Canton, Toledo)
served by flights to other states, and no scheduled airline flights between Ohio cities. The app shows a note instead.

Booking links are each airline's home page. Each of the six site addresses was seen on public pages (Day 2 check).
Not checked: whether an airline keeps our tracking code on its own site."""

CHECKED = "2026-11-17"

OPERATORS = {
    "Alaska Airlines": {
        "name": "Alaska Airlines", "mode": "Air", "is_partner": False, "booking_url": "https://www.alaskaair.com",
        "notes": "Airline. Listing only: no times or fares. Not a partner.", "region": "Alaska",
        "src": "https://www.adn.com/alaska-life/travel/2025/10/11/with-tourism-season-in-the-rearview-mirror-alaskas-airline-calendar-begins-to-shift/",
        "pairs": [("Anchorage", c) for c in ("Fairbanks", "Juneau", "Kodiak", "Cordova", "King Salmon", "Adak",
                                             "Dillingham", "Bethel", "Nome", "Kotzebue", "Utqiagvik")],
    },
    "Grant Aviation": {
        "name": "Grant Aviation", "mode": "Air", "is_partner": False, "booking_url": "https://www.flygrant.com",
        "notes": "Small plane airline. Listing only: no times or fares. Not a partner.", "region": "Alaska",
        "src": "https://www.akbizmag.com/industry/transportation/aleutian-airways-adding-daily-service-to-kenai/",
        "pairs": [("Anchorage", "Kenai")],
    },
    "Aleutian Airways": {
        "name": "Aleutian Airways", "mode": "Air", "is_partner": False, "booking_url": "https://www.flyaleutian.com",
        "notes": "Airline. Listing only: no times or fares. Not a partner.", "region": "Alaska",
        "src": "https://www.kdll.org/local-news/2025-02-28/aleutian-airways-to-launch-kenai-anchorage-flights",
        "pairs": [("Anchorage", "Kenai"),
                  ("Anchorage", "Homer", "https://www.alaskaair.com/ko-kr/atmosrewards/content/partners/airlines/aleutian-airways"),
                  ("Anchorage", "King Salmon", "https://www.alaskaair.com/ko-kr/atmosrewards/content/partners/airlines/aleutian-airways"),
                  ("Anchorage", "Dutch Harbor", "https://www.alaskaair.com/ko-kr/atmosrewards/content/partners/airlines/aleutian-airways"),
                  ("Anchorage", "Sand Point", "https://www.alaskaair.com/ko-kr/atmosrewards/content/partners/airlines/aleutian-airways"),
                  ("Anchorage", "Unalakleet", "https://www.peninsulaclarion.com/news/aleutian-airways-to-offer-roundtrip-flights-between-anchorage-and-unalakleet/")],
    },
    "Air Canada": {
        "name": "Air Canada", "mode": "Air", "is_partner": False, "booking_url": "https://www.aircanada.com",
        "notes": "Airline. Listing only: no times or fares. Not a partner.", "region": "Alberta",
        "src": "https://www.flightconnections.com/flights-to-edmonton-yeg",
        "pairs": [("Calgary", "Edmonton", "https://aviability.com/en/airport/yeg-edmonton/destinations"),
                  ("Calgary", "Fort McMurray", "https://www.aircanada.com/en-ca/flights-from-calgary-to-fort-mcmurray"),
                  ("Calgary", "Grande Prairie", "https://www.flightconnections.com/flights-from-yyc-to-yqu")],
    },
    "WestJet": {
        "name": "WestJet", "mode": "Air", "is_partner": False, "booking_url": "https://www.westjet.com",
        "notes": "Airline. Listing only: no times or fares. Not a partner.", "region": "Alberta",
        "src": "https://www.flightconnections.com/flights-to-edmonton-yeg",
        "pairs": [("Calgary", "Edmonton", "https://www.aeroroutes.com/eng/260224-wsns26ca"), ("Calgary", "Fort McMurray", "https://www.aeroroutes.com/eng/260224-wsns26ca"),
                  ("Calgary", "Grande Prairie", "https://www.flightconnections.com/flights-from-yyc-to-yqu"),
                  ("Edmonton", "Fort McMurray", "https://www.aeroroutes.com/eng/260224-wsns26ca"), ("Edmonton", "Grande Prairie", "https://www.aeroroutes.com/eng/260224-wsns26ca")],
    },
    "Air North": {
        "name": "Air North", "mode": "Air", "is_partner": False, "booking_url": "https://www.flyairnorth.com",
        "notes": "Airline based in Whitehorse. Listing only: no times or fares. Not a partner.", "region": "Alberta",
        "src": "https://aviability.com/en/airport/yeg-edmonton/destinations",
        "pairs": [("Calgary", "Edmonton")],
    },
}

# Operators that used to be listed and must now be hidden in a database that still holds their rows.
REMOVED_OPERATORS = ["Ravn Alaska"]

# Both directions for every pair.
for _op in OPERATORS.values():
    # A pair is (place, place) or (place, place, source page for that pair).
    _op["trips"] = [(p[0], p[1], None, None, p[2] if len(p) > 2 else _op["src"]) for p in _op["pairs"]] + \
                   [(p[1], p[0], None, None, p[2] if len(p) > 2 else _op["src"]) for p in _op["pairs"]]

# Places that exist only because of flights (the rest already belong to a region through rail or bus rows).
ALASKA_AIR_CITIES = ["Adak", "Bethel", "Cordova", "Dillingham", "Dutch Harbor", "Homer", "Juneau", "Kenai", "King Salmon",
                     "Kodiak", "Kotzebue", "Nome", "Sand Point", "Unalakleet", "Utqiagvik"]

OHIO_NOTE = ("Airlines serve Columbus, Cleveland, Cincinnati, Dayton, Akron-Canton and Toledo mainly with flights to "
             "other states. I found no scheduled flights between Ohio cities.")
