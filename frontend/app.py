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

DEFAULT_DATE = date.today()   # the search opens on today; summer trains need a May to September date

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Atkinson+Hyperlegible:wght@400;700&family=Barlow+Condensed:wght@500;600;700&display=swap');
:root { --ink:#0e2b26; --spruce:#1f6b57; --fire:#b3265e; --paper:#e8f0ee; --line:#b9cdc8; --field:#f4f8f7;
        --green:#14543f; --muted:#40595a; --display:'Barlow Condensed','Arial Narrow',sans-serif; }
html, body, [class*="css"], .stApp { font-family:'Atkinson Hyperlegible', system-ui, sans-serif; }
.stApp { background:var(--paper); color:var(--ink); color-scheme:light; }
.stApp label, .stApp label p, .stApp [data-testid="stWidgetLabel"] p, .stApp .stMarkdown p,
.stApp [data-testid="stCheckbox"] p, .stApp [data-testid="stRadio"] p { color:var(--ink); }
.stApp h2, .stApp h3, .stApp h4 { font-family:var(--display); letter-spacing:.01em; color:var(--ink); }
.stApp [data-baseweb="select"] > div, .stApp [data-baseweb="input"], .stApp [data-baseweb="base-input"],
.stApp input { background-color:var(--field) !important; color:var(--ink) !important; }
.stApp [data-baseweb="select"] > div, .stApp [data-baseweb="input"] { border-color:#8fa9a3 !important; }
.stApp [data-baseweb="select"] svg { fill:var(--ink); }
.stApp [data-testid="stDateInput"] div, .stApp [data-testid="stDateInput"] input,
.stApp [data-testid="stNumberInput"] div, .stApp [data-testid="stNumberInput"] input,
.stApp [data-testid="stTextInput"] div, .stApp [data-testid="stTextInput"] input
    { background-color:var(--field) !important; color:var(--ink) !important; -webkit-text-fill-color:var(--ink) !important; }
.stApp [data-testid="stDateInput"] [data-testid="stWidgetLabel"], .stApp [data-testid="stDateInput"] [data-testid="stWidgetLabel"] div,
.stApp [data-testid="stNumberInput"] [data-testid="stWidgetLabel"], .stApp [data-testid="stNumberInput"] [data-testid="stWidgetLabel"] div,
.stApp [data-testid="stTextInput"] [data-testid="stWidgetLabel"], .stApp [data-testid="stTextInput"] [data-testid="stWidgetLabel"] div
    { background-color:transparent !important; }
.stApp [data-testid="stNumberInput"] button { background-color:#dbe7e4 !important; color:var(--ink) !important; }
.stApp [data-testid="stNumberInput"] button svg { fill:var(--ink) !important; }
.stApp input::placeholder { color:var(--muted) !important; -webkit-text-fill-color:var(--muted) !important; }
[data-baseweb="popover"] [data-baseweb="menu"], [data-baseweb="popover"] ul, [data-baseweb="calendar"],
[data-baseweb="calendar"] div { background-color:#fff !important; color:var(--ink) !important; }
[data-baseweb="popover"] li { background-color:#fff !important; color:var(--ink) !important; }
[data-baseweb="popover"] li:hover, [data-baseweb="popover"] li[aria-selected="true"] { background-color:#dbe9e5 !important; }
.stApp .stButton button:not([kind="primary"]), .stApp .stDownloadButton button, .stApp .stLinkButton a:not([kind="primary"])
    { background-color:#fff !important; color:var(--ink) !important; border:2px solid var(--spruce) !important; }
.stApp .stButton button:not([kind="primary"]) p, .stApp .stLinkButton a:not([kind="primary"]) p { color:var(--ink) !important; }
.stApp .stButton button:not([kind="primary"]):hover { background-color:#dbe9e5 !important; }
.stApp .stButton button[kind="primary"], .stApp .stLinkButton a[kind="primary"],
.stApp [data-testid="stFormSubmitButton"] button { background-color:var(--fire) !important; color:#fff !important; border:none !important; }
.stApp .stButton button[kind="primary"]:hover, .stApp [data-testid="stFormSubmitButton"] button:hover { background-color:#8f1d4b !important; }
.stApp .stButton button[kind="primary"] p, .stApp .stLinkButton a[kind="primary"] p,
.stApp [data-testid="stFormSubmitButton"] button p { color:#fff !important; }
.stApp .stButton button, .stApp .stLinkButton a, .stApp [data-testid="stFormSubmitButton"] button
    { border-radius:4px; font-weight:700; min-height:2.75rem; }
.stApp button:focus-visible, .stApp a:focus-visible, .stApp input:focus-visible { outline:3px solid var(--ink) !important; outline-offset:2px; }
.stApp [data-testid="stExpander"] details, .stApp [data-testid="stExpander"] summary { background-color:transparent !important; color:var(--ink) !important; }
.stApp [data-baseweb="tab"] { color:var(--ink) !important; background:transparent !important; }
.stApp [data-baseweb="checkbox"] span, .stApp [data-baseweb="radio"] div { border-color:#6f8a84; }
#MainMenu, footer, header[data-testid="stHeader"] { visibility:hidden; height:0; }
.block-container { padding-top:0 !important; max-width:1180px; }

/* captions, alerts and spacing */
.stApp [data-testid="stCaptionContainer"], .stApp [data-testid="stCaptionContainer"] p { color:var(--muted) !important; opacity:1 !important; }
.stApp [data-testid="stAlert"] { background-color:#dbe9e5 !important; border-left:5px solid var(--spruce); border-radius:4px; }
.stApp [data-testid="stAlert"] p, .stApp [data-testid="stAlert"] div { color:var(--ink) !important; }
.stApp [data-testid="stMetric"] * { color:var(--ink) !important; }
.st-key-summary, .st-key-pricebox, .st-key-tier1, .st-key-tier2 { margin-top:1.4rem; }
.st-key-whatis { background:#fff; border:1px solid var(--line); border-left:5px solid var(--fire); border-radius:6px; padding:1rem 1.2rem; margin:1rem 0; }
.st-key-whatis h3 { font-size:1.6rem; margin:0 0 .3rem; }
.st-key-tier1, .st-key-tier2 { min-height:9.5rem; }
.stApp [data-testid="stTextInput"] [data-baseweb="base-input"] { border:1px solid #8fa9a3; border-radius:4px; }
.st-key-summary h3, .st-key-tier1 h3, .st-key-tier2 h3 { font-size:1.9rem; }
.st-key-pricebox h2 { font-family:var(--display); font-size:3.2rem; margin:0; }

/* hero band with the route line */
.topband { background:var(--ink); width:100vw; margin-left:calc(50% - 50vw); padding:.6rem calc(50vw - 590px + 5rem) 5rem; color:#fff; box-sizing:border-box; }
.topband .tag { color:#b8d3cb; font-size:.95rem; margin-top:.1rem; }
.topband h1 { font-family:var(--display); font-size:3rem; font-weight:700; line-height:1.02; margin:1.2rem 0 .2rem; letter-spacing:.005em; color:#fff; }
.route { display:block; width:100%; max-width:720px; height:auto; margin:.6rem 0 .4rem; }
.notice { background:#f4f8f7; border-left:5px solid var(--fire); color:var(--ink); padding:.55rem .8rem;
          font-size:.88rem; border-radius:3px; margin:.9rem 0 0; }

/* top navigation bar, in the same dark color as the band under it */
.stApp .st-key-nav { background:var(--ink); width:100vw !important; max-width:100vw !important; margin-left:calc(50% - 50vw) !important;
              box-sizing:border-box; padding:.55rem calc(50vw - 590px + 5rem) .1rem; margin-bottom:-1rem; }
.st-key-nav .brand { font-family:var(--display); font-size:1.7rem; font-weight:700; letter-spacing:.03em; color:#fff; line-height:2.6rem; }
.stApp .st-key-nav .stButton button:not([kind="primary"]) { background:transparent !important; border:none !important;
              color:#fff !important; min-height:2.6rem; box-shadow:none; }
.stApp .st-key-nav .stButton button:not([kind="primary"]) p { color:#fff !important; }
.stApp .st-key-nav .stButton button:not([kind="primary"]):hover { background:rgba(255,255,255,.14) !important; }

/* search bar sits over the band, with a thick colored edge */
.st-key-searchbar { background:#fff; border:4px solid var(--fire); border-radius:8px;
                    padding:.9rem 1rem .4rem; margin-top:-3.6rem; position:relative; z-index:3; }

/* trust strip, popular routes, result heading, sort pills */
.trust { display:flex; flex-wrap:wrap; gap:.4rem 2rem; margin:1.2rem 0 .4rem; color:var(--ink); font-weight:700; }
.trust span:before { content:"\\2713"; color:var(--green); margin-right:.45rem; font-weight:700; }
[class*="st-key-pop-"] { background:#fff; border:1px solid var(--line); border-radius:8px; padding:.9rem 1rem; }
[class*="st-key-pop-"]:hover { border-color:var(--ink); }
.pop .r { min-height:2.3em; font-family:var(--display); font-size:1.7rem; font-weight:700; color:var(--ink); line-height:1.05; }
.pop .d { color:var(--muted); font-size:.9rem; margin:.2rem 0 .5rem; }
.count h3 { font-size:1.9rem; margin:.2rem 0 0; }
.count .sub { color:var(--muted); font-size:.92rem; margin-bottom:.4rem; }
.stApp [data-testid="stButtonGroup"] button { border-radius:999px !important; border:1.5px solid var(--spruce) !important;
              background:#fff !important; color:var(--ink) !important; font-weight:700; }
.stApp [data-testid="stButtonGroup"] button[aria-checked="true"], .stApp [data-testid="stButtonGroup"] button[aria-pressed="true"]
              { background:var(--ink) !important; color:#fff !important; border-color:var(--ink) !important; }
.stApp [data-testid="stButtonGroup"] button[aria-checked="true"] p, .stApp [data-testid="stButtonGroup"] button[aria-pressed="true"] p
              { color:#fff !important; }
.st-key-searchbar label p { font-weight:700; font-size:.85rem; color:var(--muted); }
.st-key-searchbar [data-testid="stFormSubmitButton"] button { min-height:2.9rem; margin-top:1.55rem; }

.st-key-filters { background:#fff; border:1px solid var(--line); border-radius:6px; padding:1rem 1rem .5rem; }
.st-key-filters h4 { font-size:1.25rem; margin:0 0 .4rem; }

/* result cards read like a ticket: times and route line, a perforated edge, then the price */
[class*="st-key-card-"] { background:#fff; border:1px solid var(--line); border-radius:6px; padding:1rem 1.2rem;
                          margin-bottom:.9rem; }
[class*="st-key-card-"]:hover { border-color:var(--ink); }
[class*="st-key-card-"] [data-testid="stColumn"]:last-child { border-left:2px dashed var(--line); padding-left:1.1rem; }
.op { font-weight:700; color:var(--ink); font-size:1.05rem; }
.pill { display:inline-block; font-size:.78rem; font-weight:700; padding:.05rem .5rem; border-radius:3px;
        margin-left:.5rem; background:var(--ink); color:#fff; vertical-align:middle; }
.trip { display:flex; align-items:center; gap:.9rem; margin:.7rem 0 .2rem; }
.trip .t { font-family:var(--display); font-size:2.1rem; font-weight:600; color:var(--ink); line-height:1; white-space:nowrap; }
.trip .place { font-size:.85rem; color:var(--muted); margin-top:.2rem; }
.trip .bar { flex:1; text-align:center; font-size:.82rem; color:var(--muted); min-width:90px; position:relative; padding-bottom:.9rem; }
.trip .bar:after { content:""; position:absolute; left:0; right:0; bottom:.35rem; border-top:3px solid var(--spruce);
                   background:radial-gradient(circle, var(--spruce) 0 5px, transparent 6px) left center/12px 12px no-repeat,
                              radial-gradient(circle, var(--fire) 0 5px, transparent 6px) right center/12px 12px no-repeat; height:0; }
.badges { margin-top:.6rem; }
.badge { display:inline-block; font-size:.8rem; font-weight:700; padding:.15rem .5rem; border-radius:3px;
         margin:0 .35rem .3rem 0; background:#e0eae7; color:#2b4742; }
.badge.good { background:#d6ecdf; color:var(--green); }
.badge.fast { background:#dbe7f3; color:#1d4e89; }
.badge.warn { background:#fbeccb; color:#6b4a00; }
.badge.bad { background:#f8dbe4; color:#8e1f45; }
.small { font-size:.85rem; color:var(--muted); margin-top:.3rem; }
.price { text-align:left; }
.price .big { font-family:var(--display); font-size:2.8rem; font-weight:700; color:var(--ink); line-height:1; }
.price .per { font-size:.82rem; color:var(--muted); margin-bottom:.5rem; }

.st-key-summary, .st-key-tier1, .st-key-tier2, .st-key-pricebox { background:#fff; border:1px solid var(--line);
    border-radius:6px; padding:1rem 1.2rem; }
.st-key-tier2 { border-color:var(--fire); border-width:2px; }
@media (max-width:1200px){ .topband, .stApp .st-key-nav { padding-left:4rem; padding-right:4rem; } }
@media (max-width:760px){ .topband { padding:.4rem 1rem 4.6rem !important; } .stApp .st-key-nav { padding:.4rem 1rem .1rem !important; }
    .st-key-nav [data-testid="stHorizontalBlock"] { flex-wrap:wrap; gap:.1rem; }
    .st-key-nav [data-testid="stColumn"] { flex:0 0 auto !important; width:auto !important; min-width:0 !important; }
    .st-key-nav [data-testid="stColumn"]:first-child { flex:1 0 100% !important; } .topband h1 { font-size:2.1rem; }
    .trip .t { font-size:1.6rem; } [class*="st-key-card-"] [data-testid="stColumn"]:last-child { border-left:none; padding-left:0;
    border-top:2px dashed var(--line); padding-top:.8rem; margin-top:.6rem; }
    [data-testid="stColumn"]:has(> div > div > .st-key-filters), [data-testid="stColumn"]:has(.st-key-filters) { order:2; } }
</style>
"""

if "step" not in st.session_state:
    st.session_state.step = "search"
    st.session_state.query = {"from": "Anchorage", "to": "Seward", "date": DEFAULT_DATE, "riders": 1, "region": "Alaska"}
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


ROUTE_STOPS = {"Alaska": ["Seward", "Anchorage", "Talkeetna", "Denali", "Fairbanks"],
               "Ohio": ["Toledo", "Lima", "Springfield", "Dayton", "Cincinnati"]}


def route_svg(region: str) -> str:
    names = ROUTE_STOPS.get(region, ROUTE_STOPS["Alaska"])
    pts = [(20, 9, "#b3265e", "start"), (190, 6, "#fff", "middle"), (360, 6, "#fff", "middle"),
           (530, 6, "#fff", "middle"), (700, 9, "#b3265e", "end")]
    return ("<svg class='route' viewBox='0 0 720 64' aria-hidden='true' focusable='false'>"
            "<line x1='20' y1='24' x2='700' y2='24' stroke='#4fa58d' stroke-width='4'/>"
            "<line x1='20' y1='24' x2='700' y2='24' stroke='#0e2b26' stroke-width='2' stroke-dasharray='2 14'/>"
            + "".join(f"<circle cx='{x}' cy='24' r='{r}' fill='{c}' stroke='#fff' stroke-width='3'/>"
                      f"<text x='{x}' y='56' fill='#d7e8e3' font-size='15' text-anchor='{a}' "
                      f"font-family='Atkinson Hyperlegible, sans-serif'>{n}</text>"
                      for (x, r, c, a), n in zip(pts, names))
            + "</svg>")


def nav() -> None:
    """Top bar: name on the left, main pages on the right."""
    with st.container(key="nav"):
        c0, c1, c2, c3, c4 = st.columns([3.2, 1, 1.7, 1.1, 1.1])
        c0.markdown("<div class='brand'>Rural Travel Co-op</div>", unsafe_allow_html=True)
        c1.button("Home", on_click=go, args=("search",), key="nav_home")
        c2.button("Become a member", on_click=go, args=("join",), key="nav_join")
        c3.button("Privacy", on_click=open_legal, args=("privacy",), key="nav_priv")
        c4.button("Terms", on_click=open_legal, args=("terms",), key="nav_terms")


def header(title: str, show_route: bool = False, region: str = "") -> None:
    st.markdown(CSS, unsafe_allow_html=True)
    # Ask browsers and dark mode extensions not to restyle this page (it is designed in light colors)
    st.html("<img src='data:,' style='display:none' onerror=\"var d=document,h=d.head;"
            "['color-scheme:light','darkreader-lock:'].forEach(function(x){var m=d.createElement('meta');"
            "m.name=x.split(':')[0];m.content=x.split(':')[1]||'';h.appendChild(m);});\">")
    nav()
    route = route_svg(st.session_state.get("region_pick", st.session_state.query.get("region", "Alaska"))) if show_route else ""
    st.markdown(
        f"""<div class="topband"><div class="tag">A travel site owned by the riders who use it</div><h1>{escape(title)}</h1>{f"<div class='tag'>{escape(region)}</div>" if region else ""}{route}
        <div class="notice">Unofficial research prototype. Alaska Railroad and GoBus (Ohio) times are copied from
        their public schedules, and neither is a partner. GoBus fares are estimates. Trips marked demo are
        made up. Always confirm with the operator before you buy.</div></div>""", unsafe_allow_html=True)


POPULAR = {"Alaska": [("Anchorage", "Seward", "To the coast, by train or bus"),
                      ("Anchorage", "Fairbanks", "The long way north"),
                      ("Anchorage", "Talkeetna", "On the way to Denali")],
           "Ohio": [("Toledo", "Cincinnati", "Across the state, end to end"),
                    ("Dayton", "Lima", "Through the middle of western Ohio"),
                    ("Toledo", "Dayton", "North to the Miami Valley")]}
DEFAULT_PAIR = {"Alaska": ("Anchorage", "Seward"), "Ohio": ("Toledo", "Cincinnati")}


def search_bar(regions: list[dict]) -> None:
    """Search bar shown on the search and results screens. Step 1 is the region, then the two places in it."""
    q = st.session_state.query
    names = [r["name"] for r in regions]
    with st.container(key="searchbar"):
        region = st.selectbox("Where are you travelling?", names, key="region_pick",
                              index=names.index(q["region"]) if q.get("region") in names else 0)
        cities = next(r["cities"] for r in regions if r["name"] == region)
        with st.form("search_form", border=False):
            c1, c2, c3, c4, c5 = st.columns([2, 2, 1.7, 1, 1.4])
            d_from, d_to = DEFAULT_PAIR.get(region, (cities[0], cities[min(1, len(cities) - 1)]))
            origin = c1.selectbox("From", cities, index=cities.index(q["from"]) if q["from"] in cities else cities.index(d_from))
            dest = c2.selectbox("To", cities, index=cities.index(q["to"]) if q["to"] in cities else cities.index(d_to))
            when = c3.date_input("Date", value=max(q["date"], date.today()), min_value=date.today())
            riders = c4.number_input("Riders", min_value=1, max_value=10, value=q["riders"])
            submitted = c5.form_submit_button("Search", type="primary", width="stretch")
    if submitted:
        if origin == dest:
            st.warning("Choose two different places.")
            return
        st.session_state.query = {"region": region, "from": origin, "to": dest, "date": when, "riders": riders}
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
    header("Find your way between small towns", show_route=True)
    regions = api_get("/regions")
    if not regions:
        return
    search_bar(regions)
    st.markdown("<div class='trust'><span>Free to use, no account needed</span>"
                "<span>Rail and bus together in one search</span>"
                "<span>You book with the operator, refunds follow their rules</span></div>",
                unsafe_allow_html=True)
    region = st.session_state.get("region_pick", st.session_state.query.get("region", "Alaska"))
    st.markdown(f"### Popular routes in {escape(region)}")
    cols = st.columns(3)
    for i, (a_, b_, note) in enumerate(POPULAR.get(region, [])):
        with cols[i].container(key=f"pop-{i}"):
            st.markdown(f"<div class='pop'><div class='r'>{escape(a_)} to {escape(b_)}</div>"
                        f"<div class='d'>{escape(note)}</div></div>", unsafe_allow_html=True)
            if st.button("See trips", key=f"popbtn{i}", width="stretch"):
                q0 = st.session_state.query
                st.session_state.query = {**q0, "region": region, "from": a_, "to": b_}
                go("results")
                st.rerun()
    with st.container(key="whatis"):
        st.markdown("### What is a co-op?")
        st.write("A co-op (short for cooperative) is a business owned by the people who use it. Instead of profit "
                 "going to outside investors, members vote on decisions and any profit is shared back with them, "
                 "based on how much they used the service. Joining is optional.")
        st.button("Become a member", on_click=go, args=("join",))
    report_panel()


def badge(text: str, kind: str = "") -> str:
    return f'<span class="badge {kind}">{escape(text)}</span>'


def part_of_day(hhmm: str) -> str:
    h = minutes(hhmm) // 60
    return "Morning (before noon)" if h < 12 else "Afternoon (noon to 5 PM)" if h < 17 else "Evening (after 5 PM)"


def results_screen() -> None:
    q = st.session_state.query
    header(f"{q['from']} to {q['to']}", region=q.get("region", ""))
    regions = api_get("/regions")
    if not regions:
        return
    search_bar(regions)
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
        only_partner = st.checkbox("Partner operators only", value=False)

    shown = [t for t in trips
             if (mode == "Rail and bus" or t["mode"] == ("Rail" if mode == "Rail only" else "Bus"))
             and t["price"] <= max_price
             and (not times or part_of_day(t["depart"]) in times)
             and (not only_date or t.get("in_season") is not False)
             and (not only_partner or t["partner"])]

    with right:
        st.markdown(f"<div class='count'><h3>{escape(q['from'])} to {escape(q['to'])}: "
                    f"{len(shown)} option{'s' if len(shown) != 1 else ''} found</h3>"
                    f"<div class='sub'>{q['date']:%A, %b %d, %Y}</div></div>", unsafe_allow_html=True)
        sort_by = st.segmented_control("Sort by", ["Cheapest", "Earliest departure", "Shortest trip"],
                                       default="Cheapest", key="sort_by", label_visibility="collapsed") or "Cheapest"
        keys = {"Cheapest": lambda t: t["price"], "Earliest departure": lambda t: t["depart"],
                "Shortest trip": lambda t: minutes(t["arrive"]) - minutes(t["depart"])}
        shown.sort(key=keys[sort_by])

        if not shown:
            examples = {"Alaska": "Anchorage to Seward or Anchorage to Fairbanks",
                        "Ohio": "Toledo to Cincinnati or Dayton to Lima"}.get(q.get("region", ""), "another pair of places")
            st.info("No trips match these filters. Clear a filter, pick another date, or try " + examples + ".")
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
    if t.get("fare_estimated"):
        badges.append(badge("Fare estimated", "warn"))
    badges.append(badge("Partner operator", "good") if t["partner"] else badge("Listed only"))
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
        b.markdown(f"""<div class="price"><div class="big">{"~" if t.get("fare_estimated") else ""}${t['price'] * riders:,.0f}</div>
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
        if t.get("fare_estimated"):
            st.warning("This fare is an estimate. The operator publishes a fare range, not a fare for each pair of "
                       "stops. Check the exact fare on the operator's site before you buy.")
        st.info("The operator sells and issues your ticket. Refunds and changes follow the operator's rules.")
        if t.get("source_url"):
            st.caption(f"Time and fare copied from the operator's public schedule (checked {t.get('last_updated')}). "
                       f"Confirm on the operator's site before you buy. Source: {t['source_url']}")
    with right.container(key="pricebox"):
        st.markdown("**Price**")
        st.markdown(f"## {'~' if t.get('fare_estimated') else ''}${t['price'] * q['riders']:,.0f}")
        st.caption(f"${t['price']:,.0f} x {q['riders']} rider(s). Fare shown by the operator; taxes and fees "
                   "may apply on their site.")
        if t["partner"]:
            st.caption("Disclosure: we may receive a referral fee from this operator if you buy. "
                       "It does not change your price.")
        else:
            st.caption("We earn no fee from this trip.")
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
    c2.button("Become a member", on_click=go, args=("join",), width="stretch")


def join_screen() -> None:
    header("Become a member")
    c1, c2 = st.columns(2, gap="large")
    with c1.container(key="tier1"):
        st.markdown("### Free member")
        st.write("Get updates about new routes. Searching and comparing are free for everyone, member or not.")
    with c2.container(key="tier2"):
        st.markdown("### Paying member")
        st.write("Vote on decisions and receive a share of any profit, based on how much you travel with us.")
    st.write("")
    tier = st.radio("Choose a membership", ["Free member", "Paying member"], horizontal=True)
    email = st.text_input("Email")
    st.caption("This is a prototype: no payment is taken. Paying membership is recorded as interest only.")
    st.markdown("<div class='notice'><b>What we do with your email.</b> We save it, with the membership you chose "
                "and the date, so the project team can tell you about the co-op. We do not sell it or share it, "
                "and we send no advertising. We do not ask for your name, address or payment details.</div>",
                unsafe_allow_html=True)
    agreed = st.checkbox("I have read the privacy notice and the terms of use, and I agree to them.")
    pc1, pc2, _ = st.columns([1, 1, 3])
    pc1.button("Read privacy notice", on_click=open_legal, args=("privacy",), key="join_priv")
    pc2.button("Read terms of use", on_click=open_legal, args=("terms",), key="join_terms")
    if st.button("Join", type="primary"):
        if not agreed:
            st.warning("Please tick the box to confirm you have read the privacy notice and the terms.")
            saved = None
        else:
            saved = api_post("/members", {"email": email, "tier": 1 if tier.startswith("Free") else 2})
        if saved:
            st.success(f"Thanks. {saved['email']} is on the list as a {'free' if saved['tier'] == 1 else 'paying'} member ({saved['status']}).")
    counts = api_get("/members/count")
    if counts:
        st.caption(f"Sign ups so far: {counts['total']} ({counts['tier1']} free, {counts['tier2']} paying)")
    st.button("Start a new search", on_click=go, args=("search",))


def privacy_screen() -> None:
    header("Privacy notice")
    with st.container(key="legal"):
        st.markdown("""
**This is a research prototype. Here is what it saves and what it does not.**

**What we save**
- **Your email**, the membership you chose (free or paying) and the date, only if you join as a member.
- **A record each time you press "Continue to operator site"**: which trip, how many riders, the price shown, and the time.
  This record has no name, email or device details in it. We use it to count how many people were sent to an operator.

**What we do not save**
- No name, home address, phone number, or payment details.
- Searches you run and trips you only look at are not stored.
- We run no advertising and no tracking tools of our own.

**How we use it**
- To tell members about the co-op and new routes.
- To count referrals so the project can measure whether the idea works.

**Who sees it**
- The project team. Your email is not sold, rented or shared with an operator or anyone else.
- The data is kept with our hosting providers (the website, the server and the database). They store it for us.
- If you leave our site for an operator's site, the operator's own privacy rules apply there.

**How long we keep it**
- Emails are kept while the prototype is being tested and are deleted when the project ends.

**Your choices**
- You can ask the project team to delete your email at any time. This prototype has no delete button yet, so
  the team removes it by hand.
- Joining is optional. You can search and compare trips without giving an email.
""")
    st.button("Back", on_click=go, args=(st.session_state.get("return_to", "search"),))


def terms_screen() -> None:
    header("Terms of use")
    with st.container(key="legal"):
        st.markdown("""
**Please read this before you use the prototype.**

**1. What this site is.** A research prototype that shows bus and train times and prices in one place. It is not a
finished product and it may be wrong or unavailable.

**2. We do not sell tickets.** We do not take your payment and we do not issue tickets. When you press
"Continue to operator site" you leave this site, and you buy from the operator on its own site. Your ticket, its
price, refunds and changes are decided by that operator, and the operator is responsible for them.

**3. Times and prices can be wrong.** We copy them from public schedules, and the date we checked is shown on each
trip. A fare marked with "~" or "Fare estimated" is our estimate, because the operator publishes a range and not a
price for each pair of stops. Trips marked demo are made up. Always check the time, price and season on the
operator's site before you buy.

**4. No partnership.** Alaska Railroad and GoBus are not partners of this project and have not approved this site.
Names are used only to say which service a trip belongs to.

**5. Referral fees.** Where a trip says we may receive a referral fee, that fee does not change your price.

**6. Membership.** Joining the list records interest only. No money is taken, and no vote, profit share or other
right starts from signing up on this prototype.

**7. Use it fairly.** Do not try to break the site or read other people's data.

**8. No promise.** The site is offered as it is, for testing. To the extent the law allows, the project team is not
responsible for losses that come from using it, including a missed trip caused by a wrong time or price.
""")
    c1, c2, _ = st.columns([1, 1.4, 2])
    c1.button("Back", on_click=go, args=(st.session_state.get("return_to", "search"),), key="terms_back")
    c2.button("Read privacy notice", on_click=go, args=("privacy",), key="terms_priv")


def open_legal(page: str) -> None:
    if st.session_state.step not in ("privacy", "terms"):
        st.session_state.return_to = st.session_state.step
    go(page)


def footer() -> None:
    if st.session_state.step in ("privacy", "terms"):
        return
    st.write("")
    f1, f2, _ = st.columns([1, 1, 4])
    f1.button("Privacy notice", on_click=open_legal, args=("privacy",), key="foot_priv", type="tertiary")
    f2.button("Terms of use", on_click=open_legal, args=("terms",), key="foot_terms", type="tertiary")


{"search": search_screen, "results": results_screen, "handoff": handoff_screen, "join": join_screen,
 "privacy": privacy_screen, "terms": terms_screen}[st.session_state.step]()
footer()
