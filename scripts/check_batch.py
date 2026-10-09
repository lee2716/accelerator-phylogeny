"""Check one classifier output file against its input batch: same ids, every value in vocabulary.

Usage: python3 check_batch.py <batch.jsonl> <labels.jsonl>   (exit 0 only when the file is complete and valid)
"""
import json, sys
from validate import label_row_problems, PROVENANCE_FIELDS


def problems_for(batch_path, labels_path):
    wanted = [json.loads(line)["id"] for line in open(batch_path) if line.strip()]
    rows, problems = {}, []
    for number, line in enumerate(open(labels_path), 1):
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError as error:
            problems.append(f"line {number}: NOT_JSON {error}")
            continue
        rows[row.get("id")] = row
    problems += [f"MISSING_ID {paper_id}" for paper_id in wanted if paper_id not in rows]
    problems += [f"UNKNOWN_ID {paper_id}" for paper_id in rows if paper_id not in set(wanted)]
    for paper_id, row in rows.items():
        stamped = dict(row, **{field: "pending" for field in PROVENANCE_FIELDS})  # provenance is added at merge
        problems += [f"{paper_id}: {problem}" for problem in label_row_problems(stamped)]
    return wanted, problems


if __name__ == "__main__":
    wanted, problems = problems_for(sys.argv[1], sys.argv[2])
    for problem in problems[:30]:
        print(problem)
    print(f"{len(wanted)} expected, {len(problems)} problems -> {'OK' if not problems else 'FAIL'}")
    sys.exit(1 if problems else 0)
