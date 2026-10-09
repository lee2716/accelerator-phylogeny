"""Run: python3 tests/test_validate.py   (plain asserts; exits non-zero on the first failure)."""
import copy, json, os, sys, tempfile
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "scripts"))
import validate

GOOD = {"id": "10.1/x", "prompt_id": "p1", "model": "m", "run_id": "r1", "code_hash": "abc", "is_ai_hardware": "yes",
        "A0_workload": "cnn", "A1_paradigm": "cim_digital", "A1_device": "sram", "A2_data_residency": "in_array_weights",
        "A3_numerics": "int8", "A4_sparsity_codesign": "none_stated", "A5_programmability": "not_stated",
        "A6_eval_rung": "simulator", "A6_baseline_class": "gpu", "A7_scale": "macro_circuit",
        "design_method": "not_stated", "lever": ["circuit_macro_design"]}
assert validate.label_row_problems(GOOD) == []

no_provenance = copy.deepcopy(GOOD); del no_provenance["prompt_id"]
assert "MISSING_FIELD:prompt_id" in validate.label_row_problems(no_provenance)

invented_value = copy.deepcopy(GOOD); invented_value["A1_paradigm"] = "quantum"
assert any(p.startswith("BAD_VALUE:A1_paradigm") for p in validate.label_row_problems(invented_value))

missing_axis = copy.deepcopy(GOOD); del missing_axis["A3_numerics"]   # a parse miss must not pass as a default
assert any(p.startswith("BAD_VALUE:A3_numerics") for p in validate.label_row_problems(missing_axis))

too_many_levers = copy.deepcopy(GOOD); too_many_levers["lever"] = ["sparsity", "security", "other", "power_thermal"]
assert any(p.startswith("BAD_MULTI:lever") for p in validate.label_row_problems(too_many_levers))

not_hardware = {"id": "10.1/y", "prompt_id": "p1", "model": "m", "run_id": "r1", "code_hash": "abc",
                "is_ai_hardware": "no", "gate_reason_if_no": "ai_for_eda"}
assert validate.label_row_problems(not_hardware) == []

NUMBER = {"metric": "perf_per_watt_ratio", "value": 3.4, "unit": "x", "rung": "projection", "tier": "T3",
          "baseline": "vendor-chosen edge module", "conditions": "8 nm projection calibrated from FPGA", "origin_source_id": "s1"}
assert validate.number_problems(NUMBER) == []
no_rung = copy.deepcopy(NUMBER); del no_rung["rung"]
assert "MISSING_FIELD:rung" in validate.number_problems(no_rung)
no_baseline_field = copy.deepcopy(NUMBER); del no_baseline_field["baseline"]
assert "MISSING_FIELD:baseline" in validate.number_problems(no_baseline_field)
null_baseline = copy.deepcopy(NUMBER); null_baseline["baseline"] = None      # 'no baseline named' is a legal, visible state
assert validate.number_problems(null_baseline) == []

with tempfile.NamedTemporaryFile("w", suffix=".jsonl", delete=False) as handle:
    for _ in range(5):
        handle.write(json.dumps(GOOD) + "\n")
assert validate.labels_file_problems(handle.name)[0].startswith("VACUOUS")

assert validate.prereg_problems() == []
edited = open(os.path.join(validate.REPO, "docs", "PREREG.md")).read().replace(">= 0.70", ">= 0.50", 1)
pinned = open(os.path.join(validate.REPO, "docs", "prereg_head.sha256")).read().strip()
assert validate.prereg_head_hash(edited) != pinned
amended = open(os.path.join(validate.REPO, "docs", "PREREG.md")).read() + "\n2026-10-10: example amendment\n"
assert validate.prereg_head_hash(amended) == pinned                          # appending below the line is allowed
print("test_validate: 13 checks passed")
