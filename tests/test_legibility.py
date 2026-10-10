"""Measure what a reader gets: on-screen text size and contrast for every kind of text, per view and width.

Run: python3 tests/test_legibility.py [--report]   (needs google-chrome; run outside a sandbox)
Fails when any text is smaller than MIN_PX on screen or below MIN_CONTRAST against the surface behind it.
The thresholds are the usual ones for data-dense interfaces: 12 px, and WCAG AA 4.5:1 for normal text.
"""
import json, os, re, subprocess, sys, tempfile, urllib.parse

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MIN_PX, MIN_CONTRAST = 12.0, 4.5
PROBE = open(os.path.join(REPO, "tests", "legibility_probe.js")).read()
VIEWS = [("roadmap", {"view": "roadmap"}), ("tour 2020", {"view": "roadmap", "tour": 3}), ("all papers", {"view": "tree"}), ("directions", {"view": "directions"}), ("industry", {"view": "products"})]
SIZES = ["1500,900", "1280,800"]


def measure(state, size, dark=True):
    page = open(os.path.join(REPO, "web", "index.html")).read().replace('<script src="app.js"></script>', '<script src="app.js"></script><script>setTimeout(function(){' + PROBE + '}, 1500)</script>')
    with tempfile.TemporaryDirectory() as profile:
        probe_page = os.path.join(REPO, "web", "_legibility.html")
        open(probe_page, "w").write(page)
        try:
            result = subprocess.run(["google-chrome", "--headless=new", "--no-sandbox", "--disable-gpu", f"--user-data-dir={profile}", f"--window-size={size}",
                                     *(["--force-dark-mode"] if dark else []), "--virtual-time-budget=8000", "--dump-dom",
                                     "file://" + probe_page + "?test#" + urllib.parse.quote(json.dumps(state))], capture_output=True, text=True, timeout=120)
        finally:
            os.remove(probe_page)
    found = re.search(r'<pre id="legibility">(.*?)</pre>', result.stdout, re.S)
    if not found:
        raise SystemExit(f"NO_MEASUREMENT for {state} at {size}")
    return json.loads(found.group(1).replace("&quot;", '"').replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">"))


worst, failures = {}, 0
for size in SIZES:
    for name, state in VIEWS:
        for kind, row in measure(state, size).items():
            key = kind
            if key not in worst or row["px"] < worst[key]["px"] or row["contrast"] < worst[key]["contrast"]:
                worst[key] = {"px": min(row["px"], worst.get(key, row)["px"]), "contrast": min(row["contrast"], worst.get(key, row)["contrast"]), "where": f"{name} @ {size.split(',')[0]}"}
print(f"{'text':26s} {'min px':>7s} {'min contrast':>13s}   worst case")
for kind, row in sorted(worst.items(), key=lambda kv: kv[1]["px"]):
    bad = row["px"] < MIN_PX or row["contrast"] < MIN_CONTRAST
    failures += bad
    print(f"{kind:26s} {row['px']:7.1f} {row['contrast']:13.2f}   {row['where']}{'   <-- FAIL' if bad else ''}")
print(f"{failures} kinds of text fail (limits: {MIN_PX} px, {MIN_CONTRAST}:1)")
sys.exit(1 if failures else 0)
