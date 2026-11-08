# Rural Travel Co-op prototype

An unofficial research prototype of a travel price comparison and booking cooperative for regional and rural bus and rail. It is not a real booking site: it takes no payments and sells no tickets. Visitors compare trips and are sent to the operator's own site to buy.

- Alaska Railroad trips (41) are copied by hand from the railroad's public schedule and fares pages. The railroad has not reviewed them and is not a partner.
- GoBus (Ohio) trips on 8 of its 9 lines (Red, Green, Purple, Gray, Lime, Pink, Blue, Yellow; 720 stop to stop trips, 51 places) are copied from its public timetables. GoBus publishes how fares work ($5 steps, $5 under 50 miles, at most $30 on one line, $25 on the Red Line) and not a fare for each pair of stops, so each fare is an estimate from road miles and is labeled "Fare estimated". GoBus has not reviewed them and is not a partner. The Orange Line is not loaded (only a 2023 timetable was found).
- Bus trips from "Sample Coach Lines" and "Sample Shuttle Co" are made up demos and are labeled that way on screen.

## What is in the repo

    backend/    FastAPI service and database code
      main.py        all endpoints, database setup, partner report logic
      arr_data.py    the Alaska Railroad trips and their sources
      gobus_data.py  GoBus trips for 8 lines, the $5 step fare estimate and sources; gobus_lines.json holds the posted timetables
      data.py        the made up demo bus trips
      schema.sql     Postgres tables (also run automatically at start up)
    frontend/   Streamlit app (search, results, review, join, privacy, terms, staff report)
    .streamlit/ config.toml forces the light theme
    test_api.py   unit tests (SQLite or Postgres, no server needed)
    test_flow.py  full flow test against a running backend
    test_browser.py  real-browser check of both regions (needs Playwright)
    test_ui.py    privacy notice, terms page and join consent box (needs a running backend)
    test_regions.py  regions, filters, sorting, popular routes and phone friendly checks (needs a running backend)

## How it works

1. Search: first choose the region (Alaska or Ohio), then From, To, Date and Riders. The home screen has a top menu bar and three popular route tiles for the chosen region. Results show filters (mode, price, departure time, in season), sort buttons, and badges that say whether a trip is real, demo or has an estimated fare.
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

Database on Neon: create a project, then run backend/schema.sql in the SQL Editor (the backend also runs it at start up, so this is optional). See DATABASE_PLAN.md for why Neon was chosen.

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

To change a fare or time, edit the row in backend/arr_data.py (Alaska) or the tables in backend/gobus_data.py (Ohio), change CHECKED to the new date, push to GitHub, and let Render redeploy. Rows are updated in place so trip ids and click history are kept. A row you delete from the file is hidden (is_active = false), not erased.

## Known limits

- Alaska Railroad fares are Adventure class, adult, one way. GoldStar and other classes are not listed.
- Only segments with a published fare and published times are included. Fares and times can change.
- It is unknown whether the railroad's checkout can accept or report a tracking code. This must be settled with the partner before a pilot.
- Whether a referral only site must register as a seller of travel in some states (California, Florida, Hawaii, Iowa, Washington) is unresolved.
- GoBus fares are estimates: $5 per 50 road miles step (first step $5), at most $30 on one line and $25 on the Red Line. The 50 mile step and the 1.2 road factor are assumptions. Replace them when a fare for each pair of stops is found.
- GoBus lines loaded: 8 of 9. Orange is missing. Stops marked reservation only (the rider must phone GoBus first) and transfer only are left out. Where a city has two stops on one bus, the first one listed is used. One printed time that did not fit (Marietta on Green Line trip 51) was dropped.
- The Green Line file says it was updated May 16, 2025, so its times may be out of date. Lines other than the Red Line print no season, so they show as not checked against the travel date.
- The privacy notice says there is no delete button for emails yet, so removal is by hand.
- The free hosting sleeps after 15 minutes idle (Render and Streamlit), so the first load can take a few minutes. The app shows a "waking up" message while it waits for the server.
- Remove my email: the join screen has a "Remove my email" box (POST /members/remove). It gives the same answer whether or not the email was on the list. It does not confirm by email first, so anyone who knows an address could remove it. Add a confirmation link before real emails are sent.
