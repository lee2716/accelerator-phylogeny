# Accelerator Phylogeny — execution plan and status

This file is the working plan: what is done, what runs next, and how to resume after a stop.
The contract (thresholds, hypotheses, kill criteria) is `docs/PREREG.md`; this file never overrides it.
Paths written `<data>/…` are under `data_dir` in `config.local.json` (private material, not in the repository).

## Rules for running

- **At most 3 agent calls in parallel.** Every call writes one file; a stopped run loses at most the calls in flight.
- **Everything is resumable from files.** A step is skipped when its output file exists and passes its check. Nothing is kept only in a conversation.
- **Cheapest check first.** Each phase ends with a verifier; a failed verifier stops the phase and is written into the status table, it is not worked around.
- **Budgets are caps** (`<data>/data/budget.json`): agent calls 480, API calls 6000, web searches 200.
- Classifier prompt B (the independent second wording) is applied to batches 000–001 of each slice only; agreement is reported with its n.
- **Nothing reaches the page without a checkable source.** Every paper node carries its DOI link; every product or post node carries URL, author, date and access date; every number carries its evidence tier (peer-reviewed / independent measurement / vendor claim / commentary) and its rung. The page build fails when a node has no source link or a number has no tier. The page has a Sources view listing every source used, every rejected candidate with its reason, and every coverage row still "not found".

## Status

Legend: ✅ done and verified · 🔄 running · ⬜ not started · ⛔ stopped by a kill criterion

| # | Step | Output | Verifier | Status |
|---|---|---|---|---|
| P0.1 | Axis vocabulary | `schema/axes.json` | loaded by `scripts/validate.py` | ✅ |
| P0.2 | Pre-registration | `docs/PREREG.md`, `docs/prereg_head.sha256` | `python3 scripts/validate.py prereg` | ✅ |
| P0.3 | Validator and tests | `scripts/validate.py`, `tests/test_validate.py` | `python3 tests/test_validate.py` (13 checks) | ✅ |
| P1.1 | Select slices | `<data>/data/slice_cim.jsonl` (848), `slice_ai_hw.jsonl` (2672) | printed per-year counts; empty slice refuses to write | ✅ |
| P1.2 | Batches for the in-memory slice | `<data>/batches/cim/batch_000…009.jsonl` | 10 files, 848 ids | ✅ |
| P1.3 | Label, prompt A, batches 000–009 | `<data>/labels_raw/cim/a/batch_NNN.jsonl` | `scripts/check_batch.py` per file | ✅ 848 papers |
| P1.4 | Label, prompt B, batches 000–001 | `<data>/labels_raw/cim/b/batch_NNN.jsonl` | `scripts/check_batch.py` per file | ✅ 170 papers |
| P1.5 | Merge labels, agreement, trend tables | `labels/cim_v1.jsonl`, `labels/cim_agreement.json`, `labels/cim_tables.json`, `labels/cim_prereg_results.md` | Cohen's kappa: gate ≥ 0.80, A1/A2 ≥ 0.70 → else kill criterion K1 | ✅ K1 PASS (gate 0.813, A1 0.902, A2 0.860). A7 0.674 below threshold; A5 unreadable from abstracts |
| P1.6 | Citation edges inside the corpus, three sources merged (`scripts/edges.py`) | `<data>/data/works_cim.jsonl`, `citers_cim.jsonl`, `crossref_refs.jsonl`, `edge_recall_cim.json` | recall vs 50 full-text reference sections ≥ 0.80; fetch fails if any volume is < 98% covered | ✅ 1659 edges; recall 0.96 (OpenAlex alone 0.65; ACM-published citing papers 0.28 → 0.94); 16/16 title-only edges confirmed in the citing PDF |
| P1.7 | 9 industry product lines, in-memory computing (brief: `prompts/industry_brief.md`, format: `docs/SOURCES.md`) | `sources/industry/*.json` | `python3 scripts/check_sources.py <file>` | ✅ 9/9 pass. No peer-reviewed primary source could be opened for most lines (IEEE Xplore returns empty pages); those facts are under `not_found` |
| P1.8 | Interactive page (redesigned 2026-10-09 as a river tree with a launch-style hero; measured layout probe: `web/index.html?probe`) | `web/index.html`, `web/app.js`, `web/data.js` (generated) | `python3 scripts/build_page.py cim` refuses invalid data; `python3 tests/test_page.py` loads every view in headless Chrome (run outside a sandbox: Chrome needs a local socket) | ✅ 13/13 view checks. Layout was checked as text only, not by eye |
| P2 | Widen to the AI-hardware slice, arm A, cross-field | see `docs/PREREG.md` | positive control (transformer up, CNN down), no-op control, K2 | ⬜ |
| P3 | Industry and long-form writing, wave 1 | `sources/` | K3 | ⬜ |
| P4 | Idea board | `<data>/ideas/*.md` (private) | every card carries F1–F5; K4 | ⬜ |
| P5 | Remaining waves, static figures, refresh script | `figures/`, `scripts/refresh.sh` | refresh on unchanged data is a no-op | ⬜ |

## Views the page must have

| View | Question | Data it needs | First available |
|---|---|---|---|
| Share table | which axis values grew or died | labels | P1.8 |
| Lineage | what followed this paper, technique or product | citation graph | P1.8 |
| **Direction over time** | how one direction changed: pick a direction (an axis value, e.g. digital in-memory computing) and compare periods side by side, one row per other axis (workload, numerics, scale, evaluation rung, lever); any two periods can be diffed | labels | P1.8 |
| **Time cross-section** | what the related fields were doing at a chosen time: parallel lanes on one time axis (EDA-venue accelerator papers, architecture and circuits venues, upstream ML, devices and memory, industry products) with a movable time cursor | labels (lane 1), arm A and cross-field (P2), industry (P3) | lane 1 in P1.8; other lanes as their data arrives |
| Product genealogy | how a product line changed generation to generation and what it bet on | industry sources | P1.8 (thin), P3 |
| Academia vs industry | published but never shipped; shipped but barely studied | labels + industry | P3 |
| Cross-field flows | which fields fed this one and where it exported | cross-field | P2 |
| Idea board | what to work on next, with the filter trail | all | P4 |
| Sources and coverage | what the page rests on and what is missing | all | P1.8 |
| **Marks on every paper** (not a view) | influence: citation rank inside venue-year; novelty: precedence of the paper's label combination. Shown wherever a paper is listed | corpus citation counts, labels | P1.8 |

A lane or period built from fewer than 10 papers is drawn hatched with its n; an empty lane says why (no data yet / not found), never just blank.

## How to resume

1. `cd` to the repository root; `python3 tests/test_validate.py && python3 scripts/validate.py prereg`.
2. Find the first row above that is not ✅.
3. For labelling rows, list which batch files already exist and pass:
   `for f in <data>/batches/cim/batch_*.jsonl; do python3 scripts/check_batch.py $f <data>/labels_raw/cim/a/$(basename $f) | tail -1; done`
   Only batches that are missing or fail are sent again.
4. Update the status table in this file when a row changes.

## Labelling call (one per batch)

The classifier is given three files and nothing else: the prompt (`prompts/label_a.md` or `label_b.md`),
`schema/axes.json`, and one batch file (id, title, abstract — year and venue withheld). It writes one JSON
line per paper and runs `scripts/check_batch.py` on its own output before reporting.
