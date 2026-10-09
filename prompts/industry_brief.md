# Brief: collect one industry product line

You are collecting sourced facts about one hardware product line so it can be placed on the same axes as
research papers. Accuracy and traceability matter more than completeness: an honest `unknown` or an entry
under `not_found` is a good result; a plausible guess is a defect.

## Read first

1. `docs/SOURCES.md` — the record format, the evidence tiers and the acceptance test. Follow it exactly.
2. `schema/axes.json` — the only legal axis keys and values.

## What to find, per product line

- The generations of the product since 2018 (announced and shipped years), and for each generation where it
  sits on the axes: workload target, compute paradigm, memory device, where data lives and how it moves,
  numerics, programmability and software stack, scale. Fill an axis only from a source; otherwise write
  `{"value": "unknown", "basis": "unknown", "source_id": null}`. `disclosed` = the vendor's own document states
  it. `inferred` = an independent source (teardown, benchmark, analyst, paper) infers it. Never infer an axis
  value from a performance number.
- Headline numbers, each with rung, tier, baseline (null if none is named) and conditions. A projection from a
  prototype or simulator is rung `projection`. A number quoted by a journalist keeps the tier of whoever
  originated it.
- The bets the design makes (one sentence each, in your own words), and for each whether a later source shows
  it paid off, failed, or is still open.
- What changed from one generation to the next, and why, when a source says why.
- The company's current status (alive, acquired, dead, pivoted) with a dated source. Do not state a status
  from memory.
- Where two sources disagree, record both under `conflicts`. Do not pick one.

## Sources

Prefer, in this order: peer-reviewed papers and conference industry sessions (ISSCC, Hot Chips, VLSI),
vendor white papers / datasheets / engineering posts, independent measurements, then quality commentary.
Sources in any language are welcome; summarise in English and keep the original-language title.
Apply the C1–C6 test to commentary and record the outcome for every candidate you opened, including the ones
you reject — the list of rejected candidates is part of the deliverable.

Limits per product line: at most 8 web searches, at most 12 pages opened, at most 8 sources recorded.
Stop when the generations have at least one primary source each, or when the limits are reached; whatever is
still missing goes under `not_found` in plain words.

## Writing rules

- Summaries and extracted facts are written in your own words. Do not copy sentences from a page. At most
  three quotations per source, each at most 40 words, and only where the exact wording is the evidence.
- Every source record carries URL, author (or the organisation), date, language, the date you accessed it,
  the original title, your English summary and its tier.
- No e-mail addresses, no login-walled content, no video-only sources.

## Deliver

Write `sources/industry/<slug>.json`, then run `python3 scripts/check_sources.py sources/industry/<slug>.json`
from the repository root and fix what it reports (at most two rounds; fix by re-reading the source, not by
inventing a value). Report one line per product line: slug, number of generations, number of sources accepted
and rejected, checker result.
