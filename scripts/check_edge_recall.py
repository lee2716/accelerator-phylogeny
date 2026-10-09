"""Recall of OpenAlex citation edges against full-text reference lists.

For slice papers that have full text on disk, the ground truth is: which other slice papers' titles appear in
the paper's own reference section. Recall = share of those that OpenAlex also lists in `referenced_works`.
This measures exactly the edges the lineage view draws (slice -> slice). Precision is reported too.
Papers whose text has no recognisable reference section are counted and skipped, never scored as zero.
"""
import json, random, re, sys
from common import CORPUS_INDEX, DATA

SAMPLE = 20
MIN_TITLE_CHARS = 25  # shorter normalised titles match by accident


def normalise(text):
    return re.sub(r"[^a-z0-9]", "", text.lower())


def main(slice_name):
    index = json.load(open(CORPUS_INDEX))
    works = {w["id"]: w for w in map(json.loads, open(f"{DATA}/data/works_{slice_name}.jsonl"))}
    by_openalex = {w["openalex"]: doi for doi, w in works.items() if w.get("openalex")}
    titles = {doi: normalise(index[doi]["title"]) for doi in works}
    candidates = sorted(doi for doi in works if index[doi].get("path") and works[doi].get("references"))
    random.Random(20261009).shuffle(candidates)
    scored, skipped, rows = 0, 0, []
    for doi in candidates:
        if scored == SAMPLE:
            break
        text = open(index[doi]["path"], errors="replace").read()
        cut = max(text.rfind("REFERENCES"), text.rfind("References"))
        if cut < len(text) * 0.4:
            skipped += 1
            continue
        reference_text = normalise(text[cut:])
        truth = {other for other, title in titles.items()
                 if other != doi and len(title) >= MIN_TITLE_CHARS and title in reference_text}
        openalex = {by_openalex[ref] for ref in works[doi]["references"] if ref in by_openalex}
        rows.append((doi, len(truth), len(openalex), len(truth & openalex)))
        scored += 1
    if scored < SAMPLE:
        print(f"only {scored} papers could be scored (wanted {SAMPLE})")
    truth_total = sum(r[1] for r in rows); found = sum(r[3] for r in rows); openalex_total = sum(r[2] for r in rows)
    if truth_total == 0:
        raise SystemExit("VACUOUS: no in-slice reference found in any full text; recall undefined")
    result = {"papers_scored": scored, "papers_skipped_no_reference_section": skipped,
              "edges_in_full_text": truth_total, "edges_in_openalex": openalex_total, "edges_in_both": found,
              "recall": found / truth_total, "precision_vs_title_match": found / openalex_total if openalex_total else None}
    json.dump(result, open(f"{DATA}/data/edge_recall_{slice_name}.json", "w"), indent=1)
    print(json.dumps(result, indent=1))
    print("per paper (truth, openalex, both):", [r[1:] for r in rows])


if __name__ == "__main__":
    main(sys.argv[1])
