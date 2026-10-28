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
next(b for b in at.button if b.label == "Read terms of use").click(); at.run()
next(b for b in at.button if b.label == "Back").click(); at.run()
ok(at.session_state.step == "join", "back from terms returns to join")
print("ALL PASS")
