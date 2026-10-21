"""
sample_match.py - a small deterministic match so Luiza can test the
verifier and the agents before Willian's real generator is ready.

It plants ONE story on purpose: after a substitution at minute 65,
team B recovers the ball much higher up the pitch. A good Explainer
should notice it; the verifier should be able to confirm it.

Run:  python -m fiel.sample_match  -> writes data/sample_match.json
"""

import json
import random
from pathlib import Path

from fiel.claims import Event, Match


def build_sample(seed: int = 7) -> Match:
    rng = random.Random(seed)
    events: list[Event] = []
    counter = 0

    def add(minute, etype, team, player, x, y, outcome="n/a", meta=None):
        nonlocal counter
        counter += 1
        events.append(
            Event(
                id=f"e{counter:04d}",
                minute=minute,
                second=rng.randint(0, 59),
                type=etype,
                team=team,
                player=player,
                x=round(x, 1),
                y=round(y, 1),
                outcome=outcome,
                meta=meta or {},
            )
        )

    for minute in range(0, 90):
        # Team A keeps more of the ball all game: 6 passes vs 4 per minute.
        for i in range(6):
            add(minute, "pass", "A", f"A{rng.randint(1, 11)}",
                rng.uniform(20, 80), rng.uniform(0, 100),
                "success" if rng.random() < 0.85 else "fail")
        for i in range(4):
            add(minute, "pass", "B", f"B{rng.randint(1, 11)}",
                rng.uniform(20, 80), rng.uniform(0, 100),
                "success" if rng.random() < 0.80 else "fail")

        # Planted story: B's recoveries jump from ~35 to ~55 after minute 65.
        base_x = 35 if minute < 65 else 55
        if minute % 2 == 0:
            add(minute, "recovery", "B", f"B{rng.randint(1, 11)}",
                rng.uniform(base_x - 5, base_x + 5), rng.uniform(10, 90), "success")
        if minute % 3 == 0:
            add(minute, "recovery", "A", f"A{rng.randint(1, 11)}",
                rng.uniform(30, 40), rng.uniform(10, 90), "success")

        # A few shots so shot metrics are not empty.
        if minute % 9 == 4:
            add(minute, "shot", "A", f"A{rng.randint(7, 11)}", rng.uniform(80, 95),
                rng.uniform(30, 70), "success" if rng.random() < 0.4 else "fail")
        if minute % 11 == 7:
            add(minute, "shot", "B", f"B{rng.randint(7, 11)}", rng.uniform(80, 95),
                rng.uniform(30, 70), "success" if rng.random() < 0.4 else "fail")

    # The substitution the story hangs on.
    add(65, "substitution", "B", "B12", 50, 50, "n/a", {"off": "B6", "on": "B12"})
    # One goal each so the scoreline is not empty.
    add(31, "goal", "A", "A9", 94, 48, "success")
    add(78, "goal", "B", "B12", 93, 52, "success")

    events.sort(key=lambda e: (e.minute, e.second))
    return Match(match_id="sample-001", home="A", away="B", events=events)


if __name__ == "__main__":
    match = build_sample()
    out = Path("data")
    out.mkdir(exist_ok=True)
    path = out / "sample_match.json"
    path.write_text(match.model_dump_json(indent=2), encoding="utf-8")
    truth = {
        "match_id": match.match_id,
        "planted_stories": [
            {
                "id": "story-1",
                "description": "Team B recovers the ball about 20 metres higher after the substitution at 65'.",
                "metric": "recovery_height",
                "team": "B",
                "before": [55, 65],
                "after": [65, 75],
            }
        ],
    }
    (out / "sample_truth.json").write_text(json.dumps(truth, indent=2), encoding="utf-8")
    print(f"wrote {path} with {len(match.events)} events and data/sample_truth.json")
