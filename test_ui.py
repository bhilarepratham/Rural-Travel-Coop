"""Checks the privacy notice and terms screens. Run with the backend up:
   BACKEND_URL=http://localhost:8000 python test_ui.py"""
import os, sys
from streamlit.testing.v1 import AppTest

def ok(c, l):
    print(("PASS " if c else "FAIL ") + l)
    if not c: sys.exit(1)

at = AppTest.from_file("frontend/app.py", default_timeout=60).run()
ok(not at.exception, "home loads")
labels = [b.label for b in at.button]
ok("Privacy notice" in labels and "Terms of use" in labels, "footer links on home")
next(b for b in at.button if b.label == "Privacy notice").click(); at.run()
ok(not at.exception and at.session_state.step == "privacy", "privacy screen opens")
ok(any("What we save" in m.value for m in at.markdown), "privacy text shown")
next(b for b in at.button if b.label == "Back").click(); at.run()
ok(at.session_state.step == "search", "back returns to search")
next(b for b in at.button if b.label == "Terms of use").click(); at.run()
ok(any("We do not sell tickets" in m.value for m in at.markdown), "terms text shown")
at.session_state.step = "join"; at.run()
ok(not at.exception and len(at.checkbox) == 1, "join has consent box")
at.text_input[0].set_value("ui-test@example.com").run()
next(b for b in at.button if b.label == "Join").click(); at.run()
ok(any("tick the box" in w.value for w in at.warning), "join blocked without consent")
at.checkbox[0].check().run()
next(b for b in at.button if b.label == "Join").click(); at.run()
ok(any("on the list" in s.value for s in at.success), "join works with consent")
# Remove my email, on the same screen
ok(any(e.label == "Already joined? Remove my email" for e in at.expander), "join screen has the Remove my email option")
import requests as _rq
_url = os.environ.get("BACKEND_URL", "http://localhost:8000") + "/members/count"
_before = _rq.get(_url).json()["total"]
at.text_input(key="remove_email").set_value("ui-test@example.com").run()
next(b for b in at.button if b.label == "Remove my email").click(); at.run()
ok(any("has been deleted" in s.value for s in at.success), "Remove my email shows the confirmation")
ok(_rq.get(_url).json()["total"] == _before - 1, "the email was really deleted from the member list")
at.text_input(key="remove_email").set_value("bad address").run()
next(b for b in at.button if b.label == "Remove my email").click(); at.run()
ok(any("valid email" in w.value for w in at.warning), "Remove my email rejects a bad address")
at.session_state.step = "privacy"; at.run()
ok(any("Remove my email" in m.value for m in at.markdown), "privacy notice points to Remove my email")
at.session_state.step = "join"; at.run()
next(b for b in at.button if b.label == "Read terms of use").click(); at.run()
next(b for b in at.button if b.label == "Back").click(); at.run()
ok(at.session_state.step == "join", "back from terms returns to join")
print("ALL PASS")

# ---- waking up message: backend down shows the message, then an error after the wait runs out
import os as _os
_os.environ["WAKE_MAX_SECONDS"] = "7"
_old = _os.environ.get("BACKEND_URL")
_os.environ["BACKEND_URL"] = "http://127.0.0.1:9"   # nothing listens here
import time as _t
_t0 = _t.time()
down = AppTest.from_file("frontend/app.py", default_timeout=60).run()
ok(not down.exception, "app does not crash when the backend is asleep")
ok(any("did not wake up" in (s.label or "") for s in down.status) or any("still asleep" in e.value for e in down.error), "clear message shown when the server stays asleep")
ok(_t.time() - _t0 >= 6, "waits for the server before giving up")
# privacy page must not wait for the backend
down.session_state["step"] = "privacy"; _t1 = _t.time(); down.run()
ok(_t.time() - _t1 < 5 and any("What we save" in m.value for m in down.markdown), "privacy page opens even when the backend is asleep")
if _old is None: _os.environ.pop("BACKEND_URL", None)
else: _os.environ["BACKEND_URL"] = _old
print("ALL PASS (wake tests)")
