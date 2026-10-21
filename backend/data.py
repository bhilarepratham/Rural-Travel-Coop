"""Made up demo data for the prototype. These bus trips are NOT real.
Operators, fares and times here are invented so the comparison screen has a bus to compare with.
Real Alaska Railroad trips are in arr_data.py."""

TRIPS = [
    {"from": "Anchorage", "to": "Seward", "operator": "Sample Coach Lines", "mode": "Bus",
     "depart": "09:30", "arrive": "12:30", "price": 45, "partner": True,
     "url": "https://example.com/sample-coach/book"},
    {"from": "Anchorage", "to": "Seward", "operator": "Sample Shuttle Co", "mode": "Bus",
     "depart": "13:00", "arrive": "16:30", "price": 52, "partner": False,
     "url": "https://example.com/sample-shuttle/book"},
    {"from": "Seward", "to": "Anchorage", "operator": "Sample Coach Lines", "mode": "Bus",
     "depart": "15:00", "arrive": "18:00", "price": 45, "partner": True,
     "url": "https://example.com/sample-coach/book"},
]
