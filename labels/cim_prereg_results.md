# In-memory slice: pre-registered hypotheses, results

Run 2026-10-09. Scope: DAC/DATE/ICCAD/ASP-DAC 2018-2025, papers whose labelled paradigm is in-memory or
near-memory computing (n = 376 of 562 in-scope papers; 848 abstracts were sent to the classifier).
Shares carry Wilson 95% intervals. Labels: `labels/cim_v1.jsonl`; agreement: `labels/cim_agreement.json`.
Evidence = the counts below. Everything said about *why* is inference and is marked so.

| Hypothesis (docs/PREREG.md) | Expected | Measured | Outcome |
|---|---|---|---|
| Q2 device base | RRAM most common 2018-2020; SRAM most common 2023-2025 | 2018-2020 (n=101): RRAM 69, not stated 8, MRAM 7, SRAM 5. 2023-2025 (n=177): RRAM 56, not stated 45, FeFET 21, SRAM 17, DRAM 14 | First half holds, second half **fails**: RRAM share fell 68% -> 32% but SRAM did not take its place |
| Q2b digital in-memory computing | share of in-memory papers rises >= 10 points | 8/101 = 8% [4-15] -> 30/177 = 17% [12-23], +9 points, intervals overlap | **Below the pre-registered threshold**; a rise is suggested, not established |
| Q3 scope | >= 60% macro or engine; < 15% cluster or larger | macro+engine 228/376 = 61% [56-65]; cluster or larger 18/376 = 5% [3-7]; `cluster_tile` 1/376 | Holds, **on an axis below the agreement threshold** (A7 kappa 0.674 < 0.70); see robustness below |
| Q4 evaluation rung | of papers stating a rung, >= 60% simulator or analytical | rung stated in 105/376 = 28% [24-33]; of those 80/105 = 76% [67-83] simulator or analytical; silicon 15 | Holds for the 28% of abstracts that state a rung; says nothing about the other 72% |

## Robustness of Q3 to the prompt (the 170 double-labelled papers)

- prompt A: CIM-paradigm papers in the 170-paper sample n=82 | macro+engine 52 (63%) | cluster or larger 4 (5%) | cluster_tile 0
- prompt B: CIM-paradigm papers in the 170-paper sample n=83 | macro+engine 44 (53%) | cluster or larger 6 (7%) | cluster_tile 0

## Other measured changes, 2018 -> 2025 (permutation p < 0.05 and >= 3 points)

- paradigm: analog in-memory computing on non-volatile memory -41 points; paradigm not stated +17; tool with no paradigm of its own +5
- device: RRAM -46; SRAM +9; device not stated +35
- workload: CNN -41; autoregressive LLM +23; encoder/vision transformer +9; training -13

The 50 late-period papers with paradigm not stated are mostly tool-scale (22) with levers non-ideality (13),
mapping (9), sparsity (8): they address in-memory computing generically without saying analog or digital.
That is a description of the labels; no cause is claimed.

## Axes that cannot be read from abstracts

- `A5_programmability`: 98% not stated; kappa 0.32. Not used for trends.
- `design_method`: 96% not stated. Kept as a tag only.
- `A6_eval_rung`: 72-74% not stated; perfect agreement on the rest because the wording is explicit.
- `A7_scale`: kappa 0.674, below threshold. Disagreement is concentrated in tool/engine versus not stated (20 of 27 cases).
