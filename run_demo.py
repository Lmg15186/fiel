"""
run_demo.py - the proof of concept, in the terminal.

Runs the Explainer on three windows, then stages the key moment for the
pitch: a claim that overstates the evidence, the verifier rejecting it
with a reason, and the editor rewriting it.

    python run_demo.py                  # built-in sample match
    python run_demo.py data/m-003-T4-T3.json
"""

import json
import sys
from pathlib import Path

from fiel.claims import Claim, Match
from fiel.explainer import explain_and_verify, rewrite
from fiel.sample_match import build_sample
from fiel.tactics import score_at, win_probability, xg_totals
from fiel.verifier import recompute, verify


def load_match(path: str | None) -> Match:
    if path:
        return Match.model_validate_json(Path(path).read_text(encoding="utf-8"))
    return build_sample()


def print_history(history):
    for h in history:
        status = "ACCEPTED" if h["ok"] else "REJECTED"
        print(f"  attempt {h['attempt']}: {status}")
        print(f"    \"{h['claim']['claim']}\"")
        print(f"    {h['claim']['metric']} = {h['claim']['value']} "
              f"({len(h['claim']['event_ids'])} events)")
        for r in h["reasons"]:
            print(f"    - {r}")


def forced_rejection(match: Match, sub_minute: int):
    """Stage the pitch scene: an overstated causal claim with thin evidence."""
    start, end = sub_minute, min(sub_minute + 10, 90)
    ids = [e.id for e in match.events_between(start, end)
           if e.team == "B" and e.type == "recovery"][:2]
    value = recompute("recovery_height", "B", match, start, end)
    if value is None or not ids:
        print("  (no recoveries in this window, skipping the staged scene)")
        return
    claim = Claim(
        claim=f"The substitution at {sub_minute}' won the game for team B.",
        metric="recovery_height", value=round(value, 1), team="B",
        window_start=start, window_end=end, event_ids=ids, causal=True,
    )
    history = []
    for attempt in range(1, 4):
        verdict = verify(claim, match)
        history.append({"attempt": attempt, "claim": claim.model_dump(),
                        "ok": verdict.ok, "reasons": verdict.reasons})
        if verdict.ok or attempt == 3:
            break
        claim = rewrite(claim, verdict.reasons, match)
    print_history(history)
    print("  -> ON AIR\n" if history[-1]["ok"] else "  -> NOT ON AIR\n")
    return history


def main():
    match = load_match(sys.argv[1] if len(sys.argv) > 1 else None)
    final_score = score_at(match, 999)
    print(f"Match {match.match_id}: {len(match.events)} events, "
          f"final A {final_score['A']}-{final_score['B']} B, xG {xg_totals(match)}\n")

    subs = [e for e in match.events if e.type == "substitution" and e.team == "B"]
    sub_minute = subs[0].minute if subs else 65

    windows = [
        (0, 15, "Opening phase."),
        (sub_minute - 10, sub_minute, "Ten minutes before a substitution by team B."),
        (sub_minute, min(sub_minute + 10, 90),
         f"Team B made a substitution at {sub_minute}'. Compare with the previous window."),
    ]

    all_history = []
    for start, end, context in windows:
        p = win_probability(match, start, runs=1000)
        print(f"=== minute {start}-{end}  (win prob at {start}': "
              f"A {p['A']:.0%} / draw {p['draw']:.0%} / B {p['B']:.0%}) ===")
        final, history = explain_and_verify(match, start, end, context)
        print_history(history)
        print("  -> ON AIR\n" if final else "  -> NOT ON AIR (failed after rewrites)\n")
        all_history.extend(history)

    print("=== staged scene: narrator overstates the cause ===")
    staged = forced_rejection(match, sub_minute)
    if staged:
        all_history.extend(staged)

    Path("data").mkdir(exist_ok=True)
    Path("data/last_run.json").write_text(
        json.dumps(all_history, indent=2, ensure_ascii=False), encoding="utf-8")


if __name__ == "__main__":
    main()
    