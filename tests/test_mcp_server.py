"""Offline tests for the MCP server. No transport, no model calls."""

import asyncio
import json

import pytest

from fiel import mcp_server
from fiel.generator import MatchBuilder


@pytest.fixture
def data_dir(tmp_path, monkeypatch):
    # two matches so the memory of one can be built from the other
    for mid, seed in (("m-901-T1-T2", 9), ("m-902-T2-T1", 10)):
        match = MatchBuilder(mid, mid.split("-")[-2], mid.split("-")[-1],
                             seed=seed).build(["recover_higher_after_sub"])
        (tmp_path / f"{mid}.json").write_text(match.model_dump_json(), encoding="utf-8")
    monkeypatch.setattr(mcp_server, "DATA_DIR", tmp_path)
    return tmp_path


def test_tools_are_registered():
    tools = asyncio.run(mcp_server.server.list_tools())
    names = {tool.name for tool in tools}
    assert {"list_matches", "get_match_state", "get_timeline", "get_events",
            "get_team_memory", "get_broadcast", "verify_claim"} <= names
    # every tool has a description, which is what an external agent reads
    assert all(tool.description for tool in tools)


def test_list_and_state(data_dir):
    matches = mcp_server.list_matches_data()
    assert [m["match_id"] for m in matches] == ["m-901-T1-T2", "m-902-T2-T1"]
    state = mcp_server.match_state_data("m-901-T1-T2", 70)
    assert abs(sum(state["win_probability"].values()) - 1) < 0.01
    # the MCP tool and the API must agree, since they share the engine
    assert state["score"] == mcp_server.score_at(mcp_server._load("m-901-T1-T2"), 70)


def test_events_and_memory(data_dir):
    window = mcp_server.events_data("m-901-T1-T2", 10, 12)
    assert window and all(10 <= e["minute"] < 12 for e in window)
    by_id = mcp_server.events_data("m-901-T1-T2", ids=[window[0]["id"]])
    assert len(by_id) == 1
    memory = mcp_server.team_memory_data("m-901-T1-T2")
    # baseline for side A (T1) must come only from the other match
    assert memory["teams"]["A"]["match_ids"] == ["m-902-T2-T1"]


def test_verify_claim_accepts_true_and_rejects_false(data_dir):
    match = mcp_server._load("m-901-T1-T2")
    window = match.events_between(10, 25)
    shots = [e for e in window if e.type == "shot" and e.team == "A"]
    claim = {"claim": "Team A had some shots between 10' and 25'.",
             "metric": "shots", "value": len(shots), "team": "A",
             "window_start": 10, "window_end": 25,
             "event_ids": [e.id for e in shots] or [window[0].id]}
    ok = mcp_server.verify_claim_data("m-901-T1-T2", claim)
    assert ok["verdict"]["ok"] is True

    wrong = dict(claim, value=len(shots) + 50)
    bad = mcp_server.verify_claim_data("m-901-T1-T2", wrong)
    assert bad["verdict"]["ok"] is False
    assert any("value mismatch" in r for r in bad["verdict"]["reasons"])


def test_broadcast_fallback_and_unknown_match(data_dir):
    assert mcp_server.broadcast_data("m-901-T1-T2")["on_air"] == []
    (data_dir / "demo_agents.json").write_text(
        json.dumps({"match_id": "m-901-T1-T2", "on_air": [{"text": "x"}]}), encoding="utf-8")
    assert mcp_server.broadcast_data("m-901-T1-T2")["on_air"] == [{"text": "x"}]
    with pytest.raises(ValueError):
        mcp_server.match_state_data("nope")
