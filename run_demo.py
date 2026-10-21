"""
run_demo.py - the Thursday proof of concept, in the terminal.

Loads a match (the sample one by default, or any generator output passed
as argument), runs the Explainer on three windows, and prints what was
accepted, what was rejected and why, and what came back rewritten.

    python run_demo.py                  # uses data/sample_match.json
    python run_demo.py data/match_03.json
"""

import json
import sys
from pathlib import Path

from fiel.claims import Match
from fiel.explainer import explain_and_verify
from fiel.sample_match import build_sample


def load_match(path: str | None) -> Match:
    if path:
        return Match.model_validate_json(Path(path).read_text(encoding="utf-8"))
    return build_sample()


def main():
    match = load_match(sys.argv[1] if len(sys.argv) > 1 else None)
    print(f"Match {match.match_id}: {len(match.events)} events\n")

    windows = [
        (0, 15, "Opening phase."),
        (55, 65, "Ten minutes before a substitution by team B."),
        (65, 75, "Team B made a substitution at 65'. Compare with the previous window."),
    ]

    for start, end, context in windows:
        print(f"=== minute {start}-{end} ===")
        final, history = explain_and_verify(match, start, end, context)
        for h in history:
            status = "ACCEPTED" if h["ok"] else "REJECTED"
            print(f"  attempt {h['attempt']}: {status}")
            print(f"    \"{h['claim']['claim']}\"")
            print(f"    {h['claim']['metric']} = {h['claim']['value']} "
                  f"({len(h['claim']['event_ids'])} events)")
            for r in h["reasons"]:
                print(f"    - {r}")
        if final is None:
            print("  -> NOT ON AIR (failed after rewrites)\n")
        else:
            print("  -> ON AIR\n")

    Path("data").mkdir(exist_ok=True)
    Path("data/last_run.json").write_text(
        json.dumps(history, indent=2, ensure_ascii=False), encoding="utf-8"
    )


if __name__ == "__main__":
    main()
