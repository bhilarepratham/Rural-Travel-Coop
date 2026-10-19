"""Frontend for the Rural Travel Co-op prototype (Streamlit).
It gets trips from the backend API. Set BACKEND_URL in the environment or in
Streamlit secrets. Locally it defaults to http://localhost:8000.

Run locally:  streamlit run app.py      (from the frontend folder)
"""
import os
from datetime import date
from urllib.parse import urlencode

import requests
import streamlit as st

st.set_page_config(page_title="Rural Travel Co-op (prototype)", page_icon="🚌", layout="centered")

try:
    BACKEND_URL = st.secrets["BACKEND_URL"]
except Exception:
    BACKEND_URL = os.environ.get("BACKEND_URL", "http://localhost:8000")
BACKEND_URL = BACKEND_URL.rstrip("/")

STEPS = ["search", "results", "handoff", "join"]

if "step" not in st.session_state:
    st.session_state.step = "search"
    st.session_state.query = {}
    st.session_state.selected = None
    st.session_state.click_id = None


def go(step: str) -> None:
    st.session_state.step = step


def api_get(path: str, params: dict | None = None):
    """Call the backend. Returns the JSON, or None if the backend cannot be reached."""
    try:
        r = requests.get(f"{BACKEND_URL}{path}", params=params, timeout=30)
        r.raise_for_status()
        return r.json()
    except requests.RequestException as e:
        st.error(f"Could not reach the backend at {BACKEND_URL}. ({e})")
        return None


def api_post(path: str, body: dict | None = None):
    """Send data to the backend. Returns the JSON, or None if the call failed."""
    try:
        r = requests.post(f"{BACKEND_URL}{path}", json=body, timeout=30)
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


def report_panel() -> None:
    """Staff view for the pilot: clicks, bookings and the capture rate."""
    with st.expander("Pilot click report (staff view)"):
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
            st.caption("No clicks yet. Book a sample trip first.")


def search_screen() -> None:
    st.subheader("1. Search")
    st.caption("Bus and rail in one search. Free, no account needed.")
    cities = api_get("/cities")
    if not cities:
        return
    origin = st.selectbox("From", cities, index=0)
    dest = st.selectbox("To", cities, index=1)
    when = st.date_input("Date", value=date.today())
    riders = st.number_input("Riders", min_value=1, max_value=10, value=1)
    report_panel()
    if st.button("Search bus and train", type="primary", width="stretch"):
        if origin == dest:
            st.warning("Choose two different places.")
            return
        st.session_state.query = {"from": origin, "to": dest, "date": when, "riders": riders}
        go("results")
        st.rerun()


def minutes(hhmm: str) -> int:
    h, m = hhmm.split(":")
    return int(h) * 60 + int(m)


def duration_text(t: dict) -> str:
    mins = minutes(t["arrive"]) - minutes(t["depart"])
    return f"{mins // 60}h {mins % 60:02d}m"


def results_screen() -> None:
    q = st.session_state.query
    st.subheader(f"2. Results: {q['from']} to {q['to']}")
    st.caption(f"{q['date']:%b %d, %Y} | {q['riders']} rider(s) | Sample data only")
    col_a, col_b = st.columns(2)
    mode = col_a.selectbox("Mode", ["Rail and bus", "Rail only", "Bus only"])
    sort_by = col_b.selectbox("Sort by", ["Cheapest", "Earliest departure", "Shortest trip"])

    params = {"origin": q["from"], "destination": q["to"]}
    if mode == "Rail only":
        params["mode"] = "Rail"
    elif mode == "Bus only":
        params["mode"] = "Bus"
    trips = api_get("/trips", params)   # the backend does the searching
    if trips is None:
        return

    keys = {"Cheapest": lambda t: t["price"],
            "Earliest departure": lambda t: t["depart"],
            "Shortest trip": lambda t: minutes(t["arrive"]) - minutes(t["depart"])}
    trips.sort(key=keys[sort_by])

    if not trips:
        st.info("No sample trips match. Try Anchorage to Seward, or choose Rail and bus.")
    else:
        cheapest = min(trips, key=lambda t: t["price"])
        fastest = min(trips, key=lambda t: minutes(t["arrive"]) - minutes(t["depart"]))
        m1, m2, m3 = st.columns(3)
        m1.metric("Options", len(trips))
        m2.metric("Cheapest", f"${cheapest['price'] * q['riders']:.0f}")
        m3.metric("Shortest", duration_text(fastest))

    for t in trips:
        with st.container(border=True):
            c1, c2 = st.columns([3, 1])
            c1.markdown(f"**{t['operator']}** ({t['mode']})")
            c1.write(f"{t['depart']} to {t['arrive']} | {duration_text(t)}")
            tags = ["Co-op partner" if t["partner"] else "Listed only"]
            if t is cheapest:
                tags.append("Cheapest")
            if t is fastest:
                tags.append("Shortest")
            c1.caption(" | ".join(tags))
            c2.markdown(f"### ${t['price'] * q['riders']:.0f}")
            c2.caption(f"${t['price']:.0f} per rider")
            if c2.button("Book", key=f"book{t['id']}"):
                st.session_state.selected = t
                st.session_state.click_id = None
                go("handoff")
                st.rerun()
    st.button("Back to search", on_click=go, args=("search",))


def handoff_screen() -> None:
    t = st.session_state.selected
    st.subheader("3. You are leaving to book")
    st.markdown(f"**{t['operator']}**  \n{t['from']} to {t['to']}  \n{t['depart']}, ${t['price']:.0f}")
    st.info("The operator sells and issues your ticket. Refunds and changes follow the operator's rules.")
    ref = f"coop-{t['id']}"
    link = f"{t['url']}?{urlencode({'ref': ref})}"
    if st.session_state.get("click_id") is None:
        if st.button("Continue to operator site", type="primary", width="stretch"):
            saved = api_post("/clicks", {"ref": ref, "trip_id": t["id"], "operator": t["operator"],
                                         "riders": st.session_state.query.get("riders", 1)})
            if saved:
                st.session_state.click_id = saved["id"]
                st.rerun()
    else:
        st.success(f"Referral saved (click {st.session_state.click_id}).")
        st.link_button("Open operator site", link, type="primary", width="stretch")
        if st.button("Demo: the partner confirms this ticket was sold"):
            if api_post(f"/clicks/{st.session_state.click_id}/confirm"):
                st.success("Marked as a booking. See the pilot report on the search screen.")
    st.caption(f"Link includes our tracking code: {ref}")
    c1, c2 = st.columns(2)
    c1.button("Back to results", on_click=go, args=("results",), width="stretch")
    c2.button("Join the co-op", on_click=go, args=("join",), width="stretch")


def join_screen() -> None:
    st.subheader("4. Join the co-op")
    with st.container(border=True):
        st.markdown("**Tier 1: Free**")
        st.write("Search, compare and book with any listed operator.")
    with st.container(border=True):
        st.markdown("**Tier 2: Paid member**")
        st.write("Vote on co-op decisions and share in patronage dividends.")
    tier = st.radio("Choose a membership", ["Tier 1 (free)", "Tier 2 (paid)"])
    email = st.text_input("Email")
    st.caption("Prototype: no payment is taken. Tier 2 is recorded as interest only.")
    if st.button("Continue", type="primary"):
        saved = api_post("/members", {"email": email, "tier": 1 if tier.startswith("Tier 1") else 2})
        if saved:
            st.success(f"Thanks. {saved['email']} is now on the list for Tier {saved['tier']} ({saved['status']}).")
    counts = api_get("/members/count")
    if counts:
        st.caption(f"Sign ups so far: {counts['total']} (Tier 1: {counts['tier1']}, Tier 2: {counts['tier2']})")
    st.button("Start a new search", on_click=go, args=("search",))


st.title("🚌 Rural Travel Co-op")
st.caption("Prototype with made up sample data. Not a real booking site.")
st.progress((STEPS.index(st.session_state.step) + 1) / len(STEPS))

{"search": search_screen, "results": results_screen, "handoff": handoff_screen, "join": join_screen}[
    st.session_state.step
]()
