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
  Aleutian Airways: Anchorage to Kenai (two daily round trips from June 6, 2025), Homer and King Salmon (KDLL, Feb 28,
    2025; Peninsula Clarion).
  Ravn Alaska: Anchorage to Homer (Anchorage Daily News, Jun 29, 2024; a 2026 to 2027 schedule list shows it too).

ALBERTA (Canadian dollars)
  Air Canada and WestJet between Calgary and Edmonton, Fort McMurray and Grande Prairie, and WestJet between Edmonton
  and Fort McMurray and Grande Prairie (FlightConnections, Apr 2026; Aerocorner YYC page; Airline Revenue Economics).
  NOT listed: WestJet's Calgary to Lethbridge and Calgary to Medicine Hat flights, which ended June 24, 2026.
  Not listed because the booking site was not checked: Air North (Calgary to Edmonton) and small northern carriers.

OHIO: no rows. The sources I found show Ohio airports (Columbus, Cleveland, Cincinnati, Dayton, Akron-Canton, Toledo)
served by flights to other states, and no scheduled airline flights between Ohio cities. The app shows a note instead.

Booking links are each airline's home page. Not checked: whether an airline keeps our tracking code on its own site."""

CHECKED = "2026-11-14"

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
        "pairs": [("Anchorage", "Kenai"), ("Anchorage", "Homer"), ("Anchorage", "King Salmon")],
    },
    "Ravn Alaska": {
        "name": "Ravn Alaska", "mode": "Air", "is_partner": False, "booking_url": "https://www.flyravn.com",
        "notes": "Airline. Listing only: no times or fares. Not a partner.", "region": "Alaska",
        "src": "https://adn.com/alaska-life/travel/2024/06/29/regional-air-carriers-are-a-critical-part-of-alaskas-transportation-infrastructure",
        "pairs": [("Anchorage", "Homer")],
    },
    "Air Canada": {
        "name": "Air Canada", "mode": "Air", "is_partner": False, "booking_url": "https://www.aircanada.com",
        "notes": "Airline. Listing only: no times or fares. Not a partner.", "region": "Alberta",
        "src": "https://www.flightconnections.com/flights-to-edmonton-yeg",
        "pairs": [("Calgary", "Edmonton"), ("Calgary", "Fort McMurray"), ("Calgary", "Grande Prairie")],
    },
    "WestJet": {
        "name": "WestJet", "mode": "Air", "is_partner": False, "booking_url": "https://www.westjet.com",
        "notes": "Airline. Listing only: no times or fares. Not a partner.", "region": "Alberta",
        "src": "https://www.flightconnections.com/flights-to-edmonton-yeg",
        "pairs": [("Calgary", "Edmonton"), ("Calgary", "Fort McMurray"), ("Calgary", "Grande Prairie"),
                  ("Edmonton", "Fort McMurray"), ("Edmonton", "Grande Prairie")],
    },
}

# Both directions for every pair.
for _op in OPERATORS.values():
    _op["trips"] = [(a, b, None, None, _op["src"]) for (a, b) in _op["pairs"]] + \
                   [(b, a, None, None, _op["src"]) for (a, b) in _op["pairs"]]

# Places that exist only because of flights (the rest already belong to a region through rail or bus rows).
ALASKA_AIR_CITIES = ["Adak", "Bethel", "Cordova", "Dillingham", "Homer", "Juneau", "Kenai", "King Salmon", "Kodiak",
                     "Kotzebue", "Nome", "Utqiagvik"]

OHIO_NOTE = ("Airlines serve Columbus, Cleveland, Cincinnati, Dayton, Akron-Canton and Toledo mainly with flights to "
             "other states. I found no scheduled flights between Ohio cities.")
