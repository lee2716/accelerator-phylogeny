"""Check one product-line source file. Usage: python3 check_sources.py <file.json>  (exit 0 only if valid)."""
import json, sys
from validate import AXES, number_problems

SOURCE_CLASSES = {"paper", "vendor_doc", "datasheet", "mlperf", "hotchips", "isscc_industry", "trade_press",
                  "analyst", "personal_blog", "forum", "conference_talk", "patent", "regulatory_filing"}
PRIMARY_CLASSES = {"paper", "vendor_doc", "datasheet", "mlperf", "hotchips", "isscc_industry", "conference_talk",
                   "patent", "regulatory_filing"}
REJECT_REASONS = {"NO_AUTHOR", "NO_MECHANISM", "UNCONDITIONED_NUMBERS", "NO_PRIMARY_LINKS", "PRESS_REWRITE",
                  "NO_ENGAGEMENT", "OFF_SCOPE", "PAYWALL", "VIDEO_ONLY", "DUPLICATE"}
VENDOR_OWN_CLASSES = {"vendor_doc", "datasheet", "hotchips", "isscc_industry", "conference_talk", "paper", "patent", "regulatory_filing"}
STATUS = {"alive", "acquired", "dead", "pivoted", "unknown"}
BET_STATUS = {"open", "paid_off", "failed", "unknown"}
MAX_QUOTES, MAX_QUOTE_WORDS = 3, 40
AXIS_VALUES = dict(AXES["single"], lever=AXES["multi"]["lever"]["values"])


def problems_in(record):
    problems = []
    for field in ("product_line", "vendor", "status", "generations", "sources", "conflicts", "not_found"):
        if field not in record:
            problems.append(f"MISSING_FIELD:{field}")
    if problems:
        return problems
    source_ids = set()
    source_class = {source.get("id"): source.get("class") for source in record["sources"]}
    for source in record["sources"]:
        tag = f"source {source.get('id')}"
        for field in ("id", "class", "url", "accessed", "tier", "summary_en", "title_original", "language"):
            if not source.get(field):
                problems.append(f"{tag}: MISSING_FIELD:{field}")
        if source.get("class") not in SOURCE_CLASSES:
            problems.append(f"{tag}: BAD_VALUE:class={source.get('class')!r}")
        if source.get("tier") not in AXES["number"]["tier"]:
            problems.append(f"{tag}: BAD_VALUE:tier={source.get('tier')!r}")
        if not isinstance(source.get("accepted"), bool):
            problems.append(f"{tag}: accepted must be true or false")
        elif not source["accepted"] and source.get("reject_reason") not in REJECT_REASONS:
            problems.append(f"{tag}: rejected without a valid reject_reason")
        elif source["accepted"] and source.get("class") not in PRIMARY_CLASSES:
            checks = source.get("checks") or {}
            if not checks.get("C2") or sum(bool(checks.get(c)) for c in ("C1", "C3", "C4", "C5", "C6")) < 3:
                problems.append(f"{tag}: accepted commentary must pass C2 and three more checks")
        quotes = source.get("quotes") or []
        if len(quotes) > MAX_QUOTES or any(len(q.split()) > MAX_QUOTE_WORDS for q in quotes):
            problems.append(f"{tag}: at most {MAX_QUOTES} quotations of at most {MAX_QUOTE_WORDS} words")
        source_ids.add(source.get("id"))
    status = record["status"]
    if status.get("value") not in STATUS:
        problems.append(f"status: BAD_VALUE:{status.get('value')!r}")
    if status.get("value") != "unknown" and status.get("source_id") not in source_ids:
        problems.append("status: a stated status needs a source_id that exists")
    if not record["generations"]:
        problems.append("NO_GENERATIONS")
    for generation in record["generations"]:
        tag = f"generation {generation.get('name')}"
        for axis, cell in (generation.get("axes") or {}).items():
            if axis not in AXIS_VALUES:
                problems.append(f"{tag}: UNKNOWN_AXIS:{axis}")
                continue
            if cell.get("basis") not in AXES["industry_only"]["basis"]:
                problems.append(f"{tag}: {axis}: BAD_VALUE:basis={cell.get('basis')!r}")
            if cell.get("basis") == "unknown":
                if cell.get("value") != "unknown":
                    problems.append(f"{tag}: {axis}: basis unknown must carry value 'unknown'")
            else:
                if cell.get("basis") == "disclosed" and source_class.get(cell.get("source_id")) not in VENDOR_OWN_CLASSES:
                    problems.append(f"{tag}: {axis}: 'disclosed' needs the vendor's own document; a press or analyst source is 'relayed'")
                if cell.get("value") not in AXIS_VALUES[axis]:
                    problems.append(f"{tag}: {axis}: BAD_VALUE:{cell.get('value')!r}")
                if cell.get("source_id") not in source_ids:
                    problems.append(f"{tag}: {axis}: source_id missing or not in this file")
        for number in generation.get("numbers") or []:
            problems += [f"{tag}: number {number.get('metric')}: {p}" for p in number_problems(number)]
            if number.get("origin_source_id") not in source_ids:
                problems.append(f"{tag}: number {number.get('metric')}: origin_source_id not in this file")
        for bet in generation.get("bets") or []:
            if bet.get("status") not in BET_STATUS or bet.get("source_id") not in source_ids or not bet.get("text"):
                problems.append(f"{tag}: bet needs text, a valid status and a source_id in this file")
    for conflict in record["conflicts"]:
        if len(conflict.get("accounts") or []) < 2:
            problems.append("conflict: needs at least two accounts")
        for number in conflict.get("accounts") or []:
            problems += [f"conflict {conflict.get('metric')}: {p}" for p in number_problems(number)]
    return problems


if __name__ == "__main__":
    found = problems_in(json.load(open(sys.argv[1])))
    for problem in found[:40]:
        print(problem)
    print(f"{sys.argv[1]}: {'OK' if not found else str(len(found)) + ' problems'}")
    sys.exit(1 if found else 0)
