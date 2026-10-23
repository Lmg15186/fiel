"""Run the complete FIEL agent pipeline against one synthetic match.

This is the integration demo for the three model-backed roles:

    Explainer -> deterministic Verifier/rewrite -> Producer -> Personalizer

The default run uses three useful windows so it is quick enough for a live
demo while still giving the Producer more than one approved claim to rank.

Examples:
    python run_agents.py
    python run_agents.py data/m-003-T4-T3.json --audience fan --language pt
"""

from __future__ import annotations

import argparse
import json
from collections.abc import Callable
from pathlib import Path

from fiel.claims import Claim, Match
from fiel.explainer import explain_and_verify
from fiel.memory import build_memory, memory_for_match
from fiel.personalizer import personalize
from fiel.producer import produce

DEFAULT_MATCH = Path("data/m-003-T4-T3.json")
DEFAULT_OUTPUT = Path("data/last_agents_run.json")


def load_match(path: str | Path) -> Match:
    return Match.model_validate_json(Path(path).read_text(encoding="utf-8"))


def demo_windows(match: Match) -> list[tuple[int, int, str]]:
    """Return an opening window and the windows around a substitution."""
    windows = [(0, 15, "Opening phase.")]
    substitutions = [e for e in match.events if e.type == "substitution"]
    preferred = next((e for e in substitutions if e.team == "B"), None)
    substitution = preferred or (substitutions[0] if substitutions else None)

    if substitution is not None:
        minute = substitution.minute
        windows.extend([
            (max(0, minute - 10), minute,
             f"Ten minutes before team {substitution.team}'s substitution."),
            (minute, min(minute + 10, 90),
             f"Team {substitution.team} made a substitution at {minute}'. "
             "Compare with the previous window."),
        ])

    # Keep order while removing a possible zero-length or duplicate window.
    return list(dict.fromkeys(w for w in windows if w[1] > w[0]))


def run_pipeline(
    match: Match,
    audience: str = "fan",
    language: str = "pt",
    max_items: int = 3,
    reporter: Callable[[str], None] | None = None,
    memory: dict | None = None,
) -> dict:
    """Run every role and return a JSON-serialisable integration result."""
    approved: list[Claim] = []
    verification_history: list[dict] = []

    for start, end, context in demo_windows(match):
        if reporter:
            reporter(f"Explainer: analysing minutes {start}-{end}...")
        claim, history = explain_and_verify(match, start, end, context, memory=memory)
        verification_history.append({
            "window": [start, end],
            "context": context,
            "attempts": history,
            "accepted": claim is not None,
        })
        if claim is not None:
            approved.append(claim)

    if reporter:
        reporter(f"Producer: ranking {len(approved)} approved claim(s)...")
    rundown = produce(approved, max_items=max_items)

    on_air = []
    for position, item in enumerate(rundown, start=1):
        claim = Claim.model_validate(item["claim"])
        if reporter:
            reporter(f"Personalizer: preparing item {position} for {audience}/{language}...")
        version = personalize(claim, audience, language, match, memory)
        on_air.append({
            "position": position,
            "why_now": item["why_now"],
            "text": version["text"],
            "audience": version["audience"],
            "language": version["language"],
            "personalization_verified": version["verified"],
            "receipt": claim.model_dump(),
        })

    return {
        "match_id": match.match_id,
        "audience": audience,
        "language": language,
        "match_memory": memory_for_match(match, memory or {}),
        "windows_analysed": len(verification_history),
        "approved_claims": len(approved),
        "verification_history": verification_history,
        "on_air": on_air,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run the complete FIEL agent pipeline.")
    parser.add_argument("match", nargs="?", default=str(DEFAULT_MATCH),
                        help="match JSON path (default: data/m-003-T4-T3.json)")
    parser.add_argument("--audience", choices=("analyst", "fan"), default="fan")
    parser.add_argument("--language", choices=("en", "pt"), default="pt")
    parser.add_argument("--max-items", type=int, choices=range(1, 4), default=3)
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT),
                        help="where to save the full JSON result")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    match = load_match(args.match)
    memory = build_memory(Path(args.match).parent, exclude_match_id=match.match_id)
    print(f"FIEL agents — {match.match_id} ({len(match.events)} events)")
    result = run_pipeline(match, args.audience, args.language, args.max_items, print, memory)

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")

    print("\nON AIR")
    if not result["on_air"]:
        print("  No claim survived the complete pipeline.")
    for item in result["on_air"]:
        receipt = item["receipt"]
        print(f"  {item['position']}. {item['text']}")
        print(f"     why now: {item['why_now']}")
        print(f"     receipt: {receipt['metric']}={receipt['value']}, "
              f"minutes {receipt['window_start']}-{receipt['window_end']}, "
              f"{len(receipt['event_ids'])} event(s)")
    print(f"\nFull result saved to {output}")


if __name__ == "__main__":
    main()
