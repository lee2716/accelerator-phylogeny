# accel_trends

An interactive map of how AI-accelerator research and products have moved since 2018, built to surface
research directions rather than to decorate a survey. First slice: in-memory and near-memory computing.

Open `web/index.html` in a browser (no server needed).

## What is in it

- **Papers** from DAC, DATE, ICCAD and ASP-DAC, labelled on fixed axes (workload, compute paradigm, memory
  device, where data lives, numerics, evaluation rung, scale, what the contribution acts on) from titles and
  abstracts by a language-model classifier, with agreement between two independently worded prompts reported
  per axis.
- **Citation edges** inside those venues, merged from OpenAlex, Crossref DOIs and title matching of Crossref
  reference text, with measured recall.
- **Industry product lines** with generation-to-generation changes; every number carries its evidence tier
  (peer-reviewed / independent measurement / vendor claim / commentary), its rung and its baseline.
- **Marks on every paper**: influence (citation rank inside its own venue and year) and novelty by
  precedence (whether its combination of labels was new in these venues).

Read `docs/PREREG.md` for the thresholds, hypotheses and kill criteria fixed before the data was seen, and
the "Sources and limits" tab of the page for what the numbers can and cannot support.

## Layout

| Path | Content |
|---|---|
| `web/` | the page; `data.js` is generated |
| `scripts/` | pipeline (selection, labelling checks, agreement, trends, edges, page build) |
| `schema/axes.json` | the closed vocabularies |
| `prompts/` | classifier and collection instructions |
| `labels/` | labels and derived tables (DOIs and labels only) |
| `sources/industry/` | one sourced record per product line |
| `docs/` | `PREREG.md` (contract), `PLAN.md` (status and how to resume), `SOURCES.md` (record format) |
| `tests/` | `python3 tests/test_*.py` |

## Running it

Copy `config.example.json` to `config.local.json` and set `data_dir` (private working material: API caches,
abstracts) and `corpus_index` (the four-venue index). Abstracts, full texts and API caches are never
committed. Steps and their verifiers are listed in `docs/PLAN.md`.

## How it was made

This project is a collaboration between its author and Claude (Anthropic's AI model). The author set the
question, the requirements and every decision about scope and publication. Claude designed the method with
him, wrote the pipeline and the page, ran the classification of abstracts and the collection of industry
sources, and carried out the checks reported under "Sources and limits". The labels are therefore machine
labels: the model that produced them is recorded on every label row, and their agreement and limits are
stated rather than assumed.

## What it does not claim

Labels are read from abstracts, not full text. Shares are of labelled papers in a year. Citation counts are
never compared across years. "No follower found" can be a missing record. Precedence inside four venues is
not world priority.
