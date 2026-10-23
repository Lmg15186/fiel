"""
api.py - the FIEL HTTP API (FastAPI).

This is what the public judge experience talks to, and what is deployed to
Azure App Service (F1 Free plan). All numbers come from the Tactics Engine;
the sentences come from claims the verifier already approved.

Endpoints:
  GET  /                               redirect to the OpenAPI docs
  GET  /health                         liveness check for the deploy
  GET  /matches                        list of match ids in data/
  GET  /matches/{id}/state?minute=70   score, xG, win probability at a minute
  GET  /matches/{id}/timeline          win probability and pressure per window
  GET  /matches/{id}/memory            historical baseline for both teams
  GET  /matches/{id}/claims            approved claims with receipts
                                       (?generate=true runs the agents and caches)
  GET  /matches/{id}/broadcast         cached Producer/Personalizer output
  GET  /matches/{id}/events?start=65&end=75   raw events, for the receipt view
  POST /matches/{id}/verify            run the deterministic verifier on any claim

Run locally:
    uvicorn fiel.api:app --reload --port 8000
    open http://127.0.0.1:8000/docs
"""

import json
from functools import lru_cache
from pathlib import Path

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse

from fiel.claims import Claim, Match
from fiel.memory import build_memory, memory_for_match
from fiel.tactics import (pressure_windows, score_at, win_probability,
                          win_probability_timeline, xg_totals)
from fiel.verifier import verify

DATA_DIR = Path("data")
CLAIMS_DIR = DATA_DIR / "claims"

app = FastAPI(title="FIEL API", version="0.2",
              description="Football Intelligence Engine, Live - every sentence with a receipt.")

# The judge experience is served from GitHub Pages, so it calls this API from
# another origin. The API is read-only apart from /verify, which only runs
# deterministic Python on the request body, so a permissive CORS policy is fine.
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["GET", "POST"],
                   allow_headers=["*"])


# --- helpers ----------------------------------------------------------------

def list_match_ids() -> list[str]:
    return sorted(p.stem for p in DATA_DIR.glob("m-*.json")
                  if not p.stem.endswith("_truth"))


@lru_cache(maxsize=32)
def _read_match(path: str, mtime: float) -> Match:
    # Cached by path + modification time, so a regenerated file is re-read
    # but repeated slider requests do not re-parse 1,000 events every time.
    return Match.model_validate_json(Path(path).read_text(encoding="utf-8"))


def load_match(match_id: str) -> Match:
    path = DATA_DIR / f"{match_id}.json"
    if not path.exists():
        raise HTTPException(status_code=404, detail=f"match {match_id} not found")
    return _read_match(str(path.resolve()), path.stat().st_mtime)


@lru_cache(maxsize=32)
def _memory_excluding(data_dir: str, match_id: str) -> dict:
    return build_memory(data_dir, exclude_match_id=match_id)


def default_windows(match: Match) -> list[tuple[int, int, str]]:
    """Every 15 minutes, plus the 10 minutes after each substitution."""
    windows = [(s, s + 15, "Regular window.") for s in range(0, 90, 15)]
    for e in match.events:
        if e.type == "substitution":
            windows.append((e.minute, min(e.minute + 10, 90),
                            f"Team {e.team} made a substitution at {e.minute}'. "
                            "Compare with the minutes before."))
    return sorted(set(windows))


def _cached_broadcast(match_id: str) -> dict | None:
    """The real Foundry run saved for the judges, if it belongs to this match."""
    path = DATA_DIR / "demo_agents.json"
    if not path.exists():
        return None
    result = json.loads(path.read_text(encoding="utf-8"))
    return result if result.get("match_id") == match_id else None


# --- endpoints --------------------------------------------------------------

@app.get("/", include_in_schema=False)
def root():
    return RedirectResponse(url="/docs")


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


@app.get("/matches/{match_id}/memory")
def memory(match_id: str):
    """Historical 'usual' values for both sides, built from the other matches."""
    m = load_match(match_id)
    baselines = _memory_excluding(str(DATA_DIR.resolve()), match_id)
    return {"match_id": match_id, "excluded_match_id": match_id,
            "teams": memory_for_match(m, baselines)}


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
    Approved claims with receipts. Reads data/claims/<id>.json if it exists,
    otherwise falls back to the receipts of the cached broadcast package.
    With ?generate=true, runs the Explainer + verifier on the default windows
    (costs model calls, takes a minute) and caches the result.
    """
    m = load_match(match_id)
    cache = CLAIMS_DIR / f"{match_id}.json"
    if cache.exists() and not generate:
        return json.loads(cache.read_text(encoding="utf-8"))
    if not generate:
        package = _cached_broadcast(match_id)
        if package:
            return {"match_id": match_id,
                    "claims": [item["receipt"] for item in package.get("on_air", [])],
                    "history": package.get("verification_history", []),
                    "note": "receipts from the cached Foundry run (data/demo_agents.json)"}
        return {"match_id": match_id, "claims": [], "history": [],
                "note": "no cached claims; call with ?generate=true"}

    # imported here so the API can start without a .env when only serving stats
    from fiel.explainer import explain_and_verify

    approved, history = [], []
    memory = build_memory(DATA_DIR, exclude_match_id=match_id)
    for start, end, context in default_windows(m):
        final, hist = explain_and_verify(m, start, end, context, memory=memory)
        history.extend(hist)
        if final:
            item = final.model_dump()
            item["win_probability_at_start"] = win_probability(m, start, runs=1000)
            approved.append(item)

    result = {"match_id": match_id, "claims": approved, "history": history}
    CLAIMS_DIR.mkdir(parents=True, exist_ok=True)
    cache.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    return result


@app.get("/matches/{match_id}/broadcast")
def broadcast(match_id: str):
    """Return a complete cached agent run for the studio UI."""
    load_match(match_id)  # consistent 404 for unknown matches
    result = _cached_broadcast(match_id)
    if result is None:
        return {"match_id": match_id, "on_air": [],
                "note": "no cached broadcast package for this match"}
    return result


@app.post("/matches/{match_id}/verify")
def verify_claim(match_id: str, claim: Claim):
    """
    Run the deterministic verifier on any claim, without a model call.
    This is the trust boundary of FIEL exposed as an endpoint: paste a claim
    with its receipt and get back ok/rejected with the exact reasons.
    """
    m = load_match(match_id)
    baselines = _memory_excluding(str(DATA_DIR.resolve()), match_id)
    verdict = verify(claim, m, memory=baselines)
    return {"match_id": match_id, "claim": claim.model_dump(),
            "verdict": verdict.model_dump()}
