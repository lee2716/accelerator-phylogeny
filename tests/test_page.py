"""Load web/index.html in headless Chrome, once per view, and check the rendered DOM as text.

Run: python3 tests/test_page.py      (needs google-chrome; exits non-zero on the first failed check)
Checks per view: no uncaught script error, no 'undefined' / 'NaN' / '[object Object]' in the visible text,
six navigation tabs, and view-specific minimum content. The page is never judged by looking at an image.
"""
import json, os, re, subprocess, sys, tempfile, urllib.parse

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PAGE = "file://" + os.path.join(REPO, "web", "index.html")
data_text = open(os.path.join(REPO, "web", "data.js")).read()
DATA = json.loads(data_text[data_text.index("{"):data_text.rindex("}") + 1])
followed = max(DATA["papers"], key=lambda p: len(p["fol"]))
lonely = next(p for p in DATA["papers"] if not p["fol"] and p["cit"]["status"] == "FETCHED" and p["cit"]["outside_n"] == 0)
marked = next(p for p in DATA["papers"] if p["inf"]["tier"] == "top_10" and p["nov"]["tier"] == "opened_line")
outside_only = next(p for p in DATA["papers"] if not p["fol"] and p["cit"]["status"] == "FETCHED" and p["cit"]["outside_n"] > 0)


def render(state):
    url = PAGE + "#" + urllib.parse.quote(json.dumps(state))
    with tempfile.TemporaryDirectory() as profile:
        result = subprocess.run(["google-chrome", "--headless=new", "--no-sandbox", "--disable-gpu", f"--user-data-dir={profile}",
                                 "--enable-logging=stderr", "--v=0", "--virtual-time-budget=4000", "--dump-dom", url],
                                capture_output=True, text=True, timeout=120)
    errors = [line for line in result.stderr.splitlines() if "CONSOLE" in line and ("Uncaught" in line or "rror" in line)]
    return result.stdout, errors


def visible_text(dom):
    body = dom[dom.index("<body"):]
    body = re.sub(r"<script.*?</script>", " ", body, flags=re.S)
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", body))


def check(name, state, must_contain, min_rows=0):
    dom, errors = render(state)
    text = visible_text(dom)
    problems = [f"script error: {e[-160:]}" for e in errors]
    problems += [f"'{bad}' appears in the page text" for bad in ("undefined", "NaN", "[object Object]") if bad in text]
    if dom.count('role="tab"') != 6:
        problems.append(f"expected 6 tabs, found {dom.count('role=\"tab\"')}")
    problems += [f"missing text: {needle!r}" for needle in must_contain if needle not in text]
    rows = dom.count("<tr")
    if rows < min_rows:
        problems.append(f"only {rows} table rows, expected at least {min_rows}")
    print(f"{name:34s} {'OK' if not problems else 'FAIL'}  ({len(text)} chars of text, {rows} table rows)")
    for problem in problems:
        print("   ", problem)
    return not problems


results = [
    check("trends, default axis", {"view": "trends"}, ["Which directions grew", "cim analog nvm", "papers that year"], min_rows=6),
    check("trends, every axis", {"view": "trends", "axis": "lever"}, ["What the paper acts on", "nonideality reliability"], min_rows=6),
    check("trends, cell selected", {"view": "trends", "axis": "A1_paradigm", "cell": {"value": "cim_digital", "year": 2024}}, ["Compute paradigm = cim digital, 2024"]),
    check("direction over time", {"view": "direction", "dir": "A1_paradigm=cim_digital"}, ["How one direction changed", "2018-2020", "2024-2025", "Change"], min_rows=8),
    check("lineage, no paper", {"view": "lineage", "paper": None}, ["Pick a paper", "Most followed"]),
    check("lineage, followed paper", {"view": "lineage", "paper": followed["id"]}, ["Followed by", "later paper(s) inside these four venues", followed["t"][:40], "edge from"]),
    check("marks on a marked paper", {"view": "lineage", "paper": marked["id"]}, ["★★★ top 10%", "◆ opened a line"]),
    check("lineage, nobody found", {"view": "lineage", "paper": lonely["id"]}, ["No citing work found in OpenAlex or Crossref"]),
    check("lineage, outside only", {"view": "lineage", "paper": outside_only["id"]}, ["outside these four venues", "the line continued elsewhere"]),
    check("time cross-section", {"view": "time", "year": 2022}, ["2022 in detail", "Papers: compute paradigm", "No data yet"], min_rows=7),
    check("industry products", {"view": "products"}, ["Product lines", "Sources for this line", "Looked for and not found"] if DATA["industry"] else ["No product line has been collected"]),
    check("industry, conflicting accounts", {"view": "products", "line": "axelera"}, ["Conflicting accounts", "rung:"]),
    check("sources and limits", {"view": "sources"}, ["What this page rests on", "Cohen's kappa", "Evidence tiers", "Measured recall", "Marks on every paper", "line predates the data"], min_rows=10),
]
print(f"{sum(results)}/{len(results)} views pass")
sys.exit(0 if all(results) else 1)
