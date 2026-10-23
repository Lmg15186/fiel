"""Tests for the API (offline: no model calls). Run with:  pytest -q"""

import json
from pathlib import Path

from fastapi.testclient import TestClient

from fiel import api
from fiel.generator import MatchBuilder


def make_client(tmp_path, monkeypatch):
    # point the API at a temporary data folder with one generated match
    match = MatchBuilder("m-901-T1-T2", "T1", "T2", seed=9).build(["recover_higher_after_sub"])
    (tmp_path / "m-901-T1-T2.json").write_text(match.model_dump_json(), encoding="utf-8")
    (tmp_path / "m-901-T1-T2_truth.json").write_text(
        json.dumps({"planted_stories": [{"id": "story-1"}]}), encoding="utf-8")
    monkeypatch.setattr(api, "DATA_DIR", tmp_path)
    monkeypatch.setattr(api, "CLAIMS_DIR", tmp_path / "claims")
    return TestClient(api.app)


def test_health_and_matches(tmp_path, monkeypatch):
    client = make_client(tmp_path, monkeypatch)
    assert client.get("/health").json()["status"] == "ok"
    body = client.get("/matches").json()
    assert body[0]["match_id"] == "m-901-T1-T2"
    assert body[0]["planted_stories"] == 1


def test_state_and_timeline(tmp_path, monkeypatch):
    client = make_client(tmp_path, monkeypatch)
    s = client.get("/matches/m-901-T1-T2/state?minute=70").json()
    assert set(s["win_probability"]) == {"A", "draw", "B"}
    assert abs(sum(s["win_probability"].values()) - 1) < 0.01
    t = client.get("/matches/m-901-T1-T2/timeline").json()
    assert len(t["win_probability"]) == 19
    assert t["pressure"][0]["start"] == 0


def test_events_by_ids_and_window(tmp_path, monkeypatch):
    client = make_client(tmp_path, monkeypatch)
    window = client.get("/matches/m-901-T1-T2/events?start=10&end=12").json()
    assert window and all(10 <= e["minute"] < 12 for e in window)
    first = window[0]["id"]
    by_id = client.get(f"/matches/m-901-T1-T2/events?ids={first}").json()
    assert len(by_id) == 1 and by_id[0]["id"] == first


def test_claims_without_cache_is_empty(tmp_path, monkeypatch):
    client = make_client(tmp_path, monkeypatch)
    body = client.get("/matches/m-901-T1-T2/claims").json()
    assert body["claims"] == [] and "note" in body


def test_unknown_match_is_404(tmp_path, monkeypatch):
    client = make_client(tmp_path, monkeypatch)
    assert client.get("/matches/nope/state").status_code == 404


def test_broadcast_package(tmp_path, monkeypatch):
    client = make_client(tmp_path, monkeypatch)
    package = {"match_id": "m-901-T1-T2", "on_air": [{"text": "Verified."}]}
    (tmp_path / "demo_agents.json").write_text(json.dumps(package), encoding="utf-8")
    assert client.get("/matches/m-901-T1-T2/broadcast").json() == package


def test_root_redirects_to_docs(tmp_path, monkeypatch):
    client = make_client(tmp_path, monkeypatch)
    r = client.get("/", follow_redirects=False)
    assert r.status_code in (302, 307) and r.headers["location"] == "/docs"


def test_claims_fall_back_to_cached_broadcast(tmp_path, monkeypatch):
    client = make_client(tmp_path, monkeypatch)
    receipt = {"claim": "x", "metric": "shots", "value": 1, "team": "A",
               "window_start": 0, "window_end": 10, "event_ids": ["e0001"]}
    package = {"match_id": "m-901-T1-T2", "on_air": [{"receipt": receipt}],
               "verification_history": [{"window": [0, 10]}]}
    (tmp_path / "demo_agents.json").write_text(json.dumps(package), encoding="utf-8")
    body = client.get("/matches/m-901-T1-T2/claims").json()
    assert body["claims"] == [receipt] and body["history"] == [{"window": [0, 10]}]


def test_memory_excludes_current_match(tmp_path, monkeypatch):
    client = make_client(tmp_path, monkeypatch)
    body = client.get("/matches/m-901-T1-T2/memory").json()
    # only one match in the folder, so there is no history for either side
    assert body["teams"]["A"]["matches"] == 0 and body["teams"]["B"]["match_ids"] == []


def test_verify_endpoint_is_deterministic(tmp_path, monkeypatch):
    client = make_client(tmp_path, monkeypatch)
    window = client.get("/matches/m-901-T1-T2/events?start=10&end=25").json()
    shots = [e for e in window if e["type"] == "shot" and e["team"] == "A"]
    claim = {"claim": "Team A had some shots between 10' and 25'.",
             "metric": "shots", "value": len(shots), "team": "A",
             "window_start": 10, "window_end": 25,
             "event_ids": [e["id"] for e in shots] or [window[0]["id"]]}
    good = client.post("/matches/m-901-T1-T2/verify", json=claim).json()
    assert good["verdict"]["ok"] is True
    bad = client.post("/matches/m-901-T1-T2/verify", json=dict(claim, value=99)).json()
    assert bad["verdict"]["ok"] is False and bad["verdict"]["reasons"]
    # a malformed claim is rejected by the schema, not by the verifier
    assert client.post("/matches/m-901-T1-T2/verify", json={"claim": "x"}).status_code == 422
