"""
generator.py - synthetic, football-realistic match generator (v0).

Four fictional teams, each with a tactical profile that shapes the events:
  press-high          recovers the ball high up the pitch, lots of passes
  low-block-counter   defends deep, few passes, shots from counters
  possession          many passes, high accuracy, few shots per pass
  direct              fewer passes, more shots

Every match also PLANTS one or two stories on purpose, and writes them to a
truth file. The evaluation later counts how many of them the Explainer found.

Run:
    python -m fiel.generator --matches 6 --out data
    python -m fiel.generator --matches 1 --seed 42 --out data

Output per match: data/<match_id>.json (events) and data/<match_id>_truth.json
"""

import argparse
import json
import random
from pathlib import Path

from fiel.claims import Event, Match

# --- team profiles ----------------------------------------------------------

# passes per minute, pass accuracy, recovery height (mean x), shots per 10 min
PROFILES = {
    "press-high":        {"passes": 5.0, "accuracy": 0.82, "rec_x": 55, "shots10": 1.4},
    "low-block-counter": {"passes": 3.0, "accuracy": 0.74, "rec_x": 28, "shots10": 1.0},
    "possession":        {"passes": 7.0, "accuracy": 0.88, "rec_x": 42, "shots10": 0.9},
    "direct":            {"passes": 3.5, "accuracy": 0.70, "rec_x": 38, "shots10": 1.6},
}

# The four fictional teams. Codes only, never real club names.
TEAMS = {
    "T1": "press-high",
    "T2": "low-block-counter",
    "T3": "possession",
    "T4": "direct",
}

# Stories the generator knows how to plant. Each one changes the numbers
# inside a window so a true claim exists there.
STORY_KINDS = ["recover_higher_after_sub", "possession_drop_after_goal"]


class MatchBuilder:
    """Builds one match event by event. Keeps the id counter and rng."""

    def __init__(self, match_id: str, home_code: str, away_code: str, seed: int):
        self.match_id = match_id
        self.rng = random.Random(seed)
        self.events: list[Event] = []
        self.counter = 0
        # Inside the match the teams are always "A" (home) and "B" (away).
        self.profile = {"A": dict(PROFILES[TEAMS[home_code]]),
                        "B": dict(PROFILES[TEAMS[away_code]])}
        self.codes = {"A": home_code, "B": away_code}
        self.planted: list[dict] = []
        # per-minute overrides used by planted stories
        self.rec_x_override: dict[str, dict[int, float]] = {"A": {}, "B": {}}
        self.pass_mult: dict[str, dict[int, float]] = {"A": {}, "B": {}}

    # -- helpers -------------------------------------------------------------

    def add(self, minute, etype, team, player, x, y, outcome="n/a", meta=None):
        self.counter += 1
        self.events.append(Event(
            id=f"e{self.counter:04d}", minute=minute, second=self.rng.randint(0, 59),
            type=etype, team=team, player=player, x=round(x, 1), y=round(y, 1),
            outcome=outcome, meta=meta or {},
        ))

    def player(self, team, lo=1, hi=11):
        return f"{team}{self.rng.randint(lo, hi)}"

    # -- planted stories -----------------------------------------------------

    def plant_recover_higher_after_sub(self, team: str):
        sub_minute = self.rng.randint(55, 70)
        for m in range(sub_minute, 90):
            self.rec_x_override[team][m] = self.profile[team]["rec_x"] + 18
        self.add(sub_minute, "substitution", team, f"{team}12", 50, 50, "n/a",
                 {"off": f"{team}6", "on": f"{team}12"})
        self.planted.append({
            "id": f"story-{len(self.planted) + 1}",
            "kind": "recover_higher_after_sub",
            "description": f"Team {team} recovers the ball about 18 metres higher "
                           f"after the substitution at {sub_minute}'.",
            "metric": "recovery_height", "team": team,
            "before": [sub_minute - 10, sub_minute],
            "after": [sub_minute, min(sub_minute + 10, 90)],
        })

    def plant_possession_drop_after_goal(self, team: str):
        goal_minute = self.rng.randint(20, 60)
        other = "B" if team == "A" else "A"
        for m in range(goal_minute, min(goal_minute + 15, 90)):
            self.pass_mult[team][m] = 0.5   # the scoring team sits back
            self.pass_mult[other][m] = 1.4  # the other team pushes
        self.add(goal_minute, "goal", team, self.player(team, 7, 11), 94, 50, "success")
        self.planted.append({
            "id": f"story-{len(self.planted) + 1}",
            "kind": "possession_drop_after_goal",
            "description": f"After scoring at {goal_minute}', team {team} loses most of the "
                           f"ball; team {other} dominates possession for 15 minutes.",
            "metric": "possession_pct", "team": other,
            "before": [max(goal_minute - 15, 0), goal_minute],
            "after": [goal_minute, min(goal_minute + 15, 90)],
        })

    # -- the match loop ------------------------------------------------------

    def build(self, stories: list[str]) -> Match:
        for kind in stories:
            team = self.rng.choice(["A", "B"])
            getattr(self, f"plant_{kind}")(team)

        for minute in range(0, 90):
            for team in ("A", "B"):
                p = self.profile[team]
                n_pass = p["passes"] * self.pass_mult[team].get(minute, 1.0)
                n_pass = max(1, round(self.rng.gauss(n_pass, 1.0)))
                for _ in range(n_pass):
                    self.add(minute, "pass", team, self.player(team),
                             self.rng.uniform(15, 85), self.rng.uniform(0, 100),
                             "success" if self.rng.random() < p["accuracy"] else "fail")

                # a recovery every other minute, height from profile or story
                if self.rng.random() < 0.55:
                    rec_x = self.rec_x_override[team].get(minute, p["rec_x"])
                    self.add(minute, "recovery", team, self.player(team),
                             self.rng.gauss(rec_x, 4), self.rng.uniform(10, 90), "success")

                if self.rng.random() < p["shots10"] / 10:
                    on_target = self.rng.random() < 0.38
                    self.add(minute, "shot", team, self.player(team, 7, 11),
                             self.rng.uniform(78, 96), self.rng.uniform(30, 70),
                             "success" if on_target else "fail")
                    # a small share of shots on target become goals
                    if on_target and self.rng.random() < 0.28:
                        self.add(minute, "goal", team, self.player(team, 7, 11),
                                 94, self.rng.uniform(40, 60), "success")

            if self.rng.random() < 0.08:
                team = self.rng.choice(["A", "B"])
                self.add(minute, "foul", team, self.player(team),
                         self.rng.uniform(20, 80), self.rng.uniform(0, 100), "n/a")

        self.events.sort(key=lambda e: (e.minute, e.second))
        return Match(match_id=self.match_id, home="A", away="B", events=self.events)


def fixtures(n: int, rng: random.Random):
    """n home/away pairs from the four teams, no team against itself."""
    codes = list(TEAMS)
    out = []
    for _ in range(n):
        home, away = rng.sample(codes, 2)
        out.append((home, away))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--matches", type=int, default=6)
    ap.add_argument("--seed", type=int, default=2026)
    ap.add_argument("--out", default="data")
    args = ap.parse_args()

    rng = random.Random(args.seed)
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)

    for i, (home, away) in enumerate(fixtures(args.matches, rng), start=1):
        match_id = f"m-{i:03d}-{home}-{away}"
        builder = MatchBuilder(match_id, home, away, seed=rng.randint(0, 10**6))
        stories = rng.sample(STORY_KINDS, k=rng.choice([1, 2]))
        match = builder.build(stories)

        (out / f"{match_id}.json").write_text(match.model_dump_json(indent=1), encoding="utf-8")
        truth = {
            "match_id": match_id,
            "home_code": home, "away_code": away,
            "home_profile": TEAMS[home], "away_profile": TEAMS[away],
            "planted_stories": builder.planted,
        }
        (out / f"{match_id}_truth.json").write_text(json.dumps(truth, indent=2), encoding="utf-8")
        print(f"{match_id}: {len(match.events)} events, "
              f"{len(builder.planted)} planted story(ies)")


if __name__ == "__main__":
    main()
