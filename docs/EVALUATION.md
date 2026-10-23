# FIEL evaluation

This benchmark is reproducible and offline. It evaluates synthetic ground-truth
signals and deterministic verifier guardrails; it does **not** claim to measure
language-model quality.

| Measure | Result |
| --- | ---: |
| Generated matches | 30 |
| Planted stories | 49 |
| Story signals detected | 49 (100.0%) |
| Unsupported causal claims rejected | 49 (100.0%) |
| Evidence-safe corrections accepted | 49 (100.0%) |
| Mean deterministic processing time | 3.95 ms/match |

Command:

```bash
python evaluate.py --matches 30 --seed 2026
```

The JSON result is stored in `data/evaluation_summary.json`.
