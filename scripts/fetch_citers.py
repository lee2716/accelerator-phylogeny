"""For every in-scope paper of a slice, fetch the works that cite it (OpenAlex `cites:` filter).

Output: <data>/data/citers_<slice>.jsonl, one line per paper:
  status      FETCHED | NOT_CHECKED (request failed) | NO_OPENALEX_ID
  citers      [{oa, doi, year, title, field, subfield, cited_by_count}]  (up to MAX_CITERS, most cited first)
  truncated   true when the paper has more citers than were fetched
A failed request is NOT_CHECKED, never an empty list: 'nobody followed' may only be shown for FETCHED with zero citers.
Resumable: papers already in the output file are skipped.
"""
import json, os, sys
from common import DATA, REPO, TypedFailure, get_json

OPENALEX = "https://api.openalex.org/works"
PAGE = 200
MAX_CITERS = 400  # two pages; beyond this only the count is kept and `truncated` is set


def fetch(openalex_id):
    citers, cursor = [], "*"
    while cursor and len(citers) < MAX_CITERS:
        payload = get_json(OPENALEX, {"filter": f"cites:{openalex_id}", "per-page": PAGE, "cursor": cursor,
                                      "sort": "cited_by_count:desc",
                                      "select": "id,doi,publication_year,title,primary_topic,cited_by_count"},
                           cache_name=f"cites_{openalex_id}_{len(citers)}")
        for work in payload["results"]:
            topic = work.get("primary_topic") or {}
            citers.append({"oa": work["id"].rsplit("/", 1)[-1],
                           "doi": (work.get("doi") or "").replace("https://doi.org/", "").lower(),
                           "year": work.get("publication_year"), "title": work.get("title"),
                           "field": (topic.get("field") or {}).get("display_name"),
                           "subfield": (topic.get("subfield") or {}).get("display_name"),
                           "cited_by_count": work.get("cited_by_count")})
        cursor = payload["meta"].get("next_cursor") if payload["results"] else None
    return citers, payload["meta"]["count"]


def main(slice_name):
    in_scope = {json.loads(line)["id"] for line in open(f"{REPO}/labels/{slice_name}_v1.jsonl")
                if json.loads(line)["is_ai_hardware"] != "no"}
    works = [json.loads(line) for line in open(f"{DATA}/data/works_{slice_name}.jsonl")]
    out_path = f"{DATA}/data/citers_{slice_name}.jsonl"
    done = {json.loads(line)["id"] for line in open(out_path)} if os.path.exists(out_path) else set()
    todo = [work for work in works if work["id"] in in_scope and work["id"] not in done]
    with open(out_path, "a") as out:
        for position, work in enumerate(todo, 1):
            record = {"id": work["id"], "openalex": work.get("openalex"), "cited_by_count": work.get("cited_by_count")}
            if not work.get("openalex"):
                record.update(status="NO_OPENALEX_ID", citers=[])
            else:
                try:
                    citers, total = fetch(work["openalex"])
                    record.update(status="FETCHED", citers=citers, n_total=total, truncated=total > len(citers))
                except TypedFailure as failure:
                    record.update(status="NOT_CHECKED", error=failure.kind, citers=[])
            out.write(json.dumps(record, ensure_ascii=False) + "\n")
            out.flush()
            if position % 50 == 0:
                print(f"{position}/{len(todo)}", flush=True)
    print(f"citers_{slice_name}: {len(todo)} fetched this run, {len(done)} already present")


if __name__ == "__main__":
    main(sys.argv[1])
