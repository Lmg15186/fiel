"""
mcp_server.py - FIEL exposed as a Model Context Protocol (MCP) server.

Why this exists: the judging rubric asks whether the project demonstrates
"sophisticated agent orchestration, MCP integration, or multi-agent
collaboration". Inside FIEL the agents talk to each other through Microsoft
Agent Framework; MCP is how *external* agents (GitHub Copilot, Foundry agents,
Claude, VS Code) can use the same verified match intelligence as tools.

Every tool is deterministic Python - no model call happens here - so an
external agent gets the same numbers a judge sees in the API and the UI.

Tools:
  list_matches()                          synthetic matches available
  get_match_state(match_id, minute)       score, xG, win probability
  get_timeline(match_id)                  win probability + pressure per window
  get_events(match_id, start, end, ids)   raw events (the receipt)
  get_team_memory(match_id)               historical baselines for both teams
  get_broadcast(match_id)                 cached on-air package from the real
                                          Foundry run
  verify_claim(match_id, claim)           deterministic verdict on any claim

Run (stdio transport, the one VS Code / Copilot / Claude Desktop expect):
    python -m fiel.mcp_server

Example client config (VS Code `mcp.json` / Claude Desktop):
    {"mcpServers": {"fiel": {"command": "python", "args": ["-m", "fiel.mcp_server"],
                             "cwd": "/path/to/fiel"}}}
"""

from __future__ import annotations

import json
from pathlib import Path

from mcp.server.fastmcp import FastMCP

from fiel.claims import Claim, Match
from fiel.memory import build_memory, memory_for_match
from fiel.tactics import (pressure_windows, score_at, win_probability,
                          win_probability_timeline, xg_totals)
from fiel.verifier import verify

DATA_DIR = Path("data")

server = FastMCP(
    "fiel",
    instructions=(
        "FIEL - Football Intelligence Engine, Live. Synthetic football matches "
        "with deterministic tactical metrics. Every number can be recomputed "
        "from the event ids; use verify_claim before publishing any sentence."
    ),
)


# --- plain functions (tested directly, no MCP transport needed) -------------

def _match_ids() -> list[str]:
    return sorted(p.stem for p in DATA_DIR.glob("m-*.json")
                  if not p.stem.endswith("_truth"))


def _load(match_id: str) -> Match:
    path = DATA_DIR / f"{match_id}.json"
    if not path.exists():
        raise ValueError(f"match {match_id} not found; call list_matches()")
    return Match.model_validate_json(path.read_text(encoding="utf-8"))


def list_matches_data() -> list[dict]:
    out = []
    for mid in _match_ids():
        m = _load(mid)
        out.append({"match_id": mid, "home": m.home, "away": m.away,
                    "events": len(m.events), "final": score_at(m, 999)})
    return out


def match_state_data(match_id: str, minute: int = 90) -> dict:
    m = _load(match_id)
    minute = max(0, min(int(minute), 130))
    return {"match_id": match_id, "minute": minute,
            "score": score_at(m, minute),
            "xg": xg_totals(m, upto_minute=minute),
            "win_probability": win_probability(m, minute, runs=2000)}


def timeline_data(match_id: str) -> dict:
    m = _load(match_id)
    return {"match_id": match_id,
            "win_probability": win_probability_timeline(m, step=5),
            "pressure": pressure_windows(m)}


def events_data(match_id: str, start: int = 0, end: int = 90,
                ids: list[str] | None = None) -> list[dict]:
    m = _load(match_id)
    if ids:
        wanted = set(ids)
        return [e.model_dump() for e in m.events if e.id in wanted]
    return [e.model_dump() for e in m.events_between(start, end)]


def team_memory_data(match_id: str) -> dict:
    m = _load(match_id)
    baselines = build_memory(DATA_DIR, exclude_match_id=match_id)
    return {"match_id": match_id, "excluded_match_id": match_id,
            "teams": memory_for_match(m, baselines)}


def broadcast_data(match_id: str) -> dict:
    _load(match_id)
    path = DATA_DIR / "demo_agents.json"
    if path.exists():
        package = json.loads(path.read_text(encoding="utf-8"))
        if package.get("match_id") == match_id:
            return package
    return {"match_id": match_id, "on_air": [],
            "note": "no cached broadcast package for this match"}


def verify_claim_data(match_id: str, claim: dict) -> dict:
    m = _load(match_id)
    parsed = Claim.model_validate(claim)
    baselines = build_memory(DATA_DIR, exclude_match_id=match_id)
    verdict = verify(parsed, m, memory=baselines)
    return {"match_id": match_id, "claim": parsed.model_dump(),
            "verdict": verdict.model_dump()}


# --- MCP tools (thin wrappers so the schema comes from the signatures) -------

@server.tool()
def list_matches() -> list[dict]:
    """List the synthetic matches FIEL can analyse, with the final score."""
    return list_matches_data()


@server.tool()
def get_match_state(match_id: str, minute: int = 90) -> dict:
    """Score, expected goals and Monte Carlo win probability at a minute."""
    return match_state_data(match_id, minute)


@server.tool()
def get_timeline(match_id: str) -> dict:
    """Win probability every 5 minutes and the pressure index per window."""
    return timeline_data(match_id)


@server.tool()
def get_events(match_id: str, start: int = 0, end: int = 90,
               ids: list[str] | None = None) -> list[dict]:
    """Raw events for a minute window, or the exact events behind a receipt."""
    return events_data(match_id, start, end, ids)


@server.tool()
def get_team_memory(match_id: str) -> dict:
    """Usual possession, pass accuracy, recovery height and pressure for both
    teams, computed from the other matches (the current one is excluded)."""
    return team_memory_data(match_id)


@server.tool()
def get_broadcast(match_id: str) -> dict:
    """The cached on-air package produced by the real Microsoft Foundry run."""
    return broadcast_data(match_id)


@server.tool()
def verify_claim(match_id: str, claim: dict) -> dict:
    """Run FIEL's deterministic verifier on a claim JSON (metric, value, team,
    window_start, window_end, event_ids...). Returns ok plus exact reasons."""
    return verify_claim_data(match_id, claim)


if __name__ == "__main__":
    server.run()  # stdio
