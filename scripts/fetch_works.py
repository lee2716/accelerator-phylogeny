"""Fetch OpenAlex records for a slice: id, references, topics, citation count. 50 DOIs per request, cached.

Output: <data>/data/works_<slice>.jsonl (one line per DOI found) and a printed coverage line.
A DOI that OpenAlex does not return is written as {"id": doi, "openalex": null}: 'not found' is a state,
never silently dropped and never read as 'zero references'.
"""
import hashlib, json, os, sys
from common import DATA, get_json

OPENALEX = "https://api.openalex.org/works"
FIELDS = "id,doi,publication_year,referenced_works,cited_by_count,primary_topic,topics"
PER_REQUEST = 50


def main(slice_name):
    dois = [json.loads(line)["id"] for line in open(f"{DATA}/data/slice_{slice_name}.jsonl")]
    found = {}
    for start in range(0, len(dois), PER_REQUEST):
        chunk = dois[start:start + PER_REQUEST]
        cache = "works_" + hashlib.sha256("|".join(chunk).encode()).hexdigest()[:16]
        payload = get_json(OPENALEX, {"filter": "doi:" + "|".join(chunk), "per-page": PER_REQUEST, "select": FIELDS},
                           cache_name=cache)
        for work in payload["results"]:
            doi = (work.get("doi") or "").replace("https://doi.org/", "").lower()
            if doi:
                found[doi] = work
        print(f"{min(start + PER_REQUEST, len(dois))}/{len(dois)}", flush=True)
    with open(f"{DATA}/data/works_{slice_name}.jsonl.tmp", "w") as out:
        for doi in dois:
            work = found.get(doi.lower())
            if work is None:
                out.write(json.dumps({"id": doi, "openalex": None}) + "\n")
                continue
            topic = work.get("primary_topic") or {}
            out.write(json.dumps({
                "id": doi, "openalex": work["id"].rsplit("/", 1)[-1], "year": work.get("publication_year"),
                "cited_by_count": work["cited_by_count"], "references": [r.rsplit("/", 1)[-1] for r in work.get("referenced_works") or []],
                "topic": topic.get("display_name"), "subfield": (topic.get("subfield") or {}).get("display_name"),
                "field": (topic.get("field") or {}).get("display_name"),
            }) + "\n")
    os.replace(f"{DATA}/data/works_{slice_name}.jsonl.tmp", f"{DATA}/data/works_{slice_name}.jsonl")
    missing = sum(1 for doi in dois if doi.lower() not in found)
    no_refs = sum(1 for work in found.values() if not work.get("referenced_works"))
    print(f"works_{slice_name}: {len(dois)} DOIs, {len(found)} found, {missing} not found, {no_refs} found with an empty reference list")


if __name__ == "__main__":
    main(sys.argv[1])
