"""
api.py - the FIEL HTTP API (FastAPI).

This is what the replay screen talks to, and what gets deployed to
Azure Container Apps. All numbers come from the Tactics Engine; the
sentences come from claims the verifier already approved.

Endpoints:
  GET /health                         liveness check for the deploy
  GET /matches                        list of match ids in data/
  GET /matches/{id}/state?minute=70   score, xG, win probability at a minute
  GET /matches/{id}/timeline          win probability and pressure per window
  GET /matches/{id}/claims            approved claims with receipts
                                      (?generate=true runs the agents and caches)
  GET /matches/{id}/events?start=65&end=75   raw events, for the receipt view

Run locally:
    uvicorn fiel.api:app --reload --port 8000
    open http://127.0.0.1:8000/docs
"""

import json
from pathlib import Path

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from fiel.claims import Match
from fiel.tactics import (pressure_windows, score_at, win_probability,
                          win_probability_timeline, xg_totals)

DATA_DIR = Path("data")
CLAIMS_DIR = DATA_DIR / "claims"

app = FastAPI(title="FIEL API", version="0.1",
              description="Football Intelligence Engine, Live - every sentence with a receipt.")

# The React frontend runs on another port/origin during development.
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["GET"],
                   allow_headers=["*"])


# --- helpers ----------------------------------------------------------------

def list_match_ids() -> list[str]:
    return sorted(p.stem for p in DATA_DIR.glob("m-*.json")
                  if not p.stem.endswith("_truth"))


def load_match(match_id: str) -> Match:
    path = DATA_DIR / f"{match_id}.json"
    if not path.exists():
        raise HTTPException(status_code=404, detail=f"match {match_id} not found")
    return Match.model_validate_json(path.read_text(encoding="utf-8"))


def default_windows(match: Match) -> list[tuple[int, int, str]]:
    """Every 15 minutes, plus the 10 minutes after each substitution."""
    windows = [(s, s + 15, "Regular window.") for s in range(0, 90, 15)]
    for e in match.events:
        if e.type == "substitution":
            windows.append((e.minute, min(e.minute + 10, 90),
                            f"Team {e.team} made a substitution at {e.minute}'. "
                            "Compare with the minutes before."))
    return sorted(set(windows))


# --- endpoints --------------------------------------------------------------

@app.get("/health")
def health():
    return {"status": "ok", "matches": len(list_match_ids())}


@app.get("/matches")
def matches():
    out = []
    for mid in list_match_ids():
        m = load_match(mid)
        final = score_at(m, 999)
        truth_path = DATA_DIR / f"{mid}_truth.json"
        planted = 0
        if truth_path.exists():
            planted = len(json.loads(truth_path.read_text(encoding="utf-8"))["planted_stories"])
        out.append({"match_id": mid, "home": m.home, "away": m.away,
                    "events": len(m.events), "final": final, "planted_stories": planted})
    return out


@app.get("/matches/{match_id}/state")
def state(match_id: str, minute: int = Query(90, ge=0, le=130)):
    m = load_match(match_id)
    return {
        "match_id": match_id, "minute": minute,
        "score": score_at(m, minute),
        "xg": xg_totals(m, upto_minute=minute),
        "win_probability": win_probability(m, minute, runs=2000),
    }


@app.get("/matches/{match_id}/timeline")
def timeline(match_id: str):
    m = load_match(match_id)
    return {
        "match_id": match_id,
        "win_probability": win_probability_timeline(m, step=5),
        "pressure": pressure_windows(m),
    }


@app.get("/matches/{match_id}/events")
def events(match_id: str, start: int = Query(0, ge=0), end: int = Query(90, ge=1),
           ids: str | None = None):
    """Raw events for a window, or specific ids (comma separated) for a receipt."""
    m = load_match(match_id)
    if ids:
        wanted = set(ids.split(","))
        return [e.model_dump() for e in m.events if e.id in wanted]
    return [e.model_dump() for e in m.events_between(start, end)]


@app.get("/matches/{match_id}/claims")
def claims(match_id: str, generate: bool = False):
    """
    Approved claims with receipts. Reads data/claims/<id>.json if it exists.
    With ?generate=true, runs the Explainer + verifier on the default windows
    (costs model calls, takes a minute) and caches the result.
    """
    m = load_match(match_id)
    cache = CLAIMS_DIR / f"{match_id}.json"
    if cache.exists() and not generate:
        return json.loads(cache.read_text(encoding="utf-8"))
    if not generate:
        return {"match_id": match_id, "claims": [], "history": [],
                "note": "no cached claims; call with ?generate=true"}

    # imported here so the API can start without a .env when only serving stats
    from fiel.explainer import explain_and_verify

    approved, history = [], []
    for start, end, context in default_windows(m):
        final, hist = explain_and_verify(m, start, end, context)
        history.extend(hist)
        if final:
            item = final.model_dump()
            item["win_probability_at_start"] = win_probability(m, start, runs=1000)
            approved.append(item)

    result = {"match_id": match_id, "claims": approved, "history": history}
    CLAIMS_DIR.mkdir(parents=True, exist_ok=True)
    cache.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    return result
