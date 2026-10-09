"""Merge classifier batch files into one labels file and measure agreement between the two prompts.

Usage: python3 merge_labels.py <slice>
Outputs (publishable: DOIs and labels only, no abstracts):
  labels/<slice>_v1.jsonl          one row per paper from prompt A, stamped with provenance
  labels/<slice>_agreement.json    Cohen's kappa per axis on the papers labelled by both prompts
Every batch must pass check_batch first; a missing or failing batch stops the merge (no partial file).
"""
import glob, json, os, sys, time
from agreement import cohen_kappa, mean_jaccard
from check_batch import problems_for
from common import DATA, REPO, code_hash
from validate import AXES, label_row_problems

MODEL = "claude-opus-5-5"
GATE_KAPPA_MIN, AXIS_KAPPA_MIN = 0.80, 0.70   # docs/PREREG.md, "Thresholds fixed now"
KILL_AXES = ("A1_paradigm", "A2_data_residency")  # kill criterion K1 names these two


def load_prompt(slice_name, prompt, required_batches):
    rows = {}
    for batch_path in required_batches:
        name = os.path.basename(batch_path)
        labels_path = f"{DATA}/labels_raw/{slice_name}/{prompt}/{name}"
        if not os.path.exists(labels_path):
            raise SystemExit(f"MISSING_BATCH: {labels_path}")
        _, problems = problems_for(batch_path, labels_path)
        if problems:
            raise SystemExit(f"BATCH_FAILS_CHECK: {labels_path}: {problems[0]}")
        for line in open(labels_path):
            if line.strip():
                row = json.loads(line)
                rows[row["id"]] = row
    return rows


def main(slice_name):
    batches = sorted(glob.glob(f"{DATA}/batches/{slice_name}/batch_*.jsonl"))
    if not batches:
        raise SystemExit("NO_BATCHES")
    run_id = time.strftime("%Y%m%dT%H%M%S")
    stamp = {"model": MODEL, "run_id": run_id, "code_hash": code_hash()}
    first = load_prompt(slice_name, "a", batches)
    second = load_prompt(slice_name, "b", batches[:2])   # prompt B covers batches 000-001 (PREREG amendment)

    os.makedirs(f"{REPO}/labels", exist_ok=True)
    out_path = f"{REPO}/labels/{slice_name}_v1.jsonl"
    with open(out_path + ".tmp", "w") as out:
        for paper_id in sorted(first):
            row = dict(first[paper_id], prompt_id="label_a", double_labelled=paper_id in second, **stamp)
            problems = label_row_problems(row)
            if problems:
                raise SystemExit(f"INVALID_ROW {paper_id}: {problems[0]}")
            out.write(json.dumps(row, ensure_ascii=False) + "\n")
    os.replace(out_path + ".tmp", out_path)

    shared = sorted(set(first) & set(second))
    gate_kappa = cohen_kappa([first[i]["is_ai_hardware"] for i in shared], [second[i]["is_ai_hardware"] for i in shared])
    both_in = [i for i in shared if first[i]["is_ai_hardware"] != "no" and second[i]["is_ai_hardware"] != "no"]
    axes = {}
    for axis in AXES["single"]:
        a, b = [first[i][axis] for i in both_in], [second[i][axis] for i in both_in]
        axes[axis] = {"kappa": cohen_kappa(a, b), "raw_agreement": sum(x == y for x, y in zip(a, b)) / len(a) if a else None, "n": len(a)}
    axes["lever"] = {"mean_jaccard": mean_jaccard([first[i]["lever"] for i in both_in], [second[i]["lever"] for i in both_in]), "n": len(both_in)}
    report = {"slice": slice_name, "n_double_labelled": len(shared), "n_both_in_scope": len(both_in),
              "gate": {"kappa": gate_kappa, "raw_agreement": sum(first[i]["is_ai_hardware"] == second[i]["is_ai_hardware"] for i in shared) / len(shared)},
              "axes": axes, "thresholds": {"gate_kappa_min": GATE_KAPPA_MIN, "axis_kappa_min": AXIS_KAPPA_MIN}, **stamp}
    failed = []
    if gate_kappa is None or gate_kappa < GATE_KAPPA_MIN:
        failed.append(f"gate kappa {gate_kappa}")
    for axis in KILL_AXES:
        kappa = axes[axis]["kappa"]
        if kappa is None or kappa < AXIS_KAPPA_MIN:
            failed.append(f"{axis} kappa {kappa}")
    report["k1"] = "PASS" if not failed else "FAIL: " + "; ".join(failed)
    json.dump(report, open(f"{REPO}/labels/{slice_name}_agreement.json", "w"), indent=1)

    print(f"{slice_name}: {len(first)} papers labelled (prompt A); {len(shared)} double-labelled, {len(both_in)} in scope under both prompts")
    print(f"  gate   kappa={gate_kappa:.3f}  raw={report['gate']['raw_agreement']:.3f}  (min {GATE_KAPPA_MIN})")
    for axis, result in axes.items():
        if "kappa" in result:
            kappa = "undefined" if result["kappa"] is None else f"{result['kappa']:.3f}"
            mark = "  <- K1 axis" if axis in KILL_AXES else ""
            print(f"  {axis:22s} kappa={kappa:>9s}  raw={result['raw_agreement']:.3f}  n={result['n']}{mark}")
        else:
            print(f"  {axis:22s} mean Jaccard={result['mean_jaccard']:.3f}  n={result['n']}")
    print("  K1:", report["k1"])


if __name__ == "__main__":
    main(sys.argv[1])
