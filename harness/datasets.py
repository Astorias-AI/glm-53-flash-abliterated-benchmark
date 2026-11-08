"""Dataset loaders that normalize each cyber-knowledge benchmark to a common
multiple-choice schema.

Normalized item schema:
    {
        "uid":     str,          # stable per-item id: "<dataset>-<index>"
        "dataset": str,          # "wmdp-cyber" | "cybermetric-2000"
        "question": str,
        "options": {"A": str, "B": str, "C": str, "D": str},
        "answer":  str,          # correct option letter, one of A-D
    }

Raw question text is loaded in memory for sending to the model but is NOT
written to any published results file (see run_benchmark.py). This keeps the
published study reproducible-by-reference without redistributing the question
banks.
"""
from __future__ import annotations

import json
import os
from typing import List, Dict

LETTERS = ["A", "B", "C", "D"]


def load_wmdp_cyber(path: str) -> List[Dict]:
    """WMDP-cyber: {answer:int(0-3), question:str, choices:[4 str]}."""
    with open(path) as f:
        rows = json.load(f)
    items = []
    for i, r in enumerate(rows):
        choices = r["choices"]
        if len(choices) != 4:
            # WMDP is uniformly 4-way; skip anything malformed defensively.
            continue
        items.append(
            {
                "uid": f"wmdp-cyber-{i}",
                "dataset": "wmdp-cyber",
                "question": r["question"],
                "options": {L: str(choices[j]) for j, L in enumerate(LETTERS)},
                "answer": LETTERS[int(r["answer"])],
            }
        )
    return items


def load_cybermetric(path: str) -> List[Dict]:
    """CyberMetric: {question:str, answers:{A..D:str}, solution:str}."""
    with open(path) as f:
        data = json.load(f)
    rows = data["questions"]
    items = []
    for i, r in enumerate(rows):
        ans = r["answers"]
        if not all(L in ans for L in LETTERS):
            continue
        sol = str(r["solution"]).strip().upper()
        if sol not in LETTERS:
            continue
        items.append(
            {
                "uid": f"cybermetric-2000-{i}",
                "dataset": "cybermetric-2000",
                "question": r["question"],
                "options": {L: str(ans[L]) for L in LETTERS},
                "answer": sol,
            }
        )
    return items


def load_all(raw_dir: str) -> List[Dict]:
    items: List[Dict] = []
    wmdp = os.path.join(raw_dir, "wmdp_cyber.json")
    cm = os.path.join(raw_dir, "CyberMetric-2000-v1.json")
    if os.path.exists(wmdp):
        items += load_wmdp_cyber(wmdp)
    if os.path.exists(cm):
        items += load_cybermetric(cm)
    return items
