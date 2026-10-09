"""Run: python3 tests/test_classify.py"""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "scripts"))
from classify import combination_stats, influence_tier, novelty_tier

peers = list(range(100))                                   # counts 0..99, one paper each
assert influence_tier(99, 2020, peers)[0] == "top_10"
assert influence_tier(90, 2020, peers)[0] == "top_10"      # 9 peers above -> 9%
assert influence_tier(89, 2020, peers)[0] == "top_25"      # 10 peers above -> exactly 10% is not top 10
assert influence_tier(75, 2020, peers)[0] == "top_25"
assert influence_tier(74, 2020, peers)[0] == "upper_half"
assert influence_tier(49, 2020, peers)[0] == "lower_half"
assert influence_tier(500, 2025, peers)[0] == "too_early"  # recent papers are never ranked, whatever the count
assert influence_tier(0, 2019, [0, 0, 0, 0])[0] == "top_10"  # ties: nobody is strictly above -> all share the top
try:
    influence_tier(1, 2020, []); raise SystemExit("empty peers must raise")
except ValueError:
    pass

def paper(year, paradigm, workload, lever):
    return {"y": year, "ax": {"A1_paradigm": paradigm, "A0_workload": workload}, "lever": [lever]}

papers = ([paper(2018, "cim_analog_nvm", "cnn", "circuit_macro_design")] * 3 +
          [paper(2021, "cim_digital", "transformer_encoder_vit", "precision_format")] +
          [paper(2022, "cim_digital", "transformer_encoder_vit", "precision_format")] * 2 +
          [paper(2024, "cim_digital", "transformer_encoder_vit", "precision_format")] * 3 +
          [paper(2023, "photonic", "snn", "security")])
stats = combination_stats(papers, last_year=2025)
assert novelty_tier(paper(2021, "cim_digital", "transformer_encoder_vit", "precision_format"), stats)[0] == "opened_line"
assert novelty_tier(paper(2022, "cim_digital", "transformer_encoder_vit", "precision_format"), stats)[0] == "early_entrant"
assert novelty_tier(paper(2024, "cim_digital", "transformer_encoder_vit", "precision_format"), stats)[0] == "follows_established"
assert novelty_tier(paper(2018, "cim_analog_nvm", "cnn", "circuit_macro_design"), stats)[0] == "predates_data"   # left-censored
assert novelty_tier(paper(2023, "photonic", "snn", "security"), stats)[0] == "singleton"
assert novelty_tier(paper(2023, "not_stated", "generic_dnn", "other"), stats)[0] == "unclassifiable"
tier, why = novelty_tier(paper(2021, "cim_digital", "transformer_encoder_vit", "precision_format"), stats)
assert why["first_year"] == 2021 and why["n"] == 6
print("test_classify: 16 checks passed")
