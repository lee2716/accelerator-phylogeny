# Source records: format and acceptance rules

One JSON file per product line under `sources/industry/<slug>.json`, checked by `scripts/check_sources.py`.
A record stores links and the collector's own summaries and extracted facts. It never stores article text;
at most three short quotations per source, only where the exact wording is the evidence.

## Evidence tiers (a number's tier is that of its origin, not of whoever relayed it)

| Tier | Meaning |
|---|---|
| T1 | peer-reviewed paper (carries its evaluation rung) |
| T2 | independent measurement: MLPerf closed division, third-party benchmark, teardown, a paper measuring someone else's product |
| T3 | the vendor's or author's own claim outside peer review: white paper, datasheet, press release, talk, interview |
| T4 | commentary or interpretation: trade press, analyst note, personal blog |

A vendor projection relayed by trade press is T3 at rung `projection`, with the vendor-chosen baseline named.

## Acceptance test for a source (C2 is mandatory, plus any three of the others)

- C1 the author is identifiable and has shipped or published in the area
- C2 it states mechanisms, not only outcomes
- C3 every headline number carries its conditions, or the text says it does not
- C4 it links to at least three primary sources
- C5 it is not a rewrite of a press release: it adds at least one fact or caveat
- C6 it is cited or discussed by identifiable practitioners

A source that fails is still listed with `accepted: false` and a `reject_reason`
(`NO_AUTHOR`, `NO_MECHANISM`, `UNCONDITIONED_NUMBERS`, `NO_PRIMARY_LINKS`, `PRESS_REWRITE`, `NO_ENGAGEMENT`,
`OFF_SCOPE`, `PAYWALL`, `VIDEO_ONLY`, `DUPLICATE`). Its facts may still be recorded as T3 claims when it is the
only account of an announcement; rejection means it is not counted as independent evidence.
Primary documents (vendor datasheet, white paper, peer-reviewed paper, MLPerf table) are accepted as what
they are — their tier says how far to trust them — and are not put through C1–C6.

## File layout

```
{
 "product_line": str, "vendor": str, "country": str,
 "status": {"value": "alive|acquired|dead|pivoted|unknown", "as_of": "YYYY-MM-DD", "detail": str, "source_id": str|null},
 "generations": [{
   "name": str, "year_announced": int|null, "year_shipped": int|null,
   "axes": {"<axis key from schema/axes.json>": {"value": str, "basis": "disclosed|relayed|inferred|unknown", "source_id": str|null}},
   "numbers": [{"metric","value","unit","rung","tier","baseline","conditions","origin_source_id"}],
   "bets": [{"text": str, "status": "open|paid_off|failed|unknown", "source_id": str, "status_source_id": str|null}],
   "what_changed_from_previous": str|null, "next": str|null }],
 "sources": [{"id","class","url","author","date","language","accessed","title_original","summary_en","tier",
              "accepted": bool, "reject_reason": str|null, "checks": {"C1":bool,...}|null, "quotes": [str]}],
 "conflicts": [{"metric": str, "accounts": [number, number, ...]}],
 "not_found": [str]
}
```

Rules the checker enforces: every axis cell with a basis other than `unknown` names a source that exists in
the file; every number has rung, tier, a `baseline` key (null = none named) and an origin source; a source has
URL, access date, tier and an English summary; `unknown` is written as `unknown`, never filled by analogy;
a number is never used to infer an axis value; conflicting accounts go under `conflicts`, they are not averaged.

## Basis of an axis value

| Basis | Meaning |
|---|---|
| `disclosed` | stated in the vendor's own document, talk or paper, and that document was opened |
| `relayed` | a vendor statement reported by a third party (trade press, analyst, blog); the vendor's own document was not opened |
| `inferred` | inferred by an independent source, not stated by the vendor |
| `unknown` | neither; never filled in by analogy |

`relayed` was added on 2026-10-09 after the first collection marked press-relayed vendor statements as
`disclosed`. `scripts/check_sources.py` does not yet reject a `disclosed` cell that points at a press source;
the conversion was applied once to all files by source class.
