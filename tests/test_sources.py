"""Run: python3 tests/test_sources.py"""
import copy, os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "scripts"))
from check_sources import problems_in

VENDOR_DOC = {"id": "s1", "class": "vendor_doc", "url": "https://example.org/whitepaper", "author": "Example Corp",
              "date": "2024-01-01", "language": "en", "accessed": "2026-10-09", "title_original": "White paper",
              "summary_en": "Vendor description of the architecture.", "tier": "T3", "accepted": True,
              "reject_reason": None, "checks": None, "quotes": []}
GOOD = {"product_line": "Example", "vendor": "Example Corp", "country": "NL",
        "status": {"value": "alive", "as_of": "2026-10-09", "detail": "", "source_id": "s1"},
        "generations": [{"name": "Gen 1", "year_announced": 2023, "year_shipped": None,
                         "axes": {"A1_paradigm": {"value": "cim_digital", "basis": "disclosed", "source_id": "s1"},
                                  "A3_numerics": {"value": "unknown", "basis": "unknown", "source_id": None}},
                         "numbers": [{"metric": "efficiency", "value": 15, "unit": "TOPS/W", "rung": "projection", "tier": "T3",
                                      "baseline": None, "conditions": "vendor figure, workload not stated", "origin_source_id": "s1"}],
                         "bets": [{"text": "weights stay in the array", "status": "open", "source_id": "s1", "status_source_id": None}],
                         "what_changed_from_previous": None, "next": None}],
        "sources": [VENDOR_DOC], "conflicts": [], "not_found": ["independent measurement"]}
assert problems_in(GOOD) == [], problems_in(GOOD)

def broken(mutate):
    record = copy.deepcopy(GOOD); mutate(record); return problems_in(record)

assert any("rung" in p for p in broken(lambda r: r["generations"][0]["numbers"][0].pop("rung")))
assert any("origin_source_id" in p for p in broken(lambda r: r["generations"][0]["numbers"][0].update(origin_source_id="nope")))
assert any("source_id missing" in p for p in broken(lambda r: r["generations"][0]["axes"]["A1_paradigm"].update(source_id=None)))
assert any("basis unknown" in p for p in broken(lambda r: r["generations"][0]["axes"]["A3_numerics"].update(value="int8")))   # no filling by analogy
assert any("BAD_VALUE" in p for p in broken(lambda r: r["generations"][0]["axes"]["A1_paradigm"].update(value="quantum")))
assert any("rejected without" in p for p in broken(lambda r: r["sources"][0].update(accepted=False)))
assert any("MISSING_FIELD:accessed" in p for p in broken(lambda r: r["sources"][0].pop("accessed")))
blog = dict(VENDOR_DOC, id="s2", **{"class": "personal_blog"}, tier="T4", checks={"C1": True, "C2": False, "C3": True, "C4": True, "C5": True})
assert any("must pass C2" in p for p in broken(lambda r: r["sources"].append(blog)))                 # C2 is mandatory
assert any("quotations" in p for p in broken(lambda r: r["sources"][0].update(quotes=["a", "b", "c", "d"])))
assert any("status" in p for p in broken(lambda r: r["status"].update(source_id=None)))
assert any("two accounts" in p for p in broken(lambda r: r["conflicts"].append({"metric": "x", "accounts": []})))
press = dict(VENDOR_DOC, id="s3", **{"class": "trade_press"}, tier="T4", accepted=False, reject_reason="PRESS_REWRITE")
def relay(record):
    record["sources"].append(press); record["generations"][0]["axes"]["A1_paradigm"].update(source_id="s3")
assert any("'disclosed' needs the vendor's own document" in p for p in broken(relay))                # press cannot be 'disclosed'
def relay_marked(record):
    relay(record); record["generations"][0]["axes"]["A1_paradigm"].update(basis="relayed")
assert broken(relay_marked) == []
print("test_sources: 14 checks passed")
