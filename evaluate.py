"""Reproducible offline evaluation of FIEL's synthetic story engine.

This evaluates deterministic capabilities without spending model tokens:
planted-story detection, rejection of unsupported causal claims, acceptance of
evidence-safe corrections, and processing latency.

Run:
    python evaluate.py --matches 30
"""

from __future__ import annotations

import argparse
import json
import random
import time
from pathlib import Path

from fiel.claims import Claim
from fiel.generator import MatchBuilder, STORY_KINDS, fixtures
from fiel.verifier import recompute, verify

EVENT_FOR_METRIC = {
    "recovery_height": "recovery",
    "possession_pct": "pass",
}


def story_signal(match, story: dict) -> tuple[bool, float, float]:
    metric, team = story["metric"], story["team"]
    before = recompute(metric, team, match, *story["before"])
    after = recompute(metric, team, match, *story["after"])
    if before is None or after is None:
        return False, float(before or 0), float(after or 0)
    delta = after - before
    threshold = 8.0 if metric == "recovery_height" else 10.0
    return delta >= threshold, float(before), float(after)


def guardrail_scene(match, story: dict) -> tuple[bool, bool]:
    metric, team = story["metric"], story["team"]
    start, end = story["after"]
    value = recompute(metric, team, match, start, end)
    event_type = EVENT_FOR_METRIC[metric]
    ids = [event.id for event in match.events_between(start, end)
           if event.team == team and event.type == event_type]
    if value is None or not ids:
        return False, False

    bad = Claim(
        claim=f"The trigger caused team {team} to win the game.",
        metric=metric, value=round(value, 1), team=team,
        window_start=start, window_end=end, event_ids=ids[:2], causal=True,
    )
    corrected = bad.model_copy(update={
        "claim": f"Team {team} recorded {metric} of {value:.1f} between minutes {start} and {end}.",
        "event_ids": ids,
        "causal": False,
    })
    return not verify(bad, match).ok, verify(corrected, match).ok


def evaluate_matches(count: int = 30, seed: int = 2026) -> dict:
    rng = random.Random(seed)
    started = time.perf_counter()
    stories_total = stories_detected = rejected = corrected = 0
    examples = []

    for index, (home, away) in enumerate(fixtures(count, rng), start=1):
        match_id = f"eval-{index:03d}-{home}-{away}"
        builder = MatchBuilder(match_id, home, away, seed=rng.randint(0, 10**6))
        selected = rng.sample(STORY_KINDS, k=rng.choice([1, 2]))
        match = builder.build(selected)

        for story in builder.planted:
            detected, before, after = story_signal(match, story)
            bad_rejected, correction_accepted = guardrail_scene(match, story)
            stories_total += 1
            stories_detected += int(detected)
            rejected += int(bad_rejected)
            corrected += int(correction_accepted)
            if len(examples) < 5:
                examples.append({
                    "match_id": match_id,
                    "kind": story["kind"],
                    "metric": story["metric"],
                    "team": story["team"],
                    "before": round(before, 2),
                    "after": round(after, 2),
                    "detected": detected,
                })

    elapsed_ms = (time.perf_counter() - started) * 1000

    def rate(value: int) -> float:
        return round(value / stories_total, 4) if stories_total else 0.0

    return {
        "evaluation_type": "deterministic_offline_ground_truth",
        "matches": count,
        "seed": seed,
        "planted_stories": stories_total,
        "stories_detected": stories_detected,
        "story_detection_rate": rate(stories_detected),
        "unsupported_causal_claims_rejected": rejected,
        "causal_rejection_rate": rate(rejected),
        "safe_corrections_accepted": corrected,
        "correction_acceptance_rate": rate(corrected),
        "total_processing_ms": round(elapsed_ms, 2),
        "mean_processing_ms_per_match": round(elapsed_ms / count, 2) if count else 0.0,
        "examples": examples,
        "scope_note": (
            "This benchmark evaluates deterministic story signals and verifier guardrails. "
            "It does not claim to measure LLM quality."
        ),
    }


def markdown_report(result: dict) -> str:
    return f"""# FIEL evaluation

This benchmark is reproducible and offline. It evaluates synthetic ground-truth
signals and deterministic verifier guardrails; it does **not** claim to measure
language-model quality.

| Measure | Result |
| --- | ---: |
| Generated matches | {result['matches']} |
| Planted stories | {result['planted_stories']} |
| Story signals detected | {result['stories_detected']} ({result['story_detection_rate']:.1%}) |
| Unsupported causal claims rejected | {result['unsupported_causal_claims_rejected']} ({result['causal_rejection_rate']:.1%}) |
| Evidence-safe corrections accepted | {result['safe_corrections_accepted']} ({result['correction_acceptance_rate']:.1%}) |
| Mean deterministic processing time | {result['mean_processing_ms_per_match']:.2f} ms/match |

Command:

```bash
python evaluate.py --matches {result['matches']} --seed {result['seed']}
```

The JSON result is stored in `data/evaluation_summary.json`.
"""


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--matches", type=int, default=30)
    parser.add_argument("--seed", type=int, default=2026)
    parser.add_argument("--output", default="data/evaluation_summary.json")
    parser.add_argument("--report", default="docs/EVALUATION.md")
    args = parser.parse_args()

    result = evaluate_matches(args.matches, args.seed)
    output, report = Path(args.output), Path(args.report)
    output.parent.mkdir(parents=True, exist_ok=True)
    report.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2), encoding="utf-8")
    report.write_text(markdown_report(result), encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
