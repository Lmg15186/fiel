"""
explainer.py - the Explainer agent and the rewrite loop.

explain_window()  asks the model for ONE claim about a time window,
                  giving it the recomputed numbers and the event ids,
                  so it has no reason to invent anything.
rewrite()         sends a rejected claim back with the verifier's reasons
                  and asks for a corrected one.
explain_and_verify()  runs narrator -> verifier -> editor, at most two
                  rewrites, and returns the final claim or None.
"""

import json

from fiel.claims import Claim, Match
from fiel.llm_json import ask_json
from fiel.verifier import recompute, verify

METRICS = [
    "possession_pct", "recovery_height", "shots",
    "shots_on_target", "goals", "pass_accuracy_pct",
]

SYSTEM = """You are the Explainer agent of FIEL, a live football intelligence engine.
You write ONE short sentence for broadcast about a time window of a match,
and you attach the receipt: the metric, its value and the event ids that back it.

Rules:
- Use ONLY the numbers given to you. Never invent a number.
- Pick one metric from the list and report its value exactly as given.
- event_ids must be the ids given for that metric and team, nothing else.
- Do not state causes ("because", "won the game", "decided") unless you set
  "causal": true, and only do that when the evidence is overwhelming.
- Teams are called "team A" and "team B". No real club names.

Output JSON with exactly these keys:
{"claim": string, "metric": string, "value": number, "team": "A" or "B",
 "window_start": int, "window_end": int, "event_ids": [string],
 "causal": bool, "confidence": number between 0 and 1}
"""


def _facts_for(match: Match, start: int, end: int) -> dict:
    """Recompute every metric for both teams and list the supporting ids."""
    facts = {}
    for team in ("A", "B"):
        for metric in METRICS:
            value = recompute(metric, team, match, start, end)
            if value is None:
                continue
            etype = {
                "possession_pct": "pass", "pass_accuracy_pct": "pass",
                "recovery_height": "recovery", "shots": "shot",
                "shots_on_target": "shot", "goals": "goal",
            }[metric]
            ids = [e.id for e in match.events_between(start, end)
                   if e.team == team and e.type == etype]
            facts[f"{team}.{metric}"] = {"value": round(value, 1), "event_ids": ids}
    return facts


def explain_window(match: Match, start: int, end: int, context: str = "") -> Claim:
    facts = _facts_for(match, start, end)
    user = (
        f"Match {match.match_id}, window minute {start} to {end}.\n"
        f"{context}\n"
        f"Facts (metric -> value and supporting event ids):\n"
        f"{json.dumps(facts, indent=1)}\n"
        "Write the most interesting true claim for this window."
    )
    data = ask_json(SYSTEM, user)
    return Claim(**data)


def rewrite(claim: Claim, reasons: list[str], match: Match) -> Claim:
    facts = _facts_for(match, claim.window_start, claim.window_end)
    user = (
        "Your previous claim was REJECTED by the verifier.\n"
        f"Claim: {claim.model_dump_json()}\n"
        f"Reasons: {reasons}\n"
        f"Facts you may use:\n{json.dumps(facts, indent=1)}\n"
        "Rewrite it so every reason is fixed. Keep the same window."
    )
    data = ask_json(SYSTEM, user)
    return Claim(**data)


def explain_and_verify(match: Match, start: int, end: int, context: str = "",
                       max_rewrites: int = 2):
    """Returns (final_claim_or_None, history) where history lists each attempt."""
    history = []
    claim = explain_window(match, start, end, context)
    for attempt in range(max_rewrites + 1):
        verdict = verify(claim, match)
        history.append({"attempt": attempt + 1, "claim": claim.model_dump(),
                        "ok": verdict.ok, "reasons": verdict.reasons})
        if verdict.ok:
            return claim, history
        if attempt == max_rewrites:
            break
        claim = rewrite(claim, verdict.reasons, match)
    return None, history
