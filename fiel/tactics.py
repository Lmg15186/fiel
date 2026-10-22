"""
tactics.py - the Tactics Engine: numbers computed straight from events.

  pressure_windows()  how hard each team presses, per 5-minute window:
                      defensive actions (recoveries, fouls) in the opponent
                      half, divided by opponent passes. Higher = more press.
  xg()                a simple expected-goals value for every shot, from
                      where it was taken. A transparent formula, not a model.
  win_probability()   P(home win / draw / away win) at a given minute, by
                      Monte Carlo with Poisson goals, like the FielCup model.

Run:  python -m fiel.tactics data/m-003-T4-T3.json
"""

import math
import random
import sys
from pathlib import Path

from fiel.claims import Event, Match

WINDOW = 5  # minutes


def pressure_windows(match: Match, window: int = WINDOW) -> list[dict]:
    """One row per window with a pressure index for A and B."""
    rows = []
    last_minute = max(e.minute for e in match.events) + 1
    for start in range(0, last_minute, window):
        end = start + window
        evs = match.events_between(start, end)
        row = {"start": start, "end": end}
        for team in ("A", "B"):
            other = "B" if team == "A" else "A"
            actions = [e for e in evs if e.team == team
                       and e.type in ("recovery", "foul") and e.x > 50]
            opp_passes = [e for e in evs if e.team == other and e.type == "pass"]
            row[f"press_{team}"] = (10.0 * len(actions) / len(opp_passes)
                                    if opp_passes else 0.0)
        rows.append(row)
    return rows


def xg(shot: Event) -> float:
    """Expected goals for one shot, from distance and angle to goal (x=100, y=50)."""
    if shot.type != "shot":
        return 0.0
    dx = 100.0 - shot.x
    dy = abs(50.0 - shot.y)
    dist = math.hypot(dx, dy)
    value = 0.9 * math.exp(-dist / 9.0)
    if shot.outcome == "success":
        value *= 1.4
    return round(min(value, 0.95), 3)


def xg_totals(match: Match, upto_minute: int | None = None) -> dict:
    totals = {"A": 0.0, "B": 0.0}
    for e in match.events:
        if e.type != "shot":
            continue
        if upto_minute is not None and e.minute >= upto_minute:
            continue
        totals[e.team] += xg(e)
    return {k: round(v, 2) for k, v in totals.items()}


def score_at(match: Match, minute: int) -> dict:
    goals = {"A": 0, "B": 0}
    for e in match.events:
        if e.type == "goal" and e.minute < minute:
            goals[e.team] += 1
    return goals


def _poisson(rng: random.Random, lam: float) -> int:
    """Draw one Poisson sample (Knuth's method), fine for small lambda."""
    limit = math.exp(-lam)
    k, p = 0, 1.0
    while True:
        p *= rng.random()
        if p <= limit:
            return k
        k += 1


def win_probability(match: Match, minute: int, runs: int = 3000,
                    seed: int = 0, prior_rate: float = 1.3) -> dict:
    """P(A win), P(draw), P(B win) at `minute`; the three sum to 1."""
    rng = random.Random(seed)
    current = score_at(match, minute)
    played = max(minute, 1)
    remaining = max(90 - minute, 0)
    so_far = xg_totals(match, upto_minute=minute)

    rates = {}
    for team in ("A", "B"):
        pace = so_far[team] / played * 90
        weight = played / 90
        per90 = (1 - weight) * prior_rate + weight * pace
        rates[team] = per90 * remaining / 90

    outcomes = {"A": 0, "draw": 0, "B": 0}
    for _ in range(runs):
        a = current["A"] + _poisson(rng, rates["A"])
        b = current["B"] + _poisson(rng, rates["B"])
        if a > b:
            outcomes["A"] += 1
        elif a < b:
            outcomes["B"] += 1
        else:
            outcomes["draw"] += 1
    return {k: round(v / runs, 3) for k, v in outcomes.items()}


def win_probability_timeline(match: Match, step: int = 5, seed: int = 0) -> list[dict]:
    rows = []
    for minute in range(0, 91, step):
        p = win_probability(match, minute, runs=1500, seed=seed)
        rows.append({"minute": minute, **score_at(match, minute),
                     **{f"p_{k}": v for k, v in p.items()}})
    return rows


if __name__ == "__main__":
    path = sys.argv[1] if len(sys.argv) > 1 else "data/sample_match.json"
    match = Match.model_validate_json(Path(path).read_text(encoding="utf-8"))
    final = score_at(match, 999)
    print(f"{match.match_id}: final score A {final['A']} - {final['B']} B, xG {xg_totals(match)}")
    print("\nPressure index per 5-minute window:")
    for row in pressure_windows(match):
        print(f"  {row['start']:2d}-{row['end']:2d}  A {row['press_A']:.2f}   B {row['press_B']:.2f}")
    print("\nWin probability timeline:")
    for row in win_probability_timeline(match, step=15):
        print(f"  {row['minute']:2d}'  {row['A']}-{row['B']}   "
              f"A {row['p_A']:.0%}  draw {row['p_draw']:.0%}  B {row['p_B']:.0%}")
