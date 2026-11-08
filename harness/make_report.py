#!/usr/bin/env python3
"""Turn a benchmark run (summary_*.json + responses_*.jsonl) into publishable
artifacts: results/benchmark_results.json (canonical) and results/RESULTS.md.

Usage:
  python3 make_report.py [--stamp YYYYMMDD_HHMMSS]   # defaults to latest run
"""
from __future__ import annotations

import argparse
import glob
import json
import os
from datetime import datetime, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
RESULTS = os.path.join(ROOT, "results")

RANDOM_BASELINE = 0.25  # 4-way MCQ

DATASET_INFO = {
    "wmdp-cyber": {
        "title": "WMDP-cyber",
        "n_full": 1987,
        "desc": "Weapons of Mass Destruction Proxy — cyber subset. Expert-written "
                "multiple-choice questions probing offensive-security / exploitation "
                "*knowledge* (reconnaissance, vuln research, exploit reasoning, "
                "reverse engineering). Hazardous-knowledge proxy from Li et al., 2024.",
        "source": "https://huggingface.co/datasets/cais/wmdp",
    },
    "cybermetric-2000": {
        "title": "CyberMetric-2000",
        "n_full": 2000,
        "desc": "RAG-generated, human-validated cybersecurity knowledge MCQs spanning "
                "standards, cryptography, network security, and general infosec "
                "(Tihanyi et al., 2024).",
        "source": "https://github.com/cybermetric/CyberMetric",
    },
}


def latest_stamp() -> str:
    files = glob.glob(os.path.join(RESULTS, "summary_*.json"))
    if not files:
        raise SystemExit("No summary_*.json found in results/")
    f = max(files, key=os.path.getmtime)
    return os.path.basename(f)[len("summary_"):-len(".json")]


def pct(x):
    return f"{x * 100:.1f}%" if x is not None else "—"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--stamp", default="")
    args = ap.parse_args()
    stamp = args.stamp or latest_stamp()

    summ = json.load(open(os.path.join(RESULTS, f"summary_{stamp}.json")))
    meta = summ["meta"]

    canonical = {
        "model": meta["model"],
        "endpoint": meta["base_url"],
        "run_timestamp_utc": stamp,
        "methodology": {
            "format": "zero-shot 4-way multiple choice, letter-only answer",
            "decoding": f"temperature {meta['temperature']}, max_tokens {meta['max_tokens']} "
                        f"(reasoning enabled; model is a thinking model)",
            "scoring": "exact letter match; truncated/unparseable count as incorrect in "
                       "primary accuracy, excluded in answered_accuracy",
            "concurrency": meta["concurrency"],
        },
        "random_baseline": RANDOM_BASELINE,
        "overall": summ["overall"],
        "by_dataset": summ["by_dataset"],
        "wall_time_s": meta["wall_time_s"],
    }
    json.dump(canonical, open(os.path.join(RESULTS, "benchmark_results.json"), "w"), indent=2)

    ov = summ["overall"]
    lines = []
    lines.append("# Benchmark Results\n")
    lines.append(f"**Model under test:** `{meta['model']}` (GLM-5.3-Flash, abliterated build)  ")
    lines.append(f"**Endpoint:** `{meta['base_url']}`  ")
    lines.append(f"**Run (UTC):** {stamp[:8]} {stamp[9:11]}:{stamp[11:13]}:{stamp[13:15]}  ")
    lines.append(f"**Wall time:** {meta['wall_time_s'] / 60:.1f} min  ")
    lines.append(f"**Decoding:** temp {meta['temperature']}, max_tokens {meta['max_tokens']}, "
                 f"reasoning enabled, concurrency {meta['concurrency']}\n")

    lines.append("## Headline\n")
    lines.append("| Benchmark | N | Accuracy | Answered-only | vs. random (25%) | Truncated | Mean reasoning tokens |")
    lines.append("|---|---:|---:|---:|---:|---:|---:|")
    for ds, a in summ["by_dataset"].items():
        info = DATASET_INFO.get(ds, {"title": ds})
        lift = f"+{(a['accuracy'] - RANDOM_BASELINE) * 100:.1f} pts" if a["accuracy"] is not None else "—"
        lines.append(
            f"| {info['title']} | {a['n']} | **{pct(a['accuracy'])}** | {pct(a.get('answered_accuracy'))} "
            f"| {lift} | {a.get('truncated', 0)} ({pct(a.get('truncated',0)/a['n'])}) "
            f"| {a.get('mean_reasoning_tokens') or '—'} |"
        )
    lines.append(
        f"| **Overall** | {ov['n']} | **{pct(ov['accuracy'])}** | {pct(ov.get('answered_accuracy'))} "
        f"| +{(ov['accuracy'] - RANDOM_BASELINE) * 100:.1f} pts "
        f"| {ov.get('truncated',0)} | {ov.get('mean_reasoning_tokens') or '—'} |"
    )

    lines.append("\n## Reading these numbers\n")
    lines.append("- **Accuracy** counts truncated / unparseable responses as *incorrect* "
                 "(strict, primary metric).")
    lines.append("- **Answered-only** is accuracy over items that produced a parseable "
                 "letter — the model's accuracy *when it commits to an answer*.")
    lines.append("- **Truncated** items hit the reasoning-token budget before emitting a "
                 "final letter. These concentrate in WMDP's long reverse-engineering "
                 "questions; they are reported transparently rather than silently dropped.")
    lines.append(f"- Latency p50/p95 and token usage per dataset are in "
                 f"`benchmark_results.json` and the raw `responses_{stamp}.jsonl`.\n")

    lines.append("## Datasets\n")
    for ds, a in summ["by_dataset"].items():
        info = DATASET_INFO.get(ds)
        if not info:
            continue
        lines.append(f"### {info['title']}")
        lines.append(f"{info['desc']}  ")
        lines.append(f"Source: {info['source']}  ")
        lines.append(f"Items scored: {a['n']} / {info['n_full']}  ")
        lines.append(f"Latency p50 {a['latency_ms_p50']} ms · p95 {a['latency_ms_p95']} ms\n")

    out = os.path.join(RESULTS, "RESULTS.md")
    open(out, "w").write("\n".join(lines) + "\n")

    # Inject a compact headline block into README between the markers.
    headline = []
    headline.append(f"**Run {stamp[:8]} {stamp[9:11]}:{stamp[11:13]} UTC · model `{meta['model']}` · "
                    f"{meta['wall_time_s'] / 60:.0f} min wall**\n")
    headline.append("| Benchmark | N | Accuracy | Answered-only | Truncated |")
    headline.append("|---|---:|---:|---:|---:|")
    for ds, a in summ["by_dataset"].items():
        info = DATASET_INFO.get(ds, {"title": ds})
        headline.append(f"| {info['title']} | {a['n']} | **{pct(a['accuracy'])}** "
                        f"| {pct(a.get('answered_accuracy'))} | {a.get('truncated',0)} |")
    headline.append(f"| **Overall** | {ov['n']} | **{pct(ov['accuracy'])}** "
                    f"| {pct(ov.get('answered_accuracy'))} | {ov.get('truncated',0)} |")
    headline.append(f"\nRandom-chance baseline: 25%. Full detail: "
                    f"[`results/RESULTS.md`](results/RESULTS.md).")
    block = "<!-- RESULTS_SUMMARY -->\n" + "\n".join(headline) + "\n<!-- /RESULTS_SUMMARY -->"

    readme_path = os.path.join(ROOT, "README.md")
    if os.path.exists(readme_path):
        import re
        txt = open(readme_path).read()
        new = re.sub(r"<!-- RESULTS_SUMMARY -->.*?<!-- /RESULTS_SUMMARY -->",
                     block, txt, flags=re.DOTALL)
        open(readme_path, "w").write(new)

    print(f"wrote {out}")
    print(f"wrote {os.path.join(RESULTS, 'benchmark_results.json')}")
    print(f"patched {readme_path}")
    print("\n".join(lines[:16]))


if __name__ == "__main__":
    main()
