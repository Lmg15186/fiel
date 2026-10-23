"""Deterministic tactical memory built from completed synthetic matches.

The memory is deliberately simple and inspectable: for each fictional team it
stores average possession, pass accuracy, recovery height and pressure, plus
the match ids used. The current match can be excluded to prevent leakage.
"""

from __future__ import annotations

import json
from pathlib import Path

from fiel.claims import Match
from fiel.tactics import pressure_windows
from fiel.verifier import recompute

MEMORY_METRICS = ("possession_pct", "pass_accuracy_pct", "recovery_height")


def team_codes(match_id: str) -> dict[str, str]:
    """Map in-match sides A/B to fictional team codes encoded in the id."""
    parts = match_id.split("-")
    if len(parts) < 4:
        return {"A": "A", "B": "B"}
    return {"A": parts[-2], "B": parts[-1]}


def _match_profile(match: Match, side: str) -> dict[str, float]:
    end = max((event.minute for event in match.events), default=89) + 1
    values = {
        metric: recompute(metric, side, match, 0, end)
        for metric in MEMORY_METRICS
    }
    pressure = pressure_windows(match)
    values["pressure"] = (
        sum(row[f"press_{side}"] for row in pressure) / len(pressure)
        if pressure else 0.0
    )
    return {key: round(float(value), 2) for key, value in values.items()
            if value is not None}


def build_memory(data_dir: str | Path, exclude_match_id: str | None = None) -> dict:
    """Build team baselines from every match JSON in ``data_dir``."""
    data_dir = Path(data_dir)
    collected: dict[str, dict] = {}
    paths = sorted(path for path in data_dir.glob("m-*.json")
                   if not path.stem.endswith("_truth"))

    for path in paths:
        match = Match.model_validate_json(path.read_text(encoding="utf-8"))
        if match.match_id == exclude_match_id:
            continue
        codes = team_codes(match.match_id)
        for side in ("A", "B"):
            code = codes[side]
            item = collected.setdefault(code, {"match_ids": [], "samples": []})
            item["match_ids"].append(match.match_id)
            item["samples"].append(_match_profile(match, side))

    memory = {}
    for code, item in sorted(collected.items()):
        metrics = {}
        for metric in (*MEMORY_METRICS, "pressure"):
            values = [sample[metric] for sample in item["samples"] if metric in sample]
            if values:
                metrics[metric] = round(sum(values) / len(values), 2)
        memory[code] = {
            "matches": len(item["match_ids"]),
            "match_ids": item["match_ids"],
            "metrics": metrics,
        }
    return memory


def memory_for_match(match: Match, memory: dict) -> dict:
    """Return the historical profiles relevant to the current A/B sides."""
    codes = team_codes(match.match_id)
    return {
        side: {"team_code": code, **memory.get(code, {"matches": 0,
                                                       "match_ids": [],
                                                       "metrics": {}})}
        for side, code in codes.items()
    }


def memory_context(match: Match, memory: dict) -> str:
    relevant = memory_for_match(match, memory)
    return "Historical tactical memory (current match excluded):\n" + json.dumps(
        relevant, indent=1, ensure_ascii=False
    )
