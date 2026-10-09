"""Schema checks. Pure functions return a list of typed problems; an empty list means valid.

Nothing here coerces: a value outside its vocabulary is a problem, never mapped to 'other'.
"""
import hashlib, json, os, sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
AXES = json.load(open(os.path.join(REPO, "schema", "axes.json")))
MIN_LABEL_ROWS = 100  # fewer rows than this in a labels file is a vacuous pass, not a pass
PROVENANCE_FIELDS = ("prompt_id", "model", "run_id", "code_hash")
NUMBER_REQUIRED = ("metric", "value", "unit", "rung", "tier", "baseline", "conditions", "origin_source_id")


def label_row_problems(row):
    problems = []
    for field in ("id",) + PROVENANCE_FIELDS:
        if not row.get(field):
            problems.append(f"MISSING_FIELD:{field}")
    gate = row.get("is_ai_hardware")
    if gate not in AXES["gate"]["is_ai_hardware"]:
        return problems + [f"BAD_VALUE:is_ai_hardware={gate!r}"]
    if gate == "no":
        if row.get("gate_reason_if_no") not in AXES["gate"]["gate_reason_if_no"]:
            problems.append(f"BAD_VALUE:gate_reason_if_no={row.get('gate_reason_if_no')!r}")
        return problems
    for axis, vocabulary in AXES["single"].items():
        if row.get(axis) not in vocabulary:
            problems.append(f"BAD_VALUE:{axis}={row.get(axis)!r}")
    for axis, spec in AXES["multi"].items():
        values = row.get(axis)
        if not isinstance(values, list) or not values or len(values) > spec["max"]:
            problems.append(f"BAD_MULTI:{axis}={values!r}")
        elif any(value not in spec["values"] for value in values):
            problems.append(f"BAD_VALUE:{axis}={values!r}")
    return problems


def number_problems(number):
    """A hardware number without its rung, tier and baseline field is refused (baseline may be null: 'none named')."""
    problems = [f"MISSING_FIELD:{field}" for field in NUMBER_REQUIRED if field not in number]
    if number.get("rung") not in AXES["number"]["rung"]:
        problems.append(f"BAD_VALUE:rung={number.get('rung')!r}")
    if number.get("tier") not in AXES["number"]["tier"]:
        problems.append(f"BAD_VALUE:tier={number.get('tier')!r}")
    return problems


def labels_file_problems(path):
    rows = [json.loads(line) for line in open(path) if line.strip()]
    if len(rows) < MIN_LABEL_ROWS:
        return [f"VACUOUS:{len(rows)} rows < {MIN_LABEL_ROWS}"]
    problems = []
    for row in rows:
        problems += [f"{row.get('id')}: {problem}" for problem in label_row_problems(row)]
    return problems


def prereg_head_hash(text):
    head = text.split("\n## Amendments", 1)[0]
    return hashlib.sha256(head.encode()).hexdigest()


def prereg_problems():
    text = open(os.path.join(REPO, "docs", "PREREG.md")).read()
    pinned = open(os.path.join(REPO, "docs", "prereg_head.sha256")).read().strip()
    return [] if prereg_head_hash(text) == pinned else ["PREREG_EDITED: text above '## Amendments' changed"]


if __name__ == "__main__":
    what = sys.argv[1]
    found = prereg_problems() if what == "prereg" else labels_file_problems(sys.argv[2])
    for problem in found[:40]:
        print(problem)
    print(f"{what}: {'OK' if not found else str(len(found)) + ' problems'}")
    sys.exit(1 if found else 0)
