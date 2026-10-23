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
from pathlib import Path

from fiel.agent_workflow import demo_windows, run_pipeline
from fiel.claims import Match
from fiel.memory import build_memory

DEFAULT_MATCH = Path("data/m-003-T4-T3.json")
DEFAULT_OUTPUT = Path("data/last_agents_run.json")


def load_match(path: str | Path) -> Match:
    return Match.model_validate_json(Path(path).read_text(encoding="utf-8"))


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
