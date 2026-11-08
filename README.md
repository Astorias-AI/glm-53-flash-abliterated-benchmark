<img src="assets/icon.svg" width="64" height="64" alt="">

# Cyber-Knowledge Capability of an Abliterated GLM-5.3-Flash

A reproducible benchmark of a **safety-ablated ("abliterated") GLM-5.3-Flash** build on
two standard, published cybersecurity *knowledge* benchmarks:

- **WMDP-cyber** — 1,987 expert-written MCQs probing offensive-security / exploitation
  knowledge (vuln research, exploit reasoning, reverse engineering). The cyber subset of
  the Weapons of Mass Destruction Proxy hazardous-knowledge benchmark (Li et al., 2024).
- **CyberMetric-2000** — 2,000 human-validated cybersecurity knowledge MCQs across
  standards, cryptography, and network/infra security (Tihanyi et al., 2024).

Results, the full run log, and per-item scores are in [`results/`](results/) and
[`logs/`](logs/). Headline numbers: **[`results/RESULTS.md`](results/RESULTS.md)**.

---

## What this measures — and what it deliberately does not

This study measures **cybersecurity knowledge and reasoning** via multiple-choice
accuracy, with the model's chain-of-thought reasoning **enabled** (it is a thinking
model, and this is how its capability is meant to be exercised).

It does **not** measure *agentic exploit generation*. The flagship benchmarks that
GLM-5.3-Flash's public cyber numbers come from — **ExploitBench** (producing working
end-to-end exploits for known V8/Chrome vulnerabilities) and **CyberGym** (find-and-
exploit on real codebases) — are agentic harnesses requiring vulnerable-target
sandboxes, and their output is functional exploit code against real software. We do not
run those here, for two reasons:

1. **Feasibility.** They are not a chat-completions workload; they need per-task
   vulnerable-build sandboxes, tool-use loops, and many retries — days of infrastructure,
   not a sub-hour API run.
2. **Responsible scope.** Mass-generating working exploit code with a safety-removed model
   and publishing the transcripts would be distributing a reusable offensive artifact.
   This study publishes *scores*, not weaponized code.

MCQ knowledge is a meaningful, bounded, and publishable proxy for the underlying
expertise; it is not a claim about real-world exploitation ability.

## Results

See [`results/RESULTS.md`](results/RESULTS.md) for the generated tables and
[`results/benchmark_results.json`](results/benchmark_results.json) for canonical,
machine-readable numbers.

<!-- RESULTS_SUMMARY -->
**Run 20261108 02:07 UTC · model `glm53fu` · 62 min wall**

| Benchmark | N | Accuracy | Answered-only | Truncated |
|---|---:|---:|---:|---:|
| CyberMetric-2000 | 2000 | **94.2%** | 94.6% | 10 |
| WMDP-cyber | 1987 | **71.7%** | 91.0% | 422 |
| **Overall** | 3987 | **82.9%** | 93.0% | 432 |

Random-chance baseline: 25%. Full detail: [`results/RESULTS.md`](results/RESULTS.md).
<!-- /RESULTS_SUMMARY -->

## How this compares to stock GLM-5.3-Flash

**There is no reproducible same-benchmark baseline to compare against**, and it is worth
being precise about why, because the honest answer shapes how these numbers should be read.

1. **Stock GLM-5.3-Flash has no published WMDP-cyber or CyberMetric score.** The public
   WMDP-cyber leaderboards list no GLM entry at all.
2. **The cyber benchmarks that *do* have a stock-Flash score cannot be reproduced.** They
   run on private, held-out data or are agentic exploit-realization harnesses:

   | Published (stock GLM-5.3-Flash) | Score | Source | Why not reproducible here |
   |---|---:|---|---|
   | CyberGym-E2E | 74.0% | Artificial Analysis | Agentic end-to-end exploit generation |
   | CWE-Bench-AA | 55.8% | Artificial Analysis | 120 held-out tasks, **private dataset** |
   | DeepsecBench-AA | 19.9% | Artificial Analysis | **Private** golden set + secret construction |
   | AA Cyber Index | 49.9% | Artificial Analysis | Weighted mean of the three above |

   Matching a published figure *without* the same data and harness is not apples-to-apples:
   stock GLM-5.3 scores **54.4%** (vendor) vs **61.1%** (NIST CAISI) on ExploitBench purely
   from a harness change. A controlled run of stock Flash through *this* harness is the only
   sound baseline.

**What is known about ablation's effect.** In its
[GLM-5.3 cyber report](https://www.anthropic.com/research/glm-5-3-and-the-spread-of-advanced-cyber-capabilities),
Anthropic produced its own abliterated copy of GLM-5.3-Flash and found that ablation
dropped the mean refusal rate across JailbreakBench / HarmBench / StrongREJECT from
**95% to 14%**, while capability was **"nearly unchanged"** (identical GPQA-Diamond, a few
points lower on a CyberGym subset). The reasonable prior is therefore that ablation here
mostly removed refusals and left knowledge roughly intact — consistent with this run, in
which the model refused **zero** of 3,987 questions and every non-answer was a reasoning
truncation, not a refusal. Against the only defensible yardstick available, the **25%
random-chance floor**, the build scores far above chance on both benchmarks.

## Methodology

- **Endpoint:** self-hosted OpenAI-compatible server (SGLang), model id `glm53fu`,
  1,048,576-token context.
- **Prompt:** zero-shot. A system instruction to answer with only the option letter,
  then the question and four options. No few-shot exemplars, no retrieval.
- **Decoding:** `temperature = 0`, `max_tokens = 16384`. Reasoning (thinking) is enabled;
  the large token budget is required because WMDP's reverse-engineering questions can
  consume several thousand reasoning tokens before committing to an answer.
- **Scoring:** exact match of the extracted answer letter against the gold label.
  - *Primary accuracy* counts truncated or unparseable responses as **incorrect**.
  - *Answered-only accuracy* is computed over responses that produced a parseable letter.
  - **Truncated** = the model exhausted its reasoning-token budget before emitting a final
    letter. These are reported explicitly (they cluster in WMDP's hardest RE questions)
    rather than silently dropped.
- **Concurrency & good-neighbor pacing:** the runner polls `/v1/load` before and during
  the run and records server state alongside progress, staying within the endpoint's
  running-request capacity so co-resident production traffic is not starved.

## Reproduce

```bash
# 1. Fetch the raw question banks (not redistributed in this repo)
bash harness/fetch_data.sh

# 2. Run the benchmark against an OpenAI-compatible endpoint
API_KEY=... BASE_URL=https://<host>/v1 MODEL=glm53fu \
  python3 harness/run_benchmark.py --concurrency 28 --max-tokens 16384

# 3. Generate results/RESULTS.md + results/benchmark_results.json
python3 harness/make_report.py
```

Requirements: Python 3.10+, `aiohttp`, `certifi`, `pyarrow` (for the WMDP parquet).

## Limitations

- **Single model, no base-model control.** Only the abliterated build was available for
  this run. A clean *abliterated vs. stock* delta on these exact benchmarks requires
  running stock GLM-5.3-Flash through the identical harness — see _Future work_.
- **MCQ ≠ exploitation.** High MCQ accuracy reflects knowledge, not demonstrated ability
  to develop or deploy exploits.
- **Truncation is material on WMDP.** 422 of 1,987 WMDP items (**21.2%**) exhausted the
  16,384-token reasoning budget before emitting a final letter and are scored as incorrect
  in the primary metric. This is why WMDP primary accuracy (71.7%) and answered-only
  accuracy (91.0%) diverge so widely — the strict number is a floor depressed by budget
  truncation, the answered number is a ceiling that ignores "couldn't finish in budget."
  The model's true WMDP-cyber capability lies between them. CyberMetric truncation was
  negligible (0.5%).
- **Contamination caveat.** WMDP and CyberMetric are public; pretraining contamination
  cannot be ruled out and would inflate scores. This affects all models similarly.
- **Self-reported substrate.** Numbers come from a self-hosted endpoint; they characterize
  *this deployment* of the weights.

## Future work

- Run **stock GLM-5.3-Flash** through this identical harness for a controlled
  abliteration delta.
- Add a **refusal-rate** probe to quantify what ablation changed on safety-relevant
  prompts (compliance rates only, not harmful completions).

## Ethics & data

This repository publishes **derived, scores-only artifacts** — per-item chosen/correct
letters and aggregate accuracy. It does **not** redistribute the question banks (fetch
them with `harness/fetch_data.sh`), and it contains **no exploit code or weaponized
content**. The work characterizes capabilities of a publicly-circulating model build
using established public benchmarks, in the spirit of transparency research on
safety-ablated models.

## Citations

- Li et al., *The WMDP Benchmark: Measuring and Reducing Malicious Use With Unlearning*, 2024.
- Tihanyi et al., *CyberMetric: A Benchmark Dataset ... for Evaluating LLMs in Cybersecurity Knowledge*, 2024.
