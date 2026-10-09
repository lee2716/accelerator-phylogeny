"""Build the share tables from a labels file. Shares of an arm-year only; counts appear as n.

Usage: python3 trends.py <slice>
Output: labels/<slice>_tables.json  (per-year shares with Wilson intervals, per-period profiles of each
direction, permutation tests) — DOIs and labels only, publishable.
2026 is partial (two of four venues) and never enters a test.
"""
import json, random, sys
from collections import Counter, defaultdict
from common import CORPUS_INDEX, REPO, code_hash, wilson
from validate import AXES

LAST_FULL_YEAR = 2025
PERIODS = {"2018-2020": (2018, 2020), "2021-2023": (2021, 2023), "2024-2025": (2024, 2025)}
TREND_AXES = ["A0_workload", "A1_paradigm", "A1_device", "A2_data_residency", "A3_numerics", "A4_sparsity_codesign",
              "A6_eval_rung", "A6_baseline_class", "A7_scale"]
PERMUTATIONS = 1000
MIN_CHANGE = 0.03  # 3 share points: with ~60-150 in-scope papers a year, less is one or two papers


def load(slice_name):
    index = json.load(open(CORPUS_INDEX))
    papers = []
    for line in open(f"{REPO}/labels/{slice_name}_v1.jsonl"):
        row = json.loads(line)
        if row["is_ai_hardware"] == "no":
            continue
        meta = index[row["id"]]
        papers.append(dict(row, year=meta["year"], venue=meta["venue"]))
    if len(papers) < 100:
        raise SystemExit(f"VACUOUS: only {len(papers)} in-scope papers")
    return papers


def values_of(paper, axis):
    return paper[axis] if axis == "lever" else [paper[axis]]


def share_series(papers, axis):
    by_year = defaultdict(list)
    for paper in papers:
        by_year[paper["year"]].append(paper)
    vocabulary = AXES["multi"]["lever"]["values"] if axis == "lever" else AXES["single"][axis]
    series = {}
    for value in vocabulary:
        points = []
        for year in sorted(by_year):
            total = len(by_year[year])
            hits = sum(value in values_of(paper, axis) for paper in by_year[year])
            low, high = wilson(hits, total)
            points.append({"year": year, "n": total, "k": hits, "share": hits / total, "lo": low, "hi": high,
                           "partial": year > LAST_FULL_YEAR})
        if any(point["k"] for point in points):
            series[value] = points
    return series


def slope(years, shares):
    mean_x, mean_y = sum(years) / len(years), sum(shares) / len(shares)
    return sum((x - mean_x) * (y - mean_y) for x, y in zip(years, shares)) / sum((x - mean_x) ** 2 for x in years)


def trend_test(points, rng):
    """Permutation test on the slope of share over full years; returns direction only when both
    pre-registered conditions hold (p < 0.05 and |change| >= 3 points between first and last full year)."""
    full = [point for point in points if not point["partial"]]
    years, shares = [p["year"] for p in full], [p["share"] for p in full]
    observed = slope(years, shares)
    shuffled, extreme = shares[:], 0
    for _ in range(PERMUTATIONS):
        rng.shuffle(shuffled)
        if abs(slope(years, shuffled)) >= abs(observed):
            extreme += 1
    p_value = extreme / PERMUTATIONS
    change = shares[-1] - shares[0]
    direction = "flat_or_noise"
    if p_value < 0.05 and abs(change) >= MIN_CHANGE:
        direction = "rising" if observed > 0 else "falling"
    return {"slope_per_year": observed, "p": p_value, "change_first_to_last": change, "direction": direction}


def profile(papers, axis):
    total = len(papers)
    counts = Counter(value for paper in papers for value in values_of(paper, axis))
    rows = []
    for value, hits in counts.most_common():
        low, high = wilson(hits, total)
        rows.append({"value": value, "k": hits, "share": hits / total, "lo": low, "hi": high})
    return {"n": total, "rows": rows}


def main(slice_name):
    papers = load(slice_name)
    rng = random.Random(20261009)
    tables = {"slice": slice_name, "n_in_scope": len(papers), "code_hash": code_hash(),
              "n_per_year": dict(sorted(Counter(p["year"] for p in papers).items())), "series": {}, "tests": {}, "directions": {}}
    for axis in TREND_AXES + ["lever"]:
        tables["series"][axis] = share_series(papers, axis)
        tables["tests"][axis] = {value: trend_test(points, rng) for value, points in tables["series"][axis].items()}
    for direction_axis in ("A1_paradigm", "A0_workload"):
        for value in tables["series"][direction_axis]:
            members = [p for p in papers if p[direction_axis] == value and p["year"] <= LAST_FULL_YEAR]
            if len(members) < 10:
                continue
            tables["directions"][f"{direction_axis}={value}"] = {
                period: {axis: profile([p for p in members if low <= p["year"] <= high], axis)
                         for axis in TREND_AXES + ["lever"] if axis != direction_axis}
                for period, (low, high) in PERIODS.items()}
    json.dump(tables, open(f"{REPO}/labels/{slice_name}_tables.json", "w"), indent=1)
    print(f"{slice_name}: {len(papers)} in-scope papers; per year {tables['n_per_year']}")
    for axis in ("A1_paradigm", "A0_workload", "A1_device"):
        moving = {v: t for v, t in tables["tests"][axis].items() if t["direction"] != "flat_or_noise"}
        print(f"  {axis}: " + (", ".join(f"{v} {t['direction']} ({t['change_first_to_last']*100:+.0f} pts, p={t['p']:.3f})" for v, t in moving.items()) or "nothing passes the test"))


if __name__ == "__main__":
    main(sys.argv[1])
