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
    st.session_state.click_log = []


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
    if st.button("Search bus and train", type="primary", width="stretch"):
        if origin == dest:
            st.warning("Choose two different places.")
            return
        st.session_state.query = {"from": origin, "to": dest, "date": when, "riders": riders}
        go("results")
        st.rerun()


def results_screen() -> None:
    q = st.session_state.query
    st.subheader(f"2. Results: {q['from']} to {q['to']}")
    st.caption(f"{q['date']:%b %d, %Y} | {q['riders']} rider(s) | Sample data only")
    modes = st.multiselect("Mode", ["Rail", "Bus"], default=["Rail", "Bus"])
    sort_by = st.radio("Sort by", ["Departure", "Price"], horizontal=True)

    trips = api_get("/trips", {"origin": q["from"], "destination": q["to"]})
    if trips is None:
        return
    trips = [t for t in trips if t["mode"] in modes]
    trips.sort(key=lambda t: t["price"] if sort_by == "Price" else t["depart"])

    if not trips:
        st.info("No sample trips for this route. Try Anchorage to Seward.")
    for t in trips:
        with st.container(border=True):
            c1, c2 = st.columns([3, 1])
            c1.markdown(f"**{t['operator']}** ({t['mode']})")
            c1.write(f"{t['depart']} to {t['arrive']}")
            c1.caption("Co-op partner" if t["partner"] else "Listed only")
            c2.markdown(f"### ${t['price'] * q['riders']}")
            if c2.button("Book", key=f"book{t['id']}"):
                st.session_state.selected = t
                go("handoff")
                st.rerun()
    st.button("Back to search", on_click=go, args=("search",))


def handoff_screen() -> None:
    t = st.session_state.selected
    st.subheader("3. You are leaving to book")
    st.markdown(f"**{t['operator']}**  \n{t['from']} to {t['to']}  \n{t['depart']}, ${t['price']}")
    st.info("The operator sells and issues your ticket. Refunds and changes follow the operator's rules.")
    ref = f"coop-{t['id']}"
    link = f"{t['url']}?{urlencode({'ref': ref})}"
    st.link_button("Continue to operator site", link, type="primary", width="stretch")
    # TODO (Day 4): POST the click to the backend (/clicks) instead of keeping it in session memory.
    if st.button("Log this referral click (demo)"):
        st.session_state.click_log.append({"ref": ref, "operator": t["operator"], "price": t["price"]})
        st.success(f"Logged referral {ref} (session only for now)")
    st.caption(f"Link includes our tracking code: {ref}")
    if st.session_state.click_log:
        st.write("Referral clicks this session (demo):")
        st.dataframe(st.session_state.click_log, width="stretch")
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
    st.text_input("Email")
    # TODO (Day 5): POST the email and tier to the backend (/members) and show the result.
    if st.button("Continue", type="primary"):
        st.success(f"Prototype only: nothing was saved yet. You chose {tier}.")
    st.button("Start a new search", on_click=go, args=("search",))


st.title("🚌 Rural Travel Co-op")
st.caption("Prototype with made up sample data. Not a real booking site.")
st.progress((STEPS.index(st.session_state.step) + 1) / len(STEPS))

{"search": search_screen, "results": results_screen, "handoff": handoff_screen, "join": join_screen}[
    st.session_state.step
]()
