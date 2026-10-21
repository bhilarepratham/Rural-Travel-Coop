"""Alaska Railroad scheduled trips copied by hand from the railroad's public pages.

UNOFFICIAL: this is a research prototype. Alaska Railroad has not reviewed or approved this list,
and is not a co-op partner. Times and fares can change. Always confirm on alaskarailroad.com.

Sources (checked October 21, 2026, for the 2026 to 2027 seasons):
  Schedule: https://www.alaskarailroad.com/schedules-fares
  Fares:    https://www.alaskarailroad.com/ride-a-train/fares
Fares are adult one way, Adventure class (the standard seat). GoldStar costs more and is not listed.
Only segments with a published fare AND published times are included.
Talkeetna times can vary, and one third party site lists Denali Star Talkeetna times 10 minutes
different from the railroad's own page; the railroad's page is used here.
"""

OPERATOR = {
    "name": "Alaska Railroad",
    "mode": "Rail",
    "is_partner": False,
    "booking_url": "https://www.alaskarailroad.com",
    "notes": "Pilot target only. No agreement. Unofficial listing from the published schedule.",
}

SCHEDULE_URL = "https://www.alaskarailroad.com/schedules-fares"
FARES_URL = "https://www.alaskarailroad.com/ride-a-train/fares"
CHECKED = "2026-10-21"
CLASS_NOTE = "Adventure class fare"

# (origin, destination, depart, arrive, price, days running, season start, season end)
ARR_TRIPS = [
    # Coastal Classic, daily May 14 to Sep 12, 2027
    ("Anchorage", "Girdwood", "06:45", "08:00", 103, "Daily", "2027-05-14", "2027-09-12"),
    ("Anchorage", "Seward",   "06:45", "11:20", 133, "Daily", "2027-05-14", "2027-09-12"),
    ("Girdwood",  "Seward",   "08:05", "11:20", 133, "Daily", "2027-05-14", "2027-09-12"),
    ("Seward",    "Anchorage", "18:00", "22:15", 133, "Daily", "2027-05-14", "2027-09-12"),
    ("Seward",    "Girdwood", "18:00", "20:50", 133, "Daily", "2027-05-14", "2027-09-12"),
    ("Girdwood",  "Anchorage", "20:55", "22:15", 103, "Daily", "2027-05-14", "2027-09-12"),
    # Denali Star northbound, May 12 to Sep 15, 2027
    ("Anchorage", "Wasilla",   "08:20", "09:30", 83, "Daily", "2027-05-12", "2027-09-15"),
    ("Anchorage", "Talkeetna", "08:20", "11:05", 127, "Daily", "2027-05-12", "2027-09-15"),
    ("Anchorage", "Denali",    "08:20", "15:40", 205, "Daily", "2027-05-12", "2027-09-15"),
    ("Anchorage", "Fairbanks", "08:20", "20:00", 294, "Daily", "2027-05-12", "2027-09-15"),
    ("Wasilla",   "Talkeetna", "09:35", "11:05", 127, "Daily", "2027-05-12", "2027-09-15"),
    ("Wasilla",   "Denali",    "09:35", "15:40", 205, "Daily", "2027-05-12", "2027-09-15"),
    ("Wasilla",   "Fairbanks", "09:35", "20:00", 294, "Daily", "2027-05-12", "2027-09-15"),
    ("Talkeetna", "Denali",    "11:20", "15:40", 133, "Daily", "2027-05-12", "2027-09-15"),
    ("Talkeetna", "Fairbanks", "11:20", "20:00", 174, "Daily", "2027-05-12", "2027-09-15"),
    ("Denali",    "Fairbanks", "16:00", "20:00", 102, "Daily", "2027-05-12", "2027-09-15"),
    # Denali Star southbound, May 13 to Sep 16, 2027
    ("Fairbanks", "Denali",    "08:20", "12:10", 102, "Daily", "2027-05-13", "2027-09-16"),
    ("Fairbanks", "Talkeetna", "08:20", "16:50", 174, "Daily", "2027-05-13", "2027-09-16"),
    ("Fairbanks", "Wasilla",   "08:20", "18:15", 294, "Daily", "2027-05-13", "2027-09-16"),
    ("Fairbanks", "Anchorage", "08:20", "20:00", 294, "Daily", "2027-05-13", "2027-09-16"),
    ("Denali",    "Talkeetna", "12:30", "16:50", 133, "Daily", "2027-05-13", "2027-09-16"),
    ("Denali",    "Wasilla",   "12:30", "18:15", 205, "Daily", "2027-05-13", "2027-09-16"),
    ("Denali",    "Anchorage", "12:30", "20:00", 205, "Daily", "2027-05-13", "2027-09-16"),
    ("Talkeetna", "Wasilla",   "17:15", "18:15", 127, "Daily", "2027-05-13", "2027-09-16"),
    ("Talkeetna", "Anchorage", "17:15", "20:00", 127, "Daily", "2027-05-13", "2027-09-16"),
    # Glacier Discovery, May 15 to Sep 12, 2027 (limited dates in May)
    ("Anchorage", "Girdwood",  "09:45", "10:55", 84, "Daily (limited dates in May)", "2027-05-15", "2027-09-12"),
    ("Anchorage", "Whittier",  "09:45", "12:05", 122, "Daily (limited dates in May)", "2027-05-15", "2027-09-12"),
    ("Girdwood",  "Whittier",  "11:00", "12:05", 122, "Daily (limited dates in May)", "2027-05-15", "2027-09-12"),
    ("Whittier",  "Girdwood",  "18:45", "19:40", 122, "Daily (limited dates in May)", "2027-05-15", "2027-09-12"),
    ("Whittier",  "Anchorage", "18:45", "21:00", 122, "Daily (limited dates in May)", "2027-05-15", "2027-09-12"),
    # Hurricane Turn summer, Thursday to Monday, May 13 to Sep 12, 2027
    ("Talkeetna", "Hurricane", "13:00", "15:30", 67, "Thursday to Monday", "2027-05-13", "2027-09-12"),
    # Hurricane Turn winter, first Thursday each month, Oct 1, 2026 to May 6, 2027 (no March service)
    ("Anchorage", "Hurricane", "08:30", "13:20", 107, "First Thursday of the month", "2026-10-01", "2027-05-06"),
    ("Hurricane", "Anchorage", "14:45", "20:00", 107, "First Thursday of the month", "2026-10-01", "2027-05-06"),
    ("Talkeetna", "Anchorage", "16:45", "20:00", 93, "First Thursday of the month", "2026-10-01", "2027-05-06"),
    # Aurora Winter, northbound Saturdays and southbound Sundays, Sep 19, 2026 to May 9, 2027
    ("Anchorage", "Wasilla",   "08:30", "09:50", 86, "Saturday northbound", "2026-09-19", "2027-05-09"),
    ("Anchorage", "Talkeetna", "08:30", "11:25", 104, "Saturday northbound", "2026-09-19", "2027-05-09"),
    ("Anchorage", "Healy",     "08:30", "16:40", 192, "Saturday northbound", "2026-09-19", "2027-05-09"),
    ("Anchorage", "Fairbanks", "08:30", "20:00", 265, "Saturday northbound", "2026-09-19", "2027-05-09"),
    ("Fairbanks", "Anchorage", "08:30", "20:00", 265, "Sunday southbound", "2026-09-19", "2027-05-09"),
    ("Healy",     "Anchorage", "11:45", "20:00", 192, "Sunday southbound", "2026-09-19", "2027-05-09"),
    ("Talkeetna", "Anchorage", "16:50", "20:00", 104, "Sunday southbound", "2026-09-19", "2027-05-09"),
]
