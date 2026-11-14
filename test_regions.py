"""Region, filter and sort checks for the Streamlit screens. Backend must be running:
   BACKEND_URL=http://localhost:8000 python test_regions.py"""
import re, sys
from datetime import date
from streamlit.testing.v1 import AppTest

fails = []
def ok(c, l):
    print(("PASS " if c else "FAIL ") + l)
    if not c: fails.append(l)

def card_ops(at):  # operator names in order of cards
    out = []
    for m in at.markdown:
        if 'class="op"' in m.value:
            out.append(re.search(r'class="op">([^<]+)', m.value).group(1))
    return out
def card_times(at):
    return [re.search(r'class="t">([^<]+)', m.value).group(1) for m in at.markdown if 'class="op"' in m.value]
def card_prices(at):
    return [int(re.search(r'class="big">~?\$([\d,]+)', m.value).group(1).replace(",", "")) for m in at.markdown if 'class="price"' in m.value]

def search(region, a, b, d=None):
    at = AppTest.from_file("frontend/app.py", default_timeout=60)
    at.session_state["step"] = "results"; at.session_state["selected"] = None; at.session_state["click_id"] = None
    at.session_state["query"] = {"region": region, "from": a, "to": b, "date": d or date.today(), "riders": 1}
    return at.run()

# Ohio search
at = search("Ohio", "Toledo", "Cincinnati")
ok(not at.exception, "Ohio results load")
ok(len(card_ops(at)) == 2 and all("GoBus Red Line" in o for o in card_ops(at)), "Ohio Toledo to Cincinnati shows 2 GoBus cards")
ok(any("Fare estimated" in m.value for m in at.markdown), "estimated fare badge on Ohio cards")
ok(all(p >= 5 for p in card_prices(at)), "Ohio prices at least $5")

# other GoBus lines: Green (Columbus to Athens), Purple (Columbus to Toledo), and the place list
at2 = search("Ohio", "Columbus", "Athens")
ok(not at2.exception and len(card_ops(at2)) == 3 and all("GoBus Green Line" in o for o in card_ops(at2)), "Columbus to Athens shows 3 Green Line cards")
ok(card_prices(at2) == [10, 10, 10], "Columbus to Athens fares are $10 estimates")
ok(not any("None" in m.value for m in at2.markdown if 'class="op"' in m.value) and any("No season dates" in m.value for m in at2.markdown), "no 'Season None' text on lines with no printed season")
at2 = search("Ohio", "Columbus", "Toledo")
ok(any("GoBus Purple Line" in o for o in card_ops(at2)), "Columbus to Toledo is on the Purple Line")
at2 = search("Ohio", "Athens", "Wheeling")
ok(not at2.exception and len(card_ops(at2)) == 0, "a pair with no direct bus shows no cards and does not crash")
home = AppTest.from_file("frontend/app.py", default_timeout=60); home.session_state["region_pick"] = "Ohio"; home.run()
opts = next(s_ for s_ in home.selectbox if s_.label in ("From", "Leaving from")).options if any(s_.label in ("From", "Leaving from") for s_ in home.selectbox) else []
ok(len(opts) >= 50 and "Athens" in opts and "Columbus" in opts, f"Ohio place list has all GoBus places ({len(opts)})")

# mode filter: Ohio has no rail
mode = next(r for r in at.radio if r.label == "Mode")
mode.set_value("Rail only").run()
ok(len(card_ops(at)) == 0 and any("No trips match" in i.value for i in at.info), "Ohio Rail only shows empty message")
ok(not any("Anchorage to Seward" in i.value for i in at.info), "empty message is not Alaska specific")
at.radio(key=None) if False else None
next(r for r in at.radio if r.label == "Mode").set_value("Bus only").run()
ok(len(card_ops(at)) == 2, "Ohio Bus only keeps both trips")

# time filter
ms = next(m for m in at.multiselect if m.label == "Departure time")
ms.set_value(["Afternoon (noon to 5 PM)"]).run()
ok(len(card_ops(at)) == 0, "afternoon filter removes both morning Ohio trips")
next(m for m in at.multiselect if m.label == "Departure time").set_value(["Morning (before noon)"]).run()
ok(len(card_ops(at)) == 2, "morning filter keeps both")

# sorting: earliest, cheapest, shortest on a longer pair
at = search("Ohio", "Dayton", "Toledo")
n = len(card_ops(at)); ok(n >= 1, f"Dayton to Toledo has results ({n})")
at.segmented_control(key="sort_by").set_value("Earliest departure").run()
def to24(s):
    t, ap = s.split(); h, m = map(int, t.split(":")); return (h % 12 + (12 if ap == "PM" else 0)) * 60 + m
tm = [to24(x) for x in card_times(at)[0::2]] if False else None
times = [to24(m.value) for m in []]
raw = [re.findall(r'class="t">([^<]+)', m.value) for m in at.markdown if 'class="op"' in m.value]
deps = [to24(r[0]) for r in raw]
ok(deps == sorted(deps), "sorted by earliest departure")
at.segmented_control(key="sort_by").set_value("Cheapest").run()
pr = card_prices(at); ok(pr == sorted(pr), "sorted by cheapest")
at.segmented_control(key="sort_by").set_value("Shortest trip").run()
raw = [re.findall(r'class="t">([^<]+)', m.value) for m in at.markdown if 'class="op"' in m.value]
dur = [to24(r[1]) - to24(r[0]) for r in raw]; ok(dur == sorted(dur), "sorted by shortest trip")

# Alaska
at = search("Alaska", "Anchorage", "Seward")
ok(not at.exception and len(card_ops(at)) >= 3, "Alaska Anchorage to Seward loads")
ok(any("Alaska Railroad" in o for o in card_ops(at)), "Alaska Railroad trips shown")
next(r for r in at.radio if r.label == "Mode").set_value("Rail only").run()
ok(all("Railroad" in o for o in card_ops(at)), "Alaska Rail only has only railroad")
next(r for r in at.radio if r.label == "Mode").set_value("Bus only").run()
ok(all("Railroad" not in o for o in card_ops(at)), "Alaska Bus only has no railroad")

# cross region pair returns nothing and does not crash
at = search("Alaska", "Anchorage", "Toledo")
ok(not at.exception, "cross region pair does not crash")

# select a trip and reach the handoff for an Ohio fare
at = search("Ohio", "Toledo", "Cincinnati")
next(b for b in at.button if b.label == "Select").click(); at.run()
ok(at.session_state.step == "handoff" and any("estimate" in w.value for w in at.warning), "Ohio handoff warns the fare is an estimate")

# ---- Alberta: listings without times; Red Arrow has an estimated fare in Canadian dollars ----
def price_texts(at):
    return [re.search(r'class="big"[^>]*>([^<]+)', m.value).group(1) for m in at.markdown if 'class="price"' in m.value]
at = search("Alberta", "Edmonton", "Calgary")
ok(not at.exception and len(card_ops(at)) == 4, "Alberta Edmonton to Calgary shows 4 carrier cards")
ok(card_ops(at)[0].startswith("Red Arrow (Alberta)") and {o.split("<")[0] for o in card_ops(at)} <= {"Red Arrow (Alberta)", "FlixBus (Alberta)", "Cold Shot (Alberta)", "Rider Express (Alberta)"}, "Alberta carriers are named")
ok(price_texts(at) == ["~CA$72", "Fare on operator site", "Fare on operator site", "Fare on operator site"], f"Red Arrow estimate first, others say fare on operator site ({price_texts(at)})")
ok(not any('class="t">' in m.value and ("AM" in m.value or "PM" in m.value) for m in at.markdown if 'class="op"' in m.value), "Alberta cards show no clock times")
ok(sum("Departure times are shown on the operator" in m.value for m in at.markdown) == 4 and any("Route listing, unofficial" in m.value for m in at.markdown), "Alberta cards say times are on the operator's site")
ok(not any("Cheapest" in m.value or "Fastest" in m.value for m in at.markdown if 'class="badges"' in m.value), "no Cheapest or Fastest badge when only one fare or no times are known")
ok(any("Flying instead?" in m.value for m in at.markdown), "Alberta results offer plain links to Air Canada and WestJet")
ok(not any("Flying instead?" in m.value for m in search("Ohio", "Toledo", "Cincinnati").markdown), "no airline note outside Alberta")
for how in ("Earliest departure", "Shortest trip", "Cheapest"):
    at.segmented_control(key="sort_by").set_value(how).run()
    ok(not at.exception and len(card_ops(at)) == 4, f"Alberta sort by {how} does not crash and keeps 4 cards")
ms = next(m for m in at.multiselect if m.label == "Departure time")
ms.set_value(["Morning (before noon)"]).run()
ok(len(card_ops(at)) == 4, "time filter keeps Alberta listings (their times are unknown)")
ok(next(sl for sl in at.slider if sl.label.startswith("Highest price per rider")).label.endswith("(CA$)"), "price filter is labeled in CA$")
next(r for r in at.radio if r.label == "Mode").set_value("Rail only").run()
ok(len(card_ops(at)) == 0 and any("Edmonton to Calgary" in i.value for i in at.info), "Alberta Rail only shows an Alberta example in the empty message")
at = search("Alberta", "Edmonton", "Fort McMurray")
ok(price_texts(at)[0] == "~CA$97" and len(card_ops(at)) == 3, f"Edmonton to Fort McMurray: Red Arrow ~CA$97 plus Cold Shot and Rider Express ({price_texts(at)})")
at = search("Alberta", "Gibbons", "Radway")
ok(len(card_ops(at)) == 1 and price_texts(at) == ["Fare on operator site"], "short Red Arrow pair shows no estimate")
at = search("Alberta", "Calgary", "Lethbridge")
ok(len(card_ops(at)) == 1 and card_ops(at)[0].startswith("FlixBus (Alberta)"), "Calgary to Lethbridge is Flix only")
at = search("Alberta", "Red Deer", "Fort McMurray")
ok(len(card_ops(at)) == 1 and card_ops(at)[0].startswith("Red Arrow (Alberta)"), "Red Deer to Fort McMurray is Red Arrow only")
ok(any("Mon, Tue, Wed, Thu, Sun" in m.value for m in at.markdown), "Red Arrow days from the route page are shown")
# riders multiply the estimate
at = AppTest.from_file("frontend/app.py", default_timeout=60)
at.session_state["step"] = "results"; at.session_state["selected"] = None; at.session_state["click_id"] = None
at.session_state["query"] = {"region": "Alberta", "from": "Edmonton", "to": "Calgary", "date": date.today(), "riders": 2}
at.run()
ok(price_texts(at)[0] == "~CA$144", f"two riders: ~CA$144 ({price_texts(at)[0]})")
# handoff for the priced listing and for an unpriced one
at = search("Alberta", "Edmonton", "Calgary")
btns = [b for b in at.button if b.label == "Select"]
btns[0].click(); at.run()
ok(at.session_state.step == "handoff" and any("average price for some routes" in w.value for w in at.warning), "Red Arrow handoff warns the fare is an estimate")
ok(any("Departure times are shown on the operator" in m.value for m in at.markdown) and any("CA$72" in m.value for m in at.markdown), "Red Arrow handoff shows no time and CA$72")
ok(not any(w.value.startswith("This fare is an estimate. The operator publishes fares by miles") for w in at.warning), "Alberta handoff does not use the GoBus wording")
at = search("Alberta", "Edmonton", "Calgary")
[b for b in at.button if b.label == "Select"][1].click(); at.run()
ok(at.session_state.step == "handoff" and any("Fare on operator site" in m.value for m in at.markdown) and not at.warning, "unpriced listing hands off with no fare and no estimate warning")
# switch region to Alberta on the search bar
at = search("Alaska", "Anchorage", "Seward")
next(s for s in at.selectbox if s.label == "Where are you travelling?").select("Alberta").run()
frm = next(s for s in at.selectbox if s.label == "From"); to = next(s for s in at.selectbox if s.label == "To")
ok("Edmonton" in frm.options and "Anchorage" not in frm.options and frm.value == "Edmonton" and to.value == "Calgary", "Alberta search bar lists Alberta places and defaults to Edmonton to Calgary")

# switch region on the search bar
at = search("Alaska", "Anchorage", "Seward")
sel = next(s for s in at.selectbox if s.label == "Where are you travelling?")
sel.select("Ohio").run()
frm = next(s for s in at.selectbox if s.label == "From")
ok("Toledo" in frm.options and "Anchorage" not in frm.options, "switching to Ohio changes the From list")
frm = next(s for s in at.selectbox if s.label == "From"); to = next(s for s in at.selectbox if s.label == "To")
ok(frm.value == "Toledo" and to.value == "Cincinnati", "Ohio search bar defaults to Toledo to Cincinnati")
# popular route tiles lead to results for each region
for region, pairs in (("Alaska", None), ("Ohio", None), ("Alberta", None)):
    at = AppTest.from_file("frontend/app.py", default_timeout=60)
    at.session_state["step"] = "search"; at.session_state["selected"] = None; at.session_state["click_id"] = None
    at.session_state["query"] = {"region": region, "from": "x", "to": "y", "date": date.today(), "riders": 1}
    at.run()
    tiles = [b for b in at.button if b.label == "See trips"]
    ok(len(tiles) == 3, f"{region} home has 3 popular route tiles")
    for i in range(len(tiles)):
        at = AppTest.from_file("frontend/app.py", default_timeout=60)
        at.session_state["step"] = "search"; at.session_state["selected"] = None; at.session_state["click_id"] = None
        at.session_state["query"] = {"region": region, "from": "x", "to": "y", "date": date.today(), "riders": 1}
        at.run()
        [b for b in at.button if b.label == "See trips"][i].click(); at.run()
        ok(at.session_state.step == "results" and len(card_ops(at)) >= 1 and not at.exception,
           f"{region} popular tile {i + 1} opens results with trips ({at.session_state.query['from']} to {at.session_state.query['to']})")
print("FAILED:" if fails else "ALL PASS", fails)
sys.exit(1 if fails else 0)
