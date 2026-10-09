"""Run: python3 tests/test_agreement.py"""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "scripts"))
from agreement import cohen_kappa, mean_jaccard

assert cohen_kappa(["a", "b", "a", "b"], ["a", "b", "a", "b"]) == 1.0
assert abs(cohen_kappa(["a", "a", "b", "b"], ["a", "b", "a", "b"])) < 1e-12          # agreement exactly at chance
# worked example: 50 items, 20 yes/yes, 15 no/no, 5 yes/no, 10 no/yes -> po=0.70, pe=0.50, kappa=0.40
first = ["y"] * 20 + ["y"] * 5 + ["n"] * 10 + ["n"] * 15
second = ["y"] * 20 + ["n"] * 5 + ["y"] * 10 + ["n"] * 15
assert abs(cohen_kappa(first, second) - 0.40) < 1e-12
assert cohen_kappa([], []) is None                                                 # undefined, not 0
assert cohen_kappa(["a", "a"], ["a", "a"]) is None                                 # one category only: undefined, not 1
try:
    cohen_kappa(["a"], ["a", "b"]); raise SystemExit("length mismatch must raise")
except ValueError:
    pass
assert mean_jaccard([["x", "y"]], [["x", "y"]]) == 1.0
assert mean_jaccard([["x", "y"]], [["y", "z"]]) == 1 / 3
assert mean_jaccard([["x"], ["x", "y"]], [["z"], ["x", "y"]]) == 0.5
assert mean_jaccard([], []) is None
print("test_agreement: 10 checks passed")
