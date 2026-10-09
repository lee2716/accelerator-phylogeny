"""Select the abstracts to label. Word-bounded regexes only: substring matching counted 'NPU' 835 times
in this corpus where the word occurs 25 times.

Output (private, holds abstracts): <data>/data/slice_<name>.jsonl, one paper per line.
The regex decides only what is sent to the classifier; the classifier's relevance gate decides membership.
"""
import json, os, re, sys
from collections import Counter
from common import CORPUS_INDEX, DATA

AI_TERMS = (r"neural|DNNs?|CNNs?|deep learning|transformers?|LLMs?|large language|machine learning|inference|"
            r"in-memory|compute-in-memory|processing-in-memory|CIM|PIM")
HW_TERMS = (r"accelerat\w*|architectures?|hardware|processors?|chips?|SoCs?|FPGAs?|ASICs?|systolic|dataflow|"
            r"NPUs?|TPUs?|PE array|cores?")
CIM_TERMS = (r"in-memory comput\w*|comput\w*-in-memory|process\w*-in-memory|in-memory process\w*|logic-in-memory|"
             r"CIM|PIM|IMC|near-memory|memristor\w*|memristive|crossbars?|RRAM|ReRAM|FeFETs?|PCM|"
             r"phase-change memor\w*|resistive (?:RAM|memor\w*)")

SLICES = {
    "ai_hw": lambda text: bool(re.search(rf"\b(?:{AI_TERMS})\b", text, re.I)) and bool(re.search(rf"\b(?:{HW_TERMS})\b", text, re.I)),
    "cim": lambda text: bool(re.search(rf"\b(?:{CIM_TERMS})\b", text)),  # case-sensitive: 'pim'/'cim' are not words
}


def main(name):
    index = json.load(open(CORPUS_INDEX))
    chosen, skipped_no_abstract = [], 0
    for paper in index.values():
        text = f"{paper['title']}. {paper.get('abstract') or ''}"
        if not SLICES[name](text):
            continue
        if not paper.get("abstract"):
            skipped_no_abstract += 1
            continue
        chosen.append({"id": paper["doi"], "venue": paper["venue"], "year": paper["year"],
                       "title": paper["title"], "abstract": paper["abstract"]})
    if not chosen:
        raise SystemExit("EMPTY_SLICE: the regex matched nothing; refusing to write an empty file")
    chosen.sort(key=lambda p: (p["year"], p["venue"], p["id"]))
    os.makedirs(f"{DATA}/data", exist_ok=True)
    with open(f"{DATA}/data/slice_{name}.jsonl", "w") as out:
        for paper in chosen:
            out.write(json.dumps(paper, ensure_ascii=False) + "\n")
    per_year = Counter(p["year"] for p in chosen)
    print(f"slice {name}: {len(chosen)} papers with abstracts ({skipped_no_abstract} matched but have no abstract)")
    print("  per year:", dict(sorted(per_year.items())))
    print("  per venue:", dict(Counter(p["venue"] for p in chosen)))


if __name__ == "__main__":
    main(sys.argv[1])
