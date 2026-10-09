"""Two derived classifications: influence (citation rank inside venue-year) and novelty by precedence.

Pure functions. Definitions are fixed in docs/PREREG.md (amendment of 2026-10-09).
"""
FIRST_DATA_YEAR = 2018
TOO_EARLY_FROM = 2025      # citation counts of the last two editions are near zero for everyone
MIN_LINE_SIZE = 5          # a combination counts as a line that grew from this many papers
MAX_SINGLETON = 2
IGNORED = {"not_stated", "other", "generic_dnn", "target_generic", "none_stated", "none"}
NOVELTY_ORDER = ["opened_line", "early_entrant", "singleton", "follows_established", "predates_data", "unclassifiable"]
INFLUENCE_ORDER = ["top_10", "top_25", "upper_half", "lower_half", "too_early"]


def influence_tier(count, year, peer_counts):
    """peer_counts: citation counts of every paper of the same venue and year, the paper itself included."""
    if year >= TOO_EARLY_FROM:
        return "too_early", None
    if not peer_counts:
        raise ValueError("no peers: a paper is always its own peer")
    better = sum(1 for other in peer_counts if other > count)
    rank_fraction = better / len(peer_counts)          # share of peers strictly more cited
    if rank_fraction < 0.10:
        return "top_10", rank_fraction
    if rank_fraction < 0.25:
        return "top_25", rank_fraction
    if rank_fraction < 0.50:
        return "upper_half", rank_fraction
    return "lower_half", rank_fraction


def combinations_of(paper):
    """paper: {"ax": {...}, "lever": [...]}. Returns the usable (name, a, b) combinations."""
    paradigm = paper["ax"]["A1_paradigm"]
    pairs = [("paradigm × workload", paradigm, paper["ax"]["A0_workload"]),
             ("paradigm × lever", paradigm, paper["lever"][0])]
    return [pair for pair in pairs if pair[1] not in IGNORED and pair[2] not in IGNORED]


def combination_stats(papers, last_year):
    """First year and size of every combination among papers up to last_year."""
    stats = {}
    for paper in papers:
        if paper["y"] > last_year:
            continue
        for combination in combinations_of(paper):
            entry = stats.setdefault(combination, {"first_year": paper["y"], "n": 0})
            entry["first_year"] = min(entry["first_year"], paper["y"])
            entry["n"] += 1
    return stats


def novelty_tier(paper, stats):
    """Strongest tier over the paper's combinations, with the combination that gave it."""
    best = None
    for combination in combinations_of(paper):
        entry = stats.get(combination)
        if entry is None:                      # paper after last_year whose combination never appeared before
            tier = "singleton"
            entry = {"first_year": paper["y"], "n": 0}
        elif entry["first_year"] == FIRST_DATA_YEAR:
            tier = "predates_data"
        elif entry["n"] <= MAX_SINGLETON:
            tier = "singleton"
        elif entry["n"] >= MIN_LINE_SIZE and paper["y"] == entry["first_year"]:
            tier = "opened_line"
        elif entry["n"] >= MIN_LINE_SIZE and paper["y"] <= entry["first_year"] + 1:
            tier = "early_entrant"
        else:
            tier = "follows_established"
        candidate = (NOVELTY_ORDER.index(tier), tier, combination, entry)
        if best is None or candidate[0] < best[0]:
            best = candidate
    if best is None:
        return "unclassifiable", None
    _, tier, combination, entry = best
    return tier, {"kind": combination[0], "a": combination[1], "b": combination[2],
                  "first_year": entry["first_year"], "n": entry["n"]}
