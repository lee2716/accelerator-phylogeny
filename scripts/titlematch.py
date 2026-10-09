"""Find which known paper titles occur as a whole title inside a free-text reference. Pure functions, no I/O.

Used where a reference list gives text but no DOI. A bare substring test is wrong: the DATE 2018 title
"ReRAM-based accelerator for deep learning" is contained in "PipeLayer: A pipelined ReRAM-based accelerator
for deep learning", so every citation of the second was counted as a citation of the first. A match
therefore has to be bounded on both sides: before it, the start of the text or sentence punctuation (not a
letter, digit, colon or hyphen); after it, the end of the text or punctuation (not another word).
Titles shorter than MIN_TITLE_CHARS after normalisation are never matched.
"""
import re

MIN_TITLE_CHARS = 25
KEY = 14                       # index titles by their first KEY normalised characters
SKIP = set(" \t\r\n\"'“”‘’`*_")  # ignored when looking at what precedes or follows a match
OPENERS = set(".,;])")          # what may precede a title: end of the author list or of a reference number
CLOSERS = set(".,;?!([")        # what may follow a title


def normalise(text):
    return re.sub(r"[^a-z0-9]", "", text.lower())


def _normalise_with_positions(raw):
    chars, positions = [], []
    for position, char in enumerate(raw.lower()):
        if char.isascii() and char.isalnum():
            chars.append(char)
            positions.append(position)
    return "".join(chars), positions


def _neighbour(raw, position, step):
    """First character that is not whitespace or a quote mark, walking from `position` in direction `step`."""
    while 0 <= position < len(raw):
        if raw[position] not in SKIP:
            return raw[position]
        position += step
    return None


class TitleIndex:
    def __init__(self, titles):
        """titles: {paper_id: raw title}"""
        self.by_prefix = {}
        for paper_id, title in titles.items():
            norm = normalise(title)
            if len(norm) >= MIN_TITLE_CHARS:
                self.by_prefix.setdefault(norm[:KEY], []).append((norm, paper_id))

    def find(self, raw_text):
        """Return the ids of the titles that occur in `raw_text` as a bounded whole title."""
        norm_text, positions = _normalise_with_positions(raw_text)
        found = set()
        for start in range(len(norm_text) - KEY + 1):
            for norm, paper_id in self.by_prefix.get(norm_text[start:start + KEY], ()):
                if not norm_text.startswith(norm, start):
                    continue
                before = _neighbour(raw_text, positions[start] - 1, -1)
                after = _neighbour(raw_text, positions[start + len(norm) - 1] + 1, +1)
                if (before is None or before in OPENERS) and (after is None or after in CLOSERS):
                    found.add(paper_id)
        return found
