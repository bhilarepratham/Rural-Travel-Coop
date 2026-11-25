# Rural Travel Co-op prototype

An unofficial research prototype of a travel price comparison and booking cooperative for regional and rural bus, rail and air. It is not a real booking site: it takes no payments and sells no tickets. Visitors compare trips and are sent to the operator's own site to buy.

- Alaska Railroad trips (41) are copied by hand from the railroad's public schedule and fares pages. The railroad has not reviewed them and is not a partner.
- GoBus (Ohio) trips on all 9 lines (Red, Green, Purple, Gray, Lime, Pink, Blue, Yellow, Orange; 768 stop to stop trips, 55 places) are copied from its public timetables. GoBus publishes how fares work (a mileage table: next stop $5, under 75 miles $10, 75 to 159 miles $15, 160 to 199 miles $20, 200 miles or more $25, and $5 under 50 miles on one line) and not a fare for each pair of stops, so each fare is an estimate from our own mile count and is labeled "Fare estimated". GoBus has not reviewed them and is not a partner.
- Alberta bus listings (110 rows, 19 places) say which carrier sells a route between two towns: Red Arrow (60 pairs), FlixBus (12), Cold Shot (26) and Rider Express (12), read from the carriers' public route pages, the 511 Alberta bus list and third-party listings. No Alberta carrier publishes a timetable we could read, so these rows have no times: each card says times are on the operator's site. Only Red Arrow rows carry a fare (Canadian dollars, labeled "Fare estimated"); the others say "Fare on operator site". None of these carriers is a partner. Air Canada and WestJet appear only as two plain links on Alberta results; the app does not compare or sell flights.
- Airline route listings (54 rows) say which airline flies a route, with no times and no fares: each card says times and fares are on the airline's site. Alaska: Alaska Airlines from Anchorage to Fairbanks, Juneau, Kodiak, Cordova, King Salmon, Adak, Dillingham, Bethel, Nome, Kotzebue and Utqiagvik; Grant Aviation and Aleutian Airways to Kenai; Aleutian Airways to Homer, King Salmon, Dutch Harbor, Sand Point and Unalakleet. Ravn Alaska is not listed because it stopped flying on August 5, 2025. Alberta: Air Canada and WestJet between Calgary and Edmonton, Fort McMurray and Grande Prairie, and WestJet between Edmonton and Fort McMurray and Grande Prairie; Air North between Calgary and Edmonton. Sources are news pages and route lists (see `backend/flight_data.py`); routes change often, so each row is a snapshot checked 2026-11-17. WestJet's Calgary to Lethbridge and Medicine Hat flights ended June 24, 2026 and are not listed. Ohio has no flight rows: the sources show Ohio airports served by flights to other states and no scheduled flights between Ohio cities, so the app shows a note. Flights use mode `Air`; the Mode filter has an "Air only" choice.
- Bus trips from "Sample Coach Lines" and "Sample Shuttle Co" are made up demos and are labeled that way on screen.

## What is in the repo

    backend/    FastAPI service and database code
      main.py        all endpoints, database setup, partner report logic
      arr_data.py    the Alaska Railroad trips and their sources
      gobus_data.py  GoBus trips for 8 lines, the mileage fare table, the fare estimate and sources; gobus_lines.json holds the posted timetables
      alberta_data.py  Alberta carrier listings (no times), the Red Arrow fare estimate and sources
      flight_data.py   Airline route listings for Alaska and Alberta (no times, no fares) and sources
      data.py        the made up demo bus trips
      schema.sql     Postgres tables (also run automatically at start up)
    frontend/   Streamlit app (search, results, review, join, privacy, terms, staff report)
    .streamlit/ config.toml forces the light theme
    test_api.py   unit tests (SQLite or Postgres, no server needed)
    test_flow.py  full flow test against a running backend
    test_browser.py  real-browser check of all three regions (needs Playwright)
    test_ui.py    privacy notice, terms page and join consent box (needs a running backend)
    test_regions.py  regions, filters, sorting, popular routes and phone friendly checks (needs a running backend)

## How it works

1. Search: first choose the region (Alaska, Alberta or Ohio), then From, To, Date and Riders. The home screen has a top menu bar and three popular route tiles for the chosen region. Results show filters (mode, price, departure time, in season), sort buttons, and badges that say whether a trip is real, demo or has an estimated fare.
2. Review: the visitor sees the trip, the source and check date, and a referral fee note. Clicking "Continue to operator site" saves a click with a tracking code (coop-ID) that is added to the operator link.
3. Pilot report (staff): clicks and bookings, plus the partner's weekly sales and tagged tickets. The capture rate is tagged ticket value divided by the partner's total sales on the same routes and weeks, shown against the pilot decision bands (9% or more go, 5.5 to 9% extend, below 5.5% stop or change). A decision is only shown as final after 12 weeks and 100 tagged tickets. Tagged sales are a floor.
4. Join: saves an email and a tier (1 free, 2 paid interest only), after the visitor ticks a box to confirm they read the privacy notice and terms. A repeat email updates the tier.
5. Privacy notice and terms: plain language pages linked in the top bar, the footer and the join screen. They say what is saved (an email if someone joins, and a record of each operator click with no name or email in it), that the site sells no tickets, that estimated fares are estimates, and that no operator is a partner.

## Run locally (two terminals)

    cd backend && pip install -r requirements.txt && uvicorn main:app --reload
    cd frontend && pip install -r requirements.txt && streamlit run app.py

Without DATABASE_URL the backend uses a local SQLite file (trips.db). Backend docs open at http://localhost:8000/docs. The frontend uses http://localhost:8000 unless BACKEND_URL is set.

## Settings (never put these in GitHub)

| Name | Where | Meaning |
|---|---|---|
| DATABASE_URL | Render, Environment | Neon connection string. If set, data is saved in Postgres and survives restarts. |
| ADMIN_KEY | Render, Environment, AND Streamlit secrets | Long random text. Protects the staff partner numbers. If unset, anyone can use them (local testing only). |
| BACKEND_URL | Streamlit secrets | The Render service address, for example "https://rural-travel-coop.onrender.com". |

## Deploy (free)

Backend on Render: New, Web Service, connect this repository. Root directory: backend. Build command: pip install -r requirements.txt. Start command: uvicorn main:app --host 0.0.0.0 --port $PORT. Add DATABASE_URL and ADMIN_KEY under Environment. The first request after 15 minutes idle can take about a minute.

Frontend on Streamlit Community Cloud: New app, main file path frontend/app.py. Add BACKEND_URL and ADMIN_KEY under Advanced settings, Secrets.

Database on Neon: create a project, then run backend/schema.sql in the SQL Editor (the backend also runs it at start up, so this is optional). The file also widens the operator mode check to allow Air, so an older database picks up airline rows on the next start. See DATABASE_PLAN.md for why Neon was chosen.

## Tests

    python test_api.py                       # unit tests; add DATABASE_URL to test Postgres
    BACKEND_URL=... ADMIN_KEY=... python test_regions.py   # both regions, filters, sorting, popular tiles
    BACKEND_URL=... ADMIN_KEY=... python test_ui.py        # privacy notice, terms page, join consent
    FRONTEND_URL=... python test_browser.py                # real browser, both regions, no login, link has tracking code
    BACKEND_URL=... ADMIN_KEY=... python test_flow.py                  # full flow on a running backend
    BACKEND_URL=... ADMIN_KEY=... python test_flow.py --after-restart  # data survived a restart

Both test files write test rows. Run them against a test database, not the pilot one.

Last full run (October 30, 2026): unit tests passed on SQLite and on Postgres 16; full flow and restart checks passed on Postgres 16; the region, filter, sorting, popular route and privacy and terms screen checks passed against the Postgres backend and the SQLite backend.

## Updating data

To change a fare or time, edit the row in backend/arr_data.py (Alaska), the tables in backend/gobus_data.py (Ohio) the pair lists in backend/alberta_data.py (Alberta) or backend/flight_data.py (airlines), change CHECKED to the new date, push to GitHub, and let Render redeploy. Rows are updated in place so trip ids and click history are kept. A row you delete from the file is hidden (is_active = false), not erased.

## Known limits

- Alaska Railroad fares are Adventure class, adult, one way. GoldStar and other classes are not listed.
- Only segments with a published fare and published times are included. Fares and times can change.
- It is unknown whether the railroad's checkout can accept or report a tracking code. This must be settled with the partner before a pilot.
- Whether a referral only site must register as a seller of travel in some states (California, Florida, Hawaii, Iowa, Washington) is unresolved.
- GoBus fares are estimates. The fare steps come from GoBus's own mileage table (its 2024 and 2025 requests for proposals), but the miles are our own: straight line miles between town centers times a road factor of 1.12. The factor is an assumption (1.09 to 1.16 reproduces six one way fares found in news and an unofficial fare listing, and the $25 top fare on the Red Line). Fares above $25 come from changing lines, which the app does not model. Replace the miles with GoBus's own when they are found.
- Alberta rows have no times and, except Red Arrow, no fare. In the database an empty time and price 0 mean "not shown"; the API returns null for both and puts those rows last when sorting by price. The pair lists for Cold Shot, Rider Express and Flix come from third-party and news pages and may include or miss pairs; the carriers' own sites are the check. Red Arrow days come from its route pages (the Red Deer to Fort McMurray page says Mon, Tue, Wed, Thu, Sun; the reverse page prints no days).
- Alberta fare estimate: $0.23 per road km (straight line km between town centers times 1.12), fitted to three Red Arrow route averages (Edmonton to Fort McMurray $92.24, Fort McMurray to Red Deer $136.76, Edmonton to Calgary $74.57 from a search snippet; the rule gives $97, $134 and $72). It is a fit to three points, so it is used only from 150 road km up. Town coordinates are approximate and typed by hand. The click report adds up dollars from every region without converting Canadian dollars; ignore it for Alberta until the pilot uses one region at a time.
- Alberta rules on selling travel were read in public documents only (provincial licence list, an industry body, consumer pages); no Alberta travel seller licence was found, but the regulation text was not read. This is a desk reading, not legal advice.
- GoBus lines loaded: all 9 (Orange, Blue and Gray use the Sept 14, 2026 timetables). GoBus now lists base fares up to $30 with no published distance rule, so a few very long trips shown at $25 may really cost $30 (rechecked 2026-11-24, still no rule). Orange schedules 58 and 59 print the Athens stops out of order in GoBus's own file. Tax and a service charge ($2.00 on GoBus's ticket page, $2.50 in a March 2026 news story) are added at booking. Stops marked reservation only (the rider must phone GoBus first) and transfer only are left out. Where a city has two stops on one bus, the first one listed is used. One printed time that did not fit (Marietta on Green Line trip 51) was dropped.
- The Green Line file says it was updated May 16, 2025, so its times may be out of date. Lines other than the Red Line print no season, so they show as not checked against the travel date.
- Tracking code check (2026-11-24, opened from a US location). Every operator link is the operator's home or booking page plus `?ref=coop-ID`. Of 12 distinct links, 9 load and keep the code in the address (GoBus booking site, Cold Shot, Rider Express, Alaska Airlines, Aleutian Airways, Grant Aviation, Air North, WestJet and the Alaska Railroad). Red Arrow's old `/order/reservation` address redirected to its home page and dropped the code, so the link now goes to the Betterez booking page that Red Arrow's own Book Now button uses, which keeps the code in the address. flixbus.ca redirected to flixbus.com and dropped the code (this may depend on location), and aircanada.com dropped it after loading. Keeping the code in the address does not show that an operator records it: the GoBus booking page, for one, set no cookie or stored value with it. No operator page found says it honors a `ref` code; FlixBus and the Alaska Railroad publish partner or agent programs that need a sign-up, so paid attribution needs an agreement with each operator. A real booking would be needed to test the rest.
- The privacy notice says there is no delete button for emails yet, so removal is by hand.
- The free hosting sleeps after 15 minutes idle (Render and Streamlit), so the first load can take a few minutes. The app shows a "waking up" message while it waits for the server.
- Remove my email: the join screen has a "Remove my email" box (POST /members/remove). It gives the same answer whether or not the email was on the list. It does not confirm by email first, so anyone who knows an address could remove it. Add a confirmation link before real emails are sent.
