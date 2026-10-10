"""Load web/index.html in headless Chrome, once per view, and check the rendered DOM as text.

Run: python3 tests/test_page.py      (needs google-chrome; run outside a sandbox: Chrome needs a local socket)
Checks per view: no uncaught script error; no 'undefined' / 'NaN' / '[object Object]' in the visible text;
four navigation tabs; view-specific content; on the tree, one light per paper and the right kinship threads.
"""
import json, os, re, subprocess, sys, tempfile, urllib.parse

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PAGE = "file://" + os.path.join(REPO, "web", "index.html")
data_text = open(os.path.join(REPO, "web", "data.js")).read()
DATA = json.loads(data_text[data_text.index("{"):data_text.rindex("}") + 1])
PAPERS = DATA["papers"]
ids = {p["id"] for p in PAPERS}
followed = max(PAPERS, key=lambda p: len(p["fol"]))
marked = next(p for p in PAPERS if p["inf"]["tier"] == "top_10" and p["nov"]["tier"] == "opened_line")
lonely = next(p for p in PAPERS if not p["fol"] and p["cit"]["status"] == "FETCHED" and p["cit"]["outside_n"] == 0)
outside_only = next(p for p in PAPERS if not p["fol"] and p["cit"]["status"] == "FETCHED" and p["cit"]["outside_n"] > 0)


def render(state):
    url = PAGE + "?test#" + urllib.parse.quote(json.dumps(state))   # a query switches the entrance animation off
    with tempfile.TemporaryDirectory() as profile:
        result = subprocess.run(["google-chrome", "--headless=new", "--no-sandbox", "--disable-gpu", f"--user-data-dir={profile}",
                                 "--enable-logging=stderr", "--v=0", "--virtual-time-budget=5000", "--dump-dom", url],
                                capture_output=True, text=True, timeout=120)
    errors = [line for line in result.stderr.splitlines() if "CONSOLE" in line and ("Uncaught" in line or "rror" in line) and "fonts.g" not in line]
    return result.stdout, errors


def visible_text(dom):
    body = dom[dom.index("<body"):]
    body = re.sub(r"<script.*?</script>", " ", body, flags=re.S)
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", body))


def check(name, state, must_contain, extra=None):
    dom, errors = render(state)
    text = visible_text(dom)
    problems = [f"script error: {e[-160:]}" for e in errors]
    problems += [f"'{bad}' appears in the page text" for bad in ("undefined", "NaN", "[object Object]") if bad in text]
    if dom.count('role="tab"') != 4:
        problems.append(f"expected 4 tabs, found {dom.count('role=\"tab\"')}")
    problems += [f"missing text: {needle!r}" for needle in must_contain if needle not in text]
    if extra:
        problems += extra(dom)
    print(f"{name:36s} {'OK' if not problems else 'FAIL'}  ({len(text)} chars of text)")
    for problem in problems:
        print("   ", problem)
    return not problems


def tree_shape(dom):
    lights = len(re.findall(r'class="dot[ "]', dom))
    problems = [] if lights == len(PAPERS) else [f"{lights} lights drawn for {len(PAPERS)} papers"]
    if dom.count('class="river"') < 4:
        problems.append("fewer than four rivers drawn")
    if "class=\"kin" in dom:
        problems.append("kinship threads drawn with nothing selected")
    names = re.findall(r'class="plabel[^"]*"[^>]*>([^<]+)<', dom)
    if len(names) < 30:
        problems.append(f"only {len(names)} landmark names on the tree, expected at least 30")
    if len(dom.split('class="halo"')) - 1 < 50:
        problems.append("fewer than 50 landmark halos drawn")
    products = sum(1 for line in DATA["industry"] for g in line["generations"] if g["year_announced"] and 2018 <= g["year_announced"] <= 2026)
    if dom.count('class="prod"') != products:
        problems.append(f"{dom.count('class=\"prod\"')} product markers for {products} dated generations")
    return problems


def kin_threads(paper):
    def expect(dom):
        direct = sum(1 for f in paper["fol"] if f["id"] in ids) + sum(1 for r in paper["refs"] if r["id"] in ids)
        drawn = dom.count('class="kin')
        problems = [] if drawn >= direct else [f"{drawn} threads drawn, at least {direct} direct in-slice links expected"]
        if dom.count(" sel\"") != 1:
            problems.append("exactly one light should be marked selected")
        if 'class="plabel self"' not in dom:
            problems.append("the selected paper is not named on the tree")
        if dom.count('class="plabel down"') + dom.count('class="plabel up"') < min(direct, 5):
            problems.append("the selection's kin are not named on the tree")
        return problems
    return expect


results = [
    check("hero and tree", {"view": "tree"}, ["Accelerator Phylogeny", "papers placed", "lineage threads", "Every paper is a light", "Start anywhere", "Industry products", "Landmarks, named", "ReTransformer"], tree_shape),
    check("tree coloured by workload", {"view": "tree", "colorBy": "A0_workload"}, ["LLM (autoregressive)", "two-prompt agreement"]),
    check("paper selected: threads", {"view": "tree", "sel": {"type": "paper", "id": followed["id"]}}, ["Grew out of it", "Grew from", followed["t"][:40], "Lit on the tree", "via "], kin_threads(followed)),
    check("marks on a marked paper", {"view": "tree", "sel": {"type": "paper", "id": marked["id"]}}, ["★★★ top 10%", "◆ opened a line", "T1 peer-reviewed"]),
    check("paper nobody cited", {"view": "tree", "sel": {"type": "paper", "id": lonely["id"]}}, ["No citing work found in OpenAlex or Crossref"]),
    check("paper followed elsewhere only", {"view": "tree", "sel": {"type": "paper", "id": outside_only["id"]}}, ["outside these four venues", "the line continued elsewhere"]),
    check("year cross-section", {"view": "tree", "sel": {"type": "year", "id": 2022}}, ["2022 — a cross-section", "Compute paradigm", "Industry that year", "No data yet"]),
    check("river selected", {"view": "tree", "sel": {"type": "lane", "id": "cim_digital"}}, ["Digital in-memory", "Most followed", "Compare its periods"]),
    check("directions", {"view": "directions", "axis": "A1_paradigm", "dir": "A1_paradigm=cim_digital"}, ["Which directions grew", "How one direction changed", "2018-2020", "2024-2025", "n="]),
    check("directions, other axis", {"view": "directions", "axis": "lever"}, ["What the paper acts on", "nonideality reliability"]),
    check("industry", {"view": "products"}, ["What industry shipped", "Where it sits", "Looked for and not found", "Sources for this line", "year ?"]),
    check("industry, conflicting accounts", {"view": "products", "line": "axelera", "gen": 0}, ["Conflicting accounts", "rung:", "T2"]),
    check("sources", {"view": "sources"}, ["What this page rests on", "Cohen's kappa", "Measured recall", "Title-only threads", "Evidence tiers", "Novelty by precedence"]),
]
print(f"{sum(results)}/{len(results)} views pass")
sys.exit(0 if all(results) else 1)
