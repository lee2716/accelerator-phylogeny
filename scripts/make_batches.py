"""Split a slice into batch files for the classifier. Year and venue are withheld so a label cannot
be conditioned on them. Batches are written once: an existing batch directory is never regenerated,
because batch membership is part of each label's provenance.
"""
import json, os, random, sys
from common import DATA

BATCH_SIZE = 85  # one classifier call reads this many abstracts (~30k tokens) and stays attentive


def main(slice_name, exclude_slice=None):
    papers = [json.loads(line) for line in open(f"{DATA}/data/slice_{slice_name}.jsonl")]
    if exclude_slice:
        seen = {json.loads(line)["id"] for line in open(f"{DATA}/data/slice_{exclude_slice}.jsonl")}
        papers = [paper for paper in papers if paper["id"] not in seen]
    out_dir = f"{DATA}/batches/{slice_name}"
    if os.path.exists(out_dir):
        raise SystemExit(f"BATCHES_EXIST: {out_dir} (delete it deliberately to re-split)")
    os.makedirs(out_dir)
    random.Random(20261009).shuffle(papers)  # mix years inside a batch so drift across batches is not a year effect
    for start in range(0, len(papers), BATCH_SIZE):
        with open(f"{out_dir}/batch_{start // BATCH_SIZE:03d}.jsonl", "w") as out:
            for paper in papers[start:start + BATCH_SIZE]:
                out.write(json.dumps({"id": paper["id"], "title": paper["title"], "abstract": paper["abstract"]},
                                     ensure_ascii=False) + "\n")
    print(f"{slice_name}: {len(papers)} papers in {-(-len(papers) // BATCH_SIZE)} batches under {out_dir}")


if __name__ == "__main__":
    main(*sys.argv[1:])
