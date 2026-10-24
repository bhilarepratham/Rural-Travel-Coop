"""Frontend for the Rural Travel Co-op prototype (Streamlit), laid out like a booking site:
a search bar on top of every screen, filters on the left, result cards with the price on the right.
It gets trips from the backend API. Set BACKEND_URL in the environment or in
Streamlit secrets. Locally it defaults to http://localhost:8000.

Run locally:  streamlit run app.py      (from the frontend folder)
"""
import os
from datetime import date
from html import escape
from urllib.parse import urlencode

import requests
import streamlit as st

st.set_page_config(page_title="Rural Travel Co-op (prototype)", page_icon="🚆", layout="wide")

try:
    BACKEND_URL = st.secrets["BACKEND_URL"]
except Exception:
    BACKEND_URL = os.environ.get("BACKEND_URL", "http://localhost:8000")
BACKEND_URL = BACKEND_URL.rstrip("/")

DEFAULT_DATE = date(2027, 7, 15)   # most listed Alaska Railroad trains run in summer 2027

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Public+Sans:wght@400;500;600;700;800&display=swap');
:root { --ink:#0f2a4a; --blue:#1b5fa8; --amber:#f2a900; --paper:#f1f5fa; --line:#d6dee9;
        --green:#0a7c4a; --muted:#5b6b80; }
html, body, [class*="css"], .stApp { font-family:'Public Sans', system-ui, sans-serif; }
.stApp { background:var(--paper); color:var(--ink); color-scheme:light; }
.stApp label, .stApp label p, .stApp [data-testid="stWidgetLabel"] p, .stApp .stMarkdown p,
.stApp [data-testid="stCheckbox"] p, .stApp [data-testid="stRadio"] p { color:var(--ink); }
.stApp [data-baseweb="select"] > div, .stApp [data-baseweb="input"], .stApp [data-baseweb="base-input"],
.stApp input { background-color:#eef2f7 !important; color:var(--ink) !important; }
.stApp [data-baseweb="select"] svg { fill:var(--ink); }
#MainMenu, footer, header[data-testid="stHeader"] { visibility:hidden; height:0; }
.block-container { padding-top:0 !important; max-width:1180px; }

/* top band */
.topband { background:var(--ink); width:100vw; margin-left:calc(50% - 50vw); padding:1.1rem calc(50vw - 590px + 5rem) 4.6rem; color:#fff; box-sizing:border-box; }
.topband .brand { font-size:1.35rem; font-weight:800; letter-spacing:-.01em; }
.topband .tag { color:#b9c9de; font-size:.95rem; margin-top:.15rem; }
.topband h1 { font-size:2.05rem; font-weight:800; margin:1.3rem 0 0; letter-spacing:-.02em; color:#fff; }
.notice { background:#fff7e0; border-left:4px solid var(--amber); color:#5a4300; padding:.55rem .8rem;
          font-size:.85rem; border-radius:4px; margin:.8rem 0 0; }

/* search bar sits over the band, framed in amber */
.st-key-searchbar { background:#fff; border:4px solid var(--amber); border-radius:10px;
                    padding:.9rem 1rem .4rem; margin-top:-3.6rem; position:relative; z-index:3; box-shadow:0 6px 18px rgba(15,42,74,.18); }
.st-key-searchbar label p { font-weight:600; font-size:.8rem; color:var(--muted); }
.st-key-searchbar [data-testid="stFormSubmitButton"] button {
    background:var(--blue); border:none; font-weight:700; min-height:2.9rem; margin-top:1.55rem; color:#fff; }

/* filter panel */
.st-key-filters { background:#fff; border:1px solid var(--line); border-radius:8px; padding:1rem 1rem .5rem; }
.st-key-filters h4 { font-size:1rem; margin:0 0 .4rem; color:var(--ink); }

/* result cards */
[class*="st-key-card-"] { background:#fff; border:1px solid var(--line); border-radius:8px; padding:1rem 1.1rem;
                          margin-bottom:.8rem; }
[class*="st-key-card-"]:hover { border-color:var(--blue); }
.op { font-weight:700; color:var(--ink); font-size:1.05rem; }
.pill { display:inline-block; font-size:.72rem; font-weight:600; padding:.1rem .5rem; border-radius:99px;
        margin-left:.4rem; background:#e5eefb; color:var(--blue); vertical-align:middle; }
.trip { display:flex; align-items:center; gap:.8rem; margin:.7rem 0 .2rem; }
.trip .t { font-size:1.45rem; font-weight:700; color:var(--ink); line-height:1; }
.trip .place { font-size:.78rem; color:var(--muted); margin-top:.2rem; }
.trip .bar { flex:1; text-align:center; font-size:.78rem; color:var(--muted); min-width:90px; }
.trip .bar:before { content:""; display:block; border-top:2px solid var(--line); margin-bottom:.25rem; }
.badges { margin-top:.55rem; }
.badge { display:inline-block; font-size:.74rem; font-weight:600; padding:.15rem .5rem; border-radius:4px;
         margin:0 .35rem .3rem 0; background:#eef2f7; color:#33475f; }
.badge.good { background:#dff3e8; color:var(--green); }
.badge.fast { background:#e5eefb; color:var(--blue); }
.badge.warn { background:#fff1cc; color:#7a5600; }
.badge.bad { background:#fde8e8; color:#9b1c1c; }
.small { font-size:.8rem; color:var(--muted); margin-top:.3rem; }
.price { text-align:right; }
.price .big { font-size:1.9rem; font-weight:800; color:var(--ink); line-height:1.1; }
.price .per { font-size:.78rem; color:var(--muted); }

/* summary and tier cards */
.st-key-summary, .st-key-tier1, .st-key-tier2, .st-key-pricebox { background:#fff; border:1px solid var(--line);
    border-radius:8px; padding:1rem 1.2rem; }
.st-key-tier2 { border-color:var(--blue); border-width:2px; }
.stButton button, .stLinkButton a { border-radius:6px; font-weight:600; }
.stButton button[kind="primary"], .stLinkButton a[kind="primary"] { background:var(--blue); border:none; }
@media (max-width:1200px){ .topband { padding-left:4rem; padding-right:4rem; } }
@media (max-width:760px){ .topband { padding:1rem 1rem 4.6rem !important; } .topband h1 { font-size:1.5rem; }
    .trip .t { font-size:1.15rem; } .price { text-align:left; margin-top:.6rem; } }
@media (prefers-reduced-motion:no-preference){ [class*="st-key-card-"] { transition:border-color .15s; } }
</style>
"""

if "step" not in st.session_state:
    st.session_state.step = "search"
    st.session_state.query = {"from": "Anchorage", "to": "Seward", "date": DEFAULT_DATE, "riders": 1}
    st.session_state.selected = None
    st.session_state.click_id = None


def go(step: str) -> None:
    st.session_state.step = step


try:
    ADMIN_KEY = st.secrets["ADMIN_KEY"]
except Exception:
    ADMIN_KEY = os.environ.get("ADMIN_KEY", "")
STAFF = {"X-Admin-Key": ADMIN_KEY} if ADMIN_KEY else {}


def api_get(path: str, params: dict | None = None, staff: bool = False):
    """Call the backend. Returns the JSON, or None if the backend cannot be reached."""
    try:
        r = requests.get(f"{BACKEND_URL}{path}", params=params, timeout=30, headers=STAFF if staff else None)
        if r.status_code == 401:
            st.warning("Staff key missing or wrong. Add ADMIN_KEY to the Streamlit secrets.")
            return None
        r.raise_for_status()
        return r.json()
    except requests.RequestException as e:
        st.error(f"Could not reach the backend at {BACKEND_URL}. The free server may be waking up. "
                 f"Wait 30 seconds and reload. ({e})")
        return None


def api_post(path: str, body: dict | None = None, staff: bool = False):
    """Send data to the backend. Returns the JSON, or None if the call failed."""
    try:
        r = requests.post(f"{BACKEND_URL}{path}", json=body, timeout=30, headers=STAFF if staff else None)
        if r.status_code == 401:
            st.warning("Staff key missing or wrong. Add ADMIN_KEY to the Streamlit secrets.")
            return None
        if r.status_code == 422:
            # The backend rejected the input (for example a bad email). Show its plain message.
            detail = r.json().get("detail", "Please check what you entered.")
            st.warning(detail if isinstance(detail, str) else "Please check what you entered.")
            return None
        r.raise_for_status()
        return r.json()
    except requests.RequestException as e:
        st.error(f"Could not save to the backend at {BACKEND_URL}. ({e})")
        return None


def minutes(hhmm: str) -> int:
    h, m = hhmm.split(":")
    return int(h) * 60 + int(m)


def duration_text(t: dict) -> str:
    mins = minutes(t["arrive"]) - minutes(t["depart"])
    return f"{mins // 60}h {mins % 60:02d}m"


def clock(hhmm: str) -> str:
    """24 hour text to 12 hour text, for example 18:00 to 6:00 PM."""
    h, m = minutes(hhmm) // 60, minutes(hhmm) % 60
    return f"{(h % 12) or 12}:{m:02d} {'AM' if h < 12 else 'PM'}"


def header(title: str) -> None:
    st.markdown(CSS, unsafe_allow_html=True)
    # Ask browsers and dark mode extensions not to restyle this page (it is designed in light colors)
    st.html("<img src='data:,' style='display:none' onerror=\"var d=document,h=d.head;"
            "['color-scheme:light','darkreader-lock:'].forEach(function(x){var m=d.createElement('meta');"
            "m.name=x.split(':')[0];m.content=x.split(':')[1]||'';h.appendChild(m);});\">")
    st.markdown(
        f"""<div class="topband"><div class="brand">🚆 Rural Travel Co-op</div>
        <div class="tag">Compare rail and bus in one search</div><h1>{escape(title)}</h1>
        <div class="notice">Unofficial research prototype. Alaska Railroad times and fares are copied from its
        public schedule and it is not a partner. Trips marked demo are made up. Always confirm with the
        operator before you buy.</div></div>""", unsafe_allow_html=True)


def search_bar(cities: list[str]) -> None:
    """Search bar shown on the search and results screens."""
    q = st.session_state.query
    with st.container(key="searchbar"):
        with st.form("search_form", border=False):
            c1, c2, c3, c4, c5 = st.columns([2, 2, 1.7, 1, 1.4])
            origin = c1.selectbox("From", cities, index=cities.index(q["from"]) if q["from"] in cities else 0)
            dest = c2.selectbox("To", cities, index=cities.index(q["to"]) if q["to"] in cities else 1)
            when = c3.date_input("Date", value=q["date"])
            riders = c4.number_input("Riders", min_value=1, max_value=10, value=q["riders"])
            submitted = c5.form_submit_button("Search", type="primary", width="stretch")
    if submitted:
        if origin == dest:
            st.warning("Choose two different places.")
            return
        st.session_state.query = {"from": origin, "to": dest, "date": when, "riders": riders}
        go("results")
        st.rerun()


def click_tab() -> None:
    sales = st.number_input("Partner ticket sales for the same routes and weeks ($, optional)",
                            min_value=0.0, value=0.0, step=100.0)
    report = api_get("/clicks/report", {"partner_sales": sales} if sales > 0 else None)
    if not report:
        return
    m1, m2, m3 = st.columns(3)
    m1.metric("Clicks", report["total_clicks"])
    m2.metric("Bookings", report["total_bookings"])
    m3.metric("Capture rate", f"{report['capture_rate']:.1%}" if "capture_rate" in report else "n/a")
    if report["operators"]:
        st.dataframe(report["operators"], width="stretch")
    else:
        st.caption("No clicks yet. Select a trip first.")


def partner_tab() -> None:
    """Weekly numbers the partner sends us, and the capture rate they produce."""
    operators = ["Alaska Railroad"]
    with st.form("partner_form", border=True):
        st.markdown("**Enter this week's partner numbers**")
        c1, c2 = st.columns(2)
        operator = c1.selectbox("Operator", operators)
        week = c2.date_input("Week starting (Monday)", value=date(2027, 6, 7))
        route = st.text_input("Routes covered", value="Anchorage to Seward")
        c3, c4, c5 = st.columns(3)
        total = c3.number_input("Partner total ticket sales ($)", min_value=0.0, step=100.0)
        tickets = c4.number_input("Tickets with our tracking code", min_value=0, step=1)
        value = c5.number_input("Value of those tickets ($)", min_value=0.0, step=50.0)
        notes = st.text_input("Notes (optional)")
        if st.form_submit_button("Save week", type="primary"):
            saved = api_post("/partner-reports", {
                "operator": operator, "week_start": week.isoformat(), "route_label": route,
                "partner_sales_total": total, "tagged_tickets": int(tickets),
                "tagged_value": value, "notes": notes}, staff=True)
            if saved:
                st.success(f"Week {saved['status']}.")
    data = api_get("/partner-reports", staff=True)
    if not data or not data["rows"]:
        st.caption("No partner numbers yet. Enter the first week above.")
        return
    sm = data["summary"]
    m1, m2, m3 = st.columns(3)
    m1.metric("Weeks reported", f"{sm['weeks_reported']} of 12")
    m2.metric("Tagged tickets", sm["tagged_tickets"])
    m3.metric("Capture rate so far", f"{sm['capture_rate']:.1%}" if sm["capture_rate"] is not None else "n/a")
    st.info(f"{sm['decision']}. {sm['note']}")
    st.dataframe(data["rows"], width="stretch", hide_index=True)
    weekly = {}
    for r in data["rows"]:
        w = weekly.setdefault(r["week_start"], [0.0, 0.0])
        w[0] += r["partner_sales_total"]
        w[1] += r["tagged_value"]
    st.caption("Capture rate by week (decision lines: 5.5% and 9%)")
    st.bar_chart({k: v[1] / v[0] for k, v in sorted(weekly.items()) if v[0] > 0}, height=200)


def report_panel() -> None:
    """Staff view for the pilot: clicks, bookings, partner weekly numbers and the capture rate."""
    with st.expander("Pilot report (staff view)"):
        tab1, tab2 = st.tabs(["Clicks and bookings", "Partner weekly numbers"])
        with tab1:
            click_tab()
        with tab2:
            partner_tab()


def search_screen() -> None:
    header("Find your way between small towns")
    cities = api_get("/cities")
    if not cities:
        return
    search_bar(cities)
    st.write("")
    c1, c2, c3 = st.columns(3)
    for col, title, text in [
            (c1, "Rail and bus together", "See trains and buses for the same trip, sorted by price or time."),
            (c2, "You book with the operator", "We send you to the operator's own site. Refunds follow their rules."),
            (c3, "Free to use", "No account needed. Join the co-op to vote and share in patronage dividends.")]:
        with col.container(border=True):
            st.markdown(f"**{title}**")
            st.caption(text)
    st.button("Join the co-op", on_click=go, args=("join",))
    report_panel()


def badge(text: str, kind: str = "") -> str:
    return f'<span class="badge {kind}">{escape(text)}</span>'


def part_of_day(hhmm: str) -> str:
    h = minutes(hhmm) // 60
    return "Morning (before noon)" if h < 12 else "Afternoon (noon to 5 PM)" if h < 17 else "Evening (after 5 PM)"


def results_screen() -> None:
    q = st.session_state.query
    header(f"{q['from']} to {q['to']}")
    cities = api_get("/cities")
    if not cities:
        return
    search_bar(cities)
    st.write("")

    trips = api_get("/trips", {"origin": q["from"], "destination": q["to"], "on": q["date"].isoformat()})
    if trips is None:
        return

    left, right = st.columns([1, 3], gap="large")
    with left.container(key="filters"):
        st.markdown("#### Filter by")
        mode = st.radio("Mode", ["Rail and bus", "Rail only", "Bus only"])
        top = max([t["price"] for t in trips], default=100)
        max_price = st.slider("Highest price per rider ($)", 0, int(top) + 1, int(top) + 1) if trips else 0
        times = st.multiselect("Departure time", ["Morning (before noon)", "Afternoon (noon to 5 PM)",
                                                  "Evening (after 5 PM)"])
        only_date = st.checkbox("Only trips that run on my date", value=False)
        only_partner = st.checkbox("Co-op partners only", value=False)

    shown = [t for t in trips
             if (mode == "Rail and bus" or t["mode"] == ("Rail" if mode == "Rail only" else "Bus"))
             and t["price"] <= max_price
             and (not times or part_of_day(t["depart"]) in times)
             and (not only_date or t.get("in_season") is not False)
             and (not only_partner or t["partner"])]

    with right:
        top1, top2 = st.columns([2, 3])
        top1.markdown(f"**{len(shown)} option{'s' if len(shown) != 1 else ''}** on {q['date']:%b %d, %Y}")
        sort_by = top2.radio("Sort by", ["Cheapest", "Earliest departure", "Shortest trip"],
                             horizontal=True, label_visibility="collapsed")
        keys = {"Cheapest": lambda t: t["price"], "Earliest departure": lambda t: t["depart"],
                "Shortest trip": lambda t: minutes(t["arrive"]) - minutes(t["depart"])}
        shown.sort(key=keys[sort_by])

        if not shown:
            st.info("No trips match these filters. Clear a filter, pick another date, or try Anchorage to "
                    "Seward or Anchorage to Fairbanks.")
            return
        cheapest = min(shown, key=lambda t: t["price"])
        fastest = min(shown, key=lambda t: minutes(t["arrive"]) - minutes(t["depart"]))
        for t in shown:
            card(t, q["riders"], t is cheapest and len(shown) > 1, t is fastest and len(shown) > 1)


def card(t: dict, riders: int, is_cheapest: bool, is_fastest: bool) -> None:
    badges = []
    if is_cheapest:
        badges.append(badge("Cheapest", "good"))
    if is_fastest:
        badges.append(badge("Fastest", "fast"))
    badges.append(badge("Demo data, made up", "warn") if t["sample"] else badge("Published schedule, unofficial"))
    badges.append(badge("Co-op partner", "good") if t["partner"] else badge("Listed only"))
    if t.get("in_season") is True:
        badges.append(badge("Runs on your date", "good"))
    elif t.get("in_season") is False:
        badges.append(badge("Not running on your date", "bad"))
    season = f"{t['days']}. Season {t['season_start']} to {t['season_end']}." if t.get("days") else ""
    with st.container(key=f"card-{t['id']}"):
        a, b = st.columns([3.2, 1.2])
        a.markdown(
            f"""<div class="op">{escape(t['operator'])}<span class="pill">{escape(t['mode'])}</span></div>
            <div class="trip"><div><div class="t">{clock(t['depart'])}</div>
            <div class="place">{escape(t['from'])}</div></div>
            <div class="bar">{duration_text(t)}</div>
            <div><div class="t">{clock(t['arrive'])}</div><div class="place">{escape(t['to'])}</div></div></div>
            <div class="badges">{''.join(badges)}</div><div class="small">{escape(season)}</div>""",
            unsafe_allow_html=True)
        b.markdown(f"""<div class="price"><div class="big">${t['price'] * riders:,.0f}</div>
            <div class="per">{f"${t['price']:,.0f} per rider, {riders} riders" if riders != 1 else "per rider"}</div></div>""",
                   unsafe_allow_html=True)
        if b.button("Select", key=f"book{t['id']}", type="primary", width="stretch"):
            st.session_state.selected = t
            st.session_state.click_id = None
            go("handoff")
            st.rerun()


def handoff_screen() -> None:
    t = st.session_state.selected
    q = st.session_state.query
    header("Review your trip")
    left, right = st.columns([2, 1], gap="large")
    with left.container(key="summary"):
        st.markdown(f"### {t['operator']} ({t['mode']})")
        st.markdown(f"**{t['from']}** at {clock(t['depart'])}  \n**{t['to']}** at {clock(t['arrive'])}  \n"
                    f"{duration_text(t)} | {q['date']:%A, %b %d, %Y}")
        if t.get("days"):
            st.caption(f"{t['days']}. Season {t['season_start']} to {t['season_end']}.")
        if t.get("in_season") is False:
            st.warning("This trip does not run on the date you searched. Check the season before you buy.")
        st.info("The operator sells and issues your ticket. Refunds and changes follow the operator's rules.")
        if t.get("source_url"):
            st.caption(f"Time and fare copied from the operator's public schedule (checked {t.get('last_updated')}). "
                       f"Confirm on the operator's site before you buy. Source: {t['source_url']}")
    with right.container(key="pricebox"):
        st.markdown("**Price**")
        st.markdown(f"## ${t['price'] * q['riders']:,.0f}")
        st.caption(f"${t['price']:,.0f} x {q['riders']} rider(s). Fare shown by the operator; taxes and fees "
                   "may apply on their site.")
        if t["partner"]:
            st.caption("Disclosure: the co-op may receive a referral fee from this operator if you buy. "
                       "It does not change your price.")
        else:
            st.caption("The co-op earns no fee from this trip.")
        ref = f"coop-{t['id']}"
        link = f"{t['url']}?{urlencode({'ref': ref})}"
        if st.session_state.get("click_id") is None:
            if st.button("Continue to operator site", type="primary", width="stretch"):
                saved = api_post("/clicks", {"ref": ref, "trip_id": t["id"], "operator": t["operator"],
                                             "riders": q.get("riders", 1)})
                if saved:
                    st.session_state.click_id = saved["id"]
                    st.rerun()
        else:
            st.success(f"Referral saved (click {st.session_state.click_id}).")
            st.link_button("Open operator site", link, type="primary", width="stretch")
            if st.button("Demo: the partner confirms this ticket was sold", width="stretch"):
                if api_post(f"/clicks/{st.session_state.click_id}/confirm"):
                    st.success("Marked as a booking. See the pilot report on the home screen.")
        st.caption(f"Link includes our tracking code: {ref}")
    c1, c2, _ = st.columns([1, 1, 2])
    c1.button("Back to results", on_click=go, args=("results",), width="stretch")
    c2.button("Join the co-op", on_click=go, args=("join",), width="stretch")


def join_screen() -> None:
    header("Join the co-op")
    c1, c2 = st.columns(2, gap="large")
    with c1.container(key="tier1"):
        st.markdown("### Tier 1: Free")
        st.write("Search, compare and book with any listed operator. No account needed.")
    with c2.container(key="tier2"):
        st.markdown("### Tier 2: Paid member")
        st.write("Vote on co-op decisions and share in patronage dividends.")
    st.write("")
    tier = st.radio("Choose a membership", ["Tier 1 (free)", "Tier 2 (paid)"], horizontal=True)
    email = st.text_input("Email")
    st.caption("Prototype: no payment is taken. Tier 2 is recorded as interest only.")
    if st.button("Join", type="primary"):
        saved = api_post("/members", {"email": email, "tier": 1 if tier.startswith("Tier 1") else 2})
        if saved:
            st.success(f"Thanks. {saved['email']} is now on the list for Tier {saved['tier']} ({saved['status']}).")
    counts = api_get("/members/count")
    if counts:
        st.caption(f"Sign ups so far: {counts['total']} (Tier 1: {counts['tier1']}, Tier 2: {counts['tier2']})")
    st.button("Start a new search", on_click=go, args=("search",))


{"search": search_screen, "results": results_screen, "handoff": handoff_screen, "join": join_screen}[
    st.session_state.step
]()
