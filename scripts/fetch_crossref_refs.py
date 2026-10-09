"""Fetch the reference lists Crossref holds for every paper of the four venues.

OpenAlex reference lists are incomplete for part of this corpus (measured recall 0.63 against 50 full texts,
0.26 where the citing paper was published by ACM), so citation edges are the union of both sources.
Output: <data>/data/crossref_refs.jsonl  {doi, n_listed, ref_dois, ref_texts}  — n_listed counts all entries,
ref_dois those that carry a DOI, ref_texts the raw text of the others, cut at 500 characters (title matching needs the punctuation). A paper Crossref returns with no `reference` field is written with
n_listed = null ("no list deposited"), which is not the same as an empty list.
Volumes whose title contains a comma cannot use Crossref's exact filter and are paged by relevance with a
client-side exact match (offset paging: a cursor drops relevance ordering).
"""
import json, os, sys, time, urllib.parse, subprocess
from common import CORPUS_INDEX, DATA, REPO, TypedFailure

CROSSREF = "https://api.crossref.org/works"
SELECT = "DOI,container-title,issued,reference"
EMPTY_PAGES_TO_STOP = 3
MIN_COVERAGE = 0.98  # a volume with fewer papers than this share of the corpus count fails the fetch
MAX_REFERENCE_CHARS = 500  # one reference entry; raw text is kept because title matching needs its punctuation


def get(params):
    url = CROSSREF + "?" + urllib.parse.urlencode(params)
    for attempt in range(8):
        result = subprocess.run(["curl", "-sL", "--max-time", "180", "-A", "accel-trends/1.0", "-w", "\n%{http_code}", url],
                                capture_output=True, timeout=200)
        body, _, status = result.stdout.decode(errors="replace").rpartition("\n")
        if result.returncode == 0 and status == "200":
            time.sleep(1.2)
            return json.loads(body)["message"]
        time.sleep(6 * (attempt + 1))
    raise TypedFailure("CROSSREF_RETRIES_EXHAUSTED", url[:140])


def issued_year(item):
    return (item.get("issued", {}).get("date-parts") or [[None]])[0][0]


def exact(title, edition):
    cursor, items = "*", []
    while True:
        message = get({"filter": f"container-title:{title}", "rows": 300, "cursor": cursor, "select": SELECT})
        items += [i for i in message["items"] if issued_year(i) == edition]
        if not message["items"]:
            return items
        cursor = message["next-cursor"]


def by_relevance(titles, edition):
    """Offset paging by relevance with a client-side exact match.

    The date window is the edition year only: with a window reaching into the next year the first page was
    filled by the next edition, matched nothing, and the fetch stopped with zero papers (DATE 2024, 2026-10-09).
    Paging continues until EMPTY_PAGES_TO_STOP consecutive pages match nothing.
    """
    wanted, offset, items, empty_pages = set(titles), 0, [], 0
    while offset < 10000 and empty_pages < EMPTY_PAGES_TO_STOP:
        message = get({"query.container-title": "Design Automation Test in Europe Conference DATE",
                       "filter": f"type:proceedings-article,from-pub-date:{edition}-01-01,until-pub-date:{edition}-12-31",
                       "sort": "score", "order": "desc", "rows": 300, "offset": offset, "select": SELECT})
        if not message["items"]:
            break
        hits = [i for i in message["items"] if (i.get("container-title") or [""])[0] in wanted and issued_year(i) == edition]
        items += hits
        empty_pages = 0 if hits else empty_pages + 1
        offset += 300
    return items


def row_for(venue, edition, item):
    references = item.get("reference")
    return {"venue": venue, "edition": edition, "doi": item["DOI"].lower(),
            "n_listed": None if references is None else len(references),
            "ref_dois": sorted({r["DOI"].lower() for r in references or [] if r.get("DOI")}),
            "ref_texts": [(r.get("article-title") or r.get("unstructured") or "")[:MAX_REFERENCE_CHARS]
                          for r in references or [] if not r.get("DOI")]}


def fill_missing():
    """Fetch, one by one, every corpus DOI the volume queries did not return. Coverage then rests on the
    corpus's own DOI list rather than on how a search happened to rank its results."""
    index = json.load(open(CORPUS_INDEX))
    venue_key = {"DAC": "dac", "DATE": "date", "ICCAD": "iccad", "ASP-DAC": "aspdac"}
    out_path = f"{DATA}/data/crossref_refs.jsonl"
    have = {json.loads(line)["doi"] for line in open(out_path)}
    missing = [(doi, paper) for doi, paper in index.items() if doi not in have]
    with open(out_path, "a") as out:
        for doi, paper in missing:
            url = CROSSREF + "/" + urllib.parse.quote(doi, safe="/")
            result = subprocess.run(["curl", "-sL", "--max-time", "120", "-A", "accel-trends/1.0", "-w", "\n%{http_code}", url],
                                    capture_output=True, timeout=150)
            body, _, status = result.stdout.decode(errors="replace").rpartition("\n")
            time.sleep(1.0)
            if result.returncode != 0 or status != "200":
                print(f"MISSING_NOT_FETCHED {doi}: curl {result.returncode}, HTTP {status}", flush=True)
                continue
            out.write(json.dumps(row_for(venue_key[paper["venue"]], paper["year"], json.loads(body)["message"])) + "\n")
            out.flush()
    print(f"fill_missing: {len(missing)} corpus DOIs were absent after the volume queries", flush=True)


def coverage_shortfalls():
    """Volumes where a primary corpus DOI has no row. A fetch that ends with any is a failure."""
    index = json.load(open(CORPUS_INDEX))
    have = {json.loads(line)["doi"] for line in open(f"{DATA}/data/crossref_refs.jsonl")}
    wanted, fetched = {}, {}
    for doi, paper in index.items():
        key = (paper["venue"], paper["year"])
        wanted[key] = wanted.get(key, 0) + 1
        fetched[key] = fetched.get(key, 0) + (doi in have)
    return [(key, fetched[key], count) for key, count in sorted(wanted.items()) if fetched[key] < MIN_COVERAGE * count]


def main():
    out_path = f"{DATA}/data/crossref_refs.jsonl"
    done = {(json.loads(line)["venue"], json.loads(line)["edition"]) for line in open(out_path)} if os.path.exists(out_path) else set()
    with open(out_path, "a") as out:
        for volume in json.load(open(f"{REPO}/schema/volumes.json")):
            if (volume["venue"], volume["edition"]) in done:
                continue
            titles = volume["container_titles"]
            items = by_relevance(titles, volume["edition"]) if any("," in t for t in titles) else \
                [item for title in titles for item in exact(title, volume["edition"])]
            seen = set()
            for item in items:
                if item["DOI"].lower() in seen:
                    continue
                seen.add(item["DOI"].lower())
                out.write(json.dumps(row_for(volume["venue"], volume["edition"], item)) + "\n")
            out.flush()
            print(f"{volume['venue']} {volume['edition']}: {len(seen)} papers", flush=True)


if __name__ == "__main__":
    main()
    fill_missing()
    short = coverage_shortfalls()
    for (venue, edition), got, want in short:
        print(f"SHORT {venue} {edition}: fetched {got} of {want}")
    print("coverage:", "OK" if not short else f"FAIL ({len(short)} volumes short)")
    sys.exit(1 if short else 0)
