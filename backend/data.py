"""Sample data for the prototype. Everything here is made up for demonstration.
Operators, fares and times are NOT real. Replace with real data later."""

CITIES = ["Anchorage", "Seward", "Talkeetna", "Fairbanks"]

TRIPS = [
    {"id": 1, "from": "Anchorage", "to": "Seward", "operator": "Sample Railroad", "mode": "Rail",
     "depart": "08:00", "arrive": "12:00", "price": 89, "partner": True,
     "url": "https://example.com/sample-railroad/book"},
    {"id": 2, "from": "Anchorage", "to": "Seward", "operator": "Sample Coach Lines", "mode": "Bus",
     "depart": "09:30", "arrive": "12:30", "price": 45, "partner": True,
     "url": "https://example.com/sample-coach/book"},
    {"id": 3, "from": "Anchorage", "to": "Seward", "operator": "Sample Shuttle Co", "mode": "Bus",
     "depart": "13:00", "arrive": "16:30", "price": 52, "partner": False,
     "url": "https://example.com/sample-shuttle/book"},
    {"id": 4, "from": "Anchorage", "to": "Talkeetna", "operator": "Sample Railroad", "mode": "Rail",
     "depart": "08:15", "arrive": "11:45", "price": 79, "partner": True,
     "url": "https://example.com/sample-railroad/book"},
    {"id": 5, "from": "Anchorage", "to": "Fairbanks", "operator": "Sample Railroad", "mode": "Rail",
     "depart": "08:00", "arrive": "20:00", "price": 199, "partner": True,
     "url": "https://example.com/sample-railroad/book"},
    {"id": 6, "from": "Seward", "to": "Anchorage", "operator": "Sample Coach Lines", "mode": "Bus",
     "depart": "15:00", "arrive": "18:00", "price": 45, "partner": True,
     "url": "https://example.com/sample-coach/book"},
]
