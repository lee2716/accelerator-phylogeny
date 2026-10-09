"""Citation edges inside the corpus, citing -> cited, each with the source(s) that report it.

Three sources are merged because none is complete here:
  openalex        OpenAlex `referenced_works` of slice papers and its `cites:` lists
  crossref        Crossref reference entries that carry a DOI
  crossref-title  Crossref reference entries without a DOI whose text contains a slice paper's title
Only edges whose cited paper is in the slice are built (the lineage view asks "who followed this paper").
A title that is a prefix of a longer title matches both; such edges are rare and kept, flagged by source.
"""
import json, os
from common import CORPUS_INDEX, DATA
from titlematch import TitleIndex


def load_jsonl(path):
    return [json.loads(line) for line in open(path) if line.strip()]


def build(slice_name, sources=("openalex", "crossref", "crossref-title")):
    index = json.load(open(CORPUS_INDEX))
    primary = {alt: doi for doi, paper in index.items() for alt in paper.get("alt_dois", [])}
    resolve = lambda doi: doi if doi in index else primary.get(doi)
    works = {w["id"]: w for w in load_jsonl(f"{DATA}/data/works_{slice_name}.jsonl")}
    by_openalex = {w["openalex"]: doi for doi, w in works.items() if w.get("openalex")}
    edges = {}

    def add(citing, cited, source):
        if citing and cited and citing != cited and index[citing]["year"] >= index[cited]["year"]:
            edges.setdefault((citing, cited), set()).add(source)

    if "openalex" in sources:
        for doi, work in works.items():
            for reference in work.get("references") or []:
                add(doi, by_openalex.get(reference), "openalex")
        citers_path = f"{DATA}/data/citers_{slice_name}.jsonl"
        if os.path.exists(citers_path):
            for record in load_jsonl(citers_path):
                for citer in record["citers"]:
                    add(resolve(citer["doi"]), record["id"], "openalex")
    crossref_path = f"{DATA}/data/crossref_refs.jsonl"
    crossref_rows = load_jsonl(crossref_path) if os.path.exists(crossref_path) else []
    titles = TitleIndex({doi: index[doi]["title"] for doi in works})
    for row in crossref_rows:
        citing = resolve(row["doi"])
        if "crossref" in sources:
            for reference in row["ref_dois"]:
                cited = resolve(reference)
                if cited in works:
                    add(citing, cited, "crossref")
        if "crossref-title" in sources:
            for text in row.get("ref_texts", []):
                for cited in titles.find(text):
                    add(citing, cited, "crossref-title")
    return edges, {"crossref_papers_read": len(crossref_rows)}
