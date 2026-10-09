"""Assemble web/data.js from labels, citation edges and industry source files. Fails closed.

Usage: python3 build_page.py <slice>
The page reads one global, ACCEL_DATA. Only publishable material goes in: DOIs, titles, years, venues,
labels, citation edges, and the collector's own summaries of web sources. No abstracts, no article text.

Validity ladder (each failure is typed and stops the build):
  1. every label row passes the schema;  2. every paper has a DOI link;
  3. citation conservation: OpenAlex in-corpus citers + outside citers == citers fetched <= reported total;
  4. every industry file passes check_sources;  5. the output is non-trivial (vacuity guard).
A paper whose citers were not fetched is NOT_CHECKED; it is never shown as having no followers.
"""
import glob, json, os, sys, time
from collections import Counter
import classify
import edges as edge_builder
from check_sources import problems_in
from common import CORPUS_INDEX, DATA, REPO, TypedFailure, code_hash
from validate import AXES, label_row_problems

TOP_OUTSIDE = 5
MIN_PAPERS = 100


def load_jsonl(path):
    return [json.loads(line) for line in open(path) if line.strip()]


def main(slice_name):
    index = json.load(open(CORPUS_INDEX))
    primary = {alt: doi for doi, paper in index.items() for alt in paper.get("alt_dois", [])}
    resolve = lambda doi: doi if doi in index else primary.get(doi)

    labels = {row["id"]: row for row in load_jsonl(f"{REPO}/labels/{slice_name}_v1.jsonl")}
    for row in labels.values():
        problems = label_row_problems(row)
        if problems:
            raise TypedFailure("INVALID_LABEL_ROW", f"{row['id']}: {problems[0]}")
    in_scope = {doi for doi, row in labels.items() if row["is_ai_hardware"] != "no"}
    works = {w["id"]: w for w in load_jsonl(f"{DATA}/data/works_{slice_name}.jsonl")}
    citers = {c["id"]: c for c in load_jsonl(f"{DATA}/data/citers_{slice_name}.jsonl")}

    edges, edge_info = edge_builder.build(slice_name)
    followers, references_in = {}, {}
    for (citing, cited), sources in edges.items():
        followers.setdefault(cited, []).append((citing, sorted(sources)))
        references_in.setdefault(citing, []).append((cited, sorted(sources)))

    # influence mark: rank of the citation count among all corpus papers of the same venue and year
    peers = {}
    for paper in index.values():
        peers.setdefault((paper["venue"], paper["year"]), []).append(paper.get("cited_by_count") or 0)

    def influence(doi):
        paper = index[doi]
        tier, fraction = classify.influence_tier(paper.get("cited_by_count") or 0, paper["year"], peers[(paper["venue"], paper["year"])])
        return {"tier": tier, "cites": paper.get("cited_by_count") or 0, "above": fraction,
                "peers": len(peers[(paper["venue"], paper["year"])])}

    def brief(doi):
        paper = index[doi]
        return {"id": doi, "t": paper["title"], "y": paper["year"], "v": paper["venue"], "in_slice": doi in in_scope,
                "inf": influence(doi)}

    papers = []
    for doi in sorted(in_scope):
        row, meta, work, record = labels[doi], index[doi], works[doi], citers.get(doi)
        if not doi.startswith("10."):
            raise TypedFailure("NO_SOURCE_LINK", doi)
        node = {"id": doi, "t": meta["title"], "y": meta["year"], "v": meta["venue"],
                "au": (meta.get("authors") or [""])[0], "gate": row["is_ai_hardware"], "dbl": row.get("double_labelled", False),
                "ax": {axis: row[axis] for axis in AXES["single"]}, "lever": row["lever"],
                "refs": [dict(brief(cited), src=src) for cited, src in sorted(references_in.get(doi, []), key=lambda e: index[e[0]]["year"])],
                "fol": [dict(brief(citing), src=src) for citing, src in sorted(followers.get(doi, []), key=lambda e: index[e[0]]["year"])]}
        node["inf"] = influence(doi)
        if record is None or record["status"] != "FETCHED":
            node["cit"] = {"status": "NOT_CHECKED"}
        else:
            outside = [c for c in record["citers"] if resolve(c["doi"]) is None]
            inside = len(record["citers"]) - len(outside)
            if inside + len(outside) != len(record["citers"]) or len(record["citers"]) > record["n_total"]:
                raise TypedFailure("EDGE_CONSERVATION_FAIL", doi)
            fields = Counter(c["field"] or "unknown field" for c in outside)
            node["cit"] = {"status": "FETCHED", "total": record["n_total"], "fetched": len(record["citers"]),
                           "truncated": record["truncated"], "outside_n": len(outside), "outside_fields": dict(fields.most_common(6)),
                           "outside_top": [{"t": c["title"], "y": c["year"], "doi": c["doi"], "c": c["cited_by_count"], "f": c["subfield"]}
                                           for c in outside[:TOP_OUTSIDE]]}
        papers.append(node)
    if len(papers) < MIN_PAPERS:
        raise TypedFailure("VACUOUS", f"{len(papers)} papers")
    # novelty-by-precedence mark, from label combinations inside the slice through the last full year
    stats = classify.combination_stats(papers, last_year=2025)
    for node in papers:
        tier, why = classify.novelty_tier(node, stats)
        node["nov"] = {"tier": tier, "why": why}

    industry = []
    for path in sorted(glob.glob(f"{REPO}/sources/industry/*.json")):
        record = json.load(open(path))
        problems = problems_in(record)
        if problems:
            raise TypedFailure("INVALID_SOURCE_FILE", f"{os.path.basename(path)}: {problems[0]}")
        record["slug"] = os.path.basename(path)[:-5]
        industry.append(record)

    recall_path = f"{DATA}/data/edge_recall_{slice_name}.json"
    recall = json.load(open(recall_path)) if os.path.exists(recall_path) else None
    if recall:
        recall = {k: v for k, v in recall.items() if k != "rows"}
    edge_sources = Counter("+".join(sorted(s)) for s in edges.values())
    data = {
        "meta": {"built": time.strftime("%Y-%m-%d %H:%M"), "code_hash": code_hash(), "slice": slice_name,
                 "n_sent_to_classifier": len(labels), "n_in_scope": len(papers),
                 "n_borderline": sum(p["gate"] == "borderline" for p in papers),
                 "venues": "DAC, DATE, ICCAD, ASP-DAC", "years": "2018-2026 (2026 partial: DATE and ASP-DAC only)",
                 "edges": {"n": len(edges), "by_source": dict(edge_sources), **edge_info},
                 "citers_not_checked": sum(p["cit"]["status"] != "FETCHED" for p in papers), "edge_recall": recall,
                 "gold_set": "none: classifier checked against itself only (two independently worded prompts)",
                 "marks": {"influence": dict(Counter(p["inf"]["tier"] for p in papers)),
                           "novelty": dict(Counter(p["nov"]["tier"] for p in papers)),
                           "citation_counts_as_of": "2026-09-17 (OpenAlex snapshot in the corpus index)"}},
        "axes": AXES, "agreement": json.load(open(f"{REPO}/labels/{slice_name}_agreement.json")),
        "tables": json.load(open(f"{REPO}/labels/{slice_name}_tables.json")),
        "papers": papers, "industry": industry,
    }
    os.makedirs(f"{REPO}/web", exist_ok=True)
    with open(f"{REPO}/web/data.js.tmp", "w") as out:
        out.write("// generated by scripts/build_page.py — do not edit\nwindow.ACCEL_DATA = ")
        json.dump(data, out, ensure_ascii=False, separators=(",", ":"))
        out.write(";\n")
    os.replace(f"{REPO}/web/data.js.tmp", f"{REPO}/web/data.js")
    with_followers = sum(bool(p["fol"]) for p in papers)
    print(f"data.js: {len(papers)} papers, {len(edges)} in-corpus edges {dict(edge_sources)}, "
          f"{with_followers} papers with an in-corpus follower, {data['meta']['citers_not_checked']} not checked, "
          f"{len(industry)} product lines, {os.path.getsize(f'{REPO}/web/data.js') / 1e6:.1f} MB")


if __name__ == "__main__":
    try:
        main(sys.argv[1])
    except TypedFailure as failure:
        print(f"BUILD REFUSED — {failure}")
        sys.exit(1)
