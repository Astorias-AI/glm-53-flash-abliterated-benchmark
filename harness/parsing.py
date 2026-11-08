"""Extract the chosen option letter (A-D) from a model completion.

Returns the letter, or None if no confident answer could be parsed (counted as
`unparseable` / effective non-answer in scoring).
"""
from __future__ import annotations

import re
from typing import Optional

_LETTER = r"[ABCD]"

# Ordered from most to least explicit. First match wins.
_PATTERNS = [
    rf"\bfinal answer\b[^A-D]{{0,20}}({_LETTER})\b",
    rf"\banswer\b\s*(?:is|:|=)?\s*[\(\[]?({_LETTER})[\)\].:]?",
    rf"\boption\b\s*[\(\[]?({_LETTER})\b",
    rf"\bcorrect\b[^A-D]{{0,20}}({_LETTER})\b",
    rf"^\s*[\(\[]?({_LETTER})[\)\].:]",          # "C)" / "(C)" / "C." at start
    rf"^\s*({_LETTER})\s*$",                        # bare letter line
    rf"\b({_LETTER})\b",                           # last resort: first standalone letter
]


def parse_answer(text: str) -> Optional[str]:
    if not text:
        return None
    t = text.strip()
    upper = t.upper()
    for i, pat in enumerate(_PATTERNS):
        flags = re.IGNORECASE | (re.MULTILINE if "^" in pat else 0)
        m = re.search(pat, upper if i >= 1 else t, flags)
        # For the last-resort bare-letter scan, require the match to be early
        # so we don't grab an "A" from an explanatory sentence.
        if m:
            if pat == _PATTERNS[-1] and m.start() > 40:
                continue
            return m.group(1).upper()
    return None
