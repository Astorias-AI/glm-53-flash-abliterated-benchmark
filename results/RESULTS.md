# Benchmark Results

**Model under test:** `glm53fu` (GLM-5.3-Flash, abliterated build)  
**Endpoint:** `https://<model-endpoint>/v1`  
**Run (UTC):** 20261108 02:07:58  
**Wall time:** 62.3 min  
**Decoding:** temp 0.0, max_tokens 16384, reasoning enabled, concurrency 28

## Headline

| Benchmark | N | Accuracy | Answered-only | vs. random (25%) | Truncated | Mean reasoning tokens |
|---|---:|---:|---:|---:|---:|---:|
| CyberMetric-2000 | 2000 | **94.2%** | 94.6% | +69.2 pts | 10 (0.5%) | 245.3 |
| WMDP-cyber | 1987 | **71.7%** | 91.0% | +46.7 pts | 422 (21.2%) | 4827.8 |
| **Overall** | 3987 | **82.9%** | 93.0% | +57.9 pts | 432 | 2529.1 |

## Reading these numbers

- **Accuracy** counts truncated / unparseable responses as *incorrect* (strict, primary metric).
- **Answered-only** is accuracy over items that produced a parseable letter — the model's accuracy *when it commits to an answer*.
- **Truncated** items hit the reasoning-token budget before emitting a final letter. These concentrate in WMDP's long reverse-engineering questions; they are reported transparently rather than silently dropped.
- Latency p50/p95 and token usage per dataset are in `benchmark_results.json` and the raw `responses_20261108_020758.jsonl`.

## Datasets

### CyberMetric-2000
RAG-generated, human-validated cybersecurity knowledge MCQs spanning standards, cryptography, network security, and general infosec (Tihanyi et al., 2024).  
Source: https://github.com/cybermetric/CyberMetric  
Items scored: 2000 / 2000  
Latency p50 1317.9 ms · p95 7805.6 ms

### WMDP-cyber
Weapons of Mass Destruction Proxy — cyber subset. Expert-written multiple-choice questions probing offensive-security / exploitation *knowledge* (reconnaissance, vuln research, exploit reasoning, reverse engineering). Hazardous-knowledge proxy from Li et al., 2024.  
Source: https://huggingface.co/datasets/cais/wmdp  
Items scored: 1987 / 1987  
Latency p50 8612.3 ms · p95 183261.3 ms

